"""Sources MCP watchdog: sustained-failure state machine and real dumps (#10674)."""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import textwrap
import time
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts.orchestration import sources_watchdog as wd
from scripts.rag import hang_diagnostics as hd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REAL_HOST = wd.Host

PROC_NET_TCP = textwrap.dedent(
    """\
      sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
       0: 0100007F:223E 00000000:0000 0A 00000000:00000055 00:00000000 00000000  1000        0 1 1
       1: 0100007F:223E 0100007F:9C40 08 00000000:00000000 00:00000000 00000000  1000        0 2 1
       2: 0100007F:223E 0100007F:9C41 08 00000000:00000000 00:00000000 00000000  1000        0 3 1
       3: 0100007F:223E 0100007F:9C42 01 00000000:00000000 00:00000000 00000000  1000        0 4 1
       4: 0100007F:9C43 0100007F:223E 05 00000000:00000000 00:00000000 00000000  1000        0 5 1
       5: 0100007F:1F90 00000000:0000 0A 00000000:00000003 00:00000000 00000000  1000        0 6 1
    """
)


def test_parse_proc_net_tcp_counts_server_side_states_and_backlog() -> None:
    counts, backlog = wd.parse_proc_net_tcp(PROC_NET_TCP, 0x223E)
    # The client-side FIN-WAIT-2 socket (local port 0x9C43) is not the server's.
    assert counts == {"LISTEN": 1, "CLOSE-WAIT": 2, "ESTAB": 1}
    assert backlog == 0x55


class FakeHost:
    def __init__(self, tmp_path: Path, *, active: str = "active", pid: int = 4242) -> None:
        self.tmp_path = tmp_path
        self.healthy: list[bool] = []
        self.active = active
        self.pid = pid
        self.started = 7_000_000
        self.clock = 1_000_000.0
        self.probes = 0
        self.captures: list[int] = []
        self.restarts: list[str] = []
        self.published: list[tuple[str, str]] = []
        self.publish_fails = 0
        self.during_capture: Callable[[], None] | None = None

    def host(self) -> wd.Host:
        return REAL_HOST(
            probe=self.probe,
            unit_state=self.unit_state,
            restart=self.restart,
            capture=self.capture,
            wait_healthy=lambda url, timeout, deadline: (True, "healthy 3s after restart"),
            publish=self.publish,
            now=lambda: self.clock,
        )

    def unit_state(self, unit: str) -> wd.UnitState:
        sub = "running" if self.active == "active" else "dead"
        return wd.UnitState(self.active, sub, self.pid, self.started)

    def probe(self, url: str, timeout: float) -> tuple[bool, str]:
        self.probes += 1
        ok = self.healthy.pop(0) if self.healthy else False
        return ok, "ok" if ok else "TimeoutError: timed out after 5.0s"

    def capture(self, pid: int, dump_dir: Path, port: int, now: float, *, reason: str) -> Path:
        self.captures.append(pid)
        path = dump_dir / f"incident-{len(self.captures)}"
        path.mkdir(parents=True, exist_ok=True)
        if self.during_capture is not None:
            self.during_capture()
        return path

    def restart(self, unit: str) -> str:
        self.restarts.append(unit)
        return "killed and started"

    def publish(self, message: str, key: str) -> None:
        if self.publish_fails:
            self.publish_fails -= 1
            raise RuntimeError("bus down")
        self.published.append((message, key))


def _config(tmp_path: Path, **overrides: object) -> wd.Config:
    values: dict[str, object] = {
        "dump_dir": tmp_path / "dumps",
        "apply": True,
        "health_url": "http://127.0.0.1:18766/health",
    }
    values.update(overrides)
    return wd.Config(**values)  # type: ignore[arg-type]


def _tick(fake: FakeHost, config: wd.Config, healthy: bool, *, advance: float = 15.0) -> str:
    fake.healthy.append(healthy)
    result = wd.run_once(config, fake.host())
    fake.clock += advance
    return result


def test_failures_below_threshold_take_no_action(tmp_path: Path) -> None:
    fake, config = FakeHost(tmp_path), _config(tmp_path)
    assert "failure 1/3" in _tick(fake, config, False)
    assert "failure 2/3" in _tick(fake, config, False)
    assert "healthy" in _tick(fake, config, True)
    assert "failure 1/3" in _tick(fake, config, False)
    assert fake.captures == [] and fake.restarts == [] and fake.published == []


