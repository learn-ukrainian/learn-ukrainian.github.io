"""The v4 PostgreSQL fixture keeps its state in private scratch and unique settings (#10786)."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import _v4_shared_runtime_fixtures as fixtures
import psycopg
import pytest

FIXTURE_DIR = Path(__file__).resolve().parent
REPO = FIXTURE_DIR.parents[2]

pytest_plugins = ("pytester",)


@pytest.fixture
def scratch(tmp_path_factory):
    """A private root with room for a server's socket directory below it."""
    nested = Path("v4pg-00000000") / fixtures._SOCKET_NAME_WORST_CASE
    for parent in (fixtures._scratch_root(tmp_path_factory.getbasetemp()), fixtures._SHORT_SYSTEM_TEMP):
        try:
            root = Path(tempfile.mkdtemp(prefix="s", dir=parent))
        except OSError:
            continue
        if len(os.fsencode(root / nested)) < fixtures._MAX_SOCKET_PATH_BYTES:
            break
        root.rmdir()
    else:
        pytest.fail("no writable directory is short enough to hold a server socket directory")
    yield root
    shutil.rmtree(root, ignore_errors=True)


def _alive(pid: int) -> bool:
    return fixtures._process_alive(pid)


def test_fixture_runs_with_the_system_temp_directory_unwritable(pytester, scratch, monkeypatch):
    """No state goes to ``/tmp``: a subprocess session refuses it and still gets a server."""
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(scratch))
    pytester.makeini("[pytest]\n")
    pytester.makeconftest(
        f"""
        import errno, os, sys, tempfile
        sys.path.insert(0, {str(REPO)!r})
        sys.path.insert(0, {str(FIXTURE_DIR)!r})
        _real = tempfile.mkdtemp

        def _refuse(suffix=None, prefix=None, dir=None):
            if dir is not None and os.fspath(dir).rstrip("/") == "/tmp":
                raise OSError(errno.EROFS, "Read-only file system", "/tmp")
            return _real(suffix, prefix, dir)

        tempfile.mkdtemp = _refuse
        pytest_plugins = ("_v4_shared_runtime_fixtures",)
        """
    )
    pytester.makepyfile(
        test_in_scratch="""
        import os

        def test_server_lives_in_scratch(pg_cluster):
            assert pg_cluster.execute("SELECT 1 AS one").fetchone() == {"one": 1}
            assert os.path.dirname(pg_cluster.info.host) == os.environ["LU_SCRATCH_ROOT"]
            assert pg_cluster.info.port != 55439
        """
    )
    result = pytester.runpytest_subprocess("-n", "0", "-q", "test_in_scratch.py", timeout=120)
    result.assert_outcomes(passed=1)
    assert list(scratch.iterdir()) == [], "teardown must remove the socket directory from scratch"


def test_two_servers_run_concurrently_on_distinct_ports_and_directories(scratch, tmp_path):
    with (
        fixtures._running_pg_server(scratch, tmp_path / "a") as first,
        fixtures._running_pg_server(scratch, tmp_path / "b") as second,
    ):
        assert first.info.port != second.info.port
        assert first.info.host != second.info.host
        assert {first.info.host, second.info.host} <= {str(path) for path in scratch.iterdir()}
        for conn in (first, second):
            assert conn.execute("SELECT 1 AS one").fetchone() == {"one": 1}
    assert list(scratch.iterdir()) == []
    assert not (tmp_path / "a").exists()
    assert not (tmp_path / "b").exists()


def test_free_tcp_port_never_repeats_within_a_process():
    ports = [fixtures._free_tcp_port() for _ in range(50)]
    assert len(set(ports)) == 50


def test_setup_failure_after_start_stops_the_server_and_removes_directories(scratch, tmp_path, monkeypatch):
    seen = {}

    def fail_after_start(template):
        data = tmp_path / "work" / "data"
        seen["pid"] = fixtures._postmaster_pid(data)
        seen["sock"] = [path for path in scratch.iterdir()]
        raise RuntimeError("injected schema failure")

    monkeypatch.setattr(fixtures, "apply_pg_schema", fail_after_start)
    with pytest.raises(RuntimeError, match="injected schema failure"):
        with fixtures._running_pg_server(scratch, tmp_path / "work"):
            pytest.fail("setup must not yield")
    assert seen["pid"] is not None
    assert len(seen["sock"]) == 1
    assert not _alive(seen["pid"])
    assert list(scratch.iterdir()) == []
    assert not (tmp_path / "work").exists()


def test_start_failure_retries_on_new_ports_then_cleans_up(scratch, tmp_path, monkeypatch):
    attempts = []

    def invalid_port():
        attempts.append(99999)  # outside 1..65535, so the server refuses to start
        return 99999

    monkeypatch.setattr(fixtures, "_free_tcp_port", invalid_port)
    with pytest.raises(RuntimeError, match="PostgreSQL did not start on ports"):
        with fixtures._running_pg_server(scratch, tmp_path / "work"):
            pytest.fail("setup must not yield")
    assert len(attempts) == fixtures._PG_START_ATTEMPTS
    assert list(scratch.iterdir()) == []
    assert not (tmp_path / "work").exists()


