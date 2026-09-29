"""Finding and stopping a dispatch worker's leftover processes (#8991)."""

from __future__ import annotations

import os
import signal
from pathlib import Path

from scripts.orchestration import worker_leftovers as wl
from tests.worker_leftovers_fakes import FAKE_PID_BASE, UNKILLABLE, FakeProc, FakeProcs

SCOPE_CGROUP = "/user.slice/lu.slice/lu-dispatch.slice/lu-worker-t1-n-abcd.scope"
UNIT = "lu-worker-t1-n-abcd"
JOB = FAKE_PID_BASE + 1
OTHER = FAKE_PID_BASE + 2


def test_scope_scan_lists_the_cgroup_minus_the_caller_and_zombies() -> None:
    zombie = FAKE_PID_BASE + 3
    fake = FakeProcs(
        procs={JOB: FakeProc(), OTHER: FakeProc(), zombie: FakeProc(state="Z")},
        cgroups={SCOPE_CGROUP: [os.getpid(), JOB, zombie]},
    )
    scope = wl.WorkerScope(task_id="t1", launch_mode="scope", unit=UNIT, cgroup=SCOPE_CGROUP)

    found = wl.find_leftovers(scope, reader=fake)

    assert [proc.pid for proc in found or []] == [JOB]


def test_fallback_scan_matches_only_this_tasks_marker() -> None:
    fake = FakeProcs(procs={JOB: FakeProc(task="t1"), OTHER: FakeProc(task="t2"), OTHER + 1: FakeProc(task=None)})
    scope = wl.WorkerScope(task_id="t1", launch_mode="popen-fallback")

    assert [proc.pid for proc in wl.find_leftovers(scope, reader=fake) or []] == [JOB]


def test_fallback_trusts_the_session_only_while_the_caller_leads_it() -> None:
    fake = FakeProcs(procs={JOB: FakeProc(task=None, sid=os.getpid())})

    led = wl.WorkerScope(task_id="t1", launch_mode="popen-fallback", session_id=os.getpid())
    stale = wl.WorkerScope(task_id="t1", launch_mode="popen-fallback", session_id=os.getpid() + 1)

    assert [proc.pid for proc in wl.find_leftovers(led, reader=fake) or []] == [JOB]
    assert wl.find_leftovers(stale, reader=fake) == []


def test_worker_scope_records_the_cgroup_only_when_it_is_this_launch_unit() -> None:
    fake = FakeProcs(own=SCOPE_CGROUP)

    ours = wl.worker_scope_at_exit(task_id="t1", launch_mode="scope", launch_unit=UNIT, reader=fake)
    other = wl.worker_scope_at_exit(task_id="t1", launch_mode="scope", launch_unit="lu-worker-else", reader=fake)
    fallback = wl.worker_scope_at_exit(task_id="t1", launch_mode="popen-fallback", launch_unit=None, reader=fake)

    assert ours.cgroup == SCOPE_CGROUP
    assert other.cgroup is None
    assert fallback.cgroup is None
    assert wl.WorkerScope.from_state(ours.as_state()) == ours


def test_leftovers_state_names_pids_and_truncated_cmdlines() -> None:
    scope = wl.WorkerScope(task_id="t1", launch_mode="popen-fallback")
    procs = [wl.LeftoverProcess(pid=FAKE_PID_BASE + i, start_ticks=1, cmdline="x" * 500) for i in range(30)]

    state = wl.leftovers_state(scope, procs)

    assert state["reason"] == wl.BACKGROUND_JOBS_REASON
    assert state["count"] == 30
    assert len(state["processes"]) == wl.MAX_RECORDED_PROCESSES
    assert len(state["processes"][0]["cmdline"]) == wl.CMDLINE_MAX_CHARS
    assert state["scope"]["task_id"] == "t1"


def test_stop_sends_sigterm_first_and_leaves_other_processes_alone() -> None:
    fake = FakeProcs(procs={JOB: FakeProc(task="t1"), OTHER: FakeProc(task="t2")})
    scope = wl.WorkerScope(task_id="t1", launch_mode="popen-fallback")

    result = wl.stop_leftovers(scope, reader=fake, kill=fake.kill, sleep=lambda _s: None, clock=fake.clock)

    assert result.ok is True
    assert fake.signals == [(JOB, signal.SIGTERM)]
    assert OTHER in fake.procs


