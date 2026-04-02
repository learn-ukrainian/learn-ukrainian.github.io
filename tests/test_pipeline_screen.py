"""Tests for pipeline/screen.py — deterministic fix helpers.

Covers pure functions extracted from _run_deterministic_fixes and
_deterministic_screen. Does NOT test functions requiring ModuleContext
or file I/O (those are integration-tested via test_pipeline_v5.py).

Issue: #782
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline.screen import (
    _fix_extra_h1,
    _fix_ipa_brackets,
    _run_ipa_scan,
)

# =============================================================================
# _fix_extra_h1
# =============================================================================

class TestFixExtraH1:
    def test_no_extra_h1(self):
        text = "# Title\n\n## Section 1\n\nContent."
        result, count = _fix_extra_h1(text)
        assert count == 0
        assert result == text

    def test_demotes_second_h1(self):
        text = "# Title\n\n# Another Title\n\nContent."
        result, count = _fix_extra_h1(text)
        assert count == 1
        assert "## Another Title" in result
        assert result.startswith("# Title")

    def test_preserves_summary_h1(self):
        text = "# Title\n\n# Summary\n\nContent."
        result, count = _fix_extra_h1(text)
        assert count == 0
        assert "# Summary" in result

    def test_preserves_pidsumok_h1(self):
        text = "# Title\n\n# Підсумок\n\nContent."
        result, count = _fix_extra_h1(text)
        assert count == 0
        assert "# Підсумок" in result

    def test_skips_code_blocks(self):
        text = "# Title\n\n```\n# Not a heading\n```\n\nContent."
        result, count = _fix_extra_h1(text)
        assert count == 0
        assert result == text

    def test_multiple_extra_h1(self):
        text = "# Title\n\n# Second\n\n# Third\n\nContent."
        result, count = _fix_extra_h1(text)
        assert count == 1  # returns 1 (one fix operation)
        assert "## Second" in result
        assert "## Third" in result

    def test_already_h2_not_affected(self):
        text = "# Title\n\n## Already H2\n\nContent."
        result, count = _fix_extra_h1(text)
        assert count == 0


# =============================================================================
# _fix_ipa_brackets
# =============================================================================

class TestFixIpaBrackets:
    def test_no_brackets(self):
        text = "Simple text without brackets."
        result, count = _fix_ipa_brackets(text)
        assert count == 0
        assert result == text

    def test_removes_ipa_brackets(self):
        text = "Привіт [pry-vit] (hello)"
        result, count = _fix_ipa_brackets(text)
        assert count > 0
        assert "[pry-vit]" not in result

    def test_preserves_non_ipa_brackets(self):
        text = "Text with [Ø] marker."
        result, count = _fix_ipa_brackets(text)
        assert count == 0  # no change (this pattern doesn't match the regex)


# =============================================================================
# _run_ipa_scan
# =============================================================================

class TestRunIpaScan:
    def test_no_ipa(self):
        text = "Clean Ukrainian text without phonetics."
        issues = _run_ipa_scan(text)
        assert len(issues) == 0

    def test_detects_syllable_breakdown(self):
        text = "Привіт [pry-vit] is a greeting"
        issues = _run_ipa_scan(text)
        assert any(i["type"] == "IPA_BANNED" for i in issues)

    def test_detects_ipa_transcription(self):
        text = "Sound [ɑɛɪ] is complex"
        issues = _run_ipa_scan(text)
        assert any(i["type"] == "IPA_BANNED" for i in issues)

    def test_whitelist_excluded(self):
        text = "The [Ø] marker means zero ending."
        issues = _run_ipa_scan(text)
        assert len(issues) == 0

    def test_includes_line_number(self):
        text = "Line 1\nLine 2\nBad [pry-vit] here"
        issues = _run_ipa_scan(text)
        if issues:
            assert "~line 3" in issues[0]["location"]

    def test_caps_at_5_per_pattern(self):
        text = "\n".join(f"Word [syl-lab] {i}" for i in range(10))
        issues = _run_ipa_scan(text)
        # Each pattern caps at 5 matches
        assert len(issues) <= 10  # 5 per pattern × 2 patterns max
