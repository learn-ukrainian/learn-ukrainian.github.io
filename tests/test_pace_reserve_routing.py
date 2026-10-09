"""#9615: the same reserve-backed pace decision in all five routing consumers."""

from __future__ import annotations

import copy
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from scripts import delegate
from scripts.api import state_router
from scripts.fleet import capacity_pick, credit_lane, idle_settle
from scripts.fleet.reset_reserve import unavailable_reserve
from scripts.review.reviewer_resolver import OPENAI_FRONTIER, ResolverInputs, evaluate_candidate, resolve_reviewer
from tests.api.test_routing_budget import _configure_base
from tests.api.test_routing_budget_endpoint import _record


@pytest.mark.parametrize(
    ("used", "expected", "delta", "will_last", "status"),
    [
        (68.0, 76.0, -8.0, True, "cool"),
        (80.0, 79.0, 1.0, False, "warm"),
        (41.0, 40.0, 1.0, False, "cool"),
        (68.0, None, None, None, "warm"),
        (68.0, None, -8.0, True, "warm"),
        (68.0, 0.5, -8.0, True, "warm"),
        (20.0, None, None, None, "cool"),
        (68.0, 60.0, 8.0, False, "hot"),
        (90.0, 98.0, -8.0, True, "near_cap"),
    ],
)
def test_weekly_status_follows_visible_headroom(used, expected, delta, will_last, status):
    pace = {
        "weekly_expected_pct": expected,
        "weekly_pace_delta_pct": delta,
        "will_last_to_reset": will_last,
    }
    info = {
        "status": "near_cap" if used >= 90 else "warm" if used >= 50 else "cool",
        "remaining_pct": 100 - used,
        "codexbar": pace,
    }
    assert state_router._status_from_weekly_used(used, pace, lane="claude", info=info) == status
    assert credit_lane.pace_deficit_state("claude", info)["status"] == status


@pytest.mark.parametrize("reserve", ["credits", "resets"])
@pytest.mark.parametrize("delta", [1.0, 10.0])
def test_high_usage_covered_deficit_is_cool(reserve, delta, monkeypatch):
    now = datetime.now(UTC)
    info = {
        "status": "warm",
        "remaining_pct": 20.0,
        "freshness": "fresh",
        "age_s": 0,
        "fetched_at": now.isoformat(),
        "credit_balance": 62500.0 if reserve == "credits" else 0.0,
        "reset_credits": {
            "available_count": 1,
            "expires_at": [(now + timedelta(days=7)).isoformat()],
            "fetched_at": now.isoformat(),
        }
        if reserve == "resets"
        else None,
        "codexbar": {
            "weekly_used_pct": 80.0,
            "weekly_resets_at": (now + timedelta(days=7 * (1 - (80.0 - delta) / 100))).isoformat(),
            "weekly_expected_pct": 80.0 - delta,
            "weekly_pace_delta_pct": delta,
            "will_last_to_reset": False,
        },
    }
    monkeypatch.setattr(
        credit_lane, "read_recent_rate_limits", lambda *_a, **_k: {"count": 0, "last_rate_limited_at": None}
    )
    assert credit_lane.pace_deficit_state("codex", info, now=now)["status"] == "cool"
    assert state_router._status_from_weekly_used(80.0, info["codexbar"], lane="codex", info=info, now=now) == "cool"


