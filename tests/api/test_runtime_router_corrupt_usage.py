"""runtime_router._iter_usage_records shares the strict usage line reader (#9924).

A line that is not strict UTF-8, not JSON, or not a JSON object — including a
truncated last line — is skipped and counted on the caller's ``unreadable``
counter instead of raising or being silently dropped. Valid rows from the
same file and from later files still count, and runtime API totals over the
valid rows are unchanged. Every production caller surfaces the counts in the
#9868 evidence shape (``{"files", "lines", "records", "total"}``): the usage,
recent, acpx, and agents responses read them off the returned list's
``unreadable`` attribute, and the headroom response reads them off the
``has_headroom`` counter keyword.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent_runtime import usage as usage_mod
from scripts.api import runtime_router
from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)


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
    assert records.unreadable == {"files": 0, "lines": 1, "records": 0, "total": 1}


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
    assert summary["unreadable"] == {"files": 0, "lines": 3, "records": 0, "total": 3}


# --- Runtime API responses surface the unreadable counts (#9924) ---

ONE_UNREADABLE_LINE = {"files": 0, "lines": 1, "records": 0, "total": 1}
ZERO_UNREADABLE = {"files": 0, "lines": 0, "records": 0, "total": 0}


def _ctx_with_batch_state_dir(batch_state_dir: Path):
    """MonitorContext pinned to a disposable ``batch_state`` root.

    ``runtime_router`` resolves its usage-log directory from
    ``ctx.roots.batch_state_dir / "api_usage"``, so API tests redirect it by
    swapping ``app.state.ctx`` for the duration of the test — the pattern
    ``tests/test_runtime_api.py`` established.
    """
    return app.state.ctx.with_roots(batch_state_dir=Path(batch_state_dir))


def _usage_api_dir(batch_state_dir: Path) -> Path:
    usage_dir = Path(batch_state_dir) / "api_usage"
    usage_dir.mkdir(parents=True)
    return usage_dir


def _today_file(usage_dir: Path) -> Path:
    return usage_dir / f"usage_codex-delegate_{datetime.now(UTC):%Y-%m-%d}.jsonl"


@pytest.fixture
def headroom_usage_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Pin ``agent_runtime.usage._usage_dir`` to a disposable directory.

    ``/api/runtime/headroom`` calls ``has_headroom``, which resolves its scan
    directory from that module's ``_usage_dir`` global — the pattern
    ``tests/agent_runtime/test_usage_headroom_corrupt.py`` established.
    """
    usage_mod._reset_rate_limit_cache_for_tests()
    monkeypatch.delenv("LU_BYPASS_RATE_LIMIT", raising=False)
    monkeypatch.setattr(usage_mod, "_usage_dir", lambda: tmp_path)
    yield tmp_path
    usage_mod._reset_rate_limit_cache_for_tests()


@CORRUPT_KINDS
def test_usage_api_reports_unreadable_and_counts_valid_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corrupt_kind: str
) -> None:
    """GET /api/runtime/usage answers 200 over a corrupt file: the valid rows
    are counted and the bad lines surface on ``unreadable``."""
    usage_dir = _usage_api_dir(tmp_path)
    _today_file(usage_dir).write_bytes(
        _line(_record("codex", "ok")) + _corrupt_line(corrupt_kind) + _line(_record("codex", "error"))
    )
    monkeypatch.setattr(app.state, "ctx", _ctx_with_batch_state_dir(tmp_path))

    response = client.get("/api/runtime/usage?days=1")

    assert response.status_code == 200
    data = response.json()
    assert data["records_total"] == 2
    assert data["by_agent"]["codex"]["total"] == 2
    assert data["unreadable"] == ONE_UNREADABLE_LINE


