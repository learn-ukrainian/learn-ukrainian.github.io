"""Finding and stopping a dispatch worker's leftover processes (#8991)."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts.orchestration import dispatch_isolation
from scripts.orchestration import worker_leftovers as wl
from tests.worker_leftovers_fakes import (
    FAKE_PID_BASE,
    RUN_NONCE,
    SCOPE_CGROUP,
    TASK_ID,
    UNIT,
    UNKILLABLE,
    FakeProc,
    FakeProcs,
    scope_of,
    stop_kwargs,
)

JOB = FAKE_PID_BASE + 1
OTHER = FAKE_PID_BASE + 2
WORKER_CGROUP = "/user.slice/user-1000.slice/user@1000.service/app.slice/delegate.service"


def _pids(found: list[wl.LeftoverProcess]) -> list[int]:
    return [proc.pid for proc in found]


# --- scanning -------------------------------------------------------------


def test_scope_scan_lists_the_cgroup_minus_the_caller_and_zombies() -> None:
    zombie = FAKE_PID_BASE + 3
    fake = FakeProcs(
        procs={JOB: FakeProc(), OTHER: FakeProc(), zombie: FakeProc(state="Z")},
        cgroups={SCOPE_CGROUP: [os.getpid(), JOB, zombie]},
    )

    assert _pids(wl.find_leftovers(scope_of(launch_mode="scope"), reader=fake)) == [JOB]


def test_fallback_scan_matches_only_this_tasks_marker() -> None:
    fake = FakeProcs(procs={JOB: FakeProc(task=TASK_ID), OTHER: FakeProc(task="t2"), OTHER + 1: FakeProc(task=None)})

    assert _pids(wl.find_leftovers(scope_of(), reader=fake)) == [JOB]


def test_fallback_trusts_the_session_only_while_the_caller_leads_it() -> None:
    fake = FakeProcs(procs={JOB: FakeProc(task=None, sid=os.getpid())})

    led = scope_of(session_id=os.getpid())
    stale = scope_of(session_id=os.getpid() + 1)

    assert _pids(wl.find_leftovers(led, reader=fake)) == [JOB]
    assert wl.find_leftovers(stale, reader=fake) == []


def test_fallback_scan_skips_processes_older_than_the_worker_or_of_another_uid_outside_its_cgroup() -> None:
    fake = FakeProcs(
        procs={
            JOB: FakeProc(task=TASK_ID, start=500),
            # Unreadable, but provably not this worker's: another real uid in
            # another cgroup, or started before the worker (an ssh-agent, say).
            OTHER: FakeProc(uid=os.getuid() + 1, start=600, env_unreadable=True),
            OTHER + 1: FakeProc(start=100, env_unreadable=True),
        }
    )
    scope = scope_of(worker_start_ticks=400, fallback_cgroup=WORKER_CGROUP)

    assert _pids(wl.find_leftovers(scope, reader=fake)) == [JOB]


def test_fallback_scan_finds_a_marked_job_that_changed_its_real_uid() -> None:
    """Membership is the task marker, read before any uid filter (review-8991-r2)."""
    fake = FakeProcs(procs={JOB: FakeProc(task=TASK_ID, start=500, uid=os.getuid() + 1)})
    scope = scope_of(worker_start_ticks=400, fallback_cgroup=WORKER_CGROUP)

    assert _pids(wl.find_leftovers(scope, reader=fake)) == [JOB]
    assert wl.exit_scan(scope, reader=fake, settle_s=0.0).status == wl.SCAN_LIVE


@pytest.mark.parametrize("fallback_cgroup", [WORKER_CGROUP, None])
def test_another_uids_closed_environment_in_the_workers_cgroup_is_unknown(fallback_cgroup: str | None) -> None:
    """A job that changed its uid keeps the worker's cgroup; without one recorded nothing rules it out."""
    fake = FakeProcs(
        procs={JOB: FakeProc(uid=os.getuid() + 1, start=500, env_unreadable=True)},
        cgroups={WORKER_CGROUP: [JOB]},
    )
    scope = scope_of(worker_start_ticks=400, fallback_cgroup=fallback_cgroup)

    with pytest.raises(wl.ScanUnknown, match="environ"):
        wl.find_leftovers(scope, reader=fake)
    assert wl.exit_scan(scope, reader=fake, settle_s=0.0).status == wl.SCAN_UNKNOWN


@pytest.mark.parametrize("uid_offset", [0, 1])
def test_closed_environment_outside_the_workers_cgroup_is_not_a_leftover(uid_offset: int) -> None:
    """A non-dumpable process of any uid started anywhere else on the host does not void the scan (#9514)."""
    fake = FakeProcs(
        procs={
            JOB: FakeProc(task=TASK_ID, start=500),
            OTHER: FakeProc(uid=os.getuid() + uid_offset, start=600, env_unreadable=True),
        }
    )
    scope = scope_of(worker_start_ticks=400, fallback_cgroup=WORKER_CGROUP)

    assert _pids(wl.find_leftovers(scope, reader=fake)) == [JOB]
    del fake.procs[JOB]
    assert wl.exit_scan(scope, reader=fake, settle_s=0.0).status == wl.SCAN_CLEAR


@pytest.mark.parametrize("fallback_cgroup", [WORKER_CGROUP, None])
def test_our_uids_closed_environment_in_the_workers_cgroup_or_without_one_is_unknown(
    fallback_cgroup: str | None,
) -> None:
    fake = FakeProcs(procs={JOB: FakeProc(start=500, env_unreadable=True)}, cgroups={WORKER_CGROUP: [JOB]})
    scope = scope_of(worker_start_ticks=400, fallback_cgroup=fallback_cgroup)

    with pytest.raises(wl.ScanUnknown, match="environ"):
        wl.find_leftovers(scope, reader=fake)
    assert wl.exit_scan(scope, reader=fake, settle_s=0.0).status == wl.SCAN_UNKNOWN


