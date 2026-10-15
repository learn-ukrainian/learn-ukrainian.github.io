"""Call governor: concurrency cap, queue and call timeouts, logging, slow dumps (#10674)."""

from __future__ import annotations

import asyncio
import functools
import itertools
import logging
import os
import threading
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pytest

from scripts.rag.call_governor import EXECUTOR_MARGIN, CallGovernor, CallRefused, GovernorLimits


def _governor(caplog: pytest.LogCaptureFixture, **limits: float) -> CallGovernor:
    logger = logging.getLogger("test.sources.calls")
    logger.setLevel(logging.INFO)
    caplog.set_level(logging.INFO, logger="test.sources.calls")
    return CallGovernor(GovernorLimits(**limits), logger=logger)  # type: ignore[arg-type]


def test_concurrency_is_capped_and_queued_calls_complete(caplog: pytest.LogCaptureFixture) -> None:
    governor = _governor(caplog, max_concurrent=3, queue_timeout=5, call_timeout=5)
    running = peak = 0

    async def call() -> str:
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0.05)
        running -= 1
        return "ok"

    async def main() -> list[str]:
        return await asyncio.gather(*(governor.run("verify_words", call) for _ in range(20)))

    assert asyncio.run(main()) == ["ok"] * 20
    assert peak == 3
    assert governor.in_flight == 0 and governor.queued == 0


