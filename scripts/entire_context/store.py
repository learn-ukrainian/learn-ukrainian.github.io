"""Caller-owned, rebuildable SQLite projection for body-free context links.

The projection keeps an append-only ``link_events`` log (claimed / promoted /
tombstoned) plus a derived ``context_links`` table that search and hydration
may read. Duplicate admission is a no-op, tombstones are terminal, and a full
rebuild replays the event log into an identical logical projection.

This store is non-load-bearing by design: it never calls Entire, GitHub,
Fleet, ACP, Monitor, or the network, and it never writes outside its own
caller-supplied database file.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any

from .model import (
    LOCATOR_ID_RE,
    SCHEMA_VERSION,
    ContextLink,
    LinkKind,
    SchemaError,
    VerificationEvidence,
    VerificationStatus,
    canonical_json,
    isoformat_z,
    parse_timestamp,
    utc_now,
    validate_identity,
)

DEFAULT_VERIFICATION_MAX_AGE_SECONDS = 3600
MAX_CLOCK_SKEW_SECONDS = 300
MAX_RELATED_SCAN_ROWS = 500

_DDL = """
CREATE TABLE IF NOT EXISTS link_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    locator_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('claimed', 'promoted', 'tombstoned')),
    payload_json TEXT NOT NULL DEFAULT '{}',
    reason TEXT NOT NULL DEFAULT '',
    actor TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_link_events_locator ON link_events(locator_id, event_id);
