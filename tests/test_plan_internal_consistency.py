"""Tests for deterministic plan internal consistency checks."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from add_dialogue_situations import add_situations_to_plan
from audit.check_plan import check_plan_internal_consistency


def test_plan_internal_consistency_flags_pet_shop_vs_room_furniture_mismatch() -> None:
    plan = {
        "dialogue_situations": [
            {
                "setting": "At a pet shop — use кіт, рибка, черепаха, акваріум.",
                "speakers": ["Марія", "Оленка"],
                "motivation": "він/вона/воно with animals and pet items",
            }
        ],
        "content_outline": [
            {
                "section": "Діалоги",
                "words": 300,
                "points": [
                    "Dialogue 1 — show your room: стіл, лампа, ліжко, кімната.",
                    "Dialogue 2 — what is in your bag? книга, телефон, ручка.",
                ],
            }
        ],
    }

    issues = check_plan_internal_consistency(plan)

    assert len(issues) == 1
    assert issues[0].check == "plan_internal_consistency"


def test_plan_internal_consistency_skips_non_dialogue_seminar_shapes() -> None:
    plan = {
        "dialogue_situations": [
            {
                "setting": "Formal panel discussion at a conference.",
                "speakers": ["Модератор", "Історик"],
                "motivation": "Advanced register control",
            }
        ],
        "content_outline": [
            {
                "section": "Історичний контекст",
                "words": 1200,
                "subsections": ["Політичне тло", "Джерельна база"],
            }
        ],
    }

    assert check_plan_internal_consistency(plan) == []


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
