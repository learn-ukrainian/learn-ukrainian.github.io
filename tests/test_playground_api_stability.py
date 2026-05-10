"""Smoke tests for dashboard API stability."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import scripts.api.admin_router as admin_router
import scripts.api.comms_router as comms_router
import scripts.api.dashboard_comms as dashboard_comms
import scripts.api.images_router as images_router
import scripts.api.state_helpers as state_helpers
from scripts.ai_agent_bridge import _db
from scripts.api.main import app

SAMPLE_COUNT = 3
HEALTH_ENDPOINT = "/api/health"

DASHBOARD_LOADS = {
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

BUDGETS = {
    # True in-process health probe: no filesystem, git, sqlite, or network path.
    HEALTH_ENDPOINT: 0.1,
    # Dashboard endpoints below can transitively touch filesystem scans, sqlite,
    # git, GH, RAG/textbook indexes, or cold in-memory caches. GH #1826 relaxes
    # these network/IO-bound smoke budgets to 1.5s while keeping health tight.
    "/api/admin/backup/list": 1.5,
    "/api/admin/disk-usage": 1.5,
    "/api/admin/health": 1.5,
    "/api/admin/maintenance/embedding-cache-stats": 1.5,
    "/api/analytics/cost": 1.5,
    "/api/analytics/cost/module/a1/hello": 1.5,
    "/api/analytics/cost/phase/write": 1.5,
    "/api/build/events/active": 1.5,
    "/api/build/events/recent?limit=50&offset=0": 1.5,
    "/api/comms/batch-progress": 1.5,
    "/api/comms/channels": 1.5,
    "/api/comms/channels/general": 1.5,
    "/api/comms/channels/general/deliveries?status=pending&limit=20": 1.5,
    "/api/comms/channels/general/messages?tail=50": 1.5,
    "/api/comms/live-activity?minutes=30": 1.5,
    "/api/comms/messages?limit=1&offset=0": 1.5,
    "/api/comms/zombies": 1.5,
    "/api/config": 1.5,
    "/api/consultation/history?limit=200": 1.5,
    "/api/consultation/metrics": 1.5,
    "/api/consultation/queue": 1.5,
    "/api/dashboard/module/a1/hello": 1.5,
    "/api/dashboard/overview": 1.5,
    "/api/dashboard/track/a1": 1.5,
    "/api/dashboard/track/a1/summary": 1.5,
    "/api/delegate/tasks?limit=100": 1.5,
    "/api/images/annotations?per_page=5": 1.5,
    "/api/images/stats": 1.5,
    "/api/images/textbooks": 1.5,
    "/api/orient": 1.5,
    "/api/rag/search_text?q=test&limit=5": 1.5,
    "/api/runtime/agents": 1.5,
    "/api/runtime/auth": 1.5,
    "/api/runtime/recent?limit=50": 1.5,
    "/api/runtime/usage?days=7": 1.5,
    "/api/state/build-status": 1.5,
    "/api/state/enrichment-status": 1.5,
    "/api/state/issues": 1.5,
    "/api/state/module/a1/1": 1.5,
    "/api/state/pipeline/a1": 1.5,
    "/api/state/pipeline-versions": 1.5,
    "/api/state/research-coverage": 1.5,
    "/api/state/review-coverage": 1.5,
    "/api/state/summary": 1.5,
    "/api/state/track-health/a1": 1.5,
    "/api/state/weak-points?limit=500": 1.5,
    "/api/wiki/build-log?limit=50": 1.5,
    "/api/wiki/quality-gate/a1": 1.5,
    "/api/wiki/status": 1.5,
    "/api/wiki/status/a1": 1.5,
}


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


def _p95_of_three(timings: list[float]) -> float:
    """GH #1826 finite-sample p95: two of three samples must be under budget."""
    if len(timings) != SAMPLE_COUNT:
        raise ValueError(f"expected {SAMPLE_COUNT} timings, got {len(timings)}")
    return sorted(timings)[SAMPLE_COUNT - 2]