@pytest.mark.parametrize("visible", [True, False])
def test_claude_headroom_reaches_routing_consumers(visible, monkeypatch, tmp_path):
    now = datetime(2026, 10, 3, 15, 12, tzinfo=UTC)
    budget_path = _configure_base(monkeypatch, tmp_path)
    native = {
        "status": "healthy",
        "weekly_used_pct": 68.0,
        "weekly_remaining_pct": 32.0,
        "weekly_expected_pct": 76.0 if visible else None,
        "weekly_pace_delta_pct": -8.0 if visible else None,
        "will_last_to_reset": True if visible else None,
        "weekly_resets_at": "2026-10-05T07:00:00Z" if visible else None,
        "freshness": "fresh",
        "age_s": 0,
        "fetched_at": now.isoformat(),
    }
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda lane: native if lane == "claude" else {})
    monkeypatch.setattr(state_router, "get_cursor_lane_usage", lambda: {})
    monkeypatch.setattr(state_router, "summarize_fleet_burn", lambda *_a, **_k: {"windows": {}})
    data = state_router.compute_routing_budget(
        now,
        budget_config_path=budget_path,
        tasks_dir=tmp_path / "tasks",
        project_root=tmp_path,
        curriculum_root=tmp_path,
        batch_state_dir=tmp_path,
    )
    expected_status = "cool" if visible else "warm"
    assert data["agents"]["claude"]["status"] == expected_status
    assert data["agents"]["claude"]["interactive"]["status"] == expected_status
    rows = capacity_pick.build_lane_rows(data, now=now, reset_reserve=unavailable_reserve())
    claude = next(row for row in rows if row["lane"] == "claude")
    assert claude["status"] == expected_status
    # Hold burn and in-flight constant: cool Claude outranks warm Codex;
    # otherwise Codex's lane priority wins between equally warm seats.
    competing = {**claude, "lane": "codex", "status": "warm"}
    assert capacity_pick.build_pick_order([claude, competing])[0]["lane"] == ("claude" if visible else "codex")
    recommendation = state_router._recommend_agent(
        {
            "claude": data["agents"]["claude"],
            "codex": {"status": "warm", "remaining_pct": 32.0, "burn_pct_7d": 10.0, "health": {"healthy": True}},
        },
        [],
        current_time=now,
        authoritative_data_available=True,
    )
    assert recommendation["primary_agent_for_code"] == ("claude" if visible else "codex")
    result = resolve_reviewer(
        ResolverInputs(author_model="gpt-6.1-sol", review_profile="code", risk="critical", routing_snapshot=data)
    )
    assert result.selected is not None
    assert result.selected.route == "claude"
    assert result.selected.health == ("healthy" if visible else "degraded")


@pytest.fixture(
    params=[
        "both",
        "credits",
        "resets",
        "none",
        "stale_credits",
        "rate_limited",
        "expired_resets",
        "unreadable",
        "stale_resets",
        "stale_snapshot",
    ]
)
def reserve_case(request, monkeypatch):
    now = datetime.now(UTC)
    fetched = (now - timedelta(seconds=60)).isoformat()
    info = {
        "status": "hot",
        "status_source": "weekly_pace",
        "remaining_pct": 87.0,
        "burn_pct_7d": 13.0,
        "freshness": "fresh",
        "age_s": 60.0,
        "fetched_at": fetched,
        "credit_balance": 62500.0,
        "reset_credits": {
            "available_count": 2,
            "expires_at": [(now + timedelta(days=19)).isoformat(), (now + timedelta(days=26)).isoformat()],
            "fetched_at": fetched,
        },
        "runtime": {"headroom_blocked": False, "window_s": 300, "rate_limited": 0},
        "codexbar": {
            "weekly_used_pct": 13.0,
            "weekly_resets_at": (now + timedelta(days=7 * (1 - 0.105))).isoformat(),
            "weekly_remaining_pct": 87.0,
            "weekly_pace_delta_pct": 2.5,
            "weekly_expected_pct": 10.5,
            "will_last_to_reset": False,
            "pace_summary": "pace_delta=+2.5%",
            "freshness": "fresh",
            "age_s": 60.0,
            "fetched_at": fetched,
        },
    }
    case = request.param
    if case in {"credits", "none", "stale_credits"}:
        info["reset_credits"] = None
    if case in {"resets", "none", "expired_resets", "stale_resets"}:
        info["credit_balance"] = 0.0
    if case == "stale_credits":
        info["fetched_at"] = (now - timedelta(hours=1)).isoformat()
    if case == "expired_resets":
        info["reset_credits"]["expires_at"] = [(now - timedelta(days=1)).isoformat()] * 2
    if case == "stale_resets":
        info["reset_credits"]["fetched_at"] = (now - timedelta(hours=1)).isoformat()
    if case == "unreadable":
        info["reset_credits"] = "unreadable"
        info["credit_balance"] = None
    count = int(case == "rate_limited")
    monkeypatch.setattr(
        credit_lane, "read_recent_rate_limits", lambda *_a, **_k: {"count": count, "last_rate_limited_at": None}
    )
    stale = case == "stale_snapshot"
    if stale:
        info["freshness"] = "stale_last_good"
    return info, case in {"both", "credits", "resets"}, now


