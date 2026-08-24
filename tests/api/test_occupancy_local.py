"""Unit tests for local occupancy seats (session streams + markers)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import LeaseHolder
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api.occupancy_local import (
    clear_marker,
    driver_seat_host_id,
    occupancy_marker_scope,
    occupants_from_markers,
    occupants_from_session_streams,
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
) -> None:
    store = SessionStreamStore(SessionStreamDatabase(db_path))
    store.open_session(
        stream_id=stream_id,
        holder=LeaseHolder(
            agent=agent,
            harness="claude-code",
            instance_id="runtime-1",
            process_id=41001,
            task_id=task_id,
        ),
        lineage_id="lineage-occupancy",
        ttl_seconds=ttl_seconds,
        session_id="session-occupancy",
        lease_id="lease-occupancy",
    )


def test_driver_seat_host_id_uses_explicit_opaque_then_self_host(monkeypatch: pytest.MonkeyPatch) -> None:
    mapping = {"teach-box": "host-teacher", "job-box": "host-job"}
    selected = {"host-teacher": "teach-box", "host-job": "job-box"}
    monkeypatch.delenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", raising=False)
    monkeypatch.delenv("ATLAS_JOB_SELF_HOST", raising=False)
    assert driver_seat_host_id(mapping, selected) is None

    monkeypatch.setenv("ATLAS_JOB_SELF_HOST", "teach-box")
    assert driver_seat_host_id(mapping, selected) == "host-teacher"

    monkeypatch.setenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", "host-job")
    assert driver_seat_host_id(mapping, selected) == "host-job"

    monkeypatch.setenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", "atlas-runner")
    assert driver_seat_host_id(mapping, selected) is None


def test_resolve_launcher_host_id_uses_occupancy_mapping_and_fallbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LU_MONITOR_HOST_ID", raising=False)
    monkeypatch.delenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", raising=False)
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", "teach-box=host-teacher,job-box=host-job")
    monkeypatch.setenv("ATLAS_JOB_SELF_HOST", "job-box")
    assert resolve_launcher_host_id() == "host-job"

    monkeypatch.setenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", "host-driver")
    assert resolve_launcher_host_id() == "host-driver"
    monkeypatch.delenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", raising=False)
    monkeypatch.setenv("ATLAS_JOB_SELF_HOST", "unknown-box")
    assert resolve_launcher_host_id() == "local"

    monkeypatch.setenv("LU_MONITOR_HOST_ID", "host-explicit")
    assert resolve_launcher_host_id() == "host-explicit"


def test_occupants_from_session_streams_reads_active_lease_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "session-streams.sqlite3"
    _open_lease(db_path)
    mapping = {"teach-box": "host-teacher"}
    selected = {"host-teacher": "teach-box", "host-job": "job-box"}
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
            host_id="host-job",
            mapping=mapping,
            selected=selected,
            db_path=db_path,
        )
        == []
    )


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
    assert occupants_from_markers(host_id="host-job", root=markers) == []

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
