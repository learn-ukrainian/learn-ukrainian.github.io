#!/usr/bin/env python
"""delegate.py — async task dispatch over agent_runtime.

Layer 3 of the #1184 architecture (see watchdog.py::should_kill for the
incident chain that led here). This module is the "fire and wait later"
execution model: callers dispatch a task, get a task-id back
immediately, and poll/wait at their own pace. No heuristic stall
detection, no speculative kills, no 30-minute caller blocks. The user
controls how long to wait.

CLI:

    # Fire a task. Returns immediately with the task-id.
    # Write-capable modes (workspace-write / danger) require a dispatch worktree.
    delegate.py dispatch --agent codex --task-id my-task \
        --prompt "do the thing" [--mode workspace-write --worktree] [--model gpt-6-sol]
        [--allow-merge] [--force-new]

    # Check status without blocking.
    delegate.py status my-task
    → {"status": "running", "pid": 12345, "elapsed_s": 42.1, ...}
    → {"status": "done",    "result_file": ".../my-task.result", ...}
    → {"status": "failed",  "stderr_excerpt": "...", ...}
    → {"status": "crashed", "reason": "pid 12345 is dead but state says running"}

    # Guardrail check for stale async-task claims.
    delegate.py status-or-fail my-task
    → exits 0 only when Monitor API says the task is currently running

    # Wait for completion. Polls at 2s intervals.
    delegate.py wait my-task [--timeout 3600]

State files live at ``batch_state/tasks/<task-id>.json``. Format:

    {
        "task_id": str,
        "run_nonce": str,           # unique run identifier for split-brain detection (#7168)
        "repository": str | null,   # authoritative "owner/repo" of the dispatch target (#7083)
        "agent": str,
        "model": str,
        "resolved_model": str,  # Cursor's concrete model, or "unknown"
        "resolved_model_known": bool,
        "resolved_model_source": str,
        "effort": str,
        "cli_version": str,
        "mode": str,
        "pid": int,
        "status": "running" | "done" | "failed" | "timeout" | "rate_limited" | "crashed"
                  | "needs_finalize" | "no_deliverable",
        "started_at": iso-8601 UTC,
        "finished_at": iso-8601 UTC | null,
        "duration_s": float | null,
        "prompt_chars": int,
        "prompt_sha256": str,        # sha256 of the prompt as given (--prompt/--prompt-file), before appended blocks
        "effective_prompt_sha256": str,  # sha256 of the final prompt handed to the worker, after every appended block
        "prompt_blocks": [str],      # kinds of the blocks delegate added, in prompt order: "worktree", "lifecycle", "research"
        "review_attempt": {review_id, attempt_id, manifest_sha256} | absent,  # --review-attempt dispatches only (#9022)
        "dispatch_args_sha256": str,  # sha256 of every parsed `dispatch` arg except DISPATCH_ARGS_HASH_EXCLUDED_FIELDS
        "response_chars": int | null,
        "result_file": str | null,   # path to the full response text
        "stderr_excerpt": str | null,
        "returncode": int | null,
        "returncode_reason": str | null,
        "require_review_verdict": bool,  # opt-in bridge review completion gate
        "failure_reason": str | null,  # named cause on failed verdict-required reviews
        "launch_mode": "scope" | "popen-fallback",  # #8645 part C
        "launch_unit": str | null,                  # scope unit when launch_mode is scope
        "launch_fallback_reason": str | null,
        "peak_rss_mib": float | null,               # terminal records; largest reaped child
        "owned_paths": [str] | absent,              # the --owned-path values: auto-finalize scope (#8991)
        "leftovers_scan": "clear" | "live" | "unknown" | absent,  # exit scan of the worker's scope
        "leftovers_scope": {task_id, launch_mode, unit, cgroup, run_nonce, ...} | absent,
        "leftovers_scan_error": str | absent,       # why the scan was unknown
        "incomplete_run_reason": "background_jobs_alive_at_exit" | "leftovers_scan_unknown" | absent,
        "background_jobs_alive_at_exit": {reason, count, processes: [{pid, cmdline}], scope} | absent,
        "finalize_skipped_paths": [str] | absent,   # changed files auto-finalize left out of its commit
        "kimi_content_refusal": str | absent        # a Kimi diff held Cyrillic text or content that is not plain text; nothing was committed
    }

Design notes:

* Zombie detection. ``os.kill(pid, 0)`` is the POSIX way to ask "is this
  PID alive?" without sending a signal. The ``status`` command does this
  whenever it reads a state file that says ``running``. If the PID is
  dead but the file still says running, we mark the state file
  ``crashed`` — this catches OOM kills, machine reboots, and any other
  abrupt termination of the worker process.

* PID recycling is theoretically possible (the OS reuses PIDs), but in
  practice a PID from minutes ago is extremely unlikely to be recycled
  AND owned by a process matching our command line. For the short-lived
  nature of agent tasks this is acceptable. A fully bulletproof version
  would record the process start_time from ``/proc/<pid>/stat`` (Linux)
  or ``kvm_getprocs`` (BSD/macOS) and re-verify — deferred as over-engineering
  for the current scale.

* Atomic writes. Every state-file update goes via write-rename so a
  concurrent reader never sees a half-written JSON. ``os.replace`` is
  atomic on POSIX.

* No lock contention on the state dir. Each task owns its own file;
  there's no shared index, no global lock.

* Quota safety. The detached worker calls ``agent_runtime.runner.invoke``
  which already consults ``has_headroom`` before spawning the CLI — so
  you can't stampede the provider by firing many delegate tasks in a
  row if the last one got rate-limited.

* Dual-host VPS placement. When healthy VPS occupancy hosts are available
  and the local retired marker exists, ``dispatch`` forwards execution
  over BatchMode SSH to the remote host.
  Host environment contract:
  - ``LU_JOB_DISPATCH_HOST`` (or ``ATLAS_RUNNER_HOST``) and ``LU_JOB_REPO``
  - ``LU_TEACHER_DISPATCH_HOST`` (or ``LU_DISPATCH_SSH``) and ``LU_TEACHER_REPO``
  - ``LU_ALLOW_NOTEBOOK_DISPATCH=1`` bypasses VPS forwarding to force local spawn.
  Configuration errors fail closed without fallback to preserve visibility.

Issue: #1184, #7230.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import functools
import hashlib
import json
import logging
import os
import re
import resource
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agent_runtime.routes import RUNTIME_ROUTE_TOOL_CONFIG_KEY

# Resolve repo root from this file's location so we work from any cwd —
# then hop to the primary checkout so worktree copies behave identically.
_local_repo_root = Path(__file__).resolve().parents[1]
if str(_local_repo_root) not in sys.path:
    sys.path.insert(0, str(_local_repo_root))

from scripts.api.subscription_usage import pace_is_deficit, pace_is_visible
from scripts.common.repo_root import main_checkout_root as _main_checkout_root  # noqa: F401  # compatibility seam
from scripts.common.repo_root import project_interpreter, resolve_repo_root
from scripts.common.scratch import (
    DEFAULT_SCRATCH_ROOT,
    ensure_scratch_root,
    fallback_scratch_root,
    resolve_scratch_root,
    scratch_scan_roots,
)
from scripts.common.task_store_paths import tasks_dir
from scripts.config import (
    DELEGATE_WORKTREE_ADD_MAX_S,
    DELEGATE_WORKTREE_ADD_STALL_S,
    DELEGATE_WORKTREE_ADD_TIMEOUT_S,
)
from scripts.fleet.reset_reserve import codex_is_threatened as _codex_is_threatened
from scripts.fleet.reset_reserve import codex_reset_reserve_eligible as _codex_reset_reserve_eligible
from scripts.fleet.reset_reserve import load_reset_reserve as _load_reset_reserve
from scripts.orchestration import (
    dispatch_admission,
    dispatch_isolation,
    reaper_lifecycle,
    task_record_store,
    worker_leftovers,
    worktree_claims,
    worktree_prep,
)
from scripts.orchestration.dead_worker_state import (
    mark_dead_worker_terminal,
    mark_orphaned_admission_hold_crashed,
    mark_orphaned_worktree_prep_crashed,
    task_state_lock,
    write_state_unlocked,
)

_REPO_ROOT = resolve_repo_root(Path(__file__), 1)
_BASH_SECRETS_PATH = Path.home() / ".bash_secrets"
# The Gemini-family seat is intentionally absent in BOTH spellings: the
# retired ``gemini`` alias resolves to ``agy`` before Popen (#7041), so the
# strip has to attach to the resolved seat id ``agy`` — otherwise every
# ``--agent gemini`` dispatch would slip a parent operator ``GH_TOKEN`` /
# ``GITHUB_TOKEN`` back in through the alias. Intended App or
# ``LU_AGENT_GITHUB_TOKEN`` identity still reaches that CLI via
# ``build_agent_env`` (#7020).
_GH_TOKEN_AGENTS = {
    "bridge",
    "claude",
    "codex",
    "cursor",
    "deepseek",
    "glm",
    "grok",
    "grok-build",
    "grok-hermes",
    "kimi",
}
_RUNTIME_TMP_TERMINAL_STATUSES = frozenset(
    {
        "done",
        "failed",
        "timeout",
        "rate_limited",
        "cancelled",
        "crashed",
        "dry_run",
        "needs_finalize",
        "no_deliverable",
    }
)
_RUNTIME_TMP_ORPHAN_MAX_AGE_S = 7 * 24 * 60 * 60
_RUNTIME_TMP_SWEEP_ERROR_DETAILS_LIMIT = 10
_RUNTIME_TMP_TASK_ID_MARKER = ".delegate-task-id"
_READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX = ".snapshots"
# Task records must stay small enough for frequent reads during dispatch sweeps.
# Whole-checkout read-only snapshots live in ``<task>.snapshots/`` sidecars (#7203).
_READ_ONLY_CHECKOUT_RECORD_BYTE_BUDGET = 256 * 1024
_FALLBACK_SUBS_PATH = _REPO_ROOT / "scripts" / "config" / "agent_fallback_substitutions.yaml"
# Single source for dispatchable agents: argparse choices AND the hard-sub
# validation in _resolve_agent_with_budget_guard (a yaml typo must never
# dispatch a nonexistent adapter).
_DISPATCH_AGENT_CHOICES = (
    "codex",
    "gemini",  # permanent retired-CLI alias → agy (RETIRED_AGENT_ALIASES); gemini CLI not installed
    "claude",
    "grok",  # canonical native CLI seat
    "grok-build",  # permanent alias → grok
    "grok-hermes",  # demoted Hermes path
    "kimi",  # managed native kimi-code CLI seat; web, UI and backend coding only; no automatic fallback chain
    "deepseek",
    "agy",
    "cursor",
    "glm",
)
# "native" is accepted for explicit task-state attribution but is
# observability-only: KimiAdapter treats it identically to an omitted flag
# (#5938 F2). Only "kimicc" changes the transport.
_KIMI_HARNESSES = frozenset({"native", "kimicc"})
# Dispatch agent → effort validator. Keep this mapping at the dispatch
# boundary so an effort unsupported by a provider fails before a task state,
# worktree, runtime lease, or worker process is created. The native Grok alias
# deliberately shares the canonical adapter's vocabulary; grok-hermes is a
# different transport and must not inherit the native CLI restriction.
_EFFORT_VALIDATOR_BY_DISPATCH_AGENT = {
    "grok": "native_grok",
    "grok-build": "native_grok",
}
_MONITOR_API_BASE_URL = "http://127.0.0.1:8765"
_logger = logging.getLogger(__name__)

# Fields of the parsed `dispatch` Namespace that legitimately differ between
# otherwise-identical runs and carry no content of the request itself — the
# only fields ``dispatch_args_sha256`` excludes. Every other parsed `dispatch`
# argument (including --output-schema, --cwd, --worktree, --mode, --model,
# --effort, and every research/lifecycle flag) is bound into the hash, so a
# caller cannot smuggle an extra flag past a check that only names a subset
# of fields (#8430 R3-A r8).
DISPATCH_ARGS_HASH_EXCLUDED_FIELDS = {
    "run_nonce": "unique per attempt; only used for stale cross-host split-brain detection (#7168)",
    "force_new": "a retry/idempotency knob for reusing an existing --task-id, not part of what the seat is asked",
    "initiator": "orchestrator attribution metadata, auto-detected when omitted",
}
# argparse plumbing present on every subcommand's Namespace, not a CLI-supplied
# dispatch argument.
_DISPATCH_ARGS_HASH_ARGPARSE_KEYS = frozenset({"command", "func"})


def dispatch_args_sha256(args: argparse.Namespace) -> str:
    """sha256 of the canonical JSON of every parsed ``dispatch`` argument that binds the record.

    Additive to ``prompt_sha256``/``effective_prompt_sha256`` (which prove the prompt): this proves the
    *arguments* that produced the dispatch, so a record cannot pass a check that compares only a named
    subset of fields while carrying an unchecked extra flag (e.g. a caller-supplied --output-schema).
    Canonical means ``sort_keys=True`` and no separator whitespace, so the same arguments always hash the
    same regardless of argv order.
    """
    payload = {
        key: value
        for key, value in vars(args).items()
        if key not in DISPATCH_ARGS_HASH_EXCLUDED_FIELDS and key not in _DISPATCH_ARGS_HASH_ARGPARSE_KEYS
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _resolve_dispatch_harness(agent: str, harness: str | None) -> str | None:
    """Validate the opt-in Kimi harness selector without changing its seat."""
    if harness is None:
        return None
    if agent != "kimi":
        raise ValueError("--harness is currently supported only with --agent kimi")
    if harness not in _KIMI_HARNESSES:
        raise ValueError(f"unsupported Kimi harness {harness!r}; expected one of {sorted(_KIMI_HARNESSES)}")
    return harness


def _warn_kimicc_oauth_token_life(harness: str | None, hard_timeout: int) -> None:
    """Pre-flight note when a KimiCC dispatch can outlive its OAuth session (#5938 F4)."""
    if harness != "kimicc" or hard_timeout <= _KIMICC_OAUTH_SESSION_LIFE_S:
        return
    print(
        f"⚠️  --harness kimicc with --hard-timeout {hard_timeout}s exceeds the ~15-minute "
        "Kimi OAuth session lifetime; the wrapper refreshes the session only at spawn, "
        "so calls still running past ~15 minutes may fail auth. Prefer shorter dispatches "
        "and relaunch instead of one long call.",
        file=sys.stderr,
    )


def _validate_dispatch_effort(agent: str, effort: str | None) -> None:
    """Fail closed when a dispatch effort cannot reach its selected CLI.

    The top-level ``--effort`` parser accepts the cross-runtime vocabulary.
    Provider-specific limits belong here, before dispatch creates any durable
    task or process state. Revalidate after a budget substitution because that
    can change the effective provider.
    """
    if effort is None:
        return
    validator = _EFFORT_VALIDATOR_BY_DISPATCH_AGENT.get(agent.strip().lower())
    if validator == "native_grok":
        from agent_runtime.adapters.grok_build import validate_grok_effort

        try:
            validate_grok_effort(effort)
        except ValueError as exc:
            raise ValueError(
                f"--agent {agent} cannot use --effort {effort!r}: {exc}. "
                "Refusing before worker spawn; choose low, medium, or high, "
                "or omit --effort for the native Grok default."
            ) from exc


def _resolve_github_token() -> str | None:
    """Resolve the App-first GitHub token used by an agent shell."""
    from agent_runtime.agent_github_identity import resolve_agent_github_identity

    return resolve_agent_github_identity(bash_secrets_path=_BASH_SECRETS_PATH).token


def _inject_gh_token_for_agent(worker_env: dict[str, str], agent: str) -> None:
    """Inject the resolved agent identity for every dispatchable push lane."""
    worker_env.pop("GITHUB_TOKEN", None)
    if agent not in _GH_TOKEN_AGENTS:
        worker_env.pop("GH_TOKEN", None)
        return

    token = _resolve_github_token()
    if token:
        worker_env["GH_TOKEN"] = token
        return

    # Without an agent identity, do not allow a dispatch shell to inherit an
    # operator credential by accident through its parent environment.
    worker_env.pop("GH_TOKEN", None)


def _scrub_unusable_gh_config_dir(worker_env: dict[str, str]) -> None:
    """Drop empty/sandbox GH_CONFIG_DIR so review seats recover host gh (#7472).

    A prior agent-runtime token-mode (or pre-#7166) isolate leaves
    ``GH_CONFIG_DIR`` pointing at an empty dir. Inherited into the next
    read-only review dispatch, that makes ``gh`` report unauthenticated even
    when ``~/.config/gh/hosts.yml`` is valid. Only drop unusable paths; a
    real hosts.yml dir (or unset) is left alone. Never copies token values.
    """
    from agent_runtime.env_sanitize import usable_host_gh_config_dir

    current = worker_env.get("GH_CONFIG_DIR")
    if current and usable_host_gh_config_dir(current) is None:
        worker_env.pop("GH_CONFIG_DIR", None)


DEFAULT_HARD_TIMEOUT_S = 7200
# Silence timeout is a composite hang backstop: stdout/stderr, liveness-file
# updates, and process-tree CPU/disk activity all keep it alive. Do not lower it
# for build/test/enrich jobs merely because wrapper stdout is expected to be
# quiet; that recreates the false-kill shape from #3875.
DEFAULT_SILENCE_TIMEOUT_S = 3600
# Fail fast only when no observable startup activity occurs: stdout/stderr,
# documented liveness-file updates, or process-tree CPU/disk work. This is
# distinct from the long silence window above (#2071).
# 600s: reasoning-heavy models at high/max effort routinely think for minutes
# before their first token; the old 180s killed healthy workers mid-thought
# (observed: deepseek review dispatch reaped at 181s, 1s over the limit).
DEFAULT_INITIAL_RESPONSE_TIMEOUT_S = 600
# KimiCC headless calls authenticate with a Kimi OAuth session whose
# lifetime is roughly 15 minutes (~840s). The wrapper refreshes credentials
# only at spawn, so a worker still running past that point can start failing
# auth.
_KIMICC_OAUTH_SESSION_LIFE_S = 840
# Timeout bounds for synchronous subprocess invocations (#7213).
DEFAULT_GIT_TIMEOUT_S: float = 30.0
DEFAULT_NETWORK_GIT_TIMEOUT_S: float = 180.0
DEFAULT_GH_CLI_TIMEOUT_S: float = 180.0


# ---------------------------------------------------------------------------
# State file helpers
# ---------------------------------------------------------------------------


def _state_path_no_create(task_id: str) -> Path:
    """The task record's path, without creating the task directory (for readers that must not write)."""
    # task-ids with slashes would break paths; sanitize
    safe = task_id.replace("/", "_").replace("\\", "_")
    return tasks_dir() / f"{safe}.json"


def _state_path(task_id: str) -> Path:
    tasks_dir().mkdir(parents=True, exist_ok=True)
    return _state_path_no_create(task_id)


def _result_path(task_id: str) -> Path:
    return _state_path(task_id).with_suffix(".result")


def _archived_state_path(task_id: str) -> Path:
    """Where ``stale_task_records archive`` moved an old terminal record (#8625).

    Only terminal records are archived. By-id readers (status, wait, task-id
    reuse) fall back to this path; the worktree claim scan never needs it.
    """
    return task_record_store.archived_task_record_path(tasks_dir(), task_id)


def _read_state_or_archived(task_id: str) -> tuple[Path, dict[str, Any] | None]:
    """Return ``task_id``'s record path and state: the hot record, else the archived one (#8625).

    An archived state is marked ``archived: true`` and its ``result_file`` names
    the ``.result`` sidecar that moved into the archive with it. Archived
    records are terminal, so no caller ever rewrites one.
    """
    state_path = _state_path(task_id)
    state = _read_state(state_path)
    if state is not None:
        return state_path, state
    archived_path = _archived_state_path(task_id)
    archived = _read_state(archived_path)
    if archived is None:
        return state_path, None
    archived = {**archived, "archived": True}
    if "result_file" in archived:
        archived["result_file"] = task_record_store.relocated_result_file(archived_path, archived["result_file"])
    return archived_path, archived


def _generate_run_nonce() -> str:
    """Generate a unique run identifier to disambiguate dispatches (#7168)."""
    return uuid.uuid4().hex[:16]


def _archive_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def _archived_artifact_path(path: Path, stamp: str) -> Path:
    dest = path.with_name(f"{path.stem}.{stamp}.archived{path.suffix}")
    if dest.exists():
        dest = path.with_name(f"{path.stem}.{stamp}.{os.getpid()}.archived{path.suffix}")
    return dest


def _read_only_snapshot_dir_for(task_id: str) -> Path:
    state_path = _state_path(task_id)
    return state_path.parent / f"{state_path.stem}{_READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX}"


_READ_ONLY_SNAPSHOT_DIGEST_NAME = "digest.json"
_READ_ONLY_SNAPSHOT_RETENTION_DIGEST = "digest"
_READ_ONLY_SNAPSHOT_RETENTION_FULL = "full"


def _read_only_snapshot_sidecar_path(task_id: str, phase: str) -> Path:
    return _read_only_snapshot_dir_for(task_id) / f"read_only_checkout_{phase}.json"


def _read_only_snapshot_digest_path(task_id: str) -> Path:
    return _read_only_snapshot_dir_for(task_id) / _READ_ONLY_SNAPSHOT_DIGEST_NAME


def _write_read_only_snapshot_sidecar(
    task_id: str,
    phase: str,
    snapshot: dict[str, str] | None,
) -> None:
    """Persist a read-only checkout snapshot beside the task record."""
    path = _read_only_snapshot_sidecar_path(task_id, phase)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".json.tmp.{os.getpid()}")
    tmp.write_text(
        json.dumps(snapshot if snapshot is not None else {}, separators=(",", ":")),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _canonical_snapshot_bytes(snapshot: dict[str, str] | None) -> bytes:
    """Bytes written for a phase sidecar: compact JSON, empty object when missing."""
    payload = snapshot if isinstance(snapshot, dict) else {}
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _snapshot_digest_phase(snapshot: dict[str, str] | None) -> dict[str, Any]:
    raw = _canonical_snapshot_bytes(snapshot)
    payload = snapshot if isinstance(snapshot, dict) else {}
    return {"sha256": hashlib.sha256(raw).hexdigest(), "entries": len(payload)}


def read_only_snapshot_digest(
    pre: dict[str, str] | None,
    post: dict[str, str] | None,
) -> dict[str, Any]:
    """Content digest of the two canonical checkout snapshots."""
    return {"pre": _snapshot_digest_phase(pre), "post": _snapshot_digest_phase(post)}


def read_only_snapshot_keep_full(
    mutation_paths: list[str] | None,
    snapshot_error: str | None,
) -> bool:
    """Full sidecars stay only for a recorded mutation or a snapshot error."""
    return bool(mutation_paths) or snapshot_error is not None


def _read_only_phase_paths(snapshot_dir: Path) -> list[Path]:
    return [snapshot_dir / f"read_only_checkout_{phase}.json" for phase in ("pre", "post")]


def stage_read_only_snapshot_digest(
    snapshot_dir: Path,
    pre: dict[str, str] | None,
    post: dict[str, str] | None,
) -> int:
    """Write ``digest.json`` and leave the phase files in place.

    Returns the bytes a later discard would reclaim. Writing the digest first
    means a crash before the task record is published still leaves the full
    sidecars on disk.
    """
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    before = 0
    for path in _read_only_phase_paths(snapshot_dir):
        try:
            info = path.lstat()
        except OSError:
            continue
        if stat.S_ISREG(info.st_mode):
            before += info.st_size
    digest = read_only_snapshot_digest(pre, post)
    digest_path = snapshot_dir / _READ_ONLY_SNAPSHOT_DIGEST_NAME
    raw = json.dumps(digest, separators=(",", ":")).encode("utf-8")
    tmp = digest_path.with_suffix(f".json.tmp.{os.getpid()}")
    tmp.write_bytes(raw)
    os.replace(tmp, digest_path)
    return before - len(raw)


def discard_read_only_snapshot_phases(snapshot_dir: Path) -> None:
    """Unlink regular phase files. Symlinks are left in place."""
    for path in _read_only_phase_paths(snapshot_dir):
        try:
            info = path.lstat()
        except OSError:
            continue
        if stat.S_ISREG(info.st_mode):
            path.unlink()


def collapse_read_only_snapshot_dir(
    snapshot_dir: Path,
    pre: dict[str, str] | None,
    post: dict[str, str] | None,
) -> int:
    """Replace phase JSON with ``digest.json``. Return bytes reclaimed.

    The digest hashes the same canonical bytes ``_write_read_only_snapshot_sidecar``
    writes. Callers that still have to publish the task record must
    :func:`stage_read_only_snapshot_digest`, write the record, then
    :func:`discard_read_only_snapshot_phases`. This helper does both file steps
    and is for a caller that has already published the record.
    """
    reclaimed = stage_read_only_snapshot_digest(snapshot_dir, pre, post)
    discard_read_only_snapshot_phases(snapshot_dir)
    return reclaimed


def _load_read_only_snapshot_sidecar(task_id: str, phase: str) -> dict[str, str] | None:
    path = _read_only_snapshot_sidecar_path(task_id, phase)
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _hydrate_read_only_checkout_snapshots(state: dict[str, Any]) -> dict[str, Any]:
    """Load sidecar snapshots into the in-memory state dict when present."""
    task_id = state.get("task_id")
    if not isinstance(task_id, str):
        return state
    for phase in ("pre", "post"):
        key = f"read_only_checkout_{phase}"
        if key in state and isinstance(state[key], dict):
            continue
        sidecar = _load_read_only_snapshot_sidecar(task_id, phase)
        if sidecar is not None:
            state[key] = sidecar
    return state


def _archive_task_artifacts(task_id: str, *, stamp: str | None = None) -> list[Path]:
    """Move the prior record and result aside. Never overwrite an archive.

    Holds the per-task lock for the whole rename. The retention sweep holds
    that same lock across its digest and record write; without it, this move
    can land after the sweep's hot-name recheck and the sweep then creates a
    new hot record whose sidecar is already gone.
    """
    stamp = stamp or _archive_stamp()
    state_path = _state_path(task_id)
    archived: list[Path] = []
    with task_state_lock(state_path):
        for path in (state_path, _result_path(task_id)):
            if not path.exists():
                continue
            dest = _archived_artifact_path(path, stamp)
            os.replace(path, dest)
            archived.append(dest)
        snapshot_dir = state_path.parent / f"{state_path.stem}{_READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX}"
        if snapshot_dir.is_dir():
            dest = snapshot_dir.parent / f"{snapshot_dir.name}.{stamp}.archived"
            if dest.exists():
                dest = snapshot_dir.parent / f"{snapshot_dir.name}.{stamp}.{os.getpid()}.archived"
            os.replace(snapshot_dir, dest)
            archived.append(dest)
    return archived


def _existing_task_status(state_path: Path, existing: dict[str, Any] | None) -> str:
    status = existing.get("status") if existing else None
    if isinstance(status, str) and status.strip():
        return status
    if state_path.exists():
        return "unreadable"
    return "result-only"


def _core_terminal_fields(
    *,
    status: str,
    duration_s: float,
    response: str,
    result_file: str | None,
    stderr_excerpt: str | None,
    returncode: int | None,
    returncode_reason: str | None,
    dirty_on_exit: bool | None,
    commits_ahead: int | None,
    needs_finalize: bool,
    finalize_error: str | None,
    last_error: str | None,
) -> dict[str, Any]:
    """The complete set of fields that define a finished dispatch's outcome.

    Both writers that can be the LAST word on a task — the normal checkpoint and
    the interrupt fallback — build their record here. The fallback used to
    hand-assemble a subset, so an interrupted run persisted a terminal status
    beside stale placeholder ``response_chars``/``exit_code``/``last_error``:
    the same duplication that let the return-code invariant apply on one path
    and not the other. One definition, both paths. (Cross-family review of
    #5807, round ten.)
    """
    return {
        "status": status,
        "finished_at": datetime.now(UTC).isoformat(),
        "duration_s": round(duration_s, 3),
        "response_chars": len(response),
        "result_file": result_file,
        "stderr_excerpt": stderr_excerpt,
        "returncode": returncode,
        "returncode_reason": returncode_reason,
        "last_error": last_error if status != "done" else None,
        "exit_code": returncode,
        "worktree_dirty_on_exit": dirty_on_exit,
        "commits_ahead": commits_ahead,
        "needs_finalize": needs_finalize,
        "finalize_error": finalize_error,
        "peak_rss_mib": _children_peak_rss_mib(),
    }


def _children_peak_rss_mib() -> float | None:
    """Peak RSS of the largest process this worker has reaped, in MiB (#8645).

    The worker is the waiting parent of the agent CLI, so
    ``getrusage(RUSAGE_CHILDREN)`` covers the CLI and every descendant that was
    itself waited for (a shell tool's pytest, xdist workers, git). It is the
    largest single process, not the tree's sum, and misses descendants that
    were never reaped up the chain (daemonized or still running at exit).
    """
    try:
        peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    except (OSError, ValueError):
        return None
    if peak <= 0:
        return None
    # Linux reports KiB; macOS reports bytes.
    peak_bytes = peak if sys.platform == "darwin" else peak * 1024
    return round(peak_bytes / (1024 * 1024), 1)


def _apply_returncode_invariant(status: str, returncode: int | None) -> str:
    """A success without a terminal child return code is not a success (#4837).

    Lives on its own because it is applied twice: once on the normal completion
    path and once in the interrupt fallback. When only the normal path enforced
    it, a cancel landing between classification and the check persisted
    ``done`` with a null return code — the fallback contradicting the invariant
    precisely when it was exercised (cross-family review of #5807).
    """
    if status == "done" and returncode is None:
        return "failed"
    return status


@contextlib.contextmanager
def _sigterm_deferred():
    """Ignore SIGTERM for the duration of a critical write, then restore.

    The worker's SIGTERM handler raises KeyboardInterrupt, and an exception
    raised inside an ``except`` suite is not caught by that same suite. So a
    SECOND cancel arriving while the terminal-status fallback is writing escapes
    before the atomic rename, and the task stays recorded as ``running`` even
    though its worker finished — the very failure the fallback exists to prevent
    (cross-family review of #5807).

    The window is one small file write. Deferring the signal across it cannot
    hang a cancel meaningfully, and the interrupt is re-raised immediately after.
    Degrades to a no-op off the main thread, where ``signal.signal`` is illegal.
    """
    try:
        previous = signal.signal(signal.SIGTERM, signal.SIG_IGN)
    except (ValueError, OSError):  # not the main thread — nothing to defer
        yield
        return
    try:
        yield
    finally:
        with contextlib.suppress(ValueError, OSError):
            signal.signal(signal.SIGTERM, previous)


def _detach_read_only_checkout_snapshots(state: dict[str, Any]) -> dict[str, Any]:
    """Drop hydrated snapshot dicts before persisting; sidecars are canonical."""
    task_id = state.get("task_id")
    if not isinstance(task_id, str):
        return state
    detached = dict(state)
    for phase in ("pre", "post"):
        key = f"read_only_checkout_{phase}"
        if key in detached and _read_only_snapshot_sidecar_path(task_id, phase).exists():
            detached.pop(key, None)
    return detached


def _write_state_atomic(path: Path, state: dict[str, Any]) -> None:
    """Write state JSON atomically via write-rename.

    os.replace() is atomic on POSIX, so concurrent readers never see
    a partially-written file. Ensures the parent directory exists
    before writing — callers that bypass _state_path may not have
    created it yet.

    Concurrency: a per-task lock serializes worker and probe writes. Each
    writer also uses a PID-suffixed tmp filename before ``os.replace``.
    """
    if state.get("require_review_verdict"):
        state = {
            **state,
            "failure_reason": _review_task_failure_reason(state) if state.get("status") == "failed" else None,
        }
    state = _detach_read_only_checkout_snapshots(state)
    with task_state_lock(path):
        write_state_unlocked(path, state)


def _review_task_failure_reason(state: dict[str, Any]) -> str:
    """Give every failed verdict-required review a stable, queryable cause."""
    if state.get("review_verdict_failure"):
        return state["review_verdict_failure"]
    if state.get("read_only_mutation_paths"):
        return "read_only_checkout_mutation"
    if state.get("read_only_checkout_snapshot_error"):
        return "read_only_checkout_snapshot_failed"
    if state.get("returncode") is None:
        if state.get("returncode_reason") in {
            "worktree preparation failed", "forward configuration failed", "worker process was not started",
            "scoped worker startup was ambiguous; not relaunched",
        }:
            return "review_worker_not_started"
        return "review_worker_returncode_missing"
    if state["returncode"] != 0:
        return "review_worker_nonzero_exit"
    return "review_worker_reported_failure"


def _append_dispatch_event(event: str, **fields: Any) -> None:
    """Append one delegate JSONL event without making telemetry fatal."""
    payload = {
        "ts": datetime.now(UTC).isoformat(),
        "event": event,
        **fields,
    }
    try:
        tasks_dir().mkdir(parents=True, exist_ok=True)
        line = (json.dumps(payload, ensure_ascii=False, default=str) + "\n").encode("utf-8")
        fd = os.open(
            str(tasks_dir() / "dispatch_events.jsonl"),
            os.O_APPEND | os.O_CREAT | os.O_WRONLY,
            0o600,
        )
        try:
            os.write(fd, line)
        finally:
            os.close(fd)
    except OSError as exc:
        print(
            f"[delegate] WARNING: failed to write dispatch event: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )


def _read_state_json(path: Path) -> dict[str, Any] | None:
    """Read a state file without hydrating read-only snapshot sidecars."""
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _read_state(path: Path) -> dict[str, Any] | None:
    """Read a state file; return None if missing or corrupted."""
    state = _read_state_json(path)
    if state is None:
        return None
    return _hydrate_read_only_checkout_snapshots(state)


def _state_file_unparseable(path: Path) -> bool:
    """True when a state file exists on disk but cannot be parsed to a dict."""
    return path.is_file() and _read_state_json(path) is None


def _bound_task_state_unparseable_reason(path: Path) -> str | None:
    """Return a refusal reason when a layout-bound state file is corrupt."""
    for task_id in _task_status_candidates_for_worktree(path):
        state_path = _state_path(task_id)
        if _state_file_unparseable(state_path):
            return f"unparseable task state for task-id={task_id}"
    return None


def _pid_alive(pid: int) -> bool:
    """Check if a PID is currently alive via signal-0 probe.

    os.kill(pid, 0) raises ProcessLookupError if the PID doesn't exist,
    PermissionError if it exists but is owned by another user (which
    still counts as "alive" for our purposes), or returns None on success.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, we just can't signal it
    return True


def _normalize_worktree_path(raw_path: str, *, repo_root: Path | None = None) -> Path:
    """Resolve a worktree path relative to the repo root.

    Every task record stores ``worktree_path`` in this resolved absolute form,
    which is what settle's active-claim scan compares against (#8610).
    """
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (repo_root if repo_root is not None else _REPO_ROOT) / path
    return path.resolve()


def _helper_worktree_path(raw_path: str | None, validated_path: Path | None) -> Path:
    """Return the path a worktree helper operates on (#8775).

    ``validated_path`` is the path dispatch resolved once at validation and
    re-checked after taking the worktree lock. It is used exactly as given:
    resolving it again would follow a symlink swapped in after that re-check.
    Only ``raw_path``, from direct callers that have no validated path, is
    resolved here.
    """
    if validated_path is not None:
        return validated_path
    if raw_path is None:
        raise ValueError("a worktree helper needs raw_path or validated_path")
    return _normalize_worktree_path(raw_path)


# Caller-supplied paths reach the worker prompt, task records, and subprocess
# cwd (#8775). Controls (Cc: C0, C1, DEL) and line/paragraph separators (Zl,
# Zp) can start a new line in a prompt; format controls (Cf: bidi overrides
# and isolates such as U+202E and U+2066, zero-width characters) can make the
# displayed text differ from the stored one; lone surrogates (Cs) are bytes
# that are not UTF-8. None belongs in a filesystem path this repo uses.
_CALLER_PATH_FORBIDDEN_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})


def _caller_path_control_char_error(flag: str, raw: str, *, what: str = "the path") -> str | None:
    """Refuse a ``--worktree``/``--cwd`` value that contains a control or format character.

    The message names the rule and the offending code point, never the raw
    value, so the refusal itself cannot carry injected text.
    """
    for offset, char in enumerate(raw):
        if unicodedata.category(char) in _CALLER_PATH_FORBIDDEN_CATEGORIES:
            return (
                f"❌ {flag} refused: {what} contains control or format character U+{ord(char):04X} "
                f"at offset {offset}; caller-supplied paths may not contain control characters, "
                "format (bidi) characters, or line separators (#8775)."
            )
    return None


def _validate_caller_path(flag: str, raw: str, *, resolve: Callable[[str], Path]) -> tuple[Path | None, str | None]:
    """Check ``raw``, resolve it once, and check the resolved path (#8775).

    A clean name can be a symlink to a path that is not clean, so both the
    caller's string and the path it resolves to are checked. Returns the
    resolved path, which dispatch uses for every later step instead of ``raw``.
    """
    error = _caller_path_control_char_error(flag, raw)
    if error:
        return None, error
    try:
        resolved = resolve(raw)
    except (OSError, RuntimeError) as exc:
        return None, f"❌ {flag} refused: the path cannot be resolved ({type(exc).__name__}) (#8775)."
    error = _caller_path_control_char_error(flag, str(resolved), what="the resolved path")
    if error:
        return None, error
    return resolved, None


def _worktree_containment_anchor(agent: str, *, repo_root: Path) -> tuple[Path | None, str | None]:
    """Return ``<resolved repo>/.worktrees/dispatch/<agent>`` when each level is a real directory.

    Resolving the anchor would let a symlinked ``.worktrees``, ``dispatch`` or
    agent directory move the whole subtree outside the repository, so each
    level is checked with ``lstat`` instead: it must exist and be a directory,
    not a symlink (#8775).
    """
    if agent in {"", ".", ".."} or "/" in agent or "\\" in agent:
        return None, f"❌ --worktree refused: agent {agent!r} is not a single path component (#8775)."
    anchor = repo_root.resolve()
    for part in (".worktrees", "dispatch", agent):
        anchor = anchor / part
        try:
            mode: int | None = os.lstat(anchor).st_mode
        except OSError:
            mode = None
        if mode is None or stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            state = "is missing" if mode is None else "is a symlink" if stat.S_ISLNK(mode) else "is not a directory"
            return None, (
                f"❌ --worktree refused: {str(anchor)!r} {state}; an explicit --worktree PATH needs "
                f".worktrees/dispatch/{agent}/ to be a real directory inside the target repository (#8775). "
                "Pass bare `--worktree` to auto-create one."
            )
    return anchor, None


def _validate_explicit_worktree(raw: str, *, agent: str, repo_root: Path) -> tuple[Path | None, str | None]:
    """Validate an explicit ``--worktree PATH`` and return its resolved path (#8775).

    The path must resolve, symlinks followed, strictly inside the
    real-directory anchor ``<repo>/.worktrees/dispatch/<agent>/``, and neither
    the caller's string nor the resolved path may contain a control or format
    character. The message quotes only resolved paths via ``repr``.
    """
    candidate, error = _validate_caller_path(
        "--worktree", raw, resolve=lambda value: _normalize_worktree_path(value, repo_root=repo_root)
    )
    if candidate is None:
        return None, error
    anchor, error = _worktree_containment_anchor(agent, repo_root=repo_root)
    if anchor is None:
        return None, error
    if candidate != anchor and candidate.is_relative_to(anchor):
        return candidate, None
    return None, (
        f"❌ --worktree refused: {str(candidate)!r} does not resolve under {str(anchor)!r}; "
        f"an explicit --worktree PATH must be a directory inside .worktrees/dispatch/{agent}/ "
        "of the target repository after following symlinks (#8775). "
        "Pass bare `--worktree` to auto-create one."
    )


def _validated_path_changed_error(flag: str, validated: Path) -> str | None:
    """Refuse when a validated path no longer resolves to itself (#8775).

    ``validated`` was fully resolved at validation time, so it keeps resolving
    to itself until one of its components is replaced by a symlink. Dispatch
    calls this after taking the worktree lock and before the worktree helpers
    run, and the helpers use ``validated`` as given without resolving it again
    (:func:`_helper_worktree_path`), so a swap after validation is refused
    instead of redirecting the lock, git operations, or the worker.

    Scope: the prompt-injection vector of #8775 is closed by the character
    check on the raw and resolved paths plus JSON quoting in the worker
    prompt. Path containment is checked on real directories and re-checked
    here, after the lock. A symlink swap in the remaining gap (after this
    check, while git or the filesystem follows the path) needs write access
    to a directory on ``validated``. Under ``.worktrees/dispatch/`` that is a
    process running as the same user, which already holds every capability
    the dispatcher has, so the race grants it nothing new; it is out of
    scope. ``--cwd`` also accepts registered worktrees elsewhere, where write
    access to any parent directory is enough to swap the worktree without
    access to it. The out-of-scope argument holds there only when every
    directory on the path is writable by the dispatching user alone.

    ``--dry-run`` takes no lock: a ``--worktree`` dry run still calls this
    check, and a ``--cwd`` dry run returns before calling it.
    """
    try:
        current: Path | None = validated.resolve()
    except (OSError, RuntimeError):
        current = None
    if current == validated:
        return None
    return (
        f"❌ {flag} refused: {str(validated)!r} changed after validation (a component is now a symlink "
        "or cannot be resolved); refusing to follow it (#8775)."
    )


def _resolve_output_schema(
    raw_path: str | None,
    *,
    agent: str,
) -> tuple[str | None, str | None]:
    """Validate one provider output schema before any worker is spawned.

    The Codex CLI is currently the only native dispatch adapter with a
    file-backed structured-output flag. Returning an absolute path prevents
    the detached worker from resolving a relative schema against a different
    working directory. The SHA is persisted in task state as proof of the
    exact schema bytes admitted at the dispatch boundary.
    """
    if raw_path is None:
        return None, None
    if agent != "codex":
        raise ValueError("--output-schema is supported only with the effective codex agent")

    candidate = Path(raw_path).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"output schema does not exist: {candidate}") from exc
    if not resolved.is_file():
        raise ValueError(f"output schema is not a regular file: {resolved}")
    try:
        payload = resolved.read_bytes()
        schema = json.loads(payload.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"output schema is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(schema, dict):
        raise ValueError("output schema JSON must be an object")
    return str(resolved), hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Worktree lifecycle — create, validate, reuse
# ---------------------------------------------------------------------------
#
# The four failure classes below drove a design change from "silent-reuse
# existing directory" to "validate before reuse, raise a specific error
# otherwise." Silent reuse is how #1473 shipped a stub alignment_manifest.py
# as a real PR: the dispatched worktree already existed on a stale branch
# and delegate.py inherited that state. Each exception carries the exact
# remediation command in its message so operators can unblock without
# digging.


class WorktreeBranchMismatch(RuntimeError):
    """Existing worktree is on a branch other than the expected dispatch branch."""


class WorktreeDirty(RuntimeError):
    """Existing worktree has uncommitted changes; refuse to reuse."""


class WorktreeStaleBase(RuntimeError):
    """Existing worktree is behind origin/<base> and the fast-forward rebase failed."""


class WorktreeBranchDiverged(RuntimeError):
    """A local --branch ref contains commits absent from its fetched origin ref."""


WorktreeLockError = worktree_claims.WorktreeLockError
WorktreeLockTimeout = worktree_claims.WorktreeLockTimeout
WorktreeLockReentry = worktree_claims.WorktreeLockReentry

# Dispatch (create-or-attach, then publish the task record) and every
# dispatch-worktree removal (see _remove_dispatch_worktree) serialize on one
# lock per worktree, so an attachment can never land between a remover's claim
# scan and its removal (#8610). The lock itself lives in
# scripts/orchestration/worktree_claims.py, shared with the scheduled reaper.
_WORKTREE_LOCK_DEFAULT_TIMEOUT_S = worktree_claims.DEFAULT_LOCK_TIMEOUT_S
# Test seam: overrides ``<git common dir>/lu-worktree-locks`` when set.
_WORKTREE_LOCK_DIR: Path | None = None


def _worktree_lock_dir() -> Path:
    """Return the lock home shared by every checkout of this repository."""
    if _WORKTREE_LOCK_DIR is not None:
        return _WORKTREE_LOCK_DIR
    common_dir = _git_common_dir(_REPO_ROOT)
    return (common_dir if common_dir is not None else tasks_dir().parent) / worktree_claims.LOCK_DIR_NAME


def _worktree_lock_path(path: Path | str) -> tuple[str, Path]:
    """Return the canonical absolute worktree path and its lock file."""
    return worktree_claims.lock_path(path, lock_dir=_worktree_lock_dir())


def worktree_lock(path: Path | str, timeout_s: float | None = None) -> contextlib.AbstractContextManager[None]:
    """Hold this repository's exclusive advisory lock for one worktree path.

    See :func:`scripts.orchestration.worktree_claims.worktree_lock`. Every
    failure raises a :class:`WorktreeLockError`; ``timeout_s`` defaults to
    ``_WORKTREE_LOCK_DEFAULT_TIMEOUT_S``.
    """
    return worktree_claims.worktree_lock(
        path,
        lock_dir=_worktree_lock_dir(),
        timeout_s=_WORKTREE_LOCK_DEFAULT_TIMEOUT_S if timeout_s is None else timeout_s,
    )


def _normalize_task_id(agent: str, task_id: str) -> str:
    """Strip a leading ``{agent}-`` or ``{agent}/`` from task_id.

    Shared by :func:`_derive_worktree_branch` and :func:`_auto_worktree_path`
    so the branch name and the dispatch/ subtree path land in sync even
    when the caller accidentally prefixed the agent name (our own tools
    often do — task-ids like ``codex-1472-foo`` are common).
    """
    for prefix in (f"{agent}-", f"{agent}/"):
        if task_id.startswith(prefix):
            return task_id[len(prefix) :]
    return task_id


def _runtime_tmp_lease_name(task_id: str) -> str:
    """Return one safe path component for a task's runtime tmp lease."""
    return re.sub(r"[^A-Za-z0-9._-]+", "-", task_id).strip("./-") or "task"


def _create_runtime_tmp_lease(task_id: str) -> tuple[Path, Path]:
    """Create and return a task lease plus its resolved namespace root.

    The lease is intentionally deterministic per task ID: a task can restart
    after its previous worker has finished and re-create the same root, while
    Stage 2 will eventually handle roots left by crashed processes.

    #7164: the namespace lives under the disk-backed fleet scratch root
    (``scripts/common/scratch.py``), not tmpfs ``/tmp`` — worker TMPDIR
    payloads must not be able to exhaust the small per-user tmpfs quota.
    """
    namespace_root = ensure_scratch_root() / "learn-ukrainian"
    try:
        namespace_root.mkdir(parents=True, exist_ok=True)
        namespace_stat = namespace_root.lstat()
    except OSError as exc:
        raise RuntimeError(
            f"could not create runtime tmp namespace {namespace_root}: {exc}",
        ) from exc
    if stat.S_ISLNK(namespace_stat.st_mode):
        raise RuntimeError(
            f"runtime tmp namespace must not be a symlink: {namespace_root}",
        )

    lease_root = namespace_root / _runtime_tmp_lease_name(task_id)
    try:
        lease_root.mkdir(exist_ok=True)
        lease_stat = lease_root.lstat()
        resolved_namespace = namespace_root.resolve(strict=True)
        resolved_lease = lease_root.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError(
            f"could not create runtime tmp lease {lease_root}: {exc}",
        ) from exc
    if stat.S_ISLNK(lease_stat.st_mode):
        raise RuntimeError(
            f"runtime tmp lease must not be a symlink: {lease_root}",
        )
    if not stat.S_ISDIR(lease_stat.st_mode) or resolved_lease.parent != resolved_namespace:
        raise RuntimeError(
            f"runtime tmp lease is not a direct child of its namespace: {lease_root}",
        )
    _write_runtime_tmp_task_id_marker(resolved_lease, task_id)
    return resolved_lease, resolved_namespace


def _runtime_tmp_task_id_marker_path(lease_root: Path) -> Path:
    return lease_root / _RUNTIME_TMP_TASK_ID_MARKER


def _write_runtime_tmp_task_id_marker(
    lease_root: Path,
    task_id: str,
    *,
    no_clobber: bool = False,
) -> None:
    """Persist the owning task id so orphan sweeps never scan task records."""
    marker = _runtime_tmp_task_id_marker_path(lease_root)
    if no_clobber:
        try:
            fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(task_id)
        return
    tmp = marker.with_suffix(f".tmp.{os.getpid()}")
    tmp.write_text(task_id, encoding="utf-8")
    os.replace(tmp, marker)


def _read_runtime_tmp_task_id_marker(lease_root: Path) -> str | None:
    marker = _runtime_tmp_task_id_marker_path(lease_root)
    try:
        task_id = marker.read_text(encoding="utf-8").strip()
    except (OSError, ValueError):
        return None
    return task_id or None


def _runtime_tmp_lease_bytes(lease_root: Path) -> int:
    """Count lease payload bytes without traversing directory symlinks."""
    total = 0
    seen_regular_files: set[tuple[int, int]] = set()
    for directory, dirnames, filenames in os.walk(lease_root, followlinks=False):
        for name in [*dirnames, *filenames]:
            path = Path(directory) / name
            try:
                entry = path.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISREG(entry.st_mode):
                inode = (entry.st_dev, entry.st_ino)
                if inode in seen_regular_files:
                    continue
                seen_regular_files.add(inode)
                total += entry.st_size
            elif stat.S_ISLNK(entry.st_mode):
                # Account for the link's own small directory entry, never its
                # target. ``os.walk(..., followlinks=False)`` will not descend.
                total += entry.st_size
    return total


def _grant_owner_rwx_at(path: Path, *, dir_fd: int) -> bool:
    """Give the owner access to a non-symlink path anchored at ``dir_fd``."""
    try:
        entry = os.stat(path, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(entry.st_mode):
        return False
    mode = stat.S_IMODE(entry.st_mode)
    repaired_mode = mode | stat.S_IRWXU
    if repaired_mode == mode:
        return False
    os.chmod(
        path,
        repaired_mode,
        dir_fd=dir_fd,
        follow_symlinks=False,
    )
    return True


def _runtime_tmp_reap_onexc(
    lease: Path,
    namespace: Path,
    namespace_fd: int,
    repairs: set[Path],
):
    """Build an ``rmtree`` repair callback confined to one verified lease."""

    def repair(_func: Any, raw_path: str | os.PathLike[str], exc: BaseException) -> None:
        if not isinstance(exc, PermissionError):
            raise exc
        path = Path(raw_path)
        try:
            candidate = path.relative_to(namespace) if path.is_absolute() else path
            candidate.relative_to(lease.name)
        except ValueError:
            raise exc from None
        if _grant_owner_rwx_at(candidate, dir_fd=namespace_fd):
            repairs.add(candidate)
        if _grant_owner_rwx_at(candidate.parent, dir_fd=namespace_fd):
            repairs.add(candidate.parent)

    return repair


def _remove_runtime_tmp_lease(lease: Path, namespace: Path) -> None:
    """Delete one verified lease, repairing restrictive owned entries first."""
    if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
        raise RuntimeError("platform rmtree lacks symlink-attack protection")
    if not hasattr(os, "O_NOFOLLOW"):
        raise RuntimeError("platform lacks O_NOFOLLOW for runtime tmp cleanup")
    open_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    open_flags |= os.O_NOFOLLOW
    last_error: OSError | None = None
    # ``shutil.rmtree`` calls onexc but cannot resume an ``os.open`` that
    # failed while descending into a mode-000 directory. Re-run the complete,
    # fd-relative walk after every actual permission repair: a tree can have
    # any number of nested restricted directories, so a fixed retry count
    # abandons valid entries below the next barrier.
    while os.path.lexists(lease):
        repairs: set[Path] = set()
        namespace_fd = os.open(namespace, open_flags)
        try:
            shutil.rmtree(
                lease.name,
                dir_fd=namespace_fd,
                onexc=_runtime_tmp_reap_onexc(lease, namespace, namespace_fd, repairs),
            )
        except FileNotFoundError:
            return
        except OSError as exc:
            last_error = exc
        finally:
            os.close(namespace_fd)
        if not os.path.lexists(lease):
            return
        if not repairs:
            break
    # A lease already gone at entry (e.g. a concurrent sweep won the race) is
    # success, not a survived-cleanup failure — the loop guard never ran rmtree,
    # so nothing above could return early on its behalf.
    if not os.path.lexists(lease):
        return
    if last_error is not None:
        raise OSError(
            last_error.errno,
            f"runtime tmp lease survived hardened cleanup: {lease}: {last_error.strerror or last_error}",
            last_error.filename or str(lease),
        )
    raise OSError(f"runtime tmp lease survived hardened cleanup: {lease}")


def _build_runtime_tmp_legacy_stem_index() -> dict[str, str]:
    """Map lease names to task-record stems without opening any JSON."""
    index: dict[str, str] = {}
    try:
        state_files = tuple(tasks_dir().glob("*.json")) if tasks_dir().is_dir() else ()
    except OSError:
        return index
    for state_path in state_files:
        if state_path.name.endswith(".tmp") or ".tmp." in state_path.name:
            continue
        stem = state_path.stem
        index[_runtime_tmp_lease_name(stem)] = stem
    return index


def _read_runtime_tmp_state_for_legacy_lease(
    lease_name: str,
    *,
    legacy_stem_index: dict[str, str],
) -> dict[str, Any] | None:
    """Resolve one marker-less lease, falling back to a bounded record scan."""
    stem = legacy_stem_index.get(lease_name)
    if stem is not None:
        return _read_state_json(tasks_dir() / f"{stem}.json")
    try:
        state_files = tuple(tasks_dir().glob("*.json")) if tasks_dir().is_dir() else ()
    except OSError:
        return None
    for state_path in state_files:
        if state_path.name.endswith(".tmp") or ".tmp." in state_path.name:
            continue
        state = _read_state_json(state_path)
        if not isinstance(state, dict):
            continue
        task_id = state.get("task_id")
        if isinstance(task_id, str) and _runtime_tmp_lease_name(task_id) == lease_name:
            return state
    return None


def _runtime_tmp_state_for_lease(
    lease_name: str,
    lease_root: Path,
    *,
    legacy_stem_index: dict[str, str] | None,
) -> dict[str, Any] | None:
    """Find the task state that owns a runtime-lease directory."""
    task_id = _read_runtime_tmp_task_id_marker(lease_root)
    if task_id is not None:
        return _read_state_json(_state_path(task_id))
    if legacy_stem_index is None:
        return None
    return _read_runtime_tmp_state_for_legacy_lease(
        lease_name,
        legacy_stem_index=legacy_stem_index,
    )


def _runtime_tmp_state_has_live_pid(state: dict[str, Any]) -> bool:
    """Treat a valid live recorded PID as an active lease regardless of status."""
    pid = state.get("pid")
    if isinstance(pid, bool):
        return False
    try:
        return isinstance(pid, (int, str)) and int(pid) > 0 and _pid_alive(int(pid))
    except (TypeError, ValueError):
        return False


def _sweep_runtime_tmp_orphans(
    *,
    now: float | None = None,
) -> dict[str, Any]:
    """Reap terminal or clearly abandoned task leases before a new dispatch.

    A state-backed lease is removed only once its task is terminal and no
    recorded process is alive. A state-less lease must be older than seven
    days. Symlinks and malformed entries are skipped rather than followed.
    """
    error_details: list[tuple[str, int | None, str]] = []
    result: dict[str, Any] = {
        "leases_reaped": 0,
        "bytes_freed": 0,
        "errors": 0,
        "error_details": error_details,
    }
    # #7164: the lease namespace moved to the disk-backed fleet scratch root;
    # sweep every known scratch base (new root + legacy tmpfs $TMPDIR) so old
    # namespaces still drain.
    namespaces: list[Path] = []
    seen_namespaces: set[Path] = set()
    for scratch_base in scratch_scan_roots():
        namespace = scratch_base / "learn-ukrainian"
        if namespace in seen_namespaces:
            continue
        seen_namespaces.add(namespace)
        namespaces.append(namespace)
    cutoff = (time.time() if now is None else now) - _RUNTIME_TMP_ORPHAN_MAX_AGE_S
    legacy_stem_index: dict[str, str] | None = None

    for namespace in namespaces:
        try:
            namespace_stat = namespace.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            result["errors"] += 1
            error_details.append((namespace.name, exc.errno, str(exc.filename or namespace)))
            continue
        if stat.S_ISLNK(namespace_stat.st_mode) or not stat.S_ISDIR(namespace_stat.st_mode):
            result["errors"] += 1
            continue

        try:
            candidates = tuple(namespace.iterdir())
        except OSError as exc:
            result["errors"] += 1
            error_details.append((namespace.name, exc.errno, str(exc.filename or namespace)))
            continue
        for lease in candidates:
            try:
                lease_stat = lease.lstat()
            except FileNotFoundError:
                continue
            except OSError as exc:
                result["errors"] += 1
                if len(error_details) < _RUNTIME_TMP_SWEEP_ERROR_DETAILS_LIMIT:
                    error_details.append((lease.name, exc.errno, str(exc.filename or lease)))
                continue
            if stat.S_ISLNK(lease_stat.st_mode) or not stat.S_ISDIR(lease_stat.st_mode):
                continue

            had_marker = _read_runtime_tmp_task_id_marker(lease) is not None
            if not had_marker and legacy_stem_index is None:
                legacy_stem_index = _build_runtime_tmp_legacy_stem_index()
            state = _runtime_tmp_state_for_lease(
                lease.name,
                lease,
                legacy_stem_index=legacy_stem_index,
            )
            if state is not None:
                status = state.get("status")
                if status not in _RUNTIME_TMP_TERMINAL_STATUSES or _runtime_tmp_state_has_live_pid(state):
                    if not had_marker:
                        resolved_task_id = state.get("task_id")
                        if isinstance(resolved_task_id, str):
                            with contextlib.suppress(OSError):
                                _write_runtime_tmp_task_id_marker(
                                    lease,
                                    resolved_task_id,
                                    no_clobber=True,
                                )
                    continue
            elif lease_stat.st_mtime >= cutoff:
                continue

            try:
                bytes_freed = _runtime_tmp_lease_bytes(lease)
                _remove_runtime_tmp_lease(lease, namespace)
            except OSError as exc:
                result["errors"] += 1
                if len(error_details) < _RUNTIME_TMP_SWEEP_ERROR_DETAILS_LIMIT:
                    error_details.append((lease.name, exc.errno, str(exc.filename or lease)))
                continue
            result["leases_reaped"] += 1
            result["bytes_freed"] += bytes_freed
    return result


def _reap_runtime_tmp_lease(
    lease_root: Path | str | None,
    namespace_root: Path | str | None,
) -> dict[str, int | str | None]:
    """Best-effort, fd-relative deletion of one task-scoped runtime lease.

    This is intentionally stricter than a generic ``rm -rf``. It only removes
    a non-symlink direct child of the dispatcher-created namespace and uses
    ``shutil.rmtree``'s fd-based implementation so a symlink swap cannot turn
    cleanup into a deletion outside the lease. Any failure is state telemetry,
    never a worker failure.
    """
    result: dict[str, int | str | None] = {
        "tmp_bytes_freed": 0,
        "tmp_reap_error": None,
    }
    try:
        if lease_root is None or namespace_root is None:
            raise ValueError("runtime tmp lease metadata is missing")
        lease = Path(lease_root)
        namespace = Path(namespace_root)
        namespace_stat = namespace.lstat()
        lease_stat = lease.lstat()
        if stat.S_ISLNK(namespace_stat.st_mode):
            raise ValueError("runtime tmp namespace is a symlink")
        if stat.S_ISLNK(lease_stat.st_mode):
            raise ValueError("runtime tmp lease is a symlink")
        if not stat.S_ISDIR(namespace_stat.st_mode):
            raise ValueError("runtime tmp namespace is not a directory")
        if not stat.S_ISDIR(lease_stat.st_mode):
            raise ValueError("runtime tmp lease is not a directory")

        resolved_namespace = namespace.resolve(strict=True)
        resolved_lease = lease.resolve(strict=True)
        resolved_tmp_root = Path(tempfile.gettempdir()).resolve(strict=True)
        if resolved_tmp_root == resolved_lease:
            # The worker deliberately points TMPDIR at its lease. In that one
            # process context, use the pre-override root recorded by the
            # dispatcher; parent cleanup still validates against its live
            # tempfile root, so a stale inherited base cannot bless a child.
            runtime_tmp_base_root = os.environ.get("LU_RUNTIME_TMP_BASE_ROOT")
            if not runtime_tmp_base_root:
                raise ValueError("runtime tmp worker is missing its base root")
            accepted_parents = {Path(runtime_tmp_base_root).resolve(strict=True)}
        else:
            # #7164: leases live under the disk-backed fleet scratch root; the
            # legacy tmpfs $TMPDIR namespace stays accepted so pre-change
            # leases can still be reaped. Fallback scratch root is also accepted.
            accepted_parents = {root.resolve() for root in scratch_scan_roots()}
            with contextlib.suppress(OSError):
                accepted_parents.add(resolve_scratch_root().resolve())
            with contextlib.suppress(OSError):
                accepted_parents.add(fallback_scratch_root().resolve())
            with contextlib.suppress(OSError):
                accepted_parents.add(DEFAULT_SCRATCH_ROOT.resolve())
            accepted_parents.add(resolved_tmp_root)
        if resolved_namespace.parent not in accepted_parents:
            raise ValueError(
                "resolved runtime tmp namespace is not directly under an approved scratch root",
            )
        if resolved_lease.parent != resolved_namespace:
            raise ValueError(
                "resolved runtime tmp lease is not under $TMPDIR/learn-ukrainian",
            )
        if resolved_namespace.name != "learn-ukrainian":
            raise ValueError("runtime tmp namespace has the wrong name")
        if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
            raise RuntimeError("platform rmtree lacks symlink-attack protection")

        bytes_freed = _runtime_tmp_lease_bytes(lease)
        _remove_runtime_tmp_lease(lease, namespace)
        if os.path.lexists(lease):
            raise OSError(f"runtime tmp lease survived hardened cleanup: {lease}")
        result["tmp_bytes_freed"] = bytes_freed
    except Exception as exc:
        result["tmp_reap_error"] = (f"{type(exc).__name__}: {exc}")[:500]
    return result


def _derive_worktree_branch(agent: str, task_id: str) -> str:
    """Derive a git-safe branch name for a delegated worktree.

    Normalizes task_id first so ``codex-1472-foo`` produces
    ``codex/1472-foo`` rather than ``codex/codex-1472-foo``.
    """
    normalized = _normalize_task_id(agent, task_id)
    safe_task = re.sub(r"[^A-Za-z0-9._/-]+", "-", normalized).strip("./-")
    safe_task = re.sub(r"/{2,}", "/", safe_task)
    if not safe_task:
        safe_task = "task"
    return f"{agent}/{safe_task}"


def _auto_worktree_path(agent: str, task_id: str, *, repo_root: Path | None = None) -> Path:
    """Default worktree path for a fresh dispatch: ``.worktrees/dispatch/{agent}/{task}/``.

    Defaults under :data:`_REPO_ROOT`. With ``--repo`` (#672 P2.1) the path is
    rooted at the allowlisted sibling checkout instead. A bare sibling cwd
    still cannot retarget this path — use ``--repo`` or the manual ``--cwd``
    flow (:func:`_resolve_cross_repo_binding_error`).
    """
    normalized = _normalize_task_id(agent, task_id)
    # Slashes are fine in branch names but not in a single path component,
    # so flatten them here (task_id ``foo/bar`` → path ``foo-bar``).
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized).strip("./-") or "task"
    root = Path(repo_root).resolve() if repo_root is not None else _REPO_ROOT
    return root / ".worktrees" / "dispatch" / agent / safe


# ``git worktree add`` bounds, configurable in scripts/config.py (#8663). Tests
# shrink them here instead of generating host load.
_WORKTREE_ADD_TIMEOUT_S: float = DELEGATE_WORKTREE_ADD_TIMEOUT_S
_WORKTREE_ADD_STALL_S: float = DELEGATE_WORKTREE_ADD_STALL_S
_WORKTREE_ADD_MAX_S: float = DELEGATE_WORKTREE_ADD_MAX_S
# How often a slow add's checkout is re-counted once the base window has passed.
_WORKTREE_ADD_POLL_S: float = 5.0
# How long a stopped add gets to run git's own cleanup after SIGTERM, and to
# exit after SIGKILL.
_WORKTREE_ADD_STOP_GRACE_S: float = 30.0

_GIT_INITIALIZING_LOCK_REASON = worktree_prep.INITIALIZING_LOCK_REASON


class WorktreeAddFailed(RuntimeError):
    """``git worktree add`` failed or timed out before any worker was spawned (#8663).

    ``cleanup`` records what dispatch found and did after the add; the failed
    task record carries it as ``worktree_prep_cleanup``. ``prep`` is this
    call's path reservation, stored as ``worktree_prep``, or ``None`` when the
    path could not be reserved.
    """

    def __init__(self, message: str, *, cleanup: dict[str, Any], prep: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.cleanup = cleanup
        self.prep = prep


class WorktreeAddTimeout(subprocess.TimeoutExpired):
    """A stopped ``git worktree add``; ``git_exited`` says whether its exit was confirmed."""

    def __init__(self, cmd: list[str], timeout: float, *, git_exited: bool) -> None:
        super().__init__(cmd, timeout)
        self.git_exited = git_exited


def _checkout_entry_count(path: Path) -> int:
    """Count the files and directories under ``path``, skipping ``.git``.

    The progress signal for a slow ``git worktree add``: a checkout that is
    still being written keeps gaining entries. Entries that vanish mid-walk
    are skipped; a missing ``path`` counts as zero.
    """
    count = 0
    pending = [path]
    while pending:
        try:
            with os.scandir(pending.pop()) as entries:
                for entry in entries:
                    if entry.name == ".git":
                        continue
                    count += 1
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            pending.append(Path(entry.path))
                    except OSError:
                        continue
        except OSError:
            continue
    return count


def _stop_worktree_add(proc: subprocess.Popen[str]) -> bool:
    """Stop a slow ``git worktree add`` and its checkout child.

    SIGTERM goes to the whole process group first, and git gets
    :data:`_WORKTREE_ADD_STOP_GRACE_S` to run its own signal cleanup, which
    deletes the worktree directory and admin directory it was building.
    SIGKILL follows only after that grace. Returns whether the add was
    confirmed exited; a process that outlives even SIGKILL (for example one
    stuck in uninterruptible I/O) may still write, so nothing may be touched
    while this is False.
    """
    for sig in (signal.SIGTERM, signal.SIGKILL):
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(proc.pid, sig)
        try:
            proc.communicate(timeout=_WORKTREE_ADD_STOP_GRACE_S)
            return True
        except subprocess.TimeoutExpired:
            continue
    return False


def _run_worktree_add(
    add_command: list[str],
    *,
    cwd: Path,
    worktree_path: Path,
    env: dict[str, str] | None = None,
    on_spawn: Callable[[int], None] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``git worktree add`` with a progress-aware bound (#8663).

    The add always gets :data:`_WORKTREE_ADD_TIMEOUT_S`. After that it keeps
    running while the checkout at ``worktree_path`` is still gaining entries,
    is stopped once it gains none for :data:`_WORKTREE_ADD_STALL_S`, and is
    never allowed past :data:`_WORKTREE_ADD_MAX_S`. A stopped add (see
    :func:`_stop_worktree_add`) raises :class:`WorktreeAddTimeout`. The add
    runs in the C locale so the lock reason git holds during it is the
    literal ``initializing``. ``on_spawn`` receives git's pid as soon as it
    is spawned.
    """
    add_env = dict(os.environ if env is None else env)
    add_env["LC_ALL"] = "C"
    add_env.pop("LANGUAGE", None)
    proc = subprocess.Popen(
        add_command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=add_env,
        # Its own process group, so a stop also reaches the checkout child.
        start_new_session=True,
    )
    started = time.monotonic()
    if on_spawn is not None:
        on_spawn(proc.pid)
    poll_s = max(min(_WORKTREE_ADD_POLL_S, _WORKTREE_ADD_STALL_S), 0.01)
    last_count: int | None = None
    last_growth = started
    while True:
        elapsed = time.monotonic() - started
        if elapsed < _WORKTREE_ADD_TIMEOUT_S:
            wait_s = min(_WORKTREE_ADD_TIMEOUT_S, _WORKTREE_ADD_MAX_S) - elapsed
        else:
            wait_s = min(poll_s, _WORKTREE_ADD_MAX_S - elapsed)
        try:
            stdout, stderr = proc.communicate(timeout=max(wait_s, 0.01))
        except subprocess.TimeoutExpired:
            pass
        else:
            return subprocess.CompletedProcess(add_command, proc.returncode, stdout, stderr)
        now = time.monotonic()
        if now - started >= _WORKTREE_ADD_MAX_S:
            break
        if now - started < _WORKTREE_ADD_TIMEOUT_S:
            continue
        count = _checkout_entry_count(worktree_path)
        if last_count is None or count > last_count:
            last_count = count
            last_growth = now
        elif now - last_growth >= _WORKTREE_ADD_STALL_S:
            break
    git_exited = _stop_worktree_add(proc)
    raise WorktreeAddTimeout(add_command, time.monotonic() - started, git_exited=git_exited)


def _worktree_registration(repo_root: Path, worktree_path: Path) -> tuple[bool, str | None] | None:
    """Return whether ``repo_root`` registers ``worktree_path`` and its lock reason.

    The lock reason is ``None`` for an unlocked worktree and ``""`` for a lock
    without a reason. Returns ``None`` when git cannot list its worktrees.
    """
    try:
        proc = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
            env=_sanitized_git_env(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    target = worktree_path.resolve()
    registered = False
    lock_reason: str | None = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith("worktree "):
            if registered:
                break
            registered = Path(line.removeprefix("worktree ")).resolve() == target
            lock_reason = None
        elif registered and (line == "locked" or line.startswith("locked ")):
            lock_reason = line.removeprefix("locked").strip()
    return registered, lock_reason if registered else None


def _is_own_worktree_prep_record(state: dict[str, Any], run_nonce: str) -> bool:
    """True when ``state`` is this run's pre-``git worktree add`` reservation record."""
    prep = state.get("worktree_prep")
    return (
        state.get("run_nonce") == run_nonce
        and state.get("pid", False) is None
        and isinstance(prep, dict)
        and prep.get("run_nonce") == run_nonce
    )


def _is_own_admission_hold(state: dict[str, Any], run_nonce: str) -> bool:
    """True when ``state`` is this run's admission hold (#8717), without a worktree reservation."""
    return (
        state.get("run_nonce") == run_nonce
        and "worktree_prep" not in state
        and dispatch_admission.is_admission_hold_record(state)
    )


def _is_own_provisional_record(state: dict[str, Any], run_nonce: str) -> bool:
    """True for this run's pid-less admission hold or worktree reservation record."""
    return _is_own_worktree_prep_record(state, run_nonce) or _is_own_admission_hold(state, run_nonce)


# Fields an admission hold carries into the worktree reservation record that
# replaces it, so the reservation keeps the admitted slot (#8717).
_ADMISSION_HOLD_FIELDS = ("mode", "admission", dispatch_admission.ADMISSION_HOLD_KEY)


def _publish_admission_hold(task_id: str, run_nonce: str, *, mode: str, admission: dict[str, Any]) -> None:
    """Publish the ``spawning`` record that holds this run's admitted write slot (#8717).

    Dispatch calls this under the admission lock, before any worktree side
    effect, so a refusal leaves nothing behind. The hold names this
    dispatcher, so admission counts it for as long as the dispatcher lives
    (however long its worktree add takes) and heals it once the dispatcher is
    provably gone. The worktree reservation and the full task record replace
    it in place. Raises ``RuntimeError`` rather than overwrite a live record
    of another run.
    """
    state_path = _state_path(task_id)
    with task_state_lock(state_path):
        existing = _read_state_json(state_path)
        if (
            existing is not None
            and existing.get("status") in ("running", "spawning")
            and not _is_own_provisional_record(existing, run_nonce)
        ):
            raise RuntimeError(f"task record for {task_id!r} is {existing.get('status')}; refusing to overwrite it")
        hold = dispatch_admission.new_admission_hold(run_nonce)
        write_state_unlocked(
            state_path,
            {
                "task_id": task_id,
                "run_nonce": run_nonce,
                "status": "spawning",
                "pid": None,
                "mode": mode,
                "started_at": hold["admitted_at"],
                "finished_at": None,
                "admission": admission,
                dispatch_admission.ADMISSION_HOLD_KEY: hold,
            },
        )


def _release_admission_hold(task_id: str, run_nonce: str) -> None:
    """Drop this run's admission hold when dispatch stops before publishing any other record.

    A no-op once the hold was replaced by the full task record, a failure
    record, or a worktree reservation (kept as the reaper's evidence).
    """
    state_path = _state_path(task_id)
    with contextlib.suppress(OSError), task_state_lock(state_path):
        existing = _read_state_json(state_path)
        if existing is not None and _is_own_admission_hold(existing, run_nonce):
            state_path.unlink(missing_ok=True)


def _publish_worktree_prep(task_id: str, run_nonce: str, prep: dict[str, Any]) -> None:
    """Record this run's path reservation in its task record before git starts (#8663).

    The record says ``spawning`` with ``pid: null`` (dispatch is preparing,
    no worker exists yet), so claim scans treat the path as taken while the
    add runs, and a dispatcher that dies meanwhile is detectable from the
    recorded owner. It replaces this run's admission hold and keeps its
    fields, so the admitted slot stays held while the add runs (#8717). The
    terminal record a failed add later writes keeps ``worktree_prep`` as
    evidence for the reaper's report. Raises ``RuntimeError`` rather than
    overwrite a live record of another run.
    """
    state_path = _state_path(task_id)
    with task_state_lock(state_path):
        existing = _read_state_json(state_path)
        if (
            existing is not None
            and existing.get("status") in ("running", "spawning")
            and not _is_own_provisional_record(existing, run_nonce)
        ):
            raise RuntimeError(f"task record for {task_id!r} is {existing.get('status')}; refusing to overwrite it")
        held = (
            {key: existing[key] for key in _ADMISSION_HOLD_FIELDS if key in existing}
            if existing is not None and _is_own_provisional_record(existing, run_nonce)
            else {}
        )
        write_state_unlocked(
            state_path,
            {
                "task_id": task_id,
                "run_nonce": run_nonce,
                "status": "spawning",
                "pid": None,
                **held,
                "cwd": prep["path"],
                "worktree_path": prep["path"],
                "started_at": prep["reserved_at"],
                "finished_at": None,
                "worktree_prep": prep,
            },
        )


def _update_worktree_prep(task_id: str, run_nonce: str, prep: dict[str, Any]) -> None:
    """Rewrite ``worktree_prep`` in this run's provisional record; best effort."""
    state_path = _state_path(task_id)
    with contextlib.suppress(OSError), task_state_lock(state_path):
        existing = _read_state_json(state_path)
        if existing is not None and _is_own_worktree_prep_record(existing, run_nonce):
            existing["worktree_prep"] = dict(prep)
            write_state_unlocked(state_path, existing)


def _retire_worktree_prep(task_id: str, run_nonce: str) -> None:
    """Drop this run's reservation record once its ``git worktree add`` succeeded.

    Dispatch publishes the full task record next; until then no record
    claims the finished worktree, exactly as before reservations existed.
    A reservation that replaced an admission hold reverts to that hold, so
    the admitted slot stays held until the full record replaces it (#8717).
    """
    state_path = _state_path(task_id)
    with contextlib.suppress(OSError), task_state_lock(state_path):
        existing = _read_state_json(state_path)
        if existing is None or not _is_own_worktree_prep_record(existing, run_nonce):
            return
        hold = existing.get(dispatch_admission.ADMISSION_HOLD_KEY)
        if not isinstance(hold, dict):
            state_path.unlink(missing_ok=True)
            return
        write_state_unlocked(
            state_path,
            {
                "task_id": task_id,
                "run_nonce": run_nonce,
                "status": "spawning",
                "pid": None,
                **{key: existing[key] for key in _ADMISSION_HOLD_FIELDS if key in existing},
                "started_at": hold.get("admitted_at"),
                "finished_at": None,
            },
        )


def _leave_reservation(worktree_path: Path, prep: dict[str, Any]) -> dict[str, Any]:
    """Report the reserved directory a failed add left unregistered; never remove it (#8663).

    Git 2.53 can write another add's admin registration while this path is
    still empty and before its ``.git`` exists, so no ``rmdir`` of the
    reservation is safe. The directory stays as it is, empty or not, and
    ``reserved_dir_left`` is recorded in ``prep`` and the returned report.
    An empty, unregistered one is swept later by the reaper's existing
    dispatch-husk rule (``reap_worktrees._reap_dispatch_husks``).
    """
    left = os.path.lexists(worktree_path)
    prep["reserved_dir_left"] = left
    report: dict[str, Any] = {"error": None, "reserved_dir_left": left}
    if not left:
        return {**report, "action": "none", "reason": "git left no worktree behind"}
    if not worktree_prep.identity_matches(prep, worktree_path):
        reason = "path holds a directory this run did not reserve (device/inode differ); never removed"
    else:
        reason = "git registered no worktree; reserved directory left in place, never removed automatically"
    return {**report, "action": "skipped", "reason": reason}


def _settle_failed_worktree_add(
    worktree_path: Path,
    *,
    repo_root: Path,
    git_exited: bool,
    prep: dict[str, Any],
) -> dict[str, Any]:
    """Record what this run's failed ``git worktree add`` left; remove nothing (#8663).

    A stopped add got SIGTERM first, so git normally deleted its own partial
    worktree and admin directory. Whatever remains stays: a reserved
    directory git left unregistered is reported with ``reserved_dir_left``
    (see :func:`_leave_reservation`). A worktree git left
    registered is never removed, unlocked or pruned here: it is reported, as
    :data:`worktree_prep.LEFTOVER_KIND` when git still holds its
    ``initializing`` lock, with a removal command to run only after
    verification. Returns the record stored as ``worktree_prep_cleanup``;
    never raises.
    """
    prep["reserved_dir_left"] = os.path.lexists(worktree_path)
    base: dict[str, Any] = {
        "path": str(worktree_path),
        "branch_ref_kept": True,
        "reserved_dir_left": prep["reserved_dir_left"],
    }
    if not git_exited:
        return {
            **base,
            "action": "skipped",
            "reason": "git worktree add not confirmed exited after SIGKILL; nothing touched",
            "error": None,
            "git_exited": False,
        }
    registration = _worktree_registration(repo_root, worktree_path)
    if registration is None:
        return {**base, "action": "error", "reason": "could not list git worktrees; nothing touched", "error": None}
    registered, lock_reason = registration
    if not registered:
        return {**base, **_leave_reservation(worktree_path, prep)}
    report = {
        **base,
        "action": "skipped",
        "error": None,
        "lock_reason": lock_reason,
        "command": worktree_prep.verify_first_command(repo_root, worktree_path),
    }
    if lock_reason == _GIT_INITIALIZING_LOCK_REASON:
        return {
            **report,
            "needs_attention": worktree_prep.LEFTOVER_KIND,
            "reason": "git left a registered worktree locked 'initializing'; never removed automatically",
        }
    return {**report, "reason": f"git left a registered worktree (lock={lock_reason!r}); never removed automatically"}


def _resolve_commit(repo_root: Path, ref: str, env: dict[str, str] | None) -> str | None:
    """Resolve ``ref`` to a commit SHA in ``repo_root``, or ``None``."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
            env=_sanitized_git_env() if env is None else env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    sha = (proc.stdout or "").strip()
    return sha if proc.returncode == 0 and sha else None


def _add_reserved_worktree(
    add_command: list[str],
    *,
    repo_root: Path,
    worktree_path: Path,
    task_id: str,
    run_nonce: str | None = None,
    env: dict[str, str] | None = None,
    base_sha: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run this dispatch's ``git worktree add`` into a freshly reserved path (#8663).

    The path is first reserved with ``mkdir``, which fails when anything is
    already there (git accepts the empty directory). A path that cannot be
    reserved is never passed to git and never removed. ``base_sha`` is the
    commit the add checks out; without it, the last element of
    ``add_command`` is resolved.

    The reservation (see :mod:`scripts.orchestration.worktree_prep`) records
    the reserved directory's device and inode, the base commit, this
    dispatcher's pid and start time, and git's as soon as it is spawned. With
    ``run_nonce``, it is published as ``worktree_prep`` in the task record
    before git starts.

    Returns the completed process on success. On a timeout or a non-zero
    exit, reports what the add left (see :func:`_settle_failed_worktree_add`),
    removing nothing, and raises :class:`WorktreeAddFailed`.
    """
    try:
        os.mkdir(worktree_path)
    except OSError as exc:
        exists = isinstance(exc, FileExistsError)
        raise WorktreeAddFailed(
            f"could not reserve worktree path {worktree_path}: {type(exc).__name__}: {exc}",
            cleanup={
                "path": str(worktree_path),
                "action": "skipped" if exists else "none",
                "reason": "path existed before this dispatch reserved it; never removed"
                if exists
                else "path could not be reserved; git was not run",
                "error": None,
                "branch_ref_kept": True,
            },
        ) from exc
    identity = worktree_prep.directory_identity(worktree_path)
    owner = worktree_prep.process_identity(os.getpid())
    prep: dict[str, Any] = {
        "path": str(worktree_path),
        "run_nonce": run_nonce,
        "reserved_by_mkdir": True,
        "reserved_at": datetime.now(UTC).isoformat(),
        "dir_dev": identity[0] if identity else None,
        "dir_ino": identity[1] if identity else None,
        "base_sha": base_sha or _resolve_commit(repo_root, add_command[-1], env),
        "git_pid": None,
        "git_start": None,
        "owner_pid": owner["pid"],
        "owner_start": owner["start"],
    }

    def record_git(pid: int) -> None:
        git_identity = worktree_prep.process_identity(pid)
        prep["git_pid"] = git_identity["pid"]
        prep["git_start"] = git_identity["start"]
        if run_nonce is not None:
            _update_worktree_prep(task_id, run_nonce, prep)

    if run_nonce is not None:
        try:
            _publish_worktree_prep(task_id, run_nonce, prep)
        except (OSError, RuntimeError) as exc:
            left = _leave_reservation(worktree_path, prep)
            raise WorktreeAddFailed(
                f"could not record the reservation of {worktree_path}: {exc}",
                cleanup={"path": str(worktree_path), **left, "branch_ref_kept": True},
                prep=dict(prep),
            ) from exc
    git_exited = True
    try:
        proc = _run_worktree_add(add_command, cwd=repo_root, worktree_path=worktree_path, env=env, on_spawn=record_git)
    except subprocess.TimeoutExpired as exc:
        # Only a stop that saw git exit proves it can no longer write.
        git_exited = getattr(exc, "git_exited", False)
        message = f"git worktree add timed out after {exc.timeout:.1f}s"
    except OSError as exc:
        message = f"git worktree add could not start: {type(exc).__name__}: {exc}"
    else:
        if proc.returncode == 0:
            if run_nonce is not None:
                _retire_worktree_prep(task_id, run_nonce)
            return proc
        message = (proc.stderr or proc.stdout or "git worktree add failed").strip()
    cleanup = _settle_failed_worktree_add(worktree_path, repo_root=repo_root, git_exited=git_exited, prep=prep)
    if run_nonce is not None:
        _update_worktree_prep(task_id, run_nonce, prep)
    raise WorktreeAddFailed(message, cleanup=cleanup, prep=dict(prep))


def _ensure_sibling_repo_worktree(
    *,
    repo_root: Path,
    agent: str,
    task_id: str,
    raw_path: str | None = None,
    base: str = "main",
    dry_run: bool = False,
    run_nonce: str | None = None,
    detached: bool = False,
    validated_path: Path | None = None,
) -> tuple[Path, str | None, dict[str, Any]]:
    """Create or reuse a layout-A worktree under an allowlisted sibling checkout.

    Public-primary helpers (sparse checkout, data symlinks, mirror-aware
    ``_fetch_base``) stay on :data:`_REPO_ROOT`. Sibling repos get a narrow
    fetch + ``git worktree add`` path so private product/infra trees are not
    forced through public monorepo provisioning (#672 P2.1). ``validated_path``,
    when given, is used as is and never resolved again (#8775).
    """
    root = Path(repo_root).resolve()
    if validated_path is not None:
        worktree_path = validated_path
    elif raw_path is None:
        raise ValueError("a worktree helper needs raw_path or validated_path")
    else:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = root / path
        worktree_path = path.resolve()
    try:
        worktree_path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"sibling worktree path {worktree_path} is outside target repo {root}") from exc
    worktree_branch = None if detached else _derive_worktree_branch(agent, task_id)
    telemetry: dict[str, Any] = {
        "base_sha": None,
        "rebased": False,
        "layout": "dispatch",
        "reused": False,
        "sparse": None,
        "local_venv": None,
        "repo_root": str(root),
    }
    if worktree_path.exists():
        if detached:
            raise ValueError(f"detached read-only worktree already exists: {worktree_path}; refuse reuse")
        if not worktree_path.is_dir():
            raise ValueError(f"worktree path exists but is not a directory: {worktree_path}")
        _refuse_review_attempt_worktree_reuse(worktree_path)
        telemetry["reused"] = True
        actual_sha = _resolve_sha(worktree_path)
        if actual_sha is None:
            raise RuntimeError(f"could not resolve HEAD for existing worktree {worktree_path}")
        telemetry["base_sha"] = actual_sha
        return worktree_path, worktree_branch, telemetry
    if dry_run:
        raise ValueError(
            f"sibling --repo dry-run found no worktree at {worktree_path}; rerun without --dry-run to create one"
        )
    branch_name = _base_branch_name(base)
    origin_ref = f"origin/{branch_name}"
    try:
        fetch_proc = subprocess.run(
            [
                "git",
                "fetch",
                "origin",
                f"+refs/heads/{branch_name}:refs/remotes/origin/{branch_name}",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
            env=_sanitized_git_env(),
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git fetch timed out after {DEFAULT_GIT_TIMEOUT_S}s for sibling repo {root}") from exc
    if fetch_proc.returncode != 0:
        detail = (fetch_proc.stderr or fetch_proc.stdout or "git fetch failed").strip()
        raise RuntimeError(f"could not fetch {origin_ref} in sibling repo {root}: {detail}")
    if _resolve_sha(root, origin_ref) is None:
        raise RuntimeError(f"{origin_ref} unresolvable in sibling repo {root} after fetch")
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    add_command = ["git", "worktree", "add"]
    if detached:
        add_command.extend(["--detach", str(worktree_path), origin_ref])
    else:
        add_command.extend(["-b", worktree_branch, str(worktree_path), origin_ref])
    _add_reserved_worktree(
        add_command,
        repo_root=root,
        worktree_path=worktree_path,
        task_id=task_id,
        run_nonce=run_nonce,
        env=_sanitized_git_env(),
    )
    actual_sha = _resolve_sha(worktree_path)
    if actual_sha is None:
        raise RuntimeError(f"could not resolve HEAD for created worktree {worktree_path}")
    telemetry["base_sha"] = actual_sha
    return worktree_path, worktree_branch, telemetry


def _classify_worktree_layout(path: Path | str | None) -> str | None:
    """Return "dispatch" (new subtree), "flat" (old), "external", or None."""
    if path is None:
        return None
    p = Path(path)
    try:
        rel = p.resolve().relative_to(_REPO_ROOT)
    except ValueError:
        return "external"
    parts = rel.parts
    if parts and parts[0] == ".worktrees":
        if len(parts) >= 4 and parts[1] == "dispatch":
            return "dispatch"
        if len(parts) >= 2:
            return "flat"
    return None


# ---------------------------------------------------------------------------
# Write-capable-mode worktree guard (#4445)
# ---------------------------------------------------------------------------
#
# ``workspace-write`` and ``danger`` let the delegated worker mutate files. Both
# MUST run inside an isolated dispatch worktree so those writes never dirty the
# protected primary checkout — the operator contract must not rely on a model
# *remembering* the worktree rule. ``read-only`` dispatches are exempt from
# this write guard; they get a detached worktree by default or an explicit cwd.

_WRITE_CAPABLE_MODES = frozenset({"workspace-write", "danger"})
# This is deliberately a narrow, directive-only check.  It catches briefs
# whose first-order outcome is a repository mutation without treating an
# ordinary read-only discussion of a proposed change as write intent.
_WRITE_SHAPED_PROMPT_RE = re.compile(
    r"""(?imx)
    ^\s*(?P<prefix>[-*+]\s+|\d+[.)]\s+|\#{1,6}\s+)?(?:please\s+)?
    (?:
        (?:implement|fix|add|update|modify|edit|remove|delete|refactor|rename|create|build)\b
        |
        write\s+(?:(?:new|the)\s+)?(?:code|tests?|scripts?|files?|documentation|docs?)\b
    )
    """,
)
_FENCED_BLOCK_RE = re.compile(r"^(`{3,}|~{3,}).*?^\1", re.DOTALL | re.MULTILINE)
_BLOCKQUOTE_LINE_RE = re.compile(r"^\s*>.*$", re.MULTILINE)
_HEADING_BOUNDARY_RE = re.compile(r"^\s*\#{1,6}\s+")
_LIST_BOUNDARY_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
_THEMATIC_BREAK_RE = re.compile(r"^\s*[-*_]{3,}\s*$")
_NO_DELIVERABLE_STATUS = "no_deliverable"
# A clean read-only checkout holds no uncommitted deliverable. Every terminal
# status the worker can persist is enough to drop it (#8536). Write-capable
# modes stay on the danger rule: only a clean successful ``done``.
_READ_ONLY_SETTLE_REAP_STATUSES = frozenset(
    {
        "done",
        "failed",
        _NO_DELIVERABLE_STATUS,
        "timeout",
        "rate_limited",
        "cancelled",
        "crashed",
        "needs_finalize",
    }
)
# Explicit unattested classification for Cursor Auto when no concrete model was
# extracted (#6964 / #6953). Never record a bare ``"unknown"`` here.
_CURSOR_UNKNOWN_MODEL = "unattested-harness"
_NON_CONCRETE_MODEL_VALUES = frozenset({"", "auto", "default", "unknown", "none", "null", "n/a", "unattested-harness"})


def _cursor_model_state(
    *,
    agent: str,
    result: Any | None = None,
    substitution: dict[str, Any] | None = None,
    initial: bool = False,
) -> dict[str, Any]:
    """Return a truthful Cursor model-attribution companion for task state.

    ``model`` remains the requested selector unless the runtime supplied a
    concrete Cursor model. The separate ``resolved_model`` field makes an
    unresolved Auto run explicit without promoting ``auto`` to family proof.
    """
    if agent != "cursor":
        return {}

    if initial:
        return {
            "resolved_model": _CURSOR_UNKNOWN_MODEL,
            "resolved_model_known": False,
            "resolved_model_source": "pending",
        }

    actual_model: object = None
    source = "unattested-harness"
    known_raw: object = None
    if isinstance(substitution, dict):
        actual_model = substitution.get("actual_model")
        known_raw = substitution.get("actual_model_known")
        source_value = substitution.get("source")
        if isinstance(source_value, str) and source_value.strip():
            source = source_value.strip()

    concrete = actual_model.strip() if isinstance(actual_model, str) else ""
    is_concrete = bool(concrete) and concrete.casefold() not in _NON_CONCRETE_MODEL_VALUES
    explicitly_unknown = str(known_raw).strip().casefold() in {"false", "0", "no"}
    resolved_model = concrete if is_concrete and not explicitly_unknown else _CURSOR_UNKNOWN_MODEL
    known = resolved_model != _CURSOR_UNKNOWN_MODEL
    if not known and source.casefold() in {"unknown", "pending", ""}:
        # Receipts must carry the explicit unattested classification, not a
        # bare "unknown" placeholder (#6953 / #6964).
        source = _CURSOR_UNKNOWN_MODEL

    state = {
        "resolved_model": resolved_model,
        "resolved_model_known": known,
        "resolved_model_source": source,
    }
    if result is not None and known:
        # Keep the legacy ``model`` field useful to consumers that only read
        # one field, while leaving it at the requested ``auto`` selector when
        # attribution is unknown.
        state["model"] = resolved_model
    return state


def _deepseek_model_state(*, agent: str, model: str | None, cache_path: Path | None = None) -> dict[str, Any]:
    """Attest a DeepSeek route from its versioned pin or cached alias name."""
    if agent != "deepseek":
        return {}
    if model == "deepseek-v4-pro":
        return {
            "resolved_model": model,
            "resolved_model_known": True,
            "resolved_model_source": "versioned_first_party_route",
        }
    if model not in {"deepseek-v4.1-flash", "deepseek/deepseek-flash"}:
        return {
            "resolved_model": "unattested-harness",
            "resolved_model_known": False,
            "resolved_model_source": "unrecognized_deepseek_route",
        }
    path = cache_path or Path.home() / ".cache" / "opencode" / "models.json"
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
        name = cache["deepseek"]["models"]["deepseek-flash"]["name"]
    except (OSError, ValueError, KeyError, TypeError):
        name = None
    if name == "DeepSeek V4.1 Flash":
        return {
            "resolved_model": "deepseek-v4.1-flash",
            "resolved_model_known": True,
            "resolved_model_source": "models_dev_cached_alias",
        }
    return {
        "resolved_model": "unattested-harness",
        "resolved_model_known": False,
        "resolved_model_source": "models_dev_alias_unverified",
    }


_NO_DELIVERABLE_UNKNOWN_COMMIT_COUNT_REASON = "commit_count_unknown"
_NO_DELIVERABLE_NO_COMMITS_REASON = "no_commits_no_changes"
_NO_DELIVERABLE_INVALID_DECLARATION_REASON = "invalid_delivery_declaration"
_NO_DELIVERABLE_JUNK_ONLY_WORKTREE_REASON = "junk_only_worktree_changes"
# Auto-finalize refusals (#8991): every deliverable change is outside the
# owned paths, or the task declared no --owned-path at all.
_AUTO_FINALIZE_NOTHING_OWNED_REASON = "no_changes_under_owned_paths"
_AUTO_FINALIZE_NO_OWNED_PATHS_REASON = "no_owned_paths_declared"
_NO_DELIVERABLE_MISSING_REVIEW_VERDICT_REASON = "review_missing_verdict_line"
# Verdict vocabulary mirrors the live review parsers — no third vocabulary
# (#8421): APPROVE is accepted by scripts/build/cf_preflight.py, and
# APPROVED / CHANGES_REQUESTED / BLOCKED by
# scripts/fleet_comms/review_publication.py (and formerly
# scripts/ai_agent_bridge/_review_verdict.py, removed in #8520). REQUEST_CHANGES is the token
# cf_preflight.py and the review prompts actually ask reviewers to write.
# Reviewers routinely render the label and token in Markdown emphasis
# (``**Verdict**: **APPROVE**``, ``VERDICT: **REQUEST_CHANGES**``); those are
# full verdicts and must not be misread as missing (#8786). A verdict line
# STARTS with the label: optional emphasis (``*``, ``_``), ``VERDICT``, then
# emphasis/backticks/whitespace around its colon, then the token and a word
# boundary. Anything may follow the token — reviewers write
# ``**VERDICT: APPROVE.** Both issues are fixed.`` and
# ``**VERDICT: APPROVE** (three non-blocking findings below)``. An inline or
# quoted example ("I will report ``VERDICT: APPROVE`` later",
# ``> VERDICT: APPROVE``) does not start with the label, so is not a verdict.
# The boundary treats ``_`` as emphasis (``__APPROVE__``) unless a letter or
# digit follows it (``APPROVE_LATER``), so ``APPROVEX`` is not a verdict.
# Indentation follows CommonMark: at most three leading spaces; four or more,
# or a tab, make the line an indented code block, i.e. an example.
_REVIEW_VERDICT_LINE_RE = re.compile(
    r"^ {0,3}(?:[*_][*_\s]*)?VERDICT[*_`\s]*:[*_`\s]*"
    r"(APPROVED?|CHANGES_REQUESTED|REQUEST_CHANGES|BLOCKED)"
    r"(?![^\W_]|_+[^\W_])",
    re.IGNORECASE,
)
# A CommonMark fence line: at most three leading spaces, then three or more
# backticks or tildes; group 2 is the rest of the line (info string).
_CODE_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_DELIVERY_DECLARATION_PREFIX = "DELIVERABLE:"
# A declaration is an optional positive signal, so tolerate a few closing
# lines after it — but do not scan the whole report, or a quoted example of
# the format would masquerade as the worker's own declaration.
_DELIVERY_DECLARATION_SCAN_LINES = 5
_DELIVERY_OUTCOMES = frozenset({"change", "no_change"})

_WRITE_WORKTREE_HINT = (
    "Write-capable dispatch must run inside a dispatch worktree, never the "
    "primary checkout. Preferred: pass bare `--worktree` to auto-create "
    ".worktrees/dispatch/<agent>/<task>/. Alternatively point `--cwd` at an "
    "existing added worktree there."
)
_CROSS_REPO_BINDING_HINT = (
    "Dispatch binds the Learn Ukrainian primary checkout that owns this "
    "script, not the invocation cwd. Prefer first-class "
    "`dispatch --repo {infra-private|hramatka} --worktree` (#672 P2.1). "
    "Legacy: create a worktree in the sibling manually "
    "(`git worktree add .worktrees/dispatch/<agent>/<task> <base>`), then "
    "run `dispatch --mode workspace-write --cwd <that-worktree>` without "
    "`--worktree` or `--branch`. See docs/runbooks/agent-seat-onboarding.md."
)


def _strip_quoted_content(prompt: str) -> str:
    """Drop fenced blocks and Markdown blockquotes before the write-intent scan.

    A critique dispatch attaches or includes the brief under review, and that
    brief legitimately contains write-shaped lines ("Add a CLI …").  Quoted
    content is data for the worker to critique, not a directive to mutate the
    repository, so it must not trip the read-only gate (#7814 item 6).
    """
    without_fences = _FENCED_BLOCK_RE.sub("", prompt)
    return _BLOCKQUOTE_LINE_RE.sub("", without_fences)


def _is_list_or_heading_boundary(line: str) -> bool:
    """Return True if line is a markdown heading, list item, or thematic break."""
    return bool(_HEADING_BOUNDARY_RE.match(line) or _LIST_BOUNDARY_RE.match(line) or _THEMATIC_BREAK_RE.match(line))


def _is_write_directive(line: str, prev_non_empty: str | None) -> bool:
    """Classify whether a line in a prompt is a write directive (#8703).

    A line is a directive only if:
    1. It matches the write verb action pattern.
    2. It does not end in '?' (which indicates a question to the reviewer).
    3. It starts a sentence:
       - The line itself is a numbered/bulleted item or heading; OR
       - The previous non-empty line is absent (e.g. first line of the prompt); OR
       - The previous non-empty line ends in '.', ':', '!', '?'; OR
       - The previous non-empty line is a list item or heading boundary.
    A line that continues the previous line's sentence is prose, not a directive.
    """
    match = _WRITE_SHAPED_PROMPT_RE.match(line)
    if not match:
        return False

    # A line ending in '?' is a question to the reviewer, not a directive.
    stripped = line.rstrip()
    if stripped.endswith("?") or stripped.rstrip("\"'`").endswith("?"):
        return False

    # A numbered or bulleted item (or heading) starting with a write verb is a directive.
    if match.group("prefix"):
        return True

    # Continuation rule: a line without a list/heading prefix is a directive
    # only if it starts a sentence (the previous non-empty line is absent,
    # ends in '.', ':', '!', '?', or is a list item / heading boundary).
    # A line that continues the previous line's sentence is prose, not a directive.
    if prev_non_empty is None:
        return True

    prev_stripped = prev_non_empty.rstrip()
    if prev_stripped.rstrip("\"')`").endswith((".", ":", "!", "?")):
        return True

    if _HEADING_BOUNDARY_RE.match(prev_stripped) or _THEMATIC_BREAK_RE.match(prev_stripped):
        return True

    if _LIST_BOUNDARY_RE.match(prev_stripped):
        # Indented line under an unpunctuated list item continues that item's sentence
        is_indented_continuation = line.startswith(("  ", "\t")) and not prev_stripped.rstrip("\"')`").endswith(
            (".", ":", "!", "?")
        )
        return not is_indented_continuation

    return False


def _has_write_directive(prompt: str) -> bool:
    """Scan stripped prompt lines for an unquoted write directive (#8703)."""
    stripped_prompt = _strip_quoted_content(prompt)
    prev_non_empty: str | None = None
    for line in stripped_prompt.splitlines():
        if not line.strip():
            prev_non_empty = None
            continue
        if _is_write_directive(line, prev_non_empty):
            return True
        prev_non_empty = line
    return False


def _read_only_write_intent_error(*, mode: str, prompt: str) -> str | None:
    """Reject clearly write-shaped briefs before a read-only worker starts.

    ``read-only`` remains the default for genuine review and investigation
    work.  A directive to change repository content, however, cannot produce
    its requested deliverable in that mode and must fail before it can look
    like a successful no-op.  The conservative expression intentionally
    requires an instruction-shaped line, rather than matching incidental
    words such as "changes" in a review prompt.  Fenced blocks and blockquote
    lines are excluded from the scan: they carry the brief under critique,
    not the worker's own instructions.  Wrapped continuation prose and
    review questions ending in '?' are not classified as directives (#8703).
    """
    if mode != "read-only":
        return None
    if not _has_write_directive(prompt):
        return None
    return (
        "❌ write-shaped prompt cannot run with --mode read-only. "
        "Re-run with --mode workspace-write --worktree for repository edits "
        "(or --mode danger --worktree only when its extra permissions are required)."
    )


def _parse_delivery_declaration(response: str) -> dict[str, Any] | None:
    """Return a structured outcome declaration from a worker response, if any.

    The declaration is an OPTIONAL positive signal: its presence can prove
    delivery, but its absence never implies failure (git evidence decides
    first). A worker may close with one machine-readable line:

    ``DELIVERABLE: {"outcome":"change",...}`` or
    ``DELIVERABLE: {"outcome":"no_change","reason":"..."}``.

    Only the last few non-empty lines are scanned, so a polite closing line
    after the declaration does not void it while a mid-report example of the
    format is not mistaken for the worker's own declaration.
    """
    lines = [line.strip() for line in response.splitlines() if line.strip()]
    line = next(
        (
            candidate
            for candidate in reversed(lines[-_DELIVERY_DECLARATION_SCAN_LINES:])
            if candidate.startswith(_DELIVERY_DECLARATION_PREFIX)
        ),
        None,
    )
    if line is None:
        return None
    try:
        declaration = json.loads(line.removeprefix(_DELIVERY_DECLARATION_PREFIX).strip())
    except json.JSONDecodeError:
        return None
    if not isinstance(declaration, dict):
        return None
    outcome = declaration.get("outcome")
    if outcome not in _DELIVERY_OUTCOMES:
        return None
    if outcome == "no_change":
        reason = declaration.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            return None
        return {"outcome": outcome, "reason": reason.strip()}
    summary = declaration.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        return None
    changed_paths = declaration.get("changed_paths")
    if (
        not isinstance(changed_paths, list)
        or not changed_paths
        or any(
            not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts
            for path in changed_paths
        )
    ):
        return None
    return {
        "outcome": outcome,
        "summary": summary.strip(),
        "changed_paths": sorted(set(changed_paths)),
    }


def _delivery_failure_reason(
    response: str,
    declaration: dict[str, Any] | None,
    *,
    commits_ahead: int | None,
) -> str | None:
    """Return why a write-capable run lacks delivery evidence, or None.

    Delivery is inferred from observable facts the runner already has —
    own-branch commits and response size — never from a formatting contract
    imposed on every worker's final message:

    - commits on the dispatch branch prove delivery on their own;
    - an unknown commit count proves nothing, so it fails closed;
    - a reasoned ``no_change`` declaration proves a legitimate no-op, while a
      ``change`` claim against a zero-commit branch contradicts the git
      evidence and is flagged;
    - with zero commits and no valid ``no_change`` declaration, there is
      nothing to finalize (#8448). A long "waiting in the background" reply
      is not a deliverable. A reasoned ``no_change`` declaration still is.
    """
    if commits_ahead is None:
        return _NO_DELIVERABLE_UNKNOWN_COMMIT_COUNT_REASON
    if commits_ahead > 0:
        return None
    if declaration is not None:
        if declaration["outcome"] == "no_change":
            return None
        return _NO_DELIVERABLE_INVALID_DECLARATION_REASON
    return _NO_DELIVERABLE_NO_COMMITS_REASON


def _code_fence_opener(line: str) -> str | None:
    """Return the fence run when ``line`` opens a CommonMark code fence.

    A backtick fence's info string may not contain a backtick (that line is
    inline code, not a fence).
    """
    match = _CODE_FENCE_RE.match(line)
    if match is None:
        return None
    fence, info = match.groups()
    if fence[0] == "`" and "`" in info:
        return None
    return fence


def _closes_code_fence(line: str, opener: str) -> bool:
    """Return whether ``line`` closes the fence opened by ``opener``.

    Per CommonMark the closer uses the opener's character, is at least as
    long, and carries nothing but trailing spaces or tabs; any other line —
    including a fence of the other character — is block content.
    """
    match = _CODE_FENCE_RE.match(line)
    if match is None:
        return False
    fence, rest = match.groups()
    return fence[0] == opener[0] and len(fence) >= len(opener) and not rest.strip(" \t")


def parse_review_verdict(response: str) -> str | None:
    """Return the review's verdict token, or ``None`` when it states none.

    The single verdict parser for the review-success contract (#8786): the
    dispatch worker and the ask-* review wrapper both call it. Only a line
    that starts with a verdict (see ``_REVIEW_VERDICT_LINE_RE``) outside a
    code block counts, and the LAST such line wins — a report may discuss earlier
    drafts, but its closing line is its verdict. An unclosed fence runs to the
    end of the text, as in CommonMark.
    """
    verdict: str | None = None
    open_fence: str | None = None
    for line in response.splitlines():
        if open_fence is not None:
            if _closes_code_fence(line, open_fence):
                open_fence = None
            continue
        open_fence = _code_fence_opener(line)
        if open_fence is not None:
            continue
        match = _REVIEW_VERDICT_LINE_RE.match(line)
        if match:
            verdict = match.group(1).upper()
    return verdict


def _review_verdict_failure_reason(response: str) -> str | None:
    """Return the failure reason when a review-typed reply has no verdict line.

    Applies only to dispatches that opt in via ``--require-review-verdict``
    (the ask-* review wrapper); ordinary asks and implement dispatches never
    require a magic marker. A review reply that never states
    ``VERDICT: <APPROVE|APPROVED|CHANGES_REQUESTED|REQUEST_CHANGES|BLOCKED>``
    at the start of a line is not a completed review — on 2026-09-21 several
    review tasks settled ``done`` with a promise to wait for a background
    command as the whole body (#8421).
    """
    if parse_review_verdict(response) is not None:
        return None
    return _NO_DELIVERABLE_MISSING_REVIEW_VERDICT_REASON


def _load_worktree_containment():
    """Import the shared containment predicate (#4444), ensuring repo root on path.

    Mirrors the import guard used for :mod:`scripts.orchestration.reap_worktrees`
    below: running ``scripts/delegate.py`` directly puts ``scripts/`` (not the
    repo root) on ``sys.path``, so the ``scripts.*`` package needs its parent.
    """
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.guardrails import worktree_containment

    return worktree_containment


def _load_primary_write_guard():
    """Import the primary write guard logic (#5389), ensuring repo root on path."""
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.guardrails import primary_write_guard

    return primary_write_guard


def _resolve_cwd_path(raw: str) -> Path:
    """Resolve a ``--cwd`` argument the way the spawned worker will see it.

    A relative ``--cwd`` is handed to the worker subprocess verbatim and thus
    resolved against the dispatch process cwd, so classify it the same way.
    """
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return p.resolve()


# Authoritative repository attribution (#7083). Task state carries the
# dispatch target's ``owner/repo`` slug so the public Work projection can
# scope its delegate join without ever inferring identity from paths or task
# ids at read time. Only GitHub remotes yield a slug; anything else stays
# unclassified (the projection fails closed on it).
_GITHUB_REMOTE_PATTERNS = (
    re.compile(r"^https?://(?:[^/@\s]+@)?github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^ssh://git@github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^git@github\.com:([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^git://github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
)
# Same authoritative-claim contract as scripts/api/delegate_router.py:
# only these fields attribute a task to a repository.
_REPOSITORY_ATTR_FIELDS = ("repository_id", "repository")
# Canonical GitHub home of this repository (#7522): the remote dispatch must
# pin base SHAs to when a host's ``origin`` is only a lagging mirror.
_CANONICAL_GITHUB_REPO = "learn-ukrainian/learn-ukrainian.github.io"


def _parse_github_owner_repo(remote_url: str | None) -> str | None:
    """Return ``owner/repo`` for a GitHub remote URL, else None (fail closed)."""
    if not remote_url:
        return None
    text = remote_url.strip()
    for pattern in _GITHUB_REMOTE_PATTERNS:
        match = pattern.match(text)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return None


_GITCONFIG_REMOTE_SECTION_RE = re.compile(r'^\s*\[\s*remote\s+"([^"]+)"\s*\]')
_GITCONFIG_ANY_SECTION_RE = re.compile(r"^\s*\[")
_GITCONFIG_URL_RE = re.compile(r"^\s*url\s*=\s*(.+?)\s*$")


def _git_common_dir(root: Path) -> Path | None:
    """Return the git common dir for a checkout or linked worktree.

    Pure filesystem — never a git subprocess. The dispatch path stays
    independent of the ``subprocess.Popen`` stubs used by dispatch tests,
    same contract as :func:`_resolve_invocation_git_root`.
    """
    dot_git = root / ".git"
    try:
        if dot_git.is_dir():
            return dot_git
        if not dot_git.is_file():
            return None
        text = dot_git.read_text(encoding="utf-8", errors="replace").strip()
        if not text.startswith("gitdir:"):
            return None
        gitdir = Path(text.split(":", 1)[1].strip())
        if not gitdir.is_absolute():
            gitdir = (root / gitdir).resolve()
        commondir_file = gitdir / "commondir"
        if commondir_file.is_file():
            common = Path(commondir_file.read_text(encoding="utf-8", errors="replace").strip())
            if not common.is_absolute():
                common = (gitdir / common).resolve()
            return common
        return gitdir
    except OSError:
        return None


def _git_remote_urls(root: Path) -> dict[str, str]:
    """Map remote names to URLs from the checkout's common git config.

    Pure filesystem, same contract as :func:`_git_common_dir` — never a git
    subprocess, so dispatch-path logic stays independent of the
    ``subprocess.Popen`` stubs used by dispatch tests and hook environments.
    The first ``url`` entry wins for remotes configured with multiple URLs.
    """
    common = _git_common_dir(root)
    if common is None:
        return {}
    try:
        lines = (common / "config").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    urls: dict[str, str] = {}
    current_remote: str | None = None
    for line in lines:
        remote_section = _GITCONFIG_REMOTE_SECTION_RE.match(line)
        if remote_section:
            current_remote = remote_section.group(1)
            continue
        if _GITCONFIG_ANY_SECTION_RE.match(line):
            current_remote = None
            continue
        if current_remote is not None:
            url = _GITCONFIG_URL_RE.match(line)
            if url and current_remote not in urls:
                urls[current_remote] = url.group(1)
    return urls


def _read_origin_url(root: Path) -> str | None:
    """Read ``remote.origin.url`` from the checkout's common git config."""
    return _git_remote_urls(root).get("origin")


def _resolve_canonical_remote_name(remote_urls: dict[str, str]) -> str | None:
    """Return the name of the remote that serves the canonical GitHub repo.

    Prefers a remote literally named ``github`` whose URL is the canonical
    ``owner/repo``; otherwise ``origin`` when origin itself is that GitHub
    URL. Any other layout stays unclassified (None) so the dispatch path
    keeps its origin-only behavior instead of inventing a remote (#7522).
    """
    github_url = remote_urls.get("github")
    if github_url and _parse_github_owner_repo(github_url) == _CANONICAL_GITHUB_REPO:
        return "github"
    origin_url = remote_urls.get("origin")
    if origin_url and _parse_github_owner_repo(origin_url) == _CANONICAL_GITHUB_REPO:
        return "origin"
    return None


def _resolve_dispatch_repository(target: str | Path | None) -> str | None:
    """Resolve the authoritative ``owner/repo`` identity for a dispatch target.

    Reads the target checkout's git config from disk — never a network call,
    never a subprocess. A target inside the primary checkout (including an
    auto worktree, existing or already reaped) binds the primary's origin by
    construction; any other target must exist on disk so its own
    ``remote.origin.url`` can be read. Returns None when no GitHub slug can be
    proven — callers then leave the task unclassified rather than guess.
    """
    if target is None or str(target) == "":
        return None
    try:
        target_path = Path(target).expanduser().resolve()
        primary = _REPO_ROOT.resolve()
    except OSError:
        return None
    if target_path == primary or primary in target_path.parents:
        config_dir = primary
    elif target_path.is_dir():
        config_dir = target_path
    else:
        return None
    return _parse_github_owner_repo(_read_origin_url(config_dir))


def _state_repository_claims(state: dict[str, Any]) -> list[str]:
    """Return the distinct authoritative repository claims on a task state."""
    claims: list[str] = []
    for field_name in _REPOSITORY_ATTR_FIELDS:
        raw = state.get(field_name)
        if raw is None or raw == "":
            continue
        text = str(raw).strip()
        if text and text not in claims:
            claims.append(text)
    return claims


def _resolve_invocation_git_root(start: Path | str | None = None) -> Path | None:
    """Primary checkout that owns ``start`` (default: process cwd), or None.

    Walks ``.git`` on disk instead of calling ``git rev-parse``. The answer we
    need is "same repository or a sibling?", and the filesystem shape already
    distinguishes a primary ``.git`` directory from a linked worktree gitdir.
    Avoiding a git subprocess also keeps this preflight independent of the
    ``subprocess.Popen`` stubs used by dispatch tests and hook environments.
    """
    wc = _load_worktree_containment()
    origin = wc.canonicalize(start if start is not None else Path.cwd())
    probe = origin if origin.is_dir() else origin.parent
    return wc._fs_main_root(probe)


def _resolve_cross_repo_binding_error(
    *,
    worktree_arg: str | None,
    cwd_arg: str | None,
    requested_branch: str | None = None,
    invocation_cwd: Path | str | None = None,
    target_repo_root: Path | str | None = None,
) -> str | None:
    """Refuse silent primary-repo binding when invoked from another git root.

    ``--worktree`` / ``--branch`` without ``--repo`` still create under
    :data:`_REPO_ROOT` (see :func:`_auto_worktree_path`). An invocation cwd
    whose git root is a sibling checkout used to look like "dispatch here"
    while the worktree landed in the primary — issue #6900.

    With allowlisted ``--repo`` (#672 P2.1), worktrees are created under the
    resolved sibling checkout; the guard allows that explicit retarget.
    """
    invocation_root = _resolve_invocation_git_root(invocation_cwd)
    if invocation_root is None:
        return None
    wc = _load_worktree_containment()
    primary = wc.canonicalize(_REPO_ROOT)
    if invocation_root == primary:
        return None
    if target_repo_root is not None:
        target = wc.canonicalize(target_repo_root)
        if invocation_root == target:
            return None
        # Explicit --repo retargets creation even when the shell sits elsewhere.
        if target != primary:
            return None
    # Documented sibling flow: explicit --cwd, never --worktree/--branch.
    # cmd_dispatch promotes a bare --branch to worktree_arg="auto" first.
    if cwd_arg and not worktree_arg and not requested_branch:
        return None
    flags = [flag for flag, present in (("--worktree", worktree_arg), ("--branch", requested_branch)) if present]
    flag_bit = (
        " and ".join(flags) + " would silently create or attach a worktree under the primary"
        if flags
        else "the worker would silently run in the primary checkout"
    )
    return (
        f"❌ dispatch targets the primary checkout ({primary}); "
        f"invocation cwd resolves to a different git root ({invocation_root}). "
        f"{flag_bit}.\n   {_CROSS_REPO_BINDING_HINT}"
    )


# Runtime worktrees the ACP bridge creates, git-locks, and removes on its own
# schedule (scripts/ai_agent_bridge/_acp_execution.py). They are never a
# dispatch attach target (#8610).
_ACP_RUNTIME_SUBTREE = (".worktrees", "dispatch", "acp")


def _is_acp_runtime_path(path: Path) -> bool:
    """True when ``path`` lies in a repository's ``.worktrees/dispatch/acp/`` subtree."""
    parts = path.parts
    width = len(_ACP_RUNTIME_SUBTREE)
    return any(parts[index : index + width] == _ACP_RUNTIME_SUBTREE for index in range(len(parts) - width + 1))


def _resolve_acp_runtime_target_error(
    *,
    worktree_arg: str | None,
    cwd_arg: str | None,
    target_repo_root: Path,
) -> str | None:
    """Refuse a dispatch whose ``--cwd`` or explicit ``--worktree`` is an ACP runtime.

    The ACP bridge removes its runtime worktrees without consulting dispatch
    task records, so a worker attached to one could lose its cwd (#8610).
    Checked for every mode, before any side effect.
    """
    candidates: list[tuple[str, str, Path]] = []
    if cwd_arg:
        candidates.append(("--cwd", cwd_arg, _resolve_cwd_path(cwd_arg)))
    if worktree_arg and worktree_arg != "auto":
        candidates.append(
            ("--worktree", worktree_arg, _normalize_worktree_path(worktree_arg, repo_root=target_repo_root))
        )
    for flag, raw, candidate in candidates:
        if _is_acp_runtime_path(candidate):
            return (
                f"❌ {flag} {raw!r} resolves inside an ACP runtime worktree ({candidate}); "
                ".worktrees/dispatch/acp/ belongs to the ACP bridge and is never a dispatch target.\n"
                "   Pass bare `--worktree` to auto-create .worktrees/dispatch/<agent>/<task>/, "
                "or point `--cwd` at an existing dispatch worktree."
            )
    return None


def _resolve_verified_worktree_path(path: Path) -> Path | None:
    """Return canonical Path of the containing registered worktree if ``path`` resolves
    inside a git-registered worktree that is not the primary checkout, else None.

    "Verified" means the containing worktree appears in ``git worktree list``. A
    bare directory that only *looks* like ``.worktrees/**`` but was never
    ``git worktree add``-ed does NOT qualify — the worker would otherwise run
    outside any real worktree while believing it was isolated. An ACP runtime
    worktree does not qualify either (:func:`_is_acp_runtime_path`).
    """
    wc = _load_worktree_containment()
    target = wc.canonicalize(path)
    if target == wc.canonicalize(_REPO_ROOT):
        # The exact primary root cannot be an added worktree. This common
        # explicit --cwd path needs no git subprocess before worker spawn.
        return None
    start = target if target.exists() else target.parent
    try:
        main_root = wc.resolve_main_root(start)
    except wc.NotAGitRepositoryError:
        return None
    for worktree in wc.registered_worktrees(main_root):
        if worktree == main_root:
            continue
        if target == worktree or target.is_relative_to(worktree):
            return None if _is_acp_runtime_path(worktree) else worktree
    return None


def _is_verified_added_worktree(path: Path) -> bool:
    """True if ``path`` resolves inside a git-registered worktree that is not the
    primary checkout.
    """
    return _resolve_verified_worktree_path(path) is not None


def _apply_worktree_git_ceiling(worker_env: dict[str, str], worktree_path: Path) -> None:
    """Pin GIT_CEILING_DIRECTORIES at the worktree's PARENT (#5803 follow-up).

    Damage reduction, NOT isolation: stops git repo discovery at the dispatch
    parent dir so a broken/missing worktree .git pointer can never bind the
    worker to the PRIMARY checkout via upward traversal. The ceiling must be
    the parent — a ceiling at the worktree root itself excludes the root from
    the discovery walk and breaks git from subdirectories (verified
    2026-07-25). Linked worktrees resolve their own .git file at the root and
    share the git control plane, so normal ops (subdirs, fetch, commit) are
    unaffected.
    """
    ceiling = str(worktree_path.parent)
    existing_ceiling = worker_env.get("GIT_CEILING_DIRECTORIES")
    worker_env["GIT_CEILING_DIRECTORIES"] = f"{existing_ceiling}{os.pathsep}{ceiling}" if existing_ceiling else ceiling


def _resolve_write_cwd_error(
    *,
    mode: str,
    worktree_arg: str | None,
    cwd_arg: str | None,
) -> str | None:
    """Reject a write-capable dispatch that would run outside a verified worktree.

    Returns an operator-facing error string, or None when the dispatch is safe.
    Evaluated before any side effects (log files, ``git worktree add``) so a
    rejection leaves no worktree/branch residue behind.

    Policy (issue #4445):

    * ``--worktree`` (bare/``auto``) is the recommended path and always lands in
      ``.worktrees/dispatch/<agent>/<task>/`` — :func:`_ensure_worktree` creates
      or validates it. An explicit ``--worktree PATH`` is rejected only when it
      *is* the primary checkout.
    * ``--cwd`` is allowed only when it resolves to a verified added worktree,
      never the primary checkout or a bare in-repo directory.
    * With neither flag the worker would default to the primary checkout, so a
      write-capable dispatch is rejected outright.
    """
    if mode not in _WRITE_CAPABLE_MODES:
        return None

    wc = _load_worktree_containment()

    if worktree_arg:
        # Bare ``--worktree`` (the sentinel ``auto``) auto-derives the dispatch
        # subtree — always isolated, nothing to verify up front.
        if worktree_arg == "auto":
            return None
        candidate = _normalize_worktree_path(worktree_arg)
        if wc.is_primary_checkout(candidate):
            return (
                f"❌ --worktree {worktree_arg!r} points at the primary checkout; "
                f"write-capable dispatch may not run there.\n   {_WRITE_WORKTREE_HINT}"
            )
        return None

    if cwd_arg:
        candidate = _resolve_cwd_path(cwd_arg)
        if wc.is_primary_checkout(candidate):
            return (
                f"❌ --cwd {cwd_arg!r} resolves inside the primary checkout; "
                f"write-capable dispatch may not run there.\n   {_WRITE_WORKTREE_HINT}"
            )
        if not _is_verified_added_worktree(candidate):
            return (
                f"❌ --cwd {cwd_arg!r} is not a verified git worktree; "
                f"write-capable dispatch requires an added worktree under "
                f".worktrees/dispatch/<agent>/<task>/.\n   {_WRITE_WORKTREE_HINT}"
            )
        return None

    return (
        f"❌ --mode {mode} requires an isolated worktree; without --worktree/--cwd "
        f"the worker would run in the primary checkout.\n   {_WRITE_WORKTREE_HINT}"
    )


def _format_dirty_entries(entries: list[dict[str, str]], *, limit: int = 10) -> str:
    shown = [f"{entry.get('xy', '').strip() or '??'} {entry.get('path', '')}" for entry in entries[:limit]]
    if len(entries) > limit:
        shown.append(f"... and {len(entries) - limit} more")
    return ", ".join(shown) if shown else "(none)"


# Declared receipt collection points unignored in .gitignore as tracked-by-design (#6967).
# Untracked files under these directories are allowlisted by the clean-tree guard so
# concurrent jobs writing receipts do not block write-capable dispatches.
_CLEAN_TREE_UNTRACKED_RECEIPT_ALLOWLIST: tuple[str, ...] = ("batch_state/atlas-jobs/receipts/",)


def _is_untracked_receipt_allowlisted(entry: dict[str, str]) -> bool:
    """Return True if entry is an untracked file under a declared receipt collection point."""
    if entry.get("kind") != "untracked" and entry.get("xy", "").strip() != "??":
        return False
    raw_path = (entry.get("path") or "").replace("\\", "/")
    if raw_path.startswith("./"):
        raw_path = raw_path[2:]
    raw_path = raw_path.lstrip("/")
    for prefix in _CLEAN_TREE_UNTRACKED_RECEIPT_ALLOWLIST:
        clean_prefix = prefix.strip("/")
        if raw_path == clean_prefix or raw_path.startswith(clean_prefix + "/"):
            return True
    return False


def _resolve_dirty_primary_checkout_error(*, mode: str) -> str | None:
    """Reject write-capable dispatch when the protected primary checkout is dirty.

    This is separate from the #4445 isolation check: even a correctly isolated
    new worktree should not be dispatched while main/master already has tracked
    or untracked non-ignored dirt, because the next worker inherits polluted
    operator state. Read-only dispatches stay allowed for preflight and diagnosis.
    """
    if mode not in _WRITE_CAPABLE_MODES:
        return None

    wc = _load_worktree_containment()
    try:
        status = wc.primary_checkout_dirty_status(_REPO_ROOT)
    except Exception as exc:
        return (
            "❌ could not verify primary checkout cleanliness before "
            f"write-capable dispatch: {type(exc).__name__}: {exc}"
        )

    if not status.get("protected_branch") or not status.get("dirty"):
        return None

    raw_entries = status.get("entries") or []
    entries = [entry for entry in raw_entries if not _is_untracked_receipt_allowlisted(entry)]
    if not entries:
        return None

    extra_diagnostic = ""
    try:
        pwg = _load_primary_write_guard()
        writable = pwg.get_writable_tracked_files(_REPO_ROOT)
        if writable:
            offenders = [str(f.relative_to(_REPO_ROOT)) for f in writable]
            extra_diagnostic = f"   writable tracked files (guard OFF): {', '.join(offenders)}\n"
        else:
            extra_diagnostic = "   writable tracked files (guard ON): (none)\n"
    except Exception as exc:
        extra_diagnostic = f"   could not check write guard status: {exc}\n"

    return (
        "❌ primary checkout is dirty; refusing write-capable dispatch before "
        "creating branch/worktree residue.\n"
        f"   checkout role: {status.get('role')}\n"
        f"   head: {status.get('head_sha')}\n"
        f"   command: {status.get('checked_command')}\n"
        f"   branch: {status.get('branch')}\n"
        f"   dirty files: {_format_dirty_entries(entries)}\n"
        f"{extra_diagnostic}"
        "   Clean/stash the primary checkout, or keep only gitignored local "
        "runtime state, then retry."
    )


def _resolve_primary_integrity_error(*, mode: str) -> str | None:
    """Block NEW write-capable dispatches while the primary checkout is drifted.

    #5803 follow-up: a worker detached the primary (`checkout: moving from main
    to FETCH_HEAD`) and every worktree branched afterwards would inherit a
    wrong base. The watchdog only diagnoses and records drift here; new
    write-capable dispatches stop until an operator explicitly repairs the
    checkout. Read-only dispatches stay allowed for preflight and diagnosis,
    same contract as the dirty-primary guard.
    """
    if mode not in _WRITE_CAPABLE_MODES:
        return None

    try:
        try:
            from scripts.audit.check_primary_integrity import check_primary_integrity
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_primary_integrity import check_primary_integrity

        ok, message = check_primary_integrity(_REPO_ROOT, fix=False, tasks_dir=tasks_dir())
    except Exception as exc:
        print(
            f"⚠️  primary-integrity watchdog errored ({type(exc).__name__}: {exc}); "
            "proceeding — the health-poll canary will surface persistent failures",
            file=sys.stderr,
        )
        return None

    if ok:
        return None

    return (
        "❌ primary checkout drift is UNREPAIRED; refusing to start a new "
        "write-capable dispatch (it would branch from a wrong base). Running "
        "dispatches are not touched.\n"
        f"   watchdog: {message}\n"
        "   Inspect the primary checkout and run the explicit doctor only when "
        "appropriate: .venv/bin/python scripts/audit/check_primary_integrity.py "
        "--fix. Evidence is under "
        "data/telemetry/primary-integrity/events.jsonl."
    )


def _warn_venv_integrity() -> None:
    """Advisory-only primary-venv integrity probe (#6830 follow-up).

    A mid-session venv rebuild can leave `.venv` empty (every import fails)
    or with console-script launchers pointing at a deleted worktree venv
    (`pytest`/`py.test`/`cbor2` live finding). This probe DETECTS and RECORDS
    such corruption; it never blocks a dispatch and never repairs here —
    reinstalling packages is a package mutation, gated to an explicit
    operator command (see check_venv_integrity.py). Fails open on any probe
    error, same contract as the sibling integrity watchdogs.
    """
    try:
        try:
            from scripts.audit.check_venv_integrity import check_venv_integrity
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_venv_integrity import check_venv_integrity

        ok, message = check_venv_integrity(_REPO_ROOT, tasks_dir=tasks_dir())
    except Exception as exc:
        print(
            f"⚠️  venv-integrity probe errored ({type(exc).__name__}: {exc}); "
            "proceeding — detection only, never blocks dispatch",
            file=sys.stderr,
        )
        return

    if not ok:
        print(f"⚠️  {message}", file=sys.stderr)


def _warn_worktree_cleanup_integrity() -> None:
    """Advisory-only worktree-cleanup launchd probe (#6937 follow-up).

    A venv rebuild can leave launchd unable to start
    ``com.learn-ukrainian.worktree-cleanup`` (LWCR init failure, exit 78)
    with no new receipt for days. This probe DETECTS and RECORDS that
    darkness; it never blocks a dispatch and never reloads launchd here —
    reinstall is an explicit operator action from the merged primary.
    Fails open on any probe error, same contract as the sibling integrity
    watchdogs.
    """
    try:
        try:
            from scripts.audit.check_worktree_cleanup_integrity import (
                check_worktree_cleanup_integrity,
            )
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_worktree_cleanup_integrity import (
                check_worktree_cleanup_integrity,
            )

        ok, message = check_worktree_cleanup_integrity(_REPO_ROOT, tasks_dir=tasks_dir())
    except Exception as exc:
        print(
            f"⚠️  worktree-cleanup-integrity probe errored ({type(exc).__name__}: {exc}); "
            "proceeding — detection only, never blocks dispatch",
            file=sys.stderr,
        )
        return

    if not ok:
        print(f"⚠️  {message}", file=sys.stderr)


def _warn_node_modules_integrity() -> None:
    """Advisory-only node_modules symlink-corruption probe (#6818 follow-up).

    `_provision_data_symlinks` symlinks the primary's `node_modules` and
    `site/node_modules` directly into every dispatch worktree — any write a
    worktree makes through that path lands in the primary's real files
    (#6805 incident). This probe DETECTS and RECORDS such corruption; per the
    K3-reviewed design it never blocks a dispatch and never repairs here —
    auto-repair is gated on the Node-version pin landing first and is a
    separate operator decision (see check_node_modules_integrity.py). Fails
    open on any probe error, same contract as the primary-integrity watchdog.
    """
    try:
        try:
            from scripts.audit.check_node_modules_integrity import (
                check_node_modules_integrity,
            )
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_node_modules_integrity import check_node_modules_integrity

        ok, message = check_node_modules_integrity(_REPO_ROOT, tasks_dir=tasks_dir())
    except Exception as exc:
        print(
            f"⚠️  node_modules-integrity probe errored ({type(exc).__name__}: {exc}); "
            "proceeding — detection only, never blocks dispatch",
            file=sys.stderr,
        )
        return

    if not ok:
        print(f"⚠️  {message}", file=sys.stderr)


def _warn_if_monitor_api_unreachable() -> None:
    """Make a dead local Monitor API visible without making dispatch depend on it.

    Dispatch remains a recovery path when the dashboard is down. The warning is
    deliberately advisory, unlike primary-integrity drift, because workers can
    still run with their file-based fallbacks and may be needed to repair the
    API itself.
    """
    url = f"{_monitor_api_base_url()}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            if response.status != 200:
                raise MonitorApiUnavailable(f"HTTP {response.status}")
    except (OSError, TimeoutError, urllib.error.URLError, MonitorApiUnavailable) as exc:
        detail = f"{type(exc).__name__}: {exc}"
        _append_dispatch_event("monitor_api_unreachable_pre_dispatch", url=url, detail=detail)
        print(
            "⚠ MONITOR API UNREACHABLE — dispatch will continue with offline fallbacks.\n"
            f"   probe: GET {url}\n"
            f"   error: {detail}\n"
            "   recovery: ./services.sh status api; inspect .pids/api-last-crash.json; "
            "then ./services.sh restart api",
            file=sys.stderr,
        )


def _origin_tracking_refspec(branch: str) -> str:
    """Explicit fetch mapping that lands ``branch`` under refs/remotes/origin."""
    from scripts.common.git_context import origin_tracking_refspec

    return origin_tracking_refspec(branch)


def _fetch_remote_branch(remote: str, branch: str) -> subprocess.CompletedProcess[str] | None:
    """Fetch ``branch`` from ``remote`` into the origin tracking ref.

    Returns None when the fetch could not run at all (spawn failure or
    timeout); a completed process with a nonzero returncode is returned
    as-is so callers can fail closed carrying git's own diagnostics.
    """
    try:
        return subprocess.run(
            ["git", "fetch", remote, _origin_tracking_refspec(branch)],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_NETWORK_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _ls_remote_branch_sha(remote: str, branch: str) -> str | None:
    """Probe the SHA ``remote`` serves for ``branch`` without touching refs.

    ``git ls-remote`` answers from the remote directly, so a lagging mirror
    can be detected (#7522) while ``refs/remotes/origin/<branch>`` is written
    only by the canonical fetch. Best-effort: a spawn failure, timeout, or
    unresolved ref yields None.
    """
    try:
        proc = subprocess.run(
            ["git", "ls-remote", remote, f"refs/heads/{branch}"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_NETWORK_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    for line in (proc.stdout or "").splitlines():
        sha, sep, ref = line.partition("\t")
        if sep and ref.strip() == f"refs/heads/{branch}":
            return sha.strip() or None
    return None


def _verify_origin_tracking_ref(branch: str) -> subprocess.CompletedProcess[str] | None:
    """Verify that ``origin/<branch>`` resolves after a mapped fetch."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "--verify", f"origin/{branch}"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _fetch_origin_branch(branch: str) -> bool:
    """Single-remote fetch contract: fetch origin, report success as bool."""
    proc = _fetch_remote_branch("origin", branch)
    if proc is None or proc.returncode != 0:
        return False
    verify = _verify_origin_tracking_ref(branch)
    return verify is not None and verify.returncode == 0


def _canonical_fetch_failure_error(
    *,
    branch: str,
    canonical_remote: str,
    canonical_url: str,
    mirror_url: str,
    detail: str,
) -> RuntimeError:
    """Build the #7522 fail-closed error for a canonical-remote fetch failure."""
    return RuntimeError(
        f"could not fetch base branch {branch!r} from canonical GitHub remote "
        f"'{canonical_remote}' ({canonical_url}): {detail}. Remote 'origin' is "
        f"{mirror_url!r} (a non-canonical mirror) and was NOT used as a fallback — "
        "a lagging mirror must never pin the worktree base. Recovery: inspect "
        "`git remote -v`, then run "
        f"`git fetch {canonical_remote} {_origin_tracking_refspec(branch)}` and "
        "retry the dispatch."
    )


def _fetch_base(base: str) -> bool:
    """Fetch the dispatch base branch into ``origin/<branch>``.

    ``base`` may be a plain branch name (``main``), an origin-prefixed ref
    (``origin/main`` — the form the dispatch runbooks mandate), or a
    github-prefixed one (``github/main``). The remote refspec is an explicit
    mapping ``+refs/heads/<branch>:refs/remotes/origin/<branch>`` so the
    remote-tracking ref exists regardless of host git fetch refspec config
    (#7168).

    #7522: on hosts where ``origin`` is a lagging mirror and a separate
    remote points at the canonical GitHub repository, the base must be
    fetched from that canonical remote — the mirror is probed read-only
    (``git ls-remote``) only so divergence can be warned about, and a
    canonical fetch failure fails closed instead of silently pinning the
    mirror's stale SHA. The canonical fetch is the only writer of
    ``refs/remotes/origin/<branch>``: a fail-closed dispatch leaves the
    prior tracking ref untouched, never pinned to the lagging mirror.
    """
    branch = _base_branch_name(base)
    remote_urls = _git_remote_urls(_REPO_ROOT)
    canonical_remote = _resolve_canonical_remote_name(remote_urls)
    if canonical_remote is None or canonical_remote == "origin":
        # Single-remote hosts — origin is the canonical GitHub remote, or no
        # GitHub remote is configured at all. Exactly the pre-#7522 origin
        # fetch, including its bool failure contract: callers own the
        # instructive fail-closed message.
        return _fetch_origin_branch(branch)

    canonical_url = remote_urls.get(canonical_remote) or "<unknown url>"
    mirror_url = remote_urls.get("origin") or "<unknown url>"

    # Probe the mirror read-only — never a fetch. A mirror fetch lands its
    # lagging SHA in refs/remotes/origin/<branch>; if the canonical fetch
    # below then fails closed, the tracking ref would stay poisoned at that
    # stale SHA. ls-remote writes no local ref, so the canonical fetch is
    # the only writer of the tracking ref.
    mirror_sha: str | None = None
    if "origin" in remote_urls:
        mirror_sha = _ls_remote_branch_sha("origin", branch)

    canonical_proc = _fetch_remote_branch(canonical_remote, branch)
    if canonical_proc is None:
        raise _canonical_fetch_failure_error(
            branch=branch,
            canonical_remote=canonical_remote,
            canonical_url=canonical_url,
            mirror_url=mirror_url,
            detail=f"fetch timed out or failed to start after {DEFAULT_NETWORK_GIT_TIMEOUT_S}s",
        )
    if canonical_proc.returncode != 0:
        raise _canonical_fetch_failure_error(
            branch=branch,
            canonical_remote=canonical_remote,
            canonical_url=canonical_url,
            mirror_url=mirror_url,
            detail=_format_process_failure(canonical_proc),
        )
    canonical_sha = _resolve_sha(_REPO_ROOT, f"origin/{branch}")
    if canonical_sha is None:
        raise _canonical_fetch_failure_error(
            branch=branch,
            canonical_remote=canonical_remote,
            canonical_url=canonical_url,
            mirror_url=mirror_url,
            detail=f"fetched, but refs/remotes/origin/{branch} did not resolve afterwards",
        )
    if mirror_sha is not None and mirror_sha != canonical_sha:
        print(
            f"⚠️  remote 'origin' ({mirror_url}) lags the canonical GitHub remote "
            f"'{canonical_remote}' ({canonical_url}) for branch {branch!r}: "
            f"origin SHA {mirror_sha} != canonical SHA {canonical_sha}. "
            "Dispatching from the canonical GitHub SHA.",
            file=sys.stderr,
        )
    return True


def _validate_branch_reuse_name(branch: str) -> str:
    """Reject unsafe or ambiguous ``--branch`` values before attaching a worktree."""
    from scripts.common.git_context import UnsafeBranchNameError, validate_plain_branch_name

    try:
        normalized = validate_plain_branch_name(branch, repo_root=_REPO_ROOT)
    except UnsafeBranchNameError as exc:
        raise ValueError(
            "--branch must be a local branch name without origin/, github/, or refs/ "
            f"prefixes, and a valid git branch: got {branch!r} ({exc})"
        ) from exc

    containment = _load_worktree_containment()
    if normalized in containment.PROTECTED_BRANCHES:
        raise ValueError(
            f"refusing --branch {normalized!r}: protected branches may not be attached to a dispatch worktree"
        )
    return normalized


def _fetch_existing_branch(branch: str) -> None:
    """Fetch and verify the remote branch used by ``--branch`` reuse mode.

    The remote refspec is an explicit mapping ``+refs/heads/<branch>:refs/remotes/origin/<branch>``
    so the remote-tracking ref exists regardless of host git fetch refspec config (#7168).
    #7522: when a canonical GitHub remote is configured it is the fetch
    source — a host mirror may lag or not carry the PR branch at all.
    """
    remote_urls = _git_remote_urls(_REPO_ROOT)
    canonical_remote = _resolve_canonical_remote_name(remote_urls)
    remote_name = canonical_remote or "origin"
    refspec = _origin_tracking_refspec(branch)
    try:
        proc = subprocess.run(
            ["git", "fetch", remote_name, refspec],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_NETWORK_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"could not fetch existing branch {branch!r} from remote {remote_name!r}: "
            f"fetch timed out after {DEFAULT_NETWORK_GIT_TIMEOUT_S}s"
        ) from exc
    if proc.returncode != 0:
        if canonical_remote is not None and canonical_remote != "origin":
            raise RuntimeError(
                f"could not fetch existing branch {branch!r} from canonical GitHub "
                f"remote '{canonical_remote}' ({remote_urls.get(canonical_remote)}): "
                f"{_format_process_failure(proc)}. Remote 'origin' is "
                f"{remote_urls.get('origin')!r} (a non-canonical mirror) and was NOT "
                "used as a fallback — the mirror may lag or not carry the PR branch. "
                "Recovery: inspect `git remote -v`, then run "
                f"`git fetch {canonical_remote} {refspec}` and retry the dispatch."
            )
        raise RuntimeError(f"could not fetch existing branch {branch!r}: {_format_process_failure(proc)}")
    try:
        verify = subprocess.run(
            ["git", "rev-parse", "--verify", f"origin/{branch}"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"origin/{branch} was not found after fetch; rev-parse timed out after {DEFAULT_GIT_TIMEOUT_S}s"
        ) from exc
    if verify.returncode != 0:
        raise RuntimeError(f"origin/{branch} was not found after fetch; --branch requires an existing remote branch")


def _require_local_branch_is_ancestor_of_origin(branch: str) -> str:
    """Return fetched origin SHA or refuse a local-only branch divergence."""
    origin_ref = f"origin/{branch}"
    local_ref = f"refs/heads/{branch}"
    origin_sha = _resolve_sha(_REPO_ROOT, origin_ref)
    if origin_sha is None:
        raise RuntimeError(f"{origin_ref} was not found after fetch; --branch requires an existing remote branch")
    local_sha = _resolve_sha(_REPO_ROOT, local_ref)
    if local_sha is None or local_sha == origin_sha:
        return origin_sha

    try:
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", local_ref, origin_ref],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"could not compare local {branch!r} against {origin_ref}: merge-base timed out after {DEFAULT_GIT_TIMEOUT_S}s"
        ) from exc
    if ancestry.returncode == 0:
        return origin_sha
    if ancestry.returncode != 1:
        raise RuntimeError(
            f"could not compare local {branch!r} against {origin_ref}: {_format_process_failure(ancestry)}"
        )
    raise WorktreeBranchDiverged(
        f"refusing --branch {branch!r}: local {local_ref} is not an ancestor of "
        f"{origin_ref}; local_sha={local_sha} origin_sha={origin_sha}. "
        "Reconcile explicitly before dispatching: inspect with "
        f"`git log --left-right --graph --oneline {local_ref}...{origin_ref}`; "
        f"to preserve local commits, run `git switch {branch} && git rebase {origin_ref}` "
        f"then `git push --force-with-lease origin {branch}`; to discard the local-only "
        f"ref, run `git branch -f {branch} {origin_ref}`."
    )


def _branch_worktree_paths(branch: str) -> list[Path]:
    """Return registered worktree roots currently attached to ``branch``."""
    try:
        proc = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"could not list git worktrees: timed out after {DEFAULT_GIT_TIMEOUT_S}s") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"could not list git worktrees: {_format_process_failure(proc)}")

    matches: list[Path] = []
    current_path: Path | None = None
    current_branch: str | None = None
    for line in [*(proc.stdout or "").splitlines(), ""]:
        if not line:
            if current_path is not None and current_branch == branch:
                matches.append(current_path.resolve())
            current_path = None
            current_branch = None
        elif line.startswith("worktree "):
            current_path = Path(line.removeprefix("worktree ").strip())
        elif line.startswith("branch refs/heads/"):
            current_branch = line.removeprefix("branch refs/heads/").strip()
    return matches


def _dispatch_layout_parts(path: Path) -> tuple[str, str] | None:
    """Return ``(agent, path_component)`` for ``.worktrees/dispatch/<agent>/<task>/``."""
    try:
        rel = path.resolve().relative_to((_REPO_ROOT / ".worktrees" / "dispatch").resolve())
    except ValueError:
        return None
    if len(rel.parts) >= 2:
        return rel.parts[0], rel.parts[1]
    return None


def _task_status_candidates_for_worktree(path: Path) -> list[str]:
    """Candidate task IDs that may own a dispatch worktree path.

    Path components are *normalized* (agent prefix stripped, non-alnum flattened)
    while state files keep the original task_id with ``/`` → ``_``. Prefer an
    exact ``worktree_path`` match in batch_state; candidates are a fallback only.
    """
    parts = _dispatch_layout_parts(path)
    if parts is None:
        return []
    agent, component = parts
    candidates = [
        component,
        f"{agent}-{component}",
        f"{agent}/{component}",
        f"{agent}_{component}",
    ]
    # Preserve order, drop duplicates.
    seen: set[str] = set()
    out: list[str] = []
    for cand in candidates:
        if cand not in seen:
            seen.add(cand)
            out.append(cand)
    return out


def _task_state_for_worktree(path: Path) -> tuple[str | None, dict[str, Any] | None]:
    """Load the path-bound task record for a dispatch worktree.

    Resolution order:
    1. Exact ``worktree_path`` match in any task state (authoritative).
    2. Candidate task IDs reconstructed from the dispatch layout.

    ``None`` is meaningful to the branch-holder release path: a legacy holder
    can have no task record, but only a separate known-empty liveness probe may
    authorize its release.  Never infer a task record from a path component
    alone.
    """
    resolved = path.resolve()
    # 1) Authoritative: scan states for worktree_path match.
    try:
        state_files = list(tasks_dir().glob("*.json")) if tasks_dir().is_dir() else []
    except OSError:
        state_files = []
    for state_file in state_files:
        if state_file.name.endswith(".tmp") or ".tmp." in state_file.name:
            continue
        state = _read_state(state_file)
        if not isinstance(state, dict):
            continue
        wt = state.get("worktree_path") or state.get("cwd")
        if not wt:
            continue
        try:
            if Path(str(wt)).resolve() == resolved:
                task_id = state.get("task_id")
                return (str(task_id) if task_id is not None else None), state
        except OSError:
            continue

    # 2) Fallback candidates from path layout — only if state records an
    # exact worktree_path/cwd match. Never accept path-less legacy states
    # (CF F001 #5708): a shared path-component name must not authorize remove.
    for task_id in _task_status_candidates_for_worktree(path):
        state = _read_state(_state_path(task_id))
        if not isinstance(state, dict):
            continue
        wt = state.get("worktree_path") or state.get("cwd")
        if not wt:
            continue
        try:
            if Path(str(wt)).resolve() != resolved:
                continue
        except OSError:
            continue
        return task_id, state
    return None, None


def _task_status_for_worktree(path: Path) -> str | None:
    """Return a path-bound worktree owner's recorded status, when present."""
    _task_id, state = _task_state_for_worktree(path)
    if state is None:
        return None
    status = state.get("status")
    return str(status) if status is not None else None


def _worktree_is_clean(path: Path) -> bool:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if proc.returncode != 0:
        return False
    return not bool((proc.stdout or "").strip())


def _worktree_matches_origin_branch(path: Path, branch: str) -> bool:
    """True when HEAD and origin/<branch> point at the same commit."""
    head = _resolve_sha(path, "HEAD")
    remote = _resolve_sha(_REPO_ROOT, f"origin/{branch}")
    if not head or not remote:
        # origin may only be resolvable from the worktree after local fetch
        remote = _resolve_sha(path, f"origin/{branch}")
    return bool(head and remote and head == remote)


# Terminal statuses that mean a prior dispatch no longer needs the worktree
# mounted. Includes failure modes — a crashed review worktree should not
# permanently pin a PR branch for follow-up dispatches (#5340). The same set
# decides which task records stop claiming a worktree for removal (#8610).
_RELEASED_TASK_STATUSES = worktree_claims.RELEASED_TASK_STATUSES


def _branch_holder_activity_reason(
    path: Path,
    *,
    task_id: str | None,
    task_state: dict[str, Any] | None,
) -> str | None:
    """Return why a branch holder cannot be released while activity is possible.

    Unlike scheduled cleanup, a branch hand-off needs to support legacy
    holders whose task state has already been removed.  That is safe only when
    both of the reaper's independent liveness probes are available and empty:
    the active-dispatch API rules out an attached task and ``lsof`` rules out a
    process still using the checkout.  Probe failure is a refusal, not evidence
    of inactivity.
    """
    candidate_task_ids = [task_id] if task_id is not None else _task_status_candidates_for_worktree(path)
    if not candidate_task_ids:
        return "holder is outside the dispatch layout"

    unparseable = _bound_task_state_unparseable_reason(path)
    if unparseable is not None:
        return unparseable

    try:
        from scripts.orchestration import reap_worktrees

        active_ids = reap_worktrees._active_task_ids()
        live_cwds = reap_worktrees._live_cwd_paths(_REPO_ROOT)
    except Exception as exc:
        return f"activity probes unavailable ({type(exc).__name__})"
    if task_state is None and active_ids is None:
        return "active-task probe unavailable"
    if live_cwds is None:
        return "process-CWD activity probe unavailable"
    if active_ids is not None:
        active_task_id = next((candidate for candidate in candidate_task_ids if candidate in active_ids), None)
        if active_task_id is not None:
            return f"active dispatch task-id={active_task_id}"
    if task_state is None:
        for candidate in candidate_task_ids:
            cand_state = _read_state(_state_path(candidate))
            if isinstance(cand_state, dict):
                cand_status = cand_state.get("status")
                if cand_status not in _RELEASED_TASK_STATUSES:
                    return f"active dispatch task-id={candidate}"
                if reap_worktrees._task_pid_alive(cand_state):
                    return f"live task PID for task-id={candidate}"
    elif reap_worktrees._task_pid_alive(task_state):
        return f"live task PID for task-id={candidate_task_ids[0]}"

    worktree = path.resolve()
    for cwd in live_cwds:
        try:
            resolved_cwd = cwd.resolve()
            resolved_cwd.relative_to(worktree)
        except (OSError, ValueError):
            continue
        return f"live process cwd={cwd}"
    return None


def _stale_branch_holder_releasable(path: Path, branch: str) -> tuple[bool, str]:
    """Return (ok, reason) for auto-releasing a worktree holding ``branch`` (#5340).

    Safe only when clean and fully pushed (HEAD == origin/<branch>). A bound
    task must be terminal or already marked reaped; an absent legacy record is
    allowed only after known-empty active-task and process-CWD probes prove the
    holder is not live. Reaper reservations always win to avoid attaching a
    branch while another cleanup owns its removal.
    """
    if reaper_lifecycle.is_reap_pending(_REPO_ROOT, path):
        return False, "reaper lifecycle reservation is pending"
    if not _worktree_is_clean(path):
        return False, "dirty"
    if not _worktree_matches_origin_branch(path, branch):
        return False, "HEAD != origin/<branch>"
    unparseable = _bound_task_state_unparseable_reason(path)
    if unparseable is not None:
        return False, unparseable
    task_id, task_state = _task_state_for_worktree(path)
    activity = _branch_holder_activity_reason(
        path,
        task_id=task_id,
        task_state=task_state,
    )
    if activity is not None:
        return False, activity
    status = str(task_state.get("status")) if task_state and task_state.get("status") is not None else None
    if task_state is None:
        return True, "clean+synced; task record absent; activity probes empty"
    if status in _RELEASED_TASK_STATUSES:
        return True, f"clean+synced; task status={status}"
    return False, f"task still active or invalid status (status={status})"


_REVIEW_SERIES_RE = re.compile(r"^(?P<stem>review-.+)-r(?P<round>[1-9][0-9]*)$")


def _review_series(task_id: str) -> tuple[str, int] | None:
    """Return ``(stem, round)`` for a review task, or None for other tasks.

    ``review-gpt6-routing`` is round 0. ``review-gpt6-routing-r7`` is round 7
    of that same series. A later round replaces every earlier checkout.
    """
    name = task_id.strip().strip("/")
    if not name.startswith("review-"):
        return None
    match = _REVIEW_SERIES_RE.fullmatch(name)
    if match is None:
        return name, 0
    return match.group("stem"), int(match.group("round"))


def _dispatch_worktree_components() -> list[tuple[Path, str]]:
    """Return ``(path, task component)`` for registered dispatch worktrees."""
    try:
        proc = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    found: list[tuple[Path, str]] = []
    current: Path | None = None
    for line in [*(proc.stdout or "").splitlines(), ""]:
        if not line:
            if current is not None:
                parts = _dispatch_layout_parts(current)
                if parts is not None:
                    found.append((current, parts[1]))
            current = None
        elif line.startswith("worktree "):
            current = Path(line.removeprefix("worktree ").strip())
    return found


def _live_origin_branch_shas(cwd: Path, branches: list[str]) -> dict[str, str] | None:
    """Return live ``refs/heads/<name>`` SHAs from one batched ``ls-remote``.

    ``None`` means the lookup itself failed (git error, unreachable origin,
    timeout) and proves nothing. A branch absent from a successful mapping is
    genuinely gone from the remote; its local tracking ref is a stale cache.
    """
    if not branches:
        return {}
    patterns = sorted({f"refs/heads/{branch}" for branch in branches})
    try:
        proc = subprocess.run(
            ["git", "ls-remote", "origin", *patterns],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    live: dict[str, str] = {}
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, ref = parts
        if ref.startswith("refs/heads/"):
            live[ref.removeprefix("refs/heads/")] = sha
    return live


def _commit_is_durably_contained(cwd: Path, sha: str) -> bool:
    """True when ``sha`` is on ``origin/main`` or a live origin branch.

    A local ``refs/remotes/origin/*`` ref is a cache, not proof: the remote
    branch may already be deleted while the tracking ref still contains the
    tip. Every tracking-ref candidate is re-verified against the live remote;
    containment counts only when the live SHA equals the cached tracking SHA
    or has ``sha`` as an ancestor. Any git error, a missing remote ref, or an
    unreadable live SHA is not containment. A clean worktree is not enough:
    its commits may exist only in that checkout.
    """
    try:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", sha, "origin/main"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if ancestor.returncode == 0:
        return True
    if ancestor.returncode != 1:
        return False
    try:
        listed = subprocess.run(
            [
                "git",
                "for-each-ref",
                "--contains",
                sha,
                "--format=%(refname)%09%(objectname)",
                "refs/remotes/origin",
            ],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if listed.returncode != 0:
        return False
    candidates: list[tuple[str, str]] = []
    for line in (listed.stdout or "").splitlines():
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        ref, tracking_sha = parts
        if ref.startswith("refs/remotes/origin/"):
            candidates.append((ref.removeprefix("refs/remotes/origin/"), tracking_sha))
    live = _live_origin_branch_shas(cwd, [name for name, _ in candidates])
    if live is None:
        return False
    for name, tracking_sha in candidates:
        live_sha = live.get(name)
        if live_sha is None:
            continue
        if live_sha == tracking_sha:
            return True
        try:
            contains = subprocess.run(
                ["git", "merge-base", "--is-ancestor", sha, live_sha],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if contains.returncode == 0:
            return True
    return False


def _worktree_head_is_durably_contained(path: Path) -> bool:
    sha = _resolve_sha(path, "HEAD")
    if not sha:
        return False
    return _commit_is_durably_contained(path, sha)


def _superseded_review_releasable(path: Path) -> tuple[bool, str]:
    """A finished review checkout can go once a later round of the same series starts.

    Cleanliness and liveness are required. The checkout does not have to match
    ``origin/<branch>``: a detached earlier round no longer holds the branch,
    which is why the branch-holder release never saw it. Removal still requires
    a separate containment proof of HEAD; this predicate does not provide it.
    """
    if reaper_lifecycle.is_reap_pending(_REPO_ROOT, path):
        return False, "reaper lifecycle reservation is pending"
    if not _worktree_is_clean(path):
        return False, "dirty"
    unparseable = _bound_task_state_unparseable_reason(path)
    if unparseable is not None:
        return False, unparseable
    task_id, task_state = _task_state_for_worktree(path)
    activity = _branch_holder_activity_reason(
        path,
        task_id=task_id,
        task_state=task_state,
    )
    if activity is not None:
        return False, activity
    if task_state is None:
        return True, "clean; task record absent; activity probes empty"
    status = str(task_state.get("status") or "")
    if status in _RELEASED_TASK_STATUSES:
        return True, f"clean; task status={status}"
    return False, f"task still active or invalid status (status={status})"


def _superseded_review_release_proof(path: Path) -> tuple[bool, str]:
    """Return ``(ok, reason)`` for removing an earlier review round's checkout.

    The checkout must be releasable (:func:`_superseded_review_releasable`)
    and its HEAD durably contained in main or a remote ref.
    """
    ok, reason = _superseded_review_releasable(path)
    if not ok:
        return False, reason
    if not _worktree_head_is_durably_contained(path):
        return False, "tip not contained in main or a remote ref"
    return True, reason


def _release_superseded_review_worktrees(task_id: str, *, dry_run: bool) -> list[Path]:
    """Remove earlier rounds of this review series before the new checkout is made.

    Each removal goes through :func:`_remove_dispatch_worktree`, which runs the
    release proof while holding the earlier round's worktree lock (#8610).
    """
    series = _review_series(task_id)
    if series is None:
        return []
    stem, current_round = series
    released: list[Path] = []
    for path, component in _dispatch_worktree_components():
        earlier = _review_series(component)
        if earlier is None:
            continue
        earlier_stem, earlier_round = earlier
        if earlier_stem != stem or earlier_round >= current_round:
            continue
        if dry_run:
            ok, reason = _superseded_review_release_proof(path)
            if not ok:
                print(f"ℹ️  earlier review {path} kept ({reason})", file=sys.stderr)
                continue
            print(
                f"🌲 dry-run: would remove superseded review worktree {path} ({reason})",
                file=sys.stderr,
            )
            released.append(path)
            continue
        removal = _remove_dispatch_worktree(
            path,
            reason="superseded by a later review round",
            owner_task_id=None,
            releasable=functools.partial(_superseded_review_release_proof, path),
        )
        if removal["action"] == "skipped":
            print(f"ℹ️  earlier review {path} kept ({removal['reason']})", file=sys.stderr)
            continue
        if removal["action"] != "removed":
            print(
                f"⚠️  failed to remove superseded review worktree {path}: {removal['error']}",
                file=sys.stderr,
            )
            continue
        print(f"🌲 removed superseded review worktree {path} ({removal['reason']})", file=sys.stderr)
        # Delete only the local branch named for this review round.
        scratch_branch = removal["branch"]
        if scratch_branch is not None and scratch_branch.split("/")[-1] == component:
            _delete_local_branch(scratch_branch)
        released.append(path)
    return released


def _delete_local_branch(branch: str) -> None:
    if any(item == branch for item in _checked_out_branch_names()):
        print(f"ℹ️  kept local branch {branch}; another checkout still has it", file=sys.stderr)
        return
    sha = _resolve_sha(_REPO_ROOT, f"refs/heads/{branch}")
    if not sha or not _commit_is_durably_contained(_REPO_ROOT, sha):
        print(
            f"ℹ️  kept local branch {branch}; tip not contained in main or a remote ref",
            file=sys.stderr,
        )
        return
    try:
        proc = subprocess.run(
            ["git", "branch", "-D", branch],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(
            f"⚠️  failed to delete local branch {branch}: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return
    if proc.returncode != 0:
        print(
            f"⚠️  failed to delete local branch {branch}: {_format_process_failure(proc)}",
            file=sys.stderr,
        )
        return
    print(f"🌲 deleted superseded review branch {branch}", file=sys.stderr)


def _checked_out_branch_names() -> list[str]:
    names: list[str] = []
    try:
        proc = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return names
    for line in (proc.stdout or "").splitlines():
        if line.startswith("branch refs/heads/"):
            names.append(line.removeprefix("branch refs/heads/").strip())
    return names


def _release_stale_branch_holders(
    *,
    branch: str,
    holders: list[Path],
    dry_run: bool,
) -> list[Path]:
    """Remove releasable holders of ``branch`` so a new worktree can attach.

    Returns paths successfully released (or that would be released in dry-run).
    Non-releasable holders are left in place for the caller to refuse on. Each
    removal goes through :func:`_remove_dispatch_worktree`, which runs
    :func:`_stale_branch_holder_releasable` while holding the holder's
    worktree lock (#8610).
    """
    released: list[Path] = []
    for path in holders:
        if dry_run:
            ok, reason = _stale_branch_holder_releasable(path, branch)
            if not ok:
                print(
                    f"ℹ️  branch {branch!r} held by {path} not auto-releasable ({reason})",
                    file=sys.stderr,
                )
                continue
            print(
                f"🌲 dry-run: would release stale branch holder {path} ({reason})",
                file=sys.stderr,
            )
            released.append(path)
            continue
        # No force: if the tree went dirty after the cleanliness check
        # (dirty-TOCTOU), or a process adopted the holder as cwd after the
        # live-CWD probe (live-cwd TOCTOU — accepted residual), git refuses
        # removal and we leave the holder mounted (#5708 CF, #7242).
        removal = _remove_dispatch_worktree(
            path,
            reason=f"stale holder of {branch!r}",
            owner_task_id=None,
            releasable=functools.partial(_stale_branch_holder_releasable, path, branch),
        )
        if removal["action"] == "skipped":
            print(
                f"ℹ️  branch {branch!r} held by {path} not auto-releasable ({removal['reason']})",
                file=sys.stderr,
            )
            continue
        if removal["action"] != "removed":
            print(
                f"⚠️  failed to release stale branch holder {path}: {removal['error']}",
                file=sys.stderr,
            )
            continue
        print(
            f"🌲 released stale branch holder {path} ({removal['reason']}) so {branch!r} can attach to a new dispatch worktree",
            file=sys.stderr,
        )
        released.append(path)
    return released


def _resolve_sha(path: Path, ref: str = "HEAD") -> str | None:
    """Return the commit SHA at ``ref`` in ``path``, or None if unresolvable."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", ref],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    sha = (proc.stdout or "").strip()
    return sha or None


def _record_final_branch_head(state: dict[str, Any]) -> None:
    """Capture the current HEAD when a terminal task still owns a worktree."""
    raw_path = state.get("worktree_path")
    if isinstance(raw_path, str) and Path(raw_path).is_dir():
        state["final_branch_head_commit"] = _resolve_sha(Path(raw_path))


def _mark_crashed_task(state_path: Path, state: dict[str, Any], *, source: str) -> None:
    """Persist a zombie correction with the worktree's final branch head."""
    current, _changed = mark_dead_worker_terminal(
        state_path,
        state,
        source=source,
        terminal_status="crashed",
        allowed_statuses=("running", "spawning"),
        pid_alive=_pid_alive,
        resolve_head=_resolve_sha,
    )
    state.clear()
    state.update(_hydrate_read_only_checkout_snapshots(current))


def _heal_dead_task(state_path: Path, state: dict[str, Any], *, source: str) -> None:
    """Mark an active record ``crashed`` when the process that owns it is gone.

    A worker record's owner is its pid. A worktree-prep record (``pid: null``
    while dispatch runs ``git worktree add``) is owned by the dispatcher
    recorded in ``worktree_prep``; if the dispatcher died, no pid will ever be
    written, so it is marked ``crashed`` with reason
    ``dispatch_died_during_worktree_prep`` (#8663). An admission hold is
    owned by the dispatcher recorded in ``admission_hold`` and is marked
    ``crashed`` with reason ``dispatch_died_after_admission`` (#8717).
    """
    if state.get("status") not in ("running", "spawning"):
        return
    pid = state.get("pid")
    if pid and not _pid_alive(int(pid)):
        _mark_crashed_task(state_path, state, source=source)
    elif worktree_prep.is_orphaned_prep_record(state):
        current, _changed = mark_orphaned_worktree_prep_crashed(
            state_path,
            state,
            source=source,
            is_orphaned=worktree_prep.is_orphaned_prep_record,
        )
        state.clear()
        state.update(current)
    elif dispatch_admission.is_orphaned_admission_hold(state):
        current, _changed = mark_orphaned_admission_hold_crashed(
            state_path,
            state,
            source=source,
            is_orphaned=dispatch_admission.is_orphaned_admission_hold,
            reason=dispatch_admission.ORPHANED_HOLD_REASON,
        )
        state.clear()
        state.update(current)


# Exit code for a dispatch refused by host admission: retryable once a worker
# finishes or the host recovers, unlike exit 2 (invalid request).
_ADMISSION_REFUSED_EXIT = 3


def _evaluate_dispatch_admission(
    mode: str,
    *,
    sweep: bool,
    thresholds: dispatch_admission.Thresholds | None = None,
) -> dispatch_admission.AdmissionDecision:
    """Host admission for a ``mode`` dispatch (#8645 part A).

    With ``sweep`` every running/spawning record whose owner is gone (a dead
    worker pid, or a pid-less worktree reservation or admission hold whose
    dispatcher died) is marked ``crashed`` first by the healer ``status``,
    ``wait``, ``list`` and reconcile use, so it never holds a slot and never
    sits active until someone probes it (#8717).
    """
    return dispatch_admission.evaluate(
        mode,
        tasks_dir(),
        pid_alive=_pid_alive,
        on_dead=(lambda path, state: _heal_dead_task(path, state, source="admission")) if sweep else None,
        thresholds=thresholds,
    )


def _report_dispatch_admission(
    decision: dispatch_admission.AdmissionDecision, *, force_reason: str | None
) -> int | None:
    """Print the admission outcome; return the exit code when dispatch must stop."""
    if decision.exempt:
        return None
    if decision.admitted:
        print(f"🚦 dispatch admission: admitted — {decision.summary()}", file=sys.stderr)
        return None
    if force_reason is not None:
        print(
            f"⚠️  dispatch admission overridden by --force-admission ({force_reason!r}): {'; '.join(decision.failures)}",
            file=sys.stderr,
        )
        return None
    print(f"❌ {decision.refusal_line()}", file=sys.stderr)
    return _ADMISSION_REFUSED_EXIT


def _tracking_remote_for_current_branch(worktree: Path) -> str | None:
    """Return the configured upstream remote for the checked-out branch.

    A reused ``--cwd`` worktree can belong to a private repository whose
    canonical remote is not named ``origin``.  Its checked-out dispatch branch
    is the narrowest local source for that repository identity: unlike scanning
    every configured remote, it cannot accidentally select an unrelated mirror.
    """
    try:
        branch = _current_branch(worktree)
    except OSError:
        return None
    if not branch or branch == "HEAD":
        return None
    try:
        proc = subprocess.run(
            ["git", "config", "--get", f"branch.{branch}.remote"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    remote = (proc.stdout or "").strip()
    return remote or None


def _commit_count_refs(worktree: Path, base_ref: str) -> tuple[str, ...]:
    """Return ordered, local-only base-ref candidates for finalization.

    ``origin/<base>`` remains the canonical candidate for ordinary dispatches.
    If it is unavailable, count against the base branch on the checked-out
    branch's upstream remote before falling back to the local base.  The remote
    candidate must win because a reused checkout can have a stale local branch.
    The remote fallback is required for private/secondary remotes, where a
    pushed dispatch branch may track ``private/<task>`` and the shared checkout
    intentionally has neither ``origin/<base>`` nor a current local ``<base>``
    branch.
    """
    candidates = [base_ref]
    _remote, separator, branch = base_ref.partition("/")
    if not separator:
        branch = base_ref

    tracking_remote = _tracking_remote_for_current_branch(worktree)
    if tracking_remote and branch:
        candidates.append(f"{tracking_remote}/{branch}")
    if separator:
        candidates.append(branch)
    return tuple(dict.fromkeys(candidate for candidate in candidates if candidate))


def _count_commits_ahead(worktree: Path, base_ref: str) -> int | None:
    """Return commits on HEAD not reachable from an eligible base ref, or None.

    ``None`` means "cannot count", and a vanished worktree is exactly that: on
    2026-07-25 a dispatch whose worktree disappeared mid-run raised
    FileNotFoundError out of here, which killed the finalize path before it
    could write a terminal status and left the task reading ``running`` with a
    dead pid — invisible to every settle-loop watching it. The sibling
    ``_worktree_is_dirty`` already treated OSError as unknown; this is the same
    contract, and callers already fail closed on ``None``.
    """
    for candidate in _commit_count_refs(worktree, base_ref):
        try:
            proc = subprocess.run(
                ["git", "rev-list", "--count", f"{candidate}..HEAD"],
                cwd=worktree,
                capture_output=True,
                text=True,
                check=False,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if proc.returncode != 0:
            continue
        try:
            return int((proc.stdout or "").strip())
        except ValueError:
            return None
    return None


def _unpushed_commit_refs(worktree: Path, branch: str) -> tuple[str, ...]:
    """Return ordered remote-tracking ref candidates for unpushed-commit checks."""
    clean_branch = branch.removeprefix("refs/heads/").removeprefix("refs/remotes/")
    if clean_branch.startswith("origin/"):
        clean_branch = clean_branch.removeprefix("origin/")
    if not clean_branch:
        return ()

    candidates: list[str] = [f"{clean_branch}@{{upstream}}", "@{upstream}"]
    tracking_remote = _tracking_remote_for_current_branch(worktree)
    if tracking_remote:
        candidates.append(f"{tracking_remote}/{clean_branch}")
    candidates.append(f"origin/{clean_branch}")
    return tuple(dict.fromkeys(candidate for candidate in candidates if candidate))


def _count_unpushed_commits(worktree: Path, branch: str) -> int | None:
    """Return commits on HEAD not reachable from the branch's remote, or None.

    ``None`` means cannot count or no remote tracking ref exists. Fail closed
    on unknown or unpushed commits (#7311).
    """
    for candidate in _unpushed_commit_refs(worktree, branch):
        try:
            proc = subprocess.run(
                ["git", "rev-list", "--count", f"{candidate}..HEAD"],
                cwd=worktree,
                capture_output=True,
                text=True,
                check=False,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if proc.returncode != 0:
            continue
        try:
            return int((proc.stdout or "").strip())
        except ValueError:
            return None
    return None


def _commit_count_base_ref(worktree: Path, base_branch: str) -> str:
    """Keep an explicit available non-origin remote base for finalization."""
    explicit_ref = base_branch.removeprefix("refs/remotes/")
    if "/" in explicit_ref and _resolve_sha(worktree, explicit_ref) is not None:
        return explicit_ref
    return _origin_base_ref(base_branch)


def _origin_base_ref(base_branch: str) -> str:
    """Return the remote ref used for ahead-count checks."""
    if base_branch.startswith("origin/"):
        return base_branch
    return f"origin/{_base_branch_name(base_branch)}"


def _base_branch_name(base_branch: str) -> str:
    """Return a PR base branch name without the remote prefix.

    ``origin/main`` and ``github/main`` both name the canonical ``main`` —
    the dispatch fetch lands every base into ``refs/remotes/origin/<name>``
    regardless of which remote served it (#7522).
    """
    stripped = base_branch.removeprefix("origin/")
    return stripped.removeprefix("github/")


_GIT_ENV_DENYLIST = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_COMMON_DIR",
}


def _sanitized_git_env() -> dict[str, str]:
    """Drop repo-redirecting Git env so ``cwd=worktree`` resolves that repo."""
    return {
        key: value
        for key, value in os.environ.items()
        if key not in _GIT_ENV_DENYLIST and not key.startswith("PRE_COMMIT")
    }


def _is_virtualenv_bin_path(entry: str) -> bool:
    """Return whether a PATH entry is a conventional Python virtualenv bin."""
    path = Path(entry)
    return path.name == "bin" and path.parent.name in {".venv", "venv"}


def _pinned_worker_venv_env(source: dict[str, str]) -> dict[str, str]:
    """Pin a detached worker to this repository's venv, never an inherited one.

    A dispatch worker can run arbitrary project commands.  If its parent was
    launched from a different checkout's activated virtualenv, retaining that
    ``VIRTUAL_ENV`` or its ``bin`` directory in ``PATH`` lets ``pip`` rewrite
    that other environment's console scripts.  The worker always receives the
    canonical project venv path; its explicit ``.venv/bin/python`` spawn
    command has no fallback if that interpreter is unavailable.
    """
    venv_root = _REPO_ROOT / ".venv"
    venv_bin = venv_root / "bin"
    pinned = dict(source)
    inherited_path = source.get("PATH", "")
    inherited_venv = source.get("VIRTUAL_ENV")
    inherited_venv_bin = os.path.normpath(str(Path(inherited_venv) / "bin")) if inherited_venv else None
    path_entries = [
        entry
        for entry in inherited_path.split(os.pathsep)
        if entry and not _is_virtualenv_bin_path(entry) and os.path.normpath(entry) != inherited_venv_bin
    ]
    pinned["PATH"] = os.pathsep.join((str(venv_bin), *path_entries))
    pinned["VIRTUAL_ENV"] = str(venv_root)
    # PYTHONHOME can override the interpreter's calculated prefix and make a
    # correctly pinned venv behave like an unrelated Python installation.
    pinned.pop("PYTHONHOME", None)
    return pinned


@dataclass(frozen=True)
class AutoFinalizeResult:
    ok: bool
    commit_sha: str | None = None
    pr_url: str | None = None
    error: str | None = None
    changed_files: tuple[str, ...] = ()
    # The task's declared --owned-path values, or None when it declared none (#8991).
    owned_paths: tuple[str, ...] | None = None
    # Changed files outside the owned paths: never staged, left in the tree.
    skipped_paths: tuple[str, ...] = ()
    # Additions and deletions that could be one move across the owned-path
    # boundary (an owned side plus an opposite outside side): all skipped.
    cross_boundary_moves: tuple[str, ...] = ()


def _format_process_failure(proc: subprocess.CompletedProcess[str]) -> str:
    detail = (proc.stderr or proc.stdout or "").strip()
    if detail:
        return detail.splitlines()[-1]
    return f"exit {proc.returncode}"


def _worktree_is_dirty(worktree: Path) -> bool | None:
    try:
        status_proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if status_proc.returncode != 0:
        return None
    return bool((status_proc.stdout or "").strip())


# Top-level checkout dirs the read-only snapshot never records. Other lanes'
# dispatch worktrees live under ``.worktrees/`` (layout A): concurrent activity
# there — including writes inside a sandbox that already existed at pre-snapshot
# time — is never this task's mutation, and it false-failed cleanly-successful
# read-only dispatches (#7124). The guard diffs only what the task could own.
_READ_ONLY_SNAPSHOT_EXCLUDED_TOP_LEVEL_DIRS = frozenset({".worktrees"})


def _is_read_only_snapshot_excluded_path(path: str) -> bool:
    """Return whether a checkout-relative path is outside the snapshot scope."""
    normalized = _normalize_read_only_relpath(path)
    top_level = normalized.split("/", 1)[0]
    return top_level in _READ_ONLY_SNAPSHOT_EXCLUDED_TOP_LEVEL_DIRS


def _read_only_checkout_snapshot(cwd: Path) -> tuple[dict[str, str] | None, str | None]:
    """Capture the observable Git state of a read-only worker's checkout.

    The snapshot includes ignored files because a writeful legacy audit can
    create ignored cache entries that ordinary ``git status`` deliberately
    hides.  It is diagnostic only: this guard reports leaked paths and never
    removes them, since a pre-existing user file cannot be attributed safely.

    Paths under ``.worktrees/`` are excluded entirely (#7124): they belong to
    concurrent dispatch lanes, not to the task being guarded.
    """
    commands = (
        (
            "status",
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        ),
        (
            "ignored",
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored"],
        ),
    )
    outputs: dict[str, str] = {}
    for label, command in commands:
        try:
            proc = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return None, f"{label} snapshot could not start: {type(exc).__name__}: {exc}"
        if proc.returncode != 0:
            return None, f"{label} snapshot failed: {_format_process_failure(proc)}"
        outputs[label] = proc.stdout or ""

    entries: dict[str, str] = {}
    status_records = outputs["status"].split("\0")
    index = 0
    while index < len(status_records):
        record = status_records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4 or record[2] != " ":
            return None, "status snapshot returned an unparseable porcelain record"
        state, path = record[:2], record[3:]
        # Porcelain v1 emits the pre-rename/pre-copy path as a second NUL item.
        # Consume it even for excluded paths so the record stream stays aligned.
        rename_source: str | None = None
        if "R" in state or "C" in state:
            if index >= len(status_records) or not status_records[index]:
                return None, "status snapshot returned an incomplete rename/copy record"
            rename_source = status_records[index]
            index += 1
        # Filter the rename/copy source and destination independently
        # (#7147): ``git mv tracked.txt .worktrees/lane/tracked.txt`` must still
        # surface the tracked source deletion even though the destination is
        # out of snapshot scope.
        if not _is_read_only_snapshot_excluded_path(path):
            entries[path] = state
        if rename_source is not None and not _is_read_only_snapshot_excluded_path(rename_source):
            entries[rename_source] = f"{state}:source"
    # ``git status`` without ``--ignored`` omits ignored paths entirely. The
    # second status invocation makes those paths observable as ``!!`` while
    # retaining porcelain's tracked/untracked classification for the first
    # invocation. Do not let the second invocation overwrite real statuses.
    for record in outputs["ignored"].split("\0"):
        if len(record) < 4 or record[:2] != "!!" or record[2] != " ":
            continue
        path = record[3:]
        if not _is_read_only_snapshot_excluded_path(path):
            entries[path] = "!!"
    return entries, None


def _read_only_task_record_snapshot(
    task_id: str,
    baseline: dict[str, tuple[str, str | None]] | None = None,
) -> tuple[dict[str, tuple[str, str | None]] | None, str | None]:
    """Fingerprint results of tasks already terminal when the review starts.

    A sibling task owns its live record and may finish during a review. Only
    changes to a pre-existing terminal result are attributable here. A new
    run_nonce means ``--force-new`` replaced the hot record, not that the old
    result was edited.
    """
    own_stem = _state_path(task_id).stem
    snapshot: dict[str, tuple[str, str | None]] = {}
    try:
        paths = (
            list(tasks_dir().glob("*.result"))
            if baseline is None
            else [tasks_dir() / Path(name).name for name in baseline]
        )
    except OSError as exc:
        return None, f"task record snapshot failed: {type(exc).__name__}: {exc}"
    for path in paths:
        if path.stem == own_stem:
            continue
        state = _read_state_json(path.with_suffix(".json"))
        if baseline is None and (state is None or state.get("status") not in _TERMINAL_STATUSES):
            continue
        name = f"batch_state/tasks/{path.name}"
        nonce = state.get("run_nonce") if state else None
        if baseline is not None and nonce != baseline[name][1]:
            continue
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            # The task may have been archived or reaped during the scan.
            continue
        snapshot[name] = (digest, nonce)
    return snapshot, None


# Harness-owned Entire residue under the checkout (ADR-018 capture). These paths
# are gitignored and appear in the read-only snapshot because the guard includes
# ignored files (#4840). Treating them as task mutations false-fails healthy
# read-only dispatches at repo root and inside dispatch worktrees (#6803).
# Keep this list precise: committed ``.entire/`` config (settings, allowlist,
# private-recall) must still fail the guard when a worker edits it.
# Force-added tracked files under these prefixes are NOT exempt: exemption
# requires an ignored/untracked porcelain status at snapshot time (#6803 r2).
_READ_ONLY_RUNTIME_TELEMETRY_PREFIXES = (
    ".entire/metadata",
    ".entire/logs",
    ".entire/tmp",
    ".entire/redactors/local",
)
_READ_ONLY_RUNTIME_TELEMETRY_FILES = frozenset({".entire/settings.local.json"})
# Gitignored-by-default dirs a worker's own tooling writes (#6860). Observed
# false-fails: ``.agent/sessions/*.json``, fleet-comms sqlite ``-shm/-wal``,
# ``.pytest_cache/``, ``.pytest_breadcrumbs/``. Siblings are the same class
# (harness/session/cache residue). Membership is load-bearing (#8516 AC-02):
# an ignored ``!!`` path escapes the mutation guard ONLY through this
# classification, so task-authored leak targets like ``.cache/`` (#4840),
# root-level ``/*.py`` scratch, and ``/scratch/`` deliberately stay OUT and
# now fail the task. Deploy-target dirs (``.claude``, ``.codex``, ``.gemini``,
# ``.cursor``, ``.agents``) are not in this set: they hold tracked,
# harness-executed content, so an untracked new file there (e.g.
# ``.claude/hooks/``) must still fail a read-only task in its own worktree.
# Tracked files under these names still fail via porcelain status.
_READ_ONLY_RUNTIME_STATE_DIR_NAMES = frozenset(
    {
        ".agent",
        ".antigravitycli",
        ".deploy-state",
        ".pytest_breadcrumbs",
        ".pytest_cache",
        ".runtime",
        ".ruff_cache",
        "__pycache__",
        "batch_state",
    }
)
_READ_ONLY_RUNTIME_STATE_SUFFIXES = (
    ".db-journal",
    ".db-shm",
    ".db-wal",
    ".sqlite-journal",
    ".sqlite-shm",
    ".sqlite-wal",
    ".sqlite3-journal",
    ".sqlite3-shm",
    ".sqlite3-wal",
)
_READ_ONLY_PACKAGE_BUILD_PREFIXES = (
    "packages/v4-runtime/build",
    "packages/v4-runtime/src/learn_ukrainian_v4_runtime.egg-info",
)
_READ_ONLY_UNTRACKED_OR_IGNORED_STATUSES = frozenset({"??", "!!"})
# Dispatch sandboxes live at ``.worktrees/dispatch/<agent>/<task>/`` (layout A).
# Concurrent ``git worktree add`` under that prefix must not false-fail a
# read-only task that is scanning the shared primary checkout (#6938).
_READ_ONLY_DISPATCH_SANDBOX_PREFIX = (".worktrees", "dispatch")
_READ_ONLY_DISPATCH_SANDBOX_ROOT_PARTS = 4  # .worktrees / dispatch / agent / task


def _normalize_read_only_relpath(path: str) -> str:
    """Normalize a checkout-relative path for read-only guard matching."""
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.rstrip("/")


def _is_read_only_runtime_telemetry_path(path: str) -> bool:
    """Return whether a path is harness Entire telemetry, not a task mutation."""
    normalized = _normalize_read_only_relpath(path)
    if normalized in _READ_ONLY_RUNTIME_TELEMETRY_FILES:
        return True
    return any(
        normalized == prefix or normalized.startswith(f"{prefix}/") for prefix in _READ_ONLY_RUNTIME_TELEMETRY_PREFIXES
    )


def _is_read_only_delegate_snapshot_sidecar_path(path: str) -> bool:
    """Return whether *path* is a delegate-owned read-only snapshot sidecar."""
    normalized = _normalize_read_only_relpath(path)
    if not normalized.endswith(".json"):
        return False
    parts = normalized.split("/")
    if len(parts) < 2:
        return False
    if not parts[-2].endswith(f"{_READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX}"):
        return False
    name = parts[-1]
    if name == _READ_ONLY_SNAPSHOT_DIGEST_NAME:
        return True
    return name.startswith("read_only_checkout_") and name.endswith(".json")


def _is_read_only_runtime_state_path(path: str) -> bool:
    """Return whether a path is harness/tooling runtime state, not repo content.

    Covers Entire telemetry (#6803) plus the gitignored runtime dirs and sqlite
    sidecars that false-failed successful read-only tasks (#6860). Since #8516
    AC-02 this classification is ALSO the only way an ignored ``!!`` path
    escapes the mutation guard: task-authored ignored leaks outside it (the
    review-a3-api-ui ``/*.py`` + ``/scratch/`` scratch class; ``.cache/``
    residue from #4840/#7253) now fail the task like any other mutation.
    """
    if _is_read_only_delegate_snapshot_sidecar_path(path):
        return True
    if _is_read_only_runtime_telemetry_path(path):
        return True
    normalized = _normalize_read_only_relpath(path)
    # `pip`/setuptools can regenerate these Git-ignored package outputs while
    # a reviewer runs tests. They are build residue, not review edits (#9213).
    if _is_read_only_package_build_path(normalized):
        return True
    parts = tuple(part for part in normalized.split("/") if part and part != ".")
    if any(part in _READ_ONLY_RUNTIME_STATE_DIR_NAMES for part in parts):
        return True
    return any(normalized.endswith(suffix) for suffix in _READ_ONLY_RUNTIME_STATE_SUFFIXES)


def _is_read_only_package_build_path(path: str) -> bool:
    normalized = _normalize_read_only_relpath(path)
    return any(normalized == prefix or normalized.startswith(f"{prefix}/") for prefix in _READ_ONLY_PACKAGE_BUILD_PREFIXES)


def _read_only_dispatch_sandbox_root(path: str) -> str | None:
    """Return ``.worktrees/dispatch/<agent>/<task>`` when *path* is under one.

    Paths outside the dispatch sandbox layout (including other ``.worktrees/``
    entries) return ``None`` so the guard still sees them as ordinary mutations.
    """
    normalized = _normalize_read_only_relpath(path)
    parts = tuple(part for part in normalized.split("/") if part and part != ".")
    if len(parts) < _READ_ONLY_DISPATCH_SANDBOX_ROOT_PARTS:
        return None
    if parts[:2] != _READ_ONLY_DISPATCH_SANDBOX_PREFIX:
        return None
    return "/".join(parts[:_READ_ONLY_DISPATCH_SANDBOX_ROOT_PARTS])


def _read_only_dispatch_sandbox_roots(snapshot: dict[str, str]) -> frozenset[str]:
    """Collect dispatch sandbox roots visible in a read-only checkout snapshot."""
    return frozenset(root for path in snapshot if (root := _read_only_dispatch_sandbox_root(path)) is not None)


def _is_read_only_new_sibling_dispatch_sandbox_path(path: str, *, before_roots: frozenset[str]) -> bool:
    """Return whether *path* belongs to a sibling sandbox absent from *before*.

    Only newly appeared ``.worktrees/dispatch/<agent>/<task>/`` trees are
    exempt (#6938). A write under a sandbox root that already appeared in the
    pre-snapshot still counts as a mutation when the root checkout can see it.
    """
    root = _read_only_dispatch_sandbox_root(path)
    if root is None:
        return False
    return root not in before_roots


def _is_read_only_untracked_or_ignored_status(state: str | None) -> bool:
    """Return whether a porcelain status is ignored/untracked (not git-tracked).

    Absent entries are treated as non-tracked for the exemption gate: a clean
    tracked file is invisible in the snapshot until it mutates, and the
    post-mutation status then fails this check.
    """
    if state is None:
        return True
    return state[:2] in _READ_ONLY_UNTRACKED_OR_IGNORED_STATUSES


def _is_read_only_runtime_state_exemption(
    path: str,
    *,
    before_state: str | None,
    after_state: str | None,
) -> bool:
    """Exempt harness runtime state only when it is not tracked at snapshot time."""
    if not _is_read_only_runtime_state_path(path):
        return False
    if _is_read_only_package_build_path(path):
        # The package exemption is for Git-ignored build products only. An
        # ordinary untracked scratch file under this tree is still a leak.
        return (
            before_state in (None, "!!")
            and after_state in (None, "!!")
            and (before_state == "!!" or after_state == "!!")
        )
    return _is_read_only_untracked_or_ignored_status(before_state) and _is_read_only_untracked_or_ignored_status(
        after_state
    )


def _is_read_only_ignored_status(state: str | None) -> bool:
    """Return whether a snapshot status is Git's ignored ``!!`` marker."""
    return state is not None and state[:2] == "!!"


def _is_read_only_ignored_mutation(*, before_state: str | None, after_state: str | None) -> bool:
    """Return whether a changed path is ignored in its observable final state.

    A deleted ignored file disappears from both porcelain snapshots, so its
    pre-snapshot ``!!`` marker is also sufficient to classify that delta as an
    ignored mutation. A path that becomes ordinary untracked ``??`` remains a
    real mutation and is intentionally not classified as ignored.
    """
    if after_state is not None:
        return _is_read_only_ignored_status(after_state)
    return _is_read_only_ignored_status(before_state)


def _read_only_ignored_mutation_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Return changed ignored paths the guard deliberately tolerates as noise.

    Diagnostic companion to :func:`_read_only_mutation_paths` (#8516): an
    ignored ``!!`` status alone no longer exempts a path, so this list holds
    exactly the ignored deltas that were ALSO recognized as harness/runtime
    state — the build-noise class a read-only dispatch legitimately cannot
    own (``.pytest_cache/``, ``batch_state/``, ``.entire/`` telemetry, …).
    """
    before_roots = _read_only_dispatch_sandbox_roots(before)
    return sorted(
        path
        for path in set(before) | set(after)
        if before.get(path) != after.get(path)
        and _is_read_only_ignored_mutation(
            before_state=before.get(path),
            after_state=after.get(path),
        )
        and _is_read_only_runtime_state_exemption(
            path,
            before_state=before.get(path),
            after_state=after.get(path),
        )
        and not _is_read_only_new_sibling_dispatch_sandbox_path(path, before_roots=before_roots)
    )


def _read_only_mutation_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Return exact paths whose observable Git state changed during a review.

    A changed path is exempt only when it is recognized harness/runtime noise
    (:func:`_is_read_only_runtime_state_exemption`: gitignored tooling residue
    such as ``.pytest_cache/`` or ``batch_state/``) or a newly appeared
    sibling dispatch sandbox under ``.worktrees/dispatch/<agent>/<task>/``
    (#6938 defense in depth; since #7124 the snapshot itself already drops
    every ``.worktrees/`` path). Tracked paths under runtime prefixes
    (including force-added files) still trip the guard.

    #8516 AC-02: an ignored ``!!`` status BY ITSELF no longer exempts a path.
    The review-a3-api-ui leak showed why: the agy worker wrote its scratch
    files at the checkout root and under ``scratch/``, where ``.gitignore``
    (``/*.py``, ``/scratch/``) marked them ``!!``, and the guard filed them
    as diagnostic-only "ignored mutations" while the task settled ``done``.
    Now any other new, modified, or deleted path — tracked, untracked, or
    ignored — fails the task and is named.
    """
    before_roots = _read_only_dispatch_sandbox_roots(before)
    return sorted(
        path
        for path in set(before) | set(after)
        if before.get(path) != after.get(path)
        and not _is_read_only_runtime_state_exemption(
            path,
            before_state=before.get(path),
            after_state=after.get(path),
        )
        and not _is_read_only_new_sibling_dispatch_sandbox_path(path, before_roots=before_roots)
    )


def _auto_finalize_changed_files(worktree: Path) -> tuple[str, ...]:
    try:
        # --no-renames lists both sides of a rename, so an owned-path filter
        # never commits the new path while leaving the old one's deletion out.
        tracked = subprocess.run(
            ["git", "diff", "--no-renames", "--name-only", "-z", "HEAD", "--"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
        untracked = subprocess.run(
            ["git", "ls-files", "-z", "--others", "--exclude-standard"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ()
    if tracked.returncode != 0 or untracked.returncode != 0:
        return ()
    changed = {path for path in (*tracked.stdout.split("\0"), *untracked.stdout.split("\0")) if path}
    return tuple(sorted(changed))


def _is_disposable_auto_finalize_path(path: str) -> bool:
    """Return whether a changed path is scratch residue, not deliverable content.

    This is intentionally a narrow allowlist of known generated dependency and
    cache paths. A single other path means the auto-finalizer retains its
    existing preserve-and-publish behavior rather than guessing whether that
    content is important.
    """
    parts = tuple(part for part in path.replace("\\", "/").split("/") if part and part != ".")
    if not parts:
        return True
    if any(part in {".venv", "node_modules", "__pycache__", ".pytest_cache"} for part in parts):
        return True
    return parts[-1].endswith(".pyc")


def _auto_finalize_is_junk_only(changed_files: tuple[str, ...]) -> bool:
    """Return whether auto-finalization would publish only disposable residue."""
    return bool(changed_files) and all(_is_disposable_auto_finalize_path(path) for path in changed_files)


def _declared_owned_paths(raw: object) -> tuple[str, ...] | None:
    """The task record's ``owned_paths`` (its ``--owned-path`` values), or None."""
    if not isinstance(raw, (list, tuple)):
        return None
    paths = tuple(str(item) for item in raw if isinstance(item, str) and item.strip())
    return paths or None


def _owned_path_errors(values: Sequence[str] | None) -> list[str]:
    """``--owned-path`` values that could never own a file; dispatch refuses them."""
    try:
        from scripts.guardrails.delegate_ownership import owned_path_matcher
    except ImportError:  # pragma: no cover - flat script path
        from guardrails.delegate_ownership import owned_path_matcher  # type: ignore

    return [value for value in values or () if owned_path_matcher(value) is None]


def _path_is_owned(path: str, owned_paths: Sequence[str]) -> bool:
    """Whether a repo-relative changed ``path`` falls under a declared owned path (:func:`path_is_owned`)."""
    try:
        from scripts.guardrails.delegate_ownership import path_is_owned
    except ImportError:  # pragma: no cover - flat script path
        from guardrails.delegate_ownership import path_is_owned  # type: ignore

    return path_is_owned(path, owned_paths)


def _worktree_diff_output(worktree: Path, diff_args: Sequence[str], *, git_options: Sequence[str] = ()) -> str | None:
    """``git diff <diff_args>`` as if every change, untracked files included, were committed; None when unknown.

    Untracked files are marked intent-to-add in a throwaway copy of the index
    (no file content is written to the object store) so they show up as
    additions; the real index is never touched.
    """
    env = _sanitized_git_env()
    try:
        index_proc = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-path", "index"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
        if index_proc.returncode != 0:
            return None
        with tempfile.TemporaryDirectory(prefix="lu-finalize-index-") as scratch:
            scratch_index = Path(scratch) / "index"
            real_index = Path(index_proc.stdout.strip())
            if real_index.is_file():
                shutil.copyfile(real_index, scratch_index)
            scratch_env = {**env, "GIT_INDEX_FILE": str(scratch_index)}
            add_proc = subprocess.run(
                ["git", "add", "-A", "--intent-to-add"],
                cwd=worktree,
                capture_output=True,
                text=True,
                check=False,
                env=scratch_env,
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
            if add_proc.returncode != 0:
                return None
            diff_proc = subprocess.run(
                ["git", *git_options, "diff", *diff_args],
                cwd=worktree,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                env=scratch_env,
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if diff_proc.returncode != 0:
        return None
    return diff_proc.stdout


def _auto_finalize_additions_deletions(worktree: Path) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    """Files added and deleted relative to ``HEAD`` if every change were committed; None when unknown.

    Renames are not detected: git pairs a move only above a similarity
    threshold, so a caller that must not split a move treats every deletion
    as a possible source of every addition.
    """
    output = _worktree_diff_output(worktree, ["--no-renames", "--name-status", "-z", "HEAD", "--"])
    if output is None:
        return None
    fields = output.split("\0")
    added: list[str] = []
    deleted: list[str] = []
    for index in range(0, len(fields) - 1, 2):
        status, path = fields[index], fields[index + 1]
        if not status or not path:
            break
        if status == "A":
            added.append(path)
        elif status == "D":
            deleted.append(path)
    return tuple(added), tuple(deleted)


def _kimi_worker_refusal(
    task_id: str,
    *,
    agent: str,
    model: str | None,
    mode: str,
    cwd: Path,
    review: bool,
) -> str | None:
    """The worker-side Kimi gate; installs the worktree boundary when it admits.

    A Kimi seat is refused unless its mode and review flags are admitted (read
    first, from the argv alone), the task's owned paths pass admission read in
    ``cwd`` — the tree the worker runs in — and in the commit checked out
    there, and ``cwd`` is the task's worktree, where the boundary (hooks and
    push block, ``kimi_boundary``) must install. For any other seat a boundary
    left in ``cwd`` by an earlier Kimi run is taken down. Writes nothing but
    that worktree's git config and hooks directory.
    """
    from scripts.agent_runtime import kimi_boundary
    from scripts.agent_runtime.kimi_admission import (
        ADMITTED_MODE,
        KimiAdmissionRefused,
        format_refusal,
        is_kimi_seat,
        refuse_kimi_if_disallowed,
    )

    boundary_errors = (kimi_boundary.BoundaryError, OSError, subprocess.SubprocessError)
    if not is_kimi_seat(agent, model=model):
        if mode in _WRITE_CAPABLE_MODES and kimi_boundary.is_installed(cwd):
            try:
                kimi_boundary.remove(cwd, env=_sanitized_git_env())
            except boundary_errors as exc:
                return f"the Kimi worktree boundary left in {cwd} could not be removed: {exc}"
        return None
    try:
        if mode != ADMITTED_MODE or review:
            # Refused by mode or review alone: no need to read the task record (or create its directory).
            refuse_kimi_if_disallowed((agent,), (model,), mode=mode, review=review)
        # Read-only: a refused worker must leave no task directory or file behind.
        launch = _read_state_json(_state_path_no_create(task_id)) or {}
        owned = _declared_owned_paths(launch.get("owned_paths")) or ()
        refuse_kimi_if_disallowed(
            (agent,),
            (model,),
            mode=mode,
            review=review,
            paths=owned,
            repo_root=_REPO_ROOT,
            trees=lambda: _kimi_worktree_trees(cwd),
        )
    except KimiAdmissionRefused as exc:
        return str(exc)
    worktree = launch.get("worktree_path")
    if not worktree or Path(worktree).resolve() != cwd.resolve():
        return format_refusal(agent, [f"workspace-write outside the task's dispatch worktree (cwd {str(cwd)!r})"])
    base_ref = _commit_count_base_ref(cwd, str(launch.get("worktree_base") or "main"))
    try:
        kimi_boundary.install(cwd, agent=agent, base_ref=base_ref, owned_paths=owned, env=_sanitized_git_env())
    except boundary_errors as exc:
        return format_refusal(agent, [f"the worktree boundary could not be installed ({exc})"])
    return None


def _kimi_diff_refusal(worktree: Path, base_ref: str, agent: str) -> str | None:
    """The refusal when a Kimi worker's changed files are not plain UTF-8 text or hold Cyrillic text; None otherwise.

    The changes run from the merge base with ``base_ref`` to the working tree,
    so they cover the worker's own commits and its uncommitted and untracked
    files. Each changed path's post-image is read in full, so git's binary
    classification cannot hide text. Fails closed: changes that cannot be
    read are a refusal.
    """
    from scripts.agent_runtime import kimi_boundary
    from scripts.agent_runtime.kimi_admission import KimiAdmissionRefused, format_refusal, refuse_kimi_changes

    unreadable = format_refusal(agent, ["the finalized changes could not be read for Ukrainian content"])
    try:
        base_proc = subprocess.run(
            ["git", "merge-base", base_ref, "HEAD"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return unreadable
    merge_base = (base_proc.stdout or "").strip()
    if base_proc.returncode != 0 or not merge_base:
        return unreadable
    name_status = _worktree_diff_output(worktree, ["--name-status", "-z", "--no-renames", merge_base, "--"])
    if name_status is None:
        return unreadable
    try:
        changes = kimi_boundary.changes(
            worktree, kimi_boundary.parse_name_status(name_status), after=None, env=_sanitized_git_env()
        )
        refuse_kimi_changes(agent, changes)
    except KimiAdmissionRefused as exc:
        return str(exc)
    except (OSError, subprocess.SubprocessError):
        return unreadable
    return None


def _cross_boundary_moves(added: Sequence[str], deleted: Sequence[str], owned: Sequence[str]) -> set[str]:
    """Additions and deletions that could be one move across the owned-path boundary.

    Every deletion is a possible source of every addition, so an owned
    addition is paired with any outside deletion and an owned deletion with
    any outside addition; both sides of each pairing are returned.
    """
    moves: set[str] = set()
    for sources, targets in ((deleted, added), (added, deleted)):
        outside = [path for path in sources if not _path_is_owned(path, owned)]
        inside = [path for path in targets if _path_is_owned(path, owned)]
        if outside and inside:
            moves.update(outside, inside)
    return moves


def _current_branch(worktree: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    branch = (proc.stdout or "").strip()
    return branch or None


def _x_agent_task_id(agent: str, task_id: str) -> str:
    normalized = _normalize_task_id(agent, task_id)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized).strip(".-")
    return safe or "task"


def _x_agent_trailer(agent: str, task_id: str) -> str:
    return f"X-Agent: {agent}/{_x_agent_task_id(agent, task_id)}"


def _build_worker_env(
    *,
    task_id: str,
    dispatch_agent: str,
    attribution: Any | None = None,
    run_nonce: str = "",
    runtime_tmp_root: Path | str | None = None,
    runtime_tmp_namespace_root: Path | str | None = None,
    worktree_path: Path | None = None,
    allow_merge: bool = False,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Construct the execution environment for a dispatched worker process."""
    source = dict(os.environ if base_env is None else base_env)
    worker_env = _pinned_worker_venv_env(source)
    if attribution is not None:
        worker_env["LU_RUNTIME_INITIATOR"] = getattr(attribution, "initiator", str(attribution))
        worker_env["LU_RUNTIME_INITIATOR_SOURCE"] = getattr(attribution, "source", "")
    if run_nonce:
        worker_env["LU_RUNTIME_RUN_NONCE"] = run_nonce
    # Explicit dispatch-worker identity (#7827): the SessionStart gate uses
    # this marker to skip the per-agent thread lease, which belongs to the
    # orchestrator of the agent family, never to a headless worker. Both
    # names are allowlisted in agent_runtime/env_sanitize.py (name and
    # value lists — a task id containing "sk-" must survive the secret
    # redactor), so the marker reaches the harness CLI's SessionStart hook.
    # The marker is the primary signal: a read-only dispatch without
    # --worktree runs from the primary checkout, so the
    # .worktrees/dispatch/<agent>/<task>/ path is only the fallback.
    worker_env["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] = task_id
    worker_env["LEARN_UKRAINIAN_DISPATCH_AGENT"] = dispatch_agent
    worker_env["LU_X_AGENT_TRAILER"] = _x_agent_trailer(dispatch_agent, task_id)
    # #8645 part B: CI's `--override-ini addopts=-v` drops the pyproject
    # `-p ci.pytest_dispatch_cap`. Load it from the environment instead.
    _dispatch_cap_plugin = "ci.pytest_dispatch_cap"
    _pytest_plugins = [part.strip() for part in worker_env.get("PYTEST_PLUGINS", "").split(",") if part.strip()]
    if _dispatch_cap_plugin not in _pytest_plugins:
        _pytest_plugins.append(_dispatch_cap_plugin)
    worker_env["PYTEST_PLUGINS"] = ",".join(_pytest_plugins)
    # #8795: "ci.pytest_dispatch_cap" only resolves via pyproject.toml's
    # `pythonpath = ["scripts"]`, which is rootdir-relative and inactive for a
    # pytest process started elsewhere (e.g. a test's own `pytester` subprocess
    # in a temp dir). PYTHONPATH is an interpreter-level env var, so it makes
    # the import resolve regardless of that nested pytest's rootdir.
    _worker_scripts_dir = str((worktree_path if worktree_path is not None else _REPO_ROOT) / "scripts")
    _worker_pythonpath = [part for part in worker_env.get("PYTHONPATH", "").split(os.pathsep) if part]
    if _worker_scripts_dir not in _worker_pythonpath:
        worker_env["PYTHONPATH"] = os.pathsep.join([_worker_scripts_dir, *_worker_pythonpath])
    _inject_gh_token_for_agent(worker_env, dispatch_agent)
    _scrub_unusable_gh_config_dir(worker_env)
    worker_env["AGENT_NO_TELEMETRY_FOOTER"] = "1"
    if runtime_tmp_root is not None:
        worker_env["TMPDIR"] = str(runtime_tmp_root)
        worker_env["LU_RUNTIME_TMP_ROOT"] = str(runtime_tmp_root)
    if runtime_tmp_namespace_root is not None:
        worker_env["LU_RUNTIME_TMP_BASE_ROOT"] = str(Path(runtime_tmp_namespace_root).parent)
    if worktree_path is not None:
        _apply_worktree_git_ceiling(worker_env, worktree_path)
    if allow_merge:
        worker_env.pop("AGENT_NO_MERGE", None)
        worker_env["AGENT_ALLOW_MERGE"] = "1"
    else:
        worker_env["AGENT_NO_MERGE"] = "1"
        worker_env.pop("AGENT_ALLOW_MERGE", None)
    return worker_env


def _push_auto_finalize_branch(worktree: Path, branch: str) -> None:
    try:
        proc = subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_NETWORK_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git push timed out after {DEFAULT_NETWORK_GIT_TIMEOUT_S}s") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"git push failed: {_format_process_failure(proc)}")


def _create_auto_finalize_pr(
    worktree: Path,
    *,
    branch: str,
    base_branch: str,
    title: str,
    body: str,
) -> str | None:
    try:
        proc = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--draft",
                "--base",
                base_branch,
                "--head",
                branch,
                "--title",
                title,
                "--body",
                body,
            ],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GH_CLI_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"gh pr create timed out after {DEFAULT_GH_CLI_TIMEOUT_S}s") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"gh pr create failed: {_format_process_failure(proc)}")
    lines = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
    return lines[-1] if lines else None


def _auto_finalize_dirty_worktree(
    *,
    worktree: Path,
    task_id: str,
    agent: str,
    branch: str | None,
    base_branch: str,
    open_pr: bool = False,
    owned_paths: object = None,
) -> AutoFinalizeResult:
    """Stage, commit, and push the owned part of a cleanly exited dirty dispatch.

    ``owned_paths`` is the task record's ``owned_paths`` list, written at
    dispatch from the task's explicit ``--owned-path`` values (#8991). Only
    changed files under them are staged and committed; the rest stay
    uncommitted in the tree and come back as ``skipped_paths``. A move across
    the owned-path boundary is never split, whatever git's rename similarity
    says: when any file outside the owned paths was deleted, no owned
    addition is committed, and when any outside file was added, no owned
    deletion is. Those paths are listed in ``cross_boundary_moves``.
    A task that declared no owned paths gets no commit at all
    (``no_owned_paths_declared``).
    """
    owned = _declared_owned_paths(owned_paths)
    all_changed = _auto_finalize_changed_files(worktree)
    changed_files: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    moves: tuple[str, ...] = ()

    def _result(**fields: Any) -> AutoFinalizeResult:
        return AutoFinalizeResult(owned_paths=owned, skipped_paths=skipped, cross_boundary_moves=moves, **fields)

    try:
        worktree_proc = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return _result(
            ok=False,
            error="not a git worktree",
            changed_files=changed_files,
        )
    if worktree_proc.returncode != 0 or (worktree_proc.stdout or "").strip() != "true":
        return _result(
            ok=False,
            error="not a git worktree",
            changed_files=changed_files,
        )

    if not all_changed:
        return _result(ok=False, error="clean-tree")
    if _auto_finalize_is_junk_only(all_changed):
        return _result(
            ok=False,
            error=_NO_DELIVERABLE_JUNK_ONLY_WORKTREE_REASON,
            changed_files=all_changed,
        )
    if owned is None:
        skipped = all_changed
        return _result(ok=False, error=_AUTO_FINALIZE_NO_OWNED_PATHS_REASON)
    added_deleted = _auto_finalize_additions_deletions(worktree)
    if added_deleted is None:
        return _result(ok=False, error="move detection failed; nothing committed")
    moves = tuple(sorted(_cross_boundary_moves(*added_deleted, owned)))
    changed_files = tuple(path for path in all_changed if path not in moves and _path_is_owned(path, owned))
    skipped = tuple(path for path in all_changed if path not in changed_files)
    if not changed_files or _auto_finalize_is_junk_only(changed_files):
        # Real work exists only outside the declared scope: a human decides.
        return _result(ok=False, error=_AUTO_FINALIZE_NOTHING_OWNED_REASON, changed_files=changed_files)

    resolved_branch = branch or _current_branch(worktree)
    if not resolved_branch or resolved_branch in {"HEAD", "main", "master"}:
        return _result(
            ok=False,
            error=f"unsafe or unresolved branch {resolved_branch!r}",
            changed_files=changed_files,
        )

    safe_task = _x_agent_task_id(agent, task_id)
    subject = f"chore(dispatch): finalize {agent} task {safe_task}"
    body = (
        "Auto-finalized a dirty delegate worktree after the agent exited "
        "with returncode 0 but made no commits.\n\n"
        f"Delegate task: {task_id}\n"
        f"Agent: {agent}"
    )

    # git reads the exact file list from stdin as literal pathspecs; ``commit
    # --only`` then leaves anything the worker had already staged outside that
    # list out of the commit.
    scoped_input = "\0".join(changed_files)
    scoped_args = ["--pathspec-from-file=-", "--pathspec-file-nul"]
    git_prefix = ["git", "--literal-pathspecs"]
    commit_sha: str | None = None
    try:
        add_proc = subprocess.run(
            [*git_prefix, "add", "-A", *scoped_args],
            cwd=worktree,
            input=scoped_input,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
        if add_proc.returncode != 0:
            return _result(
                ok=False,
                error=f"git add failed: {_format_process_failure(add_proc)}",
                changed_files=changed_files,
            )

        commit_proc = subprocess.run(
            [
                *git_prefix,
                "commit",
                "--only",
                *scoped_args,
                "-m",
                subject,
                "-m",
                body,
                "--trailer",
                _x_agent_trailer(agent, task_id),
            ],
            cwd=worktree,
            input=scoped_input,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
        if commit_proc.returncode != 0:
            with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                subprocess.run(
                    [*git_prefix, "restore", "--staged", *scoped_args],
                    cwd=worktree,
                    input=scoped_input,
                    capture_output=True,
                    text=True,
                    check=False,
                    env=_sanitized_git_env(),
                    timeout=DEFAULT_GIT_TIMEOUT_S,
                )
            return _result(
                ok=False,
                error=f"git commit failed: {_format_process_failure(commit_proc)}",
                changed_files=changed_files,
            )

        commit_sha = _resolve_sha(worktree)
        _push_auto_finalize_branch(worktree, resolved_branch)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        error = str(exc)
        if commit_sha is not None:
            try:
                reset_proc = subprocess.run(
                    ["git", "reset", "--soft", "HEAD~1"],
                    cwd=worktree,
                    capture_output=True,
                    text=True,
                    check=False,
                    env=_sanitized_git_env(),
                    timeout=DEFAULT_GIT_TIMEOUT_S,
                )
            except (OSError, subprocess.TimeoutExpired) as reset_exc:
                error = f"{error}; git reset failed: {reset_exc}"
            else:
                if reset_proc.returncode != 0:
                    error = f"{error}; git reset failed: {_format_process_failure(reset_proc)}"
                else:
                    commit_sha = None
        return _result(
            ok=False,
            commit_sha=commit_sha,
            error=error,
            changed_files=changed_files,
        )

    pr_url = None
    if open_pr:
        try:
            pr_url = _create_auto_finalize_pr(
                worktree,
                branch=resolved_branch,
                base_branch=_base_branch_name(base_branch),
                title=subject,
                body=(
                    f"Auto-finalized delegate task `{task_id}` for `{agent}`.\n\n"
                    "The agent exited with `returncode=0`, left a dirty worktree, "
                    "and had made zero commits, so delegate.py staged and pushed the work."
                ),
            )
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            # The commit is already pushed. Never soft-reset it after a PR error.
            return _result(ok=False, commit_sha=commit_sha, error=str(exc), changed_files=changed_files)

    return _result(
        ok=True,
        commit_sha=commit_sha,
        pr_url=pr_url,
        changed_files=changed_files,
    )


_RESCUE_TERMINAL_STATUSES = frozenset({"crashed", "timeout", "failed", "no_deliverable", "needs_finalize"})
_RESCUE_MAX_FILE_BYTES = 5 * 1024 * 1024


def _rescue_git(worktree: Path, *args: str, network: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
        env=_sanitized_git_env(),
        timeout=DEFAULT_NETWORK_GIT_TIMEOUT_S if network else DEFAULT_GIT_TIMEOUT_S,
    )


def _rescue_remote_head(worktree: Path, branch: str) -> str | None:
    proc = _rescue_git(worktree, "ls-remote", "--heads", "origin", branch, network=True)
    if proc.returncode != 0:
        raise RuntimeError("rescue remote proof unavailable")
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        return None
    if len(lines) != 1 or lines[0].split("\t")[-1] != f"refs/heads/{branch}":
        raise RuntimeError("rescue remote proof ambiguous")
    return lines[0].split("\t", 1)[0]


def _clean_rescue_junk(worktree: Path, changed: tuple[str, ...]) -> bool:
    """Remove only the already classified disposable changes."""
    index = _rescue_git(worktree, "ls-files", "-z", "--", *changed)
    head = _rescue_git(worktree, "ls-tree", "-r", "-z", "--name-only", "HEAD", "--", *changed)
    if index.returncode != 0 or head.returncode != 0:
        return False
    indexed_paths = set(index.stdout.split("\0"))
    head_paths = set(head.stdout.split("\0"))
    indexed = tuple(path for path in changed if path in indexed_paths)
    restore = tuple(path for path in changed if path in head_paths)
    remove = tuple(path for path in changed if path not in head_paths)
    if indexed and _rescue_git(worktree, "restore", "--staged", "--", *indexed).returncode != 0:
        return False
    if restore and _rescue_git(worktree, "restore", "--source=HEAD", "--worktree", "--", *restore).returncode != 0:
        return False
    if remove and _rescue_git(worktree, "clean", "-fd", "--", *remove).returncode != 0:
        return False
    return _worktree_is_dirty(worktree) is False


def _rescue_task(state_path: Path, *, apply: bool) -> dict[str, Any]:
    """Preserve one terminal task on origin; never remove its worktree here."""
    state = _read_state(state_path)
    task_id = state.get("task_id") if state else None
    row: dict[str, Any] = {"task_id": task_id, "action": "skipped"}
    if not state or state.get("status") not in _RESCUE_TERMINAL_STATUSES:
        row["reason"] = "task is not terminal non-success"
        return row
    raw_worktree = state.get("worktree_path")
    if not isinstance(raw_worktree, str):
        row["reason"] = "no recorded worktree"
        return row
    worktree = Path(raw_worktree).resolve()
    dispatch_root = (_REPO_ROOT / ".worktrees" / "dispatch").resolve()
    if not worktree.is_relative_to(dispatch_root) or _resolve_verified_worktree_path(worktree) != worktree:
        row["reason"] = "not a registered dispatch worktree"
        return row
    if state.get("worktree_reused") is not False:
        row["reason"] = "worktree ownership unknown or reused"
        return row
    lease = state.get("lease")
    if (isinstance(lease, dict) and lease.get("state") == "active") or state.get("lease_state") == "active":
        row["reason"] = "task lease active"
        return row
    try:
        from scripts.orchestration import reap_worktrees

        with worktree_lock(worktree) if apply else contextlib.nullcontext():
            current = _read_state(state_path)
            if current != state:
                row["reason"] = "task state changed"
                return row
            if reap_worktrees._task_pid_alive(state):
                row["reason"] = "task process alive"
                return row
            active_ids = reap_worktrees._active_task_ids()
            live_cwds = reap_worktrees._live_cwd_paths(_REPO_ROOT)
            if active_ids is None or live_cwds is None:
                row["reason"] = "activity probe unavailable"
                return row
            if task_id in active_ids or any(cwd == worktree or cwd.is_relative_to(worktree) for cwd in live_cwds):
                row["reason"] = "worktree active"
                return row
            current_branch = _current_branch(worktree)
            recorded_branch = state.get("worktree_branch")
            branch = f"rescue/{_x_agent_task_id(str(state.get('agent') or 'agent'), str(task_id))}"
            if current_branch not in {recorded_branch, branch}:
                row["reason"] = "worktree branch differs from task record"
                return row
            dirty = _worktree_is_dirty(worktree)
            if dirty is None:
                row["reason"] = "git status unavailable"
                return row
            changed = _auto_finalize_changed_files(worktree) if dirty else ()
            if dirty and not changed:
                row["reason"] = "changed files unavailable"
                return row
            large = [
                name
                for name in changed
                if (worktree / name).is_file() and (worktree / name).stat().st_size > _RESCUE_MAX_FILE_BYTES
            ]
            if large:
                row["reason"] = "files exceed 5 MB"
                row["large_files"] = large
                return row
            cleaned_junk = False
            if _auto_finalize_is_junk_only(changed):
                if not apply:
                    row["action"] = "candidate"
                    row["reason"] = "clean disposable residue"
                    return row
                if not _clean_rescue_junk(worktree, changed):
                    row["action"] = "error"
                    row["reason"] = "could not clean disposable residue"
                    return row
                cleaned_junk = True
                dirty = False
                changed = ()
            head = _resolve_sha(worktree)
            if head is None:
                row["reason"] = "HEAD unavailable"
                return row
            if not dirty and state.get("rescue_status") == "rescued" and state.get("rescue_head_commit") == head:
                row["reason"] = "already rescued at HEAD"
                return row
            if not dirty:
                ahead = _count_commits_ahead(
                    worktree, _commit_count_base_ref(worktree, str(state.get("worktree_base") or "main"))
                )
                if ahead is None:
                    row["reason"] = "ahead count unavailable"
                    return row
                if ahead == 0 or _count_unpushed_commits(worktree, str(state.get("worktree_branch") or "")) == 0:
                    row["action"] = "cleaned" if cleaned_junk else "skipped"
                    row["reason"] = "disposable residue removed" if cleaned_junk else "no provable unpushed work"
                    return row
            existing_remote = _rescue_remote_head(worktree, branch)
            if existing_remote is not None and existing_remote != head:
                row["reason"] = "rescue remote branch already exists at another head"
                return row
            row.update({"action": "candidate", "rescue_ref": branch, "head": head})
            if not apply:
                return row
            if dirty:
                if current_branch != branch:
                    proc = _rescue_git(worktree, "switch", "-c", branch)
                    if proc.returncode != 0:
                        raise RuntimeError("cannot create rescue branch")
                proc = _rescue_git(worktree, "add", "-A")
                if proc.returncode != 0:
                    raise RuntimeError("cannot stage rescue work")
                proc = _rescue_git(
                    worktree,
                    "commit",
                    "-m",
                    f"chore(dispatch): rescue {task_id}",
                    "--trailer",
                    f"X-Agent: {state.get('agent') or 'agent'}/{task_id}",
                )
                if proc.returncode != 0:
                    raise RuntimeError("cannot commit rescue work")
                head = _resolve_sha(worktree)
                if head is None:
                    raise RuntimeError("rescue commit HEAD unavailable")
            proc = _rescue_git(worktree, "push", "origin", f"HEAD:refs/heads/{branch}", network=True)
            if proc.returncode != 0:
                raise RuntimeError("cannot push rescue branch")
            if _rescue_remote_head(worktree, branch) != head:
                raise RuntimeError("rescue remote verification failed")
            proc = _rescue_git(
                worktree,
                "fetch",
                "origin",
                f"refs/heads/{branch}:refs/remotes/origin/{branch}",
                network=True,
            )
            if proc.returncode != 0 or _resolve_sha(worktree, f"refs/remotes/origin/{branch}") != head:
                raise RuntimeError("rescue tracking ref verification failed")
            state.update({"rescue_ref": branch, "rescue_head_commit": head, "rescue_status": "rescued"})
            _write_state_atomic(state_path, state)
            row.update({"action": "rescued", "head": head})
            return row
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        row.update({"action": "error", "reason": str(exc)})
        return row


def cmd_rescue(args: argparse.Namespace) -> int:
    """Show or preserve terminal dispatch work before the P0 reaper runs."""
    if args.all_stale:
        try:
            amount = str(args.older_than).removesuffix("h")
            min_age_hours = float(amount)
            if min_age_hours < 0:
                raise ValueError
        except (TypeError, ValueError):
            print("--older-than must be a non-negative hour duration, such as 6h", file=sys.stderr)
            return 2
        paths = sorted(tasks_dir().glob("*.json")) if tasks_dir().is_dir() else []
    elif args.task_id:
        paths = [_state_path(args.task_id)]
        min_age_hours = 0
    else:
        print("provide a task ID or --all-stale", file=sys.stderr)
        return 2

    rows: list[dict[str, Any]] = []
    now = datetime.now(UTC)
    for path in paths:
        state = _read_state(path)
        if args.all_stale:
            if state is None:
                rows.append({"task_id": path.stem, "action": "skipped", "reason": "unreadable task state"})
                continue
            if state.get("status") not in _RESCUE_TERMINAL_STATUSES:
                continue
            try:
                finished = datetime.fromisoformat(str(state["finished_at"]).replace("Z", "+00:00"))
                age_hours = (now - finished).total_seconds() / 3600
            except (KeyError, TypeError, ValueError, OverflowError):
                rows.append(
                    {
                        "task_id": state.get("task_id"),
                        "action": "skipped",
                        "reason": "no finished_at" if not state.get("finished_at") else "invalid finished_at",
                    }
                )
                continue
            if age_hours < min_age_hours:
                continue
        rows.append(_rescue_task(path, apply=bool(args.apply or not args.all_stale)))
    summary = {
        action: sum(row["action"] == action for row in rows)
        for action in ("candidate", "rescued", "cleaned", "skipped", "error")
    }
    print(
        json.dumps(
            {"mode": "apply" if args.apply or not args.all_stale else "dry_run", "summary": summary, "tasks": rows}
        )
    )
    return 1 if summary["error"] else 0


def _branch_ref_exists(repo_root: Path, branch: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def _should_reap_settled_worktree(
    *,
    mode: str,
    keep_worktree: bool,
    final_status: str,
    returncode: int | None,
    dirty_on_exit: bool | None,
) -> bool:
    """Return whether settle may remove this dispatch checkout.

    ``ask-* --review`` reaches this path through ``delegate.py dispatch
    --mode read-only --worktree``. The sealed snapshot helper tears its own
    temp root down and is not a second worktree owner.

    Dirty or unknown trees stay mounted. ``--keep-worktree`` stays mounted.
    Read-only reaps on any terminal status. ``workspace-write`` uses the same
    rule as ``danger``: status ``done`` and return code 0.
    """
    if keep_worktree or dirty_on_exit is not False:
        return False
    if mode == "read-only":
        return final_status in _READ_ONLY_SETTLE_REAP_STATUSES
    if mode in _WRITE_CAPABLE_MODES:
        return final_status == "done" and returncode == 0
    return False


def _settled_worktree_ownership(worktree: Path, *, created_by_this_dispatch: bool | None) -> tuple[bool, str]:
    """Return settle's ``(ok, reason)`` ownership proof for removing ``worktree``.

    Settle removes only a checkout this dispatch created. An attached or
    reused checkout belongs to another task, and that owner reaps it (#8610).
    Ownership that cannot be established fails closed; the default reaper
    does not collect that legacy case, so the refusal names the explicit
    operator cleanup.
    """
    if created_by_this_dispatch is None:
        return False, (
            "worktree ownership unknown; refusing worktree removal; operator cleanup: "
            "scripts/orchestration/reap_worktrees.py --terminal-dispatches "
            f"--worktree {worktree} --apply"
        )
    if not created_by_this_dispatch:
        return False, "reused worktree; owner reaps"
    return True, ""


# The claim scan's byte pre-filter; see scripts/orchestration/worktree_claims.py.
_worktree_claim_needles = worktree_claims.worktree_claim_needles
_record_may_claim_worktree = worktree_claims.record_may_claim_worktree


def _remove_dispatch_worktree(
    worktree: Path,
    *,
    reason: str,
    owner_task_id: str | None,
    releasable: Callable[[], tuple[bool, str]],
    force: bool = False,
    lock_timeout_s: float | None = None,
) -> dict[str, Any]:
    """Remove one dispatch worktree. Every removal in this module comes here (#8610).

    An adapter over
    :func:`scripts.orchestration.worktree_claims.remove_unclaimed_worktree`,
    the chokepoint every remover in the repository shares, bound to this
    repository's task records and lock home. Holding :func:`worktree_lock`,
    it runs ``releasable``, the caller's ownership proof returning
    ``(ok, detail)``; for ``force``, a clean-tree proof; the active-claim
    scan, which exempts only ``owner_task_id``'s own record; and only then
    the removal. ``reason`` is the caller's purpose, recorded on success.
    Returns a ``worktree_reap`` record whose ``action`` is ``removed``,
    ``skipped``, or ``error``; this never raises.
    """
    removal = worktree_claims.remove_unclaimed_worktree(
        worktree,
        # A ``--repo`` sibling worktree is git-operated in its own repository,
        # while its records and locks stay on this control plane (#8624).
        repo_root=worktree_claims.owning_repo_root(worktree, default=_REPO_ROOT),
        control_root=_REPO_ROOT,
        reason=reason,
        owner_task_id=owner_task_id,
        releasable=releasable,
        force=force,
        tasks_dir=tasks_dir(),
        lock_dir=_worktree_lock_dir(),
        lock_timeout_s=_WORKTREE_LOCK_DEFAULT_TIMEOUT_S if lock_timeout_s is None else lock_timeout_s,
    )
    return {**removal.as_record(), "pr": None}


def _stop_worker_background_jobs(task_record: Mapping[str, Any], *, task_id: str) -> tuple[bool, str]:
    """Stop a worker's possibly live background jobs; ``(ok, refusal detail)``.

    The scope comes from the task record only when it matches the task's
    launch identity (:func:`worker_leftovers.scope_from_record`).
    """
    scope, refusal = worker_leftovers.scope_from_record(task_record, task_id=task_id)
    if refusal is not None:
        return (
            False,
            f"background jobs may be alive but the recorded scope is refused ({refusal}); refusing worktree removal",
        )
    if scope is None:
        return True, ""
    try:
        stopped = worker_leftovers.stop_leftovers(scope, reader=_worker_process_reader())
    except Exception as exc:
        return False, f"background jobs could not be stopped ({type(exc).__name__}: {exc}); refusing worktree removal"
    if stopped.ok:
        return True, ""
    survivors = ", ".join(str(proc.pid) for proc in stopped.survivors) or "unknown"
    return False, f"background jobs could not be stopped ({stopped.error}; pids {survivors}); refusing worktree removal"


def _settle_worktree_reap(
    worktree: Path,
    *,
    created_by_this_dispatch: bool | None,
    settling_task_id: str,
    lock_timeout_s: float | None = None,
    task_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Remove a settled checkout this dispatch created and keep its branch ref.

    The scheduled reaper's PR, rollover, and GraphQL gates skip the clean
    read-only review checkouts this path exists to drop. Removal goes through
    :func:`_remove_dispatch_worktree` with settle's ownership proof and is
    worktree-only: ``git branch`` is never invoked, and a missing branch ref
    after removal is an error. ``task_record`` is the settling task's record:
    when its exit scan says jobs may be alive, once ownership is proven those
    processes are stopped inside the worker's own scope before removal, and
    removal is refused if any survive or the scope is refused (#8991). This
    never raises.
    """

    def releasable() -> tuple[bool, str]:
        ok, detail = _settled_worktree_ownership(worktree, created_by_this_dispatch=created_by_this_dispatch)
        if not ok or task_record is None:
            return ok, detail
        stopped, refusal = _stop_worker_background_jobs(task_record, task_id=settling_task_id)
        return (True, detail) if stopped else (False, refusal)

    # Resolved before removal: the checkout's ``.git`` pointer is gone after it.
    owning_repo = worktree_claims.owning_repo_root(worktree, default=_REPO_ROOT)
    removal = _remove_dispatch_worktree(
        worktree,
        reason="settled clean worktree; branch ref kept",
        owner_task_id=settling_task_id,
        releasable=releasable,
        force=True,
        lock_timeout_s=lock_timeout_s,
    )
    branch = removal["branch"]
    if removal["action"] == "removed" and branch is not None and not _branch_ref_exists(owning_repo, branch):
        return {
            **removal,
            "action": "error",
            "reason": "branch ref missing after worktree removal",
            "error": f"refs/heads/{branch} was deleted",
        }
    return removal


def _validate_existing_worktree(
    *,
    path: Path,
    expected_branch: str,
    base: str,
    allow_rebase: bool = True,
) -> bool:
    """Validate a reused worktree. Returns True if a rebase occurred.

    Raises :class:`WorktreeBranchMismatch`, :class:`WorktreeDirty`, or
    :class:`WorktreeStaleBase` on the respective failure mode. The
    checks skip silently when the path isn't a real git worktree (e.g.
    a tmp_path fixture) — those cases either fail at the first real git
    operation later or were never on the dispatch path to begin with.
    """
    # 1. Branch check.
    try:
        branch_proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if branch_proc.returncode != 0:
        # Not a git worktree (e.g. test tmp dir). Don't treat as an error —
        # the caller may be a test fixture, and real dispatch paths will
        # surface the issue on the next git op.
        return False
    actual_branch = (branch_proc.stdout or "").strip()
    if actual_branch and actual_branch != expected_branch:
        raise WorktreeBranchMismatch(
            f"worktree at {path} is on branch {actual_branch!r}, expected "
            f"{expected_branch!r}. Remove it and retry:\n"
            f"    git worktree remove {path}"
        )

    # 2. Dirty check.
    try:
        status_proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git status timed out after {DEFAULT_GIT_TIMEOUT_S}s checking {path}") from exc
    dirty_output = (status_proc.stdout or "").strip()
    if dirty_output:
        first_files = [line[3:] for line in dirty_output.splitlines()[:3]]
        raise WorktreeDirty(
            f"worktree at {path} has uncommitted changes "
            f"(first {len(first_files)}): {first_files}. "
            f"Commit, stash, or remove the worktree before reuse."
        )

    # 3. Stale-base check. Refresh origin/{base} first. Single-remote hosts
    # keep the lenient bool contract — an offline fetch falls back to
    # whatever ref is locally available below. Two-remote hosts fail
    # closed inside _fetch_base when the canonical GitHub remote is
    # unreachable: a lagging mirror must never pin the base (#7522).
    # Normalize so an origin-prefixed ``base`` (the form the dispatch
    # runbooks mandate) never yields ``origin/origin/main`` — that
    # unresolvable ref made this whole check a silent no-op.
    origin_ref = _origin_base_ref(base)
    _fetch_base(base)
    try:
        count_proc = subprocess.run(
            ["git", "rev-list", "--count", f"HEAD..{origin_ref}"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if count_proc.returncode != 0:
        # origin/{base} unresolvable (offline / no remote). Nothing to do.
        return False
    try:
        behind = int((count_proc.stdout or "0").strip())
    except ValueError:
        behind = 0
    if behind == 0:
        return False

    if not allow_rebase:
        raise WorktreeStaleBase(
            f"worktree at {path} is {behind} commit(s) behind {origin_ref}; "
            "automatic rebasing is disabled. Synchronize it explicitly (for "
            "example, `git merge --ff-only "
            f"{origin_ref}`) before attaching a worker."
        )

    print(
        f"⚠️  worktree {path} is {behind} commit(s) behind {origin_ref}; attempting fast-forward rebase",
        file=sys.stderr,
    )
    try:
        rebase_proc = subprocess.run(
            ["git", "rebase", origin_ref],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                ["git", "rebase", "--abort"],
                cwd=path,
                capture_output=True,
                text=True,
                check=False,
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        raise WorktreeStaleBase(
            f"worktree at {path} is {behind} commit(s) behind {origin_ref} "
            f"and rebase timed out after {DEFAULT_GIT_TIMEOUT_S}s."
        ) from exc
    if rebase_proc.returncode != 0:
        # Clean up so the worktree isn't left mid-rebase.
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                ["git", "rebase", "--abort"],
                cwd=path,
                capture_output=True,
                text=True,
                check=False,
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        raise WorktreeStaleBase(
            f"worktree at {path} is {behind} commit(s) behind {origin_ref} "
            f"and rebase failed. Resolve manually or remove:\n"
            f"    git worktree remove {path}"
        )
    return True


def _provision_data_symlinks(worktree_path: Path, main_repo_root: Path) -> None:
    """Symlink heavy local-only files into a delegated worktree.

    Worktrees omit gitignored DBs and Node dependency directories, but quality
    gates open them relative to the running checkout. Use symlinks so each
    delegated worktree sees the same local files without copying multi-GB
    directories. The primary Python environment is deliberately excluded:
    workers invoke its absolute interpreter and must not receive a local
    ``.venv`` symlink.

    Self-link guard: if ``worktree_path`` *is* the main checkout, provisioning
    would create ``node_modules -> node_modules`` (a self-referential loop) that
    makes every later ``npm`` invocation die with ``spawn ELOOP``. Refuse. The
    per-link guards below also skip a ``source`` that already loops, so a bad
    root link is never propagated into worktrees. See the autopsy
    ``docs/bug-autopsies/node-modules-eloop-symlink.md``.
    """
    if worktree_path.resolve() == main_repo_root.resolve():
        print(
            "⚠️  refusing to provision symlinks into the main checkout "
            f"({worktree_path}) — would create self-referential loops",
            file=sys.stderr,
        )
        return

    for relative_path in (
        "data/vesum.db",
        "data/sources.db",
        "node_modules",
        "site/node_modules",
    ):
        source = main_repo_root / relative_path
        # ``source.exists()`` follows symlinks and returns False for a looping
        # source, so a self-referential root ``node_modules`` is skipped here
        # rather than copied into the worktree.
        if not source.exists():
            print(
                f"⚠️  skipping worktree link for missing/looping {source}",
                file=sys.stderr,
            )
            continue

        target = worktree_path / relative_path
        if target.exists() or target.is_symlink():
            continue

        resolved_source = source.resolve()
        if resolved_source == target.resolve():
            print(
                f"⚠️  skipping worktree link {target} — would be self-referential",
                file=sys.stderr,
            )
            continue

        if target.parent.exists() and not target.parent.is_dir():
            print(
                f"⚠️  skipping worktree link because {target.parent} is not a directory",
                file=sys.stderr,
            )
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(resolved_source)


# Default cone sparse-checkout exclusions for dispatch worktrees.
# Measured 2026-09-23 on a full working tree (du -sh, .git excluded): 1.6GB,
# of which curriculum/ is 289MB, wiki/ 66MB, data/projects/ 633MB, and
# data/lexicon/ 277MB. The migrated open-model registry payload tree is also
# excluded independently from registry/ so registry/lexicon remains available.
# Dropping these trees leaves a default dispatch under
# 450MB (re-measured 2026-09-25: 287MB). Opt back in with --sparse-include
# or --full-checkout. wiki/ is still a top-level tree
# (`git ls-tree -d HEAD wiki`), so it stays excluded.
#
# curriculum/ stays in the exclusion set, with one cone anchor so
# ``pytest -m repo_wide`` can read the manifest. Measured 2026-09-25 in a
# default sparse worktree (no curriculum/): that command failed 15 tests,
# and each one read only ``curriculum/l2-uk-en/curriculum.yaml``
# (FileNotFoundError, or ORCH_TRACK_NOT_ACTIVE because a missing manifest
# yields no active levels). Cone mode also checks out files that sit
# directly in every ancestor of an included directory. The anchor is
# ``curriculum/l2-uk-en/lesson-plans`` (192K), not a smaller sibling:
# once ``curriculum/`` exists, collection of
# tests/curriculum/test_plan_validate_cross.py loads
# ``lesson-plans/a1/_arc.yaml`` (tree_absent is false). An evidence-only
# anchor (3.4M, yaml present, arc absent) died at collection with exit 2.
# Including lesson-plans materialises the arc, curriculum.yaml, and the
# other loose files beside the manifest (vocabulary.db,
# module-mapping.json, callout-claims-review.md). ``du -sh`` of that
# tree: 3.6M, not 289M. The anchor is added only when that directory
# exists at HEAD.
_DISPATCH_SPARSE_EXCLUDE_DEFAULT = frozenset(
    {
        "curriculum",
        "wiki",
        "data/projects",
        "data/lexicon",
        "registry/projects",
    }
)
_DISPATCH_SPARSE_CURRICULUM_MANIFEST_CONE = "curriculum/l2-uk-en/lesson-plans"
# Owned-path prefixes that re-include a default-excluded tree even when the
# path itself is not under that tree (tests and scripts that read it).
# Filename stems end with "_" and match tests/test_open_model_*.py. Exact
# files are listed only when grep shows that file reads the tree. ``site/``
# consumes site/src/data/lexicon-*.json, not raw data/lexicon/.
# ``tests/test_open_model_`` is content-gated: most of those modules never
# read data/projects, and a blanket stem would check out ~633MB.
_SPARSE_OWNED_PATH_REINCLUDE: dict[str, tuple[str, ...]] = {
    "data/projects": (
        "data/projects",
        "tests/projects/open_model_data",
        "scripts/projects/open_model_data",
        "tests/test_open_model_",
    ),
    "data/lexicon": (
        "data/lexicon",
        "scripts/lexicon",
        "tests/lexicon",
        "tests/test_source_inventory_",
        "scripts/audit/source_inventory_review_decisions.py",
        "scripts/audit/generate_source_inventory_review_candidates.py",
        "scripts/practice/author_densified_pairs.py",
        "scripts/practice/creation_review.py",
        "scripts/practice/thin_mode_source_inventory.py",
    ),
}
# Stem prefixes whose match still has to mention the tree in that file.
_SPARSE_REINCLUDE_CONTENT_MARKERS: dict[str, tuple[str, ...]] = {
    "tests/test_open_model_": ("data/projects",),
}


def _sparse_path_has_prefix(path: str, prefix: str) -> bool:
    prefix = prefix.strip("/")
    return path == prefix or path.startswith(prefix + "/")


def _sparse_reinclude_prefix_matches(path: str, prefix: str) -> bool:
    """Match a directory prefix, an exact file, or a filename stem.

    Stems end with ``_`` so ``tests/test_open_model_`` matches
    ``tests/test_open_model_foundry_cli.py`` without also matching a
    sibling directory.
    """
    if _sparse_path_has_prefix(path, prefix):
        return True
    return prefix.endswith("_") and path.startswith(prefix)


def _assignment_mentions_marker(module_path: Path, name: str, markers: tuple[str, ...]) -> bool:
    """True when ``name = ...`` in ``module_path`` embeds a marker string."""
    try:
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError, UnicodeError):
        return False
    for stmt in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(stmt, ast.Assign):
            targets = list(stmt.targets)
            value = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            targets = [stmt.target]
            value = stmt.value
        if value is None:
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            rendered = ast.unparse(value)
            if any(marker in rendered for marker in markers):
                return True
    return False


def _imported_binding_mentions_marker(text: str, markers: tuple[str, ...]) -> bool:
    """True when the file uses an imported name whose value embeds a marker.

    Content-gated sparse stems used to require the literal ``data/projects``
    in the owned file. Readers that reach the tree through an imported path
    constant (``foundry.DEFAULT_V011_MANIFEST``) still need that tree.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    imported: dict[str, tuple[str, str]] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.ImportFrom) and stmt.module and stmt.level == 0:
            for alias in stmt.names:
                if alias.name == "*":
                    continue
                imported[alias.asname or alias.name] = (stmt.module, alias.name)
    needed: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and isinstance(node.ctx, ast.Load):
            binding = imported.get(node.value.id)
            if binding is None:
                continue
            module, imported_name = binding
            needed.add((f"{module}.{imported_name}", node.attr))
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            binding = imported.get(node.id)
            if binding is not None:
                needed.add(binding)
    for dotted, attr in needed:
        module_path = _REPO_ROOT / Path(*dotted.split(".")).with_suffix(".py")
        if module_path.is_file() and _assignment_mentions_marker(module_path, attr, markers):
            return True
    return False


def _reinclude_file_confirms(path: str, prefix: str) -> bool:
    """Content-gated stems must read the tree, directly or via an import."""
    markers = _SPARSE_REINCLUDE_CONTENT_MARKERS.get(prefix)
    if not markers:
        return True
    file_path = _REPO_ROOT / path
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return False
    if any(marker in text for marker in markers):
        return True
    return _imported_binding_mentions_marker(text, markers)


def _normalize_sparse_include(raw: Sequence[str] | None) -> tuple[str, ...]:
    """Normalize --sparse-include values to unique default-excluded trees.

    Fail closed: explicit values must be names in the default exclusion set
    (``curriculum``, ``wiki``, ``data/projects``, ``data/lexicon``,
    ``registry/projects``). Other nested paths and unknown names raise
    :class:`ValueError`.
    """
    if not raw:
        return ()
    seen: set[str] = set()
    ordered: list[str] = []
    allowed = ", ".join(sorted(_DISPATCH_SPARSE_EXCLUDE_DEFAULT))
    for item in raw:
        name = str(item).strip().strip("/")
        if not name or name in {".", ".."} or name.startswith("../") or "/../" in f"/{name}/":
            raise ValueError(
                f"--sparse-include {item!r} is empty or invalid; "
                "pass a default-excluded tree such as 'curriculum', 'wiki', 'data/projects', "
                "or 'registry/projects'"
            )
        if name not in _DISPATCH_SPARSE_EXCLUDE_DEFAULT:
            if "/" in name:
                raise ValueError(
                    f"--sparse-include {item!r} must name a default-excluded tree "
                    "(nested exclusions: data/projects, data/lexicon, registry/projects). "
                    f"Allowed: {allowed}"
                )
            raise ValueError(f"--sparse-include {name!r} is not a default-excluded tree; allowed: {allowed}")
        if name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return tuple(ordered)


def _infer_sparse_include_from_text(text: str | None) -> tuple[str, ...]:
    """Detect default-excluded path prefixes referenced in a prompt."""
    if not text:
        return ()
    found: list[str] = []
    for name in sorted(_DISPATCH_SPARSE_EXCLUDE_DEFAULT, key=len, reverse=True):
        # Path-like reference: curriculum/…, data/projects/… — not bare words.
        if re.search(rf"(?<![\w.-]){re.escape(name)}/", text):
            found.append(name)
    return tuple(found)


def _sparse_tree_for_owned_path(raw: str) -> str | None:
    """Return the excluded tree a research-owned path requires, if any."""
    path = str(raw).strip().strip("/")
    if not path:
        return None
    for name in sorted(_DISPATCH_SPARSE_EXCLUDE_DEFAULT, key=len, reverse=True):
        if _sparse_path_has_prefix(path, name):
            return name
    for tree, prefixes in _SPARSE_OWNED_PATH_REINCLUDE.items():
        if any(
            _sparse_reinclude_prefix_matches(path, prefix) and _reinclude_file_confirms(path, prefix)
            for prefix in prefixes
        ):
            return tree
    return None


def _infer_sparse_include(
    explicit: Sequence[str] | None,
    *,
    owned_paths: Sequence[str] | None = None,
    prompt_text: str | None = None,
) -> tuple[str, ...]:
    """Merge explicit includes with owned-path prefixes and prompt path references.

    A dispatch that already declares ``--research-owned-path curriculum/...``,
    ``scripts/projects/open_model_data/...``, or a lexicon reader such as
    ``scripts/lexicon/...`` materializes the matching excluded tree without a
    second flag. ``site/...`` does not: the frontend reads runtime JSON under
    ``site/src/data/``, not raw ``data/lexicon/``.
    """
    merged: list[str] = list(_normalize_sparse_include(explicit))
    seen = set(merged)
    for raw in owned_paths or ():
        name = _sparse_tree_for_owned_path(str(raw))
        if name and name not in seen:
            seen.add(name)
            merged.append(name)
    for name in _infer_sparse_include_from_text(prompt_text):
        if name not in seen:
            seen.add(name)
            merged.append(name)
    return tuple(merged)


def _list_worktree_dirs(worktree_path: Path, *tree_path: str, at_ref: str = "HEAD") -> list[str]:
    """Return directory names from ``git ls-tree -d`` at ``at_ref``.

    With no ``tree_path``, lists top-level directories. ``data/`` lists the
    children (``data/projects``, …) so new ``data/*`` dirs are included
    automatically and only the named exclusions drop out.
    """
    label = "/".join(tree_path) if tree_path else "top-level"
    try:
        proc = subprocess.run(
            ["git", "ls-tree", "-d", "--name-only", at_ref, *tree_path],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"could not list {label} dirs in {worktree_path}: timed out after {DEFAULT_GIT_TIMEOUT_S}s"
        ) from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "git ls-tree failed").strip()
        raise RuntimeError(f"could not list {label} dirs in {worktree_path}: {detail}")
    return [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]


def _list_worktree_top_dirs(worktree_path: Path, *, at_ref: str = "HEAD") -> list[str]:
    """Return top-level directory names at ``at_ref`` inside a worktree."""
    return _list_worktree_dirs(worktree_path, at_ref=at_ref)


def _dispatch_sparse_cone_dirs(
    top_dirs: Sequence[str],
    data_children: Sequence[str],
    exclude: Collection[str],
    registry_children: Sequence[str] = (),
) -> tuple[list[str], list[str]]:
    """Build a cone include list that drops excluded dirs at directory level.

    Nested exclusions (``data/projects``, ``data/lexicon``, and
    ``registry/projects``) are expressed by listing the sibling directories
    instead of their parent. Cone mode then keeps files directly in each
    parent and preserves the other sibling trees.
    """
    exclude_set = set(exclude)
    nested_children = {"data": data_children, "registry": registry_children}
    cone: list[str] = []
    excluded: list[str] = []
    for name in top_dirs:
        if name not in nested_children:
            if name in exclude_set:
                excluded.append(name)
            else:
                cone.append(name)
            continue
        if name in exclude_set:
            excluded.append(name)
            continue
        children = list(nested_children[name])
        dropped = [child for child in children if child in exclude_set]
        if not dropped:
            cone.append(name)
            continue
        for child in children:
            if child in exclude_set:
                excluded.append(child)
            else:
                cone.append(child)
    return cone, sorted(excluded)


def _apply_dispatch_sparse_checkout(
    worktree_path: Path,
    *,
    full_checkout: bool = False,
    sparse_include: Sequence[str] = (),
) -> dict[str, Any]:
    """Apply (or disable) cone sparse-checkout on a dispatch worktree.

    Default profile excludes ``curriculum/``, ``wiki/``, ``data/projects/``
    (~633MB), ``data/lexicon/`` (~277MB), and ``registry/projects/``. The
    latter is excluded as a nested tree so ``registry/lexicon/`` stays
    available. When ``curriculum`` stays
    excluded and ``curriculum/l2-uk-en/lesson-plans`` exists at HEAD, that
    directory is still cone-included so ``curriculum/l2-uk-en/curriculum.yaml``
    and ``lesson-plans/a1/_arc.yaml`` are present (~3.6MB) without the rest
    of ``curriculum/``.
    ``--full-checkout`` disables sparse mode. ``--sparse-include`` keeps a
    named excluded tree.
    """
    includes = _normalize_sparse_include(sparse_include)
    telemetry: dict[str, Any] = {
        "full_checkout": bool(full_checkout),
        "sparse_include": list(includes),
        "excluded": [],
        "included_dirs": [],
        "applied": False,
        "error": None,
    }

    def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
        # Must sanitize GIT_* so sparse-checkout applies to *this* worktree
        # when a parent harness injects GIT_DIR/GIT_WORK_TREE (pre-commit, etc.).
        try:
            return subprocess.run(
                args,
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=False,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(
                args=args,
                returncode=124,
                stdout="",
                stderr=f"sparse-checkout command timed out after {DEFAULT_GIT_TIMEOUT_S}s",
            )

    if full_checkout:
        proc = _run_git(["git", "sparse-checkout", "disable"])
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "sparse-checkout disable failed").strip()
            telemetry["error"] = detail
            raise RuntimeError(f"failed to disable sparse-checkout in {worktree_path}: {detail}")
        telemetry["applied"] = True
        return telemetry

    exclude = set(_DISPATCH_SPARSE_EXCLUDE_DEFAULT) - set(includes)
    all_dirs = _list_worktree_top_dirs(worktree_path)
    data_children = _list_worktree_dirs(worktree_path, "data/") if "data" in all_dirs else []
    registry_children = _list_worktree_dirs(worktree_path, "registry/") if "registry" in all_dirs else []
    included, excluded = _dispatch_sparse_cone_dirs(all_dirs, data_children, exclude, registry_children)
    manifest_cone = _DISPATCH_SPARSE_CURRICULUM_MANIFEST_CONE
    if "curriculum" in excluded and manifest_cone in _list_worktree_dirs(worktree_path, manifest_cone):
        included.append(manifest_cone)
    telemetry["excluded"] = excluded
    telemetry["included_dirs"] = included

    if not excluded:
        # Nothing to drop at this ref (or everything was re-included). Prefer a
        # full tree rather than an empty cone set.
        proc = _run_git(["git", "sparse-checkout", "disable"])
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "sparse-checkout disable failed").strip()
            telemetry["error"] = detail
            raise RuntimeError(f"failed to disable sparse-checkout in {worktree_path}: {detail}")
        telemetry["applied"] = True
        return telemetry

    proc = _run_git(["git", "sparse-checkout", "init", "--cone"])
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "sparse-checkout init failed").strip()
        telemetry["error"] = detail
        raise RuntimeError(f"failed to init sparse-checkout in {worktree_path}: {detail}")

    set_args = ["git", "sparse-checkout", "set", "--cone"]
    if included:
        set_args.extend(["--", *included])
    proc = _run_git(set_args)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "sparse-checkout set failed").strip()
        telemetry["error"] = detail
        raise RuntimeError(
            f"failed to set sparse-checkout in {worktree_path}: {detail}. "
            "Commit/stash local changes under excluded paths, or pass "
            "--full-checkout / --sparse-include."
        )

    telemetry["applied"] = True
    print(
        f"🌲 dispatch sparse-checkout: excluded {', '.join(excluded)} "
        f"in {worktree_path} "
        "(git sparse-checkout add <dir>, or --sparse-include / --full-checkout)",
        file=sys.stderr,
    )
    return telemetry


def _inspect_worktree_local_venv(worktree_path: Path) -> dict[str, str | bool | None]:
    """Describe a prohibited worktree-local environment without modifying it.

    Dispatch worktrees share the primary checkout's project interpreter. Git
    does not copy ignored files into a new worktree, but an adapter or worker
    can still create a local ``.venv`` after creation. Record an early warning
    in dispatch state instead of deleting a possibly active environment; the
    P0 reaper remains the sole automatic deletion hand after merge.
    """
    candidate = worktree_path / ".venv"
    try:
        candidate.lstat()
    except FileNotFoundError:
        return {"present": False, "kind": None, "path": None}
    except OSError as exc:
        return {
            "present": False,
            "kind": "unreadable",
            "path": str(candidate),
            "error": type(exc).__name__,
        }

    if candidate.is_symlink():
        kind = "symlink"
    elif candidate.is_dir():
        kind = "directory"
    else:
        kind = "file"
    return {"present": True, "kind": kind, "path": str(candidate)}


def _record_worktree_local_venv_warning(
    worktree_path: Path,
    telemetry: dict[str, Any],
) -> None:
    """Attach local-venv state to telemetry and warn when it is present."""
    local_venv = _inspect_worktree_local_venv(worktree_path)
    telemetry["local_venv"] = local_venv
    if local_venv.get("present"):
        print(
            "⚠️  dispatch worktree contains a local .venv; do not use, copy, or "
            f"replace it. Use the primary interpreter {project_interpreter()} "
            f"instead: {worktree_path / '.venv'} ({local_venv.get('kind')}).",
            file=sys.stderr,
        )


def _refuse_if_gate_head_moved(origin_sha: str, pinned_head_sha: str | None) -> None:
    """Refuse when a later fetch is not the SHA the Gemini path gate checked."""
    if pinned_head_sha is not None and origin_sha != pinned_head_sha:
        raise RuntimeError(
            "refusing dispatch: fetched branch head "
            f"{origin_sha} differs from the Gemini path-gate SHA {pinned_head_sha}"
        )


def _resolve_worktree_base_sha(
    *,
    agent: str,
    task_id: str,
    raw_path: str | None = None,
    base: str,
    branch: str | None,
    allow_rebase: bool = True,
    pinned_head_sha: str | None = None,
    detached: bool = False,
    validated_path: Path | None = None,
) -> str:
    """Resolve one immutable base SHA before worktree creation.

    A dispatch receipt and its worker must bind the same checkout state. This
    helper performs moving-ref validation first, then returns the SHA passed to
    :func:`_ensure_worktree`. The latter must not fetch, rebase, or dereference
    a branch again when the SHA is supplied. ``validated_path``, when given, is
    used as is and never resolved again (#8775, :func:`_helper_worktree_path`).
    """
    worktree_path = _helper_worktree_path(raw_path, validated_path)
    requested_branch = _validate_branch_reuse_name(branch) if branch else None
    if detached and worktree_path.exists():
        raise ValueError(f"detached read-only worktree already exists: {worktree_path}; refuse reuse")

    if worktree_path.exists():
        if not worktree_path.is_dir():
            raise ValueError(f"worktree path exists but is not a directory: {worktree_path}")
        _validate_existing_worktree(
            path=worktree_path,
            expected_branch=requested_branch or _derive_worktree_branch(agent, task_id),
            base=requested_branch or base,
            # Receipt-bound dispatches must leave a reused worktree untouched
            # until admission succeeds. Ordinary follow-ups retain the
            # established auto-rebase behavior.
            # An explicit branch is an attach request, not permission to
            # rewrite the PR's history. In particular, rebasing an attached
            # branch can flatten or replay merge commits. A stale attachment
            # must be synchronized deliberately by its owner.
            allow_rebase=allow_rebase and requested_branch is None,
        )
        if requested_branch:
            # Existing paths used to return before this check, allowing local
            # commits not present on the PR branch to slip into a new worker.
            # Validate only after the dirty check above, so a dirty checkout
            # always receives the most actionable refusal.
            _fetch_existing_branch(requested_branch)
            _refuse_if_gate_head_moved(
                _require_local_branch_is_ancestor_of_origin(requested_branch),
                pinned_head_sha,
            )
        resolved = _resolve_sha(worktree_path)
        if resolved is None:
            raise RuntimeError(f"could not resolve HEAD for existing worktree {worktree_path}")
        return resolved

    if requested_branch:
        _fetch_existing_branch(requested_branch)
        origin_sha = _require_local_branch_is_ancestor_of_origin(requested_branch)
        _refuse_if_gate_head_moved(origin_sha, pinned_head_sha)
        return pinned_head_sha or origin_sha

    origin_ref = _origin_base_ref(base)
    if _fetch_base(base):
        resolved = _resolve_sha(_REPO_ROOT, origin_ref)
        if resolved is not None:
            return resolved

    branch_name = _base_branch_name(base)
    raise RuntimeError(
        f"could not fetch origin/{branch_name} and {origin_ref} is "
        f"unresolvable — refusing to branch from possibly-stale local "
        f"{branch_name}. Check connectivity and that "
        "`git remote get-url origin` points at the canonical remote "
        "(github.com:learn-ukrainian/learn-ukrainian.github.io), then "
        f"run `git fetch origin +refs/heads/{branch_name}:refs/remotes/origin/{branch_name}` and retry the dispatch. "
        "Do NOT use the primary checkout as a freshness source."
    )


_REVIEW_ATTEMPT_NO_REUSE_MARKER = "lu-review-attempt-no-reuse"


def _review_attempt_marker_path(worktree_path: Path) -> Path:
    try:
        proc = subprocess.run(
            ["git", "-C", str(worktree_path), "rev-parse", "--absolute-git-dir"],
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
            env=_sanitized_git_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"could not resolve git admin directory for {worktree_path}: {exc}") from exc
    git_dir = Path(proc.stdout.strip())
    if proc.returncode != 0 or not git_dir.is_absolute():
        raise RuntimeError(f"could not resolve git admin directory for {worktree_path}")
    return git_dir / _REVIEW_ATTEMPT_NO_REUSE_MARKER


def _refuse_review_attempt_worktree_reuse(worktree_path: Path) -> None:
    # A real linked worktree has a .git pointer. Test stubs may model only the
    # directory; the existing validation still handles those paths.
    if not (worktree_path / ".git").exists():
        return
    marker = _review_attempt_marker_path(worktree_path)
    if marker.is_file():
        try:
            task_id = marker.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise RuntimeError(f"could not read review attempt marker in {worktree_path}: {exc}") from exc
        raise ValueError(f"worktree {worktree_path} belongs to review attempt task {task_id!r}; reuse refused (#8517)")


def _mark_review_attempt_worktree(worktree_path: Path, task_id: str) -> None:
    marker = _review_attempt_marker_path(worktree_path)
    marker.write_text(f"{task_id}\n", encoding="utf-8")


def _ensure_worktree(
    *,
    agent: str,
    task_id: str,
    raw_path: str | None = None,
    base: str = "main",
    branch: str | None = None,
    resolved_base_sha: str | None = None,
    dry_run: bool = False,
    full_checkout: bool = False,
    sparse_include: Sequence[str] = (),
    run_nonce: str | None = None,
    detached: bool = False,
    validated_path: Path | None = None,
) -> tuple[Path, str | None, dict[str, Any]]:
    """Return a ready worktree path, creating or validating as needed.

    ``run_nonce`` names the dispatch run a fresh worktree's path reservation
    is recorded under (see :func:`_add_reserved_worktree`). ``validated_path``,
    when given, is used as is and never resolved again (#8775,
    :func:`_helper_worktree_path`).

    The telemetry dict (third tuple element) carries:
    - ``base_sha``: the SHA the worktree was branched from (or is currently
      sitting on, if reused).
    - ``rebased``: whether :func:`_validate_existing_worktree` advanced the
      reused worktree.
    - ``layout``: ``"dispatch"`` or ``"flat"``.
    - ``reused``: whether the path already existed and was validated rather
      than created.
    - ``sparse``: sparse-checkout profile telemetry (when applied).
    """
    worktree_path = _helper_worktree_path(raw_path, validated_path)
    requested_branch = _validate_branch_reuse_name(branch) if branch else None
    if detached and requested_branch:
        raise ValueError("detached worktree cannot attach a branch")
    worktree_branch = None if detached else requested_branch or _derive_worktree_branch(agent, task_id)
    layout = _classify_worktree_layout(worktree_path)
    telemetry: dict[str, Any] = {
        "base_sha": None,
        "rebased": False,
        "layout": layout,
        "reused": False,
        "sparse": None,
        "local_venv": None,
    }
    _release_superseded_review_worktrees(task_id, dry_run=dry_run)

    if requested_branch:
        if resolved_base_sha is None:
            _fetch_existing_branch(requested_branch)
            _require_local_branch_is_ancestor_of_origin(requested_branch)
        occupied_paths = _branch_worktree_paths(requested_branch)
        elsewhere = [path for path in occupied_paths if path != worktree_path]
        if elsewhere:
            # #5340: clean+synced+terminal holders are pure friction — release
            # them instead of bouncing the dispatch. Live/dirty holders still refuse.
            _release_stale_branch_holders(
                branch=requested_branch,
                holders=elsewhere,
                dry_run=dry_run,
            )
            occupied_paths = _branch_worktree_paths(requested_branch)
            elsewhere = [path for path in occupied_paths if path != worktree_path]
            # dry-run treats releasable holders as free without mutating
            if dry_run:
                still_blocking = [
                    path for path in elsewhere if not _stale_branch_holder_releasable(path, requested_branch)[0]
                ]
            else:
                still_blocking = elsewhere
            if still_blocking:
                locations = ", ".join(str(path) for path in still_blocking)
                raise WorktreeBranchMismatch(
                    f"branch {requested_branch!r} is already checked out in {locations}; "
                    "refusing to attach it to another worktree"
                )

    if worktree_path.exists():
        if detached:
            raise ValueError(f"detached read-only worktree already exists: {worktree_path}; refuse reuse")
        if not worktree_path.is_dir():
            raise ValueError(f"worktree path exists but is not a directory: {worktree_path}")
        _refuse_review_attempt_worktree_reuse(worktree_path)
        telemetry["reused"] = True
        if resolved_base_sha is None:
            telemetry["rebased"] = _validate_existing_worktree(
                path=worktree_path,
                expected_branch=worktree_branch,
                # For --branch reuse the staleness/fast-forward reference is the
                # requested branch ITSELF (origin/<branch>), never origin/main: a
                # follow-up worktree for an existing PR is almost always behind
                # main (main moved since the PR branched), and validating against
                # main would spuriously fail the dry-run or rebase a PR branch
                # onto main as a validation side effect. (review-4905-grok)
                base=requested_branch or base,
                # `--branch` is an explicit attach request. Never rewrite its
                # history during provisioning; a stale worktree must be
                # synchronized deliberately by its owner.
                allow_rebase=not dry_run and requested_branch is None,
            )
        actual_sha = _resolve_sha(worktree_path)
        if actual_sha is None:
            raise RuntimeError(f"could not resolve HEAD for existing worktree {worktree_path}")
        if resolved_base_sha is not None and actual_sha != resolved_base_sha:
            raise WorktreeStaleBase(
                "existing worktree HEAD changed after immutable-base resolution; "
                f"expected {resolved_base_sha}, found {actual_sha}. Refusing worker spawn."
            )
        telemetry["base_sha"] = actual_sha
        if dry_run:
            return worktree_path, worktree_branch, telemetry
        # Reused worktrees may predate this provisioning hook; the helper is
        # idempotent and never clobbers existing files.
        _provision_data_symlinks(worktree_path, _REPO_ROOT)
        # Re-apply sparse profile so pre-existing full trees shrink on reuse.
        telemetry["sparse"] = _apply_dispatch_sparse_checkout(
            worktree_path,
            full_checkout=full_checkout,
            sparse_include=sparse_include,
        )
        _record_worktree_local_venv_warning(worktree_path, telemetry)
        return worktree_path, worktree_branch, telemetry

    if dry_run:
        raise ValueError(
            f"branch reuse dry-run found no existing worktree at {worktree_path}; rerun without --dry-run to create one"
        )

    # Fix 1 (#1476): fetch origin/{base} and branch from the remote ref,
    # not the local one. Local `main` drifts the moment a PR merges while
    # a dispatch is queued — this is the stale-base footgun Codex
    # diagnosed in bridge msg #431 (2026-04-23). Normalize so an
    # origin-prefixed ``base`` (``--base origin/main``, the mandated form)
    # fetches ``main`` and branches from ``origin/main`` — not the
    # unresolvable ``origin/origin/main``.
    if resolved_base_sha is not None:
        worktree_base_ref = resolved_base_sha
    elif requested_branch:
        # Attach directly to the fetched PR/follow-up branch.  Never branch
        # from origin/main here: that was the follow-up-dispatch footgun.
        worktree_base_ref = requested_branch
    else:
        origin_ref = _origin_base_ref(base)
        if _fetch_base(base):
            worktree_base_ref = origin_ref
        else:
            # #5803 follow-up: NO silent fallback to the local base. That
            # fallback is exactly why a worker concluded "origin/main may be
            # stale" and went to the PRIMARY checkout for a fresh copy,
            # leaving it detached. Fail with an actionable error instead.
            branch_name = _base_branch_name(base)
            raise RuntimeError(
                f"could not fetch origin/{branch_name} and {origin_ref} is "
                f"unresolvable — refusing to branch from possibly-stale local "
                f"{branch_name}. Check connectivity and that "
                "`git remote get-url origin` points at the canonical remote "
                "(github.com:learn-ukrainian/learn-ukrainian.github.io), then "
                f"run `git fetch origin +refs/heads/{branch_name}:refs/remotes/origin/{branch_name}` and retry the dispatch. "
                "Do NOT use the primary checkout as a freshness source."
            )

    # Ensure parent dirs exist for the dispatch/ subtree layout.
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    add_command = ["git", "worktree", "add"]
    if requested_branch and resolved_base_sha is None:
        # ``-B`` intentionally resets a behind local tracking ref to the SHA
        # fetched from origin. _require_local_branch_is_ancestor_of_origin()
        # already refused any local-only commits, and branch holders were
        # released/refused above, so this cannot silently overwrite work.
        add_command.extend(
            [
                "--track",
                "-B",
                requested_branch,
                str(worktree_path),
                f"origin/{requested_branch}",
            ]
        )
    elif requested_branch:
        # The branch was resolved before creation. Reset only to that immutable
        # commit, never a ref that might move before creation.
        add_command.extend(["-B", requested_branch, str(worktree_path), worktree_base_ref])
    elif detached:
        add_command.extend(["--detach", str(worktree_path), worktree_base_ref])
    else:
        add_command.extend(["-b", worktree_branch, str(worktree_path), worktree_base_ref])
    _add_reserved_worktree(
        add_command,
        repo_root=_REPO_ROOT,
        worktree_path=worktree_path,
        task_id=task_id,
        run_nonce=run_nonce,
        base_sha=resolved_base_sha,
    )
    actual_sha = _resolve_sha(worktree_path)
    if actual_sha is None:
        raise RuntimeError(f"could not resolve HEAD for created worktree {worktree_path}")
    if resolved_base_sha is not None and actual_sha != resolved_base_sha:
        raise WorktreeStaleBase(
            "created worktree HEAD differs from immutable base; "
            f"expected {resolved_base_sha}, found {actual_sha}. Refusing worker spawn."
        )
    telemetry["base_sha"] = actual_sha
    if requested_branch and resolved_base_sha is not None:
        # `git worktree add -B <branch> <path> <sha>` does not configure an
        # upstream. Restore the tracking contract the non-SHA branch path
        # gets from `--track`, after verifying the immutable checkout and
        # before any provisioning or worker side effect.
        try:
            upstream_proc = subprocess.run(
                ["git", "branch", "--set-upstream-to", f"origin/{requested_branch}", requested_branch],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"could not configure upstream origin/{requested_branch} for {worktree_path}: timed out after {DEFAULT_GIT_TIMEOUT_S}s"
            ) from exc
        if upstream_proc.returncode != 0:
            detail = (upstream_proc.stderr or upstream_proc.stdout or "git branch failed").strip()
            raise RuntimeError(f"could not configure upstream origin/{requested_branch} for {worktree_path}: {detail}")
    _provision_data_symlinks(worktree_path, _REPO_ROOT)
    telemetry["sparse"] = _apply_dispatch_sparse_checkout(
        worktree_path,
        full_checkout=full_checkout,
        sparse_include=sparse_include,
    )
    _record_worktree_local_venv_warning(worktree_path, telemetry)
    return worktree_path, worktree_branch, telemetry


def _augment_prompt_with_worktree(
    prompt: str,
    worktree_path: Path | None,
    *,
    mode: str = "read-only",
    sparse_telemetry: dict[str, Any] | None = None,
    delegate_commits: bool = False,
) -> str:
    """Inject worktree context into the delegated prompt when relevant.

    ``delegate_commits`` (Kimi seats) replaces the commit-and-push closeout:
    the worker leaves its changes in the tree and delegate commits the owned
    paths after checking that the diff adds no Cyrillic text.
    """
    if worktree_path is None:
        return prompt
    sparse_note = ""
    if sparse_telemetry and not sparse_telemetry.get("full_checkout"):
        excluded = sparse_telemetry.get("excluded") or []
        if excluded:
            add_commands = " ".join(f"`git sparse-checkout add {name}`" for name in excluded)
            sparse_note = (
                "Sparse-checkout is active: these trees are NOT present: "
                + ", ".join(str(p) for p in excluded)
                + ". To materialize one inside this worktree, run "
                + add_commands
                + " (for example `git sparse-checkout add data/projects`). "
                + "Do not invent content for missing paths.\n"
            )
    delivery_note = ""
    if mode in _WRITE_CAPABLE_MODES and delegate_commits:
        delivery_note = (
            "\n[write-mode closeout]\n"
            "Do not commit or push. Leave your changes in this worktree, inside the owned paths.\n"
            "After you exit, delegate checks the diff and commits and pushes the owned paths; "
            "a diff that adds any Cyrillic character, or content that is not text, is refused and "
            "nothing is committed. This worktree's git hooks refuse the same commits, and it has no push access.\n"
            "Delete scratch files before you finish.\n"
        )
    elif mode in _WRITE_CAPABLE_MODES:
        delivery_note = (
            "\n[write-mode closeout]\n"
            "Commit your work (use the literal trailer in `$LU_X_AGENT_TRAILER`).\n"
            "`git push -u origin HEAD`\n"
            "Leave `git status --porcelain` empty (commit or delete scratch files).\n"
            "Do not open or merge PRs unless the brief says so; "
            "report the pushed head SHA and clean status.\n"
            "\n[optional delivery signal]\n"
            "If you finish with zero commits (a verified no-op), you MAY end your final response "
            "with one machine-readable line as positive proof: "
            '`DELIVERABLE: {"outcome":"no_change","reason":"why no changes are required"}`. '
            "This line is optional — its absence never fails the dispatch.\n"
        )
    # #9057: every worktree dispatch carries one test-scope rule. Write modes
    # run only the tests for files they changed, including importers of a
    # changed shared helper; review modes cite CI. The PR's own CI, and the
    # merge queue on the merged tree, are the full-suite proof — a dispatch
    # `gh workflow run` does not satisfy the PR's required check.
    if mode in _WRITE_CAPABLE_MODES:
        test_scope = (
            "\n[test scope]\n"
            "Run only the tests that cover the files you changed, including tests of "
            "code that imports a changed shared helper, and name those test files explicitly.\n"
            "Never collect the whole `tests/` tree (`pytest tests`, `pytest tests -k …`); "
            "never `-n auto` or `-n` above 2.\n"
            "Run tests in the foreground and wait for them "
            "(never end the turn while a test runs in the background).\n"
            "The full suite runs in the PR's CI (and again in the merge queue on the merged "
            "tree) — that is the proof; do not trigger extra full runs. "
            "Use `gh workflow run ci.yml --ref <branch>` only when the brief explicitly asks "
            "for it (a branch with no PR yet, a baseline capture, or diagnosis).\n"
        )
    else:
        test_scope = (
            "\n[test scope]\n"
            "Do not re-run test suites that the PR's CI runs. Review the diff.\n"
            "Run at most the specific tests that reproduce a finding you are checking.\n"
            "Cite CI run ids for suite results.\n"
        )
    # #8775: the path is data. ASCII JSON quoting keeps it one quoted line even
    # if an unvalidated path ever reaches this block.
    return (
        "[delegate worktree]\n"
        "Run all file edits, tests, and git commands inside this worktree "
        f"(JSON-quoted path): {json.dumps(str(worktree_path))}\n"
        "Do not switch branches in the main checkout.\n"
        # #5803 follow-up: remove the workflow reason to visit the primary.
        # A linked worktree shares the canonical `origin` remote, so fresh
        # main is always one fetch away from INSIDE the worktree.
        "If you need a fresh base, run `git fetch origin main` INSIDE this worktree — "
        "`origin` here points at the canonical GitHub remote and fetch works from any "
        "linked worktree. NEVER use the primary checkout as a source of freshness "
        "(no `git -C <primary> pull/fetch/checkout`); it is the human's interactive home.\n"
        "\n[shared project interpreter]\n"
        "Never create, copy, symlink, activate, or use a `.venv` inside this worktree. "
        f"Run every project Python command with `{project_interpreter()}` "
        "(the absolute primary interpreter), never `python`, `.venv/bin/python`, or "
        "`python -m venv .venv`. Do not change `PYTHONPATH` merely because the worker "
        "cwd is a worktree.\n"
        f"{sparse_note}{test_scope}{delivery_note}\n"
        f"{prompt}"
    )


def _load_task_lifecycle_carrier(raw_path: str | None) -> tuple[dict[str, Any] | None, str]:
    """Validate one canonical lifecycle ledger before dispatch side effects."""
    if not raw_path:
        return None, ""
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.orchestration import task_lifecycle

    path = Path(raw_path).expanduser().resolve()
    ledger = task_lifecycle.load_lifecycle(path)
    carrier = task_lifecycle.carrier_projection(ledger, state_file=str(path))
    return carrier, task_lifecycle.render_carrier_prompt(carrier)


class ResearchContextError(ValueError):
    """A --research-* flag violated a request-side bound (mirrors the API 422s)."""


def _build_research_context(args: argparse.Namespace):
    """Return a normalized research ``Context`` from the explicit --research-* flags.

    Returns ``None`` when no flag was given (the no-flags path stays byte-identical
    to a pre-P3 dispatch). Never infers a value from the prompt, agent, provider, or
    branch — ADR-011 P3 requires explicit dimensions and fails closed on the rest.
    Validates the same request-side caps the FastAPI query layer enforces so a
    direct CLI caller cannot smuggle an oversize/over-count context past the API.
    """
    role = getattr(args, "research_role", None)
    family = getattr(args, "research_task_family", None)
    track = getattr(args, "research_track", None)
    owned = getattr(args, "research_owned_path", None) or []
    if not (role or family or track or owned):
        return None

    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.research import registry as reg

    for label, value in (
        ("--research-role", role),
        ("--research-task-family", family),
        ("--research-track", track),
    ):
        if value is not None and len(value) > reg.MAX_QUERY_VALUE_LEN:
            raise ResearchContextError(f"{label} value too long (max {reg.MAX_QUERY_VALUE_LEN} chars)")
    if len(owned) > reg.MAX_OWNED_PATHS:
        raise ResearchContextError(f"too many --research-owned-path values ({len(owned)} > {reg.MAX_OWNED_PATHS})")
    for path in owned:
        if len(path) > reg.MAX_OWNED_PATH_LEN:
            raise ResearchContextError(f"--research-owned-path value too long (max {reg.MAX_OWNED_PATH_LEN} chars)")
    return reg.normalize_context(role, family, track, owned)


def _render_research_prompt_block(pointers: list[dict[str, Any]]) -> str:
    """Render the bounded, POINTER-ONLY research block appended to a delegated prompt.

    Never contains a digest body/summary/source — only ids, states, and content
    hashes plus the on-demand fetch instruction. The pointer set is already capped
    (top-5 / ≤1.5 KB) by the selector.
    """
    lines = [
        "",
        "[project research pointers — ADR-011 P3]",
        "These research-registry records match this task's context. Bodies are NOT",
        "included; fetch one on demand only if you need it:",
        "  GET /api/knowledge/record/{id}?task={your-task-id}",
    ]
    for ptr in pointers:
        lines.append(f"- {ptr['id']} [{ptr['state']}] content_hash={ptr['content_hash']}")
    lines.append("")
    return "\n".join(lines)


def _with_optional_research_state(state: dict[str, Any], research_state: dict[str, Any] | None) -> dict[str, Any]:
    """Add ``"research"`` to ``state`` only when ``research_state`` is non-``None``.

    ADR-011 P3 default-compatibility: a no-flags dispatch, a disabled registry, or
    a degraded/failed injection must persist byte-identical pre-P3 state — the key
    is OMITTED, never present as ``"research": null``. Pointer ids / filtered ETag
    / dropped ids / context fingerprint only when present — never raw owned paths,
    digest/source/prompt text, role, or task family.
    """
    if research_state is not None:
        state["research"] = research_state
    return state


def _resolve_research_injection(ctx, task_id: str) -> tuple[str, dict[str, Any] | None]:
    """Fail-open pointer resolution for a dispatch context.

    Returns ``(prompt_block, persist_state)``. ``persist_state`` records ONLY the
    pointer ids, filtered projection ETag, dropped ids, and a context fingerprint —
    never raw owned paths, digest/source/prompt text, role, or task family. Any
    disabled/malformed/unexpected registry condition degrades to ``("", None)`` so a
    dispatch is never blocked by the research surface. Emits one surface (not
    consumption) telemetry event per injected pointer, attributed to ``task_id``.
    """
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.research import consumption
    from scripts.research import registry as reg

    try:
        if not reg.is_enabled(root=_REPO_ROOT):
            return "", None
        runtime = reg.load_runtime_safe(root=_REPO_ROOT)
        if runtime is None:
            return "", None
        pointers, dropped = reg.select_pointers(runtime, ctx)
        etag = reg.filtered_manifest(runtime, ctx).etag_hex
        persist_state = {
            "pointer_ids": [ptr["id"] for ptr in pointers],
            "filtered_etag": etag,
            "dropped_ids": list(dropped),
            "context_fingerprint": reg.context_fingerprint(ctx),
        }
        if not pointers:
            return "", persist_state
        for ptr in pointers:
            consumption.emit_surface(
                research_id=ptr["id"],
                surface=consumption.SURFACE_DISPATCH,
                task_id=task_id,
            )
        return _render_research_prompt_block(pointers), persist_state
    except Exception as exc:  # fail-open: research never blocks a dispatch
        print(
            f"[delegate] WARNING: research pointer injection skipped: {type(exc).__name__}",
            file=sys.stderr,
        )
        return "", None


# ---------------------------------------------------------------------------
# Worker entrypoint — runs inside the detached subprocess
# ---------------------------------------------------------------------------


def _worker_sigterm_handler(_signum, _frame):
    """SIGTERM handler for the worker process.

    Default Python SIGTERM behavior is to terminate abruptly WITHOUT
    running any finally blocks — meaning a cancel via
    ``delegate.py cancel`` would leave the child CLI subprocess
    (codex exec, gemini, claude) orphaned. That's a real leak,
    especially for workspace-write / danger modes.

    Fix: install this handler in _run_worker. When the parent sends
    SIGTERM, this raises KeyboardInterrupt, which propagates up
    through runner.invoke()'s try/finally block, which kills the
    subprocess and stops the watchdog cleanly. The worker's own
    try/except in _run_worker catches the KeyboardInterrupt, writes
    a final state file with status=failed + a "cancelled via SIGTERM"
    stderr excerpt, and exits 1.

    Added after Gemini review 2026-04-10.
    """
    raise KeyboardInterrupt("SIGTERM received; unwinding for cleanup")


def _classify_final_status(
    *,
    cancelled: bool,
    rate_limited: bool,
    ok_outcome: bool,
    timed_out: bool = False,
) -> str:
    """Map worker outcome flags to the persisted delegate task status."""
    if cancelled:
        return "cancelled"
    if timed_out:
        return "timeout"
    if rate_limited:
        return "rate_limited"
    if ok_outcome:
        return "done"
    return "failed"


def _worker_run_incomplete(stderr_excerpt: str | None) -> bool:
    """True when the adapter could not prove the worker's run finished its work.

    AGY print mode can exit 0 while the agent's backgrounded commands are still
    running or were killed (#8502/#8503); the adapter then leads
    ``stderr_excerpt`` with a reason code — including when no transcript bound
    to this run exists to prove completion. Whatever that worker left in its
    worktree is unconfirmed, so it must never be auto-finalized as ``done``.
    """
    from agent_runtime.adapters.agy import AGY_INCOMPLETE_RUN_REASONS

    return _first_error_line(stderr_excerpt) in AGY_INCOMPLETE_RUN_REASONS


# Children that exit on their own right after the CLI (a stdio MCP server
# reading EOF) get this long before they count as background jobs.
_BACKGROUND_JOBS_SETTLE_S = 5.0


def _worker_process_reader() -> worker_leftovers.ProcessReader:
    """Seam for tests: the live ``/proc`` and cgroup reader."""
    return worker_leftovers.ProcFsReader()


def _background_jobs_at_exit(state: Mapping[str, Any], *, task_id: str) -> worker_leftovers.ExitScan | None:
    """Whether processes of this worker outlived its CLI (#8991); None when not checked.

    Runs inside the detached worker, so only records carrying the
    ``launch_mode`` that spawn wrote are checked: a foreground or test run has
    no scope or session of its own to inspect. The scope's ``cgroup.procs``
    (or, on the Popen fallback, the task's environment marker and the worker's
    session) bound the scan. A headless session cannot be woken by a
    background-task notification, so whatever is still running is unfinished
    work, and a scan that could not read everything it needed is ``unknown``,
    never ``clear``. Never raises.
    """
    launch_mode = state.get("launch_mode")
    if launch_mode not in {dispatch_isolation.LAUNCH_SCOPE, dispatch_isolation.LAUNCH_FALLBACK}:
        return None

    def recorded(key: str) -> str | None:
        value = state.get(key)
        return value if isinstance(value, str) and value else None

    scope = worker_leftovers.WorkerScope(
        task_id=task_id,
        launch_mode=str(launch_mode),
        unit=recorded("launch_unit") if launch_mode == dispatch_isolation.LAUNCH_SCOPE else None,
        run_nonce=recorded("run_nonce"),
    )
    try:
        reader = _worker_process_reader()
        scope = worker_leftovers.worker_scope_at_exit(
            task_id=task_id,
            launch_mode=str(launch_mode),
            launch_unit=recorded("launch_unit"),
            run_nonce=recorded("run_nonce"),
            reader=reader,
        )
        scan = worker_leftovers.exit_scan(scope, reader=reader, settle_s=_BACKGROUND_JOBS_SETTLE_S)
    except Exception as exc:
        scan = worker_leftovers.ExitScan(
            status=worker_leftovers.SCAN_UNKNOWN, scope=scope, error=f"{type(exc).__name__}: {exc}"[:300]
        )
    if scan.status == worker_leftovers.SCAN_UNKNOWN:
        print(
            f"[delegate] WARNING: background-job check could not read the worker scope: {scan.error}", file=sys.stderr
        )
    return scan


def _first_error_line(stderr_excerpt: str | None) -> str | None:
    """Return the first non-blank captured stderr line for task summaries."""
    if not stderr_excerpt:
        return None
    return next(
        (line.strip() for line in stderr_excerpt.splitlines() if line.strip()),
        None,
    )


def _emit_terminal_dispatch_event(
    *,
    task_id: str,
    agent: str,
    final_state: dict[str, Any],
    result: Any,
    fallback_prompt_chars: int,
) -> None:
    """Emit the central terminal dispatch event without affecting worker exit."""
    try:
        try:
            from telemetry.emit import emit_event
            from telemetry.pricing import compute_cost
        except ImportError:  # pragma: no cover - package import path
            from scripts.telemetry.emit import emit_event
            from scripts.telemetry.pricing import compute_cost

        usage_record = getattr(result, "usage_record", None)
        tokens = usage_record.get("tokens") if isinstance(usage_record, dict) else None
        substitution = final_state.get("substitution")
        if substitution is None and isinstance(usage_record, dict):
            substitution = usage_record.get("substitution")
        model = final_state.get("model")
        cost = compute_cost(
            str(model).strip() if model else None,
            tokens,
            agent=agent,
        )
        emit_event(
            "dispatch",
            {
                "task_id": task_id,
                "agent": agent,
                "model": model,
                "resolved_model": final_state.get("resolved_model"),
                "resolved_model_known": final_state.get("resolved_model_known"),
                "resolved_model_source": final_state.get("resolved_model_source"),
                "effort": final_state.get("effort"),
                "branch": final_state.get("worktree_branch"),
                "worktree": final_state.get("worktree_path"),
                "status": final_state.get("status"),
                "duration_s": final_state.get("duration_s"),
                "result_file": final_state.get("result_file"),
                "prompt_chars": final_state.get("prompt_chars", fallback_prompt_chars),
                "response_chars": final_state.get("response_chars"),
                "tokens": tokens,
                "substitution": substitution,
                "cost_usd": cost.cost_usd,
                "billing_model": cost.billing_model,
                "cost_provenance": cost.provenance,
                "tmp_bytes_freed": final_state.get("tmp_bytes_freed"),
                "tmp_reap_error": final_state.get("tmp_reap_error"),
            },
        )
    except Exception as exc:  # pragma: no cover - degraded mode only
        _logger.debug(
            "failed to emit terminal dispatch telemetry: %s: %s",
            type(exc).__name__,
            exc,
        )


def _dispatch_worker_identity_flags(args: argparse.Namespace, requested_harness: str | None) -> list[str]:
    """Flags ``cmd_dispatch`` copies onto the ``_worker`` argv.

    ``--harness`` selects the Kimi transport and ``--require-review-verdict``
    carries the review completion gate. Review-attempt MCP flags stay on the
    ``review_plan`` branch and are not part of this list.
    """
    flags: list[str] = []
    if requested_harness is not None:
        flags.extend(["--harness", requested_harness])
    if bool(getattr(args, "require_review_verdict", False)):
        flags.append("--require-review-verdict")
    return flags


def _run_worker(
    task_id: str,
    agent: str,
    prompt: str,
    mode: str,
    cwd_str: str,
    model: str | None,
    hard_timeout: int,
    silence_timeout: int = DEFAULT_SILENCE_TIMEOUT_S,
    effort: str | None = None,
    max_budget_usd: float | None = None,
    initial_response_timeout: int = DEFAULT_INITIAL_RESPONSE_TIMEOUT_S,
    keep_worktree: bool = False,
    provider: str | None = None,
    output_schema_path: str | None = None,
    output_schema_sha256: str | None = None,
    harness: str | None = None,
    runtime_tmp_root: str | None = None,
    runtime_tmp_namespace_root: str | None = None,
    run_nonce: str | None = None,
    require_review_verdict: bool = False,
    review_id: str | None = None,
    attempt_id: str | None = None,
    mcp_config_path: str | None = None,
    strict_mcp_config: bool = False,
    finalize_open_pr: bool = False,
) -> int:
    """Worker main loop. Invokes the runtime, updates the state file.

    Returns the process exit code to use: 0 on ok, 1 on any failure.
    The parent never sees this return code directly — it reads the
    state file instead — but returning it cleanly allows the process
    to show up correctly in ``ps`` and systemd-style supervisors if
    we ever wrap this in one.
    """
    # The worker is a second entry point: a worker argv built by hand or a
    # stale parent must not invoke a Kimi seat outside web, UI and backend
    # coding. It reads the task's owned paths in the tree it is about to run
    # in, then installs the worktree boundary (hooks and push block), before
    # any state write or invocation. A refusal goes to the caller only.
    kimi_refusal = _kimi_worker_refusal(
        task_id,
        agent=agent,
        model=model,
        mode=mode,
        cwd=Path(cwd_str),
        review=require_review_verdict or review_id is not None,
    )
    if kimi_refusal:
        print(f"❌ {kimi_refusal}", file=sys.stderr)
        return 1
    from scripts.agent_runtime.kimi_admission import OWNED_PATHS_KEY, is_kimi_seat

    # Install SIGTERM handler so `delegate.py cancel` unwinds cleanly
    # through the runtime's finally block (see handler docstring).
    signal.signal(signal.SIGTERM, _worker_sigterm_handler)

    # Imports inside the function so the CLI startup path stays fast
    # and doesn't pay the cost of loading the runtime on 'status' calls.
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    from agent_runtime.errors import (
        AgentRuntimeError,
        AgentStalledError,
        AgentTimeoutError,
        RateLimitedError,
    )
    from agent_runtime.runner import invoke as runtime_invoke
    from agent_runtime.telemetry import resolve_dispatch_start_telemetry

    state_path = _state_path(task_id)

    # Update state to include our actual PID. The parent wrote an
    # initial state before forking; we overwrite with the real one
    # (in case the parent's guess was off, or we were re-exec'd).
    state = _read_state(state_path) or {}
    state["pid"] = os.getpid()
    state["status"] = "running"
    state["max_budget_usd"] = max_budget_usd
    effective_nonce = run_nonce or os.environ.get("LU_RUNTIME_RUN_NONCE")
    if effective_nonce:
        state["run_nonce"] = effective_nonce
    if "cli_version" not in state:
        start_telemetry = resolve_dispatch_start_telemetry(
            agent_name=agent,
            requested_model=model,
            requested_effort=effort,
            harness=harness,
        )
        state.setdefault("model", start_telemetry.model)
        state.setdefault("effort", start_telemetry.effort)
        state.setdefault("cli_version", start_telemetry.cli_version)
    _write_state_atomic(state_path, state)

    cwd = Path(cwd_str)
    read_only_checkout_pre: dict[str, str] | None = None
    read_only_checkout_post: dict[str, str] | None = None
    task_records_pre: dict[str, str] | None = None
    read_only_snapshot_error: str | None = None
    task_records_snapshot_error: str | None = None
    read_only_mutation_paths: list[str] = []
    read_only_ignored_mutation_paths: list[str] = []
    # Set only after digest.json is on disk. Phase files stay until the
    # terminal record that names retention=digest has been written.
    clean_snapshots_to_discard: Path | None = None
    if mode == "read-only":
        read_only_checkout_pre, read_only_snapshot_error = _read_only_checkout_snapshot(cwd)
        task_records_pre, task_records_error = _read_only_task_record_snapshot(task_id)
        task_records_snapshot_error = task_records_error
        if read_only_snapshot_error is None:
            read_only_snapshot_error = task_records_error
        _write_read_only_snapshot_sidecar(task_id, "pre", read_only_checkout_pre)
        state["read_only_checkout_snapshot_error"] = read_only_snapshot_error
        _write_state_atomic(state_path, state)
    start = time.monotonic()
    ok_outcome = False
    stderr_excerpt = None
    response = ""
    returncode: int | None = None
    returncode_reason: str | None = None
    rate_limited = False
    timed_out = False
    result = None
    substitution: dict[str, Any] | None = None
    runtime_tmp_reap: dict[str, int | str | None] | None = None

    cancelled = False
    # ONE recovery region, spanning the runtime call itself through the moment
    # the outcome is on disk.
    #
    # Seven review rounds each found a different instruction-level gap — the
    # reaper, the checkpoint, a second signal, lease cleanup, the boundary right
    # after lease cleanup — and each fix guarded that gap and created the next
    # one, because the interval kept being cut into guarded and unguarded
    # halves. The gaps were not the bug; splitting the interval was. This region
    # is the whole interval, so there is no boundary left to land between.
    #
    # A cancellation during the runtime call records ``cancelled`` — accurate,
    # the worker really was stopped. A cancellation after it records the
    # outcome the worker reached. Either way the state file stops saying
    # "running" about a process that is gone, and the signal still propagates.
    # What remains uncoverable in-process is SIGKILL, which the dead-pid probe
    # in cmd_status/cmd_wait already reports.
    #
    # Nothing the fallback reads may be bound only inside this region: a handler
    # that raises UnboundLocalError fails exactly when it is needed. Every name
    # it touches is initialized above, including the runtime-outcome flags.
    # Read the persisted record BEFORE the region, not inside it. Starting the
    # fallback from {} meant an early interrupt atomically REPLACED the task
    # file — recording a terminal status while destroying task_id, pid, mode,
    # cwd and worktree metadata that status/wait/cleanup and the operator all
    # read. A terminal status with no context is not an improvement over a stale
    # running one. (Cross-family review of #5807, round nine.)
    final_state: dict[str, Any] = _read_state(state_path) or {}
    worktree_path = final_state.get("worktree_path")
    final_status = ""
    duration_s = time.monotonic() - start
    result_file: str | None = None
    dirty_on_exit: bool | None = None
    commits_ahead: int | None = None
    needs_finalize = False
    finalize_error: str | None = None
    no_deliverable = False
    no_deliverable_reason: str | None = None
    pre_spawn_failure = False
    delivery_declaration: dict[str, Any] | None = None
    auto_finalize: AutoFinalizeResult | None = None
    leftovers_scan: worker_leftovers.ExitScan | None = None
    leftovers_unconfirmed = False
    telemetry_settled = False
    rescue_status: str | None = None
    kimi_worker = is_kimi_seat(agent, model=model)
    kimi_content_refusal: str | None = None
    cursor_mcp_path: Path | None = None
    cursor_mcp_backup: bytes | None = None
    cursor_mcp_existed = False

    try:
        try:
            stdout_silence_timeout = silence_timeout if silence_timeout > 0 else None
            initial_probe = initial_response_timeout if initial_response_timeout > 0 else None
            tool_config: dict[str, Any] = {}
            if max_budget_usd is not None:
                tool_config["max_budget_usd"] = max_budget_usd
            if provider is not None:
                tool_config[RUNTIME_ROUTE_TOOL_CONFIG_KEY] = {"provider": provider}
            if output_schema_path is not None:
                tool_config["output_schema_path"] = output_schema_path
                tool_config["output_schema_sha256"] = output_schema_sha256
            if harness is not None:
                tool_config["harness"] = harness
            if mode == "read-only" and runtime_tmp_root is not None:
                tool_config["read_only_tmp_root"] = runtime_tmp_root
            if mcp_config_path is not None:
                tool_config["mcp_config_path"] = mcp_config_path
            if strict_mcp_config:
                tool_config["strict_mcp_config"] = True
                tool_config["mcp_server_names"] = ["sources"]
            if review_id is not None:
                tool_config["review_id"] = review_id
            if attempt_id is not None:
                tool_config["attempt_id"] = attempt_id
            if strict_mcp_config and review_id is not None and attempt_id is not None and agent == "claude":
                from scripts.agent_runtime.review_mcp import review_tools_allowed_csv

                tool_config["allowed_tools"] = review_tools_allowed_csv(agent)
            elif agent in {"claude", "grok", "grok-build"} and mode == "read-only":
                tool_config["reviewer_tools"] = True
            if (
                strict_mcp_config
                and review_id is not None
                and attempt_id is not None
                and mcp_config_path is not None
                and agent == "codex"
            ):
                # Codex has no --mcp-config: -c mcp_servers.* MERGES with global config, so
                # the attempt runs under its scoped CODEX_HOME (sibling of the .mcp.json)
                # with no daemon URL override, and is gated on the effective MCP set (#8517).
                from scripts.agent_runtime.review_mcp import (
                    codex_review_home_path,
                    verify_codex_review_launch,
                )

                tool_config["codex_home_override"] = str(codex_review_home_path(mcp_config_path))
                verify_codex_review_launch(
                    config_path=mcp_config_path,
                    cwd=cwd,
                    mode=mode,
                    model=model,
                    effort=effort,
                    task_id=task_id,
                    tool_config=tool_config,
                )
            if (
                strict_mcp_config
                and review_id is not None
                and attempt_id is not None
                and mcp_config_path is not None
                and agent == "agy"
            ):
                # agy has no per-invocation MCP flag and reads its servers from
                # $HOME/.gemini/config, so the attempt runs under its scoped home (sibling
                # of the .mcp.json) and is gated on the effective MCP set (#8617).
                from scripts.agent_runtime.review_mcp import (
                    agy_review_home_path,
                    verify_agy_review_launch,
                )

                tool_config["agy_home_override"] = str(agy_review_home_path(mcp_config_path))
                verify_agy_review_launch(
                    config_path=mcp_config_path,
                    cwd=cwd,
                    mode=mode,
                    model=model,
                    effort=effort,
                    task_id=task_id,
                    tool_config=tool_config,
                )
            if strict_mcp_config and agent == "cursor":
                cursor_mcp_path = cwd / ".cursor" / "mcp.json"
                if cursor_mcp_path.is_file():
                    cursor_mcp_existed = True
                    try:
                        cursor_mcp_backup = cursor_mcp_path.read_bytes()
                    except OSError as exc:
                        raise RuntimeError(f"failed to back up {cursor_mcp_path}: {exc}") from exc

            if strict_mcp_config and review_id is not None and attempt_id is not None and mcp_config_path is not None:
                # Last check before the path strings reach the launcher: re-walk the attempt
                # directory no-follow and owner-checked (#8652). It narrows, not closes, the window.
                from scripts.agent_runtime.review_mcp import verify_review_attempt_paths

                verify_review_attempt_paths(mcp_config_path)

            if is_kimi_seat(agent, model=model):
                # The runner and the adapters run the same gate on these paths and this tree.
                tool_config[OWNED_PATHS_KEY] = list(_declared_owned_paths(state.get("owned_paths")) or ())
            result = runtime_invoke(
                agent,
                prompt,
                mode=mode,
                cwd=cwd,
                model=model,
                task_id=task_id,
                session_id=None,  # Layer 3 is always fresh-session
                tool_config=tool_config,
                entrypoint="delegate",
                hard_timeout=hard_timeout,
                stdout_silence_timeout=stdout_silence_timeout,
                initial_response_timeout=initial_probe,
                effort=effort,
            )
            ok_outcome = result.ok
            response = result.response
            stderr_excerpt = result.stderr_excerpt
            returncode = result.returncode
            rate_limited = result.rate_limited
            substitution = getattr(result, "substitution", None)
        except KeyboardInterrupt as exc:
            # Raised by our SIGTERM handler (or by Ctrl+C in manual runs).
            # The runtime's finally block has already killed the CLI
            # subprocess and stopped the watchdog by the time we catch
            # this, so no extra cleanup is needed here. Mark as cancelled.
            cancelled = True
            stderr_excerpt = f"cancelled via SIGTERM or Ctrl+C: {exc}"[:500]
            returncode_reason = "worker interrupted before a terminal subprocess returncode was available"
        except RateLimitedError as exc:
            rate_limited = True
            stderr_excerpt = str(exc)[:500]
            returncode_reason = "runtime rejected the dispatch before a terminal subprocess returncode was available"
        except AgentStalledError as exc:
            timed_out = True
            substitution = getattr(exc, "substitution", None)
            if getattr(exc, "kind", "stall") == "initial_response_timeout":
                stderr_excerpt = (
                    f"initial_response_timeout fired after {exc.stall_timeout}s "
                    f"with no first observable startup activity "
                    f"(stdout, stderr, liveness file, or process-tree work): {exc} "
                    f"— raise it with --initial-response-timeout "
                    f"(current default {DEFAULT_INITIAL_RESPONSE_TIMEOUT_S}s)"
                )[:500]
            else:
                stderr_excerpt = (
                    f"stdout_silence_timeout fired after {exc.stall_timeout}s "
                    f"without watchdog activity: {exc} "
                    f"— raise it with --silence-timeout "
                    f"(current default {DEFAULT_SILENCE_TIMEOUT_S}s)"
                )[:500]
            returncode_reason = "runtime timeout raised before a terminal subprocess returncode was available"
        except AgentTimeoutError as exc:
            substitution = getattr(exc, "substitution", None)
            stderr_excerpt = (
                f"hard_timeout fired after {exc.hard_timeout}s: {exc} "
                f"— raise it with --hard-timeout "
                f"(current default {DEFAULT_HARD_TIMEOUT_S}s)"
            )[:500]
            returncode_reason = "runtime timeout raised before a terminal subprocess returncode was available"
        except AgentRuntimeError as exc:
            stderr_excerpt = f"runtime error: {type(exc).__name__}: {exc}"[:500]
            returncode_reason = "runtime exception did not expose a terminal subprocess returncode"
        except ValueError as exc:
            pre_spawn_failure = True
            stderr_excerpt = f"adapter rejected before spawn: {exc}"[:500]
            returncode_reason = "adapter rejected the dispatch before a process was spawned"
        except Exception as exc:
            # Last-ditch: don't crash the worker on an unexpected bug — we
            # need to update the state file or the parent will see us as
            # "crashed" forever.
            stderr_excerpt = f"worker unexpected: {type(exc).__name__}: {exc}"[:500]
            returncode_reason = "unexpected worker exception before a terminal subprocess returncode was available"
        finally:
            if cursor_mcp_path is not None:
                try:
                    if cursor_mcp_existed and cursor_mcp_backup is not None:
                        cursor_mcp_path.write_bytes(cursor_mcp_backup)
                    elif not cursor_mcp_existed and cursor_mcp_path.is_file():
                        cursor_mcp_path.unlink()
                except OSError as exc:
                    print(f"⚠️  failed to restore {cursor_mcp_path}: {exc}", file=sys.stderr)
            if runtime_tmp_root is not None or runtime_tmp_namespace_root is not None:
                # This cleanup runs AFTER the worker has finished but BEFORE the
                # guarded span below, and it catches Exception rather than the
                # KeyboardInterrupt a SIGTERM raises — so a cancel landing here used
                # to unwind out of _run_worker with no terminal status written.
                # Deferring the signal across the cleanup drops a cancel that has
                # nothing left to cancel (the work is already done) in exchange for
                # never losing the record that it was done. (Cross-family review of
                # #5807.) Cleanup stays in `finally` so an interrupt during the
                # runtime call itself still frees the lease.
                with _sigterm_deferred():
                    runtime_tmp_reap = _reap_runtime_tmp_lease(
                        runtime_tmp_root,
                        runtime_tmp_namespace_root,
                    )

        duration_s = time.monotonic() - start
        final_status = _classify_final_status(
            cancelled=cancelled,
            rate_limited=rate_limited,
            ok_outcome=ok_outcome,
            timed_out=timed_out,
        )

        # A successful runtime result must carry the completed child process's
        # return code.  Refuse to persist a misleading ``done``/null combination
        # if a future runner regression drops it; failures without a child code
        # retain a precise reason instead of inventing a number (#4837).
        if _apply_returncode_invariant(final_status, returncode) != final_status:
            final_status = _apply_returncode_invariant(final_status, returncode)
            ok_outcome = False
            returncode_reason = "runtime reported success without a terminal subprocess returncode"
            stderr_excerpt = "runtime reported success without a terminal subprocess returncode"
        elif returncode is None and returncode_reason is None:
            returncode_reason = "no terminal subprocess returncode was available"
        if returncode is not None and returncode < 0 and returncode_reason is None:
            # Python reports signal deaths as negative returncodes. Decode the
            # signal so a SIGKILLed worker persists as SIGKILL, not an opaque
            # -9 (#7124).
            signum = -returncode
            try:
                signal_name = signal.Signals(signum).name
            except ValueError:
                signal_name = f"signal {signum}"
            returncode_reason = f"worker subprocess terminated by {signal_name} (returncode {returncode})"

        final_state = _read_state(state_path) or {}
        final_state["require_review_verdict"] = require_review_verdict
        final_state["review_verdict_failure"] = None
        if strict_mcp_config:
            final_state["worktree_disallow_reuse"] = True

        # A headless worker that ended its turn while its own background jobs
        # still run has not finished (#8991): record them before anything
        # reads the worktree, so no finalize step treats it as settled. A scan
        # that could not prove nothing is left counts the same way.
        if not pre_spawn_failure:
            leftovers_scan = _background_jobs_at_exit(final_state, task_id=task_id)
        if leftovers_scan is not None:
            final_state.update(leftovers_scan.record_fields())
            leftovers_unconfirmed = leftovers_scan.unconfirmed

        if (
            strict_mcp_config
            and review_id is not None
            and attempt_id is not None
            and mcp_config_path is not None
            and agent == "agy"
        ):
            from scripts.agent_runtime.review_mcp import agy_oauth_link_problem

            link_problem = agy_oauth_link_problem(mcp_config_path)
            if link_problem is not None:
                # Never copy credentials back automatically: both files stay as they
                # are for the operator, and the attempt cannot settle as done (#8617).
                final_state["agy_oauth_link_error"] = "agy_oauth_link_replaced"
                stderr_excerpt = f"agy_oauth_link_replaced: {link_problem}\n{stderr_excerpt or ''}".strip()[:500]
                final_status = "failed"
                ok_outcome = False

        if mode == "read-only":
            read_only_checkout_post, post_snapshot_error = _read_only_checkout_snapshot(cwd)
            task_records_post, task_records_error = _read_only_task_record_snapshot(task_id, task_records_pre)
            if task_records_snapshot_error is None:
                task_records_snapshot_error = task_records_error
            if post_snapshot_error is None:
                post_snapshot_error = task_records_error
            _write_read_only_snapshot_sidecar(task_id, "post", read_only_checkout_post)
            if read_only_snapshot_error is None and post_snapshot_error is not None:
                read_only_snapshot_error = post_snapshot_error
            final_state["read_only_checkout_snapshot_error"] = read_only_snapshot_error
            if read_only_checkout_pre is not None and read_only_checkout_post is not None:
                read_only_ignored_mutation_paths = _read_only_ignored_mutation_paths(
                    read_only_checkout_pre,
                    read_only_checkout_post,
                )
                read_only_mutation_paths = _read_only_mutation_paths(
                    read_only_checkout_pre,
                    read_only_checkout_post,
                )
            if task_records_pre is not None and task_records_post is not None:
                read_only_mutation_paths = sorted(
                    set(read_only_mutation_paths)
                    | {
                        path
                        for path, fingerprint in task_records_post.items()
                        if fingerprint[0] != task_records_pre[path][0]
                    }
                )
            final_state["read_only_ignored_mutation_paths"] = read_only_ignored_mutation_paths
            final_state["read_only_mutation_paths"] = read_only_mutation_paths
            if read_only_snapshot_keep_full(read_only_mutation_paths, read_only_snapshot_error):
                final_state["read_only_snapshot_retention"] = _READ_ONLY_SNAPSHOT_RETENTION_FULL
            else:
                snapshot_dir = _read_only_snapshot_dir_for(task_id)
                stage_read_only_snapshot_digest(
                    snapshot_dir,
                    read_only_checkout_pre,
                    read_only_checkout_post,
                )
                final_state["read_only_snapshot_retention"] = _READ_ONLY_SNAPSHOT_RETENTION_DIGEST
                # Drop hydrated copies so the terminal record stays small even
                # while the phase files are still on disk.
                final_state.pop("read_only_checkout_pre", None)
                final_state.pop("read_only_checkout_post", None)
                clean_snapshots_to_discard = snapshot_dir
            if read_only_mutation_paths or task_records_snapshot_error:
                final_status = "failed"
                ok_outcome = False

        # Write the full response to a result file (may be large).
        if response:
            result_path = state_path.with_suffix(".result")
            try:
                result_path.write_text(response)
                result_file = str(result_path)
            except OSError:
                result_file = None

        # Fix 5 (#1476 AC 5): dispatch-finish telemetry — record whether the
        # worktree exited dirty so follow-up reviewers can see at a glance
        # that the dispatched agent left uncommitted changes behind.
        # Ownership is fixed at launch: only a worktree_path recorded with an
        # explicit ``worktree_reused: false`` was created by this dispatch. A
        # path derived from cwd below, or a legacy record without the flag,
        # has unknown ownership and settle will not remove it (#8610).
        reused_flag = final_state.get("worktree_reused")
        worktree_created_by_dispatch = (
            (reused_flag is False) if worktree_path and isinstance(reused_flag, bool) else None
        )
        if not worktree_path and final_state.get("cwd"):
            candidate_cwd = Path(final_state.get("cwd"))
            resolved_wt = _resolve_verified_worktree_path(candidate_cwd)
            if resolved_wt:
                worktree_path = str(resolved_wt)
                final_state["worktree_path"] = worktree_path

        if worktree_path:
            dirty_on_exit = _worktree_is_dirty(Path(worktree_path))

        # EVERYTHING from here to the state write is telemetry ABOUT a worker that
        # has already finished. None of it may prevent the terminal status from
        # being recorded: a task stuck at ``running`` with a dead pid is worse than
        # a task with unknown telemetry, because no settle-loop can ever wake on it
        # and the operator sees a job that appears to still be working. See the
        # 2026-07-25 incident where a vanished worktree crashed the count and hid a
        # dead dispatch for 52 minutes.
        try:
            # The dirty-worktree safety net must cover EVERY write-capable mode, not just
            # ``danger``. It was gated on ``danger`` alone, so a ``workspace-write``
            # dispatch that left finished work uncommitted settled as ``done`` — a real
            # failure reported as success. On 2026-07-25 three lanes did exactly that
            # (``timeouts-B3``, ``timeouts-B6``, ``timeouts-B4-orig``: dirty worktrees,
            # zero commits, ``status: done``) and 31 files of finished work were one agent
            # restart away from being lost. Detection now runs for the whole write-capable
            # set; the riskier auto-finalize action stays scoped to ``danger``, except for
            # Kimi, whose work delegate always commits after the content check below.
            if worktree_path and mode in _WRITE_CAPABLE_MODES:
                base_branch = str(final_state.get("worktree_base") or "main")
                base_ref = _commit_count_base_ref(Path(worktree_path), base_branch)
                commits_ahead = _count_commits_ahead(
                    Path(worktree_path),
                    base_ref,
                )
                # Kimi takes only plain text without Ukrainian content: a diff that breaks
                # that is refused before auto-finalize can stage or commit anything.
                if kimi_worker:
                    kimi_content_refusal = _kimi_diff_refusal(Path(worktree_path), base_ref, agent)
                # Fail CLOSED on BOTH unknowns — they are the same bug in two variables.
                #
                # ``_count_commits_ahead`` returns None when it cannot count, and
                # ``commits_ahead == 0`` silently skipped that case, which is how the B4
                # dispatch (commits_ahead=None, dirty_on_exit=True) still reported ``done``.
                #
                # ``_worktree_is_dirty`` can ALSO return None (OSError, or a non-zero
                # ``git status --porcelain``). A bare ``if dirty_on_exit`` treats that unknown
                # as falsy and skips the check entirely — failing OPEN in precisely the way
                # this fix exists to prevent. Caught in cross-family review of #5754, which
                # noted the asymmetry after the count half had been fixed.
                #
                # Neither unknown can prove the work was committed, so either one surfaces
                # the task for finalization rather than letting it settle as ``done``.
                # A worker cut off mid-work (#8502) leaves unfinished edits even
                # when it had pushed earlier commits: surface them, never ``done``.
                run_incomplete = _worker_run_incomplete(stderr_excerpt) or leftovers_unconfirmed
                if dirty_on_exit in (True, None) and (commits_ahead in (0, None) or run_incomplete):
                    needs_finalize = True

                # Catch committed-but-unpushed write dispatches (#7311):
                # A clean tree with local commits on the dispatch branch has commits_ahead >= 1
                # relative to base_ref (e.g. origin/main), but if those commits were never
                # pushed to the branch's remote tracking ref, the work has not left the machine.
                worktree_branch = final_state.get("worktree_branch")
                if isinstance(worktree_branch, str) and worktree_branch.strip():
                    normalized_branch = worktree_branch.strip()
                    if normalized_branch.startswith("refs/heads/"):
                        normalized_branch = normalized_branch.removeprefix("refs/heads/")
                    if normalized_branch.startswith("origin/"):
                        normalized_branch = normalized_branch.removeprefix("origin/")
                    containment = _load_worktree_containment()
                    if normalized_branch not in containment.PROTECTED_BRANCHES and not (
                        commits_ahead == 0 and dirty_on_exit is False
                    ):
                        unpushed_commits = _count_unpushed_commits(
                            Path(worktree_path),
                            normalized_branch,
                        )
                        if unpushed_commits is None or unpushed_commits > 0:
                            needs_finalize = True
                            if unpushed_commits is not None and unpushed_commits > 0:
                                rescue_status = "unpushed work - needs rescue"
                            elif commits_ahead != 0:
                                rescue_status = "unpushed state unknown - needs rescue"
                            if rescue_status:
                                finalize_error = rescue_status

                if (
                    needs_finalize
                    and rescue_status is None
                    and returncode == 0
                    and (mode == "danger" or kimi_worker)
                    and kimi_content_refusal is None
                    and not run_incomplete
                ):
                    if kimi_worker:
                        # The content check passed and the worker has exited: take the
                        # boundary down so delegate's own commit and push go through.
                        from scripts.agent_runtime import kimi_boundary

                        kimi_boundary.remove(Path(worktree_path), env=_sanitized_git_env())
                    auto_finalize = _auto_finalize_dirty_worktree(
                        worktree=Path(worktree_path),
                        task_id=task_id,
                        agent=agent,
                        branch=final_state.get("worktree_branch"),
                        base_branch=base_branch,
                        open_pr=finalize_open_pr,
                        owned_paths=final_state.get("owned_paths"),
                    )
                    dirty_on_exit = _worktree_is_dirty(Path(worktree_path))
                    commits_ahead = _count_commits_ahead(Path(worktree_path), base_ref)
                    if auto_finalize.ok and not auto_finalize.skipped_paths:
                        needs_finalize = False
                        ok_outcome = True
                        final_status = "done"
                    elif auto_finalize.ok:
                        # Owned work is committed and pushed, but changes outside
                        # the owned paths are still in the tree: a human decides.
                        finalize_error = (
                            f"{len(auto_finalize.skipped_paths)} changed path(s) outside the owned paths "
                            "left uncommitted (finalize_skipped_paths)"
                        )
                    elif auto_finalize.error == _NO_DELIVERABLE_JUNK_ONLY_WORKTREE_REASON:
                        # A dirty tree with only known scratch residue has no
                        # user-visible deliverable. Refuse before staging so it
                        # cannot create a branch, push, or public PR.
                        needs_finalize = False
                        no_deliverable = True
                        no_deliverable_reason = _NO_DELIVERABLE_JUNK_ONLY_WORKTREE_REASON
        # Deliberately broad: this is measurement about a worker that has already
        # finished, and no measurement failure may cost the task its terminal status.
        except Exception as finalize_exc:
            finalize_error = f"{type(finalize_exc).__name__}: {finalize_exc}"[:300]
            # Unknown telemetry cannot prove the work was committed, so surface
            # the task for a human instead of settling it as done.
            needs_finalize = True
        # Live background jobs, or a scan that could not rule them out, make any
        # run unconfirmed (#8991), read-only included, even when its tree is
        # clean and pushed: the jobs may still be producing the result.
        if leftovers_unconfirmed:
            needs_finalize = True
        # Either way the verdict is now measured rather than assumed, so an
        # interrupt below must persist it as-is instead of forcing attention
        # onto a dispatch already shown to be clean and committed.
        telemetry_settled = True

        # A write-capable dispatch that settled ``done`` must have SOME
        # verifiable deliverable. The signal is inferred from observable
        # facts — own-branch commits, worktree state, response size — never
        # from a formatting contract on the worker's final message, so a
        # worker needs no magic phrase to count as successful. A structured
        # ``DELIVERABLE:`` line is honoured as an optional positive signal.
        # Read-only tasks are excluded: their deliverable may be analysis or
        # an external side effect such as a posted review comment.
        if (
            mode in _WRITE_CAPABLE_MODES
            and final_status == "done"
            and returncode == 0
            and not needs_finalize
            and no_deliverable_reason is None
        ):
            delivery_declaration = _parse_delivery_declaration(response)
            no_deliverable_reason = _delivery_failure_reason(
                response,
                delivery_declaration,
                commits_ahead=commits_ahead,
            )
            no_deliverable = no_deliverable_reason is not None

        # A review-typed dispatch (#8421) that settled ``done`` must actually
        # state a verdict. A reviewer that backgrounds its work and replies
        # with a promise to keep waiting exits 0 with an intent-only body; the
        # observable-facts rule above does not cover read-only review tasks, so
        # without this gate the false ``done`` reported success to ask-* review
        # drivers. Opt-in via ``--require-review-verdict`` (the ask-* review
        # wrapper only) — ordinary asks and implement dispatches are unchanged.
        if (
            require_review_verdict
            and final_status == "done"
            and returncode == 0
            and not needs_finalize
            and no_deliverable_reason is None
        ):
            review_verdict_failure = _review_verdict_failure_reason(response)
            if review_verdict_failure is not None:
                final_state["review_verdict_failure"] = review_verdict_failure
                final_status = "failed"
                ok_outcome = False
                stderr_excerpt = review_verdict_failure

        if pre_spawn_failure:
            needs_finalize = False
            final_status = "failed"
            ok_outcome = False
        elif kimi_content_refusal:
            # Nothing was committed for the worker; its changes stay in the tree.
            needs_finalize = False
            final_status = "failed"
            ok_outcome = False
            final_state["kimi_content_refusal"] = kimi_content_refusal
            stderr_excerpt = f"{kimi_content_refusal}\n{stderr_excerpt}" if stderr_excerpt else kimi_content_refusal
        elif needs_finalize:
            final_status = "needs_finalize"
        elif no_deliverable:
            final_status = _NO_DELIVERABLE_STATUS
            ok_outcome = False

        last_error = _first_error_line(stderr_excerpt) if final_status != "done" else None
        if leftovers_scan is not None and leftovers_scan.reason and final_status == "needs_finalize":
            reason = leftovers_scan.reason
            last_error = f"{reason}; {last_error}" if last_error else reason
        if read_only_mutation_paths:
            mutation_diagnostic = "read-only checkout mutation detected: " + ", ".join(read_only_mutation_paths)
            # Never REPLACE a real failure with the guard diagnostic (#7124):
            # overwriting it hid the actual cause (e.g. a SIGKILLed worker's
            # stderr) behind the mutation list. The paths stay independently
            # queryable via ``read_only_mutation_paths`` either way.
            last_error = f"{last_error}; {mutation_diagnostic}" if last_error else mutation_diagnostic
        if task_records_snapshot_error:
            last_error = f"{last_error}; {task_records_snapshot_error}" if last_error else task_records_snapshot_error
        if no_deliverable_reason is not None:
            last_error = no_deliverable_reason

        # CHECKPOINT: persist the COMPLETE core outcome before any best-effort work.
        #
        # Everything below — worktree reaping, usage extraction, the enriched state
        # assembly — is enrichment, and any of it can raise: worktree reaping once
        # performed its import outside its own handler, so an unimportable reaper
        # module skipped the write entirely and stood the task back up as ``running``
        # with a dead pid. Ordering fixes that by construction, where wrapping each
        # statement would only hold until someone adds the next one.
        #
        # The checkpoint carries every field that defines the outcome, not just the
        # status: a watcher that sees ``done`` must not find null ``finished_at`` /
        # ``duration_s`` / ``result_file`` / ``returncode`` next to it, and if this
        # process dies mid-enrichment the surviving record must still be complete
        # and true. Only genuinely optional metadata (reap telemetry, usage record,
        # runtime model/effort/cli labels) is left to the second write.
        # (Both points from cross-family review of this PR.)
        core_terminal_state = _core_terminal_fields(
            status=final_status,
            duration_s=duration_s,
            response=response,
            result_file=result_file,
            stderr_excerpt=stderr_excerpt,
            returncode=returncode,
            returncode_reason=returncode_reason,
            dirty_on_exit=dirty_on_exit,
            commits_ahead=commits_ahead,
            needs_finalize=needs_finalize,
            finalize_error=finalize_error,
            last_error=last_error,
        )
        final_state["final_branch_head_commit"] = _resolve_sha(Path(worktree_path)) if worktree_path else None
        final_state["rescue_status"] = rescue_status
        _write_state_atomic(state_path, {**final_state, **core_terminal_state})
        if clean_snapshots_to_discard is not None:
            discard_read_only_snapshot_phases(clean_snapshots_to_discard)
            clean_snapshots_to_discard = None
    except BaseException as interrupt_exc:
        # Defer SIGTERM across the ENTIRE handler, not just its write. A second
        # cancel arriving while the fallback was still computing raised from
        # inside this `except` suite, which the same suite cannot catch — the
        # same boundary-between-guarded-spans mistake as the region itself, one
        # level down. (Cross-family review of #5807, round nine.)
        with _sigterm_deferred():
            # Honour a verdict the telemetry already reached; fail closed only
            # when the interrupt beat the measurement to it — and only for modes
            # that can leave work behind, so an interrupted read-only review is
            # not dressed up as a dispatch needing manual finalization — unless
            # its own background jobs may still be running (#8991).
            interrupted_needs_finalize = (
                needs_finalize if telemetry_settled else (mode in _WRITE_CAPABLE_MODES or leftovers_unconfirmed)
            )
            # The interrupt may have landed before classification ran, so derive
            # the outcome from the runtime flags rather than persisting an empty
            # status, and apply the same return-code invariant the normal path
            # enforces.
            interrupted_status = _apply_returncode_invariant(
                final_status
                or _classify_final_status(
                    cancelled=cancelled,
                    rate_limited=rate_limited,
                    ok_outcome=ok_outcome,
                    timed_out=timed_out,
                ),
                returncode,
            )
            if interrupted_needs_finalize:
                interrupted_status = "needs_finalize"
            _write_state_atomic(
                state_path,
                {
                    # final_state was read before the region, so this MERGES onto
                    # the real task record instead of replacing it...
                    **final_state,
                    "final_branch_head_commit": _resolve_sha(Path(worktree_path)) if worktree_path else None,
                    "rescue_status": rescue_status,
                    # ...and the outcome fields come from the same builder the
                    # checkpoint uses, so an interrupted run never persists a
                    # terminal status beside stale placeholder values.
                    **_core_terminal_fields(
                        status=interrupted_status,
                        duration_s=duration_s,
                        response=response,
                        result_file=result_file,
                        stderr_excerpt=stderr_excerpt,
                        returncode=returncode,
                        returncode_reason=returncode_reason,
                        dirty_on_exit=dirty_on_exit,
                        commits_ahead=commits_ahead,
                        needs_finalize=interrupted_needs_finalize,
                        finalize_error=(f"interrupted during finalize: {type(interrupt_exc).__name__}"),
                        last_error=(
                            no_deliverable_reason
                            or (_first_error_line(stderr_excerpt) if interrupted_status != "done" else None)
                        ),
                    ),
                },
            )
            if clean_snapshots_to_discard is not None:
                discard_read_only_snapshot_phases(clean_snapshots_to_discard)
                clean_snapshots_to_discard = None
        raise

    last_error = _first_error_line(stderr_excerpt) if final_status != "done" else None
    if no_deliverable_reason is not None:
        last_error = no_deliverable_reason
    if last_error:
        # Task logs capture this worker's stderr, while agent_runtime captures
        # the CLI child's stderr internally. Re-emit the excerpt so an
        # instant CLI failure is visible in both task state and its stderr log.
        print(stderr_excerpt, file=sys.stderr, flush=True)

    # Read-only checkout snapshots (read_only_checkout_pre/post) already ran
    # above. Reap only after that comparison.
    worktree_reap: dict[str, Any] | None = None
    if worktree_path and _should_reap_settled_worktree(
        mode=mode,
        keep_worktree=keep_worktree,
        final_status=final_status,
        returncode=returncode,
        dirty_on_exit=dirty_on_exit,
    ):
        worktree_reap = _settle_worktree_reap(
            Path(worktree_path),
            created_by_this_dispatch=worktree_created_by_dispatch,
            settling_task_id=task_id,
            task_record=final_state,
        )

    usage_record = getattr(result, "usage_record", None)
    result_substitution = getattr(result, "substitution", None)
    if result_substitution is not None:
        substitution = result_substitution
    if substitution is None and isinstance(usage_record, dict):
        substitution = usage_record.get("substitution")
    runtime_substitution = substitution
    substitution = _merge_agent_substitution(final_state.get("substitution"), runtime_substitution)
    cursor_model_state = _cursor_model_state(
        agent=agent,
        result=result,
        substitution=runtime_substitution if isinstance(runtime_substitution, dict) else None,
    )

    final_state.update(
        {
            # The core outcome was already checkpointed above; re-stating it here
            # keeps this write self-contained and idempotent — same values, so a
            # reader between the two writes never sees the status change.
            **core_terminal_state,
            "model": getattr(result, "model", final_state.get("model")),
            **cursor_model_state,
            **_deepseek_model_state(
                agent=agent,
                model=getattr(result, "model", final_state.get("model")),
            ),
            "effort": getattr(result, "effort", final_state.get("effort")),
            "cli_version": getattr(result, "cli_version", final_state.get("cli_version")),
            "substitution": substitution,
            "no_deliverable_reason": no_deliverable_reason,
            "delivery_declaration": delivery_declaration,
            "keep_worktree": keep_worktree,
            "worktree_reap": worktree_reap,
            "tmp_bytes_freed": (
                runtime_tmp_reap["tmp_bytes_freed"]
                if runtime_tmp_reap is not None
                else final_state.get("tmp_bytes_freed")
            ),
            "tmp_reap_error": (
                runtime_tmp_reap["tmp_reap_error"]
                if runtime_tmp_reap is not None
                else final_state.get("tmp_reap_error")
            ),
            "auto_finalize": (
                {
                    "ok": auto_finalize.ok,
                    "commit_sha": auto_finalize.commit_sha,
                    "pr_url": auto_finalize.pr_url,
                    "error": auto_finalize.error,
                    "changed_files": list(auto_finalize.changed_files),
                    "owned_paths": (list(auto_finalize.owned_paths) if auto_finalize.owned_paths is not None else None),
                    "owned_paths_declared": auto_finalize.owned_paths is not None,
                    "cross_boundary_moves": list(auto_finalize.cross_boundary_moves),
                }
                if auto_finalize is not None
                else None
            ),
        }
    )
    if auto_finalize is not None:
        final_state["finalize_skipped_paths"] = list(auto_finalize.skipped_paths)
    _write_state_atomic(state_path, final_state)
    if worktree_path:
        print(
            f"[delegate] final branch={final_state.get('worktree_branch')} "
            f"head={final_state.get('final_branch_head_commit') or 'unknown'} "
            f"rescue_status={final_state.get('rescue_status') or 'none'}",
            file=sys.stderr,
        )
    _emit_terminal_dispatch_event(
        task_id=task_id,
        agent=agent,
        final_state=final_state,
        result=result,
        fallback_prompt_chars=len(prompt),
    )

    # Post-worker primary-integrity sweep (#5803 follow-up): if THIS worker
    # touched the primary checkout, the drift is caught here while its
    # task_id/agent/pid are still known, so the drift event names the likely
    # actor. Diagnostic only: never switches the human's checkout. Runs after
    # final_state is persisted.
    try:
        try:
            from scripts.audit.check_primary_integrity import check_primary_integrity
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_primary_integrity import check_primary_integrity

        pi_ok, pi_message = check_primary_integrity(_REPO_ROOT, fix=False, tasks_dir=tasks_dir())
        if not pi_ok:
            _append_dispatch_event(
                "primary_integrity_post_worker",
                task_id=task_id,
                agent=agent,
                ok=pi_ok,
                detail=pi_message,
            )
    except Exception as pi_exc:
        print(
            f"[delegate] WARNING: primary-integrity post-worker sweep failed: {type(pi_exc).__name__}: {pi_exc}",
            file=sys.stderr,
        )

    # Post-worker node_modules-integrity sweep (#6818 follow-up): same shape
    # as the primary-integrity sweep above, but for the symlink conduit
    # `_provision_data_symlinks` opens into every worktree's node_modules.
    # ALERT-only — never blocks, never repairs; attributes this worker's
    # task_id/agent/pid while they're still known.
    try:
        try:
            from scripts.audit.check_node_modules_integrity import (
                check_node_modules_integrity,
            )
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_node_modules_integrity import check_node_modules_integrity

        nmi_ok, nmi_message = check_node_modules_integrity(_REPO_ROOT, tasks_dir=tasks_dir())
        if not nmi_ok:
            _append_dispatch_event(
                "node_modules_integrity_post_worker",
                task_id=task_id,
                agent=agent,
                ok=nmi_ok,
                detail=nmi_message,
            )
    except Exception as nmi_exc:
        print(
            f"[delegate] WARNING: node_modules-integrity post-worker sweep failed: {type(nmi_exc).__name__}: {nmi_exc}",
            file=sys.stderr,
        )

    # Post-worker venv-integrity sweep (#6830 follow-up): same shape as the
    # node_modules-integrity sweep above, but for an empty/broken primary
    # venv. ALERT-only — never blocks, never repairs; attributes this
    # worker's task_id/agent/pid while they're still known.
    try:
        try:
            from scripts.audit.check_venv_integrity import check_venv_integrity
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_venv_integrity import check_venv_integrity

        vi_ok, vi_message = check_venv_integrity(_REPO_ROOT, tasks_dir=tasks_dir())
        if not vi_ok:
            _append_dispatch_event(
                "venv_integrity_post_worker",
                task_id=task_id,
                agent=agent,
                ok=vi_ok,
                detail=vi_message,
            )
    except Exception as vi_exc:
        print(
            f"[delegate] WARNING: venv-integrity post-worker sweep failed: {type(vi_exc).__name__}: {vi_exc}",
            file=sys.stderr,
        )

    # Post-worker worktree-cleanup-integrity sweep (#6937 follow-up): same
    # shape as the venv-integrity sweep above, but for a dark/red scheduled
    # LaunchAgent. ALERT-only — never blocks, never reloads launchd.
    try:
        try:
            from scripts.audit.check_worktree_cleanup_integrity import (
                check_worktree_cleanup_integrity,
            )
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_worktree_cleanup_integrity import (
                check_worktree_cleanup_integrity,
            )

        wci_ok, wci_message = check_worktree_cleanup_integrity(_REPO_ROOT, tasks_dir=tasks_dir())
        if not wci_ok:
            _append_dispatch_event(
                "worktree_cleanup_integrity_post_worker",
                task_id=task_id,
                agent=agent,
                ok=wci_ok,
                detail=wci_message,
            )
    except Exception as wci_exc:
        print(
            f"[delegate] WARNING: worktree-cleanup-integrity post-worker sweep failed: "
            f"{type(wci_exc).__name__}: {wci_exc}",
            file=sys.stderr,
        )

    if timed_out:
        _append_dispatch_event(
            "dispatch_silence_timeout",
            task_id=task_id,
            agent=agent,
            model=final_state.get("model"),
            effort=final_state.get("effort"),
            cwd=str(cwd),
            pid=final_state.get("pid"),
            status=final_status,
            silence_timeout_s=silence_timeout,
            hard_timeout_s=hard_timeout,
            max_budget_usd=max_budget_usd,
            duration_s=round(duration_s, 3),
            stderr_excerpt=stderr_excerpt,
        )

    return 0 if ok_outcome and not needs_finalize and not no_deliverable else 1


def _record_worktree_prep_failure(
    *,
    task_id: str,
    run_nonce: str,
    attribution: Any,
    agent: str,
    mode: str,
    prompt: str,
    error: Exception | str,
    requested_model: str | None = None,
    requested_effort: str | None = None,
    requested_harness: str | None = None,
    lifecycle_carrier: Any = None,
    worktree_path: str | Path | None = None,
    worktree_branch: str | None = None,
    worktree_base_sha: str | None = None,
    worktree_base: str | None = None,
    agent_alias_note: str | None = None,
    output_schema_path: str | None = None,
    output_schema_sha256: str | None = None,
    keep_worktree: bool = False,
    hard_timeout: float | None = None,
    silence_timeout: float | None = None,
    initial_response_timeout: float | None = None,
    max_budget_usd: float | None = None,
    require_review_verdict: bool = False,
    returncode_reason: str = "worktree preparation failed",
    worktree_prep_cleanup: dict[str, Any] | None = None,
    worktree_prep: dict[str, Any] | None = None,
    substitution: dict[str, Any] | None = None,
) -> bool:
    """Persist a terminal failed task record when worktree provisioning is refused.

    Returns True when a record was written. Refuses to overwrite an existing
    running/spawning record (pre-write re-check closes the guard→write race),
    except this run's own admission hold or path-reservation record, whose
    admission snapshot it keeps. ``worktree_prep`` is that
    reservation and ``worktree_prep_cleanup`` what dispatch found and did
    after a failed ``git worktree add`` (#8663); each is recorded when given.
    """
    if str(_REPO_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    from agent_runtime.telemetry import resolve_dispatch_start_telemetry

    start_telemetry = resolve_dispatch_start_telemetry(
        agent_name=agent,
        requested_model=requested_model,
        requested_effort=requested_effort,
        harness=requested_harness,
    )
    now_iso = datetime.now(UTC).isoformat()
    error_str = str(error)
    wt_path_str = str(worktree_path) if worktree_path else None
    wt_layout = _classify_worktree_layout(Path(worktree_path)) if worktree_path else None
    failed_state: dict[str, Any] = {
        "task_id": task_id,
        "run_nonce": run_nonce,
        "repository": _resolve_dispatch_repository(_REPO_ROOT),
        "initiator": attribution.initiator,
        "attribution_source": attribution.source,
        "agent": agent,
        "model": start_telemetry.model,
        **_cursor_model_state(agent=agent, initial=True),
        **_deepseek_model_state(agent=agent, model=start_telemetry.model),
        "effort": start_telemetry.effort,
        "cli_version": start_telemetry.cli_version,
        "allow_merge": False,
        "require_review_verdict": require_review_verdict,
        "mode": mode,
        "cwd": wt_path_str or str(_REPO_ROOT),
        "worktree_path": wt_path_str,
        "worktree_branch": worktree_branch,
        "final_branch_head_commit": _resolve_sha(Path(worktree_path)) if worktree_path else None,
        "worktree_base_sha": worktree_base_sha,
        "worktree_base": worktree_base,
        "worktree_rebased": False,
        "worktree_reused": False,
        "worktree_layout": wt_layout,
        "worktree_sparse": None,
        "worktree_local_venv": None,
        "runtime_tmp_root": None,
        "tmp_bytes_freed": None,
        "tmp_reap_error": None,
        "keep_worktree": keep_worktree,
        "hard_timeout": hard_timeout,
        "silence_timeout": silence_timeout,
        "initial_response_timeout": initial_response_timeout,
        "max_budget_usd": max_budget_usd,
        "output_schema_path": output_schema_path,
        "output_schema_sha256": output_schema_sha256,
        "pid": None,
        "status": "failed",
        "started_at": now_iso,
        "finished_at": now_iso,
        "duration_s": 0.0,
        "prompt_chars": len(prompt) if prompt else 0,
        "response_chars": None,
        "result_file": None,
        "stderr_excerpt": f"{returncode_reason}: {error_str}"[:500],
        "returncode": None,
        "returncode_reason": returncode_reason,
        "last_error": _first_error_line(error_str) or error_str,
        "exit_code": None,
        "substitution": substitution,
        "agent_alias_note": agent_alias_note,
    }
    if requested_harness is not None:
        failed_state["harness"] = requested_harness
    if lifecycle_carrier is not None:
        failed_state["task_lifecycle"] = lifecycle_carrier
    if worktree_prep is not None:
        failed_state["worktree_prep"] = worktree_prep
    if worktree_prep_cleanup is not None:
        failed_state["worktree_prep_cleanup"] = worktree_prep_cleanup
    state_path = _state_path(task_id)
    existing = _read_state(state_path)
    if existing is not None and existing.get("status") in ("running", "spawning"):
        if not _is_own_provisional_record(existing, run_nonce):
            return False
        if isinstance(existing.get("admission"), dict):
            failed_state["admission"] = existing["admission"]
    _write_state_atomic(state_path, failed_state)
    return True


def _record_forward_failure(
    *,
    task_id: str,
    run_nonce: str,
    attribution: Any,
    agent: str,
    mode: str,
    prompt: str,
    error: Exception | str,
    requested_model: str | None = None,
    requested_effort: str | None = None,
    requested_harness: str | None = None,
    lifecycle_carrier: Any = None,
    worktree_path: str | Path | None = None,
    worktree_branch: str | None = None,
    worktree_base_sha: str | None = None,
    worktree_base: str | None = None,
    agent_alias_note: str | None = None,
    output_schema_path: str | None = None,
    output_schema_sha256: str | None = None,
    keep_worktree: bool = False,
    hard_timeout: float | None = None,
    silence_timeout: float | None = None,
    initial_response_timeout: float | None = None,
    max_budget_usd: float | None = None,
    require_review_verdict: bool = False,
    substitution: dict[str, Any] | None = None,
) -> bool:
    """Persist a terminal failed task record when VPS forward dispatch is refused."""
    return _record_worktree_prep_failure(
        task_id=task_id,
        run_nonce=run_nonce,
        attribution=attribution,
        agent=agent,
        mode=mode,
        prompt=prompt,
        error=error,
        requested_model=requested_model,
        requested_effort=requested_effort,
        requested_harness=requested_harness,
        lifecycle_carrier=lifecycle_carrier,
        worktree_path=worktree_path,
        worktree_branch=worktree_branch,
        worktree_base_sha=worktree_base_sha,
        worktree_base=worktree_base,
        agent_alias_note=agent_alias_note,
        output_schema_path=output_schema_path,
        output_schema_sha256=output_schema_sha256,
        keep_worktree=keep_worktree,
        hard_timeout=hard_timeout,
        silence_timeout=silence_timeout,
        initial_response_timeout=initial_response_timeout,
        max_budget_usd=max_budget_usd,
        require_review_verdict=require_review_verdict,
        returncode_reason="forward configuration failed",
        substitution=substitution,
    )


# ---------------------------------------------------------------------------
# Dispatch command — spawn detached worker
# ---------------------------------------------------------------------------


def _run_preflight_triage(args: argparse.Namespace, *, worktree_arg: str | None) -> int | None:
    """#8183: TypeSafe readiness triage before any worker is spawned.

    Returns the fast-fail exit code, or ``None`` to let dispatch proceed
    (pass, missing key, API/git failure — advisory, never blocks).
    """
    from scripts.typesafe import preflight_triage as pt

    if args.cwd:
        cwd = Path(args.cwd)
    elif worktree_arg and worktree_arg != "auto" and Path(worktree_arg).is_dir():
        cwd = Path(worktree_arg)
    else:
        cwd = Path.cwd()
    try:
        paths, diff = pt.collect_candidate(getattr(args, "preflight_base", None) or "origin/main", cwd)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"preflight-triage: could not resolve git diff ({type(exc).__name__}) — skipping.", file=sys.stderr)
        return None
    log_arg = getattr(args, "preflight_test_log", None)
    log_path = Path(log_arg) if log_arg else cwd / ".preflight-test.log"
    result = pt.run_preflight(paths, diff, pt.read_test_log(log_path), pt.load_api_key())
    print(result.message, file=sys.stderr)
    if not result.fast_fail:
        return None
    pt.record_fast_fail(args.task_id, result, tasks_dir().parent / "preflight_fast_fail.jsonl")
    return pt.FAST_FAIL_EXIT_CODE


# The short form rejects common file suffixes so source locations do not become issue repositories.
_DOR_ISSUE_RE = re.compile(
    r"(?<![\w/=])(?:"
    r"https://github\.com/(?P<url_repo>[\w.-]+/[\w.-]+)/issues/(?P<url_number>\d+)\b"
    r"|(?P<short_repo>[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/"
    r"(?!(?:[A-Za-z0-9._-]+\.(?i:md|markdown|py|pyi|rst|txt))#)"
    r"(?=[A-Za-z0-9._-]*[A-Za-z0-9_-]#)[A-Za-z0-9._-]+)"
    r"#(?P<short_number>\d+)\b(?![/\\])"
    r"|#(?P<number>\d+)\b)"
)


def _run_dor_preflight(
    prompt: str, allow_reason: str | None, *, dispatch_repo: str
) -> tuple[str | None, dict[str, Any] | None]:
    """Check each issue named by an implementation brief before dispatch side effects."""
    distinct: dict[tuple[str, int], tuple[str, int]] = {}
    for match in _DOR_ISSUE_RE.finditer(_strip_quoted_content(prompt)):
        repo = match.group("url_repo") or match.group("short_repo") or dispatch_repo
        if repo.casefold() == _CANONICAL_GITHUB_REPO.casefold():
            repo = _CANONICAL_GITHUB_REPO
        number = int(match.group("url_number") or match.group("short_number") or match.group("number"))
        distinct.setdefault((repo.casefold(), number), (repo, number))
    candidates = sorted(distinct.values(), key=lambda issue: (issue[1], issue[0].casefold()))
    if not candidates:
        return None, None
    warnings: dict[str, str] = {}
    issue_numbers: list[int] = []
    checker = _REPO_ROOT / "scripts" / "ci" / "check_issue_task_quality.py"
    issue_repositories: list[dict[str, Any]] = []
    for repo, number in candidates:
        label = str(number) if repo.casefold() == _CANONICAL_GITHUB_REPO.casefold() else f"{repo}#{number}"
        recorded = False
        try:
            issue = subprocess.run(
                ["gh", "api", f"repos/{repo}/issues/{number}"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            if issue.returncode:
                raise ValueError("issue lookup failed")
            issue_payload = json.loads(issue.stdout)
            if not isinstance(issue_payload, dict) or issue_payload.get("number") != number:
                raise ValueError("issue lookup must identify the requested number")
            if "pull_request" in issue_payload:
                continue
            issue_numbers.append(number)
            recorded = True
            if repo.casefold() != _CANONICAL_GITHUB_REPO.casefold():
                issue_repositories.append({"issue": number, "repo": repo})
            result = subprocess.run(
                [sys.executable, str(checker), "--issue", str(number), "--repo", repo, "--strict", "--json"],
                capture_output=True,
                text=True,
                timeout=75,
                check=False,
            )
            payload = json.loads(result.stdout)
            if not isinstance(payload, dict):
                raise ValueError("checker result must be an object")
            if result.returncode or payload.get("verdict") != "PASS":
                warnings[label] = ",".join(payload.get("missing") or ["checker_error"])
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError, TypeError, ValueError):
            if not recorded:
                issue_numbers.append(number)
                if repo.casefold() != _CANONICAL_GITHUB_REPO.casefold():
                    issue_repositories.append({"issue": number, "repo": repo})
            warnings[label] = "checker_error"
    if not issue_numbers:
        return None, None
    record: dict[str, Any] = {"issues": issue_numbers, "warnings": warnings}
    if issue_repositories:
        record["issue_repositories"] = issue_repositories
    if allow_reason is not None:
        record["allow_warn_reason"] = allow_reason
    if warnings and allow_reason is None:
        details = "; ".join(
            f"{('#' + label) if label.isdigit() else label}: {missing}" for label, missing in warnings.items()
        )
        return f"❌ DoR issue card WARN ({details}); fix the issue or pass --allow-dor-warn REASON", record
    return None, record


def cmd_dispatch(args: argparse.Namespace) -> int:
    """Spawn a detached worker and return immediately (stdout: `<task_id>\n<run_nonce>`)."""
    # The stack owns the worktree lock taken before create-or-attach. Dispatch
    # releases it once the task record is published; every earlier return or
    # exception releases it here (#8610). ``admission_holds`` drops an
    # admission hold that no later record replaced (#8717).
    with contextlib.ExitStack() as worktree_locks, contextlib.ExitStack() as admission_holds:
        return _dispatch(args, worktree_locks=worktree_locks, admission_holds=admission_holds)


def _dispatch(
    args: argparse.Namespace,
    *,
    worktree_locks: contextlib.ExitStack,
    admission_holds: contextlib.ExitStack,
) -> int:
    """Body of :func:`cmd_dispatch`; ``worktree_locks`` holds the worktree lock.

    ``admission_holds`` releases this run's admission hold on any return or
    exception before the task record replaces it.
    """
    from scripts.agent_runtime.attribution import resolve_invocation_attribution
    from scripts.orchestration.job_host_exec import (
        SshTransportError,
        decide_dispatch_placement,
        format_forward_config_refusal,
        forward_dispatch,
        notebook_fallback_after_forward,
    )

    # Captured before any later mutation of ``args`` (e.g. --pr resolving into
    # args.branch, a rejected --model cleared to None): the hash binds what was
    # literally parsed, not what dispatch later resolved it to (#8430 R3-A r8).
    dispatch_args_hash = dispatch_args_sha256(args)

    task_id = args.task_id
    run_nonce = getattr(args, "run_nonce", None) or os.environ.get("LU_RUNTIME_RUN_NONCE") or _generate_run_nonce()

    caller_task_id = os.environ.get("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "").strip()
    if caller_task_id:
        # Read-only: this runs before the Kimi gate, so it must not create the task directory.
        caller_state = _read_state_json(_state_path_no_create(caller_task_id))
        if caller_state is None or caller_state.get("mode") not in _WRITE_CAPABLE_MODES:
            print(
                f"❌ dispatch refused from task {caller_task_id!r}: "
                "read-only or unavailable parent task record cannot start a dispatch.",
                file=sys.stderr,
            )
            return 2

    try:
        attribution = resolve_invocation_attribution(
            explicit=getattr(args, "initiator", None),
            task_id=task_id,
        )
    except ValueError as exc:
        print(f"❌ invalid --initiator: {exc}", file=sys.stderr)
        return 2

    # Resolve before DoR: the first check runs before worktree setup (#9133).
    fleet_repo_key = getattr(args, "repo", None)
    try:
        from scripts.orchestration.fleet_repos import (
            FleetRepoError,
            fleet_repo_as_dict,
            resolve_fleet_repo,
        )
    except ImportError:  # pragma: no cover - flat script path
        from orchestration.fleet_repos import (  # type: ignore
            FleetRepoError,
            fleet_repo_as_dict,
            resolve_fleet_repo,
        )

    try:
        fleet_repo, target_repo_root = resolve_fleet_repo(fleet_repo_key, primary_root=_REPO_ROOT)
    except FleetRepoError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", fleet_repo.github):
        print(f"❌ --repo {fleet_repo.key!r} has no valid owner/name in fleet_repos", file=sys.stderr)
        return 2
    fleet_repo_meta = fleet_repo_as_dict(fleet_repo, target_repo_root)

    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    from agent_runtime.agent_identity import resolve_retired_agent_alias
    from agent_runtime.routes import is_retired_gpt56_model
    from agent_runtime.telemetry import resolve_dispatch_start_telemetry

    # Resolve the effective route first: --model, the retired-CLI alias and any budget
    # substitution (#8517: a review attempt never takes a substitute).
    review_attempt = getattr(args, "review_attempt", None)
    from scripts.agent_runtime.kimi_admission import is_kimi_seat

    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.ai_agent_bridge.routing_guard import (
        RoutingGuardError,
        assert_agent_routing_allowed,
        assert_model_routing_allowed,
    )

    try:
        assert_agent_routing_allowed(args.agent, context="delegate dispatch")
        assert_model_routing_allowed(getattr(args, "model", None), context="delegate dispatch --model")
    except RoutingGuardError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    if is_retired_gpt56_model(getattr(args, "model", None)):
        print(f"❌ retired GPT-5.6 model {args.model!r} is not a dispatch route", file=sys.stderr)
        return 2

    # Permanent CLI retirement (e.g. gemini→agy, operator 2026-08-18): resolve
    # BEFORE the budget guard and unconditionally — a hot/cool budget reading
    # for a retired lane is not proof its binary still exists (CodexBar showed
    # gemini ~99% remaining the same night `--agent gemini` failed with
    # `FileNotFoundError: 'gemini'`). --force-agent bypasses the budget guard,
    # not this — there is no CLI left to force.
    original_agent = args.agent
    original_model = getattr(args, "model", None)
    model_resolution: dict[str, Any] = {}
    agent_alias_note: str | None = None
    retired_target = resolve_retired_agent_alias(args.agent)
    requested_agent = args.agent
    if retired_target:
        if review_attempt:
            print(
                f"❌ review attempt refused: agent substitution from {args.agent} to {retired_target} (retired CLI) is not allowed (#8517)",
                file=sys.stderr,
            )
            return 2
        try:
            retired_model, retired_how = _resolve_substitution_model(retired_target, original_model)
        except BudgetGuardRefuseError as exc:
            print(f"❌ {exc}", file=sys.stderr)
            return 2
        _remember_agent_substitution(
            model_resolution,
            source="retired-cli",
            requested_agent=original_agent,
            requested_model=original_model,
            actual_agent=retired_target,
            actual_model=retired_model,
            how=retired_how,
        )
        agent_alias_note = f"NOTE: {requested_agent}→{retired_target} retired CLI"
        print(
            f"🔄 RETIRED CLI ALIAS: --agent {requested_agent} → {retired_target} "
            f"{_substitution_model_phrase(retired_model, retired_how, original_model)} "
            f"({agent_alias_note}; the {requested_agent} CLI is not installed/supported).",
            file=sys.stderr,
        )
        requested_agent = retired_target

    language_lane = _dispatch_is_language_lane(args)
    if language_lane and requested_agent not in _LANGUAGE_LANES:
        print(
            "❌ ROUTING REFUSED: LANGUAGE-LANES RULE (operator 2026-09-27): "
            f"--agent {requested_agent} cannot author, review, critique, settle, or judge "
            "Ukrainian language, culture, or heritage content; "
            "allowed lanes are claude, codex (GPT), and agy (Gemini).",
            file=sys.stderr,
        )
        return 2

    if _dispatch_check_budget_enabled(args) and not getattr(args, "force_agent", False):
        try:
            dispatch_agent = (
                _resolve_agent_with_budget_guard(
                    requested_agent,
                    provider="openrouter",
                    language_lane=language_lane,
                    requested_model=original_model,
                    model_resolution=model_resolution,
                    origin_agent=original_agent,
                )
                if getattr(args, "provider", None) == "openrouter"
                else _resolve_agent_with_budget_guard(
                    requested_agent,
                    language_lane=language_lane,
                    requested_model=original_model,
                    model_resolution=model_resolution,
                    origin_agent=original_agent,
                )
            )
        except BudgetGuardRefuseError as exc:
            print(f"❌ {exc}", file=sys.stderr)
            return 2
    else:
        dispatch_agent = requested_agent

    agent_substitution = _applied_agent_substitution(model_resolution, dispatch_agent)
    if dispatch_agent != original_agent and agent_substitution is None:
        try:
            chosen_model, chosen_how = _resolve_substitution_model(dispatch_agent, original_model)
        except BudgetGuardRefuseError as exc:
            print(f"❌ {exc}", file=sys.stderr)
            return 2
        _remember_agent_substitution(
            model_resolution,
            source="budget-guard",
            requested_agent=original_agent,
            requested_model=original_model,
            actual_agent=dispatch_agent,
            actual_model=chosen_model,
            how=chosen_how,
        )
        agent_substitution = model_resolution["record"]
    if agent_substitution is not None:
        args.model = agent_substitution["actual_model"]

    if language_lane and dispatch_agent not in _LANGUAGE_LANES:
        print(
            "❌ ROUTING REFUSED: LANGUAGE-LANES RULE (operator 2026-09-27): "
            f"effective --agent {dispatch_agent} is outside claude, codex (GPT), and agy (Gemini).",
            file=sys.stderr,
        )
        return 2

    # #8775: validate caller-supplied paths once, before the DoR check, PR
    # resolution, or anything else that can run an external command, and
    # before any use reaches a check, a subprocess cwd, a task record, or the
    # worker prompt. Every later step uses the resolved paths returned here,
    # never the caller's strings. An explicit --worktree PATH must stay inside
    # the dispatching agent's own dispatch subtree; --cwd keeps its documented
    # read-only-primary and sibling-repo flows. Read-only git lookups between
    # here and the worktree lock (the write-mode worktree check, the cursor
    # review check, --preflight-triage) may run git in the validated path; the
    # path is re-checked after the lock, before any step that changes it.
    worktree_arg = getattr(args, "worktree", None)
    validated_worktree: Path | None = None
    validated_cwd: Path | None = None
    if worktree_arg and worktree_arg != "auto":
        validated_worktree, path_error = _validate_explicit_worktree(
            worktree_arg,
            agent=resolve_retired_agent_alias(args.agent) or args.agent,
            repo_root=target_repo_root,
        )
        if path_error:
            print(path_error, file=sys.stderr)
            return 2
        worktree_arg = str(validated_worktree)
    if args.cwd:
        validated_cwd, path_error = _validate_caller_path("--cwd", args.cwd, resolve=_resolve_cwd_path)
        if path_error:
            print(path_error, file=sys.stderr)
            return 2
        args.cwd = str(validated_cwd)

    # The single Kimi gate runs on the effective route — after --model, the retired-CLI
    # alias and any budget substitution resolve, and on the validated paths — before any
    # other check that can run an external command, write a record, sweep runtime tmp,
    # archive a task or create a worktree. Owned paths are read in the tree the worker
    # starts from: a reused worktree on disk and at its commit, a new one at its creation
    # base commit (fetched and read with git plumbing). The worktree must start from
    # ``kimi_start_commit``; two checks below refuse one that does not.
    kimi_refusal, kimi_start_commit = _kimi_dispatch_gate(
        args,
        agent=dispatch_agent,
        repo_role=fleet_repo.role,
        target_repo_root=target_repo_root,
        validated_worktree=validated_worktree,
        validated_cwd=validated_cwd,
    )
    if kimi_refusal:
        print(f"❌ {kimi_refusal}", file=sys.stderr)
        return 2

    # Prompt is resolved early so forward failure records and sparse inference
    # have access to the raw prompt text.
    early_prompt: str | None = None
    if getattr(args, "prompt", None):
        early_prompt = str(args.prompt)
    elif getattr(args, "prompt_file", None):
        try:
            early_prompt = Path(args.prompt_file).read_text(encoding="utf-8")
        except OSError:
            early_prompt = None

    dor_reason = getattr(args, "allow_dor_warn", None)
    if dor_reason is not None:
        dor_reason = str(dor_reason).strip()
        if not dor_reason:
            print("❌ --allow-dor-warn requires a non-empty reason", file=sys.stderr)
            return 2
    dor_record: dict[str, Any] | None = None
    if early_prompt is not None and args.mode in {"workspace-write", "danger"}:
        dor_error, dor_record = _run_dor_preflight(early_prompt, dor_reason, dispatch_repo=fleet_repo.github)
        if dor_error:
            print(dor_error, file=sys.stderr)
            return 2

    task_id = args.task_id
    try:
        _validate_dispatch_effort(args.agent, getattr(args, "effort", None))
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    from scripts.ai_agent_bridge._agy import (
        GeminiChangedPathListError,
        gemini_review_verdict_dispatch_error,
        resolve_same_repo_pr_head,
    )

    pr_number = getattr(args, "pr", None)
    pinned_head = getattr(args, "pinned_head", None)
    if pr_number is not None:
        try:
            pr_branch, resolved_head = resolve_same_repo_pr_head(int(pr_number), repo_root=str(_REPO_ROOT))
        except GeminiChangedPathListError as exc:
            print(f"❌ could not resolve PR head: {exc}", file=sys.stderr)
            return 2
        supplied_head = str(pinned_head).strip().lower() if pinned_head else ""
        if supplied_head and supplied_head != resolved_head:
            print(
                f"❌ --pinned-head {pinned_head} is not PR #{pr_number} head {resolved_head}",
                file=sys.stderr,
            )
            return 2
        named_branch = getattr(args, "branch", None)
        if named_branch and named_branch != pr_branch:
            print(
                f"❌ --branch {named_branch!r} is not PR #{pr_number} head {pr_branch!r}",
                file=sys.stderr,
            )
            return 2
        if supplied_head and not named_branch:
            print(
                f"❌ --pr {pr_number} with --pinned-head requires --branch {pr_branch!r}",
                file=sys.stderr,
            )
            return 2
        pinned_head = resolved_head
        args.branch = pr_branch
        args.pinned_head = pinned_head

    gemini_checked_heads: list[str] = []
    gemini_review_error = gemini_review_verdict_dispatch_error(
        agent=str(args.agent),
        require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
        profile=getattr(args, "review_profile", None),
        pr_number=pr_number,
        branch=getattr(args, "branch", None),
        repo_root=str(_REPO_ROOT),
        model=original_model,
        review=bool(getattr(args, "review", False))
        or str(getattr(args, "type", "") or "").strip().casefold() == "review",
        head_out=gemini_checked_heads,
        head_sha=pinned_head,
    )
    if gemini_review_error is not None:
        print(f"❌ {gemini_review_error}", file=sys.stderr)
        return 2
    try:
        requested_harness = _resolve_dispatch_harness(args.agent, getattr(args, "harness", None))
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    force_admission_reason = getattr(args, "force_admission", None)
    if force_admission_reason is not None:
        force_admission_reason = str(force_admission_reason).strip()
        if not force_admission_reason:
            print("❌ --force-admission requires a non-empty reason", file=sys.stderr)
            return 2

    review_id = getattr(args, "review_id", None)
    attempt_id = getattr(args, "attempt_id", None)
    review_plan = None
    if review_attempt or review_id or attempt_id:
        if not (review_attempt and review_id and attempt_id):
            print(
                "❌ --review-attempt, --review-id, and --attempt-id must be used together",
                file=sys.stderr,
            )
            return 2
        manifest_path = Path(review_attempt)
        if not manifest_path.is_file():
            print(f"❌ review manifest file not found: {manifest_path}", file=sys.stderr)
            return 2

        effective_harness = requested_harness or args.agent
        from scripts.agent_runtime.review_mcp import (
            SUPPORTED_HARNESSES,
            UNSUPPORTED_HARNESS_REASONS,
        )

        if effective_harness in UNSUPPORTED_HARNESS_REASONS:
            print(
                f"❌ review attempt refused for {args.agent}: {UNSUPPORTED_HARNESS_REASONS[effective_harness]} (#8517)",
                file=sys.stderr,
            )
            return 2
        if effective_harness not in SUPPORTED_HARNESSES:
            print(
                f"❌ review attempt refused for {args.agent}: unsupported harness {effective_harness!r} (#8517)",
                file=sys.stderr,
            )
            return 2

    invalid_owned_paths = _owned_path_errors(getattr(args, "owned_path", None))
    if invalid_owned_paths:
        print(
            "❌ --owned-path must be a repo-relative path or narrow glob (not empty, '.', absolute, "
            "a '..' segment, or a glob starting with a wildcard): "
            + ", ".join(repr(value) for value in invalid_owned_paths),
            file=sys.stderr,
        )
        return 2

    requested_branch = getattr(args, "branch", None)
    full_checkout = bool(getattr(args, "full_checkout", False))
    try:
        sparse_include = _infer_sparse_include(
            getattr(args, "sparse_include", None),
            owned_paths=getattr(args, "research_owned_path", None),
            prompt_text=early_prompt,
        )
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1
    if early_prompt is not None:
        write_intent_error = _read_only_write_intent_error(
            mode=args.mode,
            prompt=early_prompt,
        )
        if write_intent_error:
            print(write_intent_error, file=sys.stderr)
            return 2
    state_path = _state_path(task_id)
    silence_timeout = getattr(args, "silence_timeout", DEFAULT_SILENCE_TIMEOUT_S)
    initial_response_timeout = getattr(
        args,
        "initial_response_timeout",
        DEFAULT_INITIAL_RESPONSE_TIMEOUT_S,
    )
    max_budget_usd = getattr(args, "max_budget_usd", None)
    keep_worktree = bool(getattr(args, "keep_worktree", False))

    # Branch reuse always needs an isolated worktree.  A bare --branch uses
    # the normal dispatch subtree automatically; --cwd would otherwise make
    # it unclear which checkout must be validated.
    if requested_branch and not worktree_arg:
        worktree_arg = "auto"

    if args.cwd and worktree_arg:
        print(
            "❌ --cwd cannot be combined with --worktree or --branch. Use --worktree for delegated write isolation.",
            file=sys.stderr,
        )
        return 2

    # #672 P2.1: allowlisted --repo retargets worktree creation to a sibling
    # checkout. Control-plane task state stays on the public primary.
    if not fleet_repo.default and requested_branch:
        print(
            "❌ --branch attach on sibling --repo is not supported in P2.1; "
            "use --repo with bare --worktree for a fresh branch, or the manual --cwd flow.",
            file=sys.stderr,
        )
        return 2
    detached_read_only = args.mode == "read-only" and not worktree_arg and not args.cwd
    if detached_read_only:
        worktree_arg = "auto"

    if not fleet_repo.default and not worktree_arg and not args.cwd:
        print(
            "❌ sibling --repo requires --worktree (auto) or --cwd at an existing sibling worktree.",
            file=sys.stderr,
        )
        return 2

    # #6900: --worktree/--branch (and the default worker cwd) bind the target
    # checkout (public primary, or --repo sibling). Invoking from another git
    # root without --repo used to create the worktree in the primary while the
    # shell cwd said otherwise.
    cross_repo_error = _resolve_cross_repo_binding_error(
        worktree_arg=worktree_arg,
        cwd_arg=args.cwd,
        requested_branch=requested_branch,
        target_repo_root=target_repo_root,
    )
    if cross_repo_error:
        print(cross_repo_error, file=sys.stderr)
        return 2

    acp_runtime_error = _resolve_acp_runtime_target_error(
        worktree_arg=worktree_arg,
        cwd_arg=args.cwd,
        target_repo_root=target_repo_root,
    )
    if acp_runtime_error:
        print(acp_runtime_error, file=sys.stderr)
        return 2

    # Write-capable modes (workspace-write / danger) must resolve to a verified
    # added worktree — never the primary checkout (#4445). An explicit read-only
    # --cwd may still select the primary checkout. Evaluated before side effects.
    write_cwd_error = _resolve_write_cwd_error(
        mode=args.mode,
        worktree_arg=worktree_arg,
        cwd_arg=args.cwd,
    )
    if write_cwd_error:
        print(write_cwd_error, file=sys.stderr)
        return 2

    if getattr(args, "preflight_triage", False):
        preflight_rc = _run_preflight_triage(args, worktree_arg=worktree_arg)
        if preflight_rc is not None:
            return preflight_rc

    dirty_primary_error = _resolve_dirty_primary_checkout_error(mode=args.mode)
    if dirty_primary_error:
        print(dirty_primary_error, file=sys.stderr)
        return 2

    primary_integrity_error = _resolve_primary_integrity_error(mode=args.mode)
    if primary_integrity_error:
        print(primary_integrity_error, file=sys.stderr)
        return 2

    _warn_node_modules_integrity()
    _warn_venv_integrity()
    _warn_worktree_cleanup_integrity()

    _warn_if_monitor_api_unreachable()
    if bool(getattr(args, "dry_run", False)):
        print("🧹 runtime tmp orphan sweep: skipped=dry-run", file=sys.stderr)
    else:
        runtime_tmp_sweep = _sweep_runtime_tmp_orphans()
        print(
            "🧹 runtime tmp orphan sweep: "
            f"leases_reaped={runtime_tmp_sweep['leases_reaped']} "
            f"bytes_freed={runtime_tmp_sweep['bytes_freed']} "
            f"errors={runtime_tmp_sweep['errors']} "
            f"error_details={runtime_tmp_sweep['error_details']}",
            file=sys.stderr,
        )

    # #6980: fail closed when the task record (or its .result) already
    # exists in ANY state. The previous guard only refused live
    # running/spawning PIDs, so a dispatch with a completed task-id
    # silently overwrote batch_state/tasks/<id>.json + .result and
    # destroyed receipt evidence. Must run BEFORE ownership admission
    # so a rejected duplicate cannot DELETE/replace live write claims
    # (#5643 CF F001). --force-new archives only the caller's terminal
    # record; a dead pid does not make a nonterminal record safe to replace.
    existing = _read_state(state_path)
    record_exists = state_path.exists()
    result_exists = _result_path(task_id).exists()
    # An archived record still owns its task id (#8625): reuse needs --force-new,
    # which leaves the archived record where it is.
    archived_path = _archived_state_path(task_id)
    archived_exists = archived_path.is_file()
    if record_exists or result_exists or archived_exists:
        if not bool(getattr(args, "force_new", False)):
            if record_exists or result_exists:
                status = _existing_task_status(state_path, existing)
            else:
                existing = _read_state(archived_path)
                status = f"{_existing_task_status(archived_path, existing)} (archived)"
            pid = existing.get("pid") if existing else None
            pid_part = f" (pid={pid})" if pid not in (None, "") else ""
            print(
                f"❌ task_id {task_id!r} is already {status}{pid_part}. "
                "Dispatch refuses to reuse a task-id in any state. "
                "Use a unique --task-id; --force-new can archive only "
                "the caller's own terminal record+result.",
                file=sys.stderr,
            )
            return 2
        # Only the hot record establishes ownership. Archived siblings are
        # history and may belong to earlier runs by another initiator.
        prior_status = existing.get("status") if existing else None
        prior_initiator = existing.get("initiator") if existing else None
        if (record_exists or result_exists) and (
            prior_status not in _RUNTIME_TMP_TERMINAL_STATUSES
            or prior_initiator in (None, "unknown")
            or prior_initiator != attribution.initiator
        ):
            print(
                f"❌ task_id {task_id!r} cannot be reused with --force-new: "
                f"prior status {prior_status!r} must be terminal and prior initiator "
                f"{prior_initiator!r} must match a known caller {attribution.initiator!r}. "
                "The prior record and result were not archived.",
                file=sys.stderr,
            )
            return 2
        try:
            archived = _archive_task_artifacts(task_id)
        except OSError as exc:
            print(
                f"❌ failed to archive prior task artifacts for {task_id!r}: {exc}",
                file=sys.stderr,
            )
            return 1
        for dest in archived:
            print(f"📦 archived prior task artifact: {dest.name}", file=sys.stderr)

    # Resolve prompt: literal --prompt, or - for stdin, or --prompt-file.
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text()
    elif args.prompt == "-":
        prompt = sys.stdin.read()
    elif args.prompt is not None:
        prompt = args.prompt
    else:
        print("❌ --prompt or --prompt-file is required", file=sys.stderr)
        return 2
    # What the caller handed in, before the lifecycle, worktree and research blocks are appended: a caller that
    # rendered the prompt to a file (the R3 adjudication) checks the task ran exactly that file.
    source_prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    if review_attempt:
        # A prompt whose own attempt block (#8996) names different ids than this dispatch was told to use
        # would let the seat's return validate against the wrong receipt ledger; refuse before any side effect.
        from scripts.review.prompts.check import AttemptIdsUnreadableError, parse_attempt_ids

        try:
            prompt_review_id, prompt_attempt_id = parse_attempt_ids(prompt)
        except AttemptIdsUnreadableError as err:
            print(f"❌ review attempt refused: prompt_attempt_ids_unreadable: {err} (#8996)", file=sys.stderr)
            return 2
        if prompt_review_id is None or prompt_attempt_id is None:
            # A seat whose prompt names no ids can only guess them, and a guessed id never matches the
            # ledger this dispatch prepares — the failure #8996 was filed for.
            print(
                "❌ review attempt refused: prompt_attempt_ids_missing: a --review-attempt prompt must print "
                "the review_id and attempt_id its seat echoes (render it with --review-id/--attempt-id) (#8996)",
                file=sys.stderr,
            )
            return 2
        id_mismatches = [
            f"{name} prompt={found!r} dispatch={expected!r}"
            for name, found, expected in (
                ("review_id", prompt_review_id, review_id),
                ("attempt_id", prompt_attempt_id, attempt_id),
            )
            if found != expected
        ]
        if id_mismatches:
            print(
                "❌ review attempt refused: prompt_attempt_ids_mismatch: the prompt's attempt block ids differ "
                f"from --review-id/--attempt-id ({'; '.join(id_mismatches)}) (#8996)",
                file=sys.stderr,
            )
            return 2

    if args.mode in {"workspace-write", "danger"} and prompt != early_prompt:
        dor_error, dor_record = _run_dor_preflight(prompt, dor_reason, dispatch_repo=fleet_repo.github)
        if dor_error:
            print(dor_error, file=sys.stderr)
            return 2

    # stdin prompts were unavailable to the earlier side-effect-free check.
    write_intent_error = _read_only_write_intent_error(mode=args.mode, prompt=prompt)
    if write_intent_error:
        print(write_intent_error, file=sys.stderr)
        return 2

    try:
        lifecycle_carrier, lifecycle_prompt = _load_task_lifecycle_carrier(getattr(args, "lifecycle_file", None))
    except (OSError, ValueError) as exc:
        print(f"❌ invalid --lifecycle-file: {exc}", file=sys.stderr)
        return 2
    # Kinds of the blocks delegate adds around the caller's prompt, in the order they appear in the final prompt (the
    # worktree block leads it, the lifecycle and research blocks follow it); recorded so a consumer can tell which
    # instructions the worker saw beyond the source prompt.
    prompt_blocks: list[str] = []
    if lifecycle_prompt:
        prompt += lifecycle_prompt
        prompt_blocks.append("lifecycle")

    # ADR-011 P3 research context — explicit --research-* flags only. Validate the
    # request-side caps up front (fail fast, before any worktree side effect) so a
    # direct CLI caller is bounded exactly like the API query layer.
    try:
        research_ctx = _build_research_context(args)
    except ResearchContextError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    if dispatch_agent == "agy" and getattr(args, "model", None):
        from agent_runtime.adapters.agy import AgyAdapter

        try:
            AgyAdapter()._resolve_model_flag(str(args.model))
        except ValueError as exc:
            print(f"❌ {exc}", file=sys.stderr)
            return 2

    if review_attempt and dispatch_agent != requested_agent:
        print(
            f"❌ review attempt refused: agent substitution from {requested_agent} to {dispatch_agent} (budget guard) is not allowed (#8517)",
            file=sys.stderr,
        )
        return 2

    if review_attempt:
        from scripts.agent_runtime.review_mcp import (
            SUPPORTED_HARNESSES,
            UNSUPPORTED_HARNESS_REASONS,
        )

        final_harness = requested_harness or dispatch_agent
        if final_harness in UNSUPPORTED_HARNESS_REASONS:
            print(
                f"❌ review attempt refused for {dispatch_agent}: {UNSUPPORTED_HARNESS_REASONS[final_harness]} (#8517)",
                file=sys.stderr,
            )
            return 2
        if final_harness not in SUPPORTED_HARNESSES:
            print(
                f"❌ review attempt refused for {dispatch_agent}: unsupported harness {final_harness!r} (#8517)",
                file=sys.stderr,
            )
            return 2

        if dispatch_agent == "cursor" or requested_harness == "cursor":
            has_worktree = False
            if worktree_arg:
                has_worktree = True
            elif validated_cwd is not None:
                candidate_cwd = validated_cwd
                if _resolve_verified_worktree_path(candidate_cwd):
                    has_worktree = True
            if not has_worktree:
                print(
                    "❌ review attempt for cursor requires a dispatch worktree; refusing primary checkout (#8517)",
                    file=sys.stderr,
                )
                return 2

    from agent_runtime.telemetry import _resolve_model_from_defaults

    resolved_model = _resolve_model_from_defaults(
        dispatch_agent,
        getattr(args, "model", None),
        harness=requested_harness,
    )
    gemini_review_error = gemini_review_verdict_dispatch_error(
        agent=str(dispatch_agent),
        require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
        profile=getattr(args, "review_profile", None),
        pr_number=pr_number,
        branch=getattr(args, "branch", None),
        repo_root=str(_REPO_ROOT),
        model=getattr(args, "model", None),
        resolved_model=resolved_model,
        review=bool(getattr(args, "review", False))
        or str(getattr(args, "type", "") or "").strip().casefold() == "review",
        head_out=gemini_checked_heads,
        head_sha=getattr(args, "pinned_head", None) or pinned_head,
    )
    if gemini_review_error is not None:
        print(f"❌ {gemini_review_error}", file=sys.stderr)
        return 2

    try:
        _validate_dispatch_effort(dispatch_agent, getattr(args, "effort", None))
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    if requested_harness is not None and dispatch_agent != "kimi":
        print(
            "❌ --harness kimicc requires the effective dispatch agent to remain kimi; use --force-agent.",
            file=sys.stderr,
        )
        return 2

    _warn_kimicc_oauth_token_life(requested_harness, args.hard_timeout)

    try:
        _check_capacity_hint(dispatch_agent, args=args)
    except CapacityGuardRefuseError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    # Admission must precede placement forwarding: a VPS forward is itself a
    # spawn path, so a refused Cursor dispatch must never leave this process.
    if not bool(getattr(args, "dry_run", False)):
        placement, reason, host_id = decide_dispatch_placement(repo_root=_REPO_ROOT)
        if placement == "vps" and host_id:
            if review_attempt:
                print(
                    f"❌ review attempt refused: cannot forward to {host_id}; "
                    "the attempt ledger must stay on this host (#8517)",
                    file=sys.stderr,
                )
                return 2
            print(f"→ forwarding dispatch to {host_id} (run_nonce={run_nonce})", file=sys.stderr)
            forward_error: BaseException | None = None
            forward_rc: int | None = None
            try:
                forward_rc = forward_dispatch(
                    host_id=host_id,
                    argv=sys.argv,
                    initiator=attribution.initiator,
                    initiator_source=attribution.source,
                    run_nonce=run_nonce,
                )
            except SshTransportError as exc:
                forward_error = exc
            except (ValueError, FileNotFoundError, OSError) as exc:
                forward_error = exc
            if not notebook_fallback_after_forward(forward_rc, error=forward_error):
                if forward_error is not None:
                    _record_forward_failure(
                        task_id=task_id,
                        run_nonce=run_nonce,
                        attribution=attribution,
                        agent=getattr(args, "agent", "unknown"),
                        mode=getattr(args, "mode", "read-only"),
                        prompt=early_prompt or "",
                        error=forward_error,
                        requested_model=getattr(args, "model", None),
                        requested_effort=getattr(args, "effort", None),
                        requested_harness=getattr(args, "harness", None),
                        worktree_path=getattr(args, "worktree", None),
                        worktree_branch=getattr(args, "branch", None),
                        worktree_base=getattr(args, "base", None) or "main",
                        keep_worktree=bool(getattr(args, "keep_worktree", False)),
                        hard_timeout=getattr(args, "hard_timeout", DEFAULT_HARD_TIMEOUT_S),
                        silence_timeout=getattr(args, "silence_timeout", DEFAULT_SILENCE_TIMEOUT_S),
                        initial_response_timeout=getattr(
                            args, "initial_response_timeout", DEFAULT_INITIAL_RESPONSE_TIMEOUT_S
                        ),
                        max_budget_usd=getattr(args, "max_budget_usd", None),
                        require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
                        output_schema_path=getattr(args, "output_schema", None),
                        substitution=agent_substitution,
                    )
                    refusal_msg = format_forward_config_refusal(forward_error, host_id=host_id)
                    print(refusal_msg, file=sys.stderr)
                    return 2
                return int(forward_rc or 0)
            why = str(forward_error) if forward_error is not None else f"ssh rc {forward_rc}"
            print(
                f"⚠️  VPS forward failed ({why}); spawning on notebook",
                file=sys.stderr,
            )
        elif reason in {"unavailable", "full"}:
            print(f"⚠️  every VPS worker host is {reason}; spawning on notebook", file=sys.stderr)

    # Host admission (#8645 part A) for the host that spawns the worker, so it
    # follows VPS forwarding. This check fails fast before the base fetch; the
    # authoritative one runs under the admission lock just before the first
    # worktree or task-record side effect. Dry-run reports dead-pid records
    # without marking them.
    try:
        admission = _evaluate_dispatch_admission(args.mode, sweep=not bool(getattr(args, "dry_run", False)))
    except ValueError as exc:
        print(f"❌ invalid dispatch admission threshold: {exc}", file=sys.stderr)
        return 2
    admission_rc = _report_dispatch_admission(admission, force_reason=force_admission_reason)
    if admission_rc is not None:
        return admission_rc

    try:
        output_schema_path, output_schema_sha256 = _resolve_output_schema(
            getattr(args, "output_schema", None),
            agent=dispatch_agent,
        )
    except ValueError as exc:
        print(f"❌ invalid --output-schema: {exc}", file=sys.stderr)
        return 2

    # Resolve the immutable worktree base once before ownership admission.
    resolved_worktree_base_sha: str | None = None
    resolved_worktree_raw: str | None = None
    if worktree_arg and not (detached_read_only and bool(getattr(args, "dry_run", False))):
        resolved_worktree_raw = (
            str(_auto_worktree_path(dispatch_agent, task_id, repo_root=target_repo_root))
            if worktree_arg == "auto"
            else worktree_arg
        )
        try:
            if not bool(getattr(args, "dry_run", False)):
                # Attach is lock -> verify the checkout -> mutate -> publish the
                # task record. The lock is taken before _resolve_worktree_base_sha
                # can rebase an existing checkout and held until the record naming
                # the worktree is published, so no removal can land in between.
                # A removal that finished first leaves a missing path, which the
                # checks below treat as a fresh worktree (#8610).
                worktree_locks.enter_context(
                    worktree_lock(
                        validated_worktree
                        or _normalize_worktree_path(resolved_worktree_raw, repo_root=target_repo_root)
                    )
                )
            # #8775: an explicit path is locked as validated, then re-checked
            # before the base-SHA and worktree helpers run; they use it as is.
            changed_error = validated_worktree and _validated_path_changed_error("--worktree", validated_worktree)
            if changed_error:
                raise ValueError(changed_error.removeprefix("❌ "))
            if fleet_repo.default:
                resolved_worktree_base_sha = _resolve_worktree_base_sha(
                    agent=dispatch_agent,
                    task_id=task_id,
                    raw_path=resolved_worktree_raw,
                    validated_path=validated_worktree,
                    base=getattr(args, "base", None) or "main",
                    branch=requested_branch,
                    detached=detached_read_only,
                    # A Kimi worktree is never rebased: it must stay at the commit the gate read.
                    allow_rebase=not bool(getattr(args, "dry_run", False)) and kimi_start_commit is None,
                    pinned_head_sha=(
                        getattr(args, "pinned_head", None)
                        or (gemini_checked_heads[-1] if gemini_checked_heads else None)
                    ),
                )
            else:
                # Sibling repos resolve the base SHA at create time inside
                # _ensure_sibling_repo_worktree (simple origin fetch).
                resolved_worktree_base_sha = None
        except (ValueError, RuntimeError) as exc:
            if not bool(getattr(args, "dry_run", False)):
                _record_worktree_prep_failure(
                    task_id=task_id,
                    run_nonce=run_nonce,
                    attribution=attribution,
                    agent=dispatch_agent,
                    mode=args.mode,
                    prompt=prompt,
                    error=exc,
                    requested_model=args.model,
                    requested_effort=getattr(args, "effort", None),
                    requested_harness=requested_harness,
                    lifecycle_carrier=lifecycle_carrier,
                    worktree_path=resolved_worktree_raw,
                    worktree_branch=requested_branch,
                    worktree_base=getattr(args, "base", None) or "main",
                    agent_alias_note=agent_alias_note,
                    output_schema_path=output_schema_path,
                    output_schema_sha256=output_schema_sha256,
                    keep_worktree=keep_worktree,
                    hard_timeout=args.hard_timeout,
                    silence_timeout=silence_timeout,
                    initial_response_timeout=initial_response_timeout,
                    max_budget_usd=max_budget_usd,
                    require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
                    substitution=agent_substitution,
                )
            failed_step = "lock worktree" if isinstance(exc, WorktreeLockError) else "resolve immutable worktree base"
            print(f"❌ failed to {failed_step} for {task_id!r}: {exc}", file=sys.stderr)
            return 1

    # The base resolved under the worktree lock must be the commit the Kimi gate read.
    if kimi_start_commit is not None and worktree_arg and resolved_worktree_base_sha != kimi_start_commit:
        from scripts.agent_runtime.kimi_admission import format_refusal

        moved = f"the worktree base {resolved_worktree_base_sha} is not the commit {kimi_start_commit} its owned paths were read at"
        print(f"❌ {format_refusal(dispatch_agent, [moved + '; retry the dispatch'])}", file=sys.stderr)
        return 2

    # Writable-path admission guard (#5643 Δ2-A WARN; #5645 REFUSE later).
    # Runs before task-state write / worktree / branch side effects so a refuse
    # leaves no residue. Read-only modes are exempt inside the helper.
    # Dry-run must leave zero residue (same contract as tmp-lease reap) — skip
    # the shared ownership ledger entirely (Claude CF #5649 r11).
    if not bool(getattr(args, "dry_run", False)):
        try:
            from scripts.guardrails.delegate_ownership import (
                GuardMode,
                admit_write_paths,
                env_guard_mode,
            )
        except ImportError:  # pragma: no cover - flat script path
            from guardrails.delegate_ownership import (  # type: ignore
                GuardMode,
                admit_write_paths,
                env_guard_mode,
            )

        guard_mode = env_guard_mode()
        try:
            ownership = admit_write_paths(
                task_id=task_id,
                mode=str(args.mode),
                owned_paths=getattr(args, "research_owned_path", None),
                allow_path_overlap=getattr(args, "allow_path_overlap", None),
                pid=os.getpid(),
                guard_mode=guard_mode,
            )
        except Exception as own_exc:
            # WARN (opt-in via DELEGATE_OWNERSHIP_MODE=warn): never crash on ledger I/O.
            # REFUSE (default after #5645): fail closed so conflicts cannot proceed.
            print(
                f"⚠️  write-path ownership: ledger error: {own_exc}",
                file=sys.stderr,
            )
            if guard_mode == GuardMode.REFUSE:
                print(
                    f"❌ write-path ownership refused (ledger error) for task_id={task_id!r}",
                    file=sys.stderr,
                )
                return 2
        else:
            if ownership.would_refuse or ownership.override_reason:
                # Only report a conflict count when there ARE conflicts: an
                # unprovable-disjointness refusal has none, and printing
                # "conflicts=0" next to it reads as a guard bug (#5340-adjacent).
                suffix = f" (conflicts={len(ownership.conflicts)})" if ownership.conflicts else ""
                print(
                    f"⚠️  write-path ownership: {ownership.reason}{suffix}",
                    file=sys.stderr,
                )
            if not ownership.admitted:
                print(
                    f"❌ write-path ownership refused for task_id={task_id!r}: {ownership.reason}",
                    file=sys.stderr,
                )
                return 2

    if getattr(args, "dry_run", False):
        dry_run_worktree: Path | None = None
        dry_run_branch: str | None = None
        dry_run_worktree_telemetry: dict[str, Any] = {}
        if detached_read_only:
            # A dry-run describes the eventual checkout without fetching the
            # base or creating a worktree. Both can spawn git subprocesses.
            dry_run_worktree = _auto_worktree_path(dispatch_agent, task_id, repo_root=target_repo_root)
        elif requested_branch:
            resolved_raw = str(_auto_worktree_path(dispatch_agent, task_id)) if worktree_arg == "auto" else worktree_arg
            assert resolved_raw is not None  # --branch above supplies the auto sentinel.
            try:
                (
                    dry_run_worktree,
                    dry_run_branch,
                    dry_run_worktree_telemetry,
                ) = _ensure_worktree(
                    agent=dispatch_agent,
                    task_id=task_id,
                    raw_path=resolved_raw,
                    validated_path=validated_worktree,
                    base=getattr(args, "base", None) or "main",
                    branch=requested_branch,
                    detached=detached_read_only,
                    resolved_base_sha=resolved_worktree_base_sha,
                    dry_run=True,
                    full_checkout=full_checkout,
                    sparse_include=sparse_include,
                )
            except (ValueError, RuntimeError) as exc:
                print(f"❌ failed to validate branch reuse for {task_id!r}: {exc}", file=sys.stderr)
                return 1
        elif validated_cwd is not None:
            candidate_cwd = validated_cwd
            resolved_wt = _resolve_verified_worktree_path(candidate_cwd)
            if resolved_wt:
                dry_run_worktree = resolved_wt
                dry_run_branch = _current_branch(resolved_wt)
                dry_run_worktree_telemetry["base_sha"] = _resolve_sha(resolved_wt)

        try:
            runtime_tmp_root, runtime_tmp_namespace_root = _create_runtime_tmp_lease(task_id)
        except RuntimeError as exc:
            print(f"❌ failed to create runtime tmp lease for {task_id!r}: {exc}", file=sys.stderr)
            return 1

        try:
            start_telemetry = resolve_dispatch_start_telemetry(
                agent_name=dispatch_agent,
                requested_model=args.model,
                requested_effort=getattr(args, "effort", None),
                harness=requested_harness,
            )
            dry_run_state = {
                "task_id": task_id,
                "run_nonce": run_nonce,
                "repository": _resolve_dispatch_repository(
                    dry_run_worktree or (Path(args.cwd) if args.cwd else _REPO_ROOT)
                ),
                "initiator": attribution.initiator,
                "attribution_source": attribution.source,
                "agent": dispatch_agent,
                "model": start_telemetry.model,
                **_cursor_model_state(agent=dispatch_agent, initial=True),
                **_deepseek_model_state(agent=dispatch_agent, model=start_telemetry.model),
                "effort": start_telemetry.effort,
                "cli_version": start_telemetry.cli_version,
                "mode": args.mode,
                "cwd": str(dry_run_worktree or (Path(args.cwd) if args.cwd else _REPO_ROOT)),
                "worktree_path": str(dry_run_worktree) if dry_run_worktree else None,
                "worktree_branch": dry_run_branch,
                "worktree_base_sha": dry_run_worktree_telemetry.get("base_sha"),
                "runtime_tmp_root": str(runtime_tmp_root),
                "output_schema_path": output_schema_path,
                "output_schema_sha256": output_schema_sha256,
                "tmp_bytes_freed": None,
                "tmp_reap_error": None,
                "pid": None,
                "status": "dry_run",
                "started_at": datetime.now(UTC).isoformat(),
                "finished_at": None,
                "duration_s": None,
                "prompt_chars": len(prompt),
                "response_chars": None,
                "result_file": None,
                "stderr_excerpt": None,
                "returncode": None,
                "returncode_reason": None,
                "last_error": None,
                "exit_code": None,
                "substitution": agent_substitution,
                "agent_alias_note": agent_alias_note,
            }
            if requested_harness is not None:
                dry_run_state["harness"] = requested_harness
            if not admission.exempt:
                dry_run_state["admission"] = admission.to_record(force_reason=force_admission_reason)
            if lifecycle_carrier is not None:
                dry_run_state["task_lifecycle"] = lifecycle_carrier
            dry_run_reap = _reap_runtime_tmp_lease(
                runtime_tmp_root,
                runtime_tmp_namespace_root,
            )
            dry_run_state.update(
                {
                    "finished_at": datetime.now(UTC).isoformat(),
                    "duration_s": 0.0,
                    "tmp_bytes_freed": dry_run_reap["tmp_bytes_freed"],
                    "tmp_reap_error": dry_run_reap["tmp_reap_error"],
                }
            )
            _write_state_atomic(state_path, dry_run_state)
        except BaseException:
            _reap_runtime_tmp_lease(runtime_tmp_root, runtime_tmp_namespace_root)
            raise
        if requested_branch:
            print(
                f"🌲 branch reuse validated: branch={dry_run_branch} "
                f"path={dry_run_worktree} "
                f"base_sha={dry_run_worktree_telemetry.get('base_sha') or '?'} [reused]",
                file=sys.stderr,
            )
        print(task_id)
        print(run_nonce)
        return 0

    # Authoritative admission (#8645 part A, #8717): count → check → publish
    # the admission hold under one host-wide lock, so concurrent dispatches
    # cannot all pass the check above and then exceed the cap together. It
    # runs before the review attempt, log files, worktree and task record, so
    # a refusal leaves none of them. The hold names this dispatcher and keeps
    # the slot until the full task record replaces it before the spawn.
    admission_record: dict[str, Any] | None = None
    if not admission.exempt:
        admission_refusal: str | None = None
        try:
            with dispatch_admission.admission_lock(tasks_dir()):
                admission = _evaluate_dispatch_admission(args.mode, sweep=True, thresholds=admission.thresholds)
                if admission.admitted or force_admission_reason is not None:
                    admission_record = admission.to_record(force_reason=force_admission_reason)
                    _publish_admission_hold(task_id, run_nonce, mode=args.mode, admission=admission_record)
                    admission_holds.callback(_release_admission_hold, task_id, run_nonce)
                else:
                    admission_refusal = admission.refusal_line()
        except dispatch_admission.AdmissionLockTimeout as exc:
            admission_refusal = f"dispatch admission lock unavailable: {exc}; retry the dispatch"
        except (OSError, RuntimeError) as exc:
            print(f"❌ could not publish the admission hold for {task_id!r}: {exc}", file=sys.stderr)
            return 1
        if admission_refusal is not None:
            print(f"❌ {admission_refusal}", file=sys.stderr)
            return _ADMISSION_REFUSED_EXIT

    if review_attempt:
        from scripts.agent_runtime.review_mcp import prepare_review_attempt

        effective_harness = requested_harness or dispatch_agent
        try:
            review_plan = prepare_review_attempt(
                review_id=review_id,
                attempt_id=attempt_id,
                manifest_path=Path(review_attempt),
                harness=effective_harness,
            )
        except (ValueError, FileExistsError) as exc:
            print(f"❌ {exc}", file=sys.stderr)
            return 2

    # Set up log files before provisioning a worktree. If this cheap
    # filesystem setup fails, dispatch exits before leaving worktree/branch
    # side effects behind.
    log_dir = tasks_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = log_dir / f"{task_id}.stdout.log"
    stderr_log = log_dir / f"{task_id}.stderr.log"
    # task_id may contain "/" (for example "codex/1885-foo"), which makes
    # the log path live under a per-agent subdir that log_dir.mkdir above
    # does not cover.
    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    stderr_log.parent.mkdir(parents=True, exist_ok=True)
    # These file descriptors MUST outlive this function — Popen keeps
    # them open for the child process. A context manager would close
    # them the instant Popen returns, breaking the worker's output.
    # SIM115 doesn't understand this case.
    stdout_fd = open(stdout_log, "ab", buffering=0)  # noqa: SIM115
    stderr_fd = open(stderr_log, "ab", buffering=0)  # noqa: SIM115

    worktree_path: Path | None = None
    worktree_branch: str | None = None
    worktree_telemetry: dict[str, Any] = {}
    if worktree_arg:
        # Fix 4 (#1476): the sentinel ``auto`` (from bare ``--worktree``)
        # resolves to ``.worktrees/dispatch/{agent}/{task}/``. An explicit
        # path is the one resolved at validation (#8775).
        # #672 P2.1: sibling --repo roots the auto path under that checkout.
        resolved_raw = (
            str(_auto_worktree_path(dispatch_agent, task_id, repo_root=target_repo_root))
            if worktree_arg == "auto"
            else worktree_arg
        )
        try:
            # The worktree lock taken before base resolution is still held (#8610).
            changed_error = validated_worktree and _validated_path_changed_error("--worktree", validated_worktree)
            if changed_error:
                raise ValueError(changed_error.removeprefix("❌ "))
            if fleet_repo.default:
                worktree_path, worktree_branch, worktree_telemetry = _ensure_worktree(
                    agent=dispatch_agent,
                    task_id=task_id,
                    raw_path=resolved_raw,
                    validated_path=validated_worktree,
                    base=getattr(args, "base", None) or "main",
                    branch=requested_branch,
                    detached=detached_read_only,
                    resolved_base_sha=resolved_worktree_base_sha,
                    full_checkout=full_checkout,
                    sparse_include=sparse_include,
                    run_nonce=run_nonce,
                )
            else:
                worktree_path, worktree_branch, worktree_telemetry = _ensure_sibling_repo_worktree(
                    repo_root=target_repo_root,
                    agent=dispatch_agent,
                    task_id=task_id,
                    raw_path=resolved_raw,
                    validated_path=validated_worktree,
                    base=getattr(args, "base", None) or "main",
                    run_nonce=run_nonce,
                    detached=detached_read_only,
                )
                if fleet_repo_meta is not None:
                    worktree_telemetry["fleet_repo"] = fleet_repo_meta
        except (ValueError, RuntimeError) as exc:
            stdout_fd.close()
            stderr_fd.close()
            # Record the resolved absolute path like every other writer (#8610);
            # a path that cannot even be resolved is kept verbatim. A validated
            # explicit path is recorded as validated, not resolved again (#8775).
            try:
                failed_worktree_path = str(
                    validated_worktree or _normalize_worktree_path(resolved_raw, repo_root=target_repo_root)
                )
            except (OSError, RuntimeError, ValueError):
                failed_worktree_path = resolved_raw
            _record_worktree_prep_failure(
                task_id=task_id,
                run_nonce=run_nonce,
                attribution=attribution,
                agent=dispatch_agent,
                mode=args.mode,
                prompt=prompt,
                error=exc,
                requested_model=args.model,
                requested_effort=getattr(args, "effort", None),
                requested_harness=requested_harness,
                lifecycle_carrier=lifecycle_carrier,
                worktree_path=failed_worktree_path,
                worktree_branch=(
                    None if detached_read_only else requested_branch or _derive_worktree_branch(dispatch_agent, task_id)
                ),
                worktree_base_sha=resolved_worktree_base_sha,
                worktree_base=getattr(args, "base", None) or "main",
                agent_alias_note=agent_alias_note,
                output_schema_path=output_schema_path,
                output_schema_sha256=output_schema_sha256,
                keep_worktree=keep_worktree,
                hard_timeout=args.hard_timeout,
                silence_timeout=silence_timeout,
                initial_response_timeout=initial_response_timeout,
                max_budget_usd=max_budget_usd,
                require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
                substitution=agent_substitution,
                worktree_prep_cleanup=exc.cleanup if isinstance(exc, WorktreeAddFailed) else None,
                worktree_prep=exc.prep if isinstance(exc, WorktreeAddFailed) else None,
            )
            print(f"❌ failed to prepare worktree for {task_id!r}: {exc}", file=sys.stderr)
            if isinstance(exc, WorktreeAddFailed):
                print(
                    f"   worktree cleanup: {exc.cleanup.get('action')} — {exc.cleanup.get('reason')}",
                    file=sys.stderr,
                )
                if exc.cleanup.get("reserved_dir_left"):
                    print(
                        f"   reserved_dir_left: {exc.cleanup.get('path')} — left in place, never removed automatically",
                        file=sys.stderr,
                    )
                if exc.cleanup.get("needs_attention"):
                    print(
                        f"   needs_attention: {exc.cleanup['needs_attention']} — {exc.cleanup.get('command')}",
                        file=sys.stderr,
                    )
            return 1
    elif validated_cwd is not None:
        candidate_cwd = validated_cwd
        # #8775: the validated cwd is re-checked before the registered-worktree
        # lookup below and again under the lock. In write-capable modes (and
        # for a cursor review attempt) an earlier read-only lookup already ran
        # git in this path, before either re-check.
        changed_error = _validated_path_changed_error("--cwd", candidate_cwd)
        if changed_error:
            stdout_fd.close()
            stderr_fd.close()
            print(changed_error, file=sys.stderr)
            return 1
        resolved_wt = _resolve_verified_worktree_path(candidate_cwd)
        if resolved_wt:
            try:
                worktree_locks.enter_context(worktree_lock(resolved_wt))
            except WorktreeLockError as exc:
                stdout_fd.close()
                stderr_fd.close()
                print(f"❌ failed to lock worktree for {task_id!r}: {exc}", file=sys.stderr)
                return 1
            # A removal that held the lock may have taken the checkout while
            # this dispatch waited. Never fall back to the stale cwd: fail
            # before any task record is published or any worker spawned (#8610).
            # A symlink swapped in since validation is refused too (#8775).
            changed_error = _validated_path_changed_error("--cwd", candidate_cwd)
            if changed_error:
                stdout_fd.close()
                stderr_fd.close()
                print(changed_error, file=sys.stderr)
                return 1
            if _resolve_verified_worktree_path(candidate_cwd) != resolved_wt:
                stdout_fd.close()
                stderr_fd.close()
                print(
                    f"❌ worktree {resolved_wt} for {task_id!r} was removed while dispatch waited for its lock; "
                    f"refusing to spawn in {candidate_cwd}",
                    file=sys.stderr,
                )
                return 1
            try:
                _refuse_review_attempt_worktree_reuse(resolved_wt)
            except (OSError, ValueError, RuntimeError) as exc:
                stdout_fd.close()
                stderr_fd.close()
                print(f"❌ failed to reuse worktree for {task_id!r}: {exc}", file=sys.stderr)
                return 1
            worktree_path = resolved_wt
            worktree_branch = _current_branch(resolved_wt)
            worktree_telemetry["reused"] = True
            worktree_telemetry["layout"] = _classify_worktree_layout(resolved_wt)
            worktree_telemetry["base_sha"] = _resolve_sha(resolved_wt)
            worktree_telemetry["sparse"] = _apply_dispatch_sparse_checkout(
                resolved_wt,
                full_checkout=full_checkout,
                sparse_include=sparse_include,
            )
            _record_worktree_local_venv_warning(resolved_wt, worktree_telemetry)

    # A Kimi worker needs its own worktree, checked out at the commit the gate read. The
    # gate and the check above already hold this; this re-check under the worktree lock
    # catches a worktree changed meanwhile, before any task record, tmp lease or worker exists.
    if is_kimi_seat(dispatch_agent, model=getattr(args, "model", None)):
        from scripts.agent_runtime.kimi_admission import format_refusal

        kimi_head = _resolve_sha(worktree_path) if worktree_path is not None else None
        if kimi_head is None or (kimi_start_commit is not None and kimi_head != kimi_start_commit):
            stdout_fd.close()
            stderr_fd.close()
            where = f"is at {kimi_head}, not {kimi_start_commit}" if kimi_head else "is missing"
            print(f"❌ {format_refusal(dispatch_agent, [f'the worker worktree {where}'])}", file=sys.stderr)
            return 2

    if review_plan is not None and worktree_path is not None:
        try:
            _mark_review_attempt_worktree(worktree_path, task_id)
        except (OSError, RuntimeError) as exc:
            stdout_fd.close()
            stderr_fd.close()
            print(f"❌ failed to mark review worktree for {task_id!r}: {exc}", file=sys.stderr)
            return 1

    try:
        runtime_tmp_root, runtime_tmp_namespace_root = _create_runtime_tmp_lease(task_id)
    except RuntimeError as exc:
        stdout_fd.close()
        stderr_fd.close()
        _record_worktree_prep_failure(
            task_id=task_id,
            run_nonce=run_nonce,
            attribution=attribution,
            agent=dispatch_agent,
            mode=args.mode,
            prompt=prompt,
            error=exc,
            requested_model=args.model,
            requested_effort=getattr(args, "effort", None),
            requested_harness=requested_harness,
            lifecycle_carrier=lifecycle_carrier,
            worktree_path=worktree_path,
            worktree_branch=worktree_branch,
            worktree_base_sha=worktree_telemetry.get("base_sha") or resolved_worktree_base_sha,
            worktree_base=getattr(args, "base", None) or "main",
            agent_alias_note=agent_alias_note,
            output_schema_path=output_schema_path,
            output_schema_sha256=output_schema_sha256,
            keep_worktree=keep_worktree,
            hard_timeout=args.hard_timeout,
            silence_timeout=silence_timeout,
            initial_response_timeout=initial_response_timeout,
            max_budget_usd=max_budget_usd,
            require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
            substitution=agent_substitution,
        )
        print(f"❌ failed to create runtime tmp lease for {task_id!r}: {exc}", file=sys.stderr)
        return 1

    spawned = False
    try:
        cwd = str(worktree_path or (Path(args.cwd) if args.cwd else _REPO_ROOT))
        prompt = _augment_prompt_with_worktree(
            prompt,
            worktree_path,
            mode=args.mode,
            sparse_telemetry=worktree_telemetry.get("sparse")
            if isinstance(worktree_telemetry.get("sparse"), dict)
            else None,
            delegate_commits=is_kimi_seat(dispatch_agent, model=getattr(args, "model", None)),
        )
        if worktree_path is not None:
            prompt_blocks.insert(0, "worktree")

        # POINTERS ONLY: inject bounded research pointers + an on-demand fetch
        # instruction (never digest bodies) when an explicit context was supplied and
        # the registry is enabled. Fail-open — a disabled/malformed registry leaves the
        # prompt and state untouched.
        research_state: dict[str, Any] | None = None
        if research_ctx is not None:
            research_block, research_state = _resolve_research_injection(research_ctx, task_id)
            if research_block:
                prompt_blocks.append("research")
            prompt = prompt + research_block
        effective_prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        start_telemetry = resolve_dispatch_start_telemetry(
            agent_name=dispatch_agent,
            requested_model=args.model,
            requested_effort=getattr(args, "effort", None),
            harness=requested_harness,
        )

        # Write initial state BEFORE forking so a fast caller can see it.
        # pid is filled in by the worker once it starts; for now we record
        # the parent PID as a placeholder (overwritten by worker).
        worktree_layout = worktree_telemetry.get("layout") if worktree_path else None
        initial_state = {
            "task_id": task_id,
            "run_nonce": run_nonce,
            # Authoritative repository identity for the Work projection's scoped
            # delegate join (#7083); None stays unclassified and fails closed.
            "repository": _resolve_dispatch_repository(cwd),
            "initiator": attribution.initiator,
            "attribution_source": attribution.source,
            "agent": dispatch_agent,
            "model": start_telemetry.model,
            **_cursor_model_state(agent=dispatch_agent, initial=True),
            **_deepseek_model_state(agent=dispatch_agent, model=start_telemetry.model),
            "effort": start_telemetry.effort,
            "cli_version": start_telemetry.cli_version,
            "allow_merge": bool(getattr(args, "allow_merge", False)),
            "require_review_verdict": bool(getattr(args, "require_review_verdict", False)),
            "mode": args.mode,
            "cwd": cwd,
            "worktree_path": str(worktree_path) if worktree_path else None,
            "worktree_branch": worktree_branch,
            "worktree_base_sha": worktree_telemetry.get("base_sha"),
            "worktree_base": getattr(args, "base", None) or ("main" if worktree_path else None),
            "worktree_rebased": bool(worktree_telemetry.get("rebased")),
            "worktree_reused": bool(worktree_telemetry.get("reused")),
            "worktree_layout": worktree_layout,
            "worktree_sparse": worktree_telemetry.get("sparse"),
            "worktree_local_venv": worktree_telemetry.get("local_venv"),
            "runtime_tmp_root": str(runtime_tmp_root),
            "tmp_bytes_freed": None,
            "tmp_reap_error": None,
            "keep_worktree": keep_worktree,
            "hard_timeout": args.hard_timeout,
            "silence_timeout": silence_timeout,
            "initial_response_timeout": initial_response_timeout,
            "max_budget_usd": max_budget_usd,
            "output_schema_path": output_schema_path,
            "output_schema_sha256": output_schema_sha256,
            "prompt_sha256": source_prompt_sha256,
            "effective_prompt_sha256": effective_prompt_sha256,
            "prompt_blocks": prompt_blocks,
            "dispatch_args_sha256": dispatch_args_hash,
            "pid": None,  # worker fills this
            "status": "spawning",
            "started_at": datetime.now(UTC).isoformat(),
            "finished_at": None,
            "duration_s": None,
            "prompt_chars": len(prompt),
            "response_chars": None,
            "result_file": None,
            "stderr_excerpt": None,
            "returncode": None,
            "returncode_reason": None,
            "last_error": None,
            "exit_code": None,
            "substitution": agent_substitution,
            "agent_alias_note": agent_alias_note,
            "dor_preflight": dor_record,
        }
        if requested_harness is not None:
            initial_state["harness"] = requested_harness
        if lifecycle_carrier is not None:
            initial_state["task_lifecycle"] = lifecycle_carrier
        if review_plan is not None:
            initial_state["worktree_disallow_reuse"] = True
            # Binds this task to its review attempt (#9022): the recorder attests a return's prompt hash only
            # from the task whose record names the same review, attempt and manifest.
            initial_state["review_attempt"] = {
                "review_id": review_id,
                "attempt_id": attempt_id,
                "manifest_sha256": hashlib.sha256(Path(review_attempt).read_bytes()).hexdigest(),
            }
        initial_state = _with_optional_research_state(initial_state, research_state)
        # Auto-finalize's commit scope (#8991): the explicit --owned-path values,
        # verbatim. Never derived from --research-owned-path, which classifies
        # research context and is not commit authority. Omitted, not null, when
        # none were given: auto-finalize then commits nothing.
        declared_owned_paths = _declared_owned_paths(getattr(args, "owned_path", None))
        if declared_owned_paths is not None:
            initial_state["owned_paths"] = list(declared_owned_paths)
        if worktree_path is not None and not worktree_path.is_dir():
            _reap_runtime_tmp_lease(runtime_tmp_root, runtime_tmp_namespace_root)
            print(
                f"❌ worktree {worktree_path} for {task_id!r} disappeared before its task record was published",
                file=sys.stderr,
            )
            return 1
        # The admission hold published under the lock is replaced in place, so
        # the admitted slot stays held until the worker writes its pid (#8717).
        if admission_record is not None:
            initial_state["admission"] = admission_record
        _write_state_atomic(state_path, initial_state)
        # The published record now claims the worktree for settle's scan, so
        # the lock is released before the worker, whose own settle takes it
        # again, is spawned. The two acquisitions never nest (#8610).
        worktree_locks.close()

        # Fix 5 (#1476 AC 5) — dispatch-start telemetry.
        if worktree_path:
            sparse_meta = worktree_telemetry.get("sparse") or {}
            sparse_tag = ""
            if sparse_meta.get("full_checkout"):
                sparse_tag = " [full-checkout]"
            elif sparse_meta.get("excluded"):
                sparse_tag = f" [sparse-exclude={','.join(sparse_meta['excluded'])}]"
            print(
                f"🌲 dispatch {task_id}: run_nonce={run_nonce} branch={worktree_branch} "
                f"base_sha={worktree_telemetry.get('base_sha') or '?'} "
                f"path={worktree_path} layout={worktree_layout}"
                + (" [rebased]" if worktree_telemetry.get("rebased") else "")
                + (" [reused]" if worktree_telemetry.get("reused") else "")
                + sparse_tag,
                file=sys.stderr,
            )
            if worktree_layout == "flat":
                print(
                    f"⚠️  task {task_id!r} is using the DEPRECATED flat worktree "
                    f"layout ({worktree_path}). New dispatches should use "
                    f"`--worktree` (bare) to land in "
                    f".worktrees/dispatch/{{agent}}/{{task}}/.",
                    file=sys.stderr,
                )
        else:
            print(
                f"🌲 dispatch {task_id}: run_nonce={run_nonce}",
                file=sys.stderr,
            )

        # Fork a detached subprocess that runs this same script with
        # --worker. We use Popen rather than os.fork for portability.
        #
        # Python interpreter: the project rule (non-negotiable-rules.md)
        # is to always use .venv/bin/python. delegate.py follows that rule
        # strictly.
        venv_python = project_interpreter()
        python_bin = str(venv_python)
        cmd = [
            python_bin,
            str(Path(__file__).resolve()),
            "_worker",
            "--task-id",
            task_id,
            "--agent",
            dispatch_agent,
            "--mode",
            args.mode,
            "--cwd",
            cwd,
            "--hard-timeout",
            str(args.hard_timeout),
            "--silence-timeout",
            str(silence_timeout),
            "--initial-response-timeout",
            str(initial_response_timeout),
            "--runtime-tmp-root",
            str(runtime_tmp_root),
            "--runtime-tmp-namespace-root",
            str(runtime_tmp_namespace_root),
        ]
        cmd.extend(_dispatch_worker_identity_flags(args, requested_harness))
        if keep_worktree:
            cmd.append("--keep-worktree")
        if bool(getattr(args, "finalize_open_pr", False)):
            cmd.append("--finalize-open-pr")
        if max_budget_usd is not None:
            cmd.extend(["--max-budget-usd", str(max_budget_usd)])
        if output_schema_path is not None:
            cmd.extend(
                [
                    "--output-schema",
                    output_schema_path,
                    "--output-schema-sha256",
                    str(output_schema_sha256),
                ]
            )
        if args.model:
            cmd.extend(["--model", args.model])
        if getattr(args, "provider", None):
            cmd.extend(["--provider", args.provider])
        effort = getattr(args, "effort", None)
        if effort:
            cmd.extend(["--effort", effort])
        if run_nonce:
            cmd.extend(["--run-nonce", run_nonce])
        if review_plan is not None:
            cmd.extend(
                [
                    "--review-id",
                    str(review_id),
                    "--attempt-id",
                    str(attempt_id),
                    "--mcp-config-path",
                    str(review_plan.config_path),
                    "--strict-mcp-config",
                ]
            )

        # Pipe the prompt via stdin so it doesn't hit argv length limits.
        # start_new_session=True detaches from our process group — the
        # worker survives our exit, which is what we want.
        worker_env = _build_worker_env(
            task_id=task_id,
            dispatch_agent=dispatch_agent,
            attribution=attribution,
            run_nonce=run_nonce,
            runtime_tmp_root=runtime_tmp_root,
            runtime_tmp_namespace_root=runtime_tmp_namespace_root,
            worktree_path=worktree_path,
            allow_merge=bool(getattr(args, "allow_merge", False)),
        )
        try:
            # Scoped when lu-dispatch.slice is really in force; plain Popen
            # otherwise. The recorded pid is the worker in both cases (#8645).
            proc, launch = dispatch_isolation.spawn_detached_worker(
                cmd,
                task_id=task_id,
                run_nonce=run_nonce,
                popen=subprocess.Popen,
                env=worker_env,
                stdin=subprocess.PIPE,
                stdout=stdout_fd,
                stderr=stderr_fd,
                stderr_log=stderr_log,
            )
            spawned = True
        except (OSError, FileNotFoundError, ValueError, dispatch_isolation.DispatchIsolationError) as exc:
            # Popen itself failed — typically because the Python
            # interpreter isn't where we expected, or the file
            # descriptors are somehow invalid. Without this handler
            # the state file would stay at "spawning" forever with
            # pid=None and no zombie detection could rescue it
            # (because zombie detection is gated on `pid and not alive`).
            # Codex 2026-04-10 audit finding.
            # DispatchIsolationError means the scope may already have started
            # the worker (late marker, or /proc could not prove it never
            # exec'd). The task is failed and not relaunched.
            if isinstance(exc, dispatch_isolation.DispatchIsolationError):
                spawn_error = f"dispatch isolation: {exc}"[:500]
                returncode_reason = "scoped worker startup was ambiguous; not relaunched"
            else:
                spawn_error = f"Popen failed: {type(exc).__name__}: {exc}"[:500]
                returncode_reason = "worker process was not started"
            failed_state = _read_state(state_path) or initial_state
            failed_state.update(
                {
                    "status": "failed",
                    "finished_at": datetime.now(UTC).isoformat(),
                    "stderr_excerpt": spawn_error,
                    "returncode": None,
                    "returncode_reason": returncode_reason,
                    "last_error": _first_error_line(spawn_error),
                    "exit_code": None,
                }
            )
            failed_state.update(
                _reap_runtime_tmp_lease(
                    runtime_tmp_root,
                    runtime_tmp_namespace_root,
                )
            )
            _record_final_branch_head(failed_state)
            _write_state_atomic(state_path, failed_state)
            print(
                f"❌ failed to spawn worker for {task_id!r}: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            return 1

        # CRITICAL: write the Popen child's PID into the state file
        # RIGHT NOW, from the parent, before the worker has a chance
        # to run. Without this, if the worker crashes before reaching
        # _run_worker (e.g. top-level import error in delegate.py,
        # syntax error on a future edit, env var issue), the state
        # file stays at {"status": "spawning", "pid": null} forever
        # and no subsequent status/wait call can detect the crash
        # because zombie detection is gated on `pid and not _pid_alive(pid)`.
        # Fixed after Gemini review 2026-04-10.
        state_with_pid = _read_state(state_path) or initial_state
        state_with_pid["pid"] = proc.pid
        state_with_pid.update(launch.as_state())
        _write_state_atomic(state_path, state_with_pid)
        # Bind ownership ledger rows to the long-lived worker PID (not the
        # short-lived dispatch CLI). Best-effort: WARN path must not fail spawn.
        if str(args.mode) in _WRITE_CAPABLE_MODES:
            try:
                from scripts.guardrails.delegate_ownership import update_write_claim_pid
            except ImportError:  # pragma: no cover
                from guardrails.delegate_ownership import update_write_claim_pid  # type: ignore

            try:
                update_write_claim_pid(task_id, int(proc.pid))
            except Exception as own_exc:
                print(
                    f"⚠️  write-path ownership: failed to bind worker pid: {own_exc}",
                    file=sys.stderr,
                )

        assert proc.stdin is not None  # we passed stdin=PIPE
        try:
            proc.stdin.write(prompt.encode("utf-8"))
            proc.stdin.close()
        except BrokenPipeError:
            pass  # worker crashed before reading; zombie detector will catch it
    except BaseException:
        if not spawned:
            _reap_runtime_tmp_lease(runtime_tmp_root, runtime_tmp_namespace_root)
        raise
    finally:
        # The Popen child inherited these FDs via dup; our copies can
        # be closed immediately without affecting the child.
        stdout_fd.close()
        stderr_fd.close()

    # Return task-id and run_nonce on stdout so shell callers can capture them (#7168).
    print(task_id)
    print(run_nonce)
    return 0


# ---------------------------------------------------------------------------
# Status command — read state + detect zombies
# ---------------------------------------------------------------------------


def cmd_status(args: argparse.Namespace) -> int:
    state_path, state = _read_state_or_archived(args.task_id)
    if state is None:
        print(
            json.dumps({"error": f"no state file for task {args.task_id!r}"}),
        )
        return 1

    expected_nonce = getattr(args, "run_nonce", None)
    if expected_nonce is not None and state.get("run_nonce") != expected_nonce:
        print(
            json.dumps(
                {
                    "error": "stale_run_nonce",
                    "task_id": args.task_id,
                    "expected_run_nonce": expected_nonce,
                    "record_run_nonce": state.get("run_nonce"),
                    "status": "stale",
                }
            ),
            file=sys.stderr,
        )
        return 1

    # Detect zombies: if status is "running" but PID is dead, the worker
    # crashed (OOM, SIGKILL, reboot, etc.) and never got to update the
    # state file. Mark as "crashed" and persist the correction so
    # subsequent status calls get the right answer without redoing the check.
    _heal_dead_task(state_path, state, source="status")

    # Elapsed time for still-running tasks
    if state.get("status") == "running" and state.get("started_at"):
        try:
            started = datetime.fromisoformat(str(state["started_at"]).replace("Z", "+00:00"))
            state["elapsed_s"] = round(
                (datetime.now(UTC) - started).total_seconds(),
                1,
            )
        except (ValueError, TypeError):
            pass

    # Fix 4 (#1476): backfill worktree_layout for tasks persisted before
    # the field existed, and warn about flat-layout worktrees.
    if state.get("worktree_path") and not state.get("worktree_layout"):
        state["worktree_layout"] = _classify_worktree_layout(
            state.get("worktree_path"),
        )
    if state.get("worktree_layout") == "flat":
        print(
            f"⚠️  task {args.task_id!r} uses the DEPRECATED flat worktree "
            f"layout ({state.get('worktree_path')}). New dispatches should "
            f"use the `.worktrees/dispatch/{{agent}}/{{task}}/` subtree.",
            file=sys.stderr,
        )

    print(json.dumps(state, indent=2, default=str))
    return 0


class MonitorApiUnavailable(RuntimeError):
    """Raised when the local Monitor API cannot answer a task status query."""


class BudgetGuardRefuseError(RuntimeError):
    """Raised when --check-budget must refuse dispatch (hot/deficit/near_cap, no fallback)."""


class CapacityGuardRefuseError(RuntimeError):
    """Raised when Cursor driver lease admission must refuse a worker spawn."""


def _monitor_api_base_url() -> str:
    return os.environ.get("DELEGATE_MONITOR_API", _MONITOR_API_BASE_URL).rstrip("/")


def _dispatch_check_budget_enabled(args: argparse.Namespace) -> bool:
    """True when --check-budget is set or LU_DISPATCH_CHECK_BUDGET=1."""
    if getattr(args, "check_budget", False):
        return True
    return os.environ.get("LU_DISPATCH_CHECK_BUDGET", "").strip() in {"1", "true", "yes", "on"}


def _age_seconds_from_started_at(started_at: Any) -> int:
    try:
        started = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return 0
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    return max(0, round((datetime.now(UTC) - started.astimezone(UTC)).total_seconds()))


def _fetch_monitor_task(task_id: str, *, run_nonce: str | None = None) -> dict[str, Any] | None:
    quoted = urllib.parse.quote(task_id, safe="")
    url = f"{_monitor_api_base_url()}/api/delegate/tasks/{quoted}"
    if run_nonce:
        url += f"?run_nonce={urllib.parse.quote(run_nonce, safe='')}"
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        if exc.code == 409:
            return {"task": {"status": "stale_run_nonce", "task_id": task_id}, "alive": False, "stale_run_nonce": True}
        raise MonitorApiUnavailable(str(exc)) from exc
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise MonitorApiUnavailable(str(exc)) from exc
    return payload if isinstance(payload, dict) else {}


def _fetch_routing_budget() -> dict[str, Any]:
    url = f"{_monitor_api_base_url()}/api/state/routing-budget?fresh_codexbar=true"
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise MonitorApiUnavailable(str(exc)) from exc
    return payload if isinstance(payload, dict) else {}


def _load_dispatch_fallbacks() -> dict[str, str]:
    from scripts.common.fallback_substitutions import load_dispatch_fallbacks

    return load_dispatch_fallbacks(_FALLBACK_SUBS_PATH)


def _budget_lane_status(agent: str, agent_info: dict[str, Any]) -> str | None:
    if agent == "claude":
        return (agent_info.get("interactive") or {}).get("status") or agent_info.get("status")
    return agent_info.get("status")


def _budget_will_last_to_reset(agent_info: dict[str, Any]) -> bool | None:
    cb = agent_info.get("codexbar")
    if not isinstance(cb, dict) or "will_last_to_reset" not in cb:
        return None
    val = cb.get("will_last_to_reset")
    if val is None:
        return None
    return bool(val)


def _budget_cooler_lanes(agents: dict[str, Any], *, exclude: str) -> list[str]:
    cool: list[str] = []
    for lane, info in agents.items():
        if not isinstance(info, dict):
            continue
        lane_l = str(lane).strip().lower()
        if lane_l == exclude:
            continue
        status = _budget_lane_status(lane_l, info)
        cb = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else None
        if status in {"hot", "near_cap"} or pace_is_deficit(cb) is True:
            continue
        if status in {"cool", "warm"}:
            cool.append(lane_l)
    return sorted(cool)


def _budget_pace(agent_info: dict[str, Any]) -> dict[str, Any] | None:
    cb = agent_info.get("codexbar")
    return cb if isinstance(cb, dict) else None


def _budget_headroom_blocked(agent_info: dict[str, Any]) -> bool:
    runtime = agent_info.get("runtime")
    return isinstance(runtime, dict) and bool(runtime.get("headroom_blocked"))


def _pace_expected_pct(pace: dict[str, Any] | None) -> float | None:
    if not isinstance(pace, dict):
        return None
    for key in ("expected_pct", "weekly_expected_pct", "expectedUsedPercent"):
        value = pace.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        return float(value)
    return None


def _budget_needs_hard_capacity_action(
    *,
    status: str | None,
    will_last: bool | None,
    is_stale: bool,
    records_loaded: int,
    pace: dict[str, Any] | None = None,
    headroom_blocked: bool = False,
) -> tuple[bool, str]:
    """Return (needs_action, reason) for near_cap / hot / a real pace deficit.

    ``near_cap`` is unchanged. ``status=hot`` still hard-acts, except when the
    hot label is the early-window or on-pace false positive: a pace reading is
    present and :func:`pace_is_deficit` is not true, and runtime headroom did
    not set the hot label. A bare ``will_last`` with no pace record still
    counts only when no pace dict was supplied.
    """
    if is_stale:
        return False, ""
    # Keep existing near_cap gate (fresh ledger) and extend to hot/deficit.
    if status == "near_cap" and records_loaded > 0:
        return True, "near_cap (>90% on FRESH snapshot)"
    if status == "hot" and headroom_blocked:
        return True, "status=hot"
    deficit = pace_is_deficit(pace) if pace else None
    expected = _pace_expected_pct(pace)
    hidden = expected is not None and not pace_is_visible({"expected_pct": expected})
    # Hot that the pace rule does not support is the freshly-reset / on-pace
    # false positive. Runtime headroom hot was returned above.
    if status == "hot" and pace and deficit is not True and (deficit is False or hidden):
        return False, ""
    if deficit is True:
        return True, "codexbar will_last_to_reset=False (deficit)"
    if status == "hot":
        return True, "status=hot"
    if pace is None and will_last is False:
        return True, "codexbar will_last_to_reset=False (deficit)"
    return False, ""


_LANGUAGE_LANES = frozenset({"claude", "codex", "agy"})


def _dispatch_is_language_lane(args: argparse.Namespace) -> bool:
    """True when the dispatch is Ukrainian language work.

    Signals: ``--language-lane``, ``--review-profile ukrainian``, a ``l2-uk*``
    research track, or an owned path under ``curriculum/``. Other lanes must
    not receive that work directly or through budget substitution (#8449).
    """
    if bool(getattr(args, "language_lane", False)):
        return True
    if getattr(args, "review_profile", None) == "ukrainian":
        return True
    track = str(getattr(args, "research_track", "") or "").strip().lower()
    if track.startswith("l2-uk"):
        return True
    owned = getattr(args, "research_owned_path", None) or []
    if isinstance(owned, str):
        owned = [owned]
    for path in owned:
        text = str(path).replace("\\", "/").lstrip("./")
        if text.startswith("curriculum/") or text.startswith("scripts/curriculum/"):
            return True
    return False


def _kimi_worktree_trees(worktree: Path) -> list[Any]:
    """An existing worktree as a Kimi worker sees it: its files on disk and the commit checked out there."""
    from scripts.agent_runtime.kimi_admission import worktree_trees

    return worktree_trees(worktree, env=_sanitized_git_env())


def _resolve_local_base_sha(*, base: str, branch: str | None, pinned_head_sha: str | None) -> str:
    """The commit a new Kimi worktree would start from, from local objects only.

    The Kimi content scan runs before any effect, so this never fetches: it
    verifies the pinned head, the existing remote-tracking ref of ``branch``,
    or the base's remote-tracking ref, as a commit already in the repository.
    Worktree creation later fetches as it does for any seat and refuses when
    the fetched commit is not the one scanned. Raises ``RuntimeError`` when the
    commit is not available locally.
    """
    if pinned_head_sha:
        ref = pinned_head_sha
    elif branch:
        ref = f"origin/{branch}"
    else:
        ref = _origin_base_ref(base)
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        proc = None
    sha = (proc.stdout or "").strip() if proc is not None and proc.returncode == 0 else ""
    if not sha:
        raise RuntimeError(f"base not available locally ({ref}); refresh origin and retry")
    return sha


def _kimi_start_trees(
    args: argparse.Namespace,
    *,
    agent: str,
    target_repo_root: Path,
    validated_worktree: Path | None,
    validated_cwd: Path | None,
) -> tuple[list[Any], str]:
    """The trees a Kimi worker will start from, and the commit they are read at.

    A reused worktree (``--worktree``, ``--branch`` or ``--cwd``) is read as it
    is on disk and at the commit checked out there. A new worktree is read at
    its creation base commit, resolved from objects already present locally
    (no fetch, no checkout) and read with git plumbing. Dispatch then refuses
    a worktree that is not created from, or no longer checked out at, that
    commit. Raises ``ValueError`` or ``RuntimeError`` when there is no such tree.
    """
    from scripts.agent_runtime.kimi_admission import CommitTree

    worktree = getattr(args, "worktree", None) or ("auto" if getattr(args, "branch", None) else None)
    if worktree == "auto":
        path: Path | None = _auto_worktree_path(agent, str(args.task_id), repo_root=target_repo_root)
    elif worktree:
        path = validated_worktree
    elif validated_cwd is not None:
        path = _resolve_verified_worktree_path(validated_cwd)
        if path is None:
            raise ValueError(f"--cwd {str(validated_cwd)!r} is not a dispatch worktree")
    else:
        path = None
    if path is None:
        raise ValueError("workspace-write without a dispatch worktree")
    if path.exists():
        trees = _kimi_worktree_trees(path)
        return trees, trees[-1].commit
    if getattr(args, "pr", None) and not getattr(args, "branch", None):
        raise ValueError("--pr without --branch: name the PR branch so its head is read before dispatch")
    base_sha = _resolve_local_base_sha(
        base=getattr(args, "base", None) or "main",
        branch=getattr(args, "branch", None),
        pinned_head_sha=getattr(args, "pinned_head", None),
    )
    return [CommitTree(_REPO_ROOT, base_sha, env=_sanitized_git_env())], base_sha


def _kimi_dispatch_gate(
    args: argparse.Namespace,
    *,
    agent: str,
    repo_role: str | None,
    target_repo_root: Path,
    validated_worktree: Path | None,
    validated_cwd: Path | None,
) -> tuple[str | None, str | None]:
    """The dispatch-side Kimi gate: ``(refusal, start commit)``.

    The start commit is the commit the owned paths were read at, which the
    worker's worktree must be created from or checked out at; None when the
    call is refused, is not Kimi, or owns no paths. The tree is resolved only
    after every policy check admits.
    """
    start: list[str] = []

    def trees() -> list[Any]:
        resolved, commit = _kimi_start_trees(
            args,
            agent=agent,
            target_repo_root=target_repo_root,
            validated_worktree=validated_worktree,
            validated_cwd=validated_cwd,
        )
        start.append(commit)
        return resolved

    refusal = _kimi_admission_refusal(args, agent=agent, repo_role=repo_role, trees=trees)
    return refusal, (start[0] if start and refusal is None else None)


def _kimi_admission_refusal(
    args: argparse.Namespace,
    *,
    agent: str,
    trees: Any,
    repo_role: str | None = None,
) -> str | None:
    """Refusal message when ``agent`` or ``--model`` is a Kimi seat and the dispatch is not admitted.

    ``--owned-path`` and ``--research-owned-path`` both declare task ownership,
    so every path from either flag must be on the Kimi allowlist and is read
    for Ukrainian content in ``trees`` (see ``refuse_kimi_if_disallowed``).
    """
    from scripts.agent_runtime.kimi_admission import KimiAdmissionRefused, refuse_kimi_if_disallowed

    def flag_paths(attr: str) -> list[str]:
        value = getattr(args, attr, None) or []
        return [value] if isinstance(value, str) else list(value)

    # Only ``--owned-path`` is ownership (the worker's boundary and scan use it); a
    # ``--research-owned-path`` is checked like one but never stands in for it.
    declared = flag_paths("owned_path")
    owned = declared + flag_paths("research_owned_path")
    try:
        refuse_kimi_if_disallowed(
            (agent,),
            (getattr(args, "model", None),),
            mode=str(getattr(args, "mode", "") or ""),
            paths=owned,
            declared_paths=declared,
            repo=repo_role,
            review=bool(getattr(args, "review", False))
            or bool(getattr(args, "review_attempt", None))
            or bool(getattr(args, "require_review_verdict", False))
            or bool(getattr(args, "review_profile", None))
            or str(getattr(args, "type", "") or "").strip().casefold() == "review",
            language_lane=_dispatch_is_language_lane(args),
            research_track=getattr(args, "research_track", None),
            prompt_file=getattr(args, "prompt_file", None),
            repo_root=_REPO_ROOT,
            trees=trees,
        )
    except KimiAdmissionRefused as exc:
        return str(exc)
    return None


def _discard_model_probe_output(plan: object) -> None:
    """Remove a temp file a successful model probe created. Leave repo paths alone."""
    output = getattr(plan, "output_file", None)
    if not isinstance(output, Path):
        return
    try:
        resolved = output.resolve()
        temp_root = Path(tempfile.gettempdir()).resolve()
    except OSError:
        return
    if resolved != temp_root and temp_root not in resolved.parents:
        return
    try:
        resolved.unlink(missing_ok=True)
    except OSError:
        return


def _adapter_model_rejection(agent: str, model: str) -> str | None:
    """Return the adapter's refusal text, or None when this model is not refused.

    A successful probe is not a rejection. Any error other than the adapter's
    model ValueError is inconclusive: keep the explicit model instead of
    crashing dispatch. The probe must not leave the temp file ``build_invocation``
    creates on the accepted path.
    """
    from agent_runtime.registry import get_agent_entry

    entry = get_agent_entry(agent)
    spec = str(entry.get("adapter") or "")
    if ":" not in spec:
        return None
    module_name, class_name = spec.split(":", 1)
    module = __import__(module_name, fromlist=[class_name])
    adapter = getattr(module, class_name)()
    try:
        plan = adapter.build_invocation(
            prompt="model-probe",
            mode="read-only",
            cwd=Path("."),
            model=model,
            task_id=None,
            session_id=None,
            tool_config=None,
        )
    except ValueError as exc:
        text = str(exc)
        if model in text and ("rejected" in text or "unsupported" in text.lower()):
            return text
        return None
    except Exception as exc:
        print(
            f"⚠ model probe for {agent} could not verify {model}: {type(exc).__name__}",
            file=sys.stderr,
        )
        return None
    _discard_model_probe_output(plan)
    return None


def _adapter_rejects_model(agent: str, model: str) -> bool:
    """True when the target adapter refuses this explicit model before spawn."""
    return _adapter_model_rejection(agent, model) is not None


def _lane_default_model(agent: str) -> str | None:
    """Registry default for ``agent`` — the dispatch pin, not the seat identity."""
    from agent_runtime.telemetry import _default_model_for

    return _default_model_for(agent)


def _load_budget_substitution_table() -> dict[str, dict[str, str]]:
    from scripts.review.model_catalog import ModelCatalogError, budget_substitution_table, load_model_catalog

    try:
        return budget_substitution_table(load_model_catalog())
    except ModelCatalogError as exc:
        raise BudgetGuardRefuseError(
            f"ROUTING REFUSED: model catalog cannot resolve a substitution model: {exc}"
        ) from exc


def _substitution_model_admitted(agent: str, model: str) -> bool:
    """True when ``model`` is a catalog-or-invocation model for ``agent`` and the adapter does not reject it."""
    from scripts.review.model_catalog import ModelCatalogError, load_model_catalog, substitution_model_admitted

    try:
        admitted = substitution_model_admitted(load_model_catalog(), agent, model)
    except ModelCatalogError as exc:
        raise BudgetGuardRefuseError(
            f"ROUTING REFUSED: model catalog cannot resolve a substitution model: {exc}"
        ) from exc
    if not admitted:
        return False
    return not _adapter_rejects_model(agent, model)


def _resolve_substitution_model(target_agent: str, explicit_model: str | None) -> tuple[str, str]:
    """Map ``explicit_model`` onto ``target_agent``, or use that lane's registry default.

    A mapping row wins when the substitute admits the mapped model. With no
    explicit model, or an explicit model the substitute adapter does not
    reject, dispatch uses that lane's registry default. An explicit model
    with no mapping row that the adapter rejects is refused before spawn:
    the default must not hide that refusal (retired alias and budget guard).

    Returns ``(model, "mapped"|"catalog-default")``. Raises BudgetGuardRefuseError
    when the explicit model is rejected, or neither a mapped model nor the
    default is valid for the substitute.
    """
    table = _load_budget_substitution_table().get(target_agent, {})
    mapped = table.get(explicit_model) if explicit_model else None
    default = _lane_default_model(target_agent)
    if mapped and _substitution_model_admitted(target_agent, mapped):
        return mapped, "mapped"
    if explicit_model and mapped is None:
        rejection = _adapter_model_rejection(target_agent, explicit_model)
        if rejection:
            raise BudgetGuardRefuseError(
                "ROUTING REFUSED: substitute "
                f"--agent {target_agent} rejects explicit --model {explicit_model} "
                f"({rejection}). Refusing before spawn."
            )
    if default and _substitution_model_admitted(target_agent, default):
        return default, "catalog-default"
    raise BudgetGuardRefuseError(
        "ROUTING REFUSED: no valid model for substitute "
        f"--agent {target_agent} "
        f"(requested --model {explicit_model or '(none)'}; "
        f"mapped {mapped or '(none)'}; "
        f"catalog default {default or '(none)'}). "
        "Refusing before spawn."
    )


def _substitution_model_phrase(chosen: str, how: str, explicit_model: str | None) -> str:
    if how == "mapped":
        return f"--model {chosen} (mapped from {explicit_model})"
    if explicit_model:
        return f"--model {chosen} (catalog default; {explicit_model} has no mapping)"
    return f"--model {chosen} (catalog default)"


def _remember_agent_substitution(
    sink: dict[str, Any] | None,
    *,
    source: str,
    requested_agent: str,
    requested_model: str | None,
    actual_agent: str,
    actual_model: str,
    how: str,
) -> None:
    if sink is None:
        return
    sink["applied"] = True
    sink["model"] = actual_model
    sink["record"] = {
        "kind": "agent-substitution",
        "substituted": True,
        "source": source,
        "requested_agent": requested_agent,
        "actual_agent": actual_agent,
        "requested_model": requested_model,
        "actual_model": actual_model,
        "actual_model_known": True,
        "model_resolution": how,
    }


def _applied_agent_substitution(resolution: dict[str, Any], dispatch_agent: str) -> dict[str, Any] | None:
    if not resolution.get("applied"):
        return None
    record = resolution.get("record")
    if not isinstance(record, dict) or record.get("actual_agent") != dispatch_agent:
        return None
    return record


def _merge_agent_substitution(prior: Any, runtime: Any) -> Any:
    """Keep a dispatch agent-substitution when later runtime attribution arrives."""
    if not isinstance(prior, dict) or prior.get("kind") != "agent-substitution":
        return runtime
    if not isinstance(runtime, dict):
        return prior
    if runtime.get("kind") == "agent-substitution":
        return runtime
    merged = dict(prior)
    merged["runtime_attribution"] = runtime
    return merged


def _resolve_agent_with_budget_guard(
    agent: str,
    *,
    provider: str | None = None,
    language_lane: bool = False,
    requested_model: str | None = None,
    model_resolution: dict[str, Any] | None = None,
    origin_agent: str | None = None,
) -> str:
    """Return possibly-substituted agent.

    Hard auto-sub on fresh snapshot when chosen lane is near_cap, hot, or in
    CodexBar deficit (will_last_to_reset is False), if yaml dispatch_fallbacks
    has a known target. Without a usable fallback: refuse (raise
    BudgetGuardRefuseError) unless caller used --force-agent before this call.
    Subscription stale/empty: advisory only. Prepaid requires fresh verified
    funding independently of the subscription ledger and never auto-substitutes.
    """
    requested = (agent or "").strip().lower()
    if language_lane and requested not in _LANGUAGE_LANES:
        raise BudgetGuardRefuseError(
            "ROUTING REFUSED: LANGUAGE-LANES RULE (operator 2026-09-27): "
            f"--agent {requested} is outside claude, codex (GPT), and agy (Gemini)."
        )
    try:
        payload = _fetch_routing_budget()
    except MonitorApiUnavailable:
        if requested == "deepseek" or provider == "openrouter":
            raise BudgetGuardRefuseError(
                "NOTE: ROUTING REFUSED: prepaid capacity NEED_PROBE; Monitor API unreachable."
            ) from None
        print("⚠ ROUTING CHECK SKIPPED: Monitor API unreachable", file=sys.stderr)
        return requested

    prepaid = "openrouter" if provider == "openrouter" else requested if requested == "deepseek" else None
    if prepaid:
        from scripts.api.state_router import _api_lane_status_from_account

        accounts = payload.get("api_accounts") or {}
        account = accounts.get(prepaid) or {}
        status = _api_lane_status_from_account(prepaid, account)
        if (
            status not in {"cool", "warm"}
            or account.get("is_available") is False
            or account.get("status") == "near_cap"
        ):
            raise BudgetGuardRefuseError(
                f"NOTE: ROUTING REFUSED: prepaid {prepaid} status={status}; "
                f"probe_state={account.get('probe_state', 'NEED_PROBE')}; "
                f"freshness={account.get('freshness', 'unavailable')}. "
                "Verify funding with `python -m scripts.fleet.usage refresh` or pass --force-agent."
            )
        return requested

    diags = payload.get("diagnostics") or {}
    rec = payload.get("recommendation") or {}
    agents = payload.get("agents") or {}
    records_loaded = int(diags.get("records_loaded", 0) or 0)
    is_stale = bool(diags.get("stale", False))
    codexbar_data_available = bool(diags.get("codexbar_data_available", False))
    subscription_data_available = codexbar_data_available or bool(agents)

    # An empty ledger is only unknown when the explicit subscription refresh also
    # yielded no authoritative weekly data. Never quietly fail open here.
    if not agents or (records_loaded == 0 and not subscription_data_available):
        print(
            "⚠ ROUTING CHECK UNKNOWN: budget UNKNOWN — could not verify subscription "
            "usage snapshots; lanes may be in deficit; no hard sub.",
            file=sys.stderr,
        )
        return requested

    # Check for demoted lanes and print warnings
    for item in payload.get("ranked_by_headroom") or []:
        h = item.get("health")
        if h and not h.get("healthy", True):
            lane = item.get("lane")
            cf = h.get("consecutive_failures", 0)
            sm = h.get("span_minutes", 0)
            print(f"⚠ lane {lane} demoted: {cf} spawn failures in {sm}m", file=sys.stderr)

    if records_loaded == 0:
        for warning in rec.get("warnings") or []:
            if "is in deficit" in str(warning):
                print(f"⚠ ROUTING CHECK: {warning}", file=sys.stderr)

    if is_stale:
        print(
            "⚠ ROUTING CHECK ADVISORY (stale snapshot, generatedAt/data age >15min) — verify manually; no hard sub",
            file=sys.stderr,
        )
        # Rec warning deliberately suppressed on stale: a recommendation from
        # stale numbers is worse than none (same rationale as the empty case).
    else:
        # advisory rec mismatch still emitted (for info)
        recommended = rec.get("primary_agent_for_code")
        if recommended and recommended != requested and recommended not in (None, "inline_orchestrator"):
            print(
                f"⚠ ROUTING WARNING: budget recommends --agent {recommended}, you passed --agent {requested}.",
                file=sys.stderr,
            )
            if rec.get("rationale"):
                print(f"Rationale: {rec['rationale']}", file=sys.stderr)

    agent_info = agents.get(requested, {}) or {}
    agent_dict = agent_info if isinstance(agent_info, dict) else {}
    status = _budget_lane_status(requested, agent_dict)
    will_last = _budget_will_last_to_reset(agent_dict)
    reserve = _load_reset_reserve(_REPO_ROOT)
    reserve_relaxes = (
        requested == "codex"
        and _codex_is_threatened(agent_info if isinstance(agent_info, dict) else {})
        and _codex_reset_reserve_eligible(
            reserve,
            agent_info if isinstance(agent_info, dict) else {},
            snapshot_stale=is_stale,
        )
    )
    if reserve_relaxes:
        print(
            f"⚠ Codex reset reserve active ({reserve.get('remaining_resets')} confirmed reset(s) remaining); "
            "provider and runtime headroom checks passed.",
            file=sys.stderr,
        )
    burn = (
        agent_info.get("burn_pct_7d")
        if requested != "claude"
        else (agent_info.get("interactive") or {}).get("burn_pct_7d") or agent_info.get("burn_pct_7d")
    )

    needs_action, reason = (
        (False, "")
        if reserve_relaxes
        else _budget_needs_hard_capacity_action(
            status=status,
            will_last=will_last,
            is_stale=is_stale,
            records_loaded=records_loaded,
            pace=_budget_pace(agent_dict),
            headroom_blocked=_budget_headroom_blocked(agent_dict),
        )
    )
    if not needs_action:
        return requested

    fallbacks = _load_dispatch_fallbacks()
    sub = fallbacks.get(requested)
    # The yaml `dispatch_fallbacks` map is the ONLY source for hard subs —
    # no inferred/hardcoded mappings (a deleted config entry must mean
    # refuse or advisory, not silently resurrect an old route).
    if sub and sub not in _DISPATCH_AGENT_CHOICES:
        print(
            f"⚠ ROUTING: dispatch_fallbacks maps {requested} → {sub}, not a known dispatch agent — ignoring hard sub.",
            file=sys.stderr,
        )
        sub = None
    if sub and sub != requested:
        if language_lane:
            return _language_lane_substitute(
                requested,
                fallbacks,
                agents if isinstance(agents, dict) else {},
                is_stale=is_stale,
                records_loaded=records_loaded,
                reset_reserve=reserve,
                requested_model=requested_model,
                model_resolution=model_resolution,
                origin_agent=origin_agent or requested,
            )
        chosen, how = _resolve_substitution_model(sub, requested_model)
        note = (
            f"🔄 HARD AUTO-SUBSTITUTE: --agent {requested} → {sub} "
            f"{_substitution_model_phrase(chosen, how, requested_model)} "
            f"({reason}; "
            f"sub per agent_fallback_substitutions.yaml dispatch_fallbacks). "
            "Substitution noted for operator contract / review independence."
        )
        print(note, file=sys.stderr)
        _remember_agent_substitution(
            model_resolution,
            source="budget-guard",
            requested_agent=origin_agent or requested,
            requested_model=requested_model,
            actual_agent=sub,
            actual_model=chosen,
            how=how,
        )
        if burn is not None:
            print(f"  (burn_pct_7d was ~{burn}%; resets_at={agent_info.get('resets_at')})", file=sys.stderr)
        return sub

    cooler = _budget_cooler_lanes(agents if isinstance(agents, dict) else {}, exclude=requested)
    cooler_txt = ", ".join(cooler) if cooler else "(none marked cool/warm in snapshot)"
    raise BudgetGuardRefuseError(
        f"ROUTING REFUSED: --agent {requested} is {reason} and "
        f"dispatch_fallbacks has no usable substitute. "
        f"Cooler seats from budget snapshot: {cooler_txt}. "
        "Re-route (see `python -m scripts.fleet.capacity_pick`) or pass --force-agent."
    )


def _language_lane_substitute(
    requested: str,
    fallbacks: dict[str, str],
    agents: dict[str, Any],
    *,
    is_stale: bool,
    records_loaded: int,
    reset_reserve: dict[str, Any] | None = None,
    requested_model: str | None = None,
    model_resolution: dict[str, Any] | None = None,
    origin_agent: str | None = None,
) -> str:
    """Walk fallbacks, staying inside claude/codex/agy (#8449)."""
    seat = requested
    seen = {seat}
    current_model = requested_model
    origin = origin_agent or requested
    while True:
        info = agents.get(seat, {}) or {}
        info_dict = info if isinstance(info, dict) else {}
        status = _budget_lane_status(seat, info_dict)
        will_last = _budget_will_last_to_reset(info_dict)
        reserve_relaxes = (
            seat == "codex"
            and _codex_is_threatened(info_dict)
            and _codex_reset_reserve_eligible(reset_reserve or {}, info_dict, snapshot_stale=is_stale)
        )
        needs, why = (
            (False, "")
            if reserve_relaxes
            else _budget_needs_hard_capacity_action(
                status=status,
                will_last=will_last,
                is_stale=is_stale,
                records_loaded=records_loaded,
                pace=_budget_pace(info_dict),
                headroom_blocked=_budget_headroom_blocked(info_dict),
            )
        )
        if not needs:
            return seat
        nxt = fallbacks.get(seat)
        if not nxt or nxt in seen or nxt not in _LANGUAGE_LANES:
            raise BudgetGuardRefuseError(
                "ROUTING REFUSED: LANGUAGE-LANES RULE (operator 2026-09-27). "
                f"Language work on --agent {requested} cannot move to "
                f"{nxt or 'no fallback'}; allowed lanes are claude, codex (GPT), and agy (Gemini)."
            )
        chosen, how = _resolve_substitution_model(nxt, current_model)
        print(
            f"🔄 HARD AUTO-SUBSTITUTE: --agent {seat} → {nxt} "
            f"{_substitution_model_phrase(chosen, how, current_model)} "
            f"({why}; language-lane fallback stays inside claude, codex, agy).",
            file=sys.stderr,
        )
        _remember_agent_substitution(
            model_resolution,
            source="budget-guard",
            requested_agent=origin,
            requested_model=requested_model,
            actual_agent=nxt,
            actual_model=chosen,
            how=how,
        )
        current_model = chosen
        seen.add(nxt)
        seat = nxt
        if len(seen) > len(_LANGUAGE_LANES):
            raise BudgetGuardRefuseError("ROUTING REFUSED: language-lane fallback chain did not reach a cool seat.")


def _session_stream_store() -> Any:
    """Build the canonical read-only session-stream store used by fleet code."""
    from agents_extensions.shared.session_streams.db import DEFAULT_RELATIVE_DATABASE, SessionStreamDatabase
    from agents_extensions.shared.session_streams.store import SessionStreamStore

    return SessionStreamStore(SessionStreamDatabase(_REPO_ROOT / DEFAULT_RELATIVE_DATABASE))


def _find_live_cursor_driver_lease() -> dict[str, Any] | None:
    """Return one live Cursor process-driver lease, or ``None`` when absent.

    The session-stream database is the sole source of truth here. A missing
    store file means absence (no live lease), not refusal. An unreadable or
    malformed existing store still refuses admission rather than allowing an
    unverifiable Cursor spawn.
    """
    try:
        from agents_extensions.shared.session_streams.model import parse_timestamp

        store = _session_stream_store()
        database = getattr(store, "database", None)
        database_path = getattr(database, "path", None)
        if database_path is not None and not Path(database_path).is_file():
            return None

        projections = store.list_remote_projections()
        now = datetime.now(UTC)
        for projection in projections:
            if not isinstance(projection, dict):
                raise ValueError("session-stream projection is not an object")

            nested_lease = projection.get("lease")
            lease = nested_lease if isinstance(nested_lease, dict) else projection
            holder_agent = str(lease.get("holder_agent") or "").strip().lower()
            if holder_agent != "cursor":
                continue
            if str(lease.get("holder_harness") or "").strip().lower() != "cursor-agent":
                continue
            if str(lease.get("holder_kind") or "process").strip().lower() != "process":
                continue
            if str(lease.get("state") or "").strip().lower() != "active":
                continue
            session_state = str(lease.get("session_state") or projection.get("session_state") or "").strip().lower()
            if session_state not in {"open", "rolling"}:
                continue
            if lease.get("session_expired_at") or projection.get("session_expired_at"):
                continue

            expires_at = lease.get("expires_at")
            if not isinstance(expires_at, str) or not expires_at.strip():
                raise ValueError("Cursor lease has no expiry")
            if parse_timestamp(expires_at) > now:
                return lease
        return None
    except CapacityGuardRefuseError:
        raise
    except Exception as exc:
        raise CapacityGuardRefuseError(
            "CAPACITY REFUSED: unable to verify the session-stream store for a live Cursor driver lease; "
            "use --force-agent to override."
        ) from exc


def _proc_parent_pid(pid: int) -> int:
    """Return the parent pid of ``pid`` from Linux ``/proc``."""
    stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8", errors="replace")
    # comm is parenthesized and may contain spaces or ')'; the fields after the
    # final ')' are state, ppid, ...
    return int(stat.rsplit(")", 1)[1].split()[1])


def _process_is_self_or_ancestor(holder_pid: int) -> bool:
    """True when ``holder_pid`` is this process or one of its ancestors."""
    pid = os.getpid()
    seen: set[int] = set()
    while pid > 0 and pid not in seen:
        if pid == holder_pid:
            return True
        seen.add(pid)
        pid = _proc_parent_pid(pid)
    return False


def _cursor_driver_lease_is_self_dispatch(lease: dict[str, Any]) -> bool:
    """True only when the live Cursor driver lease belongs to this process tree.

    The documented rule refuses ``--agent cursor`` only from within the Cursor
    driver session itself (the self-dispatch deadlock case). A lease held on
    another host, or by an unrelated local process, is another lane's driver:
    concurrent Cursor workers are allowed. An ancestry lookup failure (no
    /proc, permission error) is treated as "not self" so dispatch never
    crashes on the probe.
    """
    holder_host_id = str(lease.get("holder_host_id") or "").strip().lower()
    if holder_host_id:
        try:
            try:
                from scripts.api.occupancy_local import resolve_launcher_host_id
            except ImportError:
                from api.occupancy_local import resolve_launcher_host_id

            local_host_id = resolve_launcher_host_id()
        except Exception:
            local_host_id = ""
        if local_host_id and holder_host_id != str(local_host_id).strip().lower():
            return False
    holder_pid = lease.get("holder_process_id")
    if not isinstance(holder_pid, int) or isinstance(holder_pid, bool) or holder_pid <= 0:
        return False
    try:
        return _process_is_self_or_ancestor(holder_pid)
    except Exception:
        print(
            "NOTE: unable to verify the Cursor driver lease holder ancestry; "
            "treating the live lease as another session and spawning --agent cursor.",
            file=sys.stderr,
        )
        return False


def _check_capacity_hint(dispatch_agent: str, args: argparse.Namespace | None = None) -> None:
    """Refuse Cursor driver-lease self-dispatch; otherwise retain the busy-lane hint."""
    target_norm = str(dispatch_agent or "").strip().lower()
    force_agent = bool(getattr(args, "force_agent", False)) if args is not None else False

    if target_norm == "cursor":
        try:
            cursor_driver_lease = _find_live_cursor_driver_lease()
        except CapacityGuardRefuseError:
            if not force_agent:
                raise
            print(
                "NOTE: --force-agent overrides Cursor driver-lease admission after the live lease check failed; "
                "spawning --agent cursor.",
                file=sys.stderr,
            )
        else:
            if cursor_driver_lease is not None:
                if _cursor_driver_lease_is_self_dispatch(cursor_driver_lease):
                    if not force_agent:
                        raise CapacityGuardRefuseError(
                            "CAPACITY REFUSED: --agent cursor dispatch from inside the live Cursor "
                            "driver session (the stream lease is held by this process tree); refusing "
                            "worker spawn. Dispatch from outside the Cursor driver session, or pass "
                            "--force-agent to override."
                        )
                    print(
                        "NOTE: --force-agent overrides the live Cursor driver stream lease; spawning --agent cursor.",
                        file=sys.stderr,
                    )
                else:
                    stream_id = str(cursor_driver_lease.get("stream_id") or "").strip() or "unknown stream"
                    print(
                        f"NOTE: Cursor driver live on {stream_id} (other session); spawning a separate Cursor worker.",
                        file=sys.stderr,
                    )

    if args is not None and (getattr(args, "json", False) or getattr(args, "quiet", False)):
        return

    with contextlib.suppress(Exception):
        try:
            from scripts.api.lane_health import compute_lane_health, normalize_agent_name
        except ImportError:
            from api.lane_health import compute_lane_health, normalize_agent_name

        from agent_runtime.agent_identity import RETIRED_AGENT_ALIASES
        from scripts.agent_runtime.kimi_admission import DirectoryTree

        # "gemini" excluded: it is a permanent retired-CLI alias (→ agy), so
        # it must never appear as a "idle capacity available in: gemini"
        # suggestion — that would just point drivers back at the dead CLI.
        # "kimi" is suggested only when this dispatch is web, UI or backend coding that a
        # Kimi seat would admit (default public repo, no refusal reason).
        target_norm = normalize_agent_name(dispatch_agent) or target_norm
        # A suggestion only: the owned paths are read in this checkout, not in a worker's tree.
        kimi_admissible = target_norm == "kimi" or (
            args is not None
            and getattr(args, "repo", None) is None
            and _kimi_admission_refusal(args, agent="kimi", trees=(DirectoryTree(_REPO_ROOT),)) is None
        )
        subscription_lanes = tuple(
            lane
            for lane in ("claude", "codex", "gemini", "grok", "cursor", "kimi")
            if lane not in RETIRED_AGENT_ALIASES and (lane != "kimi" or kimi_admissible)
        )

        in_flight: dict[str, int] = {lane: 0 for lane in subscription_lanes}
        if tasks_dir().is_dir():
            for state_file in tasks_dir().glob("*.json"):
                state = _read_state(state_file)
                if not state or state.get("status") not in ("running", "spawning"):
                    continue
                pid = state.get("pid")
                if pid and not _pid_alive(int(pid)):
                    continue
                agent_norm = normalize_agent_name(state.get("agent"))
                if agent_norm in in_flight:
                    in_flight[agent_norm] += 1

        busy_count = in_flight.get(target_norm, 0)
        if busy_count <= 0:
            return

        health: dict[str, Any] = {}
        with contextlib.suppress(Exception):
            health = compute_lane_health(tasks_dir())

        idle_lanes = [
            lane
            for lane in subscription_lanes
            if lane != target_norm and in_flight.get(lane, 0) == 0 and health.get(lane, {}).get("healthy", True)
        ]

        if idle_lanes:
            idle_str = ", ".join(idle_lanes)
            print(
                f"💡 Note: lane '{target_norm}' has {busy_count} task(s) in flight while idle capacity is available in: {idle_str}",
                file=sys.stderr,
            )


def _status_or_fail_payload(task_id: str, *, run_nonce: str | None = None) -> dict[str, Any]:
    payload = _fetch_monitor_task(task_id, run_nonce=run_nonce)
    if payload is None:
        return {"task_id": task_id, "status": "task not found", "age_s": 0}

    task = payload.get("task") if isinstance(payload.get("task"), dict) else {}
    status = str(task.get("status") or "unknown")
    if status == "running" and payload.get("alive") is False:
        status = "stale"
    result = {
        "task_id": task.get("task_id") or task_id,
        "status": status,
        "age_s": _age_seconds_from_started_at(task.get("started_at")),
        "alive": payload.get("alive"),
    }
    if run_nonce is not None:
        result["run_nonce"] = task.get("run_nonce")
    return result


def cmd_status_or_fail(args: argparse.Namespace) -> int:
    """Exit 0 only when Monitor API confirms a task is currently running."""
    run_nonce = getattr(args, "run_nonce", None)
    try:
        status = _status_or_fail_payload(args.task_id, run_nonce=run_nonce)
    except MonitorApiUnavailable as exc:
        print(f"Monitor API unreachable: {exc}", file=sys.stderr)
        return 2

    if getattr(args, "verbose", False):
        print(json.dumps(status, indent=2, default=str))

    if status["status"] == "running":
        return 0

    print(
        f"task {args.task_id} is not running (status={status['status']}, age={status['age_s']}s)",
        file=sys.stderr,
    )
    return 1


# ---------------------------------------------------------------------------
# Wait command — poll until terminal state or timeout
# ---------------------------------------------------------------------------

_TERMINAL_STATUSES = frozenset(
    {
        "done",
        "failed",
        "timeout",
        "rate_limited",
        "crashed",
        "cancelled",
        "dry_run",
        # A worker that settles as ``needs_finalize`` HAS finished — the status
        # flags leftover work for a human, it does not mean "still running".
        # Omitting it made ``delegate.py wait`` poll a finished task until its
        # own timeout, and made ``cancel`` willing to signal a stored PID the OS
        # may already have recycled. Worktree claims differ on purpose: a
        # ``needs_finalize`` record still claims its checkout for the leftover
        # work (see _RELEASED_TASK_STATUSES).
        "needs_finalize",
        _NO_DELIVERABLE_STATUS,
    },
)


def cmd_wait(args: argparse.Namespace) -> int:
    poll_interval = max(0.5, float(args.poll_interval))
    deadline = time.monotonic() + float(args.timeout) if args.timeout else None
    expected_nonce = getattr(args, "run_nonce", None)

    while True:
        state_path, state = _read_state_or_archived(args.task_id)
        if state is None:
            if expected_nonce is not None and (deadline is None or time.monotonic() < deadline):
                time.sleep(poll_interval)
                continue
            print(
                json.dumps({"error": f"no state file for task {args.task_id!r}"}),
            )
            return 1

        record_nonce = state.get("run_nonce")
        if expected_nonce is not None and record_nonce != expected_nonce:
            if deadline and time.monotonic() >= deadline:
                print(
                    json.dumps(
                        {
                            "error": "stale_run_nonce",
                            "task_id": args.task_id,
                            "expected_run_nonce": expected_nonce,
                            "record_run_nonce": record_nonce,
                            "last_known_status": state.get("status"),
                            "waited_s": args.timeout,
                        }
                    ),
                    file=sys.stderr,
                )
                return 1
            time.sleep(poll_interval)
            continue

        # Zombie probe (same logic as cmd_status)
        _heal_dead_task(state_path, state, source="wait")

        status = state.get("status")
        if status in _TERMINAL_STATUSES:
            print(json.dumps(state, indent=2, default=str))
            # Exit code: 0 if done, 1 otherwise (failed/crashed/rate_limited)
            if status == "timeout":
                return 124
            return 0 if status == "done" else 1

        if deadline and time.monotonic() >= deadline:
            print(
                json.dumps(
                    {
                        "error": "timeout",
                        "task_id": args.task_id,
                        "last_known_status": status,
                        "waited_s": args.timeout,
                    }
                ),
                file=sys.stderr,
            )
            return 124  # conventional timeout exit code

        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Cancel command — signal the worker
# ---------------------------------------------------------------------------


def cmd_cancel(args: argparse.Namespace) -> int:
    """Send SIGTERM to the worker's PID. Lets the runtime unwind cleanly.

    Refuses to signal a task whose status is already terminal (done,
    failed, crashed, cancelled, rate_limited). Otherwise we'd be
    signalling a PID that the OS may have recycled to some unrelated
    process. Codex 2026-04-10 audit finding.
    """
    state_path = _state_path(args.task_id)
    state = _read_state(state_path)
    if state is None:
        print(f"❌ no state file for task {args.task_id!r}", file=sys.stderr)
        return 1

    expected_nonce = getattr(args, "run_nonce", None)
    if expected_nonce is not None and state.get("run_nonce") != expected_nonce:
        print(
            f"❌ task {args.task_id!r} run_nonce mismatch (expected {expected_nonce!r}, "
            f"got {state.get('run_nonce')!r}); refusing to cancel unrelated worker",
            file=sys.stderr,
        )
        return 1

    status = state.get("status")
    if status in _TERMINAL_STATUSES:
        print(
            f"⚠️  task {args.task_id!r} is already in terminal state "
            f"{status!r}; refusing to signal the stored PID "
            f"(could be recycled by the OS).",
            file=sys.stderr,
        )
        return 1

    if status not in ("running", "spawning"):
        print(
            f"❌ task {args.task_id!r} has unexpected status {status!r}; refusing to cancel.",
            file=sys.stderr,
        )
        return 1

    pid = state.get("pid")
    if not pid:
        print(f"❌ state has no pid for {args.task_id!r}", file=sys.stderr)
        return 1

    pid = int(pid)
    if not _pid_alive(pid):
        print(f"⚠️  pid {pid} is already dead; nothing to cancel")
        return 0

    try:
        os.kill(pid, signal.SIGTERM)
        print(f"✅ SIGTERM sent to pid {pid}")
        return 0
    except PermissionError:
        print(f"❌ permission denied signalling pid {pid}", file=sys.stderr)
        return 1
    except ProcessLookupError:
        print(f"⚠️  pid {pid} vanished before we could signal it")
        return 0


# ---------------------------------------------------------------------------
# List command — show all tasks (for operators)
# ---------------------------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> int:
    """Print task summaries as a JSON list.

    History is bounded to the hot directory unless ``--all`` is given: records
    ``stale_task_records archive`` moved to ``archive/`` (#8625) are then listed
    too, marked ``"archived": true``. Without ``--all`` a stderr note counts the
    archived records left out.
    """
    tasks_dir().mkdir(parents=True, exist_ok=True)
    include_archive = bool(getattr(args, "all", False))
    tasks: list[dict[str, Any]] = []
    flat_tasks: list[str] = []
    for state_file in task_record_store.iter_task_records(tasks_dir(), include_archive=include_archive):
        state = _read_state(state_file)
        if state is None:
            continue
        # Zombie probe inline for running tasks
        _heal_dead_task(state_file, state, source="list")
        if args.status and state.get("status") != args.status:
            continue
        # Fix 4 (#1476): classify worktree layout so operators can see at
        # a glance which tasks are on the deprecated flat path.
        layout = state.get("worktree_layout") or _classify_worktree_layout(
            state.get("worktree_path"),
        )
        if layout == "flat":
            flat_tasks.append(str(state.get("task_id")))
        tasks.append(
            {
                "task_id": state.get("task_id"),
                "agent": state.get("agent"),
                "model": state.get("model"),
                "effort": state.get("effort"),
                "cli_version": state.get("cli_version"),
                "status": state.get("status"),
                "started_at": state.get("started_at"),
                "duration_s": state.get("duration_s"),
                "worktree_path": state.get("worktree_path"),
                "worktree_layout": layout,
                **({"archived": True} if state_file.parent.name == task_record_store.ARCHIVE_DIR_NAME else {}),
            }
        )
    print(json.dumps(tasks, indent=2, default=str))
    if not include_archive:
        archive_dir = tasks_dir() / task_record_store.ARCHIVE_DIR_NAME
        archived = sum(1 for _ in task_record_store.iter_task_records(archive_dir, include_archive=False))
        if archived:
            print(
                f"ℹ️  history is the hot directory only: {archived} archived record(s) not listed; pass --all.",
                file=sys.stderr,
            )
    if flat_tasks:
        print(
            f"⚠️  {len(flat_tasks)} task(s) use the DEPRECATED flat worktree "
            f"layout: {flat_tasks[:5]}" + (" …" if len(flat_tasks) > 5 else "") + ". New dispatches should use "
            "`.worktrees/dispatch/{agent}/{task}/`.",
            file=sys.stderr,
        )
    return 0


def cmd_backfill_repository(args: argparse.Namespace) -> int:
    """Stamp authoritative ``repository`` identity on legacy task states (#7083).

    Task states written before dispatch-time attribution have no
    ``repository`` / ``repository_id`` claim, so the public Work projection's
    repository-scoped delegate join (correctly) drops them and reports
    ``delegate_tasks.count=0``. This rewrites history the same way new
    dispatches stamp it: the target's git ``remote.origin.url`` is read by the
    owner of the state directory — never inferred by projection readers from
    paths, branches, or task ids.

    Dry-run by default; ``--apply`` performs the atomic write-rename updates.
    Existing claims are authoritative: consistent claims are kept, conflicting
    claims are reported and never overwritten. Targets whose repository cannot
    be proven stay unclassified.
    """
    apply_changes = bool(getattr(args, "apply", False))
    if not tasks_dir().is_dir():
        print(f"❌ tasks dir not found: {tasks_dir()}", file=sys.stderr)
        return 1
    scanned = stamped = already = unresolved = conflicts = errors = 0
    # Archived records (#8625) are history too; they are stamped where they lie.
    for state_file in task_record_store.iter_task_records(tasks_dir(), include_archive=True):
        state = _read_state(state_file)
        if state is None:
            continue
        scanned += 1
        task_id = str(state.get("task_id") or state_file.stem)
        claims = _state_repository_claims(state)
        if len(claims) == 1:
            already += 1
            continue
        if len(claims) > 1:
            conflicts += 1
            print(
                f"⚠️  {task_id}: conflicting repository claims {claims}; left untouched",
                file=sys.stderr,
            )
            continue
        target = state.get("worktree_path") or state.get("cwd")
        slug = _resolve_dispatch_repository(target)
        if slug is None:
            unresolved += 1
            print(
                f"⚠️  {task_id}: cannot prove repository from recorded target; left unclassified",
                file=sys.stderr,
            )
            continue
        if apply_changes:
            state["repository"] = slug
            try:
                _write_state_atomic(state_file, state)
            except OSError as exc:
                errors += 1
                print(f"❌ {task_id}: failed to write stamp: {exc}", file=sys.stderr)
                continue
        stamped += 1
        print(f"{'✅' if apply_changes else '🔎'} {task_id}: repository={slug}")
    mode = "apply" if apply_changes else "dry-run"
    print(
        f"repository backfill ({mode}): scanned={scanned} stamped={stamped} "
        f"already_attributed={already} unresolved={unresolved} "
        f"conflicts={conflicts} errors={errors}"
    )
    if not apply_changes and stamped:
        print("dry-run only — re-run with --apply to write these stamps")
    return 1 if errors else 0


# ---------------------------------------------------------------------------
# _worker command — internal, called by cmd_dispatch's spawned process
# ---------------------------------------------------------------------------


def cmd_worker(args: argparse.Namespace) -> int:
    """Internal entrypoint for the detached worker subprocess."""
    prompt = sys.stdin.read()
    return _run_worker(
        task_id=args.task_id,
        agent=args.agent,
        prompt=prompt,
        mode=args.mode,
        cwd_str=args.cwd,
        model=args.model,
        hard_timeout=args.hard_timeout,
        provider=getattr(args, "provider", None),
        output_schema_path=getattr(args, "output_schema", None),
        output_schema_sha256=getattr(args, "output_schema_sha256", None),
        harness=getattr(args, "harness", None),
        silence_timeout=args.silence_timeout,
        max_budget_usd=getattr(args, "max_budget_usd", None),
        effort=args.effort,
        initial_response_timeout=getattr(
            args,
            "initial_response_timeout",
            DEFAULT_INITIAL_RESPONSE_TIMEOUT_S,
        ),
        keep_worktree=bool(getattr(args, "keep_worktree", False)),
        require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
        runtime_tmp_root=getattr(args, "runtime_tmp_root", None),
        runtime_tmp_namespace_root=getattr(args, "runtime_tmp_namespace_root", None),
        run_nonce=getattr(args, "run_nonce", None) or os.environ.get("LU_RUNTIME_RUN_NONCE"),
        review_id=getattr(args, "review_id", None),
        attempt_id=getattr(args, "attempt_id", None),
        mcp_config_path=getattr(args, "mcp_config_path", None),
        strict_mcp_config=bool(getattr(args, "strict_mcp_config", False)),
        finalize_open_pr=bool(getattr(args, "finalize_open_pr", False)),
    )


# ---------------------------------------------------------------------------
# CLI glue
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="delegate.py",
        description=(
            "Dispatch async agent_runtime tasks and monitor their lifecycle.\n"
            "Use it for long-running background agent work; do not use it for one-shot local invocations."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/delegate.py dispatch --agent codex --task-id review-123 --prompt-file prompt.md --mode read-only\n"
            "  .venv/bin/python scripts/delegate.py dispatch --agent codex --task-id fix-123 --prompt-file brief.md --mode workspace-write --worktree\n"
            "  .venv/bin/python scripts/delegate.py dispatch --agent codex --task-id pr-123 --prompt-file brief.md --mode danger --worktree\n"
            "  .venv/bin/python scripts/delegate.py dispatch --agent claude --task-id review-456 --prompt-file brief.md --max-budget-usd 0.50\n"
            "  .venv/bin/python scripts/delegate.py status-or-fail review-123\n"
            "  .venv/bin/python scripts/delegate.py wait review-123 --timeout 600\n"
            "  .venv/bin/python scripts/delegate.py list --status running\n\n"
            "Outputs:\n"
            "  Persists task state under batch_state/tasks/ and streams worker output to task-owned logs.\n\n"
            "Timeouts:\n"
            "  --hard-timeout is the absolute wall-clock fallback for the worker.\n"
            "  --silence-timeout kills the agent CLI earlier when no watchdog activity arrives within the window.\n"
            f"    Default is {DEFAULT_SILENCE_TIMEOUT_S}s to tolerate quiet build/test phases; 0 disables it.\n\n"
            "  --max-budget-usd caps Claude Code API spend for this dispatch when set; omitted means no dollar cap.\n\n"
            "Placement & VPS Forwarding:\n"
            "  Dual-host occupancy routes dispatches to healthy VPS worker hosts when available.\n"
            "  Forwarding requires host environment variables in the launcher environment:\n"
            "    LU_JOB_DISPATCH_HOST (or ATLAS_RUNNER_HOST) and LU_JOB_REPO for host-job\n"
            "    LU_TEACHER_DISPATCH_HOST (or LU_DISPATCH_SSH) and LU_TEACHER_REPO for host-teacher\n"
            "  To bypass VPS forwarding and force local spawn: export LU_ALLOW_NOTEBOOK_DISPATCH=1\n"
            "  Configuration errors fail closed without fallback to prevent silent local drift.\n\n"
            "Exit codes:\n"
            "  0 on successful command completion; non-zero on CLI misuse or worker/task failures;\n"
            "  dispatch exits 3 when host admission refuses a write worker (see `dispatch --help`).\n\n"
            "Related:\n"
            "  Runtime: scripts/agent_runtime/\n"
            "  Rule: agents_extensions/shared/rules/delegate-must-use-worktree.md\n"
            "  Issue: #1379, #7230\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="command", required=True)

    rescue = sub.add_parser(
        "rescue",
        help="Inspect or preserve terminal dispatch work on rescue/<task>.",
        description=(
            "Preserve terminal non-success dispatch work on a verified rescue branch.\n"
            "Use after a worker exits; --all-stale previews candidates unless --apply is set."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/delegate.py rescue impl-8508\n"
            "  .venv/bin/python scripts/delegate.py rescue --all-stale --older-than 6h\n"
            "  .venv/bin/python scripts/delegate.py rescue --all-stale --older-than 6h --apply\n\n"
            "Outputs: JSON summary and task dispositions; apply may clean residue, commit, and push rescue refs.\n"
            "Exit codes: 0 inspection or rescue completed; 1 rescue error; 2 invalid arguments.\n"
            "Related: docs/runbooks/worktree-cleanup.md; issue #8508."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    rescue.add_argument("task_id", nargs="?", help="One terminal task ID, e.g. impl-8508; applies immediately.")
    rescue.add_argument("--all-stale", action="store_true", help="Inspect all terminal tasks older than --older-than.")
    rescue.add_argument("--older-than", default="6h", metavar="HOURS", help="Minimum terminal age (default: 6h).")
    rescue.add_argument(
        "--apply", action="store_true", help="Apply rescue to --all-stale candidates (default: dry-run)."
    )
    rescue.set_defaults(func=cmd_rescue)

    # dispatch
    def _dispatch_help_formatter(prog: str) -> argparse.HelpFormatter:
        return argparse.RawDescriptionHelpFormatter(prog, max_help_position=36, width=120)

    admission_defaults = dispatch_admission.config_defaults()
    d = sub.add_parser(
        "dispatch",
        help="Fire a task, return immediately (stdout: `<task_id>\\n<run_nonce>`)",
        description=(
            "Fire an async agent task and return immediately with the task ID and run nonce.\n"
            "Routes to available VPS worker hosts unless LU_ALLOW_NOTEBOOK_DISPATCH=1 is set.\n"
            "Forward configuration requires LU_JOB_DISPATCH_HOST (or ATLAS_RUNNER_HOST) and LU_JOB_REPO."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/delegate.py dispatch --agent codex --task-id fix-123 --prompt-file brief.md "
            "--mode workspace-write --worktree\n"
            "  DISPATCH_MAX_LIVE_WRITE_WORKERS=0 .venv/bin/python scripts/delegate.py dispatch --agent codex "
            "--task-id probe-1 --prompt x --mode workspace-write --worktree --dry-run\n"
            '  .venv/bin/python scripts/delegate.py dispatch ... --force-admission "hotfix for #1234; one worker is draining"\n\n'
            "Host admission (#8645; workspace-write and danger only, read-only is exempt):\n"
            "  Refuses a new worker when live write workers (running/spawning, pid alive) reach "
            f"DISPATCH_MAX_LIVE_WRITE_WORKERS (default {admission_defaults.max_live_write_workers}),\n"
            f"  /proc/meminfo MemAvailable is below DISPATCH_MIN_MEM_AVAILABLE_GIB (default "
            f"{admission_defaults.min_mem_available_gib:g} GiB), or the 1-minute load per CPU\n"
            f"  exceeds DISPATCH_MAX_LOAD_PER_CPU (default {admission_defaults.max_load_per_cpu:g}). "
            "Environment variables override the scripts/config.py defaults.\n"
            "  Without /proc (macOS) memory and CPU are unknown and only the worker cap applies. Records whose pid\n"
            "  is dead are marked crashed first. The final check holds a host-wide lock until the spawning record\n"
            "  is published. Preview the decision with: .venv/bin/python -m scripts.fleet.capacity_pick\n\n"
            "Outputs:\n"
            "  stdout `<task_id>\\n<run_nonce>`; batch_state/tasks/<task_id>.json (write modes carry an `admission`\n"
            "  snapshot; `launch_mode` is `scope` or `popen-fallback`; terminal records carry `peak_rss_mib`);\n"
            "  worker logs under batch_state/tasks/logs/. Workers run in the user slice lu-dispatch.slice when\n"
            "  that slice is installed with its memory limits; otherwise dispatch warns and uses plain Popen.\n"
            "  A scoped start that does not prove the worker never started is marked failed and is not relaunched.\n"
            "  LU_DISPATCH_ISOLATION=fallback forces the plain Popen path. See packaging/systemd/README.md.\n\n"
            "Exit codes:\n"
            "  0 dispatched, or --dry-run validated; 1 worktree, lease, or spawn failure;\n"
            "  2 invalid request or another guard refused; 3 host admission refused (retry later or --force-admission).\n\n"
            "Related:\n"
            "  scripts/orchestration/dispatch_admission.py; docs/bug-autopsies/2026-09-24-dispatch-fanout-oom.md; #8645\n"
        ),
        formatter_class=_dispatch_help_formatter,
    )
    d.add_argument(
        "--agent",
        required=True,
        choices=list(_DISPATCH_AGENT_CHOICES),
        # "qwen" removed from choices (banned agent): advertising it in --help
        # while the routing guard rejects it at dispatch is a UX trap. The
        # guard still catches programmatic Namespace bypass.
        help="Agent to run for the task: codex, gemini (retired CLI — permanent "
        "alias to agy, do not install gemini), claude, grok "
        "(native CLI; grok-build=alias), grok-hermes, deepseek, agy, cursor, or kimi "
        "(web, UI and backend coding only: workspace-write in site UI, scripts/ and tests/; "
        "Ukrainian-language content, reviews, consults, design and rules are refused).",
    )
    d.add_argument(
        "--harness",
        choices=sorted(_KIMI_HARNESSES),
        default=None,
        help=(
            "Opt-in Kimi transport. Only valid with --agent kimi; use kimicc "
            "for Kimi through headless Claude Code. Omit to keep native Kimi Code. "
            "'native' is observability-only: it records harness=native in task "
            "state and is functionally identical to omitting the flag (#5938)."
        ),
    )
    d.add_argument("--task-id", required=True, help="Stable task identifier used for state/log files, e.g. review-123.")
    d.add_argument(
        "--force-new",
        action="store_true",
        help=(
            "Reuse an existing --task-id by first archiving the prior record "
            "and result alongside (never clobber). Required when the task "
            "record is terminal and has the caller's initiator (#9075). "
            "Refuses nonterminal or foreign records even when their pid is dead."
        ),
    )
    d.add_argument(
        "--force-admission",
        metavar="REASON",
        default=None,
        help=(
            "Start a write-capable worker even when host admission refuses it (live write-worker cap, "
            "MemAvailable floor, or load per CPU; #8645). REASON is required and is recorded in the "
            "task record under admission.force_reason."
        ),
    )
    d.add_argument(
        "--initiator",
        default=None,
        help=(
            "Initiating orchestrator identity for runtime attribution. Launcher "
            "and Codex Desktop identity are detected automatically when omitted."
        ),
    )
    d.add_argument(
        "--run-nonce",
        default=None,
        help="Unique run identifier for detecting stale cross-host task records (#7168).",
    )
    d.add_argument("--prompt", help="Prompt text, or '-' to read the prompt from stdin.")
    d.add_argument("--prompt-file", help="Read the prompt body from this file path.")
    d.add_argument(
        "--allow-dor-warn",
        metavar="REASON",
        help="Allow an implementation dispatch with a WARN issue card; record the required reason in task JSON.",
    )
    d.add_argument(
        "--lifecycle-file",
        help=(
            "Canonical task-lifecycle.v1 ledger to validate and carry in the worker prompt/state. "
            "Invalid ledgers fail before worktree or worker side effects."
        ),
    )
    d.add_argument(
        "--mode",
        default="read-only",
        choices=["read-only", "workspace-write", "danger"],
        help="Runtime mode (default: read-only). Read-only rejects write-shaped "
        "prompts; workspace-write and danger "
        "require a verified dispatch worktree (bare --worktree, or --cwd "
        "pointing at an existing added worktree); read-only may run from repo root.",
    )
    d.add_argument("--model", default=None, help="Optional model override, e.g. gpt-6-sol or gemini-3.1-pro-preview.")
    d.add_argument(
        "--provider",
        default=None,
        choices=["openrouter"],
        help="Opt-in provider for Hermes-routed agents (e.g. deepseek). "
        "Default for DeepSeek is first-party (local-only). "
        "Use --provider openrouter for US-residency pinned path.",
    )
    d.add_argument(
        "--effort",
        default=None,
        choices=["low", "medium", "high", "xhigh", "max"],
        help=(
            "Optional reasoning / effort level. Accepted: low, medium, "
            "high, xhigh, max. Omit to use the agent's own default: "
            "Codex falls through to ~/.codex/config.toml (currently high); "
            "Claude falls through to its CLI default (currently high for "
            "Opus/Sonnet 4.6+ per CC 1.117); Gemini effort is not yet "
            "wired (gemini-cli does not expose the flag) and is a no-op. "
            "See #1396."
        ),
    )
    d.add_argument(
        "--repo",
        default=None,
        metavar="KEY",
        help=(
            "Allowlisted fleet repository for worktree creation and GitHub "
            "targeting (#672 P2.1). Keys come from scripts/config/fleet_repos.yaml "
            "(public, infra-private, hramatka). Default: public primary. Sibling "
            "write modes require --worktree (auto) or --cwd; task state stays on the "
            "public primary control plane. Legacy manual sibling --cwd flow remains valid."
        ),
    )
    d.add_argument(
        "--cwd",
        default=None,
        help="Working directory for the worker (read-only defaults to a detached dispatch worktree; "
        "pass --cwd explicitly to use the primary checkout). "
        "For workspace-write/danger it must be a verified added "
        "worktree, never the primary checkout — prefer --worktree. "
        "Sibling-repo flow: prefer `--repo KEY --worktree`, or manual "
        "`git worktree add` then `--cwd <that-worktree>` without `--worktree`.",
    )
    d.add_argument(
        "--worktree",
        nargs="?",
        const="auto",
        default=None,
        help=(
            "Run inside this git worktree (created on demand). Required for "
            "write-capable modes (workspace-write, danger). Pass `--worktree` "
            "alone (recommended) to auto-derive `.worktrees/dispatch/{agent}/"
            "{task}/` under the primary checkout that owns this script, or "
            "`--worktree PATH` to reuse a specific added worktree inside "
            "`.worktrees/dispatch/{agent}/` (validated against the expected "
            "dispatch branch before reuse; paths elsewhere, under a symlinked "
            "anchor, or with control or format characters are refused, #8775). "
            "Refuses when the invocation cwd is a different git root (#6900)."
        ),
    )
    d.add_argument(
        "--pr",
        type=int,
        default=None,
        help=(
            "Review this same-repo PR. The head SHA is resolved once and pinned; "
            "a later fetch of a different tip refuses the dispatch."
        ),
    )
    d.add_argument(
        "--pinned-head",
        default=None,
        metavar="SHA",
        help=(
            "Exact commit the worktree must check out. A fetched branch tip that "
            "differs from this SHA refuses the dispatch."
        ),
    )
    d.add_argument(
        "--branch",
        default=None,
        metavar="EXISTING",
        help=(
            "Attach the dispatch to this existing remote branch instead of creating "
            "{agent}/{task}. Fetches and validates the branch from the primary "
            "checkout, then creates/reuses an isolated worktree on it (--branch "
            "implies --worktree). Refuses protected branches (main/master), "
            "branches checked out in another worktree, and invocation from a "
            "different git root (#6900). --branch must omit origin/ and refs/ prefixes."
        ),
    )
    d.add_argument(
        "--keep-worktree",
        action="store_true",
        help=(
            "Keep a successful clean dispatch worktree instead of reaping it "
            "after the branch is recoverable from origin or PR state."
        ),
    )
    d.add_argument(
        "--finalize-open-pr",
        action="store_true",
        help="Explicitly open a draft PR after a successful dirty-worktree auto-finalize push.",
    )
    d.add_argument(
        "--require-review-verdict",
        action="store_true",
        help=(
            "Review-typed dispatch: a run that settles done without a "
            "`VERDICT: APPROVE|APPROVED|CHANGES_REQUESTED|REQUEST_CHANGES|BLOCKED` line of its own in the "
            "reply terminalizes as no_deliverable instead (#8421). Used by the "
            "ask-* review wrapper; ordinary dispatches are unaffected. "
            "On agy/gemini this also requires --review-profile ukrainian, and "
            "a --branch target must be a Ukrainian-content diff."
        ),
    )
    d.add_argument(
        "--review-profile",
        default=None,
        choices=("code", "ukrainian"),
        help=(
            "Required with --require-review-verdict when --agent is agy or gemini. "
            "code is refused (Gemini reviews Ukrainian only, never code — "
            "operator 2026-09-25). Ukrainian content review must pass ukrainian."
        ),
    )
    d.add_argument(
        "--review-attempt",
        default=None,
        metavar="MANIFEST",
        help=(
            "Path to manifest YAML file for formal review attempt recording (#8517). "
            "Used together with --review-id and --attempt-id to launch a per-attempt "
            "stdio sources MCP server with ledger receipts. Default: None. "
            "Example: --review-attempt batch_state/manifests/rev-1.yaml"
        ),
    )
    d.add_argument(
        "--review-id",
        default=None,
        metavar="REVIEW_ID",
        help=(
            "Formal review identifier for receipt recording (#8517). Required when "
            "--review-attempt is set; must match the review id in receipt paths. "
            "Default: None. Example: --review-id rev-20260922-001"
        ),
    )
    d.add_argument(
        "--attempt-id",
        default=None,
        metavar="ATTEMPT_ID",
        help=(
            "Unique attempt identifier for receipt recording (#8517). Required when "
            "--review-attempt is set; names the attempt ledger <attempt_id>.jsonl. "
            "Default: None. Example: --attempt-id att-01"
        ),
    )
    d.add_argument(
        "--full-checkout",
        action="store_true",
        help=(
            "Materialize the full git working tree in the dispatch worktree. "
            "Default cone sparse-checkout excludes curriculum/ (289MB), wiki/ (66MB), "
            "data/projects/ (633MB), data/lexicon/ (277MB), and registry/projects/ "
            "while retaining registry/lexicon/, leaving a default "
            "worktree under 450MB. Use this when the task needs the entire tree."
        ),
    )
    d.add_argument(
        "--sparse-include",
        action="append",
        default=None,
        metavar="DIR",
        help=(
            "Keep a tree that default sparse-checkout would exclude "
            "(curriculum, wiki, data/projects, data/lexicon, registry/projects). Repeatable. "
            "Example: --sparse-include data/projects, or --sparse-include registry/projects "
            "for module content. Owned paths under those trees are included automatically."
        ),
    )
    d.add_argument(
        "--base",
        default="main",
        help=(
            "Base branch to fetch and branch the worktree from "
            "(default: main). The worktree is branched from "
            "origin/{base}, not local {base}."
        ),
    )
    d.add_argument(
        "--allow-merge",
        action="store_true",
        help=(
            "Opt in to allow PR approval/merge and pushes to main inside the "
            "delegated subprocess. Default is off: AGENT_NO_MERGE=1 is set."
        ),
    )
    d.add_argument(
        "--language-lane",
        action="store_true",
        help=(
            "This dispatch authors, reviews, critiques, settles, or judges Ukrainian language, "
            "culture, or heritage content. Only claude, codex (GPT), and agy (Gemini) are admitted."
        ),
    )
    d.add_argument(
        "--check-budget",
        action="store_true",
        help=(
            "Query /api/state/routing-budget before spawning; hard-sub or refuse "
            "when the requested lane is near_cap/hot/deficit; prepaid DeepSeek/OpenRouter "
            "also refuse unknown, stale or empty funding. Also enabled when "
            "LU_DISPATCH_CHECK_BUDGET=1 (launchers can force without flag churn)."
        ),
    )
    d.add_argument(
        "--force-agent",
        action="store_true",
        help=(
            "Suppress --check-budget / LU_DISPATCH_CHECK_BUDGET routing guard and dispatch with the requested agent; "
            "also overrides a live Cursor driver-lease refusal with a NOTE."
        ),
    )
    d.add_argument(
        "--dry-run",
        action="store_true",
        help="Run dispatch pre-flight checks and print task-id without spawning a worker.",
    )
    d.add_argument(
        "--hard-timeout",
        type=int,
        default=DEFAULT_HARD_TIMEOUT_S,
        help=(
            "Absolute wall-clock seconds for the worker before the runtime "
            f"hard-kills it (default: {DEFAULT_HARD_TIMEOUT_S}). "
            f"--silence-timeout defaults to {DEFAULT_SILENCE_TIMEOUT_S}s and catches "
            "stdout-silent hangs sooner."
        ),
    )
    d.add_argument(
        "--silence-timeout",
        type=int,
        metavar="SECS",
        default=DEFAULT_SILENCE_TIMEOUT_S,
        help=(
            "Seconds without subprocess watchdog activity before killing the agent "
            "CLI and marking the task status='timeout' "
            f"(default: {DEFAULT_SILENCE_TIMEOUT_S}s; 0 disables). "
            "Watchdog activity includes stdout/stderr, liveness-file updates, "
            "and process-tree CPU/disk activity. --hard-timeout still applies as the "
            "absolute wall-clock fallback."
        ),
    )
    d.add_argument(
        "--initial-response-timeout",
        type=int,
        metavar="SECS",
        default=DEFAULT_INITIAL_RESPONSE_TIMEOUT_S,
        help=(
            "Startup probe: kill the agent CLI if it produces no "
            "observable startup activity (stdout, stderr, liveness file, or "
            "process-tree CPU/disk work) within this many seconds "
            f"(default: {DEFAULT_INITIAL_RESPONSE_TIMEOUT_S}; 0 disables). "
            "Distinct from --silence-timeout, which watches composite "
            "activity after startup (#2071, #3875)."
        ),
    )
    d.add_argument(
        "--max-budget-usd",
        type=float,
        default=None,
        help=(
            "Optional Claude Code dollar cap for this dispatch. Only Claude "
            "translates this to a CLI flag; non-Claude adapters warn and "
            "ignore it. Omit to run uncapped."
        ),
    )
    d.add_argument(
        "--output-schema",
        default=None,
        metavar="FILE",
        help=(
            "Bind a JSON Schema to the final response of an effective Codex "
            "dispatch. The file is parsed before spawn, resolved to an "
            "absolute path, hashed into task state, and revalidated by the "
            "Codex adapter before it emits --output-schema."
        ),
    )
    d.add_argument(
        "--research-role",
        default=None,
        metavar="ROLE",
        help=(
            "ADR-011 P3 research context: the task's single role (e.g. quality). "
            "Explicit only — never inferred from the prompt, agent, provider, or "
            "branch. Combined with the other --research-* flags, injects bounded, "
            "pointer-only research pointers (bodies fetched on demand)."
        ),
    )
    d.add_argument(
        "--research-task-family",
        default=None,
        metavar="FAMILY",
        help="ADR-011 P3 research context: the task's single task family (e.g. difficulty-gate).",
    )
    d.add_argument(
        "--research-track",
        default=None,
        metavar="TRACK",
        help="ADR-011 P3 research context: the task's single track (e.g. core).",
    )
    d.add_argument(
        "--research-owned-path",
        action="append",
        default=None,
        metavar="GLOB",
        help=(
            "ADR-011 P3 research context: an owned/changed path for the task. "
            "Repeatable. Matched against each record's owned_paths globs. "
            "Also feeds the writable-path admission guard (#5643)."
        ),
    )
    d.add_argument(
        "--owned-path",
        action="append",
        default=None,
        metavar="PATH",
        help=(
            "#8991: a repo-relative path (dir/, dir/**, file, or glob) this task may "
            "commit. Repeatable; recorded as the task's owned_paths. Auto-finalize of a "
            "dirty danger-mode worktree commits only changes under these paths; without "
            "any it commits nothing and the task ends needs_finalize. Independent of "
            "--research-owned-path."
        ),
    )
    d.add_argument(
        "--allow-path-overlap",
        default=None,
        metavar="REASON",
        help=(
            "Explicitly admit a write-capable dispatch that intersects another "
            "active claim. Records task, conflicts, reason, and caller in the "
            "ownership ledger. Required text reason; empty string is ignored."
        ),
    )
    d.add_argument(
        "--preflight-triage",
        action="store_true",
        help=(
            "#8183: before spawning, run cheap TypeSafe/Jev readiness triage on the candidate "
            "diff (+ local test log). A confident broken_or_failing verdict exits 3 without "
            "starting a worker. Missing key or API failure skips (dispatch proceeds)."
        ),
    )
    d.add_argument(
        "--preflight-base",
        default=None,
        metavar="REF",
        help="Base ref for the --preflight-triage diff (default: origin/main).",
    )
    d.add_argument(
        "--preflight-test-log",
        default=None,
        metavar="PATH",
        help="Local test log for --preflight-triage (default: <cwd>/.preflight-test.log if present).",
    )
    d.set_defaults(func=cmd_dispatch)

    # status
    s = sub.add_parser(
        "status",
        help="Check task status from local state (fast, no block)",
        description=(
            "Check task status from local batch_state. For guardrails that "
            "must fail when a task is no longer running, use status-or-fail."
        ),
    )
    s.add_argument("task_id", help="Task ID to inspect, e.g. review-123.")
    s.add_argument(
        "--run-nonce",
        default=None,
        help="Expected run nonce to detect stale records from prior rounds (#7168).",
    )
    s.set_defaults(func=cmd_status)

    # status-or-fail
    sof = sub.add_parser(
        "status-or-fail",
        help="Exit 0 only if Monitor API says task is running",
        description=(
            "Verify a delegated task through the Monitor API and exit 0 only when it is running.\n"
            "Use it in guardrails before trusting stale async-task claims; do not use it when the API may be offline."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/delegate.py status-or-fail review-123\n"
            "  .venv/bin/python scripts/delegate.py status-or-fail review-123 --verbose\n\n"
            "Exit codes:\n"
            "  0 Monitor API confirms the task is running.\n"
            "  1 Task is not running, done, missing, or stale.\n"
            "  2 Monitor API is unreachable.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sof.add_argument("task_id", help="Task ID to verify, e.g. review-123.")
    sof.add_argument(
        "--run-nonce",
        default=None,
        help="Expected run nonce to verify against the running task (#7168).",
    )
    sof.add_argument(
        "--verbose",
        action="store_true",
        help="Print structured status JSON before exiting.",
    )
    sof.set_defaults(func=cmd_status_or_fail)

    # wait
    w = sub.add_parser("wait", help="Block until task reaches terminal state")
    w.add_argument("task_id", help="Task ID to wait for, e.g. review-123.")
    w.add_argument("--timeout", type=float, default=0, help="Max wait seconds (0 = forever)")
    w.add_argument("--poll-interval", type=float, default=2.0, help="Poll interval seconds (default: 2.0)")
    w.add_argument(
        "--run-nonce",
        default=None,
        help="Expected run nonce to verify before accepting terminal status (#7168).",
    )
    w.set_defaults(func=cmd_wait)

    # cancel
    c = sub.add_parser("cancel", help="SIGTERM the worker")
    c.add_argument("task_id", help="Task ID to cancel, e.g. review-123.")
    c.add_argument(
        "--run-nonce",
        default=None,
        help="Expected run nonce to verify before cancelling worker (#7168).",
    )
    c.set_defaults(func=cmd_cancel)

    # list
    l = sub.add_parser("list", help="List tasks (with optional status filter)")
    l.add_argument(
        "--all",
        action="store_true",
        help="Also list records archived into batch_state/tasks/archive/ (#8625); default is the hot directory only.",
    )
    l.add_argument(
        "--status",
        default=None,
        choices=[
            "spawning",
            "running",
            "done",
            "failed",
            "timeout",
            "rate_limited",
            "crashed",
            "cancelled",
            "needs_finalize",
            _NO_DELIVERABLE_STATUS,
            "dry_run",
        ],
        help="Optional status filter, e.g. running or failed.",
    )
    l.set_defaults(func=cmd_list)

    # backfill-repository
    bf = sub.add_parser(
        "backfill-repository",
        help="Stamp authoritative repository identity on legacy task states (#7083); dry-run unless --apply",
    )
    bf.add_argument(
        "--apply",
        action="store_true",
        help="Write the stamps (default is a dry-run report).",
    )
    bf.set_defaults(func=cmd_backfill_repository)

    # _worker (hidden — internal)
    wk = sub.add_parser("_worker", help=argparse.SUPPRESS)
    wk.add_argument("--task-id", required=True)
    wk.add_argument("--agent", required=True)
    wk.add_argument("--harness", choices=sorted(_KIMI_HARNESSES), default=None)
    wk.add_argument("--mode", required=True)
    wk.add_argument("--cwd", required=True)
    wk.add_argument("--model", default=None)
    wk.add_argument("--provider", default=None)
    wk.add_argument(
        "--effort",
        default=None,
        choices=["low", "medium", "high", "xhigh", "max"],
    )
    wk.add_argument("--hard-timeout", type=int, default=DEFAULT_HARD_TIMEOUT_S)
    wk.add_argument("--silence-timeout", type=int, default=DEFAULT_SILENCE_TIMEOUT_S)
    wk.add_argument(
        "--initial-response-timeout",
        type=int,
        default=DEFAULT_INITIAL_RESPONSE_TIMEOUT_S,
    )
    wk.add_argument("--keep-worktree", action="store_true")
    wk.add_argument("--finalize-open-pr", action="store_true")
    wk.add_argument("--require-review-verdict", action="store_true")
    wk.add_argument("--max-budget-usd", type=float, default=None)
    wk.add_argument("--output-schema", default=None)
    wk.add_argument("--output-schema-sha256", default=None)
    wk.add_argument("--runtime-tmp-root", default=None)
    wk.add_argument("--runtime-tmp-namespace-root", default=None)
    wk.add_argument("--run-nonce", default=None)
    wk.add_argument("--review-id", default=None)
    wk.add_argument("--attempt-id", default=None)
    wk.add_argument("--mcp-config-path", default=None)
    wk.add_argument("--strict-mcp-config", action="store_true")
    wk.set_defaults(func=cmd_worker)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
