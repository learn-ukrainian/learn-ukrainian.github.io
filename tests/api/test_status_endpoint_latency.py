"""Concurrent status routes must share one scan and serve cache hits on the event loop.

A warm hit stays on the event loop, so a saturated worker pool cannot turn a
cached dashboard read into a wait. Cold misses for the same key share one
compute. Call counts and completion while that pool or refresh is still
blocked are the proof; wall-clock budgets are not.
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
# Attempt bound for observable polls. Not a latency budget: the loop exits
# when the condition is true, and a loaded runner only makes each yield slower.
_ATTEMPTS = 10_000


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


async def _until(ready, failure: str) -> None:
    """Poll until ``ready`` or the attempt bound is exhausted."""
    for _ in range(_ATTEMPTS):
        if ready():
            return
        await asyncio.sleep(0)
    pytest.fail(failure)


async def _burst(app: FastAPI, path: str) -> list[httpx.Response]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        responses = await asyncio.gather(*[client.get(path) for _ in range(_BURST)])
        return list(responses)


def _assert_burst(responses: list[httpx.Response], calls: dict[str, int]) -> None:
    assert calls["n"] == 1
    assert [response.status_code for response in responses] == [200] * _BURST


def test_delegate_active_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        return {"total": 0, "tasks": []}

    monkeypatch.setattr(delegate_router, "active_delegate_tasks", slow)
    responses = asyncio.run(_burst(_mount(tmp_path, delegate_router.router, "/api/delegate"), "/api/delegate/active"))
    _assert_burst(responses, calls)


def test_delegate_tasks_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        return {"total": 0, "tasks": []}

    monkeypatch.setattr(delegate_router, "list_delegate_tasks", slow)
    responses = asyncio.run(_burst(_mount(tmp_path, delegate_router.router, "/api/delegate"), "/api/delegate/tasks"))
    _assert_burst(responses, calls)


def test_state_summary_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        return {"generated_at": "2026-01-01T00:00:00Z", "tracks": {}, "totals": {}}

    monkeypatch.setattr(state_router, "compute_summary", slow)
    responses = asyncio.run(_burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/summary"))
    _assert_burst(responses, calls)


def test_pipeline_versions_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(_ctx, _track):
        calls["n"] += 1
        return {"generated_at": "2026-01-01T00:00:00Z", "total": 0, "counts": {}}

    monkeypatch.setattr(state_router, "_compute_pipeline_versions_payload", slow)
    responses = asyncio.run(_burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/pipeline-versions"))
    _assert_burst(responses, calls)


def test_weak_points_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(_ctx, _track, _min_score, _limit):
        calls["n"] += 1
        return {"count": 0, "modules": []}

    monkeypatch.setattr(state_router, "_compute_weak_points_payload", slow)
    responses = asyncio.run(_burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/weak-points"))
    _assert_burst(responses, calls)


def test_research_coverage_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        return {"generated_at": "2026-01-01T00:00:00Z", "tracks": {}}

    monkeypatch.setattr(state_router, "compute_research_coverage", slow)
    responses = asyncio.run(_burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/research-coverage"))
    _assert_burst(responses, calls)


def test_artifacts_html_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        return {"generated_at": "2026-01-01T00:00:00Z", "total": 0, "artifacts": []}

    monkeypatch.setattr(artifacts_router, "collect_html_artifacts", slow)
    responses = asyncio.run(_burst(_mount(tmp_path, artifacts_router.router, "/api/artifacts"), "/api/artifacts/html"))
    _assert_burst(responses, calls)


def test_epics_list_burst_shares_one_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(_ctx):
        calls["n"] += 1
        return {"schema": "remote-epic-lifecycle.v1", "registry_status": "ok", "streams": []}

    monkeypatch.setattr(epics_router, "_build_remote_epic_list", slow)
    responses = asyncio.run(_burst(_mount(tmp_path, epics_router.router, "/api/epics"), "/api/epics/v1"))
    _assert_burst(responses, calls)


def test_routing_budget_burst_shares_one_compute(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        return {"generated_at": "2026-01-01T00:00:00Z", "agents": {}, "recommendation": {}}

    monkeypatch.setattr(state_router, "compute_routing_budget", slow)
    responses = asyncio.run(_burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/routing-budget"))
    _assert_burst(responses, calls)


def test_warm_routing_budget_does_not_wait_on_the_worker_pool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A cached read finishes while every default-executor worker is still blocked."""
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        return {"generated_at": "2026-01-01T00:00:00Z", "marker": calls["n"]}

    monkeypatch.setattr(state_router, "compute_routing_budget", slow)
    app = _mount(tmp_path, state_router.router, "/api/state")

    async def scenario() -> None:
        transport = ASGITransport(app=app)
        release = threading.Event()
        entered = {"n": 0}
        entered_lock = threading.Lock()
        pool_full = threading.Event()
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/state/routing-budget")
            assert first.status_code == 200
            loop = asyncio.get_running_loop()
            await asyncio.to_thread(lambda: None)
            # asyncio publishes no worker count; the live executor is the pool the route uses.
            executor = getattr(loop, "_default_executor", None)
            worker_count = getattr(executor, "_max_workers", None)
            if not isinstance(worker_count, int) or worker_count < 1:
                pytest.fail("could not read the default executor size")

            def blocker() -> None:
                with entered_lock:
                    entered["n"] += 1
                    if entered["n"] >= worker_count:
                        pool_full.set()
                release.wait()

            blockers = [loop.run_in_executor(None, blocker) for _ in range(worker_count)]
            second_task: asyncio.Task | None = None
            try:
                await _until(pool_full.is_set, "default executor workers did not start")
                second_task = asyncio.create_task(client.get("/api/state/routing-budget"))
                await _until(second_task.done, "warm routing budget waited on the saturated worker pool")
                second = second_task.result()
                assert second.status_code == 200
                assert second.json()["marker"] == 1
                assert entered["n"] == worker_count
            finally:
                release.set()
                if second_task is not None and not second_task.done():
                    second_task.cancel()
                await asyncio.gather(*blockers, return_exceptions=True)

    asyncio.run(scenario())
    assert calls["n"] == 1


