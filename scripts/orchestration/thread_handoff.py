#!/usr/bin/env python
"""Prepare and guard agent-specific thread handoffs.

The Codex app can expose thread and automation tools to an agent, but a local
repo script cannot assume those app-only tools exist. This helper gathers the
durable local state, writes a handoff packet, generates the replacement-thread
bootstrap prompt, and records a lease that prevents old automation cleanup
until the replacement thread is explicitly confirmed.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import gzip
import hashlib
import http.client
import io
import json
import os
import re
import shlex
import shutil
import socket
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable, Mapping
from contextlib import closing, suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

# Script-by-path execution under the shared primary interpreter can expose the
# primary checkout through a site-packages ``.pth`` file before this linked
# worktree.  Prefer the code that is actually being executed without asking
# callers to mutate PYTHONPATH.
_LOCAL_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _LOCAL_REPO_ROOT not in sys.path:
    sys.path.insert(0, _LOCAL_REPO_ROOT)

try:
    from scripts import context_canary
    from scripts.orchestration import task_identity, thread_handoff_canary
    from scripts.orchestration.task_family import codex_state as task_family_codex_state
    from scripts.orchestration.task_family import rollover as task_family_rollover
    from scripts.orchestration.task_family import rollover_registry as task_family_rollover_registry
    from scripts.orchestration.task_family.storage import advisory_lock as task_family_advisory_lock
except ImportError as exc:
    # Two fallback-worthy shapes when running script-by-path (issue #6411):
    #   1. ModuleNotFoundError name="scripts" — repo root not on sys.path.
    #   2. Plain ImportError "cannot import name … from 'scripts'" — a FOREIGN
    #      `scripts` namespace package (e.g. a stray editable install's raw
    #      .pth path) shadows this repo's package. The 2026-08-06 incident
    #      crashed here and the SessionStart hook mislabeled the crash as a
    #      lease conflict.
    # A genuine missing submodule/dependency (ModuleNotFoundError for anything
    # other than `scripts`) still raises; so does any failure when running as a
    # real package (-m from repo root).
    if __package__ or (isinstance(exc, ModuleNotFoundError) and exc.name != "scripts"):
        raise
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import context_canary
    import task_identity
    import thread_handoff_canary
    from orchestration.task_family import codex_state as task_family_codex_state
    from orchestration.task_family import rollover as task_family_rollover
    from orchestration.task_family import rollover_registry as task_family_rollover_registry
    from orchestration.task_family.storage import advisory_lock as task_family_advisory_lock

SCHEMA_VERSION = 2
DEFAULT_MONITOR_BASE_URL = "http://127.0.0.1:8765"
DEFAULT_AGENT = "orchestrator"
DEFAULT_ROUTER_AGENTS = ("orchestrator", "codex", "claude", "gemini")
AGENT_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
LINEAGE_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
ROLLOVER_ID_RE = re.compile(r"^rollover-[a-z0-9]+(?:-[a-z0-9]+)*$")
DEFAULT_ROUTER_PATH = Path("docs/session-state/current.md")
ORCHESTRATOR_HANDOFF_PATH = Path("docs/session-state/codex-orchestrator-handoff.md")
DEFAULT_STALE_HOURS = 12
ROLLOVER_BUNDLE_SCHEMA = "rollover-bundle.v1"
ROLLOVER_BUNDLE_MANIFEST_NAME = "manifest.json"
ROLLOVER_BUNDLE_MAX_BYTES = 4 * 1024 * 1024
ROLLOVER_BUNDLE_REPO_TOKEN = "{{REPO_ROOT}}"
ROLLOVER_BUNDLE_STATUS_RANK = {
    "superseded": 0,
    "pending_start": 1,
    "resumed": 2,
    "confirmed": 3,
    # The existing state machine calls the confirmed replacement ``started``.
    "started": 3,
}
# Only these manifest fields affect bundle identity.  Host paths, export
# clocks, and server-assigned upload sequence numbers are informational or
# transport metadata and must not turn an identical state into new content.
ROLLOVER_BUNDLE_DIGEST_FIELDS = (
    "agent",
    "stream_id",
    "lineage_id",
    "rollover_id",
    "generation",
    "status",
    "prepared_at",
    "tokenized_members",
)
# Default warning threshold (percentage of window)
DEFAULT_CONTEXT_THRESHOLD = 88.0
THREAD_LEASE_SCHEMA_VERSION = 2
# Executable basenames trusted as durable agent-driver harness processes. The
# ancestor walk in _find_harness_ancestor stops at the nearest one of these; a
# transient hook-launcher subshell is never mistaken for the long-lived owner.
KNOWN_HARNESS_EXECUTABLES = frozenset(
    {"claude", "codex", "agy", "kimi", "cursor", "opencode", "hermes"}
)
MAX_HARNESS_ANCESTOR_HOPS = 10
# Start times are compared at whole-second resolution, not a wider tolerance.
# psutil reports sub-second precision; the `ps -o lstart=` fallback only has
# whole-second precision. Truncating both to integer epoch seconds before
# comparing is exact given that shared precision floor — a wider tolerance
# would silently accept a pid-reused process that started within the same
# multi-second window as a "match". Pid reuse within the same wall-clock
# second is not distinguished from the original process (an accepted,
# documented gap — the real precision boundary, not an arbitrary widening).


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_state_root(repo_root: Path) -> Path:
    """Find the primary checkout that owns shared rollover runtime state.

    Linked worktrees have their own working-tree root but share Git's common
    directory, which lives at ``<primary-checkout>/.git``.  Rollover leases
    must be visible to every worktree in that repository, so default state is
    rooted at the primary checkout rather than the invoking worktree.
    """
    result = run_command(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=repo_root,
        env=git_environment(),
    )
    if result.returncode != 0 or not result.stdout:
        detail = result.stderr or result.stdout or "git did not report a common directory"
        raise ValueError(f"cannot discover canonical Git common directory: {detail}")
    common_dir = Path(result.stdout)
    if not common_dir.is_absolute() or common_dir.name != ".git":
        raise ValueError(f"cannot derive canonical checkout root from Git common directory: {result.stdout!r}")
    return common_dir.parent.resolve()


def resolve_roots(repo_root_arg: Path | None) -> tuple[Path, Path]:
    """Return the active checkout and the root that owns rollover runtime state.

    An explicit ``--repo-root`` deliberately keeps fixtures and isolated
    operator invocations self-contained.  The default requires canonical Git
    discovery and never falls back to a worktree-local ``.agent`` directory.
    """
    if repo_root_arg is not None:
        repo_root = repo_root_arg.resolve()
        return repo_root, repo_root
    repo_root = repo_root_from_file().resolve()
    return repo_root, canonical_state_root(repo_root)


def normalize_agent_name(value: str | None) -> str:
    agent = (value or DEFAULT_AGENT).strip().lower()
    if not AGENT_NAME_RE.fullmatch(agent):
        raise ValueError("agent names must match [a-z][a-z0-9-]* so handoff paths cannot escape the repo")
    return agent


def argparse_agent_name(value: str) -> str:
    try:
        return normalize_agent_name(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def normalize_lineage_id(value: str) -> str:
    lineage_id = value.strip().lower()
    if not LINEAGE_ID_RE.fullmatch(lineage_id):
        raise ValueError("lineage ids must match [a-z][a-z0-9-]{0,63} so runtime paths cannot escape the repo")
    return lineage_id


def normalize_rollover_id(value: str) -> str:
    rollover_id = value.strip().lower()
    if rollover_id != value or not ROLLOVER_ID_RE.fullmatch(rollover_id):
        raise ValueError(
            "rollover ids must match rollover-[a-z0-9]+(-[a-z0-9]+)* so runtime paths cannot escape the repo"
        )
    return rollover_id


def argparse_lineage_id(value: str) -> str:
    try:
        return normalize_lineage_id(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def argparse_rollover_id(value: str) -> str:
    try:
        return normalize_rollover_id(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def lineage_id_for(agent: str, active_thread_id: str) -> str:
    """Derive a stable, path-safe lineage for one active runtime thread."""
    digest = hashlib.sha256(f"{agent}\0{active_thread_id.strip()}".encode()).hexdigest()
    return f"lineage-{digest[:24]}"


def runtime_dir(agent: str, lineage_id: str, generation: int, rollover_id: str) -> Path:
    return Path(".agent/thread-rollovers") / agent / lineage_id / f"generation-{generation:04d}" / rollover_id


def default_state_path(agent: str, lineage_id: str) -> Path:
    return Path(".agent/thread-rollovers") / agent / lineage_id / "lease.json"


def default_thread_lease_path(agent: str) -> Path:
    """Return the single-writer lease for one cold-start handoff slot.

    Rollover packets intentionally permit distinct lineages for the same agent.
    That is correct for replacement-thread history, but it cannot arbitrate two
    independently launched driver sessions.  This flat, per-slot lease does.
    """
    return Path(".agent") / f"{agent}-thread-lease.json"


def default_bootstrap_path(agent: str, lineage_id: str, generation: int, rollover_id: str) -> Path:
    return runtime_dir(agent, lineage_id, generation, rollover_id) / "bootstrap.md"


def default_thread_handoff_path(agent: str, lineage_id: str, generation: int, rollover_id: str) -> Path:
    return runtime_dir(agent, lineage_id, generation, rollover_id) / "handoff.md"


def replacement_packet_paths(agent: str, lineage_id: str, generation: int, rollover_id: str) -> dict[str, str]:
    """Return the complete, immutable set of paths reserved by one rollover."""
    packet_dir = runtime_dir(agent, lineage_id, generation, rollover_id)
    return {
        "runtime_path": packet_dir.as_posix(),
        "bootstrap_prompt_path": (packet_dir / "bootstrap.md").as_posix(),
        "handoff_path": (packet_dir / "handoff.md").as_posix(),
        "semantic_snapshot_path": (packet_dir / "semantic-snapshot.json").as_posix(),
        "strict_probe_path": (packet_dir / "strict-probe.json").as_posix(),
        "strict_questions_path": (packet_dir / "strict-questions.json").as_posix(),
        "strict_answers_path": (packet_dir / "strict-answers.json").as_posix(),
        "strict_verdict_path": (packet_dir / "strict-verdict.json").as_posix(),
        "canary_proof_path": (packet_dir / "canary-pass.json").as_posix(),
        "identity_receipt_path": (packet_dir / "identity-receipt.json").as_posix(),
    }


def semantic_snapshot_template(state: dict[str, Any], *, generated_at: datetime) -> dict[str, Any]:
    """Build the answer-free strict-snapshot scaffold for one reserved packet.

    The source references deliberately satisfy the closed ``context_canary``
    grammar while the empty semantic fields keep an unfilled scaffold from
    being minted as a production probe.
    """
    replacement = state.get("replacement") or {}
    lineage_id = state.get("lineage_id")
    rollover_id = replacement.get("rollover_id")
    handoff_path = replacement.get("handoff_path")
    if not isinstance(lineage_id, str) or not isinstance(rollover_id, str) or not isinstance(handoff_path, str):
        raise ValueError("prepared rollover is missing the reserved snapshot identity or handoff path")
    handoff_ref = f"handoff:{handoff_path}"
    return {
        "generated_at": isoformat_z(generated_at),
        "lineage_id": lineage_id,
        "rollover_id": rollover_id,
        "seed": 0,
        "goals": [
            {"id": f"goal-{index}", "statement": "", "source_ref": f"{handoff_ref}#goal-{index}"}
            for index in range(1, 4)
        ],
        "decision_records": [
            {"id": f"decision-{index}", "decision": "", "source_ref": f"{handoff_ref}#decision-{index}"}
            for index in range(1, 4)
        ],
        "constraint_records": [
            {
                "id": f"constraint-{index}",
                "prohibition": "",
                "source_ref": f"{handoff_ref}#constraint-{index}",
            }
            for index in range(1, 3)
        ],
        "next_actions": [
            {"id": f"action-{index}", "action": "", "source_ref": f"{handoff_ref}#action-{index}"}
            for index in range(1, 3)
        ],
    }


def default_handoff_path(agent: str) -> Path:
    if agent == DEFAULT_AGENT:
        return ORCHESTRATOR_HANDOFF_PATH
    if agent == "codex":
        # Codex UI rollovers read the orchestrator compatibility pointer. There
        # is no separate Codex-specific durable handoff file in this repo.
        return Path("docs/session-state/current.orchestrator.md")
    return Path(f"docs/session-state/current.{agent}.md")


def router_agents(selected_agent: str) -> list[str]:
    agents = list(DEFAULT_ROUTER_AGENTS)
    if selected_agent not in agents:
        agents.append(selected_agent)
    return agents


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (KeyError, OSError, TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def repo_local_path(repo_root: Path, value: Path) -> Path:
    """Resolve an operator-supplied path only when it remains inside this repository."""
    candidate = (repo_root / value).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"path must stay under the repository root: {value}") from exc
    return candidate


def resolve_state_path(
    *,
    repo_root: Path,
    state_root: Path,
    supplied_state_file: Path | None,
    default_path: Path | None,
) -> Path:
    """Resolve an explicit fixture path or a canonical default runtime path."""
    if supplied_state_file is not None:
        return repo_local_path(repo_root, supplied_state_file)
    if default_path is None:
        raise ValueError("--lineage-id is required when --state-file is not supplied")
    return repo_local_path(state_root, default_path)


def run_command(
    args: list[str],
    *,
    cwd: Path,
    timeout_s: int = 10,
    env: Mapping[str, str] | None = None,
) -> CommandResult:
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            env=env,
        )
    except FileNotFoundError as exc:
        return CommandResult(returncode=127, stdout="", stderr=str(exc))
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return CommandResult(
            returncode=124,
            stdout=str(stdout).strip(),
            stderr=(str(stderr).strip() or f"timeout after {timeout_s}s"),
        )
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def git_environment() -> dict[str, str]:
    """Keep inherited hook state from redirecting Git away from ``cwd``."""
    redirecting_variables = {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
        "GIT_WORK_TREE",
    }
    return {key: value for key, value in os.environ.items() if key not in redirecting_variables}


def git_output(repo_root: Path, *args: str, timeout_s: int = 10) -> str:
    result = run_command(["git", *args], cwd=repo_root, timeout_s=timeout_s, env=git_environment())
    if result.returncode != 0:
        return ""
    return result.stdout


def http_get_json(base_url: str, path: str, timeout_s: float = 3.0) -> dict[str, Any]:
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as response:
            body = response.read().decode("utf-8", errors="replace")
    except (OSError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        return {"_error": f"{type(exc).__name__}: {exc}"}
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        return {"_error": f"JSONDecodeError: {exc}"}
    return data if isinstance(data, dict) else {"value": data}


def _bundle_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _bundle_member_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("bundle member path is malformed")
    path = Path(value)
    if not path.parts or path.is_absolute() or ".." in path.parts or path.parts[0] == ROLLOVER_BUNDLE_MANIFEST_NAME:
        raise ValueError(f"bundle member path is unsafe: {value!r}")
    return path.as_posix()


def _bundle_archive(members: Mapping[str, bytes], manifest: Mapping[str, Any]) -> bytes:
    """Build a deterministic gzip tar; deterministic bytes make the receipt verifiable."""
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as archive:
        manifest_info = tarfile.TarInfo(ROLLOVER_BUNDLE_MANIFEST_NAME)
        manifest_bytes = _bundle_json(manifest)
        manifest_info.size = len(manifest_bytes)
        manifest_info.mode = 0o600
        manifest_info.mtime = 0
        manifest_info.uid = 0
        manifest_info.gid = 0
        manifest_info.uname = ""
        manifest_info.gname = ""
        archive.addfile(manifest_info, io.BytesIO(manifest_bytes))
        for name in sorted(members):
            member_name = _bundle_member_path(name)
            payload = members[name]
            info = tarfile.TarInfo(member_name)
            info.size = len(payload)
            info.mode = 0o600
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive.addfile(info, io.BytesIO(payload))
    return gzip.compress(raw.getvalue(), compresslevel=9, mtime=0)


def _bundle_digest(members: Mapping[str, bytes], manifest: Mapping[str, Any]) -> str:
    digest_manifest = {
        field: (
            sorted(manifest[field])
            if field == "tokenized_members" and isinstance(manifest.get(field), list)
            else manifest.get(field)
        )
        for field in ROLLOVER_BUNDLE_DIGEST_FIELDS
    }
    digest_members = [
        {
            "path": name,
            "sha256": hashlib.sha256(members[name]).hexdigest(),
            "bytes": len(members[name]),
        }
        for name in sorted(members)
    ]
    return hashlib.sha256(_bundle_json({"manifest": digest_manifest, "members": digest_members})).hexdigest()


def _bundle_legacy_digest(members: Mapping[str, bytes], manifest: Mapping[str, Any]) -> str:
    """Verify v1 archives emitted before the deterministic identity digest fix."""
    unsigned = dict(manifest)
    unsigned["bundle_sha256"] = ""
    return hashlib.sha256(_bundle_archive(members, unsigned)).hexdigest()


def _bundle_text_member(name: str) -> bool:
    return Path(name).suffix.lower() in {".md", ".txt"}


def _bundle_tokenize(data: bytes, *, repo_root: Path, state_root: Path) -> bytes:
    text = data.decode("utf-8")
    for root in (repo_root.resolve(), state_root.resolve()):
        text = text.replace(str(root), ROLLOVER_BUNDLE_REPO_TOKEN)
    return text.encode("utf-8")


def _bundle_rewrite(data: bytes, *, repo_root: Path) -> bytes:
    return data.replace(ROLLOVER_BUNDLE_REPO_TOKEN.encode("utf-8"), str(repo_root.resolve()).encode("utf-8"))


def _bundle_replacement_status(replacement: Mapping[str, Any]) -> str:
    status = str(replacement.get("status") or "")
    if status not in ROLLOVER_BUNDLE_STATUS_RANK:
        raise ValueError(f"replacement status is not bundle-orderable: {status!r}")
    return status


def _bundle_order(manifest: Mapping[str, Any]) -> tuple[int, int, datetime, str, int]:
    try:
        generation = int(manifest["generation"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("bundle generation is malformed") from exc
    status = _bundle_replacement_status(manifest)
    prepared_at = parse_iso_datetime(str(manifest.get("prepared_at") or ""))
    if prepared_at is None:
        raise ValueError("bundle prepared_at is malformed")
    rollover_id = normalize_rollover_id(str(manifest.get("rollover_id") or ""))
    try:
        upload_seq = int(manifest.get("upload_seq", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("bundle upload_seq is malformed") from exc
    if generation < 1 or upload_seq < 0:
        raise ValueError("bundle generation or upload_seq is out of range")
    return generation, ROLLOVER_BUNDLE_STATUS_RANK[status], prepared_at, rollover_id, upload_seq


def _bundle_state_manifest(state: Mapping[str, Any], *, stream_id: str, upload_seq: int | None = None) -> dict[str, Any]:
    replacement = state.get("replacement")
    if not isinstance(replacement, dict):
        raise ValueError("rollover state has no replacement")
    agent = normalize_agent_name(str(state.get("agent") or ""))
    lineage_id = normalize_lineage_id(str(state.get("lineage_id") or replacement.get("lineage_id") or ""))
    status = _bundle_replacement_status(replacement)
    generation = int(replacement.get("generation"))
    rollover_id = normalize_rollover_id(str(replacement.get("rollover_id") or ""))
    prepared_at = str(replacement.get("prepared_at") or "")
    if parse_iso_datetime(prepared_at) is None:
        raise ValueError("rollover replacement prepared_at is malformed")
    if upload_seq is None:
        upload_seq = int(state.get("bundle_upload_seq", 0))
    return {
        "schema": ROLLOVER_BUNDLE_SCHEMA,
        "agent": agent,
        "stream_id": stream_id,
        "lineage_id": lineage_id,
        "rollover_id": rollover_id,
        "generation": generation,
        "status": status,
        "prepared_at": prepared_at,
        "source_root": ROLLOVER_BUNDLE_REPO_TOKEN,
        "exported_at": isoformat_z(utc_now()),
        "files": [],
        "tokenized_members": [],
        "upload_seq": upload_seq,
        "bundle_sha256": "",
    }


def _bundle_state_candidates(state_root: Path, agent: str) -> list[tuple[Path, dict[str, Any]]]:
    root = state_root / ".agent" / "thread-rollovers" / agent
    candidates: list[tuple[Path, dict[str, Any]]] = []
    if not root.is_dir():
        return candidates
    for path in sorted(root.glob("*/lease.json")):
        state = load_state(path)
        replacement = state.get("replacement")
        if not isinstance(replacement, dict) or replacement.get("status") not in ROLLOVER_BUNDLE_STATUS_RANK:
            continue
        candidates.append((path, state))
    return candidates


def _select_bundle_state(
    state_root: Path,
    *,
    agent: str,
    lineage_id: str | None,
    rollover_id: str | None,
) -> tuple[Path, dict[str, Any]]:
    candidates = _bundle_state_candidates(state_root, agent)
    if lineage_id is not None:
        wanted_lineage = normalize_lineage_id(lineage_id)
        candidates = [item for item in candidates if item[1].get("lineage_id") == wanted_lineage]
    if rollover_id is not None:
        wanted_rollover = normalize_rollover_id(rollover_id)
        candidates = [
            item for item in candidates if (item[1].get("replacement") or {}).get("rollover_id") == wanted_rollover
        ]
    if not candidates:
        raise ValueError("no matching rollover lineage exists")
    if len(candidates) == 1:
        return candidates[0]
    ranked = sorted(
        candidates,
        key=lambda item: _bundle_order(
            _bundle_state_manifest(item[1], stream_id="shared:rollover")
        ),
        reverse=True,
    )
    return ranked[0]


def _bundle_handoff_candidates(repo_root: Path, stream_id: str) -> tuple[str, ...]:
    try:
        from agents_extensions.shared.session_streams.inventory import epic_handoff_map

        return tuple(epic_handoff_map(repo_root).get(stream_id, ()))
    except (OSError, ValueError, ImportError):
        return ()


def _bundle_handoff_candidates_for_agent(repo_root: Path, stream_id: str, agent: str) -> tuple[str, ...]:
    """Resolve the inventory lane first, then the canonical agent-slug template."""
    candidates = list(_bundle_handoff_candidates(repo_root, stream_id))
    if agent.startswith("claude-"):
        candidates.append(f".claude/{agent.removeprefix('claude-')}-epic/CLAUDE-DRIVER-HANDOFF.md")
    return tuple(dict.fromkeys(candidates))


def _bundle_source_members(
    repo_root: Path,
    state_root: Path,
    *,
    agent: str,
    state: Mapping[str, Any],
    stream_id: str,
) -> dict[str, bytes]:
    lineage_id = normalize_lineage_id(str(state.get("lineage_id") or ""))
    lineage_root = state_root / ".agent" / "thread-rollovers" / agent / lineage_id
    if not lineage_root.is_dir():
        raise ValueError(f"rollover lineage directory is missing: {lineage_id}")
    members: dict[str, bytes] = {}
    for path in sorted(lineage_root.rglob("*")):
        if not path.is_file() or path.is_symlink() or path.name == ".native-intent.lock" or path.name.endswith(".bundle.tgz"):
            continue
        member_name = (Path(".agent") / "thread-rollovers" / agent / lineage_id / path.relative_to(lineage_root)).as_posix()
        payload = path.read_bytes()
        if _bundle_text_member(member_name):
            payload = _bundle_tokenize(payload, repo_root=repo_root, state_root=state_root)
        members[_bundle_member_path(member_name)] = payload

    for candidate in _bundle_handoff_candidates_for_agent(repo_root, stream_id, agent):
        path = repo_root / candidate
        if path.is_file() and not path.is_symlink():
            payload = _bundle_tokenize(path.read_bytes(), repo_root=repo_root, state_root=state_root)
            members[_bundle_member_path(candidate)] = payload
            break
    return members


def _bundle_secret_hits(members: Mapping[str, bytes]) -> list[tuple[str, str]]:
    try:
        from agents_extensions.shared.session_streams.store import SECRET_PATTERNS
    except ImportError:
        return []
    hits: list[tuple[str, str]] = []
    for name, payload in members.items():
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError:
            hits.append((name, "invalid-utf8-text"))
            continue
        for rule, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append((name, rule))
    return hits


def _build_rollover_bundle(
    repo_root: Path,
    state_root: Path,
    *,
    agent: str,
    state: Mapping[str, Any],
    stream_id: str,
) -> tuple[dict[str, Any], bytes, list[tuple[str, str]]]:
    stream_id = str(stream_id)
    if not stream_id:
        raise ValueError("--stream is required for a rollover bundle")
    manifest = _bundle_state_manifest(state, stream_id=stream_id)
    members = _bundle_source_members(repo_root, state_root, agent=agent, state=state, stream_id=stream_id)
    files = []
    tokenized_members: list[str] = []
    for name in sorted(members):
        tokenized = _bundle_text_member(name)
        if tokenized:
            tokenized_members.append(name)
        files.append({"path": name, "sha256": hashlib.sha256(members[name]).hexdigest(), "bytes": len(members[name]), "tokenized": tokenized})
    manifest["files"] = files
    manifest["tokenized_members"] = tokenized_members
    manifest["bundle_sha256"] = _bundle_digest(members, manifest)
    archive = _bundle_archive(members, manifest)
    if len(archive) > ROLLOVER_BUNDLE_MAX_BYTES:
        raise ValueError("rollover bundle exceeds the 4 MiB cap")
    return manifest, archive, _bundle_secret_hits(members)


def _bundle_extract(blob: bytes, *, manifest_override: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, bytes]]:
    if len(blob) > ROLLOVER_BUNDLE_MAX_BYTES:
        raise ValueError("rollover bundle exceeds the 4 MiB cap")
    members: dict[str, bytes] = {}
    manifest: dict[str, Any] | None = None
    try:
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as archive:
            for info in archive.getmembers():
                if info.name == ROLLOVER_BUNDLE_MANIFEST_NAME:
                    if manifest is not None or not info.isfile():
                        raise ValueError("bundle manifest is malformed")
                    raw_manifest = archive.extractfile(info)
                    if raw_manifest is None:
                        raise ValueError("bundle manifest is unreadable")
                    value = json.loads(raw_manifest.read().decode("utf-8"))
                    if not isinstance(value, dict):
                        raise ValueError("bundle manifest must be an object")
                    manifest = value
                    continue
                name = _bundle_member_path(info.name)
                if name in members or not info.isfile():
                    raise ValueError("bundle contains a duplicate or non-regular member")
                payload = archive.extractfile(info)
                if payload is None:
                    raise ValueError("bundle member is unreadable")
                members[name] = payload.read()
    except (tarfile.TarError, OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"rollover bundle is not a valid tar.gz: {exc}") from exc
    if manifest is None or manifest.get("schema") != ROLLOVER_BUNDLE_SCHEMA:
        raise ValueError("rollover bundle manifest schema is invalid")
    declared_files = manifest.get("files")
    if not isinstance(declared_files, list) or not declared_files:
        raise ValueError("rollover bundle manifest has no files")
    declared_names: set[str] = set()
    declared_tokenized: set[str] = set()
    for item in declared_files:
        if not isinstance(item, dict):
            raise ValueError("rollover bundle file manifest is malformed")
        name = _bundle_member_path(item.get("path"))
        if name in declared_names or name not in members:
            raise ValueError("rollover bundle file manifest does not match the tar")
        declared_names.add(name)
        payload = members[name]
        tokenized = item.get("tokenized")
        if not isinstance(tokenized, bool) or tokenized != _bundle_text_member(name):
            raise ValueError(f"rollover bundle tokenization declaration is invalid: {name}")
        if tokenized:
            declared_tokenized.add(name)
        if item.get("bytes") != len(payload) or item.get("sha256") != hashlib.sha256(payload).hexdigest():
            raise ValueError(f"rollover bundle member fingerprint mismatch: {name}")
    if declared_names != set(members):
        raise ValueError("rollover bundle tar contains an unmanifested member")
    tokenized_members = manifest.get("tokenized_members")
    if not isinstance(tokenized_members, list) or set(tokenized_members) != declared_tokenized:
        raise ValueError("rollover bundle tokenized_members does not match its file manifest")
    _bundle_order(manifest)
    expected_digest = _bundle_digest(members, manifest)
    if manifest.get("bundle_sha256") != expected_digest and manifest.get("bundle_sha256") != _bundle_legacy_digest(
        members, manifest
    ):
        raise ValueError("rollover bundle fingerprint mismatch")
    if manifest_override is not None:
        outer = dict(manifest_override)
        if outer.get("schema") != ROLLOVER_BUNDLE_SCHEMA or outer.get("bundle_sha256") != manifest.get("bundle_sha256"):
            raise ValueError("API manifest does not match the bundle")
        for key in ("agent", "stream_id", "lineage_id", "rollover_id", "generation", "status", "prepared_at"):
            if outer.get(key) != manifest.get(key):
                raise ValueError(f"API manifest differs from bundle at {key}")
        manifest = {**manifest, "upload_seq": outer.get("upload_seq", manifest.get("upload_seq", 0))}
        _bundle_order(manifest)
    return manifest, members


def _bundle_local_members(repo_root: Path, state_root: Path, *, agent: str, lineage_id: str, stream_id: str) -> dict[str, bytes]:
    state_path = state_root / ".agent" / "thread-rollovers" / agent / lineage_id / "lease.json"
    state = load_state(state_path)
    return _bundle_source_members(repo_root, state_root, agent=agent, state=state, stream_id=stream_id)


def _bundle_write_member(repo_root: Path, state_root: Path, name: str, payload: bytes) -> None:
    target_root = state_root if name.startswith(".agent/thread-rollovers/") else repo_root
    target = (target_root / name).resolve()
    target.relative_to(target_root.resolve())
    if _bundle_text_member(name):
        payload = _bundle_rewrite(payload, repo_root=repo_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_bytes_atomic(target, payload)


def _bundle_archive_local_lineage(
    state_root: Path,
    *,
    agent: str,
    lineage_id: str,
    remote_manifest: Mapping[str, Any],
) -> Path | None:
    lineage_root = state_root / ".agent" / "thread-rollovers" / agent / lineage_id
    if not lineage_root.exists():
        return None
    timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    archive_root = state_root / ".agent" / "thread-rollovers" / agent / "_archive" / f"{lineage_id}-{timestamp}"
    suffix = 1
    while archive_root.exists():
        archive_root = state_root / ".agent" / "thread-rollovers" / agent / "_archive" / f"{lineage_id}-{timestamp}-{suffix}"
        suffix += 1
    archive_root.parent.mkdir(parents=True, exist_ok=True)
    original_lease = (lineage_root / "lease.json").read_bytes()
    try:
        shutil.move(os.fspath(lineage_root), os.fspath(archive_root))
        archived_state_path = archive_root / "lease.json"
        archived_state = load_state(archived_state_path)
        replacement = archived_state.get("replacement")
        if isinstance(replacement, dict) and replacement.get("status") in {"pending_start", "resumed"}:
            replacement["status"] = "superseded"
            replacement["superseded_by"] = {
                "lineage_id": remote_manifest.get("lineage_id"),
                "generation": remote_manifest.get("generation"),
                "rollover_id": remote_manifest.get("rollover_id"),
            }
            archived_state["replacement"] = replacement
            # The identity receipt already describes the same lineage identity;
            # only the archived lease projection changes here.  Keep this final
            # archive update local so a failed import can remove the transaction's
            # archive without leaving a second registry mutation to roll back.
            write_json_atomic(archived_state_path, archived_state)
    except Exception:
        if archive_root.exists():
            with suppress(OSError):
                write_bytes_atomic(archive_root / "lease.json", original_lease)
            with suppress(OSError):
                shutil.move(os.fspath(archive_root), os.fspath(lineage_root))
        raise
    return archive_root


def _bundle_validate_lease_member(
    state_root: Path,
    *,
    agent: str,
    lineage_id: str,
    manifest: Mapping[str, Any],
    members: Mapping[str, bytes],
) -> None:
    """Validate the imported lease before staging or replacing local state."""
    lease_name = f".agent/thread-rollovers/{agent}/{lineage_id}/lease.json"
    payload = members.get(lease_name)
    if payload is None:
        raise ValueError("bundle has no lease state member")
    try:
        state = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("bundle lease state is not valid JSON") from exc
    if not isinstance(state, dict):
        raise ValueError("bundle lease state must be an object")
    replacement, error = validate_live_lease(
        state,
        agent=agent,
        state_path=state_root / ".agent" / "thread-rollovers" / agent / lineage_id / "lease.json",
    )
    if error:
        raise ValueError(f"bundle lease is invalid: {error}")
    assert replacement is not None
    if state.get("lineage_id") != lineage_id or state.get("rollover_id") != manifest.get("rollover_id"):
        raise ValueError("bundle lease identity does not match its manifest")
    try:
        generation = int(manifest["generation"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("bundle manifest generation is malformed") from exc
    if replacement.get("generation") != generation:
        raise ValueError("bundle lease generation does not match its manifest")
    if replacement.get("prepared_at") != manifest.get("prepared_at"):
        raise ValueError("bundle lease prepared_at does not match its manifest")
    lease_status = str(replacement.get("status") or "")
    manifest_status = str(manifest.get("status") or "")
    if lease_status != manifest_status and {lease_status, manifest_status} != {"started", "confirmed"}:
        raise ValueError("bundle lease status does not match its manifest")


def _bundle_stage_install(
    repo_root: Path,
    state_root: Path,
    *,
    manifest: Mapping[str, Any],
    members: Mapping[str, bytes],
) -> tuple[Path, Path, dict[str, Path]]:
    """Stage every imported file beside its target lineage, without clobbering it."""
    agent = normalize_agent_name(str(manifest["agent"]))
    lineage_id = normalize_lineage_id(str(manifest["lineage_id"]))
    lineage_prefix = f".agent/thread-rollovers/{agent}/{lineage_id}/"
    if not any(name.startswith(lineage_prefix) for name in members):
        raise ValueError("bundle has no lineage state members")
    lineage_parent = state_root / ".agent" / "thread-rollovers" / agent
    lineage_parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(tempfile.mkdtemp(prefix=f".{lineage_id}.import-", dir=os.fspath(lineage_parent)))
    staged_lineage = stage_root / "lineage"
    staged_repo: dict[str, Path] = {}
    try:
        for name, payload in members.items():
            if name.startswith(".agent/thread-rollovers/"):
                if not name.startswith(lineage_prefix):
                    raise ValueError("bundle contains a foreign lineage member")
                destination = staged_lineage / name.removeprefix(lineage_prefix)
            else:
                destination = stage_root / "repo" / name
                staged_repo[name] = destination
            destination.relative_to(stage_root.resolve())
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(
                _bundle_rewrite(payload, repo_root=repo_root) if _bundle_text_member(name) else payload
            )
    except Exception:
        shutil.rmtree(stage_root, ignore_errors=True)
        raise
    return stage_root, staged_lineage, staged_repo


def _bundle_preserved_path(target: Path) -> Path:
    timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    preserved = target.with_name(f"{target.stem}.{timestamp}.superseded{target.suffix}")
    suffix = 1
    while preserved.exists():
        preserved = target.with_name(f"{target.stem}.{timestamp}-{suffix}.superseded{target.suffix}")
        suffix += 1
    return preserved


def _bundle_commit_install(
    repo_root: Path,
    state_root: Path,
    *,
    manifest: Mapping[str, Any],
    stage_root: Path,
    staged_lineage: Path,
    staged_repo: Mapping[str, Path],
    local_lineage_exists: bool,
    install_handoff: bool = True,
) -> tuple[Path | None, list[str]]:
    """Commit a staged bundle with exact rollback around archive+rename."""
    agent = normalize_agent_name(str(manifest["agent"]))
    lineage_id = normalize_lineage_id(str(manifest["lineage_id"]))
    lineage_root = state_root / ".agent" / "thread-rollovers" / agent / lineage_id
    receipt_path = state_root / ".agent" / "thread-rollovers" / agent / "_bundle-receipts" / f"{lineage_id}.json"
    original_backup = stage_root / "original-lineage"

    repo_backups: dict[Path, bytes | None] = {}
    created_preserved: list[Path] = []
    preserved: list[str] = []
    old_receipt = receipt_path.read_bytes() if receipt_path.is_file() else None
    archived: Path | None = None
    lineage_replaced = False
    try:
        if local_lineage_exists:
            shutil.copytree(lineage_root, original_backup)
        handoff_candidates = set(_bundle_handoff_candidates_for_agent(repo_root, str(manifest["stream_id"]), agent))
        for name, source in sorted(staged_repo.items()):
            if not install_handoff and name in handoff_candidates:
                continue
            target = (repo_root / name).resolve()
            target.relative_to(repo_root.resolve())
            if target.exists() and not target.is_file():
                raise ValueError(f"bundle target is not a regular file: {name}")
            old_payload = target.read_bytes() if target.is_file() else None
            repo_backups[target] = old_payload
            installed = source.read_bytes()
            if name in handoff_candidates and old_payload is not None and old_payload != installed:
                superseded = _bundle_preserved_path(target)
                write_bytes_atomic(superseded, old_payload)
                created_preserved.append(superseded)
                preserved.append(superseded.as_posix())
            write_bytes_atomic(target, installed)

        write_json_atomic(
            receipt_path,
            {"schema": "rollover-bundle-receipt.v1", "upload_seq": int(manifest.get("upload_seq", 0))},
        )

        # No operation that can select a different copy occurs before all
        # validation and staging above.  Archive and rename are the final
        # lineage transition, and every failure below restores the original.
        if lineage_root.exists():
            archived = _bundle_archive_local_lineage(
                state_root,
                agent=agent,
                lineage_id=lineage_id,
                remote_manifest=manifest,
            )
        os.replace(staged_lineage, lineage_root)
        lineage_replaced = True
        return archived, preserved
    except Exception:
        if lineage_replaced and lineage_root.exists():
            shutil.rmtree(lineage_root, ignore_errors=True)
        if archived is not None and archived.exists():
            shutil.rmtree(archived, ignore_errors=True)
        if local_lineage_exists and original_backup.exists() and not lineage_root.exists():
            shutil.copytree(original_backup, lineage_root)

        for target, old_payload in repo_backups.items():
            try:
                if old_payload is None:
                    target.unlink(missing_ok=True)
                else:
                    write_bytes_atomic(target, old_payload)
            except OSError:
                pass
        for path in created_preserved:
            path.unlink(missing_ok=True)
        try:
            if old_receipt is None:
                receipt_path.unlink(missing_ok=True)
            else:
                write_bytes_atomic(receipt_path, old_receipt)
        except OSError:
            pass
        raise
    finally:
        if stage_root.exists():
            shutil.rmtree(stage_root, ignore_errors=True)


def _bundle_status_manifest(state_root: Path, *, agent: str, lineage_id: str) -> dict[str, Any] | None:
    state_path = state_root / ".agent" / "thread-rollovers" / agent / lineage_id / "lease.json"
    if not state_path.is_file():
        return None
    state = load_state(state_path)
    try:
        receipt_path = state_root / ".agent" / "thread-rollovers" / agent / "_bundle-receipts" / f"{lineage_id}.json"
        receipt = load_state(receipt_path) if receipt_path.is_file() else {}
        return _bundle_state_manifest(
            state,
            stream_id="shared:rollover",
            upload_seq=int(receipt.get("upload_seq", 0)),
        )
    except (TypeError, ValueError):
        return None


class RolloverBundleAPIUnavailable(RuntimeError):
    """The optional remote bundle authority cannot be reached."""


class RolloverBundleNotFound(RuntimeError):
    """The remote bundle authority has no matching bundle."""


def _bundle_monitor_url(base_url: str) -> str:
    value = str(base_url or DEFAULT_MONITOR_BASE_URL).rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1"}:
        raise ValueError("bundle API URL must be an HTTP loopback URL")
    return f"http://127.0.0.1:{parsed.port or 8765}"


def _bundle_lease_payload(stream_id: str) -> dict[str, Any] | None:
    session_id = os.environ.get("SESSION_STREAM_SESSION_ID", "").strip()
    lease_id = os.environ.get("SESSION_STREAM_LEASE_ID", "").strip()
    if not session_id or not lease_id:
        return None
    try:
        generation = int(os.environ.get("SESSION_STREAM_GENERATION", ""))
        fencing_token = int(os.environ.get("SESSION_STREAM_FENCING_TOKEN", ""))
    except ValueError:
        return None
    holder_kind = os.environ.get("SESSION_STREAM_HOLDER_KIND", "process")
    process_id: int | None
    if holder_kind == "app_thread":
        process_id = None
    else:
        try:
            process_id = int(os.environ.get("SESSION_STREAM_PROCESS_ID", str(os.getpid())))
        except ValueError:
            return None
    task_id = os.environ.get("SESSION_STREAM_TASK_ID") or None
    return {
        "stream_id": stream_id,
        "session_id": session_id,
        "lease_id": lease_id,
        "generation": generation,
        "fencing_token": fencing_token,
        "holder": {
            "agent": os.environ.get("SESSION_STREAM_AGENT", ""),
            "harness": os.environ.get("SESSION_STREAM_HARNESS", ""),
            "instance_id": os.environ.get("SESSION_STREAM_INSTANCE_ID", ""),
            "task_id": task_id,
            "process_id": process_id,
            "holder_kind": holder_kind,
            "host_id": os.environ.get("LU_MONITOR_HOST_ID") or None,
        },
    }


def _bundle_api_request(
    base_url: str,
    *,
    method: str,
    path: str,
    payload: Mapping[str, Any] | None = None,
    timeout_s: float = 3.0,
) -> dict[str, Any]:
    body = None if payload is None else _bundle_json(payload)
    request = urllib.request.Request(
        f"{_bundle_monitor_url(base_url)}{path}",
        data=body,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            raw = response.read().decode("utf-8")
            status = int(getattr(response, "status", 200))
    except urllib.error.HTTPError as exc:
        if method == "GET" and exc.code == 404 and (
            path.split("?", 1)[0].endswith("/bundles/latest")
            or "/bundles/" in path.split("?", 1)[0]
        ):
            raise RolloverBundleNotFound("bundle API has no matching bundle") from exc
        raise RolloverBundleAPIUnavailable(f"bundle API unavailable: HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RolloverBundleAPIUnavailable(f"bundle API unavailable: {type(exc).__name__}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RolloverBundleAPIUnavailable("bundle API returned non-JSON data") from exc
    if status >= 400:
        detail = value.get("detail", "request refused") if isinstance(value, dict) else "request refused"
        if status == 404:
            raise RolloverBundleNotFound(f"bundle API has no matching bundle: {detail}")
        raise RuntimeError(f"bundle API refused request ({status}): {detail}")
    if not isinstance(value, dict):
        raise RuntimeError("bundle API returned a non-object JSON document")
    return value


def _bundle_api_upload(args: argparse.Namespace, *, stream_id: str, manifest: Mapping[str, Any], blob: bytes) -> dict[str, Any]:
    """Upload one bundle through :class:`MonitorClient` (#603 Phase 0b adoption).

    Bundles already dedupe by ``bundle_sha256`` server-side (see
    ``SessionStreamStore.upload_rollover_bundle``), so that hash doubles as this
    call's stable idempotency key — it lets the client retry the exact same
    upload across the [A, B] base URL list on an ambiguous transport failure
    without risking a second distinct bundle.
    """
    lease = _bundle_lease_payload(stream_id)
    if lease is None:
        raise RolloverBundleAPIUnavailable("SESSION_STREAM_* fenced lease envelope is unavailable")
    # Deferred: a top-level import of scripts.ai_agent_bridge.monitor_client would run
    # the ai_agent_bridge package __init__, which (via _claude -> _review_worktree ->
    # scripts.review.isolation) imports back from this very module — a circular import.
    try:
        from scripts.ai_agent_bridge.monitor_client import MonitorClient
    except ImportError:
        from ai_agent_bridge.monitor_client import MonitorClient
    manifest_value = dict(manifest)
    bundle_sha256 = manifest_value.get("bundle_sha256")
    client = MonitorClient(base_url=_bundle_monitor_url(args.monitor_base_url), timeout_s=3.0)
    try:
        status, raw, _headers = client._post(
            f"/api/epics/v1/{stream_id}/bundles",
            json_body={
                **lease,
                "manifest": manifest_value,
                "blob": base64.b64encode(blob).decode("ascii"),
            },
            idempotency_key=bundle_sha256 if isinstance(bundle_sha256, str) else None,
        )
    except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as exc:
        raise RolloverBundleAPIUnavailable(f"bundle API unavailable: {type(exc).__name__}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RolloverBundleAPIUnavailable("bundle API returned non-JSON data") from exc
    if status >= 400:
        detail = value.get("detail", "request refused") if isinstance(value, dict) else "request refused"
        raise RolloverBundleAPIUnavailable(f"bundle API unavailable: HTTP {status} ({detail})")
    if not isinstance(value, dict):
        raise RuntimeError("bundle API returned a non-object JSON document")
    return value


def _bundle_api_latest(
    args: argparse.Namespace,
    *,
    stream_id: str,
    agent: str | None = None,
) -> tuple[dict[str, Any], bytes]:
    query = urlencode({"agent": agent}) if agent is not None else ""
    suffix = f"?{query}" if query else ""
    payload = _bundle_api_request(
        args.monitor_base_url,
        method="GET",
        path=f"/api/epics/v1/{stream_id}/bundles/latest{suffix}",
    )
    manifest = payload.get("manifest")
    encoded = payload.get("blob")
    if not isinstance(manifest, dict) or not isinstance(encoded, str):
        raise ValueError("bundle API latest response omitted its manifest or blob")
    try:
        blob = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("bundle API latest blob is not valid base64") from exc
    return manifest, blob


def _bundle_api_list(
    args: argparse.Namespace,
    *,
    stream_id: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """List bundle metadata in upload-sequence order without downloading blobs."""
    if limit < 1 or limit > 100:
        raise ValueError("bundle API list limit must be between 1 and 100")
    payload = _bundle_api_request(
        args.monitor_base_url,
        method="GET",
        path=f"/api/epics/v1/{stream_id}/bundles?{urlencode({'limit': limit})}",
    )
    bundles = payload.get("bundles")
    if not isinstance(bundles, list) or not all(isinstance(bundle, dict) for bundle in bundles):
        raise ValueError("bundle API list response omitted valid bundle metadata")
    return bundles


def _bundle_api_by_seq(
    args: argparse.Namespace,
    *,
    stream_id: str,
    upload_seq: int,
) -> tuple[dict[str, Any], bytes]:
    """Fetch one bundle's manifest and blob by its immutable upload sequence."""
    if upload_seq < 1:
        raise ValueError("bundle API upload sequence must be positive")
    payload = _bundle_api_request(
        args.monitor_base_url,
        method="GET",
        path=f"/api/epics/v1/{stream_id}/bundles/{upload_seq}",
    )
    manifest = payload.get("manifest")
    encoded = payload.get("blob")
    if not isinstance(manifest, dict) or not isinstance(encoded, str):
        raise ValueError("bundle API sequence response omitted its manifest or blob")
    try:
        blob = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("bundle API sequence blob is not valid base64") from exc
    return manifest, blob


def gh_json(repo_root: Path, args: list[str], timeout_s: int = 15) -> Any:
    result = run_command(["gh", *args], cwd=repo_root, timeout_s=timeout_s)
    if result.returncode != 0:
        return {"_error": result.stderr or result.stdout or "gh command failed"}
    try:
        return json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        return {"_error": f"JSONDecodeError: {exc}"}


def parse_git_log(raw: str) -> list[dict[str, str]]:
    commits: list[dict[str, str]] = []
    for line in raw.splitlines():
        parts = line.split("\t", 1)
        if not parts or not parts[0]:
            continue
        commits.append(
            {
                "sha": parts[0],
                "subject": parts[1] if len(parts) > 1 else "",
            }
        )
    return commits


def parse_status(raw: str) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    for line in raw.splitlines():
        if not line:
            continue
        if len(line) > 2 and line[2] == " ":
            status = line[:2].strip() or line[:2]
            path = line[3:]
        elif len(line) > 1 and line[1] == " ":
            # run_command strips the porcelain line's leading worktree-status
            # column when the index is clean (for example `` M file``).
            status = line[0]
            path = line[2:]
        else:
            status = line[:2].strip() or line[:2]
            path = line[3:] if len(line) > 3 else ""
        files.append(
            {
                "status": status,
                "path": path,
            }
        )
    return files


def parse_ahead_behind(raw: str, upstream: str) -> dict[str, Any] | None:
    if not raw:
        return None
    parts = raw.split()
    if len(parts) < 2:
        return {"upstream": upstream, "parse_error": f"unexpected rev-list output: {raw!r}"}
    try:
        behind = int(parts[0])
        ahead = int(parts[1])
    except ValueError:
        return {"upstream": upstream, "parse_error": f"non-integer rev-list output: {raw!r}"}
    return {"ahead": ahead, "behind": behind, "upstream": upstream}


def gather_git_state(repo_root: Path) -> dict[str, Any]:
    branch = git_output(repo_root, "branch", "--show-current") or "DETACHED"
    head = git_output(repo_root, "rev-parse", "--short=10", "HEAD")
    full_head = git_output(repo_root, "rev-parse", "HEAD")
    upstream = git_output(repo_root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    ahead_behind = None
    if upstream:
        counts = git_output(repo_root, "rev-list", "--left-right", "--count", f"{upstream}...HEAD")
        ahead_behind = parse_ahead_behind(counts, upstream)

    return {
        "repo_root": str(repo_root),
        "branch": branch,
        "head": head,
        "full_head": full_head,
        "ahead_behind": ahead_behind,
        "last_commits": parse_git_log(git_output(repo_root, "log", "-5", "--pretty=format:%h%x09%s")),
        "modified_files": parse_status(git_output(repo_root, "status", "--short")),
    }


def source_checkout_binding(git_state: Mapping[str, Any]) -> dict[str, Any]:
    """Bind a rollover to one clean source revision.

    ``git status --short`` includes tracked and untracked files but excludes
    ignored runtime state, which is exactly the continuity boundary required
    for local rollover packets.
    """
    full_head = git_state.get("full_head")
    modified_files = git_state.get("modified_files")
    if not isinstance(full_head, str) or not full_head.strip():
        raise ValueError("source checkout HEAD could not be determined")
    if not isinstance(modified_files, list):
        raise ValueError("source checkout status could not be determined")
    if modified_files:
        paths = ", ".join(
            str(item.get("path") or "unknown") if isinstance(item, dict) else "unknown" for item in modified_files[:5]
        )
        raise ValueError(f"source checkout must be clean before prepare; dirty paths: {paths}")
    return {"full_head": full_head, "clean": True}


def source_checkout_binding_error(replacement: Mapping[str, Any]) -> str | None:
    binding = replacement.get("source_checkout")
    if not isinstance(binding, dict):
        return "live rollover is missing its source checkout binding"
    if set(binding) not in ({"full_head", "clean"}, {"full_head", "clean", "head_advanced_to"}):
        return "live rollover source checkout binding is malformed"
    if binding.get("clean") is not True:
        return "live rollover source checkout binding is not clean"
    full_head = binding.get("full_head")
    if not isinstance(full_head, str) or not full_head.strip():
        return "live rollover source checkout HEAD is malformed"
    if "head_advanced_to" in binding:
        head_advanced = binding.get("head_advanced_to")
        if not isinstance(head_advanced, str) or not head_advanced.strip():
            return "live rollover source checkout HEAD is malformed"
    return None


def checkout_continuity_error(
    replacement: Mapping[str, Any],
    current_git_state: Mapping[str, Any],
    *,
    is_ancestor: Callable[[str, str], bool | None] | None = None,
) -> str | None:
    binding_error = source_checkout_binding_error(replacement)
    if binding_error:
        return binding_error

    current_head = current_git_state.get("full_head")
    if not isinstance(current_head, str) or not current_head.strip():
        return "invoking checkout HEAD could not be determined"

    modified_files = current_git_state.get("modified_files")
    if not isinstance(modified_files, list):
        return "invoking checkout status could not be determined"
    if modified_files:
        paths = ", ".join(
            str(item.get("path") or "unknown") if isinstance(item, dict) else "unknown" for item in modified_files[:5]
        )
        return f"invoking checkout must be clean; dirty paths: {paths}"

    expected_head = replacement["source_checkout"]["full_head"]
    if current_head == expected_head:
        return None

    if is_ancestor is None:
        return f"invoking checkout HEAD {current_head} does not match prepared HEAD {expected_head} (ancestry undeterminable)"

    expected_is_ancestor = is_ancestor(expected_head, current_head)
    if expected_is_ancestor is None:
        return f"invoking checkout HEAD {current_head} does not match prepared HEAD {expected_head} (ancestry undeterminable)"
    elif expected_is_ancestor is True:
        return None

    current_is_ancestor = is_ancestor(current_head, expected_head)
    if current_is_ancestor is True:
        return f"invoking checkout HEAD {current_head} is a rewind (strict ancestor of prepared HEAD {expected_head})"
    elif current_is_ancestor is False:
        return f"invoking checkout HEAD {current_head} has diverged from prepared HEAD {expected_head}"
    else:
        return f"invoking checkout HEAD {current_head} does not match prepared HEAD {expected_head} (ancestry undeterminable)"


def require_checkout_continuity(replacement: Mapping[str, Any], repo_root: Path) -> None:
    def is_ancestor(expected_head: str, current_head: str) -> bool | None:
        res = run_command(
            ["git", "merge-base", "--is-ancestor", expected_head, current_head],
            cwd=repo_root,
            env=git_environment(),
        )
        if res.returncode == 0:
            return True
        elif res.returncode == 1:
            return False
        else:
            return None

    current_git_state = gather_git_state(repo_root)
    error = checkout_continuity_error(replacement, current_git_state, is_ancestor=is_ancestor)
    if error:
        raise ValueError(f"checkout continuity failed: {error}")

    current_head = current_git_state.get("full_head")
    expected_head = replacement["source_checkout"]["full_head"]
    if current_head != expected_head and isinstance(replacement, dict):
        source_checkout = replacement.get("source_checkout")
        if isinstance(source_checkout, dict):
            source_checkout["head_advanced_to"] = current_head


def gather_monitor_state(base_url: str) -> dict[str, Any]:
    return {
        "base_url": base_url.rstrip("/"),
        "orient": http_get_json(base_url, "/api/orient?fresh=true"),
        "active_delegates": http_get_json(base_url, "/api/delegate/active"),
        "completed_delegates": http_get_json(base_url, "/api/delegate/tasks?status=done&limit=5"),
        "worktrees": http_get_json(base_url, "/api/worktrees"),
    }


def gather_github_state(repo_root: Path) -> dict[str, Any]:
    return {
        "open_prs": gh_json(
            repo_root,
            [
                "pr",
                "list",
                "--state",
                "open",
                "--json",
                "number,title,headRefName,mergeStateStatus,statusCheckRollup,url,updatedAt,isDraft,reviewDecision",
                "--limit",
                "20",
            ],
        ),
        "open_issues": gh_json(
            repo_root,
            [
                "issue",
                "list",
                "--state",
                "open",
                "--json",
                "number,title,url,updatedAt,labels",
                "--limit",
                "10",
            ],
        ),
    }


def gather_snapshot(repo_root: Path, base_url: str) -> dict[str, Any]:
    return {
        "generated_at": isoformat_z(utc_now()),
        "git": gather_git_state(repo_root),
        "monitor": gather_monitor_state(base_url),
        "github": gather_github_state(repo_root),
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "state_error": f"unreadable state file: {path}: {type(exc).__name__}: {exc}",
        }
    if not isinstance(data, dict):
        return {"schema_version": SCHEMA_VERSION, "state_error": f"state file is not a JSON object: {path}"}
    schema_version = data.get("schema_version", 1)
    if schema_version not in {1, SCHEMA_VERSION}:
        return {
            "schema_version": SCHEMA_VERSION,
            "state_error": f"unsupported state schema version {schema_version!r}: {path}",
        }
    data["schema_version"] = schema_version
    return data


def state_error_payload(state: dict[str, Any], state_path: Path, repo_root: Path) -> dict[str, Any] | None:
    error = state.get("state_error")
    if not error:
        return None
    return {
        "error": str(error),
        "state_file": rel(state_path, repo_root),
        "hint": "Inspect the file, restore it, or rerun prepare with --force-reset-state to start a new lease.",
    }


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


@dataclass(frozen=True)
class ProcessSnapshot:
    """One process's identity facts, gathered atomically from a single probe.

    ``candidate_basenames`` deliberately holds more than one name: measured on
    a real Claude Code session, ``psutil.Process.name()`` for the ``claude``
    harness process returns its version string (e.g. ``"2.1.220"``), not
    ``claude`` — the CLI overrides its own process title. ``cmdline()[0]`` and
    ``ps -o comm=`` both still resolve to a path basename of ``claude``.
    Matching against every candidate we can cheaply gather is what makes the
    harness-ancestor walk work on the machine it actually has to run on,
    rather than only in a clean test environment.
    """

    pid: int
    ppid: int | None
    candidate_basenames: frozenset[str]
    started_at: float | None


def _epoch_seconds(value: float) -> int:
    """Truncate to whole epoch seconds — the precision both start-time probes share.

    psutil.create_time() returns sub-second precision; the `ps -o lstart=` fallback only
    parses whole seconds. Comparing at whole-second resolution is exact for both instead of
    papering over the gap with an arbitrary tolerance window.
    """
    return int(value)


def _parse_ps_lstart(raw: str) -> float | None:
    """Parse ``ps -o lstart=`` (whole-second, local-time) into epoch seconds."""
    try:
        parsed = datetime.strptime(raw.strip(), "%a %b %d %H:%M:%S %Y")
    except ValueError:
        return None
    return parsed.timestamp()


def _default_process_snapshot(pid: int) -> ProcessSnapshot | None:
    """Probe one live process for ppid, candidate executable names, and start time.

    Prefers psutil (locked in requirements-lock.txt) for one atomic read.
    Falls back to ``ps`` (forced ``LC_ALL=C`` so ``lstart`` parses regardless
    of locale) when psutil is unavailable or cannot see the process.
    """
    try:
        import psutil

        try:
            proc = psutil.Process(pid)
            candidates: set[str] = set()
            name = proc.name()
            if name:
                candidates.add(Path(name).name)
            for accessor in (proc.exe, proc.cmdline):
                try:
                    value = accessor()
                except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
                    continue
                if isinstance(value, list):
                    if value and value[0]:
                        candidates.add(Path(value[0]).name)
                elif value:
                    candidates.add(Path(value).name)
            return ProcessSnapshot(
                pid=pid,
                ppid=proc.ppid(),
                candidate_basenames=frozenset(candidates),
                started_at=proc.create_time(),
            )
        except psutil.NoSuchProcess:
            return None
        except psutil.AccessDenied:
            pass  # fall through to the ps fallback, which may still resolve lstart
    except ImportError:
        pass

    env = git_environment()
    env["LC_ALL"] = "C"
    result = run_command(
        ["ps", "-o", "ppid=,comm=,lstart=", "-p", str(pid)],
        cwd=Path.cwd(),
        env=env,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    fields = result.stdout.strip().split(None, 2)
    if len(fields) < 3:
        return None
    try:
        ppid = int(fields[0])
    except ValueError:
        ppid = None
    candidate_basenames = frozenset({Path(fields[1]).name}) if fields[1] else frozenset()
    started_at = _parse_ps_lstart(fields[2])
    return ProcessSnapshot(pid=pid, ppid=ppid, candidate_basenames=candidate_basenames, started_at=started_at)


def _find_harness_ancestor(
    starting_pid: int,
    *,
    process_snapshot: Callable[[int], ProcessSnapshot | None] | None = None,
    max_hops: int = MAX_HARNESS_ANCESTOR_HOPS,
) -> ProcessSnapshot | None:
    """Walk the parent-pid chain (bounded) for the nearest known-harness ancestor.

    A hook subprocess's immediate parent is often a short-lived launcher
    subshell, never the durable session owner. Recording that transient pid
    as ``owner_pid`` would make a live session look dead the moment the
    subshell exits, and the lease would be stolen out from under it while it
    is still driving. Walking to the nearest recognizable harness process
    (``claude``, ``codex``, ...) finds the actual long-lived owner instead.

    ``process_snapshot`` resolves inside the body (not as a bound default) so
    tests can either inject a fake process table here or monkeypatch
    ``_default_process_snapshot`` and have callers like ``claim_thread_lease``
    (which never pass an override) pick it up too.
    """
    snapshot_fn = process_snapshot or _default_process_snapshot
    pid: int | None = starting_pid
    seen: set[int] = set()
    for _ in range(max_hops):
        if pid is None or pid <= 0 or pid in seen:
            return None
        seen.add(pid)
        snapshot = snapshot_fn(pid)
        if snapshot is None:
            return None
        if snapshot.candidate_basenames & KNOWN_HARNESS_EXECUTABLES:
            return snapshot
        pid = snapshot.ppid
    return None


def _default_machine_id() -> str | None:
    """Return a stable machine identifier — never a network hostname.

    Hostnames change under macOS mDNS renames, VPN reassociation, and
    container rebuilds; keying liveness off one would silently and
    permanently push every lease onto the cross-machine fallback path and
    resurrect the exact lockout this design fixes.
    """
    if sys.platform == "darwin":
        result = run_command(
            ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
            cwd=Path.cwd(),
            env=git_environment(),
        )
        if result.returncode == 0:
            match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', result.stdout)
            if match:
                return match.group(1)
    else:
        machine_id_path = Path("/etc/machine-id")
        try:
            value = machine_id_path.read_text(encoding="utf-8").strip()
        except OSError:
            value = ""
        if value:
            return value
    hostname = socket.gethostname().strip()
    return hostname or None


def _process_is_alive(pid: int) -> bool:
    """POSIX liveness probe. EPERM means the process exists (owned by another user).

    A zombie (defunct) process also answers `kill(pid, 0)` successfully — its pid slot is
    reserved until its parent reaps it — but it can never run again, refresh a heartbeat, or
    release its lease. Treating it as alive would conflict with every future claim forever,
    recreating the original lockout (a dead owner blocking every restart) under a new name.
    A confirmed zombie is dead here, not merely absent.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return not _process_is_zombie(pid)


def _process_is_zombie(pid: int) -> bool:
    """Best-effort zombie probe. Never raises; an inconclusive read means "not confirmed zombie".

    Prefers psutil's structured status. Falls back to `ps -o stat=` (forced `LC_ALL=C`,
    matching `_default_process_snapshot`) when psutil is unavailable — the leading `Z` in the
    state column is portable across macOS and Linux `ps` implementations.
    """
    try:
        import psutil

        try:
            return psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
            return False
    except ImportError:
        pass
    env = git_environment()
    env["LC_ALL"] = "C"
    result = run_command(["ps", "-o", "stat=", "-p", str(pid)], cwd=Path.cwd(), env=env)
    if result.returncode != 0:
        return False
    return result.stdout.strip()[:1] == "Z"


def _derive_owner_liveness_fields(
    starting_pid: int,
    *,
    process_snapshot: Callable[[int], ProcessSnapshot | None] | None = None,
    machine_id: Callable[[], str | None] | None = None,
) -> dict[str, Any]:
    """Derive the v2 identity fields, or {} when liveness cannot be established.

    An empty result is a legitimate, expected outcome (no harness ancestor
    found, or no stable machine id available) — callers write a v2 lease
    without liveness fields, which is the documented uncheckable path.
    """
    machine_id_fn = machine_id or _default_machine_id
    try:
        ancestor = _find_harness_ancestor(starting_pid, process_snapshot=process_snapshot)
    except Exception:
        ancestor = None
    if ancestor is None or ancestor.started_at is None:
        return {}
    try:
        resolved_machine_id = machine_id_fn()
    except Exception:
        resolved_machine_id = None
    if not resolved_machine_id:
        return {}
    return {
        "owner_pid": ancestor.pid,
        "owner_pid_started_at": ancestor.started_at,
        "owner_machine_id": resolved_machine_id,
    }


def _lease_liveness_checkable(
    lease: Mapping[str, Any],
    *,
    machine_id: Callable[[], str | None] | None = None,
) -> bool:
    """A lease's liveness is checkable only with a complete, current-machine v2 identity."""
    if lease.get("schema_version") != THREAD_LEASE_SCHEMA_VERSION:
        return False
    pid = lease.get("owner_pid")
    started_at = lease.get("owner_pid_started_at")
    recorded_machine_id = lease.get("owner_machine_id")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    if not isinstance(started_at, (int, float)) or isinstance(started_at, bool):
        return False
    if not isinstance(recorded_machine_id, str) or not recorded_machine_id.strip():
        return False
    machine_id_fn = machine_id or _default_machine_id
    try:
        current_machine_id = machine_id_fn()
    except Exception:
        return False
    return bool(current_machine_id) and recorded_machine_id == current_machine_id


def _evaluate_owner_liveness(
    lease: Mapping[str, Any],
    *,
    process_is_alive: Callable[[int], bool] | None = None,
    process_snapshot: Callable[[int], ProcessSnapshot | None] | None = None,
    machine_id: Callable[[], str | None] | None = None,
) -> tuple[str, str]:
    """Return (path, reason); path is one of "alive", "dead", "uncheckable".

    Never raises: a probe failure of any kind is an uncheckable verdict, not
    an exception that could block a SessionStart hook.
    """
    if not _lease_liveness_checkable(lease, machine_id=machine_id):
        return "uncheckable", "lease has no complete, current-machine liveness identity"
    pid = int(lease["owner_pid"])
    recorded_started_at = float(lease["owner_pid_started_at"])
    is_alive_fn = process_is_alive or _process_is_alive
    snapshot_fn = process_snapshot or _default_process_snapshot
    try:
        alive = is_alive_fn(pid)
    except Exception as exc:
        return "uncheckable", f"liveness probe raised: {type(exc).__name__}: {exc}"
    if not alive:
        return "dead", "owner process not found or is a zombie (ESRCH, or confirmed defunct)"
    try:
        snapshot = snapshot_fn(pid)
    except Exception as exc:
        return "uncheckable", f"start-time probe raised: {type(exc).__name__}: {exc}"
    if snapshot is None or snapshot.started_at is None:
        return "uncheckable", "owner process is alive but its start time could not be determined"
    if _epoch_seconds(snapshot.started_at) != _epoch_seconds(recorded_started_at):
        return "dead", "owner pid was reused by an unrelated process (start time mismatch)"
    return "alive", "owner process is alive and its start time matches"


def _read_lease_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Read a lease file without ever raising. Returns (payload, corrupt_error).

    ``(None, None)`` means no file exists. ``(None, "<error>")`` means the file
    exists but is unreadable or not a JSON object — unlike the old raising
    loader, this is recoverable: the caller heals by acquiring a fresh lease
    rather than wedging SessionStart shut with no release path.
    """
    if not path.exists():
        return None, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if not isinstance(payload, dict):
        return None, "thread lease is not a JSON object"
    return payload, None


def _new_thread_lease_record(
    *,
    agent: str,
    generation: int,
    owner_thread_id: str,
    acquired_at: str,
    now: datetime,
    starting_pid: int,
    previous_owner_thread_id: str | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema_version": THREAD_LEASE_SCHEMA_VERSION,
        "agent": agent,
        "state": "held",
        "generation": generation,
        "owner_thread_id": owner_thread_id,
        "acquired_at": acquired_at,
        "heartbeat_at": isoformat_z(now),
        **_derive_owner_liveness_fields(starting_pid),
    }
    if previous_owner_thread_id is not None:
        record["replaced_owner_thread_id"] = previous_owner_thread_id
    return record


def _fresh_acquire_result(
    lease_path: Path,
    *,
    agent: str,
    owner_thread_id: str,
    now: datetime,
    starting_pid: int,
    recovered_from_corrupt_lease: str | None = None,
) -> dict[str, Any]:
    """Write and report a brand-new generation-1 lease (no prior owner to reconcile)."""
    record = _new_thread_lease_record(
        agent=agent,
        generation=1,
        owner_thread_id=owner_thread_id,
        acquired_at=isoformat_z(now),
        now=now,
        starting_pid=starting_pid,
        previous_owner_thread_id=None,
    )
    write_json_atomic(lease_path, record)
    result = {
        "status": "acquired",
        "lease_path": lease_path,
        "owner_thread_id": owner_thread_id,
        "generation": 1,
        "heartbeat_at": record["heartbeat_at"],
        "replaced_owner_thread_id": None,
        "liveness_fields_recorded": "owner_pid" in record,
    }
    if recovered_from_corrupt_lease is not None:
        result["recovered_from_corrupt_lease"] = recovered_from_corrupt_lease
    return result


def _same_owner_refresh_result(
    lease_path: Path,
    existing_raw: Mapping[str, Any],
    *,
    agent: str,
    owner_thread_id: str,
    now: datetime,
    starting_pid: int,
) -> dict[str, Any]:
    """Rewrite the lease this exact owner already holds, re-deriving liveness identity.

    Rule E: this always re-derives the full v2 identity fields, so a legacy
    v1 lease refreshed by its own owner is upgraded to v2 rather than staying
    permanently stuck on the uncheckable fallback path.
    """
    raw_generation = existing_raw.get("generation")
    generation = raw_generation if isinstance(raw_generation, int) and raw_generation >= 1 else 1
    acquired_at = existing_raw.get("acquired_at")
    if not isinstance(acquired_at, str) or parse_iso_datetime(acquired_at) is None:
        acquired_at = isoformat_z(now)
    record = _new_thread_lease_record(
        agent=agent,
        generation=generation,
        owner_thread_id=owner_thread_id,
        acquired_at=acquired_at,
        now=now,
        starting_pid=starting_pid,
        previous_owner_thread_id=None,
    )
    write_json_atomic(lease_path, record)
    return {
        "status": "refreshed",
        "lease_path": lease_path,
        "owner_thread_id": owner_thread_id,
        "generation": generation,
        "heartbeat_at": record["heartbeat_at"],
        "liveness_fields_recorded": "owner_pid" in record,
    }


def _same_owner_identity_confirmed(
    existing_raw: Mapping[str, Any], starting_pid: int, *, require_proof: bool = False
) -> bool:
    """True only when a resumed thread id is provably driven by the SAME process as before.

    A same-owner refresh must never blindly preserve generation across a process change: a
    resumed thread id (e.g. `claude --resume`) can be driven by a brand-new harness process
    with a different pid, and if its lease kept the old generation, a delayed SessionEnd
    release from the dead predecessor process — which cached that same old generation from
    its own SessionStart — would still pass release_thread_lease's fencing and delete the
    *successor's* live lease. When the recorded identity is checkable but a fresh probe
    cannot confirm it still matches, this returns False so the caller reacquires with a new
    generation instead of assuming continuity across an unproven process boundary.

    ``require_proof`` controls what happens when the recorded lease has NO checkable identity
    at all (legacy v1, or a v2 lease that could never derive one) — there is nothing to
    contradict continuity with, but also nothing to prove it either:

    - Default (``False``), used by ``claim_thread_lease``'s explicit same-owner resume: this
      returns True **only for a legacy v1 lease**, so the v1->v2 upgrade-on-refresh behavior
      (rule E) still heals a legacy lease the first time its own owner resumes it.
    - ``True``, used by ``refresh_thread_lease_heartbeat``: this returns False. A heartbeat
      call is implicit and frequent, not an explicit resume — it must never assume unproven
      process continuity just to keep writing a lease it cannot actually verify it still owns.
      A no-op there is safe: nothing takes a lease over on heartbeat age anymore, so a stale
      heartbeat on an uncheckable lease costs nothing.

    A **v2** lease whose identity is merely unusable (incomplete liveness fields, or another
    machine's) is NOT eligible for that upgrade concession, even on the explicit-resume path.
    Its predecessor ran under this schema and therefore may already have exported this exact
    generation at its own SessionStart, so preserving the generation would let a delayed
    ``SessionEnd`` from that dead process pass ``release_thread_lease``'s fencing and delete
    the *successor's* live lease — the precise double-driving the generation fence exists to
    stop, leaking in exactly the case where the lease is least verifiable. Only v1 predates
    the generation export and so provably cannot hold a generation to release with.
    """
    if not _lease_liveness_checkable(existing_raw):
        if existing_raw.get("schema_version") != THREAD_LEASE_SCHEMA_VERSION:
            return not require_proof
        return False
    new_fields = _derive_owner_liveness_fields(starting_pid)
    if not new_fields:
        return False
    if new_fields["owner_pid"] != existing_raw.get("owner_pid"):
        return False
    return _epoch_seconds(new_fields["owner_pid_started_at"]) == _epoch_seconds(existing_raw.get("owner_pid_started_at"))


def _identity_changed_reacquire_result(
    lease_path: Path,
    existing_raw: Mapping[str, Any],
    *,
    agent: str,
    owner_thread_id: str,
    now: datetime,
    starting_pid: int,
) -> dict[str, Any]:
    """Reacquire with an incremented generation when the resuming process's identity changed.

    See `_same_owner_identity_confirmed`: this is what actually fences a delayed release from
    the dead predecessor process out — its cached generation no longer matches this lease.
    """
    raw_generation = existing_raw.get("generation")
    generation = raw_generation if isinstance(raw_generation, int) and raw_generation >= 1 else 1
    new_generation = generation + 1
    record = _new_thread_lease_record(
        agent=agent,
        generation=new_generation,
        owner_thread_id=owner_thread_id,
        acquired_at=isoformat_z(now),
        now=now,
        starting_pid=starting_pid,
        previous_owner_thread_id=owner_thread_id,
    )
    write_json_atomic(lease_path, record)
    return {
        "status": "acquired",
        "lease_path": lease_path,
        "owner_thread_id": owner_thread_id,
        "generation": new_generation,
        "heartbeat_at": record["heartbeat_at"],
        "replaced_owner_thread_id": owner_thread_id,
        "liveness_fields_recorded": "owner_pid" in record,
        "takeover_reason": "same thread id resumed under a different process identity (pid/start time changed)",
    }


IDLE_SUSPECTED_THRESHOLD_SECONDS = 45 * 60


def _humanize_duration(seconds: float) -> str:
    """Render a duration for a human operator reading a conflict/diagnosis payload."""
    total = max(0, int(seconds))
    if total < 60:
        return f"{total}s"
    minutes, secs = divmod(total, 60)
    if minutes < 60:
        return f"{minutes}m{secs:02d}s" if secs else f"{minutes}m"
    hours, mins = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h{mins:02d}m" if mins else f"{hours}h"
    days, hrs = divmod(hours, 24)
    return f"{days}d{hrs:02d}h" if hrs else f"{days}d"


def _cas_force_release_command(
    agent: str, *, owner_thread_id: str | None, generation: int | None, include_ack: bool = False
) -> str:
    """The exact CAS-scoped force-release command an operator should run.

    Never a bare ``--force``: it always pins the current owner/generation the
    caller observed, so a stale copy-pasted command refuses instead of
    silently deleting whatever lease happens to exist by the time it runs.
    """
    parts = [
        ".venv/bin/python scripts/orchestration/thread_handoff.py release-thread-lease",
        f"--agent {shlex.quote(agent)}",
        "--force",
        f"--expect-owner-thread-id {shlex.quote(owner_thread_id or '')}",
        f"--expect-generation {generation if isinstance(generation, int) else 0}",
    ]
    if include_ack:
        parts.append("--acknowledge-live-owner")
    return " ".join(parts)


def _lease_conflict_diagnostics(
    *,
    agent: str,
    existing_raw: Mapping[str, Any],
    owner_thread_id: str | None,
    generation: int,
    heartbeat_at: datetime | None,
    now: datetime,
    liveness_path: str,
) -> dict[str, Any]:
    """Everything an operator needs to decide, without opening the lease file by hand."""
    owner_pid = existing_raw.get("owner_pid")
    owner_pid_started_at = existing_raw.get("owner_pid_started_at")
    owner_alive = True if liveness_path == "alive" else None
    heartbeat_age_seconds = (now - heartbeat_at).total_seconds() if heartbeat_at is not None else None
    return {
        "owner_pid": owner_pid if isinstance(owner_pid, int) else None,
        "owner_pid_started_at": (owner_pid_started_at if isinstance(owner_pid_started_at, (int, float)) else None),
        "owner_alive": owner_alive,
        "heartbeat_age_seconds": heartbeat_age_seconds,
        "heartbeat_age_humanized": (
            _humanize_duration(heartbeat_age_seconds) if heartbeat_age_seconds is not None else None
        ),
        "idle_suspected": bool(
            heartbeat_age_seconds is not None and heartbeat_age_seconds > IDLE_SUSPECTED_THRESHOLD_SECONDS
        ),
        "resolution": _cas_force_release_command(
            agent,
            owner_thread_id=owner_thread_id,
            generation=generation,
            include_ack=liveness_path == "alive",
        ),
    }


def _released_tombstone_record(
    existing_raw: Mapping[str, Any], *, released_by_thread_id: str, now: datetime, forced: bool = False
) -> dict[str, Any]:
    """A released lease is a tombstone, never a deleted file.

    Keeping the record (generation, prior owner/identity fields) lets a stale
    duplicate release call recognize "already released" and no-op, and lets
    the next claim continue the SAME monotonic generation counter instead of
    resetting to 1 — see ``claim_thread_lease``'s tombstone-reclaim branch.
    """
    record = dict(existing_raw)
    record["state"] = "released"
    record["released_at"] = isoformat_z(now)
    record["released_by_thread_id"] = released_by_thread_id
    if forced:
        record["released_forced"] = True
    return record


def claim_thread_lease(
    *,
    state_root: Path,
    agent: str,
    current_thread_id: str,
    now: datetime,
    starting_pid: int | None = None,
) -> dict[str, Any]:
    """Atomically claim or refresh a driver-session lease for ``agent``.

    Liveness is checked, not inferred from a clock: a different owner is a
    conflict while its process is confirmed alive, AND while its liveness
    cannot be checked at all (legacy v1 lease, cross-machine lease,
    unreadable process state). The clock never grants ownership to anyone —
    there is no emergency TTL that takes an uncheckable owner over on age.
    Silently stealing from a possibly-live owner would corrupt the very
    mutual exclusion this lease exists to provide; an uncheckable conflict
    instead surfaces the exact operator command (``release-thread-lease
    --force``) to unlock it. A confirmed-dead or pid-reused owner is
    reclaimed immediately regardless of clock age; an unreadable or
    malformed on-disk lease is treated as recoverable state, never as a
    reason to raise and block SessionStart.
    """
    owner_thread_id = current_thread_id.strip()
    if not owner_thread_id:
        raise ValueError("current thread id is required to claim a durable thread lease")

    resolved_starting_pid = starting_pid if starting_pid is not None else os.getpid()
    lease_path = repo_local_path(state_root, default_thread_lease_path(agent))
    lock_path = lease_path.with_suffix(lease_path.suffix + ".lock")

    with task_family_advisory_lock(lock_path):
        existing_raw, corrupt_error = _read_lease_json(lease_path)

        if corrupt_error is not None:
            return _fresh_acquire_result(
                lease_path,
                agent=agent,
                owner_thread_id=owner_thread_id,
                now=now,
                starting_pid=resolved_starting_pid,
                recovered_from_corrupt_lease=corrupt_error,
            )

        if existing_raw is None:
            return _fresh_acquire_result(
                lease_path,
                agent=agent,
                owner_thread_id=owner_thread_id,
                now=now,
                starting_pid=resolved_starting_pid,
            )

        if existing_raw.get("state") == "released":
            # A tombstone is held by nobody — reclaim unconditionally, but the
            # generation counter is monotonic and must never reset to 1 while
            # a tombstone exists (it is durable evidence of the last holder).
            raw_generation = existing_raw.get("generation")
            generation = raw_generation if isinstance(raw_generation, int) and raw_generation >= 1 else 0
            previous_owner = existing_raw.get("owner_thread_id")
            previous_owner = previous_owner if isinstance(previous_owner, str) and previous_owner.strip() else None
            new_generation = generation + 1
            record = _new_thread_lease_record(
                agent=agent,
                generation=new_generation,
                owner_thread_id=owner_thread_id,
                acquired_at=isoformat_z(now),
                now=now,
                starting_pid=resolved_starting_pid,
                previous_owner_thread_id=previous_owner,
            )
            write_json_atomic(lease_path, record)
            return {
                "status": "acquired",
                "lease_path": lease_path,
                "owner_thread_id": owner_thread_id,
                "generation": new_generation,
                "heartbeat_at": record["heartbeat_at"],
                "replaced_owner_thread_id": previous_owner,
                "liveness_fields_recorded": "owner_pid" in record,
                "takeover_reason": "lease was cooperatively released; claiming at the next monotonic generation",
            }

        held_by = existing_raw.get("owner_thread_id")
        held_by_valid = isinstance(held_by, str) and bool(held_by.strip())

        if held_by_valid and held_by == owner_thread_id:
            if _same_owner_identity_confirmed(existing_raw, resolved_starting_pid):
                return _same_owner_refresh_result(
                    lease_path,
                    existing_raw,
                    agent=agent,
                    owner_thread_id=owner_thread_id,
                    now=now,
                    starting_pid=resolved_starting_pid,
                )
            return _identity_changed_reacquire_result(
                lease_path,
                existing_raw,
                agent=agent,
                owner_thread_id=owner_thread_id,
                now=now,
                starting_pid=resolved_starting_pid,
            )

        raw_generation = existing_raw.get("generation")
        generation = raw_generation if isinstance(raw_generation, int) and raw_generation >= 1 else 0
        heartbeat_at = parse_iso_datetime(existing_raw.get("heartbeat_at"))
        previous_owner = held_by if held_by_valid else None
        liveness_path, liveness_reason = _evaluate_owner_liveness(existing_raw)

        if liveness_path == "alive":
            return {
                "status": "conflict",
                "lease_path": lease_path,
                "owner_thread_id": previous_owner,
                "generation": generation,
                "heartbeat_at": isoformat_z(heartbeat_at) if heartbeat_at else None,
                "liveness": "live_owner",
                "reason": liveness_reason,
                **_lease_conflict_diagnostics(
                    agent=agent,
                    existing_raw=existing_raw,
                    owner_thread_id=previous_owner,
                    generation=generation,
                    heartbeat_at=heartbeat_at,
                    now=now,
                    liveness_path=liveness_path,
                ),
            }

        if liveness_path == "uncheckable":
            # Never take over on clock age: an uncheckable owner might be alive.
            # heartbeat_at is diagnostic only here; it grants nobody ownership.
            return {
                "status": "conflict",
                "lease_path": lease_path,
                "owner_thread_id": previous_owner,
                "generation": generation,
                "heartbeat_at": isoformat_z(heartbeat_at) if heartbeat_at else None,
                "liveness": "liveness_unknown",
                "reason": liveness_reason,
                **_lease_conflict_diagnostics(
                    agent=agent,
                    existing_raw=existing_raw,
                    owner_thread_id=previous_owner,
                    generation=generation,
                    heartbeat_at=heartbeat_at,
                    now=now,
                    liveness_path=liveness_path,
                ),
            }

        # Only "dead" reaches here: a confirmed-dead or pid-reused owner is
        # reclaimed immediately, regardless of clock age.
        new_generation = generation + 1
        record = _new_thread_lease_record(
            agent=agent,
            generation=new_generation,
            owner_thread_id=owner_thread_id,
            acquired_at=isoformat_z(now),
            now=now,
            starting_pid=resolved_starting_pid,
            previous_owner_thread_id=previous_owner,
        )
        write_json_atomic(lease_path, record)
        return {
            "status": "acquired",
            "lease_path": lease_path,
            "owner_thread_id": owner_thread_id,
            "generation": new_generation,
            "heartbeat_at": record["heartbeat_at"],
            "replaced_owner_thread_id": previous_owner,
            "liveness_fields_recorded": "owner_pid" in record,
            "takeover_reason": liveness_reason,
        }


def release_thread_lease(
    *,
    state_root: Path,
    agent: str,
    current_thread_id: str,
    now: datetime,
    generation: int | None = None,
    starting_pid: int | None = None,
    force: bool = False,
    expect_owner_thread_id: str | None = None,
    expect_generation: int | None = None,
    acknowledge_live_owner: bool = False,
) -> dict[str, Any]:
    """Release a durable thread lease this exact owner (proven by identity or generation) holds.

    Best-effort by design: SessionEnd does not fire on SIGKILL, so the pid
    liveness check in ``claim_thread_lease`` remains the primary defense —
    this is only the fast, cooperative path. Never rewrites or upgrades a
    lease it does not own.

    A release never deletes the file — it rewrites it as a ``released``
    tombstone (see ``_released_tombstone_record``), preserving generation so
    the next claim continues the SAME monotonic counter rather than
    resetting to 1. A release against an already-released tombstone is
    always a no-op: there is nothing left to release.

    Identity is the primary fence, not generation: ``_same_owner_identity_confirmed``
    with ``require_proof=True`` re-derives the caller's harness-ancestor
    pid/start time rather than trusting a value it merely remembers, so it is
    strictly stronger than a caller-supplied generation. When the calling
    process's identity is confirmed, ``generation`` is OPTIONAL. When it is
    NOT confirmed (uncheckable lease, or a mismatched probe — e.g. a resumed
    thread id now driven by a different process, per
    ``_same_owner_identity_confirmed``'s docstring), the caller must supply
    the exact generation it holds, or this fails closed with a no-op —
    NEVER by reading the generation back off the lease file itself, which
    would make the check a tautology.

    ``force`` is the CAS-scoped operator escape hatch: it requires
    ``expect_owner_thread_id`` and ``expect_generation`` to match the current
    lease exactly (a bare ``--force`` with neither supplied is refused, never
    an unscoped delete), and additionally ``acknowledge_live_owner`` when the
    recorded owner process is verifiably alive.
    """
    owner_thread_id = current_thread_id.strip()
    if not force and not owner_thread_id:
        raise ValueError("current thread id is required to release a durable thread lease")

    resolved_starting_pid = starting_pid if starting_pid is not None else os.getpid()
    lease_path = repo_local_path(state_root, default_thread_lease_path(agent))
    lock_path = lease_path.with_suffix(lease_path.suffix + ".lock")

    with task_family_advisory_lock(lock_path):
        existing_raw, corrupt_error = _read_lease_json(lease_path)
        if existing_raw is None:
            return {
                "status": "noop",
                "lease_path": lease_path,
                "reason": "no lease file present" if corrupt_error is None else f"lease unreadable: {corrupt_error}",
            }

        held_by = existing_raw.get("owner_thread_id")
        held_generation = existing_raw.get("generation")

        if existing_raw.get("state") == "released":
            return {
                "status": "noop",
                "lease_path": lease_path,
                "reason": "lease is already released; nothing to release",
                "current_owner_thread_id": held_by,
                "current_generation": held_generation,
            }

        if force:
            if not expect_owner_thread_id or expect_generation is None:
                return {
                    "status": "refused",
                    "lease_path": lease_path,
                    "error_code": "THREAD_LEASE_FORCE_UNSCOPED",
                    "reason": (
                        "bare --force is refused; force release must be CAS-scoped to the exact "
                        "current owner and generation"
                    ),
                    "current_owner_thread_id": held_by,
                    "current_generation": held_generation,
                    "resolution": _cas_force_release_command(
                        agent,
                        owner_thread_id=held_by,
                        generation=held_generation,
                        include_ack=_evaluate_owner_liveness(existing_raw)[0] == "alive",
                    ),
                }
            if held_by != expect_owner_thread_id or held_generation != expect_generation:
                return {
                    "status": "refused",
                    "lease_path": lease_path,
                    "error_code": "THREAD_LEASE_FORCE_MISMATCH",
                    "reason": (
                        "force release refused: --expect-owner-thread-id/--expect-generation do not "
                        "match the current lease"
                    ),
                    "current_owner_thread_id": held_by,
                    "current_generation": held_generation,
                }
            liveness_path, _liveness_reason = _evaluate_owner_liveness(existing_raw)
            if liveness_path == "alive" and not acknowledge_live_owner:
                return {
                    "status": "refused",
                    "lease_path": lease_path,
                    "error_code": "THREAD_LEASE_FORCE_LIVE_OWNER",
                    "reason": (
                        "force release refused: the recorded owner process is verifiably alive; "
                        "pass --acknowledge-live-owner to override"
                    ),
                    "current_owner_thread_id": held_by,
                    "current_generation": held_generation,
                }
            record = _released_tombstone_record(
                existing_raw, released_by_thread_id=owner_thread_id or held_by or "", now=now, forced=True
            )
            write_json_atomic(lease_path, record)
            return {
                "status": "released",
                "lease_path": lease_path,
                "forced": True,
                "previous_owner_thread_id": held_by,
                "generation": held_generation,
            }

        if held_by != owner_thread_id:
            return {
                "status": "noop",
                "lease_path": lease_path,
                "reason": "lease is owned by a different thread id; not releasing",
                "current_owner_thread_id": held_by,
                "current_generation": held_generation,
            }

        identity_proven = _same_owner_identity_confirmed(existing_raw, resolved_starting_pid, require_proof=True)
        if not identity_proven:
            if generation is None:
                return {
                    "status": "noop",
                    "lease_path": lease_path,
                    "reason": (
                        "process identity could not be reconfirmed and no generation was supplied to "
                        "fence with; refusing to release"
                    ),
                    "current_owner_thread_id": held_by,
                    "current_generation": held_generation,
                }
            if held_generation != generation:
                return {
                    "status": "noop",
                    "lease_path": lease_path,
                    "reason": "lease generation does not match; a takeover superseded this owner",
                    "current_owner_thread_id": held_by,
                    "current_generation": held_generation,
                }

        record = _released_tombstone_record(existing_raw, released_by_thread_id=owner_thread_id, now=now)
        write_json_atomic(lease_path, record)
        return {
            "status": "released",
            "lease_path": lease_path,
            "forced": False,
            "owner_thread_id": owner_thread_id,
            "generation": held_generation,
        }


def refresh_thread_lease_heartbeat(
    *,
    state_root: Path,
    agent: str,
    current_thread_id: str,
    generation: int | None = None,
    now: datetime,
    starting_pid: int | None = None,
    min_refresh_interval: timedelta | None = None,
) -> dict[str, Any]:
    """Best-effort heartbeat refresh. A no-op unless we already own the lease.

    This never attempts a takeover — unlike ``claim_thread_lease``, a
    different owner, a stale generation, or an unconfirmed process identity
    is simply left alone. Fenced by ``owner_thread_id`` and, when supplied,
    ``generation``: thread id alone is not enough, because a takeover that
    resumes the SAME thread id under a NEW process (see
    ``_same_owner_identity_confirmed``) bumps generation but keeps the old
    thread id — a late heartbeat call still in flight from the dead
    predecessor process would otherwise pass a thread-id-only check and
    overwrite the successor's recorded process identity with its own stale
    one.

    ``generation`` is now OPTIONAL: the recorded process identity being
    reconfirmed against the calling process (``require_proof=True``) is
    strictly stronger — it re-derives the caller's harness-ancestor pid/start
    time rather than trusting a value the caller merely remembers, so it is
    the sole fence when no generation is supplied. An uncheckable identity is
    never assumed to be continuous here, unlike the explicit same-owner
    resume path in ``claim_thread_lease`` — any mismatch, or any identity
    that cannot be reconfirmed, is a no-op, never a rewrite. When a
    generation IS supplied, it is still enforced as an extra fence (belt and
    braces) on top of the identity check, never read back off the lease file
    itself as a substitute for one.

    This is diagnostic, not a safety mechanism: there is no emergency TTL
    left for a fresh heartbeat to protect against (see ``claim_thread_lease``
    — an uncheckable owner is never taken over on clock age at all now), so
    a no-op here just leaves ``heartbeat_at`` looking a little stale, which
    costs nothing.

    ``min_refresh_interval``, when given, throttles the write: the hot path
    (called from ``PostToolUse``, on every tool call) is a cheap read that
    no-ops — status ``"throttled"`` — unless the existing heartbeat is
    already older than the interval. The ``Stop`` hook fires far less often
    and omits this, refreshing unconditionally every call.
    """
    owner_thread_id = current_thread_id.strip()
    if not owner_thread_id:
        return {"status": "noop", "reason": "no current thread id supplied"}

    resolved_starting_pid = starting_pid if starting_pid is not None else os.getpid()
    lease_path = repo_local_path(state_root, default_thread_lease_path(agent))
    lock_path = lease_path.with_suffix(lease_path.suffix + ".lock")

    with task_family_advisory_lock(lock_path):
        existing_raw, corrupt_error = _read_lease_json(lease_path)
        if existing_raw is None:
            return {
                "status": "noop",
                "lease_path": lease_path,
                "reason": "no lease file present" if corrupt_error is None else f"lease unreadable: {corrupt_error}",
            }
        held_by = existing_raw.get("owner_thread_id")
        if held_by != owner_thread_id:
            return {
                "status": "noop",
                "lease_path": lease_path,
                "reason": "lease is owned by a different thread id; not refreshing",
            }
        held_generation = existing_raw.get("generation")
        if generation is not None and held_generation != generation:
            return {
                "status": "noop",
                "lease_path": lease_path,
                "reason": "lease generation does not match; a takeover superseded this owner",
                "current_generation": held_generation,
            }
        if min_refresh_interval is not None:
            heartbeat_at = parse_iso_datetime(existing_raw.get("heartbeat_at"))
            if heartbeat_at is not None and (now - heartbeat_at) < min_refresh_interval:
                return {
                    "status": "throttled",
                    "lease_path": lease_path,
                    "heartbeat_at": isoformat_z(heartbeat_at),
                }
        if not _same_owner_identity_confirmed(existing_raw, resolved_starting_pid, require_proof=True):
            return {
                "status": "noop",
                "lease_path": lease_path,
                "reason": "recorded process identity could not be reconfirmed; not refreshing",
            }
        return _same_owner_refresh_result(
            lease_path,
            existing_raw,
            agent=agent,
            owner_thread_id=owner_thread_id,
            now=now,
            starting_pid=resolved_starting_pid,
        )


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_bytes_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_bytes(payload)
    os.replace(tmp, path)


def _retire_unsatisfiable_native_plan(state: dict[str, Any], *, now: datetime) -> bool:
    """Retire a pristine legacy native plan that a non-native harness can never execute.

    Leases prepared before the identity envelope carried an unconditional
    ``native_lifecycle`` block. Deterministic legacy migration assigns the
    ``<harness>-legacy`` slug, which is never native-capable, so a pristine
    ``awaiting_native_create`` block is unsatisfiable: only ``register-created``
    can bind it, and that path requires a native adapter the transition denies.
    Converge the lease to the honest non-native fallback shape (what current
    ``prepare`` emits for such a harness) and keep the retired block as durable
    evidence. Touched plans (bound, failed, or supersession-pending) and
    native-capable transitions are never retired here.
    """
    replacement = state.get("replacement")
    if not isinstance(replacement, dict):
        return False
    native = replacement.get("native_lifecycle")
    if not isinstance(native, dict):
        return False
    transition = replacement.get("title_transition")
    if not isinstance(transition, dict) or transition.get("native_title_supported") is not False:
        return False
    if native.get("status") != "awaiting_native_create" or native.get("replacement_thread_id") is not None:
        return False
    updated_replacement = dict(replacement)
    updated_replacement.pop("native_lifecycle")
    updated_replacement["native_lifecycle_retired"] = {
        **native,
        "status": "retired_non_native_harness",
        "retired_at": isoformat_z(now),
        "reason": (
            "legacy native plan is unsatisfiable on a harness without a native adapter; "
            "converged to the recorded non-native fallback path"
        ),
    }
    state["replacement"] = updated_replacement
    return True


def normalize_identity_state(
    state: dict[str, Any], *, agent: str, now: datetime
) -> tuple[dict[str, Any], bool]:
    """Return a validated identity-aware lease, deterministically backfilling legacy v2 packets."""
    normalized, migrated = task_identity.backfill_legacy_identity(
        state,
        agent=agent,
        repository=task_identity.DEFAULT_REPOSITORY,
        now=isoformat_z(now),
    )
    if migrated:
        replacement = dict(normalized.get("replacement") or {})
        try:
            paths = replacement_packet_paths(
                agent,
                str(replacement["lineage_id"]),
                int(replacement["generation"]),
                str(replacement["rollover_id"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"legacy rollover cannot reserve its identity receipt: {exc}") from exc
        replacement.setdefault("identity_receipt_path", paths["identity_receipt_path"])
        normalized["replacement"] = replacement
    retired = _retire_unsatisfiable_native_plan(normalized, now=now)
    return normalized, migrated or retired


def write_rollover_state(
    state_path: Path,
    state_root: Path,
    state: dict[str, Any],
    *,
    already_locked: bool = False,
) -> None:
    """Commit identity receipt and lease, then refresh the recoverable registry projection."""
    replacement = state.get("replacement") or {}
    receipt_value = replacement.get("identity_receipt_path")
    if not isinstance(receipt_value, str) or not receipt_value:
        raise ValueError("rollover identity receipt path is missing")
    receipt_path = repo_local_path(state_root, Path(receipt_value))
    receipt = task_identity.receipt_payload(state)
    write_json_atomic(receipt_path, receipt)
    write_json_atomic(state_path, state)
    task_family_rollover_registry.sync_from_lease(
        state_root,
        state_path,
        state,
        already_locked=already_locked,
    )


def active_thread_id_from_env() -> str | None:
    return (
        os.environ.get("LEARN_UKRAINIAN_SESSION_ID")
        or os.environ.get("CODEX_THREAD_ID")
        or os.environ.get("CODEX_SESSION_ID")
    )


def request_claudex_rollover(
    *,
    repo_root: Path,
    state_root: Path,
    lineage_id: str,
    replacement: Mapping[str, Any],
) -> dict[str, str] | None:
    """Ask the owning Claudex supervisor to restart after durable prepare.

    Native Claude and Codex sessions have no Claudex run id and therefore keep
    the existing handoff lifecycle. A supervised Claudex session must provide
    the exact launch generation and official SessionStart id; the supervisor
    revalidates all route, process, lease, and native-lifecycle bindings.
    """
    run_id = os.environ.get("LEARN_UKRAINIAN_CLAUDEX_RUN_ID")
    if not run_id:
        return None

    launch_generation_raw = os.environ.get(
        "LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION"
    )
    session_id = os.environ.get("LEARN_UKRAINIAN_SESSION_ID")
    if not launch_generation_raw or not session_id:
        raise ValueError(
            "supervised Claudex rollover requires launch generation and official session identity"
        )
    try:
        launch_generation = int(launch_generation_raw)
    except ValueError as exc:
        raise ValueError(
            "supervised Claudex launch generation must be an integer"
        ) from exc
    if launch_generation < 0:
        raise ValueError(
            "supervised Claudex launch generation must be non-negative"
        )

    rollover_generation = replacement.get("generation")
    rollover_id = replacement.get("rollover_id")
    if not isinstance(rollover_generation, int) or rollover_generation < 1:
        raise ValueError("prepared rollover generation is malformed")
    if not isinstance(rollover_id, str):
        raise ValueError("prepared rollover id is malformed")

    supervisor_script = Path(__file__).with_name("claudex_supervisor.py")
    result = run_command(
        [
            os.fspath(repo_root / ".venv/bin/python"),
            os.fspath(supervisor_script),
            "request-rollover",
            "--state-root",
            os.fspath(state_root),
            "--run-id",
            run_id,
            "--launch-generation",
            str(launch_generation),
            "--session-id",
            session_id,
            "--lineage-id",
            lineage_id,
            "--rollover-generation",
            str(rollover_generation),
            "--rollover-id",
            rollover_id,
        ],
        cwd=repo_root,
    )
    if result.returncode != 0:
        detail = result.stderr or result.stdout or "request command failed"
        raise ValueError(f"Claudex rollover request failed: {detail}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("Claudex rollover request returned malformed JSON") from exc
    if (
        not isinstance(payload, dict)
        or set(payload) != {"request_id", "run_id", "rollover_id"}
        or payload.get("run_id") != run_id
        or payload.get("rollover_id") != rollover_id
        or not isinstance(payload.get("request_id"), str)
    ):
        raise ValueError("Claudex rollover request returned mismatched identity")
    return {key: str(value) for key, value in payload.items()}


def new_rollover_id() -> str:
    return f"rollover-{uuid.uuid4().hex}"


def new_canary_challenge() -> str:
    return uuid.uuid4().hex + uuid.uuid4().hex


def migration_error(state: dict[str, Any], state_path: Path, repo_root: Path) -> dict[str, Any]:
    return {
        "error": "schema v1 state requires an explicit migration before it can be used",
        "state_file": rel(state_path, repo_root),
        "hint": "Rerun prepare with --migrate-v1. Legacy pending replacements are discarded and replaced by a fresh v2 rollover.",
    }


def migrate_v1_state(state: dict[str, Any], *, agent: str, lineage_id: str, now: datetime) -> dict[str, Any]:
    """Safely migrate durable active identity while discarding unverifiable v1 replacement state."""
    active_v1 = dict(state.get("active") or {})
    active_thread_id = str(active_v1.get("thread_id") or "").strip()
    if not active_thread_id:
        raise ValueError("schema v1 state has no active thread id; choose a new --lineage-id and prepare afresh")
    return {
        "schema_version": SCHEMA_VERSION,
        "agent": agent,
        "lineage_id": lineage_id,
        "active": {
            "thread_id": active_thread_id,
            "automation_id": active_v1.get("automation_id"),
            "generation": 0,
            "lineage_id": lineage_id,
            "started_at": active_v1.get("started_at") or isoformat_z(now),
            "last_seen_at": active_v1.get("last_seen_at") or isoformat_z(now),
        },
        "cleanup": {
            "old_automation_ready_to_delete": False,
            "reason": "v1 state migrated; every legacy replacement is unverified",
        },
        "migrated_from_v1_at": isoformat_z(now),
    }


def prepare_state(
    state: dict[str, Any],
    *,
    agent: str = DEFAULT_AGENT,
    now: datetime,
    active_thread_id: str | None,
    active_automation_id: str | None,
    context_percent: float | None,
    force_new_replacement: bool,
    epic_title: str | None = None,
    goal: str | None = None,
    phase: str | None = None,
    next_phase: str | None = None,
    repository: str = task_identity.DEFAULT_REPOSITORY,
    stream_epic: int | None = None,
    stream_epic_url: str | None = None,
    github_issue_number: int | None = None,
    github_issue_url: str | None = None,
    semantic_title: str | None = None,
    task_family: str = "thread-rollover",
    role: str | None = None,
    terminal_goal: str | None = None,
    harness: str | None = None,
) -> dict[str, Any]:
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema v2 state is required; migrate v1 explicitly before preparing")
    if not active_thread_id:
        raise ValueError("--active-thread-id (or LEARN_UKRAINIAN_SESSION_ID/CODEX_THREAD_ID) is required for a v2 rollover")

    prepared = dict(state)
    prepared["schema_version"] = SCHEMA_VERSION
    prepared["agent"] = agent

    active = dict(prepared.get("active") or {})
    requested_thread_id = active_thread_id.strip()
    lineage_id = str(prepared.get("lineage_id") or lineage_id_for(agent, requested_thread_id))
    if (
        active.get("thread_id")
        and active["thread_id"] != requested_thread_id
        and (prepared.get("replacement") or {}).get("status") != "started"
    ):
        raise ValueError("--active-thread-id does not match the active thread recorded for this lineage")
    if not active:
        active = {
            "thread_id": requested_thread_id,
            "generation": 0,
            "lineage_id": lineage_id,
            "started_at": isoformat_z(now),
        }
    active.setdefault("generation", 0)
    active["lineage_id"] = lineage_id
    if active_automation_id:
        active["automation_id"] = active_automation_id
    active["last_seen_at"] = isoformat_z(now)
    prepared["active"] = active
    prepared["lineage_id"] = lineage_id

    replacement = dict(prepared.get("replacement") or {})
    if replacement.get("status") in {"pending_start", "resumed"} and not force_new_replacement:
        raise ValueError(
            f"pending rollover {replacement.get('rollover_id', 'unknown')} already exists; "
            "use --force-new-replacement to supersede it explicitly"
        )
    if replacement.get("status") == "started":
        active = {
            "thread_id": replacement["thread_id"],
            "automation_id": replacement.get("automation_id"),
            "generation": replacement["generation"],
            "lineage_id": lineage_id,
            "started_at": replacement.get("confirmed_at", isoformat_z(now)),
            "last_seen_at": isoformat_z(now),
        }
        if requested_thread_id != active["thread_id"]:
            raise ValueError("--active-thread-id must be the last confirmed replacement thread")
        prepared["active"] = active

    generation = int((prepared["active"] or {}).get("generation", 0)) + 1
    rollover_id = new_rollover_id()
    packet_paths = replacement_packet_paths(agent, lineage_id, generation, rollover_id)
    if (epic_title is None) != (phase is None) or (next_phase is not None and (epic_title is None or phase is None)):
        raise ValueError("legacy epic-title, phase, and optional next-phase metadata must be supplied together")
    if semantic_title is not None:
        semantic = semantic_title
        identity_source = "explicit"
        legacy_fallback = False
    elif goal:
        semantic = goal
        identity_source = "legacy-prepare-goal"
        legacy_fallback = True
    elif epic_title and phase:
        semantic = f"{phase} {epic_title}"
        identity_source = "legacy-prepare-metadata"
        legacy_fallback = True
    else:
        semantic = "Recover predecessor task context"
        identity_source = "legacy-prepare-deterministic-fallback"
        legacy_fallback = True
    resolved_harness = harness or task_identity.default_harness(agent)
    identity = task_identity.build_identity(
        repository=repository,
        stream_epic=stream_epic,
        stream_epic_url=stream_epic_url,
        github_issue_number=github_issue_number,
        github_issue_url=github_issue_url,
        semantic_title=semantic,
        task_family=task_family,
        role=role or agent,
        predecessor_task_id=requested_thread_id,
        replacement_task_id=None,
        lineage_id=lineage_id,
        generation=generation,
        terminal_goal=terminal_goal or task_identity.LEGACY_TERMINAL_GOAL,
        migration_source=identity_source,
        legacy_fallback=legacy_fallback,
    )
    intended_title = identity["visible_title"]
    title_source = identity["migration"]["source"]
    title_transition = task_identity.new_title_transition(
        harness=resolved_harness,
        visible_title_value=intended_title,
        prepared_at=isoformat_z(now),
    )
    native_lifecycle: dict[str, Any] | None = None
    if title_transition["native_title_supported"]:
        family_id, operation_id = task_family_rollover.transition_identity(
            lineage_id=lineage_id,
            generation=generation,
            rollover_id=rollover_id,
        )
        native_lifecycle = {
            "family_id": family_id,
            "operation_id": operation_id,
            "source_thread_id": requested_thread_id,
            "replacement_thread_id": None,
            "status": "awaiting_native_create",
        }
    replacement = {
        "rollover_id": rollover_id,
        "lineage_id": lineage_id,
        "generation": generation,
        "status": "pending_start",
        "prepared_at": isoformat_z(now),
        "thread_id": None,
        "canary_challenge": new_canary_challenge(),
        "display": {
            "epic_title": epic_title,
            "goal": goal,
            "phase": phase,
            "next_phase": next_phase,
            "title": intended_title,
            "title_source": title_source,
        },
        "identity": identity,
        "title_transition": title_transition,
        **packet_paths,
    }
    if native_lifecycle is not None:
        replacement["native_lifecycle"] = native_lifecycle
    prepared["replacement"] = replacement
    prepared["rollover_id"] = rollover_id

    cleanup = dict(prepared.get("cleanup") or {})
    cleanup["old_automation_ready_to_delete"] = False
    cleanup["reason"] = "replacement thread has not been explicitly confirmed"
    prepared["cleanup"] = cleanup

    prepared["last_handoff"] = {
        "prepared_at": isoformat_z(now),
        "context_percent": context_percent,
    }
    return prepared


def validate_live_lease(
    state: dict[str, Any], *, agent: str, state_path: Path
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate a detectable v2 lease without accepting partial or relocated state."""
    if state.get("state_error"):
        return None, str(state["state_error"])
    if state.get("schema_version") != SCHEMA_VERSION:
        return None, f"schema_version must be {SCHEMA_VERSION}"
    if state.get("agent") != agent:
        return None, f"lease agent {state.get('agent')!r} does not match requested agent {agent!r}"
    lineage_id = state.get("lineage_id")
    if (
        not isinstance(lineage_id, str)
        or not lineage_id.startswith("lineage-")
        or not LINEAGE_ID_RE.fullmatch(lineage_id)
    ):
        return None, "lease lineage_id is malformed"
    if state_path.parent.name != lineage_id:
        return None, "lease lineage_id does not match its canonical directory"
    active = state.get("active")
    if (
        not isinstance(active, dict)
        or active.get("lineage_id") != lineage_id
        or not isinstance(active.get("thread_id"), str)
        or not active["thread_id"].strip()
    ):
        return None, "lease active identity is malformed or mismatched"
    try:
        normalized_state, _ = normalize_identity_state(state, agent=agent, now=utc_now())
    except ValueError as exc:
        return None, f"task identity migration failed: {exc}"
    replacement = normalized_state.get("replacement")
    if not isinstance(replacement, dict):
        return None, "lease replacement is missing or malformed"
    if replacement.get("lineage_id") != lineage_id:
        return None, "replacement lineage_id does not match lease lineage_id"
    rollover_id = replacement.get("rollover_id")
    if not isinstance(rollover_id, str):
        return None, "replacement rollover_id is missing"
    try:
        normalize_rollover_id(rollover_id)
    except ValueError as exc:
        return None, str(exc)
    generation = replacement.get("generation")
    if not isinstance(generation, int) or generation < 1:
        return None, "replacement generation is malformed"
    if state.get("rollover_id") != rollover_id:
        return None, "lease rollover_id does not match replacement rollover_id"
    if replacement.get("status") not in {"pending_start", "resumed", "started"}:
        return None, "replacement status is malformed"
    if replacement.get("status") == "resumed" and (
        not isinstance(replacement.get("resumed_thread_id"), str) or not replacement["resumed_thread_id"].strip()
    ):
        return None, "resumed replacement has no valid replacement thread identity"
    if replacement.get("status") in {"pending_start", "resumed"}:
        binding_error = source_checkout_binding_error(replacement)
        if binding_error:
            return None, binding_error
        try:
            identity = task_identity.validate_identity(replacement.get("identity") or {})
            title_transition = task_identity.validate_title_transition(
                replacement.get("title_transition") or {}, identity
            )
        except ValueError as exc:
            return None, f"replacement task identity is malformed: {exc}"
        display = replacement.get("display")
        if (
            not isinstance(display, dict)
            or display.get("title") != identity["visible_title"]
            or display.get("title_source") != identity["migration"]["source"]
            or identity["predecessor_task_id"] != active["thread_id"]
            or identity["lineage_id"] != lineage_id
            or identity["generation"] != generation
        ):
            return None, "replacement display or task identity does not match the exact lease"
        native = replacement.get("native_lifecycle")
        if title_transition["native_title_supported"]:
            expected_family_id, expected_operation_id = task_family_rollover.transition_identity(
                lineage_id=lineage_id,
                generation=generation,
                rollover_id=rollover_id,
            )
            if (
                not isinstance(native, dict)
                or native.get("family_id") != expected_family_id
                or native.get("operation_id") != expected_operation_id
                or native.get("source_thread_id") != active["thread_id"]
            ):
                return None, "replacement native lifecycle identity is missing, forged, or malformed"
        expected_paths = replacement_packet_paths(agent, lineage_id, generation, rollover_id)
        for key, expected in expected_paths.items():
            if replacement.get(key) != expected:
                return None, f"replacement {key} is missing, forged, or not the reserved packet path"
        challenge = replacement.get("canary_challenge")
        if not isinstance(challenge, str) or not re.fullmatch(r"[0-9a-f]{64}", challenge):
            return None, "replacement canary_challenge is malformed"
    return replacement, None


def _canonical_json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_strict_verdict(
    *,
    replacement: dict[str, Any],
    state_root: Path,
    strict_probe: Path,
    strict_verdict: Path,
) -> dict[str, Any]:
    """Require the reserved strict v2 10/10 evidence before cleanup can unlock."""
    expected_probe = repo_local_path(state_root, Path(replacement["strict_probe_path"]))
    expected_verdict = repo_local_path(state_root, Path(replacement["strict_verdict_path"]))
    if strict_probe != expected_probe or strict_verdict != expected_verdict:
        raise ValueError("strict probe and verdict must use the paths reserved by this rollover")
    try:
        probe = json.loads(strict_probe.read_text(encoding="utf-8"))
        verdict = json.loads(strict_verdict.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"strict production evidence is unreadable: {type(exc).__name__}: {exc}") from exc
    if not isinstance(probe, dict) or not isinstance(verdict, dict):
        raise ValueError("strict production evidence must be JSON objects")
    validated_probe, probe_error = context_canary.validate_production_probe(
        probe,
        expected_lineage_id=replacement["lineage_id"],
        expected_rollover_id=replacement["rollover_id"],
    )
    if probe_error:
        raise ValueError(f"strict probe failed production validation: {probe_error}")
    assert validated_probe is not None
    probe = validated_probe
    anchor_ids = [anchor["id"] for anchor in probe["anchors"]]
    required_verdict_keys = {
        "version",
        "schema",
        "lineage_id",
        "rollover_id",
        "probe_sha256",
        "seed",
        "k",
        "correct",
        "score",
        "verdict",
        "model",
        "per_anchor",
    }
    if set(verdict) != required_verdict_keys:
        raise ValueError("strict verdict has missing or forged fields")
    if (
        verdict.get("version") != "2"
        or verdict.get("schema") != "production-handoff-v2"
        or verdict.get("lineage_id") != replacement["lineage_id"]
        or verdict.get("rollover_id") != replacement["rollover_id"]
        or verdict.get("probe_sha256") != _canonical_json_sha256(probe)
        or verdict.get("seed") != probe["seed"]
        or verdict.get("k") != 10
        or verdict.get("correct") != 10
        or verdict.get("score") != 1.0
        or verdict.get("verdict") != "PASS"
    ):
        raise ValueError("strict verdict is not the required PASS 10/10 for this reserved probe")
    rows = verdict.get("per_anchor")
    if not isinstance(rows, list) or len(rows) != 10:
        raise ValueError("strict verdict does not attest every anchor")
    row_ids = [row.get("id") for row in rows if isinstance(row, dict) and row.get("match") is True]
    if set(row_ids) != set(anchor_ids) or len(row_ids) != 10:
        raise ValueError("strict verdict does not report a matching PASS for every anchor")
    return verdict


def confirm_started(
    state: dict[str, Any],
    *,
    new_thread_id: str,
    new_automation_id: str | None,
    confirmed_by: str,
    now: datetime,
    canary_proof: Path,
    strict_probe: Path,
    strict_verdict: Path,
    state_root: Path,
) -> dict[str, Any]:
    if not new_thread_id.strip():
        raise ValueError("--new-thread-id is required")
    if state.get("schema_version") != SCHEMA_VERSION or not state.get("replacement"):
        raise ValueError("no pending replacement exists; run prepare first")

    confirmed = dict(state)
    replacement = dict(confirmed["replacement"])
    active = confirmed.get("active")
    if not isinstance(active, dict) or not isinstance(active.get("thread_id"), str) or not active["thread_id"].strip():
        raise ValueError("confirmed rollover has no exact predecessor thread identity")
    status = replacement.get("status")
    if status not in {"resumed", "started"}:
        raise ValueError("replacement must be resumed through the rollover packet before confirmation")
    if status == "started":
        if replacement.get("thread_id") != new_thread_id.strip():
            raise ValueError("--new-thread-id does not match the already confirmed replacement")
    else:
        if replacement.get("resumed_thread_id") != new_thread_id.strip():
            raise ValueError("--new-thread-id does not match the thread that resumed this rollover")
        native = replacement.get("native_lifecycle")
        if isinstance(native, dict) and native.get("replacement_thread_id") != new_thread_id.strip():
            raise ValueError("--new-thread-id does not match the exact native-created replacement")
    identity = task_identity.validate_identity(replacement.get("identity") or {})
    transition = task_identity.validate_title_transition(
        replacement.get("title_transition") or {}, identity
    )
    task_identity.assert_title_ready(
        identity,
        transition,
        replacement_task_id=new_thread_id.strip(),
    )
    if status == "started":
        proof = replacement.get("canary_proof") or {}
        verdict = replacement.get("strict_verdict") or {}
        cleanup = confirmed.get("cleanup") or {}
        if (
            identity["lifecycle_state"] != "confirmed"
            or proof.get("status") != "PASS"
            or verdict.get("verdict") != "PASS"
            or cleanup.get("old_automation_ready_to_delete") is not True
        ):
            raise ValueError("existing confirmation is incomplete or inconsistent")
        return state
    native = replacement.get("native_lifecycle")
    proof, proof_error = thread_handoff_canary.load_and_validate_pass_proof(
        canary_proof,
        rollover_id=str(replacement.get("rollover_id") or ""),
        replacement_thread_id=new_thread_id.strip(),
        challenge=str(replacement.get("canary_challenge") or ""),
    )
    if proof_error:
        raise ValueError(f"script-proven canary PASS is required: {proof_error}")
    strict_evidence = validate_strict_verdict(
        replacement=replacement,
        state_root=state_root,
        strict_probe=strict_probe,
        strict_verdict=strict_verdict,
    )
    replacement["status"] = "started"
    replacement["thread_id"] = new_thread_id.strip()
    replacement["confirmed_at"] = isoformat_z(now)
    if new_automation_id:
        replacement["automation_id"] = new_automation_id
    replacement["canary_proof"] = proof
    replacement["strict_verdict"] = strict_evidence
    replacement["identity"] = task_identity.mark_confirmed(
        identity,
        transition,
        replacement_task_id=new_thread_id.strip(),
    )
    if isinstance(native, dict):
        native = dict(native)
        native["status"] = "confirmed_started"
        native["confirmed_at"] = isoformat_z(now)
        replacement["native_lifecycle"] = native
    confirmed["replacement"] = replacement

    cleanup = dict(confirmed.get("cleanup") or {})
    cleanup["old_automation_ready_to_delete"] = True
    cleanup["confirmed_by"] = confirmed_by
    cleanup["confirmed_at"] = isoformat_z(now)
    cleanup["reason"] = "replacement thread start confirmed by operator command"
    confirmed["cleanup"] = cleanup
    confirmed["updated_at"] = isoformat_z(now)
    return confirmed


def resume_state(
    state: dict[str, Any], *, rollover_id: str, replacement_thread_id: str, now: datetime
) -> dict[str, Any]:
    """Bind exactly one new thread to a prepared local packet, without provider history."""
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema v2 state is required; run prepare with --migrate-v1 first")
    replacement = dict(state.get("replacement") or {})
    if replacement.get("status") not in {"pending_start", "resumed"}:
        raise ValueError("no pending rollover is available to resume")
    if replacement.get("rollover_id") != rollover_id:
        raise ValueError("--rollover-id does not match the pending rollover")
    thread_id = replacement_thread_id.strip()
    if not thread_id:
        raise ValueError("--replacement-thread-id is required")
    native = replacement.get("native_lifecycle")
    if isinstance(native, dict):
        bound_thread_id = native.get("replacement_thread_id")
        if not isinstance(bound_thread_id, str) or not bound_thread_id.strip():
            raise ValueError("native-created replacement must be registered before resume")
        if bound_thread_id != thread_id:
            raise ValueError("--replacement-thread-id does not match the exact native-created replacement")
    identity = task_identity.validate_identity(replacement.get("identity") or {})
    transition = task_identity.validate_title_transition(
        replacement.get("title_transition") or {}, identity
    )
    task_identity.assert_title_ready(identity, transition, replacement_task_id=thread_id)
    existing = replacement.get("resumed_thread_id")
    if existing and existing != thread_id:
        raise ValueError("pending rollover is already bound to a different replacement thread")
    if existing == thread_id and identity["lifecycle_state"] == "resumed":
        return state
    replacement["status"] = "resumed"
    replacement["resumed_thread_id"] = thread_id
    replacement.setdefault("resumed_at", isoformat_z(now))
    replacement["identity"] = task_identity.mark_resumed(
        identity,
        transition,
        replacement_task_id=thread_id,
    )
    if isinstance(native, dict):
        native = dict(native)
        native["status"] = "resumed"
        native["resumed_at"] = replacement["resumed_at"]
        replacement["native_lifecycle"] = native
    resumed = dict(state)
    resumed["replacement"] = replacement
    resumed["updated_at"] = isoformat_z(now)
    return resumed


def format_table(rows: list[list[str]], headers: list[str]) -> str:
    if not rows:
        return "_None._"
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(value))
    header_line = "| " + " | ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers)) + " |"
    sep_line = "| " + " | ".join("-" * widths[idx] for idx in range(len(headers))) + " |"
    row_lines = ["| " + " | ".join(value.ljust(widths[idx]) for idx, value in enumerate(row)) + " |" for row in rows]
    return "\n".join([header_line, sep_line, *row_lines])


def summarize_prs(open_prs: Any) -> str:
    if isinstance(open_prs, dict) and open_prs.get("_error"):
        return f"_Unavailable: {open_prs['_error']}_"
    rows = []
    for pr in open_prs if isinstance(open_prs, list) else []:
        rows.append(
            [
                f"#{pr.get('number')}",
                str(pr.get("headRefName") or ""),
                str(pr.get("mergeStateStatus") or ""),
                "yes" if pr.get("isDraft") else "no",
                str(pr.get("title") or ""),
            ]
        )
    return format_table(rows, ["PR", "Branch", "Merge", "Draft", "Title"])


def summarize_issues(open_issues: Any) -> str:
    if isinstance(open_issues, dict) and open_issues.get("_error"):
        return f"_Unavailable: {open_issues['_error']}_"
    rows = []
    for issue in open_issues if isinstance(open_issues, list) else []:
        rows.append(
            [
                f"#{issue.get('number')}",
                str(issue.get("updatedAt") or ""),
                str(issue.get("title") or ""),
            ]
        )
    return format_table(rows, ["Issue", "Updated", "Title"])


def summarize_tasks(tasks_payload: Any) -> str:
    if not isinstance(tasks_payload, dict):
        return "_Unavailable._"
    if tasks_payload.get("_error"):
        return f"_Unavailable: {tasks_payload['_error']}_"
    rows = []
    for task in tasks_payload.get("tasks") or []:
        rows.append(
            [
                str(task.get("task_id") or ""),
                str(task.get("agent") or ""),
                str(task.get("status") or ""),
                str(task.get("age_s") or task.get("duration_s") or ""),
            ]
        )
    return format_table(rows, ["Task", "Agent", "Status", "Age/Duration"])


def summarize_modified_files(files: list[dict[str, str]]) -> str:
    if not files:
        return "_None._"
    rows = [[item.get("status", ""), item.get("path", "")] for item in files]
    return format_table(rows, ["Status", "Path"])


def summarize_commits(commits: list[dict[str, str]]) -> str:
    rows = [[item.get("sha", ""), item.get("subject", "")] for item in commits]
    return format_table(rows, ["SHA", "Subject"])


def context_line(
    context_percent: float | None,
    threshold: float,
    window: int = 0,
    profile_id: str = "unknown",
    provenance: str = "default",
) -> str:
    if context_percent is None:
        return "Context percent was not supplied; use --context-percent from a statusline or manual estimate."
    state = "ROLL OVER NOW" if context_percent >= threshold else "below rollover threshold"
    if window > 0:
        abs_point = int(threshold * window / 100.0)
        abs_used = int(context_percent * window / 100.0)
        return (
            f"Context estimate: {context_percent:.1f}% ({state}; threshold {threshold:.1f}%). "
            f"Observed/estimated used: {abs_used}/{window} tokens (Warning at: {abs_point} tokens). "
            f"Policy profile: {profile_id} (Provenance: {provenance})."
        )
    else:
        return (
            f"Context estimate: {context_percent:.1f}% ({state}; threshold {threshold:.1f}%). "
            f"Policy profile: {profile_id} (No assumed denominator; Provenance: {provenance})."
        )


def first_turn_checklist_lines(
    *,
    repo_root: str,
    thread_handoff_text: str,
    role_handoff_text: str,
) -> list[str]:
    return [
        "First-turn checklist:",
        f"1. `cd {repo_root}`",
        "2. `git status --short --branch`",
        f"3. Read `{thread_handoff_text}` and `{role_handoff_text}`.",
        "4. Check `/api/orient?fresh=true` from the local monitor.",
        "5. If `/api/orient` returns an `issues_error` or the GitHub issue subsection times out, run `.venv/bin/python scripts/orchestration/issue_stream_audit.py --json`.",
        "6. `gh pr list --state open --json number,title,headRefName,mergeStateStatus,statusCheckRollup,url,updatedAt,isDraft,reviewDecision --limit 20`",
        "7. `git worktree list` and verify the active worktree is the one you intend to edit.",
    ]


def resolve_handoff_policy(context_threshold: float) -> tuple[float, int, str, str]:
    """Resolve the session record's actual capacity and rollover policy.

    Official statusline observations win over the declared launcher profile. A
    missing or untrusted route has no denominator; it must never inherit 1M.
    """
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from scripts.lib.context_profiles import resolve_profile
    from scripts.lib.session_record import read_record

    session_id = (
        os.environ.get("LEARN_UKRAINIAN_SESSION_ID")
        or os.environ.get("CODEX_SESSION_ID")
        or os.environ.get("CODEX_THREAD_ID")
    )
    record = read_record(session_id) if session_id else None

    if record is not None:
        window_raw = record.get("actual_context_window_tokens")
        window = window_raw if isinstance(window_raw, int) and window_raw > 0 else 0
        active_profile_id = str(record.get("effective_profile_id") or "fallback")
        percentages = record.get("rollover_warning_percentages")
        provenance = str(
            record.get("actual_context_window_provenance") or "unavailable"
        )
    else:
        requested_profile_id = (
            os.environ.get("LEARN_UKRAINIAN_REQUESTED_PROFILE_ID")
            or os.environ.get("LEARN_UKRAINIAN_PROFILE_ID")
        )
        observed_model_id = (
            os.environ.get("LEARN_UKRAINIAN_OBSERVED_MODEL_ID")
            or os.environ.get("LEARN_UKRAINIAN_MAIN_MODEL_ID")
        )
        profile = resolve_profile(requested_profile_id, observed_model_id)
        trusted_window = profile.get("main_context_window_tokens")
        window = (
            trusted_window
            if profile.get("trusted")
            and isinstance(trusted_window, int)
            and trusted_window > 0
            else 0
        )
        active_profile_id = str(profile.get("profile_id") or "fallback")
        percentages = profile.get("rollover_warning_percentages")
        provenance = "declared-profile" if window > 0 else "unavailable"

    valid_percentages = (
        percentages
        if isinstance(percentages, list)
        and len(percentages) == 3
        and all(isinstance(value, int | float) for value in percentages)
        else [75.0, 85.0, 90.0]
    )
    derived_threshold = float(valid_percentages[1])
    active_threshold = (
        derived_threshold
        if context_threshold == DEFAULT_CONTEXT_THRESHOLD
        else context_threshold
    )
    return active_threshold, window, active_profile_id, provenance


def render_bootstrap_prompt(
    snapshot: dict[str, Any],
    state: dict[str, Any],
    *,
    agent: str = DEFAULT_AGENT,
    router_path: Path = DEFAULT_ROUTER_PATH,
    handoff_path: Path | None = None,
    role_handoff_path: Path | None = None,
    state_root: Path | None = None,
    context_threshold: float,
) -> str:
    active_thresh, window, active_profile, provenance = resolve_handoff_policy(context_threshold)
    git = snapshot["git"]
    active = state.get("active") or {}
    replacement = state.get("replacement") or {}
    display = replacement.get("display") or {}
    identity = replacement.get("identity") or {}
    title_transition = replacement.get("title_transition") or {}
    prompt_path = replacement.get("bootstrap_prompt_path") or "unknown"
    handoff_path = handoff_path or Path(replacement.get("handoff_path") or "unknown")
    role_handoff_path = role_handoff_path or default_handoff_path(agent)
    handoff_text = role_handoff_path.as_posix()
    thread_handoff_text = handoff_path.as_posix()
    active_generation = active.get("generation") or "unknown"
    replacement_generation = replacement.get("generation") or "unknown"
    rollover_id = replacement.get("rollover_id") or "unknown"
    context_percent = (state.get("last_handoff") or {}).get("context_percent")
    agent_label = "Codex orchestrator" if agent == "orchestrator" else agent
    if title_transition.get("native_title_supported"):
        title_rules = [
            "- The predecessor app task must create and register this exact replacement, mutate its exact native title, record the acknowledgement, and reconcile an exact readback before resume.",
            "- A successful title acknowledgement without exact readback is not reconciled and must fail closed.",
        ]
    else:
        title_rules = [
            "- This harness has no native title mutation adapter. Bind the exact replacement with `bind-replacement` before resume.",
            "- Preserve the visible title in the dispatch record, brief, ledger, inbox, monitor API, and final receipt; never claim a native rename.",
        ]
    return (
        "\n".join(
            [
                f"Work locally in {git.get('repo_root')}.",
                "",
                f"You are the replacement {agent_label} thread.",
                f"Task title: {identity.get('visible_title', display.get('title', 'unknown'))}",
                f"Repository: {identity.get('repository', 'unknown')}",
                f"Stream epic: {identity.get('stream_epic_url') or identity.get('stream_epic') or 'not-recorded'}",
                f"GitHub issue: {identity.get('github_issue_url') or identity.get('github_issue_number') or 'not-applicable'}",
                f"Task family / role: {identity.get('task_family', 'unknown')} / {identity.get('role', 'unknown')}",
                f"Terminal goal: {identity.get('terminal_goal', 'unknown')}",
                f"Replacement generation: {replacement_generation}",
                f"Rollover id: {rollover_id}",
                f"Previous active generation: {active_generation}",
                f"Role handoff: {handoff_text}",
                f"Thread handoff: {thread_handoff_text}",
                "",
                "Read first:",
                f"- {thread_handoff_text}",
                f"- {handoff_text}",
                "- AGENTS.md",
                "- docs/best-practices/agent-cooperation.md",
                "- docs/best-practices/codex-thread-handoff.md",
                "",
                "Rules:",
                "- Continue from the durable packet exactly; do not fork, continue, or resume provider conversation history.",
                f"- Keep the invoking checkout clean at prepared HEAD {replacement.get('source_checkout', {}).get('full_head', 'unknown')} through resume and confirmation (clean fast-forward advances are tolerated).",
                "- Keep the main checkout read-only; thread rollover state belongs in gitignored .agent/ files.",
                "- Use dispatch worktrees for implementation work: .worktrees/dispatch/<agent>/<task>/.",
                "- Do not edit generated status/audit/review artifacts, linter configs, or .python-version.",
                "- Do not write docs/session-state/current.md for thread rollover.",
                "- Do not delete or migrate the old heartbeat automation until the confirm-started command below has succeeded.",
                "- Do not archive the predecessor unless the exact post-confirmation native action is authorized with idle and unpinned app evidence.",
                *title_rules,
                "",
                *first_turn_checklist_lines(
                    repo_root=str(git.get("repo_root")),
                    thread_handoff_text=thread_handoff_text,
                    role_handoff_text=handoff_text,
                ),
                "",
                "Local monitor follow-up:",
                "```bash",
                "curl -sS http://127.0.0.1:8765/api/delegate/active",
                "curl -sS http://127.0.0.1:8765/api/worktrees",
                ".venv/bin/python scripts/orchestration/orchestrator_control.py inbox --recent 20 --include-results",
                "```",
                "",
                "Use the compact capsule command card emitted by `detect --format session-start` for this packet.",
                "It is the only execution card: `bootstrap-replacement` emits the strict snapshot template; `confirm-replacement` emits questions when answers are absent, then mints, scores, proves, and confirms on its idempotent rerun.",
                "",
                "After confirmation, read the exact predecessor through the native app. Run `native-action --action archive` with its authoritative status and pin facts. If either fact is absent, use `unknown`; the durable receipt must block and preserve the predecessor. Only an actionable response authorizes `set_thread_archived` for the returned exact UUID, followed by `record-native-result` and `reconcile-native`.",
                "",
                "Only after that command reports old_automation_ready_to_delete=true may the old heartbeat automation be deleted or paused.",
                "",
                "Durable packet identity:",
                f"- Branch at preparation: {git.get('branch')} @ {git.get('head')}",
                f"- {context_line(float(context_percent) if context_percent is not None else None, active_thresh, window, active_profile, provenance)}",
                f"- Bootstrap prompt source: {prompt_path}",
            ]
        )
        + "\n"
    )


def render_current_markdown(
    snapshot: dict[str, Any],
    state: dict[str, Any],
    *,
    agent: str = DEFAULT_AGENT,
    role_handoff_path: Path | None = None,
    state_root: Path | None = None,
    context_threshold: float,
) -> str:
    git = snapshot["git"]
    active = state.get("active") or {}
    replacement = state.get("replacement") or {}
    identity = replacement.get("identity") or {}
    title_transition = replacement.get("title_transition") or {}
    cleanup = state.get("cleanup") or {}
    prompt_path = replacement.get("bootstrap_prompt_path") or "unknown"
    thread_handoff_text = replacement.get("handoff_path") or "unknown"
    role_handoff = (role_handoff_path or default_handoff_path(agent)).as_posix()
    title_agent = "Orchestrator" if agent == "orchestrator" else agent.title()

    lines = [
        f"# Current - {title_agent} thread handoff ({snapshot['generated_at']})",
        "",
        "> Generated by `scripts/orchestration/thread_handoff.py prepare`.",
        "> This is a rollover handoff, not proof that the replacement thread started.",
        f"> Agent: `{agent}`.",
        "",
        "## Thread Lease",
        "",
        f"- Active generation: `{active.get('generation', 'unknown')}`",
        f"- Active thread id: `{active.get('thread_id', 'unknown')}`",
        f"- Active automation id: `{active.get('automation_id', 'unknown')}`",
        f"- Replacement generation: `{replacement.get('generation', 'unknown')}`",
        f"- Rollover id: `{replacement.get('rollover_id', 'unknown')}`",
        f"- Lineage id: `{replacement.get('lineage_id', state.get('lineage_id', 'unknown'))}`",
        f"- Replacement runtime path: `{replacement.get('runtime_path', 'unknown')}`",
        f"- Replacement status: `{replacement.get('status', 'unknown')}`",
        f"- Replacement thread id: `{replacement.get('thread_id') or 'not-confirmed'}`",
        f"- Source checkout HEAD: `{replacement.get('source_checkout', {}).get('full_head', 'unknown')}`",
        f"- Old automation ready to delete: `{cleanup.get('old_automation_ready_to_delete', False)}`",
        f"- Bootstrap prompt: `{prompt_path}`",
        f"- Durable role handoff: `{role_handoff}`",
        "",
        "## Task Identity",
        "",
        f"- Visible title: `{identity.get('visible_title', 'unknown')}`",
        f"- Semantic title: `{identity.get('semantic_title', 'unknown')}`",
        f"- Repository: `{identity.get('repository', 'unknown')}`",
        f"- Stream epic: `{identity.get('stream_epic_url') or identity.get('stream_epic') or 'not-recorded'}`",
        f"- GitHub issue: `{identity.get('github_issue_url') or identity.get('github_issue_number') or 'not-applicable'}`",
        f"- Task family / role: `{identity.get('task_family', 'unknown')}` / `{identity.get('role', 'unknown')}`",
        f"- Predecessor / replacement: `{identity.get('predecessor_task_id', 'unknown')}` / `{identity.get('replacement_task_id') or 'not-bound'}`",
        f"- Terminal goal: `{identity.get('terminal_goal', 'unknown')}`",
        f"- Identity lifecycle: `{identity.get('lifecycle_state', 'unknown')}`",
        f"- Title adapter: `{title_transition.get('harness', 'unknown')}` (`{title_transition.get('state', 'unknown')}`)",
        f"- Native title mutation supported: `{title_transition.get('native_title_supported', False)}`",
        "",
        "## First-Turn Checklist",
        "",
        *first_turn_checklist_lines(
            repo_root=str(git.get("repo_root")),
            thread_handoff_text=thread_handoff_text,
            role_handoff_text=role_handoff,
        ),
        "",
        "## Rollover Command Capsule",
        "",
        "Use `detect --format session-start` for the sole compact execution card. It contains `bootstrap-replacement` and `confirm-replacement`; do not reconstruct the individual proof commands.",
        "",
        "Do not delete the old heartbeat automation before this confirmation.",
        "",
    ]
    return "\n".join(lines)


def render_router_markdown(
    *,
    generated_at: str,
    default_agent: str,
    agents: list[str],
) -> str:
    default_handoff = default_handoff_path(default_agent).as_posix()
    lines = [
        "# Current Session Router",
        "",
        f"Latest-Brief: {default_handoff}",
        "",
        "Agent-Handoff:",
    ]
    for agent in agents:
        lines.append(f"- {agent}: {default_handoff_path(agent).as_posix()}")
    lines.extend(
        [
            "",
            f"Default-Agent: {default_agent}",
            f"Generated-At: {generated_at}",
            "",
            "This file is a small compatibility router. Durable role state lives in",
            "the mapped Agent-Handoff files. Thread rollover packets live under",
            "`.agent/<agent>-thread-handoff.md` unless explicitly overridden.",
            "",
        ]
    )
    return "\n".join(lines)


def inspect_codex_home(codex_home: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "codex_home": str(codex_home),
        "exists": codex_home.exists(),
        "session_index": str(codex_home / "session_index.jsonl"),
        "automations_dir": str(codex_home / "automations"),
    }
    automations_dir = codex_home / "automations"
    if automations_dir.exists():
        result["automation_toml_files"] = [str(path) for path in sorted(automations_dir.glob("**/automation.toml"))]
    else:
        result["automation_toml_files"] = []

    state_dbs = sorted(codex_home.glob("state_*.sqlite"), key=lambda p: p.stat().st_mtime, reverse=True)
    result["state_databases"] = [str(path) for path in state_dbs[:3]]
    if state_dbs:
        db_path = state_dbs[0]
        try:
            with closing(sqlite3.connect(db_path)) as conn:
                tables = [
                    row[0] for row in conn.execute("select name from sqlite_master where type='table' order by name")
                ]
                result["latest_state_db"] = str(db_path)
                result["tables"] = tables
                if "threads" in tables:
                    result["thread_count"] = conn.execute("select count(*) from threads").fetchone()[0]
                    result["recent_threads"] = [
                        {"id": row[0], "title": row[1], "cwd": row[2], "archived": bool(row[3])}
                        for row in conn.execute(
                            "select id, title, cwd, archived from threads order by updated_at desc limit 5"
                        )
                    ]
        except sqlite3.Error as exc:
            result["sqlite_error"] = f"{type(exc).__name__}: {exc}"

    result["history_resume_used"] = False
    return result


def check_state(
    state: dict[str, Any],
    *,
    now: datetime,
    stale_after: timedelta,
    context_percent: float | None,
    context_threshold: float,
) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    facts: list[str] = []
    active = state.get("active") or {}
    replacement = state.get("replacement") or {}
    cleanup = state.get("cleanup") or {}

    if state.get("state_error"):
        warnings.append(str(state["state_error"]))

    facts.append(f"active_generation={active.get('generation', 'unknown')}")
    facts.append(f"lineage_id={state.get('lineage_id', 'unknown')}")
    facts.append(f"rollover_id={replacement.get('rollover_id', 'none')}")
    facts.append(f"replacement_status={replacement.get('status', 'none')}")
    identity = replacement.get("identity") or {}
    title_transition = replacement.get("title_transition") or {}
    facts.append(f"visible_title={identity.get('visible_title', 'legacy-unmigrated')}")
    facts.append(f"github_issue_number={identity.get('github_issue_number', 'none')}")
    facts.append(f"identity_lifecycle={identity.get('lifecycle_state', 'legacy-unmigrated')}")
    facts.append(f"title_confirmation_state={title_transition.get('state', 'legacy-unmigrated')}")
    facts.append(f"old_automation_ready_to_delete={cleanup.get('old_automation_ready_to_delete', False)}")

    active_seen = parse_iso_datetime(active.get("last_seen_at") or active.get("started_at"))
    if active_seen and now - active_seen > stale_after:
        warnings.append(f"active generation last seen {now - active_seen} ago")

    prepared_at = parse_iso_datetime(replacement.get("prepared_at"))
    if replacement.get("status") == "pending_start":
        warnings.append("replacement thread is pending_start; old automation must stay active")
        if prepared_at and now - prepared_at > stale_after:
            warnings.append(f"replacement has been pending for {now - prepared_at}")

    if cleanup.get("old_automation_ready_to_delete") and not replacement.get("thread_id"):
        warnings.append("cleanup says ready, but replacement thread_id is missing")

    active_thresh, _, _, _ = resolve_handoff_policy(context_threshold)
    if context_percent is not None and context_percent >= active_thresh:
        warnings.append(f"context estimate {context_percent:.1f}% is at/above threshold {active_thresh:.1f}%")

    return facts, warnings


def _rollover_mutation_lock_path(args: argparse.Namespace) -> Path | None:
    """Resolve one lineage lock without replacing command-specific errors."""
    try:
        _, state_root = resolve_roots(args.repo_root)
        agent = normalize_agent_name(args.agent)
        if getattr(args, "lineage_id", None):
            return state_root / default_state_path(agent, args.lineage_id).parent / ".native-intent.lock"
        if getattr(args, "state_file", None):
            state_path = resolve_state_path(
                repo_root=state_root,
                state_root=state_root,
                supplied_state_file=args.state_file,
                default_path=None,
            )
            return state_path.parent / ".native-intent.lock"
        active_thread_id = getattr(args, "active_thread_id", None) or active_thread_id_from_env()
        if active_thread_id:
            lineage_id = lineage_id_for(agent, active_thread_id)
            return state_root / default_state_path(agent, lineage_id).parent / ".native-intent.lock"
    except ValueError:
        return None
    return None


def cmd_prepare(args: argparse.Namespace) -> int:
    lock_path = _rollover_mutation_lock_path(args)
    if lock_path is None:
        return _cmd_prepare_locked(args)
    with task_family_advisory_lock(lock_path):
        return _cmd_prepare_locked(args)


def _cmd_prepare_locked(args: argparse.Namespace) -> int:
    try:
        repo_root, state_root = resolve_roots(args.repo_root)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2
    now = utc_now()
    agent = normalize_agent_name(args.agent)
    active_thread_id = args.active_thread_id or active_thread_id_from_env()
    if not active_thread_id:
        print(
            json.dumps(
                {
                    "error": "--active-thread-id (or LEARN_UKRAINIAN_SESSION_ID/CODEX_THREAD_ID) is required for a v2 rollover",
                    "agent": agent,
                },
                indent=2,
            )
        )
        return 2
    lineage_id = args.lineage_id or lineage_id_for(agent, active_thread_id)
    role_handoff_file = default_handoff_path(agent)
    router_file = args.current_file or DEFAULT_ROUTER_PATH
    try:
        state_path = resolve_state_path(
            repo_root=repo_root,
            state_root=state_root,
            supplied_state_file=args.state_file,
            default_path=default_state_path(agent, lineage_id) if lineage_id else None,
        )
        router_path = repo_local_path(repo_root, router_file)
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "agent": agent}, indent=2))
        return 2
    role_handoff_path = repo_root / role_handoff_file

    if args.write_current and not args.allow_git_router:
        print(
            json.dumps(
                {
                    "error": "--write-current is disabled by default because docs/session-state/current.md is git-tracked. "
                    "Use the default .agent/ handoff files for thread rollover, or pass --allow-git-router only for an explicitly approved compatibility-router update.",
                    "agent": agent,
                    "state_file": rel(state_path, state_root),
                },
                indent=2,
            )
        )
        return 2

    state = load_state(state_path)
    state_error = state_error_payload(state, state_path, state_root)
    if state_error and not args.force_reset_state:
        print(json.dumps(state_error, indent=2))
        return 2
    if state_error and args.force_reset_state:
        state = {
            "schema_version": SCHEMA_VERSION,
            "reset_from_error": state_error["error"],
        }
    if state.get("schema_version") == 1:
        if not args.migrate_v1:
            print(json.dumps(migration_error(state, state_path, repo_root), indent=2))
            return 2
        try:
            state = migrate_v1_state(state, agent=agent, lineage_id=lineage_id, now=now)
        except ValueError as exc:
            print(json.dumps({"error": str(exc), "state_file": rel(state_path, state_root)}, indent=2))
            return 2
    if state.get("agent") and state["agent"] != agent:
        print(
            json.dumps(
                {
                    "error": "state agent does not match --agent",
                    "state_file": rel(state_path, state_root),
                },
                indent=2,
            )
        )
        return 2
    if state.get("lineage_id") and state["lineage_id"] != lineage_id:
        print(
            json.dumps(
                {
                    "error": "state lineage does not match --lineage-id/active thread identity",
                    "state_file": rel(state_path, state_root),
                },
                indent=2,
            )
        )
        return 2
    previous_replacement = dict(state.get("replacement") or {})
    try:
        prepared_state = prepare_state(
            state,
            agent=agent,
            now=now,
            active_thread_id=active_thread_id,
            active_automation_id=args.active_automation_id,
            context_percent=args.context_percent,
            force_new_replacement=args.force_new_replacement,
            epic_title=args.epic_title,
            goal=args.goal,
            phase=args.phase,
            next_phase=args.next_phase,
            repository=args.repository,
            stream_epic=args.stream_epic,
            stream_epic_url=args.stream_epic_url,
            github_issue_number=args.issue_number,
            github_issue_url=args.issue_url,
            semantic_title=args.semantic_title,
            task_family=args.task_family,
            role=args.role,
            terminal_goal=args.terminal_goal,
            harness=args.harness or ("codex-app" if os.environ.get("LEARN_UKRAINIAN_CLAUDEX_RUN_ID") else None),
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "state_file": rel(state_path, state_root)}, indent=2))
        return 2
    replacement = prepared_state["replacement"]
    bootstrap_path = repo_local_path(state_root, Path(replacement["bootstrap_prompt_path"]))
    handoff_path = repo_local_path(state_root, Path(replacement["handoff_path"]))
    snapshot = gather_snapshot(repo_root, args.monitor_base_url)
    # Recompute after the slower Monitor/GitHub reads so the lease binds the
    # checkout as close as possible to the atomic packet write below.
    snapshot["git"] = gather_git_state(repo_root)
    try:
        replacement["source_checkout"] = source_checkout_binding(snapshot["git"])
    except ValueError as exc:
        print(
            json.dumps(
                {
                    "error": f"checkout continuity failed: {exc}",
                    "state_file": rel(state_path, state_root),
                    "old_automation_ready_to_delete": False,
                },
                indent=2,
            )
        )
        return 2
    prompt = render_bootstrap_prompt(
        snapshot,
        prepared_state,
        agent=agent,
        router_path=Path(router_file),
        handoff_path=Path(replacement["handoff_path"]),
        role_handoff_path=Path(role_handoff_file),
        state_root=state_root,
        context_threshold=args.context_threshold,
    )
    handoff_md = render_current_markdown(
        snapshot,
        prepared_state,
        agent=agent,
        role_handoff_path=Path(role_handoff_file),
        state_root=state_root,
        context_threshold=args.context_threshold,
    )
    router_md = render_router_markdown(
        generated_at=snapshot["generated_at"],
        default_agent=DEFAULT_AGENT,
        agents=router_agents(agent),
    )

    if args.dry_run:
        prompt_bytes = prompt.encode("utf-8")
        output = {
            "dry_run": True,
            "agent": agent,
            "lineage_id": lineage_id,
            "rollover_id": replacement["rollover_id"],
            "state_file": rel(state_path, state_root),
            "bootstrap_file": rel(bootstrap_path, state_root),
            "handoff_file": rel(handoff_path, state_root),
            "thread_handoff_file": rel(handoff_path, state_root),
            "role_handoff_file": role_handoff_path.as_posix(),
            "router_file": router_path.as_posix(),
            "current_file": router_path.as_posix(),
            "would_write_router": bool(args.write_current),
            "old_automation_ready_to_delete": False,
            "semantic_snapshot_file": replacement["semantic_snapshot_path"],
            "strict_probe_file": replacement["strict_probe_path"],
            "strict_questions_file": replacement["strict_questions_path"],
            "strict_answers_file": replacement["strict_answers_path"],
            "strict_verdict_file": replacement["strict_verdict_path"],
            "canary_proof_file": replacement["canary_proof_path"],
            "intended_title": replacement["display"]["title"],
            "title_source": replacement["display"]["title_source"],
            "identity": replacement["identity"],
            "title_transition": replacement["title_transition"],
            "identity_receipt_file": replacement["identity_receipt_path"],
            "native_lifecycle": replacement.get("native_lifecycle"),
            "bootstrap_prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
            "bootstrap_prompt_bytes": len(prompt_bytes),
        }
        print(json.dumps(output, indent=2))
        return 0

    native_plan = replacement.get("native_lifecycle")
    supersedes: dict[str, str] | None = None
    if args.force_new_replacement and previous_replacement.get("status") in {"pending_start", "resumed"}:
        previous_native = previous_replacement.get("native_lifecycle")
        if isinstance(previous_native, dict) != isinstance(native_plan, dict):
            print(
                json.dumps(
                    {
                        "error": "force-new-replacement cannot change native title-adapter capability",
                        "state_file": rel(state_path, state_root),
                        "old_automation_ready_to_delete": False,
                    },
                    indent=2,
                )
            )
            return 2
        if isinstance(previous_native, dict) and isinstance(native_plan, dict):
            supersedes = {
                "family_id": str(previous_native.get("family_id") or ""),
                "operation_id": str(previous_native.get("operation_id") or ""),
                "rollover_id": str(previous_replacement.get("rollover_id") or ""),
            }
            try:
                task_family_rollover.assert_transition_supersedable(
                    repo_root=state_root,
                    family_id=supersedes["family_id"],
                    operation_id=supersedes["operation_id"],
                    lineage_id=lineage_id,
                    generation=int(previous_replacement["generation"]),
                    source_thread_id=prepared_state["active"]["thread_id"],
                    successor_rollover_id=replacement["rollover_id"],
                    successor_operation_id=native_plan["operation_id"],
                    expected_rollover_id=supersedes["rollover_id"],
                )
            except (KeyError, OSError, TypeError, ValueError) as exc:
                print(
                    json.dumps(
                        {
                            "error": f"existing native rollover intent cannot be safely superseded: {exc}",
                            "recovery": "If the immutable plan belongs to an older packet, run repair-native-intent for the current exact lease.",
                            "state_file": rel(state_path, state_root),
                            "old_automation_ready_to_delete": False,
                        },
                        indent=2,
                    )
                )
                return 2
        else:
            replacement["supersedes"] = {
                "rollover_id": previous_replacement.get("rollover_id"),
                "resolution": "explicit force-new-replacement on a non-native title adapter",
            }

    write_text_atomic(bootstrap_path, prompt)
    write_text_atomic(handoff_path, handoff_md)
    try:
        native_transition = None
        if isinstance(native_plan, dict):
            native_transition = task_family_rollover.prepare_transition(
                repo_root=state_root,
                agent=agent,
                lineage_id=lineage_id,
                rollover_id=replacement["rollover_id"],
                generation=replacement["generation"],
                source_thread_id=prepared_state["active"]["thread_id"],
                intended_title=replacement["display"]["title"],
                title_source=replacement["display"]["title_source"],
                bootstrap_prompt_path=replacement["bootstrap_prompt_path"],
                supersedes=supersedes,
                task_identity_envelope=replacement["identity"],
            )
        if supersedes is not None:
            pending_state = dict(prepared_state)
            pending_replacement = dict(replacement)
            pending_native = dict(pending_replacement["native_lifecycle"])
            pending_native["status"] = "supersession_pending"
            pending_native["supersedes"] = dict(supersedes)
            pending_replacement["native_lifecycle"] = pending_native
            pending_state["replacement"] = pending_replacement
            write_rollover_state(state_path, state_root, pending_state, already_locked=True)
            task_family_rollover.supersede_unexecuted_transition(
                repo_root=state_root,
                family_id=supersedes["family_id"],
                operation_id=supersedes["operation_id"],
                lineage_id=lineage_id,
                generation=int(previous_replacement["generation"]),
                source_thread_id=prepared_state["active"]["thread_id"],
                successor_rollover_id=replacement["rollover_id"],
                successor_operation_id=replacement["native_lifecycle"]["operation_id"],
                evidence="Forced prepare superseded an untouched exact native intent after durable preflight.",
                expected_rollover_id=supersedes["rollover_id"],
            )
            task_family_rollover.activate_superseding_transition(
                repo_root=state_root,
                family_id=replacement["native_lifecycle"]["family_id"],
                operation_id=replacement["native_lifecycle"]["operation_id"],
            )
            native_plan["supersedes"] = dict(supersedes)
            native_transition["status"] = "awaiting_native_create"
            native_transition["superseded"] = dict(supersedes)
        write_rollover_state(state_path, state_root, prepared_state, already_locked=True)
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": f"native rollover intent persistence failed: {exc}",
                    "state_file": rel(state_path, state_root),
                    "old_automation_ready_to_delete": False,
                    "recovery": "Retry the exact repair or prepare command; never invoke native create while supersession is pending.",
                },
                indent=2,
            )
        )
        return 2

    wrote_router = False
    if args.write_current:
        write_text_atomic(router_path, router_md)
        wrote_router = True

    try:
        claudex_request = request_claudex_rollover(
            repo_root=repo_root,
            state_root=state_root,
            lineage_id=lineage_id,
            replacement=replacement,
        )
    except ValueError as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "state_file": rel(state_path, state_root),
                    "rollover_id": replacement["rollover_id"],
                    "old_automation_ready_to_delete": False,
                    "recovery": "The prepared handoff remains intact. Repair the supervisor identity or start the replacement manually; do not delete the lease.",
                },
                indent=2,
            )
        )
        return 2

    bundle_upload: dict[str, Any] = {"status": "not-requested"}
    if getattr(args, "stream", None):
        bundle_upload = _maybe_auto_upload_bundle(
            args,
            repo_root=repo_root,
            state_root=state_root,
            agent=agent,
            state=prepared_state,
        )

    if agent == "claude" or agent.startswith("claude-"):
        # The packet is sealed and every fallible prepare step (including the
        # Claudex rollover request above) has already succeeded: only now is
        # it safe for this predecessor's terminal mutating action to
        # cooperatively release its thread-lease slot through the same
        # identity-gated path a SessionEnd hook would use, so the replacement
        # thread's future claim never has to wait out a stale lease. This
        # MUST stay the last fallible-free step in prepare — releasing any
        # earlier would drop mutual exclusion while a later step could still
        # fail and leave the predecessor running with no lease held. Release
        # itself is best-effort and never fatal to prepare: a session whose
        # process identity cannot be reconfirmed here simply leaves the lease
        # for claim_thread_lease's pid-liveness check to reclaim later.
        try:
            seal_release_result = release_thread_lease(
                state_root=state_root, agent=agent, current_thread_id=active_thread_id, now=now
            )
            if seal_release_result.get("status") not in {"released", "noop"}:
                print(
                    f"WARNING: unexpected thread-lease release status at prepare seal for "
                    f"agent {agent!r}: {seal_release_result}",
                    file=sys.stderr,
                )
        except (OSError, ValueError) as exc:
            print(
                f"WARNING: thread-lease release at prepare seal failed for agent {agent!r}: {exc}",
                file=sys.stderr,
            )

    output = {
        "agent": agent,
        "lineage_id": lineage_id,
        "rollover_id": replacement["rollover_id"],
        "runtime_path": replacement["runtime_path"],
        "state_file": rel(state_path, state_root),
        "bootstrap_file": rel(bootstrap_path, state_root),
        "handoff_file": rel(handoff_path, state_root),
        "thread_handoff_file": rel(handoff_path, state_root),
        "role_handoff_file": rel(role_handoff_path, repo_root),
        "router_file": rel(router_path, repo_root) if wrote_router else None,
        "current_file": rel(router_path, repo_root) if wrote_router else None,
        "replacement_status": prepared_state["replacement"]["status"],
        "old_automation_ready_to_delete": prepared_state["cleanup"]["old_automation_ready_to_delete"],
        "semantic_snapshot_file": replacement["semantic_snapshot_path"],
        "strict_probe_file": replacement["strict_probe_path"],
        "strict_questions_file": replacement["strict_questions_path"],
        "strict_answers_file": replacement["strict_answers_path"],
        "strict_verdict_file": replacement["strict_verdict_path"],
        "canary_proof_file": replacement["canary_proof_path"],
        "intended_title": replacement["display"]["title"],
        "title_source": replacement["display"]["title_source"],
        "identity": replacement["identity"],
        "title_transition": replacement["title_transition"],
        "identity_receipt_file": replacement["identity_receipt_path"],
        "native_lifecycle": native_transition,
        "next_native_action": (
            {
                "tool": "create_thread",
                "title_after_create": replacement["display"]["title"],
                "source_thread_id": prepared_state["active"]["thread_id"],
                "native_title_confirmation_required": True,
            }
            if isinstance(native_plan, dict)
            else {
                "tool": "bind-replacement",
                "native_title_mutation_supported": False,
                "visible_title_carriers": list(task_identity.FALLBACK_CARRIERS),
            }
        ),
    }
    if claudex_request is not None:
        output["claudex_rollover_request"] = claudex_request
    output["bundle_upload"] = bundle_upload
    print(json.dumps(output, indent=2))
    return 0


