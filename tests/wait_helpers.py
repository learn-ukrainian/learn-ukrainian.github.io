"""Shared polling helper for tests that read a subprocess-written file.

A poll loop that stops as soon as a path exists races its writer: ``open()``
creates (and truncates) the file before the write lands, so a reader can
observe an empty or partially written file. Wait for a trailing newline
instead — a reliable proxy for "the writer's line finished" — with a real
deadline and a clear failure message.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path


def wait_for_line(
    path: Path,
    *,
    timeout: float = 60.0,
    interval: float = 0.01,
    stop_if: Callable[[], bool] | None = None,
) -> str:
    """Poll ``path`` until it holds a complete newline-terminated line.

    Returns the stripped content. Raises ``AssertionError`` naming the last
    observed content if ``timeout`` elapses first. ``stop_if``, when given, is
    checked each iteration so callers can fail fast (e.g. the writer process
    died) instead of waiting out the full deadline.
    """
    deadline = time.monotonic() + timeout
    content = ""
    while time.monotonic() < deadline:
        if path.exists():
            content = path.read_text(encoding="utf-8")
            if content.endswith("\n") and content.strip():
                return content.strip()
        if stop_if is not None and stop_if():
            break
        time.sleep(interval)
    raise AssertionError(f"{path} did not contain a complete line within {timeout}s (last read: {content!r})")


def wait_until(
    predicate: Callable[[], bool],
    *,
    timeout: float = 60.0,
    interval: float = 0.01,
    message: str = "condition",
) -> None:
    """Poll ``predicate`` until it returns true, with a real deadline.

    Raises ``AssertionError`` naming ``message`` if ``timeout`` elapses first.
    Each sleep is capped at the time remaining, so the wait never overshoots
    the deadline. A wait succeeds only if the predicate returned true at a time
    that is not after the deadline, with the time read from the monotonic clock
    after the predicate returns: a true result observed past the deadline (a
    late wake-up, or a slow predicate) is a timeout. The evaluation at exactly
    the deadline may succeed. An ``AssertionError`` raised by the predicate
    propagates, so callers can fail fast (e.g. a watched process exited) with
    their own diagnostics.
    """
    deadline = time.monotonic() + timeout
    while True:
        met = predicate()
        now = time.monotonic()
        if now <= deadline and met:
            return
        remaining = deadline - now
        if remaining <= 0:
            raise AssertionError(f"{message} not met within {timeout}s")
        time.sleep(min(interval, remaining))


def wait_for_pid_line(path: Path, *, timeout: float = 60.0) -> int:
    """Poll ``path`` until it holds a complete newline-terminated PID."""
    return int(wait_for_line(path, timeout=timeout))
