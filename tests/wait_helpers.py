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
    The predicate is checked once more at the deadline, so a condition that
    became true during the final interval is not reported as a timeout. An
    ``AssertionError`` raised by the predicate propagates, so callers can fail
    fast (e.g. a watched process exited) with their own diagnostics.
    """
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= deadline:
            raise AssertionError(f"{message} not met within {timeout}s")
        time.sleep(interval)


def wait_for_pid_line(path: Path, *, timeout: float = 60.0) -> int:
    """Poll ``path`` until it holds a complete newline-terminated PID."""
    return int(wait_for_line(path, timeout=timeout))