def _native_command_context(
    args: argparse.Namespace,
) -> tuple[Path, Path, str, Path, dict[str, Any], dict[str, Any]]:
    repo_root, state_root = resolve_roots(args.repo_root)
    agent = normalize_agent_name(args.agent)
    if not args.lineage_id and not args.state_file:
        raise ValueError("--lineage-id or --state-file is required to locate an isolated rollover")
    state_path = resolve_state_path(
        repo_root=repo_root,
        state_root=state_root,
        supplied_state_file=args.state_file,
        default_path=default_state_path(agent, args.lineage_id) if args.lineage_id else None,
    )
    state = load_state(state_path)
    state_error = state_error_payload(state, state_path, state_root)
    if state_error:
        raise ValueError(state_error["error"])
    state, migrated = normalize_identity_state(state, agent=agent, now=utc_now())
    if migrated:
        write_rollover_state(state_path, state_root, state, already_locked=True)
    replacement = state.get("replacement") or {}
    if replacement.get("rollover_id") != args.rollover_id:
        raise ValueError("--rollover-id does not match the isolated rollover")
    native = replacement.get("native_lifecycle")
    if not isinstance(native, dict) or not native.get("family_id") or not native.get("operation_id"):
        raise ValueError("rollover has no durable native lifecycle plan")
    generation = replacement.get("generation")
    lineage_id = replacement.get("lineage_id")
    if not isinstance(generation, int) or generation < 1 or not isinstance(lineage_id, str):
        raise ValueError("rollover native lifecycle identity is malformed")
    expected_family_id, expected_operation_id = task_family_rollover.transition_identity(
        lineage_id=lineage_id,
        generation=generation,
        rollover_id=replacement["rollover_id"],
    )
    if native.get("family_id") != expected_family_id or native.get("operation_id") != expected_operation_id:
        raise ValueError("rollover native lifecycle identity does not match its durable lineage")
    if native.get("status") == "supersession_pending":
        raise ValueError("rollover native intent supersession is pending; repair it before any native action")
    if native.get("source_thread_id") != (state.get("active") or {}).get("thread_id"):
        raise ValueError("rollover native predecessor does not match the active lease identity")
    task_family_rollover.assert_transition_context(
        repo_root=state_root,
        family_id=native["family_id"],
        operation_id=native["operation_id"],
        lineage_id=lineage_id,
        rollover_id=replacement["rollover_id"],
        generation=generation,
        source_thread_id=native["source_thread_id"],
    )
    bound_replacement_id = native.get("replacement_thread_id")
    resumed_replacement_id = replacement.get("resumed_thread_id") or replacement.get("thread_id")
    if bound_replacement_id and resumed_replacement_id and bound_replacement_id != resumed_replacement_id:
        raise ValueError("rollover native replacement does not match the resumed lease identity")
    return repo_root, state_root, agent, state_path, state, native


