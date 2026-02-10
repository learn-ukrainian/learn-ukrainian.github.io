"""Tests for scripts/batch_utils.py."""

import json
import os
import sys
from pathlib import Path

import pytest

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from batch_utils import (
    atomic_write,
    atomic_write_json,
    ExponentialBackoff,
    BatchLock,
    LockConflictError,
    classify_error,
    ErrorCategory,
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

    def test_overwrites_existing(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("old")
        atomic_write(p, "new")
        assert p.read_text() == "new"


class TestAtomicWriteJson:
    def test_writes_json(self, tmp_path):
        p = tmp_path / "data.json"
        atomic_write_json(p, {"key": "value", "num": 42})
        data = json.loads(p.read_text())
        assert data == {"key": "value", "num": 42}

    def test_unicode(self, tmp_path):
        p = tmp_path / "uk.json"
        atomic_write_json(p, {"word": "привіт"})
        data = json.loads(p.read_text())
        assert data["word"] == "привіт"


# ---------------------------------------------------------------------------
# ExponentialBackoff
# ---------------------------------------------------------------------------

class TestExponentialBackoff:
    def test_first_attempt(self):
        b = ExponentialBackoff(base=60, max_wait=600, jitter=0)
        assert b.wait_time(1) == 60

    def test_second_attempt_doubles(self):
        b = ExponentialBackoff(base=60, max_wait=600, jitter=0)
        assert b.wait_time(2) == 120

    def test_respects_max_wait(self):
        b = ExponentialBackoff(base=60, max_wait=300, jitter=0)
        # attempt 4: 60 * 8 = 480 > 300, capped at 300
        assert b.wait_time(4) == 300

    def test_jitter_range(self):
        b = ExponentialBackoff(base=100, max_wait=1000, jitter=0.5)
        values = [b.wait_time(1) for _ in range(100)]
        # base=100, jitter=0.5 → range [50, 150]
        assert all(50 <= v <= 150 for v in values)
        # With 100 samples, we should see variation
        assert max(values) > min(values)


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

    def test_resource_exhausted_is_quota(self):
        assert classify_error(1, "RESOURCE_EXHAUSTED: quota exceeded") == ErrorCategory.QUOTA

    def test_capacity_is_quota(self):
        assert classify_error(1, "Server capacity is at limit") == ErrorCategory.QUOTA

    def test_502_is_transient(self):
        assert classify_error(1, "502 Bad Gateway") == ErrorCategory.TRANSIENT

    def test_503_is_transient(self):
        assert classify_error(1, "503 Service Unavailable") == ErrorCategory.TRANSIENT

    def test_invalid_is_permanent(self):
        assert classify_error(1, "Invalid request format") == ErrorCategory.PERMANENT

    def test_permission_denied_is_permanent(self):
        assert classify_error(1, "Permission denied for resource") == ErrorCategory.PERMANENT

    def test_unknown_error(self):
        assert classify_error(1, "Something weird happened") == ErrorCategory.UNKNOWN

    def test_should_retry_property(self):
        assert ErrorCategory.TRANSIENT.should_retry is True
        assert ErrorCategory.QUOTA.should_retry is True
        assert ErrorCategory.UNKNOWN.should_retry is True
        assert ErrorCategory.PERMANENT.should_retry is False
