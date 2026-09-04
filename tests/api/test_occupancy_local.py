"""Unit tests for local occupancy seats (session streams + markers)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import LeaseHolder
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api.occupancy_local import (
    clear_marker,
    driver_seat_host_id,
    foundry_marker_host_id,
    occupancy_marker_scope,
    occupants_from_markers,
    occupants_from_session_streams,
    read_session_streams,
    resolve_launcher_host_id,
    write_marker,
)


def _open_lease(
    db_path: Path,
    *,
    stream_id: str = "epic:7139",
    agent: str = "claude",
    task_id: str = "infra-drive",
    ttl_seconds: int = 600,
    session_id: str | None = None,
    lease_id: str | None = None,
    instance_id: str = "runtime-1",
    process_id: int = 41001,
) -> None:
    store = SessionStreamStore(SessionStreamDatabase(db_path))
    store.open_session(
        stream_id=stream_id,
        holder=LeaseHolder(
            agent=agent,
            harness="claude-code",
            instance_id=instance_id,
            process_id=process_id,
            task_id=task_id,
        ),
        lineage_id=f"lineage-{stream_id}",
        ttl_seconds=ttl_seconds,
        session_id=session_id or f"session-{stream_id}",
        lease_id=lease_id or f"lease-{stream_id}",
    )


def test_driver_seat_host_id_uses_explicit_opaque_then_self_host(monkeypatch: pytest.MonkeyPatch) -> None:
    mapping = {"teach-box": "host-teacher", "worker-box": "host-worker"}
    selected = {"host-teacher": "teach-box", "host-worker": "worker-box"}
    monkeypatch.delenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", raising=False)
    monkeypatch.delenv("ATLAS_JOB_SELF_HOST", raising=False)
    assert driver_seat_host_id(mapping, selected) is None

    monkeypatch.setenv("ATLAS_JOB_SELF_HOST", "teach-box")
    assert driver_seat_host_id(mapping, selected) == "host-teacher"

    monkeypatch.setenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", "host-worker")
    assert driver_seat_host_id(mapping, selected) == "host-worker"

    monkeypatch.setenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", "atlas-runner")
    assert driver_seat_host_id(mapping, selected) is None


def test_driver_seat_host_id_rejects_retired_host_job_even_when_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``host-job`` is permanently retired: never usable even via explicit env var."""
    mapping = {"teach-box": "host-teacher"}
    selected = {"host-teacher": "teach-box"}
    monkeypatch.delenv("ATLAS_JOB_SELF_HOST", raising=False)
    monkeypatch.setenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", "host-job")
    assert driver_seat_host_id(mapping, selected) is None


def test_foundry_marker_host_id_rejects_retired_host_job_even_when_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``host-job`` is permanently retired: never usable even via explicit env var."""
    mapping = {"teach-box": "host-teacher"}
    monkeypatch.delenv("ATLAS_JOB_SELF_HOST", raising=False)
    monkeypatch.setenv("MONITOR_OCCUPANCY_FOUNDRY_HOST_ID", "host-job")
    assert foundry_marker_host_id(mapping) is None

    monkeypatch.setenv("MONITOR_OCCUPANCY_FOUNDRY_HOST_ID", "host-worker")
    assert foundry_marker_host_id(mapping) == "host-worker"


def test_darwin_empty_map_does_not_attach_session_stream_drivers_to_mac_operator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Darwin empty-map is observer-only — never kind=driver on mac-operator."""
    db_path = tmp_path / "session-streams.sqlite3"
    _open_lease(db_path)
    monkeypatch.delenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", raising=False)
    monkeypatch.delenv("ATLAS_JOB_SELF_HOST", raising=False)
    monkeypatch.setattr("scripts.api.occupancy_local.sys.platform", "darwin")
    mapping: dict[str, str] = {}
    selected: dict[str, str | None] = {"host-teacher": None, "mac-operator": None}

    assert driver_seat_host_id(mapping, selected) is None
    mac_occupants = occupants_from_session_streams(
        host_id="mac-operator",
        mapping=mapping,
        selected=selected,
        db_path=db_path,
    )
    assert mac_occupants == []
    assert all(row.get("kind") != "driver" for row in mac_occupants)
    assert (
        occupants_from_session_streams(
            host_id="host-teacher",
            mapping=mapping,
            selected=selected,
            db_path=db_path,
        )
        == []
    )


