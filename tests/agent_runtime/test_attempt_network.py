"""Real Unix endpoint protocol tests and bounded fault injection for #9251."""

from __future__ import annotations

import asyncio
import contextlib
import ipaddress
import socket
import tempfile
import threading
import time
from dataclasses import replace

import pytest

from scripts.agent_runtime.attempt_network import (
    AttemptEgress,
    Limits,
    canonical_host,
    host_addresses,
    load_allowlist,
    validate_answers,
)

ALLOWED = frozenset({"api.provider.example"})

# Liveness guard (#9549): the longest a test waits on a child process, socket or
# event-loop call before declaring it hung. It is never a performance
# assertion, so it is sized for a loaded CI runner (the production resolver
# child resolves in ~30 ms locally) rather than for a fast host. The fixture's
# 0.2 s proxy limits and `connect_seconds=.1` are deliberate fault-injection
# timings and stay short.
LIVENESS_SECONDS = 30


def request(proxy, data):
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(LIVENESS_SECONDS)
        client.connect(str(proxy.endpoint))
        client.sendall(data)
        return client.recv(16384)


@pytest.fixture
def proxy():
    from pathlib import Path

    # AF_UNIX has a small path limit independent of pytest's temp base.
    with tempfile.TemporaryDirectory(prefix="eg-", dir="/tmp") as directory:
        result = AttemptEgress(
            Path(directory) / "egress.sock",
            ALLOWED,
            limits=replace(Limits(), header_seconds=0.2, resolve_seconds=0.2, idle_seconds=0.2),
        )
        try:
            yield result
        finally:
            result.cleanup()
            assert not result.thread.is_alive()


@pytest.mark.parametrize("target", [
    "other.example:443", "api.provider.example.evil.example:443", "api.provider.example:80",
    "127.0.0.1:443", "[::1]:443", "user@api.provider.example:443", "API.provider.example:443",
    "api.provider.example.:443", "api.provider.example:0443", "api.provider.example:443/path",
    "api.provider.example:443:443", "api.provider.example:443?x", "api.provider.example:443#x",
])
def test_real_endpoint_refuses_authority_lookalikes(proxy, target):
    assert request(proxy, f"CONNECT {target} HTTP/1.1\r\n\r\n".encode()).startswith(b"HTTP/1.1 403")


@pytest.mark.parametrize("header", [
    b"GET https://api.provider.example/ HTTP/1.1\r\n\r\n",
    b"POST / HTTP/1.1\r\n\r\n",
    b"CONNECT api.provider.example:443 HTTP/1.1\r\nHost: other.example:443\r\n\r\n",
    b"CONNECT api.provider.example:443 HTTP/1.1\r\nHost: api.provider.example:443\r\nHost: api.provider.example:443\r\n\r\n",
    b"CONNECT api.provider.example:443 HTTP/1.1\r\n bad: header\r\n\r\n",
    b"CONNECT api.provider.example:443 HTTP/1.1\r\nContent-Length: 1\r\n\r\nx",
    b"CONNECT api.provider.example:443 HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n",
    b"CONNECT api.provider.example:443 HTTP/2\r\n\r\n",
    b"CONNECT api.provider.example:443 HTTP/1.1\r\nx: \xff\r\n\r\n",
])
def test_real_endpoint_refuses_methods_and_conflicting_headers(proxy, header):
    assert request(proxy, header).startswith(b"HTTP/1.1 403")


@pytest.mark.parametrize("answer", [
    "127.0.0.1", "::1", "::ffff:127.0.0.1", "fc00::1", "fe80::1", "ff02::1", "0.0.0.0", "::",
    # Synthetic address-class fixtures, never literal host addresses.
    pytest.param(str(ipaddress.IPv4Address((10 << 24) | 1)), id="rfc1918"),
    pytest.param(str(ipaddress.IPv4Address((100 << 24) | (64 << 16) | 1)), id="cgnat"),
    pytest.param(str(ipaddress.IPv4Address((169 << 24) | (254 << 16) | (1 << 8) | 1)), id="link-local"),
    pytest.param(str(ipaddress.IPv4Address((224 << 24) | 1)), id="multicast"),
    pytest.param(str(ipaddress.IPv4Address((240 << 24) | 1)), id="reserved"),
])
@pytest.mark.parametrize("mixed", [False, True])
def test_real_endpoint_denies_any_bad_dns_answer(proxy, monkeypatch, answer, mixed):
    async def resolve(host):
        return ["8.8.8.8", answer] if mixed else [answer]

    monkeypatch.setattr(proxy, "_resolve", resolve)
    assert request(proxy, b"CONNECT api.provider.example:443 HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 403")


