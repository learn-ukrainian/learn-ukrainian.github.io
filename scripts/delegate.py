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


def _run_worker(
    task_id: str,
    agent: str,
    prompt: str,
    mode: str,
    cwd_str: str,
    model: str | None,
    hard_timeout: int,
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

    # Classify final status
    if cancelled:
        final_status = "cancelled"
    elif rate_limited:
        final_status = "rate_limited"
    elif ok_outcome:
        final_status = "done"
    else:
        final_status = "failed"

    final_state = _read_state(state_path) or {}
    final_state.update({
        "status": final_status,
        "finished_at": datetime.now(UTC).isoformat(),
        "duration_s": round(duration_s, 3),
        "response_chars": len(response),
        "result_file": result_file,
        "stderr_excerpt": stderr_excerpt,
        "returncode": returncode,
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

    cwd = args.cwd or str(_REPO_ROOT)

    # Write initial state BEFORE forking so a fast caller can see it.
    # pid is filled in by the worker once it starts; for now we record
    # the parent PID as a placeholder (overwritten by worker).
    initial_state = {
        "task_id": task_id,
        "agent": args.agent,
        "model": args.model,
        "mode": args.mode,
        "cwd": cwd,
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

    # Fork a detached subprocess that runs this same script with
    # --worker. We use Popen rather than os.fork for portability.
    #
    # Python interpreter: the project rule (non-negotiable-rules.md)
    # is to always use .venv/bin/python, never a bare `python` or
    # whatever sys.executable happens to be. sys.executable only
    # points at the venv interpreter IF the parent was launched from
    # the venv, which isn't guaranteed when delegate.py is called
    # from other contexts. Resolve the venv python explicitly;
    # fall back to sys.executable only as a last resort. Codex
    # 2026-04-10 audit finding.
    venv_python = _REPO_ROOT / ".venv" / "bin" / "python"
    python_bin = str(venv_python) if venv_python.exists() else sys.executable
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
        tasks.append(
            {
                "task_id": state.get("task_id"),
                "agent": state.get("agent"),
                "status": state.get("status"),
                "started_at": state.get("started_at"),
                "duration_s": state.get("duration_s"),
            }
        )
    print(json.dumps(tasks, indent=2, default=str))
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
    )


# ---------------------------------------------------------------------------
# CLI glue
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="delegate.py",
        description="Async task dispatch over agent_runtime (#1184)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # dispatch
    d = sub.add_parser("dispatch", help="Fire a task, return immediately")
    d.add_argument("--agent", required=True, choices=["codex", "gemini", "claude"])
    d.add_argument("--task-id", required=True)
    d.add_argument("--prompt", help="Prompt text, or '-' for stdin")
    d.add_argument("--prompt-file", help="Read prompt from this file")
    d.add_argument("--mode", default="read-only",
                   choices=["read-only", "workspace-write", "danger"])
    d.add_argument("--model", default=None)
    d.add_argument("--cwd", default=None,
                   help="Working directory for the worker (default: repo root)")
    d.add_argument("--hard-timeout", type=int, default=3600,
                   help="Max wall-clock seconds for the worker (default: 3600)")
    d.set_defaults(func=cmd_dispatch)

    # status
    s = sub.add_parser("status", help="Check task status (fast, no block)")
    s.add_argument("task_id")
    s.set_defaults(func=cmd_status)

    # wait
    w = sub.add_parser("wait", help="Block until task reaches terminal state")
    w.add_argument("task_id")
    w.add_argument("--timeout", type=float, default=0,
                   help="Max wait seconds (0 = forever)")
    w.add_argument("--poll-interval", type=float, default=2.0,
                   help="Poll interval seconds (default: 2.0)")
    w.set_defaults(func=cmd_wait)

    # cancel
    c = sub.add_parser("cancel", help="SIGTERM the worker")
    c.add_argument("task_id")
    c.set_defaults(func=cmd_cancel)

    # list
    l = sub.add_parser("list", help="List tasks (with optional status filter)")
    l.add_argument("--status", default=None,
                   choices=["spawning", "running", "done", "failed",
                            "rate_limited", "crashed", "cancelled"])
    l.set_defaults(func=cmd_list)

    # _worker (hidden — internal)
    wk = sub.add_parser("_worker", help=argparse.SUPPRESS)
    wk.add_argument("--task-id", required=True)
    wk.add_argument("--agent", required=True)
    wk.add_argument("--mode", required=True)
    wk.add_argument("--cwd", required=True)
    wk.add_argument("--model", default=None)
    wk.add_argument("--hard-timeout", type=int, default=3600)
    wk.set_defaults(func=cmd_worker)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
