"""Narrow Postgres DDL for the request-plane slice (private #605).

Covers ONLY the three tables the pg-capable request path touches:
``conversations`` / ``comms_messages`` / ``requests``. Column types keep
TEXT-parity with the sqlite schema in ``scripts.fleet_comms.migrations``
(ISO-8601 timestamps and JSON payloads stay TEXT) so rows are comparable
across engines during the pre-cutover period. This is deliberately NOT a
mirror of the full sqlite migration chain — authority-queue, routing, and
review tables arrive with their own slices.

The connection is expected to be autocommit (the ArtifactStore pg pattern);
DDL runs inside one explicit ``conn.transaction()`` so a failure cannot
leave a half-created table set.
"""

from __future__ import annotations

from typing import Any

PG_SCHEMA_STATEMENTS: tuple[str, ...] = (
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
)


def apply_pg_schema(conn: Any) -> None:
    """Create the request-plane tables; idempotent, in ONE transaction."""
    with conn.transaction():
        for statement in PG_SCHEMA_STATEMENTS:
            conn.execute(statement)
