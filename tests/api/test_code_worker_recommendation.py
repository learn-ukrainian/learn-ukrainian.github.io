"""Monitor recommendations share the capacity picker's resource order (#10279)."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from random import Random

import pytest

from scripts.api import state_router
from scripts.fleet import capacity_pick, credit_lane

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
        ({"gemini": _lane(87.6), "codex": _lane(72)}, {}, "agy"),
        ({"glm": _lane(100), "codex": _lane(72)}, {}, "codex"),
        ({"deepseek": _lane(100), "codex": _lane(72)}, {}, "codex"),
    ],
    ids=[
        "codex-headroom", "claude-headroom", "cursor-stronger-headroom", "tie",
        "claude-cursor-tie", "missing-headroom", "codex-claude-same-band", "same-band", "cursor-lower-load",
        "codex-lower-load", "unknown-load", "missing-load", "known-headroom",
        "heat-first", "burn-is-not-headroom", "tightest-window", "separate-pool", "imminent-reset",
        "retired-gemini", "retired-glm", "excluded-deepseek",
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
    agents = {lane: _lane(80, health={"healthy": lane != "codex"})}
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


def test_monitor_picker_seeded_fuzz(monkeypatch):
    """Vary heat, headroom, load and health with retired/excluded lanes present."""
    # Parse the real, unchanged policy once; keep every routing calculation real.
    policy = credit_lane.load_policy()
    monkeypatch.setattr(credit_lane, "load_policy", lambda: policy)
    rng = Random(10279)
    counts = {"cases": 3000, "disagreements": 0, "inline_orchestrator": 0, "established_health": 0}
    disagreements = []
    for case in range(counts["cases"]):
        agents = {
            lane: _lane(
                rng.choice([None, 10, 35, 65, 72, 85, 87.6, 100]),
                status=rng.choice(["cool", "warm", "hot", "near_cap"]),
            )
            for lane in capacity_pick.CODE_LANES
        }
        if case % 10 == 0:
            for info in agents.values():
                info["status"] = rng.choice(["hot", "near_cap"])
        # Every third scenario exercises the intentional health preference.
        if case % 3 == 0:
            for info in agents.values():
                info["health"] = rng.choice([{"healthy": True}, {}])
        loads = {lane: rng.choice([None, 0, 1, 2]) for lane in agents}
        budget = {"agents": agents, "in_flight": loads, "diagnostics": {"stale": False}}
        rows = capacity_pick.build_lane_rows(budget, reset_reserve={}, now=NOW)

        def pick(candidates):
            return next((row["lane"] for row in capacity_pick.build_pick_order(candidates) if row["pick"] != "AVOID"), None)

        picker = pick(rows)
        monitor = state_router._recommend_agent(
            agents, [], records_loaded=1, current_time=NOW, in_flight=loads,
        )["primary_agent_for_code"]
        if monitor == picker:
            continue
        if monitor == "inline_orchestrator":
            assert all(info["status"] in {"hot", "near_cap"} for info in agents.values())
            counts["inline_orchestrator"] += 1
        elif monitor == pick([row for row in rows if row["health"] == "healthy"]) and any(
            row["health"] == "healthy" for row in rows
        ) and any(row["health"] == "unknown" for row in rows):
            counts["established_health"] += 1
        else:
            counts["disagreements"] += 1
            disagreements.append((case, picker, monitor))
    print(f"seed=10279 {counts}")
    assert counts["disagreements"] == 0, disagreements[:10]


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
