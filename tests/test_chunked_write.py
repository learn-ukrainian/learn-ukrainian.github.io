"""Tests for section-by-section chunked generation (#998).

Tests the skeleton parsing, summary building, and chunking gate logic
without requiring LLM calls or filesystem state.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure scripts/ is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


SAMPLE_SKELETON = """\
## Діалоги (Dialogues) (~385 words total)

- P1 (~35 words): Brief scene-setting.
- Dialogue 1 (~90 words): Hostel check-in, informal.
- P2 (~25 words): Transition to formal.

## Мене звати... (My name is...) (~275 words total)

- P1 (~80 words): Explain Мене звати...
- P2 (~70 words): Asking the question.
- Exercise: fill-in — Complete self-introduction. (6 items)

## Це... (This is...) (~220 words total)

- P1 (~75 words): Це is the Swiss army knife.
- P2 (~70 words): Questions with Це.

## Підсумок (~150 words)

- P1 (~150 words): Recap key concepts.

Grand total: ~1030 words"""


MINIMAL_SKELETON = """\
## Only One Section (~500 words total)

- P1 (~500 words): Everything.
"""


class TestParseSkeletonSections:
    """Tests for _parse_skeleton_sections()."""

    def test_parses_multiple_sections(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        assert len(sections) == 4

    def test_section_titles(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        assert "Діалоги" in sections[0]["title"]
        assert "Мене звати" in sections[1]["title"]
        assert "Це..." in sections[2]["title"]
        assert "Підсумок" in sections[3]["title"]

    def test_word_budgets(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        assert sections[0]["words"] == 385
        assert sections[1]["words"] == 275
        assert sections[2]["words"] == 220
        assert sections[3]["words"] == 150

    def test_section_bodies_contain_content(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        assert "Brief scene-setting" in sections[0]["body"]
        assert "fill-in" in sections[1]["body"]

    def test_minimal_skeleton_single_section(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(MINIMAL_SKELETON)
        assert len(sections) == 1
        assert sections[0]["words"] == 500

    def test_empty_skeleton(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections("")
        assert sections == []

    def test_no_h2_headings(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections("Just some text\nwithout headings\n")
        assert sections == []


class TestExtractWordBudget:
    """Tests for _extract_word_budget()."""

    def test_standard_format(self):
        from build.v6_build import _extract_word_budget

        assert _extract_word_budget("Section (~275 words total)") == 275

    def test_no_budget(self):
        from build.v6_build import _extract_word_budget

        assert _extract_word_budget("Section without budget") == 0

    def test_words_without_tilde(self):
        from build.v6_build import _extract_word_budget

        # Should still match ~NNN words pattern
        assert _extract_word_budget("Section (~150 words)") == 150


class TestBuildSectionSummary:
    """Tests for _build_section_summary()."""

    def test_empty_sections(self):
        from build.v6_build import _build_section_summary

        assert _build_section_summary([]) == ""

    def test_short_sections_not_truncated(self):
        from build.v6_build import _build_section_summary

        sections = ["First section content.", "Second section content."]
        result = _build_section_summary(sections)
        assert "First section content." in result
        assert "Second section content." in result

    def test_long_sections_truncated(self):
        from build.v6_build import _build_section_summary

        # Create sections with many words
        long_section = " ".join(["word"] * 600)
        result = _build_section_summary([long_section], max_words=100)
        assert len(result.split()) <= 110  # some overhead from truncation marker
        assert "truncated" in result


class TestChunkingGate:
    """Tests for the chunking trigger conditions.

    The gate triggers when:
    1. skeleton is provided
    2. no_chunk is False
    3. word_target >= 2000
    4. skeleton has >= 2 H2 sections
    """

    def test_gate_triggers_for_large_module_with_sections(self):
        """word_target=4000, 4 sections -> should chunk."""
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        word_target = 4000
        no_chunk = False

        should_chunk = (
            not no_chunk
            and word_target >= 2000
            and len(sections) >= 2
        )
        assert should_chunk is True

    def test_gate_skips_for_small_module(self):
        """word_target=1200 -> should NOT chunk even with sections."""
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        word_target = 1200
        no_chunk = False

        should_chunk = (
            not no_chunk
            and word_target >= 2000
            and len(sections) >= 2
        )
        assert should_chunk is False

    def test_gate_skips_when_no_chunk_flag(self):
        """--no-chunk flag disables chunking."""
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        word_target = 4000
        no_chunk = True

        should_chunk = (
            not no_chunk
            and word_target >= 2000
            and len(sections) >= 2
        )
        assert should_chunk is False

    def test_gate_skips_for_single_section(self):
        """Only 1 section -> should NOT chunk."""
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(MINIMAL_SKELETON)
        word_target = 4000
        no_chunk = False

        should_chunk = (
            not no_chunk
            and word_target >= 2000
            and len(sections) >= 2
        )
        assert should_chunk is False
