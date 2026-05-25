from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.build import linear_pipeline


def _vocab(count: int) -> list[dict[str, str]]:
    return [
        {
            "lemma": f"наявне-{index}",
            "translation": f"existing {index}",
            "pos": "term",
            "usage": "",
        }
        for index in range(count)
    ]


def _plan(recommended_count: int) -> dict[str, object]:
    return {
        "module": "a1-020",
        "level": "A1",
        "sequence": 20,
        "slug": "my-morning",
        "title": "Мій ранок",
        "subtitle": "Тест",
        "word_target": 1200,
        "content_outline": [
            {
                "section": "Тест",
                "words": 1200,
                "points": ["Тестова секція"],
            }
        ],
        "references": [{"title": "Тестове джерело"}],
        "vocabulary_hints": {
            "required": ["прокидатися (to wake up)"],
            "recommended": [
                f"рекомендоване-{index} (recommended {index})"
                for index in range(recommended_count)
            ],
        },
    }


def test_vocab_floor_pads_to_floor_from_recommended_only() -> None:
    updated, diagnostic = linear_pipeline._correct_vocab_floor(
        _plan(8),
        _vocab(20),
        {"floor": 25},
    )

    assert len(updated) == 25
    assert diagnostic["added_count"] == 5
    assert diagnostic["exhausted"] is False
    recommended = {
        item.split("(", 1)[0].strip()
        for item in _plan(8)["vocabulary_hints"]["recommended"]
    }
    assert set(diagnostic["added_lemmas"]) <= recommended


def test_vocab_floor_exhaustion_reports_insufficient_plan_recommendations() -> None:
    updated, diagnostic = linear_pipeline._correct_vocab_floor(
        _plan(3),
        _vocab(20),
        {"floor": 25},
    )

    assert len(updated) == 23
    assert diagnostic["added_count"] == 3
    assert diagnostic["exhausted"] is True
    assert "plan recommends insufficient" in diagnostic["message"]


def test_vocab_floor_never_adds_non_recommended_lemmas() -> None:
    updated, diagnostic = linear_pipeline._correct_vocab_floor(
        _plan(8),
        _vocab(20),
        {"floor": 25},
    )

    original = {item["lemma"] for item in _vocab(20)}
    added = {item["lemma"] for item in updated if item["lemma"] not in original}
    assert added == set(diagnostic["added_lemmas"])
    assert "прокидатися" not in added


def test_vocab_floor_noops_when_already_at_floor() -> None:
    updated, diagnostic = linear_pipeline._correct_vocab_floor(
        _plan(8),
        _vocab(25),
        {"floor": 25},
    )

    assert len(updated) == 25
    assert diagnostic["added_count"] == 0
    assert diagnostic["exhausted"] is False


def test_vocab_count_gate_dispatches_deterministic_floor_handler(tmp_path: Path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text("## Тест\n\nТекст.\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text(
        yaml.safe_dump(_vocab(20), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        yaml.safe_dump(_plan(8), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    reports = [
        {"gates": {"passed": True}},
        {"gates": {"passed": True}},
    ]

    def qg_runner() -> dict[str, object]:
        return reports.pop(0)

    report = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        plan_path,
        qg_runner=qg_runner,
    )

    assert report["gates"]["vocab_count"]["passed"] is True
    assert len(yaml.safe_load((module_dir / "vocabulary.yaml").read_text("utf-8"))) == 25
    correction = json.loads((module_dir / "python_qg_correction_r1.json").read_text("utf-8"))
    assert correction["gate"] == "vocab_count"
    assert correction["correction"]["diagnostic"]["added_count"] == 5
