"""Loopback API contract for cross-host rollover bundle storage."""

from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import LeaseHolder
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api import epics_router
from scripts.orchestration import thread_handoff as th
from tests.epics_monitor_stub import epics_app_for_store


def _client(tmp_path: Path, monkeypatch) -> TestClient:
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "api.sqlite3"))
    app = epics_app_for_store(store, tmp_path)
    return TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 8765))


def _claim(client: TestClient) -> dict:
    response = client.post(
        "/api/epics/v1/epic:7178/claim",
        json={
            "session_id": "bundle-session",
            "lease_id": "bundle-lease",
            "lineage_id": "bundle-lineage",
            "agent": "codex",
            "harness": "codex-cli",
            "instance_id": "bundle-instance",
            "process_id": 1234,
            "host_id": "api-host",
            "ttl_seconds": 900,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["lease"]


def _bundle(
    *,
    rollover_id: str,
    body: bytes,
    agent: str = "claude-infra",
    status: str = "pending_start",
    prepared_at: str = "2026-08-24T16:00:00Z",
    lineage_id: str = "bundle-lineage",
    generation: int = 3,
) -> tuple[dict, bytes]:
    name = f".agent/thread-rollovers/{agent}/{lineage_id}/generation-{generation:04d}/{rollover_id}/handoff.md"
    members = {name: body}
    manifest = {
        "schema": "rollover-bundle.v1",
        "agent": agent,
        "stream_id": "epic:7178",
        "lineage_id": lineage_id,
        "rollover_id": rollover_id,
        "generation": generation,
        "status": status,
        "prepared_at": prepared_at,
        "source_root": "{{REPO_ROOT}}",
        "exported_at": "2026-08-24T16:00:00Z",
        "files": [
            {
                "path": name,
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
                "tokenized": True,
            }
        ],
        "tokenized_members": [name],
        "upload_seq": 0,
        "bundle_sha256": "",
    }
    manifest["bundle_sha256"] = th._bundle_digest(members, manifest)
    return manifest, th._bundle_archive(members, manifest)


def test_bundle_upload_list_latest_idempotency_and_secret_refusal(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    lease = _claim(client)
    manifest, blob = _bundle(rollover_id="rollover-api1", body=b"safe handoff\n")
    request = {**lease, "manifest": manifest, "blob": base64.b64encode(blob).decode("ascii")}

    uploaded = client.post("/api/epics/v1/epic:7178/bundles", json=request)
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["upload_seq"] == 1
    replay = client.post("/api/epics/v1/epic:7178/bundles", json=request)
    assert replay.status_code == 200
    assert replay.json()["upload_seq"] == 1

    listed = client.get("/api/epics/v1/epic:7178/bundles", params={"agent": "claude-infra"})
    assert listed.status_code == 200
    assert len(listed.json()["bundles"]) == 1
    assert "blob" not in listed.json()["bundles"][0]

    latest = client.get("/api/epics/v1/epic:7178/bundles/latest", params={"agent": "claude-infra"})
    assert latest.status_code == 200
    assert latest.json()["manifest"]["upload_seq"] == 1
    assert base64.b64decode(latest.json()["blob"]) == blob

    by_sequence = client.get("/api/epics/v1/epic:7178/bundles/1")
    assert by_sequence.status_code == 200
    assert by_sequence.json()["manifest"]["upload_seq"] == 1
    assert base64.b64decode(by_sequence.json()["blob"]) == blob
    missing_sequence = client.get("/api/epics/v1/epic:7178/bundles/99")
    assert missing_sequence.status_code == 404

    secret_manifest, secret_blob = _bundle(
        rollover_id="rollover-api2",
        body=b"api-key: secret-value\n",
    )
    secret_response = client.post(
        "/api/epics/v1/epic:7178/bundles",
        json={**lease, "manifest": secret_manifest, "blob": base64.b64encode(secret_blob).decode("ascii")},
    )
    assert secret_response.status_code == 400


def test_bundle_latest_without_agent_selects_highest_order_across_agents(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    lease = _claim(client)

    own_manifest, own_blob = _bundle(
        rollover_id="rollover-grok-newer",
        body=b"grok packet\n",
        agent="grok-infra",
        lineage_id="grok-lineage",
        generation=4,
    )
    foreign_manifest, foreign_blob = _bundle(
        rollover_id="rollover-claude-older",
        body=b"claude packet\n",
        agent="claude-infra",
        lineage_id="claude-lineage",
        generation=3,
    )
    for manifest, blob in ((own_manifest, own_blob), (foreign_manifest, foreign_blob)):
        response = client.post(
            "/api/epics/v1/epic:7178/bundles",
            json={**lease, "manifest": manifest, "blob": base64.b64encode(blob).decode("ascii")},
        )
        assert response.status_code == 200, response.text

    latest = client.get("/api/epics/v1/epic:7178/bundles/latest")
    assert latest.status_code == 200, latest.text
    assert latest.json()["manifest"]["agent"] == "grok-infra"
    assert latest.json()["manifest"]["generation"] == 4
    assert latest.json()["manifest"]["upload_seq"] == 1


def test_bundle_upload_allows_status_evolution_and_rejects_same_tuple_contradiction(
    tmp_path: Path, monkeypatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    lease = _claim(client)
    pending_manifest, pending_blob = _bundle(rollover_id="rollover-evolve", body=b"pending\n")
    pending_request = {
        **lease,
        "manifest": pending_manifest,
        "blob": base64.b64encode(pending_blob).decode("ascii"),
    }
    pending = client.post("/api/epics/v1/epic:7178/bundles", json=pending_request)
    assert pending.status_code == 200
    assert pending.json()["upload_seq"] == 1

    started_manifest, started_blob = _bundle(
        rollover_id="rollover-evolve",
        body=b"pending\n",
        status="started",
    )
    started = client.post(
        "/api/epics/v1/epic:7178/bundles",
        json={
            **lease,
            "manifest": started_manifest,
            "blob": base64.b64encode(started_blob).decode("ascii"),
        },
    )
    assert started.status_code == 200, started.text
    assert started.json()["upload_seq"] == 2

    contradiction_manifest, contradiction_blob = _bundle(
        rollover_id="rollover-evolve",
        body=b"different\n",
    )
    contradiction = client.post(
        "/api/epics/v1/epic:7178/bundles",
        json={
            **lease,
            "manifest": contradiction_manifest,
            "blob": base64.b64encode(contradiction_blob).decode("ascii"),
        },
    )
    assert contradiction.status_code == 409

    latest = client.get(
        "/api/epics/v1/epic:7178/bundles/latest",
        params={"agent": "claude-infra", "lineage_id": "bundle-lineage"},
    )
    assert latest.status_code == 200
    assert latest.json()["manifest"]["status"] == "started"
    assert latest.json()["manifest"]["upload_seq"] == 2


def test_rollover_schema_has_both_unique_indexes_and_raw_digest_constraint(
    tmp_path: Path,
) -> None:
    database = SessionStreamDatabase(tmp_path / "api.sqlite3")
    store = SessionStreamStore(database)
    lease = store.open_session(
        stream_id="epic:7178",
        holder=LeaseHolder(agent="codex", harness="codex-cli", instance_id="raw", process_id=1234),
        lineage_id="raw-lineage",
        ttl_seconds=900,
    )
    connection = database.connect()
    try:
        unique_indexes = {
            str(row[1])
            for row in connection.execute("PRAGMA index_list('rollover_bundles')").fetchall()
            if int(row[2]) == 1
        }
        assert "rollover_bundles_bundle_sha256_unique" in unique_indexes
        assert "rollover_bundles_identity_unique" in unique_indexes
        foreign_keys = {
            (str(row[2]), str(row[3]), str(row[4]))
            for row in connection.execute("PRAGMA foreign_key_list('rollover_bundles')").fetchall()
        }
        assert foreign_keys == {("streams", "stream_id", "stream_id")}

        manifest_json = json.dumps(
            {
                "schema": "rollover-bundle.v1",
                "status": "pending_start",
                "prepared_at": "2026-08-24T16:00:00Z",
            }
        )
        row = (
            "epic:7178",
            "claude-infra",
            "raw-lineage",
            3,
            "rollover-raw-a",
            "pending_start",
            "2026-08-24T16:00:00Z",
            "a" * 64,
            manifest_json,
            b"raw",
            "2026-08-24T16:00:00Z",
            lease.lease_id,
        )
        columns = (
            "stream_id, agent, lineage_id, generation, rollover_id, status, prepared_at, "
            "bundle_sha256, manifest_json, blob, uploaded_at, uploaded_by_lease_id"
        )
        connection.execute(f"INSERT INTO rollover_bundles({columns}) VALUES ({','.join('?' for _ in row)})", row)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                f"INSERT INTO rollover_bundles({columns}) VALUES ({','.join('?' for _ in row)})",
                (*row[:4], "rollover-raw-b", *row[5:]),
            )
    finally:
        connection.close()


def test_claim_replaces_released_lease_with_historical_bundle_token(tmp_path: Path) -> None:
    database = SessionStreamDatabase(tmp_path / "reclaim.sqlite3")
    store = SessionStreamStore(database)
    base_time = datetime(2026, 8, 25, 10, 0, tzinfo=UTC)
    old_lease, _ = store.claim_remote_session(
        stream_id="epic:7178",
        holder=LeaseHolder(agent="claude", harness="claude-cli", instance_id="old", process_id=1234),
        lineage_id="historical-lineage",
        ttl_seconds=900,
        session_id="historical-session",
        lease_id="historical-lease",
        now=base_time,
    )
    store.release_remote_session(old_lease, now=base_time + timedelta(seconds=1))

    connection = database.connect()
    try:
        connection.execute(
            "INSERT INTO rollover_bundles("
            "stream_id, agent, lineage_id, generation, rollover_id, status, prepared_at, "
            "bundle_sha256, manifest_json, blob, uploaded_at, uploaded_by_lease_id"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "epic:7178",
                "claude-infra",
                "historical-lineage",
                1,
                "historical-rollover",
                "pending_start",
                "2026-08-25T10:00:00Z",
                "a" * 64,
                json.dumps({"status": "pending_start", "prepared_at": "2026-08-25T10:00:00Z"}),
                b"historical bundle",
                "2026-08-25T10:00:00Z",
                old_lease.lease_id,
            ),
        )
    finally:
        connection.close()

    successor, outcome = store.claim_remote_session(
        stream_id="epic:7178",
        holder=LeaseHolder(agent="grok", harness="grok-cli", instance_id="new", process_id=5678),
        lineage_id="successor-lineage",
        ttl_seconds=900,
        session_id="successor-session",
        lease_id="successor-lease",
        now=base_time + timedelta(seconds=2),
    )

    assert successor.lease_id == "successor-lease"
    assert outcome in {"claimed", "recovered"}
    with database.connect(read_only=True) as connection:
        bundle = connection.execute(
            "SELECT uploaded_by_lease_id FROM rollover_bundles WHERE rollover_id = ?",
            ("historical-rollover",),
        ).fetchone()
    assert bundle["uploaded_by_lease_id"] == old_lease.lease_id


def test_bundle_upload_enforces_four_mib_cap(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    lease = _claim(client)
    response = client.post(
        "/api/epics/v1/epic:7178/bundles",
        json={**lease, "manifest": {}, "blob": base64.b64encode(b"x" * (4 * 1024 * 1024 + 1)).decode("ascii")},
    )
    assert response.status_code == 400
