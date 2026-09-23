"""Synthetic regression test for apostrophe classification in resolver/tokenize.py (#8431)."""

from __future__ import annotations

from scripts.curriculum.resolver.tokenize import APOSTROPHES, _kind


def test_apostrophe_cyrillic_classification():
    """Verify that Cyrillic words containing any apostrophe from APOSTROPHES classify as cyrillic."""
    # Synthetic word from review finding 8
    test_word_base = "бз{apo}юк"

    for apo in sorted(APOSTROPHES):
        word = test_word_base.format(apo=apo)
        assert _kind(word) == "cyrillic", f"Expected cyrillic for {word!r} with apostrophe U+{ord(apo):04X}"

    # Also test common attested word м'ясо with each member of APOSTROPHES, especially U+02BC
    assert "\u02bc" in APOSTROPHES
    for apo in sorted(APOSTROPHES):
        word = f"м{apo}ясо"
        assert _kind(word) == "cyrillic", f"Expected cyrillic for {word!r} with apostrophe U+{ord(apo):04X}"

    # Negative case: U+02B9 (modifier letter prime) is not in APOSTROPHES and still classifies as mixed
    assert "\u02b9" not in APOSTROPHES
    assert _kind("м\u02b9ясо") == "mixed"
    assert _kind(test_word_base.format(apo="\u02b9")) == "mixed"


def test_apostrophe_without_letters_is_not_cyrillic():
    """A standalone apostrophe without Cyrillic letters does not classify as cyrillic."""
    for apo in sorted(APOSTROPHES):
        assert _kind(apo) != "cyrillic"
