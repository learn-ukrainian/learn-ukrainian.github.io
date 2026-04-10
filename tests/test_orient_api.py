"""Tests for the /api/orient endpoint."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

import scripts.api.main as api_main

client = TestClient(api_main.app, raise_server_exceptions=False)


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
