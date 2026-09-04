"""Tests for GET /api/fleet/workers/v1 and worker adapters (#7187)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from scripts.api import fleet_workers_collect as collect_mod
from scripts.api.fleet_workers_collect import UNATTRIBUTED_HOST_ID, workers_payload
from scripts.api.fleet_workers_models import WorkerRow
from scripts.api.fleet_workers_sanitize import validate_workers_list
from scripts.api.main import app
from scripts.api.observer_presence import PresenceRequest, reset_observer_presence, upsert_presence
from scripts.api.occupancy_local import OccupancyRead, _marker_fresh
from scripts.api.project_state_router import reset_local_document_cache
from scripts.api.project_state_sanitize import ProjectStateValidationError
from scripts.api.project_state_store import get_stored_report, reset_project_state_store

client = TestClient(app, raise_server_exceptions=False)
loop_client = TestClient(
    app,
    base_url="http://127.0.0.1",
    client=("127.0.0.1", 50000),
    raise_server_exceptions=False,
)

_PLACEHOLDER_MAP = "teach-box=host-teacher,worker-box=host-worker"
_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_ALIAS_LEAKS = ("atlas-runner", "hramatka", "vps")

SHA_MAIN = "a" * 40
SHA_HEAD = "c" * 40


def _host_by_id(payload: dict[str, Any], host_id: str) -> dict[str, Any]:
    hosts = payload["hosts"]
    assert isinstance(hosts, list)
    for host in hosts:
        if host.get("host_id") == host_id:
            return host
    raise AssertionError(f"host {host_id!r} not in {hosts!r}")


def _primary() -> dict[str, Any]:
    return {
        "head_sha": SHA_HEAD,
        "origin_main_sha": SHA_MAIN,
        "origin_main_age_s": 120.0,
        "ahead": 0,
        "behind": 0,
        "dirty_count": 0,
    }


def _service() -> dict[str, Any]:
    return {
        "name": "api",
        "state": "running",
        "repo": "learn-ukrainian",
        "serving_mode": "release",
        "serving_sha": SHA_MAIN,
        "checkout_sha": None,
    }


def _document(
    host_id: str = "host-worker",
    *,
    workers: list[dict[str, Any]] | None = None,
    collected_at: str | None = None,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "host_id": host_id,
        "primary": _primary(),
        "worktrees": {"count": 0},
        "services": [_service()],
        "collected_at": collected_at or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    if workers is not None:
        doc["workers"] = workers
    return doc


def _worker_row(**overrides: Any) -> dict[str, Any]:
    base = {
        "kind": "delegate",
        "agent": "cursor",
        "harness": None,
        "id": "monitor-7187",
        "run_id": "a1b2c3d4",
        "epic": "epic:7177",
        "state": "live",
        "age_s": 30,
        "seat_model": None,
    }
    base.update(overrides)
    return base


@pytest.fixture(autouse=True)
def _reset_stores() -> None:
    reset_project_state_store()
    reset_observer_presence()
    reset_local_document_cache()
    collect_mod.reset_workers_payload_cache()
    yield
    reset_project_state_store()
    reset_observer_presence()
    reset_local_document_cache()
    collect_mod.reset_workers_payload_cache()


def test_workers_route_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(collect_mod, "_self_host_ids", lambda: set())
    response = client.get("/api/fleet/workers/v1")
    assert response.status_code == 200
    data = response.json()
    assert data["schema"] == "monitor-fleet-workers.v1"
    assert "counts" in data
    assert isinstance(data["hosts"], list)


def test_retired_host_job_mapping_never_yields_worker_listing(monkeypatch: pytest.MonkeyPatch) -> None:
    """A mapping that still points a canonical alias at the retired host-job
    id must not resurrect it as a worker-listing host, mapped or not."""
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", "atlas-runner=host-job")
    monkeypatch.setattr(collect_mod, "_self_host_ids", lambda: set())
    response = client.get("/api/fleet/workers/v1?host_id=host-job")
    assert response.status_code == 200
    data = response.json()
    assert not any(host.get("host_id") == "host-job" for host in data["hosts"])


def test_v1_report_workers_unreported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setattr(collect_mod, "_self_host_ids", lambda: set())
    loop_client.post("/api/fleet/projects/v1/report", json=_document())
    host = _host_by_id(client.get("/api/fleet/workers/v1?host_id=host-worker").json(), "host-worker")
    assert host["workers_status"] == "unreported"
    assert host["workers"] == []
    assert "unreported:host-worker" in client.get("/api/fleet/workers/v1").json()["attention"]


def test_v2_empty_workers_verified_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setattr(collect_mod, "_self_host_ids", lambda: set())
    loop_client.post("/api/fleet/projects/v1/report", json=_document(workers=[]))
    host = _host_by_id(client.get("/api/fleet/workers/v1?host_id=host-worker").json(), "host-worker")
    assert host["workers_status"] == "reported"
    assert host["workers"] == []


def test_remote_reported_workers_surface(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setattr(collect_mod, "_self_host_ids", lambda: set())
    loop_client.post(
        "/api/fleet/projects/v1/report",
        json=_document(workers=[_worker_row()]),
    )
    host = _host_by_id(client.get("/api/fleet/workers/v1?host_id=host-worker").json(), "host-worker")
    assert host["workers_status"] == "reported"
    assert len(host["workers"]) == 1
    assert host["workers"][0]["source"] == "project_state"
    assert host["workers"][0]["id"] == "monitor-7187"


def test_same_task_id_different_run_id_two_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setattr(collect_mod, "_self_host_ids", lambda: set())
    loop_client.post(
        "/api/fleet/projects/v1/report",
        json=_document(
            workers=[
                _worker_row(run_id="11111111"),
                _worker_row(run_id="22222222"),
            ]
        ),
    )
    workers = _host_by_id(client.get("/api/fleet/workers/v1?host_id=host-worker").json(), "host-worker")["workers"]
    run_ids = {row["run_id"] for row in workers}
    assert run_ids == {"11111111", "22222222"}


def test_delegate_run_id_matches_sha256_nonce(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    nonce = "known-run-nonce-7187"
    expected_run_id = hashlib.sha256(nonce.encode("utf-8")).hexdigest()[:8]
    now = datetime.now(UTC)
    (tasks / "nonce-task.json").write_text(
        json.dumps(
            {
                "task_id": "nonce-task",
                "agent": "cursor",
                "status": "running",
                "pid": os.getpid(),
                "started_at": now.isoformat(),
                "run_nonce": nonce,
            }
        ),
        encoding="utf-8",
    )
    rows = collect_mod.collect_delegate_workers(tasks, now=now)
    assert len(rows) == 1
    assert rows[0].row.run_id == expected_run_id


def test_monotonic_ingest_rejects_stale_report(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    newer = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    older = (datetime.now(UTC) - timedelta(minutes=2)).isoformat().replace("+00:00", "Z")
    newer_doc = _document(workers=[], collected_at=newer)
    assert loop_client.post("/api/fleet/projects/v1/report", json=newer_doc).status_code == 200
    stored_before = get_stored_report("host-worker")
    assert stored_before is not None
    stale = loop_client.post("/api/fleet/projects/v1/report", json=_document(workers=[], collected_at=older))
    assert stale.status_code == 409
    assert stale.json()["detail"] == "stale_report"
    stored_after = get_stored_report("host-worker")
    assert stored_after is not None
    assert stored_after.document == stored_before.document


def test_collected_at_bounds_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    future = (datetime.now(UTC) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    assert loop_client.post("/api/fleet/projects/v1/report", json=_document(collected_at=future)).status_code == 400
    ancient = (datetime.now(UTC) - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    assert loop_client.post("/api/fleet/projects/v1/report", json=_document(collected_at=ancient)).status_code == 400


def test_no_occupancy_probe_on_read_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(collect_mod, "_self_host_ids", lambda: set())

    def _boom(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("occupancy probe must not run on workers read path")

    monkeypatch.setattr("scripts.api.occupancy._occupancy_payload_async", _boom)
    monkeypatch.setattr("scripts.api.atlas_jobs_router._get_host_load_entry", _boom)
    monkeypatch.setattr("scripts.api.atlas_jobs_router._get_host_load_entry_async", _boom)
    monkeypatch.setattr("scripts.api.atlas_jobs_router._schedule_host_load_refresh", _boom)
    response = client.get("/api/fleet/workers/v1")
    assert response.status_code == 200


@pytest.mark.parametrize(
    "task_id",
    [
        "a" * 65,
        "a" * 129,
        "bad/id",
    ],
)
def test_oversized_task_id_dropped_not_500(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    task_id: str,
) -> None:
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    now = datetime.now(UTC)
    (tasks / "long.json").write_text(
        json.dumps(
            {
                "task_id": task_id,
                "agent": "cursor",
                "status": "running",
                "pid": os.getpid(),
                "started_at": now.isoformat(),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setenv("LU_MONITOR_HOST_ID", "host-worker")
    monkeypatch.setattr(collect_mod, "_self_host_ids", lambda: {"host-worker"})
    monkeypatch.setattr("scripts.api.delegate_router._tasks_dir", lambda ctx=None: tasks)
    response = client.get("/api/fleet/workers/v1?host_id=host-worker")
    assert response.status_code == 200
    data = response.json()
    host = _host_by_id(data, "host-worker")
    assert not any(worker["id"] == task_id for worker in host["workers"])
    assert data["counts"]["skipped"] == 1


def test_validate_workers_list_rejects_none() -> None:
    with pytest.raises(ProjectStateValidationError):
        validate_workers_list([None])


def test_marker_without_timestamps_not_live() -> None:
    now = datetime.now(UTC)
    assert _marker_fresh({"host_id": "host-worker", "kind": "service", "task_id": "x", "agent": "codex"}, now=now) is False


def test_marker_within_ttl_is_live() -> None:
    now = datetime.now(UTC)
    payload = {
        "host_id": "host-worker",
        "kind": "service",
        "task_id": "x",
        "agent": "codex",
        "updated_at": now.isoformat().replace("+00:00", "Z"),
    }
    assert _marker_fresh(payload, now=now) is True


def test_marker_past_ttl_not_live() -> None:
    now = datetime.now(UTC)
    stale = now - timedelta(hours=1)
    payload = {
        "host_id": "host-worker",
        "kind": "service",
        "task_id": "x",
        "agent": "codex",
        "updated_at": stale.isoformat().replace("+00:00", "Z"),
    }
    assert _marker_fresh(payload, now=now) is False


def test_delegate_adapter_liveness_matrix(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    now = datetime.now(UTC)
    cases = [
        (
            "spawning.json",
            {"task_id": "spawning-1", "agent": "cursor", "status": "spawning", "started_at": now.isoformat()},
            "starting",
        ),
        (
            "live.json",
            {"task_id": "live-1", "agent": "cursor", "status": "running", "pid": 1, "started_at": now.isoformat()},
            "live",
        ),
        (
            "zombie.json",
            {
                "task_id": "zombie-1",
                "agent": "cursor",
                "status": "running",
                "pid": 999999,
                "started_at": now.isoformat(),
            },
            "zombie",
        ),
        ("done.json", {"task_id": "done-1", "agent": "cursor", "status": "done", "started_at": now.isoformat()}, None),
        (
            "failed.json",
            {"task_id": "failed-1", "agent": "cursor", "status": "failed", "started_at": now.isoformat()},
            None,
        ),
    ]
    for name, payload, _expected in cases:
        (tasks / name).write_text(json.dumps(payload), encoding="utf-8")
    rows = collect_mod.collect_delegate_workers(tasks, now=now)
    states = {row.row.id: row.row.state for row in rows}
    for _name, payload, expected in cases:
        task_id = payload["task_id"]
        if expected is None:
            assert task_id not in states
        else:
            assert states[task_id] == expected


def test_driver_hostless_lease_unattributed_bucket(tmp_path: Path) -> None:
    db = _driver_lease_db(tmp_path)
    expires = (datetime.now(UTC) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    heartbeat = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    _insert_driver_lease(db, holder_host_id=None, heartbeat=heartbeat, expires=expires, instance_id="inst-alpha")
    _, unattributed = collect_mod.collect_driver_workers(db_path=db)
    assert len(unattributed) == 1
    assert unattributed[0].row.id == "inst-alpha"
    payload = workers_payload(session_db=db, host_id=UNATTRIBUTED_HOST_ID)
    host = _host_by_id(payload, UNATTRIBUTED_HOST_ID)
    assert host["reason"] == "lease has no host claim"


def _driver_lease_db(tmp_path: Path) -> Path:
    db = tmp_path / "streams.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE sessions (
            stream_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            state TEXT NOT NULL,
            PRIMARY KEY (stream_id, session_id)
        );
        CREATE TABLE stream_leases (
            stream_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            state TEXT NOT NULL,
            holder_agent TEXT,
            holder_harness TEXT,
            holder_instance_id TEXT,
            holder_task_id TEXT,
            holder_host_id TEXT,
            heartbeat_at TEXT,
            expires_at TEXT
        );
        """
    )
    conn.execute("INSERT INTO sessions VALUES ('epic:7177', 'sess-1', 'open')")
    conn.commit()
    conn.close()
    return db


