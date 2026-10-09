"""Snapshot sources for fleet board v1. Fixture files only, no network."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

import scripts.api.fleet_board.router as board_routes
from scripts.api import main as api_main
from scripts.api.fleet_board import cache as cache_mod
from scripts.api.fleet_board import file_sources, values
from scripts.api.fleet_board import sources as sources_mod
from scripts.api.fleet_board.cache import CACHE

client = TestClient(api_main.app, raise_server_exceptions=False)

_WHEN = datetime(2026, 10, 9, 10, 0, 0, tzinfo=UTC)
_APPROVED = {"alpha": "alpha", "beta": "beta", "gamma": "gamma"}


@pytest.fixture(autouse=True)
def _isolated(monkeypatch: pytest.MonkeyPatch):
    CACHE.clear()
    for name in sources_mod.LOCATION_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("FLEET_DOWNLOAD_STALL_MIN", raising=False)
    monkeypatch.setattr(file_sources, "DOWNLOAD_ALIASES", _APPROVED)
    monkeypatch.setattr(file_sources, "DRIVER_ALIASES", _APPROVED)
    yield
    CACHE.clear()


def _validate(body: dict) -> None:
    document = client.get("/api/fleet/v1/schema").json()["data"]["endpoints"][body["schema"]]
    Draft202012Validator(document).validate(body)


def _source(body: dict) -> dict:
    assert len(body["sources"]) == 1
    return body["sources"][0]


def _write(directory, name: str, payload: dict) -> None:
    (directory / name).write_text(json.dumps(payload), encoding="utf-8")


def test_unset_snapshot_sources_are_not_configured() -> None:
    paths = (
        ("/api/fleet/v1/backups", "backups", "fleet.v1.backups"),
        ("/api/fleet/v1/downloads", "downloads", "fleet.v1.downloads"),
        ("/api/fleet/v1/harness", "harness_snapshot", "fleet.v1.harness"),
        ("/api/fleet/v1/harness/alpha", "harness_snapshot", "fleet.v1.harness_driver"),
    )
    for path, source, schema in paths:
        response = client.get(path)
        assert response.status_code == 200
        body = response.json()
        assert body["schema"] == schema
        assert _source(body) == {"name": source, "status": "not_configured", "age_s": None, "error": None}
        _validate(body)


def test_loader_bug_stays_http_200(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode():
        raise RuntimeError("boom-token")

    monkeypatch.setattr(board_routes, "load_backups", explode)
    response = client.get("/api/fleet/v1/backups")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["last_result"] is None
    assert _source(body)["status"] == "unavailable"
    assert "boom-token" not in response.text


def test_backups_ok_drops_extra_fields(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(
        tmp_path,
        "last-success.json",
        {"at": "2026-10-09T00:00:00Z", "status": "ok", "bytes": "capacity-token", "path": "archive-token"},
    )
    _write(tmp_path, "freshness.json", {"age_h": 36})
    _write(tmp_path, "receipt.json", {"at": "2026-10-09T01:00:00Z", "ok": True, "path": "archive-token"})
    monkeypatch.setenv("FLEET_BACKUP_STATE_DIR", str(tmp_path))
    response = client.get("/api/fleet/v1/backups")
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert _source(body)["status"] == "ok"
    assert _source(body)["age_s"] == 129600
    assert body["data"] == {
        "age_h": 36,
        "stale": False,
        "last_result": {"at": "2026-10-09T00:00:00Z", "status": "ok"},
        "restore_test": {"at": "2026-10-09T01:00:00Z", "ok": True},
    }
    assert "capacity-token" not in response.text
    assert "archive-token" not in response.text
    assert str(tmp_path) not in response.text


def test_backups_older_than_the_window_are_stale(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, "last-success.json", {"at": "2026-10-07T00:00:00Z", "status": "failed"})
    _write(tmp_path, "freshness.json", {"age_h": 40})
    _write(tmp_path, "receipt.json", {"at": "2026-10-07T02:00:00Z", "ok": False})
    monkeypatch.setenv("FLEET_BACKUP_STATE_DIR", str(tmp_path))
    response = client.get("/api/fleet/v1/backups")
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert _source(body)["status"] == "stale"
    assert body["data"]["stale"] is True
    assert body["data"]["age_h"] == 40
    assert body["data"]["last_result"]["status"] == "failed"
    assert body["data"]["restore_test"]["ok"] is False


def test_missing_backup_file_is_unavailable(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, "freshness.json", {"age_h": 2})
    _write(tmp_path, "receipt.json", {"at": "2026-10-09T01:00:00Z", "ok": True})
    monkeypatch.setenv("FLEET_BACKUP_STATE_DIR", str(tmp_path))
    response = client.get("/api/fleet/v1/backups")
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert _source(body)["status"] == "unavailable"
    assert body["data"]["last_result"] is None
    assert body["data"]["age_h"] == 2
    assert body["data"]["restore_test"]["ok"] is True
    assert str(tmp_path) not in response.text


def test_failed_backup_refresh_serves_cache_as_stale(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "state"
    state.mkdir()
    _write(state, "last-success.json", {"at": "2026-10-09T00:00:00Z", "status": "ok"})
    _write(state, "freshness.json", {"age_h": 1})
    _write(state, "receipt.json", {"at": "2026-10-09T01:00:00Z", "ok": True})
    monkeypatch.setenv("FLEET_BACKUP_STATE_DIR", str(state))
    first = client.get("/api/fleet/v1/backups")
    assert first.status_code == 200
    assert _source(first.json())["status"] == "ok"
    for child in state.iterdir():
        child.unlink()
    state.rmdir()
    state.write_text("x", encoding="utf-8")
    monkeypatch.setattr(values, "CACHE_TTL_S", 0)
    second = client.get("/api/fleet/v1/backups")
    assert second.status_code == 200
    assert _source(second.json())["status"] == "stale"
    assert second.json()["data"]["last_result"]["status"] == "ok"
    assert str(tmp_path) not in second.text


def test_downloads_stall_and_skip_unsafe_names(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(file_sources, "_now", lambda: _WHEN)
    payload = {
        "items": [
            {
                "source": "alpha",
                "state": "Running",
                "done": 1,
                "total": 4,
                "last_progress_at": "2026-10-09T09:30:00Z",
            },
            {
                "source": "beta",
                "state": "running",
                "done": 1,
                "total": 4,
                "last_progress_at": "2026-10-09T09:50:00Z",
            },
            {"source": "gamma", "state": "queued", "done": 0, "total": 2},
            {"source": "archive-token/hidden", "state": "running", "done": 1, "total": 1},
        ]
    }
    target = tmp_path / "status.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("FLEET_DOWNLOAD_STATUS", str(target))
    response = client.get("/api/fleet/v1/downloads")
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert _source(body)["status"] == "ok"
    assert body["data"]["state"] == "ok"
    rows = {item["source"]: item for item in body["data"]["items"]}
    assert rows["alpha"]["stalled"] is True
    assert rows["alpha"]["pct"] == 25
    assert rows["alpha"]["state"] == "running"
    assert rows["beta"]["stalled"] is False
    assert rows["gamma"]["stalled"] is None
    assert rows["gamma"]["done"] == 0
    assert rows["gamma"]["pct"] == 0
    assert set(rows) == {"alpha", "beta", "gamma", "unlisted"}
    assert rows["unlisted"]["done"] == 1
    assert "archive-token" not in response.text
    assert str(tmp_path) not in response.text


def test_unreadable_downloads_are_unknown(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "status.json"
    target.write_text("{", encoding="utf-8")
    monkeypatch.setenv("FLEET_DOWNLOAD_STATUS", str(target))
    response = client.get("/api/fleet/v1/downloads")
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert body["data"] == {"state": "unknown", "items": []}
    assert _source(body)["status"] == "unavailable"
    assert str(tmp_path) not in response.text


def test_harness_missing_fields_stay_null(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "measured_at": "2026-10-09T09:00:00Z",
        "drivers": [
            {"agent_id": "alpha"},
            {
                "agent_id": "beta",
                "context_pct": 0,
                "compactions": 0,
                "stop_count": 0,
                "ask_count": 0,
                "idle_min": 0,
            },
        ],
    }
    target = tmp_path / "harness.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("FLEET_HARNESS_SNAPSHOT", str(target))
    response = client.get("/api/fleet/v1/harness")
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert _source(body)["status"] == "ok"
    alpha, beta = body["data"]["drivers"]
    assert alpha["context_pct"] is None
    assert alpha["compactions"] is None
    assert alpha["stop_count"] is None
    assert alpha["ask_count"] is None
    assert alpha["idle_min"] is None
    assert alpha["measured_at"] == "2026-10-09T09:00:00Z"
    assert beta["context_pct"] == 0
    assert beta["compactions"] == 0
    assert beta["stop_count"] == 0
    assert beta["ask_count"] == 0
    assert beta["idle_min"] == 0
    one = client.get("/api/fleet/v1/harness/alpha")
    missing = client.get("/api/fleet/v1/harness/not-in-snapshot")
    assert one.status_code == missing.status_code == 200
    _validate(one.json())
    _validate(missing.json())
    assert one.json()["data"]["driver"]["agent_id"] == "alpha"
    assert one.json()["data"]["driver"]["idle_min"] is None
    assert missing.json()["data"]["driver"] is None
    assert _source(missing.json())["status"] == "ok"
    assert "not-in-snapshot" not in missing.text
    assert str(tmp_path) not in response.text


def _address() -> str:
    return ":".join(("2001", "db8", "0", "0", "0", "0", "0", "17"))


def _dotted() -> str:
    return ".".join(("198", "51", "100", "7"))


def test_cached_backup_age_advances_during_an_outage(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = {"now": 1_000.0}
    monkeypatch.setattr(cache_mod.time, "monotonic", lambda: clock["now"])
    state = tmp_path / "state"
    state.mkdir()
    _write(state, "last-success.json", {"at": "2026-10-09T00:00:00Z", "status": "ok"})
    _write(state, "freshness.json", {"age_h": 1})
    _write(state, "receipt.json", {"at": "2026-10-09T01:00:00Z", "ok": True})
    monkeypatch.setenv("FLEET_BACKUP_STATE_DIR", str(state))
    first = client.get("/api/fleet/v1/backups")
    assert _source(first.json())["status"] == "ok"
    assert first.json()["data"]["age_h"] == 1
    assert first.json()["data"]["stale"] is False
    for child in state.iterdir():
        child.unlink()
    state.rmdir()
    state.write_text("x", encoding="utf-8")
    clock["now"] += 48 * 3600
    second = client.get("/api/fleet/v1/backups")
    assert second.status_code == 200
    body = second.json()
    _validate(body)
    assert _source(body)["status"] == "stale"
    assert body["data"]["age_h"] == 49
    assert body["data"]["stale"] is True
    assert body["data"]["last_result"]["status"] == "ok"
    assert str(tmp_path) not in second.text


def test_cached_download_stall_advances_during_an_outage(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    moment = {"now": _WHEN}
    monkeypatch.setattr(file_sources, "_now", lambda: moment["now"])
    payload = {
        "items": [
            {"source": "beta", "state": "running", "done": 1, "total": 4, "last_progress_at": "2026-10-09T09:50:00Z"}
        ]
    }
    target = tmp_path / "status.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("FLEET_DOWNLOAD_STATUS", str(target))
    first = client.get("/api/fleet/v1/downloads")
    assert first.json()["data"]["items"][0]["stalled"] is False
    target.write_text("{", encoding="utf-8")
    moment["now"] = _WHEN + timedelta(hours=2)
    monkeypatch.setattr(values, "CACHE_TTL_S", 0)
    second = client.get("/api/fleet/v1/downloads")
    assert second.status_code == 200
    body = second.json()
    _validate(body)
    assert _source(body)["status"] == "stale"
    assert body["data"]["items"][0]["stalled"] is True
    assert body["data"]["items"][0]["source"] == "beta"
    assert str(tmp_path) not in second.text


def test_snapshot_ids_stay_plain_identifiers(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    marker = "leak-token"
    host = f"{marker}.example"
    address = _address()
    dotted = _dotted()
    downloads = {
        "items": [
            {"source": "alpha", "state": "running", "done": 1, "total": 2, "last_progress_at": "2026-10-09T09:50:00Z"},
            {"source": host, "state": "running", "done": 1, "total": 2},
            {"source": address, "state": "running", "done": 1, "total": 2},
            {"source": dotted, "state": "running", "done": 1, "total": 2},
        ]
    }
    harness = {
        "drivers": [
            {"agent_id": "alpha", "idle_min": 1},
            {"agent_id": host, "idle_min": 1},
            {"agent_id": address, "idle_min": 1},
            {"agent_id": dotted, "idle_min": 1},
        ]
    }
    status = tmp_path / "status.json"
    snapshot = tmp_path / "harness.json"
    status.write_text(json.dumps(downloads), encoding="utf-8")
    snapshot.write_text(json.dumps(harness), encoding="utf-8")
    monkeypatch.setattr(file_sources, "_now", lambda: _WHEN)
    monkeypatch.setenv("FLEET_DOWNLOAD_STATUS", str(status))
    monkeypatch.setenv("FLEET_HARNESS_SNAPSHOT", str(snapshot))
    downloaded = client.get("/api/fleet/v1/downloads")
    listed = client.get("/api/fleet/v1/harness")
    missing = client.get("/api/fleet/v1/harness/" + host)
    assert downloaded.status_code == listed.status_code == missing.status_code == 200
    _validate(downloaded.json())
    _validate(listed.json())
    _validate(missing.json())
    assert [item["source"] for item in downloaded.json()["data"]["items"]] == [
        "alpha",
        "unlisted",
        "unlisted",
        "unlisted",
    ]
    assert [row["agent_id"] for row in listed.json()["data"]["drivers"]] == [
        "alpha",
        "unlisted",
        "unlisted",
        "unlisted",
    ]
    assert missing.json()["data"]["driver"] is None
    for response in (downloaded, listed, missing):
        assert marker not in response.text
        assert address not in response.text
        assert dotted not in response.text
        assert str(tmp_path) not in response.text


def test_unreadable_receipt_refresh_serves_cached_backups_as_stale(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "state"
    state.mkdir()
    _write(state, "last-success.json", {"at": "2026-10-09T00:00:00Z", "status": "ok"})
    _write(state, "freshness.json", {"age_h": 1})
    _write(state, "receipt.json", {"at": "2026-10-09T01:00:00Z", "ok": True})
    monkeypatch.setenv("FLEET_BACKUP_STATE_DIR", str(state))
    first = client.get("/api/fleet/v1/backups")
    assert _source(first.json())["status"] == "ok"
    (state / "receipt.json").write_text("{", encoding="utf-8")
    monkeypatch.setattr(values, "CACHE_TTL_S", 0)
    second = client.get("/api/fleet/v1/backups")
    assert second.status_code == 200
    body = second.json()
    _validate(body)
    assert _source(body)["status"] == "stale"
    assert body["data"]["restore_test"] == {"at": "2026-10-09T01:00:00Z", "ok": True}
    assert body["data"]["last_result"]["status"] == "ok"
    assert str(tmp_path) not in second.text


@pytest.mark.parametrize("raw", ["null", "[]", '"text"', "3"])
@pytest.mark.parametrize("filename", ["last-success.json", "freshness.json", "receipt.json"])
def test_non_object_backup_piece_is_unavailable(tmp_path, monkeypatch: pytest.MonkeyPatch, filename, raw) -> None:
    state = tmp_path / "state"
    state.mkdir()
    pieces = {
        "last-success.json": {"at": "2026-10-09T00:00:00Z", "status": "ok"},
        "freshness.json": {"age_h": 1},
        "receipt.json": {"at": "2026-10-09T01:00:00Z", "ok": True},
    }
    for name, payload in pieces.items():
        _write(state, name, payload)
    (state / filename).write_text(raw, encoding="utf-8")
    monkeypatch.setenv("FLEET_BACKUP_STATE_DIR", str(state))
    response = client.get("/api/fleet/v1/backups")
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert _source(body)["status"] == "unavailable"
    if filename == "last-success.json":
        assert body["data"]["last_result"] is None
    if filename == "receipt.json":
        assert body["data"]["restore_test"] is None


def test_overflowing_download_percentage_is_null(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(file_sources, "_now", lambda: _WHEN)
    payload = {"items": [{"source": "alpha", "state": "running", "done": 1e308, "total": 1e-308}]}
    target = tmp_path / "status.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("FLEET_DOWNLOAD_STATUS", str(target))
    response = client.get("/api/fleet/v1/downloads")
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert _source(body)["status"] == "ok"
    assert body["data"]["items"][0]["pct"] is None
    assert body["data"]["items"][0]["done"] == 1e308


def test_single_label_identifiers_are_replaced_with_placeholder(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    marker = "leakword"
    monkeypatch.setattr(file_sources, "_now", lambda: _WHEN)
    downloads = {"items": [{"source": marker, "state": "running", "done": 1, "total": 2}]}
    harness = {"drivers": [{"agent_id": marker, "idle_min": 1}]}
    status = tmp_path / "status.json"
    snapshot = tmp_path / "harness.json"
    status.write_text(json.dumps(downloads), encoding="utf-8")
    snapshot.write_text(json.dumps(harness), encoding="utf-8")
    monkeypatch.setenv("FLEET_DOWNLOAD_STATUS", str(status))
    monkeypatch.setenv("FLEET_HARNESS_SNAPSHOT", str(snapshot))
    downloaded = client.get("/api/fleet/v1/downloads")
    listed = client.get("/api/fleet/v1/harness")
    named = client.get("/api/fleet/v1/harness/" + marker)
    placeholder = client.get("/api/fleet/v1/harness/" + file_sources.UNLISTED)
    for response in (downloaded, listed, named, placeholder):
        assert response.status_code == 200
        _validate(response.json())
        assert marker not in response.text
    assert [item["source"] for item in downloaded.json()["data"]["items"]] == [file_sources.UNLISTED]
    assert [row["agent_id"] for row in listed.json()["data"]["drivers"]] == [file_sources.UNLISTED]
    assert named.json()["data"]["driver"] is None
    assert placeholder.json()["data"]["driver"] is None


def test_approved_driver_aliases_are_the_only_published_driver_ids(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(file_sources, "DRIVER_ALIASES", {"claude": "claude"})
    snapshot = tmp_path / "harness.json"
    snapshot.write_text(json.dumps({"drivers": [{"agent_id": "claude"}, {"agent_id": "alpha"}]}), encoding="utf-8")
    monkeypatch.setenv("FLEET_HARNESS_SNAPSHOT", str(snapshot))
    listed = client.get("/api/fleet/v1/harness")
    assert [row["agent_id"] for row in listed.json()["data"]["drivers"]] == ["claude", file_sources.UNLISTED]
    assert client.get("/api/fleet/v1/harness/alpha").json()["data"]["driver"] is None
