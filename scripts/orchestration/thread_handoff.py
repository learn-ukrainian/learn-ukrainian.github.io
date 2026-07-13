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
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from collections.abc import Mapping
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from scripts import context_canary
    from scripts.orchestration import thread_handoff_canary
except ModuleNotFoundError as exc:
    if __package__ or exc.name != "scripts":
        raise
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import context_canary
    import thread_handoff_canary

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
# Rollover warn point as a percent of the context window. Raised 82.0 → 88.0
# (user direction 2026-06-15): Opus 4.8 has NO >200K long-context premium and no
# brain-rot cliff, so staying high is cheap (cache-read tax ≈ $0.50 per 1M-of-context
# per turn) — warn later to avoid early-nag and waste less of the window. 88% on a 1M
# window ≈ 880K, leaving ~120K margin below the hard wall for the handoff write (~35K)
# + clean-execution headroom. Measure context deterministically, not by gut estimate
# (self-estimate runs ~1.8× high; see memory/MEMORY.md #2).
DEFAULT_CONTEXT_THRESHOLD = 88.0


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


def lineage_id_for(agent: str, active_thread_id: str) -> str:
    """Derive a stable, path-safe lineage for one active runtime thread."""
    digest = hashlib.sha256(f"{agent}\0{active_thread_id.strip()}".encode()).hexdigest()
    return f"lineage-{digest[:24]}"


def runtime_dir(agent: str, lineage_id: str, generation: int, rollover_id: str) -> Path:
    return Path(".agent/thread-rollovers") / agent / lineage_id / f"generation-{generation:04d}" / rollover_id


def default_state_path(agent: str, lineage_id: str) -> Path:
    return Path(".agent/thread-rollovers") / agent / lineage_id / "lease.json"


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
    except ValueError:
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
            str(item.get("path") or "unknown") if isinstance(item, dict) else "unknown"
            for item in modified_files[:5]
        )
        raise ValueError(f"source checkout must be clean before prepare; dirty paths: {paths}")
    return {"full_head": full_head, "clean": True}


def source_checkout_binding_error(replacement: Mapping[str, Any]) -> str | None:
    binding = replacement.get("source_checkout")
    if not isinstance(binding, dict):
        return "live rollover is missing its source checkout binding"
    if set(binding) != {"full_head", "clean"}:
        return "live rollover source checkout binding is malformed"
    if binding.get("clean") is not True:
        return "live rollover source checkout binding is not clean"
    full_head = binding.get("full_head")
    if not isinstance(full_head, str) or not full_head.strip():
        return "live rollover source checkout HEAD is malformed"
    return None


def checkout_continuity_error(
    replacement: Mapping[str, Any], current_git_state: Mapping[str, Any]
) -> str | None:
    binding_error = source_checkout_binding_error(replacement)
    if binding_error:
        return binding_error
    current_head = current_git_state.get("full_head")
    if not isinstance(current_head, str) or not current_head.strip():
        return "invoking checkout HEAD could not be determined"
    expected_head = replacement["source_checkout"]["full_head"]
    if current_head != expected_head:
        return f"invoking checkout HEAD {current_head} does not match prepared HEAD {expected_head}"
    modified_files = current_git_state.get("modified_files")
    if not isinstance(modified_files, list):
        return "invoking checkout status could not be determined"
    if modified_files:
        paths = ", ".join(
            str(item.get("path") or "unknown") if isinstance(item, dict) else "unknown"
            for item in modified_files[:5]
        )
        return f"invoking checkout must be clean; dirty paths: {paths}"
    return None


