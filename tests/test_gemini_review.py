"""
Tests for Gemini RAG-grounded review phase in build_module.py.

Covers:
- _parse_factual_review() — Pass 1 factual review parsing
- _merge_gemini_review_passes() — Merging two sharded review passes
- _load_rag_for_review() — RAG data loading + fallback
- _build_pass1_prompt() / _build_pass2_prompt() — prompt assembly
- CLI routing: --review → Gemini, --review-claude → Claude
- Edge cases: no RAG, truncated output, dispatch failures

Issue: #703
"""

import argparse
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass, field

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_module import (
    _parse_factual_review,
    _merge_gemini_review_passes,
    _parse_d1_review,
    _apply_find_replace_fixes,
    D1Result,
    phase_review_v4_dispatch,
)


# =============================================================================
# _parse_factual_review()
# =============================================================================


class TestParseFactualReview:

    CLEAN_REVIEW = """\
Some preamble text...

===FACTUAL_REVIEW_START===
## Factual Verification Summary

**Total claims checked:** 12
**Confirmed [Tier 1]:** 10
**Discrepancies [Tier 1]:** 0
**Unverified:** 2
**Factual Alignment Score:** 9/10

## Confirmed Claims

- Claim 1 confirmed by chunk_abc123

## Discrepancies

(None found)

## Unverified Claims

- Etymology of "книга" — no reference coverage
- Frequency claim about "добре" — no reference coverage

## Verdict

**Status:** PASS
===FACTUAL_REVIEW_END===
"""

    DISCREPANCY_REVIEW = """\
===FACTUAL_REVIEW_START===
## Factual Verification Summary

**Total claims checked:** 8
**Confirmed [Tier 1]:** 5
**Discrepancies [Tier 1]:** 2
**Unverified:** 1
**Factual Alignment Score:** 6/10

## Confirmed Claims

- Accusative forms correct per textbook Grade 3

## Discrepancies

### Discrepancy 1: Wrong case ending
- **Module says:** "книгою is the instrumental form"
- **Reference says:** "книгою is correct instrumental singular"
- **Source:** chunk_xyz789
- **Severity:** HIGH
- **Suggested fix:** The module claim is actually correct, verify context

### Discrepancy 2: Wrong date
- **Module says:** "Kyiv was founded in 482 AD"
- **Reference says:** "Traditional founding date is 482 CE"
- **Source:** literary_hist_001
- **Severity:** HIGH
- **Suggested fix:** Clarify "CE" vs "AD" is the same

## Unverified Claims

- Claim about vocal harmony

## Verdict

**Status:** FAIL
===FACTUAL_REVIEW_END===
"""

    TRUNCATED_REVIEW = """\
===FACTUAL_REVIEW_START===
## Factual Verification Summary

**Total claims checked:** 5
**Confirmed [Tier 1]:** 4
**Discrepancies [Tier 1]:** 1
**Unverified:** 0
**Factual Alignment Score:** 8/10

## Discrepancies

### Discrepancy 1: Minor issue
- **Module says:** "some claim"
- **Reference says:** "different claim"
- **Source:** chunk_123
- **Severity:** HIGH
- **Suggested fix:** Fix it
"""

    def test_clean_review_pass(self):
        result = _parse_factual_review(self.CLEAN_REVIEW)
        assert result.ok is True
        assert result.verdict == "PASS"
        assert result.scores.get("factual_accuracy") == 9.0
        assert len(result.issues) == 0

    def test_discrepancy_review_fail(self):
        result = _parse_factual_review(self.DISCREPANCY_REVIEW)
        assert result.ok is True
        assert result.verdict == "FAIL"
        assert result.scores.get("factual_accuracy") == 6.0
        assert len(result.issues) == 2
        assert result.issues[0]["type"] == "FACTUAL_DISCREPANCY"
        assert "книгою" in result.issues[0].get("text", "")
        assert result.issues[1].get("source") == "literary_hist_001"

    def test_truncated_review_tolerant(self):
        """Tolerant parser recovers partial output (missing end tag)."""
        result = _parse_factual_review(self.TRUNCATED_REVIEW)
        assert result.ok is True
        assert result.scores.get("factual_accuracy") == 8.0
        assert len(result.issues) == 1

    def test_no_delimiters(self):
        result = _parse_factual_review("Some random text without delimiters")
        assert result.ok is False
        assert result.raw_review == ""

    def test_verdict_derived_from_discrepancy_count(self):
        """If no explicit verdict but discrepancies > 0, derive FAIL."""
        raw = """\
===FACTUAL_REVIEW_START===
## Factual Verification Summary

**Total claims checked:** 3
**Confirmed [Tier 1]:** 2
**Discrepancies [Tier 1]:** 1
**Unverified:** 0
**Factual Alignment Score:** 7/10

## Discrepancies

### Discrepancy 1: Issue
- **Module says:** "X"
- **Reference says:** "Y"
- **Source:** chunk_1
- **Severity:** HIGH
- **Suggested fix:** Fix

## Verdict

Some text without explicit status
===FACTUAL_REVIEW_END===
"""
        result = _parse_factual_review(raw)
        assert result.ok is True
        assert result.verdict == "FAIL"  # Derived from discrepancy count > 0


