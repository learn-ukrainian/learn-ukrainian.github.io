"""Deterministic authority-mode durability coverage for #6159."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.fleet_comms.authority import (
    AuthorityService,
    AuthorityServiceError,
    AuthorityStaleLeaseError,
)
from scripts.fleet_comms.cli import main
from scripts.fleet_comms.message_plane import MessagePlane, resolve_plane_mode
from scripts.fleet_comms.migrations import MIGRATIONS, apply_migrations
from scripts.fleet_comms.review_publisher import record_publication_receipt
from scripts.fleet_comms.routing_reservations import (
    RoutingReservationError,
    RoutingReservationLedger,
    RoutingReservationRequest,
    RoutingReservationUnavailable,
    RoutingSelection,
)


class _UnusedExecutor:
    """Enough of the executor contract for mode-only tests."""

    def close(self) -> None:
        return None


def _root(tmp_path: Path) -> Path:
    return tmp_path / "fleet-comms" / "v1"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _historic_routing_semantic_sha(request: RoutingReservationRequest) -> str:
    """Return the pre-#6342 request identity without envelope dimensions."""
    payload = {
        "author_family": request.author_family,
        "author_model": request.author_model,
        "authority_key": request.authority_key,
        "estimated_input_bytes": request.estimated_input_bytes,
        "requested_profile": request.requested_profile,
        "requested_reviewer": request.requested_reviewer,
        "requested_risk": request.requested_risk,
        "requested_role": request.requested_role,
        "route_mode": request.route_mode,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_authority_mode_resolves_without_changing_existing_modes() -> None:
    assert resolve_plane_mode("off") == "off"
    assert resolve_plane_mode("shadow") == "shadow"
    assert resolve_plane_mode("dual-write") == "dual_write"
    assert resolve_plane_mode("authority") == "authority"

    authority = MessagePlane(mode="authority", executor=_UnusedExecutor())
    shadow = MessagePlane(mode="shadow", executor=_UnusedExecutor())
    dual = MessagePlane(mode="dual_write", executor=_UnusedExecutor())
    try:
        # Authority mode does not authorize a legacy status/file projection.
        assert authority.may_mark_legacy_replied(None) is False
        # The established mode contract remains unchanged.
        assert shadow.may_mark_legacy_replied(None) is True
        assert dual.may_mark_legacy_replied(None) is False
    finally:
        authority.close()
        shadow.close()
        dual.close()


def test_authority_migration_reapplies_and_old_tables_remain_readable(tmp_path: Path) -> None:
    db = tmp_path / "comms.sqlite3"
    conn = sqlite3.connect(str(db))
    try:
        assert apply_migrations(conn) == MIGRATIONS[-1].version
        assert apply_migrations(conn) == MIGRATIONS[-1].version
        assert conn.execute("SELECT COUNT(*) FROM comms_messages").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM authority_jobs").fetchone()[0] == 0
        versions = [
            row[0]
            for row in conn.execute(
                "SELECT version FROM comms_schema_migrations ORDER BY version ASC"
            )
        ]
        assert versions == list(range(1, MIGRATIONS[-1].version + 1))
        assert MIGRATIONS[3].checksum == (
            "acfb1b810841f74035e39647ecbaf9482427068cd7770441c62b3d12e2415828"
        )
        v5_objects = {
            row[0]
            for row in conn.execute(
                """SELECT name FROM sqlite_master
                   WHERE name IN (
                     'idx_authority_job_subject_unique',
                     'authority_message_metadata_immutable_update',
                     'authority_comms_message_immutable_update',
                     'authority_context_revision_immutable_update'
                   )"""
            )
        }
        assert len(v5_objects) == 4

        # Preserve the one exact pre-merge soak checksum that embedded v5's
        # equivalent constraints in v4; arbitrary checksum drift still fails.
        conn.execute(
            "UPDATE comms_schema_migrations SET checksum = ? WHERE version = 4",
            ("a563b19a7a0cf84c5425a56f4338fc650ceb3266d26540aefe95cd64d371bb44",),
        )
        conn.commit()
        assert apply_migrations(conn) == MIGRATIONS[-1].version
    finally:
        conn.close()


def _claim_job(root: Path, worker_id: str) -> str | None:
    with AuthorityService(root=root) as service:
        lease = service.claim_next_job(worker_id, now="2035-01-01T00:00:00Z")
        return lease.job.job_id if lease is not None else None


def test_queue_claim_is_concurrent_and_exactly_once(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with AuthorityService(root=root) as service:
        job = service.enqueue_request(
            recipient="codex",
            body="review this bounded request",
            idempotency_key="concurrent-request",
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        claimed = list(pool.map(lambda worker: _claim_job(root, worker), ("worker-a", "worker-b")))

    assert claimed.count(job.job_id) == 1
    assert claimed.count(None) == 1
    with AuthorityService(root=root) as service:
        loaded = service.get_job(job.job_id)
        assert loaded.state == "running"
        assert loaded.attempt_count == 1
        assert loaded.fence_token == 1


def test_request_message_persists_initiating_source_and_target_agent(tmp_path: Path) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        job = service.enqueue_request(
            recipient="agy",
            sender="codex",
            body="bounded provenance request",
            idempotency_key="request-provenance",
        )
        message = service.get_message(job.subject_id)

    assert message.sender == "codex"
    assert message.recipient == "agy"
    assert message.provenance == {"Source": "codex", "Agent": "agy", "Via": "queue"}


def test_discussion_enqueue_atomically_creates_initial_state_and_provenance(
    tmp_path: Path,
) -> None:
    root = _root(tmp_path)
    with AuthorityService(root=root) as service:
        job = service.enqueue_discussion(
            channel="bounded-consultation",
            prompt="Compare the two bounded options.",
            participants=("kimi", "glm"),
            rounds=2,
            task_digest=_sha("task-6243"),
            correlation_id="correlation-6243",
            deadline_at="2036-06-01T01:00:00Z",
            source="codex",
            task_id="task-6243",
            idempotency_key="discussion-6243",
        )
        conversation = service.store.connection.execute(
            "SELECT source FROM conversations WHERE conversation_id = ?",
            (job.subject_id,),
        ).fetchone()
        events = service.store.connection.execute(
            """SELECT sequence, event_type, state, metadata_json
               FROM acp_conversation_events WHERE conversation_id = ?""",
            (job.subject_id,),
        ).fetchall()
        message = service.store.connection.execute(
            """SELECT metadata.provenance_json
               FROM comms_messages AS message
               JOIN authority_message_metadata AS metadata
                 ON metadata.message_id = message.message_id
               WHERE message.conversation_id = ? AND message.kind = 'discussion'""",
            (job.subject_id,),
        ).fetchone()

    assert conversation is not None and conversation["source"] == "codex"
    assert len(events) == 1
    assert tuple(events[0][:3]) == (1, "CREATED", "CREATED")
    assert json.loads(events[0]["metadata_json"]) == {"authority_reserved": True}
    assert message is not None
    assert json.loads(message["provenance_json"]) == {
        "Agent": "acp-controller",
        "Source": "codex",
        "Via": "queue",
        "task_id": "task-6243",
    }


def test_exact_claim_and_terminal_result_replay_do_not_take_unrelated_work(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with AuthorityService(root=root) as service:
        older = service.enqueue_request(
            recipient="codex", body="older", idempotency_key="older-job"
        )
        target = service.enqueue_request(
            recipient="codex", body="target", idempotency_key="target-job"
        )
        lease = service.claim_job(target.job_id, "sync-worker", now="2036-06-01T00:00:00Z")
        assert lease.job.job_id == target.job_id
        assert service.claim_job(
            target.job_id, "sync-worker", now="2036-06-01T00:00:01Z"
        ).fence_token == lease.fence_token
        complete = service.finish_job(
            target.job_id,
            worker_id="sync-worker",
            fence_token=lease.fence_token,
            state="complete",
            result=b"durable result",
            now="2036-06-01T00:00:02Z",
        )
        assert complete.state == "complete"
        assert service.read_job_result(target.job_id) == b"durable result"
        assert service.get_job(older.job_id).state == "queued"


def test_finish_job_matching_terminal_replay_is_idempotent(tmp_path: Path) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        job = service.enqueue_request(
            recipient="agy", body="idempotent finish", idempotency_key="terminal-replay"
        )
        lease = service.claim_job(job.job_id, "worker", now="2036-06-01T00:00:00Z")
        first = service.finish_job(
            job.job_id,
            worker_id="worker",
            fence_token=lease.fence_token,
            state="complete",
            result=b"provider response",
            now="2036-06-01T00:00:01Z",
        )

        replay = service.finish_job(
            job.job_id,
            worker_id="worker",
            fence_token=lease.fence_token,
            state="complete",
            result=b"provider response",
            now="2036-06-01T00:00:02Z",
        )

        assert replay == first
        assert service.read_job_result(job.job_id) == b"provider response"
        with pytest.raises(AuthorityStaleLeaseError, match="terminalization_conflict"):
            service.finish_job(
                job.job_id,
                worker_id="worker",
                fence_token=lease.fence_token,
                state="complete",
                result=b"different provider response",
                now="2036-06-01T00:00:03Z",
            )


def test_failed_job_retry_preserves_identity_and_attempt_history(tmp_path: Path) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        job = service.enqueue_request(
            recipient="glm",
            body="review immutable subject",
            idempotency_key="retry-subject",
        )
        first = service.claim_job(
            job.job_id,
            "worker-a",
            now="2036-06-01T00:00:00Z",
        )
        failed = service.finish_job(
            job.job_id,
            worker_id="worker-a",
            fence_token=first.fence_token,
            state="failed",
            result=b"transport failed",
            now="2036-06-01T00:00:01Z",
        )
        assert failed.state == "failed"
        retried = service.retry_job(job.job_id, now="2036-06-01T00:00:02Z")
        assert retried.job_id == job.job_id
        assert retried.state == "queued"
        assert retried.attempt_count == 1
        assert retried.result_artifact_id is None
        second = service.claim_job(
            job.job_id,
            "worker-b",
            now="2036-06-01T00:00:03Z",
        )
        assert second.fence_token == first.fence_token + 1
        assert second.job.attempt_count == 2
        events = [
            row[0]
            for row in service.store.connection.execute(
                "SELECT event_type FROM authority_job_events WHERE job_id = ? ORDER BY rowid",
                (job.job_id,),
            )
        ]
        assert events == ["enqueued", "claimed", "finished", "retried", "claimed"]


def test_failed_job_event_accepts_only_closed_body_free_failure_metadata(
    tmp_path: Path,
) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        job = service.enqueue_request(
            recipient="glm",
            body="bounded request",
            idempotency_key="safe-failure",
        )
        lease = service.claim_job(job.job_id, "worker", now="2036-06-01T00:00:00Z")
        service.finish_job(
            job.job_id,
            worker_id="worker",
            fence_token=lease.fence_token,
            state="failed",
            failure={"phase": "provider", "code": "rate_limited", "retryable": True},
            now="2036-06-01T00:00:01Z",
        )
        terminal = service.store.connection.execute(
            """SELECT metadata_json FROM authority_job_events
               WHERE job_id = ? AND event_type = 'finished'""",
            (job.job_id,),
        ).fetchone()

        second = service.enqueue_request(
            recipient="kimi",
            body="another bounded request",
            idempotency_key="unsafe-failure",
        )
        second_lease = service.claim_job(
            second.job_id, "worker", now="2036-06-01T00:00:02Z"
        )
        with pytest.raises(AuthorityServiceError, match="failure_metadata_fields_invalid"):
            service.finish_job(
                second.job_id,
                worker_id="worker",
                fence_token=second_lease.fence_token,
                state="failed",
                failure={
                    "phase": "provider",
                    "code": "unknown",
                    "retryable": False,
                    "exception": "password=must-not-persist",
                },
                now="2036-06-01T00:00:03Z",
            )

    assert terminal is not None
    assert json.loads(terminal["metadata_json"]) == {
        "failure": {"code": "rate_limited", "phase": "provider", "retryable": True},
        "worker_id": "worker",
    }


def test_expired_job_retry_keeps_dead_letter_receipt(tmp_path: Path) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        job = service.enqueue_request(
            recipient="glm",
            body="time-bounded review",
            deadline_at="2036-06-01T00:00:01Z",
            idempotency_key="expired-subject",
        )
        assert service.reclaim_expired_jobs(now="2036-06-01T00:00:02Z") == 1
        assert service.get_job(job.job_id).state == "expired"
        retried = service.retry_job(
            job.job_id,
            now="2036-06-01T00:00:02Z",
            deadline_at="2036-06-01T00:01:00Z",
        )
        assert retried.state == "queued"
        assert retried.job_id == job.job_id
        dead_letters = service.store.connection.execute(
            "SELECT COUNT(*) FROM authority_dead_letters WHERE job_id = ?",
            (job.job_id,),
        ).fetchone()[0]
        assert dead_letters == 1


def test_delivery_attempt_exhaustion_moves_to_dead_letter(tmp_path: Path) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        message = service.publish_message(
            sender="operator",
            body="deliver with bounded retries",
            recipients=("codex",),
            idempotency_key="delivery-exhaustion",
        )
        delivery_id = message.delivery_ids[0]
        first = service.claim_next_delivery(
            "codex",
            "worker-a",
            lease_seconds=1,
            max_attempts=2,
            now="2036-06-01T00:00:00Z",
        )
        assert first is not None and first.delivery.delivery_id == delivery_id
        assert service.reclaim_expired_deliveries(
            max_attempts=2,
            now="2036-06-01T00:00:02Z",
        ) == 1
        second = service.claim_next_delivery(
            "codex",
            "worker-b",
            lease_seconds=1,
            max_attempts=2,
            now="2036-06-01T00:00:03Z",
        )
        assert second is not None and second.delivery.attempt_count == 2
        assert service.reclaim_expired_deliveries(
            max_attempts=2,
            now="2036-06-01T00:00:05Z",
        ) == 1
        assert service.get_delivery(delivery_id).state == "dead_lettered"
        reason = service.store.connection.execute(
            "SELECT reason_code FROM authority_dead_letters WHERE delivery_id = ?",
            (delivery_id,),
        ).fetchone()[0]
        assert reason == "attempts_exhausted"


def test_formal_review_subject_is_exactly_once_across_key_versions(tmp_path: Path) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        first = service.enqueue_formal_review(
            repository="owner/repo",
            pr_number=42,
            head_sha="a" * 40,
            gate_kind="cross-family-review",
            snapshot=b"sealed snapshot",
            idempotency_key="formal-review:legacy-key",
        )
        replay = service.enqueue_formal_review(
            repository="owner/repo",
            pr_number=42,
            head_sha="a" * 40,
            gate_kind="cross-family-review",
            snapshot=b"sealed snapshot",
            idempotency_key="formal-review:safe-key",
        )
        assert replay.job_id == first.job_id
        with pytest.raises(
            AuthorityServiceError,
            match="idempotency_key_reused_with_different_payload",
        ):
            service._enqueue_job_tx(
                job_kind="formal_review",
                subject_id=first.subject_id,
                payload={"different": True},
                deadline_at=None,
                idempotency_key="formal-review:different-payload",
            )


def test_authority_message_rows_are_schema_immutable(tmp_path: Path) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        message = service.publish_message(
            sender="operator",
            body="immutable",
            idempotency_key="immutable-message",
        )
        with pytest.raises(sqlite3.IntegrityError, match="authority_message_immutable"):
            service.store.connection.execute(
                "UPDATE comms_messages SET body_inline = ? WHERE message_id = ?",
                ("altered", message.message_id),
            )


def test_channel_subscribers_receive_atomic_default_fanout(tmp_path: Path) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        service.create_channel("coordination", subscribers=("codex", "claude"))
        service.subscribe("coordination", ("grok",))
        message = service.publish_message(
            sender="operator",
            body="fan out once",
            channel="coordination",
            idempotency_key="fanout-message",
        )
        recipients = [
            row["recipient"]
            for row in service.store.connection.execute(
                """SELECT recipient FROM authority_deliveries
                   WHERE message_id = ? ORDER BY recipient ASC""",
                (message.message_id,),
            )
        ]
        assert recipients == ["claude", "codex", "grok"]
        wakes = service.store.connection.execute(
            "SELECT COUNT(*) FROM authority_wake_receipts WHERE delivery_id IN (?, ?, ?)",
            message.delivery_ids,
        ).fetchone()[0]
        assert wakes == 3


def test_authority_channel_cli_owns_context_and_fanout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _root(tmp_path)
    assert main(
        [
            "channel",
            "create",
            "coordination",
            "--subscriber",
            "codex",
            "--root",
            str(root),
        ]
    ) == 0
    created = json.loads(capsys.readouterr().out)
    assert created["subscribers"] == ["codex"]

    assert main(
        [
            "channel",
            "context",
            "coordination",
            "current bounded context",
            "--root",
            str(root),
        ]
    ) == 0
    revision = json.loads(capsys.readouterr().out)
    assert revision["sha256"] == _sha("current bounded context")

    publish_args = [
        "channel",
        "publish",
        "coordination",
        "deliver once",
        "--sender",
        "operator",
        "--idempotency-key",
        "cli-fanout-once",
        "--root",
        str(root),
    ]
    assert main(publish_args) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["delivery_ids"]
    assert first["context_revisions"]["channel"] == revision["context_revision_id"]
    assert first["content_included"] is False
    assert "deliver once" not in json.dumps(first)

    assert main(publish_args) == 0
    replay = json.loads(capsys.readouterr().out)
    assert replay["message_id"] == first["message_id"]


def test_crash_reclaim_fences_stale_job_and_delivery_workers(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with AuthorityService(root=root) as service:
        message = service.publish_message(
            sender="operator",
            body="durable body",
            channel=None,
            recipients=("codex",),
            idempotency_key="crash-message",
        )
        job = service.enqueue_request(
            recipient="claude",
            body="durable job",
            idempotency_key="crash-job",
        )
        delivery = service.claim_next_delivery(
            "codex", "worker-a", lease_seconds=1, now="2036-01-01T00:00:00Z"
        )
        lease = service.claim_next_job(
            "worker-a", lease_seconds=1, now="2036-01-01T00:00:00Z"
        )
        assert delivery is not None
        assert lease is not None and lease.job.job_id == job.job_id
        old_delivery_token = delivery.fence_token
        old_job_token = lease.fence_token
        assert message.delivery_ids == (delivery.delivery.delivery_id,)

    # Reopening a new service models a worker process that died after claim.
    with AuthorityService(root=root) as recovered:
        assert recovered.reclaim_expired_deliveries(now="2036-01-01T00:00:02Z") == 1
        assert recovered.reclaim_expired_jobs(now="2036-01-01T00:00:02Z") == 1
        redelivery = recovered.claim_next_delivery(
            "codex", "worker-b", now="2036-01-01T00:00:03Z"
        )
        rejob = recovered.claim_next_job("worker-b", now="2036-01-01T00:00:03Z")
        assert redelivery is not None and redelivery.fence_token == old_delivery_token + 1
        assert rejob is not None and rejob.fence_token == old_job_token + 1
        with pytest.raises(AuthorityStaleLeaseError, match="stale_delivery_lease"):
            recovered.acknowledge_delivery(
                redelivery.delivery.delivery_id,
                worker_id="worker-a",
                fence_token=old_delivery_token,
                now="2036-01-01T00:00:03Z",
            )
        with pytest.raises(AuthorityStaleLeaseError, match="stale_job_lease"):
            recovered.finish_job(
                job.job_id,
                worker_id="worker-a",
                fence_token=old_job_token,
                state="complete",
                now="2036-01-01T00:00:03Z",
            )
        assert recovered.acknowledge_delivery(
            redelivery.delivery.delivery_id,
            worker_id="worker-b",
            fence_token=redelivery.fence_token,
            acknowledgment=b"receipt",
            now="2036-01-01T00:00:04Z",
        ).state == "acknowledged"
        assert recovered.finish_job(
            job.job_id,
            worker_id="worker-b",
            fence_token=rejob.fence_token,
            state="complete",
            result=b"complete",
            now="2036-01-01T00:00:04Z",
        ).state == "complete"


def test_historical_import_is_idempotent_and_preserves_thread_provenance(tmp_path: Path) -> None:
    root = _root(tmp_path)
    root_body = "root body"
    reply_body = "reply body"
    records = [
        # Child first proves the import transaction preserves out-of-order links.
        {
            "external_id": "reply",
            "body": reply_body,
            "body_sha256": _sha(reply_body),
            "channel": "legacy",
            "sender": "codex",
            "recipient": "claude",
            "thread_id": "thread-1",
            "parent_id": "root",
            "correlation_id": "corr-1",
            "created_at": "2034-02-01T10:00:01Z",
            "provenance": {"Source": "bridge", "Agent": "codex", "Via": "broker"},
        },
        {
            "external_id": "root",
            "body": root_body,
            "body_sha256": _sha(root_body),
            "channel": "legacy",
            "sender": "operator",
            "recipient": "codex",
            "thread_id": "thread-1",
            "correlation_id": "corr-1",
            "created_at": "2034-02-01T10:00:00Z",
            "provenance": {"Source": "bridge", "Agent": "operator", "Via": "broker"},
        },
    ]
    with AuthorityService(root=root) as service:
        first = service.import_records(records, source="legacy-bridge")
        second = service.import_records(records, source="legacy-bridge")
        assert first.imported == 2
        assert first.replayed == 0
        assert second.imported == 0
        assert second.replayed == 2
        reply = service.get_message(first.message_ids[0])
        root_message = service.get_message(first.message_ids[1])
        assert reply.in_reply_to == root_message.message_id
        assert reply.thread_id == root_message.thread_id
        assert reply.thread_id == "thread-1"
        assert reply.correlation_id == "corr-1"
        assert reply.provenance["Source"] == "bridge"
        assert reply.provenance["Agent"] == "codex"
        assert reply.provenance["Via"] == "broker"
        assert reply.provenance["LegacyThreadId"] == "thread-1"
        assert reply.provenance["LegacyReplyTo"] == "root"
        assert service.read_message_body(reply.message_id) == reply_body
        count = service.store.connection.execute(
            "SELECT COUNT(*) FROM authority_import_receipts"
        ).fetchone()[0]
        assert count == 2


def test_authority_import_cli_does_not_echo_bodies(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _root(tmp_path)
    body = "private imported payload"
    records_path = tmp_path / "records.jsonl"
    records_path.write_text(
        json.dumps(
            {
                "external_id": "one",
                "body": body,
                "sender": "operator",
                "recipient": "codex",
                "created_at": "2034-02-01T10:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert main(
        [
            "authority-import",
            "--root",
            str(root),
            "--source",
            "legacy-jsonl",
            "--records-jsonl",
            str(records_path),
        ]
    ) == 0
    captured = capsys.readouterr()
    assert body not in captured.out
    assert json.loads(captured.out)["imported"] == 1


def test_legacy_sqlite_import_preserves_bridge_and_channel_metadata(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.sqlite3"
    conn = sqlite3.connect(str(legacy))
    try:
        conn.executescript(
            """
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
                task_id TEXT,
                from_llm TEXT,
                to_llm TEXT,
                message_type TEXT,
                content TEXT,
                data TEXT,
                timestamp TEXT
            );
            CREATE TABLE channels (
                name TEXT PRIMARY KEY,
                description TEXT,
                include TEXT,
                subscribers TEXT
            );
            CREATE TABLE channel_messages (
                message_id TEXT PRIMARY KEY,
                channel TEXT,
                thread_id TEXT,
                parent_id TEXT,
                correlation_id TEXT,
                from_agent TEXT,
                kind TEXT,
                body TEXT,
                context_rev_shared TEXT,
                context_rev_channel TEXT,
                created_at TEXT
            );
            CREATE TABLE deliveries (message_id TEXT, to_agent TEXT);
            """
        )
        conn.execute(
            """INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                1,
                "task-1",
                "operator",
                "codex",
                "ask",
                "bridge body",
                '{"Source":"bridge"}',
                "2037-01-01T00:00:00Z",
            ),
        )
        conn.execute(
            "INSERT INTO channels VALUES (?, ?, ?, ?)",
            ("coordination", "coordination work", "shared", "codex,claude"),
        )
        conn.execute(
            """INSERT INTO channel_messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "channel-1",
                "coordination",
                "thread-1",
                None,
                "corr-1",
                "codex",
                "post",
                "channel body",
                "",
                "",
                "2037-01-01T00:01:00Z",
            ),
        )
        conn.execute(
            """INSERT INTO channel_messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "channel-2",
                "coordination",
                "thread-1",
                "channel-1",
                "corr-1",
                "claude",
                "reply",
                "channel reply",
                "",
                "",
                "2037-01-01T00:02:00Z",
            ),
        )
        conn.execute("INSERT INTO deliveries VALUES (?, ?)", ("channel-1", "claude"))
        conn.commit()
    finally:
        conn.close()

    with AuthorityService(root=_root(tmp_path)) as service:
        result = service.import_legacy_sqlite(legacy, source="legacy-broker-v1")
        assert result.imported == 3
        channel = service.get_channel("coordination")
        assert channel.subscribers == ("claude", "codex")
        imported_channel = service.get_message(result.message_ids[1])
        assert imported_channel.correlation_id == "corr-1"
        assert imported_channel.provenance["Via"] == "legacy-channel"
        assert service.read_message_body(imported_channel.message_id) == "channel body"
        imported_reply = service.get_message(result.message_ids[2])
        assert imported_reply.in_reply_to == imported_channel.message_id
        assert imported_reply.conversation_id == imported_channel.conversation_id
        assert service.read_message_body(imported_reply.message_id) == "channel reply"


def test_formal_review_refuses_head_mismatch_before_verdict_publication(tmp_path: Path) -> None:
    root = _root(tmp_path)
    head = "a" * 40
    with AuthorityService(root=root) as service:
        queued = service.enqueue_formal_review(
            repository="owner/repo",
            pr_number=42,
            head_sha=head,
            gate_kind="cross-family-review",
            snapshot=b'{"head":"' + head.encode("ascii") + b'"}',
            idempotency_key="review-snapshot",
        )
        review = service.require_publishable_formal_review(
            queued.subject_id, current_head_sha=head
        )
        assert review.snapshot_artifact_id is not None
        with pytest.raises(AuthorityServiceError, match="formal_review_head_mismatch"):
            service.require_publishable_formal_review(
                queued.subject_id, current_head_sha="b" * 40
            )
        seal = service.store.connection.execute(
            """SELECT snapshot_artifact_id, snapshot_sha256
               FROM formal_review_snapshot_seals WHERE review_id = ?""",
            (queued.subject_id,),
        ).fetchone()
        assert seal is not None
        assert seal["snapshot_artifact_id"] == review.snapshot_artifact_id


def _substitution_request(authority_key: str, idempotency_key: str = "substitute") -> RoutingReservationRequest:
    return RoutingReservationRequest(
        authority_key=authority_key,
        idempotency_key=idempotency_key,
        initiator="codex/orchestrator",
        author_model="gpt-5.6-sol",
        author_family="openai",
        requested_role="code:high",
        requested_profile="code",
        requested_risk="high",
        route_mode="explicit",
        estimated_input_bytes=123,
        requested_reviewer="glm-5.2",
        required_capabilities=("code_review", "sealed_evidence"),
        data_egress_policy="approved",
        isolation_required=True,
    )


def _substitution_selection(_context: object) -> RoutingSelection:
    return RoutingSelection(
        candidate="glm-5.2",
        route="glm",
        model="glm-5.2",
        family="zhipu",
        quota_bucket="glm-weekly",
        credential_bucket="glm-key-a",
        quota_limit=1,
        credential_limit=1,
        policy_version="resolver-v1",
        quota_snapshot={"remaining": 1},
        quota_fresh_at="2035-01-01T00:00:00Z",
        trace={"source": "fixture"},
    )


def _failed_formal_substitution_fixture(
    service: AuthorityService,
    *,
    legacy_envelope: bool = False,
) -> tuple[object, object, RoutingReservationRequest, dict[str, object]]:
    """Create the sole admissible post-result-invalid substitution boundary."""
    head = "a" * 40
    authority_key = "formal-review:substitution-fixture"
    job = service.enqueue_formal_review(
        repository="owner/repo",
        pr_number=42,
        head_sha=head,
        gate_kind="cross-family-review",
        snapshot=b'{"head":"' + head.encode("ascii") + b'"}',
        idempotency_key=authority_key,
    )
    review = service.require_publishable_formal_review(job.subject_id, current_head_sha=head)
    assert review.snapshot_artifact_id is not None
    egress_policy = None if legacy_envelope else "approved"
    original_request = RoutingReservationRequest(
        authority_key=authority_key,
        idempotency_key="original",
        initiator="codex/orchestrator",
        author_model="gpt-5.6-sol",
        author_family="openai",
        requested_role="code:high",
        requested_profile="code",
        requested_risk="high",
        route_mode="auto",
        estimated_input_bytes=123,
        required_capabilities=("code_review", "sealed_evidence"),
        data_egress_policy=egress_policy,
        isolation_required=True,
    )
    with RoutingReservationLedger(store=service.store) as ledger:
        original_append = ledger._append_decision_tx
        if legacy_envelope:
            def append_without_envelope(
                reservation_id: str,
                event_type: str,
                state: str,
                evidence: dict[str, object],
                created_at: str,
            ) -> None:
                old_evidence = dict(evidence)
                if event_type == "reserved":
                    old_evidence.pop("authorization_envelope", None)
                original_append(
                    reservation_id,
                    event_type,
                    state,
                    old_evidence,
                    created_at,
                )

            ledger._append_decision_tx = append_without_envelope
        original = ledger.reserve_selection(
            original_request,
            lambda _context: RoutingSelection(
                candidate="grok-4.5",
                route="grok",
                model="grok-4.5",
                family="xai",
                quota_bucket="grok-weekly",
                credential_bucket="grok-key-a",
                quota_limit=1,
                credential_limit=1,
                policy_version="resolver-v1",
                quota_snapshot={"remaining": 1},
                quota_fresh_at="2035-01-01T00:00:00Z",
                trace={"source": "fixture"},
            ),
            now="2035-01-01T00:00:00Z",
        )
        if legacy_envelope:
            ledger._append_decision_tx = original_append
            ledger._conn.execute(
                "UPDATE routing_reservations SET semantic_sha256 = ? WHERE reservation_id = ?",
                (_historic_routing_semantic_sha(original_request), original.reservation_id),
            )
            ledger._conn.commit()
        ledger.settle(
            original.reservation_id,
            status="failed",
            failure_classification="result_invalid",
            now="2035-01-01T00:00:01Z",
        )
    lease = service.claim_job(job.job_id, "fixture-worker", now="2035-01-01T00:00:00Z")
    service.finish_job(
        job.job_id,
        worker_id="fixture-worker",
        fence_token=lease.fence_token,
        state="failed",
        result=b'{"failure_classification":"result_invalid"}',
        now="2035-01-01T00:00:01Z",
    )
    request = replace(_substitution_request(authority_key), data_egress_policy=egress_policy)
    evidence = {
        "prior_reservation_id": original.reservation_id,
        "reason": "operator-authorized result-invalid substitution",
        "review_id": review.review_id,
        "authority_job_id": job.job_id,
        "authority_key": authority_key,
        "data_egress_policy": egress_policy,
        "new_requested_reviewer": "glm-5.2",
    }
    return job, review, request, evidence


def test_authority_authorizes_one_atomic_result_invalid_substitution(tmp_path: Path) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        job, review, request, evidence = _failed_formal_substitution_fixture(service)
        reservation = service.authorize_formal_review_substitution(
            authority_job_id=job.job_id,
            review_id=review.review_id,
            current_head_sha="a" * 40,
            expected_snapshot_artifact_id=review.snapshot_artifact_id,
            routing_request=request,
            selector=_substitution_selection,
            substitution_evidence=evidence,
            ttl_seconds=60,
            now="2035-01-01T00:00:02Z",
        )

        assert reservation.attempt == 2
        assert service.get_job(job.job_id).state == "queued"
        with RoutingReservationLedger(store=service.store) as ledger:
            assert [item.event_type for item in ledger.decisions(reservation.reservation_id)] == [
                "reserved",
                "authorized_substitution",
            ]


def test_authority_authorizes_the_pre_6342_formal_review_default_envelope(
    tmp_path: Path,
) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        job, review, request, evidence = _failed_formal_substitution_fixture(
            service,
            legacy_envelope=True,
        )
        reservation = service.authorize_formal_review_substitution(
            authority_job_id=job.job_id,
            review_id=review.review_id,
            current_head_sha="a" * 40,
            expected_snapshot_artifact_id=review.snapshot_artifact_id,
            routing_request=request,
            selector=_substitution_selection,
            substitution_evidence=evidence,
            ttl_seconds=60,
            now="2035-01-01T00:00:02Z",
        )

        assert reservation.attempt == 2
        with RoutingReservationLedger(store=service.store) as ledger:
            prior = next(
                item
                for item in ledger.decisions(evidence["prior_reservation_id"])
                if item.event_type == "legacy_authorization_envelope_reconstructed"
            )
            substitute = next(
                item
                for item in ledger.decisions(reservation.reservation_id)
                if item.event_type == "authorized_substitution"
            )
        assert prior.evidence["source"] == "formal-review-default-contract-before-6342"
        assert (
            substitute.evidence["prior_authorization_envelope_source"]
            == "formal-review-default-contract-before-6342"
        )
        assert substitute.evidence["requested_data_egress_policy"] is None


def test_authority_identical_substitution_replay_returns_existing_reservation(tmp_path: Path) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        job, review, request, evidence = _failed_formal_substitution_fixture(service)
        first = service.authorize_formal_review_substitution(
            authority_job_id=job.job_id,
            review_id=review.review_id,
            current_head_sha="a" * 40,
            expected_snapshot_artifact_id=review.snapshot_artifact_id,
            routing_request=request,
            selector=_substitution_selection,
            substitution_evidence=evidence,
            ttl_seconds=60,
            now="2035-01-01T00:00:02Z",
        )
        assert service.authorize_formal_review_substitution(
            authority_job_id=job.job_id,
            review_id=review.review_id,
            current_head_sha="a" * 40,
            expected_snapshot_artifact_id=review.snapshot_artifact_id,
            routing_request=request,
            selector=_substitution_selection,
            substitution_evidence=evidence,
            ttl_seconds=60,
            now="2035-01-01T00:00:03Z",
        ) == first


def test_authority_refuses_replay_after_substitution_reservation_ttl_expiry(tmp_path: Path) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        job, review, request, evidence = _failed_formal_substitution_fixture(service)
        substitute = service.authorize_formal_review_substitution(
            authority_job_id=job.job_id,
            review_id=review.review_id,
            current_head_sha="a" * 40,
            expected_snapshot_artifact_id=review.snapshot_artifact_id,
            routing_request=request,
            selector=_substitution_selection,
            substitution_evidence=evidence,
            ttl_seconds=1,
            now="2035-01-01T00:00:02Z",
        )
        with RoutingReservationLedger(store=service.store) as ledger:
            expired = ledger.recover_expired(now="2035-01-01T00:00:04Z")
            assert len(expired) == 1 and expired[0].reservation_id == substitute.reservation_id
            assert ledger.get(substitute.reservation_id).status == "expired"

        with pytest.raises(
            RoutingReservationError,
            match="substitution_idempotent_replay_not_active",
        ):
            service.authorize_formal_review_substitution(
                authority_job_id=job.job_id,
                review_id=review.review_id,
                current_head_sha="a" * 40,
                expected_snapshot_artifact_id=review.snapshot_artifact_id,
                routing_request=request,
                selector=_substitution_selection,
                substitution_evidence=evidence,
                ttl_seconds=1,
                now="2035-01-01T00:00:04Z",
            )
        assert service.get_job(job.job_id).state == "queued"


@pytest.mark.parametrize("rejection", ("sealed", "published", "head", "snapshot", "job", "review"))
def test_authority_substitution_rejects_terminal_or_identity_drift(
    tmp_path: Path,
    rejection: str,
) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        job, review, request, evidence = _failed_formal_substitution_fixture(service)
        kwargs = {
            "authority_job_id": job.job_id,
            "review_id": review.review_id,
            "current_head_sha": "a" * 40,
            "expected_snapshot_artifact_id": review.snapshot_artifact_id,
            "routing_request": request,
            "selector": _substitution_selection,
            "substitution_evidence": evidence,
            "ttl_seconds": 60,
            "now": "2035-01-01T00:00:02Z",
        }
        error = ""
        if rejection == "sealed":
            artifact = service.store.store_bytes(b"sealed", producer="test")
            service.store.connection.execute(
                "UPDATE formal_review_jobs SET sealed_verdict_artifact_id = ? WHERE review_id = ?",
                (artifact.artifact_id, review.review_id),
            )
            service.store.connection.commit()
            error = "substitution_verdict_already_accepted"
        elif rejection == "published":
            record_publication_receipt(
                service.store.connection,
                review_id=review.review_id,
                head_sha="a" * 40,
            )
            error = "substitution_verdict_already_published"
        elif rejection == "head":
            kwargs["current_head_sha"] = "b" * 40
            error = "formal_review_head_mismatch"
        elif rejection == "snapshot":
            kwargs["expected_snapshot_artifact_id"] = "artifact_wrong"
            error = "substitution_snapshot_drift"
        elif rejection == "job":
            other = service.enqueue_request(
                recipient="codex",
                body="unrelated",
                idempotency_key="unrelated-authority-job",
            )
            kwargs["authority_job_id"] = other.job_id
            error = "substitution_authority_job_mismatch"
        else:
            kwargs["review_id"] = "review_wrong"
            error = "substitution_authority_job_mismatch"

        with pytest.raises(AuthorityServiceError, match=error):
            service.authorize_formal_review_substitution(**kwargs)
        assert service.get_job(job.job_id).state == "failed"


@pytest.mark.parametrize("selector_kind", ("none", "capacity"))
def test_authority_substitution_refusal_rolls_back_requeue_and_reservation(
    tmp_path: Path,
    selector_kind: str,
) -> None:
    with AuthorityService(root=_root(tmp_path)) as service:
        job, review, request, evidence = _failed_formal_substitution_fixture(service)

        def no_route_selector(_context: object) -> None:
            return None

        selector = no_route_selector
        if selector_kind == "capacity":
            with RoutingReservationLedger(store=service.store) as ledger:
                ledger.reserve_selection(
                    _substitution_request("formal-review:capacity-blocker", "blocker"),
                    _substitution_selection,
                    now="2035-01-01T00:00:02Z",
                )
            selector = _substitution_selection
        with pytest.raises(RoutingReservationUnavailable):
            service.authorize_formal_review_substitution(
                authority_job_id=job.job_id,
                review_id=review.review_id,
                current_head_sha="a" * 40,
                expected_snapshot_artifact_id=review.snapshot_artifact_id,
                routing_request=request,
                selector=selector,
                substitution_evidence=evidence,
                ttl_seconds=60,
                now="2035-01-01T00:00:02Z",
            )

        assert service.get_job(job.job_id).state == "failed"
        with RoutingReservationLedger(store=service.store) as ledger:
            attempts = [
                item for item in (ledger.latest_for_authority_key(request.authority_key),)
                if item is not None
            ]
            assert len(attempts) == 1 and attempts[0].attempt == 1
        events = service.store.connection.execute(
            "SELECT event_type FROM authority_job_events WHERE job_id = ? ORDER BY rowid",
            (job.job_id,),
        ).fetchall()
        assert "substitution_authorized" not in [row[0] for row in events]


def _concurrent_substitution(root: Path, job_id: str, review_id: str, snapshot: str, request: RoutingReservationRequest, evidence: dict[str, str]) -> str:
    with AuthorityService(root=root) as service:
        try:
            return service.authorize_formal_review_substitution(
                authority_job_id=job_id,
                review_id=review_id,
                current_head_sha="a" * 40,
                expected_snapshot_artifact_id=snapshot,
                routing_request=request,
                selector=_substitution_selection,
                substitution_evidence=evidence,
                ttl_seconds=60,
                now="2035-01-01T00:00:02Z",
            ).reservation_id
        except AuthorityServiceError as exc:
            return str(exc)


def test_concurrent_substitution_requests_do_not_fork_authority_or_reservation(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with AuthorityService(root=root) as service:
        job, review, request, evidence = _failed_formal_substitution_fixture(service)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(
            pool.map(
                lambda _index: _concurrent_substitution(
                    root,
                    job.job_id,
                    review.review_id,
                    str(review.snapshot_artifact_id),
                    request,
                    evidence,
                ),
                range(2),
            )
        )
    reservation_ids = [value for value in outcomes if value.startswith("routing-reservation_")]
    assert reservation_ids and len(set(reservation_ids)) == 1
    assert all(
        value.startswith("routing-reservation_") or value == "substitution_authority_job_not_failed"
        for value in outcomes
    )
    with AuthorityService(root=root) as service, RoutingReservationLedger(store=service.store) as ledger:
        reservation = ledger.latest_for_authority_key(request.authority_key)
        assert reservation is not None and reservation.attempt == 2
        assert service.get_job(job.job_id).state == "queued"
