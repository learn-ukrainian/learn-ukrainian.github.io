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


def test_contract_correction_directive_lists_violations() -> None:
    directive = build_contract_correction_directive(
        [{"section": "Intro", "message": "Missing factual anchor"}]
    )
    assert "Intro" in directive
    assert "Missing factual anchor" in directive
