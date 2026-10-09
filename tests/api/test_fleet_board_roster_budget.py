"""Roster and budget routes for fleet board v1, plus the routing-budget shape lock."""

from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from scripts.api import state_router
from scripts.api.fleet_board import budget as budget_mod
from scripts.api.fleet_board import roster as roster_mod
from scripts.api.fleet_board import router as board_routes
from scripts.api.monitor_context import fixture_context
from scripts.api.subscription_usage import compute_usage_pace

NOW = datetime(2026, 10, 9, 9, 0, tzinfo=UTC)
STAMP = "2026-10-09T09:00:00Z"
RESET = "2026-10-12T00:00:00Z"

ROUTING_BUDGET_KEYS = frozenset(
    {
        "agents",
        "api_accounts",
        "diagnostics",
        "generated_at",
        "in_flight",
        "ranked_by_headroom",
        "recommendation",
        "reset_reserve",
        "transport",
    }
)
RECOMMENDATION_KEYS = frozenset({"primary_agent_for_code", "rationale", "warnings"})
DIAGNOSTIC_KEYS = frozenset(
    {
        "budget_ledger_empty",
        "codexbar_data_available",
        "codexbar_freshness",
        "codexbar_max_age_s",
        "data_age_s",
        "fleet_burn_available",
        "fresh_codexbar_blocking",
        "fresh_codexbar_requested",
        "missing_cost_records",
        "notebook_report_available",
        "notebook_report_max_age_s",
        "records_loaded",
        "reset_imminent_hours",
        "runtime_data_available",
        "runtime_usage_records_7d",
        "stale",
        "stale_threshold_s",
        "usage_sources",
        "window_start",
    }
)
USAGE_SOURCE_KEYS = frozenset({"allotment", "burn_rate_limit", "fleet_burn"})


@pytest.fixture(autouse=True)
def _clear_budget_cache() -> None:
    budget_mod.clear_cache()


def _client(tmp_path, *, state: bool = False) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    if state:
        app.include_router(state_router.router, prefix="/api/state")
    app.include_router(board_routes.router, prefix="/api/fleet/v1")
    return TestClient(app, raise_server_exceptions=False)


