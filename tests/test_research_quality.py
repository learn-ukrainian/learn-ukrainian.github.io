"""Tests for research quality rubric scoring functions."""
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "research"))

from scripts.research.research_quality import (
    _parse_discovery,
    find_research_path,
)


def _make_discovery(blogs=None, videos=None, rag_chunks=None, rag_literary=None):
    """Helper to build a discovery dict matching _parse_discovery output."""
    return {
        "blogs": blogs or [],
        "videos": videos or [],
        "rag_chunks": rag_chunks or [],
        "rag_literary": rag_literary or [],
    }


# ── _parse_discovery ────────────────────────────────────────────────────


class TestParseDiscovery:
    """Tests for the shared discovery.yaml parser."""

    def test_missing_file_returns_empty(self, tmp_path):
        result = _parse_discovery(tmp_path / "nonexistent.yaml")
        assert result == _make_discovery()

    def test_valid_file_parsed(self, tmp_path):
        import yaml
        path = tmp_path / "discovery.yaml"
        path.write_text(yaml.dump({
            "blogs": [{"url": "https://example.com"}],
            "videos": [{"url": "https://youtube.com/v"}],
            "rag_chunks": [{"text": "chunk"}],
            "rag_literary": [{"text": "lit"}],
        }))
        result = _parse_discovery(path)
        assert len(result["blogs"]) == 1
        assert len(result["videos"]) == 1
        assert len(result["rag_chunks"]) == 1
        assert len(result["rag_literary"]) == 1

    def test_invalid_yaml_returns_empty(self, tmp_path):
        path = tmp_path / "discovery.yaml"
        path.write_text(": : invalid yaml [[[")
        result = _parse_discovery(path)
        assert result == _make_discovery()

    def test_top_level_list_returns_empty(self, tmp_path):
        """A YAML file with a top-level list instead of dict should not crash."""
        path = tmp_path / "discovery.yaml"
        path.write_text("- item1\n- item2\n")
        result = _parse_discovery(path)
        assert result == _make_discovery()


class TestFindResearchPath:
    def test_prefers_curriculum_research_file(self, tmp_path, monkeypatch):
        import scripts.research.research_quality as research_quality

        track_dir = tmp_path / "curriculum" / "l2-uk-en" / "bio"
        research_dir = track_dir / "research"
        docs_dir = tmp_path / "docs" / "research" / "bio"
        research_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)
        curriculum_file = research_dir / "ivan-franko-research.md"
        docs_file = docs_dir / "ivan-franko.md"
        curriculum_file.write_text("curriculum research", encoding="utf-8")
        docs_file.write_text("docs dossier", encoding="utf-8")

        monkeypatch.setattr(research_quality, "DOCS_RESEARCH_ROOT", tmp_path / "docs" / "research")

        assert find_research_path(track_dir, "ivan-franko") == curriculum_file

    def test_falls_back_to_docs_research_dossier(self, tmp_path, monkeypatch):
        import scripts.research.research_quality as research_quality

        track_dir = tmp_path / "curriculum" / "l2-uk-en" / "bio"
        docs_dir = tmp_path / "docs" / "research" / "bio"
        track_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)
        docs_file = docs_dir / "ivan-franko.md"
        docs_file.write_text("docs dossier", encoding="utf-8")

        monkeypatch.setattr(research_quality, "DOCS_RESEARCH_ROOT", tmp_path / "docs" / "research")

        assert find_research_path(track_dir, "ivan-franko") == docs_file


# ── _score_source_verification ──────────────────────────────────────────


# ── _score_discovery_integration ────────────────────────────────────────


# ── _score_claim_grounding ──────────────────────────────────────────────
