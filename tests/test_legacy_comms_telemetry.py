"""Contract tests for body-free legacy comms route telemetry (#6106)."""

from __future__ import annotations

import json
import sqlite3
import stat
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api import comms_router, telemetry_router
from scripts.api.telemetry import legacy_comms


@pytest.fixture()
def telemetry_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "telemetry" / "legacy-comms.db"
    monkeypatch.setattr(legacy_comms, "_DB_PATH", path)
    legacy_comms._reset_initialized_paths_for_tests()
    return path


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, telemetry_db: Path):
    monkeypatch.setattr(comms_router, "MESSAGE_DB", tmp_path / "missing-broker.db")
    app = FastAPI()
    app.include_router(comms_router.router, prefix="/api/comms")
    app.include_router(telemetry_router.router)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def _rows(path: Path) -> list[tuple]:
    with sqlite3.connect(str(path)) as connection:
        return connection.execute(
            """
            SELECT hour_utc, route_id, method, caller_class, status_class,
                   count, first_seen, last_seen
            FROM legacy_comms_route_usage
            ORDER BY route_id, caller_class, status_class
            """
        ).fetchall()


def test_route_matcher_is_exact_and_normalizes_parameters() -> None:
    assert legacy_comms.match_legacy_route("GET", "/api/comms/messages") == "messages"
    assert legacy_comms.match_legacy_route("GET", "/api/comms/conversations") == "conversations"
    assert (
        legacy_comms.match_legacy_route("GET", "/api/comms/conversation/private-task")
        == "conversation_detail"
    )
    assert legacy_comms.match_legacy_route("POST", "/api/comms/acknowledge/42") == "acknowledge"
    assert legacy_comms.match_legacy_route("POST", "/api/comms/send") == "send"
    assert legacy_comms.match_legacy_route("POST", "/api/comms/messages") is None
    assert legacy_comms.match_legacy_route("GET", "/api/comms/messages/extra") is None
    assert legacy_comms.match_legacy_route("GET", "/api/comms/channels/private/messages") is None


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({"X-Learn-Uk-Caller": "canary"}, "canary"),
        ({"X-Learn-Uk-Caller": "not-allowlisted", "User-Agent": "Mozilla/5.0"}, "browser"),
        ({"User-Agent": "curl/8.0"}, "cli"),
        ({"User-Agent": "python-httpx/0.28"}, "programmatic"),
        ({"User-Agent": "opaque-client"}, "unknown"),
    ],
)
def test_caller_classification_returns_only_allowlisted_classes(headers, expected) -> None:
    assert legacy_comms.classify_caller(headers) == expected


def test_all_legacy_routes_and_validation_failures_are_counted(
    client: TestClient,
    telemetry_db: Path,
) -> None:
    assert client.get("/api/comms/messages").status_code == 200
    assert client.get("/api/comms/conversations").status_code == 200
    assert client.get("/api/comms/conversation/task-1").status_code == 200
    assert client.post("/api/comms/acknowledge/1").status_code == 410
    assert client.post(
        "/api/comms/send",
        json={"from_llm": "a", "to_llm": "b", "content": "body"},
    ).status_code == 410
    assert client.post("/api/comms/send", json={"content": "invalid"}).status_code == 422

    response = client.get("/api/telemetry/legacy-comms-routes?window=1h")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 6
    assert payload["by_caller"] == {"test": 6}
    assert payload["by_status"] == {"2xx": 3, "4xx": 3}
    assert payload["scope_note"].startswith("Direct ask-* CLI calls bypass")
    assert {item["route_id"]: item["count"] for item in payload["routes"]} == {
        "messages": 1,
        "conversations": 1,
        "conversation_detail": 1,
        "acknowledge": 1,
        "send": 2,
    }
    assert telemetry_db.exists()


def test_telemetry_never_persists_paths_queries_bodies_credentials_or_raw_headers(
    client: TestClient,
    telemetry_db: Path,
) -> None:
    secrets = {
        "path-secret": "private-task-67890",
        "query-secret": "query-token-67890",
        "body-secret": "body-token-67890",
        "auth-secret": "auth-token-67890",
        "cookie-secret": "cookie-token-67890",
        "header-secret": "header-token-67890",
    }
    headers = {
        "Authorization": f"Bearer {secrets['auth-secret']}",
        "Cookie": f"session={secrets['cookie-secret']}",
        "X-Learn-Uk-Caller": secrets["header-secret"],
        "User-Agent": "curl/8.0",
    }
    assert client.get(
        f"/api/comms/conversation/{secrets['path-secret']}?token={secrets['query-secret']}",
        headers=headers,
    ).status_code == 200
    assert client.post(
        "/api/comms/send",
        headers=headers,
        json={"from_llm": "a", "to_llm": "b", "content": secrets["body-secret"]},
    ).status_code == 410

    persisted = json.dumps(_rows(telemetry_db))
    assert all(secret not in persisted for secret in secrets.values())
    assert '"conversation_detail"' in persisted
    assert '"send"' in persisted
    assert '"cli"' in persisted


