"""Tests for deterministic contract-compliance checks."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from audit.checks.contract_compliance import (
    check_archetype_fit,
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


def test_contract_compliance_treats_budget_as_minimum_only() -> None:
    contract = _sample_contract()
    contract["section_word_budgets"] = {
        "Intro": {"min": 5, "max": 10},
        "Practice": {"min": 5, "max": 10},
    }
    content = """## Intro
У classroom Вчитель і Учень пояснюють, що звук і літера не те саме. Привіт і добре тут. Ще кілька слів зверху.
<!-- INJECT_ACTIVITY: quiz-intro -->

## Practice
Учень каже привіт і добре ще раз у practice section. Додаємо ще трохи тексту, щоб перевищити стару стелю.
<!-- INJECT_ACTIVITY: match-practice -->
"""
    violations = check_contract_compliance(content, contract)
    assert not any(v["type"] == "WORD_BUDGET" for v in violations)


def test_contract_compliance_accepts_simple_inflected_required_vocab() -> None:
    contract = {
        "teaching_beats": {"section_order": [], "sections": []},
        "vocab_grammar_targets": {"must_introduce": ["кава (coffee, f)"]},
        "activity_obligations": [],
    }
    content = "## Діалоги\nМожна мені, будь ласка, каву?\n"
    violations = check_contract_compliance(content, contract)
    assert not any(v["type"] == "VOCAB_TARGETS" for v in violations)


def test_contract_compliance_accepts_titles_without_parenthetical_gloss() -> None:
    contract = {
        "teaching_beats": {
            "section_order": ["Діалоги (Dialogues)", "Підсумок — Summary"],
            "sections": [
                {"name": "Діалоги (Dialogues)", "required_terms": []},
                {"name": "Підсумок — Summary", "required_terms": []},
            ],
        },
        "section_word_budgets": {
            "Діалоги (Dialogues)": {"min": 1, "max": 50},
            "Підсумок — Summary": {"min": 1, "max": 50},
        },
        "activity_obligations": [],
    }
    content = """## Діалоги
Короткий текст.

## Підсумок — Summary
Ще трохи тексту.
"""
    violations = check_contract_compliance(content, contract)
    assert not any(v["type"] in {"SECTION_ORDER", "MISSING_SECTION"} for v in violations)


def test_contract_compliance_dialogue_grounding_uses_speakers_not_english_setting() -> None:
    contract = {
        "teaching_beats": {"section_order": [], "sections": []},
        "dialogue_acts": [
            {
                "setting": "Ordering at a café",
                "speakers": ["Клієнт", "Офіціантка"],
                "function": "A1 service exchange",
            }
        ],
        "activity_obligations": [],
    }
    content = """## Діалоги
> — **Клієнт:** Добрий день!
> — **Офіціантка:** Добрий день!
"""
    violations = check_contract_compliance(content, contract)
    assert not any(v["type"] == "DIALOGUE_ACT" for v in violations)


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


def test_activity_order_accepts_swapped_descriptive_markers() -> None:
    """Activity obligations are a multiset; marker order is incidental."""
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
    assert order_violations == []


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


def test_activity_order_reports_single_position_mismatch() -> None:
    contract = {
        "activity_obligations": [
            {"type": "fill-in"},
            {"type": "quiz"},
        ],
    }
    content = """
