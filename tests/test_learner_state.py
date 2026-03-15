"""Tests for learner state manifest generation."""

import sys
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pipeline.learner_state import build_learner_state, format_learner_state


class TestBuildLearnerState:
    """build_learner_state collects cumulative vocab + grammar."""

    def test_first_module_empty(self):
        state = build_learner_state("a1", 1)
        assert state["cumulative_vocabulary"] == []
        assert state["known_grammar"] == []
        assert state["module_count"] == 0

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
        vocab_dir = root / "test" / "vocabulary"
        vocab_dir.mkdir(parents=True)
        (vocab_dir / "mod-1.yaml").write_text(yaml.dump({
            "items": [
                {"lemma": "кіт", "translation": "cat", "pos": "noun"},
                {"lemma": "мама", "translation": "mom", "pos": "noun"},
            ]
        }, allow_unicode=True))

        # Vocab for mod-2
        (vocab_dir / "mod-2.yaml").write_text(yaml.dump({
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

    def test_module_2_only_sees_module_1(self, tmp_path):
        curriculum = {
            "levels": {
                "test": {
                    "modules": ["mod-1", "mod-2"]
                }
            }
        }
        root = tmp_path / "curriculum" / "l2-uk-en"
        (root).mkdir(parents=True)
        (root / "curriculum.yaml").write_text(yaml.dump(curriculum, allow_unicode=True))

        vocab_dir = root / "test" / "vocabulary"
        vocab_dir.mkdir(parents=True)
        (vocab_dir / "mod-1.yaml").write_text(yaml.dump({
            "items": [{"lemma": "так", "translation": "yes", "pos": "particle"}]
        }, allow_unicode=True))
        (vocab_dir / "mod-2.yaml").write_text(yaml.dump({
            "items": [{"lemma": "ні", "translation": "no", "pos": "particle"}]
        }, allow_unicode=True))

        with patch("pipeline.learner_state.CURRICULUM_ROOT", root):
            state = build_learner_state("test", 2)

        assert state["cumulative_vocabulary"] == ["так"]
        assert "ні" not in state["cumulative_vocabulary"]


class TestFormatLearnerState:
    """format_learner_state produces readable text."""

    def test_first_module(self):
        state = {"cumulative_vocabulary": [], "known_grammar": [], "module_count": 0}
        text = format_learner_state(state)
        assert "first module" in text.lower()

    def test_with_vocab_and_grammar(self):
        state = {
            "cumulative_vocabulary": ["кіт", "мама", "тато"],
            "known_grammar": ["Це + noun", "Simple present"],
            "module_count": 2,
        }
        text = format_learner_state(state)
        assert "кіт" in text
        assert "Це + noun" in text
        assert "3 words" in text
        assert "2 topics" in text
