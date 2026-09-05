"""Numbered/checksummed Postgres migration ledger for Fleet Comms (#7483 1.14).

Owns the pg byte-plane blob table plus the narrow request-plane tables the
pg-capable execute path touches. Column types keep TEXT-parity with the
sqlite schema in ``scripts.fleet_comms.migrations`` (ISO-8601 timestamps and
JSON payloads stay TEXT) so rows are comparable across engines during the
pre-cutover period. This is deliberately NOT a mirror of the full sqlite
migration chain — authority-queue, routing, and review tables arrive with
their own slices.

The connection is expected to be autocommit (the ArtifactStore pg pattern);
each migration runs inside one explicit ``conn.transaction()`` so a failure
cannot leave a half-created table set, and receipts land in
``fleet_comms_pg_schema_migrations`` with a SHA-256 checksum over the
statement payload. ``verify_pg_schema`` is the read-only drift gate used
before authority enablement.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

PG_BLOB_TABLE = "fleet_comms_artifact_blobs"
PG_MIGRATION_TABLE = "fleet_comms_pg_schema_migrations"


class PgSchemaError(RuntimeError):
    """A pg schema is newer, corrupt, incomplete, or otherwise unsafe."""


@dataclass(frozen=True, slots=True)
class PgMigration:
    version: int
    name: str
    statements: tuple[str, ...]

    @property
    def checksum(self) -> str:
        payload = "\n".join(self.statements).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


# #7483 (1.14): blob DDL leaves ArtifactStore inline CREATE and lives in the
# numbered ledger so drift is detectable before pg authority enablement.
_V1_ARTIFACT_BLOBS = (
    f"""CREATE TABLE IF NOT EXISTS {PG_BLOB_TABLE} (
        sha256 TEXT PRIMARY KEY,
        artifact_id TEXT NOT NULL UNIQUE,
        bytes BIGINT NOT NULL,
        mime_type TEXT,
        logical_filename TEXT,
        producer TEXT NOT NULL,
        retention_class TEXT NOT NULL,
        created_at TEXT NOT NULL,
        payload BYTEA NOT NULL
    )""",
)

# Request-plane tables (private #605). The artifact side of message_artifacts
# points at the pg byte-plane table (UNIQUE artifact_id), so v1 must apply
# before this version.
_V2_REQUEST_PLANE = (
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
    f"""CREATE TABLE IF NOT EXISTS message_artifacts (
        message_id TEXT NOT NULL,
        artifact_id TEXT NOT NULL,
        relation TEXT NOT NULL,
        PRIMARY KEY (message_id, artifact_id, relation),
        FOREIGN KEY (message_id) REFERENCES comms_messages(message_id),
        FOREIGN KEY (artifact_id) REFERENCES {PG_BLOB_TABLE}(artifact_id)
    )""",
)

# Back-compat alias: older callers imported the request-plane tuple directly.
PG_SCHEMA_STATEMENTS: tuple[str, ...] = _V2_REQUEST_PLANE

# V4 canonical authority store (PR #7662 repair 6): the operator-approved
# extension of this same pg plane for text-free full execution observations
# and Sources invocation records. See ``scripts.fleet_comms.v4_canonical_
# authority_store`` for the write/resolve contract. TEXT-parity with the
# sqlite migration below, same as every other table in this ledger.
_V3_V4_CANONICAL_AUTHORITY = (
    """CREATE TABLE IF NOT EXISTS v4_execution_observations (
        task_id TEXT NOT NULL,
        run_id TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('author', 'reviewer')),
        record_sha256 TEXT NOT NULL,
        record_json TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        PRIMARY KEY (task_id, run_id, role)
    )""",
    """CREATE TABLE IF NOT EXISTS v4_sources_invocations (
        invocation_id TEXT PRIMARY KEY,
        record_sha256 TEXT NOT NULL,
        record_json TEXT NOT NULL,
        recorded_at TEXT NOT NULL
    )""",
)

# V4 canonical authority store, execution-boundary slice (PR #7662 repair 7):
# pre-execution dispatch authorization plus request-correlation columns. See
# the sqlite twin ``scripts.fleet_comms.migrations._V9_STATEMENTS``.
_V4_EXECUTION_DISPATCH_BINDING = (
    """CREATE TABLE IF NOT EXISTS v4_execution_dispatch_bindings (
        request_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        run_id TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('author', 'reviewer')),
        record_sha256 TEXT NOT NULL,
        record_json TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        UNIQUE (task_id, run_id, role)
    )""",
    "ALTER TABLE v4_execution_observations ADD COLUMN IF NOT EXISTS request_id TEXT",
    "ALTER TABLE v4_sources_invocations ADD COLUMN IF NOT EXISTS request_id TEXT",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_v4_execution_observations_request ON v4_execution_observations(request_id)",
    "CREATE INDEX IF NOT EXISTS idx_v4_sources_invocations_request ON v4_sources_invocations(request_id)",
)

# V4 runner-owned execution attempts + per-attempt Sources capability
# (PR #7662 repair 8). The native runner claims one attempt immediately
# before Popen and stores only the capability digest; Sources HTTP auth
# resolves that digest to the active attempt. Sqlite twin:
# ``scripts.fleet_comms.migrations._V10_STATEMENTS``.
_V5_V4_RUNNER_ATTEMPTS = (
    """CREATE TABLE IF NOT EXISTS v4_execution_attempts (
        attempt_id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL UNIQUE,
        task_id TEXT NOT NULL,
        run_id TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('author', 'reviewer')),
        state TEXT NOT NULL CHECK (state IN ('running', 'terminal')),
        capability_digest TEXT NOT NULL UNIQUE,
        binding_sha256 TEXT NOT NULL,
        started_at TEXT NOT NULL,
        terminal_at TEXT
    )""",
    "ALTER TABLE v4_sources_invocations ADD COLUMN IF NOT EXISTS attempt_id TEXT",
    "CREATE INDEX IF NOT EXISTS idx_v4_sources_invocations_attempt ON v4_sources_invocations(attempt_id)",
    """CREATE TABLE IF NOT EXISTS v4_authorship_receipts (
        receipt_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        run_id TEXT NOT NULL,
        record_sha256 TEXT NOT NULL,
        record_json TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        UNIQUE (task_id, run_id)
    )""",
)

MIGRATIONS: tuple[PgMigration, ...] = (
    PgMigration(
        version=1,
        name="fleet-comms-pg-v1-artifact-blobs",
        statements=_V1_ARTIFACT_BLOBS,
    ),
    PgMigration(
        version=2,
        name="fleet-comms-pg-v2-request-plane",
        statements=_V2_REQUEST_PLANE,
    ),
    PgMigration(
        version=3,
        name="fleet-comms-pg-v3-v4-canonical-authority",
        statements=_V3_V4_CANONICAL_AUTHORITY,
    ),
    PgMigration(
        version=4,
        name="fleet-comms-pg-v4-execution-dispatch-binding",
        statements=_V4_EXECUTION_DISPATCH_BINDING,
    ),
    PgMigration(
        version=5,
        name="fleet-comms-pg-v5-v4-runner-attempts",
        statements=_V5_V4_RUNNER_ATTEMPTS,
    ),
)


def _ensure_migration_table(conn: Any) -> None:
    conn.execute(
        f"""CREATE TABLE IF NOT EXISTS {PG_MIGRATION_TABLE} (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )"""
    )


def _applied_migrations(conn: Any) -> dict[int, tuple[str, str]]:
    rows = conn.execute(
        f"SELECT version, name, checksum FROM {PG_MIGRATION_TABLE}"
    ).fetchall()
    applied: dict[int, tuple[str, str]] = {}
    for row in rows:
        if isinstance(row, dict):
            version, name, checksum = int(row["version"]), str(row["name"]), str(row["checksum"])
        else:
            version, name, checksum = int(row[0]), str(row[1]), str(row[2])
        applied[version] = (name, checksum)
    return applied


def _validate_applied_migrations(
    applied: dict[int, tuple[str, str]],
    known: dict[int, PgMigration],
) -> None:
    unknown = set(applied).difference(known)
    if unknown:
        raise PgSchemaError(f"Unsupported future fleet_comms pg schema version(s): {sorted(unknown)}")
    for version, (name, checksum) in applied.items():
        expected = known[version]
        if name != expected.name or checksum != expected.checksum:
            raise PgSchemaError(f"fleet_comms pg migration {version} has an unexpected checksum")


def verify_pg_schema(conn: Any) -> int:
    """Verify the complete applied pg-migration receipt set without mutating it.

    Authority enablement must not be the operation that repairs a target
    schema. This read-only check requires every currently-known migration,
    its expected name, and its checksum receipt before a caller can treat
    the pg plane as authoritative.
    """
    known = {migration.version: migration for migration in MIGRATIONS}
    try:
        applied = _applied_migrations(conn)
    except Exception as exc:
        raise PgSchemaError("fleet_comms pg migration receipts unavailable") from exc
    _validate_applied_migrations(applied, known)
    if set(applied) != set(known):
        raise PgSchemaError("fleet_comms pg migration version set is incomplete")
    return max(applied, default=0)


def apply_pg_schema(conn: Any) -> int:
    """Apply each known pg migration atomically and refuse unknown future versions.

    Idempotent: ``CREATE TABLE IF NOT EXISTS`` plus a receipt row per version.
    Returns the highest applied version.
    """
    known = {migration.version: migration for migration in MIGRATIONS}
    with conn.transaction():
        _ensure_migration_table(conn)
        applied = _applied_migrations(conn)
        _validate_applied_migrations(applied, known)
        for migration in MIGRATIONS:
            if migration.version in applied:
                continue
            for statement in migration.statements:
                conn.execute(statement)
            conn.execute(
                f"INSERT INTO {PG_MIGRATION_TABLE}(version, name, checksum, applied_at) "
                "VALUES (%s, %s, %s, %s)",
                (
                    migration.version,
                    migration.name,
                    migration.checksum,
                    datetime.now(UTC).isoformat(),
                ),
            )
            applied[migration.version] = (migration.name, migration.checksum)
    return max(applied.keys(), default=0)
