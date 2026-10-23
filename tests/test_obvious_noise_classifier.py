from __future__ import annotations

import pytest

from scripts.lexicon.obvious_noise_classifier import (
    classify_lemma,
)


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
