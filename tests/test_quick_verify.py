"""Tests for V6 quick verify — fast structural checks after WRITE."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build.quick_verify import (
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


def test_structure_missing_section():
    plan = _make_plan()
    # Content only has first section
    content = "## Звуки і літери\n\nContent here. " * 200
    results = quick_verify(content, plan)
    structure_errors = [r for r in results if r.check == "STRUCTURE"]
    assert len(structure_errors) == 1
    assert "Перші слова" in structure_errors[0].message


# --- Word count checks ---


def test_word_count_too_short():
    plan = _make_plan(word_target=1200)
    content = _make_content(word_count=300)  # Way under
    results = quick_verify(content, plan)
    wc_errors = [r for r in results if r.check == "WORD_COUNT"]
    assert len(wc_errors) == 1
    assert wc_errors[0].severity == "ERROR"
    assert "Too short" in wc_errors[0].message


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


def test_vocabulary_accepts_simple_inflected_required_form():
    plan = _make_plan(required_vocab=["кава (coffee, f)"])
    content = _make_content(extra="Можна мені, будь ласка, каву?")
    results = quick_verify(content, plan)
    vocab_errors = [r for r in results if r.check == "VOCABULARY"]
    assert len(vocab_errors) == 0


# --- Integration ---


# --- Exercise item count checks ---


def _make_plan_with_activities(activity_hints=None, **kwargs):
    """Create a plan dict with activity_hints."""
    plan = _make_plan(**kwargs)
    if activity_hints is not None:
        plan["activity_hints"] = activity_hints
    return plan


# --- INJECT_ACTIVITY marker counting (#1054) ---


def test_exercises_inject_markers_zero_no_false_warning():
    """Plan with hints + INJECT markers should NOT warn about 0 placeholders (#1054)."""
    plan = _make_plan_with_activities(activity_hints=[
        {"type": "quiz", "title": "Test 1"},
    ])
    content = _make_content(extra="\n<!-- INJECT_ACTIVITY: quiz-test -->\n")
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert len(ex_errors) == 0


def test_exercises_unnormalized_markers_count():
    """Unnormalized `type, description` form markers count too (#1189).

    Regression test for the false EXERCISE failures on participles-passive
    (1/6 reported), participle-phrases (2/6 reported), b1-baseline-past-present
    (5/6 reported), and daily-life-and-routines (4/5 reported). The strict
    regex `[a-z0-9][a-z0-9-]*` only matched normalized kebab-case IDs and
    rejected the loose `type, description` form that the writer commonly
    emits before the marker normalizer runs. Codex root-cause analysis in
    issue #1189 task `b1-participles-exercises`.
    """
    plan = _make_plan_with_activities(activity_hints=[
        {"type": "reading", "title": "T1"},
        {"type": "essay-response", "title": "T2"},
        {"type": "fill-in", "title": "T3"},
        {"type": "error-correction", "title": "T4"},
        {"type": "quiz", "title": "T5"},
        {"type": "match-up", "title": "T6"},
    ])
    # All 6 markers in unnormalized "type, description" form
    content = _make_content(extra=(
        "\n<!-- INJECT_ACTIVITY: reading, Past participle reading -->\n"
        "\n<!-- INJECT_ACTIVITY: essay-response, Compose 5 sentences -->\n"
        "\n<!-- INJECT_ACTIVITY: fill-in, Past tense forms -->\n"
        "\n<!-- INJECT_ACTIVITY: error-correction, Aspect mistakes -->\n"
        "\n<!-- INJECT_ACTIVITY: quiz, Participle vs adjective -->\n"
        "\n<!-- INJECT_ACTIVITY: match-up, Verb to participle -->\n"
    ))
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert ex_errors == [], (
        f"Loose marker regex should match `type, description` form. "
        f"Got: {[str(e) for e in ex_errors]}"
    )


# --- AC10: Retry catches bad output ---
