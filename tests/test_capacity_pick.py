"""Unit tests for scripts.fleet.capacity_pick pure formatting (no live CodexBar)."""

from __future__ import annotations

import json

import pytest

from scripts.fleet import capacity_pick


def _fixture_budget() -> dict:
    return {
        "generated_at": "2026-08-12T12:00:00Z",
        "agents": {
            "codex": {
                "status": "hot",
                "burn_pct_7d": 72.0,
                "remaining_pct": 28.0,
                "codexbar": {
                    "will_last_to_reset": False,
                    "pace_summary": "won't last to reset",
                    "weekly_pace_delta_pct": 12.0,
                },
            },
            "cursor": {
                "status": "cool",
                "burn_pct_7d": 8.0,
                "remaining_pct": 92.0,
                "codexbar": {"will_last_to_reset": True, "pace_summary": "on pace"},
            },
            "claude": {
                "status": "near_cap",
                "interactive": {"status": "near_cap", "burn_pct_7d": 95.0},
                "burn_pct_7d": 95.0,
                "remaining_pct": 5.0,
                "codexbar": {"will_last_to_reset": False},
            },
            "agy": {"status": "cool", "burn_pct_7d": 15.0, "remaining_pct": 85.0},
            "kimi": {"status": "warm", "burn_pct_7d": 55.0, "remaining_pct": 45.0},
            "gemini": {"status": "unknown", "burn_pct_7d": None},
            "grok": {"status": "cool", "burn_pct_7d": 20.0, "remaining_pct": 80.0},
            "glm": {"status": "cool", "burn_pct_7d": 12.0, "remaining_pct": 88.0},
        },
        "api_accounts": {"deepseek": {
            "probe_state": "ok", "freshness": "fresh", "age_s": 0,
            "currency": "USD", "total_balance": 30.0, "is_available": True,
        }},
        "in_flight": {"cursor": 0, "codex": 1},
        "recommendation": {
            "primary_agent_for_code": "cursor",
            "rationale": "Cursor is cool; Codex is in deficit.",
            "warnings": ["lane codex is in deficit"],
        },
        "diagnostics": {"records_loaded": 4, "stale": False},
    }


def test_lane_rows_mark_avoid():
    rows = {r["lane"]: r for r in capacity_pick.build_lane_rows(_fixture_budget())}
    assert rows["codex"]["avoid"] is True
    assert "AVOID" in rows["codex"]["notes"]
    assert "deficit" in rows["codex"]["notes"]
    assert rows["claude"]["avoid"] is True
    assert rows["cursor"]["avoid"] is False
    assert rows["cursor"]["status"] == "cool"
    assert rows["cursor"]["will_last"] is True
    # glm's z.ai subscription is retired (operator 2026-09-03): AVOID even
    # when the budget snapshot itself still reports the lane as cool/wrong.
    assert rows["glm"]["avoid"] is True
    assert "retired→cursor" in rows["glm"]["notes"]


def test_reset_reserve_relaxes_only_eligible_threatened_codex():
    budget = _fixture_budget()
    budget["agents"]["codex"].update(
        {
            "eligible": True,
            "health": {"healthy": True},
            "freshness": "fresh",
            "age_s": 10,
            "runtime": {"headroom_blocked": False, "rate_limited": 0, "last_rate_limited_at": None},
            "codexbar": {
                **budget["agents"]["codex"]["codexbar"],
                "windows": {"primary": {"remaining_pct": 12.0}},
            },
        }
    )
    reserve = {"available": True, "provider": "codex", "remaining_resets": 2}
    rows = {r["lane"]: r for r in capacity_pick.build_lane_rows(budget, reset_reserve=reserve)}
    assert rows["codex"]["avoid"] is False
    assert rows["codex"]["status"] == "hot"
    assert rows["codex"]["will_last"] is False
    assert rows["codex"]["reset_reserve_eligible"] is True
    assert "reset reserve eligible (2 remaining)" in rows["codex"]["notes"]

    report = capacity_pick.build_report(budget, reset_reserve=reserve)
    assert report["pick_order"][0]["lane"] == "codex"
    assert "codex" in report["cooler_lanes"]

    budget["agents"]["codex"]["runtime"]["headroom_blocked"] = True
    blocked = {r["lane"]: r for r in capacity_pick.build_lane_rows(budget, reset_reserve=reserve)}
    assert blocked["codex"]["avoid"] is True


