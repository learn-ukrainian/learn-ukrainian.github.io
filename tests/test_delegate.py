"""Tests for scripts/delegate.py — async task dispatch over agent_runtime.

These tests exercise the state-file state machine and the zombie-detection
logic without actually spawning real CLI subprocesses. The Popen spawn
path is covered by a single smoke test that uses a fast local Python
script as the "agent" via monkey-patching.

Issue: #1184.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from agent_runtime.adapters.base import InvocationPlan
from agent_runtime.result import ParseResult
from agent_runtime.telemetry import InvocationTelemetry


@pytest.fixture
def tmp_tasks_dir(tmp_path, monkeypatch):
    """Redirect delegate._TASKS_DIR to a tmp path so tests don't pollute
    the real batch_state/tasks/ directory."""
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate, "_TASKS_DIR", tasks_dir)
    return tasks_dir


def _sanitize_git_env_for_test(monkeypatch) -> None:
    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)


def test_sanitized_git_env_keeps_benign_git_transport_env(monkeypatch):
    monkeypatch.setenv("GIT_SSH_COMMAND", "ssh -i test-key")
    monkeypatch.setenv("GIT_SSH_VARIANT", "ssh")
    monkeypatch.setenv("GIT_TRACE", "1")
    monkeypatch.setenv("GIT_DIR", "/tmp/wrong-git-dir")
    monkeypatch.setenv("GIT_WORK_TREE", "/tmp/wrong-work-tree")
    monkeypatch.setenv("PRE_COMMIT_HOME", "/tmp/pre-commit")

    env = delegate._sanitized_git_env()

    assert env["GIT_SSH_COMMAND"] == "ssh -i test-key"
    assert env["GIT_SSH_VARIANT"] == "ssh"
    assert env["GIT_TRACE"] == "1"
    assert "GIT_DIR" not in env
    assert "GIT_WORK_TREE" not in env
    assert "PRE_COMMIT_HOME" not in env


# ---------------------------------------------------------------------------
# State file helpers
# ---------------------------------------------------------------------------

def test_state_path_creates_dir(tmp_tasks_dir):
    p = delegate._state_path("my-task")
    assert tmp_tasks_dir.exists()
    assert p.name == "my-task.json"


def test_state_path_sanitizes_slashes(tmp_tasks_dir):
    p = delegate._state_path("issue/1184/subtask")
    assert "/" not in p.name
    assert p.name == "issue_1184_subtask.json"


def test_write_state_atomic_no_partial_reads(tmp_tasks_dir):
    """Atomic write should never leave a partial file visible."""
    path = tmp_tasks_dir / "atomic-test.json"
    delegate._write_state_atomic(path, {"status": "running", "pid": 123})
    # Re-read
    loaded = json.loads(path.read_text())
    assert loaded["status"] == "running"
    assert loaded["pid"] == 123
    # tmp file must be cleaned up
    assert not path.with_suffix(".json.tmp").exists()


def test_read_state_missing_file(tmp_tasks_dir):
    assert delegate._read_state(tmp_tasks_dir / "nope.json") is None


def test_read_state_corrupted_json(tmp_tasks_dir):
    path = tmp_tasks_dir / "corrupted.json"
    tmp_tasks_dir.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")
    assert delegate._read_state(path) is None


def test_classify_final_status_prioritizes_cancelled_over_other_flags():
    assert delegate._classify_final_status(
        cancelled=True,
        rate_limited=True,
        ok_outcome=True,
        timed_out=True,
    ) == "cancelled"


def test_dispatch_parser_timeout_defaults():
    args = delegate.build_parser().parse_args([
        "dispatch",
        "--agent",
        "codex",
        "--task-id",
        "defaults",
        "--prompt",
        "hi",
    ])

    assert args.hard_timeout == 7200
    assert args.silence_timeout == 3600


def test_silence_timeout_default_is_3600():
    args = delegate.build_parser().parse_args([
        "dispatch",
        "--agent",
        "codex",
        "--task-id",
        "defaults",
        "--prompt",
        "hi",
    ])

    assert args.silence_timeout == 3600


def test_explicit_silence_timeout_override_still_works():
    args = delegate.build_parser().parse_args([
        "dispatch",
        "--agent",
        "codex",
        "--task-id",
        "override",
        "--prompt",
        "hi",
        "--silence-timeout",
        "600",
    ])

    assert args.silence_timeout == 600


def test_dispatch_help_documents_timeout_interaction(capsys):
    parser = delegate.build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["dispatch", "--help"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert "--hard-timeout" in captured.out
    assert "--silence-timeout" in captured.out
    assert "3600s" in captured.out
    assert "watchdog activity" in captured.out
    assert "fallback" in captured.out
    assert "0 disables" in captured.out


# ---------------------------------------------------------------------------
# PID liveness probe
# ---------------------------------------------------------------------------

def test_pid_alive_true_for_own_process():
    """Our own process is definitely alive."""
    assert delegate._pid_alive(os.getpid()) is True


def test_pid_alive_false_for_nonexistent_pid():
    """PID 999999999 is overwhelmingly unlikely to exist."""
    assert delegate._pid_alive(999_999_999) is False


# ---------------------------------------------------------------------------
# cmd_status zombie detection
# ---------------------------------------------------------------------------

def test_status_detects_zombie_when_pid_dead(tmp_tasks_dir, capsys):
    """Regression: if state says 'running' but PID is dead, status must
    flip the state to 'crashed' and persist the correction."""
    path = delegate._state_path("zombie-task")
    delegate._write_state_atomic(path, {
        "task_id": "zombie-task",
        "agent": "codex",
        "status": "running",
        "pid": 999_999_998,  # guaranteed dead
        "started_at": "2026-04-10T12:00:00+00:00",
    })

    # Run the status command
    import argparse
    args = argparse.Namespace(task_id="zombie-task")
    rc = delegate.cmd_status(args)
    assert rc == 0

    # State file should now be persisted as crashed
    updated = delegate._read_state(path)
    assert updated["status"] == "crashed"
    assert "not alive" in (updated.get("stderr_excerpt") or "")
    assert "'running'" in (updated.get("stderr_excerpt") or ""), (
        "stderr_excerpt should reference the PRIOR status, not the new one"
    )

    # stdout should contain the updated state as JSON
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["status"] == "crashed"


def test_status_leaves_running_alone_when_pid_alive(tmp_tasks_dir, capsys):
    """If the PID is our own (always alive), status must NOT flip to crashed."""
    path = delegate._state_path("alive-task")
    delegate._write_state_atomic(path, {
        "task_id": "alive-task",
        "agent": "codex",
        "status": "running",
        "pid": os.getpid(),
        "started_at": "2026-04-10T12:00:00+00:00",
    })

    import argparse
    args = argparse.Namespace(task_id="alive-task")
    delegate.cmd_status(args)

    updated = delegate._read_state(path)
    assert updated["status"] == "running"


def test_status_done_task_unchanged(tmp_tasks_dir, capsys):
    """A task already in a terminal state must not be touched."""
    path = delegate._state_path("done-task")
    delegate._write_state_atomic(path, {
        "task_id": "done-task",
        "agent": "codex",
        "status": "done",
        "pid": 999_999_998,  # dead, but should not trigger zombie flip
        "started_at": "2026-04-10T12:00:00+00:00",
        "finished_at": "2026-04-10T12:01:00+00:00",
    })

    import argparse
    args = argparse.Namespace(task_id="done-task")
    delegate.cmd_status(args)

    updated = delegate._read_state(path)
    assert updated["status"] == "done"  # unchanged


def test_status_missing_task_returns_error(tmp_tasks_dir, capsys):
    import argparse
    args = argparse.Namespace(task_id="nonexistent")
    rc = delegate.cmd_status(args)
    assert rc == 1
    captured = capsys.readouterr()
    assert "no state file" in captured.out


class _FakeMonitorResponse:
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def _monitor_payload(task_id: str, status: str, *, alive: bool = True) -> dict[str, Any]:
    return {
        "task": {
            "task_id": task_id,
            "status": status,
            "started_at": "2026-05-08T00:00:00+00:00",
        },
        "alive": alive,
    }


def test_status_or_fail_running_task_exits_zero_quiet(monkeypatch, capsys):
    import argparse

    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _FakeMonitorResponse(
            _monitor_payload("sleep-task", "running")
        ),
    )

    rc = delegate.cmd_status_or_fail(
        argparse.Namespace(task_id="sleep-task", verbose=False)
    )

    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_status_or_fail_completed_task_exits_one(monkeypatch, capsys):
    import argparse

    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _FakeMonitorResponse(
            _monitor_payload("sleep-task", "done", alive=False)
        ),
    )

    rc = delegate.cmd_status_or_fail(
        argparse.Namespace(task_id="sleep-task", verbose=False)
    )

    assert rc == 1
    captured = capsys.readouterr()
    assert "task sleep-task is not running (status=done, age=" in captured.err
    assert captured.err.rstrip().endswith("s)")


def test_status_or_fail_unknown_task_exits_one(monkeypatch, capsys):
    import argparse

    def fake_urlopen(*_args, **_kwargs):
        raise urllib.error.HTTPError(
            "http://localhost:8765/api/delegate/tasks/missing",
            404,
            "Not Found",
            {},
            None,
        )

    monkeypatch.setattr(delegate.urllib.request, "urlopen", fake_urlopen)

    rc = delegate.cmd_status_or_fail(
        argparse.Namespace(task_id="missing", verbose=False)
    )

    assert rc == 1
    captured = capsys.readouterr()
    assert "task missing is not running" in captured.err
    assert "task not found" in captured.err


def test_status_or_fail_monitor_api_down_exits_two(monkeypatch, capsys):
    import argparse

    def fake_urlopen(*_args, **_kwargs):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(delegate.urllib.request, "urlopen", fake_urlopen)

    rc = delegate.cmd_status_or_fail(
        argparse.Namespace(task_id="sleep-task", verbose=False)
    )

    assert rc == 2
    captured = capsys.readouterr()
    assert "Monitor API unreachable" in captured.err


# ---------------------------------------------------------------------------
# cmd_wait polling loop
# ---------------------------------------------------------------------------

def test_wait_returns_immediately_when_already_done(tmp_tasks_dir, capsys):
    path = delegate._state_path("wait-done")
    delegate._write_state_atomic(path, {
        "task_id": "wait-done",
        "agent": "codex",
        "status": "done",
        "started_at": "2026-04-10T12:00:00+00:00",
    })

    import argparse
    args = argparse.Namespace(
        task_id="wait-done", timeout=0, poll_interval=0.1,
    )
    t0 = time.monotonic()
    rc = delegate.cmd_wait(args)
    elapsed = time.monotonic() - t0

    assert rc == 0
    assert elapsed < 1.0, "wait on already-done task should return immediately"


def test_wait_returns_nonzero_on_failed(tmp_tasks_dir, capsys):
    path = delegate._state_path("wait-failed")
    delegate._write_state_atomic(path, {
        "task_id": "wait-failed",
        "status": "failed",
    })
    import argparse
    args = argparse.Namespace(
        task_id="wait-failed", timeout=0, poll_interval=0.1,
    )
    rc = delegate.cmd_wait(args)
    assert rc == 1  # nonzero for any non-done terminal status


def test_wait_returns_124_on_task_timeout(tmp_tasks_dir, capsys):
    path = delegate._state_path("wait-task-timeout")
    delegate._write_state_atomic(path, {
        "task_id": "wait-task-timeout",
        "status": "timeout",
    })
    import argparse
    args = argparse.Namespace(
        task_id="wait-task-timeout", timeout=0, poll_interval=0.1,
    )
    rc = delegate.cmd_wait(args)
    assert rc == 124


def test_wait_timeout_returns_124(tmp_tasks_dir, capsys):
    """Regression: on timeout, wait should return 124 (conventional
    timeout exit code) and print a timeout error on stderr."""
    path = delegate._state_path("wait-timeout")
    delegate._write_state_atomic(path, {
        "task_id": "wait-timeout",
        "status": "running",
        "pid": os.getpid(),  # alive, so no zombie detection
        "started_at": "2026-04-10T12:00:00+00:00",
    })
    import argparse
    args = argparse.Namespace(
        task_id="wait-timeout", timeout=1.0, poll_interval=0.1,
    )
    t0 = time.monotonic()
    rc = delegate.cmd_wait(args)
    elapsed = time.monotonic() - t0

    assert rc == 124
    assert 0.9 < elapsed < 2.5, f"wait should respect timeout, took {elapsed}s"
    captured = capsys.readouterr()
    assert "timeout" in captured.err


def test_wait_detects_zombie_and_returns_nonzero(tmp_tasks_dir, capsys):
    path = delegate._state_path("wait-zombie")
    delegate._write_state_atomic(path, {
        "task_id": "wait-zombie",
        "status": "running",
        "pid": 999_999_998,
        "started_at": "2026-04-10T12:00:00+00:00",
    })
    import argparse
    args = argparse.Namespace(
        task_id="wait-zombie", timeout=5.0, poll_interval=0.1,
    )
    rc = delegate.cmd_wait(args)
    assert rc == 1  # crashed → nonzero

    updated = delegate._read_state(path)
    assert updated["status"] == "crashed"


# ---------------------------------------------------------------------------
# cmd_dispatch guards
# ---------------------------------------------------------------------------

def test_dispatch_refuses_to_clobber_running_task(tmp_tasks_dir, capsys):
    """Dispatching with a task-id that's already running must fail fast."""
    path = delegate._state_path("duplicate-task")
    delegate._write_state_atomic(path, {
        "task_id": "duplicate-task",
        "status": "running",
        "pid": os.getpid(),  # alive
    })
    import argparse
    args = argparse.Namespace(
        agent="codex",
        task_id="duplicate-task",
        prompt="test",
        prompt_file=None,
        mode="read-only",
        model=None,
        cwd=None,
        worktree=None,
        hard_timeout=3600,
    )
    rc = delegate.cmd_dispatch(args)
    assert rc == 2
    captured = capsys.readouterr()
    assert "already running" in captured.err