<!-- INJECT_ACTIVITY: fill-in-khotity -->
<!-- INJECT_ACTIVITY: match-up -->
"""
    violations = check_contract_compliance(content, contract)
    order_violations = [v for v in violations if v["type"] == "ACTIVITY_ORDER"]
    assert len(order_violations) == 1
    assert "Missing required activity obligation markers: ['quiz']" in order_violations[0]["message"]


# ====================================================================
# Bug #1316 Bug D — META_NARRATION opener-only scoping
# ====================================================================


def _opener_contract() -> dict:
    """Minimal contract — only exercised for its META_NARRATION check path."""
    return {
        "teaching_beats": {"section_order": [], "sections": []},
        "section_word_budgets": {},
        "vocab_grammar_targets": {"must_introduce": []},
        "activity_obligations": [],
        "dialogue_acts": [],
        "factual_anchors": [],
    }


def _meta_narration_violations(content: str) -> list[dict]:
    return [
        v
        for v in check_contract_compliance(content, _opener_contract())
        if v["type"] == "META_NARRATION"
    ]


def test_meta_narration_flags_heading_no_blank_line_before_opener() -> None:
    """Bug #1316 Bug D second pass (Codex finding).

    The common Markdown pattern ``## Intro\\nLet us begin.`` has no
    blank line between the heading and the opening sentence. Both
    heading and opener belong to the same blank-line-separated
    "paragraph" block, so the check must strip the leading heading
    line and still flag the opener.
    """
    content = "## Intro\nLet us begin. First point.\n"
    violations = _meta_narration_violations(content)
    assert len(violations) == 1
    assert "Let us" in violations[0]["message"]


# ====================================================================
# A1 module archetype fit wrapper
# ====================================================================


def test_archetype_fit_accepts_current_m1_textbook_workbook_shape() -> None:
    content = (
        "## Sound first\n"
        "Listen for the letter shape, then say the tiny Ukrainian sound.\n"
        "<!-- INJECT_ACTIVITY: act-1 -->\n"
        "А Б В Г Ґ\n"
    )
    activities = [
        {"id": "act-1", "type": "quiz"},
        {"id": "act-2", "type": "match-up"},
        {"id": "act-3", "type": "fill-in"},
        {"id": "act-4", "type": "true-false"},
        {"id": "act-5", "type": "order"},
    ]

    report = check_archetype_fit(
        content,
        {"module": {"level": "a1", "module_num": 1}},
        activities=activities,
    )

    assert report["passed"] is True
    assert report["archetype"] == "a1-zero-script-onboarding"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["english_led_surface"]["latin_words"] > checks["english_led_surface"]["cyrillic_words"]
    assert checks["textbook_workbook_split"]["workbook_only_ids"]


def test_archetype_fit_rejects_internal_wiki_links() -> None:
    report = check_archetype_fit(
        "## Sound First\nSee wiki/pedagogy/a1/sounds-letters-and-hello.md.",
        {"module": {"level": "a1", "module_num": 1}},
        activities=[
            {"id": "act-1", "type": "quiz"},
            {"id": "act-2", "type": "match-up"},
            {"id": "act-3", "type": "fill-in"},
            {"id": "act-4", "type": "true-false"},
            {"id": "act-5", "type": "translate"},
        ],
    )

    assert report["passed"] is False
    assert any(item["check"] == "no_internal_wiki_links" for item in report["violations"])


def test_archetype_fit_rejects_ukrainian_led_zero_script_surface() -> None:
    content = (
        "## Звуки\n"
        "<!-- INJECT_ACTIVITY: act-1 -->\n"
        + " ".join(["український"] * 80)
    )
    activities = [
        {"id": "act-1", "type": "quiz"},
        {"id": "act-2", "type": "match-up"},
        {"id": "act-3", "type": "fill-in"},
        {"id": "act-4", "type": "true-false"},
        {"id": "act-5", "type": "translate"},
    ]

    report = check_archetype_fit(
        content,
        {"module": {"level": "a1", "module_num": 1}},
        activities=activities,
    )

    assert report["passed"] is False
    assert any(item["check"] == "english_led_surface" for item in report["violations"])


def test_archetype_fit_rejects_non_a1_workbook_activity_type() -> None:
    content = "## Sound First\nEnglish first.\n<!-- INJECT_ACTIVITY: act-1 -->"
    activities = [
        {"id": "act-1", "type": "quiz"},
        {"id": "act-2", "type": "essay-response"},
        {"id": "act-3", "type": "fill-in"},
        {"id": "act-4", "type": "true-false"},
        {"id": "act-5", "type": "translate"},
    ]

    report = check_archetype_fit(
        content,
        {"module": {"level": "a1", "module_num": 1}},
        activities=activities,
    )

    assert report["passed"] is False
    assert any(item["check"] == "a1_activity_family" for item in report["violations"])
