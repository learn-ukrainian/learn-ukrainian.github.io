"""Pure liveness probe primitives for agent-runtime subprocess monitoring.

This module intentionally has no integration points yet. Phase 2 wires these
primitives into watchdog.py; Phase 1 keeps them independently unit-testable.
"""
from __future__ import annotations

import glob
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import psutil


class Signal(Protocol):
    """A probe signal returns True if it observes liveness, False if not."""

    def evaluate(self) -> bool: ...


def _newest_path(pattern: str) -> Path | None:
    """Return the newest matching path, or None when no file exists."""
    matches = [Path(match) for match in glob.glob(pattern) if Path(match).exists()]
    if not matches:
        return None
    return max(matches, key=lambda path: path.stat().st_mtime)


@dataclass
class FileMTimeSignal:
    """Positive if the target file's mtime is within max_age_s of now.

    For glob patterns (e.g. rollout-*.jsonl), pick the newest match.
    Absent file -> False.
    """

    path: str
    max_age_s: int
    # Deviation from the sketch: injectable clock keeps tests deterministic
    # without monkeypatching module globals.
    now_provider: Callable[[], float] = field(default=time.time, repr=False, compare=False)

    def evaluate(self) -> bool:
        target = _newest_path(self.path)
        if target is None:
            return False
        return (self.now_provider() - target.stat().st_mtime) <= self.max_age_s


@dataclass
class FileSizeGrowthSignal:
    """Positive if the target file has grown by >= min_bytes since the last call.

    First call is always True (baselining). Absent file -> False.
    State lives on the instance so CompositeProbe can reuse it across cycles.
    """

    path: str
    min_bytes: int
    _last_size: int | None = field(default=None, init=False, repr=False)

    def evaluate(self) -> bool:
        target = Path(self.path)
        if not target.exists():
            self._last_size = None
            return False

        current_size = target.stat().st_size
        if self._last_size is None:
            self._last_size = current_size
            return True

        grew_by = current_size - self._last_size
        self._last_size = current_size
        return grew_by >= self.min_bytes


@dataclass
class ProcCpuSignal:
    """Positive if the given PID shows >= min_percent CPU over sample_window_s."""

    pid: int
    min_percent: float
    sample_window_s: float = 1.0

    def evaluate(self) -> bool:
        try:
            process = psutil.Process(self.pid)
            return process.cpu_percent(interval=self.sample_window_s) >= self.min_percent
        except psutil.Error:
            return False


@dataclass
class StdoutStreamedSignal:
    """Positive if stdout received any byte within max_age_s seconds."""

    last_write_time_provider: Callable[[], float | None]
    max_age_s: int
    # Deviation from the sketch: injectable clock keeps tests deterministic
    # without monkeypatching module globals.
    now_provider: Callable[[], float] = field(default=time.time, repr=False, compare=False)

    def evaluate(self) -> bool:
        last_write_time = self.last_write_time_provider()
        if last_write_time is None:
            return False
        return (self.now_provider() - last_write_time) <= self.max_age_s


@dataclass
class CompositeProbe:
    """ANY-mode composition with failure threshold."""

    signals: list[Signal]
    failure_threshold: int = 3
    period_s: int = 30
    initial_delay_s: int = 90
    _failure_count: int = 0
    _started_at: float | None = None

    def evaluate_once(self) -> bool:
        """Return True if ANY signal reports alive."""
        return any(signal.evaluate() for signal in self.signals)

    def report(self, alive_this_cycle: bool) -> None:
        """Advance or reset the failure counter."""
        if alive_this_cycle:
            self._failure_count = 0
        else:
            self._failure_count += 1

    def should_kill(self) -> bool:
        """Return True when consecutive failures reached the threshold."""
        return self._failure_count >= self.failure_threshold

    def in_initial_grace(self, now: float) -> bool:
        """True if evaluation should be deferred while startup finishes."""
        if self._started_at is None:
            return False
        return (now - self._started_at) < self.initial_delay_s
