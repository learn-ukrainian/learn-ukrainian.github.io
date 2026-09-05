"""Regression tests for duplicate agent names in runtime agent listings.

Issue #7082: ``/api/runtime/agents`` (and ``/api/orient`` ``runtime.agents``,
which shares the same source list) surfaced ``deepseek`` twice because the
alternate-harness ``hermes_deepseek`` adapter re-exports the fleet name
``deepseek``. Alternate-harness adapters (``hermes_*``) are ask-hermes-only
and must not appear as separate fleet agents.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from scripts.api.main import app
from scripts.api.monitor_context import production_context
from scripts.api.runtime_router import list_runtime_agents

client = TestClient(app, raise_server_exceptions=False)


def test_list_runtime_agents_names_are_unique():
    agents = list_runtime_agents(production_context())

    names = [agent["name"] for agent in agents]
    assert len(names) == len(set(names)), f"duplicate agent names: {sorted(names)}"


def test_agents_endpoint_names_are_unique_with_single_deepseek():
    response = client.get("/api/runtime/agents")

    assert response.status_code == 200
    agents = response.json()["agents"]
    names = [agent["name"] for agent in agents]
    assert len(names) == len(set(names)), f"duplicate agent names: {sorted(names)}"
    assert names.count("deepseek") == 1


def test_agents_endpoint_excludes_retired_cli_lanes():
    response = client.get("/api/runtime/agents")
    assert response.status_code == 200
    names = {agent["name"] for agent in response.json()["agents"]}
    assert "gemini" not in names
    assert "glm" not in names
    assert "agy" in names
    assert "cursor" in names
