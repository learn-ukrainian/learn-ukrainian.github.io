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
from agents_extensions.shared.session_streams.inventory import stream_anchor_id
from agents_extensions.shared.session_streams.model import LeaseHolder
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.orchestration import thread_handoff as th
from tests.epics_monitor_stub import epics_app_for_store

# Uploads bind the bundle agent to the lease holder's handoff slot, so they use a
# registered stream and that stream's slot (claude on the infra stream -> claude-infra),
# resolved from issue_streams.yaml so epic succession needs no edit.
REPO_ROOT = Path(__file__).resolve().parents[2]
STREAM = stream_anchor_id("infra-harness", REPO_ROOT)


def _client(tmp_path: Path, monkeypatch) -> TestClient:
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "api.sqlite3"))
    app = epics_app_for_store(store, tmp_path)
    return TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 8765))


def _claim(client: TestClient, *, stream: str = STREAM, agent: str = "claude", suffix: str = "") -> dict:
    response = client.post(
        f"/api/epics/v1/{stream}/claim",
        json={
            "session_id": f"bundle-session{suffix}",
            "lease_id": f"bundle-lease{suffix}",
            "lineage_id": "bundle-lineage",
            "agent": agent,
            "harness": f"{agent}-cli",
            "instance_id": f"bundle-instance{suffix}",
            "process_id": 1234,
            "host_id": "api-host",
            "ttl_seconds": 900,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["lease"]


@pytest.mark.parametrize("field", ["heartbeat_at", "expires_at", "created_at", "updated_at"])
def test_bundle_upload_request_timestamp_conversion_refusal(tmp_path, monkeypatch, field):
    client = _client(tmp_path, monkeypatch)
    lease = _claim(client)
    manifest, blob = _bundle(rollover_id="rollover-timestamp", body=b"packet\n")
    lease[field] = "9999-12-31T23:59:59-23:59"
    response = _post(client, lease, manifest, blob)
    assert response.status_code == 400
    assert response.json() == {
        "schema": "remote-epic-lifecycle.v1",
        "error": "request_refused",
        "detail": "invalid rollover bundle upload request",
    }
    assert client.get(f"/api/epics/v1/{STREAM}/bundles").json()["bundles"] == []


def _bundle(
    *,
    rollover_id: str,
    body: bytes,
    agent: str = "claude-infra",
    status: str = "pending_start",
    prepared_at: str = "2026-08-24T16:00:00Z",
    lineage_id: str = "bundle-lineage",
    generation: int = 3,
    stream: str = STREAM,
    extra: dict[str, bytes] | None = None,
) -> tuple[dict, bytes]:
    name = f".agent/thread-rollovers/{agent}/{lineage_id}/generation-{generation:04d}/{rollover_id}/handoff.md"
    members = {name: body, **(extra or {})}
    manifest = {
        "schema": "rollover-bundle.v1",
        "agent": agent,
        "stream_id": stream,
        "lineage_id": lineage_id,
        "rollover_id": rollover_id,
        "generation": generation,
        "status": status,
        "prepared_at": prepared_at,
        "source_root": "{{REPO_ROOT}}",
        "exported_at": "2026-08-24T16:00:00Z",
        "files": [
            {
                "path": path,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "tokenized": th._bundle_text_member(path),
            }
            for path, payload in sorted(members.items())
        ],
        "tokenized_members": sorted(path for path in members if th._bundle_text_member(path)),
        "upload_seq": 0,
        "bundle_sha256": "",
    }
    manifest["bundle_sha256"] = th._bundle_digest(members, manifest)
    return manifest, th._bundle_archive(members, manifest)


def _post(client: TestClient, lease: dict, manifest: dict, blob: bytes, *, stream: str = STREAM):
    return client.post(
        f"/api/epics/v1/{stream}/bundles",
        json={**lease, "manifest": manifest, "blob": base64.b64encode(blob).decode("ascii")},
    )


@pytest.mark.parametrize("error_type", [MemoryError, RuntimeError, OSError])
def test_bundle_validator_operational_failure_remains_unavailable(tmp_path, monkeypatch, error_type):
    client = _client(tmp_path, monkeypatch)
    lease = _claim(client)
    manifest, blob = _bundle(rollover_id="rollover-api1", body=b"safe handoff\n")

    def unavailable(_manifest):
        raise error_type("bundle-supplied-sentinel")

    monkeypatch.setattr(th, "_bundle_require_json_value", unavailable)
    response = _post(client, lease, manifest, blob)
    assert response.status_code == 503
    assert response.json()["detail"] == "Monitor session-stream store unavailable"
    assert "bundle-supplied-sentinel" not in response.text
    assert client.get(f"/api/epics/v1/{STREAM}/bundles").json()["bundles"] == []


def test_bundle_upload_list_latest_idempotency_and_secret_refusal(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    lease = _claim(client)
    manifest, blob = _bundle(rollover_id="rollover-api1", body=b"safe handoff\n")
    request = {**lease, "manifest": manifest, "blob": base64.b64encode(blob).decode("ascii")}

    uploaded = client.post(f"/api/epics/v1/{STREAM}/bundles", json=request)
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["upload_seq"] == 1
    replay = client.post(f"/api/epics/v1/{STREAM}/bundles", json=request)
    assert replay.status_code == 200
    assert replay.json()["upload_seq"] == 1

    listed = client.get(f"/api/epics/v1/{STREAM}/bundles", params={"agent": "claude-infra"})
    assert listed.status_code == 200
    assert len(listed.json()["bundles"]) == 1
    assert "blob" not in listed.json()["bundles"][0]

    latest = client.get(f"/api/epics/v1/{STREAM}/bundles/latest", params={"agent": "claude-infra"})
    assert latest.status_code == 200
    assert latest.json()["manifest"]["upload_seq"] == 1
    assert base64.b64decode(latest.json()["blob"]) == blob

    by_sequence = client.get(f"/api/epics/v1/{STREAM}/bundles/1")
    assert by_sequence.status_code == 200
    assert by_sequence.json()["manifest"]["upload_seq"] == 1
    assert base64.b64decode(by_sequence.json()["blob"]) == blob
    missing_sequence = client.get(f"/api/epics/v1/{STREAM}/bundles/99")
    assert missing_sequence.status_code == 404

    secret_manifest, secret_blob = _bundle(
        rollover_id="rollover-api2",
        body=b"api-key: secret-value\n",
    )
    secret_response = client.post(
        f"/api/epics/v1/{STREAM}/bundles",
        json={**lease, "manifest": secret_manifest, "blob": base64.b64encode(secret_blob).decode("ascii")},
    )
    assert secret_response.status_code == 400


def test_bundle_latest_without_agent_selects_highest_order_across_agents(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

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
    # Each provider publishes only its own slot, so each upload runs under its own lease.
    for index, (holder, manifest, blob) in enumerate(
        (("grok", own_manifest, own_blob), ("claude", foreign_manifest, foreign_blob))
    ):
        lease = _claim(client, agent=holder, suffix=f"-{index}")
        response = _post(client, lease, manifest, blob)
        assert response.status_code == 200, response.text
        released = client.post(f"/api/epics/v1/{STREAM}/release", json=lease)
        assert released.status_code == 200, released.text

    latest = client.get(f"/api/epics/v1/{STREAM}/bundles/latest")
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
    pending = client.post(f"/api/epics/v1/{STREAM}/bundles", json=pending_request)
    assert pending.status_code == 200
    assert pending.json()["upload_seq"] == 1

    started_manifest, started_blob = _bundle(
        rollover_id="rollover-evolve",
        body=b"pending\n",
        status="started",
    )
    started = client.post(
        f"/api/epics/v1/{STREAM}/bundles",
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
        f"/api/epics/v1/{STREAM}/bundles",
        json={
            **lease,
            "manifest": contradiction_manifest,
            "blob": base64.b64encode(contradiction_blob).decode("ascii"),
        },
    )
    assert contradiction.status_code == 409

    latest = client.get(
        f"/api/epics/v1/{STREAM}/bundles/latest",
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
        f"/api/epics/v1/{STREAM}/bundles",
        json={**lease, "manifest": {}, "blob": base64.b64encode(b"x" * (4 * 1024 * 1024 + 1)).decode("ascii")},
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    ("stream_key", "holder", "agent", "accepted"),
    [
        ("infra-harness", "claude", "claude-infra", True),
        ("infra-harness", "claude", "claude-devops", False),
        ("infra-harness", "claude", "grok-infra", False),
        ("devops", "claude", "claude-devops", True),
        ("devops", "claude", "claude-infra", False),
        ("curriculum-upgrade", "claude", "claude-core", True),
        ("curriculum-upgrade", "claude", "claude-curriculum-upgrade", False),
    ],
)
def test_bundle_upload_binds_agent_to_holder_slot_for_the_stream(
    tmp_path: Path, monkeypatch, stream_key: str, holder: str, agent: str, accepted: bool
) -> None:
    stream = stream_anchor_id(stream_key, REPO_ROOT)
    client = _client(tmp_path, monkeypatch)
    lease = _claim(client, stream=stream, agent=holder)
    manifest, blob = _bundle(rollover_id="rollover-slot", body=b"slot packet\n", agent=agent, stream=stream)

    response = _post(client, lease, manifest, blob, stream=stream)

    assert response.status_code == (200 if accepted else 400), response.text
    listed = client.get(f"/api/epics/v1/{stream}/bundles")
    assert listed.status_code == 200, listed.text
    assert len(listed.json()["bundles"]) == (1 if accepted else 0)


@pytest.mark.parametrize(
    "extra",
    [
        "README.md",
        "scripts/start-example-launcher.sh",
        ".claude/infra-epic/notes.sh",
        ".git/config",
        ".claude/other-epic/CLAUDE-DRIVER-HANDOFF.md",
        "docs/session-state/current.md",
        ".claude/infra-epic/CLAUDE-DRIVER-HANDOFF.md.bak",
        ".agent/thread-rollovers/claude-infra/bundle-lineage-extra/lease.json",
    ],
)
def test_bundle_upload_with_member_outside_lineage_and_handoffs_leaves_no_row(
    tmp_path: Path, monkeypatch, extra: str
) -> None:
    client = _client(tmp_path, monkeypatch)
    lease = _claim(client)
    manifest, blob = _bundle(rollover_id="rollover-extra", body=b"packet\n", extra={extra: b"extra\n"})

    response = _post(client, lease, manifest, blob)

    assert response.status_code == 400, response.text
    listed = client.get(f"/api/epics/v1/{STREAM}/bundles")
    assert listed.status_code == 200, listed.text
    assert listed.json()["bundles"] == []


def test_bundle_upload_with_every_own_handoff_candidate_is_accepted(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    lease = _claim(client)
    candidates = th._bundle_handoff_candidates_for_agent(REPO_ROOT, STREAM, "claude-infra")
    assert len(candidates) >= 3
    manifest, blob = _bundle(
        rollover_id="rollover-candidates",
        body=b"packet\n",
        extra={candidate: f"handoff {candidate}\n".encode() for candidate in candidates},
    )

    response = _post(client, lease, manifest, blob)

    assert response.status_code == 200, response.text
    listed = client.get(f"/api/epics/v1/{STREAM}/bundles", params={"agent": "claude-infra"})
    assert len(listed.json()["bundles"]) == 1
