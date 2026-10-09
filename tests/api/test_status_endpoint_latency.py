"""Concurrent status routes must share one scan and return without the request timeout.

A warm hit stays on the event loop, so a saturated worker pool cannot turn a
cached dashboard read into a timeout. Cold misses for the same key share one
compute.
"""

from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport

from scripts.api import artifacts_router, delegate_router, epics_router, state_helpers, state_router
from scripts.api.monitor_context import fixture_context

_BURST = 20
_BUDGET_S = 2.0
_SLOW_S = 0.3


@pytest.fixture(autouse=True)
def _clear_status_cache():
    state_helpers.cache_invalidate()
    yield
    state_helpers.cache_invalidate()


def _mount(tmp_path: Path, router, prefix: str) -> FastAPI:
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(router, prefix=prefix)
    return app


async def _burst(app: FastAPI, path: str) -> tuple[float, list[httpx.Response]]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        started = time.perf_counter()
        responses = await asyncio.gather(*[client.get(path) for _ in range(_BURST)])
        return time.perf_counter() - started, list(responses)


def _assert_burst(elapsed: float, responses: list[httpx.Response], calls: dict[str, int]) -> None:
    assert elapsed < _BUDGET_S, f"burst took {elapsed:.3f}s"
    assert calls["n"] == 1
    assert [response.status_code for response in responses] == [200] * _BURST


def test_delegate_active_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"total": 0, "tasks": []}

    monkeypatch.setattr(delegate_router, "active_delegate_tasks", slow)
    elapsed, responses = asyncio.run(_burst(_mount(tmp_path, delegate_router.router, "/api/delegate"), "/api/delegate/active"))
    _assert_burst(elapsed, responses, calls)


def test_delegate_tasks_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"total": 0, "tasks": []}

    monkeypatch.setattr(delegate_router, "list_delegate_tasks", slow)
    elapsed, responses = asyncio.run(
        _burst(_mount(tmp_path, delegate_router.router, "/api/delegate"), "/api/delegate/tasks")
    )
    _assert_burst(elapsed, responses, calls)


def test_state_summary_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"generated_at": "2026-01-01T00:00:00Z", "tracks": {}, "totals": {}}

    monkeypatch.setattr(state_router, "compute_summary", slow)
    elapsed, responses = asyncio.run(_burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/summary"))
    _assert_burst(elapsed, responses, calls)


def test_pipeline_versions_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(_ctx, _track):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"generated_at": "2026-01-01T00:00:00Z", "total": 0, "counts": {}}

    monkeypatch.setattr(state_router, "_compute_pipeline_versions_payload", slow)
    elapsed, responses = asyncio.run(
        _burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/pipeline-versions")
    )
    _assert_burst(elapsed, responses, calls)


def test_weak_points_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(_ctx, _track, _min_score, _limit):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"count": 0, "modules": []}

    monkeypatch.setattr(state_router, "_compute_weak_points_payload", slow)
    elapsed, responses = asyncio.run(
        _burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/weak-points")
    )
    _assert_burst(elapsed, responses, calls)


def test_research_coverage_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"generated_at": "2026-01-01T00:00:00Z", "tracks": {}}

    monkeypatch.setattr(state_router, "compute_research_coverage", slow)
    elapsed, responses = asyncio.run(
        _burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/research-coverage")
    )
    _assert_burst(elapsed, responses, calls)


def test_artifacts_html_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"generated_at": "2026-01-01T00:00:00Z", "total": 0, "artifacts": []}

    monkeypatch.setattr(artifacts_router, "collect_html_artifacts", slow)
    elapsed, responses = asyncio.run(
        _burst(_mount(tmp_path, artifacts_router.router, "/api/artifacts"), "/api/artifacts/html")
    )
    _assert_burst(elapsed, responses, calls)


def test_epics_list_burst_shares_one_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(_ctx):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"schema": "remote-epic-lifecycle.v1", "registry_status": "ok", "streams": []}

    monkeypatch.setattr(epics_router, "_build_remote_epic_list", slow)
    elapsed, responses = asyncio.run(_burst(_mount(tmp_path, epics_router.router, "/api/epics"), "/api/epics/v1"))
    _assert_burst(elapsed, responses, calls)


def test_routing_budget_burst_shares_one_compute(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"generated_at": "2026-01-01T00:00:00Z", "agents": {}, "recommendation": {}}

    monkeypatch.setattr(state_router, "compute_routing_budget", slow)
    elapsed, responses = asyncio.run(
        _burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/routing-budget")
    )
    _assert_burst(elapsed, responses, calls)


