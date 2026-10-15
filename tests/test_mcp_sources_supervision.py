"""The standalone sources server under a fake systemd (#10674).

The real ``server.py --standalone`` runs with a fake notify socket and state
directory: READY=1 only once it accepts connections, pings follow, and the
watchdog's SIGABRT leaves an all-thread dump. Without the systemd variables
it arms nothing.
"""

from __future__ import annotations

import os
import secrets
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

SERVER = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"
INVOCATION = "0123456789abcdef0123456789abcdef"
SYSTEMD_ENV = ("NOTIFY_SOCKET", "WATCHDOG_USEC", "WATCHDOG_PID", "STATE_DIRECTORY", "INVOCATION_ID")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except OSError:
        return False


def _start(port: int, tmp_path: Path, **extra: str) -> subprocess.Popen[str]:
    env = {key: value for key, value in os.environ.items() if key not in SYSTEMD_ENV}
    env.update(extra, LU_MCP_SOURCES_LOG_DIR=str(tmp_path / "logs"))
    return subprocess.Popen(
        [sys.executable, str(SERVER), "--standalone", "--port", str(port)],
        cwd=SERVER.parents[3],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _stop(child: subprocess.Popen[str]) -> str:
    if child.poll() is None:
        child.kill()
    child.wait(20)
    return child.stdout.read()  # type: ignore[union-attr]


def test_ready_after_listening_then_pings_then_a_dump_on_sigabrt(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    name = f"lu-test-server-notify-{secrets.token_hex(6)}"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    listener.bind("\0" + name)
    listener.settimeout(90)
    port = _free_port()
    child = _start(
        port,
        tmp_path,
        NOTIFY_SOCKET="@" + name,
        WATCHDOG_USEC="4000000",
        STATE_DIRECTORY=str(state),
        INVOCATION_ID=INVOCATION,
    )
    try:
        assert listener.recv(64) == b"READY=1"
        assert _listening(port), "READY=1 came before the server accepted connections"
        pings = 0
        deadline = time.monotonic() + 30
        while pings < 2 and time.monotonic() < deadline:
            assert listener.recv(64) == b"WATCHDOG=1"
            pings += 1
        assert pings == 2
        assert (state / "ready-invocation").read_text() == INVOCATION + "\n"
        [dump] = list(state.glob("abort-*.txt"))
        assert dump.stat().st_size == 0
        child.send_signal(signal.SIGABRT)
        assert child.wait(20) == -signal.SIGABRT
    finally:
        listener.close()
        output = _stop(child)
    text = dump.read_text(encoding="utf-8")
    assert text.startswith("Fatal Python error: Aborted"), output[-2000:]
    assert text.count("hread 0x") >= 3
    assert oct(dump.stat().st_mode & 0o777) == "0o600"
    assert "tool=_watchdog_probe outcome=ok" in output


def test_outside_systemd_nothing_is_armed(tmp_path: Path) -> None:
    """Without $NOTIFY_SOCKET and $STATE_DIRECTORY: no dump file, no probe, no notification."""
    port = _free_port()
    child = _start(port, tmp_path)
    try:
        deadline = time.monotonic() + 60
        while not _listening(port):
            assert child.poll() is None and time.monotonic() < deadline
            time.sleep(0.2)
        time.sleep(1.0)  # a pinger, were there one, probes as soon as the server listens
    finally:
        output = _stop(child)
    assert "Abort dump:" not in output
    assert "_watchdog_probe" not in output
    assert "sd_notify" not in output