@pytest.mark.parametrize("uid_offset", [0, 1])
def test_closed_environment_with_an_unreadable_cgroup_is_unknown(uid_offset: int) -> None:
    fake = FakeProcs(
        procs={JOB: FakeProc(uid=os.getuid() + uid_offset, start=500, env_unreadable=True, cgroup_unreadable=True)}
    )
    scope = scope_of(worker_start_ticks=400, fallback_cgroup=WORKER_CGROUP)

    with pytest.raises(wl.ScanUnknown, match="cgroup"):
        wl.find_leftovers(scope, reader=fake)
    assert wl.exit_scan(scope, reader=fake, settle_s=0.0).status == wl.SCAN_UNKNOWN


def test_scope_unit_stop_reaches_the_user_manager_without_the_callers_bus_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[dict[str, str]] = []

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(dict(kwargs["env"]))  # type: ignore[call-overload]
        return subprocess.CompletedProcess(argv, 0, "", "")

    derived = {"XDG_RUNTIME_DIR": "/run/user/derived", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/derived/bus"}
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    monkeypatch.delenv("DBUS_SESSION_BUS_ADDRESS", raising=False)
    monkeypatch.setattr(dispatch_isolation, "user_manager_env", lambda env: {**env, **derived})
    monkeypatch.setattr(wl.subprocess, "run", run)

    assert wl._systemctl_stop(UNIT) is True
    assert {key: seen[0][key] for key in derived} == derived
    assert "XDG_RUNTIME_DIR" not in os.environ


def test_unreadable_environment_of_a_possible_job_is_unknown_not_clear() -> None:
    fake = FakeProcs(procs={JOB: FakeProc(start=500, env_unreadable=True)})

    with pytest.raises(wl.ScanUnknown, match="environ"):
        wl.find_leftovers(scope_of(worker_start_ticks=400), reader=fake)
    scan = wl.exit_scan(scope_of(worker_start_ticks=400), reader=fake, settle_s=0.0)
    assert scan.status == wl.SCAN_UNKNOWN
    assert scan.unconfirmed is True
    assert "environ" in (scan.error or "")


def test_unreadable_cgroup_is_unknown_and_a_missing_one_counts_only_from_outside() -> None:
    scope = scope_of(launch_mode="scope")
    unreadable = FakeProcs(unreadable_cgroups={SCOPE_CGROUP})
    missing_inside = FakeProcs(own=SCOPE_CGROUP)
    missing_outside = FakeProcs()

    assert wl.exit_scan(scope, reader=unreadable, settle_s=0.0).status == wl.SCAN_UNKNOWN
    assert wl.exit_scan(scope, reader=missing_inside, settle_s=0.0).status == wl.SCAN_UNKNOWN
    assert wl.exit_scan(scope, reader=missing_outside, settle_s=0.0).status == wl.SCAN_CLEAR


def test_exit_scan_record_fields_for_each_outcome() -> None:
    scope = scope_of(worker_start_ticks=400)
    live = wl.exit_scan(scope, reader=FakeProcs(procs={JOB: FakeProc(task=TASK_ID, start=500)}), settle_s=0.0)
    clear = wl.exit_scan(scope, reader=FakeProcs(), settle_s=0.0)
    unknown = wl.exit_scan(scope, reader=FakeProcs(procs={JOB: FakeProc(start=500, env_unreadable=True)}), settle_s=0.0)

    assert clear.record_fields() == {"leftovers_scan": "clear"}
    assert live.record_fields()["leftovers_scan"] == "live"
    assert live.record_fields()["incomplete_run_reason"] == wl.BACKGROUND_JOBS_REASON
    assert live.record_fields()[wl.BACKGROUND_JOBS_REASON]["processes"][0]["pid"] == JOB
    assert unknown.record_fields()["leftovers_scan"] == "unknown"
    assert unknown.record_fields()["incomplete_run_reason"] == wl.SCAN_UNKNOWN_REASON
    assert wl.BACKGROUND_JOBS_REASON not in unknown.record_fields()
    for scan in (live, unknown):
        assert wl.WorkerScope.from_state(scan.record_fields()[wl.SCOPE_KEY]) == scope


# --- the Cursor CLI's own worker-server (#9534) ---------------------------

CURSOR_VERSIONS = Path("/opt/lu-test-cursor-agent/versions")
CURSOR_VERSION_DIR = CURSOR_VERSIONS / "2026.10.01-e373342"
CURSOR_NODE = CURSOR_VERSION_DIR / "node"
WORKER_SERVER_ARGV = [str(CURSOR_NODE), str(CURSOR_VERSION_DIR / "index.js"), "worker-server"]
PYTEST_JOB = FakeProc(cmd="python -m pytest tests/test_slow.py", exe=Path("/usr/bin/python3.12"))
OTHER_TASK_CGROUP = dispatch_isolation.scope_cgroup(f"lu-worker-t2-{RUN_NONCE}-0123abcd", uid=os.getuid())


def _worker_server(**fields: object) -> FakeProc:
    defaults: dict[str, object] = {"exe": CURSOR_NODE, "argv": WORKER_SERVER_ARGV, "cmd": " ".join(WORKER_SERVER_ARGV)}
    return FakeProc(**{**defaults, **fields})  # type: ignore[arg-type]


def _scope_fake(procs: dict[int, FakeProc]) -> FakeProcs:
    """The default scope launch's cgroup holding the caller and ``procs``."""
    return FakeProcs(procs=procs, cgroups={SCOPE_CGROUP: [os.getpid(), *procs]})


def _scope_exit_scan(
    fake: FakeProcs, *, versions: Path | None = CURSOR_VERSIONS, pidfd: wl.PidfdOps | None = None
) -> wl.ExitScan:
    return wl.exit_scan(
        scope_of(launch_mode="scope"),
        reader=fake,
        settle_s=0.0,
        pidfd=fake.pidfd_ops() if pidfd is None else pidfd,
        sleep=lambda _s: None,
        clock=fake.clock,
        cursor_versions=lambda: versions,
    )


def test_the_worker_server_in_the_tasks_scope_is_terminated_before_the_scan() -> None:
    fake = _scope_fake({JOB: _worker_server()})

    scan = _scope_exit_scan(fake)

    assert fake.signals == [(JOB, signal.SIGTERM)]
    assert scan.status == wl.SCAN_CLEAR
    assert scan.record_fields() == {
        "leftovers_scan": "clear",
        "leftovers_terminated": [
            {"pid": JOB, "cmdline": " ".join(WORKER_SERVER_ARGV), "signals": ["SIGTERM"], "stopped": True}
        ],
    }


def test_a_worker_server_ignoring_sigterm_gets_sigkill() -> None:
    fake = _scope_fake({JOB: _worker_server(ignores=frozenset({signal.SIGTERM}))})

    scan = _scope_exit_scan(fake)

    assert fake.signals == [(JOB, signal.SIGTERM), (JOB, signal.SIGKILL)]
    assert scan.status == wl.SCAN_CLEAR
    assert [proc.as_state()["signals"] for proc in scan.terminated] == [["SIGTERM", "SIGKILL"]]


def test_a_worker_server_that_survives_is_reported_and_the_reaper_keeps_its_scope() -> None:
    """Termination failure changes nothing about the verdict: live, scope recorded, reapable."""
    fake = _scope_fake({JOB: _worker_server(ignores=UNKILLABLE)})

    scan = _scope_exit_scan(fake)

    assert scan.status == wl.SCAN_LIVE
    assert [proc.pid for proc in scan.leftovers] == [JOB]
    fields = scan.record_fields()
    assert fields["incomplete_run_reason"] == wl.BACKGROUND_JOBS_REASON
    assert fields[wl.TERMINATED_KEY] == [
        {"pid": JOB, "cmdline": " ".join(WORKER_SERVER_ARGV), "signals": ["SIGTERM", "SIGKILL"], "stopped": False}
    ]
    record = {**fields, "run_nonce": RUN_NONCE, "launch_mode": "scope", "launch_unit": UNIT}
    scope, refusal = wl.scope_from_record(record, task_id=TASK_ID)
    assert refusal is None and scope == scope_of(launch_mode="scope")


def test_without_pidfd_support_the_worker_server_is_reported_unsignalled() -> None:
    fake = _scope_fake({JOB: _worker_server()})

    scan = _scope_exit_scan(fake, pidfd=wl.PidfdOps(open=None, send=None))

    assert fake.signals == []
    assert scan.status == wl.SCAN_LIVE
    assert [proc.pid for proc in scan.leftovers] == [JOB]
    assert wl.TERMINATED_KEY not in scan.record_fields()


def test_a_different_process_beside_the_worker_server_is_still_reported() -> None:
    fake = _scope_fake({JOB: _worker_server(), OTHER: PYTEST_JOB})

    scan = _scope_exit_scan(fake)

    assert fake.signals == [(JOB, signal.SIGTERM)]
    assert scan.status == wl.SCAN_LIVE
    assert [proc.pid for proc in scan.leftovers] == [OTHER]
    fields = scan.record_fields()
    assert [proc["pid"] for proc in fields[wl.BACKGROUND_JOBS_REASON]["processes"]] == [OTHER]
    assert [proc["pid"] for proc in fields[wl.TERMINATED_KEY]] == [JOB]
    assert wl.SCOPE_KEY in fields


def test_a_different_process_alone_in_the_scope_is_reported_unchanged() -> None:
    fake = _scope_fake({OTHER: PYTEST_JOB})

    scan = _scope_exit_scan(fake)

    assert fake.signals == []
    assert scan.status == wl.SCAN_LIVE
    assert wl.TERMINATED_KEY not in scan.record_fields()


@pytest.mark.parametrize(
    "fields",
    [
        # Same name and argv, but not under the resolved install's versions directory.
        {"exe": Path("/tmp/evil/versions/2026.10.01-e373342/node")},
        # Directly in, or nested below, a version directory.
        {"exe": CURSOR_VERSIONS / "node"},
        {"exe": CURSOR_VERSION_DIR / "bin" / "node"},
        {"exe": CURSOR_VERSION_DIR / "node (deleted)"},
        {"exe": Path("relative/versions/v/node")},
        # The install's node running some other script, or another subcommand.
        {"argv": [str(CURSOR_NODE), "-e", "setInterval(()=>{},1e3)", *WORKER_SERVER_ARGV[1:]]},
        {"argv": [str(CURSOR_NODE), str(CURSOR_VERSIONS / "2026.09.26-dd393fe" / "index.js"), "worker-server"]},
        {"argv": [str(CURSOR_NODE), str(CURSOR_VERSION_DIR / "index.js"), "worker-server-x"]},
        {"argv": [str(CURSOR_NODE), str(CURSOR_VERSION_DIR / "index.js"), "worker-server", "--keep"]},
        # Unreadable exe: not selected, so not signalled.
        {"exe_unreadable": True},
        # Another real uid: never ours to signal.
        {"uid": os.getuid() + 1},
    ],
)
def test_a_process_outside_the_signature_is_not_signalled_and_is_reported(fields: dict) -> None:
    fake = _scope_fake({JOB: _worker_server(**fields)})

    scan = _scope_exit_scan(fake)

    assert fake.signals == []
    assert scan.status == wl.SCAN_LIVE
    assert [proc.pid for proc in scan.leftovers] == [JOB]
    assert scan.terminated == ()


def test_nothing_is_signalled_without_a_resolved_cursor_install() -> None:
    fake = _scope_fake({JOB: _worker_server()})

    assert _scope_exit_scan(fake, versions=None).status == wl.SCAN_LIVE
    assert fake.signals == []


def test_the_worker_server_in_another_tasks_scope_is_not_signalled() -> None:
    fake = FakeProcs(procs={JOB: _worker_server()}, cgroups={SCOPE_CGROUP: [os.getpid()], OTHER_TASK_CGROUP: [JOB]})

    scan = _scope_exit_scan(fake)

    assert fake.signals == []
    assert scan.status == wl.SCAN_CLEAR
    assert scan.terminated == ()


def _pidfd_with_hooks(fake: FakeProcs, *, after_open=None, before_send=None) -> wl.PidfdOps:
    def open_(pid: int) -> int:
        fd = fake.pidfd_open(pid)
        if after_open is not None:
            after_open(pid)
        return fd

    def send(fd: int, sig: int) -> None:
        if before_send is not None:
            before_send(fd)
        fake.pidfd_send(fd, sig)

    return wl.PidfdOps(open=open_, send=send, close=lambda _fd: None)


def test_cgroup_membership_is_rechecked_through_the_pinned_pidfd() -> None:
    """A server that leaves the task's cgroup after its pidfd opens is not signalled, and is gone from the scope."""
    fake = _scope_fake({JOB: _worker_server()})

    def moved_out(_pid: int) -> None:
        fake.cgroups[SCOPE_CGROUP].remove(JOB)
        fake.cgroups[OTHER_TASK_CGROUP] = [JOB]

    scan = _scope_exit_scan(fake, pidfd=_pidfd_with_hooks(fake, after_open=moved_out))

    assert fake.signals == []
    assert scan.terminated == ()
    assert JOB in fake.procs


def test_a_pid_reused_before_the_pidfd_opens_is_not_signalled() -> None:
    """The pidfd pins the replacement; its start time differs from the scanned server's, so no signal."""
    fake = _scope_fake({JOB: _worker_server()})
    replacement = _worker_server(start=200)

    def reused(_pid: int) -> None:
        fake.procs[JOB] = replacement

    def open_(pid: int) -> int:
        reused(pid)
        return fake.pidfd_open(pid)

    scan = _scope_exit_scan(fake, pidfd=wl.PidfdOps(open=open_, send=fake.pidfd_send, close=lambda _fd: None))

    assert fake.signals == []
    assert scan.terminated == ()
    assert fake.procs[JOB] is replacement
    assert scan.status == wl.SCAN_LIVE  # the replacement is in the scope and still reported


def test_a_pid_reused_after_inspection_is_never_signalled() -> None:
    """The server inspected through its pidfd exits and its pid is reused before the signal: the dead pidfd refuses it."""
    fake = _scope_fake({JOB: _worker_server()})
    replacement = _worker_server(start=200)

    def reused(_fd: int) -> None:
        fake.procs[JOB] = replacement

    scan = _scope_exit_scan(fake, pidfd=_pidfd_with_hooks(fake, before_send=reused))

    assert fake.signals == []
    assert scan.terminated == ()
    assert fake.procs[JOB] is replacement
    assert [proc.pid for proc in scan.leftovers] == [JOB]


def test_popen_fallback_never_signals_the_worker_server() -> None:
    """No cgroup proof without a scope: the fallback scan reports and signals nothing."""
    fake = FakeProcs(procs={JOB: _worker_server(task=TASK_ID, start=500)})
    asked: list[bool] = []

    def versions() -> Path:
        asked.append(True)
        return CURSOR_VERSIONS

    scan = wl.exit_scan(
        scope_of(worker_start_ticks=400),
        reader=fake,
        settle_s=0.0,
        pidfd=fake.pidfd_ops(),
        sleep=lambda _s: None,
        clock=fake.clock,
        cursor_versions=versions,
    )

    assert scan.status == wl.SCAN_LIVE
    assert [proc.pid for proc in scan.leftovers] == [JOB]
    assert scan.terminated == ()
    assert fake.signals == []
    assert asked == []
    direct = wl.terminate_cursor_worker_servers(
        scope_of(fallback_cgroup=SCOPE_CGROUP), reader=fake, versions=CURSOR_VERSIONS, pidfd=fake.pidfd_ops()
    )
    assert direct == () and fake.signals == []


def test_a_scope_without_its_cgroup_signals_nothing() -> None:
    fake = _scope_fake({JOB: _worker_server()})
    scope = scope_of(launch_mode="scope", cgroup=None)

    terminated = wl.terminate_cursor_worker_servers(
        scope, reader=fake, versions=CURSOR_VERSIONS, pidfd=fake.pidfd_ops()
    )

    assert terminated == () and fake.signals == []


def test_an_unreadable_scope_signals_nothing_and_the_scan_is_unknown() -> None:
    fake = _scope_fake({JOB: _worker_server()})
    fake.unreadable_cgroups = {SCOPE_CGROUP}

    scan = _scope_exit_scan(fake)

    assert fake.signals == []
    assert scan.status == wl.SCAN_UNKNOWN


def test_live_worker_server_shaped_process_is_selected_and_terminated_through_proc(tmp_path: Path) -> None:
    """Real ``/proc`` reads and a real pidfd: a copied binary blocked on a FIFO named ``index.js``."""
    cat = shutil.which("cat")
    if cat is None or not hasattr(os, "mkfifo"):
        pytest.skip("needs cat and mkfifo")
    ops = wl.live_pidfd_ops()
    if ops.open is None or ops.send is None:
        pytest.skip("needs pidfd support")
    version_dir = tmp_path / "versions" / "2026.10.01-e373342"
    version_dir.mkdir(parents=True)
    node = version_dir / "node"
    shutil.copy2(Path(cat).resolve(), node)
    os.mkfifo(version_dir / "index.js")
    child = subprocess.Popen([str(node), str(version_dir / "index.js"), "worker-server"])
    try:

        class InScope(wl.ProcFsReader):
            """The child stands in for this task's scope cgroup; every other read is the kernel's."""

            def proc_cgroup(self, pid: int) -> str | None:
                return SCOPE_CGROUP if pid == child.pid and self.stat(pid) is not None else super().proc_cgroup(pid)

            def cgroup_procs(self, cgroup: str) -> list[int] | None:
                return [child.pid] if cgroup == SCOPE_CGROUP else super().cgroup_procs(cgroup)

        reader = InScope()
        for _ in range(200):  # until the child has exec'd the copied binary
            if reader.exe(child.pid) == node.resolve():
                break
            time.sleep(0.01)
        versions = (tmp_path / "versions").resolve()
        assert wl.is_cursor_worker_server(reader, child.pid, versions)
        assert not wl.is_cursor_worker_server(reader, child.pid, tmp_path.resolve())
        assert not wl.is_cursor_worker_server(reader, os.getpid(), versions)

        terminated = wl.terminate_cursor_worker_servers(
            scope_of(launch_mode="scope"), reader=reader, versions=versions, pidfd=ops
        )

        assert [(proc.pid, proc.signals, proc.stopped) for proc in terminated] == [(child.pid, ("SIGTERM",), True)]
        assert child.wait(timeout=10) == -signal.SIGTERM
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)