def test_the_bound_not_the_cpu_count_decides_how_much_thread_work_runs(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """On one CPU Python's default pool has 5 threads; all 12 calls must still run at once.

    Each call's thread waits until all 12 are running. Had the 7 calls past the
    default pool queued in the executor, they would not start, and that queued
    time would run out their call timeout.
    """
    monkeypatch.setattr(os, "cpu_count", lambda: 1)
    governor = _governor(caplog, max_concurrent=12, queue_timeout=5, call_timeout=2)
    assert governor.executor_workers == 12 + EXECUTOR_MARGIN

    async def main() -> tuple[list[object], int, set[str]]:
        all_running = threading.Barrier(12, timeout=3)
        workers = _BlockedWorkers()
        names: set[str] = set()

        def work() -> str:
            with workers.lock:
                names.add(threading.current_thread().name.rsplit("_", 1)[0])
                workers.running += 1
                workers.peak = max(workers.peak, workers.running)
            all_running.wait()
            return "ok"

        async def call() -> str:
            return await asyncio.to_thread(work)

        outcomes = await asyncio.gather(
            *(governor.run("verify_words", call) for _ in range(12)), return_exceptions=True
        )
        return outcomes, workers.peak, names

    # A fresh event loop gets its own pool: asyncio.run shut the first one down.
    for _ in range(2):
        outcomes, peak, names = asyncio.run(main())
        assert outcomes == ["ok"] * 12
        assert peak == 12
        assert names == {"sources-call"}
        assert governor.abandoned == 0


def test_queue_timeout_refuses_as_server_busy(caplog: pytest.LogCaptureFixture) -> None:
    governor = _governor(caplog, max_concurrent=1, queue_timeout=0.1, call_timeout=5)

    async def main() -> list[object]:
        release = asyncio.Event()

        async def holder() -> str:
            await release.wait()
            return "held"

        first = asyncio.create_task(governor.run("check_text", holder))
        await asyncio.sleep(0.01)
        second = await asyncio.gather(governor.run("check_text", holder), return_exceptions=True)
        release.set()
        return [await first, *second]

    first, second = asyncio.run(main())
    assert first == "held"
    assert isinstance(second, CallRefused) and second.code == "server_busy"
    assert "outcome=server_busy" in caplog.text


def test_call_timeout_returns_typed_refusal_and_frees_the_slot_when_the_work_ends(
    caplog: pytest.LogCaptureFixture,
) -> None:
    governor = _governor(caplog, max_concurrent=1, queue_timeout=5, call_timeout=0.1)

    async def slow() -> None:
        await asyncio.sleep(0.4)

    async def quick() -> str:
        return "ok"

    async def main() -> tuple[object, str]:
        refused = await asyncio.gather(governor.run("query_wikipedia", slow), return_exceptions=True)
        while governor.in_flight:
            await asyncio.sleep(0.02)
        return refused[0], await governor.run("query_wikipedia", quick)

    started = time.monotonic()
    refused, after = asyncio.run(main())
    assert time.monotonic() - started < 5
    assert isinstance(refused, CallRefused) and refused.code == "call_timeout"
    assert after == "ok"
    assert "outcome=call_timeout" in caplog.text
    assert "call_released id=1 tool=query_wikipedia outcome=ok" in caplog.text


class _BlockedWorkers:
    """Thread work that ignores cancellation, like a stuck SQLite query."""

    def __init__(self) -> None:
        self.release = threading.Event()
        self.lock = threading.Lock()
        self.running = self.peak = 0

    def work(self) -> str:
        with self.lock:
            self.running += 1
            self.peak = max(self.peak, self.running)
        try:
            self.release.wait(10)
            return "done"
        finally:
            with self.lock:
                self.running -= 1

    async def call(self) -> str:
        return await asyncio.to_thread(self.work)


async def _until(predicate: Callable[[], bool], limit: float = 5.0) -> None:
    deadline = time.monotonic() + limit
    while not predicate():
        assert time.monotonic() < deadline, "condition not reached"
        await asyncio.sleep(0.01)


def test_timed_out_thread_work_keeps_its_slot_until_it_finishes(caplog: pytest.LogCaptureFixture) -> None:
    """Sol's reproducer: a timeout must not recycle the slot of work still running."""
    governor = _governor(caplog, max_concurrent=1, queue_timeout=5, call_timeout=0.1)
    workers = _BlockedWorkers()

    async def main() -> tuple[list[object], list[float], str]:
        try:
            outcomes: list[object] = []
            waits: list[float] = []
            for _ in range(3):
                begun = time.monotonic()
                outcomes.extend(
                    await asyncio.gather(governor.run("verify_words", workers.call), return_exceptions=True)
                )
                waits.append(time.monotonic() - begun)
            assert workers.running == 1
            assert governor.in_flight == 1 and governor.abandoned == 1
        finally:
            workers.release.set()
        await _until(lambda: governor.in_flight == 0)
        assert governor.abandoned == 0
        return outcomes, waits, await governor.run("verify_words", workers.call)

    outcomes, waits, after = asyncio.run(main())
    codes = [outcome.code if isinstance(outcome, CallRefused) else outcome for outcome in outcomes]
    assert codes == ["call_timeout", "server_overloaded", "server_overloaded"]
    # Refused at once, not after the 5 s queue wait.
    assert max(waits[1:]) < 1.0
    assert workers.peak == 1
    assert after == "done"
    assert "outcome=server_overloaded" in caplog.text
    overloaded = next(
        outcome for outcome in outcomes if isinstance(outcome, CallRefused) and outcome.code != "call_timeout"
    )
    assert overloaded.detail == "all 1 call slots held by timed-out work still running"


def test_queued_calls_are_refused_once_every_slot_is_abandoned(caplog: pytest.LogCaptureFixture) -> None:
    governor = _governor(caplog, max_concurrent=1, queue_timeout=10, call_timeout=0.2)
    workers = _BlockedWorkers()

    async def main() -> tuple[list[object], float]:
        try:
            holder = asyncio.create_task(governor.run("search_text", workers.call))
            await _until(lambda: governor.in_flight == 1)
            begun = time.monotonic()
            queued = await asyncio.gather(governor.run("search_text", workers.call), return_exceptions=True)
            waited = time.monotonic() - begun
            return [*(await asyncio.gather(holder, return_exceptions=True)), *queued], waited
        finally:
            workers.release.set()

    (held, queued), waited = asyncio.run(main())
    assert isinstance(held, CallRefused) and held.code == "call_timeout"
    assert isinstance(queued, CallRefused) and queued.code == "server_overloaded"
    assert waited < 2.0
    assert governor.queued == 0


def test_finished_abandoned_work_hands_its_slot_to_the_next_waiter(caplog: pytest.LogCaptureFixture) -> None:
    governor = _governor(caplog, max_concurrent=2, queue_timeout=10, call_timeout=1.0)
    stuck, live = _BlockedWorkers(), _BlockedWorkers()

    async def quick() -> str:
        return "quick"

    async def main() -> object:
        try:
            refused = await asyncio.gather(governor.run("search_text", stuck.call), return_exceptions=True)
            assert isinstance(refused[0], CallRefused) and refused[0].code == "call_timeout"
            holder = asyncio.create_task(governor.run("search_text", live.call))
            await _until(lambda: governor.in_flight == 2)
            waiter = asyncio.create_task(governor.run("search_text", quick))
            await _until(lambda: governor.queued == 1)
            assert not waiter.done()
            stuck.release.set()
            result = await asyncio.wait_for(waiter, 0.8)
            live.release.set()
            await holder
            return result
        finally:
            stuck.release.set()
            live.release.set()

    assert asyncio.run(main()) == "quick"
    assert governor.in_flight == 0


def test_a_slot_granted_to_a_cancelled_waiter_passes_to_the_next(caplog: pytest.LogCaptureFixture) -> None:
    governor = _governor(caplog, max_concurrent=1, queue_timeout=2, call_timeout=5)

    async def main() -> list[object]:
        release = asyncio.Event()
        waiters: list[asyncio.Task[str]] = []

        async def holder() -> str:
            # Runs after the governor's own done callback has granted the
            # slot to the first waiter, before that waiter resumes.
            task = asyncio.current_task()
            assert task is not None
            task.add_done_callback(lambda _task: waiters[0].cancel())
            await release.wait()
            return "held"

        async def quick() -> str:
            return "quick"

        first = asyncio.create_task(governor.run("search_text", holder))
        await _until(lambda: governor.in_flight == 1)
        waiters.extend(asyncio.create_task(governor.run("search_text", quick)) for _ in range(2))
        await _until(lambda: governor.queued == 2)
        release.set()
        results = await asyncio.gather(first, *waiters, return_exceptions=True)
        return [*results, await asyncio.wait_for(governor.run("search_text", quick), 1)]

    held, cancelled, second, after = asyncio.run(main())
    assert held == "held"
    assert isinstance(cancelled, asyncio.CancelledError)
    assert second == "quick" and after == "quick"
    assert governor.in_flight == 0 and governor.queued == 0


def test_a_cancelled_request_keeps_the_slot_until_its_work_ends(caplog: pytest.LogCaptureFixture) -> None:
    governor = _governor(caplog, max_concurrent=1, queue_timeout=5, call_timeout=30)
    workers = _BlockedWorkers()

    async def main() -> object:
        try:
            request = asyncio.create_task(governor.run("check_text", workers.call))
            await _until(lambda: workers.running == 1)
            request.cancel()
            with pytest.raises(asyncio.CancelledError):
                await request
            assert governor.in_flight == 1 and governor.abandoned == 1
            refused = await asyncio.gather(governor.run("check_text", workers.call), return_exceptions=True)
        finally:
            workers.release.set()
        await _until(lambda: governor.in_flight == 0)
        return refused[0]

    refused = asyncio.run(main())
    assert isinstance(refused, CallRefused) and refused.code == "server_overloaded"
    assert workers.peak == 1
    assert "outcome=cancelled" in caplog.text


def test_log_lines_carry_tool_and_counts_never_arguments(caplog: pytest.LogCaptureFixture) -> None:
    governor = _governor(caplog)
    secret = "приватний-текст-учня"

    async def call() -> str:
        return secret

    assert asyncio.run(governor.run("check_text", call)) == secret
    lines = [record.getMessage() for record in caplog.records]
    assert lines[0].startswith("call_start id=1 tool=check_text inflight=1 queued=0")
    assert lines[1].startswith("call_end id=1 tool=check_text outcome=ok duration_ms=")
    assert secret not in caplog.text


def test_handler_error_is_logged_and_propagates(caplog: pytest.LogCaptureFixture) -> None:
    governor = _governor(caplog)

    async def broken() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        asyncio.run(governor.run("search_text", broken))
    assert "outcome=error" in caplog.text
    assert governor.in_flight == 0


def test_slow_call_writes_one_stack_dump(caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
    logger = logging.getLogger("test.sources.calls")
    caplog.set_level(logging.INFO, logger="test.sources.calls")
    governor = CallGovernor(
        GovernorLimits(max_concurrent=2, queue_timeout=1, call_timeout=5, slow_dump_after=0.2),
        dump_dir=tmp_path,
        logger=logger,
    )

    async def slow() -> str:
        await asyncio.sleep(0.6)
        return "done"

    assert asyncio.run(governor.run("vet_vocabulary", slow)) == "done"
    dumps = list(tmp_path.glob("slow-call-*.txt"))
    assert len(dumps) == 1
    text = dumps[0].read_text(encoding="utf-8")
    assert "tool=vet_vocabulary" in text and "most recent call first" in text
    assert oct(dumps[0].stat().st_mode & 0o777) == "0o600"


def test_slow_dumps_beyond_the_retention_limit_are_pruned_by_the_writer(
    caplog: pytest.LogCaptureFixture, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """More slow dumps than the limit leave at most the limit: the writer prunes."""
    from scripts.rag import call_governor as cg

    limit = 3
    monkeypatch.setattr(cg, "prune_dump_dir", functools.partial(cg.prune_dump_dir, keep=limit))
    monkeypatch.setattr(cg, "SLOW_DUMP_INTERVAL_S", 0.0)
    seconds = itertools.count()

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[no-untyped-def]
            return datetime(2026, 10, 15, 12, 0, next(seconds), tzinfo=tz)

    monkeypatch.setattr(cg, "datetime", Clock)
    caplog.set_level(logging.INFO, logger="test.sources.calls")
    governor = CallGovernor(
        GovernorLimits(max_concurrent=2, queue_timeout=1, call_timeout=5, slow_dump_after=0.0),
        dump_dir=tmp_path,
        logger=logging.getLogger("test.sources.calls"),
    )
    for call_id in range(1, 8):
        governor._running[call_id] = ("vet_vocabulary", governor._clock() - 1)
        assert governor.check_slow_calls() is not None
    names = sorted(path.name for path in tmp_path.glob("slow-call-*.txt"))
    assert len(names) == limit
    assert names[-1].startswith("slow-call-20261015T120006Z")


def test_limits_from_environ_reject_invalid_values() -> None:
    limits = GovernorLimits.from_environ(
        {
            "LU_SOURCES_MAX_CONCURRENT_CALLS": "4",
            "LU_SOURCES_CALL_TIMEOUT_S": "abc",
            "LU_SOURCES_QUEUE_TIMEOUT_S": "-1",
            "LU_SOURCES_SLOW_CALL_DUMP_S": "90",
        }
    )
    assert limits == GovernorLimits(max_concurrent=4, queue_timeout=30.0, call_timeout=120.0, slow_dump_after=90.0)


def test_a_governor_survives_successive_event_loops(caplog: pytest.LogCaptureFixture) -> None:
    governor = _governor(caplog, max_concurrent=1, queue_timeout=5, call_timeout=5)

    async def call() -> str:
        await asyncio.sleep(0.01)
        return "ok"

    async def contended() -> list[str]:
        return await asyncio.gather(governor.run("search_text", call), governor.run("search_text", call))

    assert asyncio.run(contended()) == ["ok", "ok"]
    assert asyncio.run(contended()) == ["ok", "ok"]