def _freeze_now(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(roster_mod, "_now", lambda: NOW)
    monkeypatch.setattr(budget_mod, "_now", lambda: NOW)


def _write_snapshot(tmp_path, body: dict) -> str:
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    return str(path)


def _sample_snapshot() -> dict:
    return {
        "generated_at": STAMP,
        "interval_s": 60,
        "ignored_note": "drop-me",
        "epics": [
            {
                "epic": "data",
                "layer": 0,
                "depends_on": ["codebase"],
                "restart_condition": "after a corpus load",
                "state": "idle",
                "flags": [
                    {"name": "loaded", "value": False, "source": "publisher", "checked_at": STAMP},
                ],
            },
            {
                "epic": "codebase",
                "layer": 0,
                "depends_on": [],
                "restart_condition": "after a published schema change",
                "state": "working",
                "flags": [
                    {"name": "ready", "value": True, "source": "publisher", "checked_at": STAMP},
                    {"name": "reviewed", "value": "unknown", "source": "publisher", "checked_at": STAMP},
                    {"name": "counted", "value": 0, "source": "publisher", "checked_at": STAMP},
                    {"name": "marked", "value": 1, "source": "publisher", "checked_at": STAMP},
                    {"name": "labeled", "value": "true", "source": "publisher", "checked_at": STAMP},
                    {"name": "missing", "source": "publisher", "checked_at": STAMP},
                ],
            },
            {
                "epic": "reader",
                "layer": 1,
                "depends_on": ["codebase", "data", "codebase"],
                "restart_condition": "when foundations are current",
                "state": "working",
                "flags": [],
            },
            {
                "epic": "later",
                "layer": "postponed",
                "depends_on": ["reader"],
                "restart_condition": "not scheduled",
                "state": "working",
                "flags": [
                    {"name": "armed", "value": "unknown", "source": "publisher", "checked_at": STAMP},
                ],
            },
        ],
        "foundations": [
            {"foundation": "codebase", "red": False, "reasons": []},
            {"foundation": "data", "red": True, "reasons": ["load incomplete"]},
            {"foundation": "notes", "reasons": ["unspecified"]},
        ],
        "alerts": [{"name": "foundation", "summary": "data foundation is red"}],
    }


def _roster(tmp_path, monkeypatch: pytest.MonkeyPatch, body: dict | None):
    _freeze_now(monkeypatch)
    monkeypatch.delenv("FLEET_ROSTER_SNAPSHOT", raising=False)
    if body is not None:
        monkeypatch.setenv("FLEET_ROSTER_SNAPSHOT", _write_snapshot(tmp_path, body))
    client = _client(tmp_path)
    response = client.get("/api/fleet/v1/roster")
    return response, client


def test_roster_projects_layers_flags_foundations_and_alerts(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    response, _client_unused = _roster(tmp_path, monkeypatch, _sample_snapshot())

    assert response.status_code == 200
    body = response.json()
    assert body["schema"] == "fleet.v1.roster"
    assert "drop-me" not in response.text
    data = body["data"]
    assert [layer["kind"] for layer in data["layers"]] == ["foundations", "consumers", "postponed"]
    assert [layer["layer"] for layer in data["layers"]] == [0, 1, None]
    foundations = data["layers"][0]["epics"]
    assert [epic["epic"] for epic in foundations] == ["codebase", "data"]
    codebase = foundations[0]
    assert codebase["depends_on"] == []
    assert codebase["restart_condition"] == "after a published schema change"
    assert codebase["state"] == "working"
    values = {flag["name"]: flag["value"] for flag in codebase["flags"]}
    assert values["ready"] is True
    assert values["reviewed"] == "unknown"
    assert values["counted"] == "unknown"
    assert values["marked"] == "unknown"
    assert values["labeled"] == "unknown"
    assert values["missing"] == "unknown"
    assert all(flag["value"] is not True for flag in codebase["flags"] if flag["name"] != "ready")
    assert all(flag["source"] == "publisher" for flag in codebase["flags"])
    reader = data["layers"][1]["epics"][0]
    assert reader["epic"] == "reader"
    assert reader["depends_on"] == ["codebase", "data"]
    later = data["layers"][2]["epics"][0]
    assert later["epic"] == "later"
    assert later["state"] == "off"
    assert later["flags"][0]["value"] == "unknown"
    assert data["foundation_status"] == [
        {"foundation": "codebase", "red": False, "reasons": []},
        {"foundation": "data", "red": True, "reasons": ["load incomplete"]},
        {"foundation": "notes", "red": None, "reasons": ["unspecified"]},
    ]
    assert data["active_alerts"] == [{"name": "foundation", "summary": "data foundation is red"}]
    roster_source = next(item for item in body["sources"] if item["name"] == "roster_snapshot")
    assert roster_source["status"] == "ok"
    assert roster_source["age_s"] == 0
    assert roster_source["error"] is None


def test_roster_schema_accepts_the_response(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    response, client = _roster(tmp_path, monkeypatch, _sample_snapshot())
    schema = client.get("/api/fleet/v1/schema")

    assert schema.status_code == 200
    document = schema.json()["data"]["endpoints"]["fleet.v1.roster"]
    Draft202012Validator(document).validate(response.json())


def test_postponed_epic_stays_off_and_unknown_flag_is_not_true(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    body = {
        "generated_at": STAMP,
        "interval_s": 60,
        "epics": [
            {
                "epic": "later",
                "postponed": True,
                "state": "working",
                "flags": [{"name": "armed", "value": "unknown"}],
            }
        ],
    }
    response, _client_unused = _roster(tmp_path, monkeypatch, body)
    epic = response.json()["data"]["layers"][2]["epics"][0]

    assert epic["state"] == "off"
    assert epic["flags"][0]["value"] == "unknown"
    assert epic["flags"][0]["value"] is not True


def test_stale_snapshot_keeps_data_and_reports_age(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    body = _sample_snapshot()
    body["generated_at"] = "2026-10-09T08:00:00Z"
    body["interval_s"] = 30
    response, _client_unused = _roster(tmp_path, monkeypatch, body)
    payload = response.json()
    source = next(item for item in payload["sources"] if item["name"] == "roster_snapshot")

    assert response.status_code == 200
    assert source["status"] == "stale"
    assert source["age_s"] == 3600
    assert payload["data"]["layers"][0]["epics"]


def test_missing_snapshot_variable_is_not_configured(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    response, _client_unused = _roster(tmp_path, monkeypatch, None)

    assert response.status_code == 200
    payload = response.json()
    source = next(item for item in payload["sources"] if item["name"] == "roster_snapshot")
    assert source == {"name": "roster_snapshot", "status": "not_configured", "age_s": None, "error": None}
    assert payload["data"]["layers"][0]["epics"] == []
    assert payload["data"]["foundation_status"] == []
    assert payload["data"]["active_alerts"] == []


def test_unreadable_snapshot_is_unavailable(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_now(monkeypatch)
    target = tmp_path / "snapshot.json"
    target.write_text("{", encoding="utf-8")
    monkeypatch.setenv("FLEET_ROSTER_SNAPSHOT", str(target))
    response = _client(tmp_path).get("/api/fleet/v1/roster")

    assert response.status_code == 200
    source = next(item for item in response.json()["sources"] if item["name"] == "roster_snapshot")
    assert source["status"] == "unavailable"
    assert source["error"] == "unavailable"
    assert str(target) not in response.text
    assert "Expecting" not in response.text


def _budget_payload() -> dict:
    return {
        "agents": {
            "claude": {
                "burn_pct_7d": 80.0,
                "status": "cool",
                "resets_at": RESET,
                "codexbar": {
                    "weekly_used_pct": 12.5,
                    "weekly_resets_at": RESET,
                    "weekly_expected_pct": 99.0,
                },
            },
            "codex": {"burn_pct_7d": 30.0, "status": "warm", "resets_at": RESET},
            "gemini": {"burn_pct_7d": None, "status": "unknown"},
            "grok": {"burn_pct_7d": 0.0, "status": "cool", "resets_at": RESET},
        },
        "diagnostics": {"stale": False},
    }


def _weekly_used(agent: dict) -> float | None:
    codexbar = agent.get("codexbar")
    if isinstance(codexbar, dict):
        weekly = codexbar.get("weekly_used_pct")
        if isinstance(weekly, (int, float)) and not isinstance(weekly, bool):
            return float(weekly)
    burn = agent.get("burn_pct_7d")
    if isinstance(burn, (int, float)) and not isinstance(burn, bool):
        return float(burn)
    return None


def test_budget_projects_weekly_pace_and_leaves_unknown_null(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_now(monkeypatch)
    calls = {"n": 0, "kwargs": {}}

    def compute(**kwargs):
        calls["n"] += 1
        calls["kwargs"] = kwargs
        return _budget_payload()

    monkeypatch.setattr(state_router, "compute_routing_budget", compute)
    client = _client(tmp_path)
    response = client.get("/api/fleet/v1/budget")
    again = client.get("/api/fleet/v1/budget")

    assert response.status_code == 200
    assert again.status_code == 200
    assert calls["n"] == 1
    assert calls["kwargs"]["fresh_codexbar"] is False
    body = response.json()
    assert body["schema"] == "fleet.v1.budget"
    rows = {row["subscription"]: row for row in body["data"]["subscriptions"]}
    assert set(rows) == set(state_router.SUBSCRIPTION_LANES)
    reading = compute_usage_pace(12.5, RESET, now=NOW)
    assert reading is not None
    assert rows["claude"]["used_pct"] == 12.5
    assert rows["claude"]["elapsed_pct"] == pytest.approx(reading["expected_pct"])
    assert rows["claude"]["pace"] == reading["stage"]
    assert rows["claude"]["reset_at"] == RESET
    assert rows["claude"]["recommendation"] == "cool"
    assert rows["claude"]["elapsed_pct"] != 99.0
    assert rows["codex"]["used_pct"] == 30.0
    assert rows["grok"]["used_pct"] == 0.0
    assert rows["gemini"]["used_pct"] is None
    assert rows["gemini"]["pace"] is None
    assert rows["gemini"]["elapsed_pct"] is None
    assert rows["cursor"]["used_pct"] is None
    source = next(item for item in body["sources"] if item["name"] == "routing_budget")
    assert source["status"] == "ok"
    assert source["age_s"] == 0
    document = client.get("/api/fleet/v1/schema").json()["data"]["endpoints"]["fleet.v1.budget"]
    Draft202012Validator(document).validate(body)


def test_budget_agrees_with_routing_budget_used_pct(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_now(monkeypatch)
    payload = _budget_payload()
    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **kwargs: payload)
    client = _client(tmp_path, state=True)
    budget_mod.clear_cache()

    old = client.get("/api/state/routing-budget")
    new = client.get("/api/fleet/v1/budget")

    assert old.status_code == 200
    assert new.status_code == 200
    rows = {row["subscription"]: row["used_pct"] for row in new.json()["data"]["subscriptions"]}
    for lane, agent in old.json()["agents"].items():
        assert rows[lane] == _weekly_used(agent)
    assert rows["gemini"] is None
    assert rows["grok"] == 0.0


def test_slow_budget_refresh_returns_stale_cache(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_now(monkeypatch)
    cached = _budget_payload()
    client = _client(tmp_path)
    budget_mod.prime(client.app.state.ctx, cached, age_s=budget_mod.BUDGET_TTL_S + 5)
    release = threading.Event()

    def compute(**kwargs):
        release.wait(0.4)
        return cached

    monkeypatch.setattr(state_router, "compute_routing_budget", compute)
    monkeypatch.setattr(budget_mod, "BUDGET_DEADLINE_S", 0.05)
    started = time.monotonic()
    response = client.get("/api/fleet/v1/budget")
    elapsed = time.monotonic() - started
    release.set()

    assert response.status_code == 200
    assert elapsed < 1.0
    source = next(item for item in response.json()["sources"] if item["name"] == "routing_budget")
    assert source["status"] == "stale"
    assert source["age_s"] >= budget_mod.BUDGET_TTL_S
    claude = next(row for row in response.json()["data"]["subscriptions"] if row["subscription"] == "claude")
    assert claude["used_pct"] == 12.5


def test_slow_budget_refresh_without_cache_is_unavailable(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_now(monkeypatch)
    release = threading.Event()

    def compute(**kwargs):
        release.wait(0.4)
        return _budget_payload()

    monkeypatch.setattr(state_router, "compute_routing_budget", compute)
    monkeypatch.setattr(budget_mod, "BUDGET_DEADLINE_S", 0.05)
    started = time.monotonic()
    response = _client(tmp_path).get("/api/fleet/v1/budget")
    elapsed = time.monotonic() - started
    release.set()

    assert response.status_code == 200
    assert elapsed < 1.0
    body = response.json()
    source = next(item for item in body["sources"] if item["name"] == "routing_budget")
    assert source == {"name": "routing_budget", "status": "unavailable", "age_s": None, "error": "unavailable"}
    assert all(row["used_pct"] is None for row in body["data"]["subscriptions"])
    assert all(row["elapsed_pct"] is None for row in body["data"]["subscriptions"])


def test_budget_compute_failure_stays_http_200(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    def compute(**kwargs):
        raise RuntimeError("boom-token")

    monkeypatch.setattr(state_router, "compute_routing_budget", compute)
    response = _client(tmp_path).get("/api/fleet/v1/budget")

    assert response.status_code == 200
    source = next(item for item in response.json()["sources"] if item["name"] == "routing_budget")
    assert source["status"] == "unavailable"
    assert "boom-token" not in response.text


def test_budget_source_is_stale_when_the_compute_is_stale(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _budget_payload()
    payload["diagnostics"] = {"stale": True, "data_age_s": 40}
    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **kwargs: payload)
    response = _client(tmp_path).get("/api/fleet/v1/budget")

    assert response.status_code == 200
    source = next(item for item in response.json()["sources"] if item["name"] == "routing_budget")
    assert source["status"] == "stale"
    assert source["age_s"] == 40
    assert source["error"] is None


def test_budget_deadline_and_ttl_are_short() -> None:
    assert budget_mod.BUDGET_DEADLINE_S == 2.0
    assert budget_mod.BUDGET_TTL_S == 15.0


def _silence_budget_io(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    shared = tmp_path / "shared"
    (shared / "batch_state" / "tasks").mkdir(parents=True)
    monkeypatch.setattr(state_router, "main_checkout_root", lambda _root: shared)
    monkeypatch.setattr(state_router, "_load_agent_budgets", lambda budget_config_path=None: ({"codex": {}}, []))
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [])
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda _provider: None)
    monkeypatch.setattr(state_router, "get_cursor_lane_usage", lambda **_kwargs: {"probe_state": "NEED_PROBE"})
    monkeypatch.setattr(state_router, "get_api_account_data", lambda _provider: {"probe_state": "NEED_PROBE"})
    monkeypatch.setattr(state_router, "summarize_fleet_burn", lambda *_args, **_kwargs: {"windows": {}})
    monkeypatch.setattr(
        state_router,
        "summarize_lane_runtime",
        lambda *_args, **_kwargs: {"headroom_blocked": False, "total": 0},
    )
    monkeypatch.setattr(state_router, "get_freshest_lane_usage", lambda: None)


def test_routing_budget_response_shape_is_frozen(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _silence_budget_io(monkeypatch, tmp_path)
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(state_router.router, prefix="/api/state")

    response = TestClient(app).get("/api/state/routing-budget")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == ROUTING_BUDGET_KEYS
    assert set(body["recommendation"]) == RECOMMENDATION_KEYS
    assert set(body["diagnostics"]) == DIAGNOSTIC_KEYS
    assert set(body["diagnostics"]["usage_sources"]) == USAGE_SOURCE_KEYS
    assert body["transport"] == "dispatch"
    assert isinstance(body["agents"], dict)
    assert isinstance(body["ranked_by_headroom"], list)