@pytest.mark.parametrize(
    ("resolved", "expected"),
    [
        (
            "/home/u/.local/share/cursor-agent/versions/2026.10.01-e373342/cursor-agent",
            "/home/u/.local/share/cursor-agent/versions",
        ),
        ("/usr/local/bin/cursor-agent", None),
        (None, None),
    ],
)
def test_cursor_versions_dir_follows_the_resolved_cursor_agent(
    monkeypatch: pytest.MonkeyPatch, resolved: str | None, expected: str | None
) -> None:
    calls: list[str] = []

    def fake_resolve(binary: str, *, path: str | None = None) -> str | None:
        calls.append(binary)
        return resolved

    monkeypatch.setattr(wl, "resolve_agent_binary", fake_resolve)

    assert wl.cursor_versions_dir() == (Path(expected) if expected else None)
    assert calls == ["cursor-agent"]


def test_cursor_versions_dir_is_none_when_resolution_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(binary: str, *, path: str | None = None) -> str | None:
        raise RuntimeError("Symlink loop")

    monkeypatch.setattr(wl, "resolve_agent_binary", broken)

    assert wl.cursor_versions_dir() is None


def test_worker_scope_records_the_cgroup_only_when_it_is_this_launch_unit() -> None:
    fake = FakeProcs(own=SCOPE_CGROUP)
    kwargs = {"task_id": TASK_ID, "launch_mode": "scope", "run_nonce": RUN_NONCE, "reader": fake}

    ours = wl.worker_scope_at_exit(launch_unit=UNIT, **kwargs)
    other_unit = wl.worker_scope_at_exit(launch_unit="lu-worker-t1-n0nce-ffffffff", **kwargs)
    fallback = wl.worker_scope_at_exit(
        task_id=TASK_ID, launch_mode="popen-fallback", launch_unit=None, run_nonce=RUN_NONCE, reader=fake
    )

    assert ours.cgroup == SCOPE_CGROUP
    assert other_unit.cgroup is None  # the caller is not in that unit's cgroup
    assert fallback.cgroup is None
    assert fallback.unit is None
    assert fallback.fallback_cgroup == SCOPE_CGROUP  # whatever cgroup the fallback worker runs in
    assert ours.fallback_cgroup is None
    assert wl.WorkerScope.from_state(ours.as_state()) == ours
    assert wl.WorkerScope.from_state(fallback.as_state()) == fallback


