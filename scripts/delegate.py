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
        --prompt "do the thing" [--mode workspace-write --worktree] [--model gpt-5.6-terra]
        [--allow-merge]

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
        "agent": str,
        "model": str,
        "effort": str,
        "cli_version": str,
        "mode": str,
        "pid": int,
        "status": "running" | "done" | "failed" | "timeout" | "rate_limited" | "crashed",
        "started_at": iso-8601 UTC,
        "finished_at": iso-8601 UTC | null,
        "duration_s": float | null,
        "prompt_chars": int,
        "response_chars": int | null,
        "result_file": str | null,   # path to the full response text
        "stderr_excerpt": str | null,
        "returncode": int | null,
        "returncode_reason": str | null
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

Issue: #1184.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from agent_runtime.routes import RUNTIME_ROUTE_TOOL_CONFIG_KEY

# Resolve repo root from this file's location so we work from any cwd —
# then hop to the primary checkout so worktree copies behave identically.
_local_repo_root = Path(__file__).resolve().parents[1]
if str(_local_repo_root) not in sys.path:
    sys.path.insert(0, str(_local_repo_root))

from scripts.common.repo_root import main_checkout_root as _main_checkout_root
from scripts.common.repo_root import resolve_repo_root

_REPO_ROOT = resolve_repo_root(Path(__file__), 1)
_TASKS_DIR = _REPO_ROOT / "batch_state" / "tasks"
_BASH_SECRETS_PATH = Path.home() / ".bash_secrets"
_GH_TOKEN_AGENTS = {"codex", "claude", "bridge"}
_FALLBACK_SUBS_PATH = _REPO_ROOT / "scripts" / "config" / "agent_fallback_substitutions.yaml"
# Single source for dispatchable agents: argparse choices AND the hard-sub
# validation in _resolve_agent_with_budget_guard (a yaml typo must never
# dispatch a nonexistent adapter).
_DISPATCH_AGENT_CHOICES = (
    "codex",
    "gemini",
    "claude",
    "grok",  # canonical native CLI seat
    "grok-build",  # permanent alias → grok
    "grok-hermes",  # demoted Hermes path
    "kimi",  # managed native kimi-code CLI seat; no automatic fallback chain
    "deepseek",
    "agy",
    "cursor",
)
_MONITOR_API_BASE_URL = "http://localhost:8765"
_logger = logging.getLogger(__name__)


def _read_github_token_from_bash_secrets(path: Path | None = None) -> str | None:
    """Read GITHUB_TOKEN from a shell env file without executing it."""
    path = path or _BASH_SECRETS_PATH
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None
    except OSError:
        return None

    for line in lines:
        try:
            parts = shlex.split(line, comments=True, posix=True)
        except ValueError:
            continue
        if not parts:
            continue
        if parts[0] == "export":
            parts = parts[1:]
        for part in parts:
            if part.startswith("GITHUB_TOKEN="):
                value = part.split("=", 1)[1]
                return value or None
    return None


def _resolve_github_token() -> str | None:
    """Resolve the GitHub token used for GH_TOKEN pass-through."""
    return os.environ.get("GITHUB_TOKEN") or _read_github_token_from_bash_secrets() or os.environ.get("GH_TOKEN")


def _inject_gh_token_for_agent(worker_env: dict[str, str], agent: str) -> None:
    """Expose GH_TOKEN only to agents allowed to run authenticated gh."""
    worker_env.pop("GITHUB_TOKEN", None)
    if agent not in _GH_TOKEN_AGENTS:
        worker_env.pop("GH_TOKEN", None)
        return

    token = _resolve_github_token()
    if token:
        worker_env["GH_TOKEN"] = token
        return

    # No GH_TOKEN env var available — that's fine. Codex/Claude inherit the
    # user's interactive `gh auth` via the gh CLI keyring; the env var is a
    # belt-and-suspenders extra, not a requirement. User confirmed 2026-05-16:
    # the previous warning was noise. Removing it.
    worker_env.pop("GH_TOKEN", None)


DEFAULT_HARD_TIMEOUT_S = 7200
# Silence timeout is a composite hang backstop: stdout/stderr, liveness-file
# updates, and process-tree CPU/disk activity all keep it alive. Do not lower it
# for build/test/enrich jobs merely because wrapper stdout is expected to be
# quiet; that recreates the false-kill shape from #3875.
DEFAULT_SILENCE_TIMEOUT_S = 3600
# Fail fast when Codex (or any agent) never produces stdout/stderr/liveness
# activity at startup — distinct from the long silence window above (#2071).
DEFAULT_INITIAL_RESPONSE_TIMEOUT_S = 180


# ---------------------------------------------------------------------------
# State file helpers
# ---------------------------------------------------------------------------


def _state_path(task_id: str) -> Path:
    _TASKS_DIR.mkdir(parents=True, exist_ok=True)
    # task-ids with slashes would break paths; sanitize
    safe = task_id.replace("/", "_").replace("\\", "_")
    return _TASKS_DIR / f"{safe}.json"


def _write_state_atomic(path: Path, state: dict[str, Any]) -> None:
    """Write state JSON atomically via write-rename.

    os.replace() is atomic on POSIX, so concurrent readers never see
    a partially-written file. Ensures the parent directory exists
    before writing — callers that bypass _state_path may not have
    created it yet.

    Concurrency: each writer uses a PID-suffixed tmp filename so
    multiple concurrent writers (e.g. two operators both running
    status on the same zombie task) don't collide on a shared
    ``.json.tmp`` scratch file. Without the PID suffix, one writer's
    os.replace() would move the tmp file out from under another
    writer that's still writing to it, causing FileNotFoundError on
    the second os.replace. Fixed after Gemini review 2026-04-10.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".json.tmp.{os.getpid()}")
    tmp.write_text(json.dumps(state, indent=2, default=str))
    os.replace(tmp, path)


def _append_dispatch_event(event: str, **fields: Any) -> None:
    """Append one delegate JSONL event without making telemetry fatal."""
    payload = {
        "ts": datetime.now(UTC).isoformat(),
        "event": event,
        **fields,
    }
    try:
        _TASKS_DIR.mkdir(parents=True, exist_ok=True)
        line = (json.dumps(payload, ensure_ascii=False, default=str) + "\n").encode("utf-8")
        fd = os.open(
            str(_TASKS_DIR / "dispatch_events.jsonl"),
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


def _read_state(path: Path) -> dict[str, Any] | None:
    """Read a state file; return None if missing or corrupted."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
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