def test_warm_routing_budget_does_not_wait_on_the_worker_pool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = {"n": 0}
    hold = threading.Event()

    def slow(**_kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            hold.wait(timeout=2)
        return {"generated_at": "2026-01-01T00:00:00Z", "marker": calls["n"]}

    monkeypatch.setattr(state_router, "compute_routing_budget", slow)
    app = _mount(tmp_path, state_router.router, "/api/state")

    async def scenario() -> float:
        transport = ASGITransport(app=app)
        release = threading.Event()
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/state/routing-budget")
            assert first.status_code == 200
            loop = asyncio.get_running_loop()
            blockers = [loop.run_in_executor(None, release.wait) for _ in range(64)]
            try:
                await asyncio.sleep(0.05)
                started = time.perf_counter()
                second = await asyncio.wait_for(client.get("/api/state/routing-budget"), timeout=1.0)
                elapsed = time.perf_counter() - started
            finally:
                release.set()
                await asyncio.gather(*blockers, return_exceptions=True)
        assert second.status_code == 200
        assert second.json()["marker"] == 1
        return elapsed

    try:
        assert asyncio.run(scenario()) < 0.5
        assert calls["n"] == 1
    finally:
        hold.set()


def test_stale_routing_budget_returns_while_refresh_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = {"t": 1_000.0}
    calls = {"n": 0}
    hold = threading.Event()
    monkeypatch.setattr(state_helpers, "_ttl_clock", lambda: clock["t"])

    def slow(**_kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            hold.wait(timeout=2)
        return {"generated_at": "2026-01-01T00:00:00Z", "marker": 1}

    monkeypatch.setattr(state_router, "compute_routing_budget", slow)
    app = _mount(tmp_path, state_router.router, "/api/state")

    async def scenario() -> float:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/state/routing-budget")
            assert first.status_code == 200
            clock["t"] += state_router.ROUTING_BUDGET_TTL_S + 1
            started = time.perf_counter()
            second = await asyncio.wait_for(client.get("/api/state/routing-budget"), timeout=1.0)
            elapsed = time.perf_counter() - started
        assert second.status_code == 200
        assert second.json()["marker"] == 1
        return elapsed

    try:
        assert asyncio.run(scenario()) < 0.5
    finally:
        hold.set()


def test_expired_routing_budget_reports_age_and_withdraws_authorization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = {"t": 1_000.0}
    calls = {"n": 0}
    monkeypatch.setattr(state_helpers, "_ttl_clock", lambda: clock["t"])

    def compute(**_kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            raise RuntimeError("refresh failed")
        return {
            "generated_at": "2026-01-01T00:00:00Z",
            "agents": {"codex": {"eligible": True, "status": "cool"}},
            "recommendation": {
                "primary_agent_for_code": "codex",
                "rationale": "fresh",
                "warnings": [],
            },
            "diagnostics": {"stale": False, "data_age_s": 0, "stale_threshold_s": 900},
            "ranked_by_headroom": [{"lane": "codex"}],
        }

    monkeypatch.setattr(state_router, "compute_routing_budget", compute)
    app = _mount(tmp_path, state_router.router, "/api/state")

    async def scenario() -> tuple[dict, dict]:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/state/routing-budget")
            assert first.status_code == 200
            assert first.json()["diagnostics"]["stale"] is False
            clock["t"] += state_router.ROUTING_BUDGET_TTL_S + 5
            aged = await client.get("/api/state/routing-budget")
            for _ in range(50):
                if calls["n"] >= 2 and not state_helpers._refresh_keys:
                    break
                await asyncio.sleep(0.02)
            clock["t"] = 1_000.0 + state_router.ROUTING_BUDGET_MAX_AGE_S + 1
            withdrawn = await client.get("/api/state/routing-budget")
        return aged.json(), withdrawn.json()

    aged, withdrawn = asyncio.run(scenario())
    assert calls["n"] >= 2
    assert aged["diagnostics"]["stale"] is True
    assert aged["diagnostics"]["data_age_s"] == state_router.ROUTING_BUDGET_TTL_S + 5
    assert set(aged["diagnostics"]) == {"stale", "data_age_s", "stale_threshold_s"}
    assert aged["recommendation"]["primary_agent_for_code"] == "codex"
    assert withdrawn["diagnostics"]["stale"] is True
    assert withdrawn["diagnostics"]["data_age_s"] == state_router.ROUTING_BUDGET_MAX_AGE_S + 1
    assert withdrawn["recommendation"]["primary_agent_for_code"] is None
    assert withdrawn["agents"]["codex"]["eligible"] is False
    assert withdrawn["agents"]["codex"]["status"] == "unknown"
    assert withdrawn["ranked_by_headroom"] == []


def test_delegate_list_replaces_the_previous_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def scan(**_kwargs):
        calls["n"] += 1
        return {"total": calls["n"], "tasks": []}

    monkeypatch.setattr(delegate_router, "active_delegate_tasks", scan)
    app = _mount(tmp_path, delegate_router.router, "/api/delegate")
    tasks_dir = tmp_path / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True)

    async def scenario() -> None:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/delegate/active")
            assert first.json()["total"] == 1
            (tasks_dir / "one.json").write_text("{}", encoding="utf-8")
            second = await client.get("/api/delegate/active")
            assert second.json()["total"] == 2

    asyncio.run(scenario())
    keys = [key for key in state_helpers._ttl_cache if ":delegate:" in key]
    assert len(keys) == 1
