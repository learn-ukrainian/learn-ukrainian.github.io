"""#7269 step 11: contracts router routes read MonitorContext."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.monitor_context import fixture_context
from scripts.api.route_contracts import router


def _client_for(root: Path) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(root)
    app.include_router(router, prefix="/api/contracts")
    return TestClient(app)


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
