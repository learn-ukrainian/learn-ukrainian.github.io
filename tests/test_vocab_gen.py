"""Tests for writer-driven словник generation (#1025).

Tests vocabulary extraction with real linguistic terms, ambiguous words,
expressions, and progression tracking — not just simple beginner words.
"""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


# ── Test data: representative vocabulary challenges ──


SAMPLE_A1_PHONETICS_VOCAB = """
vocabulary:
  - word: "звук"
    translation: "sound"
    expression: false
  - word: "літера"
    translation: "letter"
    expression: false
  - word: "голосний"
    translation: "vowel"
    expression: false
  - word: "приголосний"
    translation: "consonant"
    expression: false
  - word: "наголос"
    translation: "stress (accent)"
    expression: false
  - word: "склад"
    translation: "syllable"
    expression: false
  - word: "Як справи?"
    translation: "How are you?"
    expression: true
  - word: "Рада тебе бачити!"
    translation: "Nice to see you! (said by a woman)"
    expression: true
"""

SAMPLE_B1_GRAMMAR_VOCAB = """
vocabulary:
  - word: "іменник"
    translation: "noun"
    expression: false
  - word: "дієслово"
    translation: "verb"
    expression: false
  - word: "прикметник"
    translation: "adjective"
    expression: false
  - word: "відмінок"
    translation: "grammatical case"
    expression: false
  - word: "дієприкметник"
    translation: "participle"
    expression: false
  - word: "дієприслівник"
    translation: "gerund (adverbial participle)"
    expression: false
  - word: "складнопідрядне речення"
    translation: "subordinate clause"
    expression: true
"""

SAMPLE_AMBIGUOUS_VOCAB = """
vocabulary:
  - word: "рада"
    translation: "glad"
    expression: false
  - word: "ніс"
    translation: "nose"
    expression: false
  - word: "коса"
    translation: "braid"
    expression: false
  - word: "замок"
    translation: "castle"
    expression: false
"""


class TestVocabYamlFormat:
    """Test that vocabulary YAML has correct structure."""

    def test_a1_phonetics_parses(self):
        data = yaml.safe_load(SAMPLE_A1_PHONETICS_VOCAB)
        assert "vocabulary" in data
        assert len(data["vocabulary"]) == 8

    def test_entries_have_required_fields(self):
        data = yaml.safe_load(SAMPLE_A1_PHONETICS_VOCAB)
        for entry in data["vocabulary"]:
            assert "word" in entry, f"Missing 'word' in {entry}"
            assert "translation" in entry, f"Missing 'translation' in {entry}"
            assert "expression" in entry, f"Missing 'expression' in {entry}"

    def test_expressions_flagged(self):
        data = yaml.safe_load(SAMPLE_A1_PHONETICS_VOCAB)
        expressions = [e for e in data["vocabulary"] if e["expression"]]
        single_words = [e for e in data["vocabulary"] if not e["expression"]]
        assert len(expressions) == 2
        assert len(single_words) == 6

    def test_b1_grammar_terms(self):
        data = yaml.safe_load(SAMPLE_B1_GRAMMAR_VOCAB)
        words = {e["word"]: e["translation"] for e in data["vocabulary"]}
        assert words["іменник"] == "noun"
        assert words["дієслово"] == "verb"
        assert words["дієприкметник"] == "participle"

    def test_ambiguous_words_context(self):
        data = yaml.safe_load(SAMPLE_AMBIGUOUS_VOCAB)
        words = {e["word"]: e["translation"] for e in data["vocabulary"]}
        # These depend on context — the writer must provide the RIGHT meaning
        assert words["рада"] == "glad"  # not "council"
        assert words["ніс"] == "nose"  # not "carried"


class TestDeduplication:
    """Test vocabulary deduplication across modules."""

    def test_dedupe_removes_known_words(self):
        from build.vocab_gen import dedupe_vocab

        # M01 taught these
        previous = {"мама", "тато", "привіт", "як справи"}

        # M02 vocab includes some M01 words
        current = yaml.safe_load("""
vocabulary:
  - word: "мама"
    translation: "mother"
    expression: false
  - word: "брат"
    translation: "brother"
    expression: false
  - word: "сестра"
    translation: "sister"
    expression: false
  - word: "привіт"
    translation: "hi"
    expression: false
""")["vocabulary"]

        result = dedupe_vocab(current, previous)
        words = [e["word"] for e in result]
        assert "мама" not in words  # already taught
        assert "привіт" not in words  # already taught
        assert "брат" in words  # new
        assert "сестра" in words  # new

    def test_dedupe_empty_previous(self):
        from build.vocab_gen import dedupe_vocab

        current = [{"word": "мама", "translation": "mother", "expression": False}]
        result = dedupe_vocab(current, set())
        assert len(result) == 1

    def test_dedupe_case_insensitive(self):
        from build.vocab_gen import dedupe_vocab

        previous = {"привіт"}
        current = [{"word": "Привіт", "translation": "hi", "expression": False}]
        result = dedupe_vocab(current, previous)
        assert len(result) == 0  # Привіт matches привіт


class TestVesumEnrichment:
    """Test VESUM POS/gender enrichment of vocabulary."""

    def test_noun_gets_pos_and_gender(self):
        from build.vocab_gen import vesum_enrich_entry

        entry = {"word": "мама", "translation": "mother", "expression": False}
        enriched = vesum_enrich_entry(entry)
        assert enriched["pos"] == "ім."
        assert enriched["gender"] == "ж."

    def test_verb_gets_pos(self):
        from build.vocab_gen import vesum_enrich_entry

        entry = {"word": "читати", "translation": "to read", "expression": False}
        enriched = vesum_enrich_entry(entry)
        assert enriched["pos"] == "дієсл."

    def test_expression_skips_vesum(self):
        from build.vocab_gen import vesum_enrich_entry

        entry = {"word": "Як справи?", "translation": "How are you?", "expression": True}
        enriched = vesum_enrich_entry(entry)
        assert enriched.get("pos", "") == ""

    def test_unknown_word_no_crash(self):
        from build.vocab_gen import vesum_enrich_entry

        entry = {"word": "ґуґл", "translation": "Google", "expression": False}
        enriched = vesum_enrich_entry(entry)
        assert "word" in enriched  # didn't crash