def require_checkout_continuity(replacement: Mapping[str, Any], repo_root: Path) -> None:
    error = checkout_continuity_error(replacement, gather_git_state(repo_root))
    if error:
        raise ValueError(f"checkout continuity failed: {error}")


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


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def active_thread_id_from_env() -> str | None:
    return os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID")


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
) -> dict[str, Any]:
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema v2 state is required; migrate v1 explicitly before preparing")
    if not active_thread_id:
        raise ValueError("--active-thread-id (or CODEX_THREAD_ID) is required for a v2 rollover")

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
    replacement = {
        "rollover_id": rollover_id,
        "lineage_id": lineage_id,
        "generation": generation,
        "status": "pending_start",
        "prepared_at": isoformat_z(now),
        "thread_id": None,
        "canary_challenge": new_canary_challenge(),
        **packet_paths,
    }
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
    replacement = state.get("replacement")
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
    if replacement.get("status") != "resumed":
        raise ValueError("replacement must be resumed through the rollover packet before confirmation")
    if replacement.get("resumed_thread_id") != new_thread_id.strip():
        raise ValueError("--new-thread-id does not match the thread that resumed this rollover")
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
    existing = replacement.get("resumed_thread_id")
    if existing and existing != thread_id:
        raise ValueError("pending rollover is already bound to a different replacement thread")
    if existing == thread_id:
        return state
    replacement["status"] = "resumed"
    replacement["resumed_thread_id"] = thread_id
    replacement.setdefault("resumed_at", isoformat_z(now))
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


