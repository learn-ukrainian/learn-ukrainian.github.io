"""Hermetic tests for the worktree GC sweep loop in the Monitor API server."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import scripts.api.main as api_main
import scripts.api.state_helpers as state_helpers
from scripts.orchestration.reap_worktrees import ReapResult

client = TestClient(api_main.app, raise_server_exceptions=False)


def _patch_orient_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch non-runtime sources to keep orient fast and hermetic
    monkeypatch.setattr(api_main, "_collect_git_orient_data", lambda: {"branch": "main"})
    monkeypatch.setattr(api_main, "_collect_issues_orient_data", lambda: {"issues": []})

    async def fake_pipeline():
        return {"summary": {}}

    monkeypatch.setattr(api_main, "_collect_pipeline_orient_data", fake_pipeline)
    monkeypatch.setattr(api_main, "_collect_delegate_orient_data", lambda: {})
    monkeypatch.setattr(api_main, "_collect_wiki_orient_data", lambda: {"by_track": {}})
    monkeypatch.setattr(
        api_main,
        "_collect_governance_orient_data",
        lambda: {
            "decisions_total": 0,
            "decisions_stale": 0,
            "decisions_approaching_expiry": 0,
            "adrs_total": 0,
            "adrs_warnings": 0,
            "adrs_errors": 0,
        },
    )
    monkeypatch.setattr(api_main, "_collect_health_orient_data", lambda: {"api": True})
    monkeypatch.setattr(api_main, "_collect_session_hints_orient_data", lambda: [])

    # Patch runtime API dependencies
    monkeypatch.setattr(api_main.runtime_api, "list_runtime_agents", lambda: [])
    monkeypatch.setattr(api_main.runtime_api, "runtime_recent_outcomes_today", lambda: [])


@pytest.fixture(autouse=True)
def setup_teardown(monkeypatch: pytest.MonkeyPatch):
    # Reset global GC variables
    api_main._last_gc_sweep_summary = None
    api_main._gc_sweep_thread = None
    state_helpers.cache_invalidate("worktree_gc_sweep")

    # Force ONLY the GC sweep thread to run synchronously in tests
    original_start = threading.Thread.start
    def fake_start(self):
        target = getattr(self, "_target", None)
        if target and getattr(target, "__name__", None) == "_run_worktree_gc_sweep":
            self._target(*self._args, **self._kwargs)
        else:
            original_start(self)
    monkeypatch.setattr(threading.Thread, "start", fake_start)

    yield


def test_gc_sweep_disabled_by_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC", "0")
    _patch_orient_sources(monkeypatch)

    response = client.get("/api/orient?fresh=true")
    assert response.status_code == 200
    data = response.json()
    assert "worktree_gc" not in data.get("runtime", {})
    assert api_main._last_gc_sweep_summary is None


def test_gc_sweep_runs_and_exposes_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC", "1")
    _patch_orient_sources(monkeypatch)

    # Mock reap_worktrees to return a controlled set of results
    fake_results = [
        ReapResult(path="/wt/1", branch="b1", action="removed", reason="merged", dirty=False),
        ReapResult(path="/wt/2", branch="b2", action="removed", reason="merged", dirty=False),
        ReapResult(path="/wt/3", branch="b3", action="skipped", reason="dirty", dirty=True),
        ReapResult(path="/wt/4", branch="b4", action="error", reason="fail", dirty=False, error="err"),
    ]

    monkeypatch.setattr(api_main, "reap_worktrees", lambda **kwargs: fake_results)
    monkeypatch.setattr(api_main, "primary_checkout_root", lambda path: Path("/dummy"))

    response = client.get("/api/orient?fresh=true")
    assert response.status_code == 200
    data = response.json()
    runtime = data["runtime"]
    assert "worktree_gc" in runtime
    summary = runtime["worktree_gc"]
    assert summary["removed"] == 2
    assert summary["skipped"] == 1
    assert summary["errors"] == 1
    assert "time" in summary


def test_gc_sweep_respects_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC", "1")
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC_INTERVAL_MIN", "60")
    _patch_orient_sources(monkeypatch)

    # First call returns 1 removed
    monkeypatch.setattr(
        api_main,
        "reap_worktrees",
        lambda **kwargs: [ReapResult(path="/wt/1", branch="b1", action="removed", reason="m", dirty=False)]
    )
    monkeypatch.setattr(api_main, "primary_checkout_root", lambda path: Path("/dummy"))

    response = client.get("/api/orient?fresh=true")
    assert response.json()["runtime"]["worktree_gc"]["removed"] == 1

    # Update return value to 5 removed, but sweep shouldn't run again due to TTL cache
    monkeypatch.setattr(
        api_main,
        "reap_worktrees",
        lambda **kwargs: [ReapResult(path=f"/wt/{i}", branch=f"b{i}", action="removed", reason="m", dirty=False) for i in range(5)]
    )
    response2 = client.get("/api/orient")
    assert response2.json()["runtime"]["worktree_gc"]["removed"] == 1

    # Invalidate sweep cache, now it should run and update
    state_helpers.cache_invalidate("worktree_gc_sweep")
    response3 = client.get("/api/orient?fresh=true")
    assert response3.json()["runtime"]["worktree_gc"]["removed"] == 5
