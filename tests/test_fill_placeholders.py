"""Tests for V6 exercise placeholder filler."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build.exercises.fill_placeholders import (
    ExercisePlaceholder,
    _generate_exercise_dsl,
    _parse_placeholder,
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


def test_parse_placeholder_defaults():
    block = "type: fill-in"
    result = _parse_placeholder(block)
    assert result.exercise_type == "fill-in"
    assert result.items == 4  # default
    assert result.vocabulary == []


def test_parse_placeholder_bad_items():
    block = "type: quiz\nitems: abc"
    result = _parse_placeholder(block)
    assert result.items == 4  # fallback


# --- DSL generation tests ---


def test_generate_quiz():
    placeholder = ExercisePlaceholder(
        exercise_type="quiz",
        tests="choose the right form",
        vocabulary=["стіл", "книга"],
        items=3,
    )
    dsl = _generate_exercise_dsl(placeholder)
    assert ":::quiz" in dsl
    assert 'title: "Choose the right form"' in dsl
    assert '"стіл"' in dsl
    assert '"книга"' in dsl
    assert dsl.endswith(":::")


def test_generate_fill_in():
    placeholder = ExercisePlaceholder(
        exercise_type="fill-in",
        tests="add the correct ending",
        vocabulary=["мам", "книг"],
        items=2,
    )
    dsl = _generate_exercise_dsl(placeholder)
    assert ":::fill-in" in dsl
    assert "answer:" in dsl


def test_generate_match_up():
    placeholder = ExercisePlaceholder(
        exercise_type="match-up",
        tests="match opposites",
        vocabulary=["великий", "маленький"],
        items=2,
    )
    dsl = _generate_exercise_dsl(placeholder)
    assert ":::match-up" in dsl
    assert '"великий"' in dsl


def test_generate_group_sort():
    placeholder = ExercisePlaceholder(
        exercise_type="group-sort",
        tests="sort by gender",
        vocabulary=["стіл", "книга", "вікно", "ліжко"],
        items=4,
    )
    dsl = _generate_exercise_dsl(placeholder)
    assert ":::group-sort" in dsl
    assert "groups:" in dsl


def test_generate_unknown_type():
    placeholder = ExercisePlaceholder(
        exercise_type="mystery-type",
        tests="test",
        items=3,
    )
    dsl = _generate_exercise_dsl(placeholder)
    assert "<!-- EXERCISE:" in dsl
    assert "mystery-type" in dsl


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
type: quiz
tests: test 1
items: 2
vocabulary: а, о
:::

## Section 2

:::exercise-placeholder
type: fill-in
tests: test 2
items: 3
vocabulary: мама, тато, брат
:::
"""
    result, count = fill_placeholders(content)
    assert count == 2
    assert ":::quiz" in result
    assert ":::fill-in" in result
    assert ":::exercise-placeholder" not in result


def test_fill_placeholders_none():
    content = "## Section 1\n\nNo exercises here.\n"
    result, count = fill_placeholders(content)
    assert count == 0
    assert result == content


def test_fill_preserves_surrounding_content():
    content = """Before exercise.

:::exercise-placeholder
type: match-up
tests: matching
items: 2
vocabulary: один, два
:::

After exercise."""
    result, count = fill_placeholders(content)
    assert count == 1
    assert "Before exercise." in result
    assert "After exercise." in result
