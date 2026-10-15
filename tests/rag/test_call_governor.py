"""Call governor: concurrency cap, queue and call timeouts, logging, slow dumps (#10674)."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

import pytest

from scripts.rag.call_governor import CallGovernor, CallRefused, GovernorLimits


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


def test_call_timeout_returns_typed_refusal_and_frees_the_slot(caplog: pytest.LogCaptureFixture) -> None:
    governor = _governor(caplog, max_concurrent=1, queue_timeout=5, call_timeout=0.1)

    async def stuck() -> None:
        await asyncio.sleep(30)

    async def quick() -> str:
        return "ok"

    async def main() -> tuple[object, str]:
        refused = await asyncio.gather(governor.run("query_wikipedia", stuck), return_exceptions=True)
        return refused[0], await governor.run("query_wikipedia", quick)

    started = time.monotonic()
    refused, after = asyncio.run(main())
    assert time.monotonic() - started < 5
    assert isinstance(refused, CallRefused) and refused.code == "call_timeout"
    assert after == "ok"
    assert "outcome=call_timeout" in caplog.text


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
