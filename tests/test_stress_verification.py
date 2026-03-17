"""Tests for stress_verification.py (#961, #969 AC1)."""

import pytest

from scripts.audit.checks.stress_verification import (
    STRESS_MARK,
    _extract_stressed_words,
    _strip_stress,
    verify_stress_marks,
)


class TestStripStress:
    def test_removes_combining_accent(self):
        assert _strip_stress(f"яйце{STRESS_MARK}") == "яйце"

    def test_no_stress_unchanged(self):
        assert _strip_stress("молоко") == "молоко"

    def test_multiple_marks(self):
        # Shouldn't happen, but handle gracefully
        assert _strip_stress(f"мо{STRESS_MARK}локо{STRESS_MARK}") == "молоко"


class TestExtractStressedWords:
    def test_finds_stressed_words(self):
        text = f"Це моє се{STRESS_MARK}ло і мо{STRESS_MARK}ва."
        words = _extract_stressed_words(text)
        bare_words = [_strip_stress(w) for w, _ in words]
        assert "село" in bare_words
        assert "мова" in bare_words

    def test_skips_strikethrough(self):
        text = f"~~не{STRESS_MARK}правильно~~ пра{STRESS_MARK}вильно"
        words = _extract_stressed_words(text)
        bare = [_strip_stress(w) for w, _ in words]
        assert "неправильно" not in bare
        assert "правильно" in bare

    def test_skips_syllable_fragments(self):
        text = f"мо-ло-ко{STRESS_MARK} has three syllables"
        words = _extract_stressed_words(text)
        # The word inside a syllable pattern should be skipped
        # but standalone молоко́ should be found
        # Here the stress is on the last fragment which is part of hyphenated pattern
        # This tests that the pattern detection works
        assert len(words) == 0 or all(
            "-" not in _strip_stress(w) for w, _ in words
        )

    def test_skips_single_char(self):
        text = f"а{STRESS_MARK} — це буква"
        words = _extract_stressed_words(text)
        assert len(words) == 0

    def test_line_numbers(self):
        text = f"line one\nline two моло{STRESS_MARK}ко\nline three"
        words = _extract_stressed_words(text)
        assert len(words) == 1
        assert words[0][1] == 2  # line 2


class TestVerifyStressMarks:
    """Integration tests — require ukrainian-word-stress + Stanza model."""

    @pytest.fixture(autouse=True)
    def _check_stressifier(self):
        """Skip if ukrainian-word-stress is not installed."""
        try:
            import ukrainian_word_stress  # noqa: F401
        except ImportError:
            pytest.skip("ukrainian-word-stress not installed")

    def test_correct_stress_no_issues(self):
        # молоко́ is correct
        text = f"Це молоко{STRESS_MARK}."
        issues = verify_stress_marks(text)
        stress_mismatches = [i for i in issues if i["type"] == "STRESS_MISMATCH"]
        assert len(stress_mismatches) == 0

    def test_wrong_stress_detected(self):
        # мо́локо is wrong (should be молоко́)
        text = f"Це мо{STRESS_MARK}локо."
        issues = verify_stress_marks(text)
        stress_mismatches = [i for i in issues if i["type"] == "STRESS_MISMATCH"]
        assert len(stress_mismatches) == 1
        assert "молоко" in stress_mismatches[0]["text"].lower()

    def test_reversed_stress_yajce(self):
        # я́йце is wrong (should be яйце́)
        text = f"Це я{STRESS_MARK}йце."
        issues = verify_stress_marks(text)
        stress_mismatches = [i for i in issues if i["type"] == "STRESS_MISMATCH"]
        assert len(stress_mismatches) == 1

    def test_monosyllabic_no_issue(self):
        # кіт has one syllable — stress mark optional, no mismatch
        text = f"Мій кі{STRESS_MARK}т."
        issues = verify_stress_marks(text)
        stress_mismatches = [i for i in issues if i["type"] == "STRESS_MISMATCH"]
        assert len(stress_mismatches) == 0

    def test_empty_text(self):
        assert verify_stress_marks("") == []

    def test_no_stressed_words(self):
        assert verify_stress_marks("This is English text only.") == []