def test_host_addresses_and_mapped_global_are_denied(proxy, monkeypatch):
    assert host_addresses()
    local = ipaddress.ip_address("8.8.8.8")
    proxy.local_addresses = frozenset({local})
    for answer in (str(local), "::ffff:8.8.8.8"):
        async def resolve(host, answer=answer):
            return [answer]
        monkeypatch.setattr(proxy, "_resolve", resolve)
        assert request(proxy, b"CONNECT api.provider.example:443 HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 403")


def test_numeric_connect_prevents_rebinding(proxy, monkeypatch):
    calls = []

    async def resolve(host):
        calls.append(host)
        return ["8.8.8.8"] if len(calls) == 1 else ["127.0.0.1"]

    async def numeric(sock, address):
        calls.append(address)
        raise OSError("fixture connection refused")

    monkeypatch.setattr(proxy, "_resolve", resolve)
    monkeypatch.setattr(proxy.loop, "sock_connect", numeric)
    assert request(proxy, b"CONNECT api.provider.example:443 HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 403")
    assert calls == ["api.provider.example", ("8.8.8.8", 443)]


def test_success_is_byte_only_and_logs_no_payload(proxy, monkeypatch):
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    stopped = threading.Event()

    def echo():
        with listener.accept()[0] as connection:
            data = connection.recv(1024)
            connection.sendall(data)
            stopped.wait(LIVENESS_SECONDS)

    thread = threading.Thread(target=echo)
    thread.start()

    async def resolve(host):
        return ["8.8.8.8"]

    async def connect(addresses):
        assert addresses == [ipaddress.ip_address("8.8.8.8")]
        return await asyncio.open_connection(*listener.getsockname())

    monkeypatch.setattr(proxy, "_resolve", resolve)
    monkeypatch.setattr(proxy, "_connect", connect)
    try:
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(LIVENESS_SECONDS)
            client.connect(str(proxy.endpoint))
            client.sendall(b"CONNECT api.provider.example:443 HTTP/1.1\r\nHost: api.provider.example:443\r\n\r\n")
            assert client.recv(1024).startswith(b"HTTP/1.1 200")
            client.sendall(b"PRIVATE_PAYLOAD")
            assert client.recv(1024) == b"PRIVATE_PAYLOAD"
        deadline = time.monotonic() + LIVENESS_SECONDS
        while proxy.records[0]["bytes"] < 30 and time.monotonic() < deadline:
            time.sleep(.01)
        assert proxy.records == [{"destination": "api.provider.example:443", "bytes": 30}]
    finally:
        stopped.set()
        listener.close()
        thread.join(LIVENESS_SECONDS)


def test_resolver_hang_and_cancellation_reap_child(proxy, monkeypatch):
    children = []
    real_spawn = asyncio.create_subprocess_exec

    async def hung(*args, **kwargs):
        # Keep the real killable subprocess path; simulate a libc DNS hang.
        proc = await real_spawn(args[0], "-c", "import time; time.sleep(60)", **kwargs)
        children.append(proc)
        return proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", hung)
    assert request(proxy, b"CONNECT api.provider.example:443 HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 403")
    assert children and children[0].returncode is not None
    client = socket.socket(socket.AF_UNIX)
    try:
        client.connect(str(proxy.endpoint))
        client.sendall(b"CONNECT api.provider.example:443 HTTP/1.1\r\n\r\n")
        deadline = time.monotonic() + LIVENESS_SECONDS
        while len(children) < 2 and time.monotonic() < deadline:
            time.sleep(.01)
        proxy.cleanup()
        assert len(children) == 2 and all(p.returncode is not None for p in children)
    finally:
        client.close()


