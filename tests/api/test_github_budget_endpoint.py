"""App-factory coverage for the shared GitHub budget endpoint."""

from __future__ import annotations

from unittest.mock import Mock

from fastapi.testclient import TestClient

from scripts.api import main as api_main
from scripts.api import state_helpers, state_router
from scripts.api.monitor_context import fixture_context


def test_github_budget_endpoint_uses_app_factory_and_shared_cache(monkeypatch, tmp_path) -> None:
    state_helpers.cache_invalidate("github_graphql_budget")
    probe = Mock(return_value={
        "source": "graphql.rateLimit",
        "limit": 5000,
        "remaining": 17,
        "used": 4983,
        "reset_at": "2026-09-24T00:00:00Z",
        "exhausted": False,
        "error": None,
        "checked_at": "2026-09-23T00:00:00Z",
    })
    monkeypatch.setattr(state_router, "probe_graphql_budget", probe)
    app = api_main.create_app(fixture_context(tmp_path))

    with TestClient(app) as client:
        first = client.get("/api/state/github-budget")
        second = client.get("/api/state/github-budget")

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["source"] == "graphql.rateLimit"
    probe.assert_called_once_with()
    state_helpers.cache_invalidate("github_graphql_budget")