def _identity_command_context(
    args: argparse.Namespace,
) -> tuple[Path, Path, str, Path, dict[str, Any], dict[str, Any]]:
    repo_root, state_root = resolve_roots(args.repo_root)
    agent = normalize_agent_name(args.agent)
    if not args.lineage_id and not args.state_file:
        raise ValueError("--lineage-id or --state-file is required to locate an isolated rollover")
    state_path = resolve_state_path(
        repo_root=repo_root,
        state_root=state_root,
        supplied_state_file=args.state_file,
        default_path=default_state_path(agent, args.lineage_id) if args.lineage_id else None,
    )
    state = load_state(state_path)
    state_error = state_error_payload(state, state_path, state_root)
    if state_error:
        raise ValueError(state_error["error"])
    state, migrated = normalize_identity_state(state, agent=agent, now=utc_now())
    replacement = state.get("replacement") or {}
    if replacement.get("rollover_id") != args.rollover_id:
        raise ValueError("--rollover-id does not match the isolated rollover")
    if migrated:
        write_rollover_state(state_path, state_root, state, already_locked=True)
    return repo_root, state_root, agent, state_path, state, replacement


def cmd_repair_native_intent(args: argparse.Namespace) -> int:
    lock_path = _rollover_mutation_lock_path(args)
    if lock_path is None:
        return _cmd_repair_native_intent_locked(args)
    with task_family_advisory_lock(lock_path):
        return _cmd_repair_native_intent_locked(args)


