"""Tests for build events monitor API endpoints."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

import scripts.api.build_events_router as build_events_router
from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _write_meta(root: Path, level: str, slug: str, filename: str, timestamp: datetime, phase: str = "write") -> None:
    dispatch_dir = root / level / "orchestration" / slug / "dispatch"
    dispatch_dir.mkdir(parents=True, exist_ok=True)
    (dispatch_dir / filename).write_text(
        json.dumps(
            {
                "timestamp": _iso(timestamp),
                "phase": phase,
                "agent": "gemini (gemini-3.1-pro-preview)",
                "ok": True,
                "returncode": 0,
                "prompt_chars": 100,
                "response_chars": 200,
                "duration_s": 12.5,
            }
        ),
        encoding="utf-8",
    )


def _write_state(root: Path, level: str, slug: str, publish_status: str = "pending", current_phase: str = "write") -> None:
    state_path = root / level / "orchestration" / slug / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "mode": "v6",
                "phases": {
                    current_phase: {"status": "pending"},
                    "publish": {"status": publish_status},
                },
            }
        ),
        encoding="utf-8",
    )


def test_recent_events_newest_first(tmp_path, monkeypatch):
    monkeypatch.setattr(build_events_router, "CURRICULUM_ROOT", tmp_path)
    now = datetime.now(UTC)
    _write_meta(tmp_path, "a2", "a2-bridge", "01-write-meta.json", now - timedelta(minutes=5))
    _write_meta(tmp_path, "a2", "a2-bridge", "02-review-meta.json", now - timedelta(minutes=1), phase="review")

    response = client.get("/api/build/events/recent")

    assert response.status_code == 200
    events = response.json()["events"]
    assert events[0]["phase"] == "review"
    assert events[1]["phase"] == "write"


def test_recent_events_level_filter(tmp_path, monkeypatch):
    monkeypatch.setattr(build_events_router, "CURRICULUM_ROOT", tmp_path)
    now = datetime.now(UTC)
    _write_meta(tmp_path, "a1", "one", "01-write-meta.json", now - timedelta(minutes=2))
    _write_meta(tmp_path, "a2", "two", "01-write-meta.json", now - timedelta(minutes=1))

    response = client.get("/api/build/events/recent?level=a2")

    assert response.status_code == 200
    events = response.json()["events"]
    assert len(events) == 1
    assert events[0]["level"] == "a2"
    assert events[0]["slug"] == "two"


def test_active_events_respects_10_min_window(tmp_path, monkeypatch):
    monkeypatch.setattr(build_events_router, "CURRICULUM_ROOT", tmp_path)
    now = datetime.now(UTC)
    _write_meta(tmp_path, "a2", "fresh", "01-write-meta.json", now - timedelta(minutes=3))
    _write_state(tmp_path, "a2", "fresh", publish_status="pending", current_phase="write")
    _write_meta(tmp_path, "a2", "stale", "01-write-meta.json", now - timedelta(minutes=20))
    _write_state(tmp_path, "a2", "stale", publish_status="pending", current_phase="write")
    _write_meta(tmp_path, "a2", "done", "01-publish-meta.json", now - timedelta(minutes=2), phase="publish")
    _write_state(tmp_path, "a2", "done", publish_status="complete", current_phase="publish")

    response = client.get("/api/build/events/active")

    assert response.status_code == 200
    active = response.json()["active"]
    assert len(active) == 1
    assert active[0]["slug"] == "fresh"
    assert active[0]["current_phase"] == "write"


def test_scan_hard_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(build_events_router, "CURRICULUM_ROOT", tmp_path)
    monkeypatch.setattr(build_events_router, "BUILD_EVENTS_SCAN_CAP", 2)
    now = datetime.now(UTC)
    _write_meta(tmp_path, "a2", "one", "01-write-meta.json", now - timedelta(minutes=3))
    _write_meta(tmp_path, "a2", "two", "01-write-meta.json", now - timedelta(minutes=2))
    _write_meta(tmp_path, "a2", "three", "01-write-meta.json", now - timedelta(minutes=1))

    response = client.get("/api/build/events/recent?limit=10")

    assert response.status_code == 200
    assert len(response.json()["events"]) == 2
