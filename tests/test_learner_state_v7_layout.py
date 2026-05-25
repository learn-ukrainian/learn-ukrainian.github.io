"""Tests for V7 learner-state layout support."""

import yaml

from scripts import config
from scripts.pipeline import learner_state


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


def test_load_vocab_reads_required_hints_when_targets_are_missing(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    _write_yaml(root / "plans" / "a1" / "hint-only.yaml", {
        "vocabulary_hints": {
            "required": ["вікно (window)", "двері (door)"],
        },
    })
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)

    assert learner_state._load_vocab("a1", "hint-only") == ["вікно", "двері"]


def test_load_vocab_plan_without_vocab_returns_empty_list(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    _write_yaml(root / "plans" / "a1" / "no-vocab.yaml", {
        "title": "No vocabulary here",
    })
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)

    assert learner_state._load_vocab("a1", "no-vocab") == []


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


def test_compute_immersion_band_uses_plan_only_learner_state(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    slugs = [f"module-{index:02d}" for index in range(1, 21)]
    _write_yaml(root / "curriculum.yaml", {
        "levels": {"a1": {"modules": slugs}},
    })
    for module_index, slug in enumerate(slugs[:19], start=1):
        _write_yaml(root / "plans" / "a1" / f"{slug}.yaml", {
            "targets": {
                "new_vocabulary": [
                    f"слово-{module_index:02d}-{word_index:02d}"
                    for word_index in range(1, 9)
                ],
            },
        })
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)
    monkeypatch.setattr(config, "USE_ULP_IMMERSION_DERIVATION", True)

    state = learner_state.build_learner_state("a1", 20)
    band = config.compute_immersion_band("a1", 20, learner_state=state)

    assert state["cumulative_vocabulary"] == [
        f"слово-{module_index:02d}-{word_index:02d}"
        for module_index in range(1, 20)
        for word_index in range(1, 9)
    ]
    assert band["key"] == "a1-m04-06"
    assert (band["advisory_pct_min"], band["advisory_pct_max"]) == (8, 30)


def test_format_learner_state_contains_rule_footer_for_non_empty_state():
    text = learner_state.format_learner_state({
        "cumulative_vocabulary": ["тест"],
        "known_grammar": ["Це + noun"],
        "module_count": 1,
    })

    assert "**Rule:**" in text
