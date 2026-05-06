"""Smoke tests for playground dashboard API stability."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from fastapi.testclient import TestClient

import scripts.api.comms_router as comms_router
from scripts.ai_agent_bridge import _db
from scripts.api.main import app


def _init_broker_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(_db._LEGACY_SCHEMA)
    conn.executescript(_db._CHANNELS_SCHEMA)
    conn.execute(
        """
        INSERT INTO channels (name, created_at, description, include, subscribers)
        VALUES ('general', '2026-05-06T00:00:00Z', 'General', '', 'claude,codex')
        """
    )
    conn.execute(
        """
        INSERT INTO messages (
            task_id, from_llm, to_llm, message_type, content, timestamp, acknowledged, status
        )
        VALUES ('smoke-a1-hello', 'codex', 'claude', 'message', 'smoke', '2026-05-06T00:00:00Z', 0, 'pending')
        """
    )
    conn.commit()
    conn.close()


def test_playground_primary_endpoints_keep_health_fast(tmp_path, monkeypatch):
    broker_db = tmp_path / "messages.db"
    _init_broker_db(broker_db)
    monkeypatch.setattr(comms_router, "MESSAGE_DB", broker_db)

    client = TestClient(app, raise_server_exceptions=False)
    endpoints = [
        "/api/dashboard/overview",
        "/api/comms/channels",
        "/api/comms/messages?limit=1&offset=0",
        "/api/comms/batch-progress",
        "/api/admin/health",
        "/api/build/events/active",
        "/api/consultation/metrics",
        "/api/analytics/cost",
        "/api/delegate/tasks?limit=100",
        "/api/images/stats",
        "/api/orient",
        "/api/state/summary",
        "/api/state/research-coverage",
        "/api/runtime/agents",
        "/api/state/track-health/a1",
        "/api/wiki/status",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code < 500, endpoint

        start = time.perf_counter()
        health = client.get("/api/health")
        elapsed = time.perf_counter() - start
        assert health.status_code == 200
        assert elapsed < 0.2, f"/api/health took {elapsed:.3f}s after {endpoint}"
