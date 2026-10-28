"""#10630 S2: the Claude account is part of the route key (#10619, #10733).

Three properties, each against the real code paths:

- The snapshot read API has no default account: a call without a
  ``ClaudeAccount`` fails at type-check time (mypy) and at run time.
- Every final claude route resolves and binds its account before admission;
  an unresolved account removes the claude seats and no other (#10733).
- For one routing snapshot and one account, the five decision consumers reach
  the same capacity verdict: the owner (``claude_account_lane.capacity_verdict``),
  the dispatch budget guard, the plan-headroom stop (``model_pause``), reviewer
  admission (``target_admission``) and ``closeout_cli resolve-reviewer``.
"""

from __future__ import annotations

import pytest

from scripts.agent_runtime import target_admission
from scripts.agent_runtime.mechanical_admission import MechanicalAdmissionRefused
from scripts.fleet import claude_account_lane
from scripts.fleet.claude_account_lane import HEALTHY, HOT, UNKNOWN, ClaudeAccount
from scripts.review.reviewer_resolver import REVIEW_CANDIDATES, ResolverInputs, evaluate_candidate, resolve_reviewer
from tests.claude_route_accounts import HOST_ACCOUNT, account, unresolved
from tests.helpers.claude_account_fixtures import UNVERIFIED_ROW as _UNVERIFIED_ROW
from tests.helpers.claude_account_fixtures import account_row as _account_row
from tests.helpers.claude_account_fixtures import accounts_budget as _accounts_budget
from tests.helpers.claude_account_fixtures import bind_claude_account_b as _bind_claude_account_b
from tests.helpers.claude_account_fixtures import default_account_file as _default_account_file
from tests.helpers.claude_account_fixtures import default_claude_lane as _default_claude_lane
from tests.helpers.claude_account_fixtures import fresh_lane as _fresh_lane

# --- row 1: the snapshot read API requires a named account ----------------------------------


def _budget() -> dict:
    return _accounts_budget(_default_claude_lane("near_cap"), {"b": _account_row(89.0)})


def test_the_claude_lane_is_only_read_for_a_named_account():
    budget = _budget()
    assert claude_account_lane.lane_record(budget, "claude", account=HOST_ACCOUNT)["remaining_pct"] == 0.5
    assert claude_account_lane.lane_record(budget, "claude", account=account("b"))["remaining_pct"] == 89.0
    assert claude_account_lane.other_lane_record(budget, "codex") is budget["agents"]["codex"]
    for lane in ("claude", " Claude "):
        with pytest.raises(claude_account_lane.AccountRequired, match="named account"):
            claude_account_lane.other_lane_record(budget, lane)
    with pytest.raises(TypeError):
        claude_account_lane.select_account(budget, account("b"))  # keyword only


def test_an_unresolved_account_reads_route_facts_with_an_unknown_meter():
    budget = _budget()
    view, evidence = claude_account_lane.select_account(budget, account=unresolved("claude_account_binding_missing"))
    claude = view["agents"]["claude"]
    assert claude["status"] == "unknown" and claude["freshness"] == "unavailable"
    assert claude["health"] == budget["agents"]["claude"]["health"]  # a route fact no account owns
    assert "remaining_pct" not in claude and "codexbar" not in claude
    assert evidence == {"label": None, "meter": None, "state": "unresolved", "reason": "claude_account_binding_missing"}
    assert claude_account_lane.account_weekly_used_pct(budget, account=unresolved("claude_account_unknown")) is None


# --- row 1 at the public resolver: ResolverInputs names its account, and the resolver reads it --


def _reviewer_inputs(raw: dict, route_account: object) -> ResolverInputs:
    return ResolverInputs(
        author_model="gpt-6.1-sol",
        risk="critical",
        owned_paths=("ordinary.py",),
        routing_snapshot=raw,
        claude_account=route_account,
    )


@pytest.mark.parametrize(
    ("default_lane", "b_left", "verdict"),
    [("healthy", 0.5, HOT), ("near_cap", 89.0, HEALTHY)],
    ids=["b_hot_while_the_lane_row_is_healthy", "b_healthy_while_the_lane_row_is_near_cap"],
)
def test_the_resolver_judges_claude_on_the_named_accounts_meter(default_lane, b_left, verdict):
    """Review of e98e30c5 finding 1: the raw snapshot plus account b must be judged on b's row, both ways."""
    raw = _accounts_budget(_default_claude_lane(default_lane), {"b": _account_row(b_left)})
    assert claude_account_lane.capacity_verdict(raw, account=account("b")) == verdict

    resolution = resolve_reviewer(_reviewer_inputs(raw, account("b")))
    claude = next(entry for entry in resolution.trace if entry.route == "claude")

    assert (resolution.selected.route == "claude") is (verdict == HEALTHY)
    assert claude.status == ("selected" if verdict == HEALTHY else "excluded")
    direct = evaluate_candidate(REVIEW_CANDIDATES[claude.name], _reviewer_inputs(raw, account("b")))
    assert direct.status == ("eligible" if verdict == HEALTHY else "excluded")
    # The caller's select_account view is the same input: the view is a fixed point.
    view, _ = claude_account_lane.select_account(raw, account=account("b"))
    assert resolve_reviewer(_reviewer_inputs(view, account("b"))).selected.name == resolution.selected.name