def test_stale_routing_budget_returns_while_refresh_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A stale snapshot is served while its refresh is still blocked."""
    clock = {"t": 1_000.0}
    calls = {"n": 0}
    request_done = threading.Event()
    waited_on_refresh = {"v": False}
    monkeypatch.setattr(state_helpers, "_ttl_clock", lambda: clock["t"])

    def slow(**_kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            # Yield until the response is observable. A request that waits on
            # this refresh never sets the event, so the attempt bound fails it.
            for _ in range(_ATTEMPTS):
                if request_done.is_set():
                    break
                time.sleep(0.001)
            else:
                waited_on_refresh["v"] = True
        return {"generated_at": "2026-01-01T00:00:00Z", "marker": 1}

    monkeypatch.setattr(state_router, "compute_routing_budget", slow)
    app = _mount(tmp_path, state_router.router, "/api/state")

    async def scenario() -> None:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/state/routing-budget")
            assert first.status_code == 200
            clock["t"] += state_router.ROUTING_BUDGET_TTL_S + 1
            try:
                second = await client.get("/api/state/routing-budget")
            finally:
                request_done.set()
        assert second.status_code == 200
        assert second.json()["marker"] == 1

    asyncio.run(scenario())
    assert not waited_on_refresh["v"]


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


def _routing_snapshot(data_age_s: float) -> dict:
    return {
        "generated_at": "2026-01-01T00:00:00Z",
        "agents": {"codex": {"eligible": True, "status": "cool"}},
        "recommendation": {
            "primary_agent_for_code": "codex",
            "rationale": "fresh",
            "warnings": [],
        },
        "diagnostics": {"stale": False, "data_age_s": data_age_s, "stale_threshold_s": 900},
        "ranked_by_headroom": [{"lane": "codex"}],
    }


def test_cumulative_source_age_withdraws_routing_authorization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Source age plus cache residence is the age compared to the threshold."""
    clock = {"t": 1_000.0}
    calls = {"n": 0}
    monkeypatch.setattr(state_helpers, "_ttl_clock", lambda: clock["t"])

    def compute(**_kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            raise RuntimeError("refresh failed")
        return _routing_snapshot(890)

    monkeypatch.setattr(state_router, "compute_routing_budget", compute)
    app = _mount(tmp_path, state_router.router, "/api/state")

    async def scenario() -> dict:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/state/routing-budget")
            assert first.status_code == 200
            assert first.json()["recommendation"]["primary_agent_for_code"] == "codex"
            clock["t"] += 20
            aged = await client.get("/api/state/routing-budget")
        return aged.json()

    body = asyncio.run(scenario())
    assert body["diagnostics"]["stale"] is True
    assert body["diagnostics"]["data_age_s"] == 910
    assert set(body["diagnostics"]) == {"stale", "data_age_s", "stale_threshold_s"}
    assert body["recommendation"]["primary_agent_for_code"] is None
    assert body["agents"]["codex"]["eligible"] is False
    assert body["ranked_by_headroom"] == []


def test_cumulative_source_age_under_threshold_keeps_authorization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = {"t": 1_000.0}
    monkeypatch.setattr(state_helpers, "_ttl_clock", lambda: clock["t"])

    def compute(**_kwargs):
        return _routing_snapshot(800)

    monkeypatch.setattr(state_router, "compute_routing_budget", compute)
    app = _mount(tmp_path, state_router.router, "/api/state")

    async def scenario() -> dict:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/state/routing-budget")
            assert first.status_code == 200
            clock["t"] += 20
            aged = await client.get("/api/state/routing-budget")
        return aged.json()

    body = asyncio.run(scenario())
    assert body["diagnostics"]["stale"] is True
    assert body["diagnostics"]["data_age_s"] == 820
    assert body["recommendation"]["primary_agent_for_code"] == "codex"
    assert body["agents"]["codex"]["eligible"] is True
    assert body["ranked_by_headroom"] == [{"lane": "codex"}]


def test_artifact_filters_with_colons_do_not_share_a_cache_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[tuple[object, object]] = []

    def collect(**kwargs):
        seen.append((kwargs.get("status"), kwargs.get("author")))
        return {"status": kwargs.get("status"), "author": kwargs.get("author"), "artifacts": []}

    monkeypatch.setattr(artifacts_router, "collect_html_artifacts", collect)
    app = _mount(tmp_path, artifacts_router.router, "/api/artifacts")

    async def scenario() -> tuple[dict, dict]:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get(
                "/api/artifacts/html",
                params={"status": "draft", "author": "team:alpha"},
            )
            second = await client.get(
                "/api/artifacts/html",
                params={"status": "draft:team", "author": "alpha"},
            )
        return first.json(), second.json()

    one, two = asyncio.run(scenario())
    assert seen == [("draft", "team:alpha"), ("draft:team", "alpha")]
    assert one["author"] == "team:alpha"
    assert two["author"] == "alpha"
    assert one["status"] == "draft"
    assert two["status"] == "draft:team"


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
