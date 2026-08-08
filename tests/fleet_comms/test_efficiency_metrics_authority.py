"""WP-C: authority-aware metrics/backlog/dead-letters (cold-start-opt PR-3)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

from scripts.fleet_comms.cli import EXIT_OK
from scripts.fleet_comms.cli import main as cli_main
from scripts.fleet_comms.efficiency_metrics import (
    collect_dead_letters,
    collect_delivery_backlog,
    collect_delivery_backlog_authority,
    collect_efficiency_metrics,
    resolve_metrics_source,
)


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
    assert payload["db_path"] == str(plane_db)
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
    assert metrics["deliveries"]["queued"] == 2
    assert metrics["dead_letters"] == 1
    assert metrics["jobs"]["queued"] == 1

    dead = _run_cli(
        ["dead-letters", "--root", str(plane_root), "--db", str(broker)],
        capsys,
    )
    assert dead["source"] == "authority"
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
    assert payload["db_path"] == str(broker)
    assert payload["total"] == 2
    assert payload["by_agent"] == {"claude": 1, "codex": 1}
    assert payload["by_status"]["pending"] == 1
    assert payload["by_status"]["dispatched"] == 1

    dead = _run_cli(
        ["dead-letters", "--legacy", "--db", str(broker), "--root", str(plane_root)],
        capsys,
    )
    assert dead["source"] == "legacy_forced"
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
    stripped = {k: v for k, v in payload.items() if k not in {"source", "db_path", "content_included"}}
    # CLI adds db_path/content_included/source; collector keys must match baseline.
    for key, value in baseline.items():
        assert stripped[key] == value

    metrics_baseline = collect_efficiency_metrics(broker)
    metrics = _run_cli(["metrics", "--db", str(broker)], capsys)
    assert metrics["source"] == "legacy"
    for key, value in metrics_baseline.items():
        assert metrics[key] == value

    dead_baseline = collect_dead_letters(broker)
    dead = _run_cli(["dead-letters", "--db", str(broker)], capsys)
    assert dead["source"] == "legacy"
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
