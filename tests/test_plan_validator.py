"""Tests for deterministic plan contradiction validation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.phases.plan_validator import validate_plan_consistency


def test_clean_plan_passes() -> None:
    plan = {
        "dialogue_situations": [
            {
                "setting": "At a pet shop with animals and pet items, not room furniture.",
                "speakers": ["Марія", "Оленка"],
                "motivation": "Practice він/вона/воно with pet-shop nouns",
            }
        ],
        "content_outline": [
            {
                "section": "Діалоги",
                "words": 300,
                "points": [
                    "Dialogue 1 — At a pet shop, compare a кіт, рибка, and акваріум.",
                    "Dialogue 2 — Ask which pet accessories belong to which animal.",
                ],
            }
        ],
    }

    assert validate_plan_consistency(plan, "things-have-gender") == []


def test_pet_shop_vs_room_contradiction_detected() -> None:
    plan = {
        "dialogue_situations": [
            {
                "setting": "At a pet shop with animals and pet items, NOT room furniture.",
                "speakers": ["Марія", "Оленка"],
                "motivation": "Practice він/вона/воно with pet-shop nouns",
            }
        ],
        "content_outline": [
            {
                "section": "Діалоги",
                "words": 300,
                "points": [
                    "Dialogue 1 — Video call showing your room with a table, lamp, and bed.",
                    "Dialogue 2 — Ask what is in your bag.",
                ],
            }
        ],
    }

    messages = validate_plan_consistency(plan, "things-have-gender")

    assert len(messages) == 1
    assert "things-have-gender" in messages[0]
    assert "room furniture" in messages[0]
    assert "room" in messages[0]


def test_empty_dialogue_situations_passes() -> None:
    plan = {
        "dialogue_situations": [],
        "content_outline": [
            {
                "section": "Діалоги",
                "words": 300,
                "points": ["Dialogue 1 — Any simple exchange."],
            }
        ],
    }

    assert validate_plan_consistency(plan, "reading-ukrainian") == []
