"""
Tests for verify_track.py — stale cache detection, classification, range parsing.

All tests use temp directories and mocked external dependencies.
No real audit runs or LLM calls.

Issue: #611
"""

import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.verify_track import (
    check_sidecar_files,
    classify_module,
    is_status_stale,
)

# ---------------------------------------------------------------------------
# find_content_file
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# read_status
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# is_status_stale
# ---------------------------------------------------------------------------

class TestIsStatusStale:
    """Tests for is_status_stale. Critical regression test for #602."""

    def test_equal_mtimes_not_stale(self, tmp_path):
        """Equal mtimes (e.g., git checkout) → NOT stale (#602)."""
        status_file = tmp_path / "status.json"
        content_file = tmp_path / "content.md"

        status_file.write_text("{}", "utf-8")
        content_file.write_text("content", "utf-8")

        # Force equal mtimes
        mtime = time.time()
        os.utime(status_file, (mtime, mtime))
        os.utime(content_file, (mtime, mtime))

        assert is_status_stale(status_file, content_file) is False


# ---------------------------------------------------------------------------
# classify_module
# ---------------------------------------------------------------------------

class TestClassifyModule:
    """Tests for classify_module."""

    def test_pass_overall(self):
        """Overall pass with no failing gates → 'pass'."""
        status = {
            "overall": {"status": "pass"},
            "gates": {
                "words": {"status": "pass", "message": "OK"},
            }
        }
        classification, problems = classify_module(status, full_mode=False)
        assert classification == "pass"
        assert problems == []

    def test_failing_gate(self):
        """Failing gate → 'fail' with problem description."""
        status = {
            "overall": {"status": "fail"},
            "gates": {
                "words": {"status": "fail", "message": "850/1000"},
            }
        }
        classification, problems = classify_module(status, full_mode=False)
        assert classification == "fail"
        assert any("words" in p for p in problems)

    def test_deferred_gates_partial_mode(self):
        """Deferred gates in partial mode → 'content-complete'."""
        status = {
            "overall": {"status": "pass"},
            "gates": {
                "words": {"status": "pass", "message": "OK"},
                "activities": {"status": "deferred", "message": "skipped"},
            }
        }
        classification, _problems = classify_module(status, full_mode=False)
        assert classification == "content-complete"

    def test_deferred_gates_full_mode_fails(self):
        """Deferred gates in full mode → 'fail'."""
        status = {
            "overall": {"status": "pass"},
            "gates": {
                "words": {"status": "pass", "message": "OK"},
                "activities": {"status": "deferred", "message": "skipped"},
            }
        }
        classification, problems = classify_module(status, full_mode=True)
        assert classification == "fail"
        assert any("deferred" in p for p in problems)


# ---------------------------------------------------------------------------
# check_sidecar_files
# ---------------------------------------------------------------------------

class TestCheckSidecarFiles:
    """Tests for check_sidecar_files."""

    def test_full_mode_activities_only(self, tmp_path):
        """Full mode, only activities exists → vocab missing."""
        (tmp_path / "activities").mkdir()
        (tmp_path / "activities" / "test.yaml").write_text("- type: quiz", "utf-8")

        result = check_sidecar_files(tmp_path, "test", full_mode=True)
        assert len(result) == 1
        assert "vocabulary" in result[0]


# ---------------------------------------------------------------------------
# parse_range
# ---------------------------------------------------------------------------
