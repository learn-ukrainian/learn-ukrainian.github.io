"""Tests for deterministic plan internal consistency checks."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from add_dialogue_situations import add_situations_to_plan


def test_add_dialogue_situations_rewrites_dialogue_outline_points(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        yaml.safe_dump(
            {
                "module": "things-have-gender",
                "level": "A1",
                "slug": "things-have-gender",
                "version": "1.0",
                "title": "Things Have Gender",
                "focus": "grammar",
                "pedagogy": "PPP",
                "phase": "A1.2",
                "objectives": ["Learn gender"],
                "word_target": 1200,
                "content_outline": [
                    {
                        "section": "Діалоги (Dialogues)",
                        "words": 300,
                        "points": [
                            "Dialogue 1 — generic room scene.",
                            "Dialogue 2 — generic bag scene.",
                        ],
                    },
                    {"section": "Підсумок", "words": 300},
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )

    changed = add_situations_to_plan(
        plan_path,
        [
            {
                "setting": "At a pet shop — кіт, рибка, черепаха, акваріум.",
                "speakers": ["Марія", "Оленка"],
                "motivation": "він/вона/воно with pet-shop nouns",
            }
        ],
        dry_run=False,
    )

    assert changed is True
    updated = yaml.safe_load(plan_path.read_text("utf-8"))
    assert updated["dialogue_situations"][0]["setting"].startswith("At a pet shop")
    assert updated["content_outline"][0]["points"][0].startswith("Dialogue 1 — At a pet shop")
