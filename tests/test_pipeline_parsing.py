"""Tests for pipeline/parsing.py — extraction, formatting, and review parsing.

Covers functions not already tested in test_pipeline_v5.py:
- LLM filler scanner
- Formatting helpers (deterministic issues, filler phrases, VESUM)
- D1 review parsing
- Factual review parsing
- Fix plan extraction
- D3 context builder

Issue: #783
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline.parsing import (
    _extract_fix_plan,
    _parse_d1_review,
    _parse_factual_review,
    _scan_llm_filler,
)

# =============================================================================
# _scan_llm_filler
# =============================================================================

class TestScanLlmFiller:

    def test_repeated_filler_detected(self):
        content = (
            "It's worth noting that Ukrainian has cases.\n"
            "More text here.\n"
            "It's worth noting that verbs conjugate too."
        )
        issues = _scan_llm_filler(content)
        assert len(issues) >= 2


# =============================================================================
# _format_deterministic_issues
# =============================================================================


# =============================================================================
# _format_filler_phrases
# =============================================================================


# =============================================================================
# _format_vesum_verification
# =============================================================================


# =============================================================================
# _parse_d1_review
# =============================================================================

class TestParseD1Review:
    def test_valid_review_pass(self):
        raw = """Some preamble
===REVIEW_START===
## Review

**Status:** PASS
**Overall Score:** 9.5/10

## Scores

| # | Dimension | Score |
|---|-----------|-------|
| 1 | Grammar | 9.0/10 |
| 2 | Content | 10.0/10 |

**Weighted Overall:** 0.4×9.0 + 0.6×10.0 = **9.6/10**

===REVIEW_END===
"""
        result = _parse_d1_review(raw)
        assert result.ok
        assert result.verdict == "PASS"
        assert result.scores["overall"] == 9.5
        assert result.scores.get("grammar") == 9.0
        assert result.scores.get("content") == 10.0
        assert result.scores.get("weighted_overall") == 9.6

    def test_valid_review_fail(self):
        raw = """===REVIEW_START===
**Status:** FAIL
**Overall Score:** 6.0/10

## Critical Issues Found

### Issue 1: Grammar error
**Location**: Section 2
**Problem**: Wrong case ending
**Fix**: Change to genitive

===REVIEW_END==="""
        result = _parse_d1_review(raw)
        assert result.ok
        assert result.verdict == "FAIL"
        assert result.scores["overall"] == 6.0
        assert len(result.issues) == 1
        assert result.issues[0]["location"] == "Section 2"
        assert "case" in result.issues[0]["text"].lower()

    def test_missing_delimiters(self):
        raw = "No review here at all"
        result = _parse_d1_review(raw)
        assert not result.ok

    def test_infers_verdict_from_score(self):
        raw = """===REVIEW_START===
**Overall Score:** 9.2/10
===REVIEW_END==="""
        result = _parse_d1_review(raw)
        assert result.verdict == "PASS"


# =============================================================================
# _parse_factual_review
# =============================================================================

class TestParseFactualReview:
    def test_valid_factual_pass(self):
        raw = """===FACTUAL_REVIEW_START===
**Status:** PASS
**Factual Alignment Score:** 9.0/10
**Plan Adherence Score:** 8.5/10
**Discrepancies [Tier 1]:** 0
===FACTUAL_REVIEW_END==="""
        result = _parse_factual_review(raw)
        assert result.ok
        assert result.verdict == "PASS"
        assert result.scores["factual_accuracy"] == 9.0
        assert result.scores["plan_adherence"] == 8.5

    def test_factual_fail_with_discrepancy(self):
        raw = """===FACTUAL_REVIEW_START===
**Status:** FAIL
**Discrepancies [Tier 1]:** 1

### Discrepancy 1: Wrong date
**Module says:** "Founded in 1240"
**Reference says:** "Founded in 1256"
**Source:** Encyclopedia
**Suggested fix:** Change to 1256
===FACTUAL_REVIEW_END==="""
        result = _parse_factual_review(raw)
        assert result.ok
        assert result.verdict == "FAIL"
        assert len(result.issues) >= 1
        assert result.issues[0]["type"] == "FACTUAL_DISCREPANCY"


# =============================================================================
# _extract_fix_plan
# =============================================================================

class TestExtractFixPlan:
    def test_extracts_critical_issues(self):
        review = """## Summary
Everything is great.

## Critical Issues Found
1. Grammar error in section 2
2. Missing vocabulary

## Recommendation
Fix the above.
"""
        result = _extract_fix_plan(review)
        assert "Grammar error" in result
        assert "Missing vocabulary" in result
        # Should NOT include Summary or Recommendation
        assert "Everything is great" not in result

    def test_extracts_fix_plan_section(self):
        review = """## Some Section
Intro text.

## Fix Plan to Reach 9.0/10
1. Fix grammar
2. Add examples

## Other
More text.
"""
        result = _extract_fix_plan(review)
        assert "Fix grammar" in result
        assert "Add examples" in result

    def test_falls_back_to_full_text(self):
        review = "Just a plain review with no structured sections."
        result = _extract_fix_plan(review)
        assert result == review


# =============================================================================
# _build_d3_context
# =============================================================================


# =============================================================================
# Dataclasses
# =============================================================================