def test_usage_api_counts_malformed_last_line(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A truncated last line that is not valid JSON is one unreadable line."""
    usage_dir = _usage_api_dir(tmp_path)
    _today_file(usage_dir).write_bytes(
        _line(_record("codex", "ok")) + b'{"ts": "2026-10-08T00:00:00Z", "outcome": "rate_lim'
    )
    monkeypatch.setattr(app.state, "ctx", _ctx_with_batch_state_dir(tmp_path))

    response = client.get("/api/runtime/usage?days=1")

    assert response.status_code == 200
    data = response.json()
    assert data["records_total"] == 1
    assert data["unreadable"] == ONE_UNREADABLE_LINE


def test_usage_api_reports_zero_unreadable_for_clean_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A clean file reports an all-zero ``unreadable`` summary."""
    usage_dir = _usage_api_dir(tmp_path)
    _today_file(usage_dir).write_bytes(_line(_record("codex", "ok")) + _line(_record("codex", "error")))
    monkeypatch.setattr(app.state, "ctx", _ctx_with_batch_state_dir(tmp_path))

    response = client.get("/api/runtime/usage?days=1")

    assert response.status_code == 200
    data = response.json()
    assert data["records_total"] == 2
    assert data["unreadable"] == ZERO_UNREADABLE


@CORRUPT_KINDS
def test_headroom_api_reports_unreadable_and_keeps_clear_decision(headroom_usage_dir: Path, corrupt_kind: str) -> None:
    """GET /api/runtime/headroom answers 200 over a corrupt line: it never
    counts as a rate-limit event and surfaces on ``unreadable``."""
    _today_file(headroom_usage_dir).write_bytes(_line(_record("codex", "ok")) + _corrupt_line(corrupt_kind))

    response = client.get("/api/runtime/headroom?agent=codex&model=gpt-6.1-sol")

    assert response.status_code == 200
    data = response.json()
    assert data["has_headroom"] is True
    assert data["reason"] == ""
    assert data["unreadable"] == ONE_UNREADABLE_LINE


def test_headroom_api_blocked_decision_still_reports_unreadable(headroom_usage_dir: Path) -> None:
    """A blocked headroom decision still surfaces the corrupt line it skipped."""
    _today_file(headroom_usage_dir).write_bytes(
        _line(_record("codex", "rate_limited"))
        + _corrupt_line("invalid-json")
        + _line(_record("codex", "rate_limited"))
    )

    response = client.get("/api/runtime/headroom?agent=codex&model=gpt-6.1-sol")

    assert response.status_code == 200
    data = response.json()
    assert data["has_headroom"] is False
    assert data["reason"]
    assert data["unreadable"] == ONE_UNREADABLE_LINE


def test_headroom_api_reports_zero_unreadable_for_clean_files(headroom_usage_dir: Path) -> None:
    """A clean lane file reports an all-zero ``unreadable`` summary."""
    _today_file(headroom_usage_dir).write_bytes(_line(_record("codex", "ok")))

    response = client.get("/api/runtime/headroom?agent=codex&model=gpt-6.1-sol")

    assert response.status_code == 200
    data = response.json()
    assert data["has_headroom"] is True
    assert data["unreadable"] == ZERO_UNREADABLE


def test_headroom_api_counts_malformed_last_line(headroom_usage_dir: Path) -> None:
    """A truncated last line that is not valid JSON is one unreadable line and
    no rate-limit event, so headroom stays clear."""
    _today_file(headroom_usage_dir).write_bytes(
        _line(_record("codex", "ok")) + b'{"ts": "2026-10-08T00:00:00Z", "outcome": "rate_lim'
    )

    response = client.get("/api/runtime/headroom?agent=codex&model=gpt-6.1-sol")

    assert response.status_code == 200
    data = response.json()
    assert data["has_headroom"] is True
    assert data["unreadable"] == ONE_UNREADABLE_LINE


@CORRUPT_KINDS
def test_recent_api_reports_unreadable_and_counts_valid_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corrupt_kind: str
) -> None:
    """GET /api/runtime/recent answers 200: valid rows are listed and the bad
    lines surface on ``unreadable``."""
    usage_dir = _usage_api_dir(tmp_path)
    _today_file(usage_dir).write_bytes(_line(_record("codex", "ok")) + _corrupt_line(corrupt_kind))
    monkeypatch.setattr(app.state, "ctx", _ctx_with_batch_state_dir(tmp_path))

    response = client.get("/api/runtime/recent?limit=5")

    assert response.status_code == 200
    data = response.json()
    assert len(data["records"]) == 1
    assert data["records"][0]["agent"] == "codex"
    assert data["unreadable"] == ONE_UNREADABLE_LINE


def test_acpx_api_reports_unreadable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/runtime/acpx surfaces the unreadable counts of its evidence read."""
    usage_dir = _usage_api_dir(tmp_path)
    _today_file(usage_dir).write_bytes(_line(_record("codex", "ok")) + _corrupt_line("invalid-json"))
    monkeypatch.setattr(app.state, "ctx", _ctx_with_batch_state_dir(tmp_path))

    response = client.get("/api/runtime/acpx?days=1")

    assert response.status_code == 200
    data = response.json()
    assert data["unreadable"] == ONE_UNREADABLE_LINE


def test_agents_api_reports_unreadable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/runtime/agents surfaces the unreadable counts of its
    last-used-model read."""
    usage_dir = _usage_api_dir(tmp_path)
    _today_file(usage_dir).write_bytes(_line(_record("codex", "ok")) + _corrupt_line("invalid-json"))
    monkeypatch.setattr(app.state, "ctx", _ctx_with_batch_state_dir(tmp_path))

    response = client.get("/api/runtime/agents")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["agents"], list)
    assert data["unreadable"] == ONE_UNREADABLE_LINE
