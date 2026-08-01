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
        return {
            "schema_version": SCHEMA_VERSION,
            "counts": {str(row["state"]): int(row["n"]) for row in counts},
            "events": int(events["n"]) if events else 0,
            "last_event_at": events["last_at"] if events else None,
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
