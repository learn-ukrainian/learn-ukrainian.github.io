"""Loopback API contract for cross-host rollover bundle storage."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api import epics_router
from scripts.orchestration import thread_handoff as th


def _client(tmp_path: Path, monkeypatch) -> TestClient:
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "api.sqlite3"))
    monkeypatch.setattr(epics_router, "_store", lambda: store)
    app = FastAPI()
    app.include_router(epics_router.router, prefix="/api/epics")
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


def _bundle(*, rollover_id: str, body: bytes) -> tuple[dict, bytes]:
    name = ".agent/thread-rollovers/claude-infra/bundle-lineage/generation-0003/" + rollover_id + "/handoff.md"
    members = {name: body}
    manifest = {
        "schema": "rollover-bundle.v1",
        "agent": "claude-infra",
        "stream_id": "epic:7178",
        "lineage_id": "bundle-lineage",
        "rollover_id": rollover_id,
        "generation": 3,
        "status": "pending_start",
        "prepared_at": "2026-08-24T16:00:00Z",
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

    secret_manifest, secret_blob = _bundle(
        rollover_id="rollover-api2",
        body=b"api-key: secret-value\n",
    )
    secret_response = client.post(
        "/api/epics/v1/epic:7178/bundles",
        json={**lease, "manifest": secret_manifest, "blob": base64.b64encode(secret_blob).decode("ascii")},
    )
    assert secret_response.status_code == 400


def test_bundle_upload_enforces_four_mib_cap(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    lease = _claim(client)
    response = client.post(
        "/api/epics/v1/epic:7178/bundles",
        json={**lease, "manifest": {}, "blob": base64.b64encode(b"x" * (4 * 1024 * 1024 + 1)).decode("ascii")},
    )
    assert response.status_code == 400
