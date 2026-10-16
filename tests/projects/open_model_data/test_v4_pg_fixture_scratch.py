"""The v4 PostgreSQL fixture keeps its state in private scratch and unique settings (#10786).

The fixture holds its server as a direct child and signals nothing else:
the tests below stand up the processes a pid read from disk or ``/proc``
could have named (a replaced ``postmaster.pid``, a foreign cluster behind
a symlink) and check that they are left alone.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
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
    """Whether ``pid`` is a live process; an exited but unreaped zombie is not."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return False
    return stat.rpartition(")")[2].split()[0] not in ("Z", "X")


def _children(pid: int) -> list[int]:
    """The live processes whose parent is ``pid`` (the server's backends and auxiliaries)."""
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rpartition(")")[2].split()
        except OSError:
            continue
        if int(fields[1]) == pid and fields[0] not in ("Z", "X"):
            found.append(int(entry.name))
    return found


@pytest.fixture
def launched(monkeypatch):
    """Every server child the fixture launches, with its live children while it ran."""
    record = []
    real_launch = fixtures._launch_server

    def launch(argv, log):
        for earlier in record:
            if earlier["log"] == log:
                assert earlier["server"].returncode is not None, "an earlier attempt's child was not reaped"
        server = real_launch(argv, log)
        record.append({"server": server, "log": log, "children": []})
        return server

    real_ready = fixtures._await_ready

    def ready(server, *args):
        conn = real_ready(server, *args)
        if conn is not None:
            record[-1]["children"] = _children(server.pid)
        return conn

    monkeypatch.setattr(fixtures, "_launch_server", launch)
    monkeypatch.setattr(fixtures, "_await_ready", ready)
    return record


def _assert_gone(entry):
    """The child was reaped, and neither it nor any process it started is still running."""
    server = entry["server"]
    assert server.returncode is not None, "the server child was not reaped"
    assert not _alive(server.pid)
    survivors = [pid for pid in entry["children"] if _alive(pid)]
    assert survivors == [], f"server processes left running: {survivors}"


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


def test_two_servers_run_concurrently_on_distinct_ports_and_directories(scratch, tmp_path, launched):
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
    assert len(launched) == 2
    for entry in launched:
        assert entry["children"], "a running server has backends and auxiliary processes"
        _assert_gone(entry)


def test_free_tcp_port_never_repeats_within_a_process():
    ports = [fixtures._free_tcp_port() for _ in range(50)]
    assert len(set(ports)) == 50


def test_setup_failure_after_start_stops_the_server_and_removes_directories(scratch, tmp_path, monkeypatch, launched):
    def fail_after_start(template):
        raise RuntimeError("injected schema failure")

    monkeypatch.setattr(fixtures, "apply_pg_schema", fail_after_start)
    with pytest.raises(RuntimeError, match="injected schema failure"):
        with fixtures._running_pg_server(scratch, tmp_path / "work"):
            pytest.fail("setup must not yield")
    assert len(launched) == 1
    _assert_gone(launched[0])
    assert list(scratch.iterdir()) == []
    assert not (tmp_path / "work").exists()


def test_teardown_stops_the_real_server_with_sigquit_and_leaves_no_process(scratch, tmp_path, launched):
    with fixtures._running_pg_server(scratch, tmp_path / "work") as conn:
        assert conn.execute("SELECT 1 AS one").fetchone() == {"one": 1}
    (entry,) = launched
    # The postmaster exits by itself after SIGQUIT; the group SIGKILL only reaches its zombie.
    assert entry["server"].returncode == 0
    _assert_gone(entry)
    assert not (tmp_path / "work").exists()


def test_teardown_does_not_need_pidfd_support(scratch, tmp_path, monkeypatch, launched):
    """Round-3 reproducer: without ``os.pidfd_open`` teardown refused and the server kept running."""
    monkeypatch.delattr(os, "pidfd_open", raising=False)
    monkeypatch.delattr(signal, "pidfd_send_signal", raising=False)
    with fixtures._running_pg_server(scratch, tmp_path / "work") as conn:
        assert conn.execute("SELECT 1 AS one").fetchone() == {"one": 1}
    (entry,) = launched
    _assert_gone(entry)
    assert list(scratch.iterdir()) == []
    assert not (tmp_path / "work").exists()