def context_line(context_percent: float | None, threshold: float) -> str:
    if context_percent is None:
        return "Context percent was not supplied; use --context-percent from a statusline or manual estimate."
    state = "ROLL OVER NOW" if context_percent >= threshold else "below rollover threshold"
    return f"Context estimate: {context_percent:.1f}% ({state}; threshold {threshold:.1f}%)."


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
    git = snapshot["git"]
    monitor = snapshot["monitor"]
    github = snapshot["github"]
    active = state.get("active") or {}
    replacement = state.get("replacement") or {}
    prompt_path = replacement.get("bootstrap_prompt_path") or "unknown"
    handoff_path = handoff_path or Path(replacement.get("handoff_path") or "unknown")
    role_handoff_path = role_handoff_path or default_handoff_path(agent)
    handoff_text = role_handoff_path.as_posix()
    thread_handoff_text = handoff_path.as_posix()
    active_generation = active.get("generation") or "unknown"
    replacement_generation = replacement.get("generation") or "unknown"
    rollover_id = replacement.get("rollover_id") or "unknown"
    canary_challenge = replacement.get("canary_challenge") or "unknown"
    canary_proof_path = Path(replacement.get("canary_proof_path") or "unknown")
    semantic_snapshot_path = Path(replacement.get("semantic_snapshot_path") or "unknown")
    strict_probe_path = Path(replacement.get("strict_probe_path") or "unknown")
    strict_questions_path = Path(replacement.get("strict_questions_path") or "unknown")
    strict_answers_path = Path(replacement.get("strict_answers_path") or "unknown")
    strict_verdict_path = Path(replacement.get("strict_verdict_path") or "unknown")
    if state_root is not None:
        canary_proof_path = repo_local_path(state_root, canary_proof_path)
        semantic_snapshot_path = repo_local_path(state_root, semantic_snapshot_path)
        strict_probe_path = repo_local_path(state_root, strict_probe_path)
        strict_questions_path = repo_local_path(state_root, strict_questions_path)
        strict_answers_path = repo_local_path(state_root, strict_answers_path)
        strict_verdict_path = repo_local_path(state_root, strict_verdict_path)
    context_percent = (state.get("last_handoff") or {}).get("context_percent")
    agent_label = "Codex orchestrator" if agent == "orchestrator" else agent

    return (
        "\n".join(
            [
                f"Work locally in {git.get('repo_root')}.",
                "",
                f"You are the replacement {agent_label} thread.",
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
                f"- Keep the invoking checkout clean at prepared HEAD {replacement.get('source_checkout', {}).get('full_head', 'unknown')} through resume and confirmation.",
                "- Keep the main checkout read-only; thread rollover state belongs in gitignored .agent/ files.",
                "- Use dispatch worktrees for implementation work: .worktrees/dispatch/<agent>/<task>/.",
                "- Do not edit generated status/audit/review artifacts, linter configs, or .python-version.",
                "- Do not write docs/session-state/current.md for thread rollover.",
                "- Do not delete or migrate the old heartbeat automation until the confirm-started command below has succeeded.",
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
                "Bind this new thread and complete the strict semantic recall before proof and confirmation:",
                "```bash",
                f".venv/bin/python scripts/orchestration/thread_handoff.py resume --agent {agent} --lineage-id {replacement.get('lineage_id', 'unknown')} --rollover-id {rollover_id} --replacement-thread-id <replacement-thread-id>",
                f".venv/bin/python scripts/context_canary.py mint --snapshot {semantic_snapshot_path.as_posix()} --out {strict_probe_path.as_posix()}",
                f".venv/bin/python scripts/context_canary.py questions --probe {strict_probe_path.as_posix()} --out {strict_questions_path.as_posix()}",
                f".venv/bin/python scripts/context_canary.py score --probe {strict_probe_path.as_posix()} --answers {strict_answers_path.as_posix()} --expected-lineage-id {replacement.get('lineage_id', 'unknown')} --expected-rollover-id {rollover_id} --verdict {strict_verdict_path.as_posix()}",
                f".venv/bin/python scripts/orchestration/thread_handoff_canary.py --rollover-id {rollover_id} --replacement-thread-id <replacement-thread-id> --challenge {canary_challenge} --proof-file {canary_proof_path.as_posix()}",
                f".venv/bin/python scripts/orchestration/thread_handoff.py confirm-started --agent {agent} --lineage-id {replacement.get('lineage_id', 'unknown')} --rollover-id {rollover_id} --new-thread-id <replacement-thread-id> --canary-proof {canary_proof_path.as_posix()} --strict-probe {strict_probe_path.as_posix()} --strict-verdict {strict_verdict_path.as_posix()}",
                "```",
                "",
                "Only after that command reports old_automation_ready_to_delete=true may the old heartbeat automation be deleted or paused.",
                "",
                "Current snapshot:",
                f"- Branch: {git.get('branch')} @ {git.get('head')}",
                f"- {context_line(float(context_percent) if context_percent is not None else None, context_threshold)}",
                f"- Active delegates: {(monitor.get('active_delegates') or {}).get('total', 'unknown') if isinstance(monitor.get('active_delegates'), dict) else 'unknown'}",
                f"- Open PRs: {len(github.get('open_prs')) if isinstance(github.get('open_prs'), list) else 'unknown'}",
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
    monitor = snapshot["monitor"]
    github = snapshot["github"]
    active = state.get("active") or {}
    replacement = state.get("replacement") or {}
    cleanup = state.get("cleanup") or {}
    handoff = state.get("last_handoff") or {}
    prompt_path = replacement.get("bootstrap_prompt_path") or "unknown"
    thread_handoff_text = replacement.get("handoff_path") or "unknown"
    canary_proof_path = Path(replacement.get("canary_proof_path") or "unknown")
    strict_probe_path = Path(replacement.get("strict_probe_path") or "unknown")
    strict_questions_path = Path(replacement.get("strict_questions_path") or "unknown")
    strict_answers_path = Path(replacement.get("strict_answers_path") or "unknown")
    strict_verdict_path = Path(replacement.get("strict_verdict_path") or "unknown")
    semantic_snapshot_path = Path(replacement.get("semantic_snapshot_path") or "unknown")
    if state_root is not None:
        canary_proof_path = repo_local_path(state_root, canary_proof_path)
        strict_probe_path = repo_local_path(state_root, strict_probe_path)
        strict_questions_path = repo_local_path(state_root, strict_questions_path)
        strict_answers_path = repo_local_path(state_root, strict_answers_path)
        strict_verdict_path = repo_local_path(state_root, strict_verdict_path)
        semantic_snapshot_path = repo_local_path(state_root, semantic_snapshot_path)
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
        "## Context Budget",
        "",
        context_line(
            float(handoff["context_percent"]) if handoff.get("context_percent") is not None else None,
            context_threshold,
        ),
        "",
        "## Git State",
        "",
        f"- Repo: `{git.get('repo_root')}`",
        f"- Branch: `{git.get('branch')}`",
        f"- HEAD: `{git.get('head')}` (`{git.get('full_head')}`)",
        f"- Upstream: `{(git.get('ahead_behind') or {}).get('upstream', 'none')}`",
        f"- Ahead/behind: `{git.get('ahead_behind')}`",
        "",
        "### Last 5 Commits",
        "",
        summarize_commits(git.get("last_commits") or []),
        "",
        "### Modified Files",
        "",
        summarize_modified_files(git.get("modified_files") or []),
        "",
        "## Open PRs",
        "",
        summarize_prs(github.get("open_prs")),
        "",
        "## Open Issues",
        "",
        summarize_issues(github.get("open_issues")),
        "",
        "## Delegated Tasks",
        "",
        "### Active",
        "",
        summarize_tasks(monitor.get("active_delegates")),
        "",
        "### Recently Completed",
        "",
        summarize_tasks(monitor.get("completed_delegates")),
        "",
        "## Worktrees",
        "",
        f"- Count: `{(monitor.get('worktrees') or {}).get('count', 'unknown') if isinstance(monitor.get('worktrees'), dict) else 'unknown'}`",
        "",
        "## First-Turn Checklist",
        "",
        *first_turn_checklist_lines(
            repo_root=str(git.get("repo_root")),
            thread_handoff_text=thread_handoff_text,
            role_handoff_text=role_handoff,
        ),
        "",
        "## Local Monitor Follow-Up",
        "",
        "```bash",
        "curl -sS http://127.0.0.1:8765/api/delegate/active",
        "curl -sS http://127.0.0.1:8765/api/worktrees",
        ".venv/bin/python scripts/orchestration/orchestrator_control.py inbox --recent 20 --include-results",
        "```",
        "",
        "## Replacement Bootstrap Prompt",
        "",
        "Paste the generated bootstrap prompt into a new thread. This protocol does not fork, continue, or resume provider conversation history.",
        "After the new thread is actually running, bind and prove this exact rollover:",
        "",
        "```bash",
        f".venv/bin/python scripts/orchestration/thread_handoff.py resume --agent {agent} --lineage-id {replacement.get('lineage_id', '<lineage-id>')} --rollover-id {replacement.get('rollover_id', '<rollover-id>')} --replacement-thread-id <replacement-thread-id>",
        f".venv/bin/python scripts/context_canary.py mint --snapshot {semantic_snapshot_path.as_posix()} --out {strict_probe_path.as_posix()}",
        f".venv/bin/python scripts/context_canary.py questions --probe {strict_probe_path.as_posix()} --out {strict_questions_path.as_posix()}",
        f".venv/bin/python scripts/context_canary.py score --probe {strict_probe_path.as_posix()} --answers {strict_answers_path.as_posix()} --expected-lineage-id {replacement.get('lineage_id', '<lineage-id>')} --expected-rollover-id {replacement.get('rollover_id', '<rollover-id>')} --verdict {strict_verdict_path.as_posix()}",
        f".venv/bin/python scripts/orchestration/thread_handoff_canary.py --rollover-id {replacement.get('rollover_id', '<rollover-id>')} --replacement-thread-id <replacement-thread-id> --challenge {replacement.get('canary_challenge', '<canary-challenge>')} --proof-file {canary_proof_path.as_posix()}",
        f".venv/bin/python scripts/orchestration/thread_handoff.py confirm-started --agent {agent} --lineage-id {replacement.get('lineage_id', '<lineage-id>')} --rollover-id {replacement.get('rollover_id', '<rollover-id>')} --new-thread-id <replacement-thread-id> --canary-proof {canary_proof_path.as_posix()} --strict-probe {strict_probe_path.as_posix()} --strict-verdict {strict_verdict_path.as_posix()}",
        "```",
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

    if context_percent is not None and context_percent >= context_threshold:
        warnings.append(f"context estimate {context_percent:.1f}% is at/above threshold {context_threshold:.1f}%")

    return facts, warnings


def cmd_prepare(args: argparse.Namespace) -> int:
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
                    "error": "--active-thread-id (or CODEX_THREAD_ID) is required for a v2 rollover",
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
    try:
        prepared_state = prepare_state(
            state,
            agent=agent,
            now=now,
            active_thread_id=active_thread_id,
            active_automation_id=args.active_automation_id,
            context_percent=args.context_percent,
            force_new_replacement=args.force_new_replacement,
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
            "bootstrap_prompt": prompt,
        }
        print(json.dumps(output, indent=2))
        return 0

    write_text_atomic(bootstrap_path, prompt)
    write_text_atomic(handoff_path, handoff_md)
    write_json_atomic(state_path, prepared_state)
    wrote_router = False
    if args.write_current:
        write_text_atomic(router_path, router_md)
        wrote_router = True

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
    }
    print(json.dumps(output, indent=2))
    return 0


def cmd_confirm_started(args: argparse.Namespace) -> int:
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
    write_json_atomic(state_path, confirmed)
    print(
        json.dumps(
            {
                "agent": agent,
                "lineage_id": confirmed.get("lineage_id"),
                "rollover_id": confirmed["replacement"]["rollover_id"],
                "state_file": rel(state_path, state_root),
                "replacement_status": confirmed["replacement"]["status"],
                "replacement_thread_id": confirmed["replacement"]["thread_id"],
                "old_automation_ready_to_delete": confirmed["cleanup"]["old_automation_ready_to_delete"],
            },
            indent=2,
        )
    )
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
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
    write_json_atomic(state_path, resumed)
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
                "strict_questions_file": replacement["strict_questions_path"],
                "strict_answers_file": replacement["strict_answers_path"],
                "strict_verdict_file": replacement["strict_verdict_path"],
                "status": replacement["status"],
            },
            indent=2,
        )
    )
    return 0


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
    print(json.dumps(audit, indent=2))
    return 0


