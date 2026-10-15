"""Sources MCP watchdog: sustained-failure state machine and real dumps (#10674)."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from scripts.orchestration import sources_watchdog as wd
from scripts.rag import hang_diagnostics as hd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

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
        self.clock = 1_000_000.0
        self.captures: list[int] = []
        self.restarts: list[str] = []
        self.published: list[tuple[str, str]] = []
        self.publish_fails = 0

    def host(self) -> wd.Host:
        return wd.Host(
            probe=self.probe,
            unit_state=lambda unit: (self.active, "running" if self.active == "active" else "dead", self.pid),
            restart=self.restart,
            capture=self.capture,
            wait_healthy=lambda url, timeout, deadline: (True, "healthy 3s after restart"),
            publish=self.publish,
            now=lambda: self.clock,
        )

    def probe(self, url: str, timeout: float) -> tuple[bool, str]:
        ok = self.healthy.pop(0) if self.healthy else False
        return ok, "ok" if ok else "TimeoutError: timed out after 5.0s"

    def capture(self, pid: int, dump_dir: Path, port: int, now: float, *, reason: str) -> Path:
        self.captures.append(pid)
        path = dump_dir / f"incident-{len(self.captures)}"
        path.mkdir(parents=True, exist_ok=True)
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
    assert "HUNG" in message and "Dump captured before restart" in message
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
