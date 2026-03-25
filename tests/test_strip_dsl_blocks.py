"""Tests for _strip_dsl_blocks in v6_build.py.

Verifies that legacy DSL exercise blocks (:::quiz, :::fill-in, etc.)
are correctly stripped from content when activities YAML exists.

Issue: #1045
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build.v6_build import _strip_dsl_blocks


class TestStripDslBlocks:
    """Tests for _strip_dsl_blocks."""

    def test_strips_quiz_block(self):
        text = (
            "Some prose before.\n\n"
            ":::quiz\n"
            'title: "Test quiz"\n'
            "---\n"
            '- q: "Question?"\n'
            '  o: ["a", "b", "c"]\n'
            "  a: 0\n"
            ":::\n\n"
            "Some prose after."
        )
        result, count = _strip_dsl_blocks(text)
        assert count == 1
        assert ":::quiz" not in result
        assert "Some prose before." in result
        assert "Some prose after." in result

    def test_strips_fill_in_block(self):
        text = (
            "Content.\n\n"
            ":::fill-in\n"
            'title: "Fill"\n'
            "---\n"
            '- sentence: "Привіт! Як ___?"\n'
            '  answer: "справи"\n'
            ":::\n\n"
            "More content."
        )
        result, count = _strip_dsl_blocks(text)
        assert count == 1
        assert ":::fill-in" not in result

    def test_strips_match_up_block(self):
        text = (
            ":::match-up\n"
            'title: "Match"\n'
            "---\n"
            '- left: "А"\n'
            '  right: "vowel"\n'
            ":::\n"
        )
        result, count = _strip_dsl_blocks(text)
        assert count == 1
        assert ":::match-up" not in result

    def test_strips_group_sort_block(self):
        text = (
            ":::group-sort\n"
            'title: "Sort"\n'
            "---\n"
            "groups:\n"
            '  - name: "A"\n'
            '    items: ["x"]\n'
            ":::\n"
        )
        result, count = _strip_dsl_blocks(text)
        assert count == 1
        assert ":::group-sort" not in result

    def test_strips_true_false_block(self):
        text = (
            ":::true-false\n"
            'title: "TF"\n'
            "---\n"
            '- statement: "Fact"\n'
            "  answer: true\n"
            ":::\n"
        )
        result, count = _strip_dsl_blocks(text)
        assert count == 1
        assert ":::true-false" not in result

    def test_strips_multiple_blocks(self):
        text = (
            "Intro.\n\n"
            ":::quiz\n"
            "---\n"
            '- q: "Q1"\n'
            ":::\n\n"
            "Middle.\n\n"
            ":::fill-in\n"
            "---\n"
            '- sentence: "___"\n'
            '  answer: "x"\n'
            ":::\n\n"
            "End."
        )
        result, count = _strip_dsl_blocks(text)
        assert count == 2
        assert ":::quiz" not in result
        assert ":::fill-in" not in result
        assert "Intro." in result
        assert "Middle." in result
        assert "End." in result

    def test_preserves_non_exercise_blocks(self):
        """:::tip, :::note, :::caution should NOT be stripped."""
        text = (
            ":::tip\n"
            "This is a tip.\n"
            ":::\n\n"
            ":::note\n"
            "This is a note.\n"
            ":::\n\n"
            ":::caution\n"
            "Be careful.\n"
            ":::\n"
        )
        result, count = _strip_dsl_blocks(text)
        assert count == 0
        assert ":::tip" in result
        assert ":::note" in result
        assert ":::caution" in result

    def test_preserves_injection_markers(self):
        text = (
            "<!-- INJECT_ACTIVITY: quiz-sounds -->\n\n"
            ":::quiz\n"
            "---\n"
            '- q: "Q"\n'
            ":::\n\n"
            "<!-- INJECT_ACTIVITY: fill-greeting -->\n"
        )
        result, count = _strip_dsl_blocks(text)
        assert count == 1
        assert "<!-- INJECT_ACTIVITY: quiz-sounds -->" in result
        assert "<!-- INJECT_ACTIVITY: fill-greeting -->" in result
        assert ":::quiz" not in result

    def test_no_triple_blank_lines(self):
        """Stripping blocks should not leave more than double blank lines."""
        text = (
            "Before.\n\n"
            ":::quiz\n"
            "---\n"
            ":::\n\n"
            "After."
        )
        result, _ = _strip_dsl_blocks(text)
        assert "\n\n\n" not in result

    def test_empty_content_returns_zero(self):
        result, count = _strip_dsl_blocks("")
        assert count == 0
        assert result == ""

    def test_no_dsl_returns_unchanged(self):
        text = "Just prose with no exercises.\n\nMore prose."
        result, count = _strip_dsl_blocks(text)
        assert count == 0
        assert result == text
