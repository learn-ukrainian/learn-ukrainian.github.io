"""Tests for V6 exercise placeholder filler."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build.exercises.fill_placeholders import (
    _clean_text,
    fill_placeholders,
    validate_exercise_vocab,
)

# --- Parsing tests ---


# --- DSL generation with real content ---


# --- Integration tests ---


# --- Bug fix: _clean_text strips stray quotes (#996) ---


def test_clean_text_strips_leading_quote():
    assert _clean_text("'В") == "В"


def test_clean_text_preserves_internal_apostrophe():
    assert _clean_text("пам'ятка") == "пам'ятка"


# --- _escape_yaml_str with _clean_text ---


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
