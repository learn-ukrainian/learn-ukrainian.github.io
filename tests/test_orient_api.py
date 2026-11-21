"""Tests for product sections composed into GET /api/orient."""

from __future__ import annotations

import threading

import lu_machinery.api.main as api_main
import lu_machinery.api.state_helpers as state_helpers
import pytest
from fastapi.testclient import TestClient

import scripts.project_api.orient as product_orient

client = TestClient(api_main.app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _reset_orient_cache():
    """Each test starts and ends with drained per-context orient state."""
    for key in [k for k in state_helpers._ttl_cache if k.startswith("orient_")]:
        state_helpers._ttl_cache.pop(key, None)
    api_main.reset_detached_orient_state_for_tests()
    yield
    for key in [k for k in state_helpers._ttl_cache if k.startswith("orient_")]:
        state_helpers._ttl_cache.pop(key, None)
    api_main.reset_detached_orient_state_for_tests()


def _join_orient_refresh_threads(ctx=None) -> None:
    """Wait for active orient refresh threads in ``ctx`` to finish."""
    state = api_main._orient_state(api_main.app.state.ctx if ctx is None else ctx)
    with state.lock:
        threads = list(state.refresh_threads.values())
    for thread in threads:
        thread.join(timeout=2.0)
        assert not thread.is_alive()


def test_orient_fresh_query_bypasses_cache(monkeypatch):
    """Unavailable product sections return null + meta.error, and `?fresh=true` bypasses cache.

    Exercises the product ``governance`` section (TTL 120 s, ``merge_meta=True``,
    whose ``OrientSection`` carries zero-valued ``GOVERNANCE_FALLBACK``). Under
    lu-machinery 0.1.46 (machinery PR 1036), an unavailable section (cold failure
    or failed ``fresh=true`` refresh) returns ``null`` plus ``meta[section].error``
    instead of fabricating zero counts, and failures are not cached as values.
    """
    calls = {"governance": 0}
    should_fail = {"value": True}

    def governance_collector(ctx=None):
        calls["governance"] += 1
        if should_fail["value"]:
            raise RuntimeError("governance store unavailable")
        return {
            "decisions_total": calls["governance"],
            "decisions_stale": 0,
            "decisions_approaching_expiry": 0,
            "adrs_total": 1,
            "adrs_warnings": 0,
            "adrs_errors": 0,
        }

    monkeypatch.setattr(product_orient, "collect_governance_orient_data", governance_collector)

    cold_failed = client.get("/api/orient?sections=governance")
    assert cold_failed.status_code == 200
    cold_data = cold_failed.json()
    assert cold_data["governance"] is None
    assert cold_data["meta"]["governance"]["error"] == "governance store unavailable"
    assert "decisions_total" not in cold_data["meta"]["governance"]
    assert calls["governance"] == 1

    should_fail["value"] = False
    first = client.get("/api/orient?sections=governance")
    assert first.status_code == 200
    first_data = first.json()
    assert first_data["governance"]["decisions_total"] == 2
    assert first_data["meta"]["governance"]["cache"] == "miss"
    assert "error" not in first_data["meta"]["governance"]
    assert first_data["meta"]["governance"]["decisions_total"] == 2

    second = client.get("/api/orient?sections=governance")
    assert second.status_code == 200
    second_data = second.json()
    assert second_data["meta"]["governance"]["cache"] == "hit"
    assert calls["governance"] == 2

    fresh = client.get("/api/orient?sections=governance&fresh=true")
    assert fresh.status_code == 200
    fresh_data = fresh.json()
    assert fresh_data["governance"]["decisions_total"] == 3
    assert fresh_data["meta"]["governance"]["cache"] == "miss"
    assert calls["governance"] == 3

    should_fail["value"] = True
    fresh_failed = client.get("/api/orient?sections=governance&fresh=true")
    assert fresh_failed.status_code == 200
    failed_data = fresh_failed.json()
    assert failed_data["governance"] is None
    assert failed_data["meta"]["governance"]["error"] == "governance store unavailable"
    assert "decisions_total" not in failed_data["meta"]["governance"]
    assert calls["governance"] == 4


def test_orient_pipeline_section_skips_orient_layer_cache(monkeypatch):
    """Product ``pipeline`` section (TTL 0) serves aged values stale while refresh is gated.

    Regression for GH #1309 / reviewer BLOCKER B2: ``pipeline`` wraps
    ``state_summary()`` which carries its own 60 s cache. With TTL 0 under
    lu-machinery 0.1.46, a repeat request whose background refresh has not yet
    published returns the prior stored value labelled ``stale=True`` and
    ``cache="miss"`` while scheduling a background refresh.
    """
    calls = {"pipeline": 0}
    release_run2 = threading.Event()
    release_run3 = threading.Event()
    wait_calls: list[tuple[str, float]] = []
    real_await_thread = api_main._await_thread

    async def spy_await_thread(thread: threading.Thread, timeout: float) -> None:
        wait_calls.append((thread.name, timeout))
        await real_await_thread(thread, timeout)

    async def counting_pipeline(ctx=None):
        calls["pipeline"] += 1
        run = calls["pipeline"]
        if run == 2:
            release_run2.wait()
        elif run == 3:
            release_run3.wait()
        return {"summary": {"run": run}}

    monkeypatch.setattr(product_orient, "collect_pipeline_orient_data", counting_pipeline)

    try:
        first = client.get("/api/orient?sections=pipeline")
        assert first.status_code == 200
        first_data = first.json()
        assert first_data["pipeline"] == {"summary": {"run": 1}}
        assert first_data["meta"]["pipeline"]["cache"] == "miss"
        assert first_data["meta"]["pipeline"]["stale"] is False
        _join_orient_refresh_threads()

        monkeypatch.setattr(api_main, "_await_thread", spy_await_thread)

        second = client.get("/api/orient?sections=pipeline")
        assert second.status_code == 200
        second_data = second.json()
        assert second_data["pipeline"] == {"summary": {"run": 1}}
        assert second_data["meta"]["pipeline"]["cache"] == "miss"
        assert second_data["meta"]["pipeline"]["stale"] is True
        assert second_data["meta"]["pipeline"]["refreshing"] is True
        assert wait_calls == [], "aged non-fresh read must not wait inline for background refresh"
        release_run2.set()
        _join_orient_refresh_threads()

        third = client.get("/api/orient?sections=pipeline")
        assert third.status_code == 200
        third_data = third.json()
        assert third_data["pipeline"] == {"summary": {"run": 2}}
        assert third_data["meta"]["pipeline"]["cache"] == "miss"
        assert third_data["meta"]["pipeline"]["stale"] is True
        assert third_data["meta"]["pipeline"]["refreshing"] is True
        assert wait_calls == [], "aged non-fresh read must not wait inline for background refresh"
        release_run3.set()
        _join_orient_refresh_threads()
    finally:
        release_run2.set()
        release_run3.set()
        _join_orient_refresh_threads()

    assert calls["pipeline"] == 3


def test_orient_generated_at_floor_reflects_oldest_section(monkeypatch):
    """Top-level ``generated_at`` is the oldest section's timestamp.

    Regression for GH #1309 / reviewer CONCERN C1: a response mixing a cached
    product section (``wiki``, TTL 120 s) and a freshly collected one
    (``pipeline``, TTL 0 s) must label the response with the oldest section's
    ``generated_at``, not request time.
    """
    wiki_payload = {"by_track": {"hist": {"compiled": 1, "total": 2, "pct": 50.0}}}
    pipeline_payload = {"summary": {"totals": {"total": 1}}}
    current_ts = {"value": "2026-11-21T00:00:01Z"}

    monkeypatch.setattr(api_main, "_isoformat_z", lambda _dt: current_ts["value"])
    monkeypatch.setattr(product_orient, "collect_wiki_orient_data", lambda ctx=None: wiki_payload)

    async def fake_pipeline(ctx=None):
        return pipeline_payload

    monkeypatch.setattr(product_orient, "collect_pipeline_orient_data", fake_pipeline)

    warm = client.get("/api/orient?sections=wiki")
    assert warm.status_code == 200
    wiki_ts = warm.json()["meta"]["wiki"]["generated_at"]
    assert wiki_ts == "2026-11-21T00:00:01Z"

    current_ts["value"] = "2026-11-21T00:00:05Z"
    combined = client.get("/api/orient?sections=wiki,pipeline")
    assert combined.status_code == 200
    data = combined.json()
    assert data["wiki"] == wiki_payload
    assert data["pipeline"] == pipeline_payload
    assert "error" not in data["meta"]["wiki"]
    assert "error" not in data["meta"]["pipeline"]
    assert data["meta"]["wiki"]["cache"] == "hit"
    assert data["meta"]["wiki"]["generated_at"] == wiki_ts
    assert data["meta"]["pipeline"]["cache"] == "miss"
    assert data["meta"]["pipeline"]["generated_at"] == "2026-11-21T00:00:05Z"

    section_timestamps = [m["generated_at"] for m in data["meta"].values() if m.get("generated_at")]
    assert section_timestamps == ["2026-11-21T00:00:01Z", "2026-11-21T00:00:05Z"]
    assert data["generated_at"] == wiki_ts
    assert data["generated_at"] == min(section_timestamps)
