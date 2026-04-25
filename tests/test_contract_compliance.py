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


def test_contract_correction_directive_lists_violations() -> None:
    directive = build_contract_correction_directive(
        [{"section": "Intro", "message": "Missing factual anchor"}]
    )
    assert "Intro" in directive
    assert "Missing factual anchor" in directive


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


def test_activity_order_accepts_multi_position_reorder() -> None:
    contract = {
        "activity_obligations": [
            {"type": "fill-in"},
            {"type": "quiz"},
            {"type": "fill-in"},
            {"type": "quiz"},
        ],
    }
    content = """
<!-- INJECT_ACTIVITY: fill-in-khotity -->
<!-- INJECT_ACTIVITY: quiz-conjugation-pattern -->
<!-- INJECT_ACTIVITY: quiz-modal-choice -->
<!-- INJECT_ACTIVITY: fill-in-combo -->
"""
    violations = check_contract_compliance(content, contract)
    order_violations = [v for v in violations if v["type"] == "ACTIVITY_ORDER"]
    assert order_violations == []


def test_activity_order_reports_length_shortfall() -> None:
    contract = {
        "activity_obligations": [
            {"type": "fill-in"},
            {"type": "quiz"},
            {"type": "fill-in"},
            {"type": "quiz"},
        ],
    }
    content = """
<!-- INJECT_ACTIVITY: fill-in-khotity -->
<!-- INJECT_ACTIVITY: quiz-conjugation-pattern -->
"""
    violations = check_contract_compliance(content, contract)
    order_violations = [v for v in violations if v["type"] == "ACTIVITY_ORDER"]
    assert len(order_violations) == 1
    assert "Missing required activity obligation markers: ['fill-in', 'quiz']" in order_violations[0]["message"]


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


def test_meta_narration_ignores_inline_let_us() -> None:
    """The A1/M01 case. ``Let us practice`` as the third sentence of an
    ordinary paragraph is legitimate teacher phrasing — not a formulaic
    opener — and must not be flagged by the contract checker.
    """
    content = (
        "## Голосні звуки (Vowel Sounds)\n"
        "\n"
        "Ukrainian primary schools use a specific visual notation for "
        "sound models. Vowel sounds are always marked with a solid "
        "circle [•]. Let us practice hearing these vowels in simple "
        "words. For example, the word **мама** contains two [а] sounds.\n"
    )
    assert _meta_narration_violations(content) == []


def test_meta_narration_flags_let_us_as_paragraph_opener() -> None:
    """A paragraph that begins with ``Let us look at ...`` IS a
    formulaic opener and must be flagged."""
    content = (
        "## Intro\n"
        "\n"
        "Let us look at the Ukrainian alphabet. The alphabet has 33 letters.\n"
    )
    violations = _meta_narration_violations(content)
    assert len(violations) == 1
    assert "Let us" in violations[0]["message"]
    assert violations[0]["severity"] == "WARNING"


def test_meta_narration_flags_in_this_section_opener() -> None:
    content = (
        "## Intro\n"
        "\n"
        "In this section we will explore vowels. Vowels are essential.\n"
    )
    violations = _meta_narration_violations(content)
    assert len(violations) == 1
    assert "In this section" in violations[0]["message"]


def test_meta_narration_flags_now_lets_opener() -> None:
    content = (
        "## Practice\n"
        "\n"
        "Now let's practice. Try this word.\n"
    )
    violations = _meta_narration_violations(content)
    assert len(violations) == 1
    assert "Now let's" in violations[0]["message"]


def test_meta_narration_flags_bold_wrapped_opener() -> None:
    """Opening with ``**Let us see** ...`` — bold markers must be
    stripped before the opener check, so it still fires."""
    content = (
        "## Section\n"
        "\n"
        "**Let us see** the letters. There are 33.\n"
    )
    violations = _meta_narration_violations(content)
    assert len(violations) == 1


def test_meta_narration_ignores_second_sentence_opener() -> None:
    """Only the FIRST sentence of each paragraph is checked. A
    forbidden phrase starting the second sentence is not a signpost —
    it's regular teacher prose."""
    content = (
        "## Section\n"
        "\n"
        "The alphabet has 33 letters. Let us see what they are.\n"
    )
    assert _meta_narration_violations(content) == []


def test_meta_narration_ignores_heading_text() -> None:
    """A heading that happens to contain ``Let us`` is not a paragraph
    and must not trip the opener check."""
    content = (
        "## Let us look at letters\n"
        "\n"
        "The alphabet has 33 letters.\n"
    )
    assert _meta_narration_violations(content) == []


def test_meta_narration_ignores_list_item() -> None:
    """List items are structural markdown, not prose paragraphs."""
    content = (
        "## Tips\n"
        "\n"
        "- Let us try an example\n"
        "- Another tip\n"
    )
    assert _meta_narration_violations(content) == []


def test_meta_narration_ignores_admonition_block() -> None:
    content = (
        "## Tip\n"
        "\n"
        ":::tip\n"
        "Let us remember this\n"
        ":::\n"
    )
    assert _meta_narration_violations(content) == []


def test_meta_narration_ignores_blockquote() -> None:
    content = (
        "## Quote\n"
        "\n"
        "> Let us begin with patience.\n"
    )
    assert _meta_narration_violations(content) == []


def test_meta_narration_handles_comma_variant_of_now_lets() -> None:
    """``Now, let's begin.`` with a comma is still a formulaic opener."""
    content = (
        "## P\n"
        "\n"
        "Now, let's begin. The first letter is А.\n"
    )
    violations = _meta_narration_violations(content)
    assert len(violations) == 1


def test_meta_narration_only_reports_one_violation_per_module() -> None:
    """Multiple formulaic openers in the same module produce a single
    META_NARRATION violation (first-match semantics — matches the
    pre-Bug-D behavior and avoids duplicate noise)."""
    content = (
        "## A\n"
        "\n"
        "Let us start. First point.\n"
        "\n"
        "## B\n"
        "\n"
        "Now let's continue. Second point.\n"
    )
    violations = _meta_narration_violations(content)
    assert len(violations) == 1


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


def test_meta_narration_flags_html_comment_no_blank_line_before_opener() -> None:
    """An HTML comment line followed immediately by a formulaic opener
    on the next line must still flag."""
    content = "<!-- generated from plan -->\nLet us look at vowels. Vowels are core.\n"
    violations = _meta_narration_violations(content)
    assert len(violations) == 1


def test_meta_narration_handles_crlf_line_endings() -> None:
    """Windows CRLF must not break paragraph splitting or opener matching."""
    content = "## Intro\r\n\r\nLet us start. First point.\r\n"
    violations = _meta_narration_violations(content)
    assert len(violations) == 1
    assert "Let us" in violations[0]["message"]


def test_meta_narration_flags_triple_emphasis_opener() -> None:
    """Nested emphasis ``***Let us***`` is stripped down to ``Let us``
    by the leading ``*``/``_`` strip, and still flags."""
    content = (
        "## Section\n"
        "\n"
        "***Let us***, as a class, explore the alphabet. There are 33 letters.\n"
    )
    violations = _meta_narration_violations(content)
    assert len(violations) == 1


def test_meta_narration_ignores_heading_only_block() -> None:
    """A block that contains only a heading and nothing else must not
    report a violation (no prose to flag)."""
    content = "## Let us review\n\n## Next heading\n"
    assert _meta_narration_violations(content) == []
