"""delegate.py dispatch host admission, prompt liveness and peak RSS (#8645 part A).

Task records live under tmp_path. Memory and load come from a monkeypatched
probe; no test allocates memory, generates load, or spawns a worker.
"""

from __future__ import annotations

import json
import resource
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate

from scripts.fleet import capacity_pick
from scripts.orchestration import dispatch_admission, job_host_exec

_GIB = 1024**3


@pytest.fixture
def tasks_dir(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    monkeypatch.setattr(delegate, "_TASKS_DIR", tasks)
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch"))
    for name in (
        "_resolve_dirty_primary_checkout_error",
        "_resolve_primary_integrity_error",
    ):
        monkeypatch.setattr(delegate, name, lambda **_kwargs: None)
    for name in (
        "_warn_node_modules_integrity",
        "_warn_venv_integrity",
        "_warn_worktree_cleanup_integrity",
        "_warn_if_monitor_api_unreachable",
    ):
        monkeypatch.setattr(delegate, name, lambda: None)
    monkeypatch.setattr(
        delegate,
        "_sweep_runtime_tmp_orphans",
        lambda: {"leases_reaped": 0, "bytes_freed": 0, "errors": 0, "error_details": []},
    )
    monkeypatch.setattr(job_host_exec, "decide_dispatch_placement", lambda **_kwargs: ("local", "test", None))
    return tasks


def _running_record(tasks: Path, task_id: str, *, pid: int, mode: str = "workspace-write") -> Path:
    tasks.mkdir(parents=True, exist_ok=True)
    path = tasks / f"{task_id}.json"
    path.write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": "running",
                "mode": mode,
                "pid": pid,
                "run_nonce": f"nonce-{task_id}",
                "started_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _dry_run_args(*extra: str, mode: str = "workspace-write", task_id: str = "adm-probe"):
    argv = [
        "dispatch",
        "--agent",
        "codex",
        "--task-id",
        task_id,
        "--initiator",
        "codex",
        "--prompt",
        "test",
        "--mode",
        mode,
        "--dry-run",
        *extra,
    ]
    if mode != "read-only":
        argv.append("--worktree")
    return delegate.build_parser().parse_args(argv)


def test_dispatch_refuses_a_write_worker_at_the_cap_with_one_line(tasks_dir, monkeypatch, capsys):
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")

    rc = delegate.cmd_dispatch(_dry_run_args())

    assert rc == delegate._ADMISSION_REFUSED_EXIT == 3
    refusal = [line for line in capsys.readouterr().err.splitlines() if "admission" in line]
    assert refusal == [
        "❌ dispatch admission refused for a workspace-write worker: live write workers 0/0 reached the cap "
        "(DISPATCH_MAX_LIVE_WRITE_WORKERS=0). Wait for a worker to finish or for the host to recover, raise the "
        'threshold through the named environment variable, or pass --force-admission "<reason>" to override.'
    ]
    assert not delegate._state_path("adm-probe").exists()


def test_dispatch_refuses_on_low_memory_and_high_load(tasks_dir, monkeypatch, capsys):
    monkeypatch.setattr(
        dispatch_admission,
        "probe_host",
        lambda: dispatch_admission.HostProbe(
            mem_available_bytes=1 * _GIB, load1=20.0, cpu_count=8, proc_available=True
        ),
    )

    assert delegate.cmd_dispatch(_dry_run_args(mode="danger")) == 3

    err = capsys.readouterr().err
    assert "MemAvailable 1.0 GiB is below the floor of 3.5 GiB" in err
    assert "load 2.50 per CPU" in err


def test_read_only_dispatch_is_exempt(tasks_dir, monkeypatch, capsys):
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")

    rc = delegate.cmd_dispatch(_dry_run_args(mode="read-only", task_id="adm-reader"))

    assert rc == 0
    assert "admission" not in capsys.readouterr().err
    state = delegate._read_state(delegate._state_path("adm-reader"))
    assert state is not None and "admission" not in state


def test_force_admission_records_the_reason(tasks_dir, monkeypatch, capsys):
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")

    rc = delegate.cmd_dispatch(_dry_run_args("--force-admission", "hotfix #1234 while one worker drains"))

    assert rc == 0
    assert "overridden by --force-admission ('hotfix #1234 while one worker drains')" in capsys.readouterr().err
    state = delegate._read_state(delegate._state_path("adm-probe"))
    assert state is not None
    admission = state["admission"]
    assert admission["admitted"] is False
    assert admission["forced"] is True
    assert admission["force_reason"] == "hotfix #1234 while one worker drains"
    assert admission["max_live_write_workers"] == 0


def test_force_admission_requires_a_reason(tasks_dir, capsys):
    assert delegate.cmd_dispatch(_dry_run_args("--force-admission", "   ")) == 2
    assert "--force-admission requires a non-empty reason" in capsys.readouterr().err


def test_admission_sweeps_dead_workers_to_crashed_and_frees_their_slot(tasks_dir, monkeypatch):
    dead = _running_record(tasks_dir, "dead-writer", pid=424242)
    _running_record(tasks_dir, "live-writer", pid=515151)
    monkeypatch.setattr(delegate, "_pid_alive", lambda pid: pid == 515151)
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "2")

    decision = delegate._evaluate_dispatch_admission("workspace-write", sweep=True)

    assert decision.admitted
    assert decision.live_task_ids == ("live-writer",)
    swept = json.loads(dead.read_text(encoding="utf-8"))
    assert swept["status"] == "crashed"
    assert "marked crashed by admission probe" in swept["stderr_excerpt"]