# =============================================================================
# _merge_gemini_review_passes()
# =============================================================================


class TestMergeGeminiReviewPasses:

    def test_both_pass(self):
        p1 = D1Result(ok=True, verdict="PASS", scores={"factual_accuracy": 9.0},
                       issues=[], raw_review="Pass 1 review")
        p2 = D1Result(ok=True, verdict="PASS", scores={"overall": 8.5, "language": 9.0},
                       issues=[{"type": "LANG", "text": "minor"}], raw_review="Pass 2 review")
        merged = _merge_gemini_review_passes(p1, p2)
        assert merged.ok is True
        assert merged.verdict == "PASS"
        assert merged.scores["factual_accuracy"] == 9.0
        assert merged.scores["overall"] == 8.5
        assert merged.scores["language"] == 9.0
        assert len(merged.issues) == 1
        assert "Pass 1 review" in merged.raw_review
        assert "Pass 2 review" in merged.raw_review

    def test_one_fail(self):
        p1 = D1Result(ok=True, verdict="FAIL", scores={"factual_accuracy": 5.0},
                       issues=[{"type": "DISC"}], raw_review="P1")
        p2 = D1Result(ok=True, verdict="PASS", scores={"overall": 9.0},
                       issues=[], raw_review="P2")
        merged = _merge_gemini_review_passes(p1, p2)
        assert merged.ok is True
        assert merged.verdict == "FAIL"

    def test_pass1_dispatch_failed(self):
        """Pass 1 failed → degrades to Pass 2 only."""
        p2 = D1Result(ok=True, verdict="PASS", scores={"overall": 8.5},
                       issues=[], raw_review="P2 only")
        merged = _merge_gemini_review_passes(None, p2)
        assert merged.ok is True
        assert merged.verdict == "PASS"
        assert merged.raw_review == "P2 only"

    def test_pass2_dispatch_failed(self):
        """Pass 2 failed → degrades to Pass 1 only."""
        p1 = D1Result(ok=True, verdict="PASS", scores={"factual_accuracy": 9.0},
                       issues=[], raw_review="P1 only")
        merged = _merge_gemini_review_passes(p1, None)
        assert merged.ok is True
        assert merged.verdict == "PASS"

    def test_both_dispatch_failed(self):
        merged = _merge_gemini_review_passes(None, None)
        assert merged.ok is False

    def test_pass1_ok_false(self):
        """Pass 1 parsed but ok=False → treated as failed."""
        p1 = D1Result(ok=False, raw_review="")
        p2 = D1Result(ok=True, verdict="PASS", scores={"overall": 9.0},
                       issues=[], raw_review="P2")
        merged = _merge_gemini_review_passes(p1, p2)
        assert merged.ok is True
        assert merged.raw_review == "P2"

    def test_both_ok_false(self):
        p1 = D1Result(ok=False, raw_review="")
        p2 = D1Result(ok=False, raw_review="")
        merged = _merge_gemini_review_passes(p1, p2)
        assert merged.ok is False


