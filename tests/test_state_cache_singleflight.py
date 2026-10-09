"""Singleflight + warm for expensive state scans (#7973)."""

from __future__ import annotations

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from scripts.api import state_helpers


@pytest.fixture(autouse=True)
def _clear_ttl_cache():
    state_helpers.cache_invalidate()
    yield
    state_helpers.cache_invalidate()


def test_cache_get_or_compute_coalesces_concurrent_misses():
    calls = {"n": 0}
    barrier = threading.Barrier(8)
    started = threading.Event()

    def compute():
        calls["n"] += 1
        started.set()
        time.sleep(0.15)
        return {"ok": True, "n": calls["n"]}

    def worker():
        barrier.wait(timeout=5)
        return state_helpers.cache_get_or_compute("sf-key", 60.0, compute)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: worker(), range(8)))

    assert calls["n"] == 1
    assert all(r == {"ok": True, "n": 1} for r in results)
    assert state_helpers.cache_get("sf-key", 60.0) == {"ok": True, "n": 1}


def test_cache_get_or_compute_hit_skips_compute():
    state_helpers.cache_set("warm-key", {"v": 1})
    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        return {"v": 2}

    assert state_helpers.cache_get_or_compute("warm-key", 60.0, compute) == {"v": 1}
    assert calls["n"] == 0


def test_cache_get_or_compute_async_coalesces_and_skips_a_warm_hit():
    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        time.sleep(0.15)
        return {"n": calls["n"]}

    async def scenario():
        results = await asyncio.gather(
            *[state_helpers.cache_get_or_compute_async("async-sf", 60.0, compute) for _ in range(8)]
        )
        warm = await state_helpers.cache_get_or_compute_async("async-sf", 60.0, compute)
        return results, warm

    results, warm = asyncio.run(scenario())
    assert calls["n"] == 1
    assert all(item == {"n": 1} for item in results)
    assert warm == {"n": 1}


def test_cache_get_or_compute_force_bypasses_warm_and_coalesces():
    state_helpers.cache_set("force-key", {"v": "stale"})
    calls = {"n": 0}
    barrier = threading.Barrier(4)

    def compute():
        calls["n"] += 1
        time.sleep(0.1)
        return {"v": "fresh", "n": calls["n"]}

    def worker():
        barrier.wait(timeout=5)
        return state_helpers.cache_get_or_compute("force-key", 60.0, compute, force=True)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: worker(), range(4)))

    assert calls["n"] == 1
    assert all(r == {"v": "fresh", "n": 1} for r in results)


def test_cancelled_waiter_does_not_cancel_the_shared_flight():
    started = threading.Event()
    release = threading.Event()
    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        started.set()
        assert release.wait(timeout=2)
        return {"ok": True}

    async def scenario():
        first = asyncio.create_task(state_helpers.cache_get_or_compute_async("cancel-key", 30.0, compute))
        assert await asyncio.to_thread(started.wait, 2)
        second = asyncio.create_task(state_helpers.cache_get_or_compute_async("cancel-key", 30.0, compute))
        await asyncio.sleep(0.05)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        release.set()
        assert await asyncio.wait_for(second, 2) == {"ok": True}
        again = await state_helpers.cache_get_or_compute_async("cancel-key", 30.0, compute)
        assert again == {"ok": True}
        assert calls["n"] == 1

    try:
        asyncio.run(scenario())
    finally:
        release.set()


def test_sync_and_async_callers_share_one_flight():
    """A warmup thread and a request must not publish two results for one key."""
    started = threading.Event()
    release = threading.Event()
    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        started.set()
        assert release.wait(timeout=2)
        return {"gen": calls["n"]}

    async def scenario():
        sync_task = asyncio.create_task(
            asyncio.to_thread(state_helpers.cache_get_or_compute, "shared-key", 30.0, compute, force=True)
        )
        assert await asyncio.to_thread(started.wait, 2)
        async_task = asyncio.create_task(
            state_helpers.cache_get_or_compute_async("shared-key", 30.0, lambda: {"gen": 99}, force=True)
        )
        await asyncio.sleep(0.05)
        release.set()
        sync_result = await sync_task
        async_result = await async_task
        assert sync_result == async_result == {"gen": 1}
        assert calls["n"] == 1
        assert state_helpers.cache_get("shared-key", 30.0) == {"gen": 1}

    try:
        asyncio.run(scenario())
    finally:
        release.set()


def test_cache_retain_tolerates_concurrent_inserts():
    prefix = "race:"
    state_helpers.cache_set(prefix + "old", 1)
    errors: list[BaseException] = []
    stop = threading.Event()

    def writer() -> None:
        index = 0
        while not stop.is_set():
            state_helpers.cache_set(f"other:{index}", index)
            index += 1

    def retainer() -> None:
        for generation in range(200):
            try:
                state_helpers.cache_retain(prefix, f"{prefix}gen-{generation}")
            except BaseException as exc:
                errors.append(exc)

    thread = threading.Thread(target=writer)
    thread.start()
    try:
        retainer()
    finally:
        stop.set()
        thread.join(timeout=2)
    assert errors == []
    assert not thread.is_alive()


def test_replaced_generation_does_not_publish_again():
    state_helpers.cache_set("gen:1", {"v": 1})
    assert state_helpers.cache_retain("gen:", "gen:2") == 1
    state_helpers.cache_set("gen:1", {"v": 1})
    assert state_helpers.cache_get_stored("gen:1") is None
    state_helpers.cache_set("gen:2", {"v": 2})
    stored = state_helpers.cache_get_stored("gen:2")
    assert stored is not None
    assert stored[0] == {"v": 2}
    state_helpers.cache_invalidate("gen:")
    state_helpers.cache_set("gen:1", {"v": 3})
    restored = state_helpers.cache_get_stored("gen:1")
    assert restored is not None
    assert restored[0] == {"v": 3}


def test_schedule_state_scan_warmup_fills_default_keys(monkeypatch, tmp_path):
    from scripts.api import state_router
    from scripts.api.monitor_context import fixture_context

    ctx = fixture_context(tmp_path)
    pipe_payload = {"total": 0, "counts": {"v6": 0, "v5": 0, "v3": 0, "unbuilt": 0}}
    weak_payload = {"count": 0, "modules": []}

    monkeypatch.setattr(
        state_router,
        "_compute_pipeline_versions_payload",
        lambda _ctx, track: {**pipe_payload, "track": track},
    )
    monkeypatch.setattr(
        state_router,
        "_compute_weak_points_payload",
        lambda _ctx, track, min_score, limit: {
            **weak_payload,
            "track": track,
            "min_score": min_score,
            "limit": limit,
        },
    )

    # Isolate from any warmup thread started by another test or app startup in
    # this xdist worker (#8570): the module-global guard would otherwise make
    # this call a no-op for this test's ctx.
    monkeypatch.setattr(state_router, "_state_scan_warm_thread", None)

    warm_thread = state_router.schedule_state_scan_warmup(ctx)
    warm_thread.join(timeout=30)
    assert not warm_thread.is_alive(), "state scan warmup thread did not finish within 30s"

    pipe_key = state_router._ctx_cache_key(ctx, "pipeline_versions", "all")
    weak_key = state_router._ctx_cache_key(ctx, "weak_points", "all", 7, 20)
    assert state_helpers.cache_get(pipe_key, 60.0)["track"] is None
    assert state_helpers.cache_get(weak_key, 60.0)["limit"] == 20
