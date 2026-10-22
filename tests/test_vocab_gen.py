"""Tests for writer-driven словник generation (#1025).

Tests vocabulary extraction with real linguistic terms, ambiguous words,
expressions, and progression tracking — not just simple beginner words.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


# ── Test data: representative vocabulary challenges ──


class TestVesumEnrichment:
    """Test VESUM POS/gender enrichment of vocabulary."""

    def test_noun_gets_pos_and_gender(self, requires_vesum_db):
        from build.vocab_gen import vesum_enrich_entry

        entry = {"word": "мама", "translation": "mother", "expression": False}
        enriched = vesum_enrich_entry(entry)
        assert enriched["pos"] == "ім."
        assert enriched["gender"] == "ж."
        assert enriched["verified"] is True

    def test_expression_skips_vesum(self):
        from build.vocab_gen import vesum_enrich_entry

        entry = {"word": "Як справи?", "translation": "How are you?", "expression": True}
        enriched = vesum_enrich_entry(entry)
        assert enriched.get("pos", "") == ""
        assert enriched["verified"] is True  # expressions bypass VESUM check

    def test_unknown_word_flagged_unverified(self):
        """Words not in VESUM get verified=false (#1025 AC11)."""
        from build.vocab_gen import vesum_enrich_entry

        entry = {"word": "ґуґл", "translation": "Google", "expression": False}
        enriched = vesum_enrich_entry(entry)
        assert "word" in enriched  # didn't crash
        assert enriched["verified"] is False

    def test_stress_annotation_on_multisyllable(self):
        """Multi-syllable words get stress marks (#1025 AC10)."""
        from build.vocab_gen import vesum_enrich_entry

        entry = {"word": "літера", "translation": "letter", "expression": False}
        enriched = vesum_enrich_entry(entry)
        # літера has 3 syllables — should get stress mark
        assert "\u0301" in enriched["word"], (
            f"Expected stress mark in '{enriched['word']}'"
        )

    def test_single_syllable_no_stress(self):
        """Single-syllable words don't get stress marks."""
        from build.vocab_gen import vesum_enrich_entry

        entry = {"word": "звук", "translation": "sound", "expression": False}
        enriched = vesum_enrich_entry(entry)
        assert enriched["word"] == "звук"  # no stress mark on single syllable
