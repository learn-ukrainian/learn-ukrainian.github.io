"""Transactional append, digest, and lifecycle API for session streams."""

from __future__ import annotations

import os
import re
import sqlite3
import uuid
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager, suppress
from datetime import datetime, timedelta
from typing import Any

from .db import SessionStreamDatabase
from .model import (
    PINNED_ENTRY_TYPES,
    Entry,
    EntryRef,
    EntryType,
    ForceCloseProof,
    Lease,
    LeaseHolder,
    SessionState,
    StreamDigest,
    canonical_json,
    entry_as_dict,
    isoformat_z,
    parse_timestamp,
    sha256_text,
    utc_now,
    validate_stream_id,
)

MAX_ENTRY_BYTES = 65_536
MAX_TTL_SECONDS = 86_400
SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |PGP )?PRIVATE KEY-----")),
    ("credential-token", re.compile(r"(?:sk-|gh[pousr]_|AIza)[A-Za-z0-9_-]{16,}")),
    (
        "credential-assignment",
        re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*[^\s]{8,}"),
    ),
)
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)\+[0-9][0-9 ()-]{7,}[0-9](?!\w)")


class SessionStreamError(RuntimeError):
    """Base runtime error for a refused session-stream operation."""


class NotFoundError(SessionStreamError):
    """Raised when an exact stream/session/lease identity is absent."""


class LeaseConflictError(SessionStreamError):
    """Raised when a mutation lacks the exact current valid lease."""


class LifecycleError(SessionStreamError):
    """Raised when a requested session state change is unsafe."""


class ContentRejectedError(SessionStreamError):
    """Raised without echoing body content when a hygiene rule rejects it."""


def process_exists(process_id: int) -> bool:
    """Return whether a local process currently owns this PID."""
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def validate_entry_body(body: str) -> None:
    if not isinstance(body, str):
        raise ContentRejectedError("entry body rejected by text-type rule")
    encoded = body.encode("utf-8")
    if not encoded:
        raise ContentRejectedError("entry body rejected by non-empty rule")
    if len(encoded) > MAX_ENTRY_BYTES:
        raise ContentRejectedError("entry body rejected by 64-KiB rule")
    if "\x00" in body or any(ord(char) < 32 and char not in "\n\r\t" for char in body):
        raise ContentRejectedError("entry body rejected by control-character rule")
    for rule, pattern in SECRET_PATTERNS:
        if pattern.search(body):
            raise ContentRejectedError(f"entry body rejected by {rule} rule")
    if EMAIL_RE.search(body):
        raise ContentRejectedError("entry body rejected by email-address rule")
    if PHONE_RE.search(body):
        raise ContentRejectedError("entry body rejected by phone-number rule")


