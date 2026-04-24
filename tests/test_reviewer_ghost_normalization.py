"""Tests for reviewer ghost-finding normalization (GH #1529 P3).

Covers the convergence_loop helpers that tag reviewer-hallucinated findings —
entries whose <fixes> anchor text does not exist in current module content.

Motivating case: a1/sounds-letters-and-hello 2026-04-24 rebuild. The Codex
factual reviewer emitted a "мама reversed" finding whose ``find`` anchor
``**мама** → [• – • –] — two [а] sounds`` did not occur in the module
(the correct form ``[– • – •]`` appears once). The ghost finding dragged
Factual to 4.5 and poisoned the convergence terminal. These tests pin the
tagging contract that surfaces such ghosts into their own bundle.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.convergence_loop import (
    REVIEWER_GHOST_PATCHABILITY_STATUS,
    ReviewObservation,
    collect_reviewer_ghost_findings,
    prioritize_findings,
    tag_reviewer_ghosts,
)


def _finding(
    *,
    dimension: str,
    severity: str,
    location: str,
    issue: str,
    fix: str,
) -> dict:
    return {
        "dimension": dimension,
        "severity": severity,
        "location": location,
        "issue": issue,
        "fix": fix,
    }


def _observation(
    *,
    findings: tuple[dict, ...],
    parsed_fixes: tuple[dict, ...] | None,
    module_content: str | None,
) -> ReviewObservation:
    return ReviewObservation(
        passed=False,
        score=4.5,
        review_text="(synthetic)",
        findings=findings,
        dim_floor_dimensions=(),
        content_hash="hash-ghost-test",
        patch_available=bool(parsed_fixes),
        parsed_fixes=parsed_fixes,
        module_content=module_content,
    )


# ---------- 1. mixed plan-level + ghost anchor case ----------


def test_ghost_tagging_separates_ghost_from_hardstop_finding() -> None:
    """Observation with one plan-level finding (hardstop) and one non-plan
    finding whose fix anchor is missing → only the non-plan finding is a
    ghost; the plan-level finding keeps its ``plan_level_hardstop`` route
    and is NOT copied into the ghost tuple. Original ``findings`` list is
    left unchanged (reviewer emitted both; audit keeps them visible).
    """
    content = "Module prose that contains **мама** → [– • – •] — two sounds."
    # One plan-level finding (vocab_density) + one non-plan (notation_error).
    # The <fixes> block has one valid anchor + one hallucinated anchor. Under
    # current batch-level predicate: non-plan finding → anchor_missing (ghost);
    # plan-level finding → plan_level_hardstop (not ghost).
    findings = (
        _finding(
            dimension="Plan Adherence",
            severity="critical",
            location="## whole module",
            issue=(
                "Section opens with formal register but the plan's register contract "
                "states informal — this is a contradiction with the contract."
            ),
            fix="Resolve the contradiction with the contract by picking one register.",
        ),
        _finding(
            dimension="Factual Accuracy",
            severity="major",
            location="мама section",
            issue="The reviewer claims **мама** → [• – • –] — two [а] sounds.",
            fix="Describe мама as two [а] sounds reversed.",
        ),
    )
    parsed_fixes = (
        {"find": "[– • – •]", "replace": "[– • – •]"},
        {
            "find": "**мама** → [• – • –] — two [а] sounds",
            "replace": "**мама** → [– • – •] — two [а] sounds",
        },
    )
    observation = _observation(
        findings=findings, parsed_fixes=parsed_fixes, module_content=content
    )

    prioritized = prioritize_findings(observation, growth_log_path=None)
    statuses = {item["dimension"]: item["patchability"] for item in prioritized}
    # Non-plan → anchor_missing (ghost). Plan-level → plan_level_hardstop.
    assert statuses["factual_accuracy"] == REVIEWER_GHOST_PATCHABILITY_STATUS
    assert statuses["plan_adherence"] == "plan_level_hardstop"

    ghosts = collect_reviewer_ghost_findings(observation)
    assert len(ghosts) == 1
    ghost = ghosts[0]
    assert ghost["dimension"] == "factual_accuracy"
    assert ghost["anchor_validation"] == REVIEWER_GHOST_PATCHABILITY_STATUS
    # reviewer_find_anchor matches one of the invalid fixes' find text.
    assert "мама" in ghost["reviewer_find_anchor"]
    assert "two [а] sounds" in ghost["reviewer_find_anchor"]
    # raw_fix is the full invalid fix dict.
    assert ghost["raw_fix"]["find"] == (
        "**мама** → [• – • –] — two [а] sounds"
    )
    assert "replace" in ghost["raw_fix"]

    # Primary findings list untouched — audit still sees both.
    tagged = tag_reviewer_ghosts(observation)
    assert tagged.has_reviewer_ghosts is True
    assert len(tagged.reviewer_ghost_findings) == 1
    assert len(tagged.findings) == 2  # original findings preserved


# ---------- 2. all-valid-anchors case: no ghosts, unchanged observation ----------


def test_all_valid_anchors_yields_no_ghosts() -> None:
    content = "Hello **він** (it) in **ґанок** (porch)."
    findings = (
        _finding(
            dimension="Notation",
            severity="minor",
            location="intro paragraph",
            issue="notation uses the wrong symbol",
            fix="fix the notation in place",
        ),
    )
    parsed_fixes = (
        {"find": "Hello **він** (it)", "replace": "Hear [g] in **ґанок**"},
    )
    observation = _observation(
        findings=findings, parsed_fixes=parsed_fixes, module_content=content
    )

    ghosts = collect_reviewer_ghost_findings(observation)
    assert ghosts == ()

    tagged = tag_reviewer_ghosts(observation)
    assert tagged.has_reviewer_ghosts is False
    assert tagged.reviewer_ghost_findings == ()
    # tag_reviewer_ghosts must not mutate the input when there are no ghosts;
    # same identity (frozen dataclass short-circuit) is the strongest signal.
    assert tagged is observation


# ---------- 3. plan-level finding WITH anchor_missing underlying fix ----------


def test_plan_level_finding_keeps_hardstop_even_with_missing_anchor() -> None:
    """Edge case: plan-level finding (e.g. vocab_density / pedagogical_sequence)
    short-circuits to ``plan_level_hardstop`` in ``classify_patchability``, so
    it is NOT a ghost even when the reviewer's <fixes> block has bad anchors.

    Rationale from task spec: the predicate treats plan_level as a separate
    bucket; anchor_missing takes precedence ONLY for non-plan findings.
    """
    content = "Some module prose."
    findings = (
        _finding(
            dimension="Plan Adherence",
            severity="critical",
            location="## whole module",
            issue=(
                "The module opens with a direct contradiction — one paragraph "
                "states X and the next states not-X, both derived from the plan."
            ),
            fix="Resolve the contradiction by picking one side.",
        ),
    )
    parsed_fixes = ({"find": "ghost text not in content", "replace": "xxx"},)
    observation = _observation(
        findings=findings, parsed_fixes=parsed_fixes, module_content=content
    )

    prioritized = prioritize_findings(observation, growth_log_path=None)
    assert len(prioritized) == 1
    assert prioritized[0]["patchability"] == "plan_level_hardstop"

    ghosts = collect_reviewer_ghost_findings(observation)
    assert ghosts == ()
    tagged = tag_reviewer_ghosts(observation)
    assert tagged.has_reviewer_ghosts is False


# ---------- 4. observation without P0 inputs: no ghosts, no crash ----------


def test_legacy_observation_without_fixes_or_content_yields_no_ghosts() -> None:
    findings = (
        _finding(
            dimension="Pedagogy",
            severity="minor",
            location="activity 2",
            issue="activity type off-contract",
            fix="swap to allowed type",
        ),
    )
    observation = _observation(
        findings=findings, parsed_fixes=None, module_content=None
    )
    assert collect_reviewer_ghost_findings(observation) == ()
    assert tag_reviewer_ghosts(observation).has_reviewer_ghosts is False


# ---------- 5. has_reviewer_ghosts property contract ----------


def test_has_reviewer_ghosts_property_reflects_tuple_membership() -> None:
    observation = _observation(findings=(), parsed_fixes=None, module_content=None)
    assert observation.has_reviewer_ghosts is False
    # Default empty tuple → False.
    assert observation.reviewer_ghost_findings == ()
