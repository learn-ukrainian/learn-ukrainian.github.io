"""Regression tests for scripts/build/phases/wiki_compressor.py::_tokenize.

Ensures Ukrainian-specific Cyrillic letters (й, ї, Й, Ї) survive NFKD
normalization cleanly. Before this fix, _tokenize was silently
corrupting every token containing й or ї into forms that don't exist
in Ukrainian (білий → білии, країна → краина, жовтий → жовтии), which
broke contract-compliance matching — Opus would correctly write
`білий` in a module, but the contract-compliance check required the
tokenizer-corrupted form `білии`, so compliance always failed.

Scope: reduces the surface to the tokenizer itself. A later PR should
add a higher-level contract-compliance regression test that builds a
real plan + content pair and verifies TEACHING_BEATS / FACTUAL_ANCHOR
don't fire on correctly-spelled Ukrainian vocabulary.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.phases.wiki_compressor import _tokenize


class TestTokenizePreservesCyrillicLetters:
    """The bug: й/ї decompose under NFKD into base + combining mark.
    The old tokenizer stripped all combining marks, corrupting the letter.
    """

    def test_preserves_й_lowercase(self):
        tokens = _tokenize("білий")
        assert "білий" in tokens
        assert "білии" not in tokens  # the buggy output we're preventing

    def test_preserves_ї(self):
        tokens = _tokenize("країна")
        assert "країна" in tokens
        assert "краина" not in tokens

    def test_preserves_Й_uppercase(self):
        # Uppercase Й (U+0419) is also a separate codepoint that decomposes.
        # Since the tokenizer lowercases, assertion is on the lowercase form.
        tokens = _tokenize("ЙОРКШИР")
        assert "йоркшир" in tokens


class TestTokenizeStripsStressMarks:
    """NFKD + combining-strip was the original intent for stress removal
    in Ukrainian textbook content where acute marks flag stress. Those
    marks must still be stripped; only the Cyrillic-LETTER combiners
    (short-stroke U+0306, diaeresis U+0308) need to survive.
    """

    def test_strips_acute_stress_mark_on_vowel(self):
        # "ка́ртопля" — cyrillic а + combining acute U+0301
        text = "ка́ртопля"
        tokens = _tokenize(text)
        assert "картопля" in tokens
