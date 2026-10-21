"""Tests for learner state manifest generation."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

pytestmark = pytest.mark.reads_content

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pipeline.learner_state import (
    _load_vocab,
    _parse_vocab_hint_lemma,
    build_learner_state,
)


class TestPlannedVocabulary:
    """Planned vocab fills learner-state gaps before modules are built."""

    def test_parse_vocab_hint_lemma_basic(self):
        assert _parse_vocab_hint_lemma("готовий (ready, adj m)") == "готовий"
        assert _parse_vocab_hint_lemma("синку (son — vocative, from син)") == "синку"
        assert _parse_vocab_hint_lemma("вітаю (congratulations — chunk)") == "вітаю"
        assert _parse_vocab_hint_lemma("") is None

    def test_load_vocab_falls_back_to_planned(self, tmp_path):
        root = tmp_path / "curriculum" / "l2-uk-en"
        plans_dir = root / "plans" / "test"
        plans_dir.mkdir(parents=True)
        (plans_dir / "plan-only.yaml").write_text(yaml.dump({
            "vocabulary_hints": {
                "required": [
                    "готовий (ready, adj m)",
                    "синку (son — vocative, from син)",
                ],
                "recommended": ["вітаю (congratulations — chunk)"],
            }
        }, allow_unicode=True))

        with patch("pipeline.learner_state.CURRICULUM_ROOT", root):
            lemmas = _load_vocab("test", "plan-only")

        assert lemmas == ["готовий", "синку", "вітаю"]

    def test_load_vocab_prefers_built_when_present(self, tmp_path):
        root = tmp_path / "curriculum" / "l2-uk-en"

        plans_dir = root / "plans" / "test"
        plans_dir.mkdir(parents=True)
        (plans_dir / "sample.yaml").write_text(yaml.dump({
            "vocabulary_hints": {
                "required": ["плановий (planned)"],
                "recommended": ["запасний (backup)"],
            }
        }, allow_unicode=True))

        built_dir = root / "test" / "sample"
        built_dir.mkdir(parents=True)
        (built_dir / "vocabulary.yaml").write_text(yaml.dump({
            "items": [
                {"lemma": "готовий", "translation": "ready"},
                {"lemma": "вітаю", "translation": "congratulations"},
            ]
        }, allow_unicode=True))

        with patch("pipeline.learner_state.CURRICULUM_ROOT", root):
            lemmas = _load_vocab("test", "sample")

        assert lemmas == ["готовий", "вітаю"]


class TestBuildLearnerState:
    """build_learner_state collects cumulative vocab + grammar."""

    def test_collects_vocab_from_previous(self, tmp_path):
        # Set up a mini curriculum
        curriculum = {
            "levels": {
                "test": {
                    "modules": ["mod-1", "mod-2", "mod-3"]
                }
            }
        }
        root = tmp_path / "curriculum" / "l2-uk-en"

        # curriculum.yaml
        (root).mkdir(parents=True)
        (root / "curriculum.yaml").write_text(yaml.dump(curriculum, allow_unicode=True))

        # Vocab for mod-1
        vocab_dir = root / "test"
        (vocab_dir / "mod-1").mkdir(parents=True)
        (vocab_dir / "mod-1" / "vocabulary.yaml").write_text(yaml.dump({
            "items": [
                {"lemma": "кіт", "translation": "cat", "pos": "noun"},
                {"lemma": "мама", "translation": "mom", "pos": "noun"},
            ]
        }, allow_unicode=True))

        # Vocab for mod-2
        (vocab_dir / "mod-2").mkdir(parents=True)
        (vocab_dir / "mod-2" / "vocabulary.yaml").write_text(yaml.dump({
            "items": [
                {"lemma": "тато", "translation": "dad", "pos": "noun"},
                {"lemma": "кіт", "translation": "cat", "pos": "noun"},  # duplicate
            ]
        }, allow_unicode=True))

        # Plans with grammar
        plans_dir = root / "plans" / "test"
        plans_dir.mkdir(parents=True)
        (plans_dir / "mod-1.yaml").write_text(yaml.dump({
            "grammar": ["Це + noun"]
        }, allow_unicode=True))
        (plans_dir / "mod-2.yaml").write_text(yaml.dump({
            "grammar": ["Simple present tense"]
        }, allow_unicode=True))

        with patch("pipeline.learner_state.CURRICULUM_ROOT", root):
            state = build_learner_state("test", 3)

        assert state["module_count"] == 2
        assert "кіт" in state["cumulative_vocabulary"]
        assert "мама" in state["cumulative_vocabulary"]
        assert "тато" in state["cumulative_vocabulary"]
        # No duplicates
        assert state["cumulative_vocabulary"].count("кіт") == 1
        assert "Це + noun" in state["known_grammar"]
        assert "Simple present tense" in state["known_grammar"]
