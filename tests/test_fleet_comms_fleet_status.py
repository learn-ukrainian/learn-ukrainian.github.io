"""Unit tests for compact fleet overview in fleet status (private #670 AC-OVERVIEW).

Covers:
1. no DB -> available: False
2. unleased stream -> unknown: True
3. live lease -> holder present; redaction rejects raw host/path
4. expired lease -> stale: True
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import LeaseHolder
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.fleet_comms.cli import EXIT_OK, fleet_status_payload, main
from scripts.fleet_comms.fleet_overview import build_fleet_overview


def _init_session_db(root: Path) -> Path:
    db_dir = root / ".agent" / "session-streams" / "v1"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "session-streams.sqlite3"
    db = SessionStreamDatabase(db_path)
    conn = db.connect()
    conn.close()
    return db_path


def test_fleet_status_no_db(tmp_path: Path) -> None:
    """Requirement 1: no DB -> available: False."""
    missing_root = tmp_path / "nonexistent_repo"
    overview = build_fleet_overview(repo_root=missing_root)
    assert overview["available"] is False
    assert overview["streams"] == []

    payload = fleet_status_payload({"enabled": True}, repo_root=missing_root)
    assert payload["overview"]["available"] is False
    assert payload["overview"]["streams"] == []


def test_fleet_status_unleased_stream(tmp_path: Path) -> None:
    """Requirement 2: unleased stream -> unknown: True."""
    db_path = _init_session_db(tmp_path)
    db = SessionStreamDatabase(db_path)
    conn = db.connect()
    try:
        conn.execute(
            "INSERT INTO streams(stream_id, kind, epic_number, created_at) "
            "VALUES ('epic:101', 'epic', 101, '2026-09-06T12:00:00Z')"
        )
        conn.commit()
    finally:
        conn.close()

    overview = build_fleet_overview(repo_root=tmp_path)
    assert overview["available"] is True
    assert len(overview["streams"]) == 1

    stream = overview["streams"][0]
    assert stream["stream_id"] == "epic:101"
    assert stream["lease_state"] == "unleased"
    assert stream["unknown"] is True
    assert stream["stale"] is False
    assert stream["holder"] is None
    assert stream["heartbeat_age_seconds"] is None
    assert stream["expires_at"] is None
    assert stream["session_state"] is None


def test_fleet_status_live_lease_and_redaction(tmp_path: Path) -> None:
    """Requirement 3: live lease -> holder present; redaction rejects raw host/path."""
    db_path = _init_session_db(tmp_path)
    store = SessionStreamStore(SessionStreamDatabase(db_path))

    # Holder with raw host IP and path-containing agent
    raw_holder = LeaseHolder(
        agent="var/run/custom-agent",
        harness="valid-harness",
        instance_id="inst-001",
        host_id="192.0.2.1",
        process_id=12345,
    )
    store.open_session(
        stream_id="epic:201",
        holder=raw_holder,
        lineage_id="lineage-201",
        ttl_seconds=3600,
        session_id="session-201",
    )

    # Holder with canonical alias host_id (atlas-runner)
    alias_holder = LeaseHolder(
        agent="alias-agent",
        harness="valid-harness",
        instance_id="inst-002",
        host_id="atlas-runner",
        process_id=12346,
    )
    store.open_session(
        stream_id="epic:202",
        holder=alias_holder,
        lineage_id="lineage-202",
        ttl_seconds=3600,
        session_id="session-202",
    )

    # Holder with clean, opaque values
    clean_holder = LeaseHolder(
        agent="valid-agent",
        harness="valid-harness",
        instance_id="inst-003",
        host_id="host-worker-01",
        process_id=12347,
    )
    store.open_session(
        stream_id="epic:203",
        holder=clean_holder,
        lineage_id="lineage-203",
        ttl_seconds=3600,
        session_id="session-203",
    )

    overview = build_fleet_overview(repo_root=tmp_path)
    assert overview["available"] is True
    by_id = {s["stream_id"]: s for s in overview["streams"]}

    # Check path and IP redacted
    s201 = by_id["epic:201"]
    assert s201["lease_state"] == "active"
    assert s201["unknown"] is False
    assert s201["stale"] is False
    assert s201["holder"] is not None
    assert s201["holder"]["agent"] == "[redacted]"  # path rejected
    assert s201["holder"]["harness"] == "valid-harness"
    assert s201["holder"]["instance_id"] == "inst-001"
    assert s201["holder"]["host_id"] == "[redacted]"  # IP rejected
    assert s201["session_state"] == "open"
    assert s201["heartbeat_age_seconds"] is not None
    assert s201["expires_at"] is not None

    # Check canonical host alias redacted
    s202 = by_id["epic:202"]
    assert s202["lease_state"] == "active"
    assert s202["holder"] is not None
    assert s202["holder"]["agent"] == "alias-agent"
    assert s202["holder"]["host_id"] == "[redacted]"  # alias rejected

    # Check clean stream
    s203 = by_id["epic:203"]
    assert s203["lease_state"] == "active"
    assert s203["unknown"] is False
    assert s203["stale"] is False
    assert s203["holder"] is not None
    assert s203["holder"]["agent"] == "valid-agent"
    assert s203["holder"]["host_id"] == "host-worker-01"


def test_fleet_status_expired_lease(tmp_path: Path) -> None:
    """Requirement 4: expired lease -> stale: True."""
    db_path = _init_session_db(tmp_path)
    store = SessionStreamStore(SessionStreamDatabase(db_path))

    past_time = datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)
    holder = LeaseHolder(
        agent="past-agent",
        harness="past-harness",
        instance_id="inst-expired",
        host_id="host-past",
        process_id=22222,
    )
    store.open_session(
        stream_id="epic:301",
        holder=holder,
        lineage_id="lineage-301",
        ttl_seconds=10,
        session_id="session-301",
        now=past_time,
    )

    overview = build_fleet_overview(repo_root=tmp_path)
    assert overview["available"] is True
    by_id = {s["stream_id"]: s for s in overview["streams"]}

    s301 = by_id["epic:301"]
    assert s301["lease_state"] == "expired"
    assert s301["stale"] is True
    assert s301["unknown"] is False
    assert s301["holder"] is not None


def test_fleet_status_cli_emits_overview(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI fleet status includes overview in output payload."""
    plane_root = tmp_path / "plane"
    plane_root.mkdir()
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(plane_root))

    db_path = _init_session_db(tmp_path)
    conn = SessionStreamDatabase(db_path).connect()
    try:
        conn.execute(
            "INSERT INTO streams(stream_id, kind, epic_number, created_at) "
            "VALUES ('epic:401', 'epic', 401, '2026-09-06T12:00:00Z')"
        )
        conn.commit()
    finally:
        conn.close()

    rc = main(["fleet", "status", "--root", str(plane_root), "--repo-root", str(tmp_path)])
    assert rc == EXIT_OK
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "overview" in data
    assert data["overview"]["available"] is True
    assert len(data["overview"]["streams"]) == 1
    assert data["overview"]["streams"][0]["stream_id"] == "epic:401"
    assert data["overview"]["streams"][0]["unknown"] is True


def test_fleet_facade_status_router(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Monitor API fleet facade status endpoint includes overview."""
    from scripts.api.fleet_router import fleet_facade_status

    plane_root = tmp_path / "plane"
    plane_root.mkdir()
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(plane_root))

    db_path = _init_session_db(tmp_path)
    conn = SessionStreamDatabase(db_path).connect()
    try:
        conn.execute(
            "INSERT INTO streams(stream_id, kind, epic_number, created_at) "
            "VALUES ('epic:501', 'epic', 501, '2026-09-06T12:00:00Z')"
        )
        conn.commit()
    finally:
        conn.close()

    mock_ctx = MagicMock()
    mock_ctx.roots.project_root = tmp_path

    payload = fleet_facade_status(ctx=mock_ctx)
    assert payload["read_only"] is True
    assert "overview" in payload
    assert payload["overview"]["available"] is True
    assert len(payload["overview"]["streams"]) == 1
    assert payload["overview"]["streams"][0]["stream_id"] == "epic:501"
