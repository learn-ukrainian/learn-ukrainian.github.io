"""The v4 PostgreSQL fixture keeps its state in private scratch and unique settings (#10786)."""

from __future__ import annotations

import contextlib
import errno
import os
import shlex
import shutil
import signal
import subprocess
import sys
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


def _run_failing_start(scratch, tmp_path, monkeypatch, diagnostic=None, body=None):
    """Start through a failing ``pg_ctl`` and count its calls.

    By default it prints ``diagnostic`` to stderr and exits 2; ``body`` replaces that.
    """
    calls = tmp_path / "calls"
    body = body or f"echo '{diagnostic}' >&2\nexit 2"
    fake = _fake_bindir(tmp_path, f"echo call >> {calls}\n{body}")
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


def test_each_start_attempt_is_judged_by_its_own_diagnostics(scratch, tmp_path, monkeypatch):
    """A port clash logged by the first attempt must not make a later configuration error look like one."""
    calls = tmp_path / "calls"
    first_attempt = (
        f'if [ "$(wc -l < {calls})" -eq 1 ]; then\n'
        "  echo 'FATAL: could not bind IPv4 address: Address already in use' >> server.log\n"
        "  exit 1\n"
        "fi\n"
    )
    message, count = _run_failing_start(
        scratch, tmp_path, monkeypatch, body=first_attempt + "echo 'FATAL: SENTINEL-invalid-configuration' >&2\nexit 1"
    )
    assert count == 2
    assert "SENTINEL-invalid-configuration" in message
    assert "not a port clash" in message
    assert "Address already in use" not in message


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
def server_bin(tmp_path):
    """A bin directory whose ``postgres`` is this Python and whose ``pg_ctl`` logs calls and fails.

    A Python child started through it executes the directory's server
    binary, so it stands in for a server; the fixture must never use pg_ctl
    to stop one.
    """
    fake = tmp_path / "bin"
    fake.mkdir()
    (fake / "postgres").symlink_to(os.path.realpath(sys.executable))
    _recording_pg_ctl(fake)
    return fake


def _recording_pg_ctl(bindir):
    pg_ctl = bindir / "pg_ctl"
    pg_ctl.write_text(f'#!/bin/sh\necho "$@" >> {shlex.quote(str(bindir / "pg_ctl.calls"))}\nexit 1\n')
    pg_ctl.chmod(0o700)


def _pg_ctl_calls(bindir):
    calls = bindir / "pg_ctl.calls"
    return calls.read_text().splitlines() if calls.exists() else []


