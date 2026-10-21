"""Monitor recommendations share the capacity picker's resource order (#10279)."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime

import pytest

from scripts.api import state_router
from scripts.fleet import capacity_pick

NOW = datetime(2026, 10, 9, 12, tzinfo=UTC)


def _lane(remaining: float | None, **extra) -> dict:
    return {
        "status": "cool",
        "remaining_pct": remaining,
        "burn_pct_7d": None if remaining is None else 100 - remaining,
        "health": {"healthy": True},
        "login_state": "authenticated",
        **extra,
    }


@pytest.mark.parametrize("preferred", ["codex", "claude"])
def test_cool_plan_lane_with_headroom_outranks_low_headroom_cursor(preferred):
    agents = {preferred: _lane(85), "cursor": _lane(35)}
    result = state_router._recommend_agent(agents, [], records_loaded=1, current_time=NOW)
    assert result["primary_agent_for_code"] == preferred


def test_monitor_recommends_funded_healthy_deepseek_as_only_cool_lane():
    agents = {
        "deepseek": _lane(
            None,
            probe_state="ok",
            freshness="fresh",
            age_s=0,
            currency="USD",
            total_balance=30.0,
            is_available=True,
        ),
    }
    rows = capacity_pick.build_lane_rows(
        {"agents": agents, "api_accounts": {"deepseek": agents["deepseek"]}},
        lanes=("deepseek",), reset_reserve={}, now=NOW,
    )
    assert rows[0]["avoid"] is False

    result = state_router._recommend_agent(agents, [], records_loaded=1, current_time=NOW)

    assert result["primary_agent_for_code"] == "deepseek"


@pytest.mark.parametrize(
    ("agents", "in_flight", "expected"),
    [
        ({"codex": _lane(85), "claude": _lane(75), "cursor": _lane(35)}, {}, "codex"),
        ({"codex": _lane(75), "claude": _lane(85), "cursor": _lane(35)}, {}, "claude"),
        ({"codex": _lane(65), "claude": _lane(75), "cursor": _lane(95)}, {}, "cursor"),
        ({lane: _lane(85) for lane in ("cursor", "claude", "codex")}, {}, "codex"),
        ({lane: _lane(85) for lane in ("cursor", "claude")}, {}, "claude"),
        ({lane: _lane(None) for lane in ("cursor", "claude", "codex")}, {}, "codex"),
        ({"codex": _lane(85), "claude": _lane(89)}, {}, "codex"),
        ({"codex": _lane(82), "cursor": _lane(89)}, {}, "codex"),
        ({"codex": _lane(82), "cursor": _lane(89)}, {"codex": 2, "cursor": 0}, "cursor"),
        ({"codex": _lane(82), "cursor": _lane(89)}, {"codex": 0, "cursor": 2}, "codex"),
        ({"codex": _lane(85), "cursor": _lane(85)}, {"codex": None, "cursor": 0}, "cursor"),
        ({"codex": _lane(85), "cursor": _lane(85)}, None, "codex"),
        ({"codex": _lane(None), "cursor": _lane(35)}, {}, "cursor"),
        ({"codex": _lane(95, status="warm"), "cursor": _lane(65)}, {}, "cursor"),
        ({"codex": _lane(85), "cursor": _lane(35, burn_pct_7d=1)}, {}, "codex"),
        ({"codex": _lane(85, codexbar={"primary_remaining_pct": 45}), "cursor": _lane(65)}, {}, "cursor"),
        ({"codex": _lane(85), "claude": _lane(65, agentic_pool={"active": True, "status": "cool"})}, {}, "codex"),
        ({"codex": _lane(85, resets_at="2026-10-09T13:00:00Z"), "cursor": _lane(35)}, {}, "codex"),
        ({"gemini": _lane(87.6), "codex": _lane(72)}, {}, "agy"),
        ({"glm": _lane(100), "codex": _lane(72)}, {}, "codex"),
        ({"deepseek": _lane(100, eligible=False), "codex": _lane(72)}, {}, "codex"),
    ],
    ids=[
        "codex-headroom", "claude-headroom", "cursor-stronger-headroom", "tie",
        "claude-cursor-tie", "missing-headroom", "codex-claude-same-band", "same-band", "cursor-lower-load",
        "codex-lower-load", "unknown-load", "missing-load", "known-headroom",
        "heat-first", "burn-is-not-headroom", "tightest-window", "separate-pool", "imminent-reset",
        "retired-gemini", "retired-glm", "ineligible-deepseek",
    ],
)
def test_monitor_and_capacity_picker_agree(agents, in_flight, expected):
    original = deepcopy(agents)
    budget = {"agents": agents, "in_flight": in_flight, "diagnostics": {"stale": False}}
    lanes = tuple(dict.fromkeys((*agents, "agy"))) if "gemini" in agents else tuple(agents)
    rows = capacity_pick.build_lane_rows(budget, lanes=lanes, reset_reserve={}, now=NOW)
    picker = next(row["lane"] for row in capacity_pick.build_pick_order(rows) if row["pick"] != "AVOID")
    result = state_router._recommend_agent(
        agents, [], records_loaded=1, current_time=NOW,
        **({"in_flight": in_flight} if in_flight else {}),
    )
    assert picker == expected
    assert result["primary_agent_for_code"] == picker
    assert agents == original


@pytest.mark.parametrize("lane", ["glm", "deepseek", "codex"])
def test_monitor_suppresses_avoid_only_fallback(lane):
    agents = {lane: _lane(80, health={"healthy": lane == "glm"})}
    rows = capacity_pick.build_lane_rows({"agents": agents}, lanes=(lane,), reset_reserve={}, now=NOW)
    assert all(row["pick"] == "AVOID" for row in capacity_pick.build_pick_order(rows))
    assert state_router._recommend_agent(agents, [], records_loaded=1, current_time=NOW)["primary_agent_for_code"] is None


@pytest.mark.parametrize("health", [{}, {"healthy": None}])
def test_monitor_drops_healthy_avoid_lane_before_health_preference(health):
    agents = {
        "claude": _lane(10, status="hot", runtime_blocked=True),
        "codex": _lane(70, health=health),
    }
    rows = capacity_pick.build_lane_rows({"agents": agents}, reset_reserve={}, now=NOW)
    picks = capacity_pick.build_pick_order(rows)
    assert next(row for row in picks if row["lane"] == "claude")["pick"] == "AVOID"
    assert next(row["lane"] for row in picks if row["pick"] != "AVOID") == "codex"

    result = state_router._recommend_agent(agents, [], records_loaded=1, current_time=NOW)
    assert result["primary_agent_for_code"] == "codex"
    assert any("recommendation is not health-verified" in warning for warning in result["warnings"])
    assert not any("preferring lanes with established health" in warning for warning in result["warnings"])


def test_monitor_does_not_load_picker_write_success_demotions(monkeypatch):
    """Only picker reports supplied with write-success records apply demotions."""
    agents = {"codex": _lane(85), "claude": _lane(85)}
    stats = capacity_pick.write_success_stats(
        [{"agent": "codex", "mode": "danger", "status": "failed", "finished_at": NOW.isoformat()}] * 3,
        now=NOW,
    )
    assert stats["codex"]["demoted"] is True
    budget = {"agents": agents}
    baseline = capacity_pick.build_report(budget, reset_reserve={}, now=NOW)
    demoted = capacity_pick.build_report(budget, reset_reserve={}, now=NOW, write_success=stats)
    assert baseline["pick_order"][0]["lane"] == "codex"
    assert demoted["pick_order"][0]["lane"] == "claude"

    def unexpected_load(*_args, **_kwargs):
        pytest.fail("Monitor must not read picker write-success records")

    monkeypatch.setattr(capacity_pick, "load_write_success_stats", unexpected_load)
    result = state_router._recommend_agent(agents, [], records_loaded=1, current_time=NOW)
    assert result["primary_agent_for_code"] == "codex"


@pytest.mark.parametrize("loads, expected", [({"codex": 2, "claude": 1, "cursor": 0}, "cursor"), ({"codex": 0, "claude": 1, "cursor": 2}, "codex")])
def test_producer_passes_observed_load_to_shared_order(monkeypatch, tmp_path, loads, expected):
    from tests.api.test_routing_budget import _configure_base

    budget_path = _configure_base(monkeypatch, tmp_path)
    monkeypatch.setattr(state_router, "_in_flight_by_agent", lambda *_a: loads)
    monkeypatch.setattr(state_router, "summarize_fleet_burn", lambda *_a, **_kw: {"windows": {}})
    monkeypatch.setattr(
        state_router, "get_provider_usage_data",
        lambda lane: {
            "lane": lane, "source": "codexbar", "weekly_used_pct": 15.0,
            "weekly_remaining_pct": 85.0, "will_last_to_reset": True,
            "freshness": "fresh", "age_s": 0, "fetched_at": NOW.isoformat(),
            "stale": False,
        } if lane in {"codex", "claude"} else {},
    )
    monkeypatch.setattr(
        state_router, "get_cursor_lane_usage",
        lambda: {
            "lane": "cursor", "source": "cursor_native", "status": "cool",
            "login_state": "authenticated", "primary_used_pct": 15.0,
            "provider_windows": {"auto": {"used_pct": 15.0, "remaining_pct": 85.0}},
            "freshness": "fresh", "age_s": 0, "fetched_at": NOW.isoformat(),
        },
    )
    budget = state_router.compute_routing_budget(
        NOW, budget_config_path=budget_path, tasks_dir=tmp_path / "tasks",
        project_root=tmp_path, curriculum_root=tmp_path, batch_state_dir=tmp_path,
    )
    picked = next(
        row["lane"] for row in capacity_pick.build_report(budget, reset_reserve={}, now=NOW)["pick_order"]
        if row["pick"] != "AVOID"
    )
    assert budget["in_flight"] == loads
    assert budget["recommendation"]["primary_agent_for_code"] == picked == expected
