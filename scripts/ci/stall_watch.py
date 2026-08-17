#!/usr/bin/env python3
"""Controller-side stall watch for the required pytest CI Gate (#5776 leftover).

`pytest-timeout` (`--timeout=120 --timeout-method=thread`) lives inside xdist
WORKERS. A stall in the CONTROLLER, or a full pipe between a worker and the
controller, never trips it — the watchdog's own report can block on the same
full pipe it needs to write to. That is why a required shard has hung silently
at ~95% of the suite and only reported after the job's 25-minute cap cancelled
it (autopsy: docs/bug-autopsies/2026-07-25-ci-gate-reboot.md §3).

`tests/conftest.py` already writes a `START <nodeid>` / `FINISH <nodeid>`
breadcrumb per worker under `PYTEST_BREADCRUMB_DIR` directly to disk — outside
the xdist pipe, so it is unaffected by a pipe-full deadlock. This module polls
those breadcrumbs while pytest runs and, if any worker's most recent `START`
goes without a matching `FINISH` for `stall_budget` seconds, kills the pytest
process tree and exits non-zero — naming the stuck node ID on stderr instead
of leaving the job to sit until GitHub cancels it.
"""

from __future__ import annotations

import contextlib
import os
import re
import signal
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

DEFAULT_STALL_BUDGET_SECONDS = 90.0
_STALL_BUDGET_ENV = "CI_STALL_WATCH_SECONDS"
_POLL_INTERVAL_ENV = "CI_STALL_WATCH_POLL_SECONDS"
_BREADCRUMB_DIR_ENV = "PYTEST_BREADCRUMB_DIR"
_DEFAULT_BREADCRUMB_DIR = ".pytest_breadcrumbs"
_BREADCRUMB_LINE = re.compile(r"^(START|FINISH) (.+)$")


@dataclass(frozen=True)
class StalledNode:
    """A worker whose most recent START has gone without a FINISH too long."""

    worker_id: str
    nodeid: str
    stalled_for: float


def stall_budget_seconds() -> float:
    """Stall budget in seconds; env-overridable so tests can shrink it."""
    raw = os.environ.get(_STALL_BUDGET_ENV)
    return float(raw) if raw else DEFAULT_STALL_BUDGET_SECONDS


def poll_interval_seconds(stall_budget: float) -> float:
    raw = os.environ.get(_POLL_INTERVAL_ENV)
    if raw:
        return float(raw)
    return max(0.05, min(5.0, stall_budget / 10))


def breadcrumb_dir_from_env() -> Path | None:
    """Mirror tests/conftest.py: empty PYTEST_BREADCRUMB_DIR disables breadcrumbs."""
    raw = os.environ.get(_BREADCRUMB_DIR_ENV, _DEFAULT_BREADCRUMB_DIR)
    return Path(raw) if raw else None


def _worker_id_from_filename(path: Path) -> str:
    return path.stem.removeprefix("breadcrumb_")


