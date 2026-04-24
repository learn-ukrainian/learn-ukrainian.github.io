"""Tests for per-tool timing telemetry endpoints."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

import scripts.api.telemetry_router as telemetry_router
from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _use_temp_db(tmp_path: Path, monkeypatch) -> Path:
    db_path = tmp_path / "tool_timings.db"
    monkeypatch.setattr(telemetry_router, "_DB_PATH", db_path)
    return db_path


def _insert_timing(
    db_path: Path,
    *,
    ts: datetime,
    tool_name: str,
    duration_ms: int,
    failed: bool = False,
) -> None:
    telemetry_router._init_db(db_path)
    with closing(sqlite3.connect(str(db_path))) as conn:
        conn.execute(
            """
            INSERT INTO tool_timings (ts, tool_name, duration_ms, failed)
            VALUES (?, ?, ?, ?)
            """,
            (_iso(ts), tool_name, duration_ms, 1 if failed else 0),
        )
        conn.commit()


def test_ingest_valid_payload(tmp_path, monkeypatch):
    db_path = _use_temp_db(tmp_path, monkeypatch)

    response = client.post(
        "/api/telemetry/tool-timings",
        json={
            "ts": "2026-04-25T00:12:34.567Z",
            "tool_name": "Bash",
            "duration_ms": 142,
            "tool_use_id": "toolu_test",
            "session_id": "sess-1",
            "failed": False,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    with closing(sqlite3.connect(str(db_path))) as conn:
        row = conn.execute("SELECT tool_name, duration_ms, failed FROM tool_timings").fetchone()
    assert row == ("Bash", 142, 0)


def test_ingest_rejects_negative_duration(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)

    response = client.post(
        "/api/telemetry/tool-timings",
        json={"ts": "2026-04-25T00:12:34.567Z", "tool_name": "Bash", "duration_ms": -1},
    )

    assert response.status_code == 422


def test_ingest_rejects_missing_tool_name(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)

    response = client.post(
        "/api/telemetry/tool-timings",
        json={"ts": "2026-04-25T00:12:34.567Z", "duration_ms": 142},
    )

    assert response.status_code == 422


def test_aggregate_empty_window(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)

    response = client.get("/api/telemetry/tool-timings?window=1h")

    assert response.status_code == 200
    assert response.json() == []


def test_aggregate_computes_percentiles(tmp_path, monkeypatch):
    db_path = _use_temp_db(tmp_path, monkeypatch)
    now = datetime.now(UTC)
    for duration in range(1, 101):
        _insert_timing(db_path, ts=now - timedelta(minutes=1), tool_name="Bash", duration_ms=duration)
    _insert_timing(db_path, ts=now - timedelta(minutes=1), tool_name="Bash", duration_ms=1000, failed=True)

    response = client.get("/api/telemetry/tool-timings?window=1h")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    row = payload[0]
    assert row["tool_name"] == "Bash"
    assert row["count"] == 101
    assert row["p50_ms"] == 51
    assert row["p95_ms"] == 96
    assert row["p99_ms"] == 100
    assert row["mean_ms"] == 60
    assert row["failure_count"] == 1


def test_aggregate_window_filter(tmp_path, monkeypatch):
    db_path = _use_temp_db(tmp_path, monkeypatch)
    now = datetime.now(UTC)
    _insert_timing(db_path, ts=now - timedelta(minutes=2), tool_name="Read", duration_ms=10)
    _insert_timing(db_path, ts=now - timedelta(minutes=10), tool_name="Read", duration_ms=100)

    response = client.get("/api/telemetry/tool-timings?window=5m")

    assert response.status_code == 200
    assert response.json() == [
        {
            "tool_name": "Read",
            "count": 1,
            "p50_ms": 10,
            "p95_ms": 10,
            "p99_ms": 10,
            "mean_ms": 10,
            "failure_count": 0,
        }
    ]


def test_aggregate_tool_filter(tmp_path, monkeypatch):
    db_path = _use_temp_db(tmp_path, monkeypatch)
    now = datetime.now(UTC)
    _insert_timing(db_path, ts=now - timedelta(minutes=1), tool_name="Bash", duration_ms=20)
    _insert_timing(db_path, ts=now - timedelta(minutes=1), tool_name="Read", duration_ms=5)

    response = client.get("/api/telemetry/tool-timings?window=1h&tool=Bash")

    assert response.status_code == 200
    assert response.json() == [
        {
            "tool_name": "Bash",
            "count": 1,
            "p50_ms": 20,
            "p95_ms": 20,
            "p99_ms": 20,
            "mean_ms": 20,
            "failure_count": 0,
        }
    ]
