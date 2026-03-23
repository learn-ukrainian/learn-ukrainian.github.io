"""Tests for V6 review correction directive (#1025).

Tests PATCH-only mode (never rewrite from scratch) and словник filtering.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.v6_build import _build_review_correction, _parse_review_fixes

SAMPLE_REVIEW = """## Linguistic Scan
Found 1 issue: словник table has wrong translation for "голосні" → "plaudit" (should be "vowels").

## Exercise Check
All exercises correct.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All sections covered |
| 2. Linguistic accuracy | 8/10 | Minor issue in словник |

## Findings
[DIMENSION 2] [SEVERITY: major]
Location: Словник table
Issue: Wrong translation for голосні
Fix: Change to "vowels"

[DIMENSION 6] [SEVERITY: minor]
Location: Section 2, paragraph 3
Issue: Slightly formal tone
Fix: Use more conversational phrasing

## Verdict: REVISE
"""


class TestAlwaysPatchNeverRewrite:
    """Correction directive is ALWAYS patch — rewriting from scratch is banned."""

    def test_high_score_is_patch(self):
        result = _build_review_correction(SAMPLE_REVIEW, score=8.5)
        assert "Do NOT rewrite from scratch" in result
        assert "Keep the existing content intact" in result

    def test_low_score_is_also_patch(self):
        result = _build_review_correction(SAMPLE_REVIEW, score=5.0)
        assert "Do NOT rewrite from scratch" in result
        assert "Rewrite the module" not in result
        assert "FROM SCRATCH" not in result.replace("Do NOT rewrite from scratch", "")

    def test_zero_score_still_patch(self):
        result = _build_review_correction(SAMPLE_REVIEW, score=0.0)
        assert "Do NOT rewrite from scratch" in result

    def test_fix_only_specific_issues(self):
        result = _build_review_correction(SAMPLE_REVIEW, score=7.0)
        assert "Fix ONLY the specific issues" in result
        assert "Change as little as possible" in result


class TestSlovnykFiltering:
    """Словник findings are filtered — ENRICH's problem, not writer's."""

    def test_slovnyk_findings_filtered(self):
        result = _build_review_correction(SAMPLE_REVIEW, score=7.0)
        assert "plaudit" not in result

    def test_slovnyk_linguistic_scan_filtered(self):
        result = _build_review_correction(SAMPLE_REVIEW, score=7.0)
        assert "plaudit" not in result

    def test_tone_finding_kept(self):
        result = _build_review_correction(SAMPLE_REVIEW, score=7.0)
        assert "formal tone" in result or "NOTE" in result

    def test_non_slovnyk_findings_kept(self):
        review = """## Linguistic Scan
Found Russicism: хорошо should be добре.

## Findings
[DIMENSION 2] [SEVERITY: critical]
Location: Section 1
Issue: Russicism хорошо used
Fix: Replace with добре

## Verdict: REJECT
"""
        result = _build_review_correction(review, score=6.0)
        assert "хорошо" in result or "Russicism" in result

    def test_orphaned_lines_not_leaked(self):
        """Multi-line словник finding must be dropped as a whole block,
        not line-by-line (which would orphan Location/Issue/Fix lines)."""
        result = _build_review_correction(SAMPLE_REVIEW, score=7.0)
        # The entire словник block should be gone — no orphaned lines
        assert "Change to" not in result  # Fix line from словник block
        assert "Wrong translation" not in result  # Issue line from словník block
        # But the tone finding should survive intact
        assert "conversational" in result or "formal" in result

    def test_video_finding_filtered(self):
        """Video/YouTube findings are ENRICH-generated, should be filtered."""
        review = """## Findings
[DIMENSION 7] [SEVERITY: minor]
Location: Resources section
Issue: YouTube video embed is broken
Fix: Fix the URL

[DIMENSION 2] [SEVERITY: major]
Location: Section 1
Issue: Wrong case ending on дієслово
Fix: Use дієслова (genitive)

## Verdict: REVISE
"""
        result = _build_review_correction(review, score=7.5)
        assert "YouTube" not in result
        assert "дієслово" in result or "case ending" in result


class TestEnrichDisclaimer:
    """Every correction tells writer to ignore словник issues."""

    def test_disclaimer_present(self):
        result = _build_review_correction(SAMPLE_REVIEW, score=9.0)
        assert "downstream tool" in result.lower()

    def test_disclaimer_at_any_score(self):
        result = _build_review_correction(SAMPLE_REVIEW, score=4.0)
        assert "downstream tool" in result.lower()


class TestParseReviewFixes:
    """Parse <fixes> YAML from reviewer output."""

    def test_parse_simple_fixes(self):
        review = """## Verdict: REVISE

<fixes>
- find: "**кон** (an archaic word)"
  replace: "**лан** (field)"
- find: "м'якшені"
  replace: "пом'якшені"
</fixes>
"""
        fixes = _parse_review_fixes(review)
        assert len(fixes) == 2
        assert fixes[0]["find"] == "**кон** (an archaic word)"
        assert fixes[0]["replace"] == "**лан** (field)"
        assert fixes[1]["find"] == "м'якшені"
        assert fixes[1]["replace"] == "пом'якшені"

    def test_no_fixes_block(self):
        review = "## Verdict: PASS\nAll good."
        assert _parse_review_fixes(review) == []

    def test_insert_after(self):
        review = """<fixes>
- insert_after: "## Підсумок"
  replace: "Extra paragraph here."
</fixes>"""
        fixes = _parse_review_fixes(review)
        assert len(fixes) == 1
        assert fixes[0]["insert_after"] == "## Підсумок"

    def test_malformed_yaml_returns_empty(self):
        review = """<fixes>
this is not valid yaml: [[[
</fixes>"""
        assert _parse_review_fixes(review) == []

    def test_empty_fixes_block(self):
        review = """<fixes>
</fixes>"""
        assert _parse_review_fixes(review) == []

    def test_content_alias_for_replace(self):
        """Gemini sometimes uses 'content:' instead of 'replace:' for insert_after."""
        review = """<fixes>
- insert_after: "some text"
  content: "new paragraph here"
</fixes>"""
        fixes = _parse_review_fixes(review)
        assert len(fixes) == 1
        assert fixes[0]["replace"] == "new paragraph here"
        assert "content" not in fixes[0]
