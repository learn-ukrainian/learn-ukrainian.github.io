"""Forward-only numbered migrations for the Fleet Communications v1 schema."""
from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime


class CommsMigrationError(RuntimeError):
    """A database is newer, corrupt, or otherwise unsafe to migrate."""


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    statements: tuple[str, ...]

    @property
    def checksum(self) -> str:
        payload = "\n".join(self.statements).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


_V1_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS conversations (
        conversation_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        source TEXT NOT NULL,
        title TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS comms_messages (
        message_id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        in_reply_to TEXT,
        kind TEXT NOT NULL,
        sender TEXT NOT NULL,
        recipient TEXT,
        body_inline TEXT,
        body_artifact_id TEXT,
        content_sha256 TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
        FOREIGN KEY (in_reply_to) REFERENCES comms_messages(message_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_comms_messages_conversation ON comms_messages(conversation_id, created_at)",
    """CREATE TABLE IF NOT EXISTS requests (
        request_id TEXT PRIMARY KEY,
        request_message_id TEXT NOT NULL UNIQUE,
        requested_recipient TEXT NOT NULL,
        resolved_recipient TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('queued', 'running', 'complete', 'incomplete', 'failed', 'expired', 'dead_lettered')),
        expires_at TEXT NOT NULL,
        completion_state TEXT NOT NULL DEFAULT 'unknown',
        invocation_spec_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (request_message_id) REFERENCES comms_messages(message_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_requests_state_expiry ON requests(state, expires_at)",
    """CREATE TABLE IF NOT EXISTS agent_endpoints (
        endpoint_id TEXT PRIMARY KEY,
        canonical_name TEXT NOT NULL UNIQUE,
        registry_version INTEGER NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('live', 'draining', 'retired', 'local_only')),
        successor TEXT,
        configuration_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS artifacts (
        artifact_id TEXT PRIMARY KEY,
        sha256 TEXT NOT NULL UNIQUE,
        bytes INTEGER NOT NULL CHECK (bytes >= 0),
        mime_type TEXT,
        logical_filename TEXT,
        producer TEXT NOT NULL,
        retention_class TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS message_artifacts (
        message_id TEXT NOT NULL,
        artifact_id TEXT NOT NULL,
        relation TEXT NOT NULL,
        PRIMARY KEY (message_id, artifact_id, relation),
        FOREIGN KEY (message_id) REFERENCES comms_messages(message_id),
        FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id)
    )""",
    """CREATE TABLE IF NOT EXISTS delivery_attempts (
        attempt_id TEXT PRIMARY KEY,
        delivery_id TEXT NOT NULL,
        attempt_number INTEGER NOT NULL,
        state TEXT NOT NULL,
        completion_state TEXT NOT NULL DEFAULT 'unknown',
        provider_session_id TEXT,
        raw_capture_artifact_id TEXT,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        UNIQUE (delivery_id, attempt_number),
        FOREIGN KEY (delivery_id) REFERENCES deliveries(delivery_id),
        FOREIGN KEY (raw_capture_artifact_id) REFERENCES artifacts(artifact_id)
    )""",
    """CREATE TABLE IF NOT EXISTS dead_letters (
        dead_letter_id TEXT PRIMARY KEY,
        request_id TEXT,
        delivery_id TEXT,
        reason TEXT NOT NULL,
        successor TEXT,
        original_expires_at TEXT,
        created_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS formal_review_jobs (
        review_id TEXT PRIMARY KEY,
        repository TEXT NOT NULL,
        pr_number INTEGER NOT NULL,
        head_sha TEXT NOT NULL,
        gate_kind TEXT NOT NULL,
        state TEXT NOT NULL,
        snapshot_artifact_id TEXT,
        created_at TEXT NOT NULL,
        UNIQUE (repository, pr_number, head_sha, gate_kind)
    )""",
    """CREATE TABLE IF NOT EXISTS formal_review_attempts (
        review_attempt_id TEXT PRIMARY KEY,
        review_id TEXT NOT NULL,
        attempt_number INTEGER NOT NULL,
        completion_state TEXT NOT NULL,
        raw_capture_artifact_id TEXT,
        created_at TEXT NOT NULL,
        UNIQUE (review_id, attempt_number),
        FOREIGN KEY (review_id) REFERENCES formal_review_jobs(review_id)
    )""",
    """CREATE TABLE IF NOT EXISTS github_publications (
        publication_id TEXT PRIMARY KEY,
        review_id TEXT NOT NULL,
        head_sha TEXT NOT NULL,
        status_context TEXT NOT NULL,
        published_at TEXT NOT NULL,
        UNIQUE (review_id, status_context),
        FOREIGN KEY (review_id) REFERENCES formal_review_jobs(review_id)
    )""",
)

# PR-F slice 2: durable sealed verdict blob on the formal job (Sol milestone 2 —
# publish without manually supplied CLI provenance).
_V2_STATEMENTS = (
    """ALTER TABLE formal_review_jobs
       ADD COLUMN sealed_verdict_artifact_id TEXT""",
)

# #6078: bounded ACPX discussions are a distinct, metadata-only lifecycle.
# Directed prompt/response content remains in comms_messages plus artifacts.
_V3_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS acp_conversations (
        conversation_id TEXT PRIMARY KEY,
        task_digest TEXT NOT NULL,
        correlation_digest TEXT NOT NULL,
        idempotency_digest TEXT NOT NULL UNIQUE,
        rounds_requested INTEGER NOT NULL CHECK (rounds_requested BETWEEN 1 AND 3),
        participants_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        deadline_at TEXT NOT NULL,
        token_budget INTEGER NOT NULL CHECK (token_budget >= 0),
        content_budget_bytes INTEGER NOT NULL CHECK (content_budget_bytes >= 0),
        FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
    )""",
    """CREATE TABLE IF NOT EXISTS acp_conversation_events (
        event_id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        state TEXT NOT NULL,
        sender TEXT,
        recipient TEXT,
        round INTEGER,
        outcome TEXT,
        duration_ms INTEGER,
        token_count INTEGER,
        leg_key_digest TEXT,
        message_id TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        UNIQUE (conversation_id, sequence),
        FOREIGN KEY (conversation_id) REFERENCES acp_conversations(conversation_id),
        FOREIGN KEY (message_id) REFERENCES comms_messages(message_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_acp_conversation_events_conversation ON acp_conversation_events(conversation_id, sequence)",
)

# #6159: authority-mode durable message, fan-out, and work queue contracts.
#
# These tables deliberately extend the existing ``comms_messages`` /
# ``conversations`` / ``artifacts`` primitives instead of creating another
# database or file-owned source of truth.  Legacy bridge tables remain readable
# during cutover, while authority writers use the same Fleet Comms SQLite file.
_V4_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS authority_channels (
        channel_id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        current_context_revision_id TEXT,
        created_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS authority_channel_subscribers (
        channel_id TEXT NOT NULL,
        recipient TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        PRIMARY KEY (channel_id, recipient),
        FOREIGN KEY (channel_id) REFERENCES authority_channels(channel_id)
    )""",
    """CREATE TABLE IF NOT EXISTS authority_context_revisions (
        context_revision_id TEXT PRIMARY KEY,
        channel_id TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        artifact_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (channel_id, sha256),
        FOREIGN KEY (channel_id) REFERENCES authority_channels(channel_id),
        FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id)
    )""",
    """CREATE TABLE IF NOT EXISTS authority_message_metadata (
        message_id TEXT PRIMARY KEY,
        channel_id TEXT,
        thread_id TEXT NOT NULL,
        correlation_id TEXT,
        context_revisions_json TEXT NOT NULL DEFAULT '{}',
        provenance_json TEXT NOT NULL DEFAULT '{}',
        imported_source TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (message_id) REFERENCES comms_messages(message_id),
        FOREIGN KEY (channel_id) REFERENCES authority_channels(channel_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_authority_message_thread ON authority_message_metadata(thread_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_authority_message_channel ON authority_message_metadata(channel_id, created_at)",
    """CREATE TABLE IF NOT EXISTS authority_idempotency (
        namespace TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        payload_sha256 TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (namespace, idempotency_key)
    )""",
    """CREATE TABLE IF NOT EXISTS authority_deliveries (
        delivery_id TEXT PRIMARY KEY,
        message_id TEXT NOT NULL,
        recipient TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('queued', 'running', 'acknowledged', 'failed', 'expired', 'dead_lettered')),
        deadline_at TEXT,
        lease_owner TEXT,
        lease_expires_at TEXT,
        fence_token INTEGER NOT NULL DEFAULT 0,
        attempt_count INTEGER NOT NULL DEFAULT 0,
        acknowledgment_artifact_id TEXT,
        terminal_sha256 TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        completed_at TEXT,
        UNIQUE (message_id, recipient),
        FOREIGN KEY (message_id) REFERENCES comms_messages(message_id),
        FOREIGN KEY (acknowledgment_artifact_id) REFERENCES artifacts(artifact_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_authority_delivery_claim ON authority_deliveries(recipient, state, deadline_at, lease_expires_at)",
    """CREATE TABLE IF NOT EXISTS authority_delivery_attempts (
        attempt_id TEXT PRIMARY KEY,
        delivery_id TEXT NOT NULL,
        fence_token INTEGER NOT NULL,
        state TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        outcome_sha256 TEXT,
        artifact_id TEXT,
        UNIQUE (delivery_id, fence_token),
        FOREIGN KEY (delivery_id) REFERENCES authority_deliveries(delivery_id),
        FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id)
    )""",
    """CREATE TABLE IF NOT EXISTS authority_dead_letters (
        dead_letter_id TEXT PRIMARY KEY,
        delivery_id TEXT UNIQUE,
        job_id TEXT UNIQUE,
        reason_code TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (delivery_id) REFERENCES authority_deliveries(delivery_id)
    )""",
    """CREATE TABLE IF NOT EXISTS authority_wake_receipts (
        wake_id TEXT PRIMARY KEY,
        delivery_id TEXT NOT NULL,
        recipient TEXT NOT NULL,
        fence_token INTEGER NOT NULL DEFAULT 0,
        state TEXT NOT NULL CHECK (state IN ('emitted', 'received', 'consumed')),
        emitted_at TEXT NOT NULL,
        received_at TEXT,
        UNIQUE (delivery_id, fence_token),
        FOREIGN KEY (delivery_id) REFERENCES authority_deliveries(delivery_id)
    )""",
    """CREATE TABLE IF NOT EXISTS authority_jobs (
        job_id TEXT PRIMARY KEY,
        job_kind TEXT NOT NULL CHECK (job_kind IN ('request', 'discussion', 'formal_review')),
        subject_id TEXT NOT NULL,
        payload_artifact_id TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('queued', 'running', 'complete', 'failed', 'expired', 'dead_lettered')),
        deadline_at TEXT,
        lease_owner TEXT,
        lease_expires_at TEXT,
        fence_token INTEGER NOT NULL DEFAULT 0,
        attempt_count INTEGER NOT NULL DEFAULT 0,
        result_artifact_id TEXT,
        terminal_sha256 TEXT,
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        completed_at TEXT,
        UNIQUE (job_kind, idempotency_key),
        FOREIGN KEY (payload_artifact_id) REFERENCES artifacts(artifact_id),
        FOREIGN KEY (result_artifact_id) REFERENCES artifacts(artifact_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_authority_job_claim ON authority_jobs(job_kind, state, deadline_at, lease_expires_at)",
    """CREATE TABLE IF NOT EXISTS authority_job_events (
        event_id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL,
        fence_token INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        state TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        FOREIGN KEY (job_id) REFERENCES authority_jobs(job_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_authority_job_events_job ON authority_job_events(job_id, created_at)",
    """CREATE TABLE IF NOT EXISTS authority_import_receipts (
        source TEXT NOT NULL,
        external_id TEXT NOT NULL,
        payload_sha256 TEXT NOT NULL,
        message_id TEXT NOT NULL,
        imported_at TEXT NOT NULL,
        PRIMARY KEY (source, external_id),
        FOREIGN KEY (message_id) REFERENCES comms_messages(message_id)
    )""",
    """CREATE TABLE IF NOT EXISTS formal_review_snapshot_seals (
        review_id TEXT PRIMARY KEY,
        repository TEXT NOT NULL,
        pr_number INTEGER NOT NULL,
        head_sha TEXT NOT NULL,
        gate_kind TEXT NOT NULL,
        snapshot_artifact_id TEXT NOT NULL,
        snapshot_sha256 TEXT NOT NULL,
        sealed_at TEXT NOT NULL,
        UNIQUE (repository, pr_number, head_sha, gate_kind),
        FOREIGN KEY (review_id) REFERENCES formal_review_jobs(review_id),
        FOREIGN KEY (snapshot_artifact_id) REFERENCES artifacts(artifact_id)
    )""",
    """CREATE TRIGGER IF NOT EXISTS authority_snapshot_seal_identity
       BEFORE INSERT ON formal_review_snapshot_seals
       BEGIN
         SELECT CASE WHEN NOT EXISTS (
           SELECT 1 FROM formal_review_jobs j
           WHERE j.review_id = NEW.review_id
             AND j.repository = NEW.repository
             AND j.pr_number = NEW.pr_number
             AND lower(j.head_sha) = lower(NEW.head_sha)
             AND j.gate_kind = NEW.gate_kind
             AND j.snapshot_artifact_id = NEW.snapshot_artifact_id
         ) THEN RAISE(ABORT, 'formal_review_snapshot_identity_mismatch') END;
         SELECT CASE WHEN NOT EXISTS (
           SELECT 1 FROM artifacts a
           WHERE a.artifact_id = NEW.snapshot_artifact_id
             AND a.sha256 = NEW.snapshot_sha256
         ) THEN RAISE(ABORT, 'formal_review_snapshot_integrity_mismatch') END;
       END""",
    """CREATE TRIGGER IF NOT EXISTS authority_snapshot_seal_immutable_update
       BEFORE UPDATE ON formal_review_snapshot_seals
       BEGIN
         SELECT RAISE(ABORT, 'formal_review_snapshot_seal_immutable');
       END""",
    """CREATE TRIGGER IF NOT EXISTS authority_snapshot_seal_immutable_delete
       BEFORE DELETE ON formal_review_snapshot_seals
       BEGIN
         SELECT RAISE(ABORT, 'formal_review_snapshot_seal_immutable');
       END""",
)

# Keep v4 byte-for-byte compatible with the pre-cutover schema already applied
# by soak environments. Immutability and subject uniqueness were added later,
# so they belong in a forward-only migration instead of rewriting v4.
_V5_STATEMENTS = (
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_authority_job_subject_unique ON authority_jobs(job_kind, subject_id)",
    """CREATE TRIGGER IF NOT EXISTS authority_message_metadata_immutable_update
       BEFORE UPDATE ON authority_message_metadata
       BEGIN
         SELECT RAISE(ABORT, 'authority_message_metadata_immutable');
       END""",
    """CREATE TRIGGER IF NOT EXISTS authority_message_metadata_immutable_delete
       BEFORE DELETE ON authority_message_metadata
       BEGIN
         SELECT RAISE(ABORT, 'authority_message_metadata_immutable');
       END""",
    """CREATE TRIGGER IF NOT EXISTS authority_comms_message_immutable_update
       BEFORE UPDATE ON comms_messages
       WHEN EXISTS (
         SELECT 1 FROM authority_message_metadata meta
         WHERE meta.message_id = OLD.message_id
       )
       BEGIN
         SELECT RAISE(ABORT, 'authority_message_immutable');
       END""",
    """CREATE TRIGGER IF NOT EXISTS authority_comms_message_immutable_delete
       BEFORE DELETE ON comms_messages
       WHEN EXISTS (
         SELECT 1 FROM authority_message_metadata meta
         WHERE meta.message_id = OLD.message_id
       )
       BEGIN
         SELECT RAISE(ABORT, 'authority_message_immutable');
       END""",
    """CREATE TRIGGER IF NOT EXISTS authority_context_revision_immutable_update
       BEFORE UPDATE ON authority_context_revisions
       BEGIN
         SELECT RAISE(ABORT, 'authority_context_revision_immutable');
       END""",
    """CREATE TRIGGER IF NOT EXISTS authority_context_revision_immutable_delete
       BEFORE DELETE ON authority_context_revisions
       BEGIN
         SELECT RAISE(ABORT, 'authority_context_revision_immutable');
       END""",
)

# #6293: shared, transactionally admitted routing reservations.  This is
# intentionally part of the Fleet Comms authority SQLite rather than a
# worktree-local cache: quota admission must serialize across every initiator.
_V6_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS routing_reservations (
        reservation_id TEXT PRIMARY KEY,
        authority_key TEXT NOT NULL,
        attempt INTEGER NOT NULL CHECK (attempt > 0),
        idempotency_key TEXT NOT NULL,
        request_sha256 TEXT NOT NULL,
        initiator TEXT NOT NULL,
        author_model TEXT NOT NULL,
        author_family TEXT NOT NULL,
        requested_role TEXT NOT NULL,
        requested_profile TEXT NOT NULL,
        requested_risk TEXT NOT NULL,
        route_mode TEXT NOT NULL CHECK (route_mode IN ('auto', 'explicit')),
        resolved_candidate TEXT NOT NULL,
        resolved_route TEXT NOT NULL,
        resolved_model TEXT NOT NULL,
        resolved_family TEXT NOT NULL,
        quota_bucket TEXT NOT NULL,
        policy_version TEXT NOT NULL,
        estimated_input_bytes INTEGER NOT NULL CHECK (estimated_input_bytes >= 0),
        quota_snapshot_json TEXT NOT NULL,
        quota_fresh_at TEXT,
        trace_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        started_at TEXT,
        settled_at TEXT,
        status TEXT NOT NULL CHECK (status IN (
            'reserved', 'running', 'complete', 'failed', 'expired', 'cancelled'
        )),
        actual_bytes INTEGER,
        actual_tokens INTEGER,
        failure_classification TEXT,
        terminal_sha256 TEXT,
        UNIQUE (authority_key, attempt),
        UNIQUE (authority_key, idempotency_key)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_routing_reservations_active_bucket ON routing_reservations(quota_bucket, status, expires_at)",
    "CREATE INDEX IF NOT EXISTS idx_routing_reservations_authority ON routing_reservations(authority_key, attempt DESC)",
    """CREATE TABLE IF NOT EXISTS routing_reservation_decisions (
        decision_id TEXT PRIMARY KEY,
        reservation_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        state TEXT NOT NULL,
        evidence_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (reservation_id) REFERENCES routing_reservations(reservation_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_routing_reservation_decisions_reservation ON routing_reservation_decisions(reservation_id, created_at)",
    """CREATE TRIGGER IF NOT EXISTS routing_reservation_decisions_immutable_update
       BEFORE UPDATE ON routing_reservation_decisions
       BEGIN
         SELECT RAISE(ABORT, 'routing_reservation_decision_immutable');
       END""",
    """CREATE TRIGGER IF NOT EXISTS routing_reservation_decisions_immutable_delete
       BEFORE DELETE ON routing_reservation_decisions
       BEGIN
         SELECT RAISE(ABORT, 'routing_reservation_decision_immutable');
       END""",
    """CREATE TABLE IF NOT EXISTS routing_circuit_state (
        route_key TEXT PRIMARY KEY,
        recent_failure_count INTEGER NOT NULL DEFAULT 0 CHECK (recent_failure_count >= 0),
        last_failure_at TEXT,
        last_failure_classification TEXT,
        open_until TEXT,
        updated_at TEXT NOT NULL
    )""",
)

# #6293 follow-up: admission is credential-scoped while accounting remains
# quota-scoped.  Keep this forward-only because v6 may already exist in a
# shared authority database when a process restarts.
_V7_STATEMENTS = (
    "ALTER TABLE routing_reservations ADD COLUMN credential_bucket TEXT NOT NULL DEFAULT ''",
    "UPDATE routing_reservations SET credential_bucket = quota_bucket WHERE credential_bucket = ''",
    "ALTER TABLE routing_reservations ADD COLUMN semantic_sha256 TEXT NOT NULL DEFAULT ''",
    "UPDATE routing_reservations SET semantic_sha256 = request_sha256 WHERE semantic_sha256 = ''",
    "ALTER TABLE routing_reservations ADD COLUMN requested_reviewer TEXT",
    "ALTER TABLE routing_reservations ADD COLUMN fallback_from TEXT",
    "ALTER TABLE routing_reservations ADD COLUMN retry_attempt INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE routing_reservations ADD COLUMN quota_source TEXT NOT NULL DEFAULT 'unknown'",
    "ALTER TABLE routing_reservations ADD COLUMN quota_headroom_band TEXT NOT NULL DEFAULT 'unknown'",
    "ALTER TABLE routing_reservations ADD COLUMN actual_input_bytes INTEGER",
    "ALTER TABLE routing_reservations ADD COLUMN actual_output_bytes INTEGER",
    "ALTER TABLE routing_reservations ADD COLUMN actual_input_tokens INTEGER",
    "ALTER TABLE routing_reservations ADD COLUMN actual_output_tokens INTEGER",
    "CREATE INDEX IF NOT EXISTS idx_routing_reservations_active_credential ON routing_reservations(credential_bucket, status, expires_at)",
)

MIGRATIONS = (
    Migration(version=1, name="fleet-comms-v1-contracts", statements=_V1_STATEMENTS),
    Migration(
        version=2,
        name="fleet-comms-v2-sealed-verdict-artifact",
        statements=_V2_STATEMENTS,
    ),
    Migration(version=3, name="fleet-comms-v3-acpx-discussions", statements=_V3_STATEMENTS),
    Migration(
        version=4,
        name="fleet-comms-v4-authority-queue-and-seals",
        statements=_V4_STATEMENTS,
    ),
    Migration(
        version=5,
        name="fleet-comms-v5-authority-immutability",
        statements=_V5_STATEMENTS,
    ),
    Migration(
        version=6,
        name="fleet-comms-v6-routing-reservations",
        statements=_V6_STATEMENTS,
    ),
    Migration(
        version=7,
        name="fleet-comms-v7-routing-credential-admission",
        statements=_V7_STATEMENTS,
    ),
)

# During the pre-merge #6159 soak, one development build applied the v5
# constraints while they were still embedded in v4. Both checksums describe
# the same authority contract after v5; accept only that exact observed hash
# so live local history can advance without deleting or rewriting receipts.
_COMPATIBLE_MIGRATION_CHECKSUMS = {
    4: frozenset(
        {
            MIGRATIONS[3].checksum,
            "a563b19a7a0cf84c5425a56f4338fc650ceb3266d26540aefe95cd64d371bb44",
        }
    )
}


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})")}


def _ensure_delivery_contract_columns(conn: sqlite3.Connection) -> None:
    """Extend the legacy channel table instead of replacing its live writers."""
    if not _table_exists(conn, "deliveries"):
        conn.execute(
            """CREATE TABLE deliveries (
                delivery_id TEXT PRIMARY KEY,
                request_id TEXT,
                endpoint_id TEXT,
                status TEXT NOT NULL,
                expires_at TEXT,
                fence_token INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )"""
        )
        return
    existing = _columns(conn, "deliveries")
    additions = {
        "request_id": "TEXT",
        "endpoint_id": "TEXT",
        "expires_at": "TEXT",
        "fence_token": "INTEGER NOT NULL DEFAULT 0",
    }
    for name, definition in additions.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE deliveries ADD COLUMN {name} {definition}")


def _ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS comms_schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )"""
    )


def _applied_migrations(conn: sqlite3.Connection) -> dict[int, tuple[str, str]]:
    return {
        int(row[0]): (str(row[1]), str(row[2]))
        for row in conn.execute("SELECT version, name, checksum FROM comms_schema_migrations")
    }


def _validate_applied_migrations(
    applied: dict[int, tuple[str, str]],
    known: dict[int, Migration],
) -> None:
    unknown = set(applied).difference(known)
    if unknown:
        raise CommsMigrationError(f"Unsupported future communications schema version(s): {sorted(unknown)}")
    for version, (name, checksum) in applied.items():
        expected = known[version]
        compatible = _COMPATIBLE_MIGRATION_CHECKSUMS.get(
            version, frozenset({expected.checksum})
        )
        if name != expected.name or checksum not in compatible:
            raise CommsMigrationError(f"Communications migration {version} has an unexpected checksum")


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Apply each known migration atomically and refuse unknown future versions."""
    _ensure_migration_table(conn)
    conn.commit()
    known = {migration.version: migration for migration in MIGRATIONS}
    applied = _applied_migrations(conn)
    _validate_applied_migrations(applied, known)
    # Finish the optimistic read before acquiring a write transaction below.
    # Some connection configurations retain that read transaction, in which
    # case SQLite rejects a nested ``BEGIN IMMEDIATE``.
    conn.commit()
    for migration in MIGRATIONS:
        if migration.version in applied:
            continue
        try:
            conn.execute("BEGIN IMMEDIATE")
            # A concurrent opener may have committed this version while this
            # connection waited for the write lock. Re-read only after the
            # lock is held; the pre-lock snapshot is not safe for INSERTs.
            applied = _applied_migrations(conn)
            _validate_applied_migrations(applied, known)
            if migration.version in applied:
                conn.commit()
                continue
            _ensure_delivery_contract_columns(conn)
            for statement in migration.statements:
                conn.execute(statement)
            conn.execute(
                "INSERT INTO comms_schema_migrations(version, name, checksum, applied_at) VALUES (?, ?, ?, ?)",
                (migration.version, migration.name, migration.checksum, datetime.now(UTC).isoformat()),
            )
            conn.commit()
            applied[migration.version] = (migration.name, migration.checksum)
        except Exception:
            conn.rollback()
            raise
    return max(applied.keys(), default=0)