def test_failure_before_the_server_binary_is_found_still_removes_the_work_directory(scratch, tmp_path, monkeypatch):
    def missing_bindir():
        raise AssertionError("install the PostgreSQL server test dependency")

    monkeypatch.setattr(fixtures, "_postgres_bindir", missing_bindir)
    (tmp_path / "work").mkdir()
    with pytest.raises(AssertionError, match="install the PostgreSQL"):
        with fixtures._running_pg_server(scratch, tmp_path / "work"):
            pytest.fail("setup must not yield")
    assert not (tmp_path / "work").exists()
    assert list(scratch.iterdir()) == []


def test_stop_server_kills_a_server_pg_ctl_cannot_stop(tmp_path):
    fake = tmp_path / "bin"
    fake.mkdir()
    pg_ctl = fake / "pg_ctl"
    pg_ctl.write_text("#!/bin/sh\nexit 1\n")
    pg_ctl.chmod(0o700)
    # The shell exits at once, so init adopts the sleeper and reaps it after the kill.
    pid = int(
        subprocess.run(
            ["sh", "-c", "sleep 60 >/dev/null 2>&1 & echo $!"], check=True, capture_output=True, text=True, timeout=30
        ).stdout
    )
    data = tmp_path / "data"
    data.mkdir()
    (data / "postmaster.pid").write_text(f"{pid}\n{data}\n")
    try:
        assert _alive(pid)
        fixtures._stop_server(fake, data)
        assert not _alive(pid)
    finally:
        if _alive(pid):
            os.kill(pid, 9)


def test_stop_server_without_a_running_server_does_nothing(tmp_path):
    (tmp_path / "data").mkdir()
    fixtures._stop_server(tmp_path / "missing-bin", tmp_path / "data")


def test_scratch_root_prefers_a_writable_lu_scratch_root(tmp_path, monkeypatch):
    base = tmp_path / "base"
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path))
    assert fixtures._scratch_root(base) == tmp_path
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "missing"))
    assert fixtures._scratch_root(base) == base
    monkeypatch.setenv("LU_SCRATCH_ROOT", "")
    assert fixtures._scratch_root(base) == base
    monkeypatch.delenv("LU_SCRATCH_ROOT")
    assert fixtures._scratch_root(base) == base


def test_socket_dir_is_short_unique_private_and_under_the_scratch_root(scratch):
    first = fixtures._make_socket_dir(scratch)
    second = fixtures._make_socket_dir(scratch)
    assert first != second
    for directory in (first, second):
        assert directory.parent == scratch
        assert directory.name.startswith("v4pg-") and len(directory.name) == len("v4pg-") + 8
        assert directory.stat().st_mode & 0o777 == 0o700
        assert len(os.fsencode(directory / ".s.PGSQL.65535")) < fixtures._MAX_SOCKET_PATH_BYTES


def test_overlong_scratch_root_falls_back_to_a_writable_short_directory(tmp_path, monkeypatch):
    short = tmp_path / "s"
    short.mkdir()
    long_root = tmp_path / ("a" * 60)
    long_root.mkdir()
    monkeypatch.setattr(fixtures, "_SHORT_SYSTEM_TEMP", short)
    monkeypatch.setattr(fixtures, "_MAX_SOCKET_PATH_BYTES", len(os.fsencode(short)) + 40)
    chosen = fixtures._make_socket_dir(long_root)
    assert chosen.parent == short
    assert list(long_root.iterdir()) == [], "the rejected directory must not be left behind"


def test_overlong_scratch_root_without_a_writable_fallback_names_the_fix(tmp_path, monkeypatch):
    long_root = tmp_path / ("a" * 60)
    long_root.mkdir()
    monkeypatch.setattr(fixtures, "_SHORT_SYSTEM_TEMP", tmp_path / "missing")
    monkeypatch.setattr(fixtures, "_MAX_SOCKET_PATH_BYTES", len(os.fsencode(tmp_path)) + 20)
    with pytest.raises(RuntimeError, match="set LU_SCRATCH_ROOT to a shorter private writable directory"):
        fixtures._make_socket_dir(long_root)
    assert list(long_root.iterdir()) == []


def test_unwritable_scratch_root_falls_back_to_the_short_directory(tmp_path, monkeypatch):
    short = tmp_path / "s"
    short.mkdir()
    monkeypatch.setattr(fixtures, "_SHORT_SYSTEM_TEMP", short)
    monkeypatch.setattr(fixtures, "_MAX_SOCKET_PATH_BYTES", 4096)  # tmp_path itself is long
    assert fixtures._make_socket_dir(tmp_path / "missing").parent == short


def test_the_pg_server_fixture_yields_a_working_template_connection(_pg_server):
    assert isinstance(_pg_server, psycopg.Connection)
    assert _pg_server.execute("SELECT 1 AS one").fetchone() == {"one": 1}
    assert Path(_pg_server.info.host).name.startswith("v4pg-")
    assert _pg_server.info.port != 55439