def test_dry_run_reports_dead_workers_without_marking_them(tasks_dir, monkeypatch, capsys):
    dead = _running_record(tasks_dir, "dead-writer", pid=424242)
    monkeypatch.setattr(delegate, "_pid_alive", lambda _pid: False)

    assert delegate.cmd_dispatch(_dry_run_args()) == 0

    assert json.loads(dead.read_text(encoding="utf-8"))["status"] == "running"
    assert "1 record(s) dead pid, not counted: dead-writer" in capsys.readouterr().err


class _FakeStdin:
    def write(self, _data):
        pass

    def close(self):
        pass


def _live_danger_args(tasks: Path, task_id: str):
    import argparse

    (tasks / "wt").mkdir(parents=True, exist_ok=True)
    return argparse.Namespace(
        agent="codex",
        task_id=task_id,
        prompt="test",
        prompt_file=None,
        mode="danger",
        model=None,
        cwd=None,
        worktree=str(tasks / "wt"),
        base="main",
        hard_timeout=3600,
    )


def _stub_worktree(monkeypatch, tasks: Path):
    """A prepared worktree without git: live-dispatch tests stop at the admission lock or at Popen."""
    wt = tasks / "wt"
    monkeypatch.setattr(delegate, "_resolve_write_cwd_error", lambda **_kwargs: None)
    monkeypatch.setattr(
        delegate.subprocess,
        "run",
        lambda cmd, **_kwargs: delegate.subprocess.CompletedProcess(cmd, 0, "", ""),
    )
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", lambda **_kwargs: "abc1234")
    monkeypatch.setattr(
        delegate,
        "_ensure_worktree",
        lambda **_kwargs: (wt, "codex/adm", {"base_sha": "abc1234", "layout": "dispatch"}),
    )
    monkeypatch.setattr(delegate, "_resolve_sha", lambda *_args, **_kwargs: "abc1234")


def test_live_dispatch_records_the_admission_snapshot(tasks_dir, monkeypatch, capsys):
    _stub_worktree(monkeypatch, tasks_dir)
    spawned: list[list[str]] = []

    class _Proc:
        pid = 13579
        stdin = _FakeStdin()

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda cmd, **_kwargs: spawned.append(cmd) or _Proc())

    assert delegate.cmd_dispatch(_live_danger_args(tasks_dir, "adm-live")) == 0

    assert len(spawned) == 1
    assert "🚦 dispatch admission: admitted — live write workers 0/5" in capsys.readouterr().err
    state = delegate._read_state(delegate._state_path("adm-live"))
    assert state is not None
    assert state["admission"]["admitted"] is True
    assert state["admission"]["forced"] is False
    assert state["admission"]["mem_available_gib"] == 64.0
    assert (tasks_dir / dispatch_admission.LOCK_FILE_NAME).is_file()


