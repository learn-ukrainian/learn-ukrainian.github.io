"""
Tests for scripts/gemini_output.py — Gemini output extraction utilities.

Covers: basic extraction, missing delimiters, thinking token stripping,
YAML parsing, validation, truncation detection, edge cases.
"""

import os
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.gemini_output import (
    ALL_TAGS,
    PHASE_TAGS,
    extract_delimited,
    extract_yaml,
    find_complete_pairs,
    find_missing_pairs,
    has_any_end_marker,
    has_complete_pair,
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

    def test_multiline_content(self):
        text = (
            "===CONTENT_START===\n"
            "# Title\n\n"
            "Paragraph one.\n\n"
            "Paragraph two.\n"
            "===CONTENT_END==="
        )
        result = extract_delimited(text, "CONTENT")
        assert "# Title" in result
        assert "Paragraph two." in result

    def test_strips_whitespace(self):
        text = "===CONTENT_START===\n\n  hello  \n\n===CONTENT_END==="
        assert extract_delimited(text, "CONTENT") == "hello"

    def test_missing_start(self):
        text = "some text ===CONTENT_END==="
        assert extract_delimited(text, "CONTENT") is None

    def test_missing_end(self):
        text = "===CONTENT_START=== some text"
        assert extract_delimited(text, "CONTENT") is None

    def test_missing_both(self):
        assert extract_delimited("just plain text", "CONTENT") is None

    def test_empty_content(self):
        text = "===CONTENT_START===\n===CONTENT_END==="
        assert extract_delimited(text, "CONTENT") == ""

    def test_thinking_tokens_stripped(self):
        """Thinking tokens before/after delimiters are discarded."""
        text = (
            "Let me think about this...\n"
            "Okay, I'll structure the content as follows:\n"
            "- First section on grammar\n"
            "- Second section on vocabulary\n"
            "\n"
            "===CONTENT_START===\n"
            "# Actual lesson content\n"
            "===CONTENT_END===\n"
            "\n"
            "I hope that's helpful! Let me know if you need changes."
        )
        result = extract_delimited(text, "CONTENT")
        assert result == "# Actual lesson content"
        assert "think about" not in result
        assert "helpful" not in result

    def test_different_tags(self):
        text = (
            "===RESEARCH_START===\nresearch\n===RESEARCH_END===\n"
            "===CONTENT_START===\ncontent\n===CONTENT_END==="
        )
        assert extract_delimited(text, "RESEARCH") == "research"
        assert extract_delimited(text, "CONTENT") == "content"

    def test_tag_with_special_chars(self):
        """Tags are regex-escaped so special chars don't break matching."""
        text = "===META_OUTLINE_START===\ndata\n===META_OUTLINE_END==="
        assert extract_delimited(text, "META_OUTLINE") == "data"

    def test_first_match_wins(self):
        """If same tag appears twice, first complete pair wins (non-greedy)."""
        text = (
            "===CONTENT_START===\nfirst\n===CONTENT_END===\n"
            "===CONTENT_START===\nsecond\n===CONTENT_END==="
        )
        assert extract_delimited(text, "CONTENT") == "first"


# =============================================================================
# extract_yaml
# =============================================================================


class TestExtractYaml:
    """YAML parsing from delimited content."""

    def test_yaml_dict(self):
        text = "===META_OUTLINE_START===\ntitle: Test\nword_target: 3000\n===META_OUTLINE_END==="
        result = extract_yaml(text, "META_OUTLINE")
        assert result == {"title": "Test", "word_target": 3000}

    def test_yaml_list(self):
        text = (
            "===ACTIVITIES_START===\n"
            "- type: quiz\n"
            "  title: Test Quiz\n"
            "- type: fill-in\n"
            "  title: Fill Exercise\n"
            "===ACTIVITIES_END==="
        )
        result = extract_yaml(text, "ACTIVITIES")
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["type"] == "quiz"

    def test_yaml_parse_error(self):
        text = "===ACTIVITIES_START===\n{{invalid yaml\n===ACTIVITIES_END==="
        assert extract_yaml(text, "ACTIVITIES") is None

    def test_yaml_missing_delimiters(self):
        assert extract_yaml("no delimiters here", "ACTIVITIES") is None

    def test_yaml_with_unicode(self):
        text = "===VOCABULARY_START===\n- word: привіт\n  translation: hello\n===VOCABULARY_END==="
        result = extract_yaml(text, "VOCABULARY")
        assert result[0]["word"] == "привіт"


# =============================================================================
# has_complete_pair / find_complete_pairs / find_missing_pairs
# =============================================================================


class TestPairDetection:
    """Delimiter pair detection for truncation handling."""

    def test_has_complete_pair_true(self):
        text = "===CONTENT_START===\nstuff\n===CONTENT_END==="
        assert has_complete_pair(text, "CONTENT") is True

    def test_has_complete_pair_false_no_end(self):
        text = "===CONTENT_START===\nstuff"
        assert has_complete_pair(text, "CONTENT") is False

    def test_has_complete_pair_false_no_start(self):
        text = "stuff\n===CONTENT_END==="
        assert has_complete_pair(text, "CONTENT") is False

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

    def test_find_missing_pairs(self):
        text = (
            "===CONTENT_START===\ncontent\n===CONTENT_END===\n"
            "===ACTIVITIES_START===\nacts (truncated)"
        )
        missing = find_missing_pairs(
            text, ["CONTENT", "ACTIVITIES", "VOCABULARY"]
        )
        assert "ACTIVITIES" in missing
        assert "VOCABULARY" in missing
        assert "CONTENT" not in missing


# =============================================================================
# has_any_end_marker
# =============================================================================


class TestHasAnyEndMarker:

    def test_standard_end_marker(self):
        assert has_any_end_marker("===CONTENT_END===") is True

    def test_legacy_end_marker(self):
        assert has_any_end_marker("---END---") is True

    def test_no_marker(self):
        assert has_any_end_marker("just plain text") is False


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

    def test_empty_output(self):
        result = validate_output("", ["CONTENT"])
        assert result["valid"] is False
        assert result["missing"] == ["CONTENT"]
        assert result["truncated"] == []


# =============================================================================
# PHASE_TAGS constant
# =============================================================================


class TestPhaseTags:
    """Verify PHASE_TAGS constant is correct."""

    def test_phase_0(self):
        assert PHASE_TAGS[0] == ["RESEARCH"]

    def test_phase_1(self):
        assert PHASE_TAGS[1] == ["META_OUTLINE"]

    def test_phase_2(self):
        assert PHASE_TAGS[2] == ["CONTENT"]

    def test_phase_3(self):
        assert PHASE_TAGS[3] == ["ACTIVITIES", "VOCABULARY"]

    def test_phase_5(self):
        assert PHASE_TAGS[5] == ["REVIEW"]

    def test_phase_fix(self):
        assert "CONTENT" in PHASE_TAGS["fix"]
        assert "CHANGES" in PHASE_TAGS["fix"]

    def test_all_tags_complete(self):
        """ALL_TAGS should contain every unique tag from PHASE_TAGS."""
        all_from_phases = {tag for tags in PHASE_TAGS.values() for tag in tags}
        assert set(ALL_TAGS) == all_from_phases
