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

    def test_preserves_mix_across_multiple_tokens(self):
        text = "білий жовтий блакитний тризуб Україна"
        tokens = _tokenize(text)
        assert "білий" in tokens
        assert "жовтий" in tokens
        assert "блакитний" in tokens
        assert "україна" in tokens

    def test_canonical_flag_terms_survive(self):
        """Direct regression for the #1431 / a1/colors failure mode:
        the wiki compressor extracted `білии`/`жовтии`/`блакитнии` as
        factual anchors, no writer could possibly produce those (since
        they're not Ukrainian), compliance always failed."""
        # Simulate what the wiki body would say.
        article = "Наш прапор синьо-жовтий. Базові кольори: білий, чорний, червоний, жовтий, зелений, синій, блакитний."
        tokens = _tokenize(article)
        # Every real anchor the writer will output.
        for expected in ("білий", "чорний", "червоний", "жовтий", "зелений", "синій", "блакитний"):
            assert expected in tokens, f"Ukrainian adjective {expected!r} corrupted during tokenize: got {sorted(tokens)}"


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

    def test_strips_acute_on_multiple_words(self):
        text = "ка́ва мо́локо хлíб"
        tokens = _tokenize(text)
        assert "кава" in tokens
        assert "молоко" in tokens


class TestTokenizeStopwordsAndLength:
    """Behaviour not related to the bug — sanity that pre-existing
    filters still work after the tokenizer change."""

    def test_drops_short_tokens(self):
        tokens = _tokenize("до на за при і та")
        # All these are < 4 chars → get dropped by the `len > 2` filter.
        # "при" is 3 chars (length > 2), so it stays unless it's a stopword.
        assert "до" not in tokens
        assert "на" not in tokens
        assert "за" not in tokens

    def test_lowercases(self):
        tokens = _tokenize("Україна БІЛИЙ жовтий")
        for t in tokens:
            assert t == t.lower()


class TestTokenizeIdempotent:
    def test_tokenize_twice_gives_same_result(self):
        text = "білий жовтий блакитний"
        t1 = _tokenize(text)
        t2 = _tokenize(text)
        assert t1 == t2
