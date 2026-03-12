"""Tests for research quality rubric scoring functions."""
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "research"))

from scripts.research.research_quality import (
    _parse_discovery,
    _score_claim_grounding,
    _score_discovery_integration,
    _score_source_verification,
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

    def test_none_path_returns_empty(self):
        result = _parse_discovery(None)
        assert result == _make_discovery()

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


# ── _score_source_verification ──────────────────────────────────────────


class TestSourceVerification:
    """Tests for source_verification dimension scoring."""

    def test_no_sources_scores_zero(self):
        result = _score_source_verification("Some text without any URLs", "beginner")
        assert result["score"] == 0
        assert "no sources" in result["detail"]

    def test_known_good_domain_scores_full(self):
        text = "See https://uk.wikipedia.org/wiki/Привіт for details."
        result = _score_source_verification(text, "beginner")
        assert result["score"] == 2

    def test_unknown_domain_scores_zero(self):
        text = "See https://example.com/page for info."
        result = _score_source_verification(text, "beginner")
        assert result["score"] == 0
        assert "0 known-good" in result["detail"]

    def test_discovery_blogs_counted(self):
        """Blog URLs from discovery should be counted as sources."""
        discovery = _make_discovery(
            blogs=[{"url": "https://uk.wikipedia.org/wiki/Test", "title": "Test"}],
        )
        result = _score_source_verification("Research text", "beginner", discovery)
        assert result["score"] == 2
        assert "1 URLs" in result["detail"]

    def test_discovery_videos_counted(self):
        """Video URLs from discovery should be counted as sources."""
        discovery = _make_discovery(
            videos=[{"url": "https://www.youtube.com/watch?v=abc", "title": "Test"}],
        )
        result = _score_source_verification("Research text", "beginner", discovery)
        # youtube.com is not in KNOWN_GOOD_DOMAINS, so score stays 0
        # but the URL is still counted in the total
        assert "1 URLs" in result["detail"]

    def test_rag_chunks_counted_as_sources(self):
        """RAG textbook chunks should count as valid known-good sources."""
        discovery = _make_discovery(
            rag_chunks=[
                {"text": "Textbook content about grammar", "source": "Vashulenko"},
                {"text": "More textbook content", "source": "Zabolotnyj"},
            ],
        )
        result = _score_source_verification("Research text", "beginner", discovery)
        assert result["score"] == 2
        assert "2 RAG chunks" in result["detail"]

    def test_rag_plus_urls_combined(self):
        """RAG chunks + blog URLs should combine for total source count."""
        discovery = _make_discovery(
            blogs=[{"url": "https://sum.in.ua/s/slovo", "title": "SUM"}],
            rag_chunks=[{"text": "chunk", "source": "textbook"}],
        )
        result = _score_source_verification("Research text", "beginner", discovery)
        assert result["score"] == 2
        assert "1 URLs" in result["detail"]
        assert "1 RAG chunks" in result["detail"]

    def test_none_discovery_handled(self):
        """None discovery should not crash."""
        result = _score_source_verification("Some text", "beginner", None)
        assert result["score"] == 0

    def test_empty_discovery_handled(self):
        """Empty discovery dict should not crash."""
        result = _score_source_verification("Some text", "beginner", _make_discovery())
        assert result["score"] == 0

    def test_core_tier_needs_two_known_domains(self):
        """Core tier requires 2 known-good domains for full score."""
        text = "See https://uk.wikipedia.org/wiki/A and https://sum.in.ua/s/B"
        result = _score_source_verification(text, "core")
        assert result["score"] == 2

    def test_core_tier_one_domain_partial(self):
        """Core tier with 1 known-good domain should get partial score."""
        text = "See https://uk.wikipedia.org/wiki/A only"
        result = _score_source_verification(text, "core")
        assert result["score"] == 1


# ── _score_discovery_integration ────────────────────────────────────────


class TestDiscoveryIntegration:
    """Tests for discovery_integration dimension scoring."""

    def test_none_scores_zero(self):
        result = _score_discovery_integration(None)
        assert result["score"] == 0

    def test_empty_scores_zero(self):
        result = _score_discovery_integration(_make_discovery())
        assert result["score"] == 0

    def test_any_resource_scores_one(self):
        result = _score_discovery_integration(_make_discovery(
            rag_chunks=[{"text": "chunk"}],
        ))
        assert result["score"] == 1

    def test_detail_lists_resource_types(self):
        result = _score_discovery_integration(_make_discovery(
            blogs=[{"url": "https://example.com"}],
            rag_chunks=[{"text": "a"}, {"text": "b"}],
        ))
        assert "1 blogs" in result["detail"]
        assert "2 RAG" in result["detail"]


# ── _score_claim_grounding ──────────────────────────────────────────────


class TestClaimGrounding:
    """Tests for claim_grounding dimension scoring."""

    def test_empty_text_scores_zero(self):
        result = _score_claim_grounding("", "beginner")
        assert result["score"] == 0

    def test_quoted_examples_counted(self):
        text = "«привіт» «дякую» «добре» «так» «ласка»"
        result = _score_claim_grounding(text, "beginner")
        assert result["score"] == 2  # 5 examples >= beginner threshold

    def test_bold_examples_counted(self):
        text = "Use *привіт* and *дякую* and *добре*"
        result = _score_claim_grounding(text, "beginner")
        assert result["score"] >= 1  # 3 examples >= partial

    def test_table_cells_counted(self):
        """Ukrainian words in markdown table cells should be counted."""
        text = textwrap.dedent("""\
            | привіт | hello |
            | дякую | thanks |
            | добре | good |
            | будь | please |
            | так | yes |
        """)
        result = _score_claim_grounding(text, "beginner")
        assert result["score"] == 2  # 5 table words

    def test_bullet_items_counted(self):
        """Ukrainian words starting bullet items should be counted."""
        text = textwrap.dedent("""\
            - привіт (hello)
            - дякую (thanks)
            - добре (good)
            - будь ласка (please)
            - так (yes)
        """)
        result = _score_claim_grounding(text, "beginner")
        assert result["score"] == 2  # 5 bullet words

    def test_asterisk_bullets_counted(self):
        """Asterisk bullet items should also be counted."""
        text = textwrap.dedent("""\
            * привіт (hello)
            * дякую (thanks)
            * добре (good)
        """)
        result = _score_claim_grounding(text, "beginner")
        assert result["score"] >= 1  # 3 examples >= partial

    def test_mixed_formats_combined(self):
        """Examples from different formats should all contribute."""
        text = textwrap.dedent("""\
            The word «привіт» means hello.
            | дякую | thanks |
            - добре is commonly used
        """)
        result = _score_claim_grounding(text, "beginner")
        assert result["score"] >= 1  # 3 different format examples

    def test_no_examples_scores_zero(self):
        """Plain English text with no Ukrainian examples should score 0."""
        result = _score_claim_grounding(
            "This research discusses grammar patterns in general terms.",
            "beginner",
        )
        assert result["score"] == 0

    def test_short_words_excluded_from_tables(self):
        """Table cell words < 3 chars should not be counted (noise)."""
        text = "| я | I |\n| ти | you |"
        result = _score_claim_grounding(text, "beginner")
        # "я" and "ти" are 1-2 chars, excluded by {2,} requirement
        assert result["score"] == 0