def test_stop_escalates_to_sigkill_and_reports_survivors() -> None:
    fake = FakeProcs(
        procs={
            JOB: FakeProc(task="t1", ignores=frozenset({signal.SIGTERM})),
            OTHER: FakeProc(task="t1", ignores=UNKILLABLE),
        }
    )
    scope = wl.WorkerScope(task_id="t1", launch_mode="popen-fallback")

    result = wl.stop_leftovers(scope, reader=fake, kill=fake.kill, sleep=lambda _s: None, clock=fake.clock)

    assert result.ok is False
    assert (JOB, signal.SIGKILL) in fake.signals
    assert [proc.pid for proc in result.survivors] == [OTHER]
    assert JOB not in fake.procs


def test_stop_never_signals_a_reused_pid() -> None:
    fake = FakeProcs(procs={JOB: FakeProc(task="t1", start=100)})
    scope = wl.WorkerScope(task_id="t1", launch_mode="popen-fallback")
    original_stat = fake.stat

    def stat_then_reuse(pid: int) -> wl.ProcStat | None:
        # The scan sees the job; right after, the job exits and an unrelated
        # process is handed the same pid before the signal goes out.
        info = original_stat(pid)
        if pid == JOB and fake.procs[JOB].task == "t1":
            fake.procs[JOB] = FakeProc(task=None, start=999)
        return info

    fake.stat = stat_then_reuse  # type: ignore[method-assign]
    wl.stop_leftovers(scope, reader=fake, kill=fake.kill, sleep=lambda _s: None, clock=fake.clock)

    assert fake.signals == []


def test_stop_stops_the_scope_unit_when_the_caller_is_outside_it() -> None:
    fake = FakeProcs(procs={JOB: FakeProc()}, cgroups={SCOPE_CGROUP: [JOB]})
    scope = wl.WorkerScope(task_id="t1", launch_mode="scope", unit=UNIT, cgroup=SCOPE_CGROUP)

    result = wl.stop_leftovers(
        scope, reader=fake, kill=fake.kill, stop_unit=fake.stop_unit, sleep=lambda _s: None, clock=fake.clock
    )

    assert result.ok is True
    assert result.unit_stopped is True
    assert fake.stopped_units == [UNIT]
    assert fake.signals == []


def test_stop_inside_the_scope_signals_members_but_never_stops_its_own_unit() -> None:
    fake = FakeProcs(procs={JOB: FakeProc()}, cgroups={SCOPE_CGROUP: [os.getpid(), JOB]})
    scope = wl.WorkerScope(task_id="t1", launch_mode="scope", unit=UNIT, cgroup=SCOPE_CGROUP)

    result = wl.stop_leftovers(
        scope, reader=fake, kill=fake.kill, stop_unit=fake.stop_unit, sleep=lambda _s: None, clock=fake.clock
    )

    assert result.ok is True
    assert fake.stopped_units == []
    assert fake.signals == [(JOB, signal.SIGTERM)]


def test_only_leftovers_hold_rejects_a_foreign_cwd_holder(tmp_path: Path) -> None:
    worktree = tmp_path / "wt"
    (worktree / "sub").mkdir(parents=True)
    scope = wl.WorkerScope(task_id="t1", launch_mode="popen-fallback")

    own = FakeProcs(procs={JOB: FakeProc(task="t1", cwd=worktree / "sub"), OTHER: FakeProc(task="t2", cwd=tmp_path)})
    foreign = FakeProcs(procs={JOB: FakeProc(task="t1", cwd=worktree), OTHER: FakeProc(task="t2", cwd=worktree)})

    assert wl.only_leftovers_hold(worktree, scope, reader=own) is True
    assert wl.only_leftovers_hold(worktree, scope, reader=foreign) is False


def test_parse_stat_handles_spaces_and_parens_in_comm() -> None:
    fields = ["S", "10", "20", "30"] + ["0"] * 15 + ["4242"] + ["0"] * 5
    text = f"123 (weird ) name) {' '.join(fields)}"

    parsed = wl.parse_stat(text)

    assert parsed == wl.ProcStat(state="S", ppid=10, sid=30, start_ticks=4242)