def _cmd_repair_native_intent_locked(args: argparse.Namespace) -> int:
    """Reconcile one legacy same-generation receipt collision without native mutation."""
    try:
        repo_root, state_root = resolve_roots(args.repo_root)
        agent = normalize_agent_name(args.agent)
        if not args.lineage_id and not args.state_file:
            raise ValueError("--lineage-id or --state-file is required to locate an isolated rollover")
        state_path = resolve_state_path(
            repo_root=repo_root,
            state_root=state_root,
            supplied_state_file=args.state_file,
            default_path=default_state_path(agent, args.lineage_id) if args.lineage_id else None,
        )
        state = load_state(state_path)
        state_error = state_error_payload(state, state_path, state_root)
        if state_error:
            raise ValueError(state_error["error"])
        state, changed = normalize_identity_state(state, agent=agent, now=utc_now())
        if changed:
            write_rollover_state(state_path, state_root, state, already_locked=True)
        replacement = dict(state.get("replacement") or {})
        if replacement.get("rollover_id") != args.rollover_id:
            raise ValueError("--rollover-id does not match the isolated rollover")
        if replacement.get("status") != "pending_start":
            raise ValueError("native-intent repair is limited to an unconfirmed pending_start replacement")
        lineage_id = replacement.get("lineage_id")
        generation = replacement.get("generation")
        active = state.get("active") or {}
        source_thread_id = active.get("thread_id")
        display = replacement.get("display")
        native = replacement.get("native_lifecycle")
        if not isinstance(native, dict) and isinstance(replacement.get("native_lifecycle_retired"), dict):
            raise ValueError(
                "native plan was retired as unsatisfiable for a non-native harness; "
                "no native-intent repair applies — bind the replacement and resume instead"
            )
        if (
            not isinstance(lineage_id, str)
            or not isinstance(generation, int)
            or generation < 1
            or not isinstance(source_thread_id, str)
            or not source_thread_id.strip()
            or not isinstance(display, dict)
            or not isinstance(native, dict)
        ):
            raise ValueError("rollover lease lacks exact identity or display metadata required for repair")
        if native.get("source_thread_id") != source_thread_id or native.get("replacement_thread_id") is not None:
            raise ValueError("native-intent repair refuses a bound or mismatched replacement")

        successor_family_id, successor_operation_id = task_family_rollover.transition_identity(
            lineage_id=lineage_id,
            generation=generation,
            rollover_id=replacement["rollover_id"],
        )
        legacy_family_id, legacy_operation_id = task_family_rollover.legacy_transition_identity(
            lineage_id=lineage_id,
            generation=generation,
        )
        native_supersedes = native.get("supersedes")
        if native.get("family_id") == successor_family_id and native.get("operation_id") == successor_operation_id:
            if not isinstance(native_supersedes, dict):
                raise ValueError("packet-specific transition lacks its exact superseded receipt reference")
            supersedes = {
                "family_id": str(native_supersedes.get("family_id") or ""),
                "operation_id": str(native_supersedes.get("operation_id") or ""),
                "rollover_id": str(native_supersedes.get("rollover_id") or ""),
            }
        elif native.get("family_id") == legacy_family_id and native.get("operation_id") == legacy_operation_id:
            proof = task_family_rollover.assert_transition_supersedable(
                repo_root=state_root,
                family_id=legacy_family_id,
                operation_id=legacy_operation_id,
                lineage_id=lineage_id,
                generation=generation,
                source_thread_id=source_thread_id,
                successor_rollover_id=replacement["rollover_id"],
                successor_operation_id=successor_operation_id,
            )
            supersedes = {
                "family_id": legacy_family_id,
                "operation_id": legacy_operation_id,
                "rollover_id": str(proof["plan"]["rollover_id"]),
            }
        else:
            raise ValueError("lease does not reference the exact legacy or packet-specific native intent")

        if supersedes["rollover_id"] == replacement["rollover_id"]:
            raise ValueError("legacy receipt already belongs to the current packet; no supersession repair is valid")
        candidate_native = {
            "family_id": successor_family_id,
            "operation_id": successor_operation_id,
            "source_thread_id": source_thread_id,
            "replacement_thread_id": None,
            "status": "supersession_pending",
            "supersedes": dict(supersedes),
        }
        candidate_replacement = dict(replacement)
        candidate_replacement["native_lifecycle"] = candidate_native
        candidate_state = dict(state)
        candidate_state["replacement"] = candidate_replacement
        validated, validation_error = validate_live_lease(candidate_state, agent=agent, state_path=state_path)
        if validation_error or validated is None:
            raise ValueError(f"repaired lease validation failed: {validation_error or 'unknown error'}")

        transition = task_family_rollover.prepare_transition(
            repo_root=state_root,
            agent=agent,
            lineage_id=lineage_id,
            rollover_id=replacement["rollover_id"],
            generation=generation,
            source_thread_id=source_thread_id,
            intended_title=display["title"],
            title_source=display["title_source"],
            bootstrap_prompt_path=replacement["bootstrap_prompt_path"],
            supersedes=supersedes,
            task_identity_envelope=replacement["identity"],
        )
        write_rollover_state(state_path, state_root, candidate_state, already_locked=True)
        superseded = task_family_rollover.supersede_unexecuted_transition(
            repo_root=state_root,
            family_id=supersedes["family_id"],
            operation_id=supersedes["operation_id"],
            lineage_id=lineage_id,
            generation=generation,
            source_thread_id=source_thread_id,
            successor_rollover_id=replacement["rollover_id"],
            successor_operation_id=successor_operation_id,
            evidence=args.evidence,
            expected_rollover_id=supersedes["rollover_id"],
        )
        activated = task_family_rollover.activate_superseding_transition(
            repo_root=state_root,
            family_id=successor_family_id,
            operation_id=successor_operation_id,
        )
        candidate_native["status"] = "awaiting_native_create"
        candidate_replacement["native_lifecycle"] = candidate_native
        candidate_state["replacement"] = candidate_replacement
        candidate_state["updated_at"] = isoformat_z(utc_now())
        write_rollover_state(state_path, state_root, candidate_state, already_locked=True)
        _, final_error = validate_live_lease(candidate_state, agent=agent, state_path=state_path)
        if final_error:
            raise ValueError(f"persisted repaired lease failed validation: {final_error}")
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "action": "repair-native-intent",
                    "old_automation_ready_to_delete": False,
                },
                indent=2,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "status": "native_intent_repaired",
                "lineage_id": lineage_id,
                "rollover_id": replacement["rollover_id"],
                "source_thread_id": source_thread_id,
                "superseded": superseded,
                "native_lifecycle": {
                    **transition,
                    "status": activated["status"],
                    "supersedes": supersedes,
                },
                "old_automation_ready_to_delete": False,
            },
            indent=2,
        )
    )
    return 0


