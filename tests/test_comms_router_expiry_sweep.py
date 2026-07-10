"""Tests for the Monitor API server's periodic delivery-expiry sweep (#4837 item 4).

The sweep is a lazy, codexbar-style background trigger hooked to
GET /api/comms/agent-activity (scripts/api/comms_router.py). The critical
property under test: it must operate on THIS router's own `MESSAGE_DB`
(so it respects test patches and never diverges from what the router
reports), and must NEVER touch `ai_agent_bridge`'s own default DB path —
a real production risk since `ai_agent_bridge._db.get_db()` resolves its
own DB_PATH independently and would silently create + migrate a fresh
broker DB if ever pointed at a path that doesn't exist yet.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_agent_bridge import _channels
from ai_agent_bridge import _config as ab_config
from ai_agent_bridge import _db as ab_db

from scripts.api import comms_router
from scripts.api.state_helpers import cache_invalidate


@pytest.fixture(autouse=True)
def _reset_sweep_state():
    cache_invalidate("bridge_expire_sweep")
    comms_router._expire_sweep_thread = None
    yield
    cache_invalidate("bridge_expire_sweep")
    comms_router._expire_sweep_thread = None


def _seed_channel_db(db_path: Path) -> dict:
    """Build a real channel-bridge DB at db_path via the actual bridge code,
    temporarily redirecting ai_agent_bridge's own DB_PATH — then restore it,
    so the seeded file is indistinguishable from a real broker DB but the
    live default path is never touched."""
    with patch.object(ab_config, "DB_PATH", db_path), patch.object(ab_db, "DB_PATH", db_path):
        ab_db.init_db()
        _channels.create_channel("ops")
        stale = _channels.post("ops", "user", "stale fyi", to_agents=["claude"], auto_snapshot=False)
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "UPDATE channel_messages SET created_at = '2020-01-01T00:00:00+00:00' WHERE message_id = ?",
            (stale["message_id"],),
        )
        conn.commit()
        conn.close()
        dead = _channels.post("ops", "user", "for a dead lane", to_agents=["gemini"], auto_snapshot=False)
    return {"stale_delivery_id": stale["delivery_ids"][0], "dead_delivery_id": dead["delivery_ids"][0]}


def _delivery_status(db_path: Path, delivery_id: str) -> str:
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute("SELECT status FROM deliveries WHERE delivery_id = ?", (delivery_id,)).fetchone()
        return str(row[0])
    finally:
        conn.close()


def test_sweep_expires_stale_and_dead_lane_rows_in_the_routers_own_db(tmp_path):
    db_path = tmp_path / "messages.db"
    ids = _seed_channel_db(db_path)
    assert not ab_config.DB_PATH.exists(), "real default DB must not exist before the sweep"
    real_default_db_path = ab_config.DB_PATH

    with patch.object(comms_router, "MESSAGE_DB", db_path):
        comms_router._maybe_run_delivery_expiry_sweep()
        assert comms_router._expire_sweep_thread is not None
        comms_router._expire_sweep_thread.join(timeout=5)
        assert not comms_router._expire_sweep_thread.is_alive()

    assert _delivery_status(db_path, ids["stale_delivery_id"]) == "expired"
    assert _delivery_status(db_path, ids["dead_delivery_id"]) == "expired"

    # The real ai_agent_bridge default DB path must remain untouched — no
    # stray file created, and its module-level DB_PATH must be restored.
    assert not real_default_db_path.exists()
    assert real_default_db_path == ab_db.DB_PATH
    assert real_default_db_path == ab_config.DB_PATH


def test_sweep_is_noop_when_message_db_missing(tmp_path):
    missing = tmp_path / "does-not-exist.db"
    with patch.object(comms_router, "MESSAGE_DB", missing):
        comms_router._maybe_run_delivery_expiry_sweep()
    assert comms_router._expire_sweep_thread is None
    assert not missing.exists()


def test_sweep_is_noop_when_channel_tables_missing(tmp_path):
    """A legacy-only broker DB (messages table, no channel bridge tables)
    must not be auto-migrated as a side effect of the sweep trigger."""
    db_path = tmp_path / "messages.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, content TEXT)")
    conn.commit()
    conn.close()

    with patch.object(comms_router, "MESSAGE_DB", db_path):
        comms_router._maybe_run_delivery_expiry_sweep()

    assert comms_router._expire_sweep_thread is None
    conn = sqlite3.connect(str(db_path))
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()
    assert tables == {"messages"}, "sweep must not auto-migrate a legacy-only DB"


def test_sweep_is_noop_on_pre_priority_column_schema(tmp_path):
    """Regression (found via tests/test_manifest_api.py collision): a broker
    DB with the three channel tables but PRE-DATING the max_age_hours/
    priority columns must not trigger the sweep. ``ai_agent_bridge._db.get_db()``
    silently ALTER TABLE-migrates any DB missing those columns — if the sweep
    ran anyway, that dormant migration would fire as a side effect of a
    dashboard poll, then the newly-defaulted columns would make every row in
    an old/synthetic fixture look 24h+ stale and get force-expired."""
    db_path = tmp_path / "messages.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE channels (
            name TEXT PRIMARY KEY, created_at TEXT, description TEXT, include TEXT, subscribers TEXT
        );
        CREATE TABLE channel_messages (
            message_id TEXT PRIMARY KEY, channel TEXT, thread_id TEXT, parent_id TEXT,
            correlation_id TEXT, round_index INTEGER, from_agent TEXT, from_model TEXT,
            kind TEXT, body TEXT, attachments TEXT, context_rev_shared TEXT,
            context_rev_channel TEXT, monitor_state_snapshot TEXT, created_at TEXT
        );
        CREATE TABLE deliveries (
            delivery_id TEXT PRIMARY KEY, message_id TEXT, to_agent TEXT, to_model TEXT,
            status TEXT, dispatched_at TEXT, delivered_at TEXT, error TEXT, lease_until TEXT,
            attempt_count INTEGER DEFAULT 0, retry_after TEXT, last_error_kind TEXT
        );
        """
    )
    conn.execute("INSERT INTO channels VALUES ('reviews', '2026-05-31T10:00:00Z', '', '', '')")
    conn.execute(
        "INSERT INTO channel_messages (message_id, channel, thread_id, from_agent, kind, body, created_at, "
        "round_index) VALUES ('m1', 'reviews', 't1', 'claude', 'post', 'hi', '2026-05-31T10:01:00Z', 0)"
    )
    conn.execute(
        "INSERT INTO deliveries (delivery_id, message_id, to_agent, status) VALUES ('d1', 'm1', 'codex', 'pending')"
    )
    conn.commit()
    conn.close()

    with patch.object(comms_router, "MESSAGE_DB", db_path):
        comms_router._maybe_run_delivery_expiry_sweep()

    assert comms_router._expire_sweep_thread is None
    assert _delivery_status(db_path, "d1") == "pending"
    conn = sqlite3.connect(str(db_path))
    try:
        columns = {r[1] for r in conn.execute("PRAGMA table_info(channels)")}
    finally:
        conn.close()
    assert "max_age_hours" not in columns, "sweep must not auto-migrate the schema either"


def test_sweep_triggers_at_most_once_per_interval(tmp_path):
    db_path = tmp_path / "messages.db"
    _seed_channel_db(db_path)

    with patch.object(comms_router, "MESSAGE_DB", db_path):
        comms_router._maybe_run_delivery_expiry_sweep()
        first_thread = comms_router._expire_sweep_thread
        first_thread.join(timeout=5)

        comms_router._maybe_run_delivery_expiry_sweep()
        # Cache still warm — no second thread spawned.
        assert comms_router._expire_sweep_thread is first_thread


def test_agent_activity_endpoint_triggers_sweep(tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    db_path = tmp_path / "messages.db"
    ids = _seed_channel_db(db_path)

    app = FastAPI()
    app.include_router(comms_router.router, prefix="/api/comms")
    client = TestClient(app)

    with patch.object(comms_router, "MESSAGE_DB", db_path):
        resp = client.get("/api/comms/agent-activity")
        assert resp.status_code == 200
        thread = comms_router._expire_sweep_thread
        assert thread is not None
        thread.join(timeout=5)

    assert _delivery_status(db_path, ids["stale_delivery_id"]) == "expired"
    assert _delivery_status(db_path, ids["dead_delivery_id"]) == "expired"
