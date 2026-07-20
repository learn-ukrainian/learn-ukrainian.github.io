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

MIGRATIONS = (
    Migration(version=1, name="fleet-comms-v1-contracts", statements=_V1_STATEMENTS),
    Migration(
        version=2,
        name="fleet-comms-v2-sealed-verdict-artifact",
        statements=_V2_STATEMENTS,
    ),
)


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


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Apply each known migration atomically and refuse unknown future versions."""
    _ensure_migration_table(conn)
    conn.commit()
    known = {migration.version: migration for migration in MIGRATIONS}
    applied = {
        int(row[0]): (str(row[1]), str(row[2]))
        for row in conn.execute("SELECT version, name, checksum FROM comms_schema_migrations")
    }
    unknown = set(applied).difference(known)
    if unknown:
        raise CommsMigrationError(f"Unsupported future communications schema version(s): {sorted(unknown)}")
    for version, (name, checksum) in applied.items():
        expected = known[version]
        if name != expected.name or checksum != expected.checksum:
            raise CommsMigrationError(f"Communications migration {version} has an unexpected checksum")
    for migration in MIGRATIONS:
        if migration.version in applied:
            continue
        try:
            conn.execute("BEGIN IMMEDIATE")
            _ensure_delivery_contract_columns(conn)
            for statement in migration.statements:
                conn.execute(statement)
            conn.execute(
                "INSERT INTO comms_schema_migrations(version, name, checksum, applied_at) VALUES (?, ?, ?, ?)",
                (migration.version, migration.name, migration.checksum, datetime.now(UTC).isoformat()),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return MIGRATIONS[-1].version if MIGRATIONS else 0
