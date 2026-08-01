"""Dashboard and route-registration contract for the unified fleet observer."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.fleet_router import router as fleet_router
from scripts.api.main import app
from scripts.api.route_contracts import contract_for_page, contract_for_route

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = ROOT / "dashboards"


def test_fleet_page_is_a_read_only_consolidated_observer() -> None:
    html = (DASHBOARDS / "fleet.html").read_text(encoding="utf-8")

    assert 'data-read-only="true"' in html
    assert "Unified observer · pre-flip soak" in html
    assert "Fleet Observer is the consolidated evidence surface" in html
    assert "/api/fleet/health" in html
    assert "/api/fleet/overview" in html
    assert "/api/fleet/requests" in html
    assert "/api/fleet/authority/jobs" in html
    assert "/api/fleet/messages" in html
    assert "/api/fleet/reviews" in html
    assert "/api/fleet/acp/conversations" in html
    assert "/api/fleet/activity" in html
    assert "<th>Source</th>" in html
    assert "<th>Agent</th>" in html
    assert "<th>Via</th>" in html
    assert "Refresh data" in html
    assert "<form" not in html
    assert "method: 'POST'" not in html
    assert 'method: "POST"' not in html
    assert "/api/fleet/" in html
    assert "new URLSearchParams(location.search)" in html
    assert "hydrateFiltersFromLocation();" in html
    assert "['conversation', 'filter-conversation']" in html


def test_fleet_routes_are_registered_get_only_and_contracted() -> None:
    observer_app = FastAPI()
    observer_app.include_router(fleet_router, prefix="/api/fleet")
    openapi = observer_app.openapi()["paths"]
    paths = {path for path in openapi if path.startswith("/api/fleet")}

    expected = {
        "/api/fleet/health",
        "/api/fleet/overview",
        "/api/fleet/agents",
        "/api/fleet/endpoints",
        "/api/fleet/requests",
        "/api/fleet/authority/jobs",
        "/api/fleet/messages",
        "/api/fleet/messages/{message_id}",
        "/api/fleet/discussions",
        "/api/fleet/discussions/{conversation_id}",
        "/api/fleet/reviews",
        "/api/fleet/reviews/{review_id}",
        "/api/fleet/dead-letters",
        "/api/fleet/migrations",
        "/api/fleet/acp/conversations",
        "/api/fleet/acp/conversations/{conversation_id}",
        "/api/fleet/activity",
    }
    assert expected <= paths
    assert all(set(openapi[path]) == {"get"} for path in paths)
    assert contract_for_route("/api/fleet/messages", "http") is not None
    assert contract_for_page("fleet.html") is not None


def test_fleet_page_and_retired_entrypoints_coexist_during_cutover() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    for path in [
        "/fleet.html",
        "/comms.html",
        "/channels.html",
        "/runtime.html",
        "/acp.html",
    ]:
        response = client.get(path)
        assert response.status_code == 200, f"{path} returned {response.status_code}: {response.text[:200]}"

    observer_app = FastAPI()
    observer_app.include_router(fleet_router, prefix="/api/fleet")
    observer_client = TestClient(observer_app, raise_server_exceptions=False)
    for path in ["/api/fleet/health", "/api/fleet/requests"]:
        response = observer_client.get(path)
        assert response.status_code == 200, f"{path} returned {response.status_code}: {response.text[:200]}"

    index = (DASHBOARDS / "index.html").read_text(encoding="utf-8")
    assert 'href="/fleet.html"' in index
    assert 'href="/channels.html"' not in index
    assert 'href="/comms.html"' not in index
    for legacy in ("/comms.html", "/channels.html", "/runtime.html", "/acp.html"):
        assert (DASHBOARDS / legacy.removeprefix("/")).is_file()
