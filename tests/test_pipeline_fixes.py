"""Tests for pipeline/fixes.py — FIND/REPLACE parsing and text cleaning.

Covers pure functions that don't require ModuleContext or file I/O:
- _clean_fix_text (strip LLM formatting artifacts)
- _count_diff_lines (diff line counting)
- _apply_find_replace_fixes (FIND/REPLACE parser, uses tmp files)

Issue: #783
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline.fixes import (
    _clean_fix_text,
    _count_diff_lines,
    _apply_find_replace_fixes,
)


# =============================================================================
# _clean_fix_text
# =============================================================================

class TestCleanFixText:
    def test_plain_text_unchanged(self):
        assert _clean_fix_text("hello world") == "hello world"

    def test_strips_section_metadata(self):
        text = 'Section: "Introduction"\nActual content here'
        result = _clean_fix_text(text)
        assert "Section:" not in result
        assert "Actual content here" in result

    def test_strips_code_fences(self):
        text = "```markdown\nSome text\n```"
        result = _clean_fix_text(text)
        assert "```" not in result
        assert "Some text" in result

    def test_strips_guillemets(self):
        assert _clean_fix_text("«some text»") == "some text"

    def test_strips_german_quotes(self):
        assert _clean_fix_text("\u201esome text\u201c") == "some text"

    def test_empty_string(self):
        assert _clean_fix_text("") == ""

    def test_whitespace_only(self):
        assert _clean_fix_text("   \n   ") == ""

    def test_mixed_artifacts(self):
        text = '```\nSection: "Verbs"\nClean line\n```'
        result = _clean_fix_text(text)
        assert "Clean line" in result
        assert "```" not in result
        assert "Section:" not in result

    def test_preserves_internal_indentation(self):
        text = "line one\n    more indented"
        result = _clean_fix_text(text)
        assert "    more indented" in result

    def test_section_with_left_quote(self):
        text = 'Section: \u201cIntro\nContent'
        result = _clean_fix_text(text)
        assert "Section:" not in result
        assert "Content" in result

    def test_section_with_angle_quote(self):
        text = 'Section: \u00abIntro\nContent'
        result = _clean_fix_text(text)
        assert "Section:" not in result


# =============================================================================
# _count_diff_lines
# =============================================================================

class TestCountDiffLines:
    def test_identical_texts(self):
        assert _count_diff_lines("hello\nworld", "hello\nworld") == 0

    def test_one_line_changed(self):
        assert _count_diff_lines("hello\nworld", "hello\nearth") == 2  # -world +earth

    def test_line_added(self):
        assert _count_diff_lines("hello", "hello\nworld") >= 1

    def test_line_removed(self):
        assert _count_diff_lines("hello\nworld", "hello") >= 1

    def test_empty_to_content(self):
        count = _count_diff_lines("", "new content")
        assert count >= 1

    def test_content_to_empty(self):
        count = _count_diff_lines("some content", "")
        assert count >= 1

    def test_both_empty(self):
        assert _count_diff_lines("", "") == 0

    def test_multiline_change(self):
        before = "line1\nline2\nline3"
        after = "line1\nchanged\nline3"
        count = _count_diff_lines(before, after)
        assert count == 2  # -line2 +changed


# =============================================================================
# _apply_find_replace_fixes (with tmp files)
# =============================================================================

class TestApplyFindReplaceFixes:
    def test_basic_replacement(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("Hello world. This is a test.", "utf-8")
        raw = """===SECTION_FIX_START===
FIND:
Hello world
REPLACE:
Привіт світ
===SECTION_FIX_END==="""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 1
        assert "Привіт світ" in f.read_text("utf-8")

    def test_multiple_replacements(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("AAA BBB CCC", "utf-8")
        raw = """===SECTION_FIX_START===
FIND:
AAA
REPLACE:
XXX
---
FIND:
BBB
REPLACE:
YYY
===SECTION_FIX_END==="""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 2
        content = f.read_text("utf-8")
        assert "XXX" in content
        assert "YYY" in content

    def test_no_match_skipped(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("Hello world", "utf-8")
        raw = """===SECTION_FIX_START===
FIND:
nonexistent text
REPLACE:
replacement
===SECTION_FIX_END==="""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 0
        assert f.read_text("utf-8") == "Hello world"

    def test_empty_find_skipped(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("Hello world", "utf-8")
        raw = """===SECTION_FIX_START===
FIND:

REPLACE:
replacement
===SECTION_FIX_END==="""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 0

    def test_identical_find_replace_skipped(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("Hello world", "utf-8")
        raw = """===SECTION_FIX_START===
FIND:
Hello world
REPLACE:
Hello world
===SECTION_FIX_END==="""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 0

    def test_no_fix_block(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("Hello world", "utf-8")
        count = _apply_find_replace_fixes(f, "No fix blocks here")
        assert count == 0

    def test_nonexistent_file(self, tmp_path):
        f = tmp_path / "nonexistent.md"
        count = _apply_find_replace_fixes(f, "===SECTION_FIX_START===\nFIND:\nX\nREPLACE:\nY\n===SECTION_FIX_END===")
        assert count == 0

    def test_file_routing(self, tmp_path):
        f = tmp_path / "content.md"
        f.write_text("Hello world", "utf-8")
        raw = """===SECTION_FIX_START===
FILE: other.yaml
FIND:
Hello
REPLACE:
Goodbye
---
FILE: content.md
FIND:
world
REPLACE:
земля
===SECTION_FIX_END==="""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 1
        content = f.read_text("utf-8")
        assert "земля" in content
        assert "Hello" in content  # first fix was for different file

    def test_whitespace_normalized_match(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("Hello\n  world", "utf-8")
        raw = """===SECTION_FIX_START===
FIND:
Hello world
REPLACE:
Привіт світ
===SECTION_FIX_END==="""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 1
        assert "Привіт світ" in f.read_text("utf-8")
