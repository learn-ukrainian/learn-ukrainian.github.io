"""Tests for review_validation.py header pattern flexibility.

Ensures the review validation accepts both V4 template format AND
natural professor-style review formats (numbered headings, synonyms).
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "audit" / "checks"))
from review_validation import (
    _HEADER_SCORES,
    _HEADER_ISSUES,
    _HEADER_VERIFICATION,
    _HEADER_RECOMMENDATION,
)


class TestScoresHeader:
    """_HEADER_SCORES must match scoring/assessment sections."""

    @pytest.mark.parametrize("header", [
        "## Scores",
        "## Scores Breakdown",
        "## Detailed Assessment",
        "## Assessment",
        "## Evaluation",
        "## 2. Detailed Assessment",
        "## 3. Scores Breakdown",
        "## 1. Evaluation",
    ])
    def test_matches(self, header):
        assert re.search(_HEADER_SCORES[0], header), f"Should match: {header}"

    @pytest.mark.parametrize("header", [
        "## Executive Summary",
        "## Issues Found",
        "## Recommendation",
        "## Introduction",
    ])
    def test_rejects(self, header):
        assert not re.search(_HEADER_SCORES[0], header), f"Should NOT match: {header}"


class TestIssuesHeader:
    """_HEADER_ISSUES must match issues/critique sections."""

    @pytest.mark.parametrize("header", [
        "## Issues Found",
        "## Critical Issues Found",
        "## Issues",
        "## Critical Issues",
        "## Critique",
        "## Problems",
        "## Concerns",
        '## "Brutal" Critique',
        "## Brutal Critique",
        "## 3. Critique",
        '## 3. "Brutal" Critique (The 0.5 Deduction)',
        "## 5. Issues Found",
    ])
    def test_matches(self, header):
        assert re.search(_HEADER_ISSUES[0], header), f"Should match: {header}"

    @pytest.mark.parametrize("header", [
        "## Scores",
        "## Summary",
        "## Recommendation",
    ])
    def test_rejects(self, header):
        assert not re.search(_HEADER_ISSUES[0], header), f"Should NOT match: {header}"


class TestVerificationHeader:
    """_HEADER_VERIFICATION must match summary/verification sections."""

    @pytest.mark.parametrize("header", [
        "## Verification Summary",
        "## Summary",
        "## Executive Summary",
        "## Verification",
        "## 1. Executive Summary",
        "## 4. Verification Summary",
        "## 2. Summary",
    ])
    def test_matches(self, header):
        assert re.search(_HEADER_VERIFICATION[0], header), f"Should match: {header}"

    @pytest.mark.parametrize("header", [
        "## Scores",
        "## Issues Found",
        "## Recommendation",
        "## Detailed Assessment",
    ])
    def test_rejects(self, header):
        assert not re.search(_HEADER_VERIFICATION[0], header), f"Should NOT match: {header}"


class TestRecommendationHeader:
    """_HEADER_RECOMMENDATION must match recommendation/verdict sections."""

    @pytest.mark.parametrize("header", [
        "## Recommendation",
        "## Verdict",
        "## Conclusion",
        "## Final Recommendation",
        "## Final Verdict",
        "## Final Conclusion",
        "## 4. Final Recommendation",
        "## 3. Recommendation",
        "## 5. Verdict",
    ])
    def test_matches(self, header):
        assert re.search(_HEADER_RECOMMENDATION[0], header), f"Should match: {header}"

    @pytest.mark.parametrize("header", [
        "## Scores",
        "## Issues Found",
        "## Summary",
        "## Assessment",
    ])
    def test_rejects(self, header):
        assert not re.search(_HEADER_RECOMMENDATION[0], header), f"Should NOT match: {header}"
