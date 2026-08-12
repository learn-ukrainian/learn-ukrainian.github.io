"""Unit tests for scripts.fleet.capacity_pick pure formatting (no live CodexBar)."""

from __future__ import annotations

import json

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
            "deepseek": {"status": "cool", "burn_pct_7d": 10.0, "remaining_pct": 90.0},
            "glm": {"status": "cool", "burn_pct_7d": 12.0, "remaining_pct": 88.0},
        },
        "in_flight": {"cursor": 0, "codex": 1},
        "recommendation": {
            "primary_agent_for_code": "cursor",
            "rationale": "Cursor is cool; Codex is in deficit.",
            "warnings": ["lane codex is in deficit"],
        },
        "diagnostics": {"records_loaded": 4, "stale": False},
    }


def test_build_lane_rows_marks_avoid_for_hot_near_cap_deficit():
    rows = {r["lane"]: r for r in capacity_pick.build_lane_rows(_fixture_budget())}
    assert rows["codex"]["avoid"] is True
    assert "AVOID" in rows["codex"]["notes"]
    assert "deficit" in rows["codex"]["notes"]
    assert rows["claude"]["avoid"] is True
    assert rows["cursor"]["avoid"] is False
    assert rows["cursor"]["status"] == "cool"
    assert rows["cursor"]["will_last"] is True


def test_build_pick_order_puts_cool_before_avoid():
    report = capacity_pick.build_report(_fixture_budget(), active_in_flight={"codex": 2})
    picks = report["pick_order"]
    avoid_lanes = [p["lane"] for p in picks if p["pick"] == "AVOID"]
    ranked = [p for p in picks if p["pick"] != "AVOID"]
    assert "codex" in avoid_lanes
    assert "claude" in avoid_lanes
    assert ranked[0]["lane"] in {"cursor", "deepseek", "glm", "agy", "grok"}
    assert all(p["lane"] not in avoid_lanes for p in ranked)
    assert report["recommendation"]["primary_agent_for_code"] == "cursor"
    assert "cursor" in report["cooler_lanes"]


def test_format_table_and_human_include_recommendation():
    report = capacity_pick.build_report(_fixture_budget())
    table = capacity_pick.format_table(report["rows"])
    assert "lane" in table and "codex" in table and "cursor" in table
    human = capacity_pick.format_human(report)
    assert "recommendation.primary_agent_for_code: cursor" in human
    assert "pick order (code implement):" in human
    assert "AVOID:codex" in human or "AVOID:claude" in human


def test_main_json_uses_fixture_compute(monkeypatch, capsys):
    monkeypatch.setattr(
        capacity_pick,
        "fetch_active_in_flight",
        lambda **_kwargs: {"cursor": 0},
    )

    fake_budget = _fixture_budget()

    import scripts.api.state_router as state_router

    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **_kwargs: fake_budget)

    rc = capacity_pick.main(["--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["recommendation"]["primary_agent_for_code"] == "cursor"
    assert any(row["lane"] == "codex" and row["avoid"] for row in payload["rows"])


def test_main_strict_exits_when_no_cool(monkeypatch, capsys):
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda **_kwargs: {})
    hot_only = {
        "generated_at": "2026-08-12T12:00:00Z",
        "agents": {lane: {"status": "hot", "burn_pct_7d": 90.0} for lane in capacity_pick.CODE_LANES},
        "in_flight": {},
        "recommendation": {"primary_agent_for_code": None, "rationale": "", "warnings": []},
        "diagnostics": {},
    }
    import scripts.api.state_router as state_router

    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **_kwargs: hot_only)
    assert capacity_pick.main(["--strict"]) == 2
    assert "no cool/warm lane" in capsys.readouterr().err