def _write_native_status(
    state_path: Path,
    state_root: Path,
    state: dict[str, Any],
    *,
    status: str,
    replacement_thread_id: str | None = None,
) -> None:
    replacement = dict(state["replacement"])
    native = dict(replacement["native_lifecycle"])
    native["status"] = status
    if replacement_thread_id is not None:
        native["replacement_thread_id"] = replacement_thread_id
    replacement["native_lifecycle"] = native
    state["replacement"] = replacement
    state["updated_at"] = isoformat_z(utc_now())
    write_rollover_state(state_path, state_root, state, already_locked=True)


def _record_identity_title_ack(
    state: dict[str, Any], *, replacement_task_id: str, succeeded: bool, evidence: str, error: str
) -> None:
    replacement = dict(state["replacement"])
    identity, transition = task_identity.record_title_acknowledgement(
        replacement["identity"],
        replacement["title_transition"],
        replacement_task_id=replacement_task_id,
        succeeded=succeeded,
        evidence=evidence,
        error=error or "Native title adapter reported failure.",
        now=isoformat_z(utc_now()),
    )
    replacement["identity"] = identity
    replacement["title_transition"] = transition
    state["replacement"] = replacement


def _record_identity_title_readback(
    state: dict[str, Any], *, succeeded: bool, evidence: str, error: str
) -> None:
    replacement = dict(state["replacement"])
    identity = task_identity.validate_identity(replacement["identity"])
    replacement_task_id = identity.get("replacement_task_id")
    if not isinstance(replacement_task_id, str):
        raise ValueError("native title readback has no exact replacement binding")
    identity, transition = task_identity.record_title_readback(
        identity,
        replacement["title_transition"],
        replacement_task_id=replacement_task_id,
        observed_title=identity["visible_title"] if succeeded else None,
        succeeded=succeeded,
        evidence=evidence,
        error=error or "Native title readback did not confirm the exact visible title.",
        now=isoformat_z(utc_now()),
    )
    replacement["identity"] = identity
    replacement["title_transition"] = transition
    state["replacement"] = replacement