def test_sustained_failure_dumps_before_restart_and_notifies_once(tmp_path: Path) -> None:
    fake, config = FakeHost(tmp_path), _config(tmp_path, startup_grace=0)
    order: list[str] = []
    host = fake.host()
    host.capture = lambda *a, **k: (order.append("dump"), fake.capture(*a, **k))[1]
    host.restart = lambda unit: (order.append("restart"), fake.restart(unit))[1]
    for _ in range(3):
        fake.healthy.append(False)
        result = wd.run_once(config, host)
        fake.clock += 15
    assert order == ["dump", "restart"]
    assert "sustained failure" in result and "cto notified" in result
    assert len(fake.published) == 1
    message, key = fake.published[0]
    assert "HUNG" in message and "Dump captured: " in message
    assert key.startswith("lu-sources-watchdog:")

    # A second hang inside the same incident: dump and restart again, no new report.
    for _ in range(3):
        fake.healthy.append(False)
        wd.run_once(config, host)
        fake.clock += 15
    assert fake.captures == [4242, 4242]
    assert len(fake.restarts) == 2
    assert len(fake.published) == 1


def test_restart_budget_stops_a_restart_loop(tmp_path: Path) -> None:
    fake, config = FakeHost(tmp_path), _config(tmp_path, startup_grace=0, max_restarts=2)
    results = [_tick(fake, config, False) for _ in range(12)]
    assert len(fake.restarts) == 2
    assert len(fake.captures) == 2
    assert any("restart budget exhausted" in result for result in results)
    assert len(fake.published) == 1


def test_budget_frees_after_the_window(tmp_path: Path) -> None:
    fake, config = FakeHost(tmp_path), _config(tmp_path, startup_grace=0, max_restarts=1, restart_window=100)
    for _ in range(6):
        _tick(fake, config, False)
    assert len(fake.restarts) == 1
    fake.clock += 100
    for _ in range(3):
        _tick(fake, config, False)
    assert len(fake.restarts) == 2


def test_startup_grace_suppresses_counting_after_restart(tmp_path: Path) -> None:
    fake, config = FakeHost(tmp_path), _config(tmp_path, startup_grace=60)
    for _ in range(3):
        _tick(fake, config, False)
    assert len(fake.restarts) == 1
    # 45 s of failures inside the 60 s grace do not count.
    assert "startup grace" in _tick(fake, config, False)
    assert "startup grace" in _tick(fake, config, False)
    assert "startup grace" in _tick(fake, config, False)
    assert len(fake.restarts) == 1


def test_inactive_unit_is_never_touched(tmp_path: Path) -> None:
    fake, config = FakeHost(tmp_path, active="inactive", pid=0), _config(tmp_path)
    for _ in range(5):
        assert "systemd owns" in _tick(fake, config, False)
    assert fake.captures == [] and fake.restarts == [] and fake.published == []


def test_dry_run_changes_nothing(tmp_path: Path) -> None:
    fake, config = FakeHost(tmp_path), _config(tmp_path, apply=False, failures_to_act=1)
    assert "would dump" in _tick(fake, config, False)
    assert fake.captures == [] and fake.restarts == [] and fake.published == []
    assert not (tmp_path / "dumps" / wd.STATE_FILE).exists()


def test_failed_publish_is_retried_on_the_next_run(tmp_path: Path) -> None:
    fake, config = FakeHost(tmp_path), _config(tmp_path, startup_grace=0)
    fake.publish_fails = 1
    for _ in range(3):
        result = _tick(fake, config, False)
    assert "notification failed" in result
    assert fake.published == []
    assert "cto notified" in _tick(fake, config, True)
    assert len(fake.published) == 1
    _tick(fake, config, True)
    assert len(fake.published) == 1


def test_incident_closes_after_quiet_period_and_next_hang_reports_again(tmp_path: Path) -> None:
    fake, config = FakeHost(tmp_path), _config(tmp_path, startup_grace=0, incident_quiet=300)
    for _ in range(3):
        _tick(fake, config, False)
    assert len(fake.published) == 1
    assert "closed" not in _tick(fake, config, True)
    fake.clock += 300
    assert "closed" in _tick(fake, config, True)
    for _ in range(3):
        _tick(fake, config, False)
    assert len(fake.published) == 2
    state = json.loads((tmp_path / "dumps" / wd.STATE_FILE).read_text(encoding="utf-8"))
    assert state["incident"]["notified"] is True


