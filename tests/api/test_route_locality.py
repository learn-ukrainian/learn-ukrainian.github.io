"""Tests for route locality and machine-readable contract fields (#7365)."""

from __future__ import annotations

from pathlib import Path
from typing import get_args

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.monitor_context import fixture_context
from scripts.api.route_contracts import (
    ROUTE_CONTRACTS,
    RouteContract,
    RouteLocality,
    contract_for_route,
    router,
)

pytestmark = pytest.mark.repo_invariant

VALID_LOCALITIES = set(get_args(RouteLocality))


def test_route_locality_type_definition() -> None:
    assert set(get_args(RouteLocality)) == {"host_affine", "cluster_authoritative", "mixed"}


def test_every_route_contract_declares_valid_locality() -> None:
    assert len(ROUTE_CONTRACTS) > 0
    for contract in ROUTE_CONTRACTS:
        assert isinstance(contract, RouteContract)
        assert contract.locality in VALID_LOCALITIES, (
            f"Route contract {contract.pattern} has invalid locality: {contract.locality!r}"
        )


def test_route_contract_to_dict_includes_locality() -> None:
    for contract in ROUTE_CONTRACTS:
        d = contract.to_dict()
        assert "locality" in d
        assert d["locality"] == contract.locality


def test_stamped_phase0_locality_assignments() -> None:
    """Verify stamped Phase 0 packet locality requirements."""
    # 1. host_affine: /api/health (uptime, checkout, process-local resilience)
    health_contract = contract_for_route("/api/health")
    assert health_contract is not None
    assert health_contract.locality == "host_affine"

    # 2. cluster_authoritative: /api/epics/v1, /api/fleet, /api/fleet/agents,
    # /api/runtime/routing-assignments, /api/cluster/readiness
    cluster_routes = [
        "/api/epics/v1",
        "/api/fleet",
        "/api/fleet/agents",
        "/api/runtime/routing-assignments",
        "/api/cluster/readiness",
    ]
    for path in cluster_routes:
        c = contract_for_route(path)
        assert c is not None, f"missing contract for {path}"
        assert c.locality == "cluster_authoritative", (
            f"expected {path} to be cluster_authoritative, got {c.locality}"
        )

    # 3. mixed: /api/session-streams, /api/fleet/operations, /api/comms,
    # /api/runtime, /api/orient, /api/discussions/active, /api/fleet/projects/v1, /api/fleet/workers/v1
    mixed_routes = [
        "/api/session-streams",
        "/api/fleet/operations",
        "/api/comms",
        "/api/runtime",
        "/api/orient",
        "/api/discussions/active",
        "/api/fleet/projects/v1",
        "/api/fleet/workers/v1",
    ]
    for path in mixed_routes:
        c = contract_for_route(path)
        assert c is not None, f"missing contract for {path}"
        assert c.locality == "mixed", (
            f"expected {path} to be mixed, got {c.locality}"
        )

    # 4. host_affine for process/worktree/telemetry local routes
    host_affine_routes = [
        "/api/delegate",
        "/api/worktrees",
        "/api/telemetry",
        "/api/agent-monitor/status",
        "/api/agent-monitor/register",
        "/api/coordination",
        "/api/git",
    ]
    for path in host_affine_routes:
        c = contract_for_route(path)
        assert c is not None, f"missing contract for {path}"
        assert c.locality == "host_affine", (
            f"expected {path} to be host_affine, got {c.locality}"
        )


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
