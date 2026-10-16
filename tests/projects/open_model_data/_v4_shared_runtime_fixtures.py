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
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
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
_PG_KILL_WAIT_SECONDS = 10
_ISSUED_PORTS: set[int] = set()


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
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _stop_server(binary: Path, data: Path) -> None:
    """Stop the server in ``data`` if one runs; kill it when ``pg_ctl`` cannot."""
    pid = _postmaster_pid(data)
    if pid is None:
        return
    try:
        stopped = (
            subprocess.run(
                [str(binary / "pg_ctl"), "-D", str(data), "-m", "immediate", "-w", "-t", "30", "stop"],
                check=False,
                capture_output=True,
                timeout=45,
            ).returncode
            == 0
        )
    except subprocess.TimeoutExpired:
        stopped = False
    if stopped:
        return
    with contextlib.suppress(ProcessLookupError):
        os.kill(pid, signal.SIGKILL)
    deadline = time.monotonic() + _PG_KILL_WAIT_SECONDS
    while _process_alive(pid):
        if time.monotonic() > deadline:
            raise RuntimeError(f"PostgreSQL server {pid} survived pg_ctl stop and SIGKILL")
        time.sleep(0.05)


def _start_server(binary: Path, data: Path, log: Path, sock: Path) -> int:
    """Start the server on a fresh port, retrying on another port; return the port."""
    attempted = []
    for _ in range(_PG_START_ATTEMPTS):
        port = _free_tcp_port()
        attempted.append(port)
        started = subprocess.run(
            [
                str(binary / "pg_ctl"),
                "-D",
                str(data),
                "-l",
                str(log),
                "-o",
                f'-k {sock} -h "" -p {port}',
                "-w",
                "start",
            ],
            check=False,
            capture_output=True,
            timeout=60,
        )
        if started.returncode == 0:
            return port
        _stop_server(binary, data)
    tail = log.read_text(errors="replace")[-2000:] if log.exists() else ""
    raise RuntimeError(f"PostgreSQL did not start on ports {attempted}; server log tail:\n{tail}")


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
        port = _start_server(binary, data, work / "server.log", sock)
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
