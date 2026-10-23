"""Tests for folk_injector module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "content"))

from scripts.content.folk_injector import (
    _load_folk_data,
)


class TestLoadFolkData:
    def test_entries_have_required_fields(self):
        data = _load_folk_data()
        for entry in data["загадки"]:
            assert "text" in entry
            assert "answer" in entry
            assert "difficulty" in entry

        for entry in data["скоромовки"]:
            assert "text" in entry
            assert "target_sound" in entry
            assert "difficulty" in entry

        for entry in data["прислів'я"]:
            assert "text" in entry
            assert "theme" in entry
            assert "difficulty" in entry

    def test_difficulty_values_valid(self):
        data = _load_folk_data()
        valid = {"A1", "A2", "B1"}
        for genre in data.values():
            for entry in genre:
                assert entry.get("difficulty", "A1") in valid, (
                    f"Invalid difficulty: {entry}"
                )


class TestBuildFolkMaterial:

    def test_stress_marks_present(self):
        """All entries should include stress marks (наголос)."""
        data = _load_folk_data()
        for genre_key, entries in data.items():
            for entry in entries:
                text = entry["text"]
                # Check for at least one stress mark (combining acute accent U+0301)
                assert "\u0301" in text, (
                    f"Missing stress marks in {genre_key}: {text[:50]}..."
                )