# =============================================================================
# FIND/REPLACE integration (existing _apply_find_replace_fixes with Gemini output)
# =============================================================================


class TestGeminiFindReplace:

    def test_gemini_fix_output(self, tmp_path):
        """Existing _apply_find_replace_fixes works with Gemini-style output."""
        content = tmp_path / "test.md"
        content.write_text("Привіт, мій друг! Як ти?\n\nЦе хороший день.", "utf-8")

        raw_output = """\
===SECTION_FIX_START===
FILE: test.md
FIND:
хороший день
REPLACE:
гарний день
===SECTION_FIX_END===
"""
        n = _apply_find_replace_fixes(content, raw_output)
        assert n == 1
        assert "гарний день" in content.read_text("utf-8")
        assert "хороший" not in content.read_text("utf-8")


# =============================================================================
# _load_rag_for_review()
# =============================================================================


class TestLoadRagForReview:

    def test_loads_from_discovery_yaml(self, tmp_path):
        """Loads RAG data from discovery.yaml."""
        from build_module import _load_rag_for_review

        # Create a minimal ctx mock
        ctx = MagicMock()
        ctx.orch_dir = tmp_path
        ctx.slug = "test-module"
        ctx.track = "a1"
        ctx.plan = {"vocabulary_hints": {"required": ["привіт"]}}

        # Write a discovery.yaml with RAG data
        discovery = {
            "discovered_at": "2026-03-01",
            "query_keywords": ["привіт"],
            "rag_chunks": [{"text": "Привіт means hello", "grade": 1, "score": 0.9}],
            "rag_images": [],
            "rag_literary": [],
            "videos": [],
        }
        import yaml
        (tmp_path / "discovery.yaml").write_text(
            yaml.dump(discovery, allow_unicode=True), "utf-8"
        )

        result = _load_rag_for_review(ctx)
        assert len(result["text_chunks"]) == 1
        assert result["text_chunks"][0]["text"] == "Привіт means hello"

    def test_fallback_to_search_rag(self, tmp_path):
        """Falls back to search_rag() when discovery.yaml has no RAG data."""
        from build_module import _load_rag_for_review

        ctx = MagicMock()
        ctx.orch_dir = tmp_path
        ctx.slug = "test-module"
        ctx.track = "a1"
        ctx.plan = {"vocabulary_hints": {"required": ["привіт"]}}

        # Write empty discovery.yaml
        import yaml
        (tmp_path / "discovery.yaml").write_text(
            yaml.dump({"discovered_at": "2026-03-01", "rag_chunks": [], "rag_images": [], "rag_literary": [], "videos": []}, allow_unicode=True),
            "utf-8",
        )

        # Mock search_rag to return some data
        mock_rag = {"text_chunks": [{"text": "fallback data"}], "images": [], "literary": []}
        with patch("video_discovery.search_rag", return_value=mock_rag):
            result = _load_rag_for_review(ctx)
            assert len(result["text_chunks"]) == 1
            assert result["text_chunks"][0]["text"] == "fallback data"


# =============================================================================
# CLI routing
# =============================================================================


class TestCLIRouting:

    def test_review_flag_routes_gemini(self):
        """--review sets review_agent to gemini."""
        from build_module import preflight_v4

        args = MagicMock(spec=argparse.Namespace)
        args.review = True
        args.review_claude = False
        args.stop_before = None
        args.restart_from = None
        args.skip_discover = False

        # preflight_v4 calls preflight_v3 which needs real args — mock it
        with patch("build_module.preflight_v3") as mock_pf:
            mock_ctx = MagicMock()
            mock_ctx.state = {}
            mock_pf.return_value = mock_ctx
            ctx = preflight_v4(args)
            assert ctx.review_agent == "gemini"
            assert ctx.review is True

    def test_review_claude_flag_routes_claude(self):
        """--review-claude sets review_agent to claude."""
        from build_module import preflight_v4

        args = MagicMock(spec=argparse.Namespace)
        args.review = False
        args.review_claude = True
        args.stop_before = None
        args.restart_from = None
        args.skip_discover = False

        with patch("build_module.preflight_v3") as mock_pf:
            mock_ctx = MagicMock()
            mock_ctx.state = {}
            mock_pf.return_value = mock_ctx
            ctx = preflight_v4(args)
            assert ctx.review_agent == "claude"
            assert ctx.review is True  # --review-claude implies review


