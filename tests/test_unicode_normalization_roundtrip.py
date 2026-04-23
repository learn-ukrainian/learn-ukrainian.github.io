"""Round-trip invariants for Ukrainian text-processing helpers (#1487).

NFKD / NFD normalization without NFC recompose corrupts й (U+0438 U+0306)
and ї (U+0456 U+0308) — see issue #1487 for the full postmortem.
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


@pytest.mark.parametrize("word", ["мій", "їжа", "йому", "її", "мої", "українська"])
def test_wiki_context_normalize_preserves_cyrillic(word: str) -> None:
    from wiki.context import _normalize_text

    result = _normalize_text(word)
    assert "и" + chr(0x306) not in result
    assert "і" + chr(0x308) not in result
    for bad_form in ("міи", "іжа", "иому"):
        assert bad_form not in result, f"Cyrillic corruption: {word!r} -> {result!r}"


@pytest.mark.parametrize("word", ["мій", "їжа", "йому", "мо\u0301й"])
def test_plan_adherence_strip_stress_roundtrip(word: str) -> None:
    from audit.checks.plan_adherence import _strip_stress

    result = _strip_stress(word)
    assert "\u0301" not in result
    assert result == unicodedata.normalize("NFC", result)


@pytest.mark.parametrize("word", ["мій", "їжа", "йому"])
def test_grammar_strip_stress_roundtrip(word: str) -> None:
    from audit.checks.grammar import _strip_stress

    result = _strip_stress(word)
    assert "\u0301" not in result
    assert result == unicodedata.normalize("NFC", result)


def test_tokenize_all_ukrainian_preserves_original_bytes() -> None:
    from rag.rag_batch_verify import tokenize_all_ukrainian

    text = "бу\u0301кви мій її"
    tokens = tokenize_all_ukrainian(text)

    for original, _clean in tokens:
        assert original in text, (
            f"Token original {original!r} not a substring of input; "
            f"stressed bytes were lost during tokenization."
        )
