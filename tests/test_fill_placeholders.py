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


def test_parse_placeholder_with_questions():
    block = """type: match-up
tests: false friends
questions: В→v, Н→n, Р→r"""
    result = _parse_placeholder(block)
    assert result.questions == "В→v, Н→n, Р→r"


def test_parse_placeholder_with_groups():
    block = """type: group-sort
tests: classify
groups: Голосні: А, О, У; Приголосні: М, К, Б"""
    result = _parse_placeholder(block)
    assert result.groups == "Голосні: А, О, У; Приголосні: М, К, Б"


def test_parse_qa_pairs_arrow():
    pairs = _parse_qa_pairs("В→v, Н→n, Р→rolled r")
    assert len(pairs) == 3
    assert pairs[0] == ("В", "v")
    assert pairs[2] == ("Р", "rolled r")


def test_parse_qa_pairs_equals():
    pairs = _parse_qa_pairs("стіл=він, книга=вона, вікно=воно")
    assert len(pairs) == 3
    assert pairs[1] == ("книга", "вона")


def test_parse_qa_pairs_empty():
    assert _parse_qa_pairs("") == []
    assert _parse_qa_pairs("no separators here") == []


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


def test_generate_unknown_type():
    placeholder = ExercisePlaceholder(
        exercise_type="mystery-type",
        tests="test",
        items=3,
    )
    dsl = _generate_exercise_dsl(placeholder)
    assert "<!-- EXERCISE:" in dsl


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


def test_fill_placeholders_multiple():
    content = """## Section 1

:::exercise-placeholder
type: group-sort
tests: classify
items: 4
groups: Vowels: а, о; Consonants: м, к
:::

## Section 2

:::exercise-placeholder
type: match-up
tests: match pairs
items: 2
questions: мама→mother, тато→father
:::
"""
    result, count = fill_placeholders(content)
    assert count == 2
    assert ":::group-sort" in result
    assert ":::match-up" in result
    assert ":::exercise-placeholder" not in result
    assert '"mother"' in result  # Real content, not "?"


def test_fill_placeholders_none():
    content = "## Section 1\n\nNo exercises here.\n"
    result, count = fill_placeholders(content)
    assert count == 0
    assert result == content


def test_no_question_marks_in_real_content():
    """Exercises with explicit Q&A should never produce '?' placeholders."""
    content = """:::exercise-placeholder
type: match-up
tests: sounds
items: 3
questions: В→v, Н→n, Р→r
:::"""
    result, _ = fill_placeholders(content)
    assert '"?"' not in result


# --- Bug fix: _clean_text strips stray quotes (#996) ---


def test_clean_text_strips_leading_quote():
    assert _clean_text("'В") == "В"


def test_clean_text_strips_trailing_quote():
    assert _clean_text("зву́ки'") == "зву́ки"


def test_clean_text_strips_both_quotes():
    assert _clean_text("'мама'") == "мама"


def test_clean_text_strips_whitespace_and_quotes():
    assert _clean_text("  'hello'  ") == "hello"


def test_clean_text_preserves_internal_apostrophe():
    assert _clean_text("пам'ятка") == "пам'ятка"


def test_clean_text_empty():
    assert _clean_text("") == ""


def test_clean_text_only_quotes():
    assert _clean_text("''") == ""


# --- _escape_yaml_str with _clean_text ---


def test_escape_yaml_str_cleans_stray_quotes():
    assert _escape_yaml_str("'В") == "В"


def test_escape_yaml_str_clean_and_escape():
    assert _escape_yaml_str("""'say "hi"'""") == "say 'hi'"


# --- Vocabulary parsing strips stray quotes ---


def test_parse_vocab_strips_stray_quotes():
    block = "type: quiz\nvocabulary: 'В, зву́ки', мама"
    ph = _parse_placeholder(block)
    assert ph.vocabulary == ["В", "зву́ки", "мама"]


def test_parse_vocab_preserves_internal_apostrophe():
    block = "type: quiz\nvocabulary: пам'ятка, об'єкт"
    ph = _parse_placeholder(block)
    assert ph.vocabulary == ["пам'ятка", "об'єкт"]


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


def test_fill_in_vocab_with_translation():
    content = (
        ":::exercise-placeholder\n"
        "type: fill-in\n"
        "tests: practice\n"
        "vocabulary: мама (mother), тато (father)\n"
        ":::"
    )
    result, count = fill_placeholders(content)
    assert count == 1
    assert "mother" in result
    assert "father" in result
    assert 'answer: "мама"' in result
    assert 'answer: "тато"' in result


def test_fill_in_qa_pairs_take_precedence():
    content = (
        ":::exercise-placeholder\n"
        "type: fill-in\n"
        "tests: practice\n"
        "questions: ___ каже мама→мама\n"
        "vocabulary: тато\n"
        ":::"
    )
    result, count = fill_placeholders(content)
    assert count == 1
    assert "___ каже мама" in result
    assert 'answer: "мама"' in result


# --- TODO removal: fallback exercises produce valid DSL ---


def test_quiz_fallback_no_todo():
    content = ":::exercise-placeholder\ntype: quiz\ntests: test\n:::"
    result, _ = fill_placeholders(content)
    assert "TODO" not in result
    assert '- q: "No vocabulary provided"' in result


def test_fill_in_fallback_no_todo():
    content = ":::exercise-placeholder\ntype: fill-in\ntests: test\n:::"
    result, _ = fill_placeholders(content)
    assert "TODO" not in result
    assert '- sentence: "No vocabulary provided"' in result


def test_match_up_fallback_no_todo():
    content = ":::exercise-placeholder\ntype: match-up\ntests: test\n:::"
    result, _ = fill_placeholders(content)
    assert "TODO" not in result
    assert '- left: "—"' in result


def test_group_sort_fallback_no_todo():
    content = ":::exercise-placeholder\ntype: group-sort\ntests: test\n:::"
    result, _ = fill_placeholders(content)
    assert "TODO" not in result
    assert 'name: "—"' in result


def test_true_false_fallback_no_todo():
    content = ":::exercise-placeholder\ntype: true-false\ntests: test\n:::"
    result, _ = fill_placeholders(content)
    assert "TODO" not in result
    assert '- statement: "No content provided"' in result


# --- Stray quotes end-to-end ---


def test_stray_quotes_stripped_from_quiz_output():
    content = (
        ":::exercise-placeholder\n"
        "type: quiz\n"
        "tests: letter sounds\n"
        "vocabulary: 'В, зву́ки'\n"
        ":::"
    )
    result, count = fill_placeholders(content)
    assert count == 1
    assert "\"'В\"" not in result
    assert "\"зву́ки'\"" not in result
    assert '"В"' in result
    assert '"зву́ки"' in result
