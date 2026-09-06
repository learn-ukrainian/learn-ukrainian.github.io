"""WP-C: authority-aware metrics/backlog/dead-letters (cold-start-opt PR-3)."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.fleet_comms.cli import EXIT_OK
from scripts.fleet_comms.cli import main as cli_main
from scripts.fleet_comms.efficiency_metrics import (
    collect_dead_letters,
    collect_dead_letters_authority,
    collect_delivery_backlog,
    collect_delivery_backlog_authority,
    collect_efficiency_metrics,
    collect_efficiency_metrics_authority,
    resolve_metrics_source,
)
from scripts.fleet_comms.opsec_store import COMMS_RESPONSE_SCHEMA_VERSION


def _seed_broker(db: Path) -> None:
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE deliveries (
          delivery_id TEXT PRIMARY KEY,
          message_id TEXT,
          to_agent TEXT,
          status TEXT,
          attempt_count INTEGER DEFAULT 0,
          dispatched_at TEXT,
          delivered_at TEXT
        );
        CREATE TABLE dead_letters (
          dead_letter_id TEXT PRIMARY KEY,
          request_id TEXT,
          delivery_id TEXT,
          reason TEXT NOT NULL,
          successor TEXT,
          original_expires_at TEXT,
          created_at TEXT NOT NULL
        );
        INSERT INTO deliveries VALUES
          ('broker-d1','m1','claude','pending',0,NULL,NULL),
          ('broker-d2','m2','codex','dispatched',1,'2026-08-01T10:00:00',NULL);
        INSERT INTO dead_letters VALUES
          ('broker-dl1',NULL,'broker-d9','recipient_retired','agy',NULL,'2026-08-01T09:00:00');
        """
    )
    conn.commit()
    conn.close()


def _seed_authority_plane(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    plane_db = root / "comms.sqlite3"
    conn = sqlite3.connect(plane_db)
    conn.executescript(
        """
        CREATE TABLE authority_deliveries (
          delivery_id TEXT PRIMARY KEY,
          message_id TEXT NOT NULL,
          recipient TEXT NOT NULL,
          state TEXT NOT NULL,
          deadline_at TEXT,
          lease_owner TEXT,
          lease_expires_at TEXT,
          fence_token INTEGER NOT NULL DEFAULT 0,
          attempt_count INTEGER NOT NULL DEFAULT 0,
          acknowledgment_artifact_id TEXT,
          terminal_sha256 TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          completed_at TEXT
        );
        CREATE TABLE authority_dead_letters (
          dead_letter_id TEXT PRIMARY KEY,
          delivery_id TEXT UNIQUE,
          job_id TEXT UNIQUE,
          reason_code TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE authority_jobs (
          job_id TEXT PRIMARY KEY,
          job_kind TEXT NOT NULL,
          subject_id TEXT NOT NULL,
          payload_artifact_id TEXT NOT NULL,
          state TEXT NOT NULL,
          deadline_at TEXT,
          lease_owner TEXT,
          lease_expires_at TEXT,
          fence_token INTEGER NOT NULL DEFAULT 0,
          attempt_count INTEGER NOT NULL DEFAULT 0,
          result_artifact_id TEXT,
          terminal_sha256 TEXT,
          idempotency_key TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          completed_at TEXT
        );
        INSERT INTO authority_deliveries VALUES
          ('auth-d1','auth-m1','claude','queued',NULL,NULL,NULL,0,0,NULL,NULL,
           '2026-08-01T12:00:00Z','2026-08-01T12:00:00Z',NULL),
          ('auth-d2','auth-m2','codex','running',NULL,'worker',NULL,1,1,NULL,NULL,
           '2026-08-01T12:01:00Z','2026-08-01T12:02:00Z',NULL),
          ('auth-d3','auth-m3','gemini','queued',NULL,NULL,NULL,0,0,NULL,NULL,
           '2026-08-01T12:03:00Z','2026-08-01T12:03:00Z',NULL),
          ('auth-d4','auth-m4','agy','acknowledged',NULL,NULL,NULL,0,1,NULL,'sha',
           '2026-08-01T11:00:00Z','2026-08-01T11:05:00Z','2026-08-01T11:05:00Z');
        INSERT INTO authority_dead_letters VALUES
          ('auth-dl1','auth-d4',NULL,'attempts_exhausted','2026-08-01T11:06:00Z');
        INSERT INTO authority_jobs VALUES
          ('auth-j1','request','auth-m1','art1','queued',NULL,NULL,NULL,0,0,NULL,NULL,'k1',
           '2026-08-01T12:00:00Z','2026-08-01T12:00:00Z',NULL);
        """
    )
    conn.commit()
    conn.close()
    return plane_db


def _run_cli(argv: list[str], capsys) -> dict:
    code = cli_main(argv)
    assert code == EXIT_OK
    captured = capsys.readouterr()
    return json.loads(captured.out)


def test_resolve_metrics_source_labels(monkeypatch) -> None:
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "authority")
    assert resolve_metrics_source() == "authority"
    assert resolve_metrics_source(force_legacy=True) == "legacy_forced"
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "off")
    assert resolve_metrics_source() == "legacy"
    assert resolve_metrics_source(force_legacy=True) == "legacy_forced"


