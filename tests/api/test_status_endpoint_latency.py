"""Concurrent status routes must share one scan and serve cache hits on the event loop.

A warm hit stays on the event loop, so a saturated worker pool cannot turn a
cached dashboard read into a wait. Cold misses for the same key share one
compute. The burst holds that compute until every request has joined the
flight, so a later cache hit cannot hide a missing single-flight. Call counts
and completion while that pool or refresh is still blocked are the proof;
wall-clock budgets are not.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import threading
import types
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from fastapi import APIRouter, FastAPI
from httpx import ASGITransport

from scripts.api import artifacts_router, delegate_router, epics_router, state_helpers, state_router
from scripts.api.monitor_context import fixture_context

_BURST = 20
# Attempt bound for observable polls. Not a latency budget: the loop exits
# when the condition is true, and a loaded runner only makes each yield slower.
_ATTEMPTS = 10_000
_COLD_ROUTERS = (delegate_router, state_router, artifacts_router, epics_router)


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


class _ColdOverlap:
    """Gate that stays shut until every cold request has joined one flight.

    A missing single-flight opens the same gate by starting one compute per
    request. Either way the burst can finish, and the counts show which
    happened. The wait has no timeout.

    ``_claim_flight`` is process-global, so the status-scan warmup thread of
    another app can claim a *different* key while the burst runs (#11366).
    Only claims for a key this burst addressed count as its joiners; a foreign
    claim is not a joiner of this flight.
    """

    def __init__(self) -> None:
        self.counts = {"computes": 0, "joined": 0}
        self.burst_keys: set[str] = set()
        self.arrived = 0
        self.release = threading.Event()
        self.lock = threading.Lock()
        self.barrier: asyncio.Barrier | None = None

    def open_if_complete(self) -> None:
        if self.counts["joined"] >= _BURST or self.counts["computes"] >= _BURST:
            self.release.set()


def _arm_overlapping_cold_misses(monkeypatch: pytest.MonkeyPatch) -> _ColdOverlap:
    overlap = _ColdOverlap()
    original_claim = state_helpers._claim_flight
    original_async = state_helpers.cache_get_or_compute_async

    def wrapped_claim(key: str, ttl: float, *, force: bool = False):
        claimed = original_claim(key, ttl, force=force)
        with overlap.lock:
            if key in overlap.burst_keys:
                overlap.counts["joined"] += 1
                overlap.open_if_complete()
        return claimed

    async def wrapped_async(key: str, ttl: float, compute, *, force: bool = False):
        def gated():
            with overlap.lock:
                overlap.counts["computes"] += 1
                overlap.open_if_complete()
            overlap.release.wait()
            return compute()

        barrier = overlap.barrier
        if barrier is None:
            pytest.fail("cold-miss barrier was not armed")
        overlap.burst_keys.add(key)
        overlap.arrived += 1
        await barrier.wait()
        return await original_async(key, ttl, gated, force=force)

    monkeypatch.setattr(state_helpers, "_claim_flight", wrapped_claim)
    for module in _COLD_ROUTERS:
        monkeypatch.setattr(module, "cache_get_or_compute_async", wrapped_async)
    return overlap


async def _overlapping_burst(
    app: FastAPI,
    path: str,
    overlap: _ColdOverlap,
    *,
    intruder: Callable[[], None] | None = None,
) -> list[httpx.Response]:
    # An intruder (the warmup path) adds one party so it can claim while every
    # burst request already sits inside the flight window, before any of them
    # has claimed. The burst cannot release the barrier until the intruder is done.
    overlap.barrier = asyncio.Barrier(_BURST + (1 if intruder is not None else 0))
    loop = asyncio.get_running_loop()
    # A missing single-flight starts one blocked compute per request. The pool
    # has to fit all of them, or that failure would stall instead of counting.
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=_BURST + 1))
    transport = ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            requests = [asyncio.create_task(client.get(path)) for _ in range(_BURST)]
            if intruder is not None:
                await _until(
                    lambda: overlap.arrived >= _BURST,
                    "burst requests did not all enter the flight window",
                )
                landed = threading.Event()
                failure: list[BaseException] = []

                def run_intruder() -> None:
                    try:
                        intruder()
                    except BaseException as exc:
                        failure.append(exc)
                    finally:
                        landed.set()

                threading.Thread(target=run_intruder, name="state-scan-warmup", daemon=True).start()
                await asyncio.to_thread(landed.wait)
                if failure:
                    raise failure[0]
                await overlap.barrier.wait()
            responses = await asyncio.gather(*requests)
            return list(responses)
    finally:
        overlap.release.set()


def _run_overlapping_burst(
    monkeypatch: pytest.MonkeyPatch,
    app: FastAPI,
    path: str,
    *,
    intruder: Callable[[], None] | None = None,
) -> tuple[list[httpx.Response], dict[str, int]]:
    overlap = _arm_overlapping_cold_misses(monkeypatch)
    return asyncio.run(_overlapping_burst(app, path, overlap, intruder=intruder)), overlap.counts


def _assert_burst(responses: list[httpx.Response], calls: dict[str, int], overlap: dict[str, int]) -> None:
    assert calls["n"] == 1
    assert overlap["computes"] == 1
    assert overlap["joined"] == _BURST
    assert [response.status_code for response in responses] == [200] * _BURST


# One entry per burst route in this file, so the warmup-intruder reproducer
# covers every sibling that shares the joiner counter (#11366).
_BURST_ROUTES: dict[str, tuple[types.ModuleType, str, APIRouter, str, str, dict[str, object]]] = {
    "delegate_active": (
        delegate_router,
        "active_delegate_tasks",
        delegate_router.router,
        "/api/delegate",
        "/api/delegate/active",
        {"total": 0, "tasks": []},
    ),
    "delegate_tasks": (
        delegate_router,
        "list_delegate_tasks",
        delegate_router.router,
        "/api/delegate",
        "/api/delegate/tasks",
        {"total": 0, "tasks": []},
    ),
    "state_summary": (
        state_router,
        "compute_summary",
        state_router.router,
        "/api/state",
        "/api/state/summary",
        {"generated_at": "2026-01-01T00:00:00Z", "tracks": {}, "totals": {}},
    ),
    "pipeline_versions": (
        state_router,
        "_compute_pipeline_versions_payload",
        state_router.router,
        "/api/state",
        "/api/state/pipeline-versions",
        {"generated_at": "2026-01-01T00:00:00Z", "total": 0, "counts": {}},
    ),
    "weak_points": (
        state_router,
        "_compute_weak_points_payload",
        state_router.router,
        "/api/state",
        "/api/state/weak-points",
        {"count": 0, "modules": []},
    ),
    "research_coverage": (
        state_router,
        "compute_research_coverage",
        state_router.router,
        "/api/state",
        "/api/state/research-coverage",
        {"generated_at": "2026-01-01T00:00:00Z", "tracks": {}},
    ),
    "artifacts_html": (
        artifacts_router,
        "collect_html_artifacts",
        artifacts_router.router,
        "/api/artifacts",
        "/api/artifacts/html",
        {"generated_at": "2026-01-01T00:00:00Z", "total": 0, "artifacts": []},
    ),
    "epics_list": (
        epics_router,
        "_build_remote_epic_list",
        epics_router.router,
        "/api/epics",
        "/api/epics/v1",
        {"schema": "remote-epic-lifecycle.v1", "registry_status": "ok", "streams": []},
    ),
    "routing_budget": (
        state_router,
        "compute_routing_budget",
        state_router.router,
        "/api/state",
        "/api/state/routing-budget",
        {"generated_at": "2026-01-01T00:00:00Z", "agents": {}, "recommendation": {}},
    ),
}


def _warmup_claim() -> None:
    """Claim a foreign key the way ``state_router._run_state_scan_warmup`` does."""
    state_helpers.cache_get_or_compute("state-scan-warmup:research_coverage#11366", 60.0, lambda: {"warm": True})


@pytest.mark.parametrize("route", sorted(_BURST_ROUTES))
def test_foreign_key_claim_inside_burst_is_not_a_joiner(
    route: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A warmup claim landing inside the burst window must not be counted (#11366).

    ``_claim_flight`` is process-global: the status-scan warmup thread claims
    its own key while the burst is parked inside the flight window. Counting
    every claim made the burst observe 21 joins and fail ``assert 21 == 20``.
    The burst must count only claims for the key it addressed; the warmup is
    not a joiner of this flight and its compute is not this burst's.
    """
    module, attr, router, prefix, path, payload = _BURST_ROUTES[route]
    calls = {"n": 0}

    def slow(*_args, **_kwargs):
        calls["n"] += 1
        return payload

    monkeypatch.setattr(module, attr, slow)
    responses, overlap = _run_overlapping_burst(
        monkeypatch, _mount(tmp_path, router, prefix), path, intruder=_warmup_claim
    )
    _assert_burst(responses, calls, overlap)


def test_delegate_active_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        return {"total": 0, "tasks": []}

    monkeypatch.setattr(delegate_router, "active_delegate_tasks", slow)
    responses, overlap = _run_overlapping_burst(
        monkeypatch, _mount(tmp_path, delegate_router.router, "/api/delegate"), "/api/delegate/active"
    )
    _assert_burst(responses, calls, overlap)


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
    """A stale snapshot is served while its scheduled refresh is still blocked."""
    clock = {"t": 1_000.0}
    calls = {"n": 0}
    refresh_entered = threading.Event()
    release_refresh = threading.Event()
    refresh_finished = threading.Event()
    monkeypatch.setattr(state_helpers, "_ttl_clock", lambda: clock["t"])

    def slow(**_kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            refresh_entered.set()
            try:
                release_refresh.wait()
            finally:
                refresh_finished.set()
        return {"generated_at": "2026-01-01T00:00:00Z", "marker": 1}

    monkeypatch.setattr(state_router, "compute_routing_budget", slow)
    app = _mount(tmp_path, state_router.router, "/api/state")

    async def scenario() -> None:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/state/routing-budget")
            assert first.status_code == 200
            assert calls["n"] == 1
            clock["t"] += state_router.ROUTING_BUDGET_TTL_S + 1
            second_task = asyncio.create_task(client.get("/api/state/routing-budget"))
            try:
                await _until(refresh_entered.is_set, "stale routing budget scheduled no refresh")
                await _until(second_task.done, "stale routing budget waited on its refresh")
                second = second_task.result()
                assert second.status_code == 200
                assert second.json()["marker"] == 1
                assert calls["n"] == 2
                assert not refresh_finished.is_set()
            finally:
                release_refresh.set()
                if not second_task.done():
                    second_task.cancel()
                await asyncio.gather(second_task, return_exceptions=True)
        await _until(refresh_finished.is_set, "stale routing budget refresh did not finish after release")

    asyncio.run(scenario())
    assert calls["n"] == 2


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
