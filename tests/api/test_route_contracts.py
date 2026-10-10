"""Fleet board contracts stay distinct from the fleet-comms observer."""

import pytest

from scripts.api.fleet_board.router import endpoint_index
from scripts.api.main import app
from scripts.api.route_contracts import contract_for_route


@pytest.mark.parametrize("path", [row["path"] for row in endpoint_index(app)])
def test_fleet_board_routes_use_host_local_v1_contract(path: str) -> None:
    contract = contract_for_route(path)

    assert contract is not None
    assert contract.pattern == "/api/fleet/v1"
    assert contract.match == "prefix"
    assert contract.locality == "host_affine"
    assert contract.response_schema_version == "fleet.v1"
    assert contract.mutates is False
    assert "local roster and harness snapshots" in contract.source_of_truth
    assert "in-process delegate and occupancy" in contract.source_of_truth


@pytest.mark.parametrize("path", ["/api/fleet", "/api/fleet/requests", "/api/fleet/v10/now"])
def test_fleet_comms_routes_keep_observer_contract(path: str) -> None:
    contract = contract_for_route(path)

    assert contract is not None
    assert contract.pattern == "/api/fleet"
    assert contract.locality == "cluster_authoritative"
    assert contract.response_schema_version == "comms.v2"
