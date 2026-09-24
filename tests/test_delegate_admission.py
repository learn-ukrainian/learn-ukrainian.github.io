"""delegate.py dispatch host admission, prompt liveness and peak RSS (#8645 part A).

Task records live under tmp_path. Memory and load come from a monkeypatched
probe; no test allocates memory, generates load, or spawns a worker.
"""

from __future__ import annotations

import json
import os
import resource
import subprocess
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
    monkeypatch.setattr(
        delegate, "_ensure_worktree", lambda **_kwargs: pytest.fail("a refused dispatch must not create a worktree")
    )
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
    # Refused before the worktree, the task record and the runtime tmp lease (#8717).
    assert not delegate._state_path("adm-race").exists()
    lease_root = Path(tasks_dir.parent / "scratch" / "learn-ukrainian" / "adm-race")
    assert not lease_root.exists()


# --- #8717: admission runs before the worktree and holds the slot until the spawn ------------


# ``_stub_worktree`` replaces ``subprocess.run`` for delegate; the scratch repo needs the real one.
_REAL_RUN = subprocess.run


def _git(cwd: Path, *args: str) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    proc = _REAL_RUN(["git", *args], cwd=cwd, capture_output=True, text=True, check=True, env=env, timeout=30)
    return proc.stdout.strip()


def _scratch_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "base")
    return repo


def _load_rises_after_the_first_probe(monkeypatch) -> dict[str, int]:
    """The early check sees a quiet host; every later probe sees load over the limit (the impl-8654-r3 incident)."""
    calls = {"n": 0}

    def probe():
        calls["n"] += 1
        load = 1.0 if calls["n"] == 1 else 40.0
        return dispatch_admission.HostProbe(mem_available_bytes=64 * _GIB, load1=load, cpu_count=8, proc_available=True)

    monkeypatch.setattr(dispatch_admission, "probe_host", probe)
    return calls


def test_refused_dispatch_leaves_no_worktree_registration_or_task_record(tasks_dir, tmp_path, monkeypatch, capsys):
    repo = _scratch_repo(tmp_path)
    worktree = tmp_path / "wt-refused"
    _stub_worktree(monkeypatch, tasks_dir)

    def real_worktree_add(**_kwargs):
        _git(repo, "worktree", "add", "-q", "-b", "codex/adm", str(worktree), "HEAD")
        return worktree, "codex/adm", {"base_sha": _git(repo, "rev-parse", "HEAD"), "layout": "dispatch"}

    monkeypatch.setattr(delegate, "_ensure_worktree", real_worktree_add)
    real_popen = subprocess.Popen

    def popen_git_only(cmd, *args, **kwargs):
        if cmd[0] != "git":
            pytest.fail("a refused dispatch must not spawn")
        return real_popen(cmd, *args, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "Popen", popen_git_only)
    probes = _load_rises_after_the_first_probe(monkeypatch)
    args = _live_danger_args(tasks_dir, "adm-refused")
    args.worktree = str(worktree)

    rc = delegate.cmd_dispatch(args)

    assert rc == delegate._ADMISSION_REFUSED_EXIT
    assert probes["n"] == 2
    assert "load 5.00 per CPU" in capsys.readouterr().err
    assert not worktree.exists()
    assert _git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1
    assert not delegate._state_path("adm-refused").exists()
    assert not list(tasks_dir.glob("adm-refused*.json"))


def test_admitted_dispatch_holds_its_slot_while_the_worktree_is_created(tasks_dir, monkeypatch):
    """The hold published under the admission lock counts for other dispatches until the full record replaces it."""
    _stub_worktree(monkeypatch, tasks_dir)
    seen: dict[str, object] = {}

    def ensure_worktree(**kwargs):
        seen["record"] = delegate._read_state(delegate._state_path("adm-held"))
        seen["live"] = dispatch_admission.scan_task_records(tasks_dir).live_task_ids
        return tasks_dir / "wt", "codex/adm", {"base_sha": "abc1234", "layout": "dispatch"}

    monkeypatch.setattr(delegate, "_ensure_worktree", ensure_worktree)

    class _Proc:
        pid = 13579
        stdin = _FakeStdin()

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *_args, **_kwargs: _Proc())

    assert delegate.cmd_dispatch(_live_danger_args(tasks_dir, "adm-held")) == 0

    held = seen["record"]
    assert isinstance(held, dict)
    assert held["status"] == "spawning" and held["pid"] is None and held["mode"] == "danger"
    assert held[dispatch_admission.ADMISSION_HOLD_KEY]["owner_pid"] == os.getpid()
    assert seen["live"] == ("adm-held",)
    final = delegate._read_state(delegate._state_path("adm-held"))
    assert final is not None
    assert dispatch_admission.ADMISSION_HOLD_KEY not in final
    assert final["admission"] == held["admission"]


