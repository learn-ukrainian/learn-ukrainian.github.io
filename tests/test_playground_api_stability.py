"""Smoke tests for playground dashboard API stability."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from fastapi.testclient import TestClient

import scripts.api.admin_router as admin_router
import scripts.api.comms_router as comms_router
import scripts.api.dashboard_comms as dashboard_comms
import scripts.api.state_helpers as state_helpers
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
    monkeypatch.setattr(admin_router, "MESSAGE_DB", broker_db)
    monkeypatch.setattr(comms_router, "MESSAGE_DB", broker_db)
    monkeypatch.setattr(dashboard_comms, "MESSAGE_DB", broker_db)
    monkeypatch.setattr(state_helpers, "MESSAGE_DB", broker_db)

    client = TestClient(app, raise_server_exceptions=False)
    dashboard_loads = {
        "index.html": [
            "/api/dashboard/overview",
            "/api/state/summary",
            "/api/wiki/status",
            "/api/analytics/cost",
        ],
        "admin.html": [
            "/api/admin/health",
            "/api/admin/disk-usage",
            "/api/admin/backup/list",
            "/api/admin/maintenance/embedding-cache-stats",
        ],
        "audit-dashboard.html": [
            "/api/dashboard/overview",
            "/api/dashboard/track/a1/summary",
            "/api/state/module/a1/1",
        ],
        "build-events.html": [
            "/api/build/events/active",
            "/api/build/events/recent?limit=50&offset=0",
        ],
        "channels.html": [
            "/api/comms/channels",
            "/api/comms/channels/general",
            "/api/comms/channels/general/messages?tail=50",
            "/api/comms/channels/general/deliveries?status=pending&limit=20",
        ],
        "comms.html": [
            "/api/comms/messages?limit=1&offset=0",
            "/api/comms/live-activity?minutes=30",
            "/api/comms/batch-progress",
            "/api/comms/zombies",
        ],
        "consultation.html": [
            "/api/config",
            "/api/consultation/metrics",
            "/api/consultation/queue",
            "/api/consultation/history?limit=200",
        ],
        "cost.html": [
            "/api/analytics/cost",
            "/api/analytics/cost/module/a1/hello",
            "/api/analytics/cost/phase/write",
        ],
        "curriculum-dashboard.html": [
            "/api/dashboard/overview",
            "/api/dashboard/track/a1",
            "/api/dashboard/module/a1/hello",
        ],
        "delegate.html": [
            "/api/delegate/tasks?limit=100",
        ],
        "image-explorer.html": [
            "/api/images/textbooks",
            "/api/images/stats",
            "/api/images/annotations?per_page=5",
            "/api/rag/search_text?q=test&limit=5",
        ],
        "orient.html": [
            "/api/orient",
        ],
        "progress.html": [
            "/api/state/pipeline/a1",
            "/api/state/summary",
            "/api/state/pipeline-versions",
        ],
        "quality.html": [
            "/api/state/research-coverage",
            "/api/state/review-coverage",
            "/api/state/issues",
            "/api/state/weak-points?limit=500",
        ],
        "runtime.html": [
            "/api/runtime/agents",
            "/api/runtime/usage?days=7",
            "/api/runtime/recent?limit=50",
            "/api/runtime/auth",
        ],
        "track-health.html": [
            "/api/state/build-status",
            "/api/state/enrichment-status",
            "/api/state/track-health/a1",
            "/api/state/module/a1/1",
        ],
        "wiki.html": [
            "/api/wiki/status",
            "/api/wiki/status/a1",
            "/api/wiki/quality-gate/a1",
            "/api/wiki/build-log?limit=50",
        ],
    }

    endpoint_timings: list[tuple[str, str, float]] = []
    for dashboard, endpoints in dashboard_loads.items():
        for endpoint in endpoints:
            start = time.perf_counter()
            response = client.get(endpoint)
            elapsed = time.perf_counter() - start
            endpoint_timings.append((dashboard, endpoint, elapsed))

            if endpoint.startswith("/api/rag/"):
                assert response.status_code in {200, 503}, f"{dashboard} {endpoint}"
            else:
                assert response.status_code < 500, f"{dashboard} {endpoint}"
            assert elapsed < 0.5, f"{dashboard} {endpoint} took {elapsed:.3f}s"

        endpoint_p99 = max(
            elapsed for seen_dashboard, _endpoint, elapsed in endpoint_timings
            if seen_dashboard == dashboard
        )
        assert endpoint_p99 < 0.5, f"{dashboard} p99 budget exceeded: {endpoint_p99:.3f}s"

        start = time.perf_counter()
        health = client.get("/api/health")
        elapsed = time.perf_counter() - start
        assert health.status_code == 200
        assert elapsed < 0.2, f"/api/health took {elapsed:.3f}s after {endpoint}"