def test_scope_launch_without_its_cgroup_is_unknown_never_scanned_by_marker() -> None:
    """A scope launch whose worker was not in its unit has no boundary (review-8991-r2)."""
    fake = FakeProcs(procs={JOB: FakeProc(task=TASK_ID)}, cgroups={SCOPE_CGROUP: [JOB]})
    scope = scope_of(launch_mode="scope", cgroup=None)

    with pytest.raises(wl.ScanUnknown, match="without its cgroup"):
        wl.find_leftovers(scope, reader=fake)
    assert wl.exit_scan(scope, reader=fake, settle_s=0.0).status == wl.SCAN_UNKNOWN


def test_leftovers_state_names_pids_and_truncated_cmdlines() -> None:
    procs = [wl.LeftoverProcess(pid=FAKE_PID_BASE + i, start_ticks=1, cmdline="x" * 500) for i in range(30)]

    state = wl.leftovers_state(scope_of(), procs)

    assert state["reason"] == wl.BACKGROUND_JOBS_REASON
    assert state["count"] == 30
    assert len(state["processes"]) == wl.MAX_RECORDED_PROCESSES
    assert len(state["processes"][0]["cmdline"]) == wl.CMDLINE_MAX_CHARS
    assert state["scope"]["task_id"] == TASK_ID


