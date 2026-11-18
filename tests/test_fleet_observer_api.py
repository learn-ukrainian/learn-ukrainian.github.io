"""Contract tests for the unified, read-only fleet observer."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import lu_machinery.api.fleet_router as fleet_router
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from lu_machinery.api import product_contribution
from lu_machinery.api.monitor_context import MonitorContext, fixture_context
from lu_machinery.fleet_comms.migrations import MIGRATIONS, apply_migrations

import scripts.project_api.batch_progress as product_batch_progress


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    # The /operations route resolves its read-model roots from the app's
    # MonitorContext (same as production); keep every root under the test's
    # tmp_path.
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(fleet_router.router, prefix="/api/fleet")
    return TestClient(app)


@pytest.fixture()
def product_fleet_batches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Install the product's fleet-batches provider for one test.

    ``/operations`` reads curriculum batches through the provider the product
    contributes, which a process holds only after some earlier test built a full
    Monitor app. Install it here so these tests pass alone, in any order and in
    any shard. The hook looks ``fleet_batch_snapshot`` up when called, so the
    tests that replace it on its module are still seen.
    """
    from scripts.project_api.entry import build_api

    provider = build_api(fixture_context(tmp_path)).fleet_batches
    assert provider is not None
    monkeypatch.setattr(product_contribution, "_fleet_batches", provider)


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
                '{"Source":"legacy-bridge","Agent":"codex","Via":"queue","task_id":"task-authority-1"}',
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

    # lu-machinery 0.1.31 (machinery #756) serves /requests as the only
    # list route over the plane; messages, discussions, reviews and
    # dead-letters are no longer mounted.
    response = client.get("/api/fleet/requests")
    assert response.status_code == 200
    payload = response.json()
    assert payload["read_only"] is True
    assert payload["availability"] == "db_missing"
    assert payload["requests"] == []
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
    assert overview["counts"]["requests"] == {
        "total": 1,
        "by_state": {"queued": 1},
        "source": "authority_jobs",
    }
    assert overview["counts"]["legacy_requests"] == {
        "total": 1,
        "by_state": {"complete": 1},
        "excluded_from_authority_health": True,
    }
    assert overview["counts"]["dead_letters"]["total"] == 1


def test_authority_health_uses_only_recent_authority_evidence(
    fleet_root: Path,
) -> None:
    _seed_plane(fleet_root)
    observed_at = fleet_router.datetime(2026, 8, 2, 12, 0, tzinfo=fleet_router.UTC)
    connection = sqlite3.connect(fleet_root / "comms.sqlite3")
    connection.row_factory = sqlite3.Row
    try:
        connection.execute(
            """UPDATE authority_jobs
               SET state = 'failed', updated_at = '2026-08-02T11:00:00Z',
                   completed_at = '2026-08-02T11:00:00Z'"""
        )
        connection.execute(
            "UPDATE authority_dead_letters SET created_at = '2026-07-01T00:00:00Z'"
        )
        connection.commit()
        degraded = fleet_router._authority_health_snapshot(
            connection, now=observed_at
        )

        connection.execute(
            """UPDATE authority_jobs
               SET updated_at = '2026-07-01T00:00:00Z',
                   completed_at = '2026-07-01T00:00:00Z'"""
        )
        connection.commit()
        idle = fleet_router._authority_health_snapshot(connection, now=observed_at)
    finally:
        connection.close()

    assert degraded["state"] == "degraded"
    assert degraded["ok"] is False
    assert degraded["jobs"] == {"total": 1, "by_state": {"failed": 1}}
    assert degraded["dead_letters"] == 0
    assert idle["state"] == "idle"
    assert idle["ok"] is True
    assert idle["jobs"] == {"total": 0, "by_state": {}}


def test_request_filters_are_stable(client: TestClient, fleet_root: Path) -> None:
    _seed_plane(fleet_root)

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


