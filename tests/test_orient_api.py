"""Tests for the /api/orient endpoint."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import lu_machinery.api.main as api_main
import lu_machinery.api.state_helpers as state_helpers
import pytest
from fastapi.testclient import TestClient

import scripts.project_api.orient as product_orient

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

    monkeypatch.setattr(product_orient, "collect_pipeline_orient_data", fake_pipeline)
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
    monkeypatch.setattr(
        api_main,
        "_collect_rollovers_orient_data",
        lambda ctx=None: {"counts": {"total": 0, "live_pending": 0}, "actionable": [], "errors": []},
    )
    monkeypatch.setattr(
        product_orient,
        "collect_wiki_orient_data",
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
    import lu_machinery.hygiene.check_primary_integrity as primary_check
    import lu_machinery.hygiene.check_self_symlinks as symlink_check

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

    monkeypatch.setattr(product_orient, "collect_pipeline_orient_data", counting_pipeline)

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