# --- launch identity ------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        None,
        {"task_id": ""},
        {"task_id": "t1", "unit": 7},
        {"task_id": "t1", "cgroup": ""},
        {"task_id": "t1", "session_id": True},
        {"task_id": "t1", "worker_start_ticks": -1},
    ],
)
def test_malformed_recorded_scope_parses_to_none(raw: object) -> None:
    assert wl.WorkerScope.from_state(raw) is None


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"launch_mode": "scope", "unit": "lu-worker-t2-n0nce-0123abcd"}, "not this task's launch unit"),
        ({"launch_mode": "scope", "unit": "user@1000.service", "cgroup": None}, "not this task's launch unit"),
        ({"launch_mode": "scope", "run_nonce": "other"}, "not this task's launch unit"),
        ({"launch_mode": "scope", "run_nonce": None}, "without a unit or run nonce"),
        ({"launch_mode": "scope", "cgroup": None}, "without its cgroup"),
        (
            {"launch_mode": "scope", "cgroup": "/user.slice/user-1000.slice/user@1000.service/app.slice/x.scope"},
            "lu-dispatch.slice",
        ),
        ({"launch_mode": "popen-fallback", "unit": UNIT}, "records a unit"),
        ({"launch_mode": None}, "unknown launch_mode"),
    ],
)
def test_scope_identity_rejects_anything_not_derived_from_the_launch(fields: dict, message: str) -> None:
    assert message in (wl.scope_identity_error(scope_of(**fields)) or "")


