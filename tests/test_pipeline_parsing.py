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
    D1Result,
    DScreenResult,
    _build_d3_context,
    _extract_fix_plan,
    _format_deterministic_issues,
    _format_filler_phrases,
    _format_vesum_verification,
    _parse_d1_review,
    _parse_factual_review,
    _scan_llm_filler,
)

# =============================================================================
# _scan_llm_filler
# =============================================================================

class TestScanLlmFiller:
    def test_no_filler(self):
        content = "This is clean text about Ukrainian grammar.\nNo filler here."
        issues = _scan_llm_filler(content)
        assert len(issues) == 0

    def test_always_match_lesson_opener(self):
        content = "In this lesson, we will explore Ukrainian verbs."
        issues = _scan_llm_filler(content)
        assert len(issues) >= 1
        assert any(i["type"] == "LLM_FILLER" for i in issues)

    def test_repeated_filler_detected(self):
        content = (
            "It's worth noting that Ukrainian has cases.\n"
            "More text here.\n"
            "It's worth noting that verbs conjugate too."
        )
        issues = _scan_llm_filler(content)
        assert len(issues) >= 2

    def test_single_occurrence_not_flagged(self):
        content = "It's worth noting that Ukrainian is beautiful."
        issues = _scan_llm_filler(content)
        # Single occurrence of non-always patterns should not flag
        assert len(issues) == 0

    def test_ukrainian_filler_detected(self):
        content = (
            "давайте розглянемо цю тему.\n"
            "Ще трохи тексту.\n"
            "давайте розглянемо інший приклад."
        )
        issues = _scan_llm_filler(content)
        assert len(issues) >= 2

    def test_skips_blockquotes(self):
        content = (
            "> In this lesson, we will explore verbs.\n"
            "> In this lesson, we will explore nouns.\n"
        )
        issues = _scan_llm_filler(content)
        # Lines starting with > are skipped
        assert len(issues) == 0

    def test_skips_code_fence_lines(self):
        # The scanner skips lines starting with ``` but NOT content between fences
        content = "```python\n```\n```javascript\n```"
        issues = _scan_llm_filler(content)
        assert len(issues) == 0


# =============================================================================
# _format_deterministic_issues
# =============================================================================

class TestFormatDeterministicIssues:
    def test_empty_issues(self):
        result = _format_deterministic_issues([])
        assert "No deterministic issues" in result

    def test_single_issue(self):
        issues = [{"type": "RUSSICISM", "severity": "HIGH",
                    "location": "line 42", "text": "кот", "fix": "кіт"}]
        result = _format_deterministic_issues(issues)
        assert "RUSSICISM" in result
        assert "HIGH" in result
        assert "line 42" in result
        assert "кот" in result
        assert "кіт" in result

    def test_truncates_long_text(self):
        issues = [{"type": "TEST", "severity": "LOW",
                    "text": "x" * 200, "fix": "y" * 200}]
        result = _format_deterministic_issues(issues)
        assert len(result) < 500


# =============================================================================
# _format_filler_phrases
# =============================================================================

class TestFormatFillerPhrases:
    def test_no_filler(self):
        result = _format_filler_phrases([{"type": "RUSSICISM"}])
        assert "No LLM filler" in result

    def test_with_filler(self):
        issues = [
            {"type": "LLM_FILLER", "text": "Let's explore", "location": "~line 5"},
            {"type": "RUSSICISM", "text": "кот"},
        ]
        result = _format_filler_phrases(issues)
        assert "Let's explore" in result
        assert "~line 5" in result

    def test_caps_at_10(self):
        issues = [
            {"type": "LLM_FILLER", "text": f"phrase {i}", "location": f"line {i}"}
            for i in range(15)
        ]
        result = _format_filler_phrases(issues)
        # Should only show first 10
        assert "phrase 9" in result
        assert "phrase 10" not in result


# =============================================================================
# _format_vesum_verification
# =============================================================================

class TestFormatVesumVerification:
    def test_no_stats(self):
        result = _format_vesum_verification({}, [])
        assert "did not run" in result

    def test_all_verified(self):
        stats = {"total": 50, "vesum_hits": 50}
        result = _format_vesum_verification(stats, [])
        assert "All words verified" in result
        assert "100.0%" in result

    def test_with_not_found(self):
        stats = {"total": 50, "vesum_hits": 45}
        not_found = [
            {"status": "❌", "original": "кошка", "source": "content"},
            {"status": "⚠️", "original": "щось", "source": "activities"},
        ]
        result = _format_vesum_verification(stats, not_found)
        assert "кошка" in result
        assert "❌" in result
        assert "⚠️" in result


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

    def test_infers_fail_from_low_score(self):
        raw = """===REVIEW_START===
**Overall Score:** 7.5/10
===REVIEW_END==="""
        result = _parse_d1_review(raw)
        assert result.verdict == "FAIL"


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

    def test_missing_delimiters(self):
        result = _parse_factual_review("no review")
        assert not result.ok


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

class TestBuildD3Context:
    def test_includes_repair_cycle(self):
        result = _build_d3_context("Some review text", 2)
        assert "Repair Cycle 2" in result

    def test_includes_review_text(self):
        result = _build_d3_context("Grammar issues found in section 3", 1)
        assert "Grammar issues found" in result

    def test_truncates_long_review(self):
        long_review = "\n".join(f"Line {i}: some issue" for i in range(200))
        result = _build_d3_context(long_review, 1)
        assert "truncated" in result

    def test_includes_instructions(self):
        result = _build_d3_context("review", 1)
        assert "Verify each D.1 issue was fixed" in result
        assert "Do NOT auto-pass" in result


# =============================================================================
# Dataclasses
# =============================================================================

class TestDataclasses:
    def test_dscreen_result_defaults(self):
        r = DScreenResult(metrics={"a": "1"})
        assert r.metrics == {"a": "1"}
        assert r.deterministic_issues == []
        assert not r.audit_passed
        assert r.audit_output == ""
        assert r.vesum_stats == {}

    def test_d1_result_defaults(self):
        r = D1Result(ok=True)
        assert r.ok
        assert r.issues == []
        assert r.scores == {}
        assert r.verdict == ""
        assert r.raw_review == ""