def test_shared_deficit_decision(reserve_case):
    info, covered, now = reserve_case
    receipt = credit_lane.pace_deficit_state("codex", info, now=now)
    assert receipt["raw_deficit"] is True
    assert receipt["uncovered"] is (not covered)
    assert bool(receipt["covered_by"]) is covered
    assert receipt["status"] == ("cool" if covered else "hot")


def test_routing_budget_covered_deficit(reserve_case, monkeypatch, tmp_path):
    info, covered, now = reserve_case
    budget_path = _configure_base(monkeypatch, tmp_path)
    native = {**info["codexbar"], **copy.deepcopy(info), "lane": "codex"}
    # The producer gets reserve fields on the native record, without a nested native record.
    native.pop("codexbar")
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda lane: native if lane == "codex" else {})
    monkeypatch.setattr(state_router, "get_cursor_lane_usage", lambda: {})
    monkeypatch.setattr(state_router, "summarize_fleet_burn", lambda *_a, **_k: {"windows": {}})
    data = state_router.compute_routing_budget(
        now,
        budget_config_path=budget_path,
        tasks_dir=tmp_path / "tasks",
        project_root=tmp_path,
        curriculum_root=tmp_path,
        batch_state_dir=tmp_path,
    )
    codex = data["agents"]["codex"]
    assert codex["status"] == ("cool" if covered else "hot")
    assert codex["codexbar"]["weekly_pace_delta_pct"] == 2.5
    assert codex["pace_deficit"]["uncovered"] is (not covered)
    if covered:
        assert any("deficit covered by" in w for w in data["recommendation"]["warnings"])


def test_capacity_pick_covered_deficit(reserve_case):
    info, covered, now = reserve_case
    rows = capacity_pick.build_lane_rows(
        {"agents": {"codex": info}},
        reset_reserve=unavailable_reserve(),
        now=now,
    )
    row = next(row for row in rows if row["lane"] == "codex")
    if info["freshness"] == "stale_last_good":
        # #9740 F2: a weekly-pace deficit read from a stale probe is UNKNOWN — stale/advisory,
        # not a confirmed current deficit and not verified capacity.
        assert (row["avoid"], row["status"], row["capacity"]["state"]) == (False, "unknown", "unknown_stale")
        assert credit_lane.STALE_ADVISORY_LABEL in row["notes"]
        assert "codex" not in capacity_pick.cooler_lanes(rows)
    else:
        assert row["avoid"] is (not covered)
        assert row["status"] == ("cool" if covered else "hot")
    assert "+2.5" in row["pace"]
    if covered:
        assert "deficit covered by" in row["notes"]


def test_delegate_budget_guard_covered_deficit(reserve_case, monkeypatch):
    info, covered, _ = reserve_case
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "agents": {"codex": info, "claude": {"status": "cool"}},
            "diagnostics": {"stale": False, "records_loaded": 1},
        },
    )
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_a, **_k: unavailable_reserve())
    result = delegate._resolve_agent_with_budget_guard(
        "codex",
        requested_model="gpt-6.1-sol",
        fallbacks={"codex": "claude"},
    )
    assert result == ("codex" if covered else "claude")
    assert ("codex" in delegate._budget_cooler_lanes({"codex": info}, exclude="claude")) is covered


def test_idle_settle_covered_deficit(reserve_case):
    info, covered, _ = reserve_case
    row = {**info, "lane": "codex", "quota_ok": True}
    snapshot = idle_settle.parse_snapshot({"lanes": [row]})
    # #9740 F2: a deficit read from a stale probe is unknown, neither permission nor refusal.
    expected = None if info["freshness"] == "stale_last_good" else covered
    assert snapshot.lanes[0].quota_ok is expected
    assert snapshot.lanes[0].is_healthy_available() is False
    assert snapshot.lanes[0].status == ("cool" if covered else "hot")
    lanes = idle_settle.lanes_from_capacity_rows([row])
    assert lanes[0].quota_ok is expected
    assert lanes[0].status == snapshot.lanes[0].status