@pytest.fixture
def spawn():
    """Start processes in their own sessions; kill what the test leaves behind."""
    started = []

    def start(argv, *, cwd=None):
        process = subprocess.Popen(
            argv, cwd=cwd, start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE
        )
        started.append(process)
        return process

    yield start
    for process in started:
        if process.returncode is None:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        process.stdout.close()


def _bystander(spawn, cwd):
    """A sleeping child that exits 42 on SIGQUIT, SIGINT or SIGTERM, so any of those shows."""
    code = (
        "import signal, sys, time\n"
        "for signum in (signal.SIGQUIT, signal.SIGINT, signal.SIGTERM):\n"
        "    signal.signal(signum, lambda *_: sys.exit(42))\n"
        "print('ready', flush=True)\n"
        "time.sleep(120)\n"
    )
    child = spawn([sys.executable, "-c", code], cwd=cwd)
    assert child.stdout.readline() == b"ready\n"
    return child


def _untouched(process):
    return process.poll() is None and _alive(process.pid)


def test_a_replaced_postmaster_pid_naming_an_unrelated_child_is_left_alone(scratch, tmp_path, spawn, launched):
    """Round-1 reproducer: ``pg_ctl stop`` signaled whatever pid ``postmaster.pid`` named."""
    data = tmp_path / "work" / "data"
    with fixtures._running_pg_server(scratch, tmp_path / "work"):
        bystander = _bystander(spawn, tmp_path)
        lines = (data / "postmaster.pid").read_text().splitlines()
        (data / "postmaster.pid").write_text("\n".join([str(bystander.pid), *lines[1:]]) + "\n")
    assert _untouched(bystander), f"the bystander exited with {bystander.returncode}"
    (entry,) = launched
    _assert_gone(entry)


@pytest.fixture
def foreign_cluster(scratch, tmp_path_factory):
    """A running server this test's fixture call did not start, with its pid and data directory."""
    record = []
    real_launch = fixtures._launch_server

    def launch(argv, log):
        record.append(real_launch(argv, log))
        return record[-1]

    work = tmp_path_factory.mktemp("foreign") / "work"
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(fixtures, "_launch_server", launch)
        running = fixtures._running_pg_server(scratch, work)
        conn = running.__enter__()
    try:
        yield {"conn": conn, "server": record[-1], "work": work}
    finally:
        running.__exit__(None, None, None)


def _link_into_place(kind, work, foreign_work):
    if kind == "data":
        work.mkdir()
        (work / "data").symlink_to(foreign_work / "data")
    else:
        work.symlink_to(foreign_work)


@pytest.mark.parametrize("linked", ["data", "work"])
def test_a_symlink_to_another_running_cluster_fails_setup_and_is_left_alone(
    foreign_cluster, scratch, tmp_path, launched, linked
):
    """Round-3 reproducer: ``initdb`` failed on the linked cluster, then teardown killed it."""
    foreign = foreign_cluster
    work = tmp_path / "work"
    _link_into_place(linked, work, foreign["work"])
    before = sorted(path.name for path in (foreign["work"] / "data").iterdir())
    sockets = sorted(scratch.iterdir())
    launches = len(launched)
    with pytest.raises(RuntimeError, match="is a symlink"):
        with fixtures._running_pg_server(scratch, work):
            pytest.fail("setup must not yield")
    assert len(launched) == launches, "nothing may be started for a refused data directory"
    assert _untouched(foreign["server"])
    assert foreign["conn"].execute("SELECT 1 AS one").fetchone() == {"one": 1}
    assert sorted(path.name for path in (foreign["work"] / "data").iterdir()) == before
    assert sorted(scratch.iterdir()) == sockets
    assert work.is_symlink() or (work / "data").is_symlink(), "a link the fixture did not create stays"


