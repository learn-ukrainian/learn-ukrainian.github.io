"""Bound, time and log sources MCP tool calls (#10674).

Every ``tools/call`` passes through one :class:`CallGovernor`:

- at most ``max_concurrent`` calls hold a slot at once; the rest wait in FIFO
  order for at most ``queue_timeout`` seconds and are then refused as busy;
- a caller stops waiting after ``call_timeout`` seconds (or when its request
  is cancelled) and is answered with a typed timeout. The call itself is
  abandoned, not cancelled: its blocking work runs in a worker thread that
  Python cannot kill, so the call keeps its slot until that work finishes.
  A timeout therefore never lets more than ``max_concurrent`` calls' work run
  at once;
- while every slot is held by abandoned work, new and queued calls are
  refused at once as overloaded instead of waiting for a slot that may never
  come back;
- calls' blocking work runs on the event loop's default executor, which the
  governor replaces with its own pool of ``max_concurrent`` +
  ``EXECUTOR_MARGIN`` threads. Python's default pool has
  ``min(32, cpu_count + 4)`` threads, so on a small host it would cap
  running work below the bound, and time a call spent queued in it would
  count against ``call_timeout``;
- each call logs one start and one end line (call id, tool name, in-flight,
  queued and abandoned counts, outcome, duration), and an abandoned call one
  more line when its work finishes and frees the slot. Argument values are
  never logged.

Defaults come from the server's own request log (18,946 calls: p99 4.5 s,
p99.9 20.5 s, max 36.7 s) and are overridable through ``LU_SOURCES_*``
environment variables.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import itertools
import logging
import os
import time
from collections import deque
from collections.abc import Awaitable, Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")

LOGGER_NAME = "sources.calls"
# Each call runs at most one executor job at a time, and its slot outlives
# that job, so ``max_concurrent`` threads cover every call. The margin is
# for executor users outside a call (asyncio resolves host names on the
# default executor), so they never take a thread a call is entitled to.
# The /health handler and the call bookkeeping run on the loop thread.
EXECUTOR_MARGIN = 4


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
        logger: logging.Logger | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limits = limits
        self.logger = logger or default_logger()
        self._clock = clock
        self._ids = itertools.count(1)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._held = 0
        self._waiters: deque[asyncio.Future[bool]] = deque()
        self._running: dict[int, tuple[str, float]] = {}
        self._abandoned: set[int] = set()
        self._tasks: set[asyncio.Task[Any]] = set()
        self._queued = 0

    @property
    def in_flight(self) -> int:
        """Calls holding a slot, abandoned ones included."""
        return len(self._running)

    @property
    def abandoned(self) -> int:
        """Calls whose caller has been answered while their work still runs."""
        return len(self._abandoned)

    @property
    def queued(self) -> int:
        return self._queued

    @property
    def executor_workers(self) -> int:
        """Threads in the executor the governor gives each event loop."""
        return self.limits.max_concurrent + EXECUTOR_MARGIN

    def _bind_loop(self) -> asyncio.AbstractEventLoop:
        # Slots, waiters and tasks belong to one event loop. The server runs
        # one loop; a caller that runs several in turn (asyncio.run per call)
        # gets fresh accounting, since a closed loop's tasks never finish.
        loop = asyncio.get_running_loop()
        if self._loop is not loop:
            self._loop = loop
            self._held = self._queued = 0
            self._waiters.clear()
            self._running.clear()
            self._abandoned.clear()
            self._tasks.clear()
            # A new pool per loop: asyncio.run shuts the loop's default
            # executor down when the loop ends.
            loop.set_default_executor(
                ThreadPoolExecutor(max_workers=self.executor_workers, thread_name_prefix="sources-call")
            )
        return loop

    def _overloaded(self) -> CallRefused:
        return CallRefused(
            "server_overloaded", f"all {self.limits.max_concurrent} call slots held by timed-out work still running"
        )

    def _saturated(self) -> bool:
        return len(self._abandoned) >= self.limits.max_concurrent

    async def _acquire(self, loop: asyncio.AbstractEventLoop) -> None:
        if self._saturated():
            raise self._overloaded()
        if self._held < self.limits.max_concurrent and not self._waiters:
            self._held += 1
            return
        # A released slot passes straight to the first waiter (True); a
        # waiter refused because every slot is abandoned receives False.
        waiter: asyncio.Future[bool] = loop.create_future()
        self._waiters.append(waiter)
        self._queued += 1
        try:
            async with asyncio.timeout(self.limits.queue_timeout):
                granted = await waiter
        except BaseException as error:
            if waiter.done() and not waiter.cancelled() and waiter.result():
                # Granted in the same instant the wait ended: pass it on.
                self._release()
            else:
                waiter.cancel()
            if isinstance(error, TimeoutError):
                raise CallRefused(
                    "server_busy",
                    f"{self.limits.max_concurrent} calls running; waited {self.limits.queue_timeout:.0f}s",
                ) from None
            raise
        finally:
            self._queued -= 1
            with contextlib.suppress(ValueError):
                self._waiters.remove(waiter)
        if not granted:
            raise self._overloaded()

    def _release(self) -> None:
        while self._waiters:
            waiter = self._waiters.popleft()
            if not waiter.done():
                waiter.set_result(True)
                return
        self._held -= 1

    def _abandon(self, call_id: int) -> None:
        self._abandoned.add(call_id)
        if self._saturated():
            while self._waiters:
                waiter = self._waiters.popleft()
                if not waiter.done():
                    waiter.set_result(False)

    def _finished(self, call_id: int, tool: str, started: float, task: asyncio.Task[Any]) -> None:
        """Done callback of a call's work: its slot is freed here, when the work ends."""
        self._tasks.discard(task)
        self._running.pop(call_id, None)
        abandoned = call_id in self._abandoned
        self._abandoned.discard(call_id)
        self._release()
        if not abandoned:
            return
        # Retrieving the exception keeps asyncio from reporting it as never
        # retrieved; the caller was already answered.
        outcome = "cancelled" if task.cancelled() else "ok" if task.exception() is None else "error"
        self.logger.info(
            "call_released id=%d tool=%s outcome=%s duration_ms=%d inflight=%d queued=%d abandoned=%d",
            call_id,
            tool,
            outcome,
            (self._clock() - started) * 1000,
            self.in_flight,
            self._queued,
            self.abandoned,
        )

    async def run(self, tool: str, call: Callable[[], Awaitable[T]]) -> T:
        loop = self._bind_loop()
        call_id = next(self._ids)
        started = self._clock()
        try:
            await self._acquire(loop)
        except CallRefused as refusal:
            self._log_end(call_id, tool, refusal.code, started)
            raise
        self._running[call_id] = (tool, self._clock())
        self.logger.info(
            "call_start id=%d tool=%s inflight=%d queued=%d abandoned=%d wait_ms=%d",
            call_id,
            tool,
            self.in_flight,
            self._queued,
            self.abandoned,
            (self._clock() - started) * 1000,
        )
        try:
            work: asyncio.Future[T] = asyncio.ensure_future(call())
        except BaseException:
            self._running.pop(call_id, None)
            self._release()
            self._log_end(call_id, tool, "error", started)
            raise
        self._tasks.add(work)  # the loop keeps only weak references to tasks
        work.add_done_callback(functools.partial(self._finished, call_id, tool, started))
        outcome = "error"
        try:
            # asyncio.wait never cancels the work; it only stops waiting.
            await asyncio.wait((work,), timeout=self.limits.call_timeout)
            if not work.done():
                outcome = "call_timeout"
                self._abandon(call_id)
                raise CallRefused("call_timeout", f"no result after {self.limits.call_timeout:.0f}s")
            result = work.result()
            outcome = "ok"
            return result
        except asyncio.CancelledError:
            outcome = "cancelled"
            if not work.done():
                self._abandon(call_id)
            raise
        finally:
            self._log_end(call_id, tool, outcome, started)

    def _log_end(self, call_id: int, tool: str, outcome: str, started: float) -> None:
        self.logger.info(
            "call_end id=%d tool=%s outcome=%s duration_ms=%d inflight=%d queued=%d abandoned=%d",
            call_id,
            tool,
            outcome,
            (self._clock() - started) * 1000,
            self.in_flight,
            self._queued,
            self.abandoned,
        )
