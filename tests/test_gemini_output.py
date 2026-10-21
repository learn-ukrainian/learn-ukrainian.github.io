"""
Tests for scripts/gemini_output.py — Gemini output extraction utilities.

Covers: basic extraction, missing delimiters, thinking token stripping,
YAML parsing, validation, truncation detection, edge cases.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.gemini_output import (
    extract_delimited,
    extract_yaml,
    find_complete_pairs,
    has_any_end_marker,
    validate_output,
)

# =============================================================================
# extract_delimited
# =============================================================================


class TestExtractDelimited:
    """Basic delimiter extraction."""

    def test_simple_extraction(self):
        text = "noise ===CONTENT_START===\nHello world\n===CONTENT_END=== more noise"
        assert extract_delimited(text, "CONTENT") == "Hello world"

    def test_missing_end(self):
        text = "===CONTENT_START=== some text"
        assert extract_delimited(text, "CONTENT") is None

    def test_last_match_wins(self):
        """If same tag appears twice, last complete pair wins.

        Gemini often echoes the template delimiters before writing its actual
        output, so the first match is typically the template echo and the last
        match is the real content.
        """
        text = (
            "===CONTENT_START===\ntemplate echo\n===CONTENT_END===\n"
            "===CONTENT_START===\nreal content\n===CONTENT_END==="
        )
        assert extract_delimited(text, "CONTENT") == "real content"


# =============================================================================
# extract_yaml
# =============================================================================


class TestExtractYaml:
    """YAML parsing from delimited content."""

    def test_yaml_dict(self):
        text = "===META_OUTLINE_START===\ntitle: Test\nword_target: 3000\n===META_OUTLINE_END==="
        result = extract_yaml(text, "META_OUTLINE")
        assert result == {"title": "Test", "word_target": 3000}

    def test_yaml_parse_error(self):
        text = "===ACTIVITIES_START===\n{{invalid yaml\n===ACTIVITIES_END==="
        assert extract_yaml(text, "ACTIVITIES") is None


# =============================================================================
# has_complete_pair / find_complete_pairs / find_missing_pairs
# =============================================================================


class TestPairDetection:
    """Delimiter pair detection for truncation handling."""

    def test_find_complete_pairs(self):
        text = (
            "===CONTENT_START===\ncontent\n===CONTENT_END===\n"
            "===ACTIVITIES_START===\nacts\n===ACTIVITIES_END===\n"
            "===VOCABULARY_START===\nvocab (truncated)"
        )
        complete = find_complete_pairs(
            text, ["CONTENT", "ACTIVITIES", "VOCABULARY", "CHANGES"]
        )
        assert complete == ["CONTENT", "ACTIVITIES"]


# =============================================================================
# has_any_end_marker
# =============================================================================


class TestHasAnyEndMarker:

    def test_standard_end_marker(self):
        assert has_any_end_marker("===CONTENT_END===") is True

    def test_legacy_end_marker(self):
        assert has_any_end_marker("---END---") is True


# =============================================================================
# validate_output
# =============================================================================


class TestValidateOutput:
    """Full output validation."""

    def test_all_present(self):
        text = (
            "===CONTENT_START===\ncontent\n===CONTENT_END===\n"
            "===ACTIVITIES_START===\n- type: quiz\n===ACTIVITIES_END===\n"
            "===VOCABULARY_START===\n- word: test\n===VOCABULARY_END==="
        )
        result = validate_output(text, ["CONTENT", "ACTIVITIES", "VOCABULARY"])
        assert result["valid"] is True
        assert result["complete"] == ["CONTENT", "ACTIVITIES", "VOCABULARY"]
        assert result["missing"] == []
        assert result["truncated"] == []

    def test_partial_truncation(self):
        text = (
            "===CONTENT_START===\ncontent\n===CONTENT_END===\n"
            "===ACTIVITIES_START===\n- type: quiz (output cut off here)"
        )
        result = validate_output(text, ["CONTENT", "ACTIVITIES", "VOCABULARY"])
        assert result["valid"] is False
        assert result["complete"] == ["CONTENT"]
        assert "ACTIVITIES" in result["truncated"]
        assert "VOCABULARY" in result["missing"]
        assert "VOCABULARY" not in result["truncated"]  # never started


# =============================================================================
# PHASE_TAGS constant
# =============================================================================
