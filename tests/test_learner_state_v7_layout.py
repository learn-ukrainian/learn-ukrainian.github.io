"""Tests for V7 learner-state layout support."""

import pytest
import yaml

from scripts.pipeline import learner_state

pytestmark = pytest.mark.reads_content


def _write_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def test_load_vocab_reads_v7_module_layout(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    _write_yaml(root / "a1" / "module-a" / "vocabulary.yaml", {
        "items": [{"lemma": "тест"}],
    })
    _write_yaml(root / "plans" / "a1" / "module-a.yaml", {
        "targets": {"new_vocabulary": ["плановий"]},
    })
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)

    assert learner_state._load_vocab("a1", "module-a") == ["тест"]


def test_load_vocab_reads_plan_targets_when_built_vocab_is_missing(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    _write_yaml(root / "plans" / "a1" / "plan-only.yaml", {
        "targets": {"new_vocabulary": ["план", "ранок"]},
    })
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)

    assert learner_state._load_vocab("a1", "plan-only") == ["план", "ранок"]


def test_load_vocab_merges_plan_targets_required_and_recommended(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    _write_yaml(root / "plans" / "a1" / "merged-plan.yaml", {
        "targets": {"new_vocabulary": ["план", "ранок"]},
        "vocabulary_hints": {
            "required": ["ранок (morning)", "кава (coffee)"],
            "recommended": ["після цього (after this)"],
        },
    })
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)

    assert learner_state._load_vocab("a1", "merged-plan") == [
        "план",
        "ранок",
        "кава",
        "після цього",
    ]
