"""Tests for paradigm densify-from-lexemes refresh helper."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.practice.densify_paradigm_from_lexemes import densify_level


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_densify_level_promotes_syncretic_adjective(tmp_path: Path) -> None:
    practice_dir = tmp_path
    level = "A1"
    lexeme = {
        "lemmaId": "aktyvnyi",
        "lemma": "активний",
        "cefr": "A1",
        "pos": "adj",
        "paradigm": {
            "cases": {
                "nominative": {"singular": "активний", "plural": "активні"},
                "genitive": {"singular": "активного", "plural": "активних"},
                "dative": {"singular": "активному", "plural": "активним"},
                "accusative": {"singular": "активний", "plural": "активних"},
                "instrumental": {"singular": "активним", "plural": "активними"},
                "locative": {"singular": "активному", "plural": "активних"},
                "vocative": {"singular": "активний", "plural": "активні"},
            }
        },
    }
    _write_json(
        practice_dir / f"practice-lexemes.{level}.json",
        {
            "schema": "atlas-practice-lexemes",
            "schemaVersion": 1,
            "deckVersion": "test",
            "level": level,
            "lexemes": [lexeme],
        },
    )
    _write_json(
        practice_dir / f"practice-paradigm.{level}.json",
        {
            "schema": "atlas-practice-paradigm",
            "schemaVersion": 1,
            "deckVersion": "test",
            "level": level,
            "paradigm": [],
        },
    )
    _write_json(
        practice_dir / f"practice-index.{level}.json",
        {
            "schema": "atlas-practice-index",
            "schemaVersion": 1,
            "deckVersion": "test",
            "level": level,
            "items": [
                {
                    "lemmaId": "aktyvnyi",
                    "lemma": "активний",
                    "cefr": "A1",
                    "modes": ["flashcards", "stress"],
                    "hasCloze": False,
                    "clozeIds": [],
                    "newOrder": 0,
                }
            ],
            "counts": {
                "lexemes": 1,
                "modeCounts": {"paradigm": 0, "stress": 1},
                "modeCoverage": {"paradigm": 0.0, "stress": 1.0},
            },
        },
    )

    stats = densify_level(practice_dir, level)
    assert stats["after_unique"] == 1
    assert stats["items"] >= 4

    paradigm = json.loads((practice_dir / f"practice-paradigm.{level}.json").read_text(encoding="utf-8"))
    assert paradigm["paradigm"]
    index = json.loads((practice_dir / f"practice-index.{level}.json").read_text(encoding="utf-8"))
    assert "paradigm" in index["items"][0]["modes"]
    assert index["counts"]["modeCounts"]["paradigm"] == len(paradigm["paradigm"])