def _last_event(path: Path) -> tuple[str, str] | None:
    """Return (event, nodeid) for the last breadcrumb line, or None if idle."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    last_line = ""
    for line in text.splitlines():
        if line.strip():
            last_line = line
    match = _BREADCRUMB_LINE.match(last_line)
    return (match.group(1), match.group(2)) if match else None


def find_stalled_nodes(
    breadcrumb_dir: Path,
    *,
    stall_budget: float,
    state: dict[str, tuple[str, float]],
) -> list[StalledNode]:
    """One poll pass. `state` persists worker_id -> (nodeid, first_seen) across calls."""
    if not breadcrumb_dir.exists():
        return []
    now = time.monotonic()
    stalled: list[StalledNode] = []
    seen_workers: set[str] = set()
    for path in sorted(breadcrumb_dir.glob("breadcrumb_*.txt")):
        worker_id = _worker_id_from_filename(path)
        seen_workers.add(worker_id)
        event = _last_event(path)
        if event is None or event[0] != "START":
            state.pop(worker_id, None)
            continue
        nodeid = event[1]
        tracked = state.get(worker_id)
        if tracked is None or tracked[0] != nodeid:
            state[worker_id] = (nodeid, now)
            continue
        elapsed = now - tracked[1]
        if elapsed >= stall_budget:
            stalled.append(StalledNode(worker_id=worker_id, nodeid=nodeid, stalled_for=elapsed))
    for worker_id in [worker_id for worker_id in state if worker_id not in seen_workers]:
        state.pop(worker_id, None)
    return stalled


def format_stall_message(node: StalledNode, *, stall_budget: float) -> str:
    return (
        f"::error::CI stall watch: worker {node.worker_id} stuck on {node.nodeid} "
        f"for {node.stalled_for:.1f}s with no FINISH breadcrumb (budget {stall_budget:.0f}s) "
        "- controller-side stall, killing pytest (#5776 leftover, see #6943)."
    )


def report_stall(
    stalled: list[StalledNode],
    *,
    stall_budget: float,
    raw_fd: int | None = None,
    stream=sys.stderr,
) -> None:
    """Emit one message per stalled node.

    Prefers a raw, pre-duplicated fd: pytest's own default (fd-level) output
    capture redirects fd 2 for the run's duration, so a plain `print(...,
    file=sys.stderr)` from inside a running test session is silently
    swallowed into pytest's capture buffer instead of reaching CI's real log.
    """
    for node in stalled:
        message = format_stall_message(node, stall_budget=stall_budget) + "\n"
        if raw_fd is not None:
            with contextlib.suppress(OSError):
                os.write(raw_fd, message.encode("utf-8"))
        else:
            print(message, end="", file=stream)
    if raw_fd is None:
        stream.flush()


def kill_current_process_group() -> None:
    """Kill this controller's process group (xdist workers + self) and hard-exit."""
    try:
        pgid = os.getpgrp()
    except OSError:
        pgid = None
    if pgid is not None:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(pgid, signal.SIGKILL)
    os._exit(1)


class StallWatcher:
    """Background poller that fails a wedged controller fast instead of silently."""

    def __init__(
        self,
        breadcrumb_dir: Path | None,
        *,
        stall_budget: float | None = None,
        poll_interval: float | None = None,
        report: Callable[[list[StalledNode]], None] | None = None,
        terminate: Callable[[], None] = kill_current_process_group,
    ) -> None:
        self.breadcrumb_dir = breadcrumb_dir
        self.stall_budget = stall_budget if stall_budget is not None else stall_budget_seconds()
        self.poll_interval = (
            poll_interval if poll_interval is not None else poll_interval_seconds(self.stall_budget)
        )
        self._report = report
        self._terminate = terminate
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._state: dict[str, tuple[str, float]] = {}
        self._real_stderr_fd: int | None = None

    def start(self) -> StallWatcher:
        if self.breadcrumb_dir is not None:
            # Duplicate the real stderr fd now, before pytest.main() installs its
            # own fd-level capture redirect - see report_stall()'s docstring.
            with contextlib.suppress(OSError):
                self._real_stderr_fd = os.dup(sys.stderr.fileno())
            self._thread = threading.Thread(target=self._run, name="ci-stall-watch", daemon=True)
            self._thread.start()
        return self

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self.poll_interval * 2)
        if self._real_stderr_fd is not None:
            with contextlib.suppress(OSError):
                os.close(self._real_stderr_fd)
            self._real_stderr_fd = None

    def __enter__(self) -> StallWatcher:
        return self.start()

    def __exit__(self, *exc_info: object) -> None:
        self.stop()

    def _run(self) -> None:
        assert self.breadcrumb_dir is not None
        while not self._stop_event.is_set():
            stalled = find_stalled_nodes(self.breadcrumb_dir, stall_budget=self.stall_budget, state=self._state)
            if stalled:
                if self._report is not None:
                    self._report(stalled)
                else:
                    report_stall(stalled, stall_budget=self.stall_budget, raw_fd=self._real_stderr_fd)
                self._terminate()
                return
            self._stop_event.wait(self.poll_interval)

    @classmethod
    def from_env(cls, **overrides: object) -> StallWatcher:
        return cls(breadcrumb_dir_from_env(), **overrides)
