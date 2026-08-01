"""Authority-mode service for the Fleet Communications durable plane.

The service is deliberately a layer over the existing Fleet Comms SQLite and
artifact store.  It does not read legacy bridge files, does not write legacy
broker tables, and never turns a file diary into an authority.  Callers may
use it only after explicitly selecting ``FLEET_COMMS_MESSAGE_PLANE=authority``.

Every writer uses ``BEGIN IMMEDIATE`` and immutable content-addressed artifacts:
message fan-out, durable jobs, lease hand-off, historical import, and formal
review snapshot sealing are therefore recoverable after a process crash.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from scripts.fleet_comms.artifacts import ArtifactRecord, ArtifactStore
from scripts.fleet_comms.contracts import new_id
from scripts.fleet_comms.formal_review_jobs import (
    FormalReviewJob,
    FormalReviewJobsError,
    FormalReviewJobService,
)
from scripts.fleet_comms.migrations import MIGRATIONS, apply_migrations
from scripts.fleet_comms.review_publication import SealedVerdict, parse_sealed_verdict_payload

AuthorityJobKind = Literal["request", "discussion", "formal_review"]
AuthorityJobState = Literal[
    "queued", "running", "complete", "failed", "expired", "dead_lettered"
]
AuthorityDeliveryState = Literal[
    "queued", "running", "acknowledged", "failed", "expired", "dead_lettered"
]

_JOB_KINDS = frozenset({"request", "discussion", "formal_review"})
_JOB_TERMINAL = frozenset({"complete", "failed", "expired", "dead_lettered"})
_DELIVERY_TERMINAL = frozenset({"acknowledged", "failed", "expired", "dead_lettered"})
_WAKE_STATES = {"emitted": 0, "received": 1, "consumed": 2}
_AUTHORITY_SCHEMA_VERSION = 5


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime | None = None) -> str:
    return (value or _utc_now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: str, *, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise AuthorityServiceError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise AuthorityServiceError(f"invalid_{field}")
    return parsed.astimezone(UTC)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _nonempty(value: str | None, *, field: str) -> str:
    normalized = " ".join(str(value or "").split())
    if not normalized:
        raise AuthorityServiceError(f"{field}_required")
    return normalized


def _normalize_recipients(recipients: Iterable[str] | None) -> tuple[str, ...]:
    if recipients is None:
        return ()
    normalized = {_nonempty(recipient, field="recipient") for recipient in recipients}
    return tuple(sorted(normalized))


def _safe_json_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    try:
        encoded = _canonical_json(dict(value))
        loaded = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise AuthorityServiceError("metadata_must_be_json_serializable") from exc
    if not isinstance(loaded, dict):  # pragma: no cover - dict(value) guarantees this
        raise AuthorityServiceError("metadata_must_be_object")
    return loaded


class AuthorityServiceError(RuntimeError):
    """Authority writer rejected an invalid or unsafe operation."""


class AuthorityStaleLeaseError(AuthorityServiceError):
    """A worker attempted to complete a superseded lease."""


@dataclass(frozen=True, slots=True)
class AuthorityChannel:
    channel_id: str
    name: str
    metadata: dict[str, Any]
    current_context_revision_id: str | None
    created_at: str
    subscribers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ContextRevision:
    context_revision_id: str
    channel_id: str
    sha256: str
    artifact_id: str
    created_at: str


@dataclass(frozen=True, slots=True)
class AuthorityMessage:
    message_id: str
    conversation_id: str
    in_reply_to: str | None
    channel_id: str | None
    thread_id: str
    correlation_id: str | None
    sender: str
    recipient: str | None
    kind: str
    body_artifact_id: str
    content_sha256: str
    context_revisions: dict[str, str]
    provenance: dict[str, Any]
    created_at: str
    delivery_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AuthorityDelivery:
    delivery_id: str
    message_id: str
    recipient: str
    state: str
    deadline_at: str | None
    lease_owner: str | None
    lease_expires_at: str | None
    fence_token: int
    attempt_count: int
    acknowledgment_artifact_id: str | None
    terminal_sha256: str | None
    created_at: str
    updated_at: str
    completed_at: str | None


@dataclass(frozen=True, slots=True)
class AuthorityDeliveryLease:
    delivery: AuthorityDelivery
    body_artifact_id: str
    content_sha256: str

    @property
    def fence_token(self) -> int:
        return self.delivery.fence_token


@dataclass(frozen=True, slots=True)
class AuthorityJob:
    job_id: str
    job_kind: str
    subject_id: str
    payload_artifact_id: str
    state: str
    deadline_at: str | None
    lease_owner: str | None
    lease_expires_at: str | None
    fence_token: int
    attempt_count: int
    result_artifact_id: str | None
    terminal_sha256: str | None
    idempotency_key: str
    created_at: str
    updated_at: str
    completed_at: str | None


@dataclass(frozen=True, slots=True)
class AuthorityJobLease:
    job: AuthorityJob

    @property
    def fence_token(self) -> int:
        return self.job.fence_token


@dataclass(frozen=True, slots=True)
class HistoricalImportResult:
    imported: int
    replayed: int
    message_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "imported": self.imported,
            "replayed": self.replayed,
            "message_ids": list(self.message_ids),
            "content_included": False,
        }


class AuthorityService:
    """Transactional authority API backed by the shared Fleet Comms store."""

    def __init__(
        self,
        *,
        store: ArtifactStore | None = None,
        root: Path | None = None,
    ) -> None:
        self.store = store or ArtifactStore(root=root)
        self._owns_store = store is None
        self._conn = self.store.connection
        apply_migrations(self._conn)
        self._require_authority_schema()

    def close(self) -> None:
        if self._owns_store:
            self.store.close()

    def __enter__(self) -> AuthorityService:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Channel / immutable message surface

    def create_channel(
        self,
        name: str,
        *,
        subscribers: Iterable[str] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> AuthorityChannel:
        """Create a channel once; exact repeats are idempotent."""
        channel_name = _nonempty(name, field="channel")
        normalized_subscribers = _normalize_recipients(subscribers)
        meta = _safe_json_mapping(metadata)
        with self._write_transaction():
            row = self._conn.execute(
                "SELECT * FROM authority_channels WHERE name = ?", (channel_name,)
            ).fetchone()
            if row is None:
                channel_id = new_id("authority-channel")
                created_at = _iso()
                self._conn.execute(
                    """INSERT INTO authority_channels(
                        channel_id, name, metadata_json, created_at
                    ) VALUES (?, ?, ?, ?)""",
                    (channel_id, channel_name, _canonical_json(meta), created_at),
                )
            else:
                channel_id = str(row["channel_id"])
                existing = self._decode_mapping(row["metadata_json"], field="channel_metadata")
                if metadata is not None and existing != meta:
                    raise AuthorityServiceError("channel_metadata_conflict")
            for recipient in normalized_subscribers:
                self._conn.execute(
                    """INSERT OR IGNORE INTO authority_channel_subscribers(
                        channel_id, recipient, metadata_json, created_at
                    ) VALUES (?, ?, '{}', ?)""",
                    (channel_id, recipient, _iso()),
                )
        return self.get_channel(channel_name)

    def subscribe(
        self,
        channel: str,
        recipients: Iterable[str],
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> AuthorityChannel:
        """Add durable future fan-out subscribers without rewriting history."""
        channel_name = _nonempty(channel, field="channel")
        recipients_norm = _normalize_recipients(recipients)
        if not recipients_norm:
            raise AuthorityServiceError("subscriber_required")
        subscriber_metadata = _safe_json_mapping(metadata)
        with self._write_transaction():
            channel_row = self._require_channel_tx(channel_name)
            for recipient in recipients_norm:
                existing = self._conn.execute(
                    """SELECT metadata_json FROM authority_channel_subscribers
                       WHERE channel_id = ? AND recipient = ?""",
                    (str(channel_row["channel_id"]), recipient),
                ).fetchone()
                if existing is not None:
                    existing_metadata = self._decode_mapping(
                        existing["metadata_json"], field="subscriber_metadata"
                    )
                    if metadata is not None and existing_metadata != subscriber_metadata:
                        raise AuthorityServiceError("subscriber_metadata_conflict")
                    continue
                self._conn.execute(
                    """INSERT INTO authority_channel_subscribers(
                        channel_id, recipient, metadata_json, created_at
                    ) VALUES (?, ?, ?, ?)""",
                    (
                        str(channel_row["channel_id"]),
                        recipient,
                        _canonical_json(subscriber_metadata),
                        _iso(),
                    ),
                )
        return self.get_channel(channel_name)

    def get_channel(self, name: str) -> AuthorityChannel:
        channel_name = _nonempty(name, field="channel")
        row = self._conn.execute(
            "SELECT * FROM authority_channels WHERE name = ?", (channel_name,)
        ).fetchone()
        if row is None:
            raise AuthorityServiceError("channel_not_found")
        subscriber_rows = self._conn.execute(
            """SELECT recipient FROM authority_channel_subscribers
               WHERE channel_id = ? ORDER BY recipient ASC""",
            (str(row["channel_id"]),),
        ).fetchall()
        return AuthorityChannel(
            channel_id=str(row["channel_id"]),
            name=str(row["name"]),
            metadata=self._decode_mapping(row["metadata_json"], field="channel_metadata"),
            current_context_revision_id=(
                str(row["current_context_revision_id"])
                if row["current_context_revision_id"] is not None
                else None
            ),
            created_at=str(row["created_at"]),
            subscribers=tuple(str(item["recipient"]) for item in subscriber_rows),
        )

    def set_channel_context(
        self,
        channel: str,
        body: str,
        *,
        producer: str = "authority-service",
    ) -> ContextRevision:
        """Store an immutable context revision and make it the channel current revision."""
        if not isinstance(body, str):
            raise AuthorityServiceError("context_body_must_be_text")
        channel_name = _nonempty(channel, field="channel")
        producer_name = _nonempty(producer, field="producer")
        body_bytes = body.encode("utf-8")
        digest = _sha256_bytes(body_bytes)
        with self._write_transaction():
            channel_row = self._require_channel_tx(channel_name)
            existing = self._conn.execute(
                """SELECT * FROM authority_context_revisions
                   WHERE channel_id = ? AND sha256 = ?""",
                (str(channel_row["channel_id"]), digest),
            ).fetchone()
            if existing is None:
                artifact = self.store.store_bytes(
                    body_bytes,
                    producer=producer_name,
                    retention_class="channel-context",
                    mime_type="text/plain; charset=utf-8",
                    logical_filename=f"{channel_row['channel_id']!s}.context.txt",
                    commit=False,
                )
                revision_id = new_id("context-revision")
                created_at = _iso()
                self._conn.execute(
                    """INSERT INTO authority_context_revisions(
                        context_revision_id, channel_id, sha256, artifact_id, created_at
                    ) VALUES (?, ?, ?, ?, ?)""",
                    (
                        revision_id,
                        str(channel_row["channel_id"]),
                        digest,
                        artifact.artifact_id,
                        created_at,
                    ),
                )
                self._conn.execute(
                    """UPDATE authority_channels
                       SET current_context_revision_id = ? WHERE channel_id = ?""",
                    (revision_id, str(channel_row["channel_id"])),
                )
                return ContextRevision(
                    context_revision_id=revision_id,
                    channel_id=str(channel_row["channel_id"]),
                    sha256=digest,
                    artifact_id=artifact.artifact_id,
                    created_at=created_at,
                )
            revision = self._context_revision_from_row(existing)
            self._conn.execute(
                """UPDATE authority_channels
                   SET current_context_revision_id = ? WHERE channel_id = ?""",
                (revision.context_revision_id, revision.channel_id),
            )
            return revision

    def publish_message(
        self,
        *,
        sender: str,
        body: str,
        channel: str | None = None,
        recipients: Iterable[str] | None = None,
        kind: str = "message",
        conversation_id: str | None = None,
        in_reply_to: str | None = None,
        correlation_id: str | None = None,
        provenance: Mapping[str, Any] | None = None,
        context_revisions: Mapping[str, str] | None = None,
        deadline_at: str | None = None,
        created_at: str | None = None,
        idempotency_key: str | None = None,
    ) -> AuthorityMessage:
        """Append an immutable message and atomically fan it out to subscribers."""
        message_key = idempotency_key or new_id("authority-message-key")
        with self._write_transaction():
            return self._publish_message_tx(
                sender=sender,
                body=body,
                channel=channel,
                recipients=recipients,
                kind=kind,
                conversation_id=conversation_id,
                in_reply_to=in_reply_to,
                correlation_id=correlation_id,
                provenance=provenance,
                context_revisions=context_revisions,
                deadline_at=deadline_at,
                created_at=created_at,
                idempotency_key=message_key,
            )

    def get_message(self, message_id: str) -> AuthorityMessage:
        mid = _nonempty(message_id, field="message_id")
        row = self._conn.execute(
            """SELECT m.message_id, m.conversation_id, m.in_reply_to, m.kind, m.sender,
                      m.recipient, m.body_artifact_id, m.content_sha256, m.created_at,
                      meta.channel_id, meta.thread_id, meta.correlation_id,
                      meta.context_revisions_json, meta.provenance_json
               FROM comms_messages m
               JOIN authority_message_metadata meta ON meta.message_id = m.message_id
               WHERE m.message_id = ?""",
            (mid,),
        ).fetchone()
        if row is None:
            raise AuthorityServiceError("message_not_found")
        delivery_rows = self._conn.execute(
            """SELECT delivery_id FROM authority_deliveries
               WHERE message_id = ? ORDER BY delivery_id ASC""",
            (mid,),
        ).fetchall()
        artifact_id = row["body_artifact_id"]
        if artifact_id is None:
            raise AuthorityServiceError("message_body_artifact_missing")
        return AuthorityMessage(
            message_id=str(row["message_id"]),
            conversation_id=str(row["conversation_id"]),
            in_reply_to=str(row["in_reply_to"]) if row["in_reply_to"] is not None else None,
            channel_id=str(row["channel_id"]) if row["channel_id"] is not None else None,
            thread_id=str(row["thread_id"]),
            correlation_id=(str(row["correlation_id"]) if row["correlation_id"] else None),
            sender=str(row["sender"]),
            recipient=str(row["recipient"]) if row["recipient"] is not None else None,
            kind=str(row["kind"]),
            body_artifact_id=str(artifact_id),
            content_sha256=str(row["content_sha256"]),
            context_revisions=self._decode_string_mapping(row["context_revisions_json"]),
            provenance=self._decode_mapping(row["provenance_json"], field="provenance"),
            created_at=str(row["created_at"]),
            delivery_ids=tuple(str(item["delivery_id"]) for item in delivery_rows),
        )

    def read_message_body(self, message_id: str) -> str:
        """Read and integrity-check a message body without logging it."""
        message = self.get_message(message_id)
        try:
            return self.store.read_bytes(message.body_artifact_id).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AuthorityServiceError("message_body_not_utf8") from exc

    # ------------------------------------------------------------------
    # Worker queue surface

    def enqueue_request(
        self,
        *,
        recipient: str,
        body: str,
        sender: str = "authority-service",
        channel: str = "requests",
        deadline_at: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> AuthorityJob:
        """Queue an ordinary request atomically with its immutable message."""
        key = idempotency_key or new_id("authority-request-key")
        recipient_name = _nonempty(recipient, field="recipient")
        self._ensure_channel(channel)
        payload = {
            "recipient": recipient_name,
            "metadata": _safe_json_mapping(metadata),
            "message_body_sha256": _sha256_bytes(body.encode("utf-8")),
        }
        with self._write_transaction():
            existing = self._find_job_by_key_tx("request", key)
            if existing is not None:
                self._assert_job_payload(existing, payload)
                return existing
            message = self._publish_message_tx(
                sender=sender,
                body=body,
                channel=channel,
                recipients=(recipient_name,),
                kind="request",
                provenance={"Source": "authority", "Agent": sender, "Via": "queue"},
                deadline_at=deadline_at,
                idempotency_key=f"request-message:{key}",
            )
            return self._enqueue_job_tx(
                job_kind="request",
                subject_id=message.message_id,
                payload=payload,
                deadline_at=deadline_at,
                idempotency_key=key,
            )

    def enqueue_discussion(
        self,
        *,
        channel: str,
        prompt: str,
        participants: Sequence[str],
        rounds: int,
        task_digest: str,
        correlation_id: str,
        deadline_at: str,
        token_budget: int = 8_000,
        content_budget_bytes: int = 24_000,
        idempotency_key: str | None = None,
    ) -> AuthorityJob:
        """Queue a bounded (one-to-three round) discussion without invoking it."""
        key = idempotency_key or new_id("authority-discussion-key")
        channel_name = _nonempty(channel, field="channel")
        participants_norm = _normalize_recipients(participants)
        if not participants_norm:
            raise AuthorityServiceError("discussion_participants_required")
        if rounds not in {1, 2, 3}:
            raise AuthorityServiceError("discussion_rounds_must_be_between_1_and_3")
        if token_budget < 0 or content_budget_bytes < 0:
            raise AuthorityServiceError("discussion_budget_must_be_nonnegative")
        digest = _nonempty(task_digest, field="task_digest")
        correlation = _nonempty(correlation_id, field="correlation_id")
        deadline = self._normalize_deadline(deadline_at)
        self._ensure_channel(channel_name)
        payload = {
            "participants": list(participants_norm),
            "rounds": rounds,
            "task_digest": digest,
            "correlation_id": correlation,
            "prompt_sha256": _sha256_bytes(prompt.encode("utf-8")),
            "token_budget": token_budget,
            "content_budget_bytes": content_budget_bytes,
        }
        with self._write_transaction():
            existing = self._find_job_by_key_tx("discussion", key)
            if existing is not None:
                self._assert_job_payload(existing, payload)
                return existing
            conversation_id = new_id("conversation")
            now = _iso()
            self._conn.execute(
                """INSERT INTO conversations(conversation_id, created_at, source, title)
                   VALUES (?, ?, 'authority-discussion', ?)""",
                (conversation_id, now, channel_name),
            )
            self._conn.execute(
                """INSERT INTO acp_conversations(
                    conversation_id, task_digest, correlation_digest, idempotency_digest,
                    rounds_requested, participants_json, created_at, deadline_at,
                    token_budget, content_budget_bytes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    conversation_id,
                    digest,
                    _sha256_bytes(correlation.encode("utf-8")),
                    _sha256_bytes(key.encode("utf-8")),
                    rounds,
                    _canonical_json(list(participants_norm)),
                    now,
                    deadline,
                    token_budget,
                    content_budget_bytes,
                ),
            )
            self._publish_message_tx(
                sender="authority-service",
                body=prompt,
                channel=channel_name,
                recipients=participants_norm,
                kind="discussion",
                conversation_id=conversation_id,
                correlation_id=correlation,
                provenance={"Source": "authority", "Agent": "authority-service", "Via": "queue"},
                deadline_at=deadline,
                idempotency_key=f"discussion-message:{key}",
            )
            return self._enqueue_job_tx(
                job_kind="discussion",
                subject_id=conversation_id,
                payload=payload,
                deadline_at=deadline,
                idempotency_key=key,
            )

    def enqueue_formal_review(
        self,
        *,
        repository: str,
        pr_number: int,
        head_sha: str,
        gate_kind: str,
        snapshot: bytes | None = None,
        snapshot_artifact_id: str | None = None,
        deadline_at: str | None = None,
        idempotency_key: str | None = None,
    ) -> AuthorityJob:
        """Queue a review only after sealing its exact snapshot and head identity."""
        key = idempotency_key or new_id("authority-review-key")
        repo = _nonempty(repository, field="repository")
        if isinstance(pr_number, bool) or not isinstance(pr_number, int) or pr_number < 1:
            raise AuthorityServiceError("invalid_pr_number")
        sha = _nonempty(head_sha, field="head_sha").lower()
        gate = _nonempty(gate_kind, field="gate_kind")
        if (snapshot is None) == (snapshot_artifact_id is None):
            raise AuthorityServiceError("provide_exactly_one_snapshot_or_snapshot_artifact_id")
        deadline = self._normalize_deadline(deadline_at)
        payload_base = {
            "repository": repo,
            "pr_number": pr_number,
            "head_sha": sha,
            "gate_kind": gate,
        }
        with self._write_transaction():
            existing = self._find_job_by_key_tx("formal_review", key)
            if existing is not None:
                self._assert_job_payload(existing, payload_base, subset=True)
                return existing
            if snapshot is not None:
                artifact = self.store.store_bytes(
                    snapshot,
                    producer="authority-formal-review",
                    retention_class="formal-review-snapshot",
                    mime_type="application/json",
                    logical_filename="formal-review-snapshot.json",
                    commit=False,
                )
            else:
                artifact = self._require_artifact_tx(
                    _nonempty(snapshot_artifact_id, field="snapshot_artifact_id")
                )
            payload = {**payload_base, "snapshot_sha256": artifact.sha256}
            review = self._find_formal_review_tx(repo, pr_number, sha, gate)
            if review is None:
                review_id = new_id("review")
                created_at = _iso()
                self._conn.execute(
                    """INSERT INTO formal_review_jobs(
                        review_id, repository, pr_number, head_sha, gate_kind, state,
                        snapshot_artifact_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, 'open', ?, ?)""",
                    (review_id, repo, pr_number, sha, gate, artifact.artifact_id, created_at),
                )
                self._conn.execute(
                    """INSERT INTO formal_review_snapshot_seals(
                        review_id, repository, pr_number, head_sha, gate_kind,
                        snapshot_artifact_id, snapshot_sha256, sealed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        review_id,
                        repo,
                        pr_number,
                        sha,
                        gate,
                        artifact.artifact_id,
                        artifact.sha256,
                        created_at,
                    ),
                )
            else:
                review_id = str(review["review_id"])
                if str(review["snapshot_artifact_id"] or "") != artifact.artifact_id:
                    raise AuthorityServiceError("formal_review_snapshot_conflict")
                self._require_formal_snapshot_seal_tx(review_id, current_head_sha=sha)
            return self._enqueue_job_tx(
                job_kind="formal_review",
                subject_id=review_id,
                payload=payload,
                deadline_at=deadline,
                idempotency_key=key,
            )

    def get_job(self, job_id: str) -> AuthorityJob:
        jid = _nonempty(job_id, field="job_id")
        row = self._conn.execute(
            "SELECT * FROM authority_jobs WHERE job_id = ?", (jid,)
        ).fetchone()
        if row is None:
            raise AuthorityServiceError("job_not_found")
        return self._job_from_row(row)

    def claim_next_job(
        self,
        worker_id: str,
        *,
        job_kinds: Iterable[AuthorityJobKind] | None = None,
        lease_seconds: int = 300,
        now: str | None = None,
    ) -> AuthorityJobLease | None:
        """Claim exactly one eligible durable job under a fenced lease."""
        worker = _nonempty(worker_id, field="worker_id")
        if lease_seconds <= 0:
            raise AuthorityServiceError("lease_seconds_must_be_positive")
        kinds = self._normalize_job_kinds(job_kinds)
        now_value = self._now_string(now)
        lease_until = _iso(_parse_iso(now_value, field="now") + timedelta(seconds=lease_seconds))
        with self._write_transaction():
            self._reclaim_expired_jobs_tx(now_value)
            clauses = ["state = 'queued'", "(deadline_at IS NULL OR deadline_at > ?)"]
            params: list[Any] = [now_value]
            if kinds:
                clauses.append("job_kind IN (" + ", ".join("?" for _ in kinds) + ")")
                params.extend(sorted(kinds))
            row = self._conn.execute(
                """SELECT * FROM authority_jobs WHERE """
                + " AND ".join(clauses)
                + " ORDER BY created_at ASC, job_id ASC LIMIT 1",
                params,
            ).fetchone()
            if row is None:
                return None
            token = int(row["fence_token"]) + 1
            cursor = self._conn.execute(
                """UPDATE authority_jobs
                   SET state = 'running', lease_owner = ?, lease_expires_at = ?,
                       fence_token = ?, attempt_count = attempt_count + 1, updated_at = ?
                   WHERE job_id = ? AND state = 'queued' AND fence_token = ?""",
                (worker, lease_until, token, now_value, str(row["job_id"]), int(row["fence_token"])),
            )
            if cursor.rowcount != 1:  # BEGIN IMMEDIATE makes this defensive only.
                raise AuthorityStaleLeaseError("job_claim_raced")
            self._append_job_event_tx(
                str(row["job_id"]), token, "claimed", "running", {"worker_id": worker}
            )
            claimed = self._conn.execute(
                "SELECT * FROM authority_jobs WHERE job_id = ?", (str(row["job_id"]),)
            ).fetchone()
            if claimed is None:  # pragma: no cover - same transaction
                raise AuthorityServiceError("job_claim_lost")
            return AuthorityJobLease(self._job_from_row(claimed))

    def claim_job(
        self,
        job_id: str,
        worker_id: str,
        *,
        lease_seconds: int = 300,
        now: str | None = None,
    ) -> AuthorityJobLease:
        """Claim one named job without accidentally taking older queue work.

        A retry by the same still-live worker returns its original fenced lease
        unchanged.  That lets a synchronous caller replay a receipt rather
        than duplicate provider work after a response was lost locally.
        """
        jid = _nonempty(job_id, field="job_id")
        worker = _nonempty(worker_id, field="worker_id")
        if lease_seconds <= 0:
            raise AuthorityServiceError("lease_seconds_must_be_positive")
        now_value = self._now_string(now)
        lease_until = _iso(_parse_iso(now_value, field="now") + timedelta(seconds=lease_seconds))
        with self._write_transaction():
            self._reclaim_expired_jobs_tx(now_value)
            row = self._require_job_tx(jid)
            state = str(row["state"])
            if state == "running":
                if (
                    str(row["lease_owner"] or "") == worker
                    and row["lease_expires_at"] is not None
                    and str(row["lease_expires_at"]) > now_value
                ):
                    return AuthorityJobLease(self._job_from_row(row))
                raise AuthorityStaleLeaseError("job_already_claimed")
            if state != "queued":
                raise AuthorityServiceError("job_not_claimable")
            if row["deadline_at"] is not None and str(row["deadline_at"]) <= now_value:
                # The reclaim above should have terminalized it. Keep this
                # defensive branch fail-closed if a malformed row survived.
                raise AuthorityServiceError("job_deadline_expired")
            token = int(row["fence_token"]) + 1
            cursor = self._conn.execute(
                """UPDATE authority_jobs
                   SET state = 'running', lease_owner = ?, lease_expires_at = ?,
                       fence_token = ?, attempt_count = attempt_count + 1, updated_at = ?
                   WHERE job_id = ? AND state = 'queued' AND fence_token = ?""",
                (worker, lease_until, token, now_value, jid, int(row["fence_token"])),
            )
            if cursor.rowcount != 1:
                raise AuthorityStaleLeaseError("job_claim_raced")
            self._append_job_event_tx(jid, token, "claimed", "running", {"worker_id": worker})
            claimed = self._require_job_tx(jid)
            return AuthorityJobLease(self._job_from_row(claimed))

    def read_job_result(self, job_id: str) -> bytes | None:
        """Return the integrity-checked stored terminal result, never re-run a job."""
        job = self.get_job(job_id)
        if job.state not in _JOB_TERMINAL:
            raise AuthorityServiceError("job_result_not_terminal")
        if job.result_artifact_id is None:
            return None
        try:
            return self.store.read_bytes(job.result_artifact_id)
        except Exception as exc:
            raise AuthorityServiceError("job_result_unreadable") from exc

    def retry_job(
        self,
        job_id: str,
        *,
        now: str | None = None,
        deadline_at: str | None = None,
    ) -> AuthorityJob:
        """Explicitly requeue a failed or expired job without losing attempt history."""
        return self._requeue_terminal_job(
            job_id,
            allowed_states=frozenset({"failed", "expired"}),
            event_type="retried",
            now=now,
            deadline_at=deadline_at,
        )

    def redrive_job(
        self,
        job_id: str,
        *,
        now: str | None = None,
        deadline_at: str | None = None,
    ) -> AuthorityJob:
        """Explicitly redrive a dead-lettered job while retaining its DLQ receipt."""
        return self._requeue_terminal_job(
            job_id,
            allowed_states=frozenset({"dead_lettered"}),
            event_type="redriven",
            now=now,
            deadline_at=deadline_at,
        )

    def finish_job(
        self,
        job_id: str,
        *,
        worker_id: str,
        fence_token: int,
        state: Literal["complete", "failed"],
        result: bytes | None = None,
        result_artifact_id: str | None = None,
        now: str | None = None,
    ) -> AuthorityJob:
        """Terminalize a lease once; exact replay is harmless, divergence fails."""
        if state not in {"complete", "failed"}:
            raise AuthorityServiceError("invalid_job_terminal_state")
        if (result is not None) and (result_artifact_id is not None):
            raise AuthorityServiceError("provide_result_or_result_artifact_id_not_both")
        jid = _nonempty(job_id, field="job_id")
        worker = _nonempty(worker_id, field="worker_id")
        if fence_token < 1:
            raise AuthorityStaleLeaseError("invalid_fence_token")
        now_value = self._now_string(now)
        with self._write_transaction():
            row = self._require_job_tx(jid)
            artifact, terminal_sha = self._result_artifact_tx(
                result=result,
                result_artifact_id=result_artifact_id,
                producer=f"authority-job:{row['job_kind']!s}",
            )
            if str(row["state"]) in _JOB_TERMINAL:
                self._assert_terminal_replay(
                    actual_state=str(row["state"]),
                    actual_sha=row["terminal_sha256"],
                    expected_state=state,
                    expected_sha=terminal_sha,
                )
                return self._job_from_row(row)
            self._assert_current_job_lease(row, worker, fence_token, now_value)
            self._conn.execute(
                """UPDATE authority_jobs
                   SET state = ?, result_artifact_id = ?, terminal_sha256 = ?,
                       lease_owner = NULL, lease_expires_at = NULL,
                       updated_at = ?, completed_at = ?
                   WHERE job_id = ?""",
                (state, artifact.artifact_id if artifact else None, terminal_sha, now_value, now_value, jid),
            )
            self._append_job_event_tx(jid, fence_token, "finished", state, {"worker_id": worker})
            return self.get_job(jid)

    def reclaim_expired_jobs(self, *, now: str | None = None) -> int:
        """Recover leases left by a crash and expire jobs only at their deadline."""
        now_value = self._now_string(now)
        with self._write_transaction():
            return self._reclaim_expired_jobs_tx(now_value)

    def _requeue_terminal_job(
        self,
        job_id: str,
        *,
        allowed_states: frozenset[str],
        event_type: str,
        now: str | None,
        deadline_at: str | None,
    ) -> AuthorityJob:
        jid = _nonempty(job_id, field="job_id")
        now_value = self._now_string(now)
        with self._write_transaction():
            row = self._require_job_tx(jid)
            previous_state = str(row["state"])
            if previous_state not in allowed_states:
                raise AuthorityServiceError("job_not_retryable")
            deadline = (
                self._normalize_deadline(deadline_at)
                if deadline_at is not None
                else row["deadline_at"]
            )
            if deadline is not None and str(deadline) <= now_value:
                raise AuthorityServiceError("job_retry_deadline_expired")
            self._conn.execute(
                """UPDATE authority_jobs
                   SET state = 'queued', deadline_at = ?, result_artifact_id = NULL,
                       terminal_sha256 = NULL, lease_owner = NULL,
                       lease_expires_at = NULL, updated_at = ?, completed_at = NULL
                   WHERE job_id = ?""",
                (deadline, now_value, jid),
            )
            self._append_job_event_tx(
                jid,
                int(row["fence_token"]),
                event_type,
                "queued",
                {
                    "previous_state": previous_state,
                    "previous_result_artifact_id": row["result_artifact_id"],
                    "previous_terminal_sha256": row["terminal_sha256"],
                },
            )
            return self.get_job(jid)

    # ------------------------------------------------------------------
    # Delivery leases, acknowledgements, and wake receipts

    def get_delivery(self, delivery_id: str) -> AuthorityDelivery:
        did = _nonempty(delivery_id, field="delivery_id")
        row = self._conn.execute(
            "SELECT * FROM authority_deliveries WHERE delivery_id = ?", (did,)
        ).fetchone()
        if row is None:
            raise AuthorityServiceError("delivery_not_found")
        return self._delivery_from_row(row)

    def claim_next_delivery(
        self,
        recipient: str,
        worker_id: str,
        *,
        lease_seconds: int = 300,
        max_attempts: int = 3,
        now: str | None = None,
    ) -> AuthorityDeliveryLease | None:
        """Claim one recipient delivery; a stale worker cannot later acknowledge it."""
        recipient_name = _nonempty(recipient, field="recipient")
        worker = _nonempty(worker_id, field="worker_id")
        if lease_seconds <= 0 or max_attempts <= 0:
            raise AuthorityServiceError("lease_and_max_attempts_must_be_positive")
        now_value = self._now_string(now)
        lease_until = _iso(_parse_iso(now_value, field="now") + timedelta(seconds=lease_seconds))
        with self._write_transaction():
            self._reclaim_expired_deliveries_tx(now_value, max_attempts=max_attempts)
            row = self._conn.execute(
                """SELECT * FROM authority_deliveries
                   WHERE recipient = ? AND state = 'queued'
                     AND attempt_count < ?
                     AND (deadline_at IS NULL OR deadline_at > ?)
                   ORDER BY created_at ASC, delivery_id ASC LIMIT 1""",
                (recipient_name, max_attempts, now_value),
            ).fetchone()
            if row is None:
                return None
            token = int(row["fence_token"]) + 1
            cursor = self._conn.execute(
                """UPDATE authority_deliveries
                   SET state = 'running', lease_owner = ?, lease_expires_at = ?,
                       fence_token = ?, attempt_count = attempt_count + 1, updated_at = ?
                   WHERE delivery_id = ? AND state = 'queued' AND fence_token = ?""",
                (worker, lease_until, token, now_value, str(row["delivery_id"]), int(row["fence_token"])),
            )
            if cursor.rowcount != 1:
                raise AuthorityStaleLeaseError("delivery_claim_raced")
            self._conn.execute(
                """INSERT INTO authority_delivery_attempts(
                    attempt_id, delivery_id, fence_token, state, started_at
                ) VALUES (?, ?, ?, 'running', ?)""",
                (new_id("authority-delivery-attempt"), str(row["delivery_id"]), token, now_value),
            )
            self._record_wake_receipt_tx(
                str(row["delivery_id"]), recipient_name, token, state="received", now=now_value
            )
            claimed = self._conn.execute(
                """SELECT d.*, m.body_artifact_id, m.content_sha256
                   FROM authority_deliveries d
                   JOIN comms_messages m ON m.message_id = d.message_id
                   WHERE d.delivery_id = ?""",
                (str(row["delivery_id"]),),
            ).fetchone()
            if claimed is None or claimed["body_artifact_id"] is None:
                raise AuthorityServiceError("delivery_message_missing")
            return AuthorityDeliveryLease(
                delivery=self._delivery_from_row(claimed),
                body_artifact_id=str(claimed["body_artifact_id"]),
                content_sha256=str(claimed["content_sha256"]),
            )

    def acknowledge_delivery(
        self,
        delivery_id: str,
        *,
        worker_id: str,
        fence_token: int,
        acknowledgment: bytes | None = None,
        acknowledgment_artifact_id: str | None = None,
        now: str | None = None,
    ) -> AuthorityDelivery:
        """Acknowledge one fenced delivery; duplicate terminal acks are idempotent."""
        return self.finish_delivery(
            delivery_id,
            worker_id=worker_id,
            fence_token=fence_token,
            state="acknowledged",
            result=acknowledgment,
            result_artifact_id=acknowledgment_artifact_id,
            now=now,
        )

    def finish_delivery(
        self,
        delivery_id: str,
        *,
        worker_id: str,
        fence_token: int,
        state: Literal["acknowledged", "failed"],
        result: bytes | None = None,
        result_artifact_id: str | None = None,
        now: str | None = None,
    ) -> AuthorityDelivery:
        """Finish a delivery exactly once, recording any failed terminal as a dead letter."""
        if state not in {"acknowledged", "failed"}:
            raise AuthorityServiceError("invalid_delivery_terminal_state")
        if result is not None and result_artifact_id is not None:
            raise AuthorityServiceError("provide_result_or_result_artifact_id_not_both")
        did = _nonempty(delivery_id, field="delivery_id")
        worker = _nonempty(worker_id, field="worker_id")
        if fence_token < 1:
            raise AuthorityStaleLeaseError("invalid_fence_token")
        now_value = self._now_string(now)
        with self._write_transaction():
            row = self._require_delivery_tx(did)
            artifact, terminal_sha = self._result_artifact_tx(
                result=result,
                result_artifact_id=result_artifact_id,
                producer="authority-delivery-result",
            )
            if str(row["state"]) in _DELIVERY_TERMINAL:
                self._assert_terminal_replay(
                    actual_state=str(row["state"]),
                    actual_sha=row["terminal_sha256"],
                    expected_state=state,
                    expected_sha=terminal_sha,
                )
                return self._delivery_from_row(row)
            self._assert_current_delivery_lease(row, worker, fence_token, now_value)
            self._conn.execute(
                """UPDATE authority_deliveries
                   SET state = ?, acknowledgment_artifact_id = ?, terminal_sha256 = ?,
                       lease_owner = NULL, lease_expires_at = NULL,
                       updated_at = ?, completed_at = ?
                   WHERE delivery_id = ?""",
                (state, artifact.artifact_id if artifact else None, terminal_sha, now_value, now_value, did),
            )
            self._conn.execute(
                """UPDATE authority_delivery_attempts
                   SET state = ?, finished_at = ?, outcome_sha256 = ?, artifact_id = ?
                   WHERE delivery_id = ? AND fence_token = ?""",
                (
                    state,
                    now_value,
                    terminal_sha,
                    artifact.artifact_id if artifact else None,
                    did,
                    fence_token,
                ),
            )
            self._record_wake_receipt_tx(
                did, str(row["recipient"]), fence_token, state="consumed", now=now_value
            )
            if state == "failed":
                self._dead_letter_delivery_tx(did, reason_code="worker_failed")
            return self.get_delivery(did)

    def reclaim_expired_deliveries(
        self,
        *,
        max_attempts: int = 3,
        now: str | None = None,
    ) -> int:
        """Recover abandoned delivery leases without dropping pending work."""
        if max_attempts <= 0:
            raise AuthorityServiceError("max_attempts_must_be_positive")
        now_value = self._now_string(now)
        with self._write_transaction():
            return self._reclaim_expired_deliveries_tx(now_value, max_attempts=max_attempts)

    def record_wake_receipt(
        self,
        delivery_id: str,
        *,
        fence_token: int,
        state: Literal["received", "consumed"] = "received",
        now: str | None = None,
    ) -> None:
        """Durably record receiver observation of an authority wake signal."""
        if state not in {"received", "consumed"}:
            raise AuthorityServiceError("invalid_wake_state")
        did = _nonempty(delivery_id, field="delivery_id")
        if fence_token < 0:
            raise AuthorityServiceError("invalid_fence_token")
        now_value = self._now_string(now)
        with self._write_transaction():
            delivery = self._require_delivery_tx(did)
            self._record_wake_receipt_tx(
                did,
                str(delivery["recipient"]),
                fence_token,
                state=state,
                now=now_value,
            )

    # ------------------------------------------------------------------
    # Formal review authority seam

    def require_publishable_formal_review(
        self,
        review_id: str,
        *,
        current_head_sha: str,
    ) -> FormalReviewJob:
        """Fail closed unless the sealed immutable snapshot matches the exact PR head."""
        rid = _nonempty(review_id, field="review_id")
        head = _nonempty(current_head_sha, field="current_head_sha").lower()
        row = self._conn.execute(
            "SELECT * FROM formal_review_jobs WHERE review_id = ?", (rid,)
        ).fetchone()
        if row is None:
            raise AuthorityServiceError("formal_review_not_found")
        self._require_formal_snapshot_seal_tx(rid, current_head_sha=head)
        service = FormalReviewJobService(store=self.store)
        return service.get_job(rid, include_attempts=False)

    def accept_formal_review_verdict(
        self,
        review_id: str,
        sealed: SealedVerdict | Mapping[str, Any] | str | bytes,
    ) -> SealedVerdict:
        """Accept a verdict only after authority's exact sealed-snapshot/head gate."""
        try:
            parsed = sealed if isinstance(sealed, SealedVerdict) else parse_sealed_verdict_payload(sealed)
        except Exception as exc:
            raise AuthorityServiceError("sealed_verdict_invalid") from exc
        job = self.require_publishable_formal_review(
            review_id, current_head_sha=parsed.head_sha
        )
        if parsed.review_id != job.review_id:
            raise AuthorityServiceError("sealed_review_id_mismatch")
        try:
            return FormalReviewJobService(store=self.store).accept_sealed_verdict(
                job.review_id, parsed
            )
        except FormalReviewJobsError as exc:
            raise AuthorityServiceError("sealed_verdict_rejected") from exc

    # ------------------------------------------------------------------
    # Historical migration seam (no live-state caller is invoked here)

    def import_records(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        source: str,
    ) -> HistoricalImportResult:
        """Import immutable legacy metadata/bodies once, preserving identity links.

        A repeat with the same source/external id/body hash returns the original
        message rather than creating another row.  A changed replay is refused;
        callers must choose a new source/external identity instead of silently
        overwriting history.
        """
        source_name = _nonempty(source, field="source")
        materialized = [self._normalize_import_record(item, source_name) for item in records]
        imported = 0
        replayed = 0
        message_ids: list[str] = []
        with self._write_transaction():
            self._conn.execute("PRAGMA defer_foreign_keys = ON")
            seen: dict[str, str] = {}
            for record in materialized:
                existing_digest = seen.get(record["external_id"])
                if existing_digest is not None and existing_digest != record["payload_sha256"]:
                    raise AuthorityServiceError("duplicate_import_external_id_conflict")
                seen[record["external_id"]] = record["payload_sha256"]
                receipt = self._conn.execute(
                    """SELECT payload_sha256, message_id FROM authority_import_receipts
                       WHERE source = ? AND external_id = ?""",
                    (source_name, record["external_id"]),
                ).fetchone()
                if receipt is not None:
                    if str(receipt["payload_sha256"]) != record["payload_sha256"]:
                        raise AuthorityServiceError("historical_import_conflict")
                    replayed += 1
                    message_ids.append(str(receipt["message_id"]))
                    continue
                if record["channel"] is not None:
                    self._ensure_channel_tx(str(record["channel"]))
                message = self._publish_message_tx(
                    sender=record["sender"],
                    body=record["body"],
                    channel=record["channel"],
                    recipients=record["recipients"],
                    kind=record["kind"],
                    conversation_id=record["conversation_id"],
                    in_reply_to=record["in_reply_to"],
                    correlation_id=record["correlation_id"],
                    provenance=record["provenance"],
                    context_revisions=record["context_revisions"],
                    deadline_at=None,
                    created_at=record["created_at"],
                    idempotency_key=f"historical-message:{source_name}:{record['external_id']}",
                    thread_id=record["thread_id"],
                    message_id=record["message_id"],
                    imported_source=source_name,
                    emit_wakes=False,
                    imported_delivery_state="acknowledged",
                )
                self._conn.execute(
                    """INSERT INTO authority_import_receipts(
                        source, external_id, payload_sha256, message_id, imported_at
                    ) VALUES (?, ?, ?, ?, ?)""",
                    (
                        source_name,
                        record["external_id"],
                        record["payload_sha256"],
                        message.message_id,
                        _iso(),
                    ),
                )
                imported += 1
                message_ids.append(message.message_id)
        return HistoricalImportResult(imported, replayed, tuple(message_ids))

    def import_legacy_sqlite(self, source_path: Path, *, source: str = "legacy-broker") -> HistoricalImportResult:
        """Read a legacy bridge/channel SQLite database without modifying it."""
        path = Path(source_path).expanduser().resolve()
        if not path.is_file():
            raise AuthorityServiceError("legacy_source_db_not_found")
        source_name = _nonempty(source, field="source")
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            records: list[dict[str, Any]] = []
            if self._sqlite_table_exists(conn, "channels"):
                for row in conn.execute("SELECT * FROM channels ORDER BY name ASC"):
                    name = str(row["name"])
                    subscribers = self._split_legacy_csv(row["subscribers"])
                    self.create_channel(
                        name,
                        subscribers=subscribers,
                        metadata={
                            "Source": source_name,
                            "Agent": "legacy-channel",
                            "Via": "sqlite-import",
                            "description": str(row["description"] or ""),
                            "include": str(row["include"] or ""),
                        },
                    )
            if self._sqlite_table_exists(conn, "messages"):
                for row in conn.execute("SELECT * FROM messages ORDER BY id ASC"):
                    records.append(self._legacy_bridge_record(row, source_name))
            if self._sqlite_table_exists(conn, "channel_messages"):
                delivery_map = self._legacy_delivery_map(conn)
                for row in conn.execute("SELECT * FROM channel_messages ORDER BY created_at ASC, message_id ASC"):
                    records.append(self._legacy_channel_record(row, source_name, delivery_map))
        finally:
            conn.close()
        return self.import_records(records, source=source_name)

    # ------------------------------------------------------------------
    # Internal transaction helpers

    def _publish_message_tx(
        self,
        *,
        sender: str,
        body: str,
        channel: str | None,
        recipients: Iterable[str] | None,
        kind: str,
        conversation_id: str | None = None,
        in_reply_to: str | None = None,
        correlation_id: str | None = None,
        provenance: Mapping[str, Any] | None = None,
        context_revisions: Mapping[str, str] | None = None,
        deadline_at: str | None = None,
        created_at: str | None = None,
        idempotency_key: str,
        thread_id: str | None = None,
        message_id: str | None = None,
        imported_source: str | None = None,
        emit_wakes: bool = True,
        imported_delivery_state: str | None = None,
    ) -> AuthorityMessage:
        if not isinstance(body, str):
            raise AuthorityServiceError("message_body_must_be_text")
        sender_name = _nonempty(sender, field="sender")
        kind_name = _nonempty(kind, field="kind")
        key = _nonempty(idempotency_key, field="idempotency_key")
        channel_row = self._require_channel_tx(channel) if channel is not None else None
        if recipients is None and channel_row is not None:
            subscriber_rows = self._conn.execute(
                """SELECT recipient FROM authority_channel_subscribers
                   WHERE channel_id = ? AND recipient != ? ORDER BY recipient ASC""",
                (str(channel_row["channel_id"]), sender_name),
            ).fetchall()
            recipients_norm = tuple(str(row["recipient"]) for row in subscriber_rows)
        else:
            recipients_norm = _normalize_recipients(recipients)
        revisions = self._normalize_context_revisions(context_revisions, channel_row)
        provenance_data = _safe_json_mapping(provenance)
        deadline = self._normalize_deadline(deadline_at)
        creation = self._normalize_created_at(created_at)
        body_bytes = body.encode("utf-8")
        body_sha = _sha256_bytes(body_bytes)
        payload = {
            "sender": sender_name,
            "body_sha256": body_sha,
            "channel_id": str(channel_row["channel_id"]) if channel_row is not None else None,
            "recipients": list(recipients_norm),
            "kind": kind_name,
            "conversation_id": conversation_id or "",
            "thread_id": thread_id or "",
            "in_reply_to": in_reply_to or "",
            "correlation_id": correlation_id or "",
            "provenance": provenance_data,
            "context_revisions": revisions,
            "deadline_at": deadline or "",
            "imported_source": imported_source or "",
        }
        existing_id = self._check_idempotency_tx("message", key, _sha256_json(payload))
        if existing_id is not None:
            return self.get_message(existing_id)

        mid = message_id or new_id("message")
        if self._conn.execute("SELECT 1 FROM comms_messages WHERE message_id = ?", (mid,)).fetchone():
            raise AuthorityServiceError("message_id_already_exists")
        conversation = conversation_id
        if in_reply_to is not None:
            parent = self._conn.execute(
                "SELECT conversation_id FROM comms_messages WHERE message_id = ?", (in_reply_to,)
            ).fetchone()
            if parent is None:
                # Historical batches may include a child before its parent.
                # The import transaction defers FK checks until every immutable
                # record is inserted, but live authority writes still fail fast.
                if imported_source is None or conversation is None:
                    raise AuthorityServiceError("reply_parent_not_found")
            else:
                parent_conversation = str(parent["conversation_id"])
                if conversation is None:
                    conversation = parent_conversation
                elif conversation != parent_conversation:
                    raise AuthorityServiceError("reply_thread_mismatch")
        conversation = conversation or new_id("conversation")
        thread = _nonempty(thread_id, field="thread_id") if thread_id is not None else conversation
        self._conn.execute(
            """INSERT OR IGNORE INTO conversations(conversation_id, created_at, source, title)
               VALUES (?, ?, ?, ?)""",
            (
                conversation,
                creation,
                "authority-import" if imported_source else "authority",
                str(channel_row["name"]) if channel_row is not None else None,
            ),
        )
        artifact = self.store.store_bytes(
            body_bytes,
            producer="authority-import" if imported_source else "authority-message",
            retention_class="historical-message" if imported_source else "message-body",
            mime_type="text/plain; charset=utf-8",
            logical_filename=f"{mid}.txt",
            commit=False,
        )
        recipient_value = recipients_norm[0] if len(recipients_norm) == 1 else None
        self._conn.execute(
            """INSERT INTO comms_messages(
                message_id, conversation_id, in_reply_to, kind, sender, recipient,
                body_inline, body_artifact_id, content_sha256, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                mid,
                conversation,
                in_reply_to,
                kind_name,
                sender_name,
                recipient_value,
                body[:500],
                artifact.artifact_id,
                body_sha,
                _canonical_json({"authority": True, "body_artifact_id": artifact.artifact_id}),
                creation,
            ),
        )
        self.store.reference(mid, artifact.artifact_id, relation="body", commit=False)
        self._conn.execute(
            """INSERT INTO authority_message_metadata(
                message_id, channel_id, thread_id, correlation_id, context_revisions_json,
                provenance_json, imported_source, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                mid,
                str(channel_row["channel_id"]) if channel_row is not None else None,
                thread,
                correlation_id,
                _canonical_json(revisions),
                _canonical_json(provenance_data),
                imported_source,
                creation,
            ),
        )
        delivery_ids: list[str] = []
        for recipient in recipients_norm:
            delivery_id = new_id("authority-delivery")
            delivery_state = imported_delivery_state or "queued"
            terminal_sha = _sha256_bytes(b"") if delivery_state == "acknowledged" else None
            completed_at = creation if delivery_state in _DELIVERY_TERMINAL else None
            self._conn.execute(
                """INSERT INTO authority_deliveries(
                    delivery_id, message_id, recipient, state, deadline_at, terminal_sha256,
                    created_at, updated_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    delivery_id,
                    mid,
                    recipient,
                    delivery_state,
                    deadline,
                    terminal_sha,
                    creation,
                    creation,
                    completed_at,
                ),
            )
            delivery_ids.append(delivery_id)
            if emit_wakes and delivery_state == "queued":
                self._record_wake_receipt_tx(
                    delivery_id, recipient, 0, state="emitted", now=creation
                )
        self._insert_idempotency_tx("message", key, _sha256_json(payload), mid)
        return AuthorityMessage(
            message_id=mid,
            conversation_id=conversation,
            in_reply_to=in_reply_to,
            channel_id=str(channel_row["channel_id"]) if channel_row is not None else None,
            thread_id=thread,
            correlation_id=correlation_id,
            sender=sender_name,
            recipient=recipient_value,
            kind=kind_name,
            body_artifact_id=artifact.artifact_id,
            content_sha256=body_sha,
            context_revisions=revisions,
            provenance=provenance_data,
            created_at=creation,
            delivery_ids=tuple(delivery_ids),
        )

    def _enqueue_job_tx(
        self,
        *,
        job_kind: AuthorityJobKind,
        subject_id: str,
        payload: Mapping[str, Any],
        deadline_at: str | None,
        idempotency_key: str,
    ) -> AuthorityJob:
        if job_kind not in _JOB_KINDS:
            raise AuthorityServiceError("invalid_job_kind")
        key = _nonempty(idempotency_key, field="idempotency_key")
        payload_data = _safe_json_mapping(payload)
        existing = self._find_job_by_key_tx(job_kind, key)
        if existing is not None:
            self._assert_job_payload(existing, payload_data)
            return existing
        subject_row = self._conn.execute(
            """SELECT * FROM authority_jobs
               WHERE job_kind = ? AND subject_id = ?""",
            (job_kind, subject_id),
        ).fetchone()
        if subject_row is not None:
            existing_subject = self._job_from_row(subject_row)
            self._assert_job_payload(existing_subject, payload_data)
            return existing_subject
        artifact = self.store.store_text(
            _canonical_json(payload_data),
            producer=f"authority-job:{job_kind}",
            retention_class="authority-job-payload",
            logical_filename=f"{job_kind}.json",
            mime_type="application/json; charset=utf-8",
            commit=False,
        )
        job_id = new_id("authority-job")
        now = _iso()
        deadline = self._normalize_deadline(deadline_at)
        self._conn.execute(
            """INSERT INTO authority_jobs(
                job_id, job_kind, subject_id, payload_artifact_id, state, deadline_at,
                idempotency_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'queued', ?, ?, ?, ?)""",
            (job_id, job_kind, subject_id, artifact.artifact_id, deadline, key, now, now),
        )
        self._append_job_event_tx(job_id, 0, "enqueued", "queued", {})
        self._insert_idempotency_tx(f"job:{job_kind}", key, _sha256_json(payload_data), job_id)
        return self.get_job(job_id)

    def _find_job_by_key_tx(self, job_kind: str, idempotency_key: str) -> AuthorityJob | None:
        row = self._conn.execute(
            """SELECT * FROM authority_jobs
               WHERE job_kind = ? AND idempotency_key = ?""",
            (job_kind, idempotency_key),
        ).fetchone()
        return self._job_from_row(row) if row is not None else None

    def _assert_job_payload(
        self,
        job: AuthorityJob,
        expected_payload: Mapping[str, Any],
        *,
        subset: bool = False,
    ) -> None:
        try:
            actual = json.loads(self.store.read_bytes(job.payload_artifact_id).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AuthorityServiceError("job_payload_corrupt") from exc
        if not isinstance(actual, dict):
            raise AuthorityServiceError("job_payload_corrupt")
        expected = _safe_json_mapping(expected_payload)
        matches = (
            all(actual.get(key) == value for key, value in expected.items())
            if subset
            else actual == expected
        )
        if not matches:
            raise AuthorityServiceError("idempotency_key_reused_with_different_payload")

    def _reclaim_expired_jobs_tx(self, now: str) -> int:
        reclaimed = 0
        expired_rows = self._conn.execute(
            """SELECT job_id, fence_token FROM authority_jobs
               WHERE state IN ('queued', 'running') AND deadline_at IS NOT NULL
                 AND deadline_at <= ?""",
            (now,),
        ).fetchall()
        for row in expired_rows:
            self._conn.execute(
                """UPDATE authority_jobs
                   SET state = 'expired', lease_owner = NULL, lease_expires_at = NULL,
                       updated_at = ?, completed_at = ? WHERE job_id = ?""",
                (now, now, str(row["job_id"])),
            )
            self._append_job_event_tx(
                str(row["job_id"]), int(row["fence_token"]), "expired", "expired", {}
            )
            self._dead_letter_job_tx(str(row["job_id"]), reason_code="deadline_expired")
            reclaimed += 1
        stale_rows = self._conn.execute(
            """SELECT job_id, fence_token FROM authority_jobs
               WHERE state = 'running' AND lease_expires_at IS NOT NULL
                 AND lease_expires_at <= ?
                 AND (deadline_at IS NULL OR deadline_at > ?)""",
            (now, now),
        ).fetchall()
        for row in stale_rows:
            self._conn.execute(
                """UPDATE authority_jobs
                   SET state = 'queued', lease_owner = NULL, lease_expires_at = NULL,
                       updated_at = ? WHERE job_id = ?""",
                (now, str(row["job_id"])),
            )
            self._append_job_event_tx(
                str(row["job_id"]), int(row["fence_token"]), "reclaimed", "queued", {}
            )
            reclaimed += 1
        return reclaimed

    def _reclaim_expired_deliveries_tx(self, now: str, *, max_attempts: int) -> int:
        reclaimed = 0
        expired = self._conn.execute(
            """SELECT delivery_id, fence_token FROM authority_deliveries
               WHERE state IN ('queued', 'running') AND deadline_at IS NOT NULL
                 AND deadline_at <= ?""",
            (now,),
        ).fetchall()
        for row in expired:
            delivery_id = str(row["delivery_id"])
            self._conn.execute(
                """UPDATE authority_deliveries
                   SET state = 'expired', lease_owner = NULL, lease_expires_at = NULL,
                       updated_at = ?, completed_at = ? WHERE delivery_id = ?""",
                (now, now, delivery_id),
            )
            self._conn.execute(
                """UPDATE authority_delivery_attempts
                   SET state = 'expired', finished_at = ?
                   WHERE delivery_id = ? AND fence_token = ? AND finished_at IS NULL""",
                (now, delivery_id, int(row["fence_token"])),
            )
            self._dead_letter_delivery_tx(delivery_id, reason_code="deadline_expired")
            reclaimed += 1
        stale = self._conn.execute(
            """SELECT delivery_id, fence_token, attempt_count FROM authority_deliveries
               WHERE state = 'running' AND lease_expires_at IS NOT NULL
                 AND lease_expires_at <= ?
                 AND (deadline_at IS NULL OR deadline_at > ?)""",
            (now, now),
        ).fetchall()
        for row in stale:
            delivery_id = str(row["delivery_id"])
            terminal = int(row["attempt_count"]) >= max_attempts
            next_state = "dead_lettered" if terminal else "queued"
            self._conn.execute(
                """UPDATE authority_deliveries
                   SET state = ?, lease_owner = NULL, lease_expires_at = NULL,
                       updated_at = ?, completed_at = CASE WHEN ? THEN ? ELSE completed_at END
                   WHERE delivery_id = ?""",
                (next_state, now, terminal, now, delivery_id),
            )
            self._conn.execute(
                """UPDATE authority_delivery_attempts
                   SET state = ?, finished_at = ?
                   WHERE delivery_id = ? AND fence_token = ? AND finished_at IS NULL""",
                ("dead_lettered" if terminal else "reclaimed", now, delivery_id, int(row["fence_token"])),
            )
            if terminal:
                self._dead_letter_delivery_tx(delivery_id, reason_code="attempts_exhausted")
            reclaimed += 1
        return reclaimed

    def _record_wake_receipt_tx(
        self,
        delivery_id: str,
        recipient: str,
        fence_token: int,
        *,
        state: str,
        now: str,
    ) -> None:
        requested_rank = _WAKE_STATES[state]
        row = self._conn.execute(
            """SELECT wake_id, state FROM authority_wake_receipts
               WHERE delivery_id = ? AND fence_token = ?""",
            (delivery_id, fence_token),
        ).fetchone()
        if row is None:
            self._conn.execute(
                """INSERT INTO authority_wake_receipts(
                    wake_id, delivery_id, recipient, fence_token, state, emitted_at, received_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_id("authority-wake"),
                    delivery_id,
                    recipient,
                    fence_token,
                    state,
                    now,
                    now if state in {"received", "consumed"} else None,
                ),
            )
            return
        current_rank = _WAKE_STATES[str(row["state"])]
        if requested_rank < current_rank:
            raise AuthorityServiceError("wake_receipt_state_regression")
        if requested_rank == current_rank:
            return
        self._conn.execute(
            """UPDATE authority_wake_receipts
               SET state = ?, received_at = COALESCE(received_at, ?)
               WHERE wake_id = ?""",
            (state, now, str(row["wake_id"])),
        )

    def _dead_letter_delivery_tx(self, delivery_id: str, *, reason_code: str) -> None:
        self._conn.execute(
            """INSERT OR IGNORE INTO authority_dead_letters(
                dead_letter_id, delivery_id, reason_code, created_at
            ) VALUES (?, ?, ?, ?)""",
            (new_id("authority-dead-letter"), delivery_id, reason_code, _iso()),
        )

    def _dead_letter_job_tx(self, job_id: str, *, reason_code: str) -> None:
        self._conn.execute(
            """INSERT OR IGNORE INTO authority_dead_letters(
                dead_letter_id, job_id, reason_code, created_at
            ) VALUES (?, ?, ?, ?)""",
            (new_id("authority-dead-letter"), job_id, reason_code, _iso()),
        )

    def _append_job_event_tx(
        self,
        job_id: str,
        fence_token: int,
        event_type: str,
        state: str,
        metadata: Mapping[str, Any],
    ) -> None:
        self._conn.execute(
            """INSERT INTO authority_job_events(
                event_id, job_id, fence_token, event_type, state, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                new_id("authority-job-event"),
                job_id,
                fence_token,
                event_type,
                state,
                _canonical_json(_safe_json_mapping(metadata)),
                _iso(),
            ),
        )

    # ------------------------------------------------------------------
    # Formal snapshot and import helpers

    def _require_formal_snapshot_seal_tx(self, review_id: str, *, current_head_sha: str) -> None:
        row = self._conn.execute(
            """SELECT j.repository, j.pr_number, j.head_sha, j.gate_kind,
                      j.snapshot_artifact_id, s.snapshot_artifact_id AS sealed_artifact_id,
                      s.snapshot_sha256, a.sha256 AS artifact_sha256
               FROM formal_review_jobs j
               LEFT JOIN formal_review_snapshot_seals s ON s.review_id = j.review_id
               LEFT JOIN artifacts a ON a.artifact_id = s.snapshot_artifact_id
               WHERE j.review_id = ?""",
            (review_id,),
        ).fetchone()
        if row is None:
            raise AuthorityServiceError("formal_review_not_found")
        if str(row["head_sha"]).lower() != current_head_sha.lower():
            raise AuthorityServiceError("formal_review_head_mismatch")
        if row["sealed_artifact_id"] is None or row["snapshot_sha256"] is None:
            raise AuthorityServiceError("formal_review_snapshot_not_sealed")
        if row["snapshot_artifact_id"] != row["sealed_artifact_id"]:
            raise AuthorityServiceError("formal_review_snapshot_binding_mismatch")
        if row["artifact_sha256"] != row["snapshot_sha256"]:
            raise AuthorityServiceError("formal_review_snapshot_integrity_mismatch")
        try:
            self.store.read_bytes(str(row["sealed_artifact_id"]))
        except Exception as exc:
            raise AuthorityServiceError("formal_review_snapshot_unreadable") from exc

    def _find_formal_review_tx(
        self, repository: str, pr_number: int, head_sha: str, gate_kind: str
    ) -> sqlite3.Row | None:
        return self._conn.execute(
            """SELECT * FROM formal_review_jobs
               WHERE repository = ? AND pr_number = ? AND head_sha = ? AND gate_kind = ?""",
            (repository, pr_number, head_sha, gate_kind),
        ).fetchone()

    def _normalize_import_record(self, raw: Mapping[str, Any], source: str) -> dict[str, Any]:
        data = dict(raw)
        external_id = _nonempty(
            str(data.get("external_id") or data.get("id") or data.get("message_id") or ""),
            field="external_id",
        )
        body_raw = data.get("body", data.get("content", ""))
        if not isinstance(body_raw, str):
            raise AuthorityServiceError("historical_body_must_be_text")
        body_sha = _sha256_bytes(body_raw.encode("utf-8"))
        declared_hash = data.get("body_sha256") or data.get("content_sha256")
        if declared_hash is not None and str(declared_hash).lower() != body_sha:
            raise AuthorityServiceError("historical_body_hash_mismatch")
        channel = data.get("channel")
        if channel is not None:
            channel = _nonempty(str(channel), field="channel")
        sender = _nonempty(
            str(data.get("sender") or data.get("from_agent") or data.get("from_llm") or "legacy"),
            field="sender",
        )
        recipients_raw = data.get("recipients")
        if recipients_raw is None:
            singular = data.get("recipient") or data.get("to_agent") or data.get("to_llm")
            recipients_raw = () if singular is None else (str(singular),)
        if isinstance(recipients_raw, str):
            recipients_raw = (recipients_raw,)
        recipients = _normalize_recipients(recipients_raw)
        conversation_external = str(
            data.get("conversation_id") or data.get("thread_id") or data.get("task_id") or external_id
        )
        conversation_id = "legacy-conversation-" + _sha256_bytes(
            f"{source}:{conversation_external}".encode()
        )[:32]
        reply_raw = data.get("in_reply_to") or data.get("parent_id")
        in_reply_to = (
            "legacy-message-" + _sha256_bytes(f"{source}:{reply_raw}".encode())[:32]
            if reply_raw
            else None
        )
        message_id = "legacy-message-" + _sha256_bytes(f"{source}:{external_id}".encode())[:32]
        provenance = _safe_json_mapping(data.get("provenance") if isinstance(data.get("provenance"), Mapping) else None)
        provenance.setdefault("Source", str(data.get("Source") or source))
        provenance.setdefault("Agent", str(data.get("Agent") or sender))
        provenance.setdefault("Via", str(data.get("Via") or "historical-import"))
        provenance.setdefault("LegacyThreadId", conversation_external)
        if reply_raw:
            provenance.setdefault("LegacyReplyTo", str(reply_raw))
        metadata = data.get("metadata")
        if isinstance(metadata, Mapping):
            provenance.setdefault("metadata", _safe_json_mapping(metadata))
        context_raw = data.get("context_revisions")
        context_revisions: dict[str, str] = {}
        if isinstance(context_raw, Mapping):
            for key, value in context_raw.items():
                revision = str(value).strip()
                if revision:
                    context_revisions[_nonempty(str(key), field="context_revision_key")] = revision
        original_timestamp = str(data.get("created_at") or data.get("timestamp") or "")
        created_at = self._normalize_created_at(original_timestamp)
        if original_timestamp:
            provenance.setdefault("OriginalTimestamp", original_timestamp)
        payload = {
            "external_id": external_id,
            "message_id": message_id,
            "conversation_id": conversation_id,
            "thread_id": conversation_external,
            "in_reply_to": in_reply_to,
            "channel": channel,
            "sender": sender,
            "recipients": list(recipients),
            "kind": str(data.get("kind") or data.get("message_type") or "message"),
            "body_sha256": body_sha,
            "correlation_id": data.get("correlation_id"),
            "provenance": provenance,
            "context_revisions": context_revisions,
            "created_at": created_at,
        }
        return {
            **payload,
            "body": body_raw,
            "payload_sha256": _sha256_json(payload),
        }

    @staticmethod
    def _sqlite_table_exists(conn: sqlite3.Connection, name: str) -> bool:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
        ).fetchone() is not None

    @staticmethod
    def _split_legacy_csv(value: Any) -> tuple[str, ...]:
        return tuple(item.strip() for item in str(value or "").split(",") if item.strip())

    def _legacy_delivery_map(self, conn: sqlite3.Connection) -> dict[str, tuple[str, ...]]:
        if not self._sqlite_table_exists(conn, "deliveries"):
            return {}
        columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(deliveries)")}
        if not {"message_id", "to_agent"}.issubset(columns):
            return {}
        mapped: dict[str, list[str]] = {}
        for row in conn.execute("SELECT message_id, to_agent FROM deliveries"):
            mapped.setdefault(str(row["message_id"]), []).append(str(row["to_agent"]))
        return {key: tuple(sorted(set(value))) for key, value in mapped.items()}

    def _legacy_bridge_record(self, row: sqlite3.Row, source: str) -> dict[str, Any]:
        data_value = self._sqlite_row_optional(row, "data")
        metadata: dict[str, Any] = {}
        if data_value:
            try:
                parsed = json.loads(str(data_value))
                if isinstance(parsed, dict):
                    metadata = parsed
            except json.JSONDecodeError:
                metadata = {"legacy_data_sha256": _sha256_bytes(str(data_value).encode("utf-8"))}
        return {
            "external_id": f"bridge:{row['id']}",
            "body": str(row["content"] or ""),
            "sender": str(row["from_llm"]),
            "recipient": str(row["to_llm"]),
            "kind": str(row["message_type"] or "message"),
            "conversation_id": str(row["task_id"] or row["id"]),
            "created_at": str(row["timestamp"]),
            "provenance": {
                "Source": source,
                "Agent": str(row["from_llm"]),
                "Via": "legacy-bridge",
                "metadata": metadata,
            },
        }

    def _legacy_channel_record(
        self,
        row: sqlite3.Row,
        source: str,
        delivery_map: Mapping[str, tuple[str, ...]],
    ) -> dict[str, Any]:
        message_id = str(row["message_id"])
        return {
            "external_id": f"channel:{message_id}",
            "body": str(row["body"] or ""),
            "channel": str(row["channel"]),
            "sender": str(row["from_agent"]),
            "recipients": delivery_map.get(message_id, ()),
            "kind": str(row["kind"] or "post"),
            "conversation_id": str(row["thread_id"]),
            "in_reply_to": row["parent_id"],
            "correlation_id": row["correlation_id"],
            "context_revisions": {
                "shared": str(row["context_rev_shared"] or ""),
                "channel": str(row["context_rev_channel"] or ""),
            },
            "created_at": str(row["created_at"]),
            "provenance": {
                "Source": source,
                "Agent": str(row["from_agent"]),
                "Via": "legacy-channel",
            },
        }

    @staticmethod
    def _sqlite_row_optional(row: sqlite3.Row, key: str) -> Any:
        """Read an optional legacy column without assuming one schema version."""
        return row[key] if key in set(row.keys()) else None

    # ------------------------------------------------------------------
    # Small validation / row conversion helpers

    def _require_authority_schema(self) -> None:
        row = self._conn.execute(
            "SELECT MAX(version) AS version FROM comms_schema_migrations"
        ).fetchone()
        applied = int(row["version"] or 0) if row is not None else 0
        known = MIGRATIONS[-1].version if MIGRATIONS else 0
        if known < _AUTHORITY_SCHEMA_VERSION or applied < _AUTHORITY_SCHEMA_VERSION:
            raise AuthorityServiceError("authority_schema_migration_required")

    def _ensure_channel(self, channel: str) -> None:
        try:
            self.get_channel(channel)
        except AuthorityServiceError as exc:
            if str(exc) != "channel_not_found":
                raise
            self.create_channel(channel)

    def _ensure_channel_tx(self, channel: str) -> sqlite3.Row:
        channel_name = _nonempty(channel, field="channel")
        row = self._conn.execute(
            "SELECT * FROM authority_channels WHERE name = ?", (channel_name,)
        ).fetchone()
        if row is not None:
            return row
        channel_id = new_id("authority-channel")
        now = _iso()
        self._conn.execute(
            """INSERT INTO authority_channels(channel_id, name, metadata_json, created_at)
               VALUES (?, ?, '{}', ?)""",
            (channel_id, channel_name, now),
        )
        created = self._conn.execute(
            "SELECT * FROM authority_channels WHERE channel_id = ?", (channel_id,)
        ).fetchone()
        if created is None:  # pragma: no cover - same transaction
            raise AuthorityServiceError("channel_create_lost")
        return created

    def _require_channel_tx(self, channel: str | None) -> sqlite3.Row:
        channel_name = _nonempty(channel, field="channel")
        row = self._conn.execute(
            "SELECT * FROM authority_channels WHERE name = ?", (channel_name,)
        ).fetchone()
        if row is None:
            raise AuthorityServiceError("channel_not_found")
        return row

    def _normalize_context_revisions(
        self,
        values: Mapping[str, str] | None,
        channel_row: sqlite3.Row | None,
    ) -> dict[str, str]:
        normalized: dict[str, str] = {}
        if values is not None:
            for key, value in values.items():
                key_name = _nonempty(str(key), field="context_revision_key")
                value_name = str(value).strip()
                if value_name:
                    normalized[key_name] = value_name
        if channel_row is not None and channel_row["current_context_revision_id"] is not None:
            normalized.setdefault("channel", str(channel_row["current_context_revision_id"]))
        return normalized

    def _normalize_deadline(self, value: str | None) -> str | None:
        if value is None:
            return None
        return _iso(_parse_iso(value, field="deadline_at"))

    def _normalize_created_at(self, value: Any) -> str:
        if value is None or not str(value).strip():
            return _iso()
        return _iso(_parse_iso(str(value), field="created_at"))

    def _now_string(self, value: str | None) -> str:
        return self._normalize_created_at(value)

    @staticmethod
    def _normalize_job_kinds(values: Iterable[AuthorityJobKind] | None) -> frozenset[str]:
        if values is None:
            return frozenset()
        result = frozenset(str(value) for value in values)
        if not result.issubset(_JOB_KINDS):
            raise AuthorityServiceError("invalid_job_kind")
        return result

    def _check_idempotency_tx(self, namespace: str, key: str, payload_sha256: str) -> str | None:
        row = self._conn.execute(
            """SELECT payload_sha256, subject_id FROM authority_idempotency
               WHERE namespace = ? AND idempotency_key = ?""",
            (namespace, key),
        ).fetchone()
        if row is None:
            return None
        if str(row["payload_sha256"]) != payload_sha256:
            raise AuthorityServiceError("idempotency_key_reused_with_different_payload")
        return str(row["subject_id"])

    def _insert_idempotency_tx(
        self, namespace: str, key: str, payload_sha256: str, subject_id: str
    ) -> None:
        self._conn.execute(
            """INSERT INTO authority_idempotency(
                namespace, idempotency_key, payload_sha256, subject_id, created_at
            ) VALUES (?, ?, ?, ?, ?)""",
            (namespace, key, payload_sha256, subject_id, _iso()),
        )

    def _result_artifact_tx(
        self,
        *,
        result: bytes | None,
        result_artifact_id: str | None,
        producer: str,
    ) -> tuple[ArtifactRecord | None, str]:
        if result_artifact_id is not None:
            artifact = self._require_artifact_tx(result_artifact_id)
            return artifact, artifact.sha256
        if result is not None:
            artifact = self.store.store_bytes(
                result,
                producer=producer,
                retention_class="authority-result",
                mime_type="application/octet-stream",
                logical_filename="result.bin",
                commit=False,
            )
            return artifact, artifact.sha256
        return None, _sha256_bytes(b"")

    def _require_artifact_tx(self, artifact_id: str) -> ArtifactRecord:
        try:
            return self.store.get(artifact_id)
        except Exception as exc:
            raise AuthorityServiceError("artifact_not_found") from exc

    def _require_job_tx(self, job_id: str) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT * FROM authority_jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
        if row is None:
            raise AuthorityServiceError("job_not_found")
        return row

    def _require_delivery_tx(self, delivery_id: str) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT * FROM authority_deliveries WHERE delivery_id = ?", (delivery_id,)
        ).fetchone()
        if row is None:
            raise AuthorityServiceError("delivery_not_found")
        return row

    @staticmethod
    def _assert_terminal_replay(
        *,
        actual_state: str,
        actual_sha: Any,
        expected_state: str,
        expected_sha: str,
    ) -> None:
        if actual_state != expected_state or str(actual_sha or "") != expected_sha:
            raise AuthorityStaleLeaseError("terminalization_conflict")

    @staticmethod
    def _assert_current_job_lease(
        row: sqlite3.Row, worker: str, token: int, now: str
    ) -> None:
        if (
            str(row["state"]) != "running"
            or str(row["lease_owner"] or "") != worker
            or int(row["fence_token"]) != token
            or row["lease_expires_at"] is None
            or str(row["lease_expires_at"]) <= now
        ):
            raise AuthorityStaleLeaseError("stale_job_lease")

    @staticmethod
    def _assert_current_delivery_lease(
        row: sqlite3.Row, worker: str, token: int, now: str
    ) -> None:
        if (
            str(row["state"]) != "running"
            or str(row["lease_owner"] or "") != worker
            or int(row["fence_token"]) != token
            or row["lease_expires_at"] is None
            or str(row["lease_expires_at"]) <= now
        ):
            raise AuthorityStaleLeaseError("stale_delivery_lease")

    @staticmethod
    def _decode_mapping(raw: Any, *, field: str) -> dict[str, Any]:
        try:
            decoded = json.loads(str(raw or "{}"))
        except json.JSONDecodeError as exc:
            raise AuthorityServiceError(f"{field}_corrupt") from exc
        if not isinstance(decoded, dict):
            raise AuthorityServiceError(f"{field}_corrupt")
        return decoded

    def _decode_string_mapping(self, raw: Any) -> dict[str, str]:
        decoded = self._decode_mapping(raw, field="context_revisions")
        return {str(key): str(value) for key, value in decoded.items()}

    @staticmethod
    def _context_revision_from_row(row: sqlite3.Row) -> ContextRevision:
        return ContextRevision(
            context_revision_id=str(row["context_revision_id"]),
            channel_id=str(row["channel_id"]),
            sha256=str(row["sha256"]),
            artifact_id=str(row["artifact_id"]),
            created_at=str(row["created_at"]),
        )

    @staticmethod
    def _delivery_from_row(row: sqlite3.Row) -> AuthorityDelivery:
        return AuthorityDelivery(
            delivery_id=str(row["delivery_id"]),
            message_id=str(row["message_id"]),
            recipient=str(row["recipient"]),
            state=str(row["state"]),
            deadline_at=str(row["deadline_at"]) if row["deadline_at"] is not None else None,
            lease_owner=str(row["lease_owner"]) if row["lease_owner"] is not None else None,
            lease_expires_at=(
                str(row["lease_expires_at"]) if row["lease_expires_at"] is not None else None
            ),
            fence_token=int(row["fence_token"]),
            attempt_count=int(row["attempt_count"]),
            acknowledgment_artifact_id=(
                str(row["acknowledgment_artifact_id"])
                if row["acknowledgment_artifact_id"] is not None
                else None
            ),
            terminal_sha256=(
                str(row["terminal_sha256"]) if row["terminal_sha256"] is not None else None
            ),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            completed_at=str(row["completed_at"]) if row["completed_at"] is not None else None,
        )

    @staticmethod
    def _job_from_row(row: sqlite3.Row) -> AuthorityJob:
        return AuthorityJob(
            job_id=str(row["job_id"]),
            job_kind=str(row["job_kind"]),
            subject_id=str(row["subject_id"]),
            payload_artifact_id=str(row["payload_artifact_id"]),
            state=str(row["state"]),
            deadline_at=str(row["deadline_at"]) if row["deadline_at"] is not None else None,
            lease_owner=str(row["lease_owner"]) if row["lease_owner"] is not None else None,
            lease_expires_at=(
                str(row["lease_expires_at"]) if row["lease_expires_at"] is not None else None
            ),
            fence_token=int(row["fence_token"]),
            attempt_count=int(row["attempt_count"]),
            result_artifact_id=(
                str(row["result_artifact_id"]) if row["result_artifact_id"] is not None else None
            ),
            terminal_sha256=(
                str(row["terminal_sha256"]) if row["terminal_sha256"] is not None else None
            ),
            idempotency_key=str(row["idempotency_key"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            completed_at=str(row["completed_at"]) if row["completed_at"] is not None else None,
        )

    class _WriteTransaction:
        def __init__(self, service: AuthorityService) -> None:
            self.service = service

        def __enter__(self) -> None:
            self.service._conn.execute("BEGIN IMMEDIATE")

        def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
            if exc_type is None:
                try:
                    self.service._conn.commit()
                except Exception:
                    self.service._conn.rollback()
                    raise
            else:
                self.service._conn.rollback()
            return False

    def _write_transaction(self) -> _WriteTransaction:
        return self._WriteTransaction(self)


def open_authority_service(root: Path | None = None) -> AuthorityService:
    """Factory used by authority-mode adapters and tests."""
    return AuthorityService(root=root)


__all__ = [
    "AuthorityChannel",
    "AuthorityDelivery",
    "AuthorityDeliveryLease",
    "AuthorityJob",
    "AuthorityJobLease",
    "AuthorityMessage",
    "AuthorityService",
    "AuthorityServiceError",
    "AuthorityStaleLeaseError",
    "ContextRevision",
    "HistoricalImportResult",
    "open_authority_service",
]
