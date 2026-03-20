"""Tests for V6 quick verify — fast structural checks after WRITE."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build.quick_verify import (
    QuickVerifyError,
    build_correction_directive,
    format_results,
    has_errors,
    quick_verify,
)


def _make_plan(
    sections=None,
    word_target=1200,
    required_vocab=None,
):
    """Create a minimal plan dict for testing."""
    if sections is None:
        sections = [
            {"section": "Звуки і літери (Sounds and Letters)", "words": 300},
            {"section": "Перші слова (First Words)", "words": 300},
        ]
    plan = {
        "word_target": word_target,
        "content_outline": sections,
        "vocabulary_hints": {
            "required": required_vocab or [],
        },
    }
    return plan


def _make_content(word_count=1200, sections=None, extra=""):
    """Generate test content with given word count and sections."""
    if sections is None:
        sections = ["Звуки і літери", "Перші слова"]

    lines = []
    for s in sections:
        lines.append(f"## {s}")
        lines.append("")

    # Add filler Ukrainian words to reach target
    filler = "Українська мова дуже гарна і мелодійна. " * (word_count // 6)
    lines.append(filler)
    lines.append(extra)
    return "\n".join(lines)


# --- Structure checks ---


def test_structure_pass():
    plan = _make_plan()
    content = _make_content()
    results = quick_verify(content, plan)
    structure_errors = [r for r in results if r.check == "STRUCTURE"]
    assert len(structure_errors) == 0


def test_structure_missing_section():
    plan = _make_plan()
    # Content only has first section
    content = "## Звуки і літери\n\nContent here. " * 200
    results = quick_verify(content, plan)
    structure_errors = [r for r in results if r.check == "STRUCTURE"]
    assert len(structure_errors) == 1
    assert "Перші слова" in structure_errors[0].message


# --- Word count checks ---


def test_word_count_pass():
    plan = _make_plan(word_target=1200)
    content = _make_content(word_count=1200)
    results = quick_verify(content, plan)
    wc_errors = [r for r in results if r.check == "WORD_COUNT"]
    assert len(wc_errors) == 0


def test_word_count_too_short():
    plan = _make_plan(word_target=1200)
    content = _make_content(word_count=300)  # Way under
    results = quick_verify(content, plan)
    wc_errors = [r for r in results if r.check == "WORD_COUNT"]
    assert len(wc_errors) == 1
    assert wc_errors[0].severity == "ERROR"
    assert "Too short" in wc_errors[0].message


def test_word_count_too_long():
    plan = _make_plan(word_target=1200)
    content = _make_content(word_count=2400)  # Way over 1.5x
    results = quick_verify(content, plan)
    wc_errors = [r for r in results if r.check == "WORD_COUNT"]
    assert len(wc_errors) == 1
    assert wc_errors[0].severity == "WARNING"


# --- Toxic token checks ---


def test_toxic_russian_chars():
    plan = _make_plan()
    content = _make_content(extra="Ты знаешь русский? ы э ё")
    results = quick_verify(content, plan)
    toxic_errors = [r for r in results if r.check == "TOXIC"]
    assert any("Russian characters" in r.message for r in toxic_errors)


def test_toxic_severe_russianisms():
    plan = _make_plan()
    content = _make_content(extra="пожалуйста скажите хорошо")
    results = quick_verify(content, plan)
    toxic_errors = [r for r in results if r.check == "TOXIC"]
    assert any("Severe Russianisms" in r.message for r in toxic_errors)


def test_toxic_clean():
    plan = _make_plan()
    content = _make_content()  # No Russian
    results = quick_verify(content, plan)
    toxic_errors = [r for r in results if r.check == "TOXIC"]
    assert len(toxic_errors) == 0


# --- Vocabulary checks ---


def test_vocabulary_present():
    plan = _make_plan(required_vocab=["мова", "гарна"])
    content = _make_content(extra="Українська мова дуже гарна.")
    results = quick_verify(content, plan)
    vocab_errors = [r for r in results if r.check == "VOCABULARY"]
    assert len(vocab_errors) == 0


def test_vocabulary_missing():
    plan = _make_plan(required_vocab=[
        "стіл (table, m)",
        "книга (book, f)",
        "вікно (window, n)",
        "кімната (room, f)",
    ])
    content = _make_content(extra="Тут є стіл і книга.")  # Missing вікно, кімната
    results = quick_verify(content, plan)
    vocab_errors = [r for r in results if r.check == "VOCABULARY"]
    assert len(vocab_errors) == 1
    assert "2/4" in vocab_errors[0].message


# --- Integration ---


def test_has_errors_true():
    errors = [QuickVerifyError("TEST", "ERROR", "fail")]
    assert has_errors(errors) is True


def test_has_errors_false_warnings_only():
    errors = [QuickVerifyError("TEST", "WARNING", "warn")]
    assert has_errors(errors) is False


def test_has_errors_empty():
    assert has_errors([]) is False


def test_format_results_pass():
    result = format_results([])
    assert "PASSED" in result


def test_format_results_fail():
    errors = [QuickVerifyError("TEST", "ERROR", "something broke")]
    result = format_results(errors)
    assert "FAILED" in result
    assert "something broke" in result


def test_correction_directive():
    errors = [
        QuickVerifyError("WORD_COUNT", "ERROR", "Too short: 500 words"),
        QuickVerifyError("TOXIC", "WARNING", "Latin chars found"),
    ]
    directive = build_correction_directive(errors)
    assert "<correction_directive>" in directive
    assert "Too short: 500 words" in directive
    assert "Latin chars found" in directive
    assert "FROM SCRATCH" in directive


def test_correction_directive_empty():
    assert build_correction_directive([]) == ""
