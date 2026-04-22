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
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate


@pytest.fixture
def tmp_tasks_dir(tmp_path, monkeypatch):
    """Redirect delegate._TASKS_DIR to a tmp path so tests don't pollute
    the real batch_state/tasks/ directory."""
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate, "_TASKS_DIR", tasks_dir)
    return tasks_dir


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
    ) == "cancelled"


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
    captured = capsys.readouterr()
    assert "failed to spawn" in captured.err


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


def test_dispatch_creates_worktree_and_records_it(tmp_tasks_dir, monkeypatch, capsys):
    import argparse

    recorded_prompt: dict[str, str] = {}

    class _FakeStdin:
        def write(self, data):
            recorded_prompt["text"] = data.decode("utf-8")

        def close(self):
            pass

    class _FakeProc:
        pid = 24680
        stdin = _FakeStdin()

    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        assert cmd[:5] == ["git", "worktree", "add", "-b", "codex/issue-1383-smoke"]
        return subprocess.CompletedProcess(cmd, 0, "", "")

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
        worktree=".worktrees/codex-1383",
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
    assert "delegate worktree" in recorded_prompt["text"]
    assert ".worktrees/codex-1383" in recorded_prompt["text"]
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert "issue-1383-smoke" in captured.out


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

    monkeypatch.setattr(
        delegate.subprocess,
        "run",
        lambda *a, **k: pytest.fail("git worktree add should not run for an existing path"),
    )
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
        hard_timeout=3600,
    )

    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    state = delegate._read_state(delegate._state_path("existing-worktree"))
    assert state["worktree_path"] == str(worktree.resolve())
    assert state["cwd"] == str(worktree.resolve())


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
