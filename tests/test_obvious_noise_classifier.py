from __future__ import annotations

import pytest

from scripts.lexicon.obvious_noise_classifier import (
    classify_lemma,
    is_bare_number,
    is_interjection_onomatopoeia,
    is_latin_script,
    is_markup_debris,
    is_punctuation_debris,
    is_single_letter,
)


@pytest.mark.parametrize(
    "lemma, expected",
    [
        ("ааа", True),
        ("бах", True),
        ("ку-ку", True),
        ("п-п-п-п", True),
        ("і-і-і", True),
        ("кіт", False),
        ("аби-як", False),
        ("аа", False),
    ],
)
def test_is_interjection_onomatopoeia(lemma: str, expected: bool) -> None:
    assert is_interjection_onomatopoeia(lemma) == expected


@pytest.mark.parametrize(
    "lemma, expected",
    [
        ("123", True),
        ("2026", True),
        ("1,000", True),
        ("1-2", True),
        ("123a", False),
        ("перший", False),
        ("1. урок", False),
    ],
)
def test_is_bare_number(lemma: str, expected: bool) -> None:
    assert is_bare_number(lemma) == expected


@pytest.mark.parametrize(
    "lemma, expected",
    [
        ("д", True),
        ("и", True),
        ("к", True),
        ("a", True),
        ("кіт", False),
        ("1", False),
        ("-", False),
    ],
)
def test_is_single_letter(lemma: str, expected: bool) -> None:
    assert is_single_letter(lemma) == expected


@pytest.mark.parametrize(
    "lemma, expected",
    [
        ("{{word}}", True),
        ("<br>", True),
        ("[link]", True),
        ("*bold*", True),
        ("%s", True),
        ("кіт", False),
        ("аби-як", False),
    ],
)
def test_is_markup_debris(lemma: str, expected: bool) -> None:
    assert is_markup_debris(lemma) == expected


@pytest.mark.parametrize(
    "lemma, expected",
    [
        ("Present", True),
        ("hello", True),
        ("word", True),
        ("cat-dog", True),
        ("кіт", False),
        ("Presentкіт", False),
        ("123", False),
    ],
)
def test_is_latin_script(lemma: str, expected: bool) -> None:
    assert is_latin_script(lemma) == expected


@pytest.mark.parametrize(
    "lemma, expected",
    [
        ("...", True),
        ("!!!", True),
        ("---", True),
        ("?", True),
        ("_", True),
        ("аби-як", False),
        ("123", False),
        ("кіт", False),
    ],
)
def test_is_punctuation_debris(lemma: str, expected: bool) -> None:
    assert is_punctuation_debris(lemma) == expected


@pytest.mark.parametrize(
    "lemma, expected",
    [
        ("ааа", "interjection_onomatopoeia"),
        ("123", "bare_number"),
        ("д", "single_letter"),
        ("<br>", "markup_debris"),
        ("Present", "latin_script"),
        ("...", "punctuation_debris"),
        ("кіт", None),
    ],
)
def test_classify_lemma(lemma: str, expected: str | None) -> None:
    assert classify_lemma(lemma) == expected