class SessionStreamStore:
    """High-level API that keeps lifecycle projections fenced and auditable."""

    def __init__(
        self,
        database: SessionStreamDatabase,
        *,
        _process_probe: Callable[[int], bool] = process_exists,
    ) -> None:
        self.database = database
        self._process_probe = _process_probe

    @contextmanager
    def _transaction(self, *, now: datetime | None = None) -> Iterator[sqlite3.Connection]:
        connection = self.database.connect(now=now)
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.execute("COMMIT")
        except Exception:
            with suppress(sqlite3.Error):
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    @contextmanager
    def _read_snapshot(self) -> Iterator[sqlite3.Connection]:
        """Hold one WAL snapshot across every query that forms a read response."""
        connection = self.database.connect(read_only=True)
        try:
            connection.execute("BEGIN")
            yield connection
            connection.execute("COMMIT")
        except Exception:
            with suppress(sqlite3.Error):
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def open_session(
        self,
        *,
        stream_id: str,
        holder: LeaseHolder,
        lineage_id: str,
        ttl_seconds: int,
        session_id: str | None = None,
        lease_id: str | None = None,
        now: datetime | None = None,
        reason: str = "harness session start",
    ) -> Lease:
        """Open a distinct driver-run session only when its stream has no live session."""
        stream_id = validate_stream_id(stream_id)
        holder.validate()
        self._validate_identity("lineage_id", lineage_id)
        session_id = session_id or f"session-{uuid.uuid4().hex}"
        lease_id = lease_id or f"lease-{uuid.uuid4().hex}"
        self._validate_identity("session_id", session_id)
        self._validate_identity("lease_id", lease_id)
        self._validate_ttl(ttl_seconds)
        current_time = now or utc_now()
        timestamp = isoformat_z(current_time)
        expires_at = isoformat_z(current_time + timedelta(seconds=ttl_seconds))

        with self._transaction(now=current_time) as connection:
            self._ensure_stream(connection, stream_id=stream_id, created_at=timestamp)
            live = connection.execute(
                "SELECT session_id, state FROM sessions "
                "WHERE stream_id = ? AND state IN ('open', 'rolling')",
                (stream_id,),
            ).fetchone()
            if live is not None:
                raise LifecycleError(
                    f"stream {stream_id} already has live session {live['session_id']} ({live['state']})"
                )
            prior_lease = connection.execute(
                "SELECT * FROM stream_leases WHERE stream_id = ?",
                (stream_id,),
            ).fetchone()
            if prior_lease is not None and prior_lease["state"] != "released":
                raise LifecycleError(f"stream {stream_id} retains an unreleased lease")
            generation = 1 if prior_lease is None else int(prior_lease["generation"]) + 1
            fencing_token = 1 if prior_lease is None else int(prior_lease["fencing_token"]) + 1

            connection.execute(
                "INSERT INTO sessions("
                "session_id, stream_id, state, lineage_id, opened_at, updated_at, closed_at, state_version"
                ") VALUES (?, ?, 'open', ?, ?, ?, NULL, 1)",
                (session_id, stream_id, lineage_id, timestamp, timestamp),
            )
            connection.execute(
                "INSERT INTO session_events("
                "stream_id, session_id, from_state, to_state, ts, agent, harness, reason, proof_json"
                ") VALUES (?, ?, NULL, 'open', ?, ?, ?, ?, '{}')",
                (stream_id, session_id, timestamp, holder.agent, holder.harness, reason),
            )
            lease_event_id = self._insert_lease_event(
                connection,
                stream_id=stream_id,
                session_id=session_id,
                lease_id=lease_id,
                generation=generation,
                fencing_token=fencing_token,
                event_type="acquired",
                holder=holder,
                ttl_seconds=ttl_seconds,
                timestamp=timestamp,
                proof={},
                reason=reason,
            )
            if prior_lease is None:
                connection.execute(
                    "INSERT INTO stream_leases("
                    "stream_id, session_id, lease_id, generation, fencing_token, state, "
                    "holder_agent, holder_harness, holder_instance_id, holder_task_id, holder_process_id, "
                    "heartbeat_at, expires_at, ttl_seconds, version, last_event_id"
                    ") VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)",
                    (
                        stream_id,
                        session_id,
                        lease_id,
                        generation,
                        fencing_token,
                        holder.agent,
                        holder.harness,
                        holder.instance_id,
                        holder.task_id,
                        holder.process_id,
                        timestamp,
                        expires_at,
                        ttl_seconds,
                        lease_event_id,
                    ),
                )
                version = 1
            else:
                version = int(prior_lease["version"]) + 1
                connection.execute(
                    "UPDATE stream_leases SET "
                    "session_id = ?, lease_id = ?, generation = ?, fencing_token = ?, state = 'active', "
                    "holder_agent = ?, holder_harness = ?, holder_instance_id = ?, holder_task_id = ?, "
                    "holder_process_id = ?, heartbeat_at = ?, expires_at = ?, ttl_seconds = ?, "
                    "version = ?, last_event_id = ? WHERE stream_id = ?",
                    (
                        session_id,
                        lease_id,
                        generation,
                        fencing_token,
                        holder.agent,
                        holder.harness,
                        holder.instance_id,
                        holder.task_id,
                        holder.process_id,
                        timestamp,
                        expires_at,
                        ttl_seconds,
                        version,
                        lease_event_id,
                        stream_id,
                    ),
                )
        return Lease(
            stream_id=stream_id,
            session_id=session_id,
            lease_id=lease_id,
            generation=generation,
            fencing_token=fencing_token,
            holder=holder,
            heartbeat_at=timestamp,
            expires_at=expires_at,
            ttl_seconds=ttl_seconds,
            version=version,
        )

    def heartbeat(self, lease: Lease, *, now: datetime | None = None) -> Lease:
        """Renew an exact holder's TTL; an expired holder may revive only itself."""
        current_time = now or utc_now()
        timestamp = isoformat_z(current_time)
        with self._transaction(now=current_time) as connection:
            row = self._require_current_lease(connection, lease)
            if current_time < parse_timestamp(str(row["heartbeat_at"])):
                raise LeaseConflictError("heartbeat time cannot move backwards")
            expires_at = isoformat_z(current_time + timedelta(seconds=int(row["ttl_seconds"])))
            event_id = self._insert_lease_event_from_row(
                connection,
                row=row,
                event_type="heartbeat",
                timestamp=timestamp,
                proof={},
                reason="harness heartbeat",
            )
            version = int(row["version"]) + 1
            connection.execute(
                "UPDATE stream_leases SET heartbeat_at = ?, expires_at = ?, version = ?, last_event_id = ? "
                "WHERE stream_id = ?",
                (timestamp, expires_at, version, event_id, lease.stream_id),
            )
        return Lease(
            stream_id=lease.stream_id,
            session_id=lease.session_id,
            lease_id=lease.lease_id,
            generation=lease.generation,
            fencing_token=lease.fencing_token,
            holder=lease.holder,
            heartbeat_at=timestamp,
            expires_at=expires_at,
            ttl_seconds=lease.ttl_seconds,
            version=version,
        )

    def transition_session(
        self,
        lease: Lease,
        *,
        to_state: SessionState,
        reason: str,
        now: datetime | None = None,
    ) -> SessionState:
        """Move open↔rolling under a currently valid lease."""
        if to_state not in {SessionState.OPEN, SessionState.ROLLING}:
            raise LifecycleError("transition_session only supports open and rolling")
        current_time = now or utc_now()
        timestamp = isoformat_z(current_time)
        with self._transaction(now=current_time) as connection:
            row = self._require_current_lease(connection, lease, require_valid_at=current_time)
            session = self._session_row(connection, lease.stream_id, lease.session_id)
            from_state = SessionState(str(session["state"]))
            allowed = (from_state, to_state) in {
                (SessionState.OPEN, SessionState.ROLLING),
                (SessionState.ROLLING, SessionState.OPEN),
            }
            if not allowed:
                raise LifecycleError(f"invalid session transition {from_state.value}->{to_state.value}")
            connection.execute(
                "INSERT INTO session_events("
                "stream_id, session_id, from_state, to_state, ts, agent, harness, reason, proof_json"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{}')",
                (
                    lease.stream_id,
                    lease.session_id,
                    from_state.value,
                    to_state.value,
                    timestamp,
                    row["holder_agent"],
                    row["holder_harness"],
                    reason,
                ),
            )
            connection.execute(
                "UPDATE sessions SET state = ?, updated_at = ?, state_version = state_version + 1 "
                "WHERE stream_id = ? AND session_id = ?",
                (to_state.value, timestamp, lease.stream_id, lease.session_id),
            )
        return to_state

    def close_session(
        self,
        lease: Lease,
        *,
        reason: str = "harness clean exit",
        now: datetime | None = None,
    ) -> SessionState:
        """Idempotently close the exact holder's session; closed remains immutable."""
        current_time = now or utc_now()
        timestamp = isoformat_z(current_time)
        with self._transaction(now=current_time) as connection:
            session = self._session_row(connection, lease.stream_id, lease.session_id)
            if session["state"] == SessionState.CLOSED.value:
                historical_lease = connection.execute(
                    "SELECT 1 FROM lease_events WHERE "
                    "stream_id = ? AND session_id = ? AND lease_id = ? "
                    "AND generation = ? AND fencing_token = ? "
                    "AND holder_agent = ? AND holder_harness = ? AND holder_instance_id = ? "
                    "AND holder_task_id IS ? AND holder_process_id = ? LIMIT 1",
                    (
                        lease.stream_id,
                        lease.session_id,
                        lease.lease_id,
                        lease.generation,
                        lease.fencing_token,
                        lease.holder.agent,
                        lease.holder.harness,
                        lease.holder.instance_id,
                        lease.holder.task_id,
                        lease.holder.process_id,
                    ),
                ).fetchone()
                if historical_lease is not None:
                    return SessionState.CLOSED
                raise LeaseConflictError("closed session does not match the supplied historical lease")
            row = self._require_current_lease(connection, lease)
            proof = {"kind": "session_stream_clean_exit.v1", "holder_instance_id": lease.holder.instance_id}
            event_id = self._insert_lease_event_from_row(
                connection,
                row=row,
                event_type="released",
                timestamp=timestamp,
                proof=proof,
                reason=reason,
            )
            connection.execute(
                "UPDATE stream_leases SET state = 'released', version = version + 1, last_event_id = ? "
                "WHERE stream_id = ?",
                (event_id, lease.stream_id),
            )
            connection.execute(
                "INSERT INTO session_events("
                "stream_id, session_id, from_state, to_state, ts, agent, harness, reason, proof_json"
                ") VALUES (?, ?, ?, 'closed', ?, ?, ?, ?, ?)",
                (
                    lease.stream_id,
                    lease.session_id,
                    session["state"],
                    timestamp,
                    row["holder_agent"],
                    row["holder_harness"],
                    reason,
                    canonical_json(proof),
                ),
            )
            connection.execute(
                "UPDATE sessions SET state = 'closed', closed_at = ?, updated_at = ?, "
                "state_version = state_version + 1 WHERE stream_id = ? AND session_id = ?",
                (timestamp, timestamp, lease.stream_id, lease.session_id),
            )
        return SessionState.CLOSED

    def force_close_expired_session(
        self,
        *,
        stream_id: str,
        session_id: str,
        candidate: LeaseHolder,
        now: datetime | None = None,
        reason: str = "proof-gated crashed-holder force close",
    ) -> ForceCloseProof:
        """Force-close only an expired session whose exact holder process is absent."""
        stream_id = validate_stream_id(stream_id)
        candidate.validate()
        current_time = now or utc_now()
        timestamp = isoformat_z(current_time)
        with self._transaction(now=current_time) as connection:
            session = self._session_row(connection, stream_id, session_id)
            if session["state"] == SessionState.CLOSED.value:
                raise LifecycleError("closed sessions are immutable and cannot be force-closed again")
            row = connection.execute(
                "SELECT * FROM stream_leases WHERE stream_id = ? AND session_id = ?",
                (stream_id, session_id),
            ).fetchone()
            if row is None or row["state"] != "active":
                raise LeaseConflictError("crashed session has no exact active lease to prove and close")
            expires_at = parse_timestamp(str(row["expires_at"]))
            if current_time < expires_at:
                raise LeaseConflictError("valid live lease is untouchable until its TTL expires")
            holder_pid = int(row["holder_process_id"])
            if self._process_probe(holder_pid):
                raise LeaseConflictError("expired lease holder process is still live; force-close refused")
            if candidate.instance_id == row["holder_instance_id"]:
                raise LeaseConflictError("force-close candidate must be a distinct runtime instance")
            if not self._process_probe(candidate.process_id):
                raise LeaseConflictError("force-close candidate process is not live; proof refused")
            heartbeat_at = parse_timestamp(str(row["heartbeat_at"]))
            proof = ForceCloseProof(
                stream_id=stream_id,
                session_id=session_id,
                lease_id=str(row["lease_id"]),
                holder_instance_id=str(row["holder_instance_id"]),
                holder_process_id=holder_pid,
                heartbeat_at=str(row["heartbeat_at"]),
                expires_at=str(row["expires_at"]),
                observed_at=timestamp,
                heartbeat_age_seconds=max(0, int((current_time - heartbeat_at).total_seconds())),
                process_probe="os.kill(pid, 0): ProcessLookupError",
                candidate_agent=candidate.agent,
                candidate_harness=candidate.harness,
                candidate_instance_id=candidate.instance_id,
            )
            proof_payload = proof.as_dict()
            self._insert_lease_event_from_row(
                connection,
                row=row,
                event_type="stale_observed",
                timestamp=timestamp,
                proof=proof_payload,
                reason="expired heartbeat and absent exact holder process observed",
            )
            force_event_id = self._insert_lease_event_from_row(
                connection,
                row=row,
                event_type="force_closed",
                timestamp=timestamp,
                proof=proof_payload,
                reason=reason,
            )
            connection.execute(
                "UPDATE stream_leases SET state = 'released', version = version + 1, last_event_id = ? "
                "WHERE stream_id = ? AND session_id = ?",
                (force_event_id, stream_id, session_id),
            )
            connection.execute(
                "INSERT INTO session_events("
                "stream_id, session_id, from_state, to_state, ts, agent, harness, reason, proof_json"
                ") VALUES (?, ?, ?, 'closed', ?, ?, ?, ?, ?)",
                (
                    stream_id,
                    session_id,
                    session["state"],
                    timestamp,
                    candidate.agent,
                    candidate.harness,
                    reason,
                    canonical_json(proof_payload),
                ),
            )
            connection.execute(
                "UPDATE sessions SET state = 'closed', closed_at = ?, updated_at = ?, "
                "state_version = state_version + 1 WHERE stream_id = ? AND session_id = ?",
                (timestamp, timestamp, stream_id, session_id),
            )
        return proof

    def append_entry(
        self,
        lease: Lease,
        *,
        entry_type: EntryType,
        body: str,
        idempotency_key: str,
        refs: Sequence[EntryRef] = (),
        now: datetime | None = None,
    ) -> Entry:
        """Append one typed entry under an exact, unexpired fenced lease."""
        validate_entry_body(body)
        if not isinstance(entry_type, EntryType):
            entry_type = EntryType(entry_type)
        self._validate_idempotency_key(idempotency_key)
        ref_tuple = tuple(refs)
        for ref in ref_tuple:
            ref.validate()
        current_time = now or utc_now()
        timestamp = isoformat_z(current_time)
        body_sha256 = sha256_text(body)
        with self._transaction(now=current_time) as connection:
            existing = connection.execute(
                "SELECT * FROM entries WHERE stream_id = ? AND idempotency_key = ?",
                (lease.stream_id, idempotency_key),
            ).fetchone()
            if existing is not None:
                entry = self._entry_from_row(connection, existing)
                if (
                    entry.session_id != lease.session_id
                    or entry.type != entry_type
                    or entry.body_sha256 != body_sha256
                    or entry.refs != ref_tuple
                ):
                    raise LeaseConflictError("idempotency key already binds different immutable content")
                return entry
            self._require_current_lease(connection, lease, require_valid_at=current_time)
            cursor = connection.execute(
                "INSERT INTO entries("
                "stream_id, session_id, agent, harness, ts, type, body, body_sha256, origin, "
                "writer_lease_id, writer_instance_id, fencing_token, idempotency_key"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'live', ?, ?, ?, ?)",
                (
                    lease.stream_id,
                    lease.session_id,
                    lease.holder.agent,
                    lease.holder.harness,
                    timestamp,
                    entry_type.value,
                    body,
                    body_sha256,
                    lease.lease_id,
                    lease.holder.instance_id,
                    lease.fencing_token,
                    idempotency_key,
                ),
            )
            entry_id = int(cursor.lastrowid)
            for ordinal, ref in enumerate(ref_tuple):
                connection.execute(
                    "INSERT INTO entry_refs(entry_id, ordinal, kind, target_entry_id, uri) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (entry_id, ordinal, ref.kind, ref.target_entry_id, ref.uri),
                )
            row = connection.execute("SELECT * FROM entries WHERE entry_id = ?", (entry_id,)).fetchone()
            if row is None:
                raise SessionStreamError("entry insert did not produce a readable row")
            return self._entry_from_row(connection, row)

    def load_digest(self, stream_id: str, *, limit: int) -> StreamDigest:
        """Load all pinned entries first, then the last N non-pinned entries."""
        stream_id = validate_stream_id(stream_id)
        if limit < 0 or limit > 10_000:
            raise ValueError("limit must be between 0 and 10000")
        with self._read_snapshot() as connection:
            if connection.execute("SELECT 1 FROM streams WHERE stream_id = ?", (stream_id,)).fetchone() is None:
                raise NotFoundError(f"stream not found: {stream_id}")
            pinned_values = tuple(entry_type.value for entry_type in PINNED_ENTRY_TYPES)
            placeholders = ",".join("?" for _ in pinned_values)
            pinned_rows = connection.execute(
                f"SELECT * FROM entries WHERE stream_id = ? AND type IN ({placeholders}) ORDER BY entry_id",
                (stream_id, *pinned_values),
            ).fetchall()
            recent_rows = connection.execute(
                f"SELECT * FROM entries WHERE stream_id = ? AND type NOT IN ({placeholders}) "
                "ORDER BY entry_id DESC LIMIT ?",
                (stream_id, *pinned_values, limit),
            ).fetchall()
            recent_rows = list(reversed(recent_rows))
            high_water = int(
                connection.execute(
                    "SELECT COALESCE(MAX(entry_id), 0) FROM entries WHERE stream_id = ?",
                    (stream_id,),
                ).fetchone()[0]
            )
            return StreamDigest(
                stream_id=stream_id,
                limit=limit,
                pinned=tuple(self._entry_from_row(connection, row) for row in pinned_rows),
                recent=tuple(self._entry_from_row(connection, row) for row in recent_rows),
                high_water_entry_id=high_water,
            )

    def dump_stream(self, stream_id: str) -> dict[str, Any]:
        """Return complete ordered stream history for the operator dump surface."""
        stream_id = validate_stream_id(stream_id)
        with self._read_snapshot() as connection:
            stream = connection.execute("SELECT * FROM streams WHERE stream_id = ?", (stream_id,)).fetchone()
            if stream is None:
                raise NotFoundError(f"stream not found: {stream_id}")
            entry_rows = connection.execute(
                "SELECT * FROM entries WHERE stream_id = ? ORDER BY entry_id",
                (stream_id,),
            ).fetchall()
            return {
                "schema_migrations": self._rows_as_dicts(
                    connection.execute("SELECT * FROM schema_migrations ORDER BY version").fetchall()
                ),
                "stream": dict(stream),
                "sessions": self._rows_as_dicts(
                    connection.execute(
                        "SELECT * FROM sessions WHERE stream_id = ? ORDER BY opened_at, session_id",
                        (stream_id,),
                    ).fetchall()
                ),
                "session_events": self._rows_as_dicts(
                    connection.execute(
                        "SELECT * FROM session_events WHERE stream_id = ? ORDER BY event_id",
                        (stream_id,),
                    ).fetchall()
                ),
                "lease_events": self._rows_as_dicts(
                    connection.execute(
                        "SELECT * FROM lease_events WHERE stream_id = ? ORDER BY event_id",
                        (stream_id,),
                    ).fetchall()
                ),
                "lease": self._row_as_dict(
                    connection.execute("SELECT * FROM stream_leases WHERE stream_id = ?", (stream_id,)).fetchone()
                ),
                "entries": [entry_as_dict(self._entry_from_row(connection, row)) for row in entry_rows],
                "legacy_mirrors": self._rows_as_dicts(
                    connection.execute(
                        "SELECT * FROM legacy_mirrors WHERE stream_id = ? ORDER BY mirror_id",
                        (stream_id,),
                    ).fetchall()
                ),
                "stream_migration_state": self._row_as_dict(
                    connection.execute(
                        "SELECT * FROM stream_migration_state WHERE stream_id = ?",
                        (stream_id,),
                    ).fetchone()
                ),
                "stream_inventory_receipts": self._rows_as_dicts(
                    connection.execute(
                        "SELECT * FROM stream_inventory_receipts WHERE stream_id = ? "
                        "ORDER BY receipt_id",
                        (stream_id,),
                    ).fetchall()
                ),
                "legacy_import_receipts": self._rows_as_dicts(
                    connection.execute(
                        "SELECT * FROM legacy_import_receipts WHERE stream_id = ? "
                        "ORDER BY import_id",
                        (stream_id,),
                    ).fetchall()
                ),
                "legacy_projection_receipts": self._rows_as_dicts(
                    connection.execute(
                        "SELECT * FROM legacy_projection_receipts WHERE stream_id = ? "
                        "ORDER BY projection_id",
                        (stream_id,),
                    ).fetchall()
                ),
                "stream_control_events": self._rows_as_dicts(
                    connection.execute(
                        "SELECT * FROM stream_control_events WHERE stream_id = ? "
                        "ORDER BY event_id",
                        (stream_id,),
                    ).fetchall()
                ),
            }

    def record_legacy_mirror(
        self,
        lease: Lease,
        *,
        profile: str,
        source_path: str,
        source_sha256: str,
        source_bytes: int,
        entry: Entry,
        now: datetime | None = None,
    ) -> int:
        """Append an idempotent receipt after a legacy file was mirrored into an entry."""
        self._validate_identity("profile", profile)
        if not source_path or "\x00" in source_path:
            raise ValueError("source_path must be non-empty text without NUL")
        if len(source_sha256) != 64:
            raise ValueError("source_sha256 must be a SHA-256 hex digest")
        if source_bytes <= 0:
            raise ValueError("source_bytes must be positive")
        timestamp = isoformat_z(now or utc_now())
        with self._transaction(now=now) as connection:
            self._require_current_lease(
                connection,
                lease,
                require_valid_at=parse_timestamp(timestamp),
            )
            if entry.stream_id != lease.stream_id or entry.session_id != lease.session_id:
                raise LeaseConflictError("legacy mirror entry must belong to the exact current leased session")
            connection.execute(
                "INSERT OR IGNORE INTO legacy_mirrors("
                "profile, source_path, source_sha256, source_bytes, stream_id, session_id, entry_id, mirrored_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    profile,
                    source_path,
                    source_sha256,
                    source_bytes,
                    entry.stream_id,
                    entry.session_id,
                    entry.entry_id,
                    timestamp,
                ),
            )
            row = connection.execute(
                "SELECT mirror_id, entry_id FROM legacy_mirrors "
                "WHERE profile = ? AND source_path = ? AND source_sha256 = ?",
                (profile, source_path, source_sha256),
            ).fetchone()
            if row is None or int(row["entry_id"]) != entry.entry_id:
                raise SessionStreamError("legacy mirror identity already binds a different entry")
            return int(row["mirror_id"])

    def session_state(self, stream_id: str, session_id: str) -> SessionState:
        """Read the exact current state without inferring a session by recency."""
        stream_id = validate_stream_id(stream_id)
        with self._read_snapshot() as connection:
            row = self._session_row(connection, stream_id, session_id)
            return SessionState(str(row["state"]))

    def audit(self) -> dict[str, Any]:
        with self._read_snapshot() as connection:
            integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
            foreign_key_rows = connection.execute("PRAGMA foreign_key_check").fetchall()
            return {
                "integrity_check": integrity,
                "foreign_key_violations": self._rows_as_dicts(foreign_key_rows),
                "schema_versions": [
                    int(row[0])
                    for row in connection.execute(
                        "SELECT version FROM schema_migrations ORDER BY version"
                    ).fetchall()
                ],
            }

    @staticmethod
    def _ensure_stream(connection: sqlite3.Connection, *, stream_id: str, created_at: str) -> None:
        if stream_id.startswith("epic:"):
            kind = "epic"
            epic_number: int | None = int(stream_id.removeprefix("epic:"))
        else:
            kind = "shared"
            epic_number = None
        connection.execute(
            "INSERT OR IGNORE INTO streams(stream_id, kind, epic_number, created_at) VALUES (?, ?, ?, ?)",
            (stream_id, kind, epic_number, created_at),
        )
        row = connection.execute(
            "SELECT kind, epic_number FROM streams WHERE stream_id = ?",
            (stream_id,),
        ).fetchone()
        if row is None or row["kind"] != kind or row["epic_number"] != epic_number:
            raise LifecycleError(f"stream identity conflict for {stream_id}")

    @staticmethod
    def _validate_ttl(ttl_seconds: int) -> None:
        if not isinstance(ttl_seconds, int) or not 0 < ttl_seconds <= MAX_TTL_SECONDS:
            raise ValueError(f"ttl_seconds must be an integer between 1 and {MAX_TTL_SECONDS}")

    @staticmethod
    def _validate_identity(label: str, value: str) -> None:
        if not value or len(value) > 256 or "\x00" in value or any(char.isspace() for char in value):
            raise ValueError(f"{label} must be non-empty path-safe text up to 256 characters")

    @staticmethod
    def _validate_idempotency_key(value: str) -> None:
        if not value or len(value) > 512 or "\x00" in value:
            raise ValueError("idempotency_key must be non-empty text up to 512 characters without NUL")

    @staticmethod
    def _session_row(connection: sqlite3.Connection, stream_id: str, session_id: str) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM sessions WHERE stream_id = ? AND session_id = ?",
            (stream_id, session_id),
        ).fetchone()
        if row is None:
            raise NotFoundError(f"session not found: {stream_id}/{session_id}")
        return row

    @staticmethod
    def _require_current_lease(
        connection: sqlite3.Connection,
        lease: Lease,
        *,
        require_valid_at: datetime | None = None,
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT lease.*, session.state AS session_state FROM stream_leases AS lease "
            "JOIN sessions AS session ON session.stream_id = lease.stream_id "
            "AND session.session_id = lease.session_id WHERE lease.stream_id = ?",
            (lease.stream_id,),
        ).fetchone()
        if row is None:
            raise NotFoundError(f"lease not found for stream {lease.stream_id}")
        matches = (
            row["session_id"] == lease.session_id
            and row["lease_id"] == lease.lease_id
            and int(row["generation"]) == lease.generation
            and int(row["fencing_token"]) == lease.fencing_token
            and row["holder_agent"] == lease.holder.agent
            and row["holder_harness"] == lease.holder.harness
            and row["holder_instance_id"] == lease.holder.instance_id
            and row["holder_task_id"] == lease.holder.task_id
            and int(row["holder_process_id"]) == lease.holder.process_id
        )
        if not matches or row["state"] != "active" or row["session_state"] == SessionState.CLOSED.value:
            raise LeaseConflictError("supplied lease is not the exact current active fenced lease")
        if require_valid_at is not None and require_valid_at >= parse_timestamp(str(row["expires_at"])):
            raise LeaseConflictError("lease TTL has expired; live append/state mutation refused")
        return row

    @staticmethod
    def _insert_lease_event(
        connection: sqlite3.Connection,
        *,
        stream_id: str,
        session_id: str,
        lease_id: str,
        generation: int,
        fencing_token: int,
        event_type: str,
        holder: LeaseHolder,
        ttl_seconds: int,
        timestamp: str,
        proof: dict[str, Any],
        reason: str,
    ) -> int:
        cursor = connection.execute(
            "INSERT INTO lease_events("
            "stream_id, session_id, lease_id, generation, fencing_token, event_type, "
            "holder_agent, holder_harness, holder_instance_id, holder_task_id, holder_process_id, "
            "ttl_seconds, ts, proof_json, reason"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                stream_id,
                session_id,
                lease_id,
                generation,
                fencing_token,
                event_type,
                holder.agent,
                holder.harness,
                holder.instance_id,
                holder.task_id,
                holder.process_id,
                ttl_seconds,
                timestamp,
                canonical_json(proof),
                reason,
            ),
        )
        return int(cursor.lastrowid)

    def _insert_lease_event_from_row(
        self,
        connection: sqlite3.Connection,
        *,
        row: sqlite3.Row,
        event_type: str,
        timestamp: str,
        proof: dict[str, Any],
        reason: str,
    ) -> int:
        holder = LeaseHolder(
            agent=str(row["holder_agent"]),
            harness=str(row["holder_harness"]),
            instance_id=str(row["holder_instance_id"]),
            task_id=str(row["holder_task_id"]) if row["holder_task_id"] is not None else None,
            process_id=int(row["holder_process_id"]),
        )
        return self._insert_lease_event(
            connection,
            stream_id=str(row["stream_id"]),
            session_id=str(row["session_id"]),
            lease_id=str(row["lease_id"]),
            generation=int(row["generation"]),
            fencing_token=int(row["fencing_token"]),
            event_type=event_type,
            holder=holder,
            ttl_seconds=int(row["ttl_seconds"]),
            timestamp=timestamp,
            proof=proof,
            reason=reason,
        )

    @staticmethod
    def _entry_from_row(connection: sqlite3.Connection, row: sqlite3.Row) -> Entry:
        refs = tuple(
            EntryRef(
                kind=str(ref["kind"]),
                target_entry_id=int(ref["target_entry_id"]) if ref["target_entry_id"] is not None else None,
                uri=str(ref["uri"]) if ref["uri"] is not None else None,
            )
            for ref in connection.execute(
                "SELECT kind, target_entry_id, uri FROM entry_refs WHERE entry_id = ? ORDER BY ordinal",
                (row["entry_id"],),
            ).fetchall()
        )
        return Entry(
            entry_id=int(row["entry_id"]),
            stream_id=str(row["stream_id"]),
            session_id=str(row["session_id"]),
            agent=str(row["agent"]),
            harness=str(row["harness"]),
            ts=str(row["ts"]),
            type=EntryType(str(row["type"])),
            body=str(row["body"]),
            body_sha256=str(row["body_sha256"]),
            idempotency_key=str(row["idempotency_key"]),
            refs=refs,
        )

    @staticmethod
    def _rows_as_dicts(rows: Sequence[sqlite3.Row]) -> list[dict[str, Any]]:
        return [dict(row) for row in rows]

    @staticmethod
    def _row_as_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None