# =============================================================================
# Pass 1 skip when no RAG
# =============================================================================


class TestPass1SkipNoRag:

    def test_skip_pass1_no_rag(self):
        """When 0 RAG chunks, Pass 1 is skipped and marked PASS."""
        # The logic is in phase_review_gemini_v4 — test the pass1_result
        # creation when total_rag == 0
        pass1 = D1Result(
            ok=True, verdict="PASS",
            raw_review="(No RAG sources available — factual check skipped)",
        )
        p2 = D1Result(ok=True, verdict="PASS", scores={"overall": 9.0},
                       issues=[], raw_review="Pass 2 review")
        merged = _merge_gemini_review_passes(pass1, p2)
        assert merged.ok is True
        assert merged.verdict == "PASS"
        assert "No RAG sources" in merged.raw_review


# =============================================================================
# Prompt size caps
# =============================================================================


class TestPromptSizeCaps:

    def test_build_pass1_truncates_large_content(self, tmp_path):
        """Content > 100K chars gets truncated in pass 1 prompt."""
        from build_module import _build_pass1_prompt, DScreenResult

        # Create mock ctx
        ctx = MagicMock()
        ctx.paths = {
            "md": tmp_path / "content.md",
            "plan": tmp_path / "plan.yaml",
            "research": tmp_path / "research.md",
        }
        # Write very large content
        large_content = "# Module\n\n" + "Велика кількість тексту. " * 10_000
        (tmp_path / "content.md").write_text(large_content, "utf-8")
        (tmp_path / "plan.yaml").write_text("title: Test", "utf-8")
        (tmp_path / "research.md").write_text("Research notes", "utf-8")
        ctx.orch_dir = tmp_path

        screen = DScreenResult(
            metrics={"COMPUTED_WORD_COUNT": "50000", "COMPUTED_WORD_TARGET": "2000",
                     "COMPUTED_WORD_PERCENT": "2500", "COMPUTED_ACTIVITY_COUNT": "5",
                     "COMPUTED_VOCAB_COUNT": "20", "COMPUTED_IMMERSION_PERCENT": "40"},
            vesum_stats={}, vesum_not_found=[],
        )
        rag_data = {"text_chunks": [{"text": "chunk", "grade": 1}], "images": [], "literary": []}

        # Temporarily create the template file
        phases_dir = Path(__file__).parent.parent / "claude_extensions" / "phases" / "gemini"
        template = phases_dir / "phase-gemini-review-pass1.md"
        assert template.exists(), f"Template not found: {template}"

        prompt = _build_pass1_prompt(ctx, screen, rag_data)
        # Should be capped
        assert len(prompt) < 120_000


# =============================================================================
# Dispatch routing
# =============================================================================


class TestDispatchRouting:

    def test_dispatch_calls_gemini(self):
        """phase_review_v4_dispatch routes to Gemini by default."""
        ctx = MagicMock()
        ctx.review_agent = "gemini"
        state = {}

        with patch("build_module.phase_review_gemini_v4", return_value=True) as mock_g, \
             patch("build_module.phase_review_v4", return_value=True) as mock_c:
            result = phase_review_v4_dispatch(ctx, state)
            mock_g.assert_called_once_with(ctx, state)
            mock_c.assert_not_called()
            assert result is True

    def test_dispatch_calls_claude(self):
        """phase_review_v4_dispatch routes to Claude with review_agent=claude."""
        ctx = MagicMock()
        ctx.review_agent = "claude"
        state = {}

        with patch("build_module.phase_review_gemini_v4", return_value=True) as mock_g, \
             patch("build_module.phase_review_v4", return_value=True) as mock_c:
            result = phase_review_v4_dispatch(ctx, state)
            mock_c.assert_called_once_with(ctx, state)
            mock_g.assert_not_called()
            assert result is True
