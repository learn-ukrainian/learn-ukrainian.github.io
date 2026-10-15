"""Bound, time and log sources MCP tool calls (#10674).

Every ``tools/call`` passes through one :class:`CallGovernor`:

- at most ``max_concurrent`` calls run at once; the rest wait in FIFO order
  for at most ``queue_timeout`` seconds and are then refused as busy;
- a running call is abandoned after ``call_timeout`` seconds and answered
  with a typed timeout. The coroutine is cancelled; blocking work already
  handed to a worker thread finishes in that thread, because Python threads
  cannot be killed;
- each call logs one start and one end line (call id, tool name, in-flight
  and queued counts, outcome, duration). Argument values are never logged;
- a call still running after ``slow_dump_after`` seconds triggers one
  all-thread stack dump into the dump directory, at most one per minute.

Defaults come from the server's own request log (18,946 calls: p99 4.5 s,
p99.9 20.5 s, max 36.7 s) and are overridable through ``LU_SOURCES_*``
environment variables.
"""

from __future__ import annotations

import asyncio
import contextlib
import faulthandler
import itertools
import logging
import os
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")

LOGGER_NAME = "sources.calls"
SLOW_DUMP_INTERVAL_S = 60.0


class CallRefused(Exception):
    """A call was not run to completion; ``code`` is the typed reason."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class GovernorLimits:
    max_concurrent: int = 12
    queue_timeout: float = 30.0
    call_timeout: float = 120.0
    slow_dump_after: float = 60.0

    @classmethod
    def from_environ(cls, environ: Mapping[str, str] | None = None) -> GovernorLimits:
        environ = os.environ if environ is None else environ
        defaults = cls()

        def number(name: str, default: float, minimum: float) -> float:
            raw = environ.get(name, "").strip()
            if not raw:
                return default
            try:
                value = float(raw)
            except ValueError:
                return default
            return value if value >= minimum else default

        return cls(
            max_concurrent=int(number("LU_SOURCES_MAX_CONCURRENT_CALLS", defaults.max_concurrent, 1)),
            queue_timeout=number("LU_SOURCES_QUEUE_TIMEOUT_S", defaults.queue_timeout, 0.1),
            call_timeout=number("LU_SOURCES_CALL_TIMEOUT_S", defaults.call_timeout, 0.1),
            slow_dump_after=number("LU_SOURCES_SLOW_CALL_DUMP_S", defaults.slow_dump_after, 0.1),
        )


def default_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


class CallGovernor:
    def __init__(
        self,
        limits: GovernorLimits,
        *,
        dump_dir: Path | None = None,
        logger: logging.Logger | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limits = limits
        self.dump_dir = dump_dir
        self.logger = logger or default_logger()
        self._clock = clock
        self._ids = itertools.count(1)
        self._slots: asyncio.Semaphore | None = None
        self._slots_loop: asyncio.AbstractEventLoop | None = None
        self._running: dict[int, tuple[str, float]] = {}
        self._dumped: set[int] = set()
        self._queued = 0
        self._last_dump = float("-inf")
        self._watcher: asyncio.Task[None] | None = None

    @property
    def in_flight(self) -> int:
        return len(self._running)

    @property
    def queued(self) -> int:
        return self._queued

    def _semaphore(self) -> asyncio.Semaphore:
        # One semaphore per event loop: an asyncio primitive that has waited on
        # one loop refuses another. The server runs one loop; callers that run
        # several in turn (asyncio.run per call) get a fresh bound each time.
        loop = asyncio.get_running_loop()
        if self._slots is None or self._slots_loop is not loop:
            self._slots = asyncio.Semaphore(self.limits.max_concurrent)
            self._slots_loop = loop
        return self._slots

    async def run(self, tool: str, call: Callable[[], Awaitable[T]]) -> T:
        call_id = next(self._ids)
        started = self._clock()
        slots = self._semaphore()
        self._queued += 1
        try:
            await asyncio.wait_for(slots.acquire(), self.limits.queue_timeout)
        except TimeoutError:
            self._queued -= 1
            self._log_end(call_id, tool, "server_busy", started)
            raise CallRefused(
                "server_busy", f"{self.limits.max_concurrent} calls running; waited {self.limits.queue_timeout:.0f}s"
            ) from None
        self._queued -= 1
        self._running[call_id] = (tool, self._clock())
        self._ensure_watcher()
        self.logger.info(
            "call_start id=%d tool=%s inflight=%d queued=%d wait_ms=%d",
            call_id,
            tool,
            self.in_flight,
            self._queued,
            (self._clock() - started) * 1000,
        )
        outcome = "error"
        try:
            result = await asyncio.wait_for(call(), self.limits.call_timeout)
            outcome = "ok"
            return result
        except TimeoutError:
            outcome = "call_timeout"
            raise CallRefused("call_timeout", f"no result after {self.limits.call_timeout:.0f}s") from None
        except asyncio.CancelledError:
            outcome = "cancelled"
            raise
        finally:
            self._running.pop(call_id, None)
            self._dumped.discard(call_id)
            slots.release()
            self._log_end(call_id, tool, outcome, started)

    def _log_end(self, call_id: int, tool: str, outcome: str, started: float) -> None:
        self.logger.info(
            "call_end id=%d tool=%s outcome=%s duration_ms=%d inflight=%d queued=%d",
            call_id,
            tool,
            outcome,
            (self._clock() - started) * 1000,
            self.in_flight,
            self._queued,
        )

    def _ensure_watcher(self) -> None:
        if self.dump_dir is None or (self._watcher is not None and not self._watcher.done()):
            return
        self._watcher = asyncio.get_running_loop().create_task(self._watch_slow_calls())

    async def _watch_slow_calls(self) -> None:
        interval = min(5.0, self.limits.slow_dump_after / 2)
        while self._running:
            await asyncio.sleep(interval)
            self.check_slow_calls()

    def check_slow_calls(self) -> Path | None:
        """Dump all thread stacks once for a call past ``slow_dump_after``."""
        now = self._clock()
        slow = [
            (call_id, tool, now - begun)
            for call_id, (tool, begun) in self._running.items()
            if now - begun >= self.limits.slow_dump_after and call_id not in self._dumped
        ]
        if not slow or self.dump_dir is None or now - self._last_dump < SLOW_DUMP_INTERVAL_S:
            return None
        self._last_dump = now
        self._dumped.update(call_id for call_id, _tool, _age in slow)
        # sources_watchdog.prune_dump_dir rotates these with the incidents.
        path = self.dump_dir / f"slow-call-{datetime.now(UTC):%Y%m%dT%H%M%SZ}-pid{os.getpid()}.txt"
        with contextlib.suppress(OSError):
            self.dump_dir.mkdir(parents=True, exist_ok=True)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                for call_id, tool, age in slow:
                    handle.write(f"slow call id={call_id} tool={tool} running={age:.0f}s\n")
                handle.write(f"inflight={self.in_flight} queued={self._queued}\n")
                handle.flush()
                faulthandler.dump_traceback(file=handle, all_threads=True)
            self.logger.warning("slow_call_dump path=%s calls=%d", path.name, len(slow))
            return path
        return None