def test_linux_empty_map_attaches_session_stream_drivers_to_host_teacher(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "session-streams.sqlite3"
    _open_lease(db_path)
    monkeypatch.delenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", raising=False)
    monkeypatch.delenv("ATLAS_JOB_SELF_HOST", raising=False)
    monkeypatch.setattr("scripts.api.occupancy_local.sys.platform", "linux")
    mapping: dict[str, str] = {}
    selected: dict[str, str | None] = {"host-teacher": None, "mac-operator": None}

    assert driver_seat_host_id(mapping, selected) == "host-teacher"
    teacher = occupants_from_session_streams(
        host_id="host-teacher",
        mapping=mapping,
        selected=selected,
        db_path=db_path,
    )
    assert teacher == [
        {"kind": "driver", "agent": "claude", "task_id": "infra-drive", "epic": "7139"}
    ]
    assert (
        occupants_from_session_streams(
            host_id="mac-operator",
            mapping=mapping,
            selected=selected,
            db_path=db_path,
        )
        == []
    )


def test_resolve_launcher_host_id_uses_occupancy_mapping_and_fallbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LU_MONITOR_HOST_ID", raising=False)
    monkeypatch.delenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", raising=False)
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", "teach-box=host-teacher,worker-box=host-worker")
    monkeypatch.setenv("ATLAS_JOB_SELF_HOST", "worker-box")
    assert resolve_launcher_host_id() == "host-worker"

    monkeypatch.setenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", "host-driver")
    assert resolve_launcher_host_id() == "host-driver"
    monkeypatch.delenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", raising=False)
    monkeypatch.setenv("ATLAS_JOB_SELF_HOST", "unknown-box")
    assert resolve_launcher_host_id() == "local"

    monkeypatch.delenv("MONITOR_OCCUPANCY_HOST_IDS", raising=False)
    monkeypatch.delenv("ATLAS_JOB_SELF_HOST", raising=False)
    monkeypatch.setattr("scripts.api.occupancy_local.sys.platform", "linux")
    assert resolve_launcher_host_id() == "host-teacher"

    monkeypatch.setenv("LU_MONITOR_HOST_ID", "host-explicit")
    assert resolve_launcher_host_id() == "host-explicit"


def test_occupants_from_session_streams_reads_active_lease_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "session-streams.sqlite3"
    _open_lease(db_path)
    mapping = {"teach-box": "host-teacher"}
    selected = {"host-teacher": "teach-box", "host-worker": "worker-box"}
    monkeypatch.setenv("ATLAS_JOB_SELF_HOST", "teach-box")
    monkeypatch.delenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", raising=False)

    teacher = occupants_from_session_streams(
        host_id="host-teacher",
        mapping=mapping,
        selected=selected,
        db_path=db_path,
    )
    assert teacher == [{"kind": "driver", "agent": "claude", "task_id": "infra-drive", "epic": "7139"}]
    assert (
        occupants_from_session_streams(
            host_id="host-worker",
            mapping=mapping,
            selected=selected,
            db_path=db_path,
        )
        == []
    )


def test_occupants_from_session_streams_preserves_distinct_epics_sharing_task_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "session-streams.sqlite3"
    _open_lease(
        db_path,
        stream_id="epic:4387",
        agent="grok",
        task_id="launcher-grok-driver",
        process_id=3176144,
    )
    _open_lease(
        db_path,
        stream_id="epic:6943",
        agent="grok",
        task_id="launcher-grok-driver",
        process_id=3128086,
    )
    _open_lease(
        db_path,
        stream_id="epic:7177",
        agent="grok",
        task_id="launcher-grok-driver",
        process_id=3172701,
    )
    mapping = {"teach-box": "host-teacher"}
    selected = {"host-teacher": "teach-box"}
    monkeypatch.setenv("ATLAS_JOB_SELF_HOST", "teach-box")
    monkeypatch.delenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", raising=False)

    occupants = occupants_from_session_streams(
        host_id="host-teacher",
        mapping=mapping,
        selected=selected,
        db_path=db_path,
    )
    assert len(occupants) == 3
    assert occupants == [
        {"kind": "driver", "agent": "grok", "task_id": "launcher-grok-driver", "epic": "4387"},
        {"kind": "driver", "agent": "grok", "task_id": "launcher-grok-driver", "epic": "6943"},
        {"kind": "driver", "agent": "grok", "task_id": "launcher-grok-driver", "epic": "7177"},
    ]


def test_read_session_streams_dedupes_same_epic_and_task_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "session-streams.sqlite3"
    _open_lease(
        db_path,
        stream_id="epic:7177",
        agent="grok",
        task_id="launcher-grok-driver",
    )
    mapping = {"teach-box": "host-teacher"}
    selected = {"host-teacher": "teach-box"}
    monkeypatch.setenv("ATLAS_JOB_SELF_HOST", "teach-box")
    monkeypatch.delenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", raising=False)

    clock = datetime.now(UTC)
    duplicate_rows = [
        {
            "stream_id": "epic:7177",
            "holder_agent": "grok",
            "holder_task_id": "launcher-grok-driver",
            "heartbeat_at": clock.isoformat().replace("+00:00", "Z"),
            "expires_at": (clock + timedelta(minutes=10)).isoformat().replace("+00:00", "Z"),
        },
        {
            "stream_id": "epic:7177",
            "holder_agent": "grok",
            "holder_task_id": "launcher-grok-driver",
            "heartbeat_at": clock.isoformat().replace("+00:00", "Z"),
            "expires_at": (clock + timedelta(minutes=10)).isoformat().replace("+00:00", "Z"),
        },
    ]

    class _FakeCursor:
        def fetchall(self) -> list[dict[str, Any]]:
            return duplicate_rows

    class _FakeConn:
        def __enter__(self) -> _FakeConn:
            return self

        def __exit__(self, *args: Any) -> None:
            pass

        def execute(self, sql: str) -> _FakeCursor:
            return _FakeCursor()

    monkeypatch.setattr(
        "scripts.api.occupancy_local.SessionStreamDatabase.connect",
        lambda self, read_only=True: _FakeConn(),
    )

    read = read_session_streams(
        host_id="host-teacher",
        mapping=mapping,
        selected=selected,
        db_path=db_path,
        now=clock,
    )
    assert read.readable is True
    assert len(read.occupants) == 1
    assert read.occupants == [
        {"kind": "driver", "agent": "grok", "task_id": "launcher-grok-driver", "epic": "7177"}
    ]


def test_occupants_from_session_streams_skips_expired_and_broken_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mapping = {"teach-box": "host-teacher"}
    selected = {"host-teacher": "teach-box"}
    monkeypatch.setenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", "host-teacher")

    expired = tmp_path / "expired.sqlite3"
    _open_lease(expired, ttl_seconds=1)
    later = datetime.now(UTC) + timedelta(seconds=5)
    assert (
        occupants_from_session_streams(
            host_id="host-teacher",
            mapping=mapping,
            selected=selected,
            db_path=expired,
            now=later,
        )
        == []
    )

    broken = tmp_path / "broken.sqlite3"
    broken.write_text("not-a-database", encoding="utf-8")
    assert (
        occupants_from_session_streams(
            host_id="host-teacher",
            mapping=mapping,
            selected=selected,
            db_path=broken,
        )
        == []
    )
    assert (
        occupants_from_session_streams(
            host_id="host-teacher",
            mapping=mapping,
            selected=selected,
            db_path=tmp_path / "missing.sqlite3",
        )
        == []
    )


def test_occupants_from_session_streams_falls_back_when_task_id_is_unsafe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "session-streams.sqlite3"
    _open_lease(db_path, agent="claude", task_id="atlas-runner-reenrich-3")
    monkeypatch.setenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", "host-teacher")
    occupants = occupants_from_session_streams(
        host_id="host-teacher",
        mapping={"teach-box": "host-teacher"},
        selected={"host-teacher": "teach-box"},
        db_path=db_path,
    )
    assert occupants == [{"kind": "driver", "agent": "claude", "task_id": "epic-7139", "epic": "7139"}]


def test_marker_round_trip_and_expiry(tmp_path: Path) -> None:
    markers = tmp_path / "markers"
    written = write_marker(
        kind="service",
        agent="foundry",
        task_id="evidence-compiler",
        epic="7102",
        host_id="host-teacher",
        path=markers,
        ttl_seconds=60,
    )
    assert written is not None
    assert written.parent == markers
    assert occupants_from_markers(host_id="host-teacher", root=markers) == [
        {
            "kind": "service",
            "agent": "foundry",
            "task_id": "evidence-compiler",
            "epic": "7102",
        }
    ]
    assert occupants_from_markers(host_id="host-worker", root=markers) == []

    stale_time = datetime.now(UTC) + timedelta(minutes=30)
    assert occupants_from_markers(host_id="host-teacher", root=markers, now=stale_time) == []

    clear_marker(kind="service", task_id="evidence-compiler", path=markers)
    assert occupants_from_markers(host_id="host-teacher", root=markers) == []


def test_marker_rejects_leaks_and_observer_kind(tmp_path: Path) -> None:
    markers = tmp_path / "markers"
    assert (
        write_marker(
            kind="service",
            agent="foundry",
            task_id="evidence-compiler",
            host_id="atlas-runner",
            path=markers,
        )
        is None
    )
    assert (
        write_marker(
            kind="service",
            agent="foundry",
            task_id="atlas-runner-job",
            host_id="host-teacher",
            path=markers,
        )
        is None
    )
    leaked = markers / "leaked.json"
    leaked.parent.mkdir(parents=True)
    leaked.write_text(
        '{"kind":"service","agent":"foundry","task_id":"ok","host_id":"host-teacher","epic":"not/a-token",'
        '"updated_at":"' + datetime.now(UTC).isoformat().replace("+00:00", "Z") + '"}',
        encoding="utf-8",
    )
    assert occupants_from_markers(host_id="host-teacher", root=markers) == [
        {"kind": "service", "agent": "foundry", "task_id": "ok", "epic": None}
    ]
    observer = markers / "observer.json"
    observer.write_text(
        '{"kind":"observer","agent":"cursor","task_id":"7061","host_id":"host-teacher"}',
        encoding="utf-8",
    )
    kinds = {row["kind"] for row in occupants_from_markers(host_id="host-teacher", root=markers)}
    assert "observer" not in kinds


def test_occupancy_marker_scope_is_opt_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MONITOR_OCCUPANCY_MARKERS", raising=False)
    monkeypatch.delenv("MONITOR_OCCUPANCY_FOUNDRY_HOST_ID", raising=False)
    with occupancy_marker_scope(
        kind="service",
        task_id="ukrainian-data-foundry",
        agent="foundry",
        epic="foundry",
        host_id="host-teacher",
    ) as written:
        assert written is None

    monkeypatch.setenv("MONITOR_OCCUPANCY_MARKERS", str(tmp_path / "markers"))
    with occupancy_marker_scope(
        kind="service",
        task_id="ukrainian-data-foundry",
        agent="foundry",
        epic="foundry",
        host_id="host-teacher",
    ) as written:
        assert written is not None
        assert occupants_from_markers(host_id="host-teacher", root=tmp_path / "markers")
    assert occupants_from_markers(host_id="host-teacher", root=tmp_path / "markers") == []
