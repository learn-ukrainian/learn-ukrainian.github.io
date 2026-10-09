"""Contract tests for the fleet board v1 skeleton."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

import scripts.api.fleet_board.router as board_routes
from scripts.api import main as api_main
from scripts.api.fleet_board import envelope as envelope_mod
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
        ("GET", "/api/fleet/v1/alerts"),
        ("GET", "/api/fleet/v1/links"),
        ("GET", "/api/fleet/v1/prs"),
        ("GET", "/api/fleet/v1/prs/{number}"),
        ("GET", "/api/fleet/v1/schema"),
        ("GET", "/api/fleet/v1/stats"),
    }
    assert body["schema"] == "fleet.v1.index"


def test_schema_validates_the_index_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_locations(monkeypatch)
    index = client.get("/api/fleet/v1")
    schema = client.get("/api/fleet/v1/schema")

    assert index.status_code == 200
    assert schema.status_code == 200
    document = schema.json()["data"]["endpoints"]["fleet.v1.index"]
    Draft202012Validator(document).validate(index.json())
    Draft202012Validator(schema.json()["data"]["endpoints"]["fleet.v1.schema"]).validate(schema.json())


def test_schema_rejects_a_source_row_that_disagrees_with_its_status(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_locations(monkeypatch)
    document = client.get("/api/fleet/v1/schema").json()["data"]["endpoints"]["fleet.v1.index"]
    payload = client.get("/api/fleet/v1").json()
    validator = Draft202012Validator(document)
    validator.validate(payload)

    contradictory = {
        "name": payload["sources"][0]["name"],
        "status": "not_configured",
        "age_s": 1,
        "error": "detail",
    }
    payload["sources"][0] = contradictory
    with pytest.raises(ValidationError):
        validator.validate(payload)


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


def test_existing_fleet_routes_stay_registered() -> None:
    paths = set(api_main.app.openapi()["paths"])
    assert "/api/fleet/agents" in paths
    assert "/api/state/routing-budget" in paths
    assert "/api/fleet/v1" in paths


def test_invalid_source_input_does_not_raise() -> None:
    row = sources_mod.report("", "ok", age_s=float("nan"), error="detail")
    assert row.status == "unavailable"
    assert row.error == "unavailable"
    assert row.as_dict()["error"] == "unavailable"


def test_stale_and_ok_reports_keep_a_finite_age() -> None:
    fresh = sources_mod.report("stats", "ok", age_s=1.5)
    old = sources_mod.report("stats", "stale", age_s=90)
    assert fresh.as_dict() == {"name": "stats", "status": "ok", "age_s": 1.5, "error": None}
    assert old.status == "stale"
    assert old.age_s == 90
    rejected = sources_mod.report("stats", "stale", age_s=-1)
    assert rejected.status == "unavailable"


def test_envelope_uses_utc_timestamp() -> None:
    moment = datetime(2026, 10, 9, 9, 14, 0, tzinfo=UTC)
    body = envelope_mod.envelope(
        "index",
        {"endpoints": []},
        (sources_mod.report("alerts", "not_configured"),),
        generated_at=moment,
    )
    assert body["schema"] == "fleet.v1.index"
    assert body["generated_at"] == "2026-10-09T09:14:00Z"
    assert body["sources"][0]["status"] == "not_configured"


def test_location_variables_match_the_optional_catalog() -> None:
    assert [(source.name, source.env_var, source.kind) for source in sources_mod.EXTERNAL_SOURCES] == [
        ("roster_snapshot", "FLEET_ROSTER_SNAPSHOT", "json_file"),
        ("harness_snapshot", "FLEET_HARNESS_SNAPSHOT", "json_file"),
        ("downloads", "FLEET_DOWNLOAD_STATUS", "json_file"),
        ("backups", "FLEET_BACKUP_STATE_DIR", "directory"),
        ("mq_state", "FLEET_MQ_STATE_DIR", "directory"),
        ("stats", "FLEET_PROMETHEUS_URL", "url"),
        ("alerts", "FLEET_ALERTMANAGER_URL", "url"),
        ("links", "FLEET_GRAFANA_URL", "url"),
    ]


def test_configuration_status_reads_a_mapping_without_touching_the_process_env() -> None:
    source = sources_mod.EXTERNAL_SOURCES[-1]
    missing = sources_mod.configuration_status(source, environ={})
    present = sources_mod.configuration_status(source, environ={source.env_var: "set"})
    assert missing.status == "not_configured"
    assert present.status == "ok"
    assert present.error is None
