"""Sol PR-M efficiency metrics (no content leakage)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.fleet_comms.efficiency_metrics import (
    collect_dead_letters,
    collect_delivery_backlog,
    collect_efficiency_metrics,
)


def _mini_db(path: Path) -> None:
    conn = sqlite3.connect(path)
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
        CREATE TABLE requests (
          request_id TEXT PRIMARY KEY,
          request_message_id TEXT,
          requested_recipient TEXT,
          resolved_recipient TEXT,
          state TEXT,
          expires_at TEXT,
          completion_state TEXT,
          created_at TEXT,
          updated_at TEXT
        );
        INSERT INTO deliveries VALUES
          ('d1','m1','claude','pending',0,NULL,NULL),
          ('d2','m2','gemini','pending',1,NULL,NULL),
          ('d3','m3','codex','delivered',1,'2026-07-21T10:00:00','2026-07-21T10:00:05');
        INSERT INTO dead_letters VALUES
          ('dl1',NULL,'d9','recipient_retired','agy',NULL,'2026-07-21T09:00:00');
        INSERT INTO requests VALUES
          ('r1','cm1','gemini','agy','dead_lettered','2026-07-21T12:00:00','unknown',
           '2026-07-21T09:00:00','2026-07-21T09:00:00');
        """
    )
    conn.commit()
    conn.close()


def test_backlog_excludes_retired_gemini(tmp_path: Path) -> None:
    db = tmp_path / "m.db"
    _mini_db(db)
    payload = collect_delivery_backlog(db, exclude_retired=True)
    assert payload["total"] == 1
    assert payload["by_agent"] == {"claude": 1}
    assert "content" not in str(payload).lower() or "content_included" not in payload


def test_dead_letters_and_metrics(tmp_path: Path) -> None:
    db = tmp_path / "m.db"
    _mini_db(db)
    dl = collect_dead_letters(db)
    assert dl["total"] == 1
    assert dl["by_reason"]["recipient_retired"] == 1
    assert "body" not in dl["rows"][0]

    m = collect_efficiency_metrics(db)
    assert m["content_included"] is False
    assert m["dead_letters"] == 1
    assert m["deliveries"]["delivered"] == 1
    assert m["retired_endpoint_pending"]["gemini"] == 1
    assert m["latency_seconds"]["delivery_dispatch_to_done"]["n"] == 1