def test_scope_identity_accepts_the_real_launch_derivation() -> None:
    unit = dispatch_isolation.scope_unit_name("impl-1", "abc123")
    cgroup = dispatch_isolation.scope_cgroup(unit, uid=os.getuid())
    scope = wl.WorkerScope(task_id="impl-1", launch_mode="scope", unit=unit, cgroup=cgroup, run_nonce="abc123")

    assert wl.scope_identity_error(scope) is None
    assert cgroup.endswith(f"/lu.slice/lu-dispatch.slice/{unit}.scope")


def _record(scope: wl.WorkerScope, **overrides: object) -> dict:
    return {
        "run_nonce": scope.run_nonce,
        "launch_mode": scope.launch_mode,
        "launch_unit": scope.unit,
        "leftovers_scan": "live",
        "leftovers_scope": scope.as_state(),
        **overrides,
    }


def test_scope_from_record_binds_the_scope_to_the_task_launch_record() -> None:
    scope = scope_of(launch_mode="scope")

    assert wl.scope_from_record(_record(scope), task_id=TASK_ID) == (scope, None)
    assert wl.scope_from_record(_record(scope, leftovers_scan="unknown"), task_id=TASK_ID) == (scope, None)
    assert wl.scope_from_record(_record(scope, leftovers_scan="clear"), task_id=TASK_ID) == (None, None)
    assert wl.scope_from_record({}, task_id=TASK_ID) == (None, None)
    for record, task_id in [
        (_record(scope), "t2"),
        (_record(scope, run_nonce="other"), TASK_ID),
        (_record(scope, launch_unit="lu-worker-t1-n0nce-ffffffff"), TASK_ID),
        (_record(scope, launch_mode="popen-fallback"), TASK_ID),
        (_record(scope, leftovers_scope={"task_id": TASK_ID, "unit": 5}), TASK_ID),
        (_record(scope, leftovers_scan="maybe"), TASK_ID),
        (_record(scope, leftovers_scope={**scope.as_state(), "cgroup": None}), TASK_ID),
    ]:
        found, refusal = wl.scope_from_record(record, task_id=task_id)
        assert found is None
        assert refusal


# --- stopping -------------------------------------------------------------


def test_stop_sends_sigterm_through_a_pidfd_and_leaves_other_processes_alone() -> None:
    fake = FakeProcs(procs={JOB: FakeProc(task=TASK_ID), OTHER: FakeProc(task="t2")})

    result = wl.stop_leftovers(scope_of(), reader=fake, **stop_kwargs(fake))

    assert result.ok is True
    assert fake.signals == [(JOB, signal.SIGTERM)]
    assert OTHER in fake.procs


def test_stop_escalates_to_sigkill_and_reports_survivors() -> None:
    fake = FakeProcs(
        procs={
            JOB: FakeProc(task=TASK_ID, ignores=frozenset({signal.SIGTERM})),
            OTHER: FakeProc(task=TASK_ID, ignores=UNKILLABLE),
        }
    )

    result = wl.stop_leftovers(scope_of(), reader=fake, **stop_kwargs(fake))

    assert result.ok is False
    assert (JOB, signal.SIGKILL) in fake.signals
    assert [proc.pid for proc in result.survivors] == [OTHER]
    assert JOB not in fake.procs


def test_stop_never_signals_a_pid_reused_before_the_pidfd_opened() -> None:
    fake = FakeProcs(procs={JOB: FakeProc(task=TASK_ID, start=100)})
    original_open = fake.pidfd_open

    def reuse_then_open(pid: int) -> int:
        # The job exits and an unrelated process gets its pid before the
        # pidfd is opened: the pidfd pins the newcomer, and the re-check sees it.
        fake.procs[JOB] = FakeProc(task=None, start=999)
        return original_open(pid)

    fake.pidfd_open = reuse_then_open  # type: ignore[method-assign]
    result = wl.stop_leftovers(scope_of(), reader=fake, **stop_kwargs(fake))

    assert fake.signals == []
    assert result.signalled == []