def test_nonlegacy_comms_routes_are_not_counted(client: TestClient) -> None:
    assert client.get("/api/comms/health").status_code == 200
    payload = client.get("/api/telemetry/legacy-comms-routes?window=1h").json()
    assert payload["total"] == 0
    assert all(item["count"] == 0 for item in payload["routes"])


def test_summary_marks_window_incomplete_until_coverage_is_old_enough(
    telemetry_db: Path,
) -> None:
    now = datetime(2026, 8, 1, 12, 30, tzinfo=UTC)
    legacy_comms.initialize_legacy_comms_telemetry(telemetry_db, now=now)
    payload = legacy_comms.legacy_comms_summary("7d", db_path=telemetry_db, now=now)
    assert payload["total"] == 0
    assert payload["window_fully_observed"] is False
    assert len(payload["routes"]) == 5


def test_summary_marks_a_complete_observation_window(telemetry_db: Path) -> None:
    now = datetime(2026, 8, 10, 12, 30, tzinfo=UTC)
    legacy_comms.initialize_legacy_comms_telemetry(
        telemetry_db,
        now=now - timedelta(days=8),
    )
    payload = legacy_comms.legacy_comms_summary("7d", db_path=telemetry_db, now=now)
    assert payload["window_fully_observed"] is True


def test_retention_cleanup_is_bounded_and_idempotent(telemetry_db: Path) -> None:
    now = datetime(2026, 8, 1, 12, 30, tzinfo=UTC)
    legacy_comms.initialize_legacy_comms_telemetry(telemetry_db, now=now - timedelta(days=100))
    with sqlite3.connect(str(telemetry_db)) as connection:
        connection.execute(
            """
            INSERT INTO legacy_comms_route_usage(
                hour_utc, route_id, method, caller_class, status_class,
                count, first_seen, last_seen
            ) VALUES (?, 'messages', 'GET', 'unknown', '2xx', 1, ?, ?)
            """,
            (
                "2026-04-01T00:00:00Z",
                "2026-04-01T00:00:00Z",
                "2026-04-01T00:00:00Z",
            ),
        )
        connection.commit()

    for _ in range(2):
        legacy_comms.record_legacy_route_usage(
            "messages",
            "GET",
            "canary",
            200,
            db_path=telemetry_db,
            now=now,
        )

    rows = _rows(telemetry_db)
    assert len(rows) == 1
    assert rows[0][1:6] == ("messages", "GET", "canary", "2xx", 2)


def test_concurrent_writers_increment_one_atomic_bucket(telemetry_db: Path) -> None:
    now = datetime(2026, 8, 1, 12, 30, tzinfo=UTC)

    def record(_index: int) -> None:
        legacy_comms.record_legacy_route_usage(
            "messages",
            "GET",
            "automation",
            200,
            db_path=telemetry_db,
            now=now,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(record, range(40)))

    assert _rows(telemetry_db)[0][5] == 40


def test_existing_database_permissions_are_migrated_to_owner_only(telemetry_db: Path) -> None:
    telemetry_db.parent.mkdir(parents=True)
    telemetry_db.touch(mode=0o644)
    telemetry_db.chmod(0o644)
    legacy_comms.initialize_legacy_comms_telemetry(telemetry_db)
    assert stat.S_IMODE(telemetry_db.stat().st_mode) == 0o600


def test_storage_failure_does_not_break_legacy_route(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*_args, **_kwargs) -> None:
        raise OSError("synthetic telemetry outage")

    monkeypatch.setattr(legacy_comms, "record_legacy_route_usage", fail)
    response = client.get("/api/comms/messages")
    assert response.status_code == 200


def test_invalid_summary_window_is_rejected(client: TestClient) -> None:
    assert client.get("/api/telemetry/legacy-comms-routes?window=forever").status_code == 422
