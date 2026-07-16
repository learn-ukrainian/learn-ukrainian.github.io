"""Scope baseline: freeze the closeout review's boundaries before the first
review pass runs, then detect when review-triggered changes (or a proposed
fix) have grown past them.

The baseline is frozen once, from a single :class:`ReviewTarget`. Every
later check compares against that frozen snapshot — never against whatever
the tree looks like *now* — so scope creep during the review/fix loop is
visible instead of silently absorbed.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from typing import Literal

from scripts.review.target_resolution import ReviewTarget

Disposition = Literal["in_scope_blocker", "follow_up", "stop_and_escalate"]

# Only these reasons justify expanding scope past a tripped breaker.
CRITICAL_OVERRIDE_REASONS = frozenset(
    {
        "active_data_loss",
        "crash",
        "broken_install_or_upgrade",
        "release_blocker",
        "concrete_security_exposure",
    }
)


@dataclass(frozen=True)
class ScopeBaseline:
    """The frozen scope statement, displayed before the first review pass."""

    issue_ref: str
    intended_behavior: str
    non_goals: str
    owner_boundary: str
    target: ReviewTarget
    review_profile: str
    risk: str
    frozen_files: frozenset[str]
    frozen_non_test_loc: int

    @classmethod
    def freeze(
        cls,
        *,
        issue_ref: str,
        intended_behavior: str,
        non_goals: str,
        owner_boundary: str,
        target: ReviewTarget,
        review_profile: str,
        risk: str,
    ) -> ScopeBaseline:
        return cls(
            issue_ref=issue_ref,
            intended_behavior=intended_behavior,
            non_goals=non_goals,
            owner_boundary=owner_boundary,
            target=target,
            review_profile=review_profile,
            risk=risk,
            frozen_files=frozenset(target.changed_paths),
            frozen_non_test_loc=target.non_test_loc,
        )

    def render(self) -> str:
        """Human-readable baseline block. Displayed once, before review starts."""
        lines = [
            f"Issue: {self.issue_ref}",
            f"Intended behavior: {self.intended_behavior}",
            f"Non-goals: {self.non_goals}",
            f"Owner boundary: {self.owner_boundary}",
            f"Mode: {self.target.mode}",
            f"Base SHA: {self.target.base_sha or '(none)'}",
            f"Head SHA: {self.target.head_sha or '(none)'}",
            f"Changed paths ({len(self.frozen_files)}): {', '.join(sorted(self.frozen_files)) or '(none)'}",
            f"Non-test LOC: {self.frozen_non_test_loc}",
            f"Review profile: {self.review_profile}",
            f"Risk: {self.risk}",
        ]
        if self.target.mode == "local" and self.target.clean_tree:
            lines.append("NOTE: clean local tree only — NOT evidence that a commit or PR was reviewed.")
        return "\n".join(lines)


@dataclass(frozen=True)
class BreakerResult:
    triggered: bool
    reason: str | None = None


def check_expansion_breaker(
    baseline: ScopeBaseline,
    current_files: frozenset[str],
    current_non_test_loc: int,
) -> BreakerResult:
    """Trip when review-triggered changes exceed 2x the frozen files or LOC.

    A frozen baseline of zero files/LOC (an empty local diff, or a doc-only
    change) can't be doubled by arithmetic — any expansion at all crosses it.
    """
    frozen_file_count = len(baseline.frozen_files)
    total_files = len(baseline.frozen_files | current_files)
    file_limit_exceeded = (
        total_files > frozen_file_count * 2 if frozen_file_count else total_files > 0
    )
    if file_limit_exceeded:
        return BreakerResult(
            True,
            f"review-triggered files ({total_files}) exceed 2x frozen baseline ({frozen_file_count})",
        )

    loc_limit_exceeded = (
        current_non_test_loc > baseline.frozen_non_test_loc * 2
        if baseline.frozen_non_test_loc
        else current_non_test_loc > 0
    )
    if loc_limit_exceeded:
        return BreakerResult(
            True,
            f"review-triggered non-test LOC ({current_non_test_loc}) exceeds "
            f"2x frozen baseline ({baseline.frozen_non_test_loc})",
        )
    return BreakerResult(False)


def check_cycle_convergence_breaker(cycle_outstanding_counts: list[int]) -> BreakerResult:
    """Trip when two review-triggered patch cycles in a row fail to converge.

    ``cycle_outstanding_counts`` is the outstanding-finding count after each
    review pass, oldest first (e.g. ``[5, 4, 4]`` — pass 2 made progress,
    pass 3 stalled). Two consecutive passes that don't shrink the count trip
    the breaker.
    """
    non_converging_streak = 0
    for prev, curr in pairwise(cycle_outstanding_counts):
        if curr >= prev:
            non_converging_streak += 1
        else:
            non_converging_streak = 0
        if non_converging_streak >= 2:
            return BreakerResult(
                True,
                f"two review-triggered patch cycles did not converge: {cycle_outstanding_counts}",
            )
    return BreakerResult(False)


def check_contract_boundary_breaker(
    *,
    changes_public_contract: bool,
    crosses_owner_boundary: bool,
) -> BreakerResult:
    """Trip when a fix changes the public/task contract or an owner boundary."""
    if changes_public_contract:
        return BreakerResult(True, "fix changes the public/task contract")
    if crosses_owner_boundary:
        return BreakerResult(True, "fix crosses the owner boundary")
    return BreakerResult(False)


def check_design_decision_breaker(*, requires_canonical_decision: bool) -> BreakerResult:
    """Trip when a canonical contract/design decision is required to proceed."""
    if requires_canonical_decision:
        return BreakerResult(True, "a canonical contract/design decision is required")
    return BreakerResult(False)


def critical_override_applies(reason: str | None) -> bool:
    """Only active data loss, crash, broken install/upgrade, release blocker,
    or concrete security exposure justify expanding scope past a tripped
    breaker. Anything else — including "it would be nice to fix too" — does
    not."""
    return reason in CRITICAL_OVERRIDE_REASONS


def classify_finding(
    *,
    is_blocking: bool,
    in_frozen_scope: bool,
    requires_scope_expansion: bool,
    critical_override_reason: str | None = None,
) -> Disposition:
    """Classify one verified finding into its disposition.

    A finding whose fix would expand scope is escalated unless a critical
    override reason applies — in which case it's treated as in-scope (the
    override exists precisely so real emergencies aren't stuck in follow-up).
    """
    if requires_scope_expansion and not critical_override_applies(critical_override_reason):
        return "stop_and_escalate"
    if is_blocking and in_frozen_scope:
        return "in_scope_blocker"
    return "follow_up"