@pytest.fixture
def spawn():
    """Start processes in their own sessions; kill what the test leaves behind."""
    started = []

    def start(argv, *, executable=None, cwd=None):
        process = subprocess.Popen(
            argv,
            executable=executable,
            cwd=cwd,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        started.append(process)
        return process

    yield start
    for process in started:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        process.stdout.close()


def _python_child(spawn, interpreter, cwd, setup=""):
    """A sleeping Python child started as ``interpreter``, returned once ``setup`` has run."""
    code = f"import signal, sys, time\n{setup}\nprint('ready', flush=True)\ntime.sleep(60)\n"
    child = spawn([str(interpreter), "-c", code], cwd=cwd)
    assert child.stdout.readline() == b"ready\n"
    return child


def _shell_child(spawn, argv0, *arguments, cwd):
    """A shell whose ``argv[0]`` is ``argv0``; ``; true`` keeps it from exec'ing sleep."""
    return spawn([argv0, "-c", "sleep 60; true", "sh", *arguments], executable="/bin/sh", cwd=cwd)


def _claim(data, pid, served=None):
    data.mkdir(exist_ok=True)
    (data / "postmaster.pid").write_text(f"{pid}\n{served or data}\n")


def _untouched(process):
    return process.poll() is None and _alive(process.pid)


def test_stop_server_quits_its_own_verified_server(tmp_path, server_bin, spawn):
    data = tmp_path / "data"
    data.mkdir()
    server = _python_child(spawn, server_bin / "postgres", data)
    _claim(data, server.pid)
    fixtures._stop_server(server_bin, data)
    assert server.wait(timeout=10) == -signal.SIGQUIT
    assert _pg_ctl_calls(server_bin) == []


def test_stop_server_kills_a_verified_server_that_outlives_sigquit(tmp_path, server_bin, spawn, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    server = _python_child(spawn, server_bin / "postgres", data, "signal.signal(signal.SIGQUIT, signal.SIG_IGN)")
    _claim(data, server.pid)
    monkeypatch.setattr(fixtures, "_PG_STOP_WAIT_SECONDS", 0.5)
    fixtures._stop_server(server_bin, data)
    assert server.wait(timeout=10) == -signal.SIGKILL


def test_stop_server_stops_a_real_server_it_started(scratch, tmp_path):
    with fixtures._running_pg_server(scratch, tmp_path / "work"):
        pid = fixtures._postmaster_pid(tmp_path / "work" / "data")
        assert pid is not None and _alive(pid)
        pidfd = os.pidfd_open(pid)
    try:
        assert fixtures._wait_for_exit(pidfd, 0), "teardown returns only after the server has exited"
    finally:
        os.close(pidfd)
    assert not (tmp_path / "work").exists()


@pytest.fixture
def cluster(tmp_path):
    """A real initialized data directory with no server running."""
    data = tmp_path / "cluster"
    subprocess.run(
        [str(fixtures._postgres_bindir() / "initdb"), "-D", str(data), "--auth=trust"],
        check=True,
        capture_output=True,
        timeout=60,
    )
    return data


def test_stop_server_never_signals_a_process_named_in_a_replaced_pid_file(cluster, spawn):
    """Review reproducer: ``pg_ctl stop`` would SIGQUIT whatever ``postmaster.pid`` names."""
    bystander = _python_child(spawn, sys.executable, cluster, "signal.signal(signal.SIGQUIT, lambda *_: sys.exit(42))")
    _claim(cluster, bystander.pid)
    with pytest.raises(RuntimeError, match=f"refusing to signal pid {bystander.pid}.*not this installation"):
        fixtures._stop_server(fixtures._postgres_bindir(), cluster)
    assert _untouched(bystander), f"the bystander exited with {bystander.returncode}"


def test_stop_server_never_signals_a_shell_posing_as_postgres(tmp_path, spawn):
    """``argv[0]`` and arguments are chosen by the process; the executed binary is not."""
    real = tmp_path / "bin"
    real.mkdir()
    (real / "postgres").symlink_to(fixtures._postgres_bindir() / "postgres")
    _recording_pg_ctl(real)
    data = tmp_path / "data"
    data.mkdir()
    impostor = _shell_child(spawn, str(real / "postgres"), "-D", str(data), cwd=data)
    _claim(data, impostor.pid)
    with pytest.raises(RuntimeError, match=r"refusing to signal.*executes /"):
        fixtures._stop_server(real, data)
    assert _untouched(impostor)
    assert _pg_ctl_calls(real) == []


def _no_pidfd_open(monkeypatch):
    monkeypatch.delattr(os, "pidfd_open")


def _failing_pidfd_open(monkeypatch):
    def refuse(pid, flags=0):
        raise OSError(errno.ENOSYS, "Function not implemented")

    monkeypatch.setattr(os, "pidfd_open", refuse)


@pytest.mark.parametrize("disable", [_no_pidfd_open, _failing_pidfd_open], ids=["missing", "failing"])
def test_stop_server_without_pidfd_support_signals_no_pid(tmp_path, server_bin, spawn, monkeypatch, disable):
    """Even a process that passes every identity check is not signaled by a bare pid."""
    data = tmp_path / "data"
    data.mkdir()
    server = _python_child(spawn, server_bin / "postgres", data)
    _claim(data, server.pid)
    disable(monkeypatch)
    with pytest.raises(RuntimeError, match=r"refusing to signal.*pidfd support is unavailable"):
        fixtures._stop_server(server_bin, data)
    assert _untouched(server)
    assert _pg_ctl_calls(server_bin) == []


def test_stop_server_without_pidfd_support_ignores_a_dead_pid(tmp_path, server_bin, monkeypatch):
    dead = subprocess.Popen(["true"])
    dead.wait()
    _claim(tmp_path / "data", dead.pid)
    _no_pidfd_open(monkeypatch)
    fixtures._stop_server(server_bin, tmp_path / "data")


def test_stop_server_never_signals_a_server_running_in_another_data_directory(tmp_path, server_bin, spawn):
    other = tmp_path / "other"
    other.mkdir()
    foreign = _python_child(spawn, server_bin / "postgres", other)
    _claim(tmp_path / "data", foreign.pid)
    with pytest.raises(RuntimeError, match="different data directory"):
        fixtures._stop_server(server_bin, tmp_path / "data")
    assert _untouched(foreign)


def test_stop_server_never_signals_when_the_pid_file_names_another_data_directory(tmp_path, server_bin, spawn):
    data = tmp_path / "data"
    data.mkdir()
    server = _python_child(spawn, server_bin / "postgres", data)
    _claim(data, server.pid, served=tmp_path / "other")
    with pytest.raises(RuntimeError, match=r"postmaster\.pid does not name"):
        fixtures._stop_server(server_bin, data)
    assert _untouched(server)


def test_stop_server_never_signals_another_users_server(tmp_path, server_bin, spawn, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    server = _python_child(spawn, server_bin / "postgres", data)
    _claim(data, server.pid)
    real_uid = os.getuid()
    monkeypatch.setattr(os, "getuid", lambda: real_uid + 1)
    with pytest.raises(RuntimeError, match="belongs to uid"):
        fixtures._stop_server(server_bin, data)
    assert _untouched(server)


def test_stop_server_never_signals_a_process_replaced_during_the_check(tmp_path, server_bin, spawn, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    server = _python_child(spawn, server_bin / "postgres", data)
    _claim(data, server.pid)
    start_times = iter(["100", "200"])
    monkeypatch.setattr(fixtures, "_start_time", lambda pid: next(start_times))
    with pytest.raises(RuntimeError, match="replaced while it was being checked"):
        fixtures._stop_server(server_bin, data)
    assert _untouched(server)


def test_stop_server_ignores_a_stale_pid_file_of_a_dead_process(tmp_path, server_bin):
    dead = subprocess.Popen(["true"])
    dead.wait()
    _claim(tmp_path / "data", dead.pid)
    fixtures._stop_server(server_bin, tmp_path / "data")


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
