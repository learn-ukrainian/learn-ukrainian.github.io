"""Tests for folk_injector module."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from folk_injector import (
    _load_folk_data,
    _match_themes,
    build_folk_material,
)


class TestLoadFolkData:
    def test_loads_successfully(self):
        data = _load_folk_data()
        assert isinstance(data, dict)
        assert "загадки" in data
        assert "скоромовки" in data
        assert "прислів'я" in data
        assert "приказки" in data
        assert "лічилки" in data
        assert "мирилки" in data

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


class TestMatchThemes:
    def test_food_module(self):
        themes = _match_themes("shopping-and-market")
        assert "їжа" in themes

    def test_nature_module(self):
        themes = _match_themes("weather-and-seasons")
        assert "природа" in themes

    def test_family_module(self):
        themes = _match_themes("my-family")
        assert "сім'я" in themes

    def test_phonetics_module(self):
        themes = _match_themes("phonetics-assimilation")
        assert "мова" in themes

    def test_unknown_slug_returns_empty(self):
        themes = _match_themes("totally-unknown-slug")
        assert themes == set()


class TestBuildFolkMaterial:
    def test_a1_returns_content(self):
        result = build_folk_material("a1", "shopping-and-market")
        assert result
        # A1 gets прислів'я/приказки/лічилки/мирилки but NOT загадки
        assert "Прислів" in result or "Приказки" in result or "Лічилки" in result

    def test_a1_no_zagadky(self):
        """A1 should NOT include загадки — grammar too complex for L2."""
        result = build_folk_material("a1", "shopping-and-market")
        assert "Загадки" not in result

    def test_a1_no_skoromovky(self):
        """A1 should NOT include скоромовки."""
        result = build_folk_material("a1", "shopping-and-market")
        assert "Скоромовки" not in result

    def test_a2_includes_zagadky(self):
        """A2 should include загадки."""
        result = build_folk_material("a2", "shopping-and-market")
        assert "Загадки" in result

    def test_a2_includes_skoromovky(self):
        """A2+ should include скоромовки when available."""
        result = build_folk_material("a2", "phonetics-assimilation")
        assert "Скоромовки" in result

    def test_b1_phonetics_gets_all_skoromovky(self):
        """Phonetics modules should get extra скоромовки."""
        result = build_folk_material("b1", "phonetics-assimilation")
        assert "Скоромовки" in result
        assert result.count("звук:") >= 3

    def test_a1_includes_lichilky(self):
        result = build_folk_material("a1", "numbers-and-counting")
        assert "Лічилки" in result

    def test_a1_greetings_includes_myrylky(self):
        result = build_folk_material("a1", "greetings-and-politeness")
        assert "Мирилки" in result

    def test_empty_for_seminar_tracks(self):
        """B2+ seminar tracks should get minimal folk material."""
        result = build_folk_material("b2", "register-literary-ukrainian")
        # Should still return something but limited
        # B2 only gets загадки and скоромовки
        if result:
            assert "Прислів'я" not in result  # B2 has dedicated proverb modules

    def test_output_has_header(self):
        result = build_folk_material("a1", "shopping-and-market")
        assert "Available Folk Material" in result
        assert "[!folk-wisdom]" in result

    def test_output_has_sources(self):
        result = build_folk_material("a1", "shopping-and-market")
        assert "джерело:" in result

    def test_max_per_genre_respected(self):
        result = build_folk_material("b1", "shopping-and-market", max_per_genre=2)
        # Count загадки entries (lines with →)
        zagadki_count = sum(1 for line in result.split("\n") if "→ **" in line)
        assert zagadki_count <= 2

    def test_unknown_slug_gets_fallback(self):
        """Unknown slugs should still get some folk material via fallback."""
        result = build_folk_material("a2", "totally-unknown-module")
        assert result
        assert "Загадки" in result

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
