import os
import time
from pathlib import Path

import yaml

from scripts.build import learner_immersion


def _write_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _mini_curriculum(root: Path) -> None:
    _write_yaml(
        root / "curriculum.yaml",
        {"levels": {"test": {"modules": ["mod-1", "mod-2", "mod-3"]}}},
    )
    _write_yaml(
        root / "test" / "mod-1" / "vocabulary.yaml",
        {"items": [{"lemma": "кіт"}, {"lemma": "мама"}]},
    )
    (root / "test" / "mod-1" / "module.md").write_text("кіт кіт мама", encoding="utf-8")
    _write_yaml(
        root / "test" / "mod-2" / "vocabulary.yaml",
        {"items": [{"lemma": "кіт"}, {"lemma": "тато"}]},
    )
    (root / "test" / "mod-2" / "module.md").write_text("тато кіт", encoding="utf-8")
    _write_yaml(root / "test" / "mod-3" / "vocabulary.yaml", {"items": [{"lemma": "дім"}]})
    (root / "test" / "mod-3" / "module.md").write_text("дім", encoding="utf-8")


def test_build_lemma_frequency_map_counts_previous_modules(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    _mini_curriculum(root)
    monkeypatch.setattr(learner_immersion, "CURRICULUM_ROOT", root)
    monkeypatch.setattr(learner_immersion, "CACHE_ROOT", tmp_path / ".cache")
    monkeypatch.setattr(
        learner_immersion,
        "_extract_all_ukrainian_surfaces",
        lambda content: content.split(),
    )

    result = learner_immersion.build_lemma_frequency_map("test", 3)

    assert result["кіт"] == [(1, 2), (2, 1)]
    assert result["мама"] == [(1, 1)]
    assert result["тато"] == [(2, 1)]
    assert "дім" not in result
    assert (tmp_path / ".cache" / "lemma-frequency-test-3.json").exists()


def test_build_lemma_frequency_map_invalidates_stale_cache(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    _mini_curriculum(root)
    monkeypatch.setattr(learner_immersion, "CURRICULUM_ROOT", root)
    monkeypatch.setattr(learner_immersion, "CACHE_ROOT", tmp_path / ".cache")
    monkeypatch.setattr(
        learner_immersion,
        "_extract_all_ukrainian_surfaces",
        lambda content: content.split(),
    )

    first = learner_immersion.build_lemma_frequency_map("test", 3)
    assert "нове" not in first

    time.sleep(1.1)
    _write_yaml(
        root / "test" / "mod-1" / "vocabulary.yaml",
        {"items": [{"lemma": "кіт"}, {"lemma": "мама"}, {"lemma": "нове"}]},
    )
    (root / "test" / "mod-1" / "module.md").write_text("кіт кіт мама нове", encoding="utf-8")

    second = learner_immersion.build_lemma_frequency_map("test", 3)

    assert second["нове"] == [(1, 1)]
    assert os.path.exists(tmp_path / ".cache" / "lemma-frequency-test-3.json")
