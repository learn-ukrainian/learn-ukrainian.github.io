"""Authority diagnostics use bounded, read-only reads and opaque failure codes."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import psycopg
import pytest

from scripts.fleet_comms import message_plane, migrations, pg_schema
from scripts.fleet_comms.cli import _short_plane_health

pytestmark = pytest.mark.repo_invariant


@pytest.fixture(autouse=True)
def isolated_authority(monkeypatch, tmp_path):
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY", "sqlite")
    monkeypatch.delenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_CP_PG_DSN", raising=False)
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "authority")
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "absent"))


def seed_sqlite(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    target = root / "comms.sqlite3"
    with sqlite3.connect(target) as conn:
        migrations.apply_migrations(conn)
    return target


class PgRead:
    """Driver-boundary fixture: production resolver and probe remain real."""

    def __init__(self, rows=None, error=None):
        self.rows = rows if rows is not None else [(m.version, m.name, m.checksum) for m in pg_schema.MIGRATIONS]
        self.error = error
        self.statements = []
        self.closed = False

    def execute(self, sql, params=None):
        self.statements.append(sql)
        assert sql.startswith(("SELECT ", "SET "))
        if sql.startswith("SELECT ") and self.error:
            raise self.error
        return self

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[-1] if self.rows else None

    def close(self):
        self.closed = True


def install_pg(monkeypatch, conn):
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", "synthetic-driver-input")

    def connect(_dsn, **kwargs):
        assert kwargs["connect_timeout"] <= 3
        assert "default_transaction_read_only=on" in kwargs["options"]
        return conn

    monkeypatch.setattr(psycopg, "connect", connect)


def test_pg_plane_status_reads_pg_ledger_without_local_file(monkeypatch, tmp_path):
    conn = PgRead()
    install_pg(monkeypatch, conn)
    status = message_plane.read_plane_status(root=tmp_path / "absent")
    assert status["schema"].get("db_error") is None
    assert status["schema"]["authority"] == "pg"
    assert status["schema"]["db_exists"] is True
    assert status["schema"]["known_version"] == pg_schema.MIGRATIONS[-1].version
    assert status["store"]["reachable"] is True
    assert status["schema"]["store"] == status["store"]
    assert _short_plane_health(status)["healthy"] is True
    assert any("fleet_comms_pg_schema_migrations" in sql and "LIMIT" in sql for sql in conn.statements)
    assert any("statement_timeout" in sql for sql in conn.statements)
    assert conn.closed
    assert not (tmp_path / "absent").exists()


@pytest.mark.parametrize("authority", ["sqlite", "shadow"])
def test_file_authority_read_is_healthy_and_does_not_mutate(monkeypatch, tmp_path, authority):
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", authority)
    target = seed_sqlite(tmp_path)
    before = target.read_bytes()
    status = message_plane.read_plane_status(root=tmp_path)
    assert status["schema"]["authority"] == authority
    assert status["schema"]["db_exists"] is True
    assert status["store"]["reachable"] is True
    assert _short_plane_health(status)["healthy"] is True
    assert target.read_bytes() == before


@pytest.mark.parametrize("state", ["empty", "corrupt", "old", "future", "checksum"])
def test_existing_sqlite_file_is_not_proof_of_healthy_schema(tmp_path, state):
    target = seed_sqlite(tmp_path)
    if state == "corrupt":
        target.write_bytes(b"synthetic invalid database")
    else:
        with sqlite3.connect(target) as conn:
            if state == "empty":
                conn.execute("DELETE FROM comms_schema_migrations")
            elif state == "old":
                conn.execute(
                    "DELETE FROM comms_schema_migrations WHERE version = ?", (migrations.MIGRATIONS[-1].version,)
                )
            elif state == "future":
                conn.execute("UPDATE comms_schema_migrations SET version = 999 WHERE version = 1")
            else:
                conn.execute("UPDATE comms_schema_migrations SET checksum = 'synthetic-invalid'")
    before = target.read_bytes()
    status = message_plane.read_plane_status(root=tmp_path)
    assert status["schema"].get("db_error") is not None
    assert _short_plane_health(status)["healthy"] is False
    assert target.read_bytes() == before


def test_missing_pg_dsn_is_not_component_refusal_or_missing_sqlite(monkeypatch, tmp_path):
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    status = message_plane.read_plane_status(root=tmp_path / "absent")
    assert status["schema"]["db_error"] == "pg_dsn_missing"
    assert status["schema"]["db_exists"] is None
    assert _short_plane_health(status)["db_exists"] is None
    assert status["store"]["reachable"] is False
    assert _short_plane_health(status)["healthy"] is False
    assert not (tmp_path / "absent").exists()


@pytest.mark.parametrize("phase", ["connect", "query"])
@pytest.mark.parametrize(
    "failure", [psycopg.OperationalError, psycopg.errors.InvalidPassword, psycopg.errors.SyntaxError]
)
def test_pg_failures_are_opaque_in_payload_and_logs(monkeypatch, tmp_path, caplog, phase, failure):
    marker = "SYNTHETIC_PRIVATE_DRIVER_DETAIL"
    conn = PgRead(error=failure(marker))
    install_pg(monkeypatch, conn)
    if phase == "connect":

        def fail(*args, **kwargs):
            raise failure(marker)

        monkeypatch.setattr(psycopg, "connect", fail)
    status = message_plane.read_plane_status(root=tmp_path)
    assert status["schema"]["db_error"] == "pg_probe_failed"
    assert status["store"]["reachable"] is False
    assert _short_plane_health(status)["healthy"] is False
    assert marker not in json.dumps(status) + caplog.text
    assert "Traceback" not in caplog.text
    if phase == "query":
        assert conn.closed


@pytest.mark.parametrize("state", ["empty", "old", "future", "checksum", "missing_table"])
def test_pg_schema_failures_are_explicit(monkeypatch, tmp_path, state):
    conn = PgRead()
    if state == "empty":
        conn.rows = []
    elif state == "old":
        conn.rows.pop()
    elif state == "future":
        conn.rows.append((999, "synthetic-future", "synthetic-checksum"))
    elif state == "checksum":
        conn.rows[0] = (1, conn.rows[0][1], "synthetic-invalid")
    else:
        conn.error = psycopg.errors.UndefinedTable("SYNTHETIC_PRIVATE_DRIVER_DETAIL")
    install_pg(monkeypatch, conn)
    status = message_plane.read_plane_status(root=tmp_path)
    assert status["schema"].get("db_error") in {"schema_incompatible", "schema_read_failed"}
    assert _short_plane_health(status)["healthy"] is False
    assert conn.closed


def test_pg_never_stats_or_opens_local_sqlite(monkeypatch, tmp_path):
    conn = PgRead()
    install_pg(monkeypatch, conn)
    original = Path.is_file

    def is_file(path):
        assert path.name != "comms.sqlite3", "PG diagnostics must not inspect a SQLite file"
        return original(path)

    monkeypatch.setattr(Path, "is_file", is_file)
    monkeypatch.setattr(sqlite3, "connect", lambda *a, **kw: pytest.fail("SQLite fallback attempted"))
    assert message_plane.read_plane_status(root=tmp_path)["store"]["reachable"] is True


def test_unsupported_probe_is_not_database_absence(monkeypatch, tmp_path):
    from scripts.control_plane.storage import COMPONENT_AUTHORITIES, Authority

    conn = PgRead()
    install_pg(monkeypatch, conn)
    monkeypatch.setitem(COMPONENT_AUTHORITIES, "plane_status", frozenset({Authority.SQLITE}))
    status = message_plane.read_plane_status(root=tmp_path)
    assert status["schema"]["db_error"] == "authority_unsupported_component"
    assert status["schema"]["db_exists"] is None
    assert status["store"]["reachable"] is None
    assert _short_plane_health(status)["db_exists"] is None
    assert not conn.statements


@pytest.mark.parametrize("command", ["metrics", "backlog", "dead-letters"])
@pytest.mark.parametrize("outcome", ["success", "connect_failure", "query_failure", "missing_dsn"])
def test_pg_sibling_cli_and_facade_collectors_agree(monkeypatch, tmp_path, capsys, command, outcome):
    from scripts.api import fleet_router
    from scripts.api.monitor_context import fixture_context
    from scripts.control_plane.storage import ControlPlanePgConnectError, ControlPlanePgDsnMissingError
    from scripts.fleet_comms import cli
    from scripts.fleet_comms.efficiency_metrics import EfficiencyMetricsReadError

    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    names = {
        "metrics": ("collect_efficiency_metrics_authority", "_facade_authority_payload"),
        "backlog": ("collect_delivery_backlog_authority", "_facade_backlog_payload"),
        "dead-letters": ("collect_dead_letters_authority", "_facade_dead_letters_payload"),
    }
    called = []

    def collector(path, **kwargs):
        called.append(path)
        if outcome != "success":
            errors = {
                "connect_failure": ControlPlanePgConnectError,
                "query_failure": EfficiencyMetricsReadError,
                "missing_dsn": ControlPlanePgDsnMissingError,
            }
            raise errors[outcome]("SYNTHETIC_PRIVATE_DRIVER_DETAIL")
        return {"total": 0}

    name, facade_name = names[command]
    monkeypatch.setattr(cli, name, collector)
    monkeypatch.setattr(fleet_router, name, collector)
    assert cli.main([command, "--root", str(tmp_path / "absent")]) == cli.EXIT_OK
    cli_result = json.loads(capsys.readouterr().out)
    facade = getattr(fleet_router, facade_name)
    ctx = fixture_context(tmp_path)
    api_result = facade(collector, ctx) if command == "metrics" else facade(10, ctx)
    assert len(called) == 2
    for payload in (cli_result, api_result):
        assert payload["authority"] == "pg"
        assert payload["store"]["reachable"] is (outcome == "success")
        assert not payload.get("db_missing")
        assert "SYNTHETIC_PRIVATE_DRIVER_DETAIL" not in json.dumps(payload)
        if outcome != "success":
            assert (
                payload["db_error"]
                == {
                    "connect_failure": "pg_probe_failed",
                    "query_failure": "schema_read_failed",
                    "missing_dsn": "pg_dsn_missing",
                }[outcome]
            )
    assert not (tmp_path / "absent").exists()


@pytest.mark.parametrize("phase", ["missing_dsn", "connect", "query"])
def test_api_and_cli_status_fail_closed_without_driver_details(monkeypatch, tmp_path, capsys, caplog, phase):
    from dataclasses import replace

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from scripts.api import fleet_router
    from scripts.api.monitor_context import fixture_context
    from scripts.fleet_comms import cli, fleet_overview

    marker = "SYNTHETIC_PRIVATE_DRIVER_DETAIL"
    install_pg(monkeypatch, PgRead(error=psycopg.errors.SyntaxError(marker)))
    expected = "pg_probe_failed"
    if phase == "missing_dsn":
        monkeypatch.delenv("LEARN_UKRAINIAN_CP_PG_DSN")
        expected = "pg_dsn_missing"
    elif phase == "connect":

        def fail(*args, **kwargs):
            raise psycopg.OperationalError(marker)

        monkeypatch.setattr(psycopg, "connect", fail)

    ctx = fixture_context(tmp_path)
    ctx = replace(ctx, stores=replace(ctx.stores, epics_store=None))
    app = FastAPI()
    app.state.ctx = ctx
    app.include_router(fleet_router.router, prefix="/api/fleet")
    monkeypatch.setattr(fleet_router, "recent_runtime_records", lambda **kwargs: {"records": []})
    with TestClient(app) as client:
        health = client.get("/api/fleet/health").json()
        overview = client.get("/api/fleet/overview").json()
        facade = client.get("/api/fleet/facade/status").json()
    assert health["ok"] is False
    assert facade["health"]["healthy"] is False
    monkeypatch.setattr(fleet_overview, "build_fleet_overview", lambda **kwargs: {"available": False})
    assert cli.main(["fleet", "status", "--root", str(tmp_path / "absent")]) == cli.EXIT_OK
    captured = capsys.readouterr()
    cli_result = json.loads(captured.out)
    assert cli_result["health"]["healthy"] is False
    for status in (health, overview["health"], facade["plane_status"], cli_result["plane_status"]):
        assert status["schema"]["db_error"] == expected
        assert status["store"]["reachable"] is False
        assert status["schema"]["store"]["reachable"] is False
        assert "authority_unsupported_component" not in json.dumps(status)
    public_output = json.dumps([health, overview, facade, cli_result]) + captured.err + caplog.text
    assert marker not in public_output
    assert "Traceback" not in public_output
