"""Tests for the /api/orient endpoint."""

from __future__ import annotations

import asyncio
import contextlib
import os
import subprocess
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import scripts.api.main as api_main
import scripts.api.state_helpers as state_helpers
from tests.latency_budget import assert_under_budget

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
    api_main.reset_detached_orient_state_for_tests()
    yield
    keys_to_drop = [k for k in state_helpers._ttl_cache if k.startswith("orient_")]
    for key in keys_to_drop:
        state_helpers._ttl_cache.pop(key, None)
    api_main.reset_detached_orient_state_for_tests()


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
    monkeypatch.setattr(api_main, "_collect_git_orient_data", lambda ctx=None: {"branch": "main", "head": "abc123"})
    monkeypatch.setattr(api_main, "_collect_issues_orient_data", lambda ctx=None: {"issues": [{"number": 1186}]})
    monkeypatch.setattr(api_main, "_collect_idle_prs_orient_data", lambda ctx=None: {"idle_prs": []})

    async def fake_pipeline(ctx=None):
        return {"summary": {"totals": {"total": 1}}}

    monkeypatch.setattr(api_main, "_collect_pipeline_orient_data", fake_pipeline)
    monkeypatch.setattr(
        api_main,
        "_collect_runtime_orient_data",
        lambda ctx=None: {
            "agents": ["codex"],
            "recent_outcomes": {"ok": 1, "error": 0, "rate_limited": 0},
            "headroom": {"codex": True},
        },
    )
    monkeypatch.setattr(api_main, "_collect_delegate_orient_data", lambda ctx=None: {"active_count": 0, "recent": []})
    monkeypatch.setattr(
        api_main,
        "_collect_capacity_orient_data",
        lambda ctx=None: {
            "lanes": {
                "codex": {"in_flight": 0, "healthy": True, "burn_pct_7d": 10.0, "remaining_pct": 90.0, "status": "cool"}
            },
            "primary_recommendation": "codex",
        },
    )
    monkeypatch.setattr(api_main, "_collect_bridge_pending_orient_data", lambda ctx=None: {})
    monkeypatch.setattr(
        api_main,
        "_collect_rollovers_orient_data",
        lambda ctx=None: {"counts": {"total": 0, "live_pending": 0}, "actionable": [], "errors": []},
    )
    monkeypatch.setattr(
        api_main,
        "_collect_wiki_orient_data",
        lambda ctx=None: {"by_track": {"hist": {"compiled": 1, "total": 2, "pct": 50.0}}},
    )
    monkeypatch.setattr(
        api_main,
        "_collect_health_orient_data",
        lambda ctx=None: {
            "api": True,
            "mcp_sources": False,
            "mcp_rag": False,
            "sources_db": True,
            "message_broker": True,
        },
    )
    monkeypatch.setattr(
        api_main,
        "_collect_session_hints_orient_data",
        lambda ctx=None: [{"file": "docs/session-state/example.md", "first_line": "# Example"}],
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
        timeout=30,
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
        timeout=30,
    )
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(
        repo,
        "remote",
        "add",
        "origin",
        "https://github.com/learn-ukrainian/learn-ukrainian.github.io.git",
    )
    (repo / "tracked.txt").write_text("clean\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def test_health_canaries_do_not_apply_general_repairs(monkeypatch):
    import scripts.audit.check_primary_integrity as primary_check
    import scripts.audit.check_self_symlinks as symlink_check

    fix_values: list[bool] = []

    def check_symlinks(_repo: Path, *, fix: bool):
        fix_values.append(fix)
        return False, "loop detected"

    def check_primary(_repo: Path, *, fix: bool, tasks_dir: Path):
        assert tasks_dir.name == "tasks"
        fix_values.append(fix)
        return False, "primary detached"

    monkeypatch.setattr(symlink_check, "check_self_symlinks", check_symlinks)
    monkeypatch.setattr(primary_check, "check_primary_integrity", check_primary)

    assert api_main._self_symlink_canary() is False
    assert api_main._primary_integrity_canary() is False
    assert fix_values == [False, False]


def test_orient_swallows_failing_subquery(monkeypatch):
    _patch_orient_sources(monkeypatch)

    def broken_git(ctx=None):
        raise RuntimeError("git failed")

    monkeypatch.setattr(api_main, "_collect_git_orient_data", broken_git)

    response = client.get("/api/orient")

    assert response.status_code == 200
    data = response.json()
    assert data["git"]["error"] == "git failed"
    assert data["runtime"]["agents"] == ["codex"]


def test_orient_hard_timeout_isolates_async_collector(monkeypatch):
    """A hung ASYNC collector caps at the per-section hard timeout.

    This covers the live-reproduced BLOCKER from the first baseline
    run: the async pipeline collector could block the whole response.
    ``asyncio.wait_for`` properly cancels pure-async awaitables.

    Both sections use async collectors here so failure isolation does
    not depend on sync executor scheduling within the 0.1 s budget.
    Sync runtime scheduling is covered separately by
    ``test_orient_runtime_survives_default_executor_saturation``.
    """
    import asyncio

    _patch_orient_sources(monkeypatch)
    monkeypatch.setattr(api_main, "ORIENT_SECTION_HARD_TIMEOUT_S", 0.1)

    async def hang_forever(ctx=None):
        await asyncio.sleep(5.0)
        return {"summary": {}}

    monkeypatch.setattr(api_main, "_collect_pipeline_orient_data", hang_forever)

    async def immediate_runtime(ctx=None):
        return {"agents": ["codex"]}

    section_specs = api_main._orient_section_specs()
    section_specs["runtime"] = (immediate_runtime, {}, True)
    monkeypatch.setattr(api_main, "_orient_section_specs", lambda: section_specs)

    start = time.perf_counter()
    response = client.get("/api/orient?sections=pipeline,runtime")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert_under_budget(elapsed, 1.0, f"orient should short-circuit, took {elapsed}s")
    data = response.json()
    assert "section_timeout" in data["pipeline"]["error"]
    # The independent async section must still populate.
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

    def flaky_issues(ctx=None):
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

    def counting_git(ctx=None):
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

    async def counting_pipeline(ctx=None):
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


def test_lean_orient_hung_capacity_and_health_do_not_stall_other_sections(monkeypatch):
    """#6983: a hung CodexBar/canary must not pin lean orient at the 5 s wall.

    ``asyncio.gather`` waits for the slowest section. Before the detached
    refresh, a 5 s ``section_timeout`` on ``capacity`` or ``health`` made
    the whole lean payload take 5.0 s. Other lean sections must still
    populate, and the request must finish well under the 10 s global
    timeout.
    """
    _patch_orient_sources(monkeypatch)
    release = threading.Event()

    def hang_capacity(ctx=None):
        release.wait(8)
        return {"lanes": {"codex": {"in_flight": 0, "healthy": True}}}

    def hang_health(ctx=None):
        release.wait(8)
        return {"api": True}

    monkeypatch.setattr(api_main, "_collect_capacity_orient_data", hang_capacity)
    monkeypatch.setattr(api_main, "_collect_health_orient_data", hang_health)

    start = time.perf_counter()
    try:
        response = client.get("/api/orient?lean=true")
        elapsed = time.perf_counter() - start
        assert response.status_code == 200
        assert_under_budget(
            elapsed,
            1.5,
            f"lean orient stalled on capacity/health, took {elapsed:.3f}s",
        )
        data = response.json()
        assert data["git"]["branch"] == "main"
        assert data["runtime"]["agents"] == ["codex"]
        assert data["delegate"]["active_count"] == 0
        assert "error" in data["meta"]["capacity"]
        assert "error" in data["meta"]["health"]
        assert data["capacity"].get("lanes") == {}
        assert data["health"].get("api") is True
        assert "section_timeout" not in str(data["meta"]["capacity"].get("error", ""))
    finally:
        release.set()


def test_lean_orient_hung_delegate_and_rollovers_do_not_stall(monkeypatch):
    """#10866: a hung delegate or rollover collector must not pin lean orient.

    Same release-event pattern as the capacity/health stall test: the
    collectors wait with a timeout, and the test sets the event on the
    way out so the detached threads do not outlive the case.
    """
    _patch_orient_sources(monkeypatch)
    release = threading.Event()
    entered = {"delegate": 0, "rollovers": 0}
    delegate_cached = {"active_count": 7, "recent": [{"task_id": "detached-delegate-10866"}]}
    rollovers_cached = {
        "counts": {"total": 1, "marker": "detached-rollover-10866"},
        "actionable": [{"id": "detached-rollover-10866"}],
        "errors": [],
    }

    def hang_delegate(ctx=None):
        entered["delegate"] += 1
        release.wait(8)
        return delegate_cached

    def hang_rollovers(ctx=None):
        entered["rollovers"] += 1
        release.wait(8)
        return rollovers_cached

    monkeypatch.setattr(api_main, "_collect_delegate_orient_data", hang_delegate)
    monkeypatch.setattr(api_main, "_collect_rollovers_orient_data", hang_rollovers)

    sequence_start = time.perf_counter()
    try:
        start = time.perf_counter()
        response = client.get("/api/orient?lean=true")
        elapsed = time.perf_counter() - start
        assert response.status_code == 200
        assert_under_budget(
            elapsed,
            1.5,
            f"lean orient stalled on delegate/rollovers, took {elapsed:.3f}s",
        )
        data = response.json()
        assert data["git"]["branch"] == "main"
        assert data["runtime"]["agents"] == ["codex"]
        assert data["capacity"]["lanes"]["codex"]["status"] == "cool"
        assert data["health"]["api"] is True
        assert data["session_hints"][0]["file"] == "docs/session-state/example.md"
        assert "bridge_pending" in data
        assert "governance" in data
        assert data["delegate"]["active_count"] == 0
        assert data["rollovers"]["actionable"] == []
        for key in ("delegate", "rollovers"):
            assert "section_timeout" not in str(data["meta"][key].get("error", ""))

        release.set()
        with api_main._detached_orient_lock:
            refresh_threads = list(api_main._detached_orient_threads.values())
        for thread in refresh_threads:
            thread.join(timeout=2.0)
            assert not thread.is_alive()
        assert entered == {"delegate": 1, "rollovers": 1}
        stored_at = time.perf_counter()

        release.clear()
        start = time.perf_counter()
        cached = client.get("/api/orient?lean=true")
        cached_elapsed = time.perf_counter() - start
        assert cached.status_code == 200
        assert_under_budget(
            cached_elapsed,
            1.0,
            f"warm lean orient waited on a re-blocked collector, took {cached_elapsed:.3f}s",
        )
        assert cached_elapsed < 8, "second request waited out the re-blocked collector"
        assert time.perf_counter() - stored_at < api_main.ORIENT_SECTION_TTLS["rollovers"]
        assert time.perf_counter() - sequence_start < api_main.ORIENT_SECTION_TTLS["rollovers"]
        assert entered == {"delegate": 1, "rollovers": 1}
        warm = cached.json()
        assert warm["delegate"] == delegate_cached
        assert warm["rollovers"] == rollovers_cached
        assert warm["meta"]["delegate"]["cache"] == "hit"
        assert warm["meta"]["rollovers"]["cache"] == "hit"
    finally:
        release.set()


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"], ids=["NEL", "LS", "PS"])
def test_orient_recent_commits_keep_unicode_separators_inside_subjects(monkeypatch, tmp_path, separator):
    # #9556: ``git log --oneline`` has one record per physical line.
    repo = _init_orient_git_repo(tmp_path)
    _git(repo, "commit", "-q", "--allow-empty", "-m", f"first{separator}tail")
    original_git_collector = api_main._collect_git_orient_data
    _patch_orient_sources(monkeypatch)
    ctx = api_main.production_context().with_roots(project_root=repo, live_repo_root=repo)

    commits = original_git_collector(ctx)["recent_commits"]

    assert [commit["subject"] for commit in commits] == [f"first{separator}tail", "init"]
    assert commits[0]["sha"] == _git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