def cmd_bind_replacement(args: argparse.Namespace) -> int:
    lock_path = _rollover_mutation_lock_path(args)
    if lock_path is None:
        return _cmd_bind_replacement_locked(args)
    with task_family_advisory_lock(lock_path):
        return _cmd_bind_replacement_locked(args)


def _cmd_bind_replacement_locked(args: argparse.Namespace) -> int:
    """Bind an exact replacement and persist an honest non-native title fallback."""
    try:
        _, state_root, _, state_path, state, replacement = _identity_command_context(args)
        identity = task_identity.validate_identity(replacement.get("identity") or {})
        transition = task_identity.validate_title_transition(
            replacement.get("title_transition") or {}, identity
        )
        if transition["native_title_supported"]:
            raise ValueError("native title adapter requires register-created and exact title readback")
        bound_identity, bound_transition = task_identity.bind_replacement(
            identity,
            transition,
            replacement_task_id=args.replacement_task_id,
            evidence=args.evidence,
            now=isoformat_z(utc_now()),
        )
        updated_replacement = dict(replacement)
        updated_replacement["identity"] = bound_identity
        updated_replacement["title_transition"] = bound_transition
        state["replacement"] = updated_replacement
        state["updated_at"] = isoformat_z(utc_now())
        write_rollover_state(state_path, state_root, state, already_locked=True)
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "action": "bind-replacement"}, indent=2))
        return 2
    print(
        json.dumps(
            {
                "status": "fallback_recorded",
                "replacement_task_id": bound_identity["replacement_task_id"],
                "visible_title": bound_identity["visible_title"],
                "native_title_mutation_supported": False,
                "fallback_receipt": bound_transition["fallback_receipt"],
                "identity_receipt_file": updated_replacement["identity_receipt_path"],
            },
            indent=2,
        )
    )
    return 0


def cmd_register_created(args: argparse.Namespace) -> int:
    lock_path = _rollover_mutation_lock_path(args)
    if lock_path is None:
        return _cmd_register_created_locked(args)
    with task_family_advisory_lock(lock_path):
        return _cmd_register_created_locked(args)


def _cmd_register_created_locked(args: argparse.Namespace) -> int:
    state_root: Path | None = None
    native: dict[str, Any] | None = None
    try:
        _, state_root, _, state_path, state, native = _native_command_context(args)
        db_path = task_family_rollover.resolve_db(args.db)
        source_id = native["source_thread_id"]
        replacement_id = args.replacement_thread_id.strip()
        source = task_family_codex_state.read_thread_record(db_path, task_id=source_id)
        replacement = task_family_codex_state.read_thread_record(db_path, task_id=replacement_id)
        binding = task_family_rollover.bind_replacement(
            repo_root=state_root,
            family_id=native["family_id"],
            operation_id=native["operation_id"],
            source=source,
            replacement=replacement,
            db_path=db_path,
            evidence=args.evidence,
        )
        lease_replacement = dict(state["replacement"])
        bound_identity, bound_transition = task_identity.bind_replacement(
            lease_replacement["identity"],
            lease_replacement["title_transition"],
            replacement_task_id=replacement_id,
            evidence=args.evidence,
            now=isoformat_z(utc_now()),
        )
        if binding["intended_title"] != bound_identity["visible_title"]:
            raise ValueError("native rollover plan title does not match the canonical task identity")
        lease_replacement["identity"] = bound_identity
        lease_replacement["title_transition"] = bound_transition
        state["replacement"] = lease_replacement
        _write_native_status(
            state_path,
            state_root,
            state,
            status="replacement_created_bound",
            replacement_thread_id=replacement_id,
        )
    except (OSError, ValueError, task_family_codex_state.CodexStateError) as exc:
        blocker_error: str | None = None
        if state_root is not None and native is not None:
            try:
                task_family_rollover.record_blocker(
                    repo_root=state_root,
                    family_id=native["family_id"],
                    operation_id=native["operation_id"],
                    action="create",
                    error=str(exc),
                    evidence=getattr(args, "evidence", "native create binding") or "native create binding",
                )
            except (OSError, ValueError) as blocker_exc:
                blocker_error = str(blocker_exc)
        payload = {"error": str(exc), "action": "register-created"}
        if blocker_error is not None:
            payload["receipt_error"] = blocker_error
        print(json.dumps(payload, indent=2))
        return 2
    print(
        json.dumps(
            {
                "status": "replacement_created_bound",
                "source_thread_id": binding["source_thread_id"],
                "replacement_thread_id": binding["replacement_thread_id"],
                "intended_title": binding["intended_title"],
                "identity": bound_identity,
                "title_transition": bound_transition,
                "relations": binding["relations"],
            },
            indent=2,
        )
    )
    return 0


def cmd_native_action(args: argparse.Namespace) -> int:
    lock_path = _rollover_mutation_lock_path(args)
    if lock_path is None:
        return _cmd_native_action_locked(args)
    with task_family_advisory_lock(lock_path):
        return _cmd_native_action_locked(args)


def _cmd_native_action_locked(args: argparse.Namespace) -> int:
    try:
        _, state_root, _, state_path, state, native = _native_command_context(args)
        if args.action == "create":
            result = task_family_rollover.request_create_action(
                repo_root=state_root,
                family_id=native["family_id"],
                operation_id=native["operation_id"],
            )
        else:
            try:
                db_path = task_family_rollover.resolve_db(args.db)
            except (OSError, ValueError, task_family_codex_state.CodexStateError) as exc:
                result = task_family_rollover.record_blocker(
                    repo_root=state_root,
                    family_id=native["family_id"],
                    operation_id=native["operation_id"],
                    action=args.action,
                    error=str(exc),
                    evidence="Codex DB discovery preflight",
                )
            else:
                result = task_family_rollover.request_action(
                    repo_root=state_root,
                    family_id=native["family_id"],
                    operation_id=native["operation_id"],
                    action=args.action,
                    db_path=db_path,
                    state=state if args.action == "archive" else None,
                    source_status=args.source_status,
                    pin_state=args.pin_state,
                    evidence=args.evidence,
                )
        if args.action == "title":
            identity = task_identity.validate_identity(state["replacement"]["identity"])
            if result.get("needs_native_action"):
                expected_arguments = {
                    "threadId": identity["replacement_task_id"],
                    "title": identity["visible_title"],
                }
                if result.get("tool") != "set_thread_title" or result.get("arguments") != expected_arguments:
                    raise ValueError("native title action does not target the exact task identity envelope")
            elif result.get("ok"):
                _record_identity_title_readback(
                    state,
                    succeeded=True,
                    evidence="Native title preflight/readback reconciled the exact replacement.",
                    error="",
                )
            else:
                _record_identity_title_readback(
                    state,
                    succeeded=False,
                    evidence="Native title preflight/readback failed for the exact replacement.",
                    error=str(result.get("error") or "Native title reconciliation failed."),
                )
        _write_native_status(state_path, state_root, state, status=str(result["status"]))
    except (OSError, ValueError, task_family_codex_state.CodexStateError) as exc:
        print(json.dumps({"error": str(exc), "action": args.action}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 2


def cmd_record_native_result(args: argparse.Namespace) -> int:
    lock_path = _rollover_mutation_lock_path(args)
    if lock_path is None:
        return _cmd_record_native_result_locked(args)
    with task_family_advisory_lock(lock_path):
        return _cmd_record_native_result_locked(args)


def _cmd_record_native_result_locked(args: argparse.Namespace) -> int:
    try:
        _, state_root, _, state_path, state, native = _native_command_context(args)
        result = task_family_rollover.record_native_result(
            repo_root=state_root,
            family_id=native["family_id"],
            operation_id=native["operation_id"],
            action=args.action,
            succeeded=args.succeeded,
            evidence=args.evidence,
            error=args.error,
        )
        if args.action == "title":
            _record_identity_title_ack(
                state,
                replacement_task_id=str(result["resource_id"]),
                succeeded=args.succeeded,
                evidence=args.evidence,
                error=args.error,
            )
        _write_native_status(state_path, state_root, state, status=str(result["status"]))
    except (OSError, ValueError, task_family_codex_state.CodexStateError) as exc:
        print(json.dumps({"error": str(exc), "action": args.action}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 2


def cmd_reconcile_native(args: argparse.Namespace) -> int:
    lock_path = _rollover_mutation_lock_path(args)
    if lock_path is None:
        return _cmd_reconcile_native_locked(args)
    with task_family_advisory_lock(lock_path):
        return _cmd_reconcile_native_locked(args)


def _cmd_reconcile_native_locked(args: argparse.Namespace) -> int:
    try:
        _, state_root, _, state_path, state, native = _native_command_context(args)
        db_path = task_family_rollover.resolve_db(args.db)
        result = task_family_rollover.reconcile_action(
            repo_root=state_root,
            family_id=native["family_id"],
            operation_id=native["operation_id"],
            action=args.action,
            db_path=db_path,
        )
        if args.action == "title":
            _record_identity_title_readback(
                state,
                succeeded=bool(result.get("ok")),
                evidence="Native DB readback for the exact replacement title.",
                error=str(result.get("error") or ""),
            )
        _write_native_status(state_path, state_root, state, status=str(result["status"]))
    except (OSError, ValueError, task_family_codex_state.CodexStateError) as exc:
        print(json.dumps({"error": str(exc), "action": args.action}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 2


def cmd_confirm_started(args: argparse.Namespace) -> int:
    lock_path = _rollover_mutation_lock_path(args)
    if lock_path is None:
        return _cmd_confirm_started_locked(args)
    with task_family_advisory_lock(lock_path):
        return _cmd_confirm_started_locked(args)


def _cmd_confirm_started_locked(args: argparse.Namespace) -> int:
    try:
        repo_root, state_root = resolve_roots(args.repo_root)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2
    agent = normalize_agent_name(args.agent)
    if not args.lineage_id and not args.state_file:
        print(
            json.dumps({"error": "--lineage-id or --state-file is required to locate an isolated rollover"}, indent=2)
        )
        return 2
    lineage_id = args.lineage_id
    try:
        state_path = resolve_state_path(
            repo_root=repo_root,
            state_root=state_root,
            supplied_state_file=args.state_file,
            default_path=default_state_path(agent, lineage_id) if lineage_id else None,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "agent": agent}, indent=2))
        return 2
    state = load_state(state_path)
    state_error = state_error_payload(state, state_path, state_root)
    if state_error:
        print(json.dumps(state_error, indent=2))
        return 2
    try:
        state, migrated = normalize_identity_state(state, agent=agent, now=utc_now())
        if migrated:
            write_rollover_state(state_path, state_root, state, already_locked=True)
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": f"task identity migration failed: {exc}"}, indent=2))
        return 2
    replacement = state.get("replacement") or {}
    if not replacement:
        print(json.dumps({"error": "run prepare first"}, indent=2))
        return 2
    if args.rollover_id != replacement.get("rollover_id"):
        print(json.dumps({"error": "--rollover-id does not match the isolated pending rollover"}, indent=2))
        return 2
    try:
        require_checkout_continuity(replacement, repo_root)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2
    expected_proof = repo_local_path(state_root, Path(state["replacement"]["canary_proof_path"]))
    try:
        supplied_proof = repo_local_path(state_root, args.canary_proof)
        supplied_strict_probe = repo_local_path(state_root, args.strict_probe)
        supplied_strict_verdict = repo_local_path(state_root, args.strict_verdict)
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "agent": agent}, indent=2))
        return 2
    if supplied_proof != expected_proof:
        print(json.dumps({"error": "--canary-proof must be the proof path reserved by this rollover"}, indent=2))
        return 2
    try:
        confirmed = confirm_started(
            state,
            new_thread_id=args.new_thread_id,
            new_automation_id=args.new_automation_id,
            confirmed_by=args.confirmed_by,
            now=utc_now(),
            canary_proof=supplied_proof,
            strict_probe=supplied_strict_probe,
            strict_verdict=supplied_strict_verdict,
            state_root=state_root,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2
    write_rollover_state(state_path, state_root, confirmed, already_locked=True)
    bundle_upload = _maybe_auto_upload_bundle(
        args,
        repo_root=repo_root,
        state_root=state_root,
        agent=agent,
        state=confirmed,
    ) if getattr(args, "stream", None) else {"status": "not-requested"}
    print(
        json.dumps(
            {
                "agent": agent,
                "lineage_id": confirmed.get("lineage_id"),
                "rollover_id": confirmed["replacement"]["rollover_id"],
                "state_file": rel(state_path, state_root),
                "replacement_status": confirmed["replacement"]["status"],
                "replacement_thread_id": confirmed["replacement"]["thread_id"],
                "predecessor_thread_id": confirmed["active"]["thread_id"],
                "native_lifecycle": confirmed["replacement"].get("native_lifecycle"),
                "identity": confirmed["replacement"]["identity"],
                "title_transition": confirmed["replacement"]["title_transition"],
                "identity_receipt_file": confirmed["replacement"]["identity_receipt_path"],
                "old_automation_ready_to_delete": confirmed["cleanup"]["old_automation_ready_to_delete"],
                "next_native_action": "Run native-action --action archive with authoritative idle and unpinned app evidence; unknown state preserves the predecessor.",
                "bundle_upload": bundle_upload,
            },
            indent=2,
        )
    )
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    lock_path = _rollover_mutation_lock_path(args)
    if lock_path is None:
        return _cmd_resume_locked(args)
    with task_family_advisory_lock(lock_path):
        return _cmd_resume_locked(args)


def _cmd_resume_locked(args: argparse.Namespace) -> int:
    try:
        repo_root, state_root = resolve_roots(args.repo_root)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2
    agent = normalize_agent_name(args.agent)
    if not args.lineage_id and not args.state_file:
        print(
            json.dumps({"error": "--lineage-id or --state-file is required to locate an isolated rollover"}, indent=2)
        )
        return 2
    try:
        state_path = resolve_state_path(
            repo_root=repo_root,
            state_root=state_root,
            supplied_state_file=args.state_file,
            default_path=default_state_path(agent, args.lineage_id) if args.lineage_id else None,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "agent": agent}, indent=2))
        return 2
    state = load_state(state_path)
    state_error = state_error_payload(state, state_path, state_root)
    if state_error:
        print(json.dumps(state_error, indent=2))
        return 2
    try:
        state, migrated = normalize_identity_state(state, agent=agent, now=utc_now())
        if migrated:
            write_rollover_state(state_path, state_root, state, already_locked=True)
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": f"task identity migration failed: {exc}"}, indent=2))
        return 2
    try:
        require_checkout_continuity(state.get("replacement") or {}, repo_root)
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "state_file": rel(state_path, state_root)}, indent=2))
        return 2
    try:
        resumed = resume_state(
            state,
            rollover_id=args.rollover_id,
            replacement_thread_id=args.replacement_thread_id,
            now=utc_now(),
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "state_file": rel(state_path, state_root)}, indent=2))
        return 2
    write_rollover_state(state_path, state_root, resumed, already_locked=True)
    replacement = resumed["replacement"]
    print(
        json.dumps(
            {
                "agent": agent,
                "lineage_id": resumed.get("lineage_id"),
                "rollover_id": replacement["rollover_id"],
                "replacement_thread_id": replacement["resumed_thread_id"],
                "canary_proof_file": replacement["canary_proof_path"],
                "semantic_snapshot_file": replacement["semantic_snapshot_path"],
                "strict_probe_file": replacement["strict_probe_path"],
                "strict_answers_file": replacement["strict_answers_path"],
                "strict_verdict_file": replacement["strict_verdict_path"],
                "status": replacement["status"],
                "identity": replacement["identity"],
                "title_transition": replacement["title_transition"],
                "identity_receipt_file": replacement["identity_receipt_path"],
            },
            indent=2,
        )
    )
    return 0


