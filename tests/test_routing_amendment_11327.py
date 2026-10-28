"""OO-58 amendment: parked Fable pins and a single Grok/Cursor allowance.

Defect classes: default routing spends on Fable, retirement blocks an explicit
Fable pin, or a second transport escapes the shared meter's reserve.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from scripts.agent_runtime.registry import AGENTS
from scripts.fleet import capacity_pick, credit_lane
from scripts.review.model_catalog import ModelCatalogError, load_model_catalog, require_execution_model
from scripts.review.reviewer_resolver import REVIEW_CANDIDATES, ResolverInputs, resolve_reviewer
from tests.claude_route_accounts import HOST_ACCOUNT

FABLE = "claude-fable-5-1"
ROOT = Path(__file__).resolve().parents[1]


def snapshot(grok=1, cursor=95):
    return {
        "agents": {
            lane: {"status": credit_lane.allowance_status(remaining), "remaining_pct": remaining,
                   "freshness": "fresh", "age_s": 0, "health": {"healthy": True}}
            for lane, remaining in (("grok", grok), ("cursor", cursor), ("codex", 50))
        },
        "diagnostics": {"stale": False, "records_loaded": 3, "codexbar_data_available": True},
    }


def test_budget_recommendation_uses_an_unparked_default():
    from scripts.api.state_router import _recommend_agent

    budget = snapshot(1, 1)
    budget["agents"]["codex"].update(status="near_cap", remaining_pct=1)
    budget["agents"]["claude"] = {"status": "cool", "remaining_pct": 80, "health": {"healthy": True}}
    result = _recommend_agent(budget["agents"], [], records_loaded=4, authoritative_data_available=True)
    assert result["primary_agent_for_code"] == "claude"
    assert "fable" not in AGENTS["claude"]["default_model"].lower()


def test_substitution_ladder_has_no_fable_or_kimi_route():
    from scripts.common.fallback_substitutions import load_dispatch_fallbacks
    from scripts.review.model_catalog import budget_substitution_table, substitution_default_model

    table = budget_substitution_table()
    for mappings in table.values():
        assert all("fable" not in value.lower() and "kimi" not in value.lower() for value in mappings.values())
    fallbacks = load_dispatch_fallbacks(ROOT / "scripts/config/agent_fallback_substitutions.yaml")
    assert "kimi" not in fallbacks.values()
    for lane in fallbacks.values():
        model = substitution_default_model(lane) or AGENTS[lane]["default_model"]
        assert "fable" not in model.lower() and "kimi" not in model.lower()


def test_reviewer_resolver_never_offers_fable():
    for risk in ("low", "medium", "high", "critical"):
        resolution = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk=risk, claude_account=HOST_ACCOUNT))
        assert resolution.selected is not None
        assert "fable" not in resolution.selected.concrete_model.lower()
        assert all("fable" not in row.concrete_model.lower() for row in resolution.trace if row.status in {"eligible", "selected"})
    assert all("fable" not in row.concrete_model.lower() for row in REVIEW_CANDIDATES.values())


def test_all_default_seats_and_harness_tables_exclude_fable():
    import json

    catalog = load_model_catalog()
    for spec in AGENTS.values():
        assert "fable" not in str(spec.get("default_model", "")).lower()
    for section in ("seats", "roles", "execution_routing", "review_candidates", "review_scheduler",
                    "orchestrator_seats", "formal_cf_defaults", "review_ladders", "budget_substitution_models"):
        assert "fable" not in json.dumps(catalog[section]).lower(), section
    fallback = yaml.safe_load((ROOT / "scripts/config/agent_fallback_substitutions.yaml").read_text())
    assert "fable" not in json.dumps(fallback).lower()


@pytest.mark.parametrize("transport", ["native_claude", "cursor"])
def test_explicit_fable_pin_requires_native_claude_transport(transport):
    """A parked pin must not advertise execution through the refusing Cursor adapter."""
    if transport == "native_claude":
        assert require_execution_model(FABLE, transport=transport) == FABLE
    else:
        with pytest.raises(ModelCatalogError, match="transport"):
            require_execution_model(FABLE, transport=transport)


def test_reviewer_capacity_and_ranking_read_shared_allowance():
    from scripts.review.capacity import review_capacity
    from scripts.review.reviewer_scheduler import _route_record, metrics_for

    budget = snapshot()
    candidate = REVIEW_CANDIDATES["grok-4.7-cursor-fallback"]
    record = _route_record(candidate, budget, prefer_route=True)
    assert review_capacity(record, budget["diagnostics"]).remaining_pct == 1
    assert review_capacity(record, budget["diagnostics"]).near_cap
    assert metrics_for(candidate, budget).quota_remaining_pct == 1


def test_pool_mirroring_preserves_route_health_and_does_not_mutate_snapshot():
    budget = snapshot(80, 95)
    budget["agents"]["cursor"]["health"] = {"healthy": False}
    original = deepcopy(budget)
    rows = {row["lane"]: row for row in capacity_pick.build_lane_rows(budget, reset_reserve={"enabled": False})}
    assert not rows["grok"]["avoid"]
    assert rows["cursor"]["avoid"]
    assert rows["grok"]["remaining_pct"] == rows["cursor"]["remaining_pct"] == 80
    assert budget == original


def test_retired_kimi_cannot_win_budget_recommendation_or_capacity_pick():
    from scripts.api.state_router import _recommend_agent

    budget = snapshot(50, 50)
    budget["agents"]["kimi"] = {"status": "cool", "remaining_pct": 100, "health": {"healthy": True}}
    report = capacity_pick.build_report(budget, reset_reserve={"enabled": False})
    kimi = next(row for row in report["rows"] if row["lane"] == "kimi")
    assert kimi["avoid"]
    assert next(row for row in report["pick_order"] if row["lane"] == "kimi")["pick"] == "AVOID"
    recommendation = _recommend_agent(budget["agents"], [], records_loaded=4, authoritative_data_available=True)
    assert recommendation["primary_agent_for_code"] in {"grok", "cursor", "codex"}


def test_capacity_picker_lists_each_cool_usage_pool_once():
    rows = capacity_pick.build_lane_rows(snapshot(80, 95), reset_reserve={"enabled": False})
    assert capacity_pick.cooler_lanes(rows) == ["codex", "grok"]


def test_route_runtime_failure_does_not_block_the_other_shared_transport():
    budget = snapshot(80, 95)
    budget["agents"]["grok"].update(status="hot", runtime={"headroom_blocked": True})
    rows = {row["lane"]: row for row in capacity_pick.build_lane_rows(budget, reset_reserve={"enabled": False})}
    assert rows["grok"]["avoid"]
    assert not rows["cursor"]["avoid"]
    assert rows["cursor"]["remaining_pct"] == 80


def test_missing_transport_meter_uses_shared_allowance_without_inventing_health():
    budget = snapshot(1, 95)
    del budget["agents"]["cursor"]
    rows = {row["lane"]: row for row in capacity_pick.build_lane_rows(budget, reset_reserve={"enabled": False})}
    assert rows["cursor"]["remaining_pct"] == 1
    assert rows["cursor"]["avoid"]
    assert rows["cursor"]["health"] == "unknown"


@pytest.mark.parametrize("agent", ["kimi", "acpx-kimicc-shadow"])
def test_kimi_registry_defaults_refuse_before_runtime_attribution(agent):
    from scripts.agent_runtime.runner import _refuse_retired_launch_model

    with pytest.raises(ValueError, match="retired in the model catalog"):
        _refuse_retired_launch_model(agent, None, None)


def test_unrelated_retired_legacy_default_is_not_a_new_gate():
    from scripts.agent_runtime.runner import _refuse_retired_launch_model

    assert _refuse_retired_launch_model("grok-hermes", None, None) is None


def test_shared_allowance_does_not_invent_capacity_for_an_unobserved_transport():
    budget = snapshot(80, 95)
    del budget["agents"]["grok"]
    rows = {row["lane"]: row for row in capacity_pick.build_lane_rows(budget, reset_reserve={"enabled": False})}
    assert rows["grok"]["remaining_pct"] == 95
    assert rows["grok"]["status"] == rows["grok"]["health"] == "unknown"
    assert not rows["cursor"]["avoid"]


@pytest.mark.parametrize("lane", ["grok", "cursor"])
def test_malformed_runtime_telemetry_keeps_the_shared_retirement_reserve(lane):
    """Partial runtime telemetry cannot crash the shared allowance reader."""
    budget = snapshot(1, 95)
    budget["agents"][lane]["runtime"] = "unknown"
    rows = {row["lane"]: row for row in capacity_pick.build_lane_rows(budget, reset_reserve={"enabled": False})}
    assert rows["grok"]["avoid"] and rows["cursor"]["avoid"]
    assert rows["grok"]["remaining_pct"] == rows["cursor"]["remaining_pct"] == 1
