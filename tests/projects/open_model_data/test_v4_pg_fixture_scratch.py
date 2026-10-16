"""The v4 PostgreSQL fixture keeps its state in private scratch and unique settings (#10786)."""

from __future__ import annotations

import contextlib
import os
import shlex
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


def _fake_bindir(tmp_path, pg_ctl_body):
    """A server bin directory whose ``pg_ctl`` is a script; ``initdb`` is the real one."""
    fake = tmp_path / "fakebin"
    fake.mkdir()
    (fake / "initdb").symlink_to(fixtures._postgres_bindir() / "initdb")
    pg_ctl = fake / "pg_ctl"
    pg_ctl.write_text(f"#!/bin/sh\n{pg_ctl_body}\n")
    pg_ctl.chmod(0o700)
    return fake


def _run_failing_start(scratch, tmp_path, monkeypatch, diagnostic):
    """Start through a ``pg_ctl`` that prints ``diagnostic`` to stderr and exits 2; count its calls."""
    calls = tmp_path / "calls"
    fake = _fake_bindir(tmp_path, f"echo call >> {calls}\necho '{diagnostic}' >&2\nexit 2")
    monkeypatch.setattr(fixtures, "_postgres_bindir", lambda: fake)
    with pytest.raises(RuntimeError) as failure:
        with fixtures._running_pg_server(scratch, tmp_path / "work"):
            pytest.fail("setup must not yield")
    assert list(scratch.iterdir()) == []
    assert not (tmp_path / "work").exists()
    return str(failure.value), len(calls.read_text().split())


def test_port_clash_retries_on_new_ports_then_cleans_up(scratch, tmp_path, monkeypatch):
    message, calls = _run_failing_start(scratch, tmp_path, monkeypatch, "FATAL: could not bind: Address already in use")
    assert calls == fixtures._PG_START_ATTEMPTS
    assert "PostgreSQL did not start on ports" in message
    assert "Address already in use" in message


def test_other_startup_failure_is_not_retried_and_keeps_pg_ctl_stderr(scratch, tmp_path, monkeypatch):
    message, calls = _run_failing_start(scratch, tmp_path, monkeypatch, "SENTINEL-pg_ctl-diagnostic")
    assert calls == 1
    assert "SENTINEL-pg_ctl-diagnostic" in message
    assert "not a port clash" in message


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


@pytest.fixture
def failing_pg_ctl(tmp_path):
    fake = tmp_path / "bin"
    fake.mkdir()
    pg_ctl = fake / "pg_ctl"
    pg_ctl.write_text("#!/bin/sh\nexit 1\n")
    pg_ctl.chmod(0o700)
    return fake


@pytest.fixture
def processes():
    """Start sleeping processes in their own sessions; kill what the test leaves behind."""
    started = []

    def start(argv0, *arguments, cwd=None):
        process = subprocess.Popen(
            [argv0, "-c", "sleep 60; true", "sh", *arguments],
            executable="/bin/sh",
            cwd=cwd,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        started.append(process)
        return process

    yield start
    for process in started:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, 9)
        process.wait()


def _claim(data, pid):
    data.mkdir(exist_ok=True)
    (data / "postmaster.pid").write_text(f"{pid}\n{data}\n")


@pytest.mark.parametrize("name", ["postgres", "postmaster"])
def test_stop_server_kills_its_own_server_found_by_command_line(tmp_path, failing_pg_ctl, processes, name):
    data = tmp_path / "data"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    server = processes(f"/usr/lib/postgresql/16/bin/{name}", "-D", str(data), "-p", "1", cwd=elsewhere)
    _claim(data, server.pid)
    fixtures._stop_server(failing_pg_ctl, data)
    assert server.wait(timeout=10) == -9


def test_stop_server_kills_its_own_server_found_by_working_directory(tmp_path, failing_pg_ctl, processes):
    data = tmp_path / "data"
    data.mkdir()
    server = processes("postgres", "-p", "1", cwd=data)
    _claim(data, server.pid)
    fixtures._stop_server(failing_pg_ctl, data)
    assert server.wait(timeout=10) == -9