def test_slow_client_large_header_and_flood_are_bounded(proxy):
    assert request(proxy, b"CONNECT api.provider.example:443 HTTP/1.1\r\nx: " + b"x" * 9000).startswith(b"HTTP/1.1 403")
    clients = []
    try:
        for _ in range(proxy.limits.connections + 5):
            client = socket.socket(socket.AF_UNIX)
            client.settimeout(LIVENESS_SECONDS)
            client.connect(str(proxy.endpoint))
            clients.append(client)
        assert len(proxy.tasks) <= proxy.limits.connections
        for client in clients:
            with contextlib.suppress(ConnectionResetError):
                data = client.recv(1024)
                assert data == b"" or data.startswith(b"HTTP/1.1 403")
    finally:
        for client in clients:
            client.close()


def test_config_and_validation_contract():
    for agent in ("agy", "codex", "claude"):
        assert all(canonical_host(host) for host in load_allowlist(agent))
    assert not canonical_host("1.2.3.4")
    assert not canonical_host("provider.example.")
    assert not canonical_host("a" * 64 + ".example")
    with pytest.raises(ValueError):
        validate_answers([], frozenset())


def test_resolver_concurrency_limit_and_cleanup(proxy, monkeypatch):
    children = []
    real_spawn = asyncio.create_subprocess_exec

    async def hung(*args, **kwargs):
        proc = await real_spawn(args[0], "-c", "import time; time.sleep(60)", **kwargs)
        children.append(proc)
        return proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", hung)
    clients = []
    try:
        for _ in range(8):
            client = socket.socket(socket.AF_UNIX)
            client.connect(str(proxy.endpoint))
            client.sendall(b"CONNECT api.provider.example:443 HTTP/1.1\r\n\r\n")
            clients.append(client)
        deadline = time.monotonic() + LIVENESS_SECONDS
        while len(children) < 2 and time.monotonic() < deadline:
            time.sleep(.005)
        assert len(children) == proxy.limits.resolvers
        proxy.cleanup()
        assert all(proc.returncode is not None for proc in children)
    finally:
        for client in clients:
            client.close()


def test_connect_deadline_closes_numeric_socket(proxy, monkeypatch):
    sockets = []

    async def resolve(host):
        return ["8.8.8.8"]

    async def hang(sock, address):
        sockets.append(sock)
        await asyncio.sleep(60)

    proxy.limits = replace(proxy.limits, connect_seconds=.1)
    monkeypatch.setattr(proxy, "_resolve", resolve)
    monkeypatch.setattr(proxy.loop, "sock_connect", hang)
    assert request(proxy, b"CONNECT api.provider.example:443 HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 403")
    assert sockets and all(sock.fileno() == -1 for sock in sockets)


def test_real_resolver_is_parent_only_and_numeric(proxy):
    # No external lookup: libc's local hosts entry is sufficient to exercise
    # the production child; the subsequent address contract must refuse it.
    # The fixture's 0.2 s resolve limit is for the hung-resolver fault tests; a
    # real interpreter child must be allowed to start on a loaded runner.
    proxy.limits = replace(proxy.limits, resolve_seconds=LIVENESS_SECONDS)
    future = asyncio.run_coroutine_threadsafe(proxy._resolve("localhost"), proxy.loop)
    answers = future.result(timeout=LIVENESS_SECONDS)
    assert answers and all(ipaddress.ip_address(a).is_loopback for a in answers)


def test_proxy_start_failure_and_forwarder_help(tmp_path, monkeypatch):
    import subprocess
    import sys
    from pathlib import Path

    from scripts.review.isolation import ReviewIsolationError

    bad = tmp_path / "missing" / "egress.sock"
    with pytest.raises(ReviewIsolationError, match="start_failed"):
        AttemptEgress(bad, ALLOWED)
    forwarder = Path(__file__).resolve().parents[2] / "scripts/agent_runtime/attempt_forwarder.py"
    help_run = subprocess.run([sys.executable, str(forwarder), "--help"], capture_output=True, text=True, timeout=LIVENESS_SECONDS)
    assert help_run.returncode == 0
    assert "Exit codes:" in help_run.stdout and "Outputs:" in help_run.stdout