def test_dispatch_popen_failure_marks_task_failed(tmp_tasks_dir, capsys):
    """Regression (Codex 2026-04-10 audit): if Popen itself fails (e.g.
    Python binary not found, invalid fd, etc.), cmd_dispatch must mark
    the task as 'failed' in the state file. Previously it would leave
    the task stuck at 'spawning' forever with pid=None, and zombie
    detection couldn't rescue it because zombie detection is gated on
    `pid and not _pid_alive(pid)`.
    """
    path = delegate._state_path("popen-failure")

    import argparse
    args = argparse.Namespace(
        agent="codex",
        task_id="popen-failure",
        prompt="test",
        prompt_file=None,
        mode="read-only",
        model=None,
        cwd=None,
        worktree=None,
        hard_timeout=3600,
    )

    # Make Popen raise FileNotFoundError — simulates a missing
    # Python interpreter or malformed command.
    with patch(
        "delegate.subprocess.Popen",
        side_effect=FileNotFoundError("no such file"),
    ):
        rc = delegate.cmd_dispatch(args)

    assert rc == 1

    # State must be terminal (failed), not stuck in spawning.
    state = delegate._read_state(path)
    assert state is not None
    assert state["status"] == "failed"
    assert "Popen failed" in (state.get("stderr_excerpt") or "")
    assert "FileNotFoundError" in (state.get("stderr_excerpt") or "")
    assert state["returncode"] is None
    assert state["returncode_reason"] == "worker process was not started"
    captured = capsys.readouterr()
    assert "failed to spawn" in captured.err


def test_dispatch_parses_max_budget_usd_flag():
    parser = delegate.build_parser()
    args = parser.parse_args([
        "dispatch",
        "--agent", "claude",
        "--task-id", "budget-task",
        "--prompt", "hi",
        "--max-budget-usd", "0.50",
    ])

    assert args.max_budget_usd == 0.5


def test_worker_parser_accepts_max_budget_usd():
    parser = delegate.build_parser()
    args = parser.parse_args([
        "_worker",
        "--task-id", "budget-task",
        "--agent", "claude",
        "--mode", "read-only",
        "--cwd", "/tmp",
        "--max-budget-usd", "0.50",
    ])

    assert args.max_budget_usd == 0.5


def test_dispatch_persists_and_forwards_max_budget_usd(tmp_tasks_dir):
    args = delegate.build_parser().parse_args([
        "dispatch",
        "--agent", "claude",
        "--task-id", "budget-dispatch",
        "--prompt", "hi",
        "--max-budget-usd", "0.50",
    ])
    captured: dict[str, list[str]] = {}

    class _FakeStdin:
        def write(self, _data):
            pass

        def close(self):
            pass

    class _FakeProc:
        pid = 12345
        stdin = _FakeStdin()

    def fake_popen(cmd, **_kwargs):
        captured["cmd"] = cmd
        return _FakeProc()

    with patch("delegate.subprocess.Popen", side_effect=fake_popen):
        rc = delegate.cmd_dispatch(args)

    assert rc == 0
    state = delegate._read_state(delegate._state_path("budget-dispatch"))
    assert state is not None
    assert state["max_budget_usd"] == 0.5
    cmd = captured["cmd"]
    assert "--max-budget-usd" in cmd
    assert cmd[cmd.index("--max-budget-usd") + 1] == "0.5"


def test_dispatch_initial_state_includes_resolved_telemetry(tmp_tasks_dir):
    """Dispatch should persist model/effort/cli_version immediately."""
    import argparse

    args = argparse.Namespace(
        agent="codex",
        task_id="telemetry-dispatch",
        prompt="test",
        prompt_file=None,
        mode="read-only",
        model=None,
        cwd=None,
        worktree=None,
        hard_timeout=3600,
        allow_merge=False,
        effort=None,
    )

    class _FakeStdin:
        def write(self, _data):
            pass

        def close(self):
            pass

    class _FakeProc:
        pid = 12345
        stdin = _FakeStdin()

    telemetry = type(
        "_Telemetry",
        (),
        {"model": "gpt-5.5", "effort": "high", "cli_version": "0.123.0"},
    )()

    with patch(
        "agent_runtime.telemetry.resolve_dispatch_start_telemetry",
        return_value=telemetry,
    ), patch("delegate.subprocess.Popen", return_value=_FakeProc()):
        rc = delegate.cmd_dispatch(args)

    assert rc == 0
    state = delegate._read_state(delegate._state_path("telemetry-dispatch"))
    assert state is not None
    assert state["model"] == "gpt-5.5"
    assert state["effort"] == "high"
    assert state["cli_version"] == "0.123.0"
    assert state["substitution"] is None


def test_dispatch_creates_logs_subdir_for_slashed_task_id(tmp_tasks_dir, monkeypatch):
    """task_id may include an agent prefix, e.g. codex/test-mkdir-1885."""
    import argparse

    class _FakeStdin:
        def write(self, _data): pass
        def close(self): pass

    class _FakeProc:
        pid = 12345
        stdin = _FakeStdin()

    args = argparse.Namespace(
        agent="codex",
        task_id="codex/test-mkdir-1885",
        prompt="test",
        prompt_file=None,
        mode="read-only",
        model=None,
        cwd=None,
        worktree=None,
        hard_timeout=3600,
        allow_merge=False,
        effort=None,
    )

    assert not (tmp_tasks_dir / "logs" / "codex").exists()

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *a, **k: _FakeProc())

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    assert (tmp_tasks_dir / "logs" / "codex" / "test-mkdir-1885.stdout.log").exists()
    assert (tmp_tasks_dir / "logs" / "codex" / "test-mkdir-1885.stderr.log").exists()


def test_cancel_refuses_terminal_status(tmp_tasks_dir, capsys):
    """Regression (Codex 2026-04-10 audit): cmd_cancel must refuse to
    signal a PID whose task is already in a terminal state. The OS may
    have recycled the stored PID to an unrelated process, and sending
    SIGTERM to that could damage something we have no business touching.
    """
    path = delegate._state_path("already-done")
    # Done task with a stored PID that happens to be our own (alive)
    # — cancel must still refuse because the TASK is done regardless
    # of whether the PID is alive.
    delegate._write_state_atomic(path, {
        "task_id": "already-done",
        "status": "done",
        "pid": os.getpid(),
    })

    import argparse
    args = argparse.Namespace(task_id="already-done")
    rc = delegate.cmd_cancel(args)

    assert rc == 1
    captured = capsys.readouterr()
    assert "terminal state" in captured.err
    assert "done" in captured.err


def test_cancel_refuses_crashed_task(tmp_tasks_dir, capsys):
    """Crashed is also terminal — cancel must refuse."""
    path = delegate._state_path("crashed-task")
    delegate._write_state_atomic(path, {
        "task_id": "crashed-task",
        "status": "crashed",
        "pid": 999_999_999,
    })
    import argparse
    args = argparse.Namespace(task_id="crashed-task")
    rc = delegate.cmd_cancel(args)
    assert rc == 1
    captured = capsys.readouterr()
    assert "terminal state" in captured.err


def test_worker_sigterm_handler_raises_keyboard_interrupt():
    """Regression (Gemini 2026-04-10 review, BUG #3): the worker's
    SIGTERM handler must raise an exception so the runtime's finally
    block unwinds. Without this, SIGTERM terminates Python abruptly
    and the codex/gemini/claude subprocess gets orphaned.
    """
    with pytest.raises(KeyboardInterrupt, match="SIGTERM"):
        delegate._worker_sigterm_handler(15, None)


def test_write_state_atomic_uses_pid_suffixed_tmp(tmp_tasks_dir):
    """Regression (Gemini 2026-04-10 review, BUG #2): concurrent writers
    must not collide on a shared .json.tmp scratch file. Each writer
    should use a PID-suffixed tmp filename.

    Verification: after a write completes, no tmp file should be left
    behind AND the scratch filename actually used should include the
    current PID.
    """
    path = tmp_tasks_dir / "concurrency-test.json"

    # Sneak in a peek at what filename _write_state_atomic picks by
    # patching os.replace to capture the source path.
    captured_tmps: list[Path] = []
    real_replace = delegate.os.replace

    def capturing_replace(src, dst):
        captured_tmps.append(Path(src))
        return real_replace(src, dst)

    with patch.object(delegate.os, "replace", side_effect=capturing_replace):
        delegate._write_state_atomic(path, {"status": "running"})

    assert len(captured_tmps) == 1
    tmp_name = captured_tmps[0].name
    assert str(os.getpid()) in tmp_name, (
        f"tmp filename should include PID for concurrency safety: {tmp_name}"
    )
    assert ".json.tmp" in tmp_name


