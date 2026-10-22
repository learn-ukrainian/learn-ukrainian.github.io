"""Tests for route locality and machine-readable contract fields (#7365)."""

from __future__ import annotations

from pathlib import Path
from typing import get_args

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.monitor_context import fixture_context
from scripts.api.route_contracts import (
    RouteLocality,
    router,
)

pytestmark = pytest.mark.repo_invariant

VALID_LOCALITIES = set(get_args(RouteLocality))


def test_contracts_routes_endpoint_exposes_locality(tmp_path: Path) -> None:
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(router, prefix="/api/contracts")
    client = TestClient(app)

    resp = client.get("/api/contracts/routes")
    assert resp.status_code == 200
    data = resp.json()
    assert "route_contracts" in data
    for entry in data["route_contracts"]:
        assert "locality" in entry
        assert entry["locality"] in VALID_LOCALITIES
