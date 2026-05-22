"""Tests for learner state manifest generation."""

import sys
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pipeline.learner_state import (
    _load_planned_vocab,
    _load_vocab,
    _parse_vocab_hint_lemma,
    build_learner_state,
    format_learner_state,
)


class TestPlannedVocabulary:
    """Planned vocab fills learner-state gaps before modules are built."""

    def test_parse_vocab_hint_lemma_basic(self):
        assert _parse_vocab_hint_lemma("готовий (ready, adj m)") == "готовий"
        assert _parse_vocab_hint_lemma("синку (son — vocative, from син)") == "синку"
        assert _parse_vocab_hint_lemma("вітаю (congratulations — chunk)") == "вітаю"
        assert _parse_vocab_hint_lemma("") is None

    def test_load_planned_vocab_a1_colors(self):
        lemmas = _load_planned_vocab("a1", "colors")

        assert len(lemmas) >= 10
        assert "червоний" in lemmas
        assert "синій" in lemmas
        assert "блакитний" in lemmas
        assert "якого кольору?" in lemmas
        assert "прапор" in lemmas

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

        vocab_dir = root / "test"
        (vocab_dir / "mod-1").mkdir(parents=True)
        (vocab_dir / "mod-1" / "vocabulary.yaml").write_text(yaml.dump({
            "items": [{"lemma": "так", "translation": "yes", "pos": "particle"}]
        }, allow_unicode=True))
        (vocab_dir / "mod-2").mkdir(parents=True)
        (vocab_dir / "mod-2" / "vocabulary.yaml").write_text(yaml.dump({
            "items": [{"lemma": "ні", "translation": "no", "pos": "particle"}]
        }, allow_unicode=True))

        with patch("pipeline.learner_state.CURRICULUM_ROOT", root):
            state = build_learner_state("test", 2)

        assert state["cumulative_vocabulary"] == ["так"]
        assert "ні" not in state["cumulative_vocabulary"]

    def test_build_learner_state_a1_m20_has_vocab(self):
        state = build_learner_state("a1", 20)

        assert state["cumulative_vocabulary"]


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