def test_zombie_detection_works_on_pid_before_worker_writes(tmp_tasks_dir, capsys):
    """Regression (Gemini 2026-04-10 review, BUG #1): if the worker
    crashes before it has a chance to overwrite the state file with its
    own PID, the PARENT must have already written the Popen child's
    PID into state. Otherwise status/wait never detect the crash
    because zombie detection is gated on 'if pid and not _pid_alive(pid)'.

    Simulation: write a state file with a dead PID + status=spawning
    (as if the parent wrote PID but the worker crashed before it could
    run). status must flip it to crashed.
    """
    path = delegate._state_path("early-crash")
    delegate._write_state_atomic(path, {
        "task_id": "early-crash",
        "status": "spawning",
        "pid": 999_999_997,  # parent wrote this, worker never ran
    })

    import argparse
    args = argparse.Namespace(task_id="early-crash")
    delegate.cmd_status(args)

    updated = delegate._read_state(path)
    assert updated["status"] == "crashed", (
        "early-crash state (parent wrote PID, worker died before "
        "updating) must be detectable as crashed. Without the Gemini fix "
        "this would be stuck in 'spawning' forever."
    )


def test_dispatch_clobber_guard_rejects_spawning_status(tmp_tasks_dir, capsys):
    """Regression (Codex 2026-04-10 review): the clobber guard must
    reject dispatch when an existing task is in EITHER 'running' OR
    'spawning' state. Earlier version only checked 'running', leaving
    a tiny window between Popen and the worker's first state-update
    where a second dispatch could overwrite state and spawn a
    duplicate worker for the same task_id.
    """
    path = delegate._state_path("spawning-clobber")
    delegate._write_state_atomic(path, {
        "task_id": "spawning-clobber",
        "status": "spawning",
        "pid": os.getpid(),  # alive
    })
    import argparse
    args = argparse.Namespace(
        agent="codex",
        task_id="spawning-clobber",
        prompt="test",
        prompt_file=None,
        mode="read-only",
        model=None,
        cwd=None,
        worktree=None,
        hard_timeout=3600,
    )
    rc = delegate.cmd_dispatch(args)
    assert rc == 2, "must reject duplicate dispatch during spawning window"
    captured = capsys.readouterr()
    assert "spawning" in captured.err


def test_dispatch_allows_new_task_when_prior_crashed(tmp_tasks_dir, capsys):
    """If the old state is terminal, dispatching should proceed (not tested
    end-to-end here — we just verify the guard doesn't trip). We patch
    subprocess.Popen so no real worker is spawned."""
    path = delegate._state_path("prior-crashed")
    delegate._write_state_atomic(path, {
        "task_id": "prior-crashed",
        "status": "crashed",
        "pid": 999_999_998,
    })
    import argparse
    args = argparse.Namespace(
        agent="codex",
        task_id="prior-crashed",
        prompt="test",
        prompt_file=None,
        mode="read-only",
        model=None,
        cwd=None,
        worktree=None,
        hard_timeout=3600,
    )

    # Patch Popen so we don't actually spawn a worker.
    class _FakeStdin:
        def write(self, _data): pass
        def close(self): pass

    class _FakeProc:
        pid = 12345  # parent writes this into state for zombie detection
        stdin = _FakeStdin()

    with patch("delegate.subprocess.Popen", return_value=_FakeProc()):
        rc = delegate.cmd_dispatch(args)

    assert rc == 0
    # State file should have been rewritten with status=spawning AND
    # the parent should have written the fake proc's PID into state
    # immediately after Popen (Gemini fix: catches early-crash zombies).
    state = delegate._read_state(path)
    assert state["status"] == "spawning"
    assert state["pid"] == 12345, (
        "parent MUST write Popen child's PID into state file immediately "
        "after spawn, before the worker gets a chance to run"
    )


def test_run_worker_persists_runtime_telemetry(tmp_tasks_dir, tmp_path):
    """Worker completion should backfill runtime-resolved telemetry fields."""
    state_path = delegate._state_path("worker-telemetry")
    delegate._write_state_atomic(state_path, {
        "task_id": "worker-telemetry",
        "model": "unknown",
        "effort": "unknown",
        "cli_version": "unknown",
    })

    mock_result = type(
        "_Result",
        (),
        {
            "ok": True,
            "response": "done",
            "stderr_excerpt": None,
            "returncode": 0,
            "rate_limited": False,
            "model": "claude-opus-4-6",
            "effort": "xhigh",
            "cli_version": "2.1.89",
        },
    )()

    with patch("agent_runtime.runner.invoke", return_value=mock_result):
        rc = delegate._run_worker(
            task_id="worker-telemetry",
            agent="claude",
            prompt="hi",
            mode="read-only",
            cwd_str=str(tmp_path),
            model=None,
            hard_timeout=60,
            effort=None,
        )

    assert rc == 0
    state = delegate._read_state(state_path)
    assert state is not None
    assert state["status"] == "done"
    assert state["model"] == "claude-opus-4-6"
    assert state["effort"] == "xhigh"
    assert state["cli_version"] == "2.1.89"
    assert state["returncode"] == 0
    assert state["returncode_reason"] is None