def test_stale_capacity_snapshot_disables_reserve_and_strict_pick(monkeypatch):
    budget = _fixture_budget()
    budget["diagnostics"] = {"stale": True}
    budget["agents"]["codex"].update(
        {
            "eligible": True,
            "health": {"healthy": True},
            "freshness": "fresh",
            "age_s": 10,
            "runtime": {"headroom_blocked": False, "rate_limited": 0, "last_rate_limited_at": None},
            "codexbar": {
                **budget["agents"]["codex"]["codexbar"],
                "windows": {"primary": {"remaining_pct": 12.0}},
            },
        }
    )
    reserve = {"available": True, "provider": "codex", "remaining_resets": 2}
    row = next(row for row in capacity_pick.build_lane_rows(budget, reset_reserve=reserve) if row["lane"] == "codex")
    assert row["avoid"] is True
    assert row["reset_reserve_eligible"] is False

    only_codex = {
        "agents": {"codex": budget["agents"]["codex"]},
        "diagnostics": {"stale": False},
        "recommendation": {"primary_agent_for_code": None, "warnings": []},
    }
    from scripts.fleet import usage

    monkeypatch.setattr(usage, "read_budget", lambda **_kwargs: only_codex)
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda **_kwargs: {})
    monkeypatch.setattr(capacity_pick, "load_reset_reserve", lambda *_args, **_kwargs: reserve)
    assert capacity_pick.main(["--strict"]) == 0


def test_pick_order_cool_first():
    report = capacity_pick.build_report(_fixture_budget(), active_in_flight={"codex": 2})
    picks = report["pick_order"]
    avoid_lanes = [p["lane"] for p in picks if p["pick"] == "AVOID"]
    ranked = [p for p in picks if p["pick"] != "AVOID"]
    assert "codex" in avoid_lanes
    assert "claude" in avoid_lanes
    assert "gemini" in avoid_lanes
    assert "glm" in avoid_lanes
    assert ranked[0]["lane"] == "cursor"
    # glm must never rank as a pick, even though _CODE_LANE_PRIORITY used to
    # place it #2 — it is force-AVOID via RETIRED_AGENT_ALIASES.
    assert "glm" not in [p["lane"] for p in ranked]


def test_format_includes_rec():
    report = capacity_pick.build_report(_fixture_budget())
    table = capacity_pick.format_table(report["rows"])
    assert "lane" in table and "codex" in table and "cursor" in table
    human = capacity_pick.format_human(report)
    assert "recommendation.primary_agent_for_code: cursor" in human
    assert "pick order (code implement):" in human
    assert "AVOID:codex" in human or "AVOID:claude" in human


