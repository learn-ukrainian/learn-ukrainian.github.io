"""#7269 step 11: contracts router routes read MonitorContext."""

from __future__ import annotations

import inspect
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.monitor_context import fixture_context
from scripts.api.route_contracts import contract_for_route, router


def _client_for(root: Path) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(root)
    app.include_router(router, prefix="/api/contracts")
    return TestClient(app)


def test_contracts_routes_inject_monitor_context() -> None:
    for route in router.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            continue
        params = inspect.signature(endpoint).parameters
        assert "ctx" in params or "_ctx" in params, route.path


def test_contracts_routes_endpoint(tmp_path: Path) -> None:
    client = _client_for(tmp_path)
    response = client.get("/api/contracts/routes")
    assert response.status_code == 200
    data = response.json()
    assert "generated_at" in data
    assert "route_contracts" in data
    assert "page_contracts" in data
    assert len(data["route_contracts"]) > 0
    assert len(data["page_contracts"]) > 0


def test_contract_for_route_exact_and_prefix() -> None:
    assert contract_for_route("/api/contracts/routes") is not None
    assert contract_for_route("/api/unknown-nonexistent-path") is None
