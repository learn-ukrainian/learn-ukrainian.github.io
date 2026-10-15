"""Sources MCP watchdog: sustained-failure state machine and real dumps (#10674)."""

from __future__ import annotations

import json
import os
import signal
import stat
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


def _stop_before_kill(fake: FakeHost, unit: str) -> str:
    raise KeyboardInterrupt


def _stop_after_kill(fake: FakeHost, unit: str) -> str:
    fake.restart(unit)
    fake.pid += 1
    fake.started += 1_000
    raise KeyboardInterrupt


def _kill_and_start(fake: FakeHost, unit: str) -> str:
    detail = fake.restart(unit)
    fake.pid += 1
    fake.started += 1_000
    return detail


def _stop_in_recovery_wait(url: str, timeout: float, deadline: float) -> tuple[bool, str]:
    raise KeyboardInterrupt


@pytest.mark.parametrize(
    ("restart", "wait_healthy", "kills"),
    [
        (_stop_before_kill, None, 0),
        (_stop_after_kill, None, 1),
        (_kill_and_start, _stop_in_recovery_wait, 1),
    ],
    ids=["before-restart", "during-restart", "during-recovery-wait"],
)
def test_interrupted_restart_still_counts_against_the_budget(
    tmp_path: Path,
    restart: Callable[[FakeHost, str], str],
    wait_healthy: Callable[[str, float, float], tuple[bool, str]] | None,
    kills: int,
) -> None:
    """Sol's reproducer: a watchdog stopped mid-restart must not bypass ``--max-restarts``."""
    fake, config = FakeHost(tmp_path), _config(tmp_path, max_restarts=1)
    state_file = tmp_path / "dumps" / wd.STATE_FILE
    host = fake.host()
    on_disk_at_kill: list[object] = []

    def restart_after_reading_state(unit: str) -> str:
        on_disk_at_kill.append(json.loads(state_file.read_text(encoding="utf-8")).get("restart_history"))
        return restart(fake, unit)

    host.restart = restart_after_reading_state
    if wait_healthy is not None:
        host.wait_healthy = wait_healthy
    results: list[str] = []
    for _ in range(12):
        fake.healthy.append(False)
        try:
            results.append(wd.run_once(config, host))
        except KeyboardInterrupt:
            results.append("interrupted")
        fake.clock += 15
    reserved_at = 1_000_000.0 + 30
    # The charge was on disk before the kill, and only one restart was attempted.
    assert on_disk_at_kill == [[reserved_at]]
    assert len(fake.restarts) == kills
    assert results.count("interrupted") == 1
    assert "restart budget exhausted (1 in 3600s)" in results[-1]
    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert state["restart_history"] == [reserved_at]
    # The interrupted incident is still reported, once, without a claimed outcome.
    assert len(fake.published) == 1
    assert "stopped before it recorded" in fake.published[0][0]


def test_state_write_is_durable_before_it_is_visible(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    real_fsync, real_replace = os.fsync, os.replace

    def fsync(fd: int) -> None:
        events.append("fsync-dir" if stat.S_ISDIR(os.fstat(fd).st_mode) else "fsync-file")
        real_fsync(fd)

    def replace(source: str | Path, target: str | Path) -> None:
        events.append("replace")
        real_replace(source, target)

    monkeypatch.setattr(wd.os, "fsync", fsync)
    monkeypatch.setattr(wd.os, "replace", replace)
    path = tmp_path / "dumps" / wd.STATE_FILE
    wd.write_state(path, {"restart_history": [1.0]})
    assert events == ["fsync-file", "replace", "fsync-dir"]
    assert json.loads(path.read_text(encoding="utf-8")) == {"restart_history": [1.0]}
    assert oct(path.stat().st_mode & 0o777) == "0o600"


def test_notification_carries_no_host_path_of_an_external_dump_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sol's reproducer: a dump directory outside the repo must not reach the cto report."""
    monkeypatch.setattr(wd, "PROJECT_ROOT", tmp_path / "repo")
    dump_dir = tmp_path / "srv-private-7f3a" / "evidence-vault-91c2"
    fake, config = FakeHost(tmp_path), _config(tmp_path, startup_grace=0, dump_dir=dump_dir)
    for _ in range(3):
        result = _tick(fake, config, False)
    incident = dump_dir / "incident-1"
    [(message, _key)] = fake.published
    assert "Dump captured: incident-1\n" in message
    for private in (str(incident), str(dump_dir), str(tmp_path), *dump_dir.relative_to(tmp_path).parts):
        assert private not in message
    # The full locator stays local: the state file and the service log line.
    state = json.loads((dump_dir / wd.STATE_FILE).read_text(encoding="utf-8"))
    assert state["incident"]["dump"] == str(incident)
    assert f"dump {incident};" in result


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

    def worker_blocked_on_shared_lock():
        lock.acquire()

    lock.acquire()
    threading.Thread(target=worker_blocked_on_shared_lock, daemon=True).start()
    print("hung", flush=True)
    lock.acquire()  # the main thread deadlocks on a lock it already holds
    """
)


def _spawn(script: str, *args: str) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-c", script, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_forced_hang_produces_a_dump_file(tmp_path: Path) -> None:
    """AC-02: a hung process yields every thread's Python stack in the incident."""
    dump_dir = tmp_path / "dumps"
    child = _spawn(HUNG_CHILD, str(dump_dir), str(PROJECT_ROOT))
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "hung"
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
