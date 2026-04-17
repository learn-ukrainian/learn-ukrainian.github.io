"""Tests for the /api/orient endpoint."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

import scripts.api.main as api_main
import scripts.api.state_helpers as state_helpers

client = TestClient(api_main.app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _reset_orient_cache():
    """Each test starts with a fresh orient cache.

    The orient handler caches per-section results in the shared
    ``state_helpers._ttl_cache`` to keep /api/orient cheap under load
    (see GH #1309). Tests must clear that cache or a later test will
    silently hit stale state from an earlier one.
    """
    keys_to_drop = [k for k in state_helpers._ttl_cache if k.startswith("orient_")]
    for key in keys_to_drop:
        state_helpers._ttl_cache.pop(key, None)
    yield
    keys_to_drop = [k for k in state_helpers._ttl_cache if k.startswith("orient_")]
    for key in keys_to_drop:
        state_helpers._ttl_cache.pop(key, None)


def _patch_orient_sources(monkeypatch) -> None:
    monkeypatch.setattr(api_main, "_collect_git_orient_data", lambda: {"branch": "main", "head": "abc123"})
    monkeypatch.setattr(api_main, "_collect_issues_orient_data", lambda: {"issues": [{"number": 1186}]})

    async def fake_pipeline():
        return {"summary": {"totals": {"total": 1}}}

    monkeypatch.setattr(api_main, "_collect_pipeline_orient_data", fake_pipeline)
    monkeypatch.setattr(
        api_main,
        "_collect_runtime_orient_data",
        lambda: {"agents": ["codex"], "recent_outcomes": {"ok": 1, "error": 0, "rate_limited": 0}, "headroom": {"codex": True}},
    )
    monkeypatch.setattr(api_main, "_collect_delegate_orient_data", lambda: {"active_count": 0, "recent": []})
    monkeypatch.setattr(api_main, "_collect_wiki_orient_data", lambda: {"by_track": {"hist": {"compiled": 1, "total": 2, "pct": 50.0}}})
    monkeypatch.setattr(api_main, "_collect_health_orient_data", lambda: {"api": True, "mcp_rag": False, "sources_db": True, "message_broker": True})
    monkeypatch.setattr(api_main, "_collect_session_hints_orient_data", lambda: [{"file": "docs/session-state/example.md", "first_line": "# Example"}])


def test_orient_returns_all_top_level_keys(monkeypatch):
    _patch_orient_sources(monkeypatch)

    response = client.get("/api/orient")

    assert response.status_code == 200
    data = response.json()
    expected = {"generated_at", "git", "issues", "pipeline", "runtime", "delegate", "wiki", "health", "session_hints"}
    assert expected <= set(data)


def test_orient_swallows_failing_subquery(monkeypatch):
    _patch_orient_sources(monkeypatch)

    def broken_git():
        raise RuntimeError("git failed")

    monkeypatch.setattr(api_main, "_collect_git_orient_data", broken_git)

    response = client.get("/api/orient")

    assert response.status_code == 200
    data = response.json()
    assert data["git"]["error"] == "git failed"
    assert data["runtime"]["agents"] == ["codex"]


def test_orient_completes_within_500ms(monkeypatch):
    _patch_orient_sources(monkeypatch)

    start = time.perf_counter()
    response = client.get("/api/orient")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert elapsed < 0.5


def test_orient_response_includes_meta_for_each_section(monkeypatch):
    """Every aggregated section must advertise its own freshness metadata.

    Per GH #1309 / reviewer ask "generated_at, stale_after, source per
    section", consumers need to decide which parts to refetch without
    guessing.
    """
    _patch_orient_sources(monkeypatch)

    response = client.get("/api/orient")

    assert response.status_code == 200
    meta = response.json()["meta"]
    for section in api_main.ORIENT_SECTION_TTLS:
        assert section in meta, f"meta missing section {section!r}"
        entry = meta[section]
        assert "generated_at" in entry
        assert "stale_after_s" in entry
        assert "source" in entry
        assert entry["cache"] in {"hit", "miss"}
        assert entry["stale_after_s"] == api_main.ORIENT_SECTION_TTLS[section]


def test_orient_second_call_hits_cache(monkeypatch):
    """Within the TTL window, a repeat call must skip the collector.

    We count how many times the git collector runs. First call = miss,
    second call = hit, so the counter stays at 1 across two requests.
    """
    _patch_orient_sources(monkeypatch)
    calls = {"git": 0}

    def counting_git():
        calls["git"] += 1
        return {"branch": "main", "head": "abc123"}

    monkeypatch.setattr(api_main, "_collect_git_orient_data", counting_git)

    first = client.get("/api/orient")
    second = client.get("/api/orient")

    assert first.status_code == 200
    assert second.status_code == 200
    assert calls["git"] == 1
    assert first.json()["meta"]["git"]["cache"] == "miss"
    assert second.json()["meta"]["git"]["cache"] == "hit"


def test_orient_hard_timeout_isolates_async_collector(monkeypatch):
    """A hung ASYNC collector caps at the per-section hard timeout.

    This covers the live-reproduced BLOCKER from the first baseline
    run: the async pipeline collector could block the whole response.
    ``asyncio.wait_for`` properly cancels pure-async awaitables.

    Note: ``asyncio.wait_for`` cannot interrupt a blocked SYNC thread
    started via ``asyncio.to_thread`` — Python threads aren't
    cancellable once running. For sync collectors, protection is the
    per-subprocess ``timeout`` inside ``_run_command`` (2 s), which is
    exercised implicitly by the "swallows failing subquery" test.
    """
    import asyncio

    _patch_orient_sources(monkeypatch)
    monkeypatch.setattr(api_main, "ORIENT_SECTION_HARD_TIMEOUT_S", 0.1)

    async def hang_forever():
        await asyncio.sleep(5.0)
        return {"summary": {}}

    monkeypatch.setattr(api_main, "_collect_pipeline_orient_data", hang_forever)

    start = time.perf_counter()
    response = client.get("/api/orient")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert elapsed < 1.0, f"orient should short-circuit, took {elapsed}s"
    data = response.json()
    assert "section_timeout" in data["pipeline"]["error"]
    # Other sections must still populate — failure isolation is the point.
    assert data["runtime"]["agents"] == ["codex"]


def test_orient_errors_are_not_cached(monkeypatch):
    """A transient error must not poison the cache for the full TTL window.

    Next call after an error should retry, not repeat the stale error.
    """
    _patch_orient_sources(monkeypatch)
    attempts = {"n": 0}

    def flaky_git():
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("first-call boom")
        return {"branch": "main", "head": "abc123"}

    monkeypatch.setattr(api_main, "_collect_git_orient_data", flaky_git)

    first = client.get("/api/orient")
    second = client.get("/api/orient")

    assert first.json()["git"]["error"] == "first-call boom"
    assert "error" not in second.json()["git"]
    assert second.json()["git"]["head"] == "abc123"
    assert attempts["n"] == 2


def test_orient_issues_errors_are_not_cached(monkeypatch):
    """Regression for GH #1309 / reviewer BLOCKER B1/C3.

    The first P0 commit for #1309 swallowed collector exceptions inside
    ``_collect_issues_orient_data`` and returned ``{"issues": [],
    "issues_error": ...}`` as a "successful" value. That value was then
    cached for the full 120 s TTL — a transient ``gh`` blip poisoned
    the endpoint for two minutes.

    Fix: the collector now raises and the ``_cached_orient_section``
    error branch does not call ``cache_set``. This test asserts the
    second call re-invokes the collector and returns a fresh payload.
    """
    _patch_orient_sources(monkeypatch)
    attempts = {"n": 0}

    def flaky_issues():
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("gh rate limited")
        return {"issues": [{"number": 1309}]}

    monkeypatch.setattr(api_main, "_collect_issues_orient_data", flaky_issues)

    first = client.get("/api/orient").json()
    second = client.get("/api/orient").json()

    # First call: error surfaced both top-level and in meta; payload is fallback.
    assert first["issues"] == []
    assert first["issues_error"] == "gh rate limited"
    assert first["meta"]["issues"]["error"].startswith("RuntimeError:")

    # Second call: collector retried, fresh payload, no leftover error.
    assert second["issues"] == [{"number": 1309}]
    assert "issues_error" not in second
    assert "error" not in second["meta"]["issues"]
    assert attempts["n"] == 2


def test_orient_fresh_query_bypasses_cache(monkeypatch):
    """`?fresh=true` must invalidate every orient_* cache entry.

    Regression for GH #1309 / reviewer BLOCKER B3: an agent that just
    made a commit needs a way to see its own work without waiting up
    to 30 s for the git TTL to expire.
    """
    _patch_orient_sources(monkeypatch)
    calls = {"git": 0}

    def counting_git():
        calls["git"] += 1
        return {"branch": "main", "head": f"abc{calls['git']}"}

    monkeypatch.setattr(api_main, "_collect_git_orient_data", counting_git)

    client.get("/api/orient")
    client.get("/api/orient")  # cache hit, collector not called
    client.get("/api/orient?fresh=true")  # bypasses cache

    assert calls["git"] == 2


def test_orient_pipeline_section_skips_orient_layer_cache(monkeypatch):
    """Pipeline must NOT be cached at the orient layer.

    Regression for GH #1309 / reviewer BLOCKER B2: ``pipeline`` wraps
    ``state_summary()`` which already has its own 60 s cache. A second
    cache at the orient layer stacks the windows and can label up to
    119 s old data as fresh. We avoid this by setting TTL to 0 for
    pipeline — the collector runs on every request.
    """
    _patch_orient_sources(monkeypatch)

    calls = {"pipeline": 0}

    async def counting_pipeline():
        calls["pipeline"] += 1
        return {"summary": {"run": calls["pipeline"]}}

    monkeypatch.setattr(api_main, "_collect_pipeline_orient_data", counting_pipeline)

    client.get("/api/orient")
    client.get("/api/orient")
    client.get("/api/orient")

    assert calls["pipeline"] == 3, (
        "pipeline collector must run on every orient call (TTL=0)"
    )
    # And the meta must always say miss, never hit.
    data = client.get("/api/orient").json()
    assert data["meta"]["pipeline"]["cache"] == "miss"


def test_orient_generated_at_floor_reflects_oldest_section(monkeypatch):
    """Top-level ``generated_at`` is the oldest section's timestamp.

    Regression for GH #1309 / reviewer CONCERN C1: request time was
    misleading — a fully cached response with 90 s old data was
    reporting ``generated_at = <now>``. Now the top-level field is
    the floor across every section.
    """
    _patch_orient_sources(monkeypatch)

    # Warm the cache so sections have distinct generated_at timestamps
    # that are older than "now".
    client.get("/api/orient")
    time.sleep(0.05)  # ensure measurable delta on the second call
    second = client.get("/api/orient").json()

    section_timestamps = [
        m["generated_at"] for m in second["meta"].values() if m.get("generated_at")
    ]
    assert section_timestamps, "every section should have generated_at"
    # Top-level must equal the minimum — NOT be the newest "now" stamp.
    assert second["generated_at"] == min(section_timestamps)
