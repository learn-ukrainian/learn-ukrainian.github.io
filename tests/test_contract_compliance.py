"""Tests for deterministic contract-compliance checks."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from audit.checks.contract_compliance import (
    build_contract_correction_directive,
    check_contract_compliance,
    has_blocking_violations,
)


def _sample_contract() -> dict:
    return {
        "teaching_beats": {
            "section_order": ["Intro", "Practice"],
            "sections": [
                {"name": "Intro", "required_terms": ["звук", "літера"]},
                {"name": "Practice", "required_terms": ["привіт", "добре"]},
            ],
        },
        "section_word_budgets": {
            "Intro": {"min": 5, "max": 80},
            "Practice": {"min": 5, "max": 80},
        },
        "vocab_grammar_targets": {
            "must_introduce": ["привіт", "добре"],
        },
        "activity_obligations": [
            {"id": "quiz-intro", "type": "quiz", "focus": "intro"},
            {"id": "match-practice", "type": "match-up", "focus": "practice"},
        ],
        "dialogue_acts": [
            {"setting": "classroom", "speakers": ["Вчитель", "Учень"], "function": "greeting"},
        ],
        "factual_anchors": [
            {"section": "Intro", "citation": "wiki :: overview", "matched_terms": ["звук", "літера"]},
        ],
    }


def test_contract_compliance_detects_missing_items() -> None:
    content = """## Intro
Тут є звук, але немає потрібного діалогу.
<!-- INJECT_ACTIVITY: quiz-intro -->
"""
    violations = check_contract_compliance(content, _sample_contract())

    assert has_blocking_violations(violations) is True
    assert any(v["type"] == "MISSING_SECTION" for v in violations)
    assert any(v["type"] == "VOCAB_TARGETS" for v in violations)
    assert any(v["type"] == "DIALOGUE_ACT" for v in violations)


def test_contract_compliance_passes_good_content() -> None:
    content = """## Intro
У classroom Вчитель і Учень пояснюють, що звук і літера не те саме. Привіт і добре тут.
<!-- INJECT_ACTIVITY: quiz-intro -->

## Practice
Учень каже привіт і добре ще раз у practice section.
<!-- INJECT_ACTIVITY: match-practice -->
"""
    violations = check_contract_compliance(content, _sample_contract())
    assert violations == []


def test_contract_compliance_flags_missing_teaching_beat_terms() -> None:
    content = """## Intro
У classroom Вчитель і Учень пояснюють тільки звук. Привіт і добре тут.
<!-- INJECT_ACTIVITY: quiz-intro -->

## Practice
Учень каже привіт і добре ще раз у practice section.
<!-- INJECT_ACTIVITY: match-practice -->
"""
    violations = check_contract_compliance(content, _sample_contract())

    assert any(v["type"] == "TEACHING_BEATS" for v in violations)
    assert any("літера" in v["message"] for v in violations if v["type"] == "TEACHING_BEATS")


def test_contract_compliance_requires_all_dialogue_and_anchor_terms() -> None:
    content = """## Intro
У classroom Вчитель пояснює, що звук не те саме. Привіт і добре тут.
<!-- INJECT_ACTIVITY: quiz-intro -->

## Practice
Слухач каже привіт і добре ще раз у practice section.
<!-- INJECT_ACTIVITY: match-practice -->
"""
    violations = check_contract_compliance(content, _sample_contract())

    assert any(v["type"] == "DIALOGUE_ACT" for v in violations)
    assert any(v["type"] == "FACTUAL_ANCHOR" for v in violations)
    assert any("Учень" in v["message"] for v in violations if v["type"] == "DIALOGUE_ACT")
    assert any("літера" in v["message"] for v in violations if v["type"] == "FACTUAL_ANCHOR")


def test_activity_order_accepts_descriptive_markers_for_bare_type_contract() -> None:
    """Writer emits full IDs like `fill-in-khotity-conjugation`; contract pins
    only the bare type `fill-in`. The prefix match must accept this so the
    heal loop does not spin on an unsatisfiable comparison (#1251)."""
    contract = {
        "teaching_beats": {"section_order": [], "sections": []},
        "activity_obligations": [
            {"type": "fill-in"},
            {"type": "quiz"},
            {"type": "fill-in"},
            {"type": "quiz"},
        ],
    }
    content = """
<!-- INJECT_ACTIVITY: fill-in-khotity-conjugation -->
<!-- INJECT_ACTIVITY: quiz-verb-patterns -->
<!-- INJECT_ACTIVITY: fill-in-modal-logic -->
<!-- INJECT_ACTIVITY: quiz-modal-choice -->
"""
    violations = check_contract_compliance(content, contract)
    assert not any(v["type"] == "ACTIVITY_ORDER" for v in violations)


def test_activity_order_flags_actual_swap_even_with_descriptive_markers() -> None:
    """Ensure the prefix-match fix does not lose its ability to detect genuine
    order mismatches — positions 3 and 4 are swapped here (F,Q,Q,F vs F,Q,F,Q)."""
    contract = {
        "teaching_beats": {"section_order": [], "sections": []},
        "activity_obligations": [
            {"type": "fill-in"},
            {"type": "quiz"},
            {"type": "fill-in"},
            {"type": "quiz"},
        ],
    }
    content = """
<!-- INJECT_ACTIVITY: fill-in-khotity-conjugation -->
<!-- INJECT_ACTIVITY: quiz-verb-patterns -->
<!-- INJECT_ACTIVITY: quiz-modal-choice -->
<!-- INJECT_ACTIVITY: fill-in-modal-logic -->
"""
    violations = check_contract_compliance(content, contract)
    order_violations = [v for v in violations if v["type"] == "ACTIVITY_ORDER"]
    assert len(order_violations) == 1
    assert "fill-in" in order_violations[0]["message"]


def test_activity_order_still_honors_exact_id_match() -> None:
    """When contract pins an exact `id`, the content marker must equal it —
    a bare-type prefix is insufficient."""
    contract = {
        "teaching_beats": {"section_order": [], "sections": []},
        "activity_obligations": [
            {"id": "quiz-intro", "type": "quiz"},
        ],
    }
    # Exact id match — passes.
    ok_content = "<!-- INJECT_ACTIVITY: quiz-intro -->"
    assert not any(
        v["type"] == "ACTIVITY_ORDER"
        for v in check_contract_compliance(ok_content, contract)
    )
    # Same bare type, different id — still passes because `type` also matches.
    other_content = "<!-- INJECT_ACTIVITY: quiz-other -->"
    assert not any(
        v["type"] == "ACTIVITY_ORDER"
        for v in check_contract_compliance(other_content, contract)
    )
    # Wrong kind entirely — fails.
    wrong_content = "<!-- INJECT_ACTIVITY: fill-in-something -->"
    assert any(
        v["type"] == "ACTIVITY_ORDER"
        for v in check_contract_compliance(wrong_content, contract)
    )


def test_contract_correction_directive_lists_violations() -> None:
    directive = build_contract_correction_directive(
        [{"section": "Intro", "message": "Missing factual anchor"}]
    )
    assert "Intro" in directive
    assert "Missing factual anchor" in directive