def render_session_start_context(candidate: dict[str, Any] | None, *, agent: str, current_thread_id: str) -> str:
    """Render the only SessionStart handoff text; shell hooks never parse leases."""
    if candidate is None:
        facts_path = ".agent/orientation-health-facts.json"
        return "\n".join(
            [
                "COLD START: NO LIVE THREAD ROLLOVER",
                "No pending or resumed packet exists for this agent.",
                "Orient from durable project state with tool-backed reads before ordinary work.",
                "Create exactly ten truthful legacy orientation facts, then run:",
                f".venv/bin/python scripts/context_canary.py mint --facts {facts_path} --out .agent/orientation-health-probe.json",
                "Do not invent a lineage_id or rollover_id; prepare creates both only when this thread later rolls over.",
                "Keep the primary checkout read-only and use a dispatch worktree for implementation.",
            ]
        )
    thread_id = current_thread_id or "<current-codex-thread-id>"
    lineage_id = candidate["lineage_id"]
    rollover_id = candidate["rollover_id"]
    base = [
        f"--agent {agent}",
        f"--lineage-id {lineage_id}",
        f"--rollover-id {rollover_id}",
    ]
    proof = candidate["canary_proof_path"]
    snapshot = candidate["semantic_snapshot_path"]
    probe = candidate["strict_probe_path"]
    questions = candidate["strict_questions_path"]
    answers = candidate["strict_answers_path"]
    verdict = candidate["strict_verdict_path"]
    common = " ".join(base)
    if candidate["status"] == "resumed":
        title = "RESUMED THREAD ROLLOVER DETECTED"
        first = "This same Codex thread already holds the packet; do not resume it again."
    else:
        title = "PENDING THREAD ROLLOVER DETECTED"
        first = "Claim this packet before ordinary work:"
    lines = [title, first]
    if candidate["status"] == "pending_start":
        lines.append(
            f".venv/bin/python scripts/orchestration/thread_handoff.py resume {common} --replacement-thread-id {thread_id}"
        )
    lines.extend(
        [
            f"Read the packet: {candidate['handoff_path']}",
            f"Write the validated durable semantic snapshot to its reserved path: {snapshot}",
            f".venv/bin/python scripts/context_canary.py mint --snapshot {snapshot} --out {probe}",
            f".venv/bin/python scripts/context_canary.py questions --probe {probe} --out {questions}",
            f'Answer only the IDs/questions in {questions} from restored context; write {{"id": "answer"}} JSON to {answers}.',
            f".venv/bin/python scripts/context_canary.py score --probe {probe} --answers {answers} --expected-lineage-id {lineage_id} --expected-rollover-id {rollover_id} --verdict {verdict}",
            f".venv/bin/python scripts/orchestration/thread_handoff_canary.py --rollover-id {rollover_id} --replacement-thread-id {thread_id} --challenge {candidate['canary_challenge']} --proof-file {proof}",
            f".venv/bin/python scripts/orchestration/thread_handoff.py confirm-started {common} --new-thread-id {thread_id} --canary-proof {proof} --strict-probe {probe} --strict-verdict {verdict}",
            "Do not auto-run any mutation above. Cleanup remains locked unless both exact proofs pass.",
        ]
    )
    return "\n".join(lines)


