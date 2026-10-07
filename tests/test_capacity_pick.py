"""Unit tests for scripts.fleet.capacity_pick pure formatting (no live CodexBar)."""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime, timedelta

import pytest

from scripts.fleet import capacity_pick, credit_lane
from scripts.fleet.reset_reserve import codex_reset_reserve_eligible


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
                    "weekly_expected_pct": 40.0,
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
        "api_accounts": {
            "deepseek": {
                "probe_state": "ok",
                "freshness": "fresh",
                "age_s": 0,
                "currency": "USD",
                "total_balance": 30.0,
                "is_available": True,
            }
        },
        "in_flight": {"cursor": 0, "codex": 1},
        "recommendation": {
            "primary_agent_for_code": "cursor",
            "rationale": "Cursor is cool; Codex is in deficit.",
            "warnings": ["lane codex is in deficit"],
        },
        "diagnostics": {"records_loaded": 4, "stale": False},
    }


def test_on_pace_band_is_not_avoid_but_real_deficit_is():
    budget = _fixture_budget()
    budget["agents"]["grok"] = {
        "status": "warm",
        "burn_pct_7d": 41.5,
        "remaining_pct": 58.5,
        "codexbar": {
            "will_last_to_reset": False,
            "weekly_pace_delta_pct": 1.5,
            "weekly_expected_pct": 40.0,
            "pace_summary": "On pace",
        },
    }
    budget["agents"]["kimi"] = {
        "status": "warm",
        "burn_pct_7d": 25.0,
        "remaining_pct": 75.0,
        "codexbar": {
            "will_last_to_reset": False,
            "weekly_pace_delta_pct": 12.0,
            "weekly_expected_pct": 13.0,
            "pace_summary": "won't last",
        },
    }
    rows = {r["lane"]: r for r in capacity_pick.build_lane_rows(budget)}
    assert rows["grok"]["avoid"] is False
    assert "deficit" not in rows["grok"]["notes"]
    assert rows["kimi"]["avoid"] is True
    assert "deficit" in rows["kimi"]["notes"]


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
    now = datetime.now(UTC)
    budget = _fixture_budget()
    budget["agents"]["codex"].update(
        {
            "eligible": True,
            "health": {"healthy": True},
            "freshness": "fresh",
            "age_s": 10,
            "status_source": "weekly_pace",
            "reset_credits": {
                "available_count": 2,
                "expires_at": ["2099-01-01T00:00:00Z", "2099-02-01T00:00:00Z"],
                "fetched_at": datetime.now(UTC).isoformat(),
            },
            "runtime": {"headroom_blocked": False, "rate_limited": 0, "last_rate_limited_at": None},
            "codexbar": {
                **budget["agents"]["codex"]["codexbar"],
                "weekly_used_pct": 72.0,
                "weekly_resets_at": (now + timedelta(days=3.5)).isoformat(),
                "windows": {"primary": {"remaining_pct": 12.0}},
            },
        }
    )
    reserve = {
        "available": True,
        "provider": "codex",
        "remaining_resets": 2,
        "confirmed_at": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
        "expires_at": "2099-03-01T00:00:00Z",
    }
    rows = {r["lane"]: r for r in capacity_pick.build_lane_rows(budget, reset_reserve=reserve)}
    assert rows["codex"]["avoid"] is False
    assert rows["codex"]["status"] == "cool"
    assert rows["codex"]["pace_deficit"]["covered_by"] == ["free full reset"]
    assert rows["codex"]["will_last"] is False
    assert rows["codex"]["reset_reserve_eligible"] is True
    assert "reset reserve eligible (2 remaining)" in rows["codex"]["notes"]

    report = capacity_pick.build_report(budget, reset_reserve=reserve)
    assert report["pick_order"][0]["lane"] == "codex"
    assert "codex" in report["cooler_lanes"]

    budget["agents"]["codex"]["runtime"]["headroom_blocked"] = True
    blocked = {r["lane"]: r for r in capacity_pick.build_lane_rows(budget, reset_reserve=reserve)}
    assert blocked["codex"]["avoid"] is True


