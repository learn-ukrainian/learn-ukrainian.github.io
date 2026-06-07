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
