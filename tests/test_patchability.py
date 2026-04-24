"""Tests for the validated-patchability predicate (GH #1525 P0).

Invariants:
1. Plan-level findings ALWAYS return ``plan_level_hardstop`` regardless of fixes
   or content — preserves ADR-007 plan_revision_request routing for genuine
   plan defects.
2. Legacy callers (no fixes, no content) get ``not_evaluated`` — old heuristic
   path stays intact.
3. ``batch_patch_ok`` fires only when ALL fixes have anchors present in content.
   A partial set is ``anchor_missing`` (reviewer saw stale text → don't trust
   the batch). The status is OBSERVATION-SCOPED (GH #1526 item 1) — it
   describes the ``<fixes>`` block as a whole, not the individual finding.
4. ``compute_anchor_validation`` runs ONCE per observation; ``classify_patchability``
   consumes the result per finding without rescanning.
5. Golden fixture derived from a1/sounds-letters-and-hello R1 (the module
   that surfaced this bug): all 9 findings across 3 failing dims must route
   to ``batch_patch_ok`` under the new predicate so the pipeline re-fire
   converges.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.patchability import (
    AnchorValidation,
    classify_patchability,
    compute_anchor_validation,
    validate_fix_anchors,
)

# ---------- primitive anchor validation ----------


def test_validate_fix_anchors_splits_by_presence() -> None:
    content = "Hello world. The quick brown fox. Another line."
    fixes = [
        {"find": "quick brown fox", "replace": "lazy dog"},
        {"find": "not in content", "replace": "irrelevant"},
        {"insert_after": "Hello world.", "text": " New content."},
    ]
    valid, invalid = validate_fix_anchors(fixes, content)
    assert len(valid) == 2
    assert len(invalid) == 1
    assert invalid[0]["find"] == "not in content"


def test_validate_fix_anchors_rejects_malformed_fix() -> None:
    content = "any content"
    fixes = [{"no_find_key": "broken"}]
    valid, invalid = validate_fix_anchors(fixes, content)
    assert valid == []
    assert invalid == fixes


# ---------- compute_anchor_validation (observation-level) ----------


def test_compute_anchor_validation_aggregates_once() -> None:
    content = "Alpha Beta Gamma"
    fixes = [
        {"find": "Alpha", "replace": "α"},
        {"find": "Beta", "replace": "β"},
        {"find": "Delta", "replace": "δ"},  # absent
    ]
    result = compute_anchor_validation(fixes, content)
    assert result == AnchorValidation(evaluated=True, total=3, valid=2, invalid=1)


def test_compute_anchor_validation_not_evaluated_when_inputs_none() -> None:
    assert compute_anchor_validation(None, "some content") == AnchorValidation(
        evaluated=False, total=0, valid=0, invalid=0
    )
    assert compute_anchor_validation([{"find": "x", "replace": "y"}], None) == AnchorValidation(
        evaluated=False, total=0, valid=0, invalid=0
    )


def test_compute_anchor_validation_accepts_tuple_without_copy() -> None:
    # Real call-site passes observation.parsed_fixes, which is a tuple.
    # Regression guard: don't require list conversion at the boundary.
    content = "tuple input works"
    result = compute_anchor_validation(({"find": "tuple", "replace": "x"},), content)
    assert result.evaluated is True
    assert result.valid == 1


# ---------- plan-level hardstop (ADR-007 preservation) ----------


def test_plan_level_finding_always_hardstops() -> None:
    finding = {"plan_level": True, "error_class": "plan_contradiction"}
    validation = compute_anchor_validation(
        [{"find": "content", "replace": "replacement"}], "content is in here"
    )
    status, reason = classify_patchability(finding, anchor_validation=validation)
    assert status == "plan_level_hardstop"
    assert "plan_contradiction" in reason


def test_plan_level_hardstop_fires_before_evaluation_check() -> None:
    # Plan-level short-circuits before we read anchor_validation.evaluated —
    # safe even if caller passed the unevaluated default.
    finding = {"plan_level": True, "error_class": "vocab_density"}
    status, reason = classify_patchability(
        finding,
        anchor_validation=AnchorValidation(evaluated=False, total=0, valid=0, invalid=0),
    )
    assert status == "plan_level_hardstop"
    assert "vocab_density" in reason


# ---------- legacy / not-evaluated path ----------


def test_not_evaluated_when_caller_skipped_validation() -> None:
    finding = {"plan_level": False, "error_class": "notation_error"}
    validation = compute_anchor_validation(None, None)
    status, reason = classify_patchability(finding, anchor_validation=validation)
    assert status == "not_evaluated"
    assert "did not supply" in reason


# ---------- no_fixes: reviewer emitted nothing ----------


def test_no_fixes_when_reviewer_emitted_empty_block() -> None:
    finding = {"plan_level": False, "error_class": "notation_error"}
    validation = compute_anchor_validation([], "module text")
    status, reason = classify_patchability(finding, anchor_validation=validation)
    assert status == "no_fixes"
    assert "nothing to patch" in reason


# ---------- anchor_missing: stale reviewer text ----------


def test_anchor_missing_when_any_fix_anchor_absent() -> None:
    finding = {"plan_level": False, "error_class": "notation_error"}
    content = "real module content is here"
    fixes = [
        {"find": "real module content", "replace": "updated"},
        {"find": "this string is not in content", "replace": "ghost"},
    ]
    validation = compute_anchor_validation(fixes, content)
    status, reason = classify_patchability(finding, anchor_validation=validation)
    assert status == "anchor_missing"
    assert "1 of 2" in reason
    assert "not present in content" in reason


def test_anchor_missing_when_all_fix_anchors_absent() -> None:
    finding = {"plan_level": False, "error_class": "notation_error"}
    content = "real module content"
    fixes = [{"find": "ghost 1", "replace": "x"}, {"find": "ghost 2", "replace": "y"}]
    validation = compute_anchor_validation(fixes, content)
    status, reason = classify_patchability(finding, anchor_validation=validation)
    assert status == "anchor_missing"
    assert "2 of 2" in reason


# ---------- batch_patch_ok: the unlock condition ----------


def test_batch_patch_ok_when_all_anchors_validate_and_not_plan_level() -> None:
    finding = {"plan_level": False, "error_class": "notation_error"}
    content = "Hear **він** (it) in **ґанок** (porch)."
    fixes = [
        {
            "find": "Hear **він** (it) in **ґанок** (porch).",
            "replace": "Hear [g] in **ґанок** (porch).",
        }
    ]
    validation = compute_anchor_validation(fixes, content)
    status, reason = classify_patchability(finding, anchor_validation=validation)
    assert status == "batch_patch_ok"
    assert "1 fix anchors validated" in reason
    # GH #1526 item 1: the reason must surface the batch-level caveat so
    # readers don't misread ``batch_patch_ok`` as a per-finding guarantee.
    assert "batch-level" in reason


def test_batch_patch_ok_with_insert_after_directive() -> None:
    finding = {"plan_level": False, "error_class": "word_budget"}
    content = "Section 1 content.\n\nSection 2 content."
    fixes = [{"insert_after": "Section 1 content.", "text": " Added sentence."}]
    validation = compute_anchor_validation(fixes, content)
    status, _ = classify_patchability(finding, anchor_validation=validation)
    assert status == "batch_patch_ok"


# ---------- dispatch-order parity with _apply_review_fixes ----------


def test_mixed_shape_fix_validates_insert_after_first() -> None:
    """Regression guard: a mixed-shape fix must be validated using the anchor
    that ``_apply_review_fixes`` will actually use.

    ``_apply_review_fixes`` (v6_build.py:8180) dispatches ``insert_after``
    BEFORE ``find``. If our validator checked ``find`` first, a fix with a
    valid ``find`` anchor but a missing ``insert_after`` anchor would be
    marked ``batch_patch_ok`` even though the apply step silently skips it
    — a false positive in the batch-patchability contract.
    """
    content = "the find-anchor is present but insert_after is missing"
    mixed_fix = [
        {
            "find": "the find-anchor is present",
            "replace": "updated",
            "insert_after": "this anchor is absent from content",
            "text": " payload",
        }
    ]
    # Apply step would use insert_after (absent) → skip. Predicate must agree.
    validation = compute_anchor_validation(mixed_fix, content)
    assert validation == AnchorValidation(evaluated=True, total=1, valid=0, invalid=1)
    finding = {"plan_level": False, "error_class": "notation_error"}
    status, _ = classify_patchability(finding, anchor_validation=validation)
    assert status == "anchor_missing"


# ---------- integration: empty-tuple telemetry through convergence_loop ----------


def test_empty_parsed_fixes_tuple_reports_no_fixes_not_unevaluated() -> None:
    """A real observation whose reviewer emitted zero <fixes> MUST report
    ``no_fixes`` (reviewer was there, had nothing to say), NOT ``not_evaluated``
    (observation wasn't populated with P0 inputs).

    Regression guard: an earlier version collapsed ``if parsed_fixes else None``
    which silently lost the distinction. The ``no_fixes`` branch would be
    dead in production and the audit trail would be wrong.
    """
    # Empty tuple (reviewer emitted nothing) + populated content → no_fixes
    validation = compute_anchor_validation((), "real module content")
    assert validation == AnchorValidation(evaluated=True, total=0, valid=0, invalid=0)
    finding = {"plan_level": False, "error_class": "notation_error"}
    status, reason = classify_patchability(finding, anchor_validation=validation)
    assert status == "no_fixes"
    assert "nothing to patch" in reason
    # None (legacy observation) → not_evaluated
    legacy_validation = compute_anchor_validation(None, None)
    assert legacy_validation.evaluated is False
    status, _ = classify_patchability(finding, anchor_validation=legacy_validation)
    assert status == "not_evaluated"


def test_empty_fixes_propagate_through_prioritize_findings() -> None:
    """Integration: construct a real ReviewObservation with parsed_fixes=()
    + populated module_content, send through prioritize_findings (the public
    wrapper over _normalize_observation), and assert the finding carries
    ``patchability == "no_fixes"`` in the audit trail — not ``not_evaluated``.

    This is the production code path Codex's round-2 review flagged as
    needing coverage beyond the helper-level unit tests.
    """
    from build.convergence_loop import ReviewObservation, prioritize_findings

    # Use a finding whose classifier topology is NOT local_to_prose, so we
    # can prove the no_fixes path does not illegally override.
    observation = ReviewObservation(
        passed=False,
        score=5.0,
        review_text="(reviewer emitted no <fixes> block)",
        findings=(
            {
                "dimension": "Plan Adherence",
                "severity": "major",
                "location": "## Intro and ## Practice",
                "issue": "Activity order and vocabulary pacing drift across multiple sections.",
                "fix": "Resequence the module.",
            },
        ),
        dim_floor_dimensions=("plan_adherence",),
        content_hash="abc123",
        patch_available=False,
        parsed_fixes=(),  # reviewer emitted zero fixes
        module_content="real module text that the reviewer read",
    )
    prioritized = prioritize_findings(observation, growth_log_path=None)
    assert len(prioritized) == 1
    item = prioritized[0]
    # Audit-trail assertion (Codex's ask): no_fixes branch is live in production
    assert item["patchability"] == "no_fixes", (
        f"expected no_fixes (reviewer emitted zero fixes), got {item['patchability']!r}"
    )
    # Override assertion: no_fixes must NOT promote classifier's cross_section
    # to local_to_prose. The finding stays cross_section → plan_revision_request.
    assert item["topology_classifier_output"] == "cross_section"
    assert item["topology"] == "cross_section"


def test_legacy_observation_without_p0_fields_reports_not_evaluated() -> None:
    """Integration: a ReviewObservation from legacy test fixtures (doesn't
    set parsed_fixes/module_content) preserves pre-P0 behavior via the
    ``not_evaluated`` path — topology classifier drives routing alone.
    """
    from build.convergence_loop import ReviewObservation, prioritize_findings

    observation = ReviewObservation(
        passed=False,
        score=5.0,
        review_text="legacy",
        findings=(
            {
                "dimension": "Linguistic Accuracy",
                "severity": "major",
                "location": "## Intro / paragraph 1 / sentence 1",
                "issue": "The sentence mislabels [=] as a dash.",
                "fix": "Change the sentence only.",
            },
        ),
        dim_floor_dimensions=(),
        content_hash="abc123",
        patch_available=False,
        # parsed_fixes and module_content intentionally omitted — default to None
    )
    prioritized = prioritize_findings(observation, growth_log_path=None)
    assert prioritized[0]["patchability"] == "not_evaluated"


# ---------- golden fixture from the pilot that surfaced this bug ----------


def test_pilot_sounds_letters_and_hello_r1_all_findings_route_to_patch() -> None:
    """Every real finding from a1/sounds-letters-and-hello R1 must route to
    batch_patch_ok under the new predicate.

    This module's R1 review emitted 9 concrete find/replace pairs across
    Honesty/Factual/Plan_Adherence. Under the old heuristic topology classifier,
    5 of the Plan_Adherence findings were labeled cross_section, blocking the
    fix-application path and escalating to plan_revision_request. The new
    predicate routes all of them correctly.
    """
    content = (
        "Hear **він** (it) in **ґанок** (porch).\n"
        "Ukrainian is strikingly vocalic — 42–46% of spoken speech is vowel sound. "
        "That musicality is what every learner hears first.\n"
        "In **молоко** the unstressed [о] stays a CLEAN [о]. Do NOT reduce it to [а] "
        "— that reduction is the Russian pattern, which Ukrainian rejects. Every "
        "unstressed Ukrainian vowel keeps its own quality.\n"
        "Ukrainian has 32 consonant sounds drawn from 22 **літер** (letters) — each "
        "**літера** (letter) can stand for a hard or soft sound.\n"
        "<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->\n"
        "<!-- INJECT_ACTIVITY: match-up-letter-to-sound -->\n"
        "<!-- INJECT_ACTIVITY: fill-in-l2-errors -->\n"
        "<!-- INJECT_ACTIVITY: quiz-melodiousness-stress -->\n"
        "Take these openers and farewells as indivisible chunks. **Добрий день!** (good day), "
        "**Доброго ранку!** (good morning), **Добрий вечір!** (good evening) — greetings. "
        "**До побачення!** (goodbye), **На все добре!** (all the best) — farewells.\n"
    )
    fixes = [
        {
            "find": "Hear **він** (it) in **ґанок** (porch).",
            "replace": "Hear [g] in **ґанок** (porch).",
        },
        {
            "find": "Ukrainian is strikingly vocalic — 42–46% of spoken speech is vowel sound. That musicality is what every learner hears first.",
            "replace": "Ukrainian speech gives beginners a clear path into syllables.",
        },
        {
            "find": "In **молоко** the unstressed [о] stays a CLEAN [о]. Do NOT reduce it to [а] — that reduction is the Russian pattern, which Ukrainian rejects. Every unstressed Ukrainian vowel keeps its own quality.",
            "replace": "In **молоко** the unstressed [о] stays a CLEAN [о]. Do NOT reduce it to [а] — that reduction is the Russian pattern, not the Ukrainian one.",
        },
        {
            "find": "Ukrainian has 32 consonant sounds drawn from 22 **літер** (letters) — each **літера** (letter) can stand for a hard or soft sound.",
            "replace": "Ukrainian has 32 consonant sounds drawn from 22 consonant **літери** (letters). Some consonants form hard/soft pairs.",
        },
        {"find": "<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->", "replace": ""},
        {"find": "<!-- INJECT_ACTIVITY: match-up-letter-to-sound -->", "replace": ""},
        {
            "find": "<!-- INJECT_ACTIVITY: fill-in-l2-errors -->",
            "replace": "One L2 trap: Ukrainian voiced consonants stay voiced at word end.\n\n<!-- INJECT_ACTIVITY: fill-in-l2-errors -->",
        },
        {
            "find": "Take these openers and farewells as indivisible chunks. **Добрий день!** (good day), **Доброго ранку!** (good morning), **Добрий вечір!** (good evening) — greetings. **До побачення!** (goodbye), **На все добре!** (all the best) — farewells.",
            "replace": "Take these openers and farewells as indivisible chunks, with stress marked: **До́брий день!** (good day), **До́брого ра́нку!** (good morning), **До́брий ве́чір!** (good evening) — greetings. **До поба́чення!** (goodbye), **На все до́бре!** (all the best) — farewells.",
        },
        {
            "find": "<!-- INJECT_ACTIVITY: quiz-melodiousness-stress -->",
            "replace": "**Милозвучність** means smooth sound flow.\n\n<!-- INJECT_ACTIVITY: quiz-melodiousness-stress -->",
        },
    ]
    findings = [
        {"plan_level": False, "error_class": "notation_error"},
        {"plan_level": False, "error_class": "factual_error"},
        {"plan_level": False, "error_class": "factual_error"},
        {"plan_level": False, "error_class": "factual_error"},
        {"plan_level": False, "error_class": "activity_order"},
        {"plan_level": False, "error_class": "activity_order"},
        {"plan_level": False, "error_class": "activity_order"},
        {"plan_level": False, "error_class": "activity_order"},
        {"plan_level": False, "error_class": "activity_order"},
    ]
    # Observation-level validation runs ONCE — not per finding.
    validation = compute_anchor_validation(fixes, content)
    assert validation == AnchorValidation(evaluated=True, total=9, valid=9, invalid=0)
    for finding in findings:
        status, _ = classify_patchability(finding, anchor_validation=validation)
        assert status == "batch_patch_ok", (
            f"Finding {finding} should route to batch_patch_ok with all 9 anchor-valid "
            f"fixes present in content; got {status!r}"
        )