def test_dispatch_that_stops_after_admission_drops_its_hold(tasks_dir, monkeypatch, capsys):
    _stub_worktree(monkeypatch, tasks_dir)
    vanished = tasks_dir / "wt-vanished"
    monkeypatch.setattr(
        delegate,
        "_ensure_worktree",
        lambda **_kwargs: (vanished, "codex/adm", {"base_sha": "abc1234", "layout": "dispatch"}),
    )
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("must not spawn"))

    assert delegate.cmd_dispatch(_live_danger_args(tasks_dir, "adm-stopped")) == 1

    assert "disappeared before its task record was published" in capsys.readouterr().err
    assert not delegate._state_path("adm-stopped").exists()


def test_worktree_reservation_keeps_the_admission_hold_and_retire_restores_it(tasks_dir):
    admission = {"admitted": True}
    delegate._publish_admission_hold("adm-prep", "nonce-p", mode="workspace-write", admission=admission)
    owner = dispatch_admission.new_admission_hold("nonce-p")
    prep = {
        "path": str(tasks_dir / "wt"),
        "run_nonce": "nonce-p",
        "reserved_at": "2026-09-24T00:00:00+00:00",
        "owner_pid": owner["owner_pid"],
        "owner_start": owner["owner_start"],
    }

    delegate._publish_worktree_prep("adm-prep", "nonce-p", prep)
    reserved = delegate._read_state(delegate._state_path("adm-prep"))
    assert reserved["worktree_prep"] == prep
    assert reserved["mode"] == "workspace-write" and reserved["admission"] == admission
    assert dispatch_admission.scan_task_records(tasks_dir).live_task_ids == ("adm-prep",)

    delegate._retire_worktree_prep("adm-prep", "nonce-p")
    restored = delegate._read_state(delegate._state_path("adm-prep"))
    assert "worktree_prep" not in restored
    assert restored[dispatch_admission.ADMISSION_HOLD_KEY]["owner_pid"] == os.getpid()
    assert dispatch_admission.scan_task_records(tasks_dir).live_task_ids == ("adm-prep",)

    delegate._release_admission_hold("adm-prep", "nonce-p")
    assert not delegate._state_path("adm-prep").exists()


def test_admission_hold_refuses_to_overwrite_another_runs_live_record(tasks_dir):
    _running_record(tasks_dir, "adm-dup", pid=os.getpid())

    with pytest.raises(RuntimeError, match="refusing to overwrite"):
        delegate._publish_admission_hold("adm-dup", "nonce-other", mode="danger", admission={})


@pytest.mark.parametrize(
    ("block", "reason"),
    [
        ("worktree_prep", "dispatch_died_during_worktree_prep"),
        (dispatch_admission.ADMISSION_HOLD_KEY, dispatch_admission.ORPHANED_HOLD_REASON),
    ],
)
def test_admission_marks_a_record_whose_dispatcher_died_crashed(tasks_dir, block, reason):
    """Admission heals orphaned pid-less records with the same healer status/wait/list/reconcile use."""
    from tests.worktree_prep_helpers import exited_process_identity

    pid, start = exited_process_identity()
    tasks_dir.mkdir(parents=True, exist_ok=True)
    path = tasks_dir / "orphan.json"
    path.write_text(
        json.dumps(
            {
                "task_id": "orphan",
                "run_nonce": "nonce-orphan",
                "status": "spawning",
                "pid": None,
                "mode": "workspace-write",
                "started_at": datetime.now(UTC).isoformat(),
                block: {"run_nonce": "nonce-orphan", "owner_pid": pid, "owner_start": start},
            }
        ),
        encoding="utf-8",
    )

    decision = delegate._evaluate_dispatch_admission("workspace-write", sweep=True)

    assert decision.live_task_ids == ()
    assert decision.dead_task_ids == ("orphan",)
    healed = json.loads(path.read_text(encoding="utf-8"))
    assert healed["status"] == "crashed"
    assert healed["returncode_reason"] == reason
    assert "marked crashed by admission probe" in healed["stderr_excerpt"]


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
