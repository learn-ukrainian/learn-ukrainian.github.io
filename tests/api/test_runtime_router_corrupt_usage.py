"""runtime_router._iter_usage_records shares the strict usage line reader (#9924).

A line that is not strict UTF-8, not JSON, or not a JSON object — including a
truncated last line — is skipped and counted on the caller's ``unreadable``
counter instead of raising or being silently dropped. Valid rows from the
same file and from later files still count, and runtime API totals over the
valid rows are unchanged.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.api import runtime_router


def _record(agent: str, outcome: str, *, day: datetime | None = None) -> dict:
    moment = day or datetime.now(UTC)
    return {
        "ts": moment.isoformat().replace("+00:00", "Z"),
        "agent": agent,
        "entrypoint": "delegate",
        "model": "gpt-6.1-sol",
        "outcome": outcome,
    }


def _line(record: dict) -> bytes:
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
        payload = json.dumps(_record("codex", "ok")).encode("ascii")
        return payload.replace(b'"codex"', b'"codex-\xff"') + b"\n"
    raise AssertionError(kind)


CORRUPT_KINDS = pytest.mark.parametrize(
    "corrupt_kind",
    ["invalid-utf8", "invalid-utf8-in-string", "invalid-json", "json-non-object"],
)


def _new_unreadable() -> dict[str, int]:
    return {"files": 0, "lines": 0, "records": 0}


@CORRUPT_KINDS
def test_corrupt_line_is_unreadable_and_valid_rows_still_count(tmp_path: Path, corrupt_kind: str) -> None:
    """One corrupt line is counted and skipped; the valid rows around it in
    the same file are still returned."""
    first = _record("codex", "ok")
    second = _record("claude", "error")
    path = tmp_path / "usage_mixed.jsonl"
    path.write_bytes(_line(first) + _corrupt_line(corrupt_kind) + _line(second))

    unreadable = _new_unreadable()
    records = runtime_router._iter_usage_records([path], unreadable)

    assert records == [first, second]
    assert unreadable == {"files": 0, "lines": 1, "records": 0}


def test_truncated_invalid_last_line_is_unreadable(tmp_path: Path) -> None:
    """A truncated last line that is not valid JSON is one unreadable line;
    the valid rows before it still count."""
    first = _record("codex", "ok")
    path = tmp_path / "usage_truncated.jsonl"
    path.write_bytes(_line(first) + b'{"ts": "2026-10-08T00:00:00Z", "outcome": "rate_lim')

    unreadable = _new_unreadable()
    records = runtime_router._iter_usage_records([path], unreadable)

    assert records == [first]
    assert unreadable == {"files": 0, "lines": 1, "records": 0}


def test_truncated_valid_last_line_is_counted(tmp_path: Path) -> None:
    """A truncated last line that is still a complete valid JSON object counts
    as a row and leaves the unreadable counters untouched."""
    first = _record("codex", "ok")
    last = _record("claude", "timeout")
    path = tmp_path / "usage_truncated_valid.jsonl"
    path.write_bytes(_line(first) + _line(last).rstrip(b"\n"))

    unreadable = _new_unreadable()
    records = runtime_router._iter_usage_records([path], unreadable)

    assert records == [first, last]
    assert unreadable == {"files": 0, "lines": 0, "records": 0}


@CORRUPT_KINDS
def test_corrupt_first_file_does_not_drop_later_files(tmp_path: Path, corrupt_kind: str) -> None:
    """A corrupt line in one file is local to that file; rows in later files
    still count."""
    early = _record("codex", "ok")
    late_a = _record("claude", "error")
    late_b = _record("grok", "ok")
    first_path = tmp_path / "usage_first.jsonl"
    second_path = tmp_path / "usage_second.jsonl"
    first_path.write_bytes(_line(early) + _corrupt_line(corrupt_kind))
    second_path.write_bytes(_line(late_a) + _line(late_b))

    unreadable = _new_unreadable()
    records = runtime_router._iter_usage_records([first_path, second_path], unreadable)

    assert records == [early, late_a, late_b]
    assert unreadable == {"files": 0, "lines": 1, "records": 0}


def test_reader_without_unreadable_counter_does_not_raise(tmp_path: Path) -> None:
    """The default call shape keeps working on a corrupt file: no exception,
    and valid rows are still returned."""
    first = _record("codex", "ok")
    path = tmp_path / "usage_default.jsonl"
    path.write_bytes(_line(first) + _corrupt_line("invalid-json"))

    records = runtime_router._iter_usage_records([path])

    assert records == [first]


def test_summarize_runtime_usage_totals_over_valid_rows(tmp_path: Path) -> None:
    """The public runtime usage summary never raises on corrupt lines and its
    totals count exactly the valid rows."""
    today = datetime.now(UTC)
    path = tmp_path / f"usage_codex-delegate_{today:%Y-%m-%d}.jsonl"
    path.write_bytes(
        _line(_record("codex", "ok"))
        + _corrupt_line("invalid-utf8")
        + _corrupt_line("json-non-object")
        + _line(_record("codex", "rate_limited"))
        + b'{"ts": "2026-10-08T00:00:00Z", "outcome": "truncated'
    )

    summary = runtime_router.summarize_runtime_usage(days=7, usage_dir=tmp_path)

    assert summary["records_total"] == 2
    assert summary["by_agent"] == {
        "codex": {"total": 2, "total_duration_s": 0.0, "ok": 1, "error": 0, "timeout": 0, "rate_limited": 1}
    }
    assert summary["by_entrypoint"] == {
        "delegate": {"total": 2, "total_duration_s": 0.0, "ok": 1, "error": 0, "timeout": 0, "rate_limited": 1}
    }