@pytest.mark.parametrize("grok_status", [None, "healthy", "unhealthy"])
def test_reviewer_resolver_covered_deficit(reserve_case, grok_status):
    info, _covered, _ = reserve_case
    agents = {"codex": info, "cursor": {"status": "unhealthy"}}
    if grok_status is not None:
        agents["grok"] = {"status": grok_status}
    result = resolve_reviewer(
        ResolverInputs(
            author_model="claude-opus-5-5",
            review_profile="code",
            risk="critical",
            routing_snapshot={"agents": agents},
        )
    )
    sol = next(candidate for candidate in result.trace if candidate.name == "openai_frontier")
    # Reviews do not require pace coverage while allowance remains above reserve.
    assert sol.status == "selected"
    assert result.selected.concrete_model == "gpt-6.1-sol"


@pytest.mark.parametrize("native_only", [False, True])
def test_capacity_rows_retain_reserve_evidence_for_idle_settle(reserve_case, native_only):
    info, covered, now = reserve_case
    info = copy.deepcopy(info)
    if native_only:
        for key in ("freshness", "age_s", "fetched_at", "reset_credits", "credit_balance"):
            info["codexbar"][key] = info.pop(key)
    rows = capacity_pick.build_lane_rows(
        {"agents": {"codex": info}, "in_flight": {}},
        reset_reserve=unavailable_reserve(),
        now=now,
    )
    lanes = idle_settle.lanes_from_capacity_rows(rows)
    codex = next(lane for lane in lanes if lane.lane == "codex")
    assert codex.is_healthy_available() is covered


@pytest.mark.parametrize("used", [90.0, 95.0])
def test_reserves_do_not_change_near_cap(reserve_case, used):
    info, _, now = reserve_case
    info = copy.deepcopy(info)
    info.update(status="near_cap", remaining_pct=100 - used)
    info["codexbar"].update(weekly_used_pct=used, weekly_remaining_pct=100 - used)
    assert credit_lane.pace_deficit_state("codex", info, now=now)["status"] == "near_cap"
    assert state_router._status_from_weekly_used(used, info["codexbar"], lane="codex", info=info, now=now) == "near_cap"


def test_credit_relief_is_model_specific(reserve_case, monkeypatch):
    info, covered, now = reserve_case
    info = copy.deepcopy(info)
    info["reset_credits"] = None
    allowed = credit_lane.pace_deficit_state("codex", info, model="gpt-6.1-sol", now=now)
    forbidden = credit_lane.pace_deficit_state("codex", info, model="gpt-5-codex", now=now)
    assert forbidden["uncovered"] is True
    if covered and info["credit_balance"]:
        assert allowed["uncovered"] is False
    # A producer's cool label is not sufficient to grant model-specific relief.
    info["status"] = "cool"
    info["pace_deficit"] = {"raw_deficit": True, "covered_by": ["credits"]}
    policy = replace(credit_lane.load_policy(), allowed_models={"codex": ("gpt-6-luna",)})
    monkeypatch.setattr(credit_lane, "load_policy", lambda: policy)
    result = evaluate_candidate(
        OPENAI_FRONTIER,
        ResolverInputs(
            author_model="claude-opus-5-5",
            routing_snapshot={"agents": {"codex": info}},
        ),
    )
    assert result.status == "eligible" and result.credit is None


@pytest.mark.parametrize("failure", ["reader_raises", "unreadable_records", "policy", "headroom", "future_fetch"])
def test_reserve_evidence_fails_closed(reserve_case, monkeypatch, failure):
    info, _, now = reserve_case
    info = copy.deepcopy(info)
    if failure == "reader_raises":

        def broken(*_a, **_k):
            raise OSError("unreadable")

        monkeypatch.setattr(credit_lane, "read_recent_rate_limits", broken)
    elif failure == "unreadable_records":
        monkeypatch.setattr(
            credit_lane,
            "read_recent_rate_limits",
            lambda *_a, **_k: {
                "count": 0,
                "last_rate_limited_at": None,
                "unreadable": {"total": 1, "files": 1},
            },
        )
    elif failure == "policy":

        def broken_policy():
            raise ValueError("unreadable")

        monkeypatch.setattr(credit_lane, "load_policy", broken_policy)
    elif failure == "headroom":
        info["runtime"]["headroom_blocked"] = True
    else:
        info["fetched_at"] = (now + timedelta(hours=1)).isoformat()
        if isinstance(info["reset_credits"], dict):
            info["reset_credits"]["fetched_at"] = info["fetched_at"]
    assert credit_lane.pace_deficit_state("codex", info, now=now)["uncovered"] is True


