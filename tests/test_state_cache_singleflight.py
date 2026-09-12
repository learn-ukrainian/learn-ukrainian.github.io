"""Singleflight + warm for expensive state scans (#7973)."""

from __future__ import annotations

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

    state_router.schedule_state_scan_warmup(ctx)
    deadline = time.monotonic() + 5.0
    pipe_key = state_router._ctx_cache_key(ctx, "pipeline_versions", "all")
    weak_key = state_router._ctx_cache_key(ctx, "weak_points", "all", 7, 20)
    while time.monotonic() < deadline:
        if state_helpers.cache_get(pipe_key, 60.0) and state_helpers.cache_get(weak_key, 60.0):
            break
        time.sleep(0.02)
    else:
        pytest.fail("warmup did not populate cache keys")

    assert state_helpers.cache_get(pipe_key, 60.0)["track"] is None
    assert state_helpers.cache_get(weak_key, 60.0)["limit"] == 20