@pytest.mark.parametrize(("asserted", "live", "expected"), [(5, 2, 2), (2, 5, 2)])
def test_raw_reset_reserve_note_reports_effective_count(asserted, live, expected):
    now = datetime.now(UTC)
    budget = _fixture_budget()
    budget["agents"]["codex"].update(
        eligible=True,
        health={"healthy": True},
        freshness="fresh",
        age_s=0,
        status_source="weekly_pace",
        reset_credits={
            "available_count": live,
            "expires_at": [None] * live,
            "fetched_at": now.isoformat(),
        },
        codexbar={
            **budget["agents"]["codex"]["codexbar"],
            "weekly_used_pct": 72.0,
            "weekly_resets_at": (now + timedelta(days=3.5)).isoformat(),
            "windows": {"primary": {"remaining_pct": 12.0}},
        },
        runtime={"headroom_blocked": False, "rate_limited": 0, "last_rate_limited_at": None},
    )
    reserve = {
        "available": True,
        "provider": "codex",
        "remaining_resets": asserted,
        "confirmed_at": (now - timedelta(minutes=1)).isoformat(),
        "expires_at": (now + timedelta(days=1)).isoformat(),
    }

    row = next(row for row in capacity_pick.build_lane_rows(budget, reset_reserve=reserve) if row["lane"] == "codex")

    assert row["reset_reserve_eligible"] is True
    assert f"reset reserve eligible ({expected} remaining)" in row["notes"]
    assert reserve["remaining_resets"] == asserted


def test_reset_reserve_never_lifts_the_owner_avoid():
    """#9740 P1: a hot label the owner keeps (not weekly pace) stays AVOID whatever the reserve."""
    now = datetime.now(UTC)
    budget = _fixture_budget()
    info = budget["agents"]["codex"]
    info.update(
        eligible=True,
        health={"healthy": True},
        freshness="fresh",
        age_s=0,
        reset_credits={"available_count": 2, "expires_at": [None, None], "fetched_at": now.isoformat()},
        codexbar={
            **info["codexbar"],
            "weekly_used_pct": 72.0,
            "weekly_resets_at": (now + timedelta(days=3.5)).isoformat(),
            "windows": {"primary": {"remaining_pct": 12.0}},
        },
        runtime={"headroom_blocked": False, "rate_limited": 0, "last_rate_limited_at": None},
    )
    reserve = {
        "available": True,
        "provider": "codex",
        "remaining_resets": 2,
        "confirmed_at": (now - timedelta(minutes=1)).isoformat(),
        "expires_at": (now + timedelta(days=1)).isoformat(),
    }
    facts = credit_lane.routing_facts("codex", info, model=None, snapshot_metadata=budget["diagnostics"])
    assert facts.capacity == credit_lane.CAPACITY_AVOID
    # Every reserve precondition but the owner's verdict holds.
    assert codex_reset_reserve_eligible(reserve, info, owner_capacity=credit_lane.CAPACITY_VERIFIED)

    rows = capacity_pick.build_lane_rows(budget, reset_reserve=reserve)
    row = next(row for row in rows if row["lane"] == "codex")
    assert row["avoid"] is True
    assert row["reset_reserve_eligible"] is False
    assert row["capacity"]["state"] == credit_lane.CAPACITY_AVOID
    assert "codex" not in capacity_pick.cooler_lanes(rows)
    assert capacity_pick.build_report(budget, reset_reserve=reserve)["pick_order"][0]["lane"] != "codex"


