"""Isolated real-adapter proof; never uses an ambient database or connection string."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo

from scripts.api import fleet_router
from scripts.api.monitor_context import fixture_context
from scripts.control_plane import storage
from scripts.fleet_comms import pg_schema
from scripts.fleet_comms.cli import _short_plane_health
from scripts.fleet_comms.message_plane import read_plane_status
from tests.epics_monitor_stub import epics_monitor_stub

pytestmark = pytest.mark.repo_invariant


def _fixture_command(args, log=None):
    result = subprocess.run(args, capture_output=True, timeout=30)
    if result.returncode:
        detail = log.read_text() if log and log.exists() else result.stderr.decode(errors="replace")
        for reason in ("too long", "Permission denied", "No such file", "syntax error", "Address already in use"):
            if reason in detail:
                pytest.fail(f"Isolated fixture error category: {reason}", pytrace=False)
        pytest.fail(f"Isolated {Path(args[0]).name} fixture command failed (output withheld)", pytrace=False)


@pytest.fixture
def isolated_pg(tmp_path, monkeypatch):
    """Seed only a fresh socket-only cluster, then grant the probe SELECT only."""
    binary = shutil.which("initdb")
    if binary is None:
        candidates = sorted(Path("/usr/lib/postgresql").glob("*/bin/initdb"))
        binary = str(candidates[-1]) if candidates else None
    if binary is None or os.geteuid() == 0 or sys.platform != "linux":
        pytest.skip("Isolated PostgreSQL proof requires Linux, binaries, and an unprivileged user")
    bindir = Path(binary).parent
    data = tmp_path / "cluster"
    # Socket paths must stay short even when pytest uses a long worktree root.
    socket_directory = tempfile.TemporaryDirectory(prefix="cp-health-", dir="/tmp")
    sockets = socket_directory.name
    log = tmp_path / "fixture.log"
    _fixture_command(
        [str(bindir / "initdb"), "-D", str(data), "-A", "trust", "-U", "fixture", "--no-locale", "--encoding=UTF8"]
    )
    _fixture_command(
        [
            str(bindir / "pg_ctl"),
            "-D",
            str(data),
            "-l",
            str(log),
            "-o",
            f"-F -k {sockets} -c listen_addresses='' -c log_statement=all",
            "-w",
            "start",
        ],
        log=log,
    )
    try:
        # These writes seed the disposable fixture. Every production probe
        # below uses a different role, without any write or DDL privilege.
        with psycopg.connect(
            make_conninfo(host=str(sockets), dbname="postgres", user="fixture"), autocommit=True
        ) as conn:
            pg_schema.apply_pg_schema(conn)
            conn.execute(
                "CREATE TABLE authority_jobs (job_id TEXT, job_kind TEXT, state TEXT, updated_at TEXT, deadline_at TEXT)"
            )
            conn.execute(
                "CREATE TABLE authority_deliveries (delivery_id TEXT, message_id TEXT, recipient TEXT, state TEXT, attempt_count INTEGER, created_at TEXT, updated_at TEXT, completed_at TEXT)"
            )
            conn.execute(
                "CREATE TABLE authority_dead_letters (dead_letter_id TEXT, delivery_id TEXT, job_id TEXT, reason_code TEXT, created_at TEXT)"
            )
            conn.execute("CREATE ROLE health_reader LOGIN")
            conn.execute("GRANT USAGE ON SCHEMA public TO health_reader")
            conn.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO health_reader")
        monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY", "sqlite")
        monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
        monkeypatch.setenv(
            "LEARN_UKRAINIAN_CP_PG_DSN", make_conninfo(host=str(sockets), dbname="postgres", user="health_reader")
        )
        root = tmp_path / "absent-plane"
        monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))
        monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "authority")
        monkeypatch.setenv("FLEET_COMMS_PLANE_TELEMETRY", str(root / "absent-telemetry"))
        yield root, log
    except psycopg.Error:
        raise RuntimeError("Isolated PostgreSQL adapter failure (driver output withheld)") from None
    finally:
        _fixture_command([str(bindir / "pg_ctl"), "-D", str(data), "-m", "immediate", "-w", "stop"])
        socket_directory.cleanup()


def test_real_pg_adapter_api_and_cli_agree_without_sqlite(isolated_pg, tmp_path, monkeypatch):
    root, log = isolated_pg
    offset = log.stat().st_size
    conn = storage.connect(storage.StoreId.FLEET_COMMS, read_only=True)
    try:
        assert conn.execute("SHOW transaction_read_only").fetchone()[0] == "on"
    finally:
        conn.close()

    status = read_plane_status(root=root)
    assert status["authority"] == "pg"
    assert status["schema"]["db_exists"] is True
    assert status["store"]["reachable"] is True
    assert _short_plane_health(status)["healthy"] is True

    app = FastAPI()
    ctx = fixture_context(tmp_path / "monitor")
    ctx = replace(ctx, stores=replace(ctx.stores, epics_store=None))
    app.state.ctx = ctx
    app.include_router(fleet_router.router, prefix="/api/fleet")
    monkeypatch.setattr(fleet_router, "recent_runtime_records", lambda **kwargs: {"records": []})
    with TestClient(app) as client:
        health = client.get("/api/fleet/health").json()
        overview = client.get("/api/fleet/overview").json()
        facade = client.get("/api/fleet/facade/status").json()
        for projected in (health, overview["health"], facade["plane_status"]):
            assert projected["schema"]["authority"] == "pg"
            assert projected["store"] == status["store"]
            assert not projected["schema"].get("db_error")
        assert health["ok"] is True
        assert health["authority_health"]["state"] == "idle"
        assert overview["availability"] == "empty"
        assert facade["health"]["healthy"] is True
        for suffix in ("metrics", "backlog", "dead"):
            payload = client.get(f"/api/fleet/facade/{suffix}").json()
            assert payload["authority"] == "pg"
            assert payload["store"]["reachable"] is True
            assert not payload.get("db_missing")
            assert not payload.get("db_error")
        # A detail component not ported to PG is explicitly unsupported.
        legacy = client.get("/api/fleet/requests").json()
        assert legacy["availability"] == "authority_unsupported_component"

    # The overview stub owns a separate synthetic session store.
    from agents_extensions.shared.session_streams.db import SessionStreamDatabase
    from agents_extensions.shared.session_streams.store import SessionStreamStore

    database = SessionStreamDatabase(tmp_path / "epics" / "sessions.sqlite3")
    database.connect().close()
    with epics_monitor_stub(SessionStreamStore(database)) as monitor:
        for args in (
            ["plane-status"],
            ["fleet", "status", "--monitor-url", monitor],
            ["metrics"],
            ["backlog"],
            ["dead-letters"],
        ):
            result = subprocess.run(
                [sys.executable, "-m", "scripts.fleet_comms", *args, "--root", str(root)],
                capture_output=True,
                text=True,
                timeout=20,
                env=os.environ.copy(),
            )
            assert result.returncode == 0
            assert result.stderr == ""
            payload = json.loads(result.stdout)
            if args[0] == "fleet":
                assert payload["health"]["healthy"] is True
                payload = payload["plane_status"]
            assert payload["store"]["reachable"] is True
            assert payload["authority"] == "pg"
            assert not payload.get("db_missing")
            assert not payload.get("db_error")

        configured = os.environ["LEARN_UKRAINIAN_CP_PG_DSN"]
        for reason in ("pg_dsn_missing", "pg_probe_failed"):
            with monkeypatch.context() as environment:
                if reason == "pg_dsn_missing":
                    environment.delenv("LEARN_UKRAINIAN_CP_PG_DSN")
                else:
                    environment.setenv(
                        "LEARN_UKRAINIAN_CP_PG_DSN", make_conninfo(configured, user="no_such_fixture_role")
                    )
                with TestClient(app) as client:
                    payload = client.get("/api/fleet/health").json()
                    assert payload["ok"] is False
                    assert payload["schema"]["db_error"] == reason
                    assert payload["store"]["reachable"] is False
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "scripts.fleet_comms",
                        "fleet",
                        "status",
                        "--root",
                        str(root),
                        "--monitor-url",
                        monitor,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    env=os.environ.copy(),
                )
                assert result.returncode == 0
                assert result.stderr == ""
                payload = json.loads(result.stdout)
                assert payload["health"]["healthy"] is False
                assert payload["plane_status"]["schema"]["db_error"] == reason
                assert "no_such_fixture_role" not in result.stdout
                assert configured not in result.stdout

    assert not root.exists()
    # Only inspect statements emitted after fixture setup. Do not print logs.
    statements = log.read_text()[offset:].upper()
    for forbidden in ("CREATE TABLE", "INSERT INTO", "UPDATE ", "DELETE FROM", "ALTER TABLE"):
        assert forbidden not in statements
    assert "FLEET_COMMS_PG_SCHEMA_MIGRATIONS" in statements
