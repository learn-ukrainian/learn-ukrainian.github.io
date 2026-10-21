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

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline.fixes import (
    _apply_find_replace_fixes,
)

# =============================================================================
# _clean_fix_text
# =============================================================================


# =============================================================================
# _count_diff_lines
# =============================================================================


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
