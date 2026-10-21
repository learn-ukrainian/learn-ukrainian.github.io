"""Private PostgreSQL fixture scratch, concurrency and failure cleanup."""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import _v4_shared_runtime_fixtures as fixtures
import psutil
import pytest


@pytest.fixture(scope="module")
def pg_scratch():
    # Test setup must stay short independently of the fixture under test.
    with tempfile.TemporaryDirectory(prefix="pg-test-", dir="/tmp") as directory:
        yield Path(directory)


@pytest.mark.parametrize("override", [True, False])
def test_pg_fixture_uses_only_private_scratch(pg_scratch, monkeypatch, override):
    base = pg_scratch
    scratch = base / "p g" if override else base
    if override:
        monkeypatch.setenv("LU_SCRATCH_ROOT", str(scratch))
    else:
        monkeypatch.delenv("LU_SCRATCH_ROOT", raising=False)
    real_mkdtemp = fixtures.tempfile.mkdtemp

    def private_mkdtemp(suffix=None, prefix=None, dir=None):
        if Path(dir or fixtures.tempfile.gettempdir()) != scratch:
            raise PermissionError("shared temporary directory is read-only")
        return real_mkdtemp(suffix=suffix, prefix=prefix, dir=dir)

    monkeypatch.setattr(fixtures.tempfile, "mkdtemp", private_mkdtemp)
    server = fixtures._pg_server.__wrapped__(SimpleNamespace(getbasetemp=lambda: pg_scratch))
    try:
        conn = next(server)
        root = Path(conn.info.host)
        pid = conn.execute("SELECT pg_backend_pid() AS pid").fetchone()["pid"]
        assert root.parent == scratch
        assert root.stat().st_mode & 0o777 == 0o700
        assert conn.execute("SHOW listen_addresses").fetchone() == {"listen_addresses": ""}
        assert (root / f".s.PGSQL.{conn.info.port}").is_socket()
    finally:
        server.close()
    assert conn.closed
    assert not root.exists()
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_pg_fixture_rejects_long_socket_path(pg_scratch, monkeypatch):
    scratch = pg_scratch / ("x" * 110)
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(scratch))
    server = fixtures._pg_server.__wrapped__(SimpleNamespace(getbasetemp=lambda: pg_scratch))
    with pytest.raises(AssertionError, match=r"Unix socket path.*103-byte.*LU_SCRATCH_ROOT"):
        next(server)
    assert list(scratch.iterdir()) == []


@pytest.mark.parametrize("unavailable_roots", [0, 1, 2])
def test_pg_fixture_falls_back_from_long_tmpdir(pg_scratch, monkeypatch, unavailable_roots):
    scratch = pg_scratch / ("long-dispatch-" * 10 + str(unavailable_roots))
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch))
    monkeypatch.delenv("LU_SCRATCH_ROOT", raising=False)
    real_mkdtemp = fixtures.tempfile.mkdtemp
    short_roots = [Path(f"/run/user/{os.getuid()}"), Path("/dev/shm"), Path("/tmp")]

    def mkdtemp(*args, **kwargs):
        if Path(kwargs["dir"]) in short_roots[:unavailable_roots]:
            raise PermissionError("injected unavailable short root")
        return real_mkdtemp(*args, **kwargs)

    monkeypatch.setattr(fixtures.tempfile, "mkdtemp", mkdtemp)
    server = fixtures._pg_server.__wrapped__(SimpleNamespace(getbasetemp=lambda: Path(os.environ["TMPDIR"])))
    try:
        conn = next(server)
        root = Path(conn.info.host)
        socket_path = root / f".s.PGSQL.{conn.info.port}"
        assert root.parent in short_roots[unavailable_roots:]
        assert root.stat().st_mode & 0o777 == 0o700
        assert len(os.fsencode(socket_path)) <= 103
        assert socket_path.is_socket()
        assert conn.execute("SELECT 42 AS answer").fetchone() == {"answer": 42}
        assert conn.execute("SHOW listen_addresses").fetchone() == {"listen_addresses": ""}
    finally:
        server.close()
    assert not root.exists()
    assert list(scratch.iterdir()) == []


@pytest.mark.parametrize(
    "stage", ["pg_config", "initdb", "start", "connect", "schema", "stop", "stop_timeout", "stop_kill"]
)
def test_pg_fixture_cleans_up_after_failure(pg_scratch, monkeypatch, stage):
    scratch = pg_scratch / "f"
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(scratch))
    real_run = fixtures.subprocess.run
    pids = []
    roots = []

    def run(command, **kwargs):
        tool = Path(command[0]).name
        if tool == stage and stage in {"pg_config", "initdb"}:
            raise RuntimeError("injected " + stage)
        if tool == "pg_ctl" and command[-1] == "stop" and stage.startswith("stop"):
            if stage == "stop_kill":
                os.kill(pids[0], signal.SIGSTOP)
            if stage == "stop_timeout":
                raise subprocess.TimeoutExpired(command, 60)
            raise RuntimeError("injected " + stage)
        result = real_run(command, **kwargs)
        if tool == "pg_ctl" and command[-1] == "start":
            data = Path(command[command.index("-D") + 1])
            roots.append(data.parent)
            pid = int((data / "postmaster.pid").read_text().splitlines()[0])
            pids.extend([pid, *(child.pid for child in psutil.Process(pid).children(recursive=True))])
            if stage == "start":
                raise subprocess.TimeoutExpired(command, 60)
        return result

    monkeypatch.setattr(fixtures.subprocess, "run", run)
    if stage == "connect":

        def fail_connect(*args, **kwargs):
            raise RuntimeError("injected connect")

        monkeypatch.setattr(fixtures.psycopg, "connect", fail_connect)
    elif stage == "schema":

        def fail_schema(*args, **kwargs):
            raise RuntimeError("injected schema")

        monkeypatch.setattr(fixtures, "apply_pg_schema", fail_schema)
    server = fixtures._pg_server.__wrapped__(SimpleNamespace(getbasetemp=lambda: pg_scratch))
    error = subprocess.TimeoutExpired if stage in {"start", "stop_timeout"} else RuntimeError
    with pytest.raises(error):
        next(server)
        server.close()
    assert list(scratch.iterdir()) == []
    assert all(not root.exists() for root in roots)
    for pid in pids:
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)


def test_pg_fixture_allows_concurrent_servers(pg_scratch, monkeypatch):
    scratch = pg_scratch / "c"
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(scratch))
    servers = [fixtures._pg_server.__wrapped__(SimpleNamespace(getbasetemp=lambda: pg_scratch)) for _ in range(2)]
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            connections = list(pool.map(next, servers))
        assert connections[0].info.host != connections[1].info.host
        for conn in connections:
            assert conn.execute("SELECT 42 AS answer").fetchone() == {"answer": 42}
    finally:
        for server in servers:
            server.close()
    assert list(scratch.iterdir()) == []