def test_stop_never_signals_a_pid_reused_after_the_identity_check() -> None:
    fake = FakeProcs(procs={JOB: FakeProc(task=TASK_ID, start=100)})
    newcomer = FakeProc(task=None, start=999)
    original_send = fake.pidfd_send

    def reuse_then_send(fd: int, sig: int) -> None:
        # Between the post-open check and the signal the job exits and its
        # pid goes to an unrelated process: the pidfd still names the job.
        fake.procs[JOB] = newcomer
        original_send(fd, sig)

    fake.pidfd_send = reuse_then_send  # type: ignore[method-assign]
    wl.stop_leftovers(scope_of(), reader=fake, **stop_kwargs(fake))

    assert fake.signals == []
    assert fake.procs[JOB] is newcomer


def test_stop_without_pidfd_signals_nothing_and_says_so() -> None:
    fake = FakeProcs(procs={JOB: FakeProc(task=TASK_ID)})
    kwargs = {**stop_kwargs(fake), "pidfd": wl.PidfdOps(open=None, send=None)}

    result = wl.stop_leftovers(scope_of(), reader=fake, **kwargs)

    assert result.ok is False
    assert fake.signals == []
    assert result.unsignalled == [JOB]
    assert "pidfd unavailable" in (result.error or "")


def test_stop_with_an_unknown_scan_signals_nothing() -> None:
    fake = FakeProcs(procs={JOB: FakeProc(task=TASK_ID, start=500), OTHER: FakeProc(start=500, env_unreadable=True)})

    result = wl.stop_leftovers(scope_of(worker_start_ticks=400), reader=fake, **stop_kwargs(fake))

    assert result.ok is False
    assert "unreadable" in (result.error or "")
    assert fake.signals == []


def test_stop_stops_the_scope_unit_when_the_caller_is_outside_it() -> None:
    fake = FakeProcs(procs={JOB: FakeProc()}, cgroups={SCOPE_CGROUP: [JOB]})

    result = wl.stop_leftovers(scope_of(launch_mode="scope"), reader=fake, **stop_kwargs(fake))

    assert result.ok is True
    assert result.unit_stopped is True
    assert fake.stopped_units == [UNIT]
    assert fake.signals == []


@pytest.mark.parametrize(
    "fields",
    [
        {"unit": "lu-worker-other-n0nce-0123abcd"},
        {"cgroup": "/user.slice/user-1000.slice/user@1000.service/app.slice/lu-worker-t1-n0nce-0123abcd.scope"},
        {"run_nonce": "someone-elses"},
        {"cgroup": None},
    ],
)
def test_stop_refuses_a_unit_that_is_not_the_tasks_launch_unit(fields: dict) -> None:
    scope = scope_of(launch_mode="scope", **fields)
    # The job also carries the task marker: a scope launch never falls back to it.
    fake = FakeProcs(procs={JOB: FakeProc(task=TASK_ID)}, cgroups={scope.cgroup or SCOPE_CGROUP: [JOB]})

    result = wl.stop_leftovers(scope, reader=fake, **stop_kwargs(fake))

    assert result.ok is False
    assert "worker scope refused" in (result.error or "")
    assert fake.stopped_units == []
    assert fake.signals == []


def test_stop_never_signals_a_job_that_changed_its_real_uid() -> None:
    fake = FakeProcs(procs={JOB: FakeProc(task=TASK_ID, uid=os.getuid() + 1)})

    result = wl.stop_leftovers(scope_of(), reader=fake, **stop_kwargs(fake))

    assert result.ok is False
    assert fake.signals == []
    assert result.unsignalled == [JOB]
    assert [proc.pid for proc in result.survivors] == [JOB]
    assert "refused a signal" in (result.error or "")


def test_stop_never_stops_a_scope_unit_holding_another_uids_member() -> None:
    """Stopping the unit would signal the foreign member too (review-8991-r3)."""
    fake = FakeProcs(
        procs={JOB: FakeProc(), OTHER: FakeProc(uid=os.getuid() + 1)},
        cgroups={SCOPE_CGROUP: [JOB, OTHER]},
    )

    result = wl.stop_leftovers(scope_of(launch_mode="scope"), reader=fake, **stop_kwargs(fake))

    assert result.ok is False
    assert result.unit_stopped is False
    assert fake.stopped_units == []
    assert fake.signals == []
    assert result.unsignalled == [OTHER]
    assert sorted(proc.pid for proc in result.survivors) == [JOB, OTHER]
    assert "refused a signal" in (result.error or "")


def test_stop_never_signals_a_member_that_changed_uid_while_its_pidfd_opened() -> None:
    fake = FakeProcs(procs={JOB: FakeProc()}, cgroups={SCOPE_CGROUP: [os.getpid(), JOB]}, own=SCOPE_CGROUP)
    original_open = fake.pidfd_open

    def change_uid_then_open(pid: int) -> int:
        fake.procs[JOB].uid = os.getuid() + 1
        return original_open(pid)

    fake.pidfd_open = change_uid_then_open  # type: ignore[method-assign]
    result = wl.stop_leftovers(scope_of(launch_mode="scope"), reader=fake, **stop_kwargs(fake))

    assert result.ok is False
    assert fake.signals == []
    assert result.unsignalled == [JOB]