def test_locked_recheck_refuses_a_dispatch_that_lost_the_race(tasks_dir, monkeypatch, capsys):
    """Two dispatches pass the early check; the locked re-check refuses the one that finds the cap full."""
    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "1")
    monkeypatch.setattr(
        delegate.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("a refused dispatch must not spawn")
    )
    real_evaluate = delegate._evaluate_dispatch_admission
    calls = {"n": 0}

    def evaluate_after_competitor(mode, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:  # the competitor published its record between the two checks
            _running_record(tasks_dir, "competitor", pid=515151, mode="workspace-write")
        return real_evaluate(mode, **kwargs)

    monkeypatch.setattr(delegate, "_evaluate_dispatch_admission", evaluate_after_competitor)
    monkeypatch.setattr(delegate, "_pid_alive", lambda pid: pid == 515151)

    rc = delegate.cmd_dispatch(_live_danger_args(tasks_dir, "adm-race"))

    assert rc == 3
    assert calls["n"] == 2
    assert "live write workers 1/1 reached the cap" in capsys.readouterr().err
    state = delegate._read_state(delegate._state_path("adm-race"))
    assert state is not None
    assert state["status"] == "failed"
    assert state["returncode_reason"] == "dispatch admission refused"
    assert state["worktree_path"] == str(tasks_dir / "wt")
    lease_root = Path(tasks_dir.parent / "scratch" / "learn-ukrainian" / "adm-race")
    assert not lease_root.exists()


def test_terminal_fields_record_peak_rss_of_reaped_children(monkeypatch):
    class _Usage:
        ru_maxrss = 3 * 1024 * 1024 if sys.platform == "darwin" else 3 * 1024  # 3 MiB

    monkeypatch.setattr(resource, "getrusage", lambda _who: _Usage())

    fields = delegate._core_terminal_fields(
        status="done",
        duration_s=1.0,
        response="ok",
        result_file=None,
        stderr_excerpt=None,
        returncode=0,
        returncode_reason=None,
        dirty_on_exit=False,
        commits_ahead=1,
        needs_finalize=False,
        finalize_error=None,
        last_error=None,
    )

    assert fields["peak_rss_mib"] == 3.0


def test_capacity_pick_prints_the_admission_line(tmp_path, monkeypatch, capsys):
    from scripts.fleet import usage

    tasks = tmp_path / "tasks"
    _running_record(tasks, "busy", pid=515151)
    dead = _running_record(tasks, "gone", pid=424242)
    monkeypatch.setattr(dispatch_admission, "process_alive", lambda pid: pid == 515151)
    monkeypatch.setattr(capacity_pick, "_TASKS_DIR", tasks)
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda **_kwargs: {})
    monkeypatch.setattr(
        usage,
        "read_budget",
        lambda **_kwargs: {"agents": {}, "recommendation": {"warnings": []}, "diagnostics": {}},
    )

    assert capacity_pick.main([]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == (
        "admission (write dispatch): would admit now | live write workers 1/5, "
        "MemAvailable 64.0 GiB (floor 3.5 GiB), load 0.00 per CPU (limit 1.50); "
        "1 record(s) dead pid, not counted: gone"
    )

    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "1")
    assert capacity_pick.main(["--json"]) == 0
    admission = json.loads(capsys.readouterr().out)["admission"]
    assert admission["admitted"] is False
    assert admission["line"].startswith("admission (write dispatch): would REFUSE now: live write workers 1/1")
    # capacity_pick only reports; marking dead records crashed is dispatch's job.
    assert json.loads(dead.read_text(encoding="utf-8"))["status"] == "running"