CREATE TABLE IF NOT EXISTS context_links (
    locator_id TEXT PRIMARY KEY,
    state TEXT NOT NULL CHECK (state IN ('pending', 'promoted', 'tombstoned')),
    schema_version INTEGER NOT NULL,
    kind TEXT NOT NULL,
    canonical_namespace TEXT NOT NULL,
    canonical_id TEXT NOT NULL,
    canonical_digest TEXT NOT NULL,
    entire_checkpoint_id TEXT,
    git_sha TEXT,
    facets_json TEXT NOT NULL DEFAULT '{}',
    ingested_at TEXT NOT NULL,
    promoted_at TEXT,
    tombstone_reason TEXT
);
CREATE TABLE IF NOT EXISTS use_receipts (
    receipt_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    consumer TEXT NOT NULL,
    purpose TEXT NOT NULL,
    locator_ids_json TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_use_receipts_recorded_at
    ON use_receipts(recorded_at, receipt_id);
CREATE TABLE IF NOT EXISTS projection_sync_state (
    source_kind TEXT PRIMARY KEY,
    attempts INTEGER NOT NULL DEFAULT 0,
    failures INTEGER NOT NULL DEFAULT 0,
    retries INTEGER NOT NULL DEFAULT 0,
    last_outcome TEXT NOT NULL DEFAULT '',
    last_attempt_at TEXT,
    last_success_at TEXT,
    last_failure_at TEXT,
    last_failure_reason TEXT,
    last_reconciliation_at TEXT,
    source_latest_at TEXT,
    lag_seconds INTEGER,
    last_examined INTEGER NOT NULL DEFAULT 0,
    last_changed INTEGER NOT NULL DEFAULT 0,
    last_skipped INTEGER NOT NULL DEFAULT 0,
    last_truncated INTEGER NOT NULL DEFAULT 0,
    last_limit INTEGER NOT NULL DEFAULT 0,
    dangling INTEGER NOT NULL DEFAULT 0
);
"""


class AdmitOutcome(StrEnum):
    PROMOTED = "promoted"
    ALREADY_PROMOTED = "already_promoted"
    REFUSED = "refused"
    ALREADY_TOMBSTONED = "already_tombstoned"


@dataclass(frozen=True, slots=True)
class AdmitResult:
    locator_id: str
    outcome: AdmitOutcome
    reason: str
    state: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "locator_id": self.locator_id,
            "outcome": self.outcome.value,
            "reason": self.reason,
            "state": self.state,
        }


@dataclass(frozen=True, slots=True)
class RelatedScan:
    """Bounded typed-join scan with explicit completeness metadata."""

    items: tuple[tuple[dict[str, Any], str], ...]
    examined: int
    truncated: bool


class ContextLinkStore:
    """High-level admission / lookup / rebuild API over one SQLite file."""

    def __init__(
        self,
        db_path: Path | str,
        *,
        verification_max_age_seconds: int = DEFAULT_VERIFICATION_MAX_AGE_SECONDS,
    ) -> None:
        self.db_path = Path(db_path)
        self.verification_max_age_seconds = verification_max_age_seconds

    @contextmanager
    def _connect(self, *, write: bool):
        if write:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.db_path)
        else:
            connection = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            if write:
                connection.executescript(_DDL)
            yield connection
        finally:
            connection.close()

    @contextmanager
    def _transaction(self):
        with self._connect(write=True) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                yield connection
                connection.execute("COMMIT")
            except Exception:
                with suppress(sqlite3.Error):
                    connection.execute("ROLLBACK")
                raise

    # ── admission ────────────────────────────────────────────────────────────

    def submit_claim(
        self,
        link: ContextLink,
        *,
        actor: str = "unknown",
        now: datetime | None = None,
    ) -> str:
        """Record one pending claim. Idempotent for the same locator ID."""
        link.validate()
        validate_identity(actor, field_name="actor")
        timestamp = isoformat_z(now or utc_now())
        locator_id = link.locator_id
        with self._transaction() as connection:
            state = self._current_state(connection, locator_id)
            if state is None:
                self._insert_claim(connection, link, actor=actor, timestamp=timestamp)
            elif not self._payload_matches(connection, link):
                raise SchemaError("locator_id is already bound to a different claim payload")
        return locator_id

    @staticmethod
    def _current_state(connection: sqlite3.Connection, locator_id: str) -> str | None:
        row = connection.execute("SELECT state FROM context_links WHERE locator_id = ?", (locator_id,)).fetchone()
        return None if row is None else str(row["state"])

    @staticmethod
    def _payload_matches(connection: sqlite3.Connection, link: ContextLink) -> bool:
        row = connection.execute(
            "SELECT schema_version, locator_id, kind, canonical_namespace, canonical_id,"
            " canonical_digest, entire_checkpoint_id, git_sha, facets_json"
            " FROM context_links WHERE locator_id = ?",
            (link.locator_id,),
        ).fetchone()
        if row is None:
            return False
        stored = {
            "schema_version": int(row["schema_version"]),
            "locator_id": str(row["locator_id"]),
            "kind": str(row["kind"]),
            "canonical_namespace": str(row["canonical_namespace"]),
            "canonical_id": str(row["canonical_id"]),
            "canonical_digest": str(row["canonical_digest"]),
            "entire_checkpoint_id": row["entire_checkpoint_id"],
            "git_sha": row["git_sha"],
            "facets": json.loads(row["facets_json"]),
        }
        return canonical_json(stored) == canonical_json(link.to_dict())

    @staticmethod
    def _insert_claim(
        connection: sqlite3.Connection,
        link: ContextLink,
        *,
        actor: str,
        timestamp: str,
    ) -> None:
        payload = link.to_dict()
        connection.execute(
            "INSERT INTO link_events(locator_id, event_type, payload_json, reason, actor, recorded_at)"
            " VALUES (?, 'claimed', ?, '', ?, ?)",
            (link.locator_id, canonical_json(payload), actor, timestamp),
        )
        connection.execute(
            "INSERT INTO context_links("
            "locator_id, state, schema_version, kind, canonical_namespace, canonical_id,"
            " canonical_digest, entire_checkpoint_id, git_sha, facets_json, ingested_at,"
            " promoted_at, tombstone_reason"
            ") VALUES (?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)",
            (
                link.locator_id,
                payload["schema_version"],
                payload["kind"],
                payload["canonical_namespace"],
                payload["canonical_id"],
                payload["canonical_digest"],
                payload["entire_checkpoint_id"],
                payload["git_sha"],
                canonical_json(payload["facets"]),
                timestamp,
            ),
        )

    def admit(
        self,
        link: ContextLink,
        verification: VerificationEvidence | None,
        *,
        actor: str = "unknown",
        now: datetime | None = None,
    ) -> AdmitResult:
        """Admit one claim. Idempotent; unverifiable claims are tombstoned."""
        link.validate()
        validate_identity(actor, field_name="actor")
        if verification is not None:
            verification.validate()
        moment = now or utc_now()
        timestamp = isoformat_z(moment)
        locator_id = link.locator_id

        with self._transaction() as connection:
            state = self._current_state(connection, locator_id)
            if state == "tombstoned":
                return AdmitResult(locator_id, AdmitOutcome.ALREADY_TOMBSTONED, "tombstone_terminal", state)
            if state is not None and not self._payload_matches(connection, link):
                if state == "pending":
                    connection.execute(
                        "INSERT INTO link_events(locator_id, event_type, payload_json, reason, actor, recorded_at)"
                        " VALUES (?, 'tombstoned', '{}', 'claim_payload_conflict', ?, ?)",
                        (locator_id, actor, timestamp),
                    )
                    connection.execute(
                        "UPDATE context_links SET state = 'tombstoned',"
                        " tombstone_reason = 'claim_payload_conflict' WHERE locator_id = ?",
                        (locator_id,),
                    )
                    return AdmitResult(
                        locator_id,
                        AdmitOutcome.REFUSED,
                        "claim_payload_conflict",
                        "tombstoned",
                    )
                return AdmitResult(
                    locator_id,
                    AdmitOutcome.REFUSED,
                    "claim_payload_conflict",
                    state,
                )
            if state == "promoted":
                return AdmitResult(locator_id, AdmitOutcome.ALREADY_PROMOTED, "duplicate", state)
            if state is None:
                self._insert_claim(connection, link, actor=actor, timestamp=timestamp)
            # state == "pending": replayed admission of an unresolved claim;
            # fall through and evaluate the (new) verification evidence.

            refusal = self._refusal_reason(link, verification, moment)
            if refusal is None:
                connection.execute(
                    "INSERT INTO link_events(locator_id, event_type, payload_json, reason, actor, recorded_at)"
                    " VALUES (?, 'promoted', '{}', '', ?, ?)",
                    (locator_id, actor, timestamp),
                )
                connection.execute(
                    "UPDATE context_links SET state = 'promoted', promoted_at = ? WHERE locator_id = ?",
                    (timestamp, locator_id),
                )
                return AdmitResult(locator_id, AdmitOutcome.PROMOTED, "", "promoted")

            connection.execute(
                "INSERT INTO link_events(locator_id, event_type, payload_json, reason, actor, recorded_at)"
                " VALUES (?, 'tombstoned', '{}', ?, ?, ?)",
                (locator_id, refusal, actor, timestamp),
            )
            connection.execute(
                "UPDATE context_links SET state = 'tombstoned', tombstone_reason = ? WHERE locator_id = ?",
                (refusal, locator_id),
            )
            return AdmitResult(locator_id, AdmitOutcome.REFUSED, refusal, "tombstoned")

    def _refusal_reason(
        self,
        link: ContextLink,
        verification: VerificationEvidence | None,
        moment: datetime,
    ) -> str | None:
        """Return a body-free machine reason, or None when admission is safe."""
        if verification is None:
            return "verification_missing"
        if verification.status is not VerificationStatus.VERIFIED:
            return f"verification_{verification.status.value}"
        if verification.canonical_digest != link.canonical_digest:
            return "digest_mismatch"
        checked_at = parse_timestamp(verification.checked_at)
        age = (moment - checked_at).total_seconds()
        if age > self.verification_max_age_seconds or age < -MAX_CLOCK_SKEW_SECONDS:
            return "verification_stale"
        return None

    def tombstone(
        self,
        locator_id: str,
        *,
        reason: str,
        actor: str,
        now: datetime | None = None,
    ) -> bool:
        """Converge one projected locator to a terminal body-free tombstone.

        Returns ``True`` only when this call applied the transition. Missing
        and already-tombstoned locators are idempotent no-ops.
        """
        if LOCATOR_ID_RE.fullmatch(locator_id) is None:
            raise SchemaError("locator_id is invalid")
        validate_identity(reason, field_name="reason")
        validate_identity(actor, field_name="actor")
        timestamp = isoformat_z(now or utc_now())
        with self._transaction() as connection:
            state = self._current_state(connection, locator_id)
            if state is None or state == "tombstoned":
                return False
            connection.execute(
                "INSERT INTO link_events(locator_id, event_type, payload_json, reason, actor, recorded_at)"
                " VALUES (?, 'tombstoned', '{}', ?, ?, ?)",
                (locator_id, reason, actor, timestamp),
            )
            connection.execute(
                "UPDATE context_links SET state = 'tombstoned', tombstone_reason = ?"
                " WHERE locator_id = ?",
                (reason, locator_id),
            )
        return True

    # ── reads ────────────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_link_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "schema_version": int(row["schema_version"]),
            "locator_id": str(row["locator_id"]),
            "kind": str(row["kind"]),
            "canonical_namespace": str(row["canonical_namespace"]),
            "canonical_id": str(row["canonical_id"]),
            "canonical_digest": str(row["canonical_digest"]),
            "entire_checkpoint_id": row["entire_checkpoint_id"],
            "git_sha": row["git_sha"],
            "facets": json.loads(row["facets_json"]),
            "ingested_at": str(row["ingested_at"]),
            "promoted_at": row["promoted_at"],
        }

    def lookup(self, locator_id: str) -> dict[str, Any] | None:
        """Return a promoted link for a known locator ID, else None.

        Pending and tombstoned claims are never searchable/hydratable.
        """
        if not LOCATOR_ID_RE.fullmatch(locator_id):
            return None
        with self._connect(write=False) as connection:
            row = connection.execute(
                "SELECT * FROM context_links WHERE locator_id = ? AND state = 'promoted'",
                (locator_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_link_dict(row)

    def explain(self, locator_id: str) -> dict[str, Any] | None:
        """Return the body-free lifecycle audit trail for a known locator ID."""
        if not LOCATOR_ID_RE.fullmatch(locator_id):
            return None
        with self._connect(write=False) as connection:
            link_row = connection.execute("SELECT * FROM context_links WHERE locator_id = ?", (locator_id,)).fetchone()
            if link_row is None:
                return None
            events = connection.execute(
                "SELECT event_id, event_type, reason, actor, recorded_at FROM link_events"
                " WHERE locator_id = ? ORDER BY event_id",
                (locator_id,),
            ).fetchall()
        return {
            "locator_id": locator_id,
            "state": str(link_row["state"]),
            "tombstone_reason": link_row["tombstone_reason"],
            "link": self._row_to_link_dict(link_row),
            "events": [
                {
                    "event_id": int(event["event_id"]),
                    "event_type": str(event["event_type"]),
                    "reason": str(event["reason"]),
                    "actor": str(event["actor"]),
                    "recorded_at": str(event["recorded_at"]),
                }
                for event in events
            ],
        }

    def status(self) -> dict[str, Any]:
        """Body-free aggregate status of the projection."""
        with self._connect(write=False) as connection:
            counts = connection.execute(
                "SELECT state, COUNT(*) AS n FROM context_links GROUP BY state ORDER BY state"
            ).fetchall()
            events = connection.execute("SELECT COUNT(*) AS n, MAX(recorded_at) AS last_at FROM link_events").fetchone()
            uses = connection.execute(
                "SELECT COUNT(*) AS n, MAX(recorded_at) AS last_at FROM use_receipts"
            ).fetchone()
            use_consumers = connection.execute(
                "SELECT consumer, COUNT(*) AS n FROM use_receipts"
                " GROUP BY consumer ORDER BY consumer"
            ).fetchall()
            tombstone_reasons = connection.execute(
                "SELECT tombstone_reason, COUNT(*) AS n FROM context_links"
                " WHERE state = 'tombstoned' GROUP BY tombstone_reason"
                " ORDER BY tombstone_reason"
            ).fetchall()
            sync_table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table'"
                " AND name = 'projection_sync_state'"
            ).fetchone()
            acp_sync = None
            if sync_table is not None:
                acp_sync = connection.execute(
                    "SELECT * FROM projection_sync_state WHERE source_kind = ?",
                    (LinkKind.ACP_CONVERSATION.value,),
                ).fetchone()
        count_map = {str(row["state"]): int(row["n"]) for row in counts}
        acp_health = {
            "attempts": 0,
            "failures": 0,
            "retries": 0,
            "last_attempt_at": None,
            "last_success_at": None,
            "last_failure_at": None,
            "last_failure_reason": None,
            "last_reconciliation_at": None,
            "source_latest_at": None,
            "lag_seconds": None,
            "last_reconciliation": {
                "examined": 0,
                "changed": 0,
                "skipped": 0,
                "truncated": False,
                "limit": 0,
            },
        }
        dangling = 0
        if acp_sync is not None:
            dangling = int(acp_sync["dangling"])
            acp_health = {
                "attempts": int(acp_sync["attempts"]),
                "failures": int(acp_sync["failures"]),
                "retries": int(acp_sync["retries"]),
                "last_attempt_at": acp_sync["last_attempt_at"],
                "last_success_at": acp_sync["last_success_at"],
                "last_failure_at": acp_sync["last_failure_at"],
                "last_failure_reason": acp_sync["last_failure_reason"],
                "last_reconciliation_at": acp_sync["last_reconciliation_at"],
                "source_latest_at": acp_sync["source_latest_at"],
                "lag_seconds": acp_sync["lag_seconds"],
                "last_reconciliation": {
                    "examined": int(acp_sync["last_examined"]),
                    "changed": int(acp_sync["last_changed"]),
                    "skipped": int(acp_sync["last_skipped"]),
                    "truncated": bool(acp_sync["last_truncated"]),
                    "limit": int(acp_sync["last_limit"]),
                },
            }
        return {
            "schema_version": SCHEMA_VERSION,
            "counts": count_map,
            "events": int(events["n"]) if events else 0,
            "last_event_at": events["last_at"] if events else None,
            "use_receipts": int(uses["n"]) if uses else 0,
            "last_use_at": uses["last_at"] if uses else None,
            "uses_by_consumer": {
                str(row["consumer"]): int(row["n"]) for row in use_consumers
            },
            "projection_health": {
                "pending": count_map.get("pending", 0),
                "tombstoned": count_map.get("tombstoned", 0),
                "dangling": dangling,
                "tombstones_by_reason": {
                    str(row["tombstone_reason"]): int(row["n"])
                    for row in tombstone_reasons
                    if row["tombstone_reason"]
                },
                "acp": acp_health,
            },
        }

    def promoted_for_kind(
        self,
        kind: LinkKind,
        *,
        limit: int,
        attempt: int = 0,
    ) -> tuple[list[dict[str, Any]], bool]:
        """Return a bounded deterministic page that rotates across retries."""
        if not isinstance(kind, LinkKind):
            raise SchemaError("kind must be an allowlisted LinkKind")
        capped = max(0, min(int(limit), MAX_RELATED_SCAN_ROWS))
        with self._connect(write=False) as connection:
            total = int(
                connection.execute(
                    "SELECT COUNT(*) FROM context_links WHERE state = 'promoted' AND kind = ?",
                    (kind.value,),
                ).fetchone()[0]
            )
            rows: list[sqlite3.Row] = []
            if capped and total:
                offset = (max(0, int(attempt)) * capped) % total
                rows = connection.execute(
                    "SELECT * FROM context_links WHERE state = 'promoted' AND kind = ?"
                    " ORDER BY canonical_id, locator_id LIMIT ? OFFSET ?",
                    (kind.value, capped, offset),
                ).fetchall()
                if len(rows) < min(capped, total):
                    rows.extend(
                        connection.execute(
                            "SELECT * FROM context_links WHERE state = 'promoted' AND kind = ?"
                            " ORDER BY canonical_id, locator_id LIMIT ?",
                            (kind.value, min(capped, total) - len(rows)),
                        ).fetchall()
                    )
        return [self._row_to_link_dict(row) for row in rows], total > capped

    def promoted_for_canonical(
        self,
        kind: LinkKind,
        canonical_id: str,
        *,
        limit: int = MAX_RELATED_SCAN_ROWS,
    ) -> tuple[list[dict[str, Any]], bool]:
        """Return bounded promoted locators for one exact canonical identity."""
        if not isinstance(kind, LinkKind):
            raise SchemaError("kind must be an allowlisted LinkKind")
        capped = max(0, min(int(limit), MAX_RELATED_SCAN_ROWS))
        with self._connect(write=False) as connection:
            rows = connection.execute(
                "SELECT * FROM context_links WHERE state = 'promoted' AND kind = ?"
                " AND canonical_id = ? ORDER BY locator_id LIMIT ?",
                (kind.value, canonical_id, capped + 1),
            ).fetchall()
        return [self._row_to_link_dict(row) for row in rows[:capped]], len(rows) > capped

    def record_projection_sync(
        self,
        *,
        source_kind: LinkKind,
        operation: str,
        outcome: str,
        reason: str = "",
        source_latest_at: str | None = None,
        examined: int = 0,
        changed: int = 0,
        skipped: int = 0,
        truncated: bool = False,
        limit: int = 0,
        dangling: int = 0,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Persist bounded body-free sync health in this disposable projection."""
        if not isinstance(source_kind, LinkKind):
            raise SchemaError("source_kind must be an allowlisted LinkKind")
        if operation not in {"live", "reconcile"}:
            raise SchemaError("operation must be live or reconcile")
        if outcome not in {"succeeded", "failed"}:
            raise SchemaError("outcome must be succeeded or failed")
        if reason:
            validate_identity(reason, field_name="reason")
        values = (examined, changed, skipped, limit, dangling)
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values):
            raise SchemaError("projection sync counts must be non-negative integers")
        if limit > MAX_RELATED_SCAN_ROWS:
            raise SchemaError("projection sync limit exceeds the bounded maximum")
        timestamp = isoformat_z(now or utc_now())
        normalized_source_at = None
        lag_seconds = None
        if source_latest_at is not None:
            normalized_source_at = isoformat_z(parse_timestamp(source_latest_at))
            # This metric is projection backlog lag, not source age. A
            # successful non-truncated pass with no dangling records proves
            # catch-up; otherwise lag is unknown rather than misleading.
            lag_seconds = 0 if outcome == "succeeded" and not truncated and dangling == 0 else None
        with self._transaction() as connection:
            prior = connection.execute(
                "SELECT * FROM projection_sync_state WHERE source_kind = ?",
                (source_kind.value,),
            ).fetchone()
            attempts = (int(prior["attempts"]) if prior is not None else 0) + 1
            failures = (int(prior["failures"]) if prior is not None else 0) + (
                1 if outcome == "failed" else 0
            )
            retries = (int(prior["retries"]) if prior is not None else 0) + (
                1 if prior is not None and prior["last_outcome"] == "failed" else 0
            )
            last_success_at = (
                timestamp if outcome == "succeeded" else (prior["last_success_at"] if prior is not None else None)
            )
            last_failure_at = (
                timestamp if outcome == "failed" else (prior["last_failure_at"] if prior is not None else None)
            )
            last_failure_reason = (
                reason if outcome == "failed" else (prior["last_failure_reason"] if prior is not None else None)
            )
            reconciliation_at = (
                timestamp
                if operation == "reconcile"
                else (prior["last_reconciliation_at"] if prior is not None else None)
            )
            reconciliation_values = (
                (examined, changed, skipped, int(truncated), limit)
                if operation == "reconcile"
                else (
                    (
                        int(prior["last_examined"]),
                        int(prior["last_changed"]),
                        int(prior["last_skipped"]),
                        int(prior["last_truncated"]),
                        int(prior["last_limit"]),
                    )
                    if prior is not None
                    else (0, 0, 0, 0, 0)
                )
            )
            connection.execute(
                "INSERT OR REPLACE INTO projection_sync_state("
                "source_kind, attempts, failures, retries, last_outcome, last_attempt_at,"
                "last_success_at, last_failure_at, last_failure_reason, last_reconciliation_at,"
                "source_latest_at, lag_seconds, last_examined, last_changed, last_skipped,"
                "last_truncated, last_limit, dangling) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    source_kind.value,
                    attempts,
                    failures,
                    retries,
                    outcome,
                    timestamp,
                    last_success_at,
                    last_failure_at,
                    last_failure_reason,
                    reconciliation_at,
                    normalized_source_at
                    if normalized_source_at is not None
                    else (prior["source_latest_at"] if prior is not None else None),
                    lag_seconds
                    if source_latest_at is not None
                    else (prior["lag_seconds"] if prior is not None else None),
                    *reconciliation_values,
                    dangling,
                ),
            )
        return {
            "attempts": attempts,
            "failures": failures,
            "retries": retries,
            "last_attempt_at": timestamp,
        }

    def record_use(
        self,
        *,
        task_id: str,
        consumer: str,
        purpose: str,
        locator_ids: list[str] | tuple[str, ...],
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Record an explicit, body-free agent-use attestation.

        This is deliberately separate from search and handoff. A search result
        proves only delivery; a use receipt is written only when the caller
        explicitly attests that the verified locators informed its work.
        Replays of the same task/consumer/purpose/locator set are idempotent.
        """
        validate_identity(task_id, field_name="task_id")
        validate_identity(consumer, field_name="consumer")
        validate_identity(purpose, field_name="purpose")
        normalized = tuple(sorted(set(locator_ids)))
        if not normalized or len(normalized) > 10:
            raise SchemaError("locator_ids must contain between 1 and 10 unique locators")
        if any(LOCATOR_ID_RE.fullmatch(locator_id) is None for locator_id in normalized):
            raise SchemaError("locator_ids contains an invalid locator")
        material = {
            "schema": "entire-context-use.v1",
            "task_id": task_id,
            "consumer": consumer,
            "purpose": purpose,
            "locator_ids": list(normalized),
        }
        receipt_id = "ecuse_" + hashlib.sha256(
            canonical_json(material).encode("utf-8")
        ).hexdigest()
        timestamp = isoformat_z(now or utc_now())
        with self._transaction() as connection:
            rows = connection.execute(
                "SELECT locator_id FROM context_links"
                f" WHERE state = 'promoted' AND locator_id IN ({','.join('?' for _ in normalized)})",
                normalized,
            ).fetchall()
            promoted = {str(row["locator_id"]) for row in rows}
            if promoted != set(normalized):
                raise SchemaError("use receipt requires promoted locators")
            cursor = connection.execute(
                "INSERT OR IGNORE INTO use_receipts("
                "receipt_id, task_id, consumer, purpose, locator_ids_json, recorded_at"
                ") VALUES (?, ?, ?, ?, ?, ?)",
                (
                    receipt_id,
                    task_id,
                    consumer,
                    purpose,
                    canonical_json(list(normalized)),
                    timestamp,
                ),
            )
            stored = connection.execute(
                "SELECT recorded_at FROM use_receipts WHERE receipt_id = ?",
                (receipt_id,),
            ).fetchone()
        return {
            "schema": "entire-context-use.v1",
            "receipt_id": receipt_id,
            "created": cursor.rowcount == 1,
            "locator_count": len(normalized),
            "recorded_at": str(stored["recorded_at"]),
        }

    # ── recall candidate scan and provenance joins ─────────────────────────────

    def candidates(self, *, limit: int = 500) -> list[dict[str, Any]]:
        """Body-free promoted candidate scan for ranking (deterministic order).

        Pending and tombstoned claims are never candidates. The order is fully
        derived from the stored locator IDs so recall ranking is reproducible.
        """
        capped = max(0, min(int(limit), MAX_RELATED_SCAN_ROWS))
        with self._connect(write=False) as connection:
            rows = connection.execute(
                "SELECT * FROM context_links WHERE state = 'promoted' ORDER BY locator_id LIMIT ?",
                (capped,),
            ).fetchall()
        return [self._row_to_link_dict(row) for row in rows]

    def find_related(
        self,
        link: dict[str, Any],
        *,
        limit: int = 50,
    ) -> RelatedScan:
        """Body-free promoted provenance joins for explain-change traversal.

        Returns ``(candidate, join)`` pairs using explicit typed joins only:
        ``same_git_sha`` (commit-backed provenance), ``references_commit`` /
        ``referenced_by_commit`` (commit ↔ receipt cross-reference), and
        ``same_canonical_id`` (the same exact identifier in another kind).
        Namespace equality is deliberately not a join: it would connect every
        same-repository commit. The seed itself and any non-promoted claim are
        excluded. SQL prefilters for typed joins before applying ``limit``, so
        unrelated locator rows cannot hide a valid join. Order is deterministic
        and truncation is explicit.
        """
        capped = max(0, min(int(limit), MAX_RELATED_SCAN_ROWS))
        locator_id = str(link["locator_id"])
        seed_sha = link.get("git_sha")
        seed_id = link.get("canonical_id")
        predicates: list[str] = []
        predicate_values: list[str] = []
        if seed_sha:
            predicates.extend(("canonical_id = ?", "git_sha = ?"))
            predicate_values.extend((str(seed_sha), str(seed_sha)))
        if seed_id:
            predicates.extend(("git_sha = ?", "canonical_id = ?"))
            predicate_values.extend((str(seed_id), str(seed_id)))
        if not predicates:
            return RelatedScan(items=(), examined=0, truncated=False)
        # Fetch one sentinel beyond the caller-visible cap so truncation is
        # observable even when the requested limit is zero.
        with self._connect(write=False) as connection:
            rows = connection.execute(
                "SELECT * FROM context_links WHERE state = 'promoted'"
                f" AND locator_id != ? AND ({' OR '.join(predicates)})"
                " ORDER BY locator_id LIMIT ?",
                (locator_id, *predicate_values, capped + 1),
            ).fetchall()
        truncated = len(rows) > capped
        rows = rows[:capped]
        related: list[tuple[dict[str, Any], str]] = []
        for row in rows:
            candidate = self._row_to_link_dict(row)
            candidate_sha = candidate.get("git_sha")
            join: str | None = None
            if seed_sha and candidate.get("canonical_id") == seed_sha:
                join = "references_commit"
            elif candidate_sha and candidate_sha == seed_id:
                join = "referenced_by_commit"
            elif seed_sha and candidate_sha == seed_sha:
                join = "same_git_sha"
            elif seed_id and candidate.get("canonical_id") == seed_id:
                join = "same_canonical_id"
            if join is not None:
                related.append((candidate, join))
        return RelatedScan(items=tuple(related), examined=len(rows), truncated=truncated)

    # ── rebuild ──────────────────────────────────────────────────────────────

    def _projection_snapshot(self, connection: sqlite3.Connection) -> str:
        rows = connection.execute(
            "SELECT locator_id, state, schema_version, kind, canonical_namespace, canonical_id,"
            " canonical_digest, entire_checkpoint_id, git_sha, facets_json, ingested_at,"
            " promoted_at, tombstone_reason FROM context_links ORDER BY locator_id"
        ).fetchall()
        return canonical_json([dict(row) for row in rows])

    def rebuild(self, *, actor: str = "rebuild", now: datetime | None = None) -> dict[str, Any]:
        """Replay the append-only event log into the projection deterministically."""
        del actor, now  # replay is fully derived from the event log
        with self._transaction() as connection:
            before = self._projection_snapshot(connection)
            events = connection.execute(
                "SELECT event_id, locator_id, event_type, payload_json, reason, recorded_at"
                " FROM link_events ORDER BY event_id"
            ).fetchall()
            projection: dict[str, dict[str, Any]] = {}

            for event in events:
                locator_id = str(event["locator_id"])
                event_type = str(event["event_type"])
                if event_type == "claimed":
                    if locator_id in projection:
                        continue  # duplicate claim replay is a no-op
                    payload = json.loads(event["payload_json"])
                    projection[locator_id] = {
                        "locator_id": locator_id,
                        "state": "pending",
                        "schema_version": payload["schema_version"],
                        "kind": payload["kind"],
                        "canonical_namespace": payload["canonical_namespace"],
                        "canonical_id": payload["canonical_id"],
                        "canonical_digest": payload["canonical_digest"],
                        "entire_checkpoint_id": payload["entire_checkpoint_id"],
                        "git_sha": payload["git_sha"],
                        "facets_json": canonical_json(payload["facets"]),
                        "ingested_at": str(event["recorded_at"]),
                        "promoted_at": None,
                        "tombstone_reason": None,
                    }
                elif event_type == "promoted":
                    if locator_id in projection and projection[locator_id]["state"] != "promoted":
                        projection[locator_id]["state"] = "promoted"
                        projection[locator_id]["promoted_at"] = str(event["recorded_at"])
                elif event_type == "tombstoned":
                    if locator_id in projection and projection[locator_id]["state"] != "tombstoned":
                        projection[locator_id]["state"] = "tombstoned"
                        projection[locator_id]["tombstone_reason"] = str(event["reason"])

            connection.execute("DELETE FROM context_links")
            for row in projection.values():
                connection.execute(
                    "INSERT INTO context_links("
                    "locator_id, state, schema_version, kind, canonical_namespace, canonical_id,"
                    " canonical_digest, entire_checkpoint_id, git_sha, facets_json, ingested_at,"
                    " promoted_at, tombstone_reason"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        row["locator_id"],
                        row["state"],
                        row["schema_version"],
                        row["kind"],
                        row["canonical_namespace"],
                        row["canonical_id"],
                        row["canonical_digest"],
                        row["entire_checkpoint_id"],
                        row["git_sha"],
                        row["facets_json"],
                        row["ingested_at"],
                        row["promoted_at"],
                        row["tombstone_reason"],
                    ),
                )
            after = self._projection_snapshot(connection)
        input_parity = before == after
        return {
            "events_replayed": len(events),
            "links": len(projection),
            "parity": input_parity,
            "applied": True,
            "drift_repaired": not input_parity,
        }
