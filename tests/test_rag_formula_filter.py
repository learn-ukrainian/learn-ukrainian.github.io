"""Tests for RAG batch verify formula filtering.

Ensures blending formulas (e.g. 'М + А + М + А → МАМА') are excluded
from word extraction so pedagogical syllables don't fail VESUM.
"""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from rag.rag_batch_verify import extract_words_from_yaml, tokenize_all_ukrainian


@pytest.fixture
def yaml_file(tmp_path):
    """Helper to create a temp YAML file from data."""
    def _make(data, name="test.yaml"):
        path = tmp_path / name
        path.write_text(yaml.dump(data, allow_unicode=True), "utf-8")
        return path
    return _make


class TestFormulaFiltering:

    def test_blending_formula_excluded(self, yaml_file):
        """Syllables in 'М + О + Л + О + К + О → ___' should not be extracted."""
        data = [
            {
                "type": "fill-in",
                "title": "Blend Letters",
                "items": [
                    {
                        "sentence": "М + О + Л + О + К + О → ___",
                        "answer": "МОЛОКО",
                        "options": ["МОЛОКО", "МІСТО", "МАСЛО"],
                    }
                ],
            }
        ]
        path = yaml_file(data)
        words = extract_words_from_yaml(path, is_vocab=False)
        # МОЛОКО, МІСТО, МАСЛО should be extracted (from answer/options)
        assert "молоко" in words
        # ЛО should NOT be extracted (it's in the formula sentence)
        assert "ло" not in words

    def test_arrow_formula_excluded(self, yaml_file):
        """Strings with → are filtered out entirely."""
        data = [
            {
                "type": "fill-in",
                "items": [
                    {"sentence": "К + І + Т → ___", "answer": "КІТ"},
                ],
            }
        ]
        path = yaml_file(data)
        words = extract_words_from_yaml(path, is_vocab=False)
        assert "кіт" in words
        # КІ should not be present (from formula)
        assert "кі" not in words

    def test_normal_sentences_not_filtered(self, yaml_file):
        """Regular activity strings without formulas are kept."""
        data = [
            {
                "type": "quiz",
                "title": "Тест",
                "items": [
                    {"question": "Що означає кіт?", "answer": "cat"},
                ],
            }
        ]
        path = yaml_file(data)
        words = extract_words_from_yaml(path, is_vocab=False)
        assert "кіт" in words
        assert "означає" in words
        assert "тест" in words

    def test_real_words_with_two_chars_kept(self, yaml_file):
        """Two-letter words like ні, до, на are NOT filtered."""
        data = [
            {
                "type": "true-false",
                "items": [
                    {"statement": "Ні, це не так"},
                ],
            }
        ]
        path = yaml_file(data)
        words = extract_words_from_yaml(path, is_vocab=False)
        assert "ні" in words
        assert "це" in words
        assert "не" in words

    def test_apostrophe_variants_normalized(self):
        """Curly apostrophes should stay inside one Ukrainian token."""
        tokens = tokenize_all_ukrainian("Це обов’язок і зобовʼязання.")
        clean_forms = [clean for _, clean in tokens]
        assert "обов'язок" in clean_forms
        assert "зобов'язання" in clean_forms

    def test_false_true_false_statement_skipped_but_explanation_kept(self, yaml_file):
        """Intentionally wrong true/false statements should not poison VESUM verify."""
        data = [
            {
                "type": "true-false",
                "title": "Перевірка",
                "items": [
                    {
                        "statement": "Ти мушиш спати.",
                        "correct": False,
                        "explanation": "Правильно: ти мусиш спати.",
                    },
                    {
                        "statement": "Я мушу працювати.",
                        "correct": True,
                        "explanation": "Це правильна форма.",
                    },
                ],
            }
        ]
        path = yaml_file(data)
        words = extract_words_from_yaml(path, is_vocab=False)
        assert "мушиш" not in words
        assert "мусиш" in words
        assert "мушу" in words

    def test_vocab_file_unaffected(self, yaml_file):
        """Vocab extraction (is_vocab=True) is unaffected by formula filter."""
        data = [
            {"lemma": "молоко", "translation": "milk"},
            {"lemma": "ні", "translation": "no"},
        ]
        path = yaml_file(data)
        words = extract_words_from_yaml(path, is_vocab=True)
        assert "молоко" in words
        assert "ні" in words