def test_an_unresolved_default_account_file_removes_every_claude_seat_from_the_resolver(tmp_path, monkeypatch):
    raw = _accounts_budget(_default_claude_lane("healthy"), {"b": _account_row(89.0)})
    _default_account_file(tmp_path, monkeypatch, b"c\n")
    route_account = claude_account_lane.resolve_route_account(None, strict=False)
    assert route_account == unresolved("claude_account_default_file_invalid")

    resolution = resolve_reviewer(_reviewer_inputs(raw, route_account))

    assert resolution.selected is not None and resolution.selected.route != "claude"
    claude = [entry for entry in resolution.trace if entry.route == "claude"]
    assert claude and all(entry.status == "excluded" for entry in claude)
    assert {entry.reason for entry in claude} == {"claude account unresolved: claude_account_default_file_invalid"}


@pytest.mark.parametrize("route_account", [HOST_ACCOUNT, account("b"), unresolved("claude_account_unknown")])
def test_the_account_view_is_a_fixed_point(route_account):
    """The resolver reads its snapshot through select_account; a caller's view must read the same."""
    for b_row in (_account_row(0.5), _account_row(89.0, status="stale"), _UNVERIFIED_ROW):
        raw = _accounts_budget(_default_claude_lane("near_cap"), {"b": b_row})
        raw["agents"]["claude"]["runtime"] = {"ok": 1, "headroom_blocked": True, "rate_limited": 2}
        view, _ = claude_account_lane.select_account(raw, account=route_account)
        again, _ = claude_account_lane.select_account(view, account=route_account)
        # The same reading; only the clock-derived pace fields of a recomputed account view may move.
        decided = ("status", "remaining_pct", "burn_pct_7d", "freshness", "health", "runtime", "scheduler")
        claude, claude_again = view["agents"]["claude"], again["agents"]["claude"]
        assert {key: claude_again.get(key) for key in decided} == {key: claude.get(key) for key in decided}
        assert {**again, "agents": {}} == {**view, "agents": {}}
        assert claude_account_lane.capacity_verdict(again, account=route_account) == (
            claude_account_lane.capacity_verdict(view, account=route_account)
        )


# --- row 5: every final claude route resolves and binds its account before admission ----------


def test_admission_refuses_any_final_claude_route_on_an_unresolved_account():
    """The backstop: whatever step chose claude, admission refuses it on an unresolved account."""

    def route(request):
        assert request.claude_account == unresolved("claude_account_default_file_invalid")
        return "claude", "claude-opus-5-5", "route:fixture"

    with pytest.raises(MechanicalAdmissionRefused, match="CLAUDE_ACCOUNT_REFUSED: claude_account_default_file_invalid"):
        target_admission.resolve_and_admit(
            ("codex",),
            mode="read-only",
            route=route,
            new_dispatch=True,
            claude_account=unresolved("claude_account_default_file_invalid"),
        )
    (target,) = target_admission.resolve_and_admit(
        ("codex",),
        mode="read-only",
        route=lambda request: ("codex", "gpt-6.1-sol", "route:fixture"),
        new_dispatch=True,
        claude_account=unresolved("claude_account_default_file_invalid"),
    )
    assert target.recipient == "codex"


# --- row 3: the five decision consumers agree on one snapshot and one account -----------------


def _agreement_snapshot(a_state: str, b_row: dict | None) -> dict:
    if a_state == "unknown":
        lane = {"status": "unknown", "freshness": "unavailable", "health": {"healthy": True}}
    else:
        lane = _default_claude_lane(a_state)
        lane["codexbar"]["stale"] = False  # the producer publishes the probe's stale flag
    budget = _accounts_budget(lane, {"b": b_row})
    for seat in ("grok", "cursor"):
        budget["agents"][seat] = _fresh_lane(
            status="cool", remaining_pct=80.0, codexbar={"weekly_remaining_pct": 80.0, "will_last_to_reset": True}
        )
    budget["diagnostics"] = {"records_loaded": 5, "stale": False, "codexbar_data_available": True}
    return budget


# case: (lane row state of account a, account b's row, default-account file, owner verdict)


@pytest.mark.parametrize(
    ("route_fact", "verdict"),
    [
        ({}, UNKNOWN),
        ({"eligible": False}, HOT),
        ({"health": {"healthy": False, "consecutive_failures": 3}}, HOT),
    ],
)
def test_a_stale_meter_is_advisory_but_a_route_fact_still_binds(route_fact, verdict):
    """The owner's rule: only a fresh reading is hot or healthy; a route fact no meter owns stays hot."""
    for b_left in (0.5, 89.0):
        budget = _agreement_snapshot("healthy", _account_row(b_left, status="stale"))
        budget["agents"]["claude"].update(route_fact)
        assert claude_account_lane.capacity_verdict(budget, account=account("b")) == verdict


def _route_key_for(tmp_path, monkeypatch, default_file: bytes | None) -> ClaudeAccount:
    """Set the operator's default-account file, then resolve the account the way every consumer does."""
    if default_file == b"unbound-b":
        _bind_claude_account_b(tmp_path, monkeypatch, bound=False)
        default_file = b"b\n"
    elif default_file == b"b\n":
        _bind_claude_account_b(tmp_path, monkeypatch)
    if default_file is None:
        monkeypatch.setenv("LU_CLAUDE_DEFAULT_ACCOUNT_FILE", "")
    else:
        _default_account_file(tmp_path, monkeypatch, default_file)
    return claude_account_lane.resolve_route_account(None, strict=False)
