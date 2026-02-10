"""
Reusable utilities for batch operations.

Provides: atomic file writes, exponential backoff, PID-based lock files,
and error classification. All stdlib — zero new dependencies.
"""

import enum
import json
import logging
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("batch")


# ---------------------------------------------------------------------------
# Atomic file writes
# ---------------------------------------------------------------------------

def atomic_write(path: Path | str, content: str, encoding: str = "utf-8") -> None:
    """Write content to a file atomically (write to PID-unique .tmp, then rename).

    Uses PID in temp filename to avoid collisions between concurrent processes.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    try:
        tmp.write_text(content, encoding=encoding)
        tmp.rename(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def atomic_write_json(path: Path | str, data, indent: int = 2) -> None:
    """Write JSON data to a file atomically."""
    atomic_write(path, json.dumps(data, indent=indent, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Exponential backoff
# ---------------------------------------------------------------------------

class ExponentialBackoff:
    """Compute exponential backoff wait times with jitter.

    Usage:
        backoff = ExponentialBackoff(base=60, max_wait=600, jitter=0.3)
        for attempt in range(1, 4):
            time.sleep(backoff.wait_time(attempt))
    """

    def __init__(self, base: float = 60, max_wait: float = 600, jitter: float = 0.3):
        self.base = base
        self.max_wait = max_wait
        self.jitter = jitter

    def wait_time(self, attempt: int) -> float:
        """Return wait time in seconds for a given attempt (1-indexed)."""
        raw = min(self.base * (2 ** (attempt - 1)), self.max_wait)
        jitter_range = raw * self.jitter
        return raw + random.uniform(-jitter_range, jitter_range)


# ---------------------------------------------------------------------------
# PID-based lock file
# ---------------------------------------------------------------------------

class LockConflictError(Exception):
    """Raised when another process holds the batch lock."""

    def __init__(self, track: str, pid: int, started: str):
        self.track = track
        self.pid = pid
        self.started = started
        super().__init__(
            f"Batch lock conflict for track '{track}': "
            f"PID {pid} started at {started}"
        )


class BatchLock:
    """Context manager providing PID-based lock files for batch runs.

    Usage:
        with BatchLock("c1-bio", lock_dir=Path("batch_state/locks")):
            # ... run batch ...

    Raises LockConflictError if another live process holds the lock.
    Cleans up stale locks (dead PIDs) automatically.
    Uses O_CREAT|O_EXCL for atomic lock creation (no TOCTOU race).
    """

    def __init__(self, track: str, lock_dir: Path | str):
        self.track = track
        self.lock_dir = Path(lock_dir)
        self.lock_file = self.lock_dir / f"batch_{track}.lock"
        self._depth = 0  # Re-entrancy counter

    def __enter__(self):
        # Re-entrant: if already holding lock, just increment depth
        if self._depth > 0:
            self._depth += 1
            return self

        self.lock_dir.mkdir(parents=True, exist_ok=True)

        if self.lock_file.exists():
            try:
                data = json.loads(self.lock_file.read_text(encoding="utf-8"))
                pid = data.get("pid", 0)
                started = data.get("started", "unknown")

                if pid == os.getpid():
                    # Same process — track re-entrancy
                    self._depth += 1
                    return self

                # Check if PID is alive
                os.kill(pid, 0)
                # Process is alive (or we lack permission) — conflict
                raise LockConflictError(self.track, pid, started)
            except ProcessLookupError:
                # Process is dead — stale lock, clean up
                log.info(f"Cleaning up stale lock for track '{self.track}' (PID {pid})")
                self.lock_file.unlink(missing_ok=True)
            except PermissionError:
                # Process exists but belongs to another user — conflict
                raise LockConflictError(self.track, pid, started)
            except (json.JSONDecodeError, OSError):
                # Corrupt lock file — remove it
                self.lock_file.unlink(missing_ok=True)

        # Atomic lock creation with O_CREAT|O_EXCL — prevents TOCTOU race
        lock_data = json.dumps({
            "pid": os.getpid(),
            "track": self.track,
            "started": datetime.now(timezone.utc).isoformat(),
        }, indent=2)

        try:
            fd = os.open(
                str(self.lock_file),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o644,
            )
            try:
                os.write(fd, lock_data.encode("utf-8"))
            finally:
                os.close(fd)
        except FileExistsError:
            # Another process won the race — try to read their lock info
            try:
                data = json.loads(self.lock_file.read_text(encoding="utf-8"))
                raise LockConflictError(
                    self.track,
                    data.get("pid", 0),
                    data.get("started", "unknown"),
                )
            except (json.JSONDecodeError, OSError):
                raise LockConflictError(self.track, 0, "unknown")

        self._depth = 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._depth -= 1
        if self._depth <= 0:
            self.lock_file.unlink(missing_ok=True)
            self._depth = 0
        return False


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

class ErrorCategory(enum.Enum):
    """Classification of batch operation errors."""
    TRANSIENT = "transient"   # Timeout, 502/503, "unavailable" — worth retrying
    QUOTA = "quota"           # Quota/rate limit — needs backoff or account rotation
    PERMANENT = "permanent"   # Invalid input, malformed — skip retries
    UNKNOWN = "unknown"       # Default — retry normally

    @property
    def should_retry(self) -> bool:
        return self in (ErrorCategory.TRANSIENT, ErrorCategory.QUOTA, ErrorCategory.UNKNOWN)


_QUOTA_KEYWORDS = ("quota", "resource_exhausted", "rate limit", "capacity", "rate_limit")
_TRANSIENT_KEYWORDS = ("timeout", "unavailable", "502", "503", "504", "connection reset",
                       "connection refused", "temporary", "try again")
_PERMANENT_KEYWORDS = ("invalid", "malformed", "not found", "permission denied",
                       "authentication", "401", "403")


def classify_error(
    returncode: int,
    stderr: str,
    elapsed_ms: int = 0,
    timeout_ms: int = 0,
) -> ErrorCategory:
    """Classify a process error into a category for retry decisions.

    Args:
        returncode: Process exit code (-1 for timeout).
        stderr: Standard error output.
        elapsed_ms: How long the process ran.
        timeout_ms: The configured timeout (for detecting near-timeout).

    Returns:
        ErrorCategory indicating how to handle the error.
    """
    lower = stderr.lower()

    # Timeout is always transient
    if returncode == -1:
        return ErrorCategory.TRANSIENT

    # Check for quota keywords (including "429")
    if "429" in stderr or any(kw in lower for kw in _QUOTA_KEYWORDS):
        return ErrorCategory.QUOTA

    # Check for permanent errors
    if any(kw in lower for kw in _PERMANENT_KEYWORDS):
        return ErrorCategory.PERMANENT

    # Check for transient errors
    if any(kw in lower for kw in _TRANSIENT_KEYWORDS):
        return ErrorCategory.TRANSIENT

    return ErrorCategory.UNKNOWN