def test_stop_inside_the_scope_signals_members_but_never_stops_its_own_unit() -> None:
    fake = FakeProcs(procs={JOB: FakeProc()}, cgroups={SCOPE_CGROUP: [os.getpid(), JOB]}, own=SCOPE_CGROUP)

    result = wl.stop_leftovers(scope_of(launch_mode="scope"), reader=fake, **stop_kwargs(fake))

    assert result.ok is True
    assert fake.stopped_units == []
    assert fake.signals == [(JOB, signal.SIGTERM)]


def test_only_leftovers_hold_rejects_a_foreign_cwd_holder(tmp_path: Path) -> None:
    worktree = tmp_path / "wt"
    (worktree / "sub").mkdir(parents=True)

    own = FakeProcs(procs={JOB: FakeProc(task=TASK_ID, cwd=worktree / "sub"), OTHER: FakeProc(task="t2", cwd=tmp_path)})
    foreign = FakeProcs(procs={JOB: FakeProc(task=TASK_ID, cwd=worktree), OTHER: FakeProc(task="t2", cwd=worktree)})
    unknown = FakeProcs(procs={JOB: FakeProc(task=TASK_ID, cwd=worktree), OTHER: FakeProc(env_unreadable=True)})

    assert wl.only_leftovers_hold(worktree, scope_of(), reader=own) is True
    assert wl.only_leftovers_hold(worktree, scope_of(), reader=foreign) is False
    assert wl.only_leftovers_hold(worktree, scope_of(), reader=unknown) is False
    assert wl.only_leftovers_hold(worktree, scope_of(unit=UNIT), reader=own) is False


# --- the live host --------------------------------------------------------


def test_parse_stat_handles_spaces_and_parens_in_comm() -> None:
    fields = ["S", "10", "20", "30"] + ["0"] * 15 + ["4242"] + ["0"] * 5
    text = f"123 (weird ) name) {' '.join(fields)}"

    parsed = wl.parse_stat(text)

    assert parsed == wl.ProcStat(state="S", ppid=10, sid=30, start_ticks=4242)


def test_procfs_reader_maps_missing_to_gone_and_unreadable_to_unknown(tmp_path: Path) -> None:
    proc_root = tmp_path / "proc"
    (proc_root / "42").mkdir(parents=True)
    environ = proc_root / "42" / "environ"
    environ.write_bytes(b"A=1\0")
    environ.chmod(0)
    cgroup_root = tmp_path / "cg"
    (cgroup_root / "x.scope").mkdir(parents=True)
    (cgroup_root / "x.scope" / "cgroup.procs").write_text("7\n")
    (cgroup_root / "x.scope" / "cgroup.procs").chmod(0)
    reader = wl.ProcFsReader(proc_root=proc_root, cgroup_root=cgroup_root)
    if os.access(environ, os.R_OK):
        pytest.skip("running with privileges that bypass file modes")

    # Not a link: readlink fails with EINVAL, which is unreadable, not gone.
    (proc_root / "42" / "exe").write_text("")

    assert reader.stat(43) is None
    assert reader.dispatch_task_id(43) is None
    assert reader.exe(43) is None
    assert reader.argv(43) is None
    assert reader.cgroup_procs("/gone.scope") is None
    with pytest.raises(wl.ScanUnknown):
        reader.dispatch_task_id(42)
    with pytest.raises(wl.ScanUnknown):
        reader.exe(42)
    with pytest.raises(wl.ScanUnknown):
        reader.cgroup_procs("/x.scope")


def test_procfs_reader_reads_this_process() -> None:
    reader = wl.ProcFsReader()
    info = reader.stat(os.getpid())

    assert info is not None and info.state in {"R", "S"}
    assert reader.real_uid(os.getpid()) == os.getuid()
    assert reader.proc_cgroup(os.getpid()) == reader.own_cgroup()
    assert reader.exe(os.getpid()) == Path(os.readlink("/proc/self/exe"))
    assert reader.argv(os.getpid()) == [
        os.fsdecode(arg) for arg in Path("/proc/self/cmdline").read_bytes().split(b"\0")[:-1]
    ]


@pytest.mark.parametrize("provider", ["live", "syscall"])
def test_live_pidfd_signals_only_the_verified_child(provider: str) -> None:
    ops = wl.live_pidfd_ops() if provider == "live" else wl._syscall_pidfd_ops()
    if ops is None or ops.open is None:
        pytest.skip("no pidfd on this host")
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; print('ready', flush=True); time.sleep(60)"],
        env={**os.environ, wl.DISPATCH_TASK_ENV: "live-pidfd-task"},
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        # Popen returns while exec is still switching images, when /proc/<pid>/environ
        # can read empty: only the child's own output proves its environment is in place.
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "ready"
        reader = wl.ProcFsReader()
        info = reader.stat(child.pid)
        assert info is not None
        scope = wl.WorkerScope(task_id="live-pidfd-task", launch_mode="popen-fallback", run_nonce="n")
        stale = wl.LeftoverProcess(pid=child.pid, start_ticks=info.start_ticks - 1, cmdline="")
        proc = wl.LeftoverProcess(pid=child.pid, start_ticks=info.start_ticks, cmdline="")

        assert wl._signal_via_pidfd(scope, reader, stale, signal.SIGTERM, ops) == "gone"
        assert child.poll() is None
        assert wl._signal_via_pidfd(scope, reader, proc, signal.SIGTERM, ops) == "signalled"
        assert child.wait(timeout=10) == -signal.SIGTERM
        # Reaped: the pid is free, and a pidfd cannot be opened on it.
        with pytest.raises(ProcessLookupError):
            ops.open(child.pid)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)
        if child.stdout is not None:
            child.stdout.close()
