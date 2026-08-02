"""Deterministic authority-mode durability coverage for #6159."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
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


class _UnusedExecutor:
    """Enough of the executor contract for mode-only tests."""

    def close(self) -> None:
        return None


def _root(tmp_path: Path) -> Path:
    return tmp_path / "fleet-comms" / "v1"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
