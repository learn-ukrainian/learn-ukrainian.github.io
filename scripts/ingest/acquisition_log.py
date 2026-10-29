"""Operator-facing progress lines for ``dictionary_acquisition`` (console and ``progress.log``).

SQLite stays the only progress authority and ``status.json``/``job.log`` stay the machine
projections. This module only renders what already happened, one readable line per resolved
target or retry plus a periodic summary, to stderr and an append-only file in the job
directory. A failing sink never stops the job.
"""

from __future__ import annotations

import contextlib
import math
import signal
import sys
import threading
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

DEFAULT_INTERVAL_SECONDS = 60.0
PROGRESS_FILE = "progress.log"
# Two resolved targets are the least that make a rate meaningful; matches status.json's ETA rule.
MIN_RESOLVED_FOR_ETA = 2


class Interrupted(BaseException):
    """SIGTERM or SIGHUP arrived. A BaseException so ``subprocess.run`` also stops its child."""

    def __init__(self, signum: int) -> None:
        super().__init__(signum)
        self.signum = signum


@contextlib.contextmanager
def operator_signals() -> Iterator[None]:
    """Turn SIGTERM/SIGHUP (kill, tmux/terminal close) into ``Interrupted`` so locks unwind and
    the stop is logged. SIGINT already raises ``KeyboardInterrupt``. A hard kill needs no
    handler: the durable store is the checkpoint. No-op off the main thread."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return

    def handler(signum: int, _frame: Any) -> None:
        raise Interrupted(signum)

    wanted = (signal.SIGTERM, signal.SIGHUP)
    previous = {number: signal.signal(number, handler) for number in wanted}
    try:
        yield
    finally:
        for number, old in previous.items():
            signal.signal(number, old)


def interrupt_code(exc: BaseException) -> int:
    """Shell-style exit status for an operator interruption."""
    return 128 + (exc.signum if isinstance(exc, Interrupted) else signal.SIGINT)


def interrupt_name(exc: BaseException) -> str:
    return signal.Signals(exc.signum).name if isinstance(exc, Interrupted) else "SIGINT"


def duration(seconds: float | None) -> str:
    """``unknown`` or a short ``1d 2h`` / ``3h 04m`` / ``5m 06s`` / ``7s`` span."""
    if seconds is None or not math.isfinite(seconds):
        return "unknown"
    total = max(0, round(seconds))
    days, rest = divmod(total, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def sleep_in_slices(
    seconds: float, *, sleep: Callable[[float], None], interval: float, each: Callable[[float], None]
) -> None:
    """Sleep ``seconds`` in slices of at most ``interval`` and call ``each(seconds_left)`` after every
    slice, so a long durable backoff still produces periodic output. A wait that fits in one
    slice is a single ``sleep`` call, exactly as before."""
    left = max(0.0, seconds)
    while True:
        step = min(left, interval)
        sleep(step)
        left -= step
        each(left)
        if left <= 0:
            return


class ProgressLog:
    """Human-readable progress for one dictionary job, written to stderr and ``path``.

    ``done`` counts resolved targets (positive, miss, reused). Rate and ETA are measured over
    this process only, so downtime between runs never distorts them.
    """

    def __init__(
        self,
        path: Path | None,
        *,
        label: str,
        clock: Callable[[], float],
        interval: float = DEFAULT_INTERVAL_SECONDS,
        stream: TextIO | None = None,
    ) -> None:
        self.path = path
        self.label = label
        self.clock = clock
        self.interval = interval
        self.stream = stream
        self.done = 0
        self.total = 0
        self.last_target = ""
        self.retries = 0
        self.errors = 0
        self._resolved_here = 0
        self._began = clock()
        self._last_summary = self._began
        self._warned = False

    def emit(self, message: str) -> None:
        stamp = datetime.fromtimestamp(self.clock(), UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"{stamp} {self.label} {message}"
        if self.path is not None:
            try:
                with self.path.open("a", encoding="utf-8") as handle:
                    handle.write(line + "\n")
            except OSError:
                self._warn("progress file unwritable; console only")
        with contextlib.suppress(OSError, ValueError):
            print(line, file=self.stream or sys.stderr, flush=True)

    def _warn(self, message: str) -> None:
        if not self._warned:
            self._warned = True
            with contextlib.suppress(OSError, ValueError):
                print(f"warning: {message}", file=self.stream or sys.stderr, flush=True)

    def percent(self) -> float:
        return self.done / self.total * 100 if self.total else 0.0

    def where(self) -> str:
        return f"{self.done}/{self.total} ({self.percent():.1f}%)"

    def begin(self, *, done: int, total: int, state: str, retries_used: int) -> None:
        """First line of a run: a fresh job or a resume from the durable checkpoint."""
        self.done, self.total = done, total
        self._began = self._last_summary = self.clock()
        self._resolved_here = 0
        verb = "resuming at" if done or retries_used else "starting at"
        self.emit(f"run: {verb} {self.where()}, job state {state}, attempts used on next target {retries_used}")

    def resolved(self, status: str, target: str, http: int | None) -> None:
        self.done += 1
        self._resolved_here += 1
        self.last_target = target
        code = f" http={http}" if http is not None else ""
        self.emit(f"{self.done}/{self.total} {self.percent():5.1f}%  {status:<9} {target}{code}")

    def retry(self, target: str, attempt: int, limit: int, http: int | None, wait: float) -> None:
        self.retries += 1
        code = f"http={http}" if http is not None else "no response"
        self.emit(f"retry {target} attempt {attempt}/{limit} {code}; next attempt in {duration(wait)}")

    def failed(self, status: str, target: str, reason: str, http: int | None) -> None:
        self.errors += 1
        code = f" http={http}" if http is not None else ""
        self.emit(f"ERROR {status} {target} reason={reason}{code}; job stops here and needs the operator")

    def summary(self) -> None:
        elapsed = self.clock() - self._began
        rate = self._resolved_here / elapsed if elapsed > 0 else 0.0
        eta = None
        if self._resolved_here >= MIN_RESOLVED_FOR_ETA and rate > 0:
            eta = (self.total - self.done) / rate
        self.emit(
            f"progress {self.where()} rate={rate:.2f}/s eta={duration(eta)} "
            f"last={self.last_target or '-'} retries={self.retries} errors={self.errors}"
        )
        self._last_summary = self.clock()

    def tick(self) -> None:
        """Emit the periodic summary once ``interval`` seconds have passed since the last one."""
        if self.clock() - self._last_summary >= self.interval:
            self.summary()

    def finished(self, state: str, reason: str, code: int, note: str = "") -> None:
        self.summary()
        why = f" ({reason})" if reason else ""
        self.emit(f"run: stopped, job state {state}{why}, exit {code}{'; ' + note if note else ''}")

    def interrupted(self, name: str, scope: str = "run") -> None:
        """``scope`` is ``run`` (knows the checkpoint) or ``supervisor`` (its run is stopped with it)."""
        where = f" at {self.where()}" if self.total else ""
        self.emit(
            f"{scope}: interrupted by {name}{where}; progress is saved. "
            "Rerun the same command to continue from the checkpoint"
        )