def _wrapper_packet_context(
    args: argparse.Namespace,
) -> tuple[Path, Path, str, Path, dict[str, Any], dict[str, Any]] | None:
    """Load one exact rollover packet for the compact replacement wrappers."""
    try:
        repo_root, state_root = resolve_roots(args.repo_root)
        agent = normalize_agent_name(args.agent)
        if not args.lineage_id and not args.state_file:
            raise ValueError("--lineage-id or --state-file is required to locate an isolated rollover")
        state_path = resolve_state_path(
            repo_root=repo_root,
            state_root=state_root,
            supplied_state_file=args.state_file,
            default_path=default_state_path(agent, args.lineage_id) if args.lineage_id else None,
        )
        state = load_state(state_path)
        state_error = state_error_payload(state, state_path, state_root)
        if state_error:
            raise ValueError(str(state_error["error"]))
        replacement = state.get("replacement")
        if not isinstance(replacement, dict):
            raise ValueError("run prepare first")
        if args.rollover_id != replacement.get("rollover_id"):
            raise ValueError("--rollover-id does not match the isolated pending rollover")
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return None
    return repo_root, state_root, agent, state_path, state, replacement


def _print_questions_only(path: Path) -> None:
    """Return the answer-free recall view after a strict proof failure."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"questions_only_error": f"{type(exc).__name__}: {exc}"}, indent=2))
        return
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def cmd_bootstrap_replacement(args: argparse.Namespace) -> int:
    """Bind, resume, and create one answer-free semantic snapshot template."""
    packet = _wrapper_packet_context(args)
    if packet is None:
        return 2
    _repo_root, _state_root, _agent, _state_path, state, replacement = packet
    identity = replacement.get("identity") or {}
    already_resumed = (
        replacement.get("status") in {"resumed", "started"}
        and identity.get("replacement_task_id") == args.replacement_thread_id
        and replacement.get("resumed_thread_id") == args.replacement_thread_id
    )
    if not already_resumed:
        title_transition = replacement.get("title_transition") or {}
        if not title_transition.get("native_title_supported"):
            bind_args = argparse.Namespace(
                repo_root=args.repo_root,
                agent=args.agent,
                lineage_id=args.lineage_id,
                state_file=args.state_file,
                rollover_id=args.rollover_id,
                replacement_task_id=args.replacement_thread_id,
                evidence=args.evidence,
            )
            if cmd_bind_replacement(bind_args) != 0:
                return 2
        resume_args = argparse.Namespace(
            repo_root=args.repo_root,
            agent=args.agent,
            lineage_id=args.lineage_id,
            state_file=args.state_file,
            rollover_id=args.rollover_id,
            replacement_thread_id=args.replacement_thread_id,
        )
        if cmd_resume(resume_args) != 0:
            return 2
    packet = _wrapper_packet_context(args)
    if packet is None:
        return 2
    _repo_root, state_root, agent, state_path, state, replacement = packet
    snapshot_path = repo_local_path(state_root, Path(replacement["semantic_snapshot_path"]))
    template_path = snapshot_path.with_name("semantic-snapshot.template.json")
    template_created = False
    try:
        if not template_path.exists():
            write_json_atomic(template_path, semantic_snapshot_template(state, generated_at=utc_now()))
            template_created = True
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "action": "bootstrap-replacement"}, indent=2))
        return 2
    print(
        json.dumps(
            {
                "status": "bootstrap_ready",
                "agent": agent,
                "lineage_id": state["lineage_id"],
                "rollover_id": replacement["rollover_id"],
                "state_file": rel(state_path, state_root),
                "handoff_path": replacement["handoff_path"],
                "bootstrap_prompt_path": replacement["bootstrap_prompt_path"],
                "semantic_snapshot_template": rel(template_path, state_root),
                "semantic_snapshot_file": replacement["semantic_snapshot_path"],
                "strict_questions_file": replacement["strict_questions_path"],
                "strict_answers_file": replacement["strict_answers_path"],
                "template_created": template_created,
            },
            indent=2,
        )
    )
    return 0


def cmd_confirm_replacement(args: argparse.Namespace) -> int:
    """Run strict mint, recall questions, score, canary proof, and confirmation."""
    packet = _wrapper_packet_context(args)
    if packet is None:
        return 2
    _repo_root, state_root, agent, _state_path, state, replacement = packet
    if replacement.get("status") not in {"resumed", "started"}:
        print(json.dumps({"error": "bootstrap-replacement must resume this packet before confirmation"}, indent=2))
        return 2
    replacement_thread_id = args.replacement_thread_id or replacement.get("resumed_thread_id") or replacement.get("thread_id")
    if not isinstance(replacement_thread_id, str) or not replacement_thread_id.strip():
        print(json.dumps({"error": "bootstrap-replacement must resume this packet before confirmation"}, indent=2))
        return 2
    replacement_thread_id = replacement_thread_id.strip()
    resumed_thread_id = replacement.get("resumed_thread_id")
    if isinstance(resumed_thread_id, str) and resumed_thread_id != replacement_thread_id:
        print(json.dumps({"error": "--replacement-thread-id does not match the thread that resumed this rollover"}, indent=2))
        return 2
    if replacement.get("status") == "started":
        if replacement.get("thread_id") != replacement_thread_id:
            print(json.dumps({"error": "--replacement-thread-id does not match the already confirmed replacement"}, indent=2))
            return 2
        print(
            json.dumps(
                {
                    "status": "already_confirmed",
                    "agent": agent,
                    "lineage_id": state["lineage_id"],
                    "rollover_id": replacement["rollover_id"],
                    "replacement_thread_id": replacement_thread_id,
                    "old_automation_ready_to_delete": (state.get("cleanup") or {}).get(
                        "old_automation_ready_to_delete", False
                    ),
                },
                indent=2,
            )
        )
        return 0
    try:
        snapshot_path = repo_local_path(state_root, Path(replacement["semantic_snapshot_path"]))
        probe_path = repo_local_path(state_root, Path(replacement["strict_probe_path"]))
        questions_path = repo_local_path(state_root, Path(replacement["strict_questions_path"]))
        answers_path = repo_local_path(state_root, Path(replacement["strict_answers_path"]))
        verdict_path = repo_local_path(state_root, Path(replacement["strict_verdict_path"]))
        proof_path = repo_local_path(state_root, Path(replacement["canary_proof_path"]))
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "action": "confirm-replacement"}, indent=2))
        return 2

    mint_args = argparse.Namespace(snapshot=snapshot_path, facts=None, out=probe_path)
    if context_canary.cmd_mint(mint_args) != 0:
        return 2
    questions_args = argparse.Namespace(probe=probe_path, out=questions_path)
    if context_canary.cmd_questions(questions_args) != 0:
        return 2
    score_args = argparse.Namespace(
        probe=probe_path,
        answers=answers_path,
        expected_lineage_id=state["lineage_id"],
        expected_rollover_id=replacement["rollover_id"],
        verdict=verdict_path,
        threshold=0.75,
        pass_ratio=0.85,
        context_tokens=0,
        model="unknown",
        log=None,
    )
    if context_canary.cmd_score(score_args) != 0:
        _print_questions_only(questions_path)
        return 2
    canary_result = thread_handoff_canary.main(
        [
            "--rollover-id",
            replacement["rollover_id"],
            "--replacement-thread-id",
            replacement_thread_id,
            "--challenge",
            replacement["canary_challenge"],
            "--proof-file",
            proof_path.as_posix(),
        ]
    )
    if canary_result != 0:
        _print_questions_only(questions_path)
        return 2
    confirm_args = argparse.Namespace(
        repo_root=args.repo_root,
        agent=agent,
        lineage_id=args.lineage_id,
        state_file=args.state_file,
        rollover_id=args.rollover_id,
        new_thread_id=replacement_thread_id,
        new_automation_id=args.new_automation_id,
        canary_proof=proof_path,
        strict_probe=probe_path,
        strict_verdict=verdict_path,
        confirmed_by=args.confirmed_by,
        stream=getattr(args, "stream", None),
    )
    return cmd_confirm_started(confirm_args)


def cmd_check(args: argparse.Namespace) -> int:
    try:
        repo_root, state_root = resolve_roots(args.repo_root)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2
    agent = normalize_agent_name(args.agent)
    if not args.lineage_id and not args.state_file:
        print(
            json.dumps({"error": "--lineage-id or --state-file is required to locate an isolated rollover"}, indent=2)
        )
        return 2
    try:
        state_path = resolve_state_path(
            repo_root=repo_root,
            state_root=state_root,
            supplied_state_file=args.state_file,
            default_path=default_state_path(agent, args.lineage_id) if args.lineage_id else None,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "agent": agent}, indent=2))
        return 2
    state = load_state(state_path)
    facts, warnings = check_state(
        state,
        now=utc_now(),
        stale_after=timedelta(hours=args.stale_hours),
        context_percent=args.context_percent,
        context_threshold=args.context_threshold,
    )
    payload = {"agent": agent, "facts": facts, "warnings": warnings, "state_file": rel(state_path, state_root)}
    print(json.dumps(payload, indent=2))
    return 2 if warnings else 0


def cmd_audit(args: argparse.Namespace) -> int:
    codex_home = Path(args.codex_home).expanduser().resolve()
    audit = inspect_codex_home(codex_home)
    audit["monitor"] = gather_monitor_state(args.monitor_base_url) if args.include_monitor else "skipped"
    try:
        _, state_root = resolve_roots(args.repo_root)
        audit["task_identity"] = rollover_identity_snapshot(state_root)
    except ValueError as exc:
        audit["task_identity"] = {"error": str(exc)}
    print(json.dumps(audit, indent=2))
    return 0


def _bundle_output_path(state_root: Path, *, agent: str, lineage_id: str, rollover_id: str, supplied: Path | None) -> Path:
    if supplied is not None:
        return supplied.expanduser().resolve()
    return (
        state_root
        / ".agent"
        / "thread-rollovers"
        / agent
        / lineage_id
        / f"{rollover_id}.bundle.tgz"
    )


def cmd_export_bundle(args: argparse.Namespace) -> int:
    try:
        repo_root, state_root = resolve_roots(args.repo_root)
        agent = normalize_agent_name(args.agent)
        state_path, state = _select_bundle_state(
            state_root,
            agent=agent,
            lineage_id=args.lineage_id,
            rollover_id=args.rollover_id,
        )
        stream_id = str(args.stream or "")
        manifest, blob, secret_hits = _build_rollover_bundle(
            repo_root,
            state_root,
            agent=agent,
            state=state,
            stream_id=stream_id,
        )
        output_path = _bundle_output_path(
            state_root,
            agent=agent,
            lineage_id=str(manifest["lineage_id"]),
            rollover_id=str(manifest["rollover_id"]),
            supplied=args.file,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write_bytes_atomic(output_path, blob)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc), "action": "export-bundle"}, indent=2))
        return 2

    result: dict[str, Any] = {
        "status": "exported",
        "agent": agent,
        "lineage_id": manifest["lineage_id"],
        "rollover_id": manifest["rollover_id"],
        "generation": manifest["generation"],
        "stream_id": stream_id,
        "file": rel(output_path, repo_root) if output_path.is_relative_to(repo_root) else str(output_path),
        "bytes": len(blob),
        "bundle_sha256": manifest["bundle_sha256"],
        "source_state": rel(state_path, state_root),
        "upload": "not-requested",
    }
    for _member, rule in secret_hits:
        print(
            f"WARNING: rollover bundle secret scan hit rule={rule}; "
            "local bundle was written but upload was skipped.",
            file=sys.stderr,
        )
    if args.upload:
        if secret_hits:
            result["upload"] = "skipped-secret-scan"
        else:
            try:
                response = _bundle_api_upload(args, stream_id=stream_id, manifest=manifest, blob=blob)
                result["upload"] = "uploaded"
                result["upload_seq"] = response.get("upload_seq")
            except (RolloverBundleAPIUnavailable, RuntimeError, ValueError) as exc:
                result["upload"] = "skipped"
                print(f"WARNING: rollover bundle upload skipped (fail-open): {exc}", file=sys.stderr)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _maybe_auto_upload_bundle(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    state_root: Path,
    agent: str,
    state: dict[str, Any],
) -> dict[str, Any]:
    """Best-effort prepare/confirm upload; never changes the lifecycle result."""
    stream_id = str(getattr(args, "stream", "") or "").strip()
    if not stream_id:
        return {"status": "not-requested"}
    try:
        manifest, blob, secret_hits = _build_rollover_bundle(
            repo_root,
            state_root,
            agent=agent,
            state=state,
            stream_id=stream_id,
        )
        output_path = _bundle_output_path(
            state_root,
            agent=agent,
            lineage_id=str(manifest["lineage_id"]),
            rollover_id=str(manifest["rollover_id"]),
            supplied=None,
        )
        write_bytes_atomic(output_path, blob)
        for _member, rule in secret_hits:
            print(
                f"WARNING: rollover bundle secret scan hit rule={rule}; "
                "local bundle was written but upload was skipped.",
                file=sys.stderr,
            )
        if secret_hits:
            return {
                "status": "skipped-secret-scan",
                "file": rel(output_path, repo_root) if output_path.is_relative_to(repo_root) else str(output_path),
                "bundle_sha256": manifest["bundle_sha256"],
            }
        response = _bundle_api_upload(args, stream_id=stream_id, manifest=manifest, blob=blob)
        upload_seq = response.get("upload_seq")
        if isinstance(upload_seq, int) and upload_seq >= 0:
            receipt_path = (
                state_root
                / ".agent"
                / "thread-rollovers"
                / agent
                / "_bundle-receipts"
                / f"{manifest['lineage_id']}.json"
            )
            write_json_atomic(
                receipt_path,
                {"schema": "rollover-bundle-receipt.v1", "upload_seq": upload_seq},
            )
        return {
            "status": "uploaded",
            "file": rel(output_path, repo_root) if output_path.is_relative_to(repo_root) else str(output_path),
            "bundle_sha256": manifest["bundle_sha256"],
            "upload_seq": upload_seq,
        }
    except Exception as exc:
        print(f"WARNING: automatic rollover bundle upload skipped (fail-open): {exc}", file=sys.stderr)
        return {"status": "skipped", "reason": str(exc)}


def _bundle_local_lineage_snapshot(
    repo_root: Path,
    state_root: Path,
    *,
    agent: str,
    lineage_id: str,
    stream_id: str,
) -> tuple[dict[str, Any] | None, dict[str, bytes] | None, bool]:
    """Read and validate the local copy before any import filesystem mutation."""
    lineage_root = state_root / ".agent" / "thread-rollovers" / agent / lineage_id
    if not lineage_root.exists():
        return None, None, False
    if lineage_root.is_symlink() or not lineage_root.is_dir():
        raise ValueError("local rollover lineage is not a regular directory")
    state_path = lineage_root / "lease.json"
    state = load_state(state_path)
    _, error = validate_live_lease(state, agent=agent, state_path=state_path)
    if error:
        raise ValueError(f"local rollover lease is invalid: {error}")
    receipt_path = state_root / ".agent" / "thread-rollovers" / agent / "_bundle-receipts" / f"{lineage_id}.json"
    receipt = load_state(receipt_path) if receipt_path.is_file() else {}
    try:
        upload_seq = int(receipt.get("upload_seq", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("local rollover bundle receipt has a malformed upload_seq") from exc
    local_manifest = _bundle_state_manifest(state, stream_id=stream_id, upload_seq=upload_seq)
    local_members = _bundle_local_members(
        repo_root,
        state_root,
        agent=agent,
        lineage_id=lineage_id,
        stream_id=stream_id,
    )
    return local_manifest, local_members, True


def _bundle_import_error(reason: str) -> int:
    print(json.dumps({"error": reason, "action": "import-bundle"}, separators=(",", ":")))
    return 2


def _bundle_import_candidate(
    repo_root: Path,
    state_root: Path,
    *,
    manifest: Mapping[str, Any],
    members: Mapping[str, bytes],
    force: bool,
    install_handoff: bool,
) -> dict[str, Any]:
    """Install one bundle while keeping packet and lane precedence separate."""
    agent = normalize_agent_name(str(manifest.get("agent") or ""))
    lineage_id = normalize_lineage_id(str(manifest["lineage_id"]))
    stream_id = str(manifest.get("stream_id") or "")
    _bundle_validate_lease_member(
        state_root,
        agent=agent,
        lineage_id=lineage_id,
        manifest=manifest,
        members=members,
    )
    remote_order = _bundle_order(manifest)
    local_manifest, local_members, local_lineage_exists = _bundle_local_lineage_snapshot(
        repo_root,
        state_root,
        agent=agent,
        lineage_id=lineage_id,
        stream_id=stream_id,
    )
    if local_manifest is not None and local_members is not None:
        local_order = _bundle_order(local_manifest)
        if local_order > remote_order and not force:
            return {
                "status": "refused",
                "error": "local rollover copy is newer; refusing to clobber it",
                "agent": agent,
                "lineage_id": lineage_id,
                "rollover_id": manifest["rollover_id"],
                "local": {
                    "generation": local_order[0],
                    "status_rank": local_order[1],
                    "prepared_at": isoformat_z(local_order[2]),
                    "rollover_id": local_order[3],
                },
                "remote": {
                    "generation": remote_order[0],
                    "status_rank": remote_order[1],
                    "prepared_at": isoformat_z(remote_order[2]),
                    "rollover_id": remote_order[3],
                },
            }
        if local_order == remote_order and not force:
            handoff_names = set(_bundle_handoff_candidates_for_agent(repo_root, stream_id, agent))
            remote_compare = {
                name: payload
                for name, payload in members.items()
                if install_handoff or name not in handoff_names
            }
            local_compare = {
                name: payload
                for name, payload in local_members.items()
                if install_handoff or name not in handoff_names
            }
            if local_compare == remote_compare and local_manifest.get("generation") == manifest.get("generation"):
                return {
                    "status": "noop",
                    "reason": "identical bundle content",
                    "agent": agent,
                    "lineage_id": lineage_id,
                    "rollover_id": manifest["rollover_id"],
                }
            return {
                "status": "refused",
                "error": "bundle order ties but content differs; refusing to choose a copy",
                "agent": agent,
                "lineage_id": lineage_id,
                "rollover_id": manifest["rollover_id"],
                "generation": manifest["generation"],
            }

    stage_root, staged_lineage, staged_repo = _bundle_stage_install(
        repo_root,
        state_root,
        manifest=manifest,
        members=members,
    )
    archived, preserved = _bundle_commit_install(
        repo_root,
        state_root,
        manifest=manifest,
        stage_root=stage_root,
        staged_lineage=staged_lineage,
        staged_repo=staged_repo,
        local_lineage_exists=local_lineage_exists,
        install_handoff=install_handoff,
    )
    return {
        "status": "installed",
        "agent": agent,
        "lineage_id": lineage_id,
        "rollover_id": manifest["rollover_id"],
        "generation": manifest["generation"],
        "stream_id": stream_id,
        "archived": str(archived.relative_to(state_root)) if archived is not None else None,
        "preserved_handoffs": preserved,
        "upload_seq": manifest.get("upload_seq", 0),
        "install_handoff": install_handoff,
    }


def cmd_import_bundle(args: argparse.Namespace) -> int:
    try:
        repo_root, state_root = resolve_roots(args.repo_root)
        agent = normalize_agent_name(args.agent)
    except (OSError, ValueError) as exc:
        return _bundle_import_error(str(exc))

    candidates: list[tuple[dict[str, Any], dict[str, bytes]]] = []
    try:
        if args.file is not None:
            blob = args.file.expanduser().resolve().read_bytes()
            manifest, members = _bundle_extract(blob)
            if manifest.get("agent") != agent:
                raise ValueError("bundle agent does not match --agent")
            candidates.append((manifest, members))
        else:
            stream_id = str(args.from_api)
            listed = _bundle_api_list(args, stream_id=stream_id)
            if not listed:
                raise RolloverBundleNotFound("bundle API has no matching bundle")

            def upload_seq(row: Mapping[str, Any]) -> int:
                try:
                    return int(row.get("upload_seq", (row.get("manifest") or {}).get("upload_seq", 0)))
                except (TypeError, ValueError) as exc:
                    raise ValueError("bundle API list upload sequence is malformed") from exc

            def row_agent(row: Mapping[str, Any]) -> str:
                if row.get("agent") is not None:
                    return str(row["agent"])
                manifest = row.get("manifest")
                if not isinstance(manifest, Mapping):
                    raise ValueError("bundle API list manifest is malformed")
                return str(manifest.get("agent") or "")

            own_row = next((row for row in listed if row_agent(row) == agent), None)
            handoff_row = max(listed, key=upload_seq)
            selected_sequences = {
                upload_seq(row)
                for row in (own_row, handoff_row)
                if row is not None
            }
            for row in listed:
                sequence = upload_seq(row)
                if sequence not in selected_sequences:
                    continue
                manifest, blob = _bundle_api_by_seq(args, stream_id=stream_id, upload_seq=sequence)
                manifest, members = _bundle_extract(blob, manifest_override=manifest)
                candidates.append((manifest, members))

        for manifest, _ in candidates:
            stream_id = str(manifest.get("stream_id") or "")
            if not stream_id:
                raise ValueError("bundle stream_id is missing")
            if args.from_api is not None and stream_id != str(args.from_api):
                raise ValueError("bundle stream does not match --from-api")
            if args.stream is not None and stream_id != str(args.stream):
                raise ValueError("bundle stream does not match --stream")
    except RolloverBundleAPIUnavailable as exc:
        print(f"WARNING: rollover bundle import skipped (fail-open): {exc}", file=sys.stderr)
        print(json.dumps({"status": "warning", "action": "import-bundle", "reason": str(exc)}, separators=(",", ":")))
        return 0
    except RolloverBundleNotFound as exc:
        return _bundle_import_error(str(exc))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return _bundle_import_error(str(exc))

    handoff_winner = max(candidates, key=lambda item: int(item[0].get("upload_seq", 0))) if len(candidates) > 1 else None
    results: list[dict[str, Any]] = []
    try:
        for candidate in candidates:
            results.append(
                _bundle_import_candidate(
                    repo_root,
                    state_root,
                    manifest=candidate[0],
                    members=candidate[1],
                    force=args.force,
                    install_handoff=handoff_winner is None or candidate is handoff_winner,
                )
            )
    except Exception as exc:
        return _bundle_import_error(str(exc))

    if len(results) == 1:
        result = results[0]
    else:
        statuses = {item["status"] for item in results}
        aggregate_status = "refused" if "refused" in statuses else "installed" if "installed" in statuses else "noop"
        result = {
            "status": aggregate_status,
            "agent": agent,
            "stream_id": str(args.from_api),
            "bundles": results,
            "handoff_source": handoff_winner[0].get("agent") if handoff_winner is not None else None,
            "handoff_upload_seq": handoff_winner[0].get("upload_seq", 0) if handoff_winner is not None else None,
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 2 if any(item["status"] == "refused" for item in results) else 0


def rollover_identity_snapshot(state_root: Path, agent: str | None = None) -> dict[str, Any]:
    """Project identity from live leases without selecting, mutating, or maintaining a registry."""
    root = state_root / ".agent" / "thread-rollovers"
    candidates: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    excluded_terminal: list[dict[str, str]] = []
    paths = root.glob(f"{agent}/*/lease.json") if agent else root.glob("*/*/lease.json")
    for path in sorted(paths):
        lease_agent = path.parent.parent.name
        state = load_state(path)
        replacement, error = validate_live_lease(state, agent=lease_agent, state_path=path)
        if error:
            errors.append({"state_file": rel(path, state_root), "error": error})
            continue
        if replacement is not None and replacement.get("status") in {"pending_start", "resumed"}:
            lineage_id = state.get("lineage_id")
            rollover_id = replacement.get("rollover_id")
            candidate_agent = str(state.get("agent") or lease_agent)
            if lineage_id and rollover_id:
                try:
                    reg_path = task_family_rollover_registry.record_path(
                        state_root, agent=candidate_agent, lineage_id=lineage_id, rollover_id=rollover_id
                    )
                    if reg_path.is_file():
                        rec = task_family_rollover_registry.load_record(
                            state_root, agent=candidate_agent, lineage_id=lineage_id, rollover_id=rollover_id
                        )
                        rec_state = rec.get("state")
                        if task_family_rollover_registry.is_terminal_state(rec_state):
                            excluded_terminal.append(
                                {
                                    "agent": candidate_agent,
                                    "lineage_id": str(lineage_id),
                                    "rollover_id": str(rollover_id),
                                    "state": str(rec_state),
                                }
                            )
                            continue
                except Exception as exc:
                    errors.append({"state_file": rel(path, state_root), "error": f"registry load error: {exc}"})
            diagnostic = task_identity.candidate_diagnostic(
                state,
                replacement,
                state_file=rel(path, state_root),
            )
            diagnostic["agent"] = lease_agent
            candidates.append(diagnostic)
    out: dict[str, Any] = {
        "schema_version": "rollover-identity-snapshot.v1",
        "generated_at": isoformat_z(utc_now()),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "errors": errors,
    }
    if excluded_terminal:
        out["excluded_terminal"] = excluded_terminal
    return out



def render_session_start_context(
    candidate: dict[str, Any] | None,
    *,
    agent: str,
    current_thread_id: str,
    stream_id: str | None = None,
) -> str:
    """Render the only SessionStart handoff text; shell hooks never parse leases."""
    if candidate is None or candidate.get("status") == "none":
        facts_path = ".agent/orientation-health-facts.json"
        lines = [
            "COLD START: NO LIVE THREAD ROLLOVER",
            "No pending or resumed packet exists for this agent.",
            "Orient from durable project state with tool-backed reads before ordinary work.",
            "Create exactly ten truthful legacy orientation facts, then run:",
            f".venv/bin/python scripts/context_canary.py mint --facts {facts_path} --out .agent/orientation-health-probe.json",
            "Do not invent a lineage_id or rollover_id; prepare creates both only when this thread later rolls over.",
            "Keep the primary checkout read-only and use a dispatch worktree for implementation.",
        ]
        if isinstance(candidate, dict):
            if candidate.get("excluded_terminal"):
                lines.append(
                    "Excluded terminal rollover: "
                    + ", ".join(
                        f"{item['agent']}/{item['lineage_id']}/{item['rollover_id']} ({item['state']})"
                        for item in candidate["excluded_terminal"]
                    )
                )
            if candidate.get("registry_errors"):
                for err in candidate["registry_errors"]:
                    lines.append(f"Registry error: {err}")
        return "\n".join(lines)
    thread_id = current_thread_id or "<current-codex-thread-id>"
    lineage_id = candidate["lineage_id"]
    rollover_id = candidate["rollover_id"]
    stream_arg = f" --stream {stream_id}" if stream_id else ""
    if candidate["status"] == "resumed":
        title = "RESUMED THREAD ROLLOVER DETECTED"
    else:
        title = "PENDING THREAD ROLLOVER DETECTED"
    lines = [title, f"Replacement generation: {candidate.get('generation', 'unknown')}", "```bash"]
    if candidate["status"] == "pending_start":
        lines.append(
            f".venv/bin/python scripts/orchestration/thread_handoff.py bootstrap-replacement -a {agent} -l {lineage_id} -r {rollover_id} -t {thread_id} -e <binding>"
        )
    lines.extend(
        [
            f".venv/bin/python scripts/orchestration/thread_handoff.py confirm-replacement -a {agent} -l {lineage_id} -r {rollover_id}{stream_arg}",
            "```",
            "Fill snapshot; first confirm emits questions. Failure keeps cleanup locked.",
        ]
    )
    if candidate.get("excluded_terminal"):
        lines.append(
            "Excluded terminal rollover: "
            + ", ".join(
                f"{item['agent']}/{item['lineage_id']}/{item['rollover_id']} ({item['state']})"
                for item in candidate["excluded_terminal"]
            )
        )
    if candidate.get("registry_errors"):
        for err in candidate["registry_errors"]:
            lines.append(f"Registry error: {err}")
    return "\n".join(lines)


def _candidate_task_family(state: dict[str, Any], replacement: dict[str, Any]) -> str:
    """Extract task_family from lease state / replacement identity blobs."""
    for blob in (replacement, state):
        if not isinstance(blob, dict):
            continue
        identity = blob.get("identity") or blob.get("task_identity") or {}
        if isinstance(identity, dict):
            family = str(identity.get("task_family") or "").strip().lower()
            if family:
                return family
        family = str(blob.get("task_family") or "").strip().lower()
        if family:
            return family
    return ""


def _filter_live_leases_by_task_family(
    live_leases: list[tuple[Path, dict[str, Any], dict[str, Any]]],
    task_family: str,
) -> list[tuple[Path, dict[str, Any], dict[str, Any]]]:
    wanted = task_family.strip().lower()
    if not wanted:
        return live_leases
    matched = [
        item
        for item in live_leases
        if _candidate_task_family(item[1], item[2]) == wanted
    ]
    return matched


def _render_multiple_pending_session_start(
    *,
    agent: str,
    candidates: list[dict[str, Any]],
    task_family_filter: str,
    excluded_terminal: list[dict[str, str]] | None = None,
    registry_errors: list[str] | None = None,
) -> str:
    lines = [
        f"MULTIPLE LIVE PENDING ROLLOVERS for agent `{agent}` (#5398 class).",
        "Do NOT cold-start. Do NOT pick by title or filesystem order.",
        f"Candidate count: {len(candidates)}.",
    ]
    if task_family_filter:
        lines.append(f"Task-family filter applied: `{task_family_filter}` (still ambiguous).")
    lines.append("")
    for i, cand in enumerate(candidates, start=1):
        lines.append(
            f"{i}. lineage_id={cand.get('lineage_id')} rollover_id={cand.get('rollover_id')} "
            f"family={cand.get('task_family')} title={cand.get('visible_title')!r}"
        )
        issue = cand.get("issue") or {}
        if isinstance(issue, dict) and issue.get("number"):
            lines.append(f"   issue=#{issue.get('number')} {issue.get('url') or ''}".rstrip())
        lines.append(
            f"   bind: .venv/bin/python scripts/orchestration/thread_handoff.py bind-replacement "
            f"--agent {agent} --lineage-id {cand.get('lineage_id')} "
            f"--rollover-id {cand.get('rollover_id')} "
            f"--replacement-task-id <this-thread-id> --evidence <harness-binding>"
        )
        lines.append("")
    if excluded_terminal:
        lines.append(
            "Excluded terminal rollover: "
            + ", ".join(
                f"{item['agent']}/{item['lineage_id']}/{item['rollover_id']} ({item['state']})"
                for item in excluded_terminal
            )
        )
    if registry_errors:
        for err in registry_errors:
            lines.append(f"Registry error: {err}")
    lines.append(
        "Resolution: bind the exact candidate for THIS lane (or re-run detect with "
        "`--task-family <family>` / launch with `--epic <name>`)."
    )
    return "\n".join(lines)



def cmd_detect(args: argparse.Namespace) -> int:
    try:
        _, state_root = resolve_roots(args.repo_root)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2
    agent = normalize_agent_name(args.agent)
    task_family_filter = str(getattr(args, "task_family", "") or "").strip().lower()

    # Agent directories to scan. Epic slots like claude-hramatka often have packets
    # prepared under the bare `claude` namespace (#5398 / hramatka interim).
    scan_agents = [agent]
    # Epic slots (claude-hramatka, codex-folk, …) often have packets prepared under
    # the bare provider namespace — scan both (#5398 slot trap).
    if agent.startswith("claude-") and agent not in {"claude-infra", "claude-atlas"}:
        scan_agents.append("claude")
    elif agent.startswith("codex-") and agent not in {"codex-infra"}:
        scan_agents.append("codex")

    live_leases: list[tuple[Path, dict[str, Any], dict[str, Any], str]] = []
    excluded_terminal: list[dict[str, str]] = []
    registry_errors: list[str] = []

    for scan_agent in scan_agents:
        agent_dir = state_root / ".agent" / "thread-rollovers" / scan_agent
        if not agent_dir.exists():
            continue
        for path in sorted(agent_dir.glob("*/lease.json")):
            state = load_state(path)
            replacement, error = validate_live_lease(state, agent=scan_agent, state_path=path)
            if error:
                print(json.dumps({"error": f"invalid rollover lease {rel(path, state_root)}: {error}"}, indent=2))
                return 2
            if replacement is not None and replacement["status"] in {"pending_start", "resumed"}:
                lineage_id = state.get("lineage_id")
                rollover_id = replacement.get("rollover_id")
                candidate_agent = str(state.get("agent") or scan_agent)
                if lineage_id and rollover_id:
                    try:
                        reg_path = task_family_rollover_registry.record_path(
                            state_root, agent=candidate_agent, lineage_id=lineage_id, rollover_id=rollover_id
                        )
                        if reg_path.is_file():
                            rec = task_family_rollover_registry.load_record(
                                state_root, agent=candidate_agent, lineage_id=lineage_id, rollover_id=rollover_id
                            )
                            rec_state = rec.get("state")
                            if task_family_rollover_registry.is_terminal_state(rec_state):
                                excluded_terminal.append(
                                    {
                                        "agent": candidate_agent,
                                        "lineage_id": str(lineage_id),
                                        "rollover_id": str(rollover_id),
                                        "state": str(rec_state),
                                    }
                                )
                                continue


                    except Exception as exc:
                        registry_errors.append(
                            f"registry record corrupt or unreadable for {candidate_agent}/{lineage_id}/{rollover_id}: {exc}"
                        )
                live_leases.append((path, state, replacement, scan_agent))

    if not live_leases:
        output: dict[str, Any] = {"agent": agent, "status": "none"}
        if excluded_terminal:
            output["excluded_terminal"] = excluded_terminal
        if registry_errors:
            output["registry_errors"] = registry_errors
        print(
            render_session_start_context(
                output,
                agent=agent,
                current_thread_id=args.current_thread_id,
                stream_id=getattr(args, "stream", None),
            )
            if args.format == "session-start"
            else json.dumps(output, indent=2)
        )
        return 0

    # Narrow multi-packet sets by task family when the launcher knows the epic (#5398).
    if task_family_filter and len(live_leases) > 1:
        filtered = [
            item
            for item in live_leases
            if _candidate_task_family(item[1], item[2]) == task_family_filter
            or (
                # Epic name often matches task_family (hramatka, folk, atlas, …).
                task_family_filter in str(item[2].get("role") or "").lower()
            )
        ]
        if len(filtered) == 1 or len(filtered) > 1:
            live_leases = filtered
        # If filter matches zero, keep full list so the operator sees everything.

    if len(live_leases) > 1:
        candidates = [
            task_identity.candidate_diagnostic(
                state,
                replacement,
                state_file=rel(path, state_root),
            )
            for path, state, replacement, _scan_agent in live_leases
        ]
        payload = {
            "error_code": "MULTIPLE_LIVE_PENDING_ROLLOVERS",
            "error": f"Multiple live pending rollovers found for agent {agent}.",
            "agent": agent,
            "status": "ambiguous",
            "candidate_count": len(candidates),
            "candidates": candidates,
            "task_family_filter": task_family_filter or None,
            "resolution_policy": (
                "Use exact candidate identifiers and receipts; never select by filesystem "
                "order, visible title, or automatic supersession. Prefer --task-family / "
                "--epic launch filter when the lane is known."
            ),
        }
        if excluded_terminal:
            payload["excluded_terminal"] = excluded_terminal
        if registry_errors:
            payload["registry_errors"] = registry_errors

        if args.format == "session-start":
            print(
                _render_multiple_pending_session_start(
                    agent=agent,
                    candidates=candidates,
                    task_family_filter=task_family_filter,
                    excluded_terminal=excluded_terminal,
                    registry_errors=registry_errors,
                )
            )
        else:
            print(json.dumps(payload, indent=2))
        return 2

    path, state, replacement, scan_agent = live_leases[0]
    if (
        replacement["status"] == "resumed"
        and args.current_thread_id
        and replacement.get("resumed_thread_id") != args.current_thread_id
    ):
        print(
            json.dumps(
                {
                    "error": "live rollover is already bound to a different replacement thread",
                    "resumed_thread_id": replacement.get("resumed_thread_id"),
                },
                indent=2,
            )
        )
        return 2

    output = {
        "agent": agent,
        "packet_agent": scan_agent,
        "lineage_id": state.get("lineage_id"),
        "rollover_id": replacement.get("rollover_id"),
        "generation": replacement.get("generation"),
        "status": replacement.get("status"),
        "state_file": rel(path, state_root),
        "state": "live",
        "runtime_path": replacement.get("runtime_path"),
        "handoff_path": replacement.get("handoff_path"),
        "bootstrap_prompt_path": replacement.get("bootstrap_prompt_path"),
        "canary_challenge": replacement.get("canary_challenge"),
        "canary_proof_path": replacement.get("canary_proof_path"),
        "resumed_thread_id": replacement.get("resumed_thread_id"),
        "strict_probe_path": replacement.get("strict_probe_path"),
        "semantic_snapshot_path": replacement.get("semantic_snapshot_path"),
        "strict_questions_path": replacement.get("strict_questions_path"),
        "strict_answers_path": replacement.get("strict_answers_path"),
        "strict_verdict_path": replacement.get("strict_verdict_path"),
        "identity_receipt_path": replacement.get("identity_receipt_path"),
        "identity": replacement.get("identity"),
        "title_transition": replacement.get("title_transition"),
        "task_family_filter": task_family_filter or None,
    }
    if excluded_terminal:
        output["excluded_terminal"] = excluded_terminal
    if registry_errors:
        output["registry_errors"] = registry_errors

    print(
        render_session_start_context(
            output,
            agent=agent,
            current_thread_id=args.current_thread_id,
            stream_id=getattr(args, "stream", None),
        )
        if args.format == "session-start"
        else json.dumps(output, indent=2)
    )
    return 0



def _lock_timeout_exit(exc: TimeoutError) -> int:
    print(json.dumps({"error_code": "LOCK_TIMEOUT", "error": str(exc)}, indent=2))
    return 124


def _lock_timeout_exit(exc: TimeoutError) -> int:
    print(json.dumps({"error_code": "LOCK_TIMEOUT", "error": str(exc)}, indent=2))
    return 124


def cmd_claim_thread_lease(args: argparse.Namespace) -> int:
    """Claim the durable single-driver lease used during SessionStart."""
    try:
        _, state_root = resolve_roots(args.repo_root)
        agent = normalize_agent_name(args.agent)
        result = claim_thread_lease(
            state_root=state_root,
            agent=agent,
            current_thread_id=args.current_thread_id,
            now=utc_now(),
            starting_pid=args.starting_pid,
        )
    except TimeoutError as exc:
        return _lock_timeout_exit(exc)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2

    lease_path = result.pop("lease_path")
    payload = {
        "agent": agent,
        "lease_file": rel(lease_path, state_root),
        **result,
    }
    if payload["status"] == "conflict":
        liveness = payload.get("liveness")
        # claim_thread_lease already computed the exact CAS-scoped command as
        # payload["resolution"]; this layer only adds the human-facing error
        # text and, for the liveness-unknown lane, a slightly different frame.
        resolution_command = payload.get("resolution") or _cas_force_release_command(
            agent, owner_thread_id=payload.get("owner_thread_id"), generation=payload.get("generation")
        )
        if liveness == "liveness_unknown":
            payload.update(
                {
                    "error_code": "THREAD_LEASE_LIVENESS_UNKNOWN",
                    "error": (
                        "durable thread lease owner's liveness could not be checked and it is "
                        "never taken over automatically (no clock-based takeover); stop to avoid "
                        "double-driving"
                    ),
                    "resolution": (
                        f"If the previous owner ({payload.get('lease_file')}) is confirmed gone, "
                        f"force-release with: {resolution_command} — then start normally "
                        f"again. Otherwise wait for it to exit and release cooperatively."
                    ),
                }
            )
        else:
            payload.update(
                {
                    "error_code": "THREAD_LEASE_CONFLICT",
                    "error": "durable thread lease is held by another live session; stop to avoid double-driving",
                    "resolution": (
                        f"Wait for the owner session to stop, or if it is confirmed gone, "
                        f"force-release with: {resolution_command}"
                    ),
                }
            )
        print(json.dumps(payload, indent=2))
        return 2
    print(json.dumps(payload, indent=2))
    return 0


def cmd_release_thread_lease(args: argparse.Namespace) -> int:
    """Release the durable single-driver lease, e.g. from a SessionEnd hook."""
    try:
        _, state_root = resolve_roots(args.repo_root)
        agent = normalize_agent_name(args.agent)
        if not args.force and not args.current_thread_id:
            raise ValueError("--current-thread-id is required unless --force is given")
        result = release_thread_lease(
            state_root=state_root,
            agent=agent,
            current_thread_id=args.current_thread_id or "",
            now=utc_now(),
            generation=args.generation,
            starting_pid=args.starting_pid,
            force=args.force,
            expect_owner_thread_id=args.expect_owner_thread_id,
            expect_generation=args.expect_generation,
            acknowledge_live_owner=args.acknowledge_live_owner,
        )
    except TimeoutError as exc:
        return _lock_timeout_exit(exc)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2

    lease_path = result.pop("lease_path")
    payload = {
        "agent": agent,
        "lease_file": rel(lease_path, state_root),
        **result,
    }
    print(json.dumps(payload, indent=2))
    return 2 if payload.get("status") == "refused" else 0


def cmd_refresh_thread_lease_heartbeat(args: argparse.Namespace) -> int:
    """Best-effort heartbeat refresh from the ``Stop``/``PostToolUse`` hooks. Always exits 0."""
    try:
        _, state_root = resolve_roots(args.repo_root)
        agent = normalize_agent_name(args.agent)
        result = refresh_thread_lease_heartbeat(
            state_root=state_root,
            agent=agent,
            current_thread_id=args.current_thread_id,
            generation=args.generation,
            now=utc_now(),
            starting_pid=args.starting_pid,
            min_refresh_interval=(
                timedelta(seconds=args.min_refresh_interval_seconds)
                if args.min_refresh_interval_seconds is not None
                else None
            ),
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 0

    lease_path = result.pop("lease_path", None)
    payload = {
        "agent": agent,
        **({"lease_file": rel(lease_path, state_root)} if lease_path is not None else {}),
        **result,
    }
    print(json.dumps(payload, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument(
        "--monitor-base-url",
        default=os.environ.get("LU_MONITOR_LOOPBACK", os.environ.get("MONITOR_API_BASE_URL", DEFAULT_MONITOR_BASE_URL)),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="Prepare a rollover handoff and bootstrap prompt.")
    prepare.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    prepare.add_argument(
        "--lineage-id",
        type=argparse_lineage_id,
        help="Optional stable isolation key; otherwise derived from --active-thread-id.",
    )
    prepare.add_argument("--state-file", type=Path)
    prepare.add_argument("--current-file", type=Path, help="Override the shared docs/session-state/current.md router.")
    prepare.add_argument("--active-thread-id")
    prepare.add_argument("--active-automation-id")
    prepare.add_argument(
        "--repository",
        default=task_identity.DEFAULT_REPOSITORY,
        help="Canonical GitHub owner/repository recorded in task-identity.v1.",
    )
    prepare.add_argument("--stream-epic", type=int, help="The task's one stream epic issue number.")
    prepare.add_argument("--stream-epic-url", help="Optional exact URL; derived when omitted.")
    prepare.add_argument("--issue-number", type=int, help="Scoped GitHub issue number when applicable.")
    prepare.add_argument("--issue-url", help="Optional exact URL; derived when omitted.")
    prepare.add_argument(
        "--semantic-title",
        help="Required semantic identity for new callers; legacy callers receive a deterministic fallback.",
    )
    prepare.add_argument("--task-family", default="thread-rollover", help="Lowercase task-family slug.")
    prepare.add_argument("--role", help="Human/agent role carried across the rollover.")
    prepare.add_argument(
        "--terminal-goal",
        choices=sorted(task_identity.TERMINAL_GOALS),
        help="Terminal outcome preserved across replacement generations (merge, deploy, or certify).",
    )
    prepare.add_argument(
        "--harness",
        help="Native harness adapter name. Only declared adapters may claim title mutation/readback support.",
    )
    prepare.add_argument("--epic-title", help="Durable human epic label for the replacement title.")
    prepare.add_argument("--goal", help="Durable current goal for the replacement title.")
    prepare.add_argument("--phase", help="Durable current phase for the replacement title.")
    prepare.add_argument("--next-phase", help="Optional next phase rendered after an arrow.")
    prepare.add_argument("--context-percent", type=float)
    prepare.add_argument("--context-threshold", type=float, default=DEFAULT_CONTEXT_THRESHOLD)
    prepare.add_argument("--force-new-replacement", action="store_true")
    prepare.add_argument("--stream", help="Explicit session stream id used for an optional bundle upload.")
    prepare.add_argument(
        "--migrate-v1", action="store_true", help="Explicitly migrate a v1 lease into a fresh v2 rollover."
    )
    prepare.add_argument(
        "--force-reset-state",
        action="store_true",
        help="Discard an unreadable lease state file and start a new lease.",
    )
    prepare.add_argument(
        "--write-current",
        action="store_true",
        help="Deprecated: also overwrite the shared current.md router. Requires --allow-git-router.",
    )
    prepare.add_argument(
        "--allow-git-router",
        action="store_true",
        help="Explicitly unlock --write-current for an approved compatibility-router update.",
    )
    prepare.add_argument("--dry-run", action="store_true", help="Print the generated packet without writing files.")
    prepare.set_defaults(func=cmd_prepare)

    repair_native_intent = subparsers.add_parser(
        "repair-native-intent",
        help="Replace one untouched legacy same-generation native receipt with the current packet-specific intent.",
    )
    repair_native_intent.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    repair_native_intent.add_argument("--lineage-id", type=argparse_lineage_id)
    repair_native_intent.add_argument("--state-file", type=Path)
    repair_native_intent.add_argument("--rollover-id", required=True)
    repair_native_intent.add_argument(
        "--evidence",
        required=True,
        help="Exact operator/app evidence that the legacy receipt never reached create_thread.",
    )
    repair_native_intent.set_defaults(func=cmd_repair_native_intent)

    register = subparsers.add_parser(
        "register-created",
        help="Bind the exact native-created replacement UUID and typed Task Family Manager relations.",
    )
    register.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    register.add_argument("--lineage-id", type=argparse_lineage_id)
    register.add_argument("--state-file", type=Path)
    register.add_argument("--rollover-id", required=True)
    register.add_argument("--replacement-thread-id", required=True)
    register.add_argument("--db", default="auto")
    register.add_argument("--evidence", required=True)
    register.set_defaults(func=cmd_register_created)

    bind_replacement = subparsers.add_parser(
        "bind-replacement",
        help="Bind the exact replacement for a harness without native title mutation and record the honest carrier fallback.",
    )
    bind_replacement.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    bind_replacement.add_argument("--lineage-id", type=argparse_lineage_id)
    bind_replacement.add_argument("--state-file", type=Path)
    bind_replacement.add_argument("--rollover-id", required=True)
    bind_replacement.add_argument("--replacement-task-id", required=True)
    bind_replacement.add_argument("--evidence", required=True)
    bind_replacement.set_defaults(func=cmd_bind_replacement)

    native_action = subparsers.add_parser(
        "native-action",
        help="Reconcile first, then emit at most one exact native title/archive action.",
    )
    native_action.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    native_action.add_argument("--lineage-id", type=argparse_lineage_id)
    native_action.add_argument("--state-file", type=Path)
    native_action.add_argument("--rollover-id", required=True)
    native_action.add_argument("--action", choices=("create", "title", "archive"), required=True)
    native_action.add_argument("--db", default="auto")
    native_action.add_argument("--source-status", default="unknown")
    native_action.add_argument("--pin-state", choices=("unpinned", "pinned", "unknown"), default="unknown")
    native_action.add_argument("--evidence", default="")
    native_action.set_defaults(func=cmd_native_action)

    native_result = subparsers.add_parser(
        "record-native-result",
        help="Persist one native tool acknowledgement or failure before read-back reconciliation.",
    )
    native_result.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    native_result.add_argument("--lineage-id", type=argparse_lineage_id)
    native_result.add_argument("--state-file", type=Path)
    native_result.add_argument("--rollover-id", required=True)
    native_result.add_argument("--action", choices=tuple(sorted(task_family_rollover.NATIVE_ACTIONS)), required=True)
    native_result.add_argument("--evidence", required=True)
    native_result.add_argument("--error", default="")
    native_result_group = native_result.add_mutually_exclusive_group(required=True)
    native_result_group.add_argument("--succeeded", dest="succeeded", action="store_true")
    native_result_group.add_argument("--failed", dest="succeeded", action="store_false")
    native_result.set_defaults(func=cmd_record_native_result)

    reconcile_native = subparsers.add_parser(
        "reconcile-native",
        help="Verify one exact native title/archive target and update the durable receipt.",
    )
    reconcile_native.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    reconcile_native.add_argument("--lineage-id", type=argparse_lineage_id)
    reconcile_native.add_argument("--state-file", type=Path)
    reconcile_native.add_argument("--rollover-id", required=True)
    reconcile_native.add_argument("--action", choices=("title", "archive"), required=True)
    reconcile_native.add_argument("--db", default="auto")
    reconcile_native.set_defaults(func=cmd_reconcile_native)

    confirm = subparsers.add_parser("confirm-started", help="Confirm that the replacement agent thread is running.")
    confirm.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    confirm.add_argument("--lineage-id", type=argparse_lineage_id)
    confirm.add_argument("--state-file", type=Path)
    confirm.add_argument("--rollover-id", required=True)
    confirm.add_argument("--new-thread-id", required=True)
    confirm.add_argument("--new-automation-id")
    confirm.add_argument("--canary-proof", type=Path, required=True)
    confirm.add_argument("--strict-probe", type=Path, required=True)
    confirm.add_argument("--strict-verdict", type=Path, required=True)
    confirm.add_argument("--confirmed-by", default=os.environ.get("USER", "operator"))
    confirm.add_argument("--stream", help="Explicit session stream id used for an optional bundle upload.")
    confirm.set_defaults(func=cmd_confirm_started)

    resume = subparsers.add_parser(
        "resume",
        help="Bind a new thread to a prepared local rollover packet; never provider conversation history.",
    )
    resume.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    resume.add_argument("--lineage-id", type=argparse_lineage_id)
    resume.add_argument("--state-file", type=Path)
    resume.add_argument("--rollover-id", required=True)
    resume.add_argument("--replacement-thread-id", required=True)
    resume.set_defaults(func=cmd_resume)

    bootstrap_replacement = subparsers.add_parser(
        "bootstrap-replacement",
        help="Bind and resume one fallback replacement, then write its answer-free strict snapshot template.",
    )
    bootstrap_replacement.add_argument("-a", "--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    bootstrap_replacement.add_argument("-l", "--lineage-id", type=argparse_lineage_id)
    bootstrap_replacement.add_argument("--state-file", type=Path)
    bootstrap_replacement.add_argument("-r", "--rollover-id", required=True)
    bootstrap_replacement.add_argument("-t", "--replacement-thread-id", required=True)
    bootstrap_replacement.add_argument("-e", "--evidence", required=True)
    bootstrap_replacement.set_defaults(func=cmd_bootstrap_replacement)

    confirm_replacement = subparsers.add_parser(
        "confirm-replacement",
        help="Mint, ask, score, canary-prove, and confirm one resumed replacement in-process.",
    )
    confirm_replacement.add_argument("-a", "--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    confirm_replacement.add_argument("-l", "--lineage-id", type=argparse_lineage_id)
    confirm_replacement.add_argument("--state-file", type=Path)
    confirm_replacement.add_argument("-r", "--rollover-id", required=True)
    confirm_replacement.add_argument(
        "--replacement-thread-id",
        help="Optional exact thread ID; defaults to the packet's already resumed replacement ID.",
    )
    confirm_replacement.add_argument("--new-automation-id")
    confirm_replacement.add_argument("--confirmed-by", default=os.environ.get("USER", "operator"))
    confirm_replacement.add_argument("--stream", help="Explicit session stream id used for an optional bundle upload.")
    confirm_replacement.set_defaults(func=cmd_confirm_replacement)

    export_bundle = subparsers.add_parser(
        "export-bundle",
        help="Export one lineage rollover packet and its stream-lane handoff as a bounded bundle.",
    )
    export_bundle.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    export_bundle.add_argument("--lineage-id", type=argparse_lineage_id)
    export_bundle.add_argument("--rollover-id", type=argparse_rollover_id)
    export_bundle.add_argument("--stream", help="Explicit launcher-derived stream id for the lane handoff/API.")
    export_bundle.add_argument("--file", type=Path, help="Write the local .tgz to this path.")
    export_bundle.add_argument("--upload", action="store_true", help="Upload through the loopback Monitor API.")
    export_bundle.set_defaults(func=cmd_export_bundle)

    import_bundle = subparsers.add_parser(
        "import-bundle",
        help="Install a newer cross-host rollover bundle without silently clobbering local state.",
    )
    import_bundle.add_argument(
        "--agent",
        type=argparse_agent_name,
        default=os.environ.get("SESSION_HANDOFF_AGENT", DEFAULT_AGENT),
    )
    import_source = import_bundle.add_mutually_exclusive_group(required=True)
    import_source.add_argument("--from-api", metavar="STREAM", help="Fetch the latest bundle for this stream.")
    import_source.add_argument("--file", type=Path, help="Read a local/scp/rsync .tgz bundle.")
    import_bundle.add_argument("--stream", help="Expected stream id for a file import.")
    import_bundle.add_argument("--force", action="store_true", help="Archive a newer local copy before installing.")
    import_bundle.set_defaults(func=cmd_import_bundle)

    check = subparsers.add_parser("check", help="Detect stale or unsafe handoff state.")
    check.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    check.add_argument("--lineage-id", type=argparse_lineage_id)
    check.add_argument("--state-file", type=Path)
    check.add_argument("--stale-hours", type=float, default=DEFAULT_STALE_HOURS)
    check.add_argument("--context-percent", type=float)
    check.add_argument("--context-threshold", type=float, default=DEFAULT_CONTEXT_THRESHOLD)
    check.set_defaults(func=cmd_check)

    audit = subparsers.add_parser(
        "audit", help="Inspect local task identity plus Codex thread/automation metadata."
    )
    audit.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    audit.add_argument("--include-monitor", action="store_true")
    audit.set_defaults(func=cmd_audit)

    detect = subparsers.add_parser(
        "detect", help="Detect task-identity-aware pending/resumed rollovers with structured conflict diagnostics."
    )
    detect.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    detect.add_argument("--current-thread-id", default="")
    detect.add_argument("--stream", help="Explicit launcher-derived stream id for the confirm/upload card.")
    detect.add_argument(
        "--task-family",
        default="",
        help=(
            "When multiple live packets exist, keep only candidates whose task_family "
            "matches this value (e.g. hramatka). Prefer launching with --epic so "
            "SessionStart can pass SESSION_EPIC here (#5398)."
        ),
    )
    detect.add_argument("--format", choices=("json", "session-start"), default="json")
    detect.set_defaults(func=cmd_detect)

    claim_thread_lease_parser = subparsers.add_parser(
        "claim-thread-lease",
        help="Atomically claim or refresh one agent slot's durable cold-start lease.",
    )
    claim_thread_lease_parser.add_argument("--agent", type=argparse_agent_name, required=True)
    claim_thread_lease_parser.add_argument("--current-thread-id", required=True)
    claim_thread_lease_parser.add_argument(
        "--starting-pid",
        type=int,
        default=None,
        help="Override the pid the harness-ancestor walk starts from (defaults to this process's own pid).",
    )
    claim_thread_lease_parser.set_defaults(func=cmd_claim_thread_lease)

    release_thread_lease_parser = subparsers.add_parser(
        "release-thread-lease",
        help="Release one agent slot's durable cold-start lease, e.g. from a SessionEnd hook.",
    )
    release_thread_lease_parser.add_argument("--agent", type=argparse_agent_name, required=True)
    release_thread_lease_parser.add_argument("--current-thread-id", default="")
    release_thread_lease_parser.add_argument(
        "--generation",
        type=int,
        default=None,
        help=(
            "Optional when this process's identity can be reconfirmed against the lease "
            "(the strictly stronger fence); required otherwise (fail closed). Never read back "
            "off the on-disk lease as a substitute."
        ),
    )
    release_thread_lease_parser.add_argument(
        "--starting-pid",
        type=int,
        default=None,
        help="Override the pid the harness-ancestor identity walk starts from (defaults to this process's own pid).",
    )
    release_thread_lease_parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Operator escape hatch: CAS-scoped, requires --expect-owner-thread-id and "
            "--expect-generation (a bare --force is refused, never an unscoped delete)."
        ),
    )
    release_thread_lease_parser.add_argument(
        "--expect-owner-thread-id",
        default=None,
        help="Required with --force: the exact owner_thread_id the operator observed on the lease.",
    )
    release_thread_lease_parser.add_argument(
        "--expect-generation",
        type=int,
        default=None,
        help="Required with --force: the exact generation the operator observed on the lease.",
    )
    release_thread_lease_parser.add_argument(
        "--acknowledge-live-owner",
        action="store_true",
        help="Required with --force when the recorded owner process is verifiably alive.",
    )
    release_thread_lease_parser.set_defaults(func=cmd_release_thread_lease)

    refresh_heartbeat_parser = subparsers.add_parser(
        "refresh-thread-lease-heartbeat",
        help=(
            "Best-effort heartbeat refresh for the lease this exact thread already owns "
            "(Stop and PostToolUse hooks)."
        ),
    )
    refresh_heartbeat_parser.add_argument("--agent", type=argparse_agent_name, required=True)
    refresh_heartbeat_parser.add_argument("--current-thread-id", required=True)
    refresh_heartbeat_parser.add_argument(
        "--generation",
        type=int,
        default=None,
        help=(
            "Optional when this process's identity can be reconfirmed against the lease "
            "(the strictly stronger fence); when supplied, also enforced as an extra fence "
            "(the exact generation this session claimed at SessionStart, e.g. "
            "$LEARN_UKRAINIAN_THREAD_LEASE_GENERATION)."
        ),
    )
    refresh_heartbeat_parser.add_argument("--starting-pid", type=int, default=None)
    refresh_heartbeat_parser.add_argument(
        "--min-refresh-interval-seconds",
        type=float,
        default=None,
        help=(
            "Throttle: no-op (cheap read only) unless the existing heartbeat is older than "
            "this many seconds. Omit for an unconditional refresh (e.g. the Stop hook)."
        ),
    )
    refresh_heartbeat_parser.set_defaults(func=cmd_refresh_thread_lease_heartbeat)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
