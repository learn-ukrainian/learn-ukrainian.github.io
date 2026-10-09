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
    ],
    ids=[
        "codex-headroom", "claude-headroom", "cursor-stronger-headroom", "tie",
        "claude-cursor-tie", "missing-headroom", "codex-claude-same-band", "same-band", "cursor-lower-load",
        "codex-lower-load", "unknown-load", "missing-load", "known-headroom",
        "heat-first", "burn-is-not-headroom", "tightest-window", "separate-pool", "imminent-reset",
    ],
)
def test_monitor_and_capacity_picker_agree(agents, in_flight, expected):
    original = deepcopy(agents)
    budget = {"agents": agents, "in_flight": in_flight, "diagnostics": {"stale": False}}
    rows = capacity_pick.build_lane_rows(budget, lanes=tuple(agents), reset_reserve={}, now=NOW)
    picker = next(row["lane"] for row in capacity_pick.build_pick_order(rows) if row["pick"] != "AVOID")
    result = state_router._recommend_agent(
        agents, [], records_loaded=1, current_time=NOW,
        **({"in_flight": in_flight} if in_flight else {}),
    )
    assert picker == expected
    assert result["primary_agent_for_code"] == picker
    assert agents == original


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