def _measure_three_runs(call: Callable[[], object]) -> tuple[list[object], list[float], float]:
    results = []
    timings = []
    for _ in range(SAMPLE_COUNT):
        start = time.perf_counter()
        results.append(call())
        timings.append(time.perf_counter() - start)
    return results, timings, _p95_of_three(timings)


@pytest.fixture
def three_run_perf_probe() -> Callable[[Callable[[], object]], tuple[list[object], list[float], float]]:
    return _measure_three_runs


def _dashboard_endpoints() -> set[str]:
    return {endpoint for endpoints in DASHBOARD_LOADS.values() for endpoint in endpoints}


def test_dashboard_endpoint_budget_coverage_is_explicit():
    missing = sorted(_dashboard_endpoints() - BUDGETS.keys())
    assert not missing, f"dashboard endpoints missing BUDGETS entries: {missing}"


def test_p95_of_three_perf_probe_allows_one_slow_tail(monkeypatch, three_run_perf_probe):
    samples = iter([0.0, 0.01, 0.01, 1.21, 1.21, 1.22])
    monkeypatch.setattr(time, "perf_counter", lambda: next(samples))

    results, timings, p95_elapsed = three_run_perf_probe(lambda: "ok")

    assert results == ["ok", "ok", "ok"]
    assert max(timings) > 1.0
    assert p95_elapsed < 0.1


def test_playground_primary_endpoints_keep_health_fast(tmp_path, monkeypatch, three_run_perf_probe):
    broker_db = tmp_path / "messages.db"
    _init_broker_db(broker_db)
    monkeypatch.setattr(admin_router, "MESSAGE_DB", broker_db)
    monkeypatch.setattr(comms_router, "MESSAGE_DB", broker_db)
    monkeypatch.setattr(dashboard_comms, "MESSAGE_DB", broker_db)
    monkeypatch.setattr(state_helpers, "MESSAGE_DB", broker_db)
    images_router._index.reload()
    images_router._page_cache.clear()

    client = TestClient(app, raise_server_exceptions=False)
    endpoint_timings: list[tuple[str, str, float]] = []
    for dashboard, endpoints in DASHBOARD_LOADS.items():
        for endpoint in endpoints:
            endpoint_budget = BUDGETS[endpoint]
            responses, timings, p95_elapsed = three_run_perf_probe(
                lambda endpoint=endpoint: client.get(endpoint)
            )
            endpoint_timings.append((dashboard, endpoint, p95_elapsed))

            for response in responses:
                if endpoint.startswith("/api/rag/"):
                    assert response.status_code in {200, 503}, f"{dashboard} {endpoint}"
                else:
                    assert response.status_code < 500, f"{dashboard} {endpoint}"
            assert p95_elapsed < endpoint_budget, (
                f"{dashboard} {endpoint} p95-of-3 took {p95_elapsed:.3f}s "
                f"(runs: {', '.join(f'{elapsed:.3f}s' for elapsed in timings)})"
            )

        dashboard_p95 = max(
            elapsed for seen_dashboard, _endpoint, elapsed in endpoint_timings
            if seen_dashboard == dashboard
        )
        dashboard_budget = max(BUDGETS[endpoint] for endpoint in endpoints)
        assert dashboard_p95 < dashboard_budget, (
            f"{dashboard} p95 budget exceeded: {dashboard_p95:.3f}s"
        )

        health_responses, health_timings, health_p95 = three_run_perf_probe(
            lambda: client.get(HEALTH_ENDPOINT)
        )
        for health in health_responses:
            assert health.status_code == 200
        assert health_p95 < BUDGETS[HEALTH_ENDPOINT], (
            f"{HEALTH_ENDPOINT} p95-of-3 took {health_p95:.3f}s after {endpoint} "
            f"(runs: {', '.join(f'{elapsed:.3f}s' for elapsed in health_timings)})"
        )