def _insert_driver_lease(
    db: Path,
    *,
    holder_host_id: str | None,
    heartbeat: str,
    expires: str,
    instance_id: str = "inst-alpha",
    stream_id: str = "epic:7177",
    session_id: str = "sess-1",
) -> None:
    conn = sqlite3.connect(db)
    conn.execute(
        """
        INSERT INTO stream_leases VALUES (
            ?, ?, 'active', 'claude', 'claude-tools',
            ?, 'task-1', ?, ?, ?
        )
        """,
        (stream_id, session_id, instance_id, holder_host_id, heartbeat, expires),
    )
    conn.commit()
    conn.close()


@pytest.mark.parametrize("holder_host_id", [None, "", "local"])
def test_driver_missing_host_claim_unattributed_bucket(
    tmp_path: Path,
    holder_host_id: str | None,
) -> None:
    db = _driver_lease_db(tmp_path)
    expires = (datetime.now(UTC) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    heartbeat = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    suffix = holder_host_id if holder_host_id is not None else "null"
    instance_id = f"inst-{suffix}"
    _insert_driver_lease(
        db,
        holder_host_id=holder_host_id,
        heartbeat=heartbeat,
        expires=expires,
        instance_id=instance_id,
    )
    attributed, unattributed = collect_mod.collect_driver_workers(db_path=db)
    assert attributed == []
    assert len(unattributed) == 1
    assert unattributed[0].row.id == instance_id
    payload = workers_payload(session_db=db)
    host = _host_by_id(payload, UNATTRIBUTED_HOST_ID)
    assert host["reason"] == "lease has no host claim"
    worker_ids = {row["id"] for row in host["workers"]}
    assert worker_ids == {instance_id}
    assert payload["counts"]["live"] == 1


def test_driver_opaque_host_claim_not_unattributed(tmp_path: Path) -> None:
    db = _driver_lease_db(tmp_path)
    expires = (datetime.now(UTC) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    heartbeat = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    _insert_driver_lease(
        db,
        holder_host_id="host-worker",
        heartbeat=heartbeat,
        expires=expires,
        instance_id="inst-real",
    )
    attributed, unattributed = collect_mod.collect_driver_workers(db_path=db)
    assert unattributed == []
    assert len(attributed) == 1
    assert attributed[0].host_id == "host-worker"
    assert attributed[0].row.id == "inst-real"
    payload = workers_payload(session_db=db)
    assert UNATTRIBUTED_HOST_ID not in {host["host_id"] for host in payload["hosts"]}


def test_driver_local_host_id_fails_without_host_claim_normalization(tmp_path: Path) -> None:
    """Mutation guard: treating 'local' as a real host drops the lease from unattributed."""
    db = _driver_lease_db(tmp_path)
    expires = (datetime.now(UTC) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    heartbeat = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    _insert_driver_lease(
        db,
        holder_host_id="local",
        heartbeat=heartbeat,
        expires=expires,
        instance_id="inst-local",
    )
    _, unattributed = collect_mod.collect_driver_workers(db_path=db)
    assert len(unattributed) == 1
    broken = [item for item in unattributed if item.host_id == "local"]
    assert broken == []


def test_related_links_equal_instance_id(tmp_path: Path) -> None:
    db = tmp_path / "streams.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE sessions (stream_id TEXT, session_id TEXT, state TEXT, PRIMARY KEY (stream_id, session_id));
        CREATE TABLE stream_leases (
            stream_id TEXT, session_id TEXT, state TEXT,
            holder_agent TEXT, holder_harness TEXT, holder_instance_id TEXT,
            holder_task_id TEXT, holder_host_id TEXT, heartbeat_at TEXT, expires_at TEXT
        );
        """
    )
    expires = (datetime.now(UTC) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    heartbeat = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    conn.execute("INSERT INTO sessions VALUES ('epic:1', 's1', 'open')")
    conn.execute(
        "INSERT INTO stream_leases VALUES ('epic:1','s1','active','claude',NULL,'shared-inst','t1','host-worker',?,?)",
        (heartbeat, expires),
    )
    conn.commit()
    conn.close()
    workers = [
        collect_mod.CollectedWorker(
            source="driver",
            row=WorkerRow(
                kind="driver",
                agent="claude",
                harness=None,
                id="shared-inst",
                run_id=None,
                epic="epic:1",
                state="live",
                age_s=1,
            ),
            host_id="host-worker",
            identity=collect_mod.WorkerIdentity("driver", "driver", "shared-inst"),
            instance_id="shared-inst",
            task_id="t1",
        ),
        collect_mod.CollectedWorker(
            source="marker",
            row=WorkerRow(
                kind="service",
                agent="claude",
                harness=None,
                id="svc-1",
                run_id=None,
                epic=None,
                state="live",
                age_s=1,
            ),
            host_id="host-worker",
            identity=collect_mod.WorkerIdentity("marker", "service", "svc-1"),
            instance_id="shared-inst",
            task_id="t1",
        ),
    ]
    collect_mod._related_links(workers, host_id="host-worker")
    assert workers[0].related
    assert workers[1].related


def test_observer_adapter_identity() -> None:
    upsert_presence(PresenceRequest(agent="cursor", task_id="observe-1", status="working", epic="7177"))
    rows = collect_mod.collect_observer_workers()
    assert len(rows) == 1
    assert rows[0].row.id == "cursor"
    assert rows[0].row.seat_model == "single"


def test_marker_kind_normalization(tmp_path: Path) -> None:
    root = tmp_path / "markers"
    root.mkdir()
    payload = {
        "schema": "monitor-occupancy-markers.v1",
        "kind": "foundry",
        "agent": "codex",
        "task_id": "compile-1",
        "epic": None,
        "host_id": "host-worker",
        "updated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
    }
    (root / "foundry-compile-1.json").write_text(json.dumps(payload), encoding="utf-8")
    rows = collect_mod.collect_marker_workers(host_id="host-worker", root=root)
    assert rows[0].row.kind == "service"


def test_workers_opsec_no_sensitive_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setattr(collect_mod, "_self_host_ids", lambda: set())
    loop_client.post("/api/fleet/projects/v1/report", json=_document(workers=[_worker_row()]))
    text = json.dumps(client.get("/api/fleet/workers/v1").json()).lower()
    assert _IP.findall(text) == []
    for alias in _ALIAS_LEAKS:
        assert alias not in text
    assert "run_nonce" not in text
    assert "pid" not in text


def test_workers_payload_warm_cache_skips_delegate_collector(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Warm GET must not re-enter collect_delegate_workers within the TTL window."""
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    now = datetime.now(UTC)
    (tasks / "warm-task.json").write_text(
        json.dumps(
            {
                "task_id": "warm-task",
                "agent": "cursor",
                "status": "running",
                "pid": os.getpid(),
                "started_at": now.isoformat(),
                "run_nonce": "warm-cache-nonce",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setenv("LU_MONITOR_HOST_ID", "host-worker")
    monkeypatch.setattr("scripts.api.delegate_router._tasks_dir", lambda ctx=None: tasks)
    monkeypatch.setattr(collect_mod, "_self_host_ids", lambda: {"host-worker"})
    monkeypatch.setattr(
        collect_mod,
        "collect_job_workers",
        lambda **_kwargs: ([], None),
    )
    monkeypatch.setattr(collect_mod, "collect_marker_workers", lambda **_kwargs: [])
    monkeypatch.setattr(
        collect_mod,
        "read_session_streams",
        lambda **_kwargs: OccupancyRead([], True, 0.0),
    )

    calls = {"delegate": 0}
    real_delegate = collect_mod.collect_delegate_workers

    def _counting_delegate(*args: Any, **kwargs: Any) -> Any:
        calls["delegate"] += 1
        return real_delegate(*args, **kwargs)

    monkeypatch.setattr(collect_mod, "collect_delegate_workers", _counting_delegate)

    first = workers_payload()
    assert calls["delegate"] == 1
    assert any(
        row.get("id") == "warm-task"
        for host in first["hosts"]
        for row in host.get("workers", [])
    )

    t0 = time.perf_counter()
    second = workers_payload()
    warm_s = time.perf_counter() - t0
    assert calls["delegate"] == 1
    assert warm_s < 0.5
    assert second["counts"] == first["counts"]
    assert second["hosts"] == first["hosts"]

    # Fixture overrides must bypass the cache (hermetic collectors).
    third = workers_payload(tasks_dir=tasks)
    assert calls["delegate"] == 2
