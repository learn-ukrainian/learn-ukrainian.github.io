"""Stdlib remote client and CLI output/fail-closed contract."""

from __future__ import annotations

import json
import urllib.error
from pathlib import Path

from agents_extensions.shared.session_streams.model import LeaseHolder
from scripts.session_supervisor import main
from scripts.session_supervisor.remote import RemoteEpicClient, RemoteUnreachableError


class _Response:
    def __init__(self, payload: dict[str, object], status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def _lease_payload() -> dict[str, object]:
    return {
        "stream_id": "epic:7178",
        "session_id": "session-client",
        "lease_id": "lease-client",
        "generation": 1,
        "fencing_token": 1,
        "heartbeat_at": "2026-08-23T00:00:00Z",
        "expires_at": "2026-08-23T00:15:00Z",
        "ttl_seconds": 900,
        "version": 1,
        "holder": {
            "agent": "codex",
            "harness": "codex-cli",
            "instance_id": "client-instance",
            "process_id": 1234,
            "holder_kind": "process",
            "host_id": "client-host",
        },
    }


def test_remote_claim_preflights_health_and_emits_one_json_document(monkeypatch, capsys) -> None:
    calls: list[str] = []

    def opener(request: object, timeout: int = 0) -> _Response:
        del timeout
        path = str(getattr(request, "full_url", "")).split("8765", 1)[-1]
        calls.append(path)
        if path.startswith("/api/epics/v1/health"):
            return _Response({"schema": "remote-epic-lifecycle.v1", "ok": True})
        if path.startswith("/api/epics/v1/epic:7178/claim"):
            return _Response(
                {
                    "schema": "remote-epic-lifecycle.v1",
                    "stream_id": "epic:7178",
                    "lease": _lease_payload(),
                    "digest": {
                        "stream_id": "epic:7178",
                        "limit": 20,
                        "high_water_entry_id": 0,
                        "pinned": [],
                        "recent": [],
                    },
                }
            )
        return _Response(
            {
                "schema": "remote-epic-lifecycle.v1",
                "stream_id": "epic:7178",
                "lease": _lease_payload(),
                "session_state": "open",
                "digest": {"stream_id": "epic:7178", "limit": 20, "high_water_entry_id": 0, "pinned": [], "recent": []},
            }
        )

    monkeypatch.setattr("urllib.request.urlopen", opener)
    assert (
        main(
            [
                "claim",
                "--role",
                "driver",
                "--stream",
                "epic:7178",
                "--agent",
                "codex",
                "--harness",
                "codex-cli",
                "--instance-id",
                "client-instance",
                "--process-id",
                "1234",
                "--host-id",
                "client-host",
                "--lineage-id",
                "client-lineage",
            ]
        )
        == 0
    )
    output = capsys.readouterr()
    assert json.loads(output.out)["schema"] == "session-supervisor-bootstrap.v1"
    assert calls[0].startswith("/api/epics/v1/health")
    assert any(path.startswith("/api/epics/v1/epic:7178/claim") for path in calls)


def test_remote_claim_fail_closed_without_api_and_does_not_post() -> None:
    calls: list[str] = []

    def opener(request: object, timeout: int = 0) -> _Response:
        del timeout
        calls.append(str(getattr(request, "method", "")))
        raise urllib.error.URLError("offline")

    client = RemoteEpicClient(opener=opener)
    try:
        client.claim(
            stream_id="epic:7178",
            holder=LeaseHolder("codex", "codex-cli", "offline", process_id=1, host_id="offline-host"),
            lineage_id="offline-lineage",
        )
    except RemoteUnreachableError:
        pass
    else:  # pragma: no cover - assertion branch
        raise AssertionError("unreachable Monitor API must refuse the claim")
    assert calls == ["GET"]


def test_local_flag_warns_and_keeps_stdout_as_one_json_document(tmp_path: Path, capsys) -> None:
    assert (
        main(
            [
                "--local",
                "--db",
                str(tmp_path / "local.sqlite3"),
                "open",
                "--role",
                "driver",
                "--stream",
                "epic:7178",
                "--agent",
                "codex",
                "--harness",
                "codex-cli",
                "--instance-id",
                "local-instance",
                "--process-id",
                "1234",
                "--lineage-id",
                "local-lineage",
            ]
        )
        == 0
    )
    output = capsys.readouterr()
    assert "LOCAL-ONLY LEASE — not visible to the fleet" in output.err
    json.loads(output.out)