def test_coverage_claim_is_rechecked(reserve_case, monkeypatch):
    info, _, now = reserve_case
    info = copy.deepcopy(info)
    info["pace_deficit"] = {"uncovered": False, "covered_by": ["credits", "free full reset"]}
    info["credit_balance"] = 0.0
    info["reset_credits"] = None
    assert credit_lane.pace_deficit_state("codex", info, now=now)["uncovered"] is True


@pytest.mark.parametrize("lane", ["", " "])
def test_missing_lane_never_covers_deficit(reserve_case, lane):
    info, _, now = reserve_case
    decision = credit_lane.pace_deficit_state(lane, info, now=now)
    assert decision["uncovered"] is True
    assert decision["covered_by"] == []
    stale = info["freshness"] == "stale_last_good"
    facts = credit_lane.routing_facts(lane, info, model=None, now=now)
    assert facts.capacity == (credit_lane.CAPACITY_UNKNOWN_STALE if stale else credit_lane.CAPACITY_AVOID)
    assert capacity_pick.is_avoid_lane(info, lane=lane) is not stale
    assert state_router._status_from_weekly_used(13.0, info["codexbar"], info=info, now=now) == "hot"
    needs_action, _ = delegate._budget_needs_hard_capacity_action(
        status="hot", will_last=False, is_stale=False, pace=info["codexbar"], info=info
    )
    assert needs_action


@pytest.mark.parametrize("source", ["ledger_burn", "cursor_auto", None])
def test_cover_never_relaxes_hot_from_other_sources(reserve_case, source):
    info, _, now = reserve_case
    info = copy.deepcopy(info)
    info["status_source"] = source
    decision = credit_lane.pace_deficit_state("codex", info, now=now)
    assert decision["status"] == "hot"
    assert decision["uncovered"] is True
    assert capacity_pick.is_avoid_lane(info, lane="codex")
    result = evaluate_candidate(
        OPENAI_FRONTIER,
        ResolverInputs(author_model="claude-opus-5-5", routing_snapshot={"agents": {"codex": info}}),
    )
    assert result.status == "eligible" and result.credit is None


@pytest.mark.parametrize(
    "expiry", ["before", "equal", "after", "no_expiry", "missing_projection", "invalid_window", "overflow_projection"]
)
def test_reset_must_outlast_projected_runout(monkeypatch, expiry):
    now = datetime(2026, 10, 3, 12, tzinfo=UTC)
    # Halfway through a seven-day window, 70% used runs out in 1.5 days.
    runout = now + timedelta(days=1.5)
    expirations = {
        "before": (runout - timedelta(seconds=1)).isoformat(),
        "equal": runout.isoformat(),
        "after": (runout + timedelta(seconds=1)).isoformat(),
        "no_expiry": None,
        "missing_projection": (runout + timedelta(days=1)).isoformat(),
        "invalid_window": (runout + timedelta(days=1)).isoformat(),
        "overflow_projection": None,
    }
    info = {
        "status": "hot",
        "status_source": "weekly_pace",
        "remaining_pct": 30.0,
        "freshness": "fresh",
        "age_s": 0,
        "credit_balance": 0,
        "reset_credits": {
            "available_count": 1,
            "expires_at": [expirations[expiry]],
            "fetched_at": now.isoformat(),
        },
        "codexbar": {
            "weekly_used_pct": 70.0,
            "weekly_expected_pct": 50.0,
            "weekly_pace_delta_pct": 20.0,
            "will_last_to_reset": False,
            "weekly_resets_at": (now + timedelta(days=3.5)).isoformat() if expiry != "missing_projection" else None,
        },
    }
    monkeypatch.setattr(
        credit_lane, "read_recent_rate_limits", lambda *_a, **_k: {"count": 0, "last_rate_limited_at": None}
    )
    if expiry == "invalid_window":
        info["codexbar"]["window_minutes"] = float("inf")
    elif expiry == "overflow_projection":
        info["codexbar"]["weekly_used_pct"] = 1e-300
    covered = expiry in {"after", "no_expiry"}
    decision = credit_lane.pace_deficit_state("codex", info, now=now)
    assert decision["uncovered"] is (not covered)
    assert decision["status"] == ("cool" if covered else "hot")


