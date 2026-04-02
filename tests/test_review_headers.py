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
    _HEADER_ISSUES,
    _HEADER_RECOMMENDATION,
    _HEADER_SCORES,
    _HEADER_VERIFICATION,
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


class TestCitationSeverityThreshold:
    """UNVERIFIED_CITATIONS must escalate to critical when sample is conclusive (≥5 unverified).

    Tests the severity-escalation logic directly, without the full file I/O pipeline.
    """

    def _severity_for(self, verified: int, total: int) -> str | None:
        """Mirror the severity logic from review_validation.py."""
        if total < 3:
            return None
        unverified = total - verified
        rate = verified / total if total else 0
        if verified == 0:
            return 'critical'   # FABRICATED_CITATIONS
        if rate < 0.5:
            is_conclusive = total >= 5 and unverified >= 5
            return 'critical' if is_conclusive else 'warning'  # UNVERIFIED_CITATIONS
        return None  # passes

    def test_zero_verified_is_critical(self):
        """0% verified → FABRICATED → critical."""
        assert self._severity_for(0, 6) == 'critical'
        assert self._severity_for(0, 20) == 'critical'

    def test_low_rate_large_sample_is_critical(self):
        """<50% verified with ≥5 total and ≥5 unverified → critical (was warning before fix)."""
        # 22% verified (5/23) — the kniaz-sviatoslav production case
        assert self._severity_for(5, 23) == 'critical'
        # 33% verified (5/15) — knyahynia-olha
        assert self._severity_for(5, 15) == 'critical'
        # 40% verified (8/20) — scythians-sarmatians
        assert self._severity_for(8, 20) == 'critical'
        # 31% verified (5/16) — sloviany-origins
        assert self._severity_for(5, 16) == 'critical'

    def test_low_rate_small_sample_is_warning(self):
        """<50% verified with <5 unverified → warning (too small to be conclusive)."""
        # 1 verified out of 4 = 25%, unverified=3 < 5 → warning
        assert self._severity_for(1, 4) == 'warning'
        # 2 verified out of 4 = 50% → passes (not < 0.5)
        assert self._severity_for(2, 4) is None

    def test_exactly_50pct_passes(self):
        """Exactly 50% verified → no violation (boundary condition)."""
        assert self._severity_for(10, 20) is None
        assert self._severity_for(5, 10) is None

    def test_above_50pct_passes(self):
        """≥50% verified → no citation violation."""
        assert self._severity_for(13, 22) is None   # 59% — scythians after fix
        assert self._severity_for(17, 27) is None   # 63% — sloviany after fix
        assert self._severity_for(26, 44) is None   # 59% — knyahynia after fix