def test_backlog_defaults_authority_when_plane_authority(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    plane_root = tmp_path / "plane"
    plane_db = _seed_authority_plane(plane_root)
    broker = tmp_path / "broker.db"
    _seed_broker(broker)
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "authority")

    payload = _run_cli(
        ["backlog", "--root", str(plane_root), "--db", str(broker)],
        capsys,
    )
    assert payload["source"] == "authority"
    assert payload["response_schema_version"] == COMMS_RESPONSE_SCHEMA_VERSION
    assert payload["store"] == {"kind": "comms-plane", "reachable": True}
    assert "db_path" not in payload
    assert payload["total"] == 2
    assert payload["by_agent"] == {"claude": 1, "codex": 1}
    assert payload["by_status"] == {"queued": 1, "running": 1}
    assert "gemini" not in payload["by_agent"]

    direct = collect_delivery_backlog_authority(plane_db, exclude_retired=True)
    assert direct["total"] == 2

    metrics = _run_cli(
        ["metrics", "--root", str(plane_root), "--db", str(broker)],
        capsys,
    )
    assert metrics["source"] == "authority"
    assert metrics["store"]["kind"] == "comms-plane"
    assert metrics["response_schema_version"] == COMMS_RESPONSE_SCHEMA_VERSION
    assert "db_path" not in metrics
    assert metrics["deliveries"]["queued"] == 2
    assert metrics["dead_letters"] == 1
    assert metrics["jobs"]["queued"] == 1

    dead = _run_cli(
        ["dead-letters", "--root", str(plane_root), "--db", str(broker)],
        capsys,
    )
    assert dead["source"] == "authority"
    assert dead["store"]["kind"] == "comms-plane"
    assert "db_path" not in dead
    assert dead["total"] == 1
    assert dead["by_reason"]["attempts_exhausted"] == 1


def test_backlog_legacy_flag_forces_broker(tmp_path: Path, capsys, monkeypatch) -> None:
    plane_root = tmp_path / "plane"
    _seed_authority_plane(plane_root)
    broker = tmp_path / "broker.db"
    _seed_broker(broker)
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "authority")

    payload = _run_cli(
        ["backlog", "--legacy", "--root", str(plane_root), "--db", str(broker)],
        capsys,
    )
    assert payload["source"] == "legacy_forced"
    assert payload["store"] == {"kind": "legacy-broker", "reachable": True}
    assert "db_path" not in payload
    assert payload["total"] == 2
    assert payload["by_agent"] == {"claude": 1, "codex": 1}
    assert payload["by_status"]["pending"] == 1
    assert payload["by_status"]["dispatched"] == 1

    dead = _run_cli(
        ["dead-letters", "--legacy", "--db", str(broker), "--root", str(plane_root)],
        capsys,
    )
    assert dead["source"] == "legacy_forced"
    assert dead["store"]["kind"] == "legacy-broker"
    assert "db_path" not in dead
    assert dead["by_reason"]["recipient_retired"] == 1


