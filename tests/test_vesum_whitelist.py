"""Tests for VESUM false-positive whitelist (scripts/vesum_whitelist.py).

Issue: #1017
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.reads_content

# Ensure scripts/ is on the path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR / "tools"))
sys.path.insert(0, str(SCRIPTS_DIR))

from vesum_whitelist import (
    add_word,
    load_combined_whitelist,
    load_global_whitelist,
    load_whitelist,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_whitelist(tmp_path: Path) -> Path:
    """Create a temporary whitelist YAML file."""
    data = {
        "words": [
            {"word": "зь", "reason": "softening example", "approved_by": "auto"},
            {"word": "морос", "reason": "special signs", "approved_by": "human"},
        ],
    }
    path = tmp_path / "vesum-whitelist.yaml"
    path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Tests: load_whitelist
# ---------------------------------------------------------------------------

class TestLoadWhitelist:
    def test_loads_valid_file(self, tmp_whitelist: Path):
        result = load_whitelist(tmp_whitelist)
        assert "зь" in result
        assert "морос" in result
        assert result["зь"]["reason"] == "softening example"
        assert result["морос"]["approved_by"] == "human"

    def test_returns_empty_for_missing_file(self, tmp_path: Path):
        result = load_whitelist(tmp_path / "nonexistent.yaml")
        assert result == {}

    def test_returns_empty_for_malformed_yaml(self, tmp_path: Path):
        path = tmp_path / "bad.yaml"
        path.write_text(": : : not valid yaml [[[", encoding="utf-8")
        result = load_whitelist(path)
        assert result == {}

    def test_lowercases_words(self, tmp_path: Path):
        data = {"words": [{"word": "Морос", "reason": "test", "approved_by": "auto"}]}
        path = tmp_path / "wl.yaml"
        path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        result = load_whitelist(path)
        assert "морос" in result
        assert "Морос" not in result


# ---------------------------------------------------------------------------
# Tests: load_global_whitelist (reads real file)
# ---------------------------------------------------------------------------

class TestLoadGlobalWhitelist:
    def test_global_whitelist_exists_and_has_seed_words(self):
        result = load_global_whitelist()
        assert len(result) >= 7, f"Expected >= 7 seed words, got {len(result)}"
        for word in ("зь", "ль", "нь", "ть", "морос", "анок", "арно"):
            assert word in result, f"Seed word '{word}' missing from global whitelist"


# ---------------------------------------------------------------------------
# Tests: load_module_whitelist
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Tests: load_combined_whitelist
# ---------------------------------------------------------------------------

class TestLoadCombinedWhitelist:
    def test_includes_global_words(self):
        combined = load_combined_whitelist("a1", "nonexistent-slug")
        assert "зь" in combined
        assert "морос" in combined


# ---------------------------------------------------------------------------
# Tests: add_word
# ---------------------------------------------------------------------------

class TestAddWord:
    def test_add_to_new_file(self, tmp_path: Path, monkeypatch):
        # Redirect global whitelist to tmp
        target = tmp_path / "vesum-whitelist.yaml"
        monkeypatch.setattr(
            "vesum_whitelist.GLOBAL_WHITELIST", target,
        )
        result_path = add_word("тест", "test word", "human")
        assert result_path == target
        assert target.exists()
        data = yaml.safe_load(target.read_text("utf-8"))
        assert len(data["words"]) == 1
        assert data["words"][0]["word"] == "тест"
        assert data["words"][0]["reason"] == "test word"
        assert data["words"][0]["approved_by"] == "human"

    def test_add_to_existing_file(self, tmp_whitelist: Path, monkeypatch):
        monkeypatch.setattr("vesum_whitelist.GLOBAL_WHITELIST", tmp_whitelist)
        add_word("новий", "new word", "auto")
        data = yaml.safe_load(tmp_whitelist.read_text("utf-8"))
        words = [e["word"] for e in data["words"]]
        assert "новий" in words
        assert "зь" in words  # original still there

    def test_no_duplicate(self, tmp_whitelist: Path, monkeypatch):
        monkeypatch.setattr("vesum_whitelist.GLOBAL_WHITELIST", tmp_whitelist)
        add_word("зь", "duplicate", "auto")
        data = yaml.safe_load(tmp_whitelist.read_text("utf-8"))
        assert sum(1 for e in data["words"] if e["word"] == "зь") == 1

    def test_add_module_scope(self, tmp_path: Path, monkeypatch):
        fake_curriculum = tmp_path / "curriculum" / "l2-uk-en"
        fake_curriculum.mkdir(parents=True)
        monkeypatch.setattr("vesum_whitelist.CURRICULUM_ROOT", fake_curriculum)
        result_path = add_word(
            "фраг", "fragment", "auto",
            scope="module", level="a1", slug="test-module",
        )
        expected = fake_curriculum / "a1" / "orchestration" / "test-module" / "vesum-whitelist.yaml"
        assert result_path == expected
        assert expected.exists()
