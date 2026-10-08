"""has_headroom reads usage JSONL through the shared strict line reader (#9924).

A line that is not strict UTF-8, not JSON, or not a JSON object — including a
truncated last line — is skipped and counted on the caller's ``unreadable``
counter instead of raising or being silently dropped. Valid rows in the same
file still drive the headroom decision, and the headroom threshold constants
are unchanged.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from agent_runtime import usage as usage_mod

AGENT = "codex"
MODEL = "gpt-6.1-sol"


def _stamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).isoformat()


def _record_line(ts: float, *, model: str = MODEL, outcome: str) -> bytes:
    record = {
        "ts": _stamp(ts),
        "agent": AGENT,
        "entrypoint": "delegate",
        "model": model,
        "outcome": outcome,
    }
    return (json.dumps(record) + "\n").encode("utf-8")


def _corrupt_line(kind: str) -> bytes:
    """One bad usage line, mirroring the corruption classes of #9868."""
    if kind == "json-non-object":
        return b"[]\n"
    if kind == "invalid-json":
        return b"{not-json\n"
    if kind == "invalid-utf8":
        return b"\xff\n"
    if kind == "invalid-utf8-in-string":
        payload = json.dumps(
            {
                "ts": _stamp(time.time() - 25),
                "agent": AGENT,
                "entrypoint": "delegate",
                "model": "MODEL_TOKEN",
                "outcome": "rate_limited",
            }
        ).encode("ascii")
        return payload.replace(b"MODEL_TOKEN", b"bad-\xff") + b"\n"
    raise AssertionError(kind)


CORRUPT_KINDS = pytest.mark.parametrize(
    "corrupt_kind",
    ["invalid-utf8", "invalid-utf8-in-string", "invalid-json", "json-non-object"],
)


@pytest.fixture
def usage_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    usage_mod._reset_rate_limit_cache_for_tests()
    monkeypatch.delenv("LU_BYPASS_RATE_LIMIT", raising=False)
    monkeypatch.setattr(usage_mod, "_usage_dir", lambda: tmp_path)
    yield tmp_path
    usage_mod._reset_rate_limit_cache_for_tests()


def _usage_file(usage_dir: Path, now: float) -> Path:
    day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
    return usage_dir / f"usage_{AGENT}-delegate_{day}.jsonl"


def _new_unreadable() -> dict[str, int]:
    return {"files": 0, "lines": 0, "records": 0}


@CORRUPT_KINDS
def test_corrupt_line_is_unreadable_and_valid_rows_still_block(usage_dir: Path, corrupt_kind: str) -> None:
    """One corrupt line is counted and skipped; the two valid rate-limited
    rows around it still block headroom (>= _MIN_EVENTS_TO_BLOCK, most recent
    inside the recency threshold)."""
    now = time.time()
    path = _usage_file(usage_dir, now)
    path.write_bytes(
        _record_line(now - 30, outcome="rate_limited")
        + _corrupt_line(corrupt_kind)
        + _record_line(now - 20, outcome="rate_limited")
        + _record_line(now - 10, outcome="ok")
    )

    unreadable = _new_unreadable()
    ok, reason = usage_mod.has_headroom(AGENT, MODEL, unreadable=unreadable)

    assert ok is False
    assert reason
    assert unreadable == {"files": 0, "lines": 1, "records": 0}


@CORRUPT_KINDS
def test_corrupt_line_is_not_a_rate_limit_event(usage_dir: Path, corrupt_kind: str) -> None:
    """A corrupt line never counts as an event: one valid rate-limited row
    plus one corrupt line stays below _MIN_EVENTS_TO_BLOCK and keeps headroom."""
    now = time.time()
    path = _usage_file(usage_dir, now)
    path.write_bytes(_record_line(now - 30, outcome="rate_limited") + _corrupt_line(corrupt_kind))

    unreadable = _new_unreadable()
    ok, reason = usage_mod.has_headroom(AGENT, MODEL, unreadable=unreadable)

    assert ok is True
    assert reason == ""
    assert unreadable == {"files": 0, "lines": 1, "records": 0}


def test_truncated_invalid_last_line_is_unreadable_and_not_an_event(usage_dir: Path) -> None:
    """A truncated last line that is not valid JSON is one unreadable line and
    contributes no rate-limit event, so a single valid event cannot block."""
    now = time.time()
    path = _usage_file(usage_dir, now)
    truncated = (
        b'{"ts": "'
        + _stamp(now - 20).encode("ascii")
        + b'", "model": "'
        + MODEL.encode("ascii")
        + b'", "outcome": "rate_lim'
    )
    path.write_bytes(_record_line(now - 30, outcome="rate_limited") + truncated)

    unreadable = _new_unreadable()
    ok, reason = usage_mod.has_headroom(AGENT, MODEL, unreadable=unreadable)

    assert ok is True
    assert reason == ""
    assert unreadable == {"files": 0, "lines": 1, "records": 0}


def test_truncated_valid_last_line_is_counted(usage_dir: Path) -> None:
    """A truncated last line that is still a complete valid JSON object counts
    as a row and leaves the unreadable counters untouched."""
    now = time.time()
    path = _usage_file(usage_dir, now)
    truncated_valid = _record_line(now - 20, outcome="rate_limited").rstrip(b"\n")
    path.write_bytes(_record_line(now - 30, outcome="rate_limited") + truncated_valid)

    unreadable = _new_unreadable()
    ok, reason = usage_mod.has_headroom(AGENT, MODEL, unreadable=unreadable)

    assert ok is False
    assert reason
    assert unreadable == {"files": 0, "lines": 0, "records": 0}


def test_file_of_only_corrupt_lines_leaves_headroom_clear(usage_dir: Path) -> None:
    """Every corrupt line is counted; none raises; no events are found."""
    now = time.time()
    path = _usage_file(usage_dir, now)
    path.write_bytes(
        b"".join(
            _corrupt_line(kind)
            for kind in ("invalid-utf8", "invalid-utf8-in-string", "invalid-json", "json-non-object")
        )
    )

    unreadable = _new_unreadable()
    ok, reason = usage_mod.has_headroom(AGENT, MODEL, unreadable=unreadable)

    assert ok is True
    assert reason == ""
    assert unreadable == {"files": 0, "lines": 4, "records": 0}


def test_headroom_without_unreadable_counter_does_not_raise(usage_dir: Path) -> None:
    """The default call shape keeps working on a corrupt file: no exception,
    and the (bool, str) return contract is unchanged."""
    now = time.time()
    path = _usage_file(usage_dir, now)
    path.write_bytes(_record_line(now - 30, outcome="rate_limited") + _corrupt_line("invalid-utf8"))

    result = usage_mod.has_headroom(AGENT, MODEL)

    assert isinstance(result, tuple) and len(result) == 2
    assert result == (True, "")
