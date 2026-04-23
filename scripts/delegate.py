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
    delegate.py dispatch --agent codex --task-id my-task \
        --prompt "do the thing" [--mode workspace-write] [--model gpt-5.4]
        [--allow-merge]

    # Check status without blocking.
    delegate.py status my-task
    → {"status": "running", "pid": 12345, "elapsed_s": 42.1, ...}
    → {"status": "done",    "result_file": ".../my-task.result", ...}
    → {"status": "failed",  "stderr_excerpt": "...", ...}
    → {"status": "crashed", "reason": "pid 12345 is dead but state says running"}

    # Wait for completion. Polls at 2s intervals.
    delegate.py wait my-task [--timeout 3600]

State files live at ``batch_state/tasks/<task-id>.json``. Format:

    {
        "task_id": str,
        "agent": str,
        "model": str | None,
        "mode": str,
        "pid": int,
        "status": "running" | "done" | "failed" | "rate_limited" | "crashed",
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
import os
import re
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Resolve repo root from this file's location so we work from any cwd.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_TASKS_DIR = _REPO_ROOT / "batch_state" / "tasks"


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


def _fetch_base(base: str) -> bool:
    """Fetch ``origin/{base}``. Returns True iff the remote ref is resolvable."""
    proc = subprocess.run(
        ["git", "fetch", "origin", base],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return False
    verify = subprocess.run(
        ["git", "rev-parse", "--verify", f"origin/{base}"],
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
    )
    if proc.returncode != 0:
        return None
    sha = (proc.stdout or "").strip()
    return sha or None


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
    # failing offline).
    _fetch_base(base)
    count_proc = subprocess.run(
        ["git", "rev-list", "--count", f"HEAD..origin/{base}"],
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
        f"⚠️  worktree {path} is {behind} commit(s) behind origin/{base}; "
        f"attempting fast-forward rebase",
        file=sys.stderr,
    )
    rebase_proc = subprocess.run(
        ["git", "rebase", f"origin/{base}"],
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
            f"worktree at {path} is {behind} commit(s) behind origin/{base} "
            f"and rebase failed. Resolve manually or remove:\n"
            f"    git worktree remove {path}"
        )
    return True


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
        return worktree_path, branch, telemetry

    # Fix 1 (#1476): fetch origin/{base} and branch from the remote ref,
    # not the local one. Local `main` drifts the moment a PR merges while
    # a dispatch is queued — this is the stale-base footgun Codex
    # diagnosed in bridge msg #431 (2026-04-23).
    if _fetch_base(base):
        worktree_base_ref = f"origin/{base}"
    else:
        print(
            f"⚠️  `git fetch origin {base}` failed or origin/{base} is "
            f"unresolvable; falling back to local {base}. This worktree "
            f"may be branched from a stale tip.",
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
) -> str:
    """Map worker outcome flags to the persisted delegate task status."""
    if cancelled:
        return "cancelled"
    if rate_limited:
        return "rate_limited"
    if ok_outcome:
        return "done"
    return "failed"


def _run_worker(
    task_id: str,
    agent: str,
    prompt: str,
    mode: str,
    cwd_str: str,
    model: str | None,
    hard_timeout: int,
    effort: str | None = None,
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
        AgentTimeoutError,
        RateLimitedError,
    )
    from agent_runtime.runner import invoke as runtime_invoke

    state_path = _state_path(task_id)

    # Update state to include our actual PID. The parent wrote an
    # initial state before forking; we overwrite with the real one
    # (in case the parent's guess was off, or we were re-exec'd).
    state = _read_state(state_path) or {}
    state["pid"] = os.getpid()
    state["status"] = "running"
    _write_state_atomic(state_path, state)

    cwd = Path(cwd_str)
    start = time.monotonic()
    ok_outcome = False
    stderr_excerpt = None
    response = ""
    returncode: int | None = None
    rate_limited = False

    cancelled = False
    try:
        result = runtime_invoke(
            agent,
            prompt,
            mode=mode,
            cwd=cwd,
            model=model,
            task_id=task_id,
            session_id=None,  # Layer 3 is always fresh-session
            tool_config=None,
            entrypoint="delegate",
            hard_timeout=hard_timeout,
            effort=effort,
        )
        ok_outcome = result.ok
        response = result.response
        stderr_excerpt = result.stderr_excerpt
        returncode = result.returncode
        rate_limited = result.rate_limited
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
    except AgentTimeoutError as exc:
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
    )

    final_state = _read_state(state_path) or {}

    # Fix 5 (#1476 AC 5): dispatch-finish telemetry — record whether the
    # worktree exited dirty so follow-up reviewers can see at a glance
    # that the dispatched agent left uncommitted changes behind.
    dirty_on_exit: bool | None = None
    worktree_path = final_state.get("worktree_path")
    if worktree_path:
        try:
            status_proc = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if status_proc.returncode == 0:
                dirty_on_exit = bool((status_proc.stdout or "").strip())
        except OSError:
            dirty_on_exit = None

    final_state.update({
        "status": final_status,
        "finished_at": datetime.now(UTC).isoformat(),
        "duration_s": round(duration_s, 3),
        "response_chars": len(response),
        "result_file": result_file,
        "stderr_excerpt": stderr_excerpt,
        "returncode": returncode,
        "worktree_dirty_on_exit": dirty_on_exit,
    })
    _write_state_atomic(state_path, final_state)

    return 0 if ok_outcome else 1


# ---------------------------------------------------------------------------
# Dispatch command — spawn detached worker
# ---------------------------------------------------------------------------

def cmd_dispatch(args: argparse.Namespace) -> int:
    """Spawn a detached worker and return immediately with the task-id."""
    task_id = args.task_id
    state_path = _state_path(task_id)
    worktree_arg = getattr(args, "worktree", None)

    if args.mode == "danger" and not worktree_arg:
        print(
            "❌ --mode danger requires --worktree to keep delegated writes out "
            "of the main checkout.",
            file=sys.stderr,
        )
        return 2
    if args.cwd and worktree_arg:
        print(
            "❌ --cwd and --worktree are mutually exclusive. Use --worktree for "
            "delegated write isolation.",
            file=sys.stderr,
        )
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

    worktree_path: Path | None = None
    worktree_branch: str | None = None
    worktree_telemetry: dict[str, Any] = {}
    if worktree_arg:
        # Fix 4 (#1476): the sentinel ``auto`` (from bare ``--worktree``)
        # resolves to ``.worktrees/dispatch/{agent}/{task}/``. Explicit
        # paths remain unchanged for back-compat with in-flight dispatches.
        resolved_raw = (
            str(_auto_worktree_path(args.agent, task_id))
            if worktree_arg == "auto"
            else worktree_arg
        )
        try:
            worktree_path, worktree_branch, worktree_telemetry = _ensure_worktree(
                agent=args.agent,
                task_id=task_id,
                raw_path=resolved_raw,
                base=getattr(args, "base", None) or "main",
            )
        except (ValueError, RuntimeError) as exc:
            print(f"❌ failed to prepare worktree for {task_id!r}: {exc}", file=sys.stderr)
            return 1

    cwd = str(worktree_path or (Path(args.cwd) if args.cwd else _REPO_ROOT))
    prompt = _augment_prompt_with_worktree(prompt, worktree_path)

    # Write initial state BEFORE forking so a fast caller can see it.
    # pid is filled in by the worker once it starts; for now we record
    # the parent PID as a placeholder (overwritten by worker).
    worktree_layout = worktree_telemetry.get("layout") if worktree_path else None
    initial_state = {
        "task_id": task_id,
        "agent": args.agent,
        "model": args.model,
        "effort": getattr(args, "effort", None),
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
        "--agent", args.agent,
        "--mode", args.mode,
        "--cwd", cwd,
        "--hard-timeout", str(args.hard_timeout),
    ]
    if args.model:
        cmd.extend(["--model", args.model])
    effort = getattr(args, "effort", None)
    if effort:
        cmd.extend(["--effort", effort])

    # Pipe the prompt via stdin so it doesn't hit argv length limits.
    # start_new_session=True detaches from our process group — the
    # worker survives our exit, which is what we want.
    log_dir = _TASKS_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = log_dir / f"{task_id}.stdout.log"
    stderr_log = log_dir / f"{task_id}.stderr.log"
    # These file descriptors MUST outlive this function — Popen keeps
    # them open for the child process. A context manager would close
    # them the instant Popen returns, breaking the worker's output.
    # SIM115 doesn't understand this case.
    stdout_fd = open(stdout_log, "ab", buffering=0)  # noqa: SIM115
    stderr_fd = open(stderr_log, "ab", buffering=0)  # noqa: SIM115

    # Explicit env=os.environ.copy() — makes the inherited env
    # explicit rather than implicit. Callers that want to scrub
    # secrets from the worker's env can override this here.
    worker_env = os.environ.copy()
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


# ---------------------------------------------------------------------------
# Wait command — poll until terminal state or timeout
# ---------------------------------------------------------------------------

_TERMINAL_STATUSES = frozenset(
    {"done", "failed", "rate_limited", "crashed", "cancelled"}
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
        effort=args.effort,
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
            "  .venv/bin/python scripts/delegate.py dispatch --agent codex --task-id review-123 --prompt-file prompt.md --mode workspace-write --cwd .\n"
            "  .venv/bin/python scripts/delegate.py dispatch --agent codex --task-id pr-123 --prompt-file brief.md --mode danger --worktree .worktrees/codex-pr-123\n"
            "  .venv/bin/python scripts/delegate.py wait review-123 --timeout 600\n"
            "  .venv/bin/python scripts/delegate.py list --status running\n\n"
            "Outputs:\n"
            "  Persists task state under batch_state/tasks/ and streams worker output to task-owned logs.\n\n"
            "Exit codes:\n"
            "  0 on successful command completion; non-zero on CLI misuse or worker/task failures.\n\n"
            "Related:\n"
            "  Runtime: scripts/agent_runtime/\n"
            "  Rule: claude_extensions/rules/delegate-must-use-worktree.md\n"
            "  Issue: #1379\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="command", required=True)

    # dispatch
    d = sub.add_parser("dispatch", help="Fire a task, return immediately")
    d.add_argument("--agent", required=True, choices=["codex", "gemini", "claude"],
                   help="Agent to run for the task: codex, gemini, or claude.")
    d.add_argument("--task-id", required=True,
                   help="Stable task identifier used for state/log files, e.g. review-123.")
    d.add_argument("--prompt", help="Prompt text, or '-' to read the prompt from stdin.")
    d.add_argument("--prompt-file", help="Read the prompt body from this file path.")
    d.add_argument("--mode", default="read-only",
                   choices=["read-only", "workspace-write", "danger"],
                   help="Runtime mode (default: read-only). Use danger only with --worktree.")
    d.add_argument("--model", default=None,
                   help="Optional model override, e.g. gpt-5.4 or gemini-3.1-pro-preview.")
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
                   help="Working directory for the worker (default: repo root)")
    d.add_argument(
        "--worktree",
        nargs="?",
        const="auto",
        default=None,
        help=(
            "Run inside this git worktree (created on demand, required for "
            "--mode danger). Pass `--worktree PATH` to use a specific path "
            "(back-compat with existing `.worktrees/{agent}-{task}/` "
            "layout), or `--worktree` alone to auto-derive the new default "
            "`.worktrees/dispatch/{agent}/{task}/`."
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
    d.add_argument("--hard-timeout", type=int, default=3600,
                   help="Max wall-clock seconds for the worker (default: 3600)")
    d.set_defaults(func=cmd_dispatch)

    # status
    s = sub.add_parser("status", help="Check task status (fast, no block)")
    s.add_argument("task_id", help="Task ID to inspect, e.g. review-123.")
    s.set_defaults(func=cmd_status)

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
                            "rate_limited", "crashed", "cancelled"],
                   help="Optional status filter, e.g. running or failed.")
    l.set_defaults(func=cmd_list)

    # _worker (hidden — internal)
    wk = sub.add_parser("_worker", help=argparse.SUPPRESS)
    wk.add_argument("--task-id", required=True)
    wk.add_argument("--agent", required=True)
    wk.add_argument("--mode", required=True)
    wk.add_argument("--cwd", required=True)
    wk.add_argument("--model", default=None)
    wk.add_argument(
        "--effort",
        default=None,
        choices=["low", "medium", "high", "xhigh", "max"],
    )
    wk.add_argument("--hard-timeout", type=int, default=3600)
    wk.set_defaults(func=cmd_worker)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