def test_an_existing_non_empty_data_directory_fails_setup_and_is_kept(scratch, tmp_path, launched):
    work = tmp_path / "work"
    (work / "data").mkdir(parents=True)
    (work / "data" / "PG_VERSION").write_text("16\n")
    with pytest.raises(RuntimeError, match="already exists and is not an empty directory"):
        with fixtures._running_pg_server(scratch, work):
            pytest.fail("setup must not yield")
    assert launched == []
    assert (work / "data" / "PG_VERSION").read_text() == "16\n"
    assert list(scratch.iterdir()) == []


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


def test_directories_stay_until_the_server_child_is_reaped(scratch, tmp_path, monkeypatch, launched):
    """A teardown that cannot confirm the child is gone must not delete the directories under it."""
    real_stop = fixtures._stop_server

    def refuse(server):
        raise RuntimeError("injected stop failure")

    monkeypatch.setattr(fixtures, "_stop_server", refuse)
    with pytest.raises(RuntimeError, match="injected stop failure"):
        with fixtures._running_pg_server(scratch, tmp_path / "work"):
            pass
    (entry,) = launched
    try:
        assert (tmp_path / "work" / "data").is_dir()
        assert len(list(scratch.iterdir())) == 1
    finally:
        real_stop(entry["server"])
    _assert_gone(entry)


def _fake_bindir(tmp_path, body):
    """A server bin directory whose ``postgres`` is a shell script; ``initdb`` is the real one."""
    fake = tmp_path / "fakebin"
    fake.mkdir()
    (fake / "initdb").symlink_to(fixtures._postgres_bindir() / "initdb")
    postgres = fake / "postgres"
    postgres.write_text(f"#!/bin/sh\n{body}\n")
    postgres.chmod(0o700)
    return fake


def _run_failing_start(scratch, tmp_path, monkeypatch, diagnostic=None, body=None):
    """Start through a failing ``postgres`` and count its calls.

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


def test_port_clash_retries_on_new_ports_reaping_each_attempt(scratch, tmp_path, monkeypatch, launched):
    message, calls = _run_failing_start(scratch, tmp_path, monkeypatch, "FATAL: could not bind: Address already in use")
    assert calls == fixtures._PG_START_ATTEMPTS
    assert "PostgreSQL did not start on ports" in message
    assert "Address already in use" in message
    assert len({entry["server"].pid for entry in launched}) == fixtures._PG_START_ATTEMPTS
    for entry in launched:
        _assert_gone(entry)


def test_an_early_exit_is_not_retried_and_reports_its_log(scratch, tmp_path, monkeypatch, launched):
    message, calls = _run_failing_start(scratch, tmp_path, monkeypatch, "SENTINEL-postgres-diagnostic")
    assert calls == 1
    assert "SENTINEL-postgres-diagnostic" in message
    assert "exit 2, not a port clash" in message
    (entry,) = launched
    _assert_gone(entry)


def test_each_start_attempt_is_judged_by_its_own_diagnostics(scratch, tmp_path, monkeypatch):
    """A port clash logged by the first attempt must not make a later configuration error look like one."""
    calls = tmp_path / "calls"
    first_attempt = (
        f'if [ "$(wc -l < {calls})" -eq 1 ]; then\n'
        "  echo 'FATAL: could not bind IPv4 address: Address already in use' >&2\n"
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


def test_a_server_that_never_accepts_connections_is_stopped_and_reaped(scratch, tmp_path, monkeypatch, launched):
    monkeypatch.setattr(fixtures, "_PG_READY_SECONDS", 0.5)
    fake = _fake_bindir(tmp_path, "echo SENTINEL-stuck >&2\nexec sleep 60")
    monkeypatch.setattr(fixtures, "_postgres_bindir", lambda: fake)
    with pytest.raises(RuntimeError, match=r"did not accept connections(.|\n)*SENTINEL-stuck"):
        with fixtures._running_pg_server(scratch, tmp_path / "work"):
            pytest.fail("setup must not yield")
    (entry,) = launched
    assert entry["server"].returncode == -signal.SIGQUIT
    _assert_gone(entry)
    assert list(scratch.iterdir()) == []
    assert not (tmp_path / "work").exists()


HOSTILE = "$(>x) `;'\""  # command substitution, backtick, space, quotes and a separator


def test_server_argv_reaches_postgres_as_literal_values(tmp_path, monkeypatch):
    """The server is exec'd with an argument list: no shell ever sees a path."""
    clean = tmp_path / "clean"
    clean.mkdir()
    monkeypatch.chdir(clean)
    record = tmp_path / "argv"
    fake = _fake_bindir(tmp_path, f"for arg in \"$@\"; do printf '<%s>' \"$arg\"; done > '{record}'")
    data, sock = tmp_path / HOSTILE / "data", tmp_path / ("s " + HOSTILE)
    argv = fixtures._server_argv(fake, data, sock, 54321)
    assert argv == [str(fake / "postgres"), "-D", str(data), "-k", str(sock), "-c", "listen_addresses=", "-p", "54321"]
    server = fixtures._launch_server(argv, tmp_path / "server.log")
    assert server.wait(timeout=30) == 0
    assert record.read_text() == f"<-D><{data}><-k><{sock}><-c><listen_addresses=><-p><54321>"
    assert list(clean.iterdir()) == []