def test_main_json_fixture(monkeypatch, capsys):
    monkeypatch.setattr(
        capacity_pick,
        "fetch_active_in_flight",
        lambda **_kwargs: {"cursor": 0},
    )

    fake_budget = _fixture_budget()

    from scripts.fleet import usage

    monkeypatch.setattr(usage, "read_budget", lambda **_kwargs: fake_budget)

    rc = capacity_pick.main(["--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["recommendation"]["primary_agent_for_code"] == "cursor"
    assert any(row["lane"] == "codex" and row["avoid"] for row in payload["rows"])


def test_main_strict_no_cool(monkeypatch, capsys):
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda **_kwargs: {})
    hot_only = {
        "generated_at": "2026-08-12T12:00:00Z",
        "agents": {lane: {"status": "hot", "burn_pct_7d": 90.0} for lane in capacity_pick.CODE_LANES},
        "in_flight": {},
        "recommendation": {"primary_agent_for_code": None, "rationale": "", "warnings": []},
        "diagnostics": {},
    }
    from scripts.fleet import usage

    monkeypatch.setattr(usage, "read_budget", lambda **_kwargs: hot_only)
    assert capacity_pick.main(["--strict"]) == 2
    assert "no cool/warm lane" in capsys.readouterr().err


@pytest.mark.parametrize("change", [
    {"total_balance": 0}, {"is_available": False}, {"total_balance": 4.99},
    {"probe_state": "NEED_PROBE"}, {"freshness": "unavailable"},
    {"freshness": "stale_last_good"}, {"age_s": 601},
])
def test_prepaid_deepseek_avoid(change):
    budget = _fixture_budget()
    budget["api_accounts"]["deepseek"].update(change)
    budget["recommendation"]["primary_agent_for_code"] = "deepseek"
    report = capacity_pick.build_report(budget)
    deepseek = next(row for row in report["pick_order"] if row["lane"] == "deepseek")
    assert deepseek["pick"] == "AVOID"
    assert deepseek["remaining_pct"] is None
    assert report["recommendation"]["primary_agent_for_code"] is None


def test_unavailable_subscription_never_cool():
    budget = _fixture_budget()
    budget["agents"]["cursor"]["codexbar"]["freshness"] = "unavailable"
    row = next(row for row in capacity_pick.build_lane_rows(budget) if row["lane"] == "cursor")
    assert row["status"] == "unknown"


def _gemini_only_budget() -> dict:
    """Live-shape budget: PROVIDER_TO_LANE keys AGY quota under 'gemini'; no 'agy' entry."""
    budget = _fixture_budget()
    del budget["agents"]["agy"]
    budget["agents"]["gemini"] = {
        "status": "cool",
        "remaining_pct": 92.0,
        "burn_pct_7d": 8.0,
        "freshness": "fresh",
        "codexbar": {
            "will_last_to_reset": True,
            "pace_summary": "on pace",
            "weekly_remaining_pct": 92.0,
        },
    }
    return budget


def test_agy_mirrors_retired_gemini_quota():
    rows = {r["lane"]: r for r in capacity_pick.build_lane_rows(_gemini_only_budget())}
    agy = rows["agy"]
    assert agy["status"] == "cool"
    assert agy["remaining_pct"] == 92.0
    assert agy["will_last"] is True
    assert agy["pace"] == "on pace"
    assert agy["avoid"] is False
    assert "quota:gemini" in agy["notes"]
    # The retired source row keeps the same reading for visibility but stays AVOID.
    gemini = rows["gemini"]
    assert gemini["avoid"] is True
    assert "retired→agy" in gemini["notes"]
    assert gemini["remaining_pct"] == 92.0


def test_agy_mirror_is_pickable_and_recommendation_substitutes():
    budget = _gemini_only_budget()
    budget["recommendation"]["primary_agent_for_code"] = "gemini"
    report = capacity_pick.build_report(budget)
    assert report["recommendation"]["primary_agent_for_code"] == "agy"
    assert any("substituted" in w for w in report["recommendation"]["warnings"])
    ranked = [p for p in report["pick_order"] if p["pick"] != "AVOID"]
    assert "agy" in [p["lane"] for p in ranked]
    assert "gemini" not in [p["lane"] for p in ranked]
    assert report["cooler_lanes"] and "agy" in report["cooler_lanes"]


def test_agy_own_entry_wins_over_mirror():
    budget = _gemini_only_budget()
    budget["agents"]["agy"] = {"status": "warm", "remaining_pct": 55.0}
    row = next(r for r in capacity_pick.build_lane_rows(budget) if r["lane"] == "agy")
    assert row["status"] == "warm"
    assert row["remaining_pct"] == 55.0
    assert "quota:gemini" not in row["notes"]


def test_agy_mirror_propagates_probe_failure():
    budget = _gemini_only_budget()
    budget["agents"]["gemini"] = {
        "status": "unknown",
        "freshness": "unavailable",
        "codexbar": {"freshness": "unavailable", "auth_error": "agy /usage failed"},
    }
    row = next(r for r in capacity_pick.build_lane_rows(budget) if r["lane"] == "agy")
    assert row["status"] == "unknown"
    assert row["remaining_pct"] is None
    assert "quota:gemini" in row["notes"]


def test_agy_mirror_need_login_is_avoid():
    budget = _gemini_only_budget()
    budget["agents"]["gemini"] = {
        "status": "unknown",
        "login_state": "NEED_LOGIN",
        "probe_state": "NEED_LOGIN",
    }
    row = next(r for r in capacity_pick.build_lane_rows(budget) if r["lane"] == "agy")
    assert row["avoid"] is True
    assert "NEED_LOGIN" in row["notes"]


def test_cursor_does_not_inherit_glm_quota():
    """glm→cursor is retirement-only; Cursor must never pick up Z.AI capacity."""
    budget = _fixture_budget()
    budget["agents"]["cursor"] = {"status": "unknown", "freshness": "unavailable"}
    budget["agents"]["glm"] = {
        "status": "cool",
        "remaining_pct": 88.0,
        "codexbar": {"will_last_to_reset": True, "pace_summary": "on pace"},
    }
    row = next(r for r in capacity_pick.build_lane_rows(budget) if r["lane"] == "cursor")
    assert row["status"] == "unknown"
    assert row["remaining_pct"] is None
    assert "quota:glm" not in row["notes"]
