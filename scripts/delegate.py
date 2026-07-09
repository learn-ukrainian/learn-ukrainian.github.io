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
        --prompt "do the thing" [--mode workspace-write --worktree] [--model gpt-5.5]
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
        "returncode": int | null
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
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from agent_runtime.routes import RUNTIME_ROUTE_TOOL_CONFIG_KEY

# Resolve repo root from this file's location so we work from any cwd.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_TASKS_DIR = _REPO_ROOT / "batch_state" / "tasks"
_BASH_SECRETS_PATH = Path.home() / ".bash_secrets"
_GH_TOKEN_AGENTS = {"codex", "claude", "bridge"}
_FALLBACK_SUBS_PATH = _REPO_ROOT / "scripts" / "config" / "agent_fallback_substitutions.yaml"
# Single source for dispatchable agents: argparse choices AND the hard-sub
# validation in _resolve_agent_with_budget_guard (a yaml typo must never
# dispatch a nonexistent adapter).
_DISPATCH_AGENT_CHOICES = ("codex", "gemini", "claude", "grok", "grok-build", "deepseek", "agy", "cursor")
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
    return (
        os.environ.get("GITHUB_TOKEN")
        or _read_github_token_from_bash_secrets()
        or os.environ.get("GH_TOKEN")
    )


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


def _main_checkout_root(repo_root: Path = _REPO_ROOT) -> Path:
    """Return the primary checkout root that owns the shared .git dir."""
    git_path = repo_root / ".git"
    if git_path.is_dir():
        return repo_root
    if not git_path.is_file():
        return repo_root

    try:
        first_line = git_path.read_text().splitlines()[0]
    except (IndexError, OSError):
        return repo_root
    prefix = "gitdir:"
    if not first_line.startswith(prefix):
        return repo_root

    git_dir = Path(first_line[len(prefix):].strip())
    if not git_dir.is_absolute():
        git_dir = repo_root / git_dir
    git_dir = git_dir.resolve()
    if git_dir.parent.name != "worktrees":
        return repo_root
    common_git_dir = git_dir.parent.parent
    if common_git_dir.name != ".git":
        return repo_root
    return common_git_dir.parent


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
            return task_id[len(prefix):]
    return task_id


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
    *, mode: str, worktree_arg: str | None, cwd_arg: str | None,
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
    changed = {
        path.strip()
        for path in (*tracked.stdout.splitlines(), *untracked.stdout.splitlines())
        if path.strip()
    }
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
                    error = (
                        f"{error}; git reset failed: "
                        f"{_format_process_failure(reset_proc)}"
                    )
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
    *, path: Path, expected_branch: str, base: str,
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

    print(
        f"⚠️  worktree {path} is {behind} commit(s) behind {origin_ref}; "
        f"attempting fast-forward rebase",
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
            cwd=path, capture_output=True, text=True, check=False,
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
                f"⚠️  skipping worktree link because {target.parent} "
                "is not a directory",
                file=sys.stderr,
            )
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(resolved_source)


