"""GET /api/orient?sections=runtime surfaces usage-read corruption counts (#9924).

The orient runtime collector reads the usage log four times: the agent
inventory's last-used-model scan, the day usage summary, today's outcome
counts, and one headroom scan per rostered agent. A corrupt line must surface
once per read on the section's aggregated ``unreadable`` counter in the #9868
evidence shape (``{"files", "lines", "records", "total"}``), while the valid
rows around it keep counting toward the section totals. A clean log reports
the all-zero shape instead of omitting the field.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent_runtime import usage as usage_mod
from scripts.api import main as api_main
from scripts.api.monitor_context import fixture_context


def _record(agent: str, outcome: str) -> dict:
    return {
        "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
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

# One corrupt line is counted once per usage read the collector makes: agent
# inventory, usage summary, recent outcomes, and the codex headroom scan.
READS_WITH_HEADROOM = 4
# Without a rostered agent there is no headroom scan.
READS_WITHOUT_HEADROOM = 3


def _unreadable(lines: int) -> dict[str, int]:
    return {"files": 0, "lines": lines, "records": 0, "total": lines}


def _usage_dir(root: Path) -> Path:
    usage_dir = root / "batch_state" / "api_usage"
    usage_dir.mkdir(parents=True, exist_ok=True)
    return usage_dir


def _today_file(usage_dir: Path) -> Path:
    return usage_dir / f"usage_codex-delegate_{datetime.now(UTC):%Y-%m-%d}.jsonl"


def _stub_codex_adapter(root: Path) -> None:
    """Give the fixture context one rostered agent so the headroom scan runs.

    A fixture context enumerates ``<root>/runtime_adapters_fixture_stub``
    instead of the installed adapters; the filename drives an import of the
    real ``agent_runtime.adapters.codex`` module, so the roster gains the
    real codex adapter with its registry default model.
    """
    stub_dir = root / "runtime_adapters_fixture_stub"
    stub_dir.mkdir(parents=True, exist_ok=True)
    (stub_dir / "codex.py").write_text('"""Fixture stub: imports the real codex adapter."""\n', encoding="utf-8")


def _make_client(root: Path, monkeypatch: pytest.MonkeyPatch, *, stub_adapter: bool) -> TestClient:
    """Build a fixture-context app whose four usage reads all hit one log dir.

    The router-side reads resolve ``ctx.roots.batch_state_dir / "api_usage"``;
    the headroom scan resolves ``agent_runtime.usage._usage_dir()``. Both are
    pinned to the same disposable directory, as they coincide in production.
    """
    usage_mod._reset_rate_limit_cache_for_tests()
    monkeypatch.delenv("LU_BYPASS_RATE_LIMIT", raising=False)
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC", "0")
    monkeypatch.setattr(usage_mod, "_usage_dir", lambda: _usage_dir(root))
    if stub_adapter:
        _stub_codex_adapter(root)
    return TestClient(api_main.create_app(fixture_context(root)))


def _get_runtime(client: TestClient) -> dict:
    response = client.get("/api/orient?sections=runtime&fresh=true")
    assert response.status_code == 200
    runtime = response.json()["runtime"]
    assert isinstance(runtime, dict)
    assert "error" not in runtime
    return runtime


@CORRUPT_KINDS
def test_orient_runtime_aggregates_unreadable_across_usage_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corrupt_kind: str
) -> None:
    """Each corrupt line surfaces once per usage read; valid rows still count."""
    root = tmp_path.resolve()
    _today_file(_usage_dir(root)).write_bytes(
        _line(_record("codex", "ok")) + _corrupt_line(corrupt_kind) + _line(_record("codex", "error"))
    )
    client = _make_client(root, monkeypatch, stub_adapter=True)

    runtime = _get_runtime(client)

    assert runtime["unreadable"] == _unreadable(READS_WITH_HEADROOM)
    # Valid totals are unchanged by the skipped line.
    assert runtime["by_agent"]["codex"] == {
        "total": 2,
        "total_duration_s": 0.0,
        "ok": 1,
        "error": 1,
        "timeout": 0,
        "rate_limited": 0,
    }
    assert runtime["recent_outcomes"] == {"ok": 1, "error": 1, "timeout": 0, "rate_limited": 0}
    # The corrupt line is not a rate-limit event, so headroom stays clear.
    assert runtime["headroom"] == {"codex": True}


def test_orient_runtime_counts_malformed_last_line(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A truncated last line that is not valid JSON is one unreadable line per read."""
    root = tmp_path.resolve()
    _today_file(_usage_dir(root)).write_bytes(
        _line(_record("codex", "ok")) + b'{"ts": "2026-10-08T00:00:00Z", "outcome": "rate_lim'
    )
    client = _make_client(root, monkeypatch, stub_adapter=True)

    runtime = _get_runtime(client)

    assert runtime["unreadable"] == _unreadable(READS_WITH_HEADROOM)
    assert runtime["by_agent"]["codex"]["total"] == 1
    assert runtime["recent_outcomes"] == {"ok": 1, "error": 0, "timeout": 0, "rate_limited": 0}
    assert runtime["headroom"] == {"codex": True}


def test_orient_runtime_reports_zero_unreadable_for_clean_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A clean log reports the all-zero shape; the field is never omitted."""
    root = tmp_path.resolve()
    _today_file(_usage_dir(root)).write_bytes(_line(_record("codex", "ok")) + _line(_record("codex", "error")))
    client = _make_client(root, monkeypatch, stub_adapter=True)

    runtime = _get_runtime(client)

    assert runtime["unreadable"] == _unreadable(0)
    assert runtime["by_agent"]["codex"]["total"] == 2
    assert runtime["recent_outcomes"] == {"ok": 1, "error": 1, "timeout": 0, "rate_limited": 0}
    assert runtime["headroom"] == {"codex": True}


def test_orient_runtime_aggregation_covers_exactly_the_reads_made(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no rostered agent there is no headroom scan: the same corrupt line
    is counted once per remaining read, proving the headroom read contributes
    to the aggregate instead of the count being a fixed constant."""
    root = tmp_path.resolve()
    _today_file(_usage_dir(root)).write_bytes(_line(_record("codex", "ok")) + _corrupt_line("invalid-json"))
    client = _make_client(root, monkeypatch, stub_adapter=False)

    runtime = _get_runtime(client)

    assert runtime["unreadable"] == _unreadable(READS_WITHOUT_HEADROOM)
    assert runtime["headroom"] == {}
    assert runtime["by_agent"]["codex"]["total"] == 1


@pytest.fixture(autouse=True)
def _reset_rate_limit_cache():
    yield
    usage_mod._reset_rate_limit_cache_for_tests()