def test_authority_job_metadata_stays_read_only(client: TestClient, fleet_root: Path) -> None:
    _seed_plane(fleet_root)

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
    assert authority_job["task_id"] == "task-authority-1"
    assert authority_job["failure"] is None
    assert authority_job["payload_content"] == "omitted"
    assert "payload_artifact_id" not in authority_job
    assert "idempotency_key" not in authority_job

    connection = sqlite3.connect(fleet_root / "comms.sqlite3")
    try:
        connection.execute(
            """INSERT INTO authority_job_events(
                event_id, job_id, fence_token, event_type, state, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                "authority-event-finished",
                "authority-job-1",
                1,
                "finished",
                "failed",
                json.dumps(
                    {
                        "failure": {
                            "phase": "provider",
                            "code": "provider_unavailable",
                            "retryable": True,
                        },
                        "raw_error": "password=must-not-leak",
                    }
                ),
                "2026-08-01T12:09:00Z",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    failed_projection = client.get(
        "/api/fleet/authority/jobs", params={"kind": "request"}
    ).json()["jobs"][0]
    assert failed_projection["failure"] == {
        "phase": "provider",
        "code": "provider_unavailable",
        "retryable": True,
    }
    assert "must-not-leak" not in json.dumps(failed_projection)


def test_fleet_reviews_direct_python_call_with_defaults(fleet_root: Path) -> None:
    """Calling fleet_reviews directly as a Python function with defaults must not
    raise AttributeError or pass Query sentinel objects into SQL/filters (#6849)."""
    _seed_plane(fleet_root)
    from lu_machinery.api.fleet_router import fleet_reviews

    public_repo = "learn-ukrainian/learn-ukrainian.github.io"
    result = fleet_reviews(limit=10, offset=0, repository=public_repo)
    assert isinstance(result, dict)
    assert result["total"] >= 1
    assert "reviews" in result
    assert result["filters"]["kind"] is None
    assert result["filters"]["state"] is None
    assert result["filters"]["source"] is None
    assert result["filters"]["since"] is None
    assert result["filters"]["until"] is None
    assert result["filters"]["pr"] is None
    assert result["filters"]["repository"] == public_repo


def test_reviews_repository_filter_applies_before_count_and_pagination(fleet_root: Path) -> None:
    """Exact repository filter participates in SQL COUNT/LIMIT so foreign volume
    cannot hide public rows or inflate public totals/truncation signals.

    lu-machinery 0.1.31 (machinery #756) no longer mounts GET /api/fleet/reviews;
    the Work API reads ``fleet_reviews`` as a Python function, so this calls it
    the same way.
    """
    from lu_machinery.api.fleet_router import fleet_reviews

    _seed_plane(fleet_root)
    public_repo = "learn-ukrainian/learn-ukrainian.github.io"
    foreign_repo = "evil-org/private-infra"
    # More foreign rows than a typical Work hard-cap page window (2000), plus a
    # handful of public rows that must remain fully visible when filtered.
    foreign_n = 2050
    public_n = 5
    connection = sqlite3.connect(fleet_root / "comms.sqlite3")
    try:
        for i in range(foreign_n):
            connection.execute(
                """
                INSERT INTO formal_review_jobs(
                    review_id, repository, pr_number, head_sha, gate_kind, state,
                    snapshot_artifact_id, sealed_verdict_artifact_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?)
                """,
                (
                    f"foreign-review-{i:04d}",
                    foreign_repo,
                    7000 + i,
                    f"dead{i:04d}",
                    "cross-family-review",
                    "running",
                    f"2026-07-01T00:00:{i % 60:02d}Z",
                ),
            )
        for i in range(public_n):
            connection.execute(
                """
                INSERT INTO formal_review_jobs(
                    review_id, repository, pr_number, head_sha, gate_kind, state,
                    snapshot_artifact_id, sealed_verdict_artifact_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?)
                """,
                (
                    f"public-review-{i:04d}",
                    public_repo,
                    8000 + i,
                    f"beef{i:04d}",
                    "cross-family-review",
                    "running",
                    f"2026-08-02T00:{i:02d}:00Z",
                ),
            )
        connection.commit()
    finally:
        connection.close()

    unfiltered = fleet_reviews(limit=10, offset=0)
    # Seed already has review-1 for public_repo; plus inserts.
    assert unfiltered["total"] == foreign_n + public_n + 1

    payload = fleet_reviews(repository=public_repo, limit=100, offset=0)
    assert payload["filters"]["repository"] == public_repo
    # total is repository-scoped — private volume does not inflate it.
    assert payload["total"] == public_n + 1
    assert len(payload["reviews"]) == public_n + 1
    assert {row["repository"] for row in payload["reviews"]} == {public_repo}
    review_ids = {row["review_id"] for row in payload["reviews"]}
    assert "review-1" in review_ids
    assert {f"public-review-{i:04d}" for i in range(public_n)} <= review_ids
    assert not any(rid.startswith("foreign-review-") for rid in review_ids)
    assert foreign_repo not in json.dumps(payload)

    # Pagination offsets also advance only within the filtered set.
    page = fleet_reviews(repository=public_repo, limit=2, offset=2)
    assert page["total"] == public_n + 1
    assert len(page["reviews"]) == 2
    assert {row["repository"] for row in page["reviews"]} == {public_repo}

    foreign_only = fleet_reviews(repository=foreign_repo, limit=5, offset=0)
    assert foreign_only["total"] == foreign_n
    assert len(foreign_only["reviews"]) == 5
    assert all(r["repository"] == foreign_repo for r in foreign_only["reviews"])


def test_acp_and_runtime_provenance_reuse_existing_read_models(
    client: TestClient,
    fleet_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_plane(fleet_root)
    monkeypatch.setattr(
        fleet_router,
        "recent_runtime_records",
        lambda *, limit, ctx=None: {
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


@pytest.mark.usefixtures("product_fleet_batches")
def test_operations_projection_is_bounded_read_only_and_source_blind(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_batches(ctx: MonitorContext | None = None) -> dict:
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

    monkeypatch.setattr(product_batch_progress, "fleet_batch_snapshot", fake_batches)

    response = client.get("/api/fleet/operations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["read_only"] is True
    assert payload["writes_enabled"] is False
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
        "private-slug",
        "private.log",
        "provider --token",
    ):
        assert forbidden not in response.text


@pytest.mark.usefixtures("product_fleet_batches")
def test_operations_dependency_outages_fail_as_sanitized_unavailable_sections(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable_batch(ctx: MonitorContext | None = None) -> dict:
        raise RuntimeError("private dependency path and credential")

    monkeypatch.setattr(product_batch_progress, "fleet_batch_snapshot", unavailable_batch)

    response = client.get("/api/fleet/operations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["batches"]["availability"] == "unavailable"
    assert "private" not in response.text
    assert "credential" not in response.text


def test_operations_batch_snapshot_reuses_uncached_read_models(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = fixture_context(tmp_path)
    monkeypatch.setattr(
        product_batch_progress,
        "_scan_preseed_logs",
        lambda ctx: [
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
        product_batch_progress,
        "_check_build_processes",
        lambda: ([{"track": "hist", "pid": 123, "cmd": "private command"}], None),
    )
    monkeypatch.setattr(
        product_batch_progress,
        "_scan_track_progress",
        lambda ctx, track: {
            "track": track,
            "total_expected": 10,
            "research_done": 3,
            "remaining": 7,
            "recent_30min": 0,
            "throughput_per_hour": 0,
            "last_created": {"slug": "private-slug"},
        },
    )
    # The comms router keeps no cache since lu-machinery 0.1.31 (machinery
    # #743); the batch progress module's own cache_set binding is the write
    # this snapshot must not reach.
    monkeypatch.setattr(
        product_batch_progress,
        "cache_set",
        lambda *_args, **_kwargs: pytest.fail("operations snapshot must not write cache state"),
    )

    snapshot = product_batch_progress.fleet_batch_snapshot(ctx)

    assert snapshot["running_processes"] == 1
    assert snapshot["tracks"]["hist"]["health"] == "healthy"
    assert snapshot["tracks"]["bio"]["health"] == "complete"


def _batch_progress_stub(track: str) -> dict:
    return {
        "track": track,
        "total_expected": 10,
        "research_done": 3,
        "remaining": 7,
        "recent_30min": 0,
        "throughput_per_hour": 0,
        "last_created": None,
    }


def test_legacy_batch_snapshot_old_log_is_unknown_when_process_probe_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = fixture_context(tmp_path)
    monkeypatch.setattr(
        product_batch_progress,
        "_scan_preseed_logs",
        lambda ctx: [{"track": "hist", "complete": False, "age_seconds": 1200}],
    )
    monkeypatch.setattr(
        product_batch_progress,
        "_check_build_processes",
        lambda: ([], "ps: TimeoutExpired"),
    )
    monkeypatch.setattr(
        product_batch_progress,
        "_scan_track_progress",
        lambda ctx, track: _batch_progress_stub(track),
    )

    snapshot = product_batch_progress.fleet_batch_snapshot(ctx)

    assert snapshot["running_processes"] is None
    assert snapshot["errors"] == ["ps: TimeoutExpired"]
    assert snapshot["tracks"]["hist"]["health"] == "unknown"
    assert snapshot["tracks"]["hist"]["reason"] == "ps: TimeoutExpired"


def test_legacy_batch_snapshot_old_log_stays_dead_when_process_probe_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = fixture_context(tmp_path)
    monkeypatch.setattr(
        product_batch_progress,
        "_scan_preseed_logs",
        lambda ctx: [{"track": "hist", "complete": False, "age_seconds": 1200}],
    )
    monkeypatch.setattr(
        product_batch_progress,
        "_check_build_processes",
        lambda: ([], None),
    )
    monkeypatch.setattr(
        product_batch_progress,
        "_scan_track_progress",
        lambda ctx, track: _batch_progress_stub(track),
    )

    snapshot = product_batch_progress.fleet_batch_snapshot(ctx)

    assert snapshot["running_processes"] == 0
    assert "errors" not in snapshot
    assert snapshot["tracks"]["hist"]["health"] == "dead"
    assert "reason" not in snapshot["tracks"]["hist"]


@pytest.mark.usefixtures("product_fleet_batches")
def test_operations_timed_out_process_probe_degrades_batch_section(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client.app.state, "ctx", fixture_context(tmp_path))

    def timed_out_batches(ctx: MonitorContext | None = None) -> dict:
        return {
            "running_processes": None,
            "errors": ["ps: TimeoutExpired", "token=source-secret /tmp/private"],
            "tracks": {
                "hist": {
                    "health": "unknown",
                    "reason": "ps: TimeoutExpired",
                    "total_expected": 4,
                    "research_done": 1,
                    "remaining": 3,
                    "recent_30min": 0,
                    "throughput_per_hour": 0,
                }
            },
        }

    monkeypatch.setattr(product_batch_progress, "fleet_batch_snapshot", timed_out_batches)

    response = client.get("/api/fleet/operations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["batches"]["availability"] == "degraded"
    assert payload["batches"]["running_processes"] is None
    assert payload["batches"]["errors"] == ["ps: TimeoutExpired"]
    assert payload["batches"]["tracks"][0]["health"] == "unknown"
    assert "source-secret" not in response.text
    assert "private" not in response.text
