"""Tests for V6 exercise placeholder filler."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build.exercises.fill_placeholders import (
    ExercisePlaceholder,
    _clean_text,
    _escape_yaml_str,
    _generate_exercise_dsl,
    _parse_placeholder,
    _parse_qa_pairs,
    fill_placeholders,
    validate_exercise_vocab,
)

# --- Parsing tests ---


def test_parse_placeholder_basic():
    block = """type: quiz
tests: gender identification
after: він/вона/воно test
items: 6
vocabulary: стіл, книга, вікно"""
    result = _parse_placeholder(block)
    assert result.exercise_type == "quiz"
    assert result.tests == "gender identification"
    assert result.after == "він/вона/воно test"
    assert result.items == 6
    assert result.vocabulary == ["стіл", "книга", "вікно"]


def test_parse_qa_pairs_arrow():
    pairs = _parse_qa_pairs("В→v, Н→n, Р→rolled r")
    assert len(pairs) == 3
    assert pairs[0] == ("В", "v")
    assert pairs[2] == ("Р", "rolled r")


# --- DSL generation with real content ---


def test_generate_quiz_with_qa_pairs():
    placeholder = ExercisePlaceholder(
        exercise_type="quiz",
        tests="match letter to sound",
        vocabulary=["В", "Н", "Р"],
        items=3,
        questions="В→v, Н→n, Р→r",
    )
    dsl = _generate_exercise_dsl(placeholder)
    assert ":::quiz" in dsl
    assert '"В"' in dsl
    assert '"v"' in dsl  # Real answer, not "?"
    assert '"?"' not in dsl  # No skeleton placeholders
    assert dsl.endswith(":::")


def test_generate_quiz_from_vocab():
    placeholder = ExercisePlaceholder(
        exercise_type="quiz",
        tests="identify the word",
        vocabulary=["мама", "тато"],
        items=2,
    )
    dsl = _generate_exercise_dsl(placeholder)
    assert ":::quiz" in dsl
    assert '"мама"' in dsl
    assert '"так"' in dsl  # Default binary options


def test_generate_match_up_with_pairs():
    placeholder = ExercisePlaceholder(
        exercise_type="match-up",
        tests="match false friends",
        questions="В→v (not b), Н→n (not h), Р→rolled r (not p)",
        items=3,
    )
    dsl = _generate_exercise_dsl(placeholder)
    assert ":::match-up" in dsl
    assert '"В"' in dsl
    assert '"v (not b)"' in dsl  # Real pair
    assert '"?"' not in dsl


def test_generate_group_sort_with_groups():
    placeholder = ExercisePlaceholder(
        exercise_type="group-sort",
        tests="sort by type",
        groups="Голосні: А, О, У, І; Приголосні: М, К, Б, Ш",
        items=8,
    )
    dsl = _generate_exercise_dsl(placeholder)
    assert ":::group-sort" in dsl
    assert '"Голосні"' in dsl
    assert '"Приголосні"' in dsl
    assert '"А"' in dsl
    assert '"М"' in dsl


def test_generate_fill_in_with_pairs():
    placeholder = ExercisePlaceholder(
        exercise_type="fill-in",
        tests="complete the greeting",
        questions="— ___! → Привіт; — Як ___? → справи",
        items=2,
    )
    dsl = _generate_exercise_dsl(placeholder)
    assert ":::fill-in" in dsl
    assert '"Привіт"' in dsl


def test_generate_true_false_with_pairs():
    placeholder = ExercisePlaceholder(
        exercise_type="true-false",
        tests="check facts",
        questions="В українській мові 33 літери → true; В українській мові 33 звуки → false",
        items=2,
    )
    dsl = _generate_exercise_dsl(placeholder)
    assert ":::true-false" in dsl
    assert "33 літери" in dsl
    assert "answer: true" in dsl
    assert "answer: false" in dsl


# --- Integration tests ---


def test_fill_placeholders_single():
    content = """## Section 1

Some teaching content here.

:::exercise-placeholder
type: quiz
tests: vowel recognition
items: 3
vocabulary: а, о, у
:::

More content after.
"""
    result, count = fill_placeholders(content)
    assert count == 1
    assert ":::quiz" in result
    assert ":::exercise-placeholder" not in result
    assert "More content after." in result


# --- Bug fix: _clean_text strips stray quotes (#996) ---


def test_clean_text_strips_leading_quote():
    assert _clean_text("'В") == "В"


def test_clean_text_preserves_internal_apostrophe():
    assert _clean_text("пам'ятка") == "пам'ятка"


# --- _escape_yaml_str with _clean_text ---


def test_escape_yaml_str_clean_and_escape():
    assert _escape_yaml_str("""'say "hi"'""") == "say 'hi'"


# --- Vocabulary parsing strips stray quotes ---


# --- Bug fix: fill-in context (#996) ---


def test_fill_in_vocab_gives_context_sentence():
    content = (
        ":::exercise-placeholder\n"
        "type: fill-in\n"
        "tests: practice\n"
        "vocabulary: мама, тато\n"
        ":::"
    )
    result, count = fill_placeholders(content)
    assert count == 1
    assert '- sentence: "___"' not in result
    assert "Write the Ukrainian word" in result
    assert 'answer: "мама"' in result
    assert 'answer: "тато"' in result


# --- TODO removal: fallback exercises produce valid DSL ---


# --- Stray quotes end-to-end ---


# --- validate_exercise_vocab ---


def test_validate_exercise_vocab_extracts_from_quiz():
    content = (
        ':::quiz\ntitle: "Test"\n---\n'
        '- q: "Яка літера?"\n  o: ["мама", "тато", "книга"]\n  a: 0\n'
        ":::"
    )
    words = validate_exercise_vocab(content)
    assert "Яка" in words
    assert "літера" in words
    assert "мама" in words
    assert "тато" in words
    assert "книга" in words


def test_validate_exercise_vocab_ignores_non_exercise_text():
    content = (
        "## Розділ перший\n\nЦе звичайний текст поза вправою.\n\n"
        ':::quiz\ntitle: "Test"\n---\n'
        '- q: "привіт"\n  o: ["так", "ні"]\n  a: 0\n'
        ":::"
    )
    words = validate_exercise_vocab(content)
    # Words outside exercise blocks should NOT be extracted
    assert "Розділ" not in words
    assert "звичайний" not in words
    # Words inside should be
    assert "привіт" in words


def test_validate_exercise_vocab_preserves_apostrophe():
    content = (
        ':::fill-in\ntitle: "Test"\n---\n'
        "- sentence: \"Це пам'ятка\"\n"
        "  answer: \"пам'ятка\"\n"
        ":::"
    )
    words = validate_exercise_vocab(content)
    assert "пам'ятка" in words


# --- enrich_exercises_llm ---
