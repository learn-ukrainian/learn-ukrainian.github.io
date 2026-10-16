"""Cross-module fixtures for open_model_data tests.

Not a collected test module (the name does not match ``test_*.py``). The
directory ``conftest.py`` imports the fixtures so every test under this
directory sees them. ``tests/test_mcp_sources_v4_invocation_recording.py``
loads this module through ``pytest_plugins`` because it lives outside the
directory. Do not point ``pytest_plugins`` at a collected ``test_*.py``:
under pytest 9.0.3 and xdist ``--dist=loadfile``, fixtures defined in a test
module stay private to that module once the module is collected on the worker.
"""

from __future__ import annotations

import contextlib
import fcntl
import importlib.metadata
import json
import os
import re
import select
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import tomllib
import uuid
from dataclasses import replace
from pathlib import Path

import psycopg
import pytest
from _v4_a7_real_slot_fixture import (
    A3_KEY_ID,
    A3_SIGNING_KEY_HEX,
    FLEET_KEY_ID,
    FLEET_SIGNING_KEY_HEX,
    SOURCES_KEY_ID,
    SOURCES_SIGNING_KEY_HEX,
    TRUST_POLICY,
)
from _v4_linguistic_context_fixture import stored_preparation
from learn_ukrainian_v4_runtime import semantic_inputs
from learn_ukrainian_v4_runtime import v4_trust_authority as trust
from learn_ukrainian_v4_runtime.operation_auth import ActionsPrincipal, canonical_bytes, digest
from learn_ukrainian_v4_runtime.operation_store import OperationStore
from learn_ukrainian_v4_runtime.pg_schema import apply_pg_schema
from packaging.markers import Marker, default_environment
from packaging.requirements import Requirement
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row

from scripts.fleet_comms.request_executor import RequestExecutor

_REPO_ROOT = Path(__file__).resolve().parents[3]


def principal(jti):
    return ActionsPrincipal(
        repository_id=1,
        workflow_ref="fixture/workflow@refs/heads/main",
        ref="refs/heads/main",
        subject="repo:fixture:ref:refs/heads/main",
        workflow_sha256="a" * 64,
        run_id=1,
        run_attempt=1,
        check_run_id=1,
        runner_id=1,
        runner_group_id=1,
        runner_label="fixture-runner",
        authz_policy_sha256="b" * 64,
        jti=jti,
    )


def role_connection(pg, role):
    connection = psycopg.connect(pg.info.dsn, autocommit=True, row_factory=dict_row)
    assert role in ("hramatka_v4_control_writer", "hramatka_v4_sources_writer")
    connection.execute("SET ROLE " + role)
    return connection


# Unix socket paths are limited to about 107 bytes; stay well below that.
_MAX_SOCKET_PATH_BYTES = 100
_SOCKET_NAME_WORST_CASE = ".s.PGSQL.65535"
# The short directory a too-long scratch root falls back to, when it is writable.
_SHORT_SYSTEM_TEMP = Path("/tmp")
_PG_START_ATTEMPTS = 5
_PG_STOP_WAIT_SECONDS = 30
_PG_KILL_WAIT_SECONDS = 10
_ISSUED_PORTS: set[int] = set()
# What postgres or pg_ctl report when the chosen port or its Unix socket file is taken.
_PORT_CLASH = re.compile(r"Address already in use|lock file \".*\.s\.PGSQL\.\d+\.lock\" already exists")