def test_backlog_unchanged_when_mode_off(tmp_path: Path, capsys, monkeypatch) -> None:
    """Non-authority modes keep legacy collector shape; source is additive only."""
    plane_root = tmp_path / "plane"
    _seed_authority_plane(plane_root)
    broker = tmp_path / "broker.db"
    _seed_broker(broker)
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "off")

    baseline = collect_delivery_backlog(broker, exclude_retired=True)
    payload = _run_cli(
        ["backlog", "--db", str(broker), "--root", str(plane_root)],
        capsys,
    )
    assert payload["source"] == "legacy"
    stripped = {
        k: v
        for k, v in payload.items()
        if k not in {"source", "store", "response_schema_version", "content_included"}
    }
    # CLI adds store/content_included/source; collector keys must match baseline.
    for key, value in baseline.items():
        assert stripped[key] == value

    metrics_baseline = collect_efficiency_metrics(broker)
    metrics = _run_cli(["metrics", "--db", str(broker)], capsys)
    assert metrics["source"] == "legacy"
    assert metrics["store"]["kind"] == "legacy-broker"
    assert "db_path" not in metrics
    for key, value in metrics_baseline.items():
        assert metrics[key] == value

    dead_baseline = collect_dead_letters(broker)
    dead = _run_cli(["dead-letters", "--db", str(broker)], capsys)
    assert dead["source"] == "legacy"
    assert dead["store"]["kind"] == "legacy-broker"
    assert "db_path" not in dead
    for key, value in dead_baseline.items():
        assert dead[key] == value


def test_authority_collectors_are_read_only(tmp_path: Path) -> None:
    plane_db = _seed_authority_plane(tmp_path / "plane")
    with patch("sqlite3.connect", wraps=sqlite3.connect) as connect:
        collect_delivery_backlog_authority(plane_db)
        assert connect.called
        uri = connect.call_args.args[0]
        assert isinstance(uri, str)
        assert uri.startswith("file:")
        assert "mode=ro" in uri
        assert connect.call_args.kwargs.get("uri") is True


_AUTHORITY_COLLECTORS = (
    collect_delivery_backlog_authority,
    collect_dead_letters_authority,
    collect_efficiency_metrics_authority,
)


@pytest.fixture(params=["sqlite", "shadow", pytest.param("pg", marks=pytest.mark.postgres)])
def authority_db(request, tmp_path, monkeypatch):
    """Identical TEXT timestamp fixtures in sqlite and an isolated real pg schema."""
    engine = request.param
    dsn = (os.environ.get("LEARN_UKRAINIAN_CP_PG_DSN") or "").strip()
    if engine == "pg" and not dsn:
        pytest.skip("LEARN_UKRAINIAN_CP_PG_DSN unset/empty — Postgres tests skipped")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", engine)
    plane_db = _seed_authority_plane(tmp_path / "seed")
    seed = sqlite3.connect(plane_db)
    if engine != "pg":
        try:
            yield plane_db, seed
        finally:
            seed.close()
        return

    import psycopg
    from psycopg import sql

    import scripts.fleet_comms.efficiency_metrics as metrics_mod

    schema = sql.Identifier(f"metrics_{uuid.uuid4().hex}")
    with psycopg.connect(dsn, autocommit=True) as writer:
        writer.execute(sql.SQL("CREATE SCHEMA {}").format(schema))
        try:
            writer.execute(sql.SQL("SET search_path TO {}").format(schema))
            for name, ddl in seed.execute("SELECT name, sql FROM sqlite_master WHERE type='table'"):
                writer.execute(ddl)
                rows = seed.execute(f"SELECT * FROM {name}").fetchall()
                if rows:
                    with writer.cursor() as cursor:
                        cursor.executemany(
                            sql.SQL("INSERT INTO {} VALUES ({})").format(
                                sql.Identifier(name),
                                sql.SQL(",").join(sql.Placeholder() for _ in rows[0]),
                            ),
                            rows,
                        )
            real_connect = metrics_mod.cp_connect

            def scoped_connect(*args, **kwargs):
                conn = real_connect(*args, **kwargs)
                conn.autocommit = True
                conn.execute(sql.SQL("SET search_path TO {}").format(schema))
                # The collector must interpret naive sqlite timestamps as UTC.
                conn.execute("SET TIME ZONE 'Pacific/Honolulu'")
                return conn

            monkeypatch.setattr(metrics_mod, "cp_connect", scoped_connect)
            yield tmp_path / "absent" / "comms.sqlite3", writer
        finally:
            seed.close()
            writer.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(schema))


