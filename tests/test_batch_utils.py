"""Tests for scripts/batch_utils.py."""

import json
import os
import sys
from pathlib import Path

import pytest

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from batch_utils import (
    BatchLock,
    ErrorCategory,
    LockConflictError,
    atomic_write,
    atomic_write_json,
    classify_error,
)

# ---------------------------------------------------------------------------
# atomic_write / atomic_write_json
# ---------------------------------------------------------------------------

class TestAtomicWrite:
    def test_writes_content(self, tmp_path):
        p = tmp_path / "test.txt"
        atomic_write(p, "hello world")
        assert p.read_text() == "hello world"

    def test_creates_parent_dirs(self, tmp_path):
        p = tmp_path / "a" / "b" / "test.txt"
        atomic_write(p, "nested")
        assert p.read_text() == "nested"

    def test_no_tmp_file_left(self, tmp_path):
        p = tmp_path / "test.txt"
        atomic_write(p, "data")
        # PID-based tmp file should be cleaned up
        assert not p.with_suffix(f".{os.getpid()}.tmp").exists()


class TestAtomicWriteJson:
    def test_unicode(self, tmp_path):
        p = tmp_path / "uk.json"
        atomic_write_json(p, {"word": "привіт"})
        data = json.loads(p.read_text())
        assert data["word"] == "привіт"


# ---------------------------------------------------------------------------
# ExponentialBackoff
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# BatchLock
# ---------------------------------------------------------------------------

class TestBatchLock:
    def test_acquires_and_releases(self, tmp_path):
        lock_dir = tmp_path / "locks"
        with BatchLock("test-track", lock_dir):
            lock_file = lock_dir / "batch_test-track.lock"
            assert lock_file.exists()
            data = json.loads(lock_file.read_text())
            assert data["pid"] == os.getpid()
            assert data["track"] == "test-track"
        # Lock released
        assert not lock_file.exists()

    def test_cleans_stale_lock(self, tmp_path):
        lock_dir = tmp_path / "locks"
        lock_dir.mkdir()
        lock_file = lock_dir / "batch_test-track.lock"
        # Write lock with a dead PID
        lock_file.write_text(json.dumps({
            "pid": 99999999,  # Very unlikely to be alive
            "track": "test-track",
            "started": "2024-01-01T00:00:00Z",
        }))
        # Should clean up stale lock and acquire
        with BatchLock("test-track", lock_dir):
            data = json.loads(lock_file.read_text())
            assert data["pid"] == os.getpid()

    def test_reentrant_same_instance(self, tmp_path):
        lock_dir = tmp_path / "locks"
        lock = BatchLock("test-track", lock_dir)
        lock_file = lock_dir / "batch_test-track.lock"
        with lock:
            assert lock._depth == 1
            with lock:
                assert lock._depth == 2
            # Inner exit decrements but does NOT delete lock
            assert lock._depth == 1
            assert lock_file.exists()
        # Outer exit deletes lock
        assert not lock_file.exists()

    def test_reentrant_via_existing_lock_file(self, tmp_path):
        """Different BatchLock instance, same PID — re-entrant via lock file."""
        lock_dir = tmp_path / "locks"
        with BatchLock("test-track", lock_dir):
            # Second instance reads lock file, sees our PID
            with BatchLock("test-track", lock_dir):
                pass

    def test_conflict_with_live_pid(self, tmp_path):
        lock_dir = tmp_path / "locks"
        lock_dir.mkdir()
        lock_file = lock_dir / "batch_test-track.lock"
        # Use parent PID (definitely alive, and we have signal permission)
        parent_pid = os.getppid()
        lock_file.write_text(json.dumps({
            "pid": parent_pid,
            "track": "test-track",
            "started": "2024-01-01T00:00:00Z",
        }))
        with pytest.raises(LockConflictError) as exc_info:
            with BatchLock("test-track", lock_dir):
                pass
        assert exc_info.value.pid == parent_pid


# ---------------------------------------------------------------------------
# classify_error
# ---------------------------------------------------------------------------

class TestClassifyError:
    def test_timeout_is_transient(self):
        assert classify_error(-1, "") == ErrorCategory.TRANSIENT

    def test_429_is_quota(self):
        assert classify_error(1, "HTTP 429 Too Many Requests") == ErrorCategory.QUOTA

    def test_invalid_is_permanent(self):
        assert classify_error(1, "Invalid request format") == ErrorCategory.PERMANENT

    def test_unknown_error(self):
        assert classify_error(1, "Something weird happened") == ErrorCategory.UNKNOWN


@pytest.mark.parametrize("message,expected", [
    ("HTTP429", ErrorCategory.QUOTA),
    ("status:401", ErrorCategory.PERMANENT),
    ("HTTP403", ErrorCategory.PERMANENT),
    ("Error 502", ErrorCategory.TRANSIENT),
    ("503", ErrorCategory.TRANSIENT),
    ("HTTP504", ErrorCategory.TRANSIENT),
    ("HTTP500", ErrorCategory.UNKNOWN),
    ("HTTP599", ErrorCategory.UNKNOWN),
    ("0.503", ErrorCategory.UNKNOWN),
    ("v1.429", ErrorCategory.UNKNOWN),
    ("QUOTA HTTP401 timeout", ErrorCategory.QUOTA),
    ("HTTP403 timeout", ErrorCategory.PERMANENT),
    ("authentication HTTP503", ErrorCategory.PERMANENT),
    ("CAPACITY", ErrorCategory.QUOTA),
    ("rate_limit", ErrorCategory.QUOTA),
    ("RESOURCE_EXHAUSTED", ErrorCategory.QUOTA),
    ("rate limit", ErrorCategory.QUOTA),
    ("INVALID", ErrorCategory.PERMANENT),
    ("malformed", ErrorCategory.PERMANENT),
    ("not found", ErrorCategory.PERMANENT),
    ("permission denied", ErrorCategory.PERMANENT),
    ("unavailable", ErrorCategory.TRANSIENT),
    ("connection reset", ErrorCategory.TRANSIENT),
    ("connection refused", ErrorCategory.TRANSIENT),
    ("temporary", ErrorCategory.TRANSIENT),
    ("try again", ErrorCategory.TRANSIENT),
])
def test_status_and_original_keyword_precedence(message, expected):
    assert classify_error(1, message) == expected


def test_timeout_precedes_quota_and_permanent_status():
    assert classify_error(-1, "HTTP429 HTTP403") == ErrorCategory.TRANSIENT
