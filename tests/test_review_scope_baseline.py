"""Tests for scripts/review/scope_baseline.py — frozen scope + breakers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.review.scope_baseline import (
    ScopeBaseline,
    check_contract_boundary_breaker,
    check_cycle_convergence_breaker,
    check_design_decision_breaker,
    check_expansion_breaker,
    classify_finding,
    critical_override_applies,
)
from scripts.review.target_resolution import ReviewTarget


def _target(*, changed_paths=("a.py", "b.py"), non_test_loc=40, mode="branch", clean_tree=False):
    return ReviewTarget(
        mode=mode,
        base_sha="base123",
        head_sha="head456",
        changed_paths=changed_paths,
        non_test_loc=non_test_loc,
        clean_tree=clean_tree,
        description="test target",
    )


def _baseline(**kwargs):
    target = _target(**{k: v for k, v in kwargs.items() if k in ("changed_paths", "non_test_loc", "mode", "clean_tree")})
    return ScopeBaseline.freeze(
        issue_ref="#5283",
        intended_behavior="do the thing",
        non_goals="not that thing",
        owner_boundary="scripts/review/**",
        target=target,
        review_profile="infra",
        risk="medium",
    )


# --- freeze + render ---------------------------------------------------------

def test_freeze_captures_target_snapshot():
    baseline = _baseline()
    assert baseline.frozen_files == {"a.py", "b.py"}
    assert baseline.frozen_non_test_loc == 40


def test_render_includes_all_required_fields():
    baseline = _baseline()
    rendered = baseline.render()
    for expected in ("#5283", "do the thing", "not that thing", "scripts/review/**", "branch", "medium", "infra"):
        assert expected in rendered


def test_render_flags_clean_local_tree_as_not_commit_proof():
    baseline = _baseline(mode="local", changed_paths=(), non_test_loc=0, clean_tree=True)
    rendered = baseline.render()
    assert "NOT evidence" in rendered


def test_render_does_not_flag_committed_modes():
    baseline = _baseline(mode="pr")
    assert "NOT evidence" not in baseline.render()


# --- expansion breaker: positive + negative fixtures --------------------------

def test_expansion_breaker_does_not_trigger_within_2x():
    baseline = _baseline(changed_paths=("a.py", "b.py"), non_test_loc=40)
    result = check_expansion_breaker(baseline, frozenset({"a.py", "b.py", "c.py"}), 70)
    assert result.triggered is False


def test_expansion_breaker_triggers_on_file_count_over_2x():
    baseline = _baseline(changed_paths=("a.py", "b.py"), non_test_loc=40)
    result = check_expansion_breaker(baseline, frozenset({"a.py", "b.py", "c.py", "d.py", "e.py"}), 40)
    assert result.triggered is True
    assert "files" in result.reason


def test_expansion_breaker_triggers_on_loc_over_2x():
    baseline = _baseline(changed_paths=("a.py", "b.py"), non_test_loc=40)
    result = check_expansion_breaker(baseline, frozenset({"a.py", "b.py"}), 90)
    assert result.triggered is True
    assert "LOC" in result.reason


def test_expansion_breaker_zero_baseline_any_growth_trips():
    baseline = _baseline(changed_paths=(), non_test_loc=0)
    result = check_expansion_breaker(baseline, frozenset({"new.py"}), 5)
    assert result.triggered is True


def test_expansion_breaker_zero_baseline_no_growth_does_not_trip():
    baseline = _baseline(changed_paths=(), non_test_loc=0)
    result = check_expansion_breaker(baseline, frozenset(), 0)
    assert result.triggered is False


# --- cycle-convergence breaker: positive + negative fixtures ------------------

def test_cycle_breaker_does_not_trigger_when_converging():
    result = check_cycle_convergence_breaker([5, 3, 1, 0])
    assert result.triggered is False


def test_cycle_breaker_triggers_on_two_consecutive_stalls():
    result = check_cycle_convergence_breaker([5, 5, 5])
    assert result.triggered is True
    assert "did not converge" in result.reason


def test_cycle_breaker_triggers_when_findings_grow():
    result = check_cycle_convergence_breaker([3, 4, 6])
    assert result.triggered is True


def test_cycle_breaker_single_stall_then_recovery_does_not_trigger():
    result = check_cycle_convergence_breaker([5, 5, 2])
    assert result.triggered is False


def test_cycle_breaker_too_few_cycles_does_not_trigger():
    result = check_cycle_convergence_breaker([5])
    assert result.triggered is False
    result2 = check_cycle_convergence_breaker([])
    assert result2.triggered is False


# --- contract/owner boundary + design-decision breakers -----------------------

def test_contract_boundary_breaker_negative():
    result = check_contract_boundary_breaker(changes_public_contract=False, crosses_owner_boundary=False)
    assert result.triggered is False


def test_contract_boundary_breaker_public_contract():
    result = check_contract_boundary_breaker(changes_public_contract=True, crosses_owner_boundary=False)
    assert result.triggered is True
    assert "public/task contract" in result.reason


def test_contract_boundary_breaker_owner_boundary():
    result = check_contract_boundary_breaker(changes_public_contract=False, crosses_owner_boundary=True)
    assert result.triggered is True
    assert "owner boundary" in result.reason


def test_design_decision_breaker():
    assert check_design_decision_breaker(requires_canonical_decision=False).triggered is False
    result = check_design_decision_breaker(requires_canonical_decision=True)
    assert result.triggered is True
    assert "design decision" in result.reason


# --- critical override -------------------------------------------------------

def test_critical_override_accepts_only_allowlisted_reasons():
    assert critical_override_applies("active_data_loss") is True
    assert critical_override_applies("crash") is True
    assert critical_override_applies("broken_install_or_upgrade") is True
    assert critical_override_applies("release_blocker") is True
    assert critical_override_applies("concrete_security_exposure") is True


def test_critical_override_rejects_everything_else():
    assert critical_override_applies(None) is False
    assert critical_override_applies("it_would_be_nice_too") is False
    assert critical_override_applies("user_asked_for_more") is False


# --- finding classification ---------------------------------------------------

def test_classify_finding_in_scope_blocker():
    disposition = classify_finding(is_blocking=True, in_frozen_scope=True, requires_scope_expansion=False)
    assert disposition == "in_scope_blocker"


def test_classify_finding_follow_up_when_not_blocking():
    disposition = classify_finding(is_blocking=False, in_frozen_scope=True, requires_scope_expansion=False)
    assert disposition == "follow_up"


def test_classify_finding_follow_up_when_out_of_scope():
    disposition = classify_finding(is_blocking=True, in_frozen_scope=False, requires_scope_expansion=False)
    assert disposition == "follow_up"


def test_classify_finding_stop_and_escalate_on_scope_expansion():
    disposition = classify_finding(is_blocking=True, in_frozen_scope=True, requires_scope_expansion=True)
    assert disposition == "stop_and_escalate"


def test_classify_finding_critical_override_keeps_it_in_scope():
    disposition = classify_finding(
        is_blocking=True,
        in_frozen_scope=True,
        requires_scope_expansion=True,
        critical_override_reason="active_data_loss",
    )
    assert disposition == "in_scope_blocker"


def test_classify_finding_non_critical_reason_still_escalates():
    disposition = classify_finding(
        is_blocking=True,
        in_frozen_scope=True,
        requires_scope_expansion=True,
        critical_override_reason="it_would_be_nice_too",
    )
    assert disposition == "stop_and_escalate"