def test_hostile_directory_names_start_a_server_and_run_nothing(scratch, tmp_path, monkeypatch, launched):
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
    _assert_gone(launched[0])


def _python_server(tmp_path, code):
    """Launch ``code`` the way the fixture launches a server; return the child once it reports ready."""
    log = tmp_path / "server.log"
    server = fixtures._launch_server([sys.executable, "-c", code], log)
    deadline = time.monotonic() + 30
    while "ready" not in log.read_text():
        assert time.monotonic() < deadline, log.read_text()
        time.sleep(0.05)
    return server, log


def test_stop_server_sends_sigquit_to_its_child_first(tmp_path):
    code = (
        "import signal, sys, time\n"
        "signal.signal(signal.SIGQUIT, lambda *_: sys.exit(7))\n"
        "print('ready', flush=True)\n"
        "time.sleep(60)\n"
    )
    server, _ = _python_server(tmp_path, code)
    fixtures._stop_server(server)
    assert server.returncode == 7


def test_a_server_that_ignores_shutdown_signals_is_killed_with_its_process_group(tmp_path, monkeypatch):
    code = (
        "import signal, subprocess, time\n"
        "for signum in (signal.SIGQUIT, signal.SIGINT, signal.SIGTERM):\n"
        "    signal.signal(signum, signal.SIG_IGN)\n"
        "helper = subprocess.Popen(['sleep', '60'])\n"
        "print('helper', helper.pid, flush=True)\n"
        "print('ready', flush=True)\n"
        "time.sleep(60)\n"
    )
    server, log = _python_server(tmp_path, code)
    helper = int(log.read_text().split()[1])
    monkeypatch.setattr(fixtures, "_PG_STOP_WAIT_SECONDS", 0.5)
    fixtures._stop_server(server)
    assert server.returncode == -signal.SIGKILL
    deadline = time.monotonic() + 10
    while _alive(helper):
        assert time.monotonic() < deadline, "the process group survived SIGKILL"
        time.sleep(0.05)


def test_waiting_for_exit_never_reaps_the_child(tmp_path):
    """An unreaped child keeps its pid and group id, so signals through the handle cannot hit a reused number."""
    server = fixtures._launch_server(["true"], tmp_path / "server.log")
    assert fixtures._wait_for_exit(server, 10)
    assert server.returncode is None
    assert os.waitid(os.P_PID, server.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None
    fixtures._stop_server(server)
    assert server.returncode == 0
    fixtures._stop_server(server)  # a reaped child is never signaled again


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
