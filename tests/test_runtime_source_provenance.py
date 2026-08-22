"""Regression tests for runtime source provenance survival (#7076).

When initiator identifiers fail the runtime attribution ID regex or are unknown,
the record's recorded source provenance (e.g. 'explicit' or 'session_env')
must not be forcibly collapsed to 'unknown'.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import scripts.api.runtime_router as runtime_router
from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _write_usage_file(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def test_explicit_provenance_preserved_when_initiator_fails_regex(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Afternoon-style records with explicit attribution_source stay explicit even if initiator fails regex."""
    usage_dir = tmp_path / "api_usage"
    now = datetime.now(UTC)
    monkeypatch.setattr(runtime_router, "USAGE_DIR", usage_dir)

    _write_usage_file(
        usage_dir / f"usage_codex-delegate_{now:%Y-%m-%d}.jsonl",
        [
            {
                "ts": _iso(now - timedelta(minutes=5)),
                "agent": "codex",
                "entrypoint": "delegate",
                "initiator": "invalid@initiator#1!",
                "attribution_source": "explicit",
                "attribution_task_id": "cf-pr-7072-r2",
                "model": "gpt-5.6-terra",
                "outcome": "ok",
                "duration_s": 42.0,
            }
        ],
    )

    records = runtime_router.recent_runtime_records(limit=10)["records"]
    assert len(records) == 1
    record = records[0]
    assert record["agent"] == "codex"
    assert record["via"] == "delegate"
    assert record["source"] == "unknown"  # sanitized because of invalid ID regex
    assert record["source_provenance"] == "explicit"  # preserved despite initiator being unknown
    assert record["source_task_id"] == "cf-pr-7072-r2"


def test_explicit_provenance_preserved_when_initiator_is_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When initiator is literal 'unknown' or None, explicit source_provenance is preserved."""
    usage_dir = tmp_path / "api_usage"
    now = datetime.now(UTC)
    monkeypatch.setattr(runtime_router, "USAGE_DIR", usage_dir)

    _write_usage_file(
        usage_dir / f"usage_claude-delegate_{now:%Y-%m-%d}.jsonl",
        [
            {
                "ts": _iso(now - timedelta(minutes=3)),
                "agent": "claude",
                "entrypoint": "delegate",
                "initiator": "unknown",
                "attribution_source": "explicit",
                "attribution_task_id": "cf-pr-7072-r3",
                "model": "claude-sonnet-5",
                "outcome": "ok",
                "duration_s": 15.5,
            },
            {
                "ts": _iso(now - timedelta(minutes=2)),
                "agent": "gemini",
                "entrypoint": "delegate",
                "initiator": None,
                "attribution_source": "session_env",
                "attribution_task_id": "cf-pr-7072-r4",
                "model": "gemini-3.1-pro-preview",
                "outcome": "ok",
                "duration_s": 8.2,
            },
        ],
    )

    records = runtime_router.recent_runtime_records(limit=10)["records"]
    assert len(records) == 2
    # Records sorted by ts desc: r4 then r3
    r4 = records[0]
    assert r4["agent"] == "gemini"
    assert r4["source"] == "unknown"
    assert r4["source_provenance"] == "session_env"
    assert r4["source_task_id"] == "cf-pr-7072-r4"

    r3 = records[1]
    assert r3["agent"] == "claude"
    assert r3["source"] == "unknown"
    assert r3["source_provenance"] == "explicit"
    assert r3["source_task_id"] == "cf-pr-7072-r3"


def test_morning_and_afternoon_dispatches_provenance_lifecycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Morning job-host dispatches and later afternoon rounds both preserve caller provenance."""
    usage_dir = tmp_path / "api_usage"
    now = datetime.now(UTC)
    monkeypatch.setattr(runtime_router, "USAGE_DIR", usage_dir)

    _write_usage_file(
        usage_dir / f"usage_codex-delegate_{now:%Y-%m-%d}.jsonl",
        [
            # Morning round: well-formed initiator
            {
                "ts": _iso(now - timedelta(hours=6)),
                "agent": "codex",
                "entrypoint": "delegate",
                "initiator": "cursor/job-host-dispatch",
                "attribution_source": "explicit",
                "attribution_task_id": "cf-pr-7070",
                "model": "gpt-5.6-terra",
                "outcome": "ok",
                "duration_s": 120.0,
            },
            # Afternoon round: malformed initiator string
            {
                "ts": _iso(now - timedelta(hours=1)),
                "agent": "codex",
                "entrypoint": "delegate",
                "initiator": "invalid initiator with spaces",
                "attribution_source": "explicit",
                "attribution_task_id": "cf-pr-7072-r5",
                "model": "gpt-5.6-terra",
                "outcome": "ok",
                "duration_s": 95.0,
            },
        ],
    )

    response = client.get("/api/runtime/recent?limit=10")
    assert response.status_code == 200
    records = response.json()["records"]
    assert len(records) == 2

    afternoon = records[0]
    assert afternoon["source"] == "unknown"
    assert afternoon["source_provenance"] == "explicit"
    assert afternoon["source_task_id"] == "cf-pr-7072-r5"

    morning = records[1]
    assert morning["source"] == "cursor/job-host-dispatch"
    assert morning["source_provenance"] == "explicit"
    assert morning["source_task_id"] == "cf-pr-7070"


def test_unrecognized_attribution_source_falls_back_to_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An invalid/unrecognized attribution_source falls back to 'unknown'."""
    usage_dir = tmp_path / "api_usage"
    now = datetime.now(UTC)
    monkeypatch.setattr(runtime_router, "USAGE_DIR", usage_dir)

    _write_usage_file(
        usage_dir / f"usage_codex-delegate_{now:%Y-%m-%d}.jsonl",
        [
            {
                "ts": _iso(now),
                "agent": "codex",
                "entrypoint": "delegate",
                "initiator": "codex",
                "attribution_source": "arbitrary_custom_source",
                "model": "gpt-5.6-terra",
                "outcome": "ok",
            }
        ],
    )

    records = runtime_router.recent_runtime_records(limit=1)["records"]
    assert len(records) == 1
    assert records[0]["source"] == "codex"
    assert records[0]["source_provenance"] == "unknown"
