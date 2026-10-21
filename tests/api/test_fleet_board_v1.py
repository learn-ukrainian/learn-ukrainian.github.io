"""Contract tests for the fleet board v1 skeleton."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

import scripts.api.fleet_board.router as board_routes
from scripts.api import main as api_main
from scripts.api.fleet_board import sources as sources_mod

client = TestClient(api_main.app, raise_server_exceptions=False)


def _clear_locations(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in sources_mod.LOCATION_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def _openapi_v1() -> set[tuple[str, str]]:
    rows: set[tuple[str, str]] = set()
    prefix = board_routes.PUBLIC_PREFIX
    for path, item in api_main.app.openapi()["paths"].items():
        if path == prefix or path.startswith(f"{prefix}/"):
            rows.update((method.upper(), path) for method in item if method.upper() not in {"HEAD", "OPTIONS"})
    return rows


def test_index_lists_every_registered_v1_route() -> None:
    response = client.get("/api/fleet/v1")

    assert response.status_code == 200
    body = response.json()
    listed = {(item["method"], item["path"]) for item in body["data"]["endpoints"]}
    assert listed == _openapi_v1()
    assert listed == {
        ("GET", "/api/fleet/v1"),
        ("GET", "/api/fleet/v1/budget"),
        ("GET", "/api/fleet/v1/agents"),
        ("GET", "/api/fleet/v1/agents/{agent_id}"),
        ("GET", "/api/fleet/v1/epics"),
        ("GET", "/api/fleet/v1/epics/{epic}"),
        ("GET", "/api/fleet/v1/now"),
        ("GET", "/api/fleet/v1/alerts"),
        ("GET", "/api/fleet/v1/links"),
        ("GET", "/api/fleet/v1/prs"),
        ("GET", "/api/fleet/v1/prs/{number}"),
        ("GET", "/api/fleet/v1/roster"),
        ("GET", "/api/fleet/v1/schema"),
        ("GET", "/api/fleet/v1/backups"),
        ("GET", "/api/fleet/v1/downloads"),
        ("GET", "/api/fleet/v1/harness"),
        ("GET", "/api/fleet/v1/harness/{agent_id}"),
        ("GET", "/api/fleet/v1/stats"),
    }
    assert body["schema"] == "fleet.v1.index"


def test_missing_env_var_is_not_configured_and_http_200(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_locations(monkeypatch)

    response = client.get("/api/fleet/v1")

    assert response.status_code == 200
    by_name = {item["name"]: item for item in response.json()["sources"]}
    assert set(by_name) == {source.name for source in sources_mod.EXTERNAL_SOURCES}
    for item in by_name.values():
        assert item["status"] == "not_configured"
        assert item["age_s"] is None
        assert item["error"] is None


def test_blank_env_var_is_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_locations(monkeypatch)
    monkeypatch.setenv("FLEET_ROSTER_SNAPSHOT", "   ")

    response = client.get("/api/fleet/v1")

    assert response.status_code == 200
    roster = next(item for item in response.json()["sources"] if item["name"] == "roster_snapshot")
    assert roster["status"] == "not_configured"


def test_present_location_is_ok_and_the_value_is_not_echoed(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_locations(monkeypatch)
    monkeypatch.setenv("FLEET_BACKUP_STATE_DIR", "present-token")

    response = client.get("/api/fleet/v1")

    assert response.status_code == 200
    backups = next(item for item in response.json()["sources"] if item["name"] == "backups")
    assert backups == {"name": "backups", "status": "ok", "age_s": None, "error": None}
    assert "present-token" not in response.text


def test_location_probe_failure_stays_http_200(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(sources_mod, "read_location", explode)

    response = client.get("/api/fleet/v1/schema")

    assert response.status_code == 200
    body = response.json()
    assert body["schema"] == "fleet.v1.schema"
    assert body["sources"]
    assert all(item["status"] == "unavailable" for item in body["sources"])
    assert all(item["error"] == "unavailable" for item in body["sources"])
    assert "boom" not in response.text


def test_source_collector_failure_stays_http_200(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode():
        raise RuntimeError("boom")

    monkeypatch.setattr(board_routes, "collect_source_reports", explode)

    response = client.get("/api/fleet/v1")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["endpoints"]
    assert body["sources"] == [{"name": "sources", "status": "unavailable", "age_s": None, "error": "unavailable"}]
    assert "boom" not in response.text


def test_invalid_source_input_does_not_raise() -> None:
    row = sources_mod.report("", "ok", age_s=float("nan"), error="detail")
    assert row.status == "unavailable"
    assert row.error == "unavailable"
    assert row.as_dict()["error"] == "unavailable"


@pytest.mark.parametrize(
    ("route", "loader", "source"),
    [
        ("alerts", "load_alerts", "alerts"),
        ("stats", "load_stats", "stats"),
        ("links", "load_links", "links"),
        ("roster", "load_roster", "roster_snapshot"),
        ("budget", "load_budget", "routing_budget"),
    ],
)
def test_merged_data_routes_fail_closed_and_match_schema(
    monkeypatch: pytest.MonkeyPatch, route: str, loader: str, source: str
) -> None:
    _clear_locations(monkeypatch)

    def explode(*_args, **_kwargs):
        raise RuntimeError("synthetic-loader-failure")

    monkeypatch.setattr(board_routes, loader, explode)
    response = client.get(f"/api/fleet/v1/{route}")
    assert response.status_code == 200
    body = response.json()
    assert body["schema"] == f"fleet.v1.{route}"
    row = next(item for item in body["sources"] if item["name"] == source)
    assert row == {"name": source, "status": "unavailable", "age_s": None, "error": "unavailable"}
    assert "synthetic-loader-failure" not in response.text
    schemas = client.get("/api/fleet/v1/schema").json()["data"]["endpoints"]
    Draft202012Validator(schemas[body["schema"]]).validate(body)
