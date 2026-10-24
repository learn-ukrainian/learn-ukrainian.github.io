"""Regression coverage for routing-budget event-loop scans and compute age."""

import asyncio
import threading

import httpx
from fastapi import FastAPI

from scripts.api import state_helpers, state_router
from scripts.api.lane_health import LaneHealthScan
from scripts.api.monitor_context import fixture_context


def _app(monkeypatch, tmp_path, compute):
    monkeypatch.setattr(state_router, "compute_routing_budget", compute)
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(state_router.router, prefix="/api/state")
    return app


def test_warm_lane_error_never_scans_tasks_on_event_loop(monkeypatch, tmp_path):
    """A cached lane failure must not cause synchronous directory scans on GET."""
    scan_threads = []

    def scan(_tasks_dir):
        scan_threads.append(threading.get_ident())
        return LaneHealthScan(observed=False, error="fixture scan failure")

    def compute(**kwargs):
        kwargs["task_generation"].append(state_router._tasks_content_token(kwargs["tasks_dir"]))
        return {
            "agents": {"codex": {"health": {"error": "previous scan failure"}}},
            "diagnostics": {"data_age_s": 0, "stale": False, "stale_threshold_s": 900},
        }

    monkeypatch.setattr(state_router, "scan_lane_health", scan)
    app = _app(monkeypatch, tmp_path, compute)

    async def scenario():
        loop_thread = threading.get_ident()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            cold = await client.get("/api/state/routing-budget")
            assert cold.status_code == 200
            for _ in range(2):
                warm = await client.get("/api/state/routing-budget")
                assert warm.status_code == 200
                assert warm.json()["agents"]["codex"]["health"]["error"] == "fixture scan failure"
        assert scan_threads, "live lane errors were never refreshed"
        assert loop_thread not in scan_threads, "warm lane-error scan blocked the event loop"

    asyncio.run(scenario())


def test_slow_compute_duration_counts_toward_served_age(monkeypatch, tmp_path):
    """Compute time must not permit a source older than 900 seconds to authorize."""
    clock = {"t": 1000.0}
    monkeypatch.setattr(state_helpers, "_ttl_clock", lambda: clock["t"])

    def compute(**kwargs):
        kwargs["task_generation"].append(state_router._tasks_content_token(kwargs["tasks_dir"]))
        clock["t"] += 20
        return {
            "agents": {"codex": {"eligible": True, "status": "cool"}},
            "recommendation": {"primary_agent_for_code": "codex", "warnings": []},
            "diagnostics": {"data_age_s": 895, "stale": False, "stale_threshold_s": 900},
            "ranked_by_headroom": [{"lane": "codex"}],
        }

    app = _app(monkeypatch, tmp_path, compute)

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            cold = await client.get("/api/state/routing-budget")
            assert cold.status_code == 200
            clock["t"] += 3
            warm = await client.get("/api/state/routing-budget")
            assert warm.status_code == 200
        for response, expected_age in ((cold, 915.0), (warm, 918.0)):
            body = response.json()
            assert body["diagnostics"] == {
                "data_age_s": expected_age, "stale": True, "stale_threshold_s": 900,
            }
            assert body["recommendation"]["primary_agent_for_code"] is None
            assert body["agents"]["codex"]["eligible"] is False
            assert body["ranked_by_headroom"] == []

    asyncio.run(scenario())
