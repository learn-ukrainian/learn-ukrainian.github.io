"""Tests for the /api/orient endpoint."""

from __future__ import annotations

import asyncio
import contextlib
import os
import subprocess
import time
from pathlib import Path

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
    # Scrub git-hook redirection vars from the PROCESS env too: the collector's
    # child git processes inherit os.environ, and under a `git commit` hook
    # (pre-commit affected-file pytest) GIT_DIR/GIT_INDEX_FILE point at the
    # committing checkout — `git branch --show-current` then reads a detached
    # worktree HEAD (empty) instead of the test repo. _clean_git_env() only
    # covers the test's OWN subprocesses.
    for key in list(os.environ):
        if key.startswith("GIT_") or key.startswith("PRE_COMMIT"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(api_main, "_collect_git_orient_data", lambda: {"branch": "main", "head": "abc123"})
    monkeypatch.setattr(api_main, "_collect_issues_orient_data", lambda: {"issues": [{"number": 1186}]})

    async def fake_pipeline():
        return {"summary": {"totals": {"total": 1}}}

    monkeypatch.setattr(api_main, "_collect_pipeline_orient_data", fake_pipeline)
    monkeypatch.setattr(
        api_main,
        "_collect_runtime_orient_data",
        lambda: {
            "agents": ["codex"],
            "recent_outcomes": {"ok": 1, "error": 0, "rate_limited": 0},
            "headroom": {"codex": True},
        },
    )
    monkeypatch.setattr(api_main, "_collect_delegate_orient_data", lambda: {"active_count": 0, "recent": []})
    monkeypatch.setattr(api_main, "_collect_bridge_pending_orient_data", lambda: {})
    monkeypatch.setattr(
        api_main,
        "_collect_rollovers_orient_data",
        lambda: {"counts": {"total": 0, "live_pending": 0}, "actionable": [], "errors": []},
    )
    monkeypatch.setattr(
        api_main, "_collect_wiki_orient_data", lambda: {"by_track": {"hist": {"compiled": 1, "total": 2, "pct": 50.0}}}
    )
    monkeypatch.setattr(
        api_main,
        "_collect_health_orient_data",
        lambda: {"api": True, "mcp_rag": False, "sources_db": True, "message_broker": True},
    )
    monkeypatch.setattr(
        api_main,
        "_collect_session_hints_orient_data",
        lambda: [{"file": "docs/session-state/example.md", "first_line": "# Example"}],
    )


def _clean_git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and not key.startswith("PRE_COMMIT")
    }


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=_clean_git_env(),
    )