def test_capacity_uses_snapshot_inventory_without_process_cache(monkeypatch, tmp_path):
    from scripts.fleet import reset_reserve

    now = datetime.now(UTC)
    budget = _fixture_budget()
    info = budget["agents"]["codex"]
    info.update(
        eligible=True,
        health={"healthy": True},
        freshness="fresh",
        age_s=10,
        status_source="weekly_pace",
        runtime={"headroom_blocked": False, "rate_limited": 0, "last_rate_limited_at": None},
        reset_credits={
            "available_count": 1,
            "expires_at": ["2099-01-01T00:00:00Z"],
            "fetched_at": now.isoformat(),
        },
    )
    info["codexbar"].update(
        weekly_used_pct=72,
        weekly_resets_at=(now + timedelta(days=3.5)).isoformat(),
        windows={"primary": {"remaining_pct": 12}},
    )
    path = tmp_path / "batch_state" / "routing_budget" / "operator_reset_reserve.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": reset_reserve.SCHEMA_VERSION,
                "provider": "codex",
                "remaining_resets": 2,
                "confirmed_at": (now - timedelta(days=7)).isoformat(),
                "expires_at": "2099-03-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(capacity_pick, "__file__", str(tmp_path / "scripts" / "fleet" / "capacity_pick.py"))
    monkeypatch.setattr(
        reset_reserve, "get_provider_usage_data", lambda _provider: pytest.fail("snapshot inventory must be used")
    )
    row = next(row for row in capacity_pick.build_lane_rows(budget) if row["lane"] == "codex")
    assert row["avoid"] is False
    assert "reset reserve eligible (1 remaining)" in row["notes"]
    info["reset_credits"]["available_count"] = 0
    row = next(row for row in capacity_pick.build_lane_rows(budget) if row["lane"] == "codex")
    assert row["avoid"] is True
    assert row["reset_reserve_eligible"] is False


