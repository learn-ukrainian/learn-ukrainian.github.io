"""Tests for V7 learner-state layout support."""

import yaml

from scripts.pipeline import learner_state


def _write_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def test_load_vocab_reads_v7_module_layout(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    _write_yaml(root / "a1" / "module-a" / "vocabulary.yaml", {
        "items": [{"lemma": "тест"}],
    })
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)

    assert learner_state._load_vocab("a1", "module-a") == ["тест"]


def test_load_vocab_missing_file_returns_empty_list(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    root.mkdir(parents=True)
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)

    assert learner_state._load_vocab("a1", "missing-module") == []


def test_build_learner_state_accumulates_only_previous_modules(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    _write_yaml(root / "curriculum.yaml", {
        "levels": {
            "a1": {
                "modules": ["module-a", "module-b", "module-c"],
            },
        },
    })
    _write_yaml(root / "a1" / "module-a" / "vocabulary.yaml", {
        "items": [{"lemma": "тест"}],
    })
    _write_yaml(root / "a1" / "module-b" / "vocabulary.yaml", {
        "items": [{"lemma": "слово"}],
    })
    _write_yaml(root / "a1" / "module-c" / "vocabulary.yaml", {
        "items": [{"lemma": "зайве"}],
    })
    _write_yaml(root / "plans" / "a1" / "module-a.yaml", {
        "title": "Module A",
        "grammar": ["Це + noun"],
    })
    _write_yaml(root / "plans" / "a1" / "module-b.yaml", {
        "title": "Module B",
        "grammar": ["я маю"],
    })
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)

    state = learner_state.build_learner_state("a1", 3)

    assert state["cumulative_vocabulary"] == ["тест", "слово"]
    assert "зайве" not in state["cumulative_vocabulary"]


def test_format_learner_state_contains_rule_footer_for_non_empty_state():
    text = learner_state.format_learner_state({
        "cumulative_vocabulary": ["тест"],
        "known_grammar": ["Це + noun"],
        "module_count": 1,
    })

    assert "**Rule:**" in text
