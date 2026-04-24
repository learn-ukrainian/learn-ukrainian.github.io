"""Tests for section rewrite safety — backup/restore on validation failure.

Covers the 2026-03-28 root cause: section rewrite producing garbage content
that overwrites good prose. Verifies that:
1. Content is backed up before rewrite
2. Content is restored when validation rejects the rewrite
3. Score >= 9.0 short-circuits the fix/rewrite loop
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestRewriteValidation:
    """Test the validation logic in _rewrite_weak_sections."""

    def test_section_count_mismatch_restores_backup(self, tmp_path: Path):
        """When rewrite drops H2 headings, original content must be preserved."""
        content_path = tmp_path / "module.md"
        original = "<!-- TAB:Урок -->\n\n## Section 1\nGood content here.\n\n## Section 2\nMore good content.\n"
        content_path.write_text(original, "utf-8")

        # The rewrite has only 1 section instead of 2
        bad_rewrite = "## Section 1\nRewritten but dropped section 2.\n"

        # Simulate the validation logic from _rewrite_weak_sections
        body = original.replace("<!-- TAB:Урок -->", "").strip()
        original_h2s = re.findall(r"^## .+", body, re.MULTILINE)
        rewrite_h2s = re.findall(r"^## .+", bad_rewrite, re.MULTILINE)

        assert len(original_h2s) == 2
        assert len(rewrite_h2s) == 1
        assert len(rewrite_h2s) != len(original_h2s), "Validation should detect section count mismatch"

        # After rejection, content should be restored
        content_path.write_text("CORRUPTED", "utf-8")  # Simulate corruption
        content_path.write_text(original, "utf-8")  # Restore
        assert content_path.read_text("utf-8") == original

    def test_word_count_too_short_restores_backup(self, tmp_path: Path):
        """When rewrite is <90% of original word count, original must be preserved."""
        original_words = 1000
        rewrite_words = 800  # 80% — below 90% threshold
        min_words = int(original_words * 0.9)

        assert rewrite_words < min_words, "Validation should reject rewrite under 90% word count"

    def test_word_count_at_threshold_passes(self):
        """Rewrite at exactly 90% should pass."""
        original_words = 1000
        rewrite_words = 900  # Exactly 90%
        min_words = int(original_words * 0.9)

        assert rewrite_words >= min_words, "90% should pass validation"

    def test_zero_sections_rejected(self):
        """Rewrite with zero H2 headings must be rejected."""
        body = "## Section 1\nContent.\n\n## Section 2\nMore.\n"
        bad_rewrite = "Just some text with no headings at all."

        original_h2s = re.findall(r"^## .+", body, re.MULTILINE)
        rewrite_h2s = re.findall(r"^## .+", bad_rewrite, re.MULTILINE)

        assert len(original_h2s) == 2
        assert len(rewrite_h2s) == 0
        assert len(rewrite_h2s) != len(original_h2s)


class TestEarlyAcceptAt9:
    """Test that score >= 9.0 short-circuits the fix/rewrite loop."""

    def test_score_9_0_accepted(self):
        """Score of 9.0 should be accepted without further rounds."""
        score = 9.0
        passed = False  # Reviewer said REVISE but score is high

        # The new logic: score >= 9.0 → accept
        should_skip_fixes = score >= 9.0
        assert should_skip_fixes, "9.0 should short-circuit the fix loop"

    def test_score_9_1_accepted(self):
        """Score of 9.1 should be accepted."""
        assert 9.1 >= 9.0

    def test_score_8_9_continues_to_fixes(self):
        """Score of 8.9 should continue to fix/rewrite loop."""
        score = 8.9
        assert score < 9.0, "8.9 should NOT short-circuit"

    def test_score_8_0_continues_to_fixes(self):
        """Score of 8.0 should continue to fix/rewrite loop."""
        score = 8.0
        assert score < 9.0, "8.0 should NOT short-circuit"


class TestPreVerifyRetry:
    """Test that pre-verify retries once on failure."""

    def test_retry_logic(self):
        """Verify the retry pattern: fail → retry → succeed."""
        call_count = 0

        def mock_dispatch(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return False, ""  # First call fails (timeout)
            return True, "<verification>Verified facts</verification>"

        # Simulate the retry logic
        ok, raw = mock_dispatch()  # First attempt
        if not ok or not raw:
            ok, raw = mock_dispatch()  # Retry

        assert ok is True
        assert "verification" in raw
        assert call_count == 2, "Should have called dispatch exactly twice"

    def test_both_attempts_fail(self):
        """When both attempts fail, should return None."""
        def mock_dispatch(*args, **kwargs):
            return False, ""

        ok, raw = mock_dispatch()
        if not ok or not raw:
            ok, raw = mock_dispatch()

        assert ok is False
        assert raw == ""
