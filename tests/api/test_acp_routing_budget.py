"""Transport-scoped ACP recommendation exclusion, including all-lanes failure."""

from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api import state_router
from scripts.fleet import capacity_pick


@pytest.fixture
def budget(monkeypatch):
    snapshot = {
        "agents": {
            lane: {"status": "cool", "burn_pct_7d": 10, "health": {"healthy": True}}
            for lane in ("codex", "cursor", "agy", "kimi", "deepseek", "gemini")
        },
        "recommendation": {"primary_agent_for_code": "cursor", "warnings": []},
        "ranked_by_headroom": [{"lane": lane} for lane in ("cursor", "codex", "deepseek")],
        "diagnostics": {"records_loaded": 1, "codexbar_data_available": True},
    }
    monkeypatch.setattr(state_router, "_compute_dispatch_routing_budget", lambda *_a, **_kw: deepcopy(snapshot))
    return snapshot


def _health(eligible):
    return {
        "healthy": eligible,
        "eligible": eligible,
        "failure_code": None if eligible else "cli_incompatible",
        "scope": "acp_cli_compatibility",
    }


def test_acp_capability_failure_never_falls_back_to_incompatible_lane(monkeypatch, budget):
    monkeypatch.setattr(
        state_router, "probe_acp_health", lambda _cwd: {lane: _health(False) for lane in budget["agents"]}
    )
    result = state_router.compute_routing_budget(transport="acp")
    assert result["recommendation"]["primary_agent_for_code"] is None
    assert result["ranked_by_headroom"] == []
    report = capacity_pick.build_report(result)
    assert report["recommendation"]["primary_agent_for_code"] is None
    assert all(row["pick"] == "AVOID" for row in report["pick_order"])
    assert all(result["agents"][lane]["dispatch_health"]["healthy"] for lane in budget["agents"])


def test_acp_capability_failure_preserves_native_dispatch(monkeypatch, budget):
    monkeypatch.setattr(
        state_router, "probe_acp_health", lambda _cwd: pytest.fail("native dispatch must not probe ACP")
    )
    result = state_router.compute_routing_budget()
    assert result["transport"] == "dispatch"
    assert result["recommendation"] == budget["recommendation"]
    assert result["agents"] == budget["agents"]


def test_acp_recommends_compatible_lane_and_recovers_without_failure_expiry(monkeypatch, budget):
    health = {lane: _health(False) for lane in budget["agents"]}
    health["codex"] = _health(True)
    monkeypatch.setattr(state_router, "probe_acp_health", lambda _cwd: deepcopy(health))
    result = state_router.compute_routing_budget(transport="acp")
    assert result["recommendation"]["primary_agent_for_code"] == "codex"
    assert [row["lane"] for row in result["ranked_by_headroom"]] == ["codex"]
    health["cursor"] = _health(True)
    assert state_router.compute_routing_budget(transport="acp")["recommendation"]["primary_agent_for_code"] == "cursor"


def test_acp_endpoint_passes_transport_and_excludes_unregistered_lanes(monkeypatch, budget, tmp_path):
    monkeypatch.setattr(state_router, "probe_acp_health", lambda _cwd: {"codex": _health(True)})
    app = FastAPI()
    app.include_router(state_router.router, prefix="/api/state")
    roots = SimpleNamespace(project_root=tmp_path, batch_state_dir=tmp_path, curriculum_root=tmp_path)
    app.dependency_overrides[state_router.get_ctx] = lambda: SimpleNamespace(roots=roots)
    with TestClient(app) as client:
        response = client.get("/api/state/routing-budget?transport=acp")
        assert response.status_code == 200
        data = response.json()
        assert data["transport"] == "acp"
        assert data["agents"]["gemini"]["eligible"] is False
        assert data["recommendation"]["primary_agent_for_code"] == "codex"
        assert client.get("/api/state/routing-budget?transport=bogus").status_code == 422


def test_acp_health_adds_missing_ask_lanes(monkeypatch, budget):
    budget["agents"].pop("agy")
    budget["agents"].pop("deepseek")
    monkeypatch.setattr(
        state_router,
        "probe_acp_health",
        lambda _cwd: {
            "agy": _health(False),
            "deepseek": _health(False),
        },
    )
    result = state_router.compute_routing_budget(transport="acp")
    assert result["agents"]["agy"]["eligible"] is False
    assert result["agents"]["deepseek"]["eligible"] is False


def test_acp_capacity_cli_selects_transport(monkeypatch, budget, capsys):
    monkeypatch.setattr(
        state_router, "probe_acp_health", lambda _cwd: {lane: _health(False) for lane in budget["agents"]}
    )
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda: {})
    assert capacity_pick.main(["--transport", "acp", "--strict", "--json"]) == 2
    assert '"transport": "acp"' in capsys.readouterr().out


def test_acp_routing_preserves_runtime_budget_evidence(monkeypatch, budget):
    budget["diagnostics"] = {"records_loaded": 0, "fleet_burn_available": True}
    monkeypatch.setattr(state_router, "probe_acp_health", lambda _cwd: {"codex": _health(True)})
    result = state_router.compute_routing_budget(transport="acp")
    assert result["recommendation"]["primary_agent_for_code"] == "codex"


def test_acp_no_inline_transport_fallback_when_all_lanes_hot(monkeypatch, budget):
    for info in budget["agents"].values():
        info["status"] = "hot"
    monkeypatch.setattr(state_router, "probe_acp_health", lambda _cwd: {"codex": _health(True)})
    assert state_router.compute_routing_budget(transport="acp")["recommendation"]["primary_agent_for_code"] is None


def test_acp_capacity_suppresses_stale_upstream_recommendation(budget):
    budget["transport"] = "acp"
    budget["agents"]["cursor"]["eligible"] = False
    report = capacity_pick.build_report(budget)
    assert report["recommendation"]["primary_agent_for_code"] is None
    assert all(row["pick"] == "AVOID" for row in report["pick_order"])