def _ensure_worktree(
    *,
    agent: str,
    task_id: str,
    raw_path: str,
    base: str = "main",
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
    """
    worktree_path = _normalize_worktree_path(raw_path)
    branch = _derive_worktree_branch(agent, task_id)
    layout = _classify_worktree_layout(worktree_path)
    telemetry: dict[str, Any] = {
        "base_sha": None,
        "rebased": False,
        "layout": layout,
        "reused": False,
    }

    if worktree_path.exists():
        if not worktree_path.is_dir():
            raise ValueError(f"worktree path exists but is not a directory: {worktree_path}")
        telemetry["reused"] = True
        telemetry["rebased"] = _validate_existing_worktree(
            path=worktree_path, expected_branch=branch, base=base,
        )
        telemetry["base_sha"] = _resolve_sha(worktree_path)
        # Reused worktrees may predate this provisioning hook; the helper is
        # idempotent and never clobbers existing files.
        _provision_data_symlinks(worktree_path, _main_checkout_root())
        return worktree_path, branch, telemetry

    # Fix 1 (#1476): fetch origin/{base} and branch from the remote ref,
    # not the local one. Local `main` drifts the moment a PR merges while
    # a dispatch is queued — this is the stale-base footgun Codex
    # diagnosed in bridge msg #431 (2026-04-23). Normalize so an
    # origin-prefixed ``base`` (``--base origin/main``, the mandated form)
    # fetches ``main`` and branches from ``origin/main`` — not the
    # unresolvable ``origin/origin/main``.
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

    proc = subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(worktree_path), worktree_base_ref],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or proc.stdout or "git worktree add failed").strip()
        raise RuntimeError(stderr)
    _provision_data_symlinks(worktree_path, _main_checkout_root())
    telemetry["base_sha"] = _resolve_sha(worktree_path)
    return worktree_path, branch, telemetry


def _augment_prompt_with_worktree(prompt: str, worktree_path: Path | None) -> str:
    """Inject worktree context into the delegated prompt when relevant."""
    if worktree_path is None:
        return prompt
    return (
        "[delegate worktree]\n"
        f"Run all file edits, tests, and git commands inside this worktree: {worktree_path}\n"
        "Do not switch branches in the main checkout.\n\n"
        f"{prompt}"
    )


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
    rate_limited = False
    timed_out = False
    result = None
    substitution: dict[str, Any] | None = None

    cancelled = False
    try:
        stdout_silence_timeout = silence_timeout if silence_timeout > 0 else None
        initial_probe = (
            initial_response_timeout if initial_response_timeout > 0 else None
        )
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
    except RateLimitedError as exc:
        rate_limited = True
        stderr_excerpt = str(exc)[:500]
    except AgentStalledError as exc:
        timed_out = True
        substitution = getattr(exc, "substitution", None)
        prefix = (
            "initial_response_timeout"
            if getattr(exc, "kind", "stall") == "initial_response_timeout"
            else "stdout_silence_timeout"
        )
        stderr_excerpt = f"{prefix}: {exc}"[:500]
    except AgentTimeoutError as exc:
        substitution = getattr(exc, "substitution", None)
        stderr_excerpt = f"hard_timeout: {exc}"[:500]
    except AgentRuntimeError as exc:
        stderr_excerpt = f"runtime error: {type(exc).__name__}: {exc}"[:500]
    except Exception as exc:
        # Last-ditch: don't crash the worker on an unexpected bug — we
        # need to update the state file or the parent will see us as
        # "crashed" forever.
        stderr_excerpt = f"worker unexpected: {type(exc).__name__}: {exc}"[:500]

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

    final_state.update({
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
        "worktree_dirty_on_exit": dirty_on_exit,
        "commits_ahead": commits_ahead,
        "needs_finalize": needs_finalize,
        "keep_worktree": keep_worktree,
        "worktree_reap": worktree_reap,
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
    })
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
    silence_timeout = getattr(args, "silence_timeout", DEFAULT_SILENCE_TIMEOUT_S)
    initial_response_timeout = getattr(
        args,
        "initial_response_timeout",
        DEFAULT_INITIAL_RESPONSE_TIMEOUT_S,
    )
    max_budget_usd = getattr(args, "max_budget_usd", None)
    keep_worktree = bool(getattr(args, "keep_worktree", False))

    if args.cwd and worktree_arg:
        print(
            "❌ --cwd and --worktree are mutually exclusive. Use --worktree for "
            "delegated write isolation.",
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
        resolved_raw = (
            str(_auto_worktree_path(dispatch_agent, task_id))
            if worktree_arg == "auto"
            else worktree_arg
        )
        try:
            worktree_path, worktree_branch, worktree_telemetry = _ensure_worktree(
                agent=dispatch_agent,
                task_id=task_id,
                raw_path=resolved_raw,
                base=getattr(args, "base", None) or "main",
            )
        except (ValueError, RuntimeError) as exc:
            print(f"❌ failed to prepare worktree for {task_id!r}: {exc}", file=sys.stderr)
            return 1

    cwd = str(worktree_path or (Path(args.cwd) if args.cwd else _REPO_ROOT))
    prompt = _augment_prompt_with_worktree(prompt, worktree_path)
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
        "substitution": None,
    }
    _write_state_atomic(state_path, initial_state)

    # Fix 5 (#1476 AC 5) — dispatch-start telemetry.
    if worktree_path:
        print(
            f"🌲 dispatch {task_id}: branch={worktree_branch} "
            f"base_sha={worktree_telemetry.get('base_sha') or '?'} "
            f"path={worktree_path} layout={worktree_layout}"
            + (" [rebased]" if worktree_telemetry.get("rebased") else "")
            + (" [reused]" if worktree_telemetry.get("reused") else ""),
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
        "--task-id", task_id,
        "--agent", dispatch_agent,
        "--mode", args.mode,
        "--cwd", cwd,
        "--hard-timeout", str(args.hard_timeout),
        "--silence-timeout", str(silence_timeout),
        "--initial-response-timeout", str(initial_response_timeout),
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
            failed_state.update({
                "status": "failed",
                "finished_at": datetime.now(UTC).isoformat(),
                "stderr_excerpt": (
                    f"Popen failed: {type(exc).__name__}: {exc}"
                )[:500],
                "returncode": None,
            })
            _write_state_atomic(state_path, failed_state)
            print(
                f"❌ failed to spawn worker for {task_id!r}: "
                f"{type(exc).__name__}: {exc}",
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
                f"worker pid {pid} is not alive but state said "
                f"{prior_status!r}; marked crashed by status probe"
            )
            _write_state_atomic(state_path, state)

    # Elapsed time for still-running tasks
    if state.get("status") == "running" and state.get("started_at"):
        try:
            started = datetime.fromisoformat(
                str(state["started_at"]).replace("Z", "+00:00")
            )
            state["elapsed_s"] = round(
                (datetime.now(UTC) - started).total_seconds(), 1,
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
    url = f"{_monitor_api_base_url()}/api/state/routing-budget"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
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

    # empty or no data: suppress hard action + rec warning per constraint (a)
    if records_loaded == 0 or not agents:
        print("⚠ ROUTING CHECK: empty snapshot (records_loaded=0) — no primary rec, no hard sub (per design)", file=sys.stderr)
        return requested

    if is_stale:
        print("⚠ ROUTING CHECK ADVISORY (stale snapshot, generatedAt/data age >15min) — verify manually; no hard sub", file=sys.stderr)
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
    burn = agent_info.get("burn_pct_7d") if requested != "claude" else (agent_info.get("interactive") or {}).get("burn_pct_7d") or agent_info.get("burn_pct_7d")

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
        f"task {args.task_id} is not running "
        f"(status={status['status']}, age={status['age_s']}s)",
        file=sys.stderr,
    )
    return 1


# ---------------------------------------------------------------------------
# Wait command — poll until terminal state or timeout
# ---------------------------------------------------------------------------

_TERMINAL_STATUSES = frozenset(
    {"done", "failed", "timeout", "rate_limited", "crashed", "cancelled"}
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
                    f"worker pid {pid} is not alive but state said "
                    f"{prior_status!r}; marked crashed by wait probe"
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
            f"❌ task {args.task_id!r} has unexpected status {status!r}; "
            f"refusing to cancel.",
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
            f"layout: {flat_tasks[:5]}"
            + (" …" if len(flat_tasks) > 5 else "")
            + ". New dispatches should use "
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
    d.add_argument("--agent", required=True,
                   choices=list(_DISPATCH_AGENT_CHOICES),
                   # "qwen" removed from choices (banned agent): advertising it in --help
                   # while the routing guard rejects it at dispatch is a UX trap. The
                   # guard still catches programmatic Namespace bypass.
                   help="Agent to run for the task: codex, gemini, claude, grok (Hermes), "
                        "grok-build (native grok CLI), deepseek, agy, or cursor.")
    d.add_argument("--task-id", required=True,
                   help="Stable task identifier used for state/log files, e.g. review-123.")
    d.add_argument("--prompt", help="Prompt text, or '-' to read the prompt from stdin.")
    d.add_argument("--prompt-file", help="Read the prompt body from this file path.")
    d.add_argument("--mode", default="read-only",
                   choices=["read-only", "workspace-write", "danger"],
                   help="Runtime mode (default: read-only). workspace-write and danger "
                        "require a verified dispatch worktree (bare --worktree, or --cwd "
                        "pointing at an existing added worktree); read-only may run from repo root.")
    d.add_argument("--model", default=None,
                   help="Optional model override, e.g. gpt-5.5 or gemini-3.1-pro-preview.")
    d.add_argument("--provider", default=None,
                   choices=["openrouter"],
                   help="Opt-in provider for Hermes-routed agents (e.g. deepseek). "
                        "Default for DeepSeek is first-party (local-only). "
                        "Use --provider openrouter for US-residency pinned path.")
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
    d.add_argument("--cwd", default=None,
                   help="Working directory for the worker (default: repo root). "
                        "For workspace-write/danger it must be a verified added "
                        "worktree, never the primary checkout — prefer --worktree.")
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
        "--keep-worktree",
        action="store_true",
        help=(
            "Keep a successful clean dispatch worktree instead of reaping it "
            "after the branch is recoverable from origin or PR state."
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
    w.add_argument("--timeout", type=float, default=0,
                   help="Max wait seconds (0 = forever)")
    w.add_argument("--poll-interval", type=float, default=2.0,
                   help="Poll interval seconds (default: 2.0)")
    w.set_defaults(func=cmd_wait)

    # cancel
    c = sub.add_parser("cancel", help="SIGTERM the worker")
    c.add_argument("task_id", help="Task ID to cancel, e.g. review-123.")
    c.set_defaults(func=cmd_cancel)

    # list
    l = sub.add_parser("list", help="List tasks (with optional status filter)")
    l.add_argument("--status", default=None,
                   choices=["spawning", "running", "done", "failed",
                            "timeout", "rate_limited", "crashed", "cancelled",
                            "needs_finalize"],
                   help="Optional status filter, e.g. running or failed.")
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
    wk.set_defaults(func=cmd_worker)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