@pytest.mark.parametrize("source", ["ledger_burn", "cursor_auto"])
@pytest.mark.parametrize("used", [75.0, 80.0, 89.0])
def test_routing_budget_preserves_hot_sources(monkeypatch, tmp_path, source, used):
    now = datetime(2026, 10, 3, 12, tzinfo=UTC)
    _configure_base(monkeypatch, tmp_path)
    monkeypatch.setattr(state_router, "summarize_fleet_burn", lambda *_a, **_k: {"windows": {}})
    native = {
        "status": "hot",
        "weekly_used_pct": used,
        "weekly_expected_pct": 50.0,
        "weekly_pace_delta_pct": used - 50.0,
        "will_last_to_reset": False,
        "weekly_resets_at": (now + timedelta(days=3.5)).isoformat(),
        "weekly_remaining_pct": 100 - used,
        "freshness": "fresh",
        "age_s": 0,
        "fetched_at": now.isoformat(),
        "credit_balance": 62500.0,
        "reset_credits": {
            "available_count": 1,
            "expires_at": [None],
            "fetched_at": now.isoformat(),
        },
    }
    lane = "cursor" if source == "cursor_auto" else "codex"
    monkeypatch.setattr(state_router, "get_cursor_lane_usage", lambda: native if lane == "cursor" else {})
    if source == "ledger_burn":
        monkeypatch.setattr(state_router, "load_cost_records", lambda **_k: [_record(lane, used * 10, now)])
    else:
        policy = credit_lane.load_policy()
        # Exercise the adapter's hot source even if a future policy admits
        # Cursor credits. Current shipping policy remains untouched.
        monkeypatch.setattr(
            credit_lane, "load_policy", lambda: replace(policy, allowed_models={"cursor": ("gpt-6.1-sol",)})
        )
    data = state_router.compute_routing_budget(
        now,
        budget_config_path=tmp_path / "agent_budgets.yaml",
        tasks_dir=tmp_path / "tasks",
        project_root=tmp_path,
        curriculum_root=tmp_path,
        batch_state_dir=tmp_path,
    )
    assert data["agents"][lane]["status_source"] == source
    assert data["agents"][lane]["status"] == "hot"
    assert data["agents"][lane]["pace_deficit"]["status"] == "hot"
    if source == "cursor_auto":
        row = next(row for row in capacity_pick.build_lane_rows(data, now=now) if row["lane"] == lane)
        assert row["status"] == "hot"
        assert row["avoid"] is True


@pytest.mark.parametrize("default_model", ["gpt-6.1-sol", "gpt-5-codex", None])
def test_delegate_credit_relief_checks_lane_default(reserve_case, monkeypatch, default_model):
    info, _, _ = reserve_case
    info = copy.deepcopy(info)
    info["reset_credits"] = None
    covered = credit_lane.pace_deficit_state("codex", info, model="gpt-6.1-sol")["uncovered"] is False
    previous_default = delegate._lane_default_model
    monkeypatch.setattr(
        delegate, "_lane_default_model", lambda lane: default_model if lane == "codex" else previous_default(lane)
    )
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "agents": {"codex": info, "claude": {"status": "cool"}},
            "diagnostics": {"stale": False, "records_loaded": 1},
        },
    )
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_a, **_k: unavailable_reserve())
    result = delegate._resolve_agent_with_budget_guard("codex", fallbacks={"codex": "claude"})
    assert result == ("codex" if covered and default_model == "gpt-6.1-sol" else "claude")
