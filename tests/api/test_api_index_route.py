"""Tests for the /api root redirect and its route contracts (#7090)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from scripts.api.main import app
from scripts.api.route_contracts import contract_for_route

client = TestClient(app, raise_server_exceptions=False)


def test_get_api_root_redirects_to_docs() -> None:
    response = client.get("/api", follow_redirects=False)

    assert response.status_code in {307, 302}, (
        f"GET /api must redirect to /docs, got {response.status_code}"
    )
    assert response.headers["location"] == "/docs"


def test_get_api_root_redirect_target_serves_200() -> None:
    response = client.get("/api")

    assert response.status_code == 200
    assert response.url.path == "/docs"


def test_api_root_route_is_registered_as_get() -> None:
    paths = app.openapi()["paths"]

    assert "/api" in paths
    assert set(paths["/api"]) == {"get"}


def test_api_root_has_exact_route_contract() -> None:
    contract = contract_for_route("/api", "http")

    assert contract is not None
    assert contract.pattern == "/api"
    assert contract.match == "exact"
    assert "/docs" in contract.purpose
    assert contract.mutates is False


def test_fleet_agents_has_exact_route_contract() -> None:
    contract = contract_for_route("/api/fleet/agents", "http")

    assert contract is not None
    assert contract.pattern == "/api/fleet/agents"
    assert contract.match == "exact"
    assert contract.source_of_truth
    assert contract.freshness
    assert contract.recommendation
    assert contract.mutates is False


def test_contracts_registry_lists_api_root_and_fleet_agents() -> None:
    response = client.get("/api/contracts/routes")

    assert response.status_code == 200
    patterns = {item["pattern"] for item in response.json()["route_contracts"]}
    assert "/api" in patterns
    assert "/api/fleet/agents" in patterns
