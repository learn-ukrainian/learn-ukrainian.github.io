"""
Tests for verify_track.py — stale cache detection, classification, range parsing.

All tests use temp directories and mocked external dependencies.
No real audit runs or LLM calls.

Issue: #611
"""

import json
import os
import sys
import time

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.verify_track import (
    check_sidecar_files,
    classify_module,
    find_content_file,
    is_status_stale,
    parse_range,
    read_status,
)

# ---------------------------------------------------------------------------
# find_content_file
# ---------------------------------------------------------------------------

class TestFindContentFile:
    """Tests for find_content_file."""

    def test_bare_slug(self, tmp_path):
        """Bare slug file found directly."""
        (tmp_path / "my-module.md").write_text("content", "utf-8")
        result = find_content_file(tmp_path, "my-module")
        assert result == tmp_path / "my-module.md"

    def test_numeric_prefix(self, tmp_path):
        """Numbered prefix file found via glob."""
        (tmp_path / "05-my-module.md").write_text("content", "utf-8")
        result = find_content_file(tmp_path, "my-module")
        assert result is not None
        assert result.name == "05-my-module.md"

    def test_bare_slug_preferred_over_numeric(self, tmp_path):
        """When both bare and numeric exist, bare wins."""
        (tmp_path / "my-module.md").write_text("bare", "utf-8")
        (tmp_path / "05-my-module.md").write_text("numbered", "utf-8")
        result = find_content_file(tmp_path, "my-module")
        assert result.name == "my-module.md"

    def test_returns_none_when_not_found(self, tmp_path):
        """No matching file → None."""
        result = find_content_file(tmp_path, "nonexistent")
        assert result is None


# ---------------------------------------------------------------------------
# read_status
# ---------------------------------------------------------------------------

class TestReadStatus:
    """Tests for read_status."""

    def test_valid_json(self, tmp_path):
        """Valid JSON file parsed and returned."""
        status_file = tmp_path / "status.json"
        data = {"overall": {"status": "pass"}, "gates": {}}
        status_file.write_text(json.dumps(data), "utf-8")

        result = read_status(status_file)
        assert result["overall"]["status"] == "pass"

    def test_missing_file_returns_none(self, tmp_path):
        """Missing file → None."""
        result = read_status(tmp_path / "nonexistent.json")
        assert result is None


# ---------------------------------------------------------------------------
# is_status_stale
# ---------------------------------------------------------------------------

class TestIsStatusStale:
    """Tests for is_status_stale. Critical regression test for #602."""

    def test_content_newer_than_status_is_stale(self, tmp_path):
        """Content modified after status → stale."""
        status_file = tmp_path / "status.json"
        content_file = tmp_path / "content.md"

        status_file.write_text("{}", "utf-8")
        time.sleep(0.05)  # Ensure different mtime
        content_file.write_text("new content", "utf-8")

        assert is_status_stale(status_file, content_file) is True

    def test_status_newer_than_content_is_fresh(self, tmp_path):
        """Status created after content → not stale."""
        content_file = tmp_path / "content.md"
        status_file = tmp_path / "status.json"

        content_file.write_text("content", "utf-8")
        time.sleep(0.05)
        status_file.write_text("{}", "utf-8")

        assert is_status_stale(status_file, content_file) is False

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

    def test_missing_status_file_returns_false(self, tmp_path):
        """Missing status file → not stale (nothing to be stale)."""
        content_file = tmp_path / "content.md"
        content_file.write_text("content", "utf-8")

        assert is_status_stale(tmp_path / "missing.json", content_file) is False

    def test_missing_content_file_returns_false(self, tmp_path):
        """Missing content file → not stale."""
        status_file = tmp_path / "status.json"
        status_file.write_text("{}", "utf-8")

        assert is_status_stale(status_file, None) is False

    def test_none_content_file_returns_false(self, tmp_path):
        """None content path → not stale."""
        status_file = tmp_path / "status.json"
        status_file.write_text("{}", "utf-8")

        assert is_status_stale(status_file, None) is False


# ---------------------------------------------------------------------------
# classify_module
# ---------------------------------------------------------------------------

class TestClassifyModule:
    """Tests for classify_module."""

    def test_none_status(self):
        """No status JSON → 'no-status'."""
        classification, problems = classify_module(None, full_mode=False)
        assert classification == "no-status"
        assert problems == []

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
        classification, problems = classify_module(status, full_mode=False)
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

    def test_unknown_overall_status(self):
        """Unknown overall status with no gates → 'fail'."""
        status = {"overall": {"status": "unknown"}, "gates": {}}
        classification, _ = classify_module(status, full_mode=False)
        assert classification == "fail"

    def test_multiple_failing_gates(self):
        """Multiple failing gates → all listed in problems."""
        status = {
            "overall": {"status": "fail"},
            "gates": {
                "words": {"status": "fail", "message": "short"},
                "activities": {"status": "fail", "message": "missing"},
                "vocab": {"status": "pass", "message": "OK"},
            }
        }
        classification, problems = classify_module(status, full_mode=False)
        assert classification == "fail"
        assert len(problems) == 2

    def test_empty_gates(self):
        """Pass overall with empty gates dict → 'pass'."""
        status = {"overall": {"status": "pass"}, "gates": {}}
        classification, _ = classify_module(status, full_mode=False)
        assert classification == "pass"


# ---------------------------------------------------------------------------
# check_sidecar_files
# ---------------------------------------------------------------------------

class TestCheckSidecarFiles:
    """Tests for check_sidecar_files."""

    def test_partial_mode_skips_check(self, tmp_path):
        """In non-full mode, no sidecar checks."""
        result = check_sidecar_files(tmp_path, "test", full_mode=False)
        assert result == []

    def test_full_mode_both_missing(self, tmp_path):
        """Full mode, no sidecar files → 2 missing."""
        result = check_sidecar_files(tmp_path, "test", full_mode=True)
        assert len(result) == 2

    def test_full_mode_both_present(self, tmp_path):
        """Full mode, both files exist → no missing."""
        (tmp_path / "activities").mkdir()
        (tmp_path / "vocabulary").mkdir()
        (tmp_path / "activities" / "test.yaml").write_text("- type: quiz", "utf-8")
        (tmp_path / "vocabulary" / "test.yaml").write_text("- word: test", "utf-8")

        result = check_sidecar_files(tmp_path, "test", full_mode=True)
        assert result == []

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

class TestParseRange:
    """Tests for parse_range."""

    def test_valid_range(self):
        """Valid range '5-10' → (5, 10)."""
        assert parse_range("5-10") == (5, 10)

    def test_single_module_range(self):
        """Single module '3-3' → (3, 3)."""
        assert parse_range("3-3") == (3, 3)

    def test_invalid_format_no_dash(self):
        """No dash → ArgumentTypeError."""
        import argparse
        with pytest.raises(argparse.ArgumentTypeError):
            parse_range("5")

    def test_invalid_format_too_many_dashes(self):
        """Too many dashes → ArgumentTypeError."""
        import argparse
        with pytest.raises(argparse.ArgumentTypeError):
            parse_range("1-5-10")

    def test_invalid_non_numeric(self):
        """Non-numeric → ValueError."""
        with pytest.raises(ValueError):
            parse_range("a-b")
