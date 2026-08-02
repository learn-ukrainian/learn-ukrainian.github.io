"""Contract tests for the unified, read-only fleet observer."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import scripts.api.fleet_router as fleet_router
from scripts.fleet_comms.migrations import MIGRATIONS, apply_migrations


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    app.include_router(fleet_router.router, prefix="/api/fleet")
    return TestClient(app)


@pytest.fixture()
def fleet_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "fleet-comms" / "v1"
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "shadow")
    return root


def _seed_plane(root: Path) -> None:
    root.mkdir(parents=True)
    connection = sqlite3.connect(root / "comms.sqlite3")
    try:
        apply_migrations(connection)
        connection.executescript(
            """
            INSERT INTO conversations(conversation_id, created_at, source, title)
            VALUES ('conv-1', '2026-08-01T12:00:00Z', 'operator', 'Observer contract');

            INSERT INTO comms_messages(
                message_id, conversation_id, kind, sender, recipient, body_inline,
                body_artifact_id, metadata_json, created_at
            ) VALUES
            (
                'message-request', 'conv-1', 'request', 'codex', 'claude',
                'TOKEN=secret-value request body that must remain bounded.', 'artifact-body',
                '{"source":"operator","via":"dispatch","task_id":"task-6159"}',
                '2026-08-01T12:00:00Z'
            ),
            (
                'message-reply', 'conv-1', 'reply', 'claude', 'codex',
                'Bearer super-secret-token reply body.', NULL,
                '{"source":"operator","transport_mode":"bridge"}',
                '2026-08-01T12:02:00Z'
            );

            INSERT INTO requests(
                request_id, request_message_id, requested_recipient, resolved_recipient,
                state, expires_at, completion_state, invocation_spec_json, created_at, updated_at
            ) VALUES (
                'request-1', 'message-request', 'claude', 'claude', 'complete',
                '2026-08-01T13:00:00Z', 'complete',
                '{"source":"operator","via":"dispatch","pr_number":6159}',
                '2026-08-01T12:00:00Z', '2026-08-01T12:02:00Z'
            );

            INSERT INTO agent_endpoints(
                endpoint_id, canonical_name, registry_version, state, successor,
                configuration_json, created_at
            ) VALUES (
                'endpoint-codex', 'codex', 1, 'live', NULL,
                '{"token":"must-not-leak"}', '2026-08-01T11:00:00Z'
            );

            INSERT INTO dead_letters(
                dead_letter_id, request_id, delivery_id, reason, successor,
                original_expires_at, created_at
            ) VALUES (
                'dead-1', 'request-1', 'delivery-1', 'transport_timeout', 'claude',
                '2026-08-01T12:01:00Z', '2026-08-01T12:03:00Z'
            );

            INSERT INTO formal_review_jobs(
                review_id, repository, pr_number, head_sha, gate_kind, state,
                snapshot_artifact_id, sealed_verdict_artifact_id, created_at
            ) VALUES (
                'review-1', 'learn-ukrainian/learn-ukrainian.github.io', 6159,
                'deadbeef', 'cross-family-review', 'complete', NULL, 'sealed-artifact',
                '2026-08-01T12:00:00Z'
            );

            INSERT INTO formal_review_attempts(
                review_attempt_id, review_id, attempt_number, completion_state,
                raw_capture_artifact_id, created_at
            ) VALUES ('review-attempt-1', 'review-1', 1, 'complete', 'capture-artifact', '2026-08-01T12:04:00Z');

            INSERT INTO github_publications(
                publication_id, review_id, head_sha, status_context, published_at
            ) VALUES (
                'publication-1', 'review-1', 'deadbeef', 'fleet/cross-family-review',
                '2026-08-01T12:05:00Z'
            );

            INSERT INTO acp_conversations(
                conversation_id, task_digest, correlation_digest, idempotency_digest,
                rounds_requested, participants_json, created_at, deadline_at,
                token_budget, content_budget_bytes
            ) VALUES (
                'acp-1', 'task-digest', 'correlation-digest', 'idempotency-digest',
                2, '["codex", "grok"]', '2026-08-01T12:00:00Z',
                '2026-08-01T13:00:00Z', 1200, 4096
            );

            INSERT INTO acp_conversation_events(
                event_id, conversation_id, sequence, event_type, state, sender, recipient,
                round, outcome, duration_ms, token_count, metadata_json, created_at
            ) VALUES (
                'acp-event-1', 'acp-1', 1, 'PARTICIPANT_MESSAGE', 'INITIAL_FANOUT',
                'codex', 'grok', 1, 'succeeded', 25, 40, '{}', '2026-08-01T12:01:00Z'
            );

            INSERT INTO conversations(conversation_id, created_at, source, title)
            VALUES ('authority-conv', '2026-08-01T12:07:00Z', 'authority', 'Authority queue');

            INSERT INTO comms_messages(
                message_id, conversation_id, kind, sender, recipient, body_inline,
                body_artifact_id, metadata_json, created_at
            ) VALUES (
                'authority-message', 'authority-conv', 'request', 'authority-service', 'codex',
                'password=queue-secret authority request', 'authority-payload', '{"authority":true}',
                '2026-08-01T12:07:00Z'
            );

            INSERT INTO authority_message_metadata(
                message_id, channel_id, thread_id, correlation_id, context_revisions_json,
                provenance_json, imported_source, created_at
            ) VALUES (
                'authority-message', NULL, 'authority-thread', NULL, '{}',
                '{"Source":"legacy-bridge","Agent":"codex","Via":"queue"}',
                'legacy-bridge', '2026-08-01T12:07:00Z'
            );

            INSERT INTO authority_deliveries(
                delivery_id, message_id, recipient, state, deadline_at, lease_owner,
                lease_expires_at, fence_token, attempt_count, acknowledgment_artifact_id,
                terminal_sha256, created_at, updated_at, completed_at
            ) VALUES (
                'authority-delivery-1', 'authority-message', 'codex', 'failed', NULL, NULL,
                NULL, 3, 3, NULL, 'terminal-sha', '2026-08-01T12:07:00Z',
                '2026-08-01T12:08:00Z', '2026-08-01T12:08:00Z'
            );

            INSERT INTO authority_dead_letters(
                dead_letter_id, delivery_id, job_id, reason_code, created_at
            ) VALUES (
                'authority-dead-letter-1', 'authority-delivery-1', NULL,
                'attempts_exhausted', '2026-08-01T12:08:00Z'
            );

            INSERT INTO authority_jobs(
                job_id, job_kind, subject_id, payload_artifact_id, state, deadline_at,
                lease_owner, lease_expires_at, fence_token, attempt_count, result_artifact_id,
                terminal_sha256, idempotency_key, created_at, updated_at, completed_at
            ) VALUES (
                'authority-job-1', 'request', 'authority-message', 'authority-payload', 'queued',
                NULL, NULL, NULL, 0, 0, NULL, NULL, 'authority-job-key',
                '2026-08-01T12:07:00Z', '2026-08-01T12:07:00Z', NULL
            );
            """
        )
        connection.commit()
    finally:
        connection.close()


def test_absent_plane_db_returns_deterministic_read_only_empty_states(
    client: TestClient, fleet_root: Path
) -> None:
    assert not fleet_root.exists()

    for path, key in [
        ("/api/fleet/requests", "requests"),
        ("/api/fleet/messages", "messages"),
        ("/api/fleet/discussions", "discussions"),
        ("/api/fleet/reviews", "reviews"),
        ("/api/fleet/dead-letters", "dead_letters"),
    ]:
        response = client.get(path)

        assert response.status_code == 200
        payload = response.json()
        assert payload["read_only"] is True
        assert payload["availability"] == "db_missing"
        assert payload[key] == []
        assert payload["total"] == 0

    migrations = client.get("/api/fleet/migrations").json()
    assert migrations["read_only"] is True
    assert migrations["availability"] == "db_missing"
    assert migrations["migrations"] == []
    assert not fleet_root.exists(), "observer must not create a missing plane root"


def test_plane_health_and_overview_expose_pre_flip_read_only_posture(
    client: TestClient, fleet_root: Path
) -> None:
    _seed_plane(fleet_root)

    health = client.get("/api/fleet/health")
    overview = client.get("/api/fleet/overview")

    assert health.status_code == 200
    assert health.json()["read_only"] is True
    assert health.json()["writes_enabled"] is False
    assert health.json()["authority"] == "file_handoffs_authoritative"
    assert health.json()["cutover"] == "pre_flip_operator_gated"
    assert health.json()["schema"]["applied_version"] == MIGRATIONS[-1].version
    assert overview.status_code == 200
    assert overview.json()["counts"]["requests"]["total"] == 1
    assert overview.json()["counts"]["messages"]["total"] == 3
    assert overview.json()["counts"]["reviews"]["total"] == 1
    assert overview.json()["counts"]["dead_letters"]["total"] == 1
    assert overview.json()["counts"]["acp_conversations"]["total"] == 1
    assert overview.json()["counts"]["authority_jobs"]["total"] == 1


def test_plane_health_and_overview_expose_active_authority_posture(
    client: TestClient, fleet_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "authority")
    _seed_plane(fleet_root)

    health = client.get("/api/fleet/health").json()
    overview = client.get("/api/fleet/overview").json()

    assert health["mode"] == "authority"
    assert health["authority"] == "fleet_comms_authoritative"
    assert health["cutover"] == "authority_active"
    assert overview["authority"] == health["authority"]
    assert overview["cutover"] == health["cutover"]
    assert overview["counts"]["dead_letters"]["total"] == 1

    dead_letters = client.get(
        "/api/fleet/dead-letters",
        params={"state": "failed", "agent": "codex", "source": "legacy-bridge"},
    ).json()
    assert dead_letters["total"] == 1
    assert dead_letters["dead_letters"][0]["reason"] == "attempts_exhausted"
    assert dead_letters["dead_letters"][0]["via"] == "queue"


def test_message_and_request_filters_are_stable_and_bodies_are_bounded(
    client: TestClient, fleet_root: Path
) -> None:
    _seed_plane(fleet_root)

    response = client.get(
        "/api/fleet/messages",
        params={
            "kind": "request",
            "agent": "codex",
            "source": "operator",
            "conversation": "conv-1",
            "since": "2026-08-01T11:59:00Z",
            "until": "2026-08-01T12:01:00Z",
            "limit": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["next_offset"] is None
    message = payload["messages"][0]
    assert message["source"] == "operator"
    assert message["agent"] == "codex"
    assert message["via"] == "dispatch"
    assert len(message["body_preview"]) <= fleet_router.MAX_BODY_PREVIEW_CHARS
    assert "secret-value" not in message["body_preview"]
    assert message["artifact_available"] is True
    assert "body_artifact_id" not in message

    detail = client.get("/api/fleet/messages/message-request")
    assert detail.status_code == 200
    assert detail.headers["cache-control"] == "no-store"
    assert detail.json()["read_only"] is True
    assert detail.json()["body_policy"]["artifact_content"] == "omitted"
    assert len(detail.json()["message"]["body_preview"]) <= fleet_router.MAX_BODY_DETAIL_CHARS
    assert "secret-value" not in detail.json()["message"]["body_preview"]

    authority_messages = client.get(
        "/api/fleet/messages", params={"source": "legacy-bridge", "agent": "codex"}
    )
    assert authority_messages.status_code == 200
    assert authority_messages.json()["total"] == 1
    authority_message = authority_messages.json()["messages"][0]
    assert authority_message["message_id"] == "authority-message"
    assert authority_message["source"] == "legacy-bridge"
    assert authority_message["agent"] == "codex"
    assert authority_message["via"] == "queue"
    assert "queue-secret" not in authority_message["body_preview"]

    requests = client.get(
        "/api/fleet/requests",
        params={
            "kind": "request",
            "state": "complete",
            "agent": "claude",
            "source": "operator",
            "conversation": "conv-1",
        },
    )
    assert requests.status_code == 200
    assert requests.json()["total"] == 1
    assert requests.json()["requests"][0]["request_id"] == "request-1"


def test_discussion_review_and_dead_letter_metadata_stay_read_only(
    client: TestClient, fleet_root: Path
) -> None:
    _seed_plane(fleet_root)

    discussion = client.get("/api/fleet/discussions", params={"kind": "request"})
    assert discussion.status_code == 200
    assert {item["conversation_id"] for item in discussion.json()["discussions"]} == {
        "conv-1",
        "authority-conv",
    }

    discussion_detail = client.get("/api/fleet/discussions/conv-1")
    assert discussion_detail.status_code == 200
    assert discussion_detail.headers["cache-control"] == "no-store"
    assert discussion_detail.json()["body_policy"].startswith("redacted_inline")
    assert discussion_detail.json()["discussion"]["message_count"] == 2
    assert discussion_detail.json()["discussion"]["latest_message_at"] == "2026-08-01T12:02:00Z"
    assert len(discussion_detail.json()["messages"]["messages"]) == 2

    reviews = client.get(
        "/api/fleet/reviews",
        params={"kind": "cross-family-review", "state": "complete", "pr": 6159},
    )
    assert reviews.status_code == 200
    assert reviews.json()["total"] == 1
    assert reviews.json()["reviews"][0]["publication_count"] == 1
    assert reviews.json()["reviews"][0]["sealed_verdict_available"] is True

    authority_jobs = client.get(
        "/api/fleet/authority/jobs",
        params={
            "kind": "request",
            "state": "queued",
            "agent": "codex",
            "source": "legacy-bridge",
            "conversation": "authority-conv",
        },
    )
    assert authority_jobs.status_code == 200
    assert authority_jobs.json()["total"] == 1
    authority_job = authority_jobs.json()["jobs"][0]
    assert authority_job["job_id"] == "authority-job-1"
    assert authority_job["source"] == "legacy-bridge"
    assert authority_job["agent"] == "codex"
    assert authority_job["via"] == "queue"
    assert authority_job["payload_content"] == "omitted"
    assert "payload_artifact_id" not in authority_job
    assert "idempotency_key" not in authority_job

    review_detail = client.get("/api/fleet/reviews/review-1")
    assert review_detail.status_code == 200
    assert review_detail.headers["cache-control"] == "no-store"
    assert review_detail.json()["detail_policy"] == "raw_capture_and_sealed_verdict_blobs_omitted"
    assert "sealed_verdict_artifact_id" not in review_detail.json()["review"]
    assert "raw_capture_artifact_id" not in json.dumps(review_detail.json())

    dead_letters = client.get(
        "/api/fleet/dead-letters",
        params={"state": "complete", "agent": "claude", "source": "operator"},
    )
    assert dead_letters.status_code == 200
    assert dead_letters.json()["total"] == 1
    assert dead_letters.json()["dead_letters"][0]["via"] == "fleet-comms"


def test_acp_and_runtime_provenance_reuse_existing_read_models(
    client: TestClient,
    fleet_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_plane(fleet_root)
    monkeypatch.setattr(
        fleet_router,
        "recent_runtime_records",
        lambda *, limit: {
            "records": [
                {
                    "ts": "2026-08-01T12:06:00Z",
                    "source": "operator",
                    "agent": "codex",
                    "via": "dispatch",
                    "entrypoint": "dispatch",
                    "model": "gpt-5.6-terra",
                    "outcome": "ok",
                    "source_provenance": "explicit",
                    "source_task_id": "task-6159",
                }
            ]
        },
    )

    acp = client.get("/api/fleet/acp/conversations", params={"agent": "codex"})
    assert acp.status_code == 200
    assert acp.json()["total"] == 1
    assert acp.json()["conversations"][0]["source"] == "acpx"
    assert acp.json()["conversations"][0]["agent"] == "codex / grok"
    assert acp.json()["conversations"][0]["via"] == "fleet-comms"

    acp_detail = client.get("/api/fleet/acp/conversations/acp-1")
    assert acp_detail.status_code == 200
    assert acp_detail.headers["cache-control"] == "no-store"
    assert acp_detail.json()["body_policy"] == "events_only_no_transcript_or_artifact_content"
    assert "events" in acp_detail.json()["conversation"]

    activity = client.get("/api/fleet/activity", params={"source": "operator", "agent": "codex"})
    assert activity.status_code == 200
    record = activity.json()["records"][0]
    assert record["source"] == "operator"
    assert record["agent"] == "codex"
    assert record["via"] == "dispatch"


def test_endpoints_and_migrations_omit_configuration_secrets(
    client: TestClient, fleet_root: Path
) -> None:
    _seed_plane(fleet_root)

    endpoints = client.get("/api/fleet/endpoints", params={"agent": "codex"})
    assert endpoints.status_code == 200
    assert endpoints.json()["configuration_policy"] == "configuration_json_omitted"
    assert "must-not-leak" not in endpoints.text
    assert "configuration_json" not in endpoints.json()["endpoints"][0]

    migrations = client.get("/api/fleet/migrations")
    assert migrations.status_code == 200
    assert migrations.json()["read_only"] is True
    assert migrations.json()["applied_version"] == MIGRATIONS[-1].version
    assert [entry["version"] for entry in migrations.json()["migrations"]] == [
        migration.version for migration in MIGRATIONS
    ]


def test_operations_projection_is_bounded_read_only_and_source_blind(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broker_path = tmp_path / "legacy-broker.db"
    connection = sqlite3.connect(broker_path)
    try:
        connection.execute(
            "CREATE TABLE messages(id INTEGER PRIMARY KEY, acknowledged INTEGER NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO messages(acknowledged) VALUES (?)",
            [(0,), (0,), (1,)],
        )
        connection.commit()
    finally:
        connection.close()
    before = broker_path.read_bytes()
    monkeypatch.setattr(fleet_router.legacy_comms, "MESSAGE_DB", broker_path)

    async def fake_processes() -> dict:
        return {
            "alive": 2,
            "processes": [
                {"pid": 99123, "file": "secret-pid.json", "task_id": "private-task"}
            ],
        }

    async def fake_zombies(*, stale_hours: float, pingpong_threshold: int) -> dict:
        assert stale_hours == 2.0
        assert pingpong_threshold == 5
        return {
            "count": 55,
            "zombies": [
                {
                    "type": "stale_message",
                    "severity": "critical",
                    "age_hours": index + 0.25,
                    "message_id": index,
                    "task_id": "private-task",
                    "preview": "Bearer source-secret",
                    "from": "private-sender",
                    "to": "private-recipient",
                }
                for index in range(55)
            ],
        }

    def fake_batches() -> dict:
        return {
            "generated_at": "2026-08-02T00:00:00Z",
            "running_processes": 3,
            "tracks": {
                f"track-{index:02d}": {
                    "track": f"track-{index:02d}",
                    "health": "healthy",
                    "total_expected": 100,
                    "research_done": index,
                    "remaining": 100 - index,
                    "recent_30min": 1,
                    "throughput_per_hour": 2,
                    "last_created": {"slug": "private-slug"},
                    "log": {"last_line": "password=source-secret", "log_file": "private.log"},
                    "process": {"pid": 4455, "cmd": "provider --token source-secret"},
                }
                for index in range(55)
            },
        }

    monkeypatch.setattr(fleet_router.legacy_comms, "active_processes", fake_processes)
    monkeypatch.setattr(fleet_router.legacy_comms, "detect_zombies", fake_zombies)
    monkeypatch.setattr(fleet_router, "_legacy_batch_snapshot", fake_batches)

    response = client.get("/api/fleet/operations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["read_only"] is True
    assert payload["writes_enabled"] is False
    assert payload["availability"] == "available"
    assert payload["broker"] == {
        "availability": "available",
        "db_exists": True,
        "readable": True,
        "size_kb": pytest.approx(broker_path.stat().st_size / 1024, abs=0.1),
        "unacknowledged_depth": 2,
        "live_process_count": 2,
        "process_availability": "available",
    }
    assert payload["zombies"]["total"] == 55
    assert payload["zombies"]["returned"] == fleet_router.MAX_OPERATIONS_ITEMS
    assert payload["zombies"]["truncated"] is True
    assert set(payload["zombies"]["items"][0]) == {"type", "severity", "age_hours"}
    assert payload["batches"]["total"] == 55
    assert payload["batches"]["returned"] == fleet_router.MAX_OPERATIONS_ITEMS
    assert payload["batches"]["truncated"] is True
    assert set(payload["batches"]["tracks"][0]) == {
        "track",
        "health",
        "total_expected",
        "research_done",
        "remaining",
        "recent_30min",
        "throughput_per_hour",
    }
    for forbidden in (
        "source-secret",
        "private-task",
        "private-sender",
        "private-recipient",
        "private-slug",
        "private.log",
        "secret-pid.json",
        "provider --token",
    ):
        assert forbidden not in response.text
    assert broker_path.read_bytes() == before, "observer must not mutate the broker database"


def test_operations_missing_store_does_not_create_it(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broker_path = tmp_path / "missing" / "legacy-broker.db"
    monkeypatch.setattr(fleet_router.legacy_comms, "MESSAGE_DB", broker_path)

    async def empty_processes() -> dict:
        return {"alive": 0, "processes": []}

    async def empty_zombies(**_kwargs: object) -> dict:
        return {"count": 0, "zombies": []}

    def empty_batches() -> dict:
        return {"running_processes": 0, "tracks": {}}

    monkeypatch.setattr(fleet_router.legacy_comms, "active_processes", empty_processes)
    monkeypatch.setattr(fleet_router.legacy_comms, "detect_zombies", empty_zombies)
    monkeypatch.setattr(fleet_router, "_legacy_batch_snapshot", empty_batches)

    payload = client.get("/api/fleet/operations").json()

    assert payload["availability"] == "partial"
    assert payload["broker"]["availability"] == "db_missing"
    assert payload["broker"]["db_exists"] is False
    assert payload["zombies"]["items"] == []
    assert payload["batches"]["tracks"] == []
    assert not broker_path.exists()
    assert not broker_path.parent.exists()


def test_operations_dependency_outages_fail_as_sanitized_unavailable_sections(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broker_path = tmp_path / "broken-broker.db"
    broker_path.write_bytes(b"not-a-sqlite-database private-outage-detail")
    monkeypatch.setattr(fleet_router.legacy_comms, "MESSAGE_DB", broker_path)

    async def unavailable(*_args: object, **_kwargs: object) -> dict:
        raise RuntimeError("private dependency path and credential")

    def unavailable_batch() -> dict:
        raise RuntimeError("private dependency path and credential")

    monkeypatch.setattr(fleet_router.legacy_comms, "active_processes", unavailable)
    monkeypatch.setattr(fleet_router.legacy_comms, "detect_zombies", unavailable)
    monkeypatch.setattr(fleet_router, "_legacy_batch_snapshot", unavailable_batch)

    response = client.get("/api/fleet/operations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["availability"] == "unavailable"
    assert payload["broker"]["availability"] == "db_unavailable"
    assert payload["broker"]["live_process_count"] is None
    assert payload["zombies"]["availability"] == "unavailable"
    assert payload["batches"]["availability"] == "unavailable"
    assert "private" not in response.text
    assert "credential" not in response.text


def test_operations_batch_snapshot_reuses_uncached_read_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        fleet_router.legacy_comms,
        "_scan_preseed_logs",
        lambda: [
            {
                "track": "hist",
                "complete": False,
                "age_seconds": 30,
                "last_line": "private log line",
            },
            {"track": "bio", "complete": True, "age_seconds": 10},
        ],
    )
    monkeypatch.setattr(
        fleet_router.legacy_comms,
        "_check_build_processes",
        lambda: [{"track": "hist", "pid": 123, "cmd": "private command"}],
    )
    monkeypatch.setattr(
        fleet_router.legacy_comms,
        "_scan_track_progress",
        lambda track: {
            "track": track,
            "total_expected": 10,
            "research_done": 3,
            "remaining": 7,
            "recent_30min": 0,
            "throughput_per_hour": 0,
            "last_created": {"slug": "private-slug"},
        },
    )
    monkeypatch.setattr(
        fleet_router.legacy_comms,
        "cache_set",
        lambda *_args, **_kwargs: pytest.fail("operations snapshot must not write cache state"),
    )

    snapshot = fleet_router._legacy_batch_snapshot()

    assert snapshot["running_processes"] == 1
    assert snapshot["tracks"]["hist"]["health"] == "healthy"
    assert snapshot["tracks"]["bio"]["health"] == "complete"