def test_authority_metrics_engine_parity(authority_db):
    plane_db, _ = authority_db
    metrics = collect_efficiency_metrics_authority(plane_db)
    assert metrics == {
        "content_included": False,
        "deliveries": {"queued": 2, "running": 1, "acknowledged": 1},
        "jobs": {"queued": 1},
        "dead_letters": 1,
        "latency_seconds": {
            "delivery_created_to_done": {"n": 1, "avg": 300.0, "min": 300.0, "max": 300.0},
        },
        "retired_endpoint_pending": {"gemini": 1},
    }
    backlog = collect_delivery_backlog_authority(plane_db)
    assert backlog["total"] == 2
    assert backlog["by_agent"] == {"codex": 1, "claude": 1}
    assert backlog["by_status"] == {"running": 1, "queued": 1}
    assert backlog["rows"] == [
        {"delivery_id": "auth-d2", "message_id": "auth-m2", "to_agent": "codex",
         "status": "running", "attempt_count": 1, "dispatched_at": "2026-08-01T12:02:00Z"},
        {"delivery_id": "auth-d1", "message_id": "auth-m1", "to_agent": "claude",
         "status": "queued", "attempt_count": 0, "dispatched_at": "2026-08-01T12:00:00Z"},
    ]
    assert backlog["exclude_retired"] == ["gemini"]
    all_backlog = collect_delivery_backlog_authority(plane_db, exclude_retired=False, limit=1)
    assert all_backlog["total"] == 1
    assert all_backlog["by_agent"] == {"gemini": 1}
    assert all_backlog["exclude_retired"] == []
    assert collect_delivery_backlog_authority(plane_db, limit=0)["rows"] == []
    dead = collect_dead_letters_authority(plane_db)
    assert dead == {
        "total": 1, "by_reason": {"attempts_exhausted": 1},
        "rows": [{"dead_letter_id": "auth-dl1", "delivery_id": "auth-d4", "job_id": None,
                  "reason": "attempts_exhausted", "reason_code": "attempts_exhausted",
                  "created_at": "2026-08-01T11:06:00Z"}],
    }
    limited_dead = collect_dead_letters_authority(plane_db, limit=0)
    assert limited_dead == {**dead, "rows": []}


def test_authority_latency_offsets_fractional_and_incomplete(authority_db):
    plane_db, writer = authority_db
    writer.execute(
        "UPDATE authority_deliveries SET created_at = '2026-08-01T11:00:00', "
        "completed_at = '2026-08-01T13:00:01.250+02:00' WHERE delivery_id = 'auth-d4'"
    )
    writer.execute(
        "UPDATE authority_deliveries SET completed_at = '2026-08-01T12:00:02.750Z' "
        "WHERE delivery_id = 'auth-d1'"
    )
    writer.execute("UPDATE authority_deliveries SET completed_at = '' WHERE delivery_id = 'auth-d2'")
    writer.commit()
    metrics = collect_efficiency_metrics_authority(plane_db)
    assert metrics["latency_seconds"]["delivery_created_to_done"] == {
        "n": 2, "avg": 2.0, "min": 1.25, "max": 2.75,
    }


def test_authority_no_completed_latency(authority_db):
    plane_db, writer = authority_db
    writer.execute("UPDATE authority_deliveries SET completed_at = NULL")
    writer.commit()
    assert collect_efficiency_metrics_authority(plane_db)["latency_seconds"] == {}


def test_authority_connections_are_readonly_and_closed(authority_db):
    from scripts.fleet_comms.efficiency_metrics import EfficiencyMetricsReadError, _connect_ro

    plane_db, _ = authority_db
    with pytest.raises((sqlite3.OperationalError, EfficiencyMetricsReadError)):
        with _connect_ro(plane_db) as conn:
            conn.execute("DELETE FROM authority_deliveries")
    if isinstance(conn, sqlite3.Connection):
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")
    else:
        assert conn.closed
    assert collect_efficiency_metrics_authority(plane_db)["deliveries"]["queued"] == 2


