"""Contract coverage tests for public Monitor routes and dashboard pages."""

from pathlib import Path

from fastapi.routing import APIRoute, APIWebSocketRoute
from fastapi.testclient import TestClient

from scripts.api.main import app
from scripts.api.route_contracts import contract_for_page, contract_for_route

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = ROOT / "dashboards"


def _public_http_routes() -> list[APIRoute]:
    return [route for route in app.routes if isinstance(route, APIRoute)]


def _public_websocket_routes() -> list[APIWebSocketRoute]:
    return [route for route in app.routes if isinstance(route, APIWebSocketRoute)]


def test_every_public_http_route_has_source_and_freshness_contract():
    missing = []
    incomplete = []
    for route in _public_http_routes():
        contract = contract_for_route(route.path, "http")
        if contract is None:
            missing.append(route.path)
            continue
        if not contract.source_of_truth or not contract.freshness or not contract.recommendation:
            incomplete.append(route.path)

    assert not missing, "HTTP routes without Monitor contracts:\n" + "\n".join(sorted(missing))
    assert not incomplete, "HTTP routes with incomplete contracts:\n" + "\n".join(sorted(incomplete))


def test_every_public_websocket_route_has_contract():
    missing = [
        route.path
        for route in _public_websocket_routes()
        if contract_for_route(route.path, "websocket") is None
    ]

    assert not missing, "WebSocket routes without Monitor contracts:\n" + "\n".join(sorted(missing))


def test_deprecated_routes_have_deprecation_contracts():
    failures = []
    for route in _public_http_routes():
        if not getattr(route, "deprecated", False):
            continue
        contract = contract_for_route(route.path, "http")
        text = " ".join(
            [
                contract.recommendation if contract else "",
                contract.replacement or "" if contract else "",
            ]
        ).lower()
        if "deprecated" not in text and "migrate" not in text:
            failures.append(route.path)

    assert not failures, "Deprecated routes without deprecation guidance:\n" + "\n".join(sorted(failures))


def test_every_dashboard_html_file_has_page_contract():
    missing = []
    incomplete = []
    for path in sorted(DASHBOARDS.glob("*.html")):
        contract = contract_for_page(path.name)
        if contract is None:
            missing.append(path.name)
            continue
        if not contract.source_of_truth or not contract.freshness or not contract.recommendation:
            incomplete.append(path.name)

    assert not missing, "Dashboard pages without contracts:\n" + "\n".join(missing)
    assert not incomplete, "Dashboard pages with incomplete contracts:\n" + "\n".join(incomplete)


def test_contract_endpoint_exposes_route_and_page_contracts():
    response = TestClient(app).get("/api/contracts/routes")

    assert response.status_code == 200
    data = response.json()
    assert "generated_at" in data
    assert data["route_contracts"]
    assert data["page_contracts"]
    assert any(item["pattern"] == "/api/worktrees" for item in data["route_contracts"])
    assert any(item["pattern"] == "/ws/batch" and item["kind"] == "websocket" for item in data["route_contracts"])
    assert any(item["file"] == "routing.html" and item["url"] == "/routing.html" for item in data["page_contracts"])
    assert any(item["file"] == "acp.html" and item["url"] == "/acp.html" for item in data["page_contracts"])


def test_routing_assignments_has_specific_observability_contract():
    contract = contract_for_route("/api/runtime/routing-assignments")

    assert contract is not None
    assert contract.pattern == "/api/runtime/routing-assignments"
    assert contract.match == "exact"
    assert "Fleet Comms routing-reservation" in contract.source_of_truth
    assert "decision-time snapshots" in contract.freshness
    assert "all-time" in contract.stale_risk
    assert contract.mutates is False


def test_every_atlas_jobs_route_matches_contracts():
    atlas_paths = [
        path for path in app.openapi()["paths"]
        if path.startswith("/api/atlas-jobs")
    ]
    assert "/api/atlas-jobs" in atlas_paths
    assert "/api/atlas-jobs/health" in atlas_paths
    assert "/api/atlas-jobs/load" in atlas_paths
    assert "/api/atlas-jobs/results" in atlas_paths
    assert "/api/atlas-jobs/submit" in atlas_paths
    assert "/api/atlas-jobs/{job_id}" in atlas_paths
    assert "/api/atlas-jobs/{job_id}/close" in atlas_paths

    for path in atlas_paths:
        contract = contract_for_route(path, "http")
        assert contract is not None, f"missing contract for {path}"
        assert contract.source_of_truth
        assert contract.freshness
        assert contract.recommendation
        if path in {"/api/atlas-jobs/submit", "/api/atlas-jobs/{job_id}", "/api/atlas-jobs/{job_id}/close"}:
            assert contract.mutates is True, f"{path} must have mutates=True"
        else:
            assert contract.mutates is False, f"{path} must have mutates=False"


def test_dead_alias_inventory_contracts():
    """Verify dead-alias/deprecated candidates in #7936 have honest contract notes."""
    candidates = [
        "/api/state/ready-to-build",
        "/api/blue/live-status",
        "/api/blue",
        "/api/gold",
        "/api/agent",
        "/api/comms/messages",
        "/api/comms/conversations",
        "/api/comms/conversation",
        "/api/comms/live-activity",
        "/api/comms/send",
        "/api/cost",
        "/api/rag",
        "/api/batch",
    ]
    for path in candidates:
        contract = contract_for_route(path, "http")
        assert contract is not None, f"missing contract for {path}"
        assert "NOTE:" in contract.recommendation, f"contract for {path} missing inventory NOTE"
        assert any(
            cls in contract.recommendation for cls in ("compat_keep", "migrate_caller_first", "retire_now")
        ), f"contract for {path} missing classification"

    assert "NOTE: retire_now" in contract_for_route("/api/blue/live-status", "http").recommendation
    assert "NOTE: retire_now" in contract_for_route("/api/rag", "http").recommendation
    assert "NOTE: retire_now" in contract_for_route("/api/state/ready-to-build", "http").recommendation
    assert "NOTE: retire_now" in contract_for_route("/api/cost", "http").recommendation

    http_paths = {route.path for route in _public_http_routes()}
    assert "/api/blue/live-status" not in http_paths
    assert not any(path.startswith("/api/rag") for path in http_paths)
    assert "/api/state/ready-to-build" not in http_paths
    assert not any(path.startswith("/api/cost") for path in http_paths)

    ws_contract = contract_for_route("/ws/batch", "websocket")
    assert ws_contract is not None
    assert "NOTE: compat_keep" in ws_contract.recommendation


def test_ops_api_openapi_describes_versioning_and_agent_onboard():
    """OpenAPI is part of the Ops API product surface — keep onboard/version text honest (#7975)."""
    info = app.openapi()["info"]
    assert info["title"] == "Ops API"
    assert info["version"] == "2.0.0"
    description = info["description"]
    assert "Application version 2.0.0" in description
    assert "/api/contracts/routes" in description
    assert "/api/orient?lean=true" in description
    assert "docs/MONITOR-API.md" in description
    assert "response_schema_version" in description


def test_launchpad_and_orient_page_contracts_match_post_7976_timeouts():
    index = contract_for_page("index.html")
    orient = contract_for_page("orient.html")
    assert index is not None and orient is not None
    assert "20s" in index.freshness
    assert "fresh=true" not in index.freshness.lower() or "no per-load" in index.freshness
    assert "singleflight" in contract_for_route("/api/state").freshness
    assert "20s" in orient.freshness
