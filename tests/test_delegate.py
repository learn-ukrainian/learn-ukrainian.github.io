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
        worktree=".worktrees/codex-1383",
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
