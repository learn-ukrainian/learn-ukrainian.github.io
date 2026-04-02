"""Testbed regression check — runs audit on baseline modules and detects regressions.

This test is marked 'slow' because it runs audit_module on 10+ modules.
CI can include it with: pytest -k testbed
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TESTBED_DIR = Path(__file__).resolve().parent / "testbed"
ROOT_DIR = TESTBED_DIR.parent.parent
BASELINE_JSON = TESTBED_DIR / "core" / "baseline.json"

sys.path.insert(0, str(TESTBED_DIR))
sys.path.insert(0, str(ROOT_DIR / "scripts"))


class TestCombinedGrade:
    """Unit tests for combined_grade — worst-of audit + review."""

    def test_no_review(self):
        from run_testbed import combined_grade
        assert combined_grade("A", None) == "A"
        assert combined_grade("B", "?") == "B"

    def test_review_worse(self):
        from run_testbed import combined_grade
        assert combined_grade("A", "B") == "B"
        assert combined_grade("A", "C") == "C"
        assert combined_grade("B", "F") == "F"

    def test_review_better(self):
        from run_testbed import combined_grade
        assert combined_grade("C", "A") == "C"
        assert combined_grade("F", "B") == "F"

    def test_review_equal(self):
        from run_testbed import combined_grade
        assert combined_grade("A", "A") == "A"
        assert combined_grade("B", "B") == "B"

    def test_review_with_plus_minus(self):
        from run_testbed import combined_grade
        assert combined_grade("A", "B+") == "B"
        assert combined_grade("A", "A-") == "A"


class TestGradeModule:
    """Unit tests for grade_module grading logic."""

    def test_no_content(self):
        from run_testbed import grade_module
        assert grade_module({"status": "NO_CONTENT"}) == "N/A"

    def test_fail(self):
        from run_testbed import grade_module
        assert grade_module({"status": "FAIL", "fix_attempts": 0, "words": 0, "word_target": 1000}) == "F"

    def test_a_grade(self):
        from run_testbed import grade_module
        assert grade_module({"status": "PASS", "fix_attempts": 1, "words": 1200, "word_target": 1000}) == "A"

    def test_b_grade(self):
        from run_testbed import grade_module
        assert grade_module({"status": "PASS", "fix_attempts": 1, "words": 1050, "word_target": 1000}) == "B"

    def test_c_grade_excessive_fixes(self):
        from run_testbed import grade_module
        assert grade_module({"status": "PASS", "fix_attempts": 5, "words": 1200, "word_target": 1000}) == "C"


class TestReviewModule:
    """Unit tests for review_module with mocked subprocess."""

    def test_claude_not_found(self):
        from unittest.mock import patch

        from run_testbed import review_module
        mod = {"track": "a1", "num": 1, "slug": "test-slug"}
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = review_module(mod)
        assert result["content_review"] is None
        assert result["prompt_review"] is None

    def test_claude_timeout(self):
        import subprocess
        from unittest.mock import patch

        from run_testbed import review_module
        mod = {"track": "a1", "num": 1, "slug": "test-slug"}
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 300)):
            result = review_module(mod)
        assert result["content_review"] is None
        assert result["prompt_review"] is None


@pytest.mark.slow
def test_no_regressions_vs_baseline():
    """Audit testbed modules and assert no grade regressions vs baseline."""
    if not BASELINE_JSON.exists():
        pytest.skip("No baseline.json — run 'run_testbed.py baseline' first")

    from run_testbed import audit_module, find_regressions, grade_module, load_baseline, load_config

    baseline = load_baseline()
    modules = load_config()
    results = []

    for mod in modules:
        r = audit_module(mod)
        r["grade"] = grade_module(r)
        results.append(r)

    regressions = find_regressions(results, baseline)
    assert not regressions, "Regressions detected:\n" + "\n".join(regressions)