def test_run_worker_emits_one_terminal_dispatch_event_with_cost_fields(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    from telemetry import emit as emit_mod

    event_dir = tmp_path / "telemetry-events"

    def event_dir_fn() -> Path:
        event_dir.mkdir(parents=True, exist_ok=True)
        return event_dir

    monkeypatch.setattr(emit_mod, "_event_dir", event_dir_fn)
    monkeypatch.setenv("LU_RUN_ID", "run-dispatch")
    monkeypatch.setenv("LU_SESSION_ID", "session-dispatch")

    state_path = delegate._state_path("worker-dispatch-event")
    delegate._write_state_atomic(state_path, {
        "task_id": "worker-dispatch-event",
        "model": "unknown",
        "effort": "unknown",
        "cli_version": "unknown",
        "prompt_chars": 2,
        "worktree_branch": "deepseek/worker-dispatch-event",
        "worktree_path": str(tmp_path),
    })

    mock_result = type(
        "_Result",
        (),
        {
            "ok": True,
            "response": "done",
            "stderr_excerpt": None,
            "returncode": 0,
            "rate_limited": False,
            "model": "text-embedding-3-small",
            "effort": "unknown",
            "cli_version": "test",
            "substitution": {
                "requested_provider": "deepseek",
                "requested_model": "deepseek-v4-pro",
                "actual_provider": "openrouter",
                "actual_model": "deepseek/deepseek-v3.2",
                "substituted": True,
            },
            "usage_record": {"tokens": 1_000},
        },
    )()

    with patch("agent_runtime.runner.invoke", return_value=mock_result):
        rc = delegate._run_worker(
            task_id="worker-dispatch-event",
            agent="deepseek",
            prompt="hi",
            mode="read-only",
            cwd_str=str(tmp_path),
            model=None,
            hard_timeout=60,
            effort=None,
        )

    assert rc == 0
    event_files = sorted(event_dir.glob("*.jsonl"))
    assert len(event_files) == 1
    events = [
        json.loads(line)
        for line in event_files[0].read_text(encoding="utf-8").splitlines()
    ]
    dispatch_events = [event for event in events if event["event_type"] == "dispatch"]
    assert len(dispatch_events) == 1
    event = dispatch_events[0]
    assert event["task_id"] == "worker-dispatch-event"
    assert event["agent"] == "deepseek"
    assert event["status"] == "done"
    assert event["duration_s"] >= 0
    assert event["prompt_chars"] == 2
    assert event["response_chars"] == 4
    assert event["tokens"] == 1_000
    assert event["substitution"]["substituted"] is True
    state = delegate._read_state(state_path)
    assert state is not None
    assert state["substitution"]["actual_provider"] == "openrouter"
    assert event["cost_usd"] == pytest.approx(0.00002)
    assert event["billing_model"] == "per_token"
    assert event["cost_provenance"] == "priced"


def test_run_worker_marks_needs_finalize_for_dirty_danger_worktree(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """Danger dispatches with edits but no commits surface needs_finalize (#2134)."""
    _sanitize_git_env_for_test(monkeypatch)
    state_path = delegate._state_path("needs-finalize")
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    delegate._write_state_atomic(state_path, {
        "task_id": "needs-finalize",
        "worktree_path": str(tmp_path),
        "worktree_base": "main",
    })
    (tmp_path / "orphan.txt").write_text("left behind", encoding="utf-8")

    mock_result = type(
        "_Result",
        (),
        {
            "ok": True,
            "response": "done",
            "stderr_excerpt": None,
            "returncode": 0,
            "rate_limited": False,
            "model": "gpt-5.5",
            "effort": "xhigh",
            "cli_version": "0.131.0",
        },
    )()

    monkeypatch.setattr(delegate, "_count_commits_ahead", lambda *_a, **_k: 0)
    monkeypatch.setattr(
        delegate,
        "_auto_finalize_dirty_worktree",
        lambda **_kwargs: delegate.AutoFinalizeResult(
            ok=False,
            error="simulated finalize failure",
            changed_files=("orphan.txt",),
        ),
    )

    with (
        patch("agent_runtime.runner.invoke", return_value=mock_result),
        patch.object(delegate, "_count_commits_ahead", return_value=0),
    ):
        rc = delegate._run_worker(
            task_id="needs-finalize",
            agent="codex",
            prompt="hi",
            mode="danger",
            cwd_str=str(tmp_path),
            model=None,
            hard_timeout=60,
            effort="xhigh",
        )

    assert rc == 1
    state = delegate._read_state(state_path)
    assert state is not None
    assert state["status"] == "needs_finalize"
    assert state["needs_finalize"] is True
    assert state["commits_ahead"] == 0
    assert state["worktree_dirty_on_exit"] is True
    assert state["auto_finalize"]["ok"] is False
    assert state["auto_finalize"]["error"] == "simulated finalize failure"


def test_run_worker_auto_finalizes_dirty_agy_worktree(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """Agy dispatches with clean rc=0, dirty worktree, and zero commits finalize."""
    _sanitize_git_env_for_test(monkeypatch)
    origin = tmp_path / "origin.git"
    worktree = tmp_path / "worktree"
    subprocess.run(
        ["git", "init", "--bare", str(origin)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "init", "--initial-branch=main", str(worktree)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=worktree,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=worktree,
        check=True,
        capture_output=True,
    )
    (worktree / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=worktree, check=True)
    subprocess.run(["git", "commit", "-m", "base"], cwd=worktree, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", str(origin)],
        cwd=worktree,
        check=True,
    )
    subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=worktree,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "-b", "agy/auto-finalize-test"],
        cwd=worktree,
        check=True,
        capture_output=True,
    )

    state_path = delegate._state_path("agy-auto-finalize-test")
    delegate._write_state_atomic(state_path, {
        "task_id": "agy-auto-finalize-test",
        "worktree_path": str(worktree),
        "worktree_branch": "agy/auto-finalize-test",
        "worktree_base": "main",
    })
    (worktree / "artifact.txt").write_text("agy wrote this\n", encoding="utf-8")

    pushed: list[str] = []
    created_prs: list[dict[str, str]] = []

    def fake_push(_worktree: Path, branch: str) -> None:
        pushed.append(branch)

    def fake_create_pr(
        _worktree: Path,
        *,
        branch: str,
        base_branch: str,
        title: str,
        body: str,
    ) -> str:
        created_prs.append({
            "branch": branch,
            "base_branch": base_branch,
            "title": title,
            "body": body,
        })
        return "https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/999"

    monkeypatch.setattr(delegate, "_push_auto_finalize_branch", fake_push)
    monkeypatch.setattr(delegate, "_create_auto_finalize_pr", fake_create_pr)

    mock_result = type(
        "_Result",
        (),
        {
            "ok": False,
            "response": "",
            "stderr_excerpt": None,
            "returncode": 0,
            "rate_limited": False,
            "model": "gemini-3.5-flash-high",
            "effort": "unknown",
            "cli_version": "1.0.0",
        },
    )()

    with patch("agent_runtime.runner.invoke", return_value=mock_result):
        rc = delegate._run_worker(
            task_id="agy-auto-finalize-test",
            agent="agy",
            prompt="hi",
            mode="danger",
            cwd_str=str(worktree),
            model=None,
            hard_timeout=60,
            effort=None,
        )

    assert rc == 0
    state = delegate._read_state(state_path)
    assert state is not None
    assert state["status"] == "done"
    assert state["needs_finalize"] is False
    assert state["worktree_dirty_on_exit"] is False
    assert state["commits_ahead"] == 1
    assert state["auto_finalize"]["ok"] is True
    assert state["auto_finalize"]["changed_files"] == ["artifact.txt"]
    assert pushed == ["agy/auto-finalize-test"]
    assert created_prs[0]["branch"] == "agy/auto-finalize-test"
    assert created_prs[0]["base_branch"] == "main"

    message = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=worktree,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "X-Agent: agy/auto-finalize-test" in message


def test_auto_finalize_push_failure_soft_resets_local_commit(tmp_path, monkeypatch):
    _sanitize_git_env_for_test(monkeypatch)
    worktree = tmp_path / "worktree"
    subprocess.run(
        ["git", "init", "--initial-branch=main", str(worktree)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=worktree,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=worktree,
        check=True,
        capture_output=True,
    )
    (worktree / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=worktree, check=True)
    subprocess.run(["git", "commit", "-m", "base"], cwd=worktree, check=True)
    subprocess.run(
        ["git", "checkout", "-b", "agy/push-fails"],
        cwd=worktree,
        check=True,
        capture_output=True,
    )
    base_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=worktree,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (worktree / "artifact.txt").write_text("agy wrote this\n", encoding="utf-8")

    def fail_push(_worktree: Path, _branch: str) -> None:
        raise RuntimeError("simulated push failure")

    def fail_create_pr(**_kwargs: Any) -> str:
        pytest.fail("PR creation must not run after push failure")

    monkeypatch.setattr(delegate, "_push_auto_finalize_branch", fail_push)
    monkeypatch.setattr(delegate, "_create_auto_finalize_pr", fail_create_pr)

    result = delegate._auto_finalize_dirty_worktree(
        worktree=worktree,
        task_id="agy-push-fails",
        agent="agy",
        branch="agy/push-fails",
        base_branch="main",
    )

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=worktree,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=worktree,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    log_subjects = subprocess.run(
        ["git", "log", "--format=%s"],
        cwd=worktree,
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    assert status
    assert head == base_head
    assert "chore(dispatch): finalize agy task agy-push-fails" not in log_subjects
    assert result.ok is False
    assert result.error == "simulated push failure"
    assert result.commit_sha is None


def test_auto_finalize_rejects_non_git_worktree(tmp_path):
    (tmp_path / "artifact.txt").write_text("not in git\n", encoding="utf-8")

    result = delegate._auto_finalize_dirty_worktree(
        worktree=tmp_path,
        task_id="not-git",
        agent="agy",
        branch="agy/not-git",
        base_branch="main",
    )

    assert result.ok is False
    assert "worktree" in (result.error or "")
    assert not (tmp_path / ".git").exists()


def test_run_worker_forwards_max_budget_usd_to_runtime(tmp_tasks_dir, tmp_path):
    state_path = delegate._state_path("worker-budget")
    delegate._write_state_atomic(state_path, {"task_id": "worker-budget"})

    mock_result = type(
        "_Result",
        (),
        {
            "ok": True,
            "response": "done",
            "stderr_excerpt": None,
            "returncode": 0,
            "rate_limited": False,
            "model": "claude-opus-4-7",
            "effort": "unknown",
            "cli_version": "2.1.116",
        },
    )()

    with patch("agent_runtime.runner.invoke", return_value=mock_result) as mock_invoke:
        rc = delegate._run_worker(
            task_id="worker-budget",
            agent="claude",
            prompt="hi",
            mode="read-only",
            cwd_str=str(tmp_path),
            model=None,
            hard_timeout=60,
            max_budget_usd=0.5,
            effort=None,
        )

    assert rc == 0
    assert mock_invoke.call_args.kwargs["tool_config"] == {"max_budget_usd": 0.5}
    state = delegate._read_state(state_path)
    assert state is not None
    assert state["max_budget_usd"] == 0.5


def test_run_worker_silence_timeout_kills_silent_subprocess(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """A stdout-silent CLI is SIGKILLed and persisted as status=timeout."""
    from agent_runtime import runner as runtime_runner

    state_path = delegate._state_path("silent-timeout")
    returncode_file = tmp_path / "returncode.txt"
    delegate._write_state_atomic(state_path, {"task_id": "silent-timeout"})

    class SleepingAdapter:
        name = "claude"
        default_model = "fixture-model"
        supported_modes = frozenset({"read-only"})

        def build_invocation(self, **kwargs: Any) -> InvocationPlan:
            return InvocationPlan(
                cmd=["/bin/sh", "-c", "sleep 60"],
                cwd=Path(kwargs["cwd"]),
            )

        def parse_response(self, *, returncode: int, **_kwargs: Any) -> ParseResult:
            returncode_file.write_text(str(returncode), encoding="utf-8")
            return ParseResult(ok=False, response="", stderr_excerpt="")

        def liveness_signal_paths(self, _plan: InvocationPlan) -> tuple[Path, ...]:
            return ()

    monkeypatch.setattr(runtime_runner, "has_headroom", lambda *_args: (True, ""))
    monkeypatch.setattr(runtime_runner, "write_record", lambda _record: None)
    monkeypatch.setattr(
        runtime_runner,
        "resolve_invocation_telemetry",
        lambda **_kwargs: InvocationTelemetry(
            model="fixture-model",
            effort="unknown",
            cli_version="fixture",
        ),
    )
    monkeypatch.setitem(runtime_runner._ADAPTER_CACHE, "claude", SleepingAdapter())

    started = time.monotonic()
    rc = delegate._run_worker(
        task_id="silent-timeout",
        agent="claude",
        prompt="hi",
        mode="read-only",
        cwd_str=str(tmp_path),
        model=None,
        hard_timeout=30,
        silence_timeout=1,
        effort=None,
    )
    elapsed = time.monotonic() - started

    state = delegate._read_state(state_path)
    events = [
        json.loads(line)
        for line in (tmp_tasks_dir / "dispatch_events.jsonl").read_text().splitlines()
    ]

    assert rc == 1
    assert elapsed < 6
    assert int(returncode_file.read_text("utf-8")) == -signal.SIGKILL
    assert state is not None
    assert state["status"] == "timeout"
    assert "stdout_silence_timeout" in (state["stderr_excerpt"] or "")
    assert events[-1]["event"] == "dispatch_silence_timeout"
    assert events[-1]["task_id"] == "silent-timeout"
    assert events[-1]["status"] == "timeout"
    assert events[-1]["silence_timeout_s"] == 1


def test_run_worker_periodic_stdout_avoids_silence_timeout(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """Scaled version of the 70-minute case: stdout before each silence window."""
    from agent_runtime import runner as runtime_runner

    state_path = delegate._state_path("periodic-stdout")
    delegate._write_state_atomic(state_path, {"task_id": "periodic-stdout"})

    class ChatteringAdapter:
        name = "claude"
        default_model = "fixture-model"
        supported_modes = frozenset({"read-only"})

        def build_invocation(self, **kwargs: Any) -> InvocationPlan:
            script = (
                "i=0; "
                "while [ $i -lt 5 ]; do "
                "echo tick-$i; "
                "i=$((i + 1)); "
                "sleep 0.2; "
                "done"
            )
            return InvocationPlan(
                cmd=["/bin/sh", "-c", script],
                cwd=Path(kwargs["cwd"]),
            )

        def parse_response(
            self,
            *,
            stdout: str,
            returncode: int,
            **_kwargs: Any,
        ) -> ParseResult:
            return ParseResult(
                ok=returncode == 0,
                response=stdout,
                stderr_excerpt=None,
            )

        def liveness_signal_paths(self, _plan: InvocationPlan) -> tuple[Path, ...]:
            return ()

    monkeypatch.setattr(runtime_runner, "has_headroom", lambda *_args: (True, ""))
    monkeypatch.setattr(runtime_runner, "write_record", lambda _record: None)
    monkeypatch.setattr(
        runtime_runner,
        "resolve_invocation_telemetry",
        lambda **_kwargs: InvocationTelemetry(
            model="fixture-model",
            effort="unknown",
            cli_version="fixture",
        ),
    )
    monkeypatch.setitem(runtime_runner._ADAPTER_CACHE, "claude", ChatteringAdapter())

    rc = delegate._run_worker(
        task_id="periodic-stdout",
        agent="claude",
        prompt="hi",
        mode="read-only",
        cwd_str=str(tmp_path),
        model=None,
        hard_timeout=10,
        silence_timeout=1,
        effort=None,
    )

    state = delegate._read_state(state_path)
    assert rc == 0
    assert state is not None
    assert state["status"] == "done"
    assert state["response_chars"] > 0
    assert not (tmp_tasks_dir / "dispatch_events.jsonl").exists()


def test_dispatch_rejects_danger_without_worktree(tmp_tasks_dir, capsys):
    import argparse

    args = argparse.Namespace(
        agent="codex",
        task_id="danger-no-worktree",
        prompt="test",
        prompt_file=None,
        mode="danger",
        model=None,
        cwd=None,
        worktree=None,
        hard_timeout=3600,
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 2
    assert delegate._read_state(delegate._state_path("danger-no-worktree")) is None
    captured = capsys.readouterr()
    assert "--worktree" in captured.err


def _make_run_stub(
    *,
    rev_parse_verify_ok: bool = True,
    rev_parse_head_sha: str = "abc1234",
    status_porcelain: str = "",
    rev_list_count: str = "0",
    abbrev_ref: str = "",
    rebase_ok: bool = True,
):
    """Helper: build a fake subprocess.run that understands the git commands
    _ensure_worktree/_validate_existing_worktree issue. Returns ``(calls, fn)``.
    """
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        if cmd[:2] == ["git", "fetch"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:2] == ["git", "rev-parse"]:
            if "--verify" in cmd:
                rc = 0 if rev_parse_verify_ok else 1
                out = rev_parse_head_sha if rc == 0 else ""
                return subprocess.CompletedProcess(cmd, rc, out, "")
            if "--abbrev-ref" in cmd:
                return subprocess.CompletedProcess(cmd, 0, abbrev_ref, "")
            return subprocess.CompletedProcess(cmd, 0, rev_parse_head_sha, "")
        if cmd[:2] == ["git", "status"]:
            return subprocess.CompletedProcess(cmd, 0, status_porcelain, "")
        if cmd[:2] == ["git", "rev-list"]:
            return subprocess.CompletedProcess(cmd, 0, rev_list_count, "")
        if cmd[:3] == ["git", "worktree", "add"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:2] == ["git", "rebase"]:
            rc = 0 if rebase_ok else 1
            return subprocess.CompletedProcess(cmd, rc, "", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    return calls, fake_run


def test_dispatch_creates_worktree_and_records_it(tmp_tasks_dir, tmp_path, monkeypatch, capsys):
    import argparse

    recorded_prompt: dict[str, str] = {}
    worktree_path = tmp_path / ".worktrees" / "codex-1383"

    class _FakeStdin:
        def write(self, data):
            recorded_prompt["text"] = data.decode("utf-8")

        def close(self):
            pass

    class _FakeProc:
        pid = 24680
        stdin = _FakeStdin()

    calls, fake_run = _make_run_stub(rev_parse_head_sha="deadbeef")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *a, **k: _FakeProc())

    args = argparse.Namespace(
        agent="codex",
        task_id="issue-1383-smoke",
        prompt="Implement the fix",
        prompt_file=None,
        mode="danger",
        model=None,
        cwd=None,
        worktree=str(worktree_path),
        base="main",
        hard_timeout=3600,
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    state = delegate._read_state(delegate._state_path("issue-1383-smoke"))
    assert state is not None
    assert state["status"] == "spawning"
    assert state["worktree_branch"] == "codex/issue-1383-smoke"
    assert state["worktree_path"].endswith(".worktrees/codex-1383")
    assert state["cwd"].endswith(".worktrees/codex-1383")
    assert state["pid"] == 24680
    assert state["worktree_base_sha"] == "deadbeef"
    assert state["worktree_reused"] is False
    assert "delegate worktree" in recorded_prompt["text"]
    assert ".worktrees/codex-1383" in recorded_prompt["text"]
    # At minimum: git fetch + git rev-parse --verify + git worktree add + git rev-parse HEAD.
    assert any(c[:3] == ["git", "worktree", "add"] for c in calls)
    assert any(c[:2] == ["git", "fetch"] for c in calls)
    # Fix 1: the worktree add MUST branch from origin/main, not local main.
    add_cmd = next(c for c in calls if c[:3] == ["git", "worktree", "add"])
    assert add_cmd[-1] == "origin/main", (
        f"worktree must be created from origin/main, got base={add_cmd[-1]!r}"
    )
    captured = capsys.readouterr()
    assert "issue-1383-smoke" in captured.out


def test_fetch_base_strips_origin_prefix(monkeypatch):
    """`--base origin/main` (the mandated runbook form) must fetch refspec `main`.

    `git fetch origin origin/main` asks the remote for a ref literally named
    ``origin/main`` — nonexistent — so the fetch failed and every conforming
    dispatch silently fell back to the local (possibly stale) tracking ref.
    """
    calls, fake_run = _make_run_stub()
    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    assert delegate._fetch_base("origin/main") is True

    fetch_cmd = next(c for c in calls if c[:2] == ["git", "fetch"])
    assert fetch_cmd == ["git", "fetch", "origin", "main"]
    verify_cmd = next(
        c for c in calls if c[:2] == ["git", "rev-parse"] and "--verify" in c
    )
    assert verify_cmd[-1] == "origin/main"


def test_fetch_base_plain_branch_unchanged(monkeypatch):
    calls, fake_run = _make_run_stub()
    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    assert delegate._fetch_base("main") is True

    fetch_cmd = next(c for c in calls if c[:2] == ["git", "fetch"])
    assert fetch_cmd == ["git", "fetch", "origin", "main"]


def test_dispatch_origin_prefixed_base_branches_from_remote_ref(
    tmp_tasks_dir, tmp_path, monkeypatch, capsys
):
    """base="origin/main" must produce `worktree add ... origin/main`,
    never the unresolvable `origin/origin/main`."""
    import argparse

    class _FakeStdin:
        def write(self, _data):
            pass

        def close(self):
            pass

    class _FakeProc:
        pid = 24681
        stdin = _FakeStdin()

    calls, fake_run = _make_run_stub(rev_parse_head_sha="feedc0de")
    monkeypatch.setattr(delegate.subprocess, "run", fake_run)
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *a, **k: _FakeProc())

    args = argparse.Namespace(
        agent="codex",
        task_id="origin-base-smoke",
        prompt="Implement the fix",
        prompt_file=None,
        mode="danger",
        model=None,
        cwd=None,
        worktree=str(tmp_path / ".worktrees" / "codex-origin-base"),
        base="origin/main",
        hard_timeout=3600,
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    fetch_cmd = next(c for c in calls if c[:2] == ["git", "fetch"])
    assert fetch_cmd == ["git", "fetch", "origin", "main"]
    add_cmd = next(c for c in calls if c[:3] == ["git", "worktree", "add"])
    assert add_cmd[-1] == "origin/main", (
        f"worktree must be created from origin/main, got base={add_cmd[-1]!r}"
    )


def test_validate_existing_worktree_origin_prefixed_base(monkeypatch, tmp_path):
    """The stale-base check must compare against origin/main, not
    origin/origin/main (which made the check a silent no-op)."""
    calls, fake_run = _make_run_stub(rev_list_count="2", abbrev_ref="codex/x")
    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    rebased = delegate._validate_existing_worktree(
        path=tmp_path, expected_branch="codex/x", base="origin/main"
    )

    assert rebased is True
    rev_list_cmd = next(c for c in calls if c[:2] == ["git", "rev-list"])
    assert rev_list_cmd[-1] == "HEAD..origin/main"
    rebase_cmd = next(
        c for c in calls if c[:2] == ["git", "rebase"] and "--abort" not in c
    )
    assert rebase_cmd[-1] == "origin/main"


def test_dispatch_defaults_worker_env_to_no_merge(tmp_tasks_dir, monkeypatch):
    import argparse

    recorded: dict[str, object] = {}

    class _FakeStdin:
        def write(self, _data):
            pass

        def close(self):
            pass

    class _FakeProc:
        pid = 24680
        stdin = _FakeStdin()

    def fake_popen(*args, **kwargs):
        recorded["env"] = kwargs.get("env", {})
        return _FakeProc()

    monkeypatch.setattr(delegate.subprocess, "Popen", fake_popen)

    args = argparse.Namespace(
        agent="codex",
        task_id="read-only-no-merge",
        prompt="test",
        prompt_file=None,
        mode="read-only",
        model=None,
        cwd=None,
        worktree=None,
        hard_timeout=3600,
        allow_merge=False,
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    env = recorded["env"]
    assert env["AGENT_NO_MERGE"] == "1"
    assert "AGENT_ALLOW_MERGE" not in env


def test_dispatch_allow_merge_opt_in_updates_worker_env(tmp_tasks_dir, monkeypatch):
    import argparse

    recorded: dict[str, object] = {}

    class _FakeStdin:
        def write(self, _data):
            pass

        def close(self):
            pass

    class _FakeProc:
        pid = 13579
        stdin = _FakeStdin()

    def fake_popen(*args, **kwargs):
        recorded["env"] = kwargs.get("env", {})
        return _FakeProc()

    _, fake_run = _make_run_stub()
    monkeypatch.setattr(delegate.subprocess, "run", fake_run)
    monkeypatch.setattr(delegate.subprocess, "Popen", fake_popen)

    args = argparse.Namespace(
        agent="codex",
        task_id="danger-merge-opt-in",
        prompt="test",
        prompt_file=None,
        mode="danger",
        model=None,
        cwd=None,
        worktree=str(tmp_tasks_dir / "wt"),
        base="main",
        hard_timeout=3600,
        allow_merge=True,
    )

    (tmp_tasks_dir / "wt").mkdir(parents=True)

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    env = recorded["env"]
    assert env.get("AGENT_NO_MERGE") != "1"
    assert env["AGENT_ALLOW_MERGE"] == "1"


def test_dispatch_codex_worker_env_maps_github_token_to_gh_token(
    tmp_tasks_dir, tmp_path, monkeypatch,
):
    import argparse

    recorded: dict[str, object] = {}
    secrets_path = tmp_path / ".bash_secrets"
    secrets_path.write_text("export GITHUB_TOKEN=ghp_fromfile\n")

    class _FakeStdin:
        def write(self, _data):
            pass

        def close(self):
            pass

    class _FakeProc:
        pid = 24680
        stdin = _FakeStdin()

    def fake_popen(*args, **kwargs):
        recorded["env"] = kwargs.get("env", {})
        return _FakeProc()

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setattr(delegate, "_BASH_SECRETS_PATH", secrets_path)
    monkeypatch.setattr(delegate.subprocess, "Popen", fake_popen)

    args = argparse.Namespace(
        agent="codex",
        task_id="codex-gh-token",
        prompt="test",
        prompt_file=None,
        mode="read-only",
        model=None,
        cwd=None,
        worktree=None,
        hard_timeout=3600,
        allow_merge=False,
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    env = recorded["env"]
    assert env["GH_TOKEN"] == "ghp_fromfile"
    assert "GITHUB_TOKEN" not in env


def test_dispatch_gemini_worker_env_strips_gh_token(
    tmp_tasks_dir, monkeypatch,
):
    import argparse

    recorded: dict[str, object] = {}

    class _FakeStdin:
        def write(self, _data):
            pass

        def close(self):
            pass

    class _FakeProc:
        pid = 24680
        stdin = _FakeStdin()

    def fake_popen(*args, **kwargs):
        recorded["env"] = kwargs.get("env", {})
        return _FakeProc()

    monkeypatch.setenv("GITHUB_TOKEN", "ghp_parentgithub")
    monkeypatch.setenv("GH_TOKEN", "ghp_parentgh")
    monkeypatch.setattr(delegate.subprocess, "Popen", fake_popen)

    args = argparse.Namespace(
        agent="gemini",
        task_id="gemini-no-gh-token",
        prompt="test",
        prompt_file=None,
        mode="read-only",
        model=None,
        cwd=None,
        worktree=None,
        hard_timeout=3600,
        allow_merge=False,
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    env = recorded["env"]
    assert "GH_TOKEN" not in env
    assert "GITHUB_TOKEN" not in env


def test_dispatch_uses_existing_worktree_without_git_add(tmp_tasks_dir, tmp_path, monkeypatch):
    import argparse

    worktree = tmp_path / "existing-worktree"
    worktree.mkdir()

    class _FakeStdin:
        def write(self, _data):
            pass

        def close(self):
            pass

    class _FakeProc:
        pid = 13579
        stdin = _FakeStdin()

    # Allow the validation calls (rev-parse, status, rev-list, fetch) to
    # run but refuse `git worktree add` — that's what "without_git_add"
    # is asserting. Validation returns "clean, matching, up-to-date" so
    # the reuse path succeeds.
    _, base_stub = _make_run_stub(
        abbrev_ref="gemini/existing-worktree",
        status_porcelain="",
        rev_list_count="0",
    )

    def fake_run(cmd, **kwargs):
        if cmd[:3] == ["git", "worktree", "add"]:
            pytest.fail("git worktree add should not run for an existing path")
        return base_stub(cmd, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *a, **k: _FakeProc())

    args = argparse.Namespace(
        agent="gemini",
        task_id="existing-worktree",
        prompt="test",
        prompt_file=None,
        mode="workspace-write",
        model=None,
        cwd=None,
        worktree=str(worktree),
        base="main",
        hard_timeout=3600,
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    state = delegate._read_state(delegate._state_path("existing-worktree"))
    assert state["worktree_path"] == str(worktree.resolve())
    assert state["cwd"] == str(worktree.resolve())
    assert state["worktree_reused"] is True


def test_branch_reuse_creates_worktree_from_existing_remote_branch(tmp_tasks_dir, tmp_path, monkeypatch):
    """--branch must attach to its fetched branch, never origin/main (#4837)."""
    target = tmp_path / "branch-reuse"
    branch = "cursor/follow-up"
    calls, base_stub = _make_run_stub(rev_parse_head_sha="branch-head")

    def fake_run(cmd, **kwargs):
        # No local branch yet: creating the worktree must create a tracking
        # branch from the fetched remote ref.
        if cmd[:2] == ["git", "rev-parse"] and cmd[-1] == f"refs/heads/{branch}":
            return subprocess.CompletedProcess(cmd, 1, "", "")
        return base_stub(cmd, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    _, actual_branch, telemetry = delegate._ensure_worktree(
        agent="cursor",
        task_id="follow-up",
        raw_path=str(target),
        branch=branch,
    )

    assert actual_branch == branch
    assert telemetry["reused"] is False
    assert ["git", "fetch", "origin", branch] in calls
    add_cmd = next(command for command in calls if command[:3] == ["git", "worktree", "add"])
    assert add_cmd == [
        "git",
        "worktree",
        "add",
        "--track",
        "-b",
        branch,
        str(target.resolve()),
        f"origin/{branch}",
    ]


def test_branch_reuse_dry_run_validates_existing_worktree_without_adding(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
    capsys,
):
    """A branch-reuse dry run performs the safe reuse checks without mutation."""
    import argparse

    worktree = tmp_path / "existing-branch-worktree"
    worktree.mkdir()
    branch = "cursor/follow-up"
    calls, base_stub = _make_run_stub(
        abbrev_ref=branch,
        status_porcelain="",
        rev_list_count="0",
        rev_parse_head_sha="branch-head",
    )

    def fake_run(cmd, **kwargs):
        if cmd[:3] == ["git", "worktree", "add"]:
            pytest.fail("branch-reuse dry-run must not add a worktree")
        return base_stub(cmd, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)
    args = argparse.Namespace(
        agent="cursor",
        task_id="branch-reuse-dry-run",
        prompt="validate only",
        prompt_file=None,
        mode="read-only",
        model=None,
        cwd=None,
        worktree=str(worktree),
        branch=branch,
        base="main",
        hard_timeout=3600,
        dry_run=True,
    )

    assert delegate.cmd_dispatch(args) == 0
    assert ["git", "fetch", "origin", branch] in calls
    output = capsys.readouterr()
    assert "branch reuse validated" in output.err
    assert "[reused]" in output.err
    assert output.out.strip() == "branch-reuse-dry-run"


def test_branch_reuse_refuses_protected_branch_before_git_calls(tmp_path, monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="protected"):
        delegate._ensure_worktree(
            agent="cursor",
            task_id="unsafe",
            raw_path=str(tmp_path / "unsafe"),
            branch="main",
        )
    assert calls == []


def test_branch_reuse_refuses_branch_checked_out_in_another_worktree(tmp_path, monkeypatch):
    target = tmp_path / "target"
    occupied = tmp_path / "occupied"
    branch = "cursor/follow-up"
    _, base_stub = _make_run_stub()

    def fake_run(cmd, **kwargs):
        if cmd[:3] == ["git", "worktree", "list"]:
            return subprocess.CompletedProcess(
                cmd,
                0,
                f"worktree {occupied}\nbranch refs/heads/{branch}\n\n",
                "",
            )
        return base_stub(cmd, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    with pytest.raises(delegate.WorktreeBranchMismatch, match="already checked out"):
        delegate._ensure_worktree(
            agent="cursor",
            task_id="follow-up",
            raw_path=str(target),
            branch=branch,
        )


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------

def test_list_filters_by_status(tmp_tasks_dir, capsys):
    delegate._write_state_atomic(delegate._state_path("t1"), {
        "task_id": "t1", "agent": "codex", "status": "done",
    })
    delegate._write_state_atomic(delegate._state_path("t2"), {
        "task_id": "t2", "agent": "gemini", "status": "failed",
    })
    delegate._write_state_atomic(delegate._state_path("t3"), {
        "task_id": "t3", "agent": "codex", "status": "done",
    })

    import argparse
    args = argparse.Namespace(status="done")
    rc = delegate.cmd_list(args)
    assert rc == 0

    captured = capsys.readouterr()
    tasks = json.loads(captured.out)
    assert len(tasks) == 2
    assert {t["task_id"] for t in tasks} == {"t1", "t3"}


def test_list_flips_dead_running_to_crashed(tmp_tasks_dir, capsys):
    delegate._write_state_atomic(delegate._state_path("dead"), {
        "task_id": "dead", "agent": "codex",
        "status": "running", "pid": 999_999_998,
    })
    import argparse
    args = argparse.Namespace(status=None)
    delegate.cmd_list(args)
    captured = capsys.readouterr()
    tasks = json.loads(captured.out)
    assert len(tasks) == 1
    assert tasks[0]["status"] == "crashed"


# ---------------------------------------------------------------------------
# #1476 — Fix 1: fetch-before-branch (stale-base footgun)
# ---------------------------------------------------------------------------

def test_ensure_worktree_branches_from_origin_main(tmp_tasks_dir, tmp_path, monkeypatch):
    """Fix 1 (#1476): _ensure_worktree must fetch origin and branch from
    origin/main, not local main. This is the regression that caused #1473
    and #1474 to ship against stale tips.
    """
    target = tmp_path / "fresh-worktree"

    calls, fake_run = _make_run_stub(rev_parse_head_sha="sha-from-origin")
    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    path, branch, telemetry = delegate._ensure_worktree(
        agent="codex",
        task_id="1476-branches-from-origin",
        raw_path=str(target),
        base="main",
    )

    assert path == target.resolve()
    assert branch == "codex/1476-branches-from-origin"
    # Fetch is called before the add.
    fetch_calls = [c for c in calls if c[:2] == ["git", "fetch"]]
    add_calls = [c for c in calls if c[:3] == ["git", "worktree", "add"]]
    assert fetch_calls, "must fetch origin/main before branching"
    assert fetch_calls[0] == ["git", "fetch", "origin", "main"]
    assert add_calls, "must invoke git worktree add"
    assert add_calls[0][-1] == "origin/main", (
        "must branch from origin/main, not local main"
    )
    assert telemetry["base_sha"] == "sha-from-origin"
    assert telemetry["reused"] is False


def test_ensure_worktree_falls_back_when_fetch_fails(tmp_tasks_dir, tmp_path, monkeypatch, capsys):
    """Fix 1 (#1476): offline/no-remote scenarios fall back to local
    base rather than hard-failing. A warning is logged on stderr.
    """
    target = tmp_path / "offline-worktree"

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"]:
            return subprocess.CompletedProcess(cmd, 1, "", "fatal: unable to access")
        if cmd[:2] == ["git", "rev-parse"] and "--verify" in cmd:
            return subprocess.CompletedProcess(cmd, 1, "", "")
        if cmd[:3] == ["git", "worktree", "add"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:2] == ["git", "rev-parse"]:
            return subprocess.CompletedProcess(cmd, 0, "localsha", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    _, branch, _ = delegate._ensure_worktree(
        agent="codex",
        task_id="1476-offline",
        raw_path=str(target),
        base="main",
    )
    assert branch == "codex/1476-offline"
    captured = capsys.readouterr()
    assert (
        ("fetch" in captured.err and "fallback" in captured.err.lower())
        or "stale" in captured.err.lower()
    )


# ---------------------------------------------------------------------------
# #1476 — Fix 2: branch-name normalization
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "agent, task_id, expected_branch",
    [
        # The doubled-prefix bug from #1472: task_id starts with the agent name.
        ("codex", "codex-1472-postmortem-must-change", "codex/1472-postmortem-must-change"),
        # Slash-separator variant.
        ("codex", "codex/1472-slash-variant", "codex/1472-slash-variant"),
        # Already-clean task_id: no change expected.
        ("codex", "1472-no-prefix", "codex/1472-no-prefix"),
        # Non-codex agents.
        ("claude", "claude-foo", "claude/foo"),
        ("gemini", "gemini-bar", "gemini/bar"),
        # Agent name is a substring, not a prefix — must NOT strip.
        ("codex", "random-name", "codex/random-name"),
        ("codex", "codexy-is-not-a-prefix", "codex/codexy-is-not-a-prefix"),
    ],
)
def test_derive_branch_strips_agent_prefix(agent, task_id, expected_branch):
    """Fix 2 (#1476): derived branch must never contain a doubled prefix
    like `codex/codex-…`."""
    assert delegate._derive_worktree_branch(agent, task_id) == expected_branch


def test_derive_branch_never_doubles_prefix_across_agents():
    """Fix 2 (#1476): for any agent × any reasonable task_id, the derived
    branch must not start with `{agent}/{agent}-` or `{agent}/{agent}/`."""
    for agent in ("codex", "claude", "gemini"):
        for task_id in (
            f"{agent}-123-foo",
            f"{agent}/456-bar",
            "789-no-prefix",
            f"prefix-{agent}-mid",
        ):
            branch = delegate._derive_worktree_branch(agent, task_id)
            assert not branch.startswith(f"{agent}/{agent}-"), (
                f"doubled prefix for agent={agent} task={task_id}: {branch}"
            )
            assert not branch.startswith(f"{agent}/{agent}/"), (
                f"doubled prefix for agent={agent} task={task_id}: {branch}"
            )


# ---------------------------------------------------------------------------
# #1476 — Fix 3: worktree-reuse validation
# ---------------------------------------------------------------------------

def test_ensure_worktree_reuse_dirty_raises(tmp_tasks_dir, tmp_path, monkeypatch):
    """Fix 3 (#1476): a dirty existing worktree must raise WorktreeDirty
    rather than being silently reused. Silent reuse is how #1473 shipped
    a stub alignment_manifest.py to a PR."""
    wt = tmp_path / "dirty-worktree"
    wt.mkdir()

    _, fake_run = _make_run_stub(
        abbrev_ref="codex/1476-dirty-task",
        status_porcelain=" M scripts/foo.py\n?? scripts/bar.py\n",
    )
    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    with pytest.raises(delegate.WorktreeDirty, match="uncommitted"):
        delegate._ensure_worktree(
            agent="codex",
            task_id="1476-dirty-task",
            raw_path=str(wt),
            base="main",
        )


def test_ensure_worktree_reuse_wrong_branch_raises(tmp_tasks_dir, tmp_path, monkeypatch):
    """Fix 3 (#1476): an existing worktree on a different branch must
    raise WorktreeBranchMismatch, with the expected remediation command
    in the message."""
    wt = tmp_path / "mismatched-worktree"
    wt.mkdir()

    _, fake_run = _make_run_stub(abbrev_ref="codex/some-other-branch")
    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    with pytest.raises(delegate.WorktreeBranchMismatch) as exc_info:
        delegate._ensure_worktree(
            agent="codex",
            task_id="1476-mismatched",
            raw_path=str(wt),
            base="main",
        )
    assert "codex/some-other-branch" in str(exc_info.value)
    assert "codex/1476-mismatched" in str(exc_info.value)
    assert "git worktree remove" in str(exc_info.value)


def test_ensure_worktree_reuse_stale_base_rebases(tmp_tasks_dir, tmp_path, monkeypatch, capsys):
    """Fix 3 (#1476): a clean worktree behind origin/main is automatically
    rebased. The reuse path succeeds and telemetry records ``rebased=True``."""
    wt = tmp_path / "stale-worktree"
    wt.mkdir()

    _, fake_run = _make_run_stub(
        abbrev_ref="codex/1476-stale-task",
        status_porcelain="",
        rev_list_count="3",
        rev_parse_head_sha="rebased-head-sha",
        rebase_ok=True,
    )
    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    path, branch, telemetry = delegate._ensure_worktree(
        agent="codex",
        task_id="1476-stale-task",
        raw_path=str(wt),
        base="main",
    )
    assert path == wt.resolve()
    assert branch == "codex/1476-stale-task"
    assert telemetry["rebased"] is True
    assert telemetry["reused"] is True
    assert telemetry["base_sha"] == "rebased-head-sha"
    captured = capsys.readouterr()
    assert "behind origin/main" in captured.err


def test_ensure_worktree_reuse_stale_base_rebase_fail_raises(tmp_tasks_dir, tmp_path, monkeypatch):
    """Fix 3 (#1476): if the fast-forward rebase fails (e.g. conflicts),
    _ensure_worktree must raise WorktreeStaleBase, aborting the rebase
    so the worktree is left in a usable state."""
    wt = tmp_path / "stale-conflict-worktree"
    wt.mkdir()

    abort_calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:3] == ["git", "rev-parse", "--verify"]:
            return subprocess.CompletedProcess(cmd, 0, "originsha", "")
        if cmd[:3] == ["git", "rev-parse", "--abbrev-ref"]:
            return subprocess.CompletedProcess(cmd, 0, "codex/1476-conflict-task", "")
        if cmd[:2] == ["git", "status"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:2] == ["git", "rev-list"]:
            return subprocess.CompletedProcess(cmd, 0, "5", "")
        if cmd[:2] == ["git", "rebase"]:
            if cmd[-1] == "--abort":
                abort_calls.append(list(cmd))
                return subprocess.CompletedProcess(cmd, 0, "", "")
            return subprocess.CompletedProcess(cmd, 1, "", "CONFLICT")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    with pytest.raises(delegate.WorktreeStaleBase, match="rebase failed"):
        delegate._ensure_worktree(
            agent="codex",
            task_id="1476-conflict-task",
            raw_path=str(wt),
            base="main",
        )
    # Must abort so the worktree isn't left mid-rebase.
    assert any(c[:2] == ["git", "rebase"] and "--abort" in c for c in abort_calls), (
        "rebase must be aborted on failure"
    )


# ---------------------------------------------------------------------------
# #1476 — Fix 4: dispatch/ subtree layout
# ---------------------------------------------------------------------------

def test_auto_worktree_path_is_dispatch_subtree():
    """Fix 4 (#1476): the auto-derived default worktree path is under
    .worktrees/dispatch/{agent}/{task_normalized}/."""
    path = delegate._auto_worktree_path("codex", "codex-1476-delegate-hardening")
    parts = path.parts[-4:]
    assert parts == (".worktrees", "dispatch", "codex", "1476-delegate-hardening")


def test_classify_worktree_layout_distinguishes_flat_and_dispatch(tmp_path):
    """Fix 4 (#1476): layout classifier tells flat from dispatch paths,
    so list/status can emit deprecation messages."""
    repo = delegate._REPO_ROOT
    assert delegate._classify_worktree_layout(
        repo / ".worktrees" / "codex-1453-sidecar-freshness",
    ) == "flat"
    assert delegate._classify_worktree_layout(
        repo / ".worktrees" / "dispatch" / "codex" / "1476",
    ) == "dispatch"
    assert delegate._classify_worktree_layout(None) is None
    assert delegate._classify_worktree_layout(tmp_path / "anywhere-else") in (
        "external", None,
    )


def test_new_dispatch_uses_dispatch_subtree(tmp_tasks_dir, monkeypatch, capsys):
    """Fix 4 (#1476): a fresh dispatch with `--worktree` (bare — no path)
    lands in `.worktrees/dispatch/{agent}/{task}/`, the new default."""
    import argparse

    class _FakeStdin:
        def write(self, _data): pass
        def close(self): pass

    class _FakeProc:
        pid = 54321
        stdin = _FakeStdin()

    _, fake_run = _make_run_stub()
    monkeypatch.setattr(delegate.subprocess, "run", fake_run)
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *a, **k: _FakeProc())

    args = argparse.Namespace(
        agent="codex",
        task_id="codex-1476-auto-path",
        prompt="test",
        prompt_file=None,
        mode="danger",
        model=None,
        cwd=None,
        worktree="auto",  # sentinel from bare `--worktree`
        base="main",
        hard_timeout=3600,
        allow_merge=False,
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    state = delegate._read_state(delegate._state_path("codex-1476-auto-path"))
    assert state is not None
    wt = Path(state["worktree_path"])
    assert wt.parts[-4:] == (".worktrees", "dispatch", "codex", "1476-auto-path")
    assert state["worktree_branch"] == "codex/1476-auto-path"
    assert state["worktree_layout"] == "dispatch"


# ---------------------------------------------------------------------------
# Write-capable-mode worktree guard (#4445)
#
# workspace-write / danger must resolve to a *verified added worktree*, never
# the primary checkout — enforcement lives in delegate, not a model's memory.
# read-only repo-root preflight and worktree creation from the primary checkout
# stay allowed.
# ---------------------------------------------------------------------------


def _init_repo_with_worktree(tmp_path: Path) -> tuple[Path, Path]:
    """Build a real primary checkout + one registered dispatch worktree.

    Returns ``(main, dispatch_wt)`` as resolved absolute paths. Uses git
    plumbing rather than fake ``.git`` files because the containment predicate
    the guard relies on asks git (``worktree list``/``rev-parse``), not string
    prefixes. The dispatch worktree sits on branch ``codex/task-1``.
    """
    env = delegate._sanitized_git_env()

    def _git(cwd: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(cwd), *args],
            check=True, capture_output=True, text=True, env=env,
        )

    main = tmp_path / "main"
    main.mkdir()
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(main)],
        check=True, capture_output=True, text=True, env=env,
    )
    _git(main, "config", "user.email", "test@example.com")
    _git(main, "config", "user.name", "Test")
    (main / ".gitignore").write_text(".worktrees/\nlocal_state/\n")
    (main / "tracked.txt").write_text("x\n")
    _git(main, "add", "-A")
    _git(main, "commit", "-q", "-m", "init")

    dispatch_wt = main / ".worktrees" / "dispatch" / "codex" / "task-1"
    _git(main, "worktree", "add", "-q", "-b", "codex/task-1", str(dispatch_wt))

    return main.resolve(), dispatch_wt.resolve()


class _GuardFakeStdin:
    def write(self, _data):
        pass

    def close(self):
        pass


class _GuardFakeProc:
    pid = 44551
    stdin = _GuardFakeStdin()


def _patch_worker_popen(monkeypatch):
    """Fake the worker spawn while letting real ``git`` still run.

    ``delegate.subprocess`` and ``worktree_containment.subprocess`` are the same
    module object, so a blanket ``Popen`` patch would also break the containment
    guard's git plumbing (``subprocess.run`` uses ``Popen`` internally). Route
    ``git`` invocations to the real Popen and fake only the ``.venv`` worker.
    """
    real_popen = delegate.subprocess.Popen

    def fake_popen(cmd, *a, **k):
        if cmd and str(cmd[0]) == "git":
            return real_popen(cmd, *a, **k)
        return _GuardFakeProc()

    monkeypatch.setattr(delegate.subprocess, "Popen", fake_popen)


def _write_args(**overrides):
    """Namespace for a cmd_dispatch call, defaulting to a write-capable mode."""
    import argparse

    base = {
        "agent": "codex",
        "task_id": "wt-guard",
        "prompt": "do it",
        "prompt_file": None,
        "mode": "workspace-write",
        "model": None,
        "cwd": None,
        "worktree": None,
        "base": "main",
        "hard_timeout": 3600,
        "allow_merge": False,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


# --- _resolve_write_cwd_error unit tests (deterministic policy) -------------


def test_write_guard_allows_read_only_repo_root():
    assert delegate._resolve_write_cwd_error(
        mode="read-only", worktree_arg=None, cwd_arg=None,
    ) is None


def test_write_guard_allows_bare_worktree_for_both_write_modes():
    for mode in ("workspace-write", "danger"):
        assert delegate._resolve_write_cwd_error(
            mode=mode, worktree_arg="auto", cwd_arg=None,
        ) is None


def test_write_guard_rejects_write_mode_without_isolation():
    for mode in ("workspace-write", "danger"):
        err = delegate._resolve_write_cwd_error(
            mode=mode, worktree_arg=None, cwd_arg=None,
        )
        assert err is not None
        assert "worktree" in err


def test_write_guard_rejects_cwd_primary_checkout(tmp_path):
    main, _ = _init_repo_with_worktree(tmp_path)
    err = delegate._resolve_write_cwd_error(
        mode="workspace-write", worktree_arg=None, cwd_arg=str(main),
    )
    assert err is not None
    assert "primary checkout" in err


def test_write_guard_rejects_cwd_in_repo_outside_worktrees(tmp_path):
    main, _ = _init_repo_with_worktree(tmp_path)
    subdir = main / "pkg"
    subdir.mkdir()
    err = delegate._resolve_write_cwd_error(
        mode="danger", worktree_arg=None, cwd_arg=str(subdir),
    )
    assert err is not None
    assert "primary checkout" in err


def test_write_guard_accepts_cwd_added_worktree(tmp_path):
    _, dispatch_wt = _init_repo_with_worktree(tmp_path)
    assert delegate._resolve_write_cwd_error(
        mode="workspace-write", worktree_arg=None, cwd_arg=str(dispatch_wt),
    ) is None
    # A subdirectory inside the verified worktree is equally fine.
    sub = dispatch_wt / "nested"
    sub.mkdir()
    assert delegate._resolve_write_cwd_error(
        mode="danger", worktree_arg=None, cwd_arg=str(sub),
    ) is None


def test_write_guard_rejects_cwd_unregistered_worktree_dir(tmp_path):
    """A directory that only *looks* like .worktrees/** but was never
    `git worktree add`-ed is not a verified worktree."""
    main, _ = _init_repo_with_worktree(tmp_path)
    ghost = main / ".worktrees" / "dispatch" / "codex" / "ghost"
    ghost.mkdir(parents=True)
    err = delegate._resolve_write_cwd_error(
        mode="workspace-write", worktree_arg=None, cwd_arg=str(ghost),
    )
    assert err is not None
    assert "verified git worktree" in err


def test_write_guard_rejects_explicit_worktree_pointing_at_primary(tmp_path):
    main, _ = _init_repo_with_worktree(tmp_path)
    err = delegate._resolve_write_cwd_error(
        mode="danger", worktree_arg=str(main), cwd_arg=None,
    )
    assert err is not None
    assert "primary checkout" in err


def _primary_dirty_status(main: Path) -> dict:
    return delegate._load_worktree_containment().primary_checkout_dirty_status(main)


def test_primary_dirty_status_clean_main(tmp_path):
    main, _ = _init_repo_with_worktree(tmp_path)

    status = _primary_dirty_status(main)

    assert status["dirty"] is False
    assert status["dirty_count"] == 0


def test_primary_dirty_status_tracks_modified_file(tmp_path):
    main, _ = _init_repo_with_worktree(tmp_path)
    (main / "tracked.txt").write_text("dirty\n")

    status = _primary_dirty_status(main)

    assert status["dirty"] is True
    assert status["tracked_dirty_count"] == 1
    assert status["entries"] == [{"xy": " M", "path": "tracked.txt", "kind": "tracked"}]


def test_primary_dirty_status_tracks_untracked_nonignored_file(tmp_path):
    main, _ = _init_repo_with_worktree(tmp_path)
    (main / "scratch.txt").write_text("new\n")

    status = _primary_dirty_status(main)

    assert status["dirty"] is True
    assert status["untracked_dirty_count"] == 1
    assert status["entries"] == [{"xy": "??", "path": "scratch.txt", "kind": "untracked"}]


def test_primary_dirty_status_ignores_gitignored_local_state(tmp_path):
    main, _ = _init_repo_with_worktree(tmp_path)
    local_state = main / "local_state" / "cache.json"
    local_state.parent.mkdir()
    local_state.write_text("{}\n")

    status = _primary_dirty_status(main)

    assert status["dirty"] is False
    assert status["dirty_count"] == 0


# --- cmd_dispatch end-to-end tests ------------------------------------------


def test_dispatch_read_only_allows_repo_root(tmp_tasks_dir, monkeypatch):
    """Read-only preflight from the primary checkout stays allowed."""
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *a, **k: _GuardFakeProc())
    args = _write_args(task_id="ro-root", mode="read-only", cwd=None, worktree=None)

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    state = delegate._read_state(delegate._state_path("ro-root"))
    assert state is not None
    assert state["cwd"] == str(delegate._REPO_ROOT)


def test_dispatch_read_only_allows_dirty_primary_checkout(
    tmp_tasks_dir, tmp_path, monkeypatch,
):
    """Read-only preflight still runs so agents can inspect and report dirt."""
    main, _ = _init_repo_with_worktree(tmp_path)
    (main / "tracked.txt").write_text("dirty\n")
    monkeypatch.setattr(delegate, "_REPO_ROOT", main)
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *a, **k: _GuardFakeProc())
    args = _write_args(task_id="ro-dirty-main", mode="read-only", cwd=None, worktree=None)

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    state = delegate._read_state(delegate._state_path("ro-dirty-main"))
    assert state is not None
    assert state["cwd"] == str(main)


def test_dispatch_rejects_write_capable_when_primary_checkout_dirty(
    tmp_tasks_dir, tmp_path, monkeypatch, capsys,
):
    main, _ = _init_repo_with_worktree(tmp_path)
    (main / "tracked.txt").write_text("dirty\n")
    monkeypatch.setattr(delegate, "_REPO_ROOT", main)
    args = _write_args(
        task_id="dirty-main",
        mode="workspace-write",
        cwd=None,
        worktree="auto",
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 2
    assert delegate._read_state(delegate._state_path("dirty-main")) is None
    err = capsys.readouterr().err
    assert "primary checkout is dirty" in err
    assert "git status --porcelain=v1 -z --untracked-files=all" in err
    assert "tracked.txt" in err
    assert not (main / ".worktrees" / "dispatch" / "codex" / "dirty-main").exists()
    branch_proc = subprocess.run(
        ["git", "-C", str(main), "branch", "--list", "codex/dirty-main"],
        check=True,
        capture_output=True,
        text=True,
        env=delegate._sanitized_git_env(),
    )
    assert branch_proc.stdout.strip() == ""


def test_dispatch_rejects_workspace_write_without_worktree(tmp_tasks_dir, capsys):
    args = _write_args(task_id="ww-no-wt", mode="workspace-write", cwd=None, worktree=None)

    rc = delegate.cmd_dispatch(args)

    assert rc == 2
    assert delegate._read_state(delegate._state_path("ww-no-wt")) is None
    assert "worktree" in capsys.readouterr().err


def test_dispatch_rejects_workspace_write_cwd_primary_checkout(
    tmp_tasks_dir, tmp_path, capsys,
):
    main, _ = _init_repo_with_worktree(tmp_path)
    args = _write_args(
        task_id="ww-cwd-main", mode="workspace-write", cwd=str(main), worktree=None,
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 2
    assert delegate._read_state(delegate._state_path("ww-cwd-main")) is None
    assert "primary checkout" in capsys.readouterr().err


def test_dispatch_accepts_workspace_write_cwd_added_worktree(
    tmp_tasks_dir, tmp_path, monkeypatch,
):
    main, dispatch_wt = _init_repo_with_worktree(tmp_path)
    monkeypatch.setattr(delegate, "_REPO_ROOT", main)
    _patch_worker_popen(monkeypatch)
    args = _write_args(
        task_id="ww-cwd-wt", mode="workspace-write", cwd=str(dispatch_wt), worktree=None,
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    state = delegate._read_state(delegate._state_path("ww-cwd-wt"))
    assert state is not None
    assert Path(state["cwd"]) == dispatch_wt


def test_dispatch_accepts_bare_worktree_for_workspace_write(
    tmp_tasks_dir, monkeypatch,
):
    _, fake_run = _make_run_stub()
    monkeypatch.setattr(delegate.subprocess, "run", fake_run)
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *a, **k: _GuardFakeProc())
    args = _write_args(
        task_id="ww-bare", mode="workspace-write", cwd=None, worktree="auto",
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    state = delegate._read_state(delegate._state_path("ww-bare"))
    assert state is not None
    wt = Path(state["worktree_path"])
    assert wt.parts[-4:] == (".worktrees", "dispatch", "codex", "ww-bare")


def test_dispatch_accepts_explicit_added_worktree(tmp_tasks_dir, tmp_path, monkeypatch):
    """An explicit --worktree pointing at a real registered dispatch worktree
    is reused, not rejected."""
    main, dispatch_wt = _init_repo_with_worktree(tmp_path)
    # _ensure_worktree's reuse validation shells out to git without sanitizing
    # the environment, so under a git hook (pre-commit/pre-push) an inherited
    # GIT_DIR/GIT_WORK_TREE would hijack `cwd=<worktree>` and report the outer
    # repo's branch. Strip those so the throwaway worktree resolves correctly.
    _sanitize_git_env_for_test(monkeypatch)
    # Route delegate's worktree machinery at the throwaway repo so reuse
    # validation and provisioning never touch the real checkout or network.
    monkeypatch.setattr(delegate, "_REPO_ROOT", main)
    _patch_worker_popen(monkeypatch)
    args = _write_args(
        agent="codex",
        task_id="task-1",
        mode="workspace-write",
        cwd=None,
        worktree=str(dispatch_wt),
        base="main",
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    state = delegate._read_state(delegate._state_path("task-1"))
    assert state is not None
    assert state["worktree_reused"] is True
    assert Path(state["cwd"]) == dispatch_wt


def test_dispatch_help_omits_deprecated_cwd_dot_example():
    """Issue #4445: help/examples must not advertise `--cwd .` or a flat
    worktree layout for write-capable work."""
    parser = delegate.build_parser()
    root_help = parser.format_help()
    dispatch_parser = next(
        action.choices["dispatch"]
        for action in parser._actions
        if action.dest == "command"
    )
    help_text = dispatch_parser.format_help()
    assert "--cwd ." not in root_help
    assert "--mode workspace-write --cwd" not in root_help
    # The flat `.worktrees/<agent>-<task>` example is gone; bare --worktree
    # is the advertised write-capable path.
    assert ".worktrees/codex-pr-123" not in root_help
    assert "--mode workspace-write --worktree" in root_help
    assert "--branch EXISTING" in help_text
    assert "protected branches" in help_text
    assert "main/master" in help_text
    assert "checked out" in help_text
    assert "another" in help_text


def test_list_and_status_walk_both_layouts(tmp_tasks_dir, tmp_path, capsys, monkeypatch):
    """Fix 4 (#1476): both the deprecated flat layout and the new dispatch
    subtree layout must surface in `list`, and flat-layout tasks emit
    a deprecation notice."""
    repo = delegate._REPO_ROOT
    flat_path = repo / ".worktrees" / "codex-1453-sidecar-freshness"
    dispatch_path = repo / ".worktrees" / "dispatch" / "codex" / "1476-new"

    delegate._write_state_atomic(delegate._state_path("flat-task"), {
        "task_id": "flat-task",
        "agent": "codex",
        "status": "done",
        "worktree_path": str(flat_path),
    })
    delegate._write_state_atomic(delegate._state_path("new-task"), {
        "task_id": "new-task",
        "agent": "codex",
        "status": "done",
        "worktree_path": str(dispatch_path),
    })

    import argparse
    args = argparse.Namespace(status=None)
    delegate.cmd_list(args)
    captured = capsys.readouterr()
    tasks = json.loads(captured.out)
    task_map = {t["task_id"]: t for t in tasks}
    assert "flat-task" in task_map
    assert "new-task" in task_map
    assert task_map["flat-task"]["worktree_layout"] == "flat"
    assert task_map["new-task"]["worktree_layout"] == "dispatch"
    # Deprecation notice surfaces on stderr for the flat-layout task.
    assert "DEPRECATED" in captured.err or "deprecated" in captured.err.lower()
    assert "flat-task" in captured.err


def test_status_warns_on_flat_layout(tmp_tasks_dir, capsys):
    """Fix 4 (#1476): `status` for a flat-layout task must print a
    deprecation notice in addition to the JSON state."""
    repo = delegate._REPO_ROOT
    flat_path = repo / ".worktrees" / "codex-old-thing"
    delegate._write_state_atomic(delegate._state_path("flat-status"), {
        "task_id": "flat-status",
        "agent": "codex",
        "status": "done",
        "worktree_path": str(flat_path),
    })

    import argparse
    args = argparse.Namespace(task_id="flat-status")
    delegate.cmd_status(args)
    captured = capsys.readouterr()
    state = json.loads(captured.out)
    assert state["worktree_layout"] == "flat"
    assert "flat" in captured.err.lower() or "deprecated" in captured.err.lower()