@pytest.mark.parametrize("collector", _AUTHORITY_COLLECTORS)
@pytest.mark.parametrize("local_file", [False, True])
def test_pg_missing_dsn_never_returns_stale_or_empty_sqlite(
    collector, local_file, tmp_path, monkeypatch,
):
    from scripts.control_plane.storage import ControlPlanePgDsnMissingError

    plane_db = _seed_authority_plane(tmp_path / "plane") if local_file else tmp_path / "missing.db"
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    monkeypatch.delenv("LEARN_UKRAINIAN_CP_PG_DSN", raising=False)
    with patch("sqlite3.connect", side_effect=AssertionError("sqlite fallback")):
        with pytest.raises(ControlPlanePgDsnMissingError):
            collector(plane_db)
    assert plane_db.exists() is local_file


@pytest.mark.parametrize("collector", _AUTHORITY_COLLECTORS)
def test_pg_query_errors_are_typed_and_redacted(collector, tmp_path, monkeypatch):
    import psycopg

    import scripts.fleet_comms.efficiency_metrics as metrics_mod

    class BrokenConnection:
        closed = False

        def execute(self, query, params=()):
            if query.startswith("SET TIME ZONE"):
                return None
            raise psycopg.errors.UndefinedColumn("private query/driver details")

        def close(self):
            self.closed = True

    conn = BrokenConnection()
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    monkeypatch.setattr(metrics_mod, "cp_connect", lambda *args, **kwargs: conn)
    with pytest.raises(metrics_mod.EfficiencyMetricsReadError) as exc:
        collector(tmp_path / "absent.db")
    assert str(exc.value) == "control-plane store 'fleet_comms' metrics read failed"
    assert conn.closed


def test_sqlite_missing_authority_file_stays_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "sqlite")
    plane_db = tmp_path / "missing.db"
    assert collect_delivery_backlog_authority(plane_db)["total"] == 0
    assert collect_dead_letters_authority(plane_db)["total"] == 0
    assert collect_efficiency_metrics_authority(plane_db)["deliveries"] == {}
    assert not plane_db.exists()


@pytest.mark.parametrize("collector", _AUTHORITY_COLLECTORS)
def test_missing_pg_schema_fails_closed(authority_db, collector):
    from scripts.fleet_comms.efficiency_metrics import EfficiencyMetricsReadError

    plane_db, writer = authority_db
    writer.execute("DROP TABLE authority_deliveries")
    writer.execute("DROP TABLE authority_dead_letters")
    writer.execute("DROP TABLE authority_jobs")
    writer.commit()
    if isinstance(writer, sqlite3.Connection):
        # Preserve optional-table behavior for old sqlite migration snapshots.
        assert collector(plane_db).get("total", 0) == 0
    else:
        with pytest.raises(EfficiencyMetricsReadError, match="metrics table unavailable"):
            collector(plane_db)


def test_bottleneck_metadata_uses_authority_dialect(authority_db, tmp_path):
    from datetime import UTC, datetime

    from scripts.fleet_comms.efficiency_metrics import collect_stream_bottleneck_metrics

    plane_db, writer = authority_db
    writer.execute(
        "CREATE TABLE formal_review_jobs (review_id TEXT PRIMARY KEY, repository TEXT, "
        "pr_number INTEGER, created_at TEXT, stream_epic INTEGER, task_family TEXT)"
    )
    writer.execute(
        "CREATE TABLE github_publications (review_id TEXT, published_at TEXT, status_context TEXT)"
    )
    writer.execute(
        "INSERT INTO formal_review_jobs VALUES "
        "('review1', 'owner/repo', 1, '2026-08-01T11:00:00Z', 4707, 'metrics')"
    )
    writer.execute(
        "INSERT INTO github_publications VALUES "
        "('review1', '2026-08-01T11:05:00Z', 'fleet/cross-family-review')"
    )
    writer.commit()
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks, plane_db=plane_db, now=datetime(2026, 8, 1, 12, tzinfo=UTC),
        github_lookup=lambda **kwargs: (None, "lookup failed"),
    )
    assert payload["by_stream_epic"]["4707"]["formal_cf_publication"]["duration_s"] == {
        "min": 300.0, "max": 300.0, "avg": 300.0,
    }
    assert payload["source_errors"] == [{
        "source": "github", "error_kind": "pr_lookup_failed", "pr_number": 1,
        "store": {"kind": "comms-plane", "reachable": True},
    }]