def test_stop_server_never_signals_an_unrelated_process(tmp_path, failing_pg_ctl, processes):
    """A pid in ``postmaster.pid`` that is not our postgres is left alone and reported."""
    bystander = processes("sleeper")
    _claim(tmp_path / "data", bystander.pid)
    with pytest.raises(RuntimeError, match="refusing to signal"):
        fixtures._stop_server(failing_pg_ctl, tmp_path / "data")
    assert bystander.poll() is None and _alive(bystander.pid)


def test_stop_server_never_signals_a_postgres_serving_another_data_directory(tmp_path, failing_pg_ctl, processes):
    other = tmp_path / "other"
    other.mkdir()
    foreign = processes("postgres", "-D", str(other), cwd=other)
    _claim(tmp_path / "data", foreign.pid)
    with pytest.raises(RuntimeError, match="different data directory"):
        fixtures._stop_server(failing_pg_ctl, tmp_path / "data")
    assert foreign.poll() is None and _alive(foreign.pid)


def test_stop_server_never_signals_another_users_postgres(tmp_path, failing_pg_ctl, processes, monkeypatch):
    data = tmp_path / "data"
    server = processes("postgres", "-D", str(data), cwd=tmp_path)
    _claim(data, server.pid)
    real_uid = os.getuid()
    monkeypatch.setattr(os, "getuid", lambda: real_uid + 1)
    with pytest.raises(RuntimeError, match="belongs to uid"):
        fixtures._stop_server(failing_pg_ctl, data)
    assert server.poll() is None and _alive(server.pid)


def test_stop_server_ignores_a_stale_pid_file_of_a_dead_process(tmp_path, failing_pg_ctl):
    dead = subprocess.Popen(["true"])
    dead.wait()
    _claim(tmp_path / "data", dead.pid)
    fixtures._stop_server(failing_pg_ctl, tmp_path / "data")


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


HOSTILE = "$(>x) `;'\""  # command substitution, backtick, space, quotes and a separator


def test_server_options_reach_postgres_as_literal_values_through_sh(tmp_path, monkeypatch):
    """``pg_ctl`` passes ``-o`` to ``sh``: the values must come out unchanged and run nothing."""
    clean = tmp_path / "clean"
    clean.mkdir()
    monkeypatch.chdir(clean)
    options = fixtures._server_options(tmp_path / HOSTILE, 54321)
    assert shlex.split(options) == ["-k", str(tmp_path / HOSTILE), "-h", "", "-p", "54321"]
    out = subprocess.run(
        ["sh", "-c", f"printf '<%s>' {options}"], check=True, capture_output=True, text=True, timeout=30
    )
    assert out.stdout == f"<-k><{tmp_path / HOSTILE}><-h><><-p><54321>"
    assert list(clean.iterdir()) == []


def test_hostile_directory_names_start_a_server_and_run_nothing(scratch, tmp_path, monkeypatch):
    """A scratch root, work directory and socket directory full of shell syntax still work."""
    root = scratch / HOSTILE
    root.mkdir(mode=0o700)
    work = tmp_path / ("w " + HOSTILE) / "work"
    clean = tmp_path / "clean"
    clean.mkdir()
    monkeypatch.chdir(clean)
    seen = {}
    real_apply = fixtures.apply_pg_schema

    def record(template):
        seen["work"] = sorted(path.name for path in work.iterdir())
        seen["root"] = [path.parent for path in root.iterdir()]
        return real_apply(template)

    monkeypatch.setattr(fixtures, "apply_pg_schema", record)
    with fixtures._running_pg_server(root, work) as conn:
        assert conn.execute("SELECT 1 AS one").fetchone() == {"one": 1}
        assert Path(conn.info.host).parent == root
    assert seen["work"] == ["data", "server.log"]
    assert seen["root"] == [root]
    assert list(clean.iterdir()) == [], "no shell command in a path may run"
    assert list(root.iterdir()) == []
    assert not work.exists()