def test_restart_budget_survives_incident_closure(tmp_path: Path) -> None:
    """Sol's reproducer: closing an incident must not refill the hourly budget."""
    fake, config = FakeHost(tmp_path), _config(tmp_path)
    failures: list[str] = []
    for _cycle in range(4):
        failures.extend(_tick(fake, config, False) for _ in range(3))
        closed = [_tick(fake, config, True) for _ in range(50)]
        assert any("closed" in result for result in closed)
    # Four cycles fit in about 2,600 s, inside the one-hour window.
    assert fake.clock - 1_000_000.0 < config.restart_window
    assert len(fake.restarts) == 3
    assert "restart budget exhausted (3 in 3600s)" in failures[-1]
    state = json.loads((tmp_path / "dumps" / wd.STATE_FILE).read_text(encoding="utf-8"))
    assert len(state["restart_history"]) == 3
    # The fourth incident opened with the budget spent: it is still reported, once.
    assert len(fake.published) == 4
    assert "Action: restart budget exhausted" in fake.published[-1][0]


def test_restart_history_keeps_only_the_window(tmp_path: Path) -> None:
    fake, config = FakeHost(tmp_path), _config(tmp_path, startup_grace=0, restart_window=100)
    for _ in range(3):
        _tick(fake, config, False)
    fake.clock += 200
    for _ in range(3):
        _tick(fake, config, False)
    state = json.loads((tmp_path / "dumps" / wd.STATE_FILE).read_text(encoding="utf-8"))
    assert state["restart_history"] == [fake.clock - 15]
    assert len(fake.restarts) == 2


def test_recovery_during_capture_aborts_the_restart(tmp_path: Path) -> None:
    """Sol's reproducer: health restored while dumping; the server must not be killed."""
    fake, config = FakeHost(tmp_path), _config(tmp_path, startup_grace=0)
    fake.during_capture = lambda: fake.healthy.append(True)
    for _ in range(2):
        _tick(fake, config, False)
    result = _tick(fake, config, False)
    assert fake.captures == [4242]
    assert fake.restarts == []
    assert fake.probes == 4, "health is probed again after the dump"
    assert "restart aborted: recovered" in result
    message, _key = fake.published[0]
    assert "restart aborted: recovered" in message
    state = json.loads((tmp_path / "dumps" / wd.STATE_FILE).read_text(encoding="utf-8"))
    assert state["failures"] == 0 and state.get("restart_history", []) == []


@pytest.mark.parametrize(
    ("change", "seen"),
    [
        (lambda fake: setattr(fake, "pid", 5151), "pid 5151"),
        (lambda fake: setattr(fake, "started", 7_000_999), "pid 4242"),
        (lambda fake: setattr(fake, "active", "deactivating"), "deactivating"),
    ],
    ids=["new-main-pid", "same-pid-new-process", "unit-stopping"],
)
def test_changed_unit_during_capture_aborts_the_restart(
    tmp_path: Path, change: Callable[[FakeHost], None], seen: str
) -> None:
    fake, config = FakeHost(tmp_path), _config(tmp_path, startup_grace=0)
    fake.during_capture = lambda: change(fake)
    for _ in range(3):
        result = _tick(fake, config, False)
    assert fake.captures == [4242]
    assert fake.restarts == []
    assert "restart aborted: changed" in result and seen in result


def test_unreadable_unit_state_after_capture_aborts_the_restart(tmp_path: Path) -> None:
    fake, config = FakeHost(tmp_path), _config(tmp_path, startup_grace=0)
    host = fake.host()
    reads: list[str] = []

    def unit_state(unit: str) -> wd.UnitState:
        reads.append(unit)
        if fake.captures:
            raise wd.WatchdogError("systemctl show exited 1: bus unavailable")
        return fake.unit_state(unit)

    host.unit_state = unit_state
    for _ in range(3):
        fake.healthy.append(False)
        result = wd.run_once(config, host)
        fake.clock += 15
    assert fake.restarts == []
    assert "restart aborted: unverified" in result and "bus unavailable" in result
    assert len(reads) == 4