def test_one_way_stream_stays_alive_then_idle_closes(proxy, monkeypatch):
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    failures = []

    def stream():
        try:
            with listener.accept()[0] as connection:
                for _ in range(12):
                    connection.sendall(b"tick")
                    time.sleep(.05)
                # After streaming exceeds the idle limit, idle closes the socket.
                time.sleep(.5)
        except OSError as exc:
            failures.append(type(exc).__name__)

    thread = threading.Thread(target=stream)
    thread.start()

    async def resolve(host):
        return ["8.8.8.8"]

    async def connect(addresses):
        return await asyncio.open_connection(*listener.getsockname())

    monkeypatch.setattr(proxy, "_resolve", resolve)
    monkeypatch.setattr(proxy, "_connect", connect)
    try:
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(LIVENESS_SECONDS)
            client.connect(str(proxy.endpoint))
            client.sendall(b"CONNECT api.provider.example:443 HTTP/1.1\r\n\r\n")
            header = bytearray()
            while not header.endswith(b"\r\n\r\n"):
                header.extend(client.recv(1))
            assert header.startswith(b"HTTP/1.1 200")
            data = bytearray()
            while chunk := client.recv(1024):
                data.extend(chunk)
            assert data == b"tick" * 12
            assert not failures
    finally:
        listener.close()
        thread.join(LIVENESS_SECONDS)


def test_projected_forwarder_run_replaces_environment_and_preserves_exit(proxy, monkeypatch, tmp_path):
    import subprocess
    import sys

    from scripts.agent_runtime.attempt_forwarder import run

    # The child opens the local TCP relay and exercises denial through the
    # actual parent Unix endpoint. No provider request is made here.
    script = (
        "import os,socket,urllib.parse\n"
        "p=urllib.parse.urlsplit(os.environ['HTTPS_PROXY'])\n"
        "assert os.environ['NO_PROXY']==os.environ['no_proxy']==''\n"
        "assert all(os.environ[k]==os.environ['HTTPS_PROXY'] for k in "
        "['https_proxy','HTTP_PROXY','http_proxy','ALL_PROXY','all_proxy'])\n"
        f"with socket.create_connection((p.hostname,p.port),timeout={LIVENESS_SECONDS}) as s:\n"
        " s.sendall(b'CONNECT not-allowed.example:443 HTTP/1.1\\r\\n\\r\\n')\n"
        " assert s.recv(1024).startswith(b'HTTP/1.1 403')\n"
        "raise SystemExit(7)\n"
    )
    monkeypatch.setenv("HTTPS_PROXY", "http://bad-proxy.example")
    monkeypatch.setenv("NO_PROXY", "*")
    assert asyncio.run(run(str(proxy.endpoint), [sys.executable, "-c", script])) == 7
    missing = tmp_path / "missing.sock"
    with pytest.raises(OSError):
        asyncio.run(run(str(missing), [sys.executable, "-c", "raise SystemExit(99)"]))
    # Internal launcher main must refuse before child startup on missing proxy.
    module = __import__("scripts.agent_runtime.attempt_forwarder", fromlist=["main"])
    result = subprocess.run([sys.executable, module.__file__, str(missing), "/bin/true"],
                            capture_output=True, text=True, timeout=LIVENESS_SECONDS)
    assert result.returncode == 125 and "attempt_forwarder_start_failed" in result.stderr


def test_dns_oversized_response_is_bounded_and_reaped(proxy, monkeypatch):
    real_spawn = asyncio.create_subprocess_exec
    children = []

    async def large(*args, **kwargs):
        proc = await real_spawn(args[0], "-c", "import sys,time; sys.stdout.write('x'*100000); "
                                "sys.stdout.flush(); time.sleep(60)", **kwargs)
        children.append(proc)
        return proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", large)
    assert request(proxy, b"CONNECT api.provider.example:443 HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 403")
    assert children and children[0].returncode is not None


def test_forwarder_cli_success_refusal_and_argument_contract(proxy, tmp_path, monkeypatch):
    import sys

    from scripts.agent_runtime import attempt_forwarder

    monkeypatch.setattr(sys, "argv", [attempt_forwarder.__file__, str(proxy.endpoint), "/bin/true"])
    assert attempt_forwarder.main() == 0
    monkeypatch.setattr(sys, "argv", [attempt_forwarder.__file__, str(tmp_path / "missing.sock"), "/bin/true"])
    assert attempt_forwarder.main() == 125
    monkeypatch.setattr(sys, "argv", [attempt_forwarder.__file__, str(proxy.endpoint)])
    with pytest.raises(SystemExit) as error:
        attempt_forwarder.main()
    assert error.value.code == 2
