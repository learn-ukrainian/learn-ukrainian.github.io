"""Tests for scripts/audit/review_plan.py — LLM adversarial plan review.

Tests prompt construction, response parsing, and report generation.
Gemini calls are mocked — no real LLM invocations.

Issue: #984
"""

from __future__ import annotations

import json

# ---------------------------------------------------------------------------
# Imports under test
# ---------------------------------------------------------------------------
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.reads_content

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from audit.review_plan import (
    parse_review_response,
    review_plan,
    save_report,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_PLAN = {
    "module": "a1-001",
    "slug": "sounds-letters-and-hello",
    "version": "1.1",
    "level": "A1",
    "sequence": 1,
    "title": "Sounds, Letters, and Hello",
    "phase": "A1.1 [Sounds, Letters, and First Contact]",
    "word_target": 1200,
    "content_outline": [
        {"section": "Sounds and Letters", "words": 250, "points": ["Point A"]},
        {"section": "First Words", "words": 300, "points": ["Point B"]},
        {"section": "Hello!", "words": 250, "points": ["Point C"]},
        {"section": "Reading Practice", "words": 250, "points": ["Point D"]},
        {"section": "Summary", "words": 150, "points": ["Point E"]},
    ],
    "vocabulary_hints": {
        "required": ["мама (mother)", "тато (father)", "привіт (hi)"],
        "recommended": ["банк (bank)"],
    },
    "activity_hints": [
        {"type": "quiz", "focus": "sounds vs letters", "items": 6},
    ],
    "grammar": ["Sounds vs letters"],
    "objectives": ["Understand sounds vs letters"],
}

SAMPLE_GEMINI_RESPONSE_PASS = json.dumps({
    "verdict": "PASS",
    "score": 9,
    "summary": "Solid A1.1 phonetics plan with good textbook grounding.",
    "findings": [
        {
            "category": "vocabulary",
            "severity": "minor",
            "location": "vocabulary_hints.recommended",
            "issue": "банк is a loanword, consider adding a native word",
            "fix": "Add хата or книга to recommended list",
        }
    ],
})

SAMPLE_GEMINI_RESPONSE_FIX = json.dumps({
    "verdict": "FIX",
    "score": 6,
    "summary": "Plan has scope creep — grammar section lists past tense.",
    "findings": [
        {
            "category": "pedagogy",
            "severity": "critical",
            "location": "grammar",
            "issue": "Past tense listed in A1.1 phonetics module",
            "fix": "Remove past tense from grammar field",
        },
        {
            "category": "dialogue",
            "severity": "major",
            "location": "activity_hints[0]",
            "issue": "Quiz pattern feels like an interrogation",
            "fix": "Reframe as a natural classroom scenario",
        },
    ],
})


# ---------------------------------------------------------------------------
# Tests: prompt construction
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Tests: response parsing
# ---------------------------------------------------------------------------


class TestParseResponse:
    def test_parse_clean_json(self):
        result = parse_review_response(SAMPLE_GEMINI_RESPONSE_PASS)
        assert result is not None
        assert result["verdict"] == "PASS"
        assert result["score"] == 9
        assert len(result["findings"]) == 1

    def test_parse_json_with_markdown_fences(self):
        wrapped = f"```json\n{SAMPLE_GEMINI_RESPONSE_PASS}\n```"
        result = parse_review_response(wrapped)
        assert result is not None
        assert result["verdict"] == "PASS"

    def test_parse_json_with_preamble(self):
        preamble = f"Here is my review:\n\n{SAMPLE_GEMINI_RESPONSE_FIX}\n\nHope this helps!"
        result = parse_review_response(preamble)
        assert result is not None
        assert result["verdict"] == "FIX"
        assert result["score"] == 6

    def test_parse_fallback_regex(self):
        # Malformed JSON but has verdict and score
        raw = 'blah "verdict": "REWRITE", "score": 3 blah'
        result = parse_review_response(raw)
        assert result is not None
        assert result["verdict"] == "REWRITE"
        assert result["score"] == 3

    def test_parse_garbage_returns_none(self):
        result = parse_review_response("completely unrelated text")
        assert result is None


# ---------------------------------------------------------------------------
# Tests: report formatting
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Tests: save report
# ---------------------------------------------------------------------------


class TestSaveReport:
    def test_save_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "audit.review_plan.CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en"
        )
        (tmp_path / "curriculum" / "l2-uk-en" / "plans" / "a1").mkdir(parents=True)

        report_path = save_report("a1", "test-slug", "# Test Report")
        assert report_path.exists()
        assert report_path.name == "test-slug-plan-review.md"
        assert report_path.read_text() == "# Test Report"


# ---------------------------------------------------------------------------
# Tests: review_plan integration (mocked Gemini)
# ---------------------------------------------------------------------------


class TestReviewPlan:
    @patch("audit.review_plan.call_gemini")
    def test_review_pass(self, mock_gemini, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "audit.review_plan.CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en"
        )
        plans_dir = tmp_path / "curriculum" / "l2-uk-en" / "plans" / "a1"
        plans_dir.mkdir(parents=True)

        import yaml
        (plans_dir / "test-slug.yaml").write_text(
            yaml.dump(SAMPLE_PLAN, allow_unicode=True)
        )

        mock_gemini.return_value = (True, SAMPLE_GEMINI_RESPONSE_PASS)

        result = review_plan("a1", "test-slug")
        assert result["verdict"] == "PASS"
        assert result["score"] == 9
        assert "path" in result
        assert Path(result["path"]).exists()

    @patch("audit.review_plan.call_gemini")
    def test_review_gemini_failure(self, mock_gemini, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "audit.review_plan.CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en"
        )
        plans_dir = tmp_path / "curriculum" / "l2-uk-en" / "plans" / "a1"
        plans_dir.mkdir(parents=True)

        import yaml
        (plans_dir / "test-slug.yaml").write_text(
            yaml.dump(SAMPLE_PLAN, allow_unicode=True)
        )

        mock_gemini.return_value = (False, "ERROR: connection refused")

        result = review_plan("a1", "test-slug")
        assert "error" in result