def test_failures_of_a_replaced_process_do_not_carry_over(tmp_path: Path) -> None:
    """An operator restart between probes gives the new process a fresh count."""
    fake, config = FakeHost(tmp_path), _config(tmp_path, startup_grace=0)
    _tick(fake, config, False)
    _tick(fake, config, False)
    fake.pid, fake.started = 5151, 7_100_000
    assert "failure 1/3" in _tick(fake, config, False)
    assert "failure 2/3" in _tick(fake, config, False)
    assert fake.restarts == []
    assert "sustained failure" in _tick(fake, config, False)
    assert fake.captures == [5151]


def test_only_the_sources_unit_reaches_the_restart_callback(tmp_path: Path) -> None:
    fake, config = FakeHost(tmp_path), _config(tmp_path, unit="unrelated.service", failures_to_act=1)
    with pytest.raises(wd.WatchdogError, match=r"refusing unit 'unrelated\.service'"):
        wd.run_once(config, fake.host())
    assert fake.restarts == [] and fake.captures == [] and fake.probes == 0


def test_cli_refuses_another_unit_before_any_action(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sol's reproducer: ``run-once --unit unrelated.service --apply --failures-to-act 1``."""
    fake = FakeHost(tmp_path)
    monkeypatch.setattr(wd, "Host", lambda **_kwargs: fake.host())
    monkeypatch.setattr(wd, "default_publisher", lambda: fake.publish)
    argv = ["--dump-dir", str(tmp_path / "dumps"), "run-once", "--unit", "unrelated.service", "--apply"]
    with pytest.raises(SystemExit) as raised:
        wd.main([*argv, "--failures-to-act", "1"])
    assert raised.value.code == 2
    assert fake.restarts == [] and fake.captures == [] and fake.probes == 0
    # The sources unit itself is still served.
    assert wd.main([*argv[:3], "--unit", wd.UNIT, "--apply", "--failures-to-act", "1"]) == 0
    assert fake.restarts == [wd.UNIT]


def test_systemd_actions_refuse_another_unit(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_subprocess(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("systemctl must not run for another unit")

    monkeypatch.setattr(wd.subprocess, "run", no_subprocess)
    for action in (wd.systemd_kill_and_start, wd.systemd_unit_state):
        with pytest.raises(wd.WatchdogError, match="refusing unit"):
            action("unrelated.service")


def test_systemd_unit_state_reads_the_main_process_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def show(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        stdout = "ActiveState=active\nSubState=running\nMainPID=299873\nExecMainStartTimestampMonotonic=1341302900692\n"
        return subprocess.CompletedProcess(command, 0, stdout, "")

    monkeypatch.setattr(wd.subprocess, "run", show)
    assert wd.systemd_unit_state(wd.UNIT) == wd.UnitState("active", "running", 299873, 1341302900692)
    assert "ActiveState,SubState,MainPID,ExecMainStartTimestampMonotonic" in calls[0]


def test_prune_keeps_newest_incidents_and_drops_dead_pid_logs(tmp_path: Path) -> None:
    dump_dir = tmp_path / "dumps"
    for stamp in ("20261015T010000Z", "20261015T020000Z", "20261015T030000Z"):
        (dump_dir / f"incident-{stamp}-pid1").mkdir(parents=True)
    proc_root = tmp_path / "proc"
    (proc_root / "77").mkdir(parents=True)
    (dump_dir / "faulthandler-77.log").write_text("", encoding="utf-8")
    (dump_dir / "faulthandler-78.log").write_text("", encoding="utf-8")
    for stamp in ("20261015T010000Z", "20261015T020000Z", "20261015T030000Z"):
        (dump_dir / f"slow-call-{stamp}-pid77.txt").write_text("", encoding="utf-8")
    wd.prune_dump_dir(dump_dir, keep=2, proc_root=proc_root)
    assert sorted(path.name for path in dump_dir.iterdir()) == [
        "faulthandler-77.log",
        "incident-20261015T020000Z-pid1",
        "incident-20261015T030000Z-pid1",
        "slow-call-20261015T020000Z-pid77.txt",
        "slow-call-20261015T030000Z-pid77.txt",
    ]


def test_resolve_dump_dir_default_and_override(tmp_path: Path) -> None:
    assert hd.resolve_dump_dir(tmp_path, {}) == tmp_path / "batch_state" / "sources-dumps"
    assert hd.resolve_dump_dir(tmp_path, {hd.DUMP_DIR_ENV: str(tmp_path / "x")}) == tmp_path / "x"


HUNG_CHILD = textwrap.dedent(
    """\
    import sys, threading
    from pathlib import Path
    sys.path.insert(0, sys.argv[2])
    from scripts.rag.hang_diagnostics import install_signal_dump

    install_signal_dump(Path(sys.argv[1]))
    lock = threading.Lock()
    condition = threading.Condition()

    def worker_blocked_on_shared_lock():
        with condition:
            print("hung", flush=True)
            lock.acquire()

    lock.acquire()
    with condition:
        threading.Thread(target=worker_blocked_on_shared_lock, daemon=True).start()
        # The worker can announce readiness only after the main thread waits.
        condition.wait()
    """
)


def _spawn(script: str, *args: str) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-c", script, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


THREAD_LINE = re.compile(r"^\d+ .* state=(\S+) wchan=")


def _thread_states(snapshot: str) -> list[str]:
    """The ``state=`` letters of the thread lines in a ``proc_snapshot`` text."""
    threads = snapshot.split("== socket states", 1)[0]
    return [match.group(1) for line in threads.splitlines() if (match := THREAD_LINE.match(line))]


def _wait_until_threads_blocked(
    pid: int,
    *,
    min_threads: int = 2,
    settle_polls: int = 3,
    timeout_s: float = 10.0,
    poll_s: float = 0.01,
) -> None:
    """Return once every thread of ``pid`` is observed asleep in ``state=S``.

    The child's ``hung`` line is printed *before* its worker blocks, so it does
    not prove any thread is asleep: a thread can still be runnable (``state=R``)
    when the snapshot is taken (#10974). Observing the same ``/proc`` thread
    lines the incident dump records, ``settle_polls`` times in a row, is the
    truthful readiness condition; a deadlocked thread never wakes again.
    """
    deadline = time.monotonic() + timeout_s
    asleep = 0
    states: list[str] = []
    while time.monotonic() < deadline:
        states = _thread_states(wd.proc_snapshot(pid, 1))
        asleep = asleep + 1 if len(states) >= min_threads and set(states) == {"S"} else 0
        if asleep >= settle_polls:
            return
        time.sleep(poll_s)
    raise AssertionError(f"pid {pid} never settled with {min_threads}+ threads all asleep; last states {states}")


def test_forced_hang_produces_a_dump_file(tmp_path: Path) -> None:
    """AC-02: a hung process yields every thread's Python stack in the incident."""
    dump_dir = tmp_path / "dumps"
    child = _spawn(HUNG_CHILD, str(dump_dir), str(PROJECT_ROOT))
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "hung"
        _wait_until_threads_blocked(child.pid)
        incident = wd.capture_incident_dump(child.pid, dump_dir, 1, time.time(), reason="forced hang")
        stacks = (incident / "python-stacks.txt").read_text(encoding="utf-8")
        assert "worker_blocked_on_shared_lock" in stacks
        assert "<string>" in stacks and "Current thread" in stacks
        assert stacks.count("Thread 0x") + stacks.count("Current thread 0x") >= 2
        summary = json.loads((incident / "summary.json").read_text(encoding="utf-8"))
        assert summary["python_stacks"] is True
        assert "state=S" in (incident / "proc.txt").read_text(encoding="utf-8")
        assert oct((incident / "python-stacks.txt").stat().st_mode & 0o777) == "0o600"
        assert child.poll() is None, "the dump must not kill the process"
    finally:
        child.kill()
        child.wait(timeout=10)


def _fake_snapshots(monkeypatch: pytest.MonkeyPatch, *samples: list[str]) -> None:
    """Serve ``samples`` (thread states per poll) from ``proc_snapshot``, then repeat the last."""
    remaining = list(samples)

    def snapshot(_pid: int, _port: int, *_args: object) -> str:
        states = remaining.pop(0) if len(remaining) > 1 else remaining[0]
        threads = "".join(f"{100 + i} python state={s} wchan=futex_wait_queue\n" for i, s in enumerate(states))
        return f"== threads of pid 1 (tid comm state wchan)\n{threads}== socket states on port 1\n"

    monkeypatch.setattr(wd, "proc_snapshot", snapshot)


def test_blocked_wait_needs_consecutive_sleeping_samples(monkeypatch: pytest.MonkeyPatch) -> None:
    """A thread that is still runnable, or flaps, restarts the settle count."""
    _fake_snapshots(monkeypatch, ["S", "R"], ["S", "S"], ["S", "R"], ["S", "S"], ["S", "S"], ["S", "S"])
    served: list[int] = []
    real = wd.proc_snapshot
    monkeypatch.setattr(wd, "proc_snapshot", lambda *a: served.append(1) or real(*a))
    _wait_until_threads_blocked(1, poll_s=0)
    assert len(served) == 6


@pytest.mark.parametrize(
    "states",
    [["R", "S"], ["S", "R"], ["R", "R"], ["S"], []],
    ids=["main-runnable", "worker-runnable", "all-runnable", "worker-missing", "no-task-list"],
)
def test_blocked_wait_rejects_an_unblocked_fixture(monkeypatch: pytest.MonkeyPatch, states: list[str]) -> None:
    """The old race: ``hung`` printed, a thread not yet asleep. It must fail, not pass or hang."""
    _fake_snapshots(monkeypatch, states)
    started = time.monotonic()
    with pytest.raises(AssertionError, match="never settled"):
        _wait_until_threads_blocked(1, timeout_s=0.2, poll_s=0)
    assert time.monotonic() - started < 5


def test_blocked_wait_rejects_a_real_runnable_thread() -> None:
    """A real child whose worker spins is ``state=R`` after printing ``hung``; the wait refuses it."""
    spinner = textwrap.dedent(
        """\
        import threading, time

        def spin():
            while True:  # runnable in constant memory (a list comprehension would retain every item)
                pass

        threading.Thread(target=spin, daemon=True).start()
        print("hung", flush=True)
        time.sleep(60)
        """
    )
    child = _spawn(spinner)
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "hung"
        with pytest.raises(AssertionError, match=r"never settled.*'R'"):
            _wait_until_threads_blocked(child.pid, timeout_s=1.0)
    finally:
        child.kill()
        child.wait(timeout=10)


def test_no_signal_without_a_registered_handler(tmp_path: Path) -> None:
    """SIGUSR1's default action kills: never send it to a process without the handler."""
    dump_dir = tmp_path / "dumps"
    dump_dir.mkdir()
    child = _spawn("import time; print('up', flush=True); time.sleep(60)")
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "up"
        sent: list[int] = []
        assert "no faulthandler log" in wd.capture_python_stacks(child.pid, dump_dir, send=lambda p, s: sent.append(s))
        # A stale log from a reused pid is not proof of a handler: SigCgt decides.
        hd.faulthandler_log_path(dump_dir, child.pid).write_text("", encoding="utf-8")
        assert "has no SIGUSR1 handler" in wd.capture_python_stacks(
            child.pid, dump_dir, send=lambda p, s: sent.append(s)
        )
        assert sent == []
        assert child.poll() is None
    finally:
        child.kill()
        child.wait(timeout=10)


def test_handles_signal_reads_sigcgt(tmp_path: Path) -> None:
    status = tmp_path / "proc" / "9" / "status"
    status.parent.mkdir(parents=True)
    status.write_text(f"Name:\tpython\nSigCgt:\t{1 << (signal.SIGUSR1 - 1):016x}\n", encoding="utf-8")
    assert wd.handles_signal(9, signal.SIGUSR1, tmp_path / "proc")
    assert not wd.handles_signal(9, signal.SIGUSR2, tmp_path / "proc")
    assert not wd.handles_signal(10, signal.SIGUSR1, tmp_path / "proc")


@pytest.mark.skipif(not Path("/proc/self/task").is_dir(), reason="needs Linux /proc")
def test_proc_snapshot_of_self_lists_threads() -> None:
    text = wd.proc_snapshot(os.getpid(), 1)
    assert f"{os.getpid()} " in text and "== socket states on port 1" in text
