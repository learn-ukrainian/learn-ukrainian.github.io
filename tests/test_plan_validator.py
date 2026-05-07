"""Tests for deterministic plan contradiction validation."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from audit.check_plan import check_textbook_references_in_corpus
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


def _write_sources_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE textbooks (source_file TEXT, grade INTEGER, author TEXT)")
    conn.execute(
        "INSERT INTO textbooks (source_file, grade, author) VALUES (?, ?, ?)",
        ("10-klas-ukrmova-karaman-2018", 10, "karaman"),
    )
    conn.execute(
        "INSERT INTO textbooks (source_file, grade, author) VALUES (?, ?, ?)",
        ("11-klas-ukrajinska-mova-avramenko-2019", 11, "avramenko"),
    )
    conn.commit()
    conn.close()


def test_plan_review_rejects_unknown_textbook(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    _write_sources_db(db_path)
    plan = {
        "references": [
            {"source": "Караман, 10 клас (2018)", "pages": "§76, с. 189"},
            {"source": "Неіснуючий, 9 клас (2024)", "pages": "с. 9"},
        ]
    }

    issues = check_textbook_references_in_corpus(plan, db_path)

    assert len(issues) == 1
    assert issues[0].severity == "ERROR"
    assert "Неіснуючий, 9 клас (2024)" in issues[0].message
    assert "Plan references unknown textbook" in issues[0].message


def test_plan_review_passes_with_only_in_corpus_refs(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    _write_sources_db(db_path)
    plan = {
        "references": [
            {"source": "Караман, 10 клас (2018)", "pages": "§76, с. 189"},
            {"title": "Авраменко Grade 11, p.42"},
        ]
    }

    assert check_textbook_references_in_corpus(plan, db_path) == []


def test_plan_review_handles_empty_references(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    _write_sources_db(db_path)

    assert check_textbook_references_in_corpus({"references": []}, db_path) == []
