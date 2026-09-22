"""Synthetic regression test for apostrophe classification in resolver/tokenize.py (#8431)."""

from __future__ import annotations

from scripts.curriculum.resolver.tokenize import APOSTROPHES, _kind


def test_apostrophe_cyrillic_classification():
    """Verify that Cyrillic words containing any apostrophe from APOSTROPHES classify as cyrillic."""
    # Synthetic word from review finding 8
    test_word_base = "бз{apo}юк"

    for apo in APOSTROPHES:
        word = test_word_base.format(apo=apo)
        assert _kind(word) == "cyrillic", f"Expected cyrillic for {word!r} with apostrophe U+{ord(apo):04X}"

    # Also test common attested word м'ясо with different apostrophes
    for apo in (
        "\u02bc",  # modifier letter apostrophe ʼ (category Lm)
        "\u2019",  # right single quotation mark ’ (category Pf)
        "\u0027",  # apostrophe ' (category Po)
        "\u02b9",  # modifier letter prime ʹ (category Lm)
    ):
        word = f"м{apo}ясо"
        assert _kind(word) == "cyrillic", f"Expected cyrillic for {word!r} with apostrophe U+{ord(apo):04X}"


def test_apostrophe_without_letters_is_not_cyrillic():
    """A standalone apostrophe without Cyrillic letters does not classify as cyrillic."""
    for apo in APOSTROPHES:
        assert _kind(apo) != "cyrillic"