def _normalize_worktree_path(raw_path: str) -> Path:
    """Resolve a worktree path relative to the repo root."""
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path.resolve()


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
    """
    namespace_root = Path(tempfile.gettempdir()) / "learn-ukrainian"
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
    return resolved_lease, resolved_namespace


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
            resolved_tmp_root = Path(runtime_tmp_base_root).resolve(strict=True)
        if resolved_namespace.parent != resolved_tmp_root:
            raise ValueError(
                "resolved runtime tmp namespace is not directly under $TMPDIR",
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
        open_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        if hasattr(os, "O_NOFOLLOW"):
            open_flags |= os.O_NOFOLLOW
        namespace_fd = os.open(namespace, open_flags)
        try:
            # Passing a basename plus dir_fd keeps the deletion anchored to
            # the verified namespace even if an ancestor changes afterwards.
            shutil.rmtree(lease.name, dir_fd=namespace_fd)
        finally:
            os.close(namespace_fd)
        result["tmp_bytes_freed"] = bytes_freed
    except Exception as exc:
        result["tmp_reap_error"] = (
            f"{type(exc).__name__}: {exc}"
        )[:500]
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


def _auto_worktree_path(agent: str, task_id: str) -> Path:
    """Default worktree path for a fresh dispatch: ``.worktrees/dispatch/{agent}/{task}/``."""
    normalized = _normalize_task_id(agent, task_id)
    # Slashes are fine in branch names but not in a single path component,
    # so flatten them here (task_id ``foo/bar`` → path ``foo-bar``).
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized).strip("./-") or "task"
    return _REPO_ROOT / ".worktrees" / "dispatch" / agent / safe


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
# *remembering* the worktree rule. ``read-only`` dispatches are exempt: repo-root
# preflight and creating a worktree from the primary checkout stay allowed.

_WRITE_CAPABLE_MODES = frozenset({"workspace-write", "danger"})

_WRITE_WORKTREE_HINT = (
    "Write-capable dispatch must run inside a dispatch worktree, never the "
    "primary checkout. Preferred: pass bare `--worktree` to auto-create "
    ".worktrees/dispatch/<agent>/<task>/. Alternatively point `--cwd` at an "
    "existing added worktree there."
)


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


def _resolve_cwd_path(raw: str) -> Path:
    """Resolve a ``--cwd`` argument the way the spawned worker will see it.

    A relative ``--cwd`` is handed to the worker subprocess verbatim and thus
    resolved against the dispatch process cwd, so classify it the same way.
    """
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return p.resolve()


def _is_verified_added_worktree(path: Path) -> bool:
    """True if ``path`` resolves inside a git-registered worktree that is not the
    primary checkout.

    "Verified" means the containing worktree appears in ``git worktree list``. A
    bare directory that only *looks* like ``.worktrees/**`` but was never
    ``git worktree add``-ed does NOT qualify — the worker would otherwise run
    outside any real worktree while believing it was isolated.
    """
    wc = _load_worktree_containment()
    target = wc.canonicalize(path)
    start = target if target.exists() else target.parent
    try:
        main_root = wc.resolve_main_root(start)
    except wc.NotAGitRepositoryError:
        return False
    for worktree in wc.registered_worktrees(main_root):
        if worktree == main_root:
            continue
        if target == worktree or target.is_relative_to(worktree):
            return True
    return False


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

    entries = status.get("entries") or []
    return (
        "❌ primary checkout is dirty; refusing write-capable dispatch before "
        "creating branch/worktree residue.\n"
        f"   cwd: {status.get('checked_cwd')}\n"
        f"   command: {status.get('checked_command')}\n"
        f"   branch: {status.get('branch')}\n"
        f"   dirty files: {_format_dirty_entries(entries)}\n"
        "   Clean/stash the primary checkout, or keep only gitignored local "
        "runtime state, then retry."
    )


def _fetch_base(base: str) -> bool:
    """Fetch ``origin/{base}``. Returns True iff the remote ref is resolvable.

    ``base`` may be a plain branch name (``main``) or an origin-prefixed ref
    (``origin/main`` — the form the dispatch runbooks mandate). The remote
    refspec is always the plain branch: ``git fetch origin origin/main`` asks
    the remote for a ref literally named ``origin/main``, which does not
    exist, so the fetch fails and callers silently fall back to the local
    (possibly stale) remote-tracking ref.
    """
    branch = _base_branch_name(base)
    proc = subprocess.run(
        ["git", "fetch", "origin", branch],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return False
    verify = subprocess.run(
        ["git", "rev-parse", "--verify", f"origin/{branch}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return verify.returncode == 0


def _validate_branch_reuse_name(branch: str) -> str:
    """Reject unsafe or ambiguous ``--branch`` values before touching git."""
    normalized = branch.strip()
    if not normalized:
        raise ValueError("--branch must name an existing non-protected branch")
    if normalized.startswith(("origin/", "refs/")):
        raise ValueError(
            "--branch must be a local branch name without origin/ or refs/ prefixes: "
            f"got {branch!r}"
        )

    containment = _load_worktree_containment()
    if normalized in containment.PROTECTED_BRANCHES:
        raise ValueError(
            f"refusing --branch {normalized!r}: protected branches may not be "
            "attached to a dispatch worktree"
        )
    return normalized


def _fetch_existing_branch(branch: str) -> None:
    """Fetch and verify the remote branch used by ``--branch`` reuse mode."""
    proc = subprocess.run(
        ["git", "fetch", "origin", branch],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=_sanitized_git_env(),
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"could not fetch existing branch {branch!r}: {_format_process_failure(proc)}"
        )
    verify = subprocess.run(
        ["git", "rev-parse", "--verify", f"origin/{branch}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=_sanitized_git_env(),
    )
    if verify.returncode != 0:
        raise RuntimeError(
            f"origin/{branch} was not found after fetch; --branch requires an existing remote branch"
        )


def _branch_worktree_paths(branch: str) -> list[Path]:
    """Return registered worktree roots currently attached to ``branch``."""
    proc = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=_sanitized_git_env(),
    )
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


def _resolve_sha(path: Path, ref: str = "HEAD") -> str | None:
    """Return the commit SHA at ``ref`` in ``path``, or None if unresolvable."""
    proc = subprocess.run(
        ["git", "rev-parse", ref],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
        env=_sanitized_git_env(),
    )
    if proc.returncode != 0:
        return None
    sha = (proc.stdout or "").strip()
    return sha or None


def _count_commits_ahead(worktree: Path, base_ref: str) -> int | None:
    """Return commits on HEAD not reachable from ``base_ref``, or None."""
    proc = subprocess.run(
        ["git", "rev-list", "--count", f"{base_ref}..HEAD"],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
        env=_sanitized_git_env(),
    )
    if proc.returncode != 0:
        return None
    try:
        return int((proc.stdout or "").strip())
    except ValueError:
        return None


def _origin_base_ref(base_branch: str) -> str:
    """Return the remote ref used for ahead-count checks."""
    if base_branch.startswith("origin/"):
        return base_branch
    return f"origin/{base_branch}"


def _base_branch_name(base_branch: str) -> str:
    """Return a PR base branch name without the remote prefix."""
    return base_branch.removeprefix("origin/")


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


@dataclass(frozen=True)
class AutoFinalizeResult:
    ok: bool
    commit_sha: str | None = None
    pr_url: str | None = None
    error: str | None = None
    changed_files: tuple[str, ...] = ()


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
        )
    except OSError:
        return None
    if status_proc.returncode != 0:
        return None
    return bool((status_proc.stdout or "").strip())


def _auto_finalize_changed_files(worktree: Path) -> tuple[str, ...]:
    tracked = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--"],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
        env=_sanitized_git_env(),
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
        env=_sanitized_git_env(),
    )
    if tracked.returncode != 0 or untracked.returncode != 0:
        return ()
    changed = {path.strip() for path in (*tracked.stdout.splitlines(), *untracked.stdout.splitlines()) if path.strip()}
    return tuple(sorted(changed))


def _current_branch(worktree: Path) -> str | None:
    proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
        env=_sanitized_git_env(),
    )
    if proc.returncode != 0:
        return None
    branch = (proc.stdout or "").strip()
    return branch or None


def _x_agent_task_id(agent: str, task_id: str) -> str:
    normalized = _normalize_task_id(agent, task_id)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized).strip(".-")
    return safe or "task"


def _push_auto_finalize_branch(worktree: Path, branch: str) -> None:
    proc = subprocess.run(
        ["git", "push", "-u", "origin", branch],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
        env=_sanitized_git_env(),
    )
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
    )
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
) -> AutoFinalizeResult:
    """Stage, commit, push, and draft-PR a cleanly exited dirty dispatch."""
    changed_files = _auto_finalize_changed_files(worktree)
    try:
        worktree_proc = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
        )
    except OSError:
        return AutoFinalizeResult(
            ok=False,
            error="not a git worktree",
            changed_files=changed_files,
        )
    if worktree_proc.returncode != 0 or (worktree_proc.stdout or "").strip() != "true":
        return AutoFinalizeResult(
            ok=False,
            error="not a git worktree",
            changed_files=changed_files,
        )

    if not changed_files:
        return AutoFinalizeResult(ok=False, error="clean-tree")

    resolved_branch = branch or _current_branch(worktree)
    if not resolved_branch or resolved_branch in {"HEAD", "main", "master"}:
        return AutoFinalizeResult(
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

    commit_sha: str | None = None
    try:
        add_proc = subprocess.run(
            ["git", "add", "-A"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
        )
        if add_proc.returncode != 0:
            return AutoFinalizeResult(
                ok=False,
                error=f"git add failed: {_format_process_failure(add_proc)}",
                changed_files=changed_files,
            )

        commit_proc = subprocess.run(
            [
                "git",
                "commit",
                "-m",
                subject,
                "-m",
                body,
                "--trailer",
                f"X-Agent: {agent}/{safe_task}",
            ],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
        )
        if commit_proc.returncode != 0:
            subprocess.run(
                ["git", "restore", "--staged", "--", *changed_files],
                cwd=worktree,
                capture_output=True,
                text=True,
                check=False,
                env=_sanitized_git_env(),
            )
            return AutoFinalizeResult(
                ok=False,
                error=f"git commit failed: {_format_process_failure(commit_proc)}",
                changed_files=changed_files,
            )

        commit_sha = _resolve_sha(worktree)
        _push_auto_finalize_branch(worktree, resolved_branch)
        pr_url = _create_auto_finalize_pr(
            worktree,
            branch=resolved_branch,
            base_branch=_base_branch_name(base_branch),
            title=subject,
            body=(
                f"Auto-finalized delegate task `{task_id}` for `{agent}`.\n\n"
                "The agent exited with `returncode=0`, left a dirty worktree, "
                "and had made zero commits, so delegate.py staged the work, "
                "created the commit, pushed the branch, and opened this draft PR."
            ),
        )
    except (OSError, RuntimeError) as exc:
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
                )
            except OSError as reset_exc:
                error = f"{error}; git reset failed: {reset_exc}"
            else:
                if reset_proc.returncode != 0:
                    error = f"{error}; git reset failed: {_format_process_failure(reset_proc)}"
                else:
                    commit_sha = None
        return AutoFinalizeResult(
            ok=False,
            commit_sha=commit_sha,
            error=error,
            changed_files=changed_files,
        )

    return AutoFinalizeResult(
        ok=True,
        commit_sha=commit_sha,
        pr_url=pr_url,
        changed_files=changed_files,
    )


def _reap_finished_worktree(worktree: Path) -> dict[str, Any]:
    """Try to reap a clean successful delegate worktree, returning state metadata."""
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.orchestration import reap_worktrees

    try:
        results = reap_worktrees.reap_worktrees(
            repo_root=_REPO_ROOT,
            apply=True,
            preserve_then_reap=False,
            target_paths=[worktree],
        )
    except Exception as exc:
        return {
            "action": "error",
            "path": str(worktree),
            "reason": "reaper raised",
            "error": f"{type(exc).__name__}: {exc}",
        }

    if not results:
        return {
            "action": "skipped",
            "path": str(worktree),
            "reason": "target path was not evaluated",
            "error": None,
        }
    result = results[0]
    return {
        "action": result.action,
        "path": result.path,
        "branch": result.branch,
        "reason": result.reason,
        "dirty": result.dirty,
        "pr": result.pr,
        "error": result.error,
    }


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
    branch_proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
    )
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
    status_proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
    )
    dirty_output = (status_proc.stdout or "").strip()
    if dirty_output:
        first_files = [line[3:] for line in dirty_output.splitlines()[:3]]
        raise WorktreeDirty(
            f"worktree at {path} has uncommitted changes "
            f"(first {len(first_files)}): {first_files}. "
            f"Commit, stash, or remove the worktree before reuse."
        )

    # 3. Stale-base check. Refresh origin/{base} first; ignore fetch failure
    # (we'll use whatever ref is locally available and warn instead of hard-
    # failing offline). Normalize so an origin-prefixed ``base`` (the form
    # the dispatch runbooks mandate) never yields ``origin/origin/main`` —
    # that unresolvable ref made this whole check a silent no-op.
    origin_ref = _origin_base_ref(base)
    _fetch_base(base)
    count_proc = subprocess.run(
        ["git", "rev-list", "--count", f"HEAD..{origin_ref}"],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
    )
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
            "dry-run will not rebase it. Rerun without --dry-run after reviewing "
            "the worktree."
        )

    print(
        f"⚠️  worktree {path} is {behind} commit(s) behind {origin_ref}; attempting fast-forward rebase",
        file=sys.stderr,
    )
    rebase_proc = subprocess.run(
        ["git", "rebase", origin_ref],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
    )
    if rebase_proc.returncode != 0:
        # Clean up so the worktree isn't left mid-rebase.
        subprocess.run(
            ["git", "rebase", "--abort"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
        )
        raise WorktreeStaleBase(
            f"worktree at {path} is {behind} commit(s) behind {origin_ref} "
            f"and rebase failed. Resolve manually or remove:\n"
            f"    git worktree remove {path}"
        )
    return True


def _provision_data_symlinks(worktree_path: Path, main_repo_root: Path) -> None:
    """Symlink heavy local-only files into a delegated worktree.

    Worktrees omit gitignored DBs and dependency directories, but quality
    gates open them relative to the running checkout. Use symlinks so each
    delegated worktree sees the same local files without copying multi-GB
    directories.

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
        ".venv",
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
# curriculum/ + wiki/ are ~300MB of the ~550MB full tree; most infra/code
# dispatches never edit them. Content work opts back in with
# --sparse-include curriculum (and/or wiki) or --full-checkout.
_DISPATCH_SPARSE_EXCLUDE_DEFAULT = frozenset({"curriculum", "wiki"})


def _normalize_sparse_include(raw: Sequence[str] | None) -> tuple[str, ...]:
    """Normalize --sparse-include values to unique top-level directory names.

    Fail closed: explicit values must be bare top-level names in the default
    exclusion set (``curriculum``, ``wiki``). Nested paths and unknown names
    raise :class:`ValueError` so content dispatches cannot silently miss trees.
    """
    if not raw:
        return ()
    seen: set[str] = set()
    ordered: list[str] = []
    for item in raw:
        name = str(item).strip().strip("/")
        if not name or name in {".", ".."}:
            raise ValueError(
                f"--sparse-include {item!r} is empty or invalid; "
                f"pass a top-level name such as 'curriculum' or 'wiki'"
            )
        if "/" in name:
            top = name.split("/", 1)[0]
            raise ValueError(
                f"--sparse-include {item!r} must be a top-level directory name "
                f"(use {top!r}, not a nested path)"
            )
        if name not in _DISPATCH_SPARSE_EXCLUDE_DEFAULT:
            allowed = ", ".join(sorted(_DISPATCH_SPARSE_EXCLUDE_DEFAULT))
            raise ValueError(
                f"--sparse-include {name!r} is not a default-excluded tree; "
                f"allowed: {allowed}"
            )
        if name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return tuple(ordered)


def _infer_sparse_include_from_text(text: str | None) -> tuple[str, ...]:
    """Detect default-excluded top-level path prefixes referenced in a prompt."""
    if not text:
        return ()
    found: list[str] = []
    for name in sorted(_DISPATCH_SPARSE_EXCLUDE_DEFAULT):
        # Path-like reference: curriculum/… or `wiki/` — not bare English words.
        if re.search(rf"(?<![\w.-]){re.escape(name)}/", text):
            found.append(name)
    return tuple(found)


def _infer_sparse_include(
    explicit: Sequence[str] | None,
    *,
    owned_paths: Sequence[str] | None = None,
    prompt_text: str | None = None,
) -> tuple[str, ...]:
    """Merge explicit includes with owned-path tops and prompt path references.

    A dispatch that already declares ``--research-owned-path curriculum/...``
    or whose brief references ``curriculum/`` / ``wiki/`` materializes those
    trees without a second flag.
    """
    merged: list[str] = list(_normalize_sparse_include(explicit))
    seen = set(merged)
    for raw in owned_paths or ():
        top = str(raw).strip().strip("/").split("/", 1)[0]
        if top in _DISPATCH_SPARSE_EXCLUDE_DEFAULT and top not in seen:
            seen.add(top)
            merged.append(top)
    for name in _infer_sparse_include_from_text(prompt_text):
        if name not in seen:
            seen.add(name)
            merged.append(name)
    return tuple(merged)


def _list_worktree_top_dirs(worktree_path: Path, *, at_ref: str = "HEAD") -> list[str]:
    """Return top-level directory names at ``at_ref`` inside a worktree."""
    proc = subprocess.run(
        ["git", "ls-tree", "-d", "--name-only", at_ref],
        cwd=worktree_path,
        capture_output=True,
        text=True,
        check=False,
        env=_sanitized_git_env(),
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "git ls-tree failed").strip()
        raise RuntimeError(
            f"could not list top-level dirs in {worktree_path}: {detail}"
        )
    return [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]


def _apply_dispatch_sparse_checkout(
    worktree_path: Path,
    *,
    full_checkout: bool = False,
    sparse_include: Sequence[str] = (),
) -> dict[str, Any]:
    """Apply (or disable) cone sparse-checkout on a dispatch worktree.

    Default profile excludes ``curriculum/`` and ``wiki/`` so each dispatch
    stays ~200MB instead of ~550MB. ``--full-checkout`` disables sparse mode.
    ``--sparse-include DIR`` keeps named top-level dirs that would otherwise
    be excluded (e.g. ``curriculum`` for module content work).
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
        return subprocess.run(
            args,
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
        )

    if full_checkout:
        proc = _run_git(["git", "sparse-checkout", "disable"])
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "sparse-checkout disable failed").strip()
            telemetry["error"] = detail
            raise RuntimeError(
                f"failed to disable sparse-checkout in {worktree_path}: {detail}"
            )
        telemetry["applied"] = True
        return telemetry

    exclude = set(_DISPATCH_SPARSE_EXCLUDE_DEFAULT) - set(includes)
    all_dirs = _list_worktree_top_dirs(worktree_path)
    included = [name for name in all_dirs if name not in exclude]
    excluded = sorted(name for name in all_dirs if name in exclude)
    telemetry["excluded"] = excluded
    telemetry["included_dirs"] = included

    if not excluded:
        # Nothing to drop at this ref (or everything was re-included). Prefer a
        # full tree rather than an empty cone set.
        proc = _run_git(["git", "sparse-checkout", "disable"])
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "sparse-checkout disable failed").strip()
            telemetry["error"] = detail
            raise RuntimeError(
                f"failed to disable sparse-checkout in {worktree_path}: {detail}"
            )
        telemetry["applied"] = True
        return telemetry

    proc = _run_git(["git", "sparse-checkout", "init", "--cone"])
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "sparse-checkout init failed").strip()
        telemetry["error"] = detail
        raise RuntimeError(
            f"failed to init sparse-checkout in {worktree_path}: {detail}"
        )

    proc = _run_git(["git", "sparse-checkout", "set", "--", *included])
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
        f"in {worktree_path} (use --sparse-include / --full-checkout to keep them)",
        file=sys.stderr,
    )
    return telemetry


def _ensure_worktree(
    *,
    agent: str,
    task_id: str,
    raw_path: str,
    base: str = "main",
    branch: str | None = None,
    dry_run: bool = False,
    full_checkout: bool = False,
    sparse_include: Sequence[str] = (),
) -> tuple[Path, str, dict[str, Any]]:
    """Return a ready worktree path, creating or validating as needed.

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
    worktree_path = _normalize_worktree_path(raw_path)
    requested_branch = _validate_branch_reuse_name(branch) if branch else None
    worktree_branch = requested_branch or _derive_worktree_branch(agent, task_id)
    layout = _classify_worktree_layout(worktree_path)
    telemetry: dict[str, Any] = {
        "base_sha": None,
        "rebased": False,
        "layout": layout,
        "reused": False,
        "sparse": None,
    }

    if requested_branch:
        _fetch_existing_branch(requested_branch)
        occupied_paths = _branch_worktree_paths(requested_branch)
        elsewhere = [path for path in occupied_paths if path != worktree_path]
        if elsewhere:
            locations = ", ".join(str(path) for path in elsewhere)
            raise WorktreeBranchMismatch(
                f"branch {requested_branch!r} is already checked out in {locations}; "
                "refusing to attach it to another worktree"
            )

    if worktree_path.exists():
        if not worktree_path.is_dir():
            raise ValueError(f"worktree path exists but is not a directory: {worktree_path}")
        telemetry["reused"] = True
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
            allow_rebase=not dry_run,
        )
        telemetry["base_sha"] = _resolve_sha(worktree_path)
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
        return worktree_path, worktree_branch, telemetry

    if dry_run:
        raise ValueError(
            f"branch reuse dry-run found no existing worktree at {worktree_path}; "
            "rerun without --dry-run to create one"
        )

    # Fix 1 (#1476): fetch origin/{base} and branch from the remote ref,
    # not the local one. Local `main` drifts the moment a PR merges while
    # a dispatch is queued — this is the stale-base footgun Codex
    # diagnosed in bridge msg #431 (2026-04-23). Normalize so an
    # origin-prefixed ``base`` (``--base origin/main``, the mandated form)
    # fetches ``main`` and branches from ``origin/main`` — not the
    # unresolvable ``origin/origin/main``.
    if requested_branch:
        # Attach directly to the fetched PR/follow-up branch.  Never branch
        # from origin/main here: that was the follow-up-dispatch footgun.
        worktree_base_ref = requested_branch
    else:
        origin_ref = _origin_base_ref(base)
        if _fetch_base(base):
            worktree_base_ref = origin_ref
        else:
            print(
                f"⚠️  `git fetch origin {_base_branch_name(base)}` failed or "
                f"{origin_ref} is unresolvable; falling back to local {base}. "
                f"This worktree may be branched from a stale tip.",
                file=sys.stderr,
            )
            worktree_base_ref = base

    # Ensure parent dirs exist for the dispatch/ subtree layout.
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    add_command = ["git", "worktree", "add"]
    if requested_branch and _resolve_sha(_REPO_ROOT, f"refs/heads/{requested_branch}"):
        add_command.extend([str(worktree_path), requested_branch])
    elif requested_branch:
        add_command.extend(
            ["--track", "-b", requested_branch, str(worktree_path), f"origin/{requested_branch}"]
        )
    else:
        add_command.extend(["-b", worktree_branch, str(worktree_path), worktree_base_ref])
    proc = subprocess.run(
        add_command,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or proc.stdout or "git worktree add failed").strip()
        raise RuntimeError(stderr)
    _provision_data_symlinks(worktree_path, _REPO_ROOT)
    telemetry["sparse"] = _apply_dispatch_sparse_checkout(
        worktree_path,
        full_checkout=full_checkout,
        sparse_include=sparse_include,
    )
    telemetry["base_sha"] = _resolve_sha(worktree_path)
    return worktree_path, worktree_branch, telemetry


def _augment_prompt_with_worktree(
    prompt: str,
    worktree_path: Path | None,
    *,
    sparse_telemetry: dict[str, Any] | None = None,
) -> str:
    """Inject worktree context into the delegated prompt when relevant."""
    if worktree_path is None:
        return prompt
    sparse_note = ""
    if sparse_telemetry and not sparse_telemetry.get("full_checkout"):
        excluded = sparse_telemetry.get("excluded") or []
        if excluded:
            sparse_note = (
                "Sparse-checkout is active: these top-level trees are NOT present: "
                + ", ".join(str(p) for p in excluded)
                + ". If you need them, re-dispatch with --sparse-include <dir> "
                "or --full-checkout (do not invent content for missing paths).\n"
            )
    return (
        "[delegate worktree]\n"
        f"Run all file edits, tests, and git commands inside this worktree: {worktree_path}\n"
        "Do not switch branches in the main checkout.\n"
        f"{sparse_note}\n"
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
        raise ResearchContextError(
            f"too many --research-owned-path values ({len(owned)} > {reg.MAX_OWNED_PATHS})"
        )
    for path in owned:
        if len(path) > reg.MAX_OWNED_PATH_LEN:
            raise ResearchContextError(
                f"--research-owned-path value too long (max {reg.MAX_OWNED_PATH_LEN} chars)"
            )
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


def _with_optional_research_state(
    state: dict[str, Any], research_state: dict[str, Any] | None
) -> dict[str, Any]:
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
    runtime_tmp_root: str | None = None,
    runtime_tmp_namespace_root: str | None = None,
) -> int:
    """Worker main loop. Invokes the runtime, updates the state file.

    Returns the process exit code to use: 0 on ok, 1 on any failure.
    The parent never sees this return code directly — it reads the
    state file instead — but returning it cleanly allows the process
    to show up correctly in ``ps`` and systemd-style supervisors if
    we ever wrap this in one.
    """
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
    if "cli_version" not in state:
        start_telemetry = resolve_dispatch_start_telemetry(
            agent_name=agent,
            requested_model=model,
            requested_effort=effort,
        )
        state.setdefault("model", start_telemetry.model)
        state.setdefault("effort", start_telemetry.effort)
        state.setdefault("cli_version", start_telemetry.cli_version)
    _write_state_atomic(state_path, state)

    cwd = Path(cwd_str)
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
    try:
        stdout_silence_timeout = silence_timeout if silence_timeout > 0 else None
        initial_probe = initial_response_timeout if initial_response_timeout > 0 else None
        tool_config: dict[str, Any] = {}
        if max_budget_usd is not None:
            tool_config["max_budget_usd"] = max_budget_usd
        if provider is not None:
            tool_config[RUNTIME_ROUTE_TOOL_CONFIG_KEY] = {"provider": provider}
        tool_config = tool_config or None
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
        prefix = (
            "initial_response_timeout"
            if getattr(exc, "kind", "stall") == "initial_response_timeout"
            else "stdout_silence_timeout"
        )
        stderr_excerpt = f"{prefix}: {exc}"[:500]
        returncode_reason = "runtime timeout raised before a terminal subprocess returncode was available"
    except AgentTimeoutError as exc:
        substitution = getattr(exc, "substitution", None)
        stderr_excerpt = f"hard_timeout: {exc}"[:500]
        returncode_reason = "runtime timeout raised before a terminal subprocess returncode was available"
    except AgentRuntimeError as exc:
        stderr_excerpt = f"runtime error: {type(exc).__name__}: {exc}"[:500]
        returncode_reason = "runtime exception did not expose a terminal subprocess returncode"
    except Exception as exc:
        # Last-ditch: don't crash the worker on an unexpected bug — we
        # need to update the state file or the parent will see us as
        # "crashed" forever.
        stderr_excerpt = f"worker unexpected: {type(exc).__name__}: {exc}"[:500]
        returncode_reason = "unexpected worker exception before a terminal subprocess returncode was available"
    finally:
        if runtime_tmp_root is not None or runtime_tmp_namespace_root is not None:
            runtime_tmp_reap = _reap_runtime_tmp_lease(
                runtime_tmp_root,
                runtime_tmp_namespace_root,
            )

    duration_s = time.monotonic() - start

    # Write the full response to a result file (may be large).
    result_file: str | None = None
    if response:
        result_path = state_path.with_suffix(".result")
        try:
            result_path.write_text(response)
            result_file = str(result_path)
        except OSError:
            result_file = None

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
    if final_status == "done" and returncode is None:
        final_status = "failed"
        ok_outcome = False
        returncode_reason = "runtime reported success without a terminal subprocess returncode"
        stderr_excerpt = "runtime reported success without a terminal subprocess returncode"
    elif returncode is None and returncode_reason is None:
        returncode_reason = "no terminal subprocess returncode was available"

    final_state = _read_state(state_path) or {}

    # Fix 5 (#1476 AC 5): dispatch-finish telemetry — record whether the
    # worktree exited dirty so follow-up reviewers can see at a glance
    # that the dispatched agent left uncommitted changes behind.
    dirty_on_exit: bool | None = None
    worktree_path = final_state.get("worktree_path")
    if worktree_path:
        dirty_on_exit = _worktree_is_dirty(Path(worktree_path))

    commits_ahead: int | None = None
    needs_finalize = False
    auto_finalize: AutoFinalizeResult | None = None
    if worktree_path and mode == "danger":
        base_branch = str(final_state.get("worktree_base") or "main")
        base_ref = _origin_base_ref(base_branch)
        commits_ahead = _count_commits_ahead(
            Path(worktree_path),
            base_ref,
        )
        if commits_ahead == 0 and dirty_on_exit:
            needs_finalize = True

        if needs_finalize and returncode == 0:
            auto_finalize = _auto_finalize_dirty_worktree(
                worktree=Path(worktree_path),
                task_id=task_id,
                agent=agent,
                branch=final_state.get("worktree_branch"),
                base_branch=base_branch,
            )
            dirty_on_exit = _worktree_is_dirty(Path(worktree_path))
            commits_ahead = _count_commits_ahead(Path(worktree_path), base_ref)
            if auto_finalize.ok:
                needs_finalize = False
                ok_outcome = True
                final_status = "done"

    if needs_finalize:
        final_status = "needs_finalize"

    worktree_reap: dict[str, Any] | None = None
    if (
        worktree_path
        and mode == "danger"
        and not keep_worktree
        and final_status == "done"
        and returncode == 0
        and dirty_on_exit is False
    ):
        worktree_reap = _reap_finished_worktree(Path(worktree_path))

    usage_record = getattr(result, "usage_record", None)
    result_substitution = getattr(result, "substitution", None)
    if result_substitution is not None:
        substitution = result_substitution
    if substitution is None and isinstance(usage_record, dict):
        substitution = usage_record.get("substitution")

    final_state.update(
        {
            "model": getattr(result, "model", final_state.get("model")),
            "effort": getattr(result, "effort", final_state.get("effort")),
            "cli_version": getattr(result, "cli_version", final_state.get("cli_version")),
            "substitution": substitution,
            "status": final_status,
            "finished_at": datetime.now(UTC).isoformat(),
            "duration_s": round(duration_s, 3),
            "response_chars": len(response),
            "result_file": result_file,
            "stderr_excerpt": stderr_excerpt,
            "returncode": returncode,
            "returncode_reason": returncode_reason,
            "worktree_dirty_on_exit": dirty_on_exit,
            "commits_ahead": commits_ahead,
            "needs_finalize": needs_finalize,
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
                }
                if auto_finalize is not None
                else None
            ),
        }
    )
    _write_state_atomic(state_path, final_state)
    _emit_terminal_dispatch_event(
        task_id=task_id,
        agent=agent,
        final_state=final_state,
        result=result,
        fallback_prompt_chars=len(prompt),
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

    return 0 if ok_outcome and not needs_finalize else 1


# ---------------------------------------------------------------------------
# Dispatch command — spawn detached worker
# ---------------------------------------------------------------------------


def cmd_dispatch(args: argparse.Namespace) -> int:
    """Spawn a detached worker and return immediately with the task-id."""
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    from agent_runtime.telemetry import resolve_dispatch_start_telemetry

    task_id = args.task_id
    state_path = _state_path(task_id)
    worktree_arg = getattr(args, "worktree", None)
    requested_branch = getattr(args, "branch", None)
    full_checkout = bool(getattr(args, "full_checkout", False))
    # Prompt is resolved later for the worker; for sparse inference we only
    # need the raw text when available so content briefs auto-include trees.
    early_prompt: str | None = None
    if getattr(args, "prompt", None):
        early_prompt = str(args.prompt)
    elif getattr(args, "prompt_file", None):
        try:
            early_prompt = Path(args.prompt_file).read_text(encoding="utf-8")
        except OSError:
            early_prompt = None
    try:
        sparse_include = _infer_sparse_include(
            getattr(args, "sparse_include", None),
            owned_paths=getattr(args, "research_owned_path", None),
            prompt_text=early_prompt,
        )
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1
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

    # Write-capable modes (workspace-write / danger) must resolve to a verified
    # added worktree — never the primary checkout (#4445). Read-only dispatches
    # stay exempt so repo-root preflight keeps working. Evaluated before any
    # side effects so a rejection leaves no worktree/branch/log residue.
    write_cwd_error = _resolve_write_cwd_error(
        mode=args.mode,
        worktree_arg=worktree_arg,
        cwd_arg=args.cwd,
    )
    if write_cwd_error:
        print(write_cwd_error, file=sys.stderr)
        return 2

    dirty_primary_error = _resolve_dirty_primary_checkout_error(mode=args.mode)
    if dirty_primary_error:
        print(dirty_primary_error, file=sys.stderr)
        return 2

    # Refuse to clobber a task that's still alive — whether it's in
    # "running" (worker up and executing) OR "spawning" (worker created
    # but not yet past its own state-update step). Without the
    # "spawning" check, a fast second dispatch during the tiny window
    # between Popen and _run_worker's first state write could overwrite
    # state and launch a duplicate worker for the same task_id.
    # Codex 2026-04-10 review finding.
    existing = _read_state(state_path)
    if existing and existing.get("status") in ("running", "spawning"):
        pid = existing.get("pid")
        if pid and _pid_alive(int(pid)):
            print(
                f"❌ task_id {task_id!r} is already {existing['status']} "
                f"(pid={pid}). Use 'delegate.py status {task_id}' to check, "
                f"or pick a different task-id.",
                file=sys.stderr,
            )
            return 2

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

    try:
        lifecycle_carrier, lifecycle_prompt = _load_task_lifecycle_carrier(
            getattr(args, "lifecycle_file", None)
        )
    except (OSError, ValueError) as exc:
        print(f"❌ invalid --lifecycle-file: {exc}", file=sys.stderr)
        return 2
    prompt += lifecycle_prompt

    # ADR-011 P3 research context — explicit --research-* flags only. Validate the
    # request-side caps up front (fail fast, before any worktree side effect) so a
    # direct CLI caller is bounded exactly like the API query layer.
    try:
        research_ctx = _build_research_context(args)
    except ResearchContextError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

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

    if getattr(args, "check_budget", False) and not getattr(args, "force_agent", False):
        dispatch_agent = _resolve_agent_with_budget_guard(args.agent)
    else:
        dispatch_agent = args.agent

    if getattr(args, "dry_run", False):
        dry_run_worktree: Path | None = None
        dry_run_branch: str | None = None
        dry_run_worktree_telemetry: dict[str, Any] = {}
        if requested_branch:
            resolved_raw = (
                str(_auto_worktree_path(dispatch_agent, task_id))
                if worktree_arg == "auto"
                else worktree_arg
            )
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
                    base=getattr(args, "base", None) or "main",
                    branch=requested_branch,
                    dry_run=True,
                    full_checkout=full_checkout,
                    sparse_include=sparse_include,
                )
            except (ValueError, RuntimeError) as exc:
                print(f"❌ failed to validate branch reuse for {task_id!r}: {exc}", file=sys.stderr)
                return 1

        try:
            runtime_tmp_root, runtime_tmp_namespace_root = _create_runtime_tmp_lease(task_id)
        except RuntimeError as exc:
            print(f"❌ failed to create runtime tmp lease for {task_id!r}: {exc}", file=sys.stderr)
            return 1

        start_telemetry = resolve_dispatch_start_telemetry(
            agent_name=dispatch_agent,
            requested_model=args.model,
            requested_effort=getattr(args, "effort", None),
        )
        dry_run_state = {
            "task_id": task_id,
            "agent": dispatch_agent,
            "model": start_telemetry.model,
            "effort": start_telemetry.effort,
            "cli_version": start_telemetry.cli_version,
            "mode": args.mode,
            "cwd": str(dry_run_worktree or (Path(args.cwd) if args.cwd else _REPO_ROOT)),
            "worktree_path": str(dry_run_worktree) if dry_run_worktree else None,
            "worktree_branch": dry_run_branch,
            "worktree_base_sha": dry_run_worktree_telemetry.get("base_sha"),
            "runtime_tmp_root": str(runtime_tmp_root),
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
            "substitution": None,
        }
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
        if requested_branch:
            print(
                f"🌲 branch reuse validated: branch={dry_run_branch} "
                f"path={dry_run_worktree} "
                f"base_sha={dry_run_worktree_telemetry.get('base_sha') or '?'} [reused]",
                file=sys.stderr,
            )
        print(task_id)
        return 0

    # Set up log files before provisioning a worktree. If this cheap
    # filesystem setup fails, dispatch exits before leaving worktree/branch
    # side effects behind.
    log_dir = _TASKS_DIR / "logs"
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
        # resolves to ``.worktrees/dispatch/{agent}/{task}/``. Explicit
        # paths remain unchanged for back-compat with in-flight dispatches.
        resolved_raw = str(_auto_worktree_path(dispatch_agent, task_id)) if worktree_arg == "auto" else worktree_arg
        try:
            worktree_path, worktree_branch, worktree_telemetry = _ensure_worktree(
                agent=dispatch_agent,
                task_id=task_id,
                raw_path=resolved_raw,
                base=getattr(args, "base", None) or "main",
                branch=requested_branch,
                full_checkout=full_checkout,
                sparse_include=sparse_include,
            )
        except (ValueError, RuntimeError) as exc:
            print(f"❌ failed to prepare worktree for {task_id!r}: {exc}", file=sys.stderr)
            return 1

    try:
        runtime_tmp_root, runtime_tmp_namespace_root = _create_runtime_tmp_lease(task_id)
    except RuntimeError as exc:
        stdout_fd.close()
        stderr_fd.close()
        print(f"❌ failed to create runtime tmp lease for {task_id!r}: {exc}", file=sys.stderr)
        return 1

    cwd = str(worktree_path or (Path(args.cwd) if args.cwd else _REPO_ROOT))
    prompt = _augment_prompt_with_worktree(
        prompt,
        worktree_path,
        sparse_telemetry=worktree_telemetry.get("sparse")
        if isinstance(worktree_telemetry.get("sparse"), dict)
        else None,
    )

    # POINTERS ONLY: inject bounded research pointers + an on-demand fetch
    # instruction (never digest bodies) when an explicit context was supplied and
    # the registry is enabled. Fail-open — a disabled/malformed registry leaves the
    # prompt and state untouched.
    research_state: dict[str, Any] | None = None
    if research_ctx is not None:
        research_block, research_state = _resolve_research_injection(research_ctx, task_id)
        prompt = prompt + research_block

    start_telemetry = resolve_dispatch_start_telemetry(
        agent_name=dispatch_agent,
        requested_model=args.model,
        requested_effort=getattr(args, "effort", None),
    )

    # Write initial state BEFORE forking so a fast caller can see it.
    # pid is filled in by the worker once it starts; for now we record
    # the parent PID as a placeholder (overwritten by worker).
    worktree_layout = worktree_telemetry.get("layout") if worktree_path else None
    initial_state = {
        "task_id": task_id,
        "agent": dispatch_agent,
        "model": start_telemetry.model,
        "effort": start_telemetry.effort,
        "cli_version": start_telemetry.cli_version,
        "allow_merge": bool(getattr(args, "allow_merge", False)),
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
        "runtime_tmp_root": str(runtime_tmp_root),
        "tmp_bytes_freed": None,
        "tmp_reap_error": None,
        "keep_worktree": keep_worktree,
        "hard_timeout": args.hard_timeout,
        "silence_timeout": silence_timeout,
        "initial_response_timeout": initial_response_timeout,
        "max_budget_usd": max_budget_usd,
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
        "substitution": None,
    }
    if lifecycle_carrier is not None:
        initial_state["task_lifecycle"] = lifecycle_carrier
    initial_state = _with_optional_research_state(initial_state, research_state)
    _write_state_atomic(state_path, initial_state)

    # Fix 5 (#1476 AC 5) — dispatch-start telemetry.
    if worktree_path:
        sparse_meta = worktree_telemetry.get("sparse") or {}
        sparse_tag = ""
        if sparse_meta.get("full_checkout"):
            sparse_tag = " [full-checkout]"
        elif sparse_meta.get("excluded"):
            sparse_tag = f" [sparse-exclude={','.join(sparse_meta['excluded'])}]"
        print(
            f"🌲 dispatch {task_id}: branch={worktree_branch} "
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

    # Fork a detached subprocess that runs this same script with
    # --worker. We use Popen rather than os.fork for portability.
    #
    # Python interpreter: the project rule (non-negotiable-rules.md)
    # is to always use .venv/bin/python. delegate.py follows that rule
    # strictly.
    venv_python = _REPO_ROOT / ".venv" / "bin" / "python"
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
    if keep_worktree:
        cmd.append("--keep-worktree")
    if max_budget_usd is not None:
        cmd.extend(["--max-budget-usd", str(max_budget_usd)])
    if args.model:
        cmd.extend(["--model", args.model])
    if getattr(args, "provider", None):
        cmd.extend(["--provider", args.provider])
    effort = getattr(args, "effort", None)
    if effort:
        cmd.extend(["--effort", effort])

    # Pipe the prompt via stdin so it doesn't hit argv length limits.
    # start_new_session=True detaches from our process group — the
    # worker survives our exit, which is what we want.
    # Explicit env=os.environ.copy() — makes the inherited env
    # explicit rather than implicit. Callers that want to scrub
    # secrets from the worker's env can override this here.
    worker_env = os.environ.copy()
    _inject_gh_token_for_agent(worker_env, dispatch_agent)
    worker_env["AGENT_NO_TELEMETRY_FOOTER"] = "1"
    worker_env["TMPDIR"] = str(runtime_tmp_root)
    worker_env["LU_RUNTIME_TMP_ROOT"] = str(runtime_tmp_root)
    worker_env["LU_RUNTIME_TMP_BASE_ROOT"] = str(runtime_tmp_namespace_root.parent)
    if getattr(args, "allow_merge", False):
        worker_env.pop("AGENT_NO_MERGE", None)
        worker_env["AGENT_ALLOW_MERGE"] = "1"
    else:
        worker_env["AGENT_NO_MERGE"] = "1"
        worker_env.pop("AGENT_ALLOW_MERGE", None)
    try:
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=stdout_fd,
                stderr=stderr_fd,
                env=worker_env,
                start_new_session=True,  # detach from our process group
                close_fds=True,
            )
        except (OSError, FileNotFoundError, ValueError) as exc:
            # Popen itself failed — typically because the Python
            # interpreter isn't where we expected, or the file
            # descriptors are somehow invalid. Without this handler
            # the state file would stay at "spawning" forever with
            # pid=None and no zombie detection could rescue it
            # (because zombie detection is gated on `pid and not alive`).
            # Codex 2026-04-10 audit finding.
            failed_state = _read_state(state_path) or initial_state
            failed_state.update(
                {
                    "status": "failed",
                    "finished_at": datetime.now(UTC).isoformat(),
                    "stderr_excerpt": (f"Popen failed: {type(exc).__name__}: {exc}")[:500],
                    "returncode": None,
                    "returncode_reason": "worker process was not started",
                }
            )
            failed_state.update(
                _reap_runtime_tmp_lease(
                    runtime_tmp_root,
                    runtime_tmp_namespace_root,
                )
            )
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
        _write_state_atomic(state_path, state_with_pid)

        assert proc.stdin is not None  # we passed stdin=PIPE
        try:
            proc.stdin.write(prompt.encode("utf-8"))
            proc.stdin.close()
        except BrokenPipeError:
            pass  # worker crashed before reading; zombie detector will catch it
    finally:
        # The Popen child inherited these FDs via dup; our copies can
        # be closed immediately without affecting the child.
        stdout_fd.close()
        stderr_fd.close()

    # Return task-id on stdout so shell callers can capture it.
    print(task_id)
    return 0


# ---------------------------------------------------------------------------
# Status command — read state + detect zombies
# ---------------------------------------------------------------------------


def cmd_status(args: argparse.Namespace) -> int:
    state_path = _state_path(args.task_id)
    state = _read_state(state_path)
    if state is None:
        print(
            json.dumps({"error": f"no state file for task {args.task_id!r}"}),
        )
        return 1

    # Detect zombies: if status is "running" but PID is dead, the worker
    # crashed (OOM, SIGKILL, reboot, etc.) and never got to update the
    # state file. Mark as "crashed" and persist the correction so
    # subsequent status calls get the right answer without redoing the check.
    prior_status = state.get("status")
    if prior_status in ("running", "spawning"):
        pid = state.get("pid")
        if pid and not _pid_alive(int(pid)):
            state["status"] = "crashed"
            state["finished_at"] = datetime.now(UTC).isoformat()
            state["stderr_excerpt"] = (
                f"worker pid {pid} is not alive but state said {prior_status!r}; marked crashed by status probe"
            )
            _write_state_atomic(state_path, state)

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


def _monitor_api_base_url() -> str:
    return os.environ.get("DELEGATE_MONITOR_API", _MONITOR_API_BASE_URL).rstrip("/")


def _age_seconds_from_started_at(started_at: Any) -> int:
    try:
        started = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return 0
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    return max(0, round((datetime.now(UTC) - started.astimezone(UTC)).total_seconds()))


def _fetch_monitor_task(task_id: str) -> dict[str, Any] | None:
    quoted = urllib.parse.quote(task_id, safe="")
    url = f"{_monitor_api_base_url()}/api/delegate/tasks/{quoted}"
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
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
    try:
        data = yaml.safe_load(_FALLBACK_SUBS_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    subs = data.get("dispatch_fallbacks") if isinstance(data, dict) else {}
    if isinstance(subs, dict):
        return {str(k).lower(): str(v).lower() for k, v in subs.items() if v}
    return {}


def _resolve_agent_with_budget_guard(agent: str) -> str:
    """Return possibly-substituted agent. Hard sub only on fresh snapshot when chosen lane near_cap (>90%).
    Stale/empty: advisory only, no sub (never-trip guard). --force wins before call.
    Substitution is NOTED (operator contract).
    """
    requested = (agent or "").strip().lower()
    try:
        payload = _fetch_routing_budget()
    except MonitorApiUnavailable:
        print("⚠ ROUTING CHECK SKIPPED: Monitor API unreachable", file=sys.stderr)
        return requested

    diags = payload.get("diagnostics") or {}
    rec = payload.get("recommendation") or {}
    agents = payload.get("agents") or {}
    records_loaded = int(diags.get("records_loaded", 0) or 0)
    is_stale = bool(diags.get("stale", False))
    codexbar_data_available = bool(diags.get("codexbar_data_available", False))

    # An empty ledger is only unknown when the explicit CodexBar refresh also
    # yielded no authoritative weekly data. Never quietly fail open here.
    if not agents or (records_loaded == 0 and not codexbar_data_available):
        print(
            "⚠ ROUTING CHECK UNKNOWN: budget UNKNOWN — could not verify CodexBar data; "
            "lanes may be in deficit; no hard sub.",
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
                print(f"⚠ ROUTING CHECK: {warning}; no hard sub (ledger empty).", file=sys.stderr)

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

    # HARD auto-sub only for subscription near_cap on FRESH non-empty
    agent_info = agents.get(requested, {}) or {}
    # claude may be nested
    if requested == "claude":
        status = (agent_info.get("interactive") or {}).get("status") or agent_info.get("status")
    else:
        status = agent_info.get("status")
    burn = (
        agent_info.get("burn_pct_7d")
        if requested != "claude"
        else (agent_info.get("interactive") or {}).get("burn_pct_7d") or agent_info.get("burn_pct_7d")
    )

    if status == "near_cap" and not is_stale and records_loaded > 0:
        fallbacks = _load_dispatch_fallbacks()
        sub = fallbacks.get(requested)
        # The yaml `dispatch_fallbacks` map is the ONLY source for hard subs —
        # no inferred/hardcoded mappings (a deleted config entry must mean
        # "no hard sub", not silently resurrect an old route).
        if sub and sub not in _DISPATCH_AGENT_CHOICES:
            print(
                f"⚠ ROUTING: dispatch_fallbacks maps {requested} → {sub}, "
                "not a known dispatch agent — ignoring hard sub.",
                file=sys.stderr,
            )
            sub = None
        if sub and sub != requested:
            note = (
                f"🔄 HARD AUTO-SUBSTITUTE: --agent {requested} → {sub} "
                f"(lane window >90% used / status=near_cap on FRESH snapshot; "
                f"sub per agent_fallback_substitutions.yaml dispatch_fallbacks + documented cases). "
                "Substitution noted for operator contract / review independence."
            )
            print(note, file=sys.stderr)
            if burn is not None:
                print(f"  (burn_pct_7d was ~{burn}%; resets_at={agent_info.get('resets_at')})", file=sys.stderr)
            return sub

    return requested


def _status_or_fail_payload(task_id: str) -> dict[str, Any]:
    payload = _fetch_monitor_task(task_id)
    if payload is None:
        return {"task_id": task_id, "status": "task not found", "age_s": 0}

    task = payload.get("task") if isinstance(payload.get("task"), dict) else {}
    status = str(task.get("status") or "unknown")
    if status == "running" and payload.get("alive") is False:
        status = "stale"
    return {
        "task_id": task.get("task_id") or task_id,
        "status": status,
        "age_s": _age_seconds_from_started_at(task.get("started_at")),
        "alive": payload.get("alive"),
    }


def cmd_status_or_fail(args: argparse.Namespace) -> int:
    """Exit 0 only when Monitor API confirms a task is currently running."""
    try:
        status = _status_or_fail_payload(args.task_id)
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
    {"done", "failed", "timeout", "rate_limited", "crashed", "cancelled", "dry_run"},
)


def cmd_wait(args: argparse.Namespace) -> int:
    state_path = _state_path(args.task_id)
    poll_interval = max(0.5, float(args.poll_interval))
    deadline = time.monotonic() + float(args.timeout) if args.timeout else None

    while True:
        state = _read_state(state_path)
        if state is None:
            print(
                json.dumps({"error": f"no state file for task {args.task_id!r}"}),
            )
            return 1

        # Zombie probe (same logic as cmd_status)
        prior_status = state.get("status")
        if prior_status in ("running", "spawning"):
            pid = state.get("pid")
            if pid and not _pid_alive(int(pid)):
                state["status"] = "crashed"
                state["finished_at"] = datetime.now(UTC).isoformat()
                state["stderr_excerpt"] = (
                    f"worker pid {pid} is not alive but state said {prior_status!r}; marked crashed by wait probe"
                )
                _write_state_atomic(state_path, state)

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
    _TASKS_DIR.mkdir(parents=True, exist_ok=True)
    tasks: list[dict[str, Any]] = []
    flat_tasks: list[str] = []
    for state_file in sorted(_TASKS_DIR.glob("*.json")):
        state = _read_state(state_file)
        if state is None:
            continue
        # Zombie probe inline for running tasks
        if state.get("status") in ("running", "spawning"):
            pid = state.get("pid")
            if pid and not _pid_alive(int(pid)):
                state["status"] = "crashed"
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
            }
        )
    print(json.dumps(tasks, indent=2, default=str))
    if flat_tasks:
        print(
            f"⚠️  {len(flat_tasks)} task(s) use the DEPRECATED flat worktree "
            f"layout: {flat_tasks[:5]}" + (" …" if len(flat_tasks) > 5 else "") + ". New dispatches should use "
            "`.worktrees/dispatch/{agent}/{task}/`.",
            file=sys.stderr,
        )
    return 0


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
        silence_timeout=args.silence_timeout,
        max_budget_usd=getattr(args, "max_budget_usd", None),
        effort=args.effort,
        initial_response_timeout=getattr(
            args,
            "initial_response_timeout",
            DEFAULT_INITIAL_RESPONSE_TIMEOUT_S,
        ),
        keep_worktree=bool(getattr(args, "keep_worktree", False)),
        runtime_tmp_root=getattr(args, "runtime_tmp_root", None),
        runtime_tmp_namespace_root=getattr(args, "runtime_tmp_namespace_root", None),
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
            "Exit codes:\n"
            "  0 on successful command completion; non-zero on CLI misuse or worker/task failures.\n\n"
            "Related:\n"
            "  Runtime: scripts/agent_runtime/\n"
            "  Rule: agents_extensions/shared/rules/delegate-must-use-worktree.md\n"
            "  Issue: #1379\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="command", required=True)

    # dispatch
    def _dispatch_help_formatter(prog: str) -> argparse.HelpFormatter:
        return argparse.HelpFormatter(prog, max_help_position=36, width=120)

    d = sub.add_parser(
        "dispatch",
        help="Fire a task, return immediately",
        formatter_class=_dispatch_help_formatter,
    )
    d.add_argument(
        "--agent",
        required=True,
        choices=list(_DISPATCH_AGENT_CHOICES),
        # "qwen" removed from choices (banned agent): advertising it in --help
        # while the routing guard rejects it at dispatch is a UX trap. The
        # guard still catches programmatic Namespace bypass.
        help="Agent to run for the task: codex, gemini, claude, grok (Hermes), "
        "grok (native CLI; grok-build=alias), grok-hermes, kimi, deepseek, agy, or cursor.",
    )
    d.add_argument("--task-id", required=True, help="Stable task identifier used for state/log files, e.g. review-123.")
    d.add_argument("--prompt", help="Prompt text, or '-' to read the prompt from stdin.")
    d.add_argument("--prompt-file", help="Read the prompt body from this file path.")
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
        help="Runtime mode (default: read-only). workspace-write and danger "
        "require a verified dispatch worktree (bare --worktree, or --cwd "
        "pointing at an existing added worktree); read-only may run from repo root.",
    )
    d.add_argument(
        "--model", default=None, help="Optional model override, e.g. gpt-5.6-terra or gemini-3.1-pro-preview."
    )
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
        "--cwd",
        default=None,
        help="Working directory for the worker (default: repo root). "
        "For workspace-write/danger it must be a verified added "
        "worktree, never the primary checkout — prefer --worktree.",
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
            "{task}/`, or `--worktree PATH` to reuse a specific added worktree "
            "(validated against the expected dispatch branch before reuse)."
        ),
    )
    d.add_argument(
        "--branch",
        default=None,
        metavar="EXISTING",
        help=(
            "Attach the dispatch to this existing remote branch instead of creating "
            "{agent}/{task}. Fetches and validates the branch, then creates/reuses "
            "an isolated worktree on it (--branch implies --worktree). Refuses "
            "protected branches (main/master) and branches checked out in another "
            "worktree. --branch must omit origin/ and refs/ prefixes."
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
        "--full-checkout",
        action="store_true",
        help=(
            "Materialize the full git working tree in the dispatch worktree. "
            "Default is cone sparse-checkout excluding curriculum/ and wiki/ "
            "(~300MB saved per worktree). Use this for tasks that need the "
            "entire tree without listing includes."
        ),
    )
    d.add_argument(
        "--sparse-include",
        action="append",
        default=None,
        metavar="DIR",
        help=(
            "Keep a top-level directory that default sparse-checkout would "
            "exclude (curriculum, wiki). Repeatable. Example: "
            "--sparse-include curriculum for module content work."
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
        "--check-budget",
        action="store_true",
        help=(
            "Query /api/state/routing-budget before spawning and warn when "
            "budget telemetry recommends a different agent."
        ),
    )
    d.add_argument(
        "--force-agent",
        action="store_true",
        help="Suppress --check-budget routing warnings and dispatch with the requested agent.",
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
            "stdout/stderr/liveness activity within this many seconds "
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
            "Repeatable. Matched against each record's owned_paths globs."
        ),
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
    w.set_defaults(func=cmd_wait)

    # cancel
    c = sub.add_parser("cancel", help="SIGTERM the worker")
    c.add_argument("task_id", help="Task ID to cancel, e.g. review-123.")
    c.set_defaults(func=cmd_cancel)

    # list
    l = sub.add_parser("list", help="List tasks (with optional status filter)")
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
            "dry_run",
        ],
        help="Optional status filter, e.g. running or failed.",
    )
    l.set_defaults(func=cmd_list)

    # _worker (hidden — internal)
    wk = sub.add_parser("_worker", help=argparse.SUPPRESS)
    wk.add_argument("--task-id", required=True)
    wk.add_argument("--agent", required=True)
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
    wk.add_argument("--max-budget-usd", type=float, default=None)
    wk.add_argument("--runtime-tmp-root", default=None)
    wk.add_argument("--runtime-tmp-namespace-root", default=None)
    wk.set_defaults(func=cmd_worker)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