def _free_tcp_port() -> int:
    """Return a port nobody holds right now and this process has not handed out before."""
    for _ in range(100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        if port not in _ISSUED_PORTS:
            _ISSUED_PORTS.add(port)
            return port
    raise RuntimeError("no unissued free TCP port after 100 attempts")


def _scratch_root(basetemp: Path) -> Path:
    """``LU_SCRATCH_ROOT`` when it is a writable directory, else the pytest base temp."""
    override = os.environ.get("LU_SCRATCH_ROOT", "").strip()
    if override and os.path.isdir(override) and os.access(override, os.W_OK | os.X_OK):
        return Path(override)
    return basetemp


def _socket_path_fits(directory: Path) -> bool:
    return len(os.fsencode(directory / _SOCKET_NAME_WORST_CASE)) < _MAX_SOCKET_PATH_BYTES


def _make_socket_dir(scratch_root: Path) -> Path:
    """Create a private ``v4pg-<8 chars>`` directory whose socket path fits the OS limit.

    The scratch root comes first; the short system temp directory is only a
    fallback for a root that is unwritable or makes the socket path too long.
    """
    for parent in (scratch_root, _SHORT_SYSTEM_TEMP):
        try:
            directory = Path(tempfile.mkdtemp(prefix="v4pg-", dir=parent))
        except OSError:
            continue
        if _socket_path_fits(directory):
            return directory
        directory.rmdir()
    raise RuntimeError(
        f"no writable directory keeps the PostgreSQL socket path under {_MAX_SOCKET_PATH_BYTES} bytes; "
        "set LU_SCRATCH_ROOT to a shorter private writable directory"
    )


def _postgres_bindir() -> Path:
    reported = Path(
        subprocess.run(["pg_config", "--bindir"], check=True, capture_output=True, text=True, timeout=30).stdout.strip()
    )
    # CI declares server 16; a newer libpq-dev can report a different bindir.
    binary = next(
        (
            path
            for path in (reported, Path("/usr/lib/postgresql/16/bin"))
            if all((path / tool).is_file() for tool in ("initdb", "pg_ctl"))
        ),
        None,
    )
    assert binary is not None, "install the PostgreSQL server test dependency"
    return binary


def _postmaster_pid(data: Path) -> int | None:
    try:
        return int((data / "postmaster.pid").read_text().splitlines()[0])
    except (OSError, ValueError, IndexError):
        return None


def _process_alive(pid: int) -> bool:
    """Whether ``pid`` is a live process; an exited but unreaped zombie is not."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return False
    return stat.rpartition(")")[2].split()[0] not in ("Z", "X")


def _start_time(pid: int) -> str:
    """Field 22 of ``/proc/<pid>/stat``, the start time that tells a reused pid apart."""
    return Path(f"/proc/{pid}/stat").read_text().rpartition(")")[2].split()[19]


def _identity_problem(pid: int, binary: Path, data: Path) -> str | None:
    """Why ``pid`` is not this fixture's own postgres server, or ``None`` when it is.

    A pid read from ``postmaster.pid`` is only a claim: the file can be stale,
    replaced, or name a reused number, and a command line can say anything.
    The process must belong to this user, execute this installation's server
    binary, run in this data directory (the postmaster changes into it), and
    the lock file must name it serving that directory.
    """
    proc = Path("/proc") / str(pid)
    server = os.path.realpath(binary / "postgres")
    wanted = os.path.realpath(data)
    try:
        started = _start_time(pid)
        owner = proc.stat().st_uid
        exe = os.readlink(proc / "exe")
        cwd = os.readlink(proc / "cwd")
        claim = (data / "postmaster.pid").read_text().splitlines()
        if _start_time(pid) != started:
            return "it was replaced while it was being checked"
    except OSError as error:
        return f"it cannot be inspected ({error})"
    if owner != os.getuid():
        return f"it belongs to uid {owner}, not uid {os.getuid()}"
    if exe != server:
        return f"it executes {exe}, not this installation's server binary {server}"
    if cwd != wanted:
        return f"it runs in a different data directory ({cwd}), not {wanted}"
    if claim[:1] != [str(pid)] or len(claim) < 2 or os.path.realpath(claim[1]) != wanted:
        return f"postmaster.pid does not name pid {pid} serving {wanted}"
    return None


def _open_own_server(pid: int, binary: Path, data: Path) -> int | None:
    """A pidfd for ``pid`` once it is proven to be this fixture's server; ``None`` when it no longer runs.

    The pidfd is opened before the proof and checked alive after it, so the
    proof and every later signal concern one process even if the number is
    reused. Without pidfd support no bare pid is ever signaled: ``pg_ctl``
    starts the server detached, so the fixture holds no child handle to fall
    back to, and it refuses instead. A refused server shuts itself down once
    teardown removes its data directory and lock file.
    """
    refusal = f"refusing to signal pid {pid} from {data}/postmaster.pid"
    try:
        pidfd_send_signal = signal.pidfd_send_signal
        pidfd = os.pidfd_open(pid)
    except ProcessLookupError:
        return None
    except (AttributeError, OSError) as error:
        if not _process_alive(pid):
            return None
        raise RuntimeError(
            f"{refusal}: pidfd support is unavailable ({error!r}) and a bare pid can be reused"
        ) from error
    owned = False
    try:
        problem = _identity_problem(pid, binary, data)
        if problem is None:
            # Still alive, so the pid was never freed and every check above read this process.
            pidfd_send_signal(pidfd, 0)
            owned = True
            return pidfd
        if _process_alive(pid):
            raise RuntimeError(f"{refusal}: {problem}")
        return None
    except ProcessLookupError:
        return None
    finally:
        if not owned:
            os.close(pidfd)


def _wait_for_exit(pidfd: int, seconds: float) -> bool:
    """Whether the process behind ``pidfd`` exits within ``seconds``."""
    poller = select.poll()
    poller.register(pidfd, select.POLLIN)
    return bool(poller.poll(int(seconds * 1000)))


def _stop_server(binary: Path, data: Path) -> None:
    """Stop the server in ``data`` if one runs, signaling only a process proven to be it.

    ``pg_ctl stop`` signals whatever pid ``postmaster.pid`` names, so it is
    not used. The verified pidfd gets SIGQUIT (``pg_ctl``'s immediate
    shutdown), then SIGKILL if the server outlives the wait.
    """
    pid = _postmaster_pid(data)
    if pid is None:
        return
    pidfd = _open_own_server(pid, binary, data)
    if pidfd is None:
        return
    try:
        for signum, seconds in ((signal.SIGQUIT, _PG_STOP_WAIT_SECONDS), (signal.SIGKILL, _PG_KILL_WAIT_SECONDS)):
            with contextlib.suppress(ProcessLookupError):
                signal.pidfd_send_signal(pidfd, signum)
            if _wait_for_exit(pidfd, seconds):
                return
        raise RuntimeError(f"PostgreSQL server {pid} survived SIGQUIT and SIGKILL")
    finally:
        os.close(pidfd)


def _server_options(sock: Path, port: int) -> str:
    """The ``pg_ctl -o`` string. ``pg_ctl`` hands it to ``sh``, so every value is quoted."""
    return f"-k {shlex.quote(str(sock))} -h {shlex.quote('')} -p {port}"


def _appended_text(log: Path, offset: int) -> str:
    """What was written to ``log`` after byte ``offset``."""
    try:
        with log.open("rb") as handle:
            handle.seek(offset)
            return handle.read().decode(errors="replace")
    except FileNotFoundError:
        return ""


def _start_server(binary: Path, work: Path, sock: Path) -> int:
    """Start the server in ``work/data``, retrying on another port after a port clash; return the port.

    ``pg_ctl`` also builds a shell command from ``-D`` and ``-l`` without
    escaping them, so it runs inside ``work`` and gets the relative names.
    Only a clash on the port or its socket file is retried; any other startup
    failure is raised at once with ``pg_ctl``'s stderr and the server log.
    Each attempt is judged by its own stderr and the log lines it appended.
    """
    data = work / "data"
    log = work / "server.log"
    attempted = []
    for _ in range(_PG_START_ATTEMPTS):
        port = _free_tcp_port()
        attempted.append(port)
        offset = log.stat().st_size if log.exists() else 0
        started = subprocess.run(
            [str(binary / "pg_ctl"), "-D", data.name, "-l", log.name, "-o", _server_options(sock, port), "-w", "start"],
            check=False,
            capture_output=True,
            cwd=work,
            timeout=60,
        )
        if started.returncode == 0:
            return port
        stderr = started.stderr.decode(errors="replace").strip()
        tail = _appended_text(log, offset)[-2000:]
        _stop_server(binary, data)
        if not _PORT_CLASH.search(stderr + tail):
            raise RuntimeError(
                f"PostgreSQL failed to start on port {port} (pg_ctl exit {started.returncode}, not a port clash); "
                f"pg_ctl stderr:\n{stderr}\nserver log tail:\n{tail}"
            )
    raise RuntimeError(
        f"PostgreSQL did not start on ports {attempted}; pg_ctl stderr:\n{stderr}\nserver log tail:\n{tail}"
    )


@contextlib.contextmanager
def _running_pg_server(scratch_root: Path, work: Path):
    """Yield a superuser connection to a fresh server holding a schema-applied template.

    The socket directory lives under ``scratch_root``, the server runs on a
    port chosen for this run, and teardown stops the server and removes both
    directories, also when setup fails midway.
    """
    data = work / "data"
    sock = None
    binary = None
    try:
        binary = _postgres_bindir()
        sock = _make_socket_dir(scratch_root)
        subprocess.run(
            [str(binary / "initdb"), "-D", str(data), "--encoding=UTF8", "--locale=C", "--auth=trust"],
            check=True,
            capture_output=True,
            timeout=60,
        )
        port = _start_server(binary, work, sock)
        conn = psycopg.connect(host=str(sock), port=port, dbname="postgres", autocommit=True, row_factory=dict_row)
        try:
            conn.execute("CREATE DATABASE v4_test_template")
            with psycopg.connect(
                make_conninfo(conn.info.dsn, dbname="v4_test_template"), autocommit=True, row_factory=dict_row
            ) as template:
                assert apply_pg_schema(template) == 6
            conn.execute("ALTER DATABASE v4_test_template ALLOW_CONNECTIONS false")
            yield conn
        finally:
            conn.close()
    finally:
        try:
            if binary is not None:
                _stop_server(binary, data)
        finally:
            if sock is not None:
                shutil.rmtree(sock, ignore_errors=True)
            shutil.rmtree(work, ignore_errors=True)


@pytest.fixture(scope="module")
def _pg_server(tmp_path_factory):
    """Keep one server and a closed, schema-applied template per module."""
    work = tmp_path_factory.mktemp("v4-pg")
    with _running_pg_server(_scratch_root(tmp_path_factory.getbasetemp()), work) as conn:
        yield conn


@pytest.fixture
def pg_cluster(_pg_server):
    """Give every test its own database, including connections opened via DSN."""
    database_name = "v4_test_" + uuid.uuid4().hex
    database = sql.Identifier(database_name)
    _pg_server.execute(sql.SQL("CREATE DATABASE {} TEMPLATE v4_test_template").format(database))
    try:
        with psycopg.connect(
            make_conninfo(_pg_server.info.dsn, dbname=database_name), autocommit=True, row_factory=dict_row
        ) as conn:
            yield conn
    finally:
        _pg_server.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(database))


def assert_authorized_request(conn, identifier, request_id):
    """Catch a foreign queue dequeue before the helper can claim or execute it."""
    assert identifier, f"no authorization for expected request {request_id}"
    row = conn.execute(
        "SELECT request_id FROM v4_operation_authorizations WHERE authorization_digest=%s",
        (digest(identifier.encode()),),
    ).fetchone()
    actual = row["request_id"] if row else None
    assert actual == request_id, f"authorization request mismatch: expected {request_id}, got {actual}"


@pytest.fixture
def prepared(pg_cluster, monkeypatch, tmp_path):
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", pg_cluster.info.dsn)
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    with RequestExecutor(root=tmp_path) as executor:
        request = executor.create_request(recipient="claude", body="source-free operation fixture")
        binding = executor.authorize_author_execution(
            request_id=request.request_id, slot_id="v4p-standard-correct-001", expected_seat="claude-sonnet-5"
        )
    with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
        semantic_inputs.freeze_semantic_input(
            conn,
            request_id=request.request_id,
            snapshot=stored_preparation(conn, request.request_id),
        )
        store = OperationStore(conn)
        policy = trust.load_production_trust_policy()[1]
        auth_principal = principal("authorize-" + request.request_id)
        raw = canonical_bytes({"schema": "hramatka-v4-operation-authorize.v1"})
        identifier = store.authorize(principal=auth_principal, raw=raw, policy_digest=policy)
        assert_authorized_request(conn, identifier, request.request_id)
    execution = canonical_bytes({"authorization_id": identifier, "schema": "hramatka-v4-operation-execute.v1"})
    return {
        "request_id": request.request_id,
        "binding": binding,
        "identifier": identifier,
        "raw": execution,
        "policy": policy,
        "principal": replace(auth_principal, jti="execute-" + request.request_id),
    }


@pytest.fixture(scope="module")
def built_wheel(tmp_path_factory, request):
    output = tmp_path_factory.mktemp("owned-wheel")
    # xdist workers share setuptools in-place build paths in this checkout.
    # Serialize wheel creation, while the behavioral tests remain parallel.
    lock_root = tmp_path_factory.getbasetemp()
    if hasattr(request.config, "workerinput"):
        lock_root = lock_root.parent
    lock_path = lock_root / "v4-runtime-build.lock"
    env = dict(os.environ)
    from learn_ukrainian_v4_runtime.provenance import verify_current_identity

    identity = verify_current_identity()
    env["LEARN_UKRAINIAN_V4_RUNTIME_COMMIT"] = identity["public_commit"]
    with lock_path.open("a") as build_lock:
        fcntl.flock(build_lock, fcntl.LOCK_EX)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--no-build-isolation",
                "packages/v4-runtime",
                "--wheel-dir",
                str(output),
            ],
            check=True,
            capture_output=True,
            timeout=120,
            env=env,
        )
    return next(output.glob("*.whl"))


@pytest.fixture
def signing_resources(tmp_path, monkeypatch):
    raw = json.dumps(TRUST_POLICY, sort_keys=True).encode()
    path = tmp_path / "policy.json"
    path.write_bytes(raw)
    monkeypatch.setattr(trust, "DEFAULT_TRUST_POLICY_PATH", path)
    monkeypatch.setattr(trust, "PRODUCTION_TRUST_POLICY_FILE_DIGEST_ALLOWLIST", frozenset({digest(raw)}))
    # The unit's credential namespace with systemd's flattened directory
    # credential names (v4-signing-keys_<role>.key[_id]), owner-private.
    namespace = tmp_path / "credentials"
    namespace.mkdir(mode=0o700)
    for role, private, key_id in [
        ("fleet_execution", FLEET_SIGNING_KEY_HEX, FLEET_KEY_ID),
        ("sources", SOURCES_SIGNING_KEY_HEX, SOURCES_KEY_ID),
        ("a3", A3_SIGNING_KEY_HEX, A3_KEY_ID),
    ]:
        for suffix, value in [(".key", private), (".key_id", key_id)]:
            key = namespace / (trust.SIGNING_KEY_CREDENTIAL + "_" + role + suffix)
            key.write_text(value)
            key.chmod(0o400)
    monkeypatch.setattr(trust, "HRAMATKA_CREDENTIAL_NAMESPACE", namespace)


@pytest.fixture(scope="module")
def isolated_install(built_wheel, tmp_path_factory):
    target = tmp_path_factory.mktemp("source-free-installed")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-compile",
            "--target",
            str(target),
            str(built_wheel),
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )
    return target


def _requirement_spec(requirement: str) -> tuple[str, set[str], Marker | None] | None:
    try:
        parsed = Requirement(requirement)
    except Exception:
        return None
    return parsed.name, set(parsed.extras), parsed.marker


def _marker_applies(marker: Marker | None, extras: set[str]) -> bool:
    if marker is None:
        return True
    environment = default_environment()
    if "extra" in str(marker):
        return any(marker.evaluate({**environment, "extra": extra}) for extra in extras)
    return marker.evaluate(environment)


@pytest.fixture(scope="module")
def external_dependencies(tmp_path_factory):
    """Stage only the wheel's declared dependency closure outside the checkout."""
    target = tmp_path_factory.mktemp("source-free-dependencies").resolve()
    assert not target.is_relative_to(_REPO_ROOT)
    package_metadata = tomllib.loads((_REPO_ROOT / "packages/v4-runtime/pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    distributions = {
        re.sub(r"[-_.]+", "-", dist.metadata["Name"]).lower(): dist
        for dist in importlib.metadata.distributions()
        if dist.metadata.get("Name")
    }
    pending = []
    for requirement in package_metadata["dependencies"]:
        spec = _requirement_spec(requirement)
        if spec is not None:
            name, extras, marker = spec
            if _marker_applies(marker, extras):
                pending.append((name, extras))
    selected = set()
    processed = set()
    while pending:
        name, extras = pending.pop()
        normalized = re.sub(r"[-_.]+", "-", name).lower()
        state = (normalized, tuple(sorted(extras)))
        if state in processed:
            continue
        processed.add(state)
        distribution = distributions.get(normalized)
        assert distribution is not None, f"declared runtime dependency is not installed: {name}"
        selected.add(normalized)
        for requirement in distribution.requires or ():
            spec = _requirement_spec(requirement)
            if spec is None:
                continue
            dependency, dependency_extras, marker = spec
            if not _marker_applies(marker, extras):
                continue
            pending.append((dependency, dependency_extras))

    for normalized in sorted(selected):
        distribution = distributions[normalized]
        for listed in distribution.files or ():
            relative = Path(str(listed))
            if relative.is_absolute() or ".." in relative.parts:
                continue
            source = Path(distribution.locate_file(listed))
            if not source.is_file():
                continue
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                assert destination.read_bytes() == source.read_bytes(), f"dependency collision: {relative}"
            else:
                shutil.copyfile(source, destination)
    return target