def test_stale_capacity_snapshot_disables_reserve_and_strict_pick(monkeypatch):
    budget = _fixture_budget()
    budget["diagnostics"] = {"stale": True}
    budget["agents"]["codex"].update(
        {
            "eligible": True,
            "health": {"healthy": True},
            "freshness": "fresh",
            "age_s": 10,
            "reset_credits": {
                "available_count": 2,
                "expires_at": ["2099-01-01T00:00:00Z", "2099-02-01T00:00:00Z"],
                "fetched_at": datetime.now(UTC).isoformat(),
            },
            "runtime": {"headroom_blocked": False, "rate_limited": 0, "last_rate_limited_at": None},
            "codexbar": {
                **budget["agents"]["codex"]["codexbar"],
                "weekly_used_pct": 72.0,
                "windows": {"primary": {"remaining_pct": 12.0}},
            },
        }
    )
    reserve = {
        "available": True,
        "provider": "codex",
        "remaining_resets": 2,
        "confirmed_at": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
        "expires_at": "2099-03-01T00:00:00Z",
    }
    row = next(row for row in capacity_pick.build_lane_rows(budget, reset_reserve=reserve) if row["lane"] == "codex")
    assert row["avoid"] is True
    assert row["reset_reserve_eligible"] is False

    # On a fresh snapshot the owner verifies a weekly-pace label whose deficit the live resets cover.
    fresh_codex = copy.deepcopy(budget["agents"]["codex"])
    fresh_codex["status_source"] = "weekly_pace"
    fresh_codex["codexbar"]["weekly_resets_at"] = (datetime.now(UTC) + timedelta(days=3.5)).isoformat()
    only_codex = {
        "agents": {"codex": fresh_codex},
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


@pytest.mark.parametrize(
    "change",
    [
        {"total_balance": 0},
        {"is_available": False},
        {"total_balance": 4.99},
        {"probe_state": "NEED_PROBE"},
        {"freshness": "unavailable"},
        {"freshness": "stale_last_good"},
        {"age_s": 601},
    ],
)
def test_prepaid_deepseek_avoid(change):
    budget = _fixture_budget()
    budget["api_accounts"]["deepseek"].update(change)
    budget["recommendation"]["primary_agent_for_code"] = "deepseek"
    report = capacity_pick.build_report(budget)
    deepseek = next(row for row in report["pick_order"] if row["lane"] == "deepseek")
    assert deepseek["pick"] == "AVOID"
    assert deepseek["remaining_pct"] is None
    assert report["recommendation"]["primary_agent_for_code"] is None


def test_unhealthy_deepseek_account_row_is_avoid():
    """A lane-health record on an account row demotes it to AVOID with the error."""
    budget = _fixture_budget()
    budget["api_accounts"]["deepseek"]["health"] = {
        "healthy": False,
        "last_error": "provider config lost (#8514)",
    }
    row = next(r for r in capacity_pick.build_lane_rows(budget) if r["lane"] == "deepseek")
    assert row["avoid"] is True
    assert "AVOID" in row["notes"]
    assert "unhealthy: provider config lost (#8514)" in row["notes"]
    report = capacity_pick.build_report(budget)
    pick = next(p for p in report["pick_order"] if p["lane"] == "deepseek")
    assert pick["pick"] == "AVOID"


def test_healthy_deepseek_account_row_unaffected():
    """health.healthy True adds no unhealthy note; the lane stays excluded from picks."""
    budget = _fixture_budget()
    baseline = next(r for r in capacity_pick.build_lane_rows(budget) if r["lane"] == "deepseek")
    budget["api_accounts"]["deepseek"]["health"] = {"healthy": True, "last_error": ""}
    row = next(r for r in capacity_pick.build_lane_rows(budget) if r["lane"] == "deepseek")
    assert row["avoid"] is baseline["avoid"] is True
    assert "unhealthy:" not in row["notes"]


def test_deepseek_prepaid_lane_is_never_a_pick():
    """A cool, funded, healthy DeepSeek account stays visible but is AVOID and never a cooler seat."""
    report = capacity_pick.build_report(_fixture_budget())
    row = next(r for r in report["pick_order"] if r["lane"] == "deepseek")
    assert row["pick"] == "AVOID"
    assert "excluded from dispatch and review" in row["notes"]
    assert row["capacity"]["state"] == credit_lane.CAPACITY_AVOID
    assert "deepseek" not in report["cooler_lanes"]


def _pick_row(lane: str, status: str, remaining: float | None, in_flight: int | None, *, avoid: bool = False) -> dict:
    return {
        "lane": lane,
        "status": status,
        "remaining_pct": remaining,
        "in_flight": in_flight,
        "avoid": avoid,
        "capacity": {"state": credit_lane.CAPACITY_AVOID if avoid else credit_lane.CAPACITY_VERIFIED},
        "reset_reserve_eligible": False,
    }


def _ranked(rows: list[dict]) -> list[str]:
    return [p["lane"] for p in capacity_pick.build_pick_order(rows) if p["pick"] != "AVOID"]


def test_pick_order_prefers_cool_lane_with_most_headroom_then_fewest_in_flight():
    """2026-10-07 live shape: codex 92%/2 in flight, grok 47%/2, kimi 94%/0, agy 99.9%/0; claude, cursor hot."""
    rows = [
        _pick_row("claude", "hot", 56.0, 1, avoid=True),
        _pick_row("codex", "cool", 92.0, 2),
        _pick_row("grok", "cool", 47.0, 2),
        _pick_row("cursor", "hot", 16.4, 0, avoid=True),
        _pick_row("kimi", "cool", 94.0, 0),
        _pick_row("agy", "cool", 99.9, 0),
    ]
    assert _ranked(rows) == ["kimi", "agy", "codex", "grok"]


def test_pick_order_falls_back_to_static_priority_without_quota():
    rows = [_pick_row(lane, "cool", None, 0) for lane in ("agy", "kimi", "grok", "codex")]
    assert _ranked(rows) == ["codex", "grok", "kimi", "agy"]


def test_pick_order_known_headroom_ranks_before_unknown_headroom():
    rows = [_pick_row("codex", "cool", None, 0), _pick_row("agy", "cool", 15.0, 3)]
    assert _ranked(rows) == ["agy", "codex"]


def test_pick_order_status_still_outranks_headroom_and_cool_cursor_still_leads():
    rows = [
        _pick_row("agy", "warm", 99.0, 0),
        _pick_row("kimi", "cool", 60.0, 4),
        _pick_row("cursor", "cool", 30.0, 1),
    ]
    assert _ranked(rows) == ["cursor", "kimi", "agy"]


_WS_NOW = datetime(2026, 10, 7, 18, 0, tzinfo=UTC)


def _write_record(agent: str, status: str, *, mode: str = "workspace-write", hours_ago: float = 1.0) -> dict:
    stamp = (_WS_NOW - timedelta(hours=hours_ago)).isoformat()
    return {"agent": agent, "mode": mode, "status": status, "started_at": stamp, "finished_at": stamp}


def test_write_success_stats_counts_terminal_write_attempts_in_window():
    records = [
        _write_record("kimi", "done"),
        _write_record("kimi", "failed"),
        _write_record("kimi", "failed"),
        _write_record("kimi", "no_deliverable"),
        _write_record("kimi", "dry_run"),
        _write_record("kimi", "running"),
        _write_record("kimi", "cancelled"),
        _write_record("kimi", "failed", mode="read-only"),
        _write_record("kimi", "failed", hours_ago=8 * 24),
        _write_record("grok-build", "done", mode="danger"),
        _write_record("gemini", "failed"),
    ]
    stats = capacity_pick.write_success_stats(records, now=_WS_NOW)
    assert stats["kimi"] == {"attempts": 4, "done": 1, "rate": 0.25, "demoted": True}
    assert stats["grok"] == {"attempts": 1, "done": 1, "rate": 1.0, "demoted": False}
    assert stats["agy"]["attempts"] == 1 and stats["agy"]["demoted"] is False


def test_write_success_under_min_attempts_is_not_demoted():
    stats = capacity_pick.write_success_stats(
        [_write_record("agy", "failed"), _write_record("agy", "no_deliverable")], now=_WS_NOW
    )
    assert stats["agy"] == {"attempts": 2, "done": 0, "rate": 0.0, "demoted": False}


def test_write_success_at_threshold_is_not_demoted():
    records = [_write_record("codex", "done")] * 3 + [_write_record("codex", "failed")] * 2
    assert capacity_pick.write_success_stats(records, now=_WS_NOW)["codex"]["demoted"] is False  # 60% exactly


def test_kimi_at_one_in_four_cannot_take_first_place_on_headroom_alone():
    rows = [
        _pick_row("codex", "cool", 92.0, 2),
        _pick_row("kimi", "cool", 94.0, 0),
        _pick_row("agy", "cool", 91.0, 1),
    ]
    assert _ranked(rows)[0] == "kimi"
    rows[1]["write_success"] = {"attempts": 4, "done": 1, "rate": 0.25, "demoted": True}
    ranked = _ranked(rows)
    assert ranked[0] != "kimi"
    assert ranked == ["agy", "codex", "kimi"]


def test_build_report_attaches_write_success_and_notes_the_demotion():
    budget = _fixture_budget()
    budget["agents"]["kimi"] = {"status": "cool", "burn_pct_7d": 6.0, "remaining_pct": 94.0}
    stats = {
        "kimi": {"attempts": 4, "done": 1, "rate": 0.25, "demoted": True},
        "agy": {"attempts": 2, "done": 0, "rate": 0.0, "demoted": False},
    }
    report = capacity_pick.build_report(budget, active_in_flight={}, write_success=stats)
    rows = {row["lane"]: row for row in report["rows"]}
    assert rows["kimi"]["write_success"]["demoted"] is True
    assert "write success 1/4 in 7d (<60%): one headroom band down" in rows["kimi"]["notes"]
    assert rows["agy"]["write_success"]["demoted"] is False
    assert rows["grok"]["write_success"] == {"attempts": 0, "done": 0, "rate": None, "demoted": False}
    assert report["write_success"]["kimi"]["attempts"] == 4
    without = capacity_pick.build_report(budget, active_in_flight={})
    assert all("write_success" not in row for row in without["rows"])


def test_load_write_success_stats_reads_hot_and_archived_records(tmp_path):
    (tmp_path / "archive").mkdir()
    (tmp_path / "a.json").write_text(json.dumps(_write_record("kimi", "done")))
    (tmp_path / "b.20261007T170000Z.archived.json").write_text(json.dumps(_write_record("kimi", "failed")))
    (tmp_path / "archive" / "c.json").write_text(json.dumps(_write_record("kimi", "failed")))
    (tmp_path / "broken.json").write_text("{not json")
    stats = capacity_pick.load_write_success_stats(tmp_path, now=_WS_NOW + timedelta(hours=1))
    assert stats["kimi"] == {"attempts": 3, "done": 1, "rate": 1 / 3, "demoted": True}
    assert capacity_pick.load_write_success_stats(tmp_path, now=_WS_NOW + timedelta(days=8)) == {}
    assert capacity_pick.load_write_success_stats(tmp_path / "missing") is None


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


# --- #9517: near-cap Codex with a credit balance ----------------------------

_CREDIT_NOW = datetime(2026, 10, 2, 17, 0, tzinfo=UTC)


def _credit_codex(**overrides) -> dict:
    info = {
        "status": "near_cap",
        "remaining_pct": 1.0,
        "burn_pct_7d": 99.0,
        "freshness": "fresh",
        "age_s": 60.0,
        "eligible": True,
        "health": {"healthy": True},
        "credit_balance": 62500.0,
        "runtime": {"headroom_blocked": False, "rate_limited": 0},
        "codexbar": {
            "weekly_remaining_pct": 1.0,
            "freshness": "fresh",
            "age_s": 60.0,
            "stale": False,
            "fetched_at": "2026-10-02T16:59:00Z",
        },
    }
    info.update(overrides)
    return info


def _credit_rows(codex: dict) -> list[dict]:
    from scripts.fleet.reset_reserve import unavailable_reserve

    budget = {
        "agents": {
            "codex": codex,
            "cursor": {"status": "warm", "remaining_pct": 40.0, "health": {"healthy": True}},
            "claude": {"status": "hot", "remaining_pct": 30.0, "health": {"healthy": True}},
        },
        "api_accounts": {},
        "diagnostics": {"stale": False},
    }
    return capacity_pick.build_lane_rows(
        budget, active_in_flight={}, reset_reserve=unavailable_reserve(), now=_CREDIT_NOW
    )


def test_credit_balance_codex_picks_after_plan_backed_warm_seat():
    """Regression guard: capacity_pick already ordered a credit-backed lane this way before #9517.

    It passes on the merge-base too; it pins the existing behaviour the
    routing-budget credit field now feeds, it does not prove new behaviour.
    """
    rows = _credit_rows(_credit_codex())
    codex = next(row for row in rows if row["lane"] == "codex")
    assert (codex["status"], codex["avoid"]) == ("credit_balance_present", False)
    order = capacity_pick.build_pick_order(rows)
    usable = [entry["lane"] for entry in order if entry["pick"] != "AVOID"]
    # After every usable plan-backed seat (warm cursor first, unknown-status lanes next), never AVOID.
    assert usable[0] == "cursor" and usable[-1] == "codex"
    assert next(entry["pick"] for entry in order if entry["lane"] == "claude") == "AVOID"
    assert "codex" in capacity_pick.cooler_lanes(rows)


@pytest.mark.parametrize(
    ("overrides", "state"),
    [
        ({"credit_balance": 0.0}, "credits_exhausted"),
        ({"credit_balance": None}, "credits_unverified"),
        ({"runtime": {"headroom_blocked": True, "rate_limited": 3}}, "credit_use_unconfirmed"),
    ],
    ids=["exhausted", "missing", "rate-limited"],
)
def test_codex_without_usable_credits_stays_near_cap_avoid(overrides, state):
    rows = _credit_rows(_credit_codex(**overrides))
    codex = next(row for row in rows if row["lane"] == "codex")
    assert (codex["credit"]["state"], codex["status"], codex["avoid"]) == (state, "near_cap", True)
    assert "codex" not in capacity_pick.cooler_lanes(rows)


# --- #9740: shared routing facts in rows, order and CLI -------------------------


def test_unknown_load_renders_as_dash_and_null(monkeypatch):
    budget = _fixture_budget()
    budget.pop("in_flight")
    rows = capacity_pick.build_lane_rows(budget, reset_reserve={"available": False})
    assert {row["in_flight"] for row in rows} == {None}
    assert all("idle" not in row["notes"].split("; ") for row in rows)
    table = capacity_pick.format_table(rows)
    cursor_line = next(line for line in table.splitlines() if line.startswith("cursor"))
    assert " — " in cursor_line or cursor_line.split(" | ")[5].strip() == "—"


def test_unreadable_active_work_is_none_not_empty(monkeypatch):
    def broken(*_a, **_k):
        raise OSError("down")

    monkeypatch.setattr(capacity_pick.urllib.request, "urlopen", broken)
    assert capacity_pick.fetch_active_in_flight() is None


def test_rows_carry_owner_facts_and_remaining_reading():
    """F1: the row's remaining is the owner's tightest window; every row carries the facts."""
    budget = _fixture_budget()
    budget["agents"]["grok"]["codexbar"] = {"primary_remaining_pct": 3.0}
    rows = {row["lane"]: row for row in capacity_pick.build_lane_rows(budget, reset_reserve={"available": False})}
    assert rows["grok"]["remaining_pct"] == 3.0
    assert rows["grok"]["remaining_source"] == "codexbar.primary_remaining_pct"
    for row in rows.values():
        assert row["routing_facts"]["plan_remaining_pct"] == row["remaining_pct"]
        assert row["capacity"]["state"] in {"verified", "unknown", "unknown_stale", "avoid"}


def test_stale_unknown_never_ranks_ahead_of_verified_capacity():
    """F2 rank-inversion control (A5): a stale-advisory lane with far more remaining allowance
    ranks after cool, warm and credit-balance rows, and is not a cooler lane or --strict success."""
    stale = {
        "lane": "codex",
        "status": "unknown",
        "remaining_pct": 99.0,
        "in_flight": 0,
        "avoid": False,
        "capacity": {"state": "unknown_stale"},
    }
    warm = {
        "lane": "kimi",
        "status": "warm",
        "remaining_pct": 11.0,
        "in_flight": 3,
        "avoid": False,
        "capacity": {"state": "verified"},
    }
    credit = {"lane": "grok", "status": "credit_balance_present", "remaining_pct": 2.0, "in_flight": 0, "avoid": False}
    order = capacity_pick.build_pick_order([stale, warm, credit])
    assert [row["lane"] for row in order] == ["kimi", "grok", "codex"]
    assert capacity_pick.cooler_lanes([stale]) == []


def test_strict_fails_when_the_only_capacity_is_stale_advisory(monkeypatch, capsys):
    from scripts.fleet import usage

    budget = {
        "agents": {
            "codex": {
                "status": "hot",
                "status_source": "weekly_pace",
                "remaining_pct": 60.0,
                "freshness": "stale_last_good",
                "codexbar": {"weekly_expected_pct": 25.0, "weekly_pace_delta_pct": 15.0, "will_last_to_reset": False},
            }
        },
        "diagnostics": {"stale": True},
        "recommendation": {"primary_agent_for_code": None, "warnings": []},
    }
    monkeypatch.setattr(usage, "read_budget", lambda **_kwargs: budget)
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda **_kwargs: {})
    monkeypatch.setattr(capacity_pick, "load_reset_reserve", lambda *_a, **_k: {"available": False})
    monkeypatch.setattr(capacity_pick, "admission_status", lambda: {"admitted": None, "line": "admission: fixture"})
    assert capacity_pick.main(["--strict", "--json"]) == 2
    report = json.loads(capsys.readouterr().out)
    codex = next(row for row in report["rows"] if row["lane"] == "codex")
    assert (codex["status"], codex["avoid"], codex["capacity"]["state"]) == ("unknown", False, "unknown_stale")
    assert report["cooler_lanes"] == []
