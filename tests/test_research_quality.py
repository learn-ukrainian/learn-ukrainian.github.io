"""Tests for research quality rubric scoring functions."""
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "research"))

from scripts.research.research_quality import (
    _parse_discovery,
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


# ── _score_source_verification ──────────────────────────────────────────


# ── _score_discovery_integration ────────────────────────────────────────


# ── _score_claim_grounding ──────────────────────────────────────────────
