"""Unit tests for compact fleet overview in fleet status (private #670 AC-OVERVIEW).

Covers:
1. remote unreachable -> available: False (even if local SQLite exists)
2. local SQLite empty, remote live -> overview reflects remote authority
3. local SQLite stale, remote live -> overview reflects remote authority, not stale local
4. unleased stream -> unknown: True (explicit)
5. live lease -> holder present; redaction rejects raw host/path/alias
6. expired lease -> stale: True
7. CLI fleet status emits overview from remote authority (fail-open when unreachable)
8. Monitor facade uses injected epic store (not local DB)
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
from tests.epics_monitor_stub import epics_monitor_stub


def _init_session_db(root: Path) -> Path:
    db_dir = root / ".agent" / "session-streams" / "v1"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "session-streams.sqlite3"
    db = SessionStreamDatabase(db_path)
    conn = db.connect()
    conn.close()
    return db_path


def test_fleet_status_remote_unreachable(tmp_path: Path) -> None:
    """Remote unreachable -> available: False, even if local SQLite exists."""
    db_path = _init_session_db(tmp_path)
    conn = SessionStreamDatabase(db_path).connect()
    try:
        conn.execute(
            "INSERT INTO streams(stream_id, kind, epic_number, created_at) "
            "VALUES ('epic:999', 'epic', 999, '2026-09-06T12:00:00Z')"
        )
        conn.commit()
    finally:
        conn.close()

    unreachable_url = "http://127.0.0.1:59999"
    overview = build_fleet_overview(repo_root=tmp_path, monitor_url=unreachable_url)
    assert overview["available"] is False
    assert overview["streams"] == []

    payload = fleet_status_payload({"enabled": True}, repo_root=tmp_path, monitor_url=unreachable_url)
    assert payload["overview"]["available"] is False
    assert payload["overview"]["streams"] == []


def test_fleet_status_local_empty_remote_live(tmp_path: Path) -> None:
    """Local SQLite empty/missing, remote live -> overview reflects remote authority."""
    remote_root = tmp_path / "remote"
    remote_db_path = _init_session_db(remote_root)
    remote_store = SessionStreamStore(SessionStreamDatabase(remote_db_path))

    clean_holder = LeaseHolder(
        agent="worker-agent",
        harness="cli",
        instance_id="inst-001",
        host_id="worker-host",
        process_id=12345,
    )
    remote_store.open_session(
        stream_id="epic:201",
        holder=clean_holder,
        lineage_id="lineage-201",
        ttl_seconds=3600,
        session_id="session-201",
    )

    local_root = tmp_path / "empty_local"
    _init_session_db(local_root)

    with epics_monitor_stub(remote_store) as base:
        overview = build_fleet_overview(repo_root=local_root, monitor_url=base)
        assert overview["available"] is True
        assert len(overview["streams"]) == 1

        stream = overview["streams"][0]
        assert stream["stream_id"] == "epic:201"  # allow-hardcoded-epic: synthetic overview fixture
        assert stream["lease_state"] == "active"
        assert stream["unknown"] is False
        assert stream["stale"] is False
        assert stream["holder"] is not None
        assert stream["holder"]["agent"] == "worker-agent"
        assert stream["holder"]["host_id"] == "worker-host"
        assert stream["session_state"] == "open"


def test_fleet_status_local_stale_remote_live(tmp_path: Path) -> None:
    """Local SQLite stale, remote live -> overview reflects authoritative remote state."""
    local_root = tmp_path / "local"
    local_db_path = _init_session_db(local_root)
    local_store = SessionStreamStore(SessionStreamDatabase(local_db_path))

    past_time = datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)
    stale_holder = LeaseHolder(
        agent="stale-worker",
        harness="cli",
        instance_id="inst-stale",
        host_id="stale-host",
        process_id=11111,
    )
    local_store.open_session(
        stream_id="epic:301",
        holder=stale_holder,
        lineage_id="lineage-stale",
        ttl_seconds=10,
        session_id="session-stale",
        now=past_time,
    )

    remote_root = tmp_path / "remote"
    remote_db_path = _init_session_db(remote_root)
    remote_store = SessionStreamStore(SessionStreamDatabase(remote_db_path))

    live_holder = LeaseHolder(
        agent="live-worker",
        harness="cli",
        instance_id="inst-live",
        host_id="live-host",
        process_id=22222,
    )
    remote_store.open_session(
        stream_id="epic:301",
        holder=live_holder,
        lineage_id="lineage-live",
        ttl_seconds=3600,
        session_id="session-live",
    )

    with epics_monitor_stub(remote_store) as base:
        overview = build_fleet_overview(repo_root=local_root, monitor_url=base)
        assert overview["available"] is True
        assert len(overview["streams"]) == 1

        stream = overview["streams"][0]
        assert stream["stream_id"] == "epic:301"  # allow-hardcoded-epic: synthetic overview fixture
        assert stream["lease_state"] == "active"
        assert stream["unknown"] is False
        assert stream["stale"] is False
        assert stream["holder"] is not None
        assert stream["holder"]["agent"] == "live-worker"
        assert stream["holder"]["host_id"] == "live-host"


def test_fleet_status_remote_unleased_stream(tmp_path: Path) -> None:
    """Remote unleased stream -> unknown: True (explicit)."""
    remote_root = tmp_path / "remote"
    remote_db_path = _init_session_db(remote_root)
    remote_store = SessionStreamStore(SessionStreamDatabase(remote_db_path))

    conn = SessionStreamDatabase(remote_db_path).connect()
    try:
        conn.execute(
            "INSERT INTO streams(stream_id, kind, epic_number, created_at) "
            "VALUES ('epic:101', 'epic', 101, '2026-09-06T12:00:00Z')"
        )
        conn.commit()
    finally:
        conn.close()

    with epics_monitor_stub(remote_store) as base:
        overview = build_fleet_overview(monitor_url=base)
        assert overview["available"] is True
        assert len(overview["streams"]) == 1

        stream = overview["streams"][0]
        assert stream["stream_id"] == "epic:101"  # allow-hardcoded-epic: synthetic overview fixture
        assert stream["lease_state"] == "unleased"
        assert stream["unknown"] is True
        assert stream["stale"] is False
        assert stream["holder"] is None
        assert stream["heartbeat_age_seconds"] is None
        assert stream["expires_at"] is None
        assert stream["session_state"] is None


def test_fleet_status_live_lease_and_redaction(tmp_path: Path) -> None:
    """Live lease -> holder present; redaction rejects raw host/path/alias."""
    remote_root = tmp_path / "remote"
    remote_db_path = _init_session_db(remote_root)
    remote_store = SessionStreamStore(SessionStreamDatabase(remote_db_path))

    # Holder with raw host IP and path-containing agent
    raw_holder = LeaseHolder(
        agent="var/run/custom-agent",
        harness="valid-harness",
        instance_id="inst-001",
        host_id="192.0.2.1",
        process_id=12345,
    )
    remote_store.open_session(
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
    remote_store.open_session(
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
    remote_store.open_session(
        stream_id="epic:203",
        holder=clean_holder,
        lineage_id="lineage-203",
        ttl_seconds=3600,
        session_id="session-203",
    )

    with epics_monitor_stub(remote_store) as base:
        overview = build_fleet_overview(monitor_url=base)
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


def test_fleet_status_remote_expired_lease(tmp_path: Path) -> None:
    """Remote expired lease -> stale: True."""
    remote_root = tmp_path / "remote"
    remote_db_path = _init_session_db(remote_root)
    remote_store = SessionStreamStore(SessionStreamDatabase(remote_db_path))

    past_time = datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)
    holder = LeaseHolder(
        agent="past-agent",
        harness="past-harness",
        instance_id="inst-expired",
        host_id="host-past",
        process_id=22222,
    )
    remote_store.open_session(
        stream_id="epic:301",
        holder=holder,
        lineage_id="lineage-301",
        ttl_seconds=10,
        session_id="session-301",
        now=past_time,
    )

    with epics_monitor_stub(remote_store) as base:
        overview = build_fleet_overview(monitor_url=base)
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
    """CLI fleet status includes overview from remote authority; fails-open when unreachable."""
    plane_root = tmp_path / "plane"
    plane_root.mkdir()
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(plane_root))

    remote_root = tmp_path / "remote"
    remote_db_path = _init_session_db(remote_root)
    remote_store = SessionStreamStore(SessionStreamDatabase(remote_db_path))

    conn = SessionStreamDatabase(remote_db_path).connect()
    try:
        conn.execute(
            "INSERT INTO streams(stream_id, kind, epic_number, created_at) "
            "VALUES ('epic:401', 'epic', 401, '2026-09-06T12:00:00Z')"
        )
        conn.commit()
    finally:
        conn.close()

    with epics_monitor_stub(remote_store) as base:
        rc = main([
            "fleet", "status",
            "--root", str(plane_root),
            "--repo-root", str(tmp_path),
            "--monitor-url", base,
        ])
        assert rc == EXIT_OK
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "overview" in data
        assert data["overview"]["available"] is True
        assert len(data["overview"]["streams"]) == 1
        assert data["overview"]["streams"][0]["stream_id"] == "epic:401"  # allow-hardcoded-epic: synthetic overview fixture
        assert data["overview"]["streams"][0]["unknown"] is True

    # Fail-open when unreachable
    rc = main([
        "fleet", "status",
        "--root", str(plane_root),
        "--repo-root", str(tmp_path),
        "--monitor-url", "http://127.0.0.1:59999",
    ])
    assert rc == EXIT_OK
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["overview"]["available"] is False
    assert data["overview"]["streams"] == []


def test_fleet_facade_status_router(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Monitor API fleet facade status uses injected epic store, not local DB."""
    from scripts.api.fleet_router import fleet_facade_status

    plane_root = tmp_path / "plane"
    plane_root.mkdir()
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(plane_root))

    # Local SQLite has different stream that should NOT be used by facade
    local_db_path = _init_session_db(tmp_path)
    conn = SessionStreamDatabase(local_db_path).connect()
    try:
        conn.execute(
            "INSERT INTO streams(stream_id, kind, epic_number, created_at) "
            "VALUES ('epic:999', 'epic', 999, '2026-09-06T12:00:00Z')"
        )
        conn.commit()
    finally:
        conn.close()

    # Injected store has epic:501
    injected_root = tmp_path / "injected"
    injected_db_path = _init_session_db(injected_root)
    injected_store = SessionStreamStore(SessionStreamDatabase(injected_db_path))
    conn2 = SessionStreamDatabase(injected_db_path).connect()
    try:
        conn2.execute(
            "INSERT INTO streams(stream_id, kind, epic_number, created_at) "
            "VALUES ('epic:501', 'epic', 501, '2026-09-06T12:00:00Z')"
        )
        conn2.commit()
    finally:
        conn2.close()

    mock_ctx = MagicMock()
    mock_ctx.roots.project_root = tmp_path
    mock_ctx.stores.epics_store = injected_store

    payload = fleet_facade_status(ctx=mock_ctx)
    assert payload["read_only"] is True
    assert "overview" in payload
    assert payload["overview"]["available"] is True
    assert len(payload["overview"]["streams"]) == 1
    # Must use injected store, not local DB
    assert payload["overview"]["streams"][0]["stream_id"] == "epic:501"  # allow-hardcoded-epic: synthetic overview fixture

    # When injected store is None -> available: False
    mock_ctx_none = MagicMock()
    mock_ctx_none.roots.project_root = tmp_path
    mock_ctx_none.stores.epics_store = None

    payload_none = fleet_facade_status(ctx=mock_ctx_none)
    assert payload_none["overview"]["available"] is False
    assert payload_none["overview"]["streams"] == []