def _init_orient_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(repo)],
        check=True,
        capture_output=True,
        text=True,
        env=_clean_git_env(),
    )
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "tracked.txt").write_text("clean\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def test_orient_returns_all_top_level_keys(monkeypatch):
    _patch_orient_sources(monkeypatch)

    response = client.get("/api/orient")

    assert response.status_code == 200
    data = response.json()
    expected = {
        "generated_at",
        "git",
        "issues",
        "pipeline",
        "runtime",
        "delegate",
        "bridge_pending",
        "rollovers",
        "wiki",
        "health",
        "session_hints",
    }
    assert expected <= set(data)


def test_parse_orient_sections_lean_preset_excludes_heavy_sections():
    # The lean cold-start preset returns only the lightweight sections; the heavy
    # pipeline/issues/wiki are excluded (fetched on demand). Tested at the pure-function
    # level: the /api/orient handler is a thin passthrough to this selector.
    lean = api_main._parse_orient_sections(None, lean=True)
    assert lean == list(api_main.LEAN_ORIENT_SECTIONS)
    assert not ({"pipeline", "issues", "wiki"} & set(lean))
    assert {"git", "delegate", "rollovers", "governance", "health", "session_hints"} <= set(lean)


def test_parse_orient_sections_explicit_list_overrides_lean():
    # An explicit sections list always wins over the lean preset...
    assert api_main._parse_orient_sections("pipeline", lean=True) == ["pipeline"]
    # ...and with neither lean nor an explicit list, the full payload is returned.
    assert api_main._parse_orient_sections(None, lean=False) == list(api_main.ORIENT_SECTION_KEYS)


def test_orient_git_exposes_primary_checkout_dirty_signal(monkeypatch, tmp_path):
    original_git_collector = api_main._collect_git_orient_data
    repo = _init_orient_git_repo(tmp_path)
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    _patch_orient_sources(monkeypatch)
    monkeypatch.setattr(api_main, "PROJECT_ROOT", repo)
    # Release-mode split (#4931): git probes target the live checkout, so the
    # collector reads LIVE_REPO_ROOT — patch it where used alongside PROJECT_ROOT.
    monkeypatch.setattr(api_main, "LIVE_REPO_ROOT", repo)
    monkeypatch.setattr(api_main, "_collect_git_orient_data", original_git_collector)

    response = client.get("/api/orient?fresh=true")

    assert response.status_code == 200
    git_info = response.json()["git"]
    assert git_info["primary_checkout_dirty"] is True
    assert git_info["primary_checkout"]["checked_cwd"] == str(repo)
    assert git_info["primary_checkout"]["tracked_dirty_count"] == 1
    assert git_info["primary_checkout"]["entries"] == [{"xy": " M", "path": "tracked.txt", "kind": "tracked"}]


def test_orient_git_survives_primary_checkout_probe_failure(monkeypatch, tmp_path):
    original_git_collector = api_main._collect_git_orient_data
    repo = _init_orient_git_repo(tmp_path)
    _patch_orient_sources(monkeypatch)
    monkeypatch.setattr(api_main, "PROJECT_ROOT", repo)
    # Release-mode split (#4931): see the dirty-signal test above.
    monkeypatch.setattr(api_main, "LIVE_REPO_ROOT", repo)
    monkeypatch.setattr(api_main, "_collect_git_orient_data", original_git_collector)

    from scripts.guardrails import worktree_containment

    def broken_primary_status(_start):
        raise RuntimeError("git status failed")

    monkeypatch.setattr(
        worktree_containment,
        "primary_checkout_dirty_status",
        broken_primary_status,
    )

    response = client.get("/api/orient?fresh=true")

    assert response.status_code == 200
    git_info = response.json()["git"]
    assert git_info["branch"]
    assert git_info["head"]
    assert git_info["primary_checkout_dirty"] is False
    assert git_info["primary_checkout"]["error"] == "git status failed"
    assert git_info["primary_checkout"]["checked_cwd"] == str(repo)


def test_health_includes_core_bare_canary():
    """#2842: the health section surfaces the git core.bare detection canary."""
    health = api_main._collect_health_orient_data()
    assert "git_core_bare_ok" in health
    # This repo has a working tree, so core.bare must be false → canary reports ok.
    assert health["git_core_bare_ok"] is True


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


def test_orient_includes_bridge_pending_field(monkeypatch):
    _patch_orient_sources(monkeypatch)
    monkeypatch.setattr(
        api_main,
        "_collect_bridge_pending_orient_data",
        lambda: {"claude": {"count": 1, "oldest_hours": 6.5}},
    )

    response = client.get("/api/orient")

    assert response.status_code == 200
    data = response.json()
    assert data["bridge_pending"] == {"claude": {"count": 1, "oldest_hours": 6.5}}
    assert "bridge_pending" in data["meta"]


def test_orient_includes_actionable_rollovers(monkeypatch):
    _patch_orient_sources(monkeypatch)
    expected = {
        "counts": {"total": 4, "live_pending": 3},
        "actionable": [{"agent": "codex", "rollover_id": "rollover-a"}],
        "errors": [],
    }
    monkeypatch.setattr(api_main, "_collect_rollovers_orient_data", lambda: expected)

    response = client.get("/api/orient")

    assert response.status_code == 200
    assert response.json()["rollovers"] == expected
    assert "rollovers" in response.json()["meta"]


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


def test_orient_runtime_survives_default_executor_saturation(monkeypatch):
    """Orient sync sections must not depend on the shared default executor.

    Regression for the CI-only failure seen after the telemetry follow-up:
    another part of the suite had already saturated the event loop's
    default ``asyncio.to_thread`` pool, so lowering
    ``ORIENT_SECTION_HARD_TIMEOUT_S`` to 0.1 s caused the trivial
    runtime collector to time out before it even started. Orient now
    uses its own executor for sync collectors, so shared-pool backlog
    must not strip the ``runtime.agents`` payload.
    """

    _patch_orient_sources(monkeypatch)
    monkeypatch.setattr(api_main, "ORIENT_SECTION_HARD_TIMEOUT_S", 0.1)

    def block_default_executor():
        time.sleep(0.5)

    async def exercise() -> dict:
        blockers = [
            asyncio.create_task(
                asyncio.wait_for(
                    asyncio.to_thread(block_default_executor),
                    timeout=0.01,
                )
            )
            for _ in range(64)
        ]
        await asyncio.sleep(0.05)
        try:
            runtime, meta = await api_main._cached_orient_section(
                "runtime",
                api_main._collect_runtime_orient_data,
                {},
            )
            return {"runtime": runtime, "meta": meta}
        finally:
            for task in blockers:
                with contextlib.suppress(Exception):
                    await task

    result = asyncio.run(exercise())

    assert result["runtime"]["agents"] == ["codex"]
    assert result["meta"]["cache"] == "miss"
    assert "error" not in result["meta"]


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

    assert calls["pipeline"] == 3, "pipeline collector must run on every orient call (TTL=0)"
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

    section_timestamps = [m["generated_at"] for m in second["meta"].values() if m.get("generated_at")]
    assert section_timestamps, "every section should have generated_at"
    # Top-level must equal the minimum — NOT be the newest "now" stamp.
    assert second["generated_at"] == min(section_timestamps)


def test_orient_sections_subset_runs_only_selected_collectors(monkeypatch):
    """``?sections=`` must skip uncalled collectors entirely."""
    _patch_orient_sources(monkeypatch)
    calls: dict[str, int] = {"git": 0, "runtime": 0, "wiki": 0}

    def counting_git():
        calls["git"] += 1
        return {"branch": "main", "head": "abc123"}

    def counting_runtime():
        calls["runtime"] += 1
        return {
            "agents": ["codex"],
            "recent_outcomes": {"ok": 1, "error": 0, "rate_limited": 0},
            "headroom": {"codex": True},
        }

    def counting_wiki():
        calls["wiki"] += 1
        return {"by_track": {}}

    monkeypatch.setattr(api_main, "_collect_git_orient_data", counting_git)
    monkeypatch.setattr(api_main, "_collect_runtime_orient_data", counting_runtime)
    monkeypatch.setattr(api_main, "_collect_wiki_orient_data", counting_wiki)

    response = client.get("/api/orient?sections=git,runtime&fresh=true")

    assert response.status_code == 200
    data = response.json()
    # _telemetry is appended only when a session transcript is resolvable
    # (dev machines with ~/.claude transcripts; absent on CI) — exclude it so
    # the section-selection assertion stays hermetic across environments.
    assert set(data) - {"_telemetry"} == {"generated_at", "git", "runtime", "meta"}
    assert calls == {"git": 1, "runtime": 1, "wiki": 0}


def test_orient_unknown_section_returns_400(monkeypatch):
    _patch_orient_sources(monkeypatch)

    response = client.get("/api/orient?sections=git,not-a-section")

    assert response.status_code == 400
    assert "not-a-section" in response.json()["detail"]
    for key in api_main.ORIENT_SECTION_KEYS:
        assert key in response.json()["detail"]


def test_orient_default_sections_remain_full_payload(monkeypatch):
    _patch_orient_sources(monkeypatch)

    response = client.get("/api/orient?fresh=true")

    assert response.status_code == 200
    data = response.json()
    assert {
        "generated_at",
        "git",
        "issues",
        "pipeline",
        "runtime",
        "delegate",
        "bridge_pending",
        "rollovers",
        "wiki",
        "governance",
        "health",
        "session_hints",
        "meta",
    } <= set(data)


def test_orient_issues_collector_uses_five_second_subprocess_timeout(monkeypatch):
    captured: dict[str, float] = {}

    def fake_run_command(args, *, timeout: float = 2.0):
        captured["timeout"] = timeout
        raise RuntimeError("gh unavailable for timeout assertion")

    monkeypatch.setattr(api_main, "_run_command", fake_run_command)

    with pytest.raises(RuntimeError, match="gh unavailable"):
        api_main._collect_issues_orient_data()

    assert captured["timeout"] == 5.0