def cmd_detect(args: argparse.Namespace) -> int:
    try:
        _, state_root = resolve_roots(args.repo_root)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2
    agent = normalize_agent_name(args.agent)

    agent_dir = state_root / ".agent" / "thread-rollovers" / agent
    if not agent_dir.exists():
        output: dict[str, Any] = {"agent": agent, "status": "none"}
        print(
            render_session_start_context(None, agent=agent, current_thread_id=args.current_thread_id)
            if args.format == "session-start"
            else json.dumps(output, indent=2)
        )
        return 0

    live_leases: list[tuple[Path, dict[str, Any], dict[str, Any]]] = []

    for path in sorted(agent_dir.glob("*/lease.json")):
        state = load_state(path)
        replacement, error = validate_live_lease(state, agent=agent, state_path=path)
        if error:
            print(json.dumps({"error": f"invalid rollover lease {rel(path, state_root)}: {error}"}, indent=2))
            return 2
        if replacement is not None and replacement["status"] in {"pending_start", "resumed"}:
            live_leases.append((path, state, replacement))

    if not live_leases:
        output = {"agent": agent, "status": "none"}
        print(
            render_session_start_context(None, agent=agent, current_thread_id=args.current_thread_id)
            if args.format == "session-start"
            else json.dumps(output, indent=2)
        )
        return 0

    if len(live_leases) > 1:
        print(
            json.dumps({"error": f"Multiple live pending rollovers found for agent {agent} in {agent_dir}"}, indent=2)
        )
        return 2

    path, state, replacement = live_leases[0]
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
        "lineage_id": state.get("lineage_id"),
        "rollover_id": replacement.get("rollover_id"),
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
    }
    print(
        render_session_start_context(output, agent=agent, current_thread_id=args.current_thread_id)
        if args.format == "session-start"
        else json.dumps(output, indent=2)
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--monitor-base-url", default=os.environ.get("MONITOR_API_BASE_URL", DEFAULT_MONITOR_BASE_URL))
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
    prepare.add_argument("--context-percent", type=float)
    prepare.add_argument("--context-threshold", type=float, default=DEFAULT_CONTEXT_THRESHOLD)
    prepare.add_argument("--force-new-replacement", action="store_true")
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

    check = subparsers.add_parser("check", help="Detect stale or unsafe handoff state.")
    check.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    check.add_argument("--lineage-id", type=argparse_lineage_id)
    check.add_argument("--state-file", type=Path)
    check.add_argument("--stale-hours", type=float, default=DEFAULT_STALE_HOURS)
    check.add_argument("--context-percent", type=float)
    check.add_argument("--context-threshold", type=float, default=DEFAULT_CONTEXT_THRESHOLD)
    check.set_defaults(func=cmd_check)

    audit = subparsers.add_parser("audit", help="Inspect local Codex thread/automation metadata.")
    audit.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    audit.add_argument("--include-monitor", action="store_true")
    audit.set_defaults(func=cmd_audit)

    detect = subparsers.add_parser("detect", help="Detect a single pending/resumed thread rollover.")
    detect.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    detect.add_argument("--current-thread-id", default="")
    detect.add_argument("--format", choices=("json", "session-start"), default="json")
    detect.set_defaults(func=cmd_detect)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
