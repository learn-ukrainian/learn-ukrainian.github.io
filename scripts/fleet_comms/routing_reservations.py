"""Transactional routing reservations in the shared Fleet Comms authority store.

This module deliberately owns admission and durable evidence, not routing
policy.  Callers provide their already-approved policy/resolver callback to
``reserve``; the callback sees current bucket occupancy and circuit evidence
while the ledger's ``BEGIN IMMEDIATE`` transaction is held.  Therefore a
candidate selected by policy is admitted (or rejected for capacity) in the
same serialization boundary, without copying reviewer-resolver policy here.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.contracts import new_id
from scripts.fleet_comms.migrations import apply_migrations
from scripts.fleet_comms.paths import default_plane_root

ReservationStatus = Literal["reserved", "running", "complete", "failed", "expired", "cancelled"]
RouteMode = Literal["auto", "explicit"]
TerminalStatus = Literal["complete", "failed", "cancelled"]

_ACTIVE_STATUSES = frozenset({"reserved", "running"})
_TERMINAL_STATUSES = frozenset({"complete", "failed", "expired", "cancelled"})
_SETTLEABLE_STATUSES = frozenset({"complete", "failed", "cancelled"})


class RoutingReservationError(RuntimeError):
    """Routing reservation admission or lifecycle operation was refused."""


class RoutingReservationUnavailable(RoutingReservationError):
    """No policy-approved route can be admitted at the current quota state."""


@dataclass(frozen=True, slots=True)
class RoutingReservationRequest:
    """Stable input to one exact-head routing decision.

    ``authority_key`` must encode every dimension that makes two requests
    non-interchangeable (at minimum the immutable head and requested role).
    It is intentionally supplied by the caller because this ledger does not
    know repository or reviewer-resolver policy semantics.
    """

    authority_key: str
    idempotency_key: str
    initiator: str
    author_model: str
    author_family: str
    requested_role: str
    requested_profile: str
    requested_risk: str
    route_mode: RouteMode
    estimated_input_bytes: int
    requested_reviewer: str | None = None


@dataclass(frozen=True, slots=True)
class RoutingSelection:
    """Policy's selected candidate, supplied while the admission transaction is open."""

    candidate: str
    route: str
    model: str
    family: str
    quota_bucket: str
    credential_bucket: str
    quota_limit: int
    credential_limit: int
    policy_version: str
    quota_snapshot: Mapping[str, Any]
    quota_fresh_at: str | None = None
    trace: Mapping[str, Any] | None = None
    fallback_from: str | None = None
    retry_attempt: int = 0
    quota_source: str = "unknown"
    quota_headroom_band: str = "unknown"


@dataclass(frozen=True, slots=True)
class RoutingCircuitState:
    route_key: str
    recent_failure_count: int
    last_failure_at: str | None
    last_failure_classification: str | None
    open_until: str | None
    updated_at: str


@dataclass(frozen=True, slots=True)
class RoutingBucketUsage:
    """Durable admission facts for one quota bucket at the transaction point."""

    quota_bucket: str
    rolling_window_seconds: int
    inflight_reservations: int
    reserved_input_bytes: int
    completed_window_bytes: int
    recent_failures: int


@dataclass(frozen=True, slots=True)
class RoutingReservation:
    reservation_id: str
    authority_key: str
    attempt: int
    idempotency_key: str
    request_sha256: str
    semantic_sha256: str
    initiator: str
    author_model: str
    author_family: str
    requested_role: str
    requested_profile: str
    requested_risk: str
    route_mode: str
    requested_reviewer: str | None
    resolved_candidate: str
    resolved_route: str
    resolved_model: str
    resolved_family: str
    quota_bucket: str
    credential_bucket: str
    policy_version: str
    estimated_input_bytes: int
    quota_snapshot: dict[str, Any]
    quota_fresh_at: str | None
    fallback_from: str | None
    retry_attempt: int
    quota_source: str
    quota_headroom_band: str
    trace: dict[str, Any]
    created_at: str
    expires_at: str
    started_at: str | None
    settled_at: str | None
    status: str
    actual_bytes: int | None
    actual_tokens: int | None
    actual_input_bytes: int | None
    actual_output_bytes: int | None
    actual_input_tokens: int | None
    actual_output_tokens: int | None
    failure_classification: str | None


@dataclass(frozen=True, slots=True)
class RoutingReservationDecision:
    decision_id: str
    reservation_id: str
    event_type: str
    state: str
    evidence: dict[str, Any]
    created_at: str


class RoutingSelectionContext:
    """Read-only admission facts exposed to the caller's policy callback."""

    def __init__(self, ledger: RoutingReservationLedger, *, now: str) -> None:
        self._ledger = ledger
        self.now = now

    def active_reservations(self, credential_bucket: str) -> int:
        """Return active holders for one credential within this transaction."""
        return self._ledger._active_credential_count(_required(credential_bucket, "credential_bucket"))

    def available_slots(self, credential_bucket: str, credential_limit: int) -> int:
        """Return credential-scoped capacity left under policy's supplied limit."""
        limit = _positive_int(credential_limit, "credential_limit")
        return max(0, limit - self.active_reservations(credential_bucket))

    def active_quota_reservations(self, quota_bucket: str) -> int:
        """Return active holders sharing one provider/account quota bucket."""
        return self._ledger._active_quota_count(_required(quota_bucket, "quota_bucket"))

    def quota_available_slots(self, quota_bucket: str, quota_limit: int) -> int:
        """Return quota-bucket capacity left within the admission transaction."""
        limit = _positive_int(quota_limit, "quota_limit")
        return max(0, limit - self.active_quota_reservations(quota_bucket))

    def bucket_usage(self, quota_bucket: str, *, rolling_window_seconds: int = 3600) -> RoutingBucketUsage:
        """Return quota accounting in an explicit rolling completion window."""
        return self._ledger._bucket_usage(
            _required(quota_bucket, "quota_bucket"),
            now_iso=self.now,
            rolling_window_seconds=rolling_window_seconds,
        )

    def circuit_state(self, route_key: str) -> RoutingCircuitState | None:
        return self._ledger._circuit_state(_required(route_key, "route_key"))

    def bucket_circuit_state(self, quota_bucket: str, credential_bucket: str) -> RoutingCircuitState | None:
        """Read the no-immediate-retry circuit for a quota/credential pairing."""
        return self._ledger._circuit_state(self._ledger._circuit_key(quota_bucket, credential_bucket))


Selector = Callable[[RoutingSelectionContext], RoutingSelection | None]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime | None = None) -> str:
    return (value or _utc_now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: str, *, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise RoutingReservationError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise RoutingReservationError(f"invalid_{field}")
    return parsed.astimezone(UTC)


def _now(value: str | None) -> tuple[datetime, str]:
    parsed = _utc_now() if value is None else _parse_iso(value, field="now")
    return parsed, _iso(parsed)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _mapping(value: Mapping[str, Any] | None, *, field: str) -> dict[str, Any]:
    if value is None:
        return {}
    try:
        decoded = json.loads(_canonical_json(dict(value)))
    except (TypeError, ValueError) as exc:
        raise RoutingReservationError(f"{field}_must_be_json_object") from exc
    if not isinstance(decoded, dict):  # pragma: no cover - dict() guarantees this
        raise RoutingReservationError(f"{field}_must_be_json_object")
    return decoded


def _required(value: str, field: str) -> str:
    normalized = " ".join(str(value or "").split())
    if not normalized:
        raise RoutingReservationError(f"{field}_required")
    return normalized


def _positive_int(value: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RoutingReservationError(f"{field}_must_be_positive")
    return value


def _nonnegative_int(value: int | None, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RoutingReservationError(f"{field}_must_be_nonnegative")
    return value


class RoutingReservationLedger:
    """Shared authority SQLite ledger for one-at-a-time routing admission."""

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

    def close(self) -> None:
        if self._owns_store:
            self.store.close()

    def __enter__(self) -> RoutingReservationLedger:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def reserve_selection(
        self,
        request: RoutingReservationRequest,
        selector: Selector,
        *,
        ttl_seconds: int = 300,
        now: str | None = None,
    ) -> RoutingReservation:
        """Replay or atomically select and admit a route.

        The policy callback is invoked *inside* the write transaction.  It may
        inspect only the context's durable occupancy and circuit facts; this
        module performs no candidate ranking or resolver-policy substitution.
        """
        req, request_sha, semantic_sha = self._validate_request(request)
        ttl = _positive_int(ttl_seconds, "ttl_seconds")
        current, current_iso = _now(now)
        with self._write_transaction():
            self._recover_expired_tx(current_iso)
            idempotent = self._conn.execute(
                """SELECT * FROM routing_reservations
                   WHERE authority_key = ? AND idempotency_key = ?""",
                (req.authority_key, req.idempotency_key),
            ).fetchone()
            if idempotent is not None:
                if str(idempotent["request_sha256"]) != request_sha:
                    raise RoutingReservationError("idempotency_key_reused_with_different_request")
                return self._reservation_from_row(idempotent)

            latest = self._conn.execute(
                """SELECT * FROM routing_reservations
                   WHERE authority_key = ?
                   ORDER BY attempt DESC LIMIT 1""",
                (req.authority_key,),
            ).fetchone()
            if latest is not None and str(latest["semantic_sha256"]) != semantic_sha:
                raise RoutingReservationError("authority_key_semantic_conflict")
            if latest is not None and str(latest["status"]) in _ACTIVE_STATUSES:
                # A distinct initiator joins the same exact-head decision rather
                # than causing a second selection or a quota herd.
                return self._reservation_from_row(latest)

            selection = selector(RoutingSelectionContext(self, now=current_iso))
            if selection is None:
                raise RoutingReservationUnavailable("no_policy_approved_route")
            selected = self._validate_selection(selection)
            circuit = self._circuit_state(self._circuit_key(selected.quota_bucket, selected.credential_bucket))
            if circuit is not None and circuit.open_until is not None and circuit.open_until > current_iso:
                raise RoutingReservationUnavailable("credential_bucket_circuit_open")
            active_credential_count = self._active_credential_count(selected.credential_bucket)
            if active_credential_count >= selected.credential_limit:
                raise RoutingReservationUnavailable("credential_bucket_exhausted")
            active_quota_count = self._active_quota_count(selected.quota_bucket)
            if active_quota_count >= selected.quota_limit:
                raise RoutingReservationUnavailable("quota_bucket_exhausted")

            attempt_row = self._conn.execute(
                "SELECT COALESCE(MAX(attempt), 0) + 1 FROM routing_reservations WHERE authority_key = ?",
                (req.authority_key,),
            ).fetchone()
            attempt = int(attempt_row[0])
            reservation_id = new_id("routing-reservation")
            expires_at = _iso(current + timedelta(seconds=ttl))
            self._conn.execute(
                """INSERT INTO routing_reservations(
                    reservation_id, authority_key, attempt, idempotency_key, request_sha256, semantic_sha256,
                    initiator, author_model, author_family, requested_role, requested_profile,
                    requested_risk, route_mode, requested_reviewer, resolved_candidate, resolved_route,
                    resolved_model, resolved_family, quota_bucket, policy_version,
                    credential_bucket, fallback_from, retry_attempt, quota_source, quota_headroom_band,
                    estimated_input_bytes, quota_snapshot_json, quota_fresh_at, trace_json,
                    created_at, expires_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'reserved')""",
                (
                    reservation_id,
                    req.authority_key,
                    attempt,
                    req.idempotency_key,
                    request_sha,
                    semantic_sha,
                    req.initiator,
                    req.author_model,
                    req.author_family,
                    req.requested_role,
                    req.requested_profile,
                    req.requested_risk,
                    req.route_mode,
                    req.requested_reviewer,
                    selected.candidate,
                    selected.route,
                    selected.model,
                    selected.family,
                    selected.quota_bucket,
                    selected.policy_version,
                    selected.credential_bucket,
                    selected.fallback_from,
                    selected.retry_attempt,
                    selected.quota_source,
                    selected.quota_headroom_band,
                    req.estimated_input_bytes,
                    _canonical_json(selected.quota_snapshot),
                    selected.quota_fresh_at,
                    _canonical_json(selected.trace),
                    current_iso,
                    expires_at,
                ),
            )
            self._append_decision_tx(
                reservation_id,
                event_type="reserved",
                state="reserved",
                evidence={
                    "authority_key": req.authority_key,
                    "attempt": attempt,
                    "active_credential_before": active_credential_count,
                    "active_quota_before": active_quota_count,
                    "credential_bucket": selected.credential_bucket,
                    "credential_limit": selected.credential_limit,
                    "quota_bucket": selected.quota_bucket,
                    "quota_limit": selected.quota_limit,
                    "policy_version": selected.policy_version,
                    "route_mode": req.route_mode,
                    "trace": selected.trace,
                },
                created_at=current_iso,
            )
            return self._get_reservation_tx(reservation_id)

    def reserve(
        self,
        request: RoutingReservationRequest,
        selector: Selector,
        *,
        ttl_seconds: int = 300,
        now: str | None = None,
    ) -> RoutingReservation:
        """Backward-compatible alias for :meth:`reserve_selection`."""
        return self.reserve_selection(request, selector, ttl_seconds=ttl_seconds, now=now)

    def start(self, reservation_id: str, *, now: str | None = None) -> RoutingReservation:
        """Mark a reservation running; repeated calls are idempotent."""
        rid = _required(reservation_id, "reservation_id")
        _, current_iso = _now(now)
        with self._write_transaction():
            self._recover_expired_tx(current_iso)
            row = self._get_reservation_tx(rid)
            if row.status == "reserved":
                self._conn.execute(
                    "UPDATE routing_reservations SET status = 'running', started_at = ? WHERE reservation_id = ?",
                    (current_iso, rid),
                )
                self._append_decision_tx(rid, "started", "running", {}, current_iso)
                return self._get_reservation_tx(rid)
            if row.status == "running":
                return row
            return row

    def mark_started(self, reservation_id: str, *, now: str | None = None) -> RoutingReservation:
        """Explicit lifecycle name used by routing adapters."""
        return self.start(reservation_id, now=now)

    def settle(
        self,
        reservation_id: str,
        *,
        status: TerminalStatus,
        actual_input_bytes: int | None = None,
        actual_output_bytes: int | None = None,
        actual_input_tokens: int | None = None,
        actual_output_tokens: int | None = None,
        failure_classification: str | None = None,
        terminal_evidence: Mapping[str, Any] | None = None,
        circuit_open_seconds: int = 0,
        now: str | None = None,
    ) -> RoutingReservation:
        """Terminally settle or release capacity; exact repeated settlement replays."""
        rid = _required(reservation_id, "reservation_id")
        if status not in _SETTLEABLE_STATUSES:
            raise RoutingReservationError("invalid_terminal_status")
        input_bytes = _nonnegative_int(actual_input_bytes, "actual_input_bytes")
        output_bytes = _nonnegative_int(actual_output_bytes, "actual_output_bytes")
        input_tokens = _nonnegative_int(actual_input_tokens, "actual_input_tokens")
        output_tokens = _nonnegative_int(actual_output_tokens, "actual_output_tokens")
        actual_byte_count = (input_bytes or 0) + (output_bytes or 0)
        actual_token_count = (input_tokens or 0) + (output_tokens or 0)
        open_seconds = _nonnegative_int(circuit_open_seconds, "circuit_open_seconds")
        classification = _required(failure_classification, "failure_classification") if status == "failed" else None
        evidence = _mapping(terminal_evidence, field="terminal_evidence")
        if status != "failed" and failure_classification is not None:
            raise RoutingReservationError("failure_classification_requires_failed_status")
        _, current_iso = _now(now)
        terminal_payload = {
            "actual_input_bytes": input_bytes,
            "actual_output_bytes": output_bytes,
            "actual_input_tokens": input_tokens,
            "actual_output_tokens": output_tokens,
            "failure_classification": classification,
            "status": status,
            "terminal_evidence": evidence,
        }
        terminal_sha = hashlib.sha256(_canonical_json(terminal_payload).encode("utf-8")).hexdigest()
        with self._write_transaction():
            self._recover_expired_tx(current_iso)
            row = self._get_reservation_tx(rid)
            if row.status in _TERMINAL_STATUSES:
                stored = self._conn.execute(
                    "SELECT terminal_sha256 FROM routing_reservations WHERE reservation_id = ?", (rid,)
                ).fetchone()
                if str(stored["terminal_sha256"] or "") != terminal_sha:
                    raise RoutingReservationError("terminal_settlement_conflict")
                return row
            self._conn.execute(
                """UPDATE routing_reservations
                   SET status = ?, settled_at = ?, actual_bytes = ?, actual_tokens = ?,
                       actual_input_bytes = ?, actual_output_bytes = ?,
                       actual_input_tokens = ?, actual_output_tokens = ?,
                       failure_classification = ?, terminal_sha256 = ?
                   WHERE reservation_id = ?""",
                (
                    status,
                    current_iso,
                    actual_byte_count,
                    actual_token_count,
                    input_bytes,
                    output_bytes,
                    input_tokens,
                    output_tokens,
                    classification,
                    terminal_sha,
                    rid,
                ),
            )
            settled = self._get_reservation_tx(rid)
            self._append_decision_tx(rid, "settled", status, terminal_payload, current_iso)
            if status == "failed":
                self._record_failure_tx(settled, classification, int(open_seconds or 0), current_iso)
            return settled

    def fail_and_release(
        self,
        reservation_id: str,
        failure_classification: str,
        *,
        actual_input_bytes: int | None = None,
        actual_output_bytes: int | None = None,
        actual_input_tokens: int | None = None,
        actual_output_tokens: int | None = None,
        circuit_open_seconds: int = 0,
        now: str | None = None,
    ) -> RoutingReservation:
        """Convenience form of failure settlement with capacity release."""
        return self.settle(
            reservation_id,
            status="failed",
            actual_input_bytes=actual_input_bytes,
            actual_output_bytes=actual_output_bytes,
            actual_input_tokens=actual_input_tokens,
            actual_output_tokens=actual_output_tokens,
            failure_classification=failure_classification,
            circuit_open_seconds=circuit_open_seconds,
            now=now,
        )

    def get(self, reservation_id: str) -> RoutingReservation:
        rid = _required(reservation_id, "reservation_id")
        row = self._conn.execute("SELECT * FROM routing_reservations WHERE reservation_id = ?", (rid,)).fetchone()
        if row is None:
            raise RoutingReservationError("reservation_not_found")
        return self._reservation_from_row(row)

    def completed_replay(self, authority_key: str) -> RoutingReservation | None:
        """Return the latest completed exact-head decision without mutating state."""
        row = self._conn.execute(
            """SELECT * FROM routing_reservations
               WHERE authority_key = ? AND status = 'complete'
               ORDER BY attempt DESC LIMIT 1""",
            (_required(authority_key, "authority_key"),),
        ).fetchone()
        return self._reservation_from_row(row) if row is not None else None

    def decisions(self, reservation_id: str) -> tuple[RoutingReservationDecision, ...]:
        rid = _required(reservation_id, "reservation_id")
        rows = self._conn.execute(
            """SELECT * FROM routing_reservation_decisions
               WHERE reservation_id = ? ORDER BY created_at, decision_id""",
            (rid,),
        ).fetchall()
        return tuple(self._decision_from_row(row) for row in rows)

    def circuit_state(self, route_key: str) -> RoutingCircuitState | None:
        return self._circuit_state(_required(route_key, "route_key"))

    def bucket_circuit_state(self, quota_bucket: str, credential_bucket: str) -> RoutingCircuitState | None:
        """Read circuit state for the admission bucket pairing."""
        return self._circuit_state(self._circuit_key(quota_bucket, credential_bucket))

    def recover_expired(self, *, now: str | None = None) -> tuple[RoutingReservation, ...]:
        """Bounded public recovery hook for expired/orphaned active reservations."""
        _, current_iso = _now(now)
        with self._write_transaction():
            ids = self._recover_expired_tx(current_iso)
            return tuple(self._get_reservation_tx(rid) for rid in ids)

    def _validate_request(self, request: RoutingReservationRequest) -> tuple[RoutingReservationRequest, str, str]:
        if not isinstance(request, RoutingReservationRequest):
            raise RoutingReservationError("routing_reservation_request_required")
        estimated = _nonnegative_int(request.estimated_input_bytes, "estimated_input_bytes")
        if request.route_mode not in {"auto", "explicit"}:
            raise RoutingReservationError("invalid_route_mode")
        normalized = RoutingReservationRequest(
            authority_key=_required(request.authority_key, "authority_key"),
            idempotency_key=_required(request.idempotency_key, "idempotency_key"),
            initiator=_required(request.initiator, "initiator"),
            author_model=_required(request.author_model, "author_model"),
            author_family=_required(request.author_family, "author_family"),
            requested_role=_required(request.requested_role, "requested_role"),
            requested_profile=_required(request.requested_profile, "requested_profile"),
            requested_risk=_required(request.requested_risk, "requested_risk"),
            route_mode=request.route_mode,
            estimated_input_bytes=int(estimated or 0),
            requested_reviewer=(
                _required(request.requested_reviewer, "requested_reviewer")
                if request.requested_reviewer is not None
                else None
            ),
        )
        semantic_payload = {
            "author_family": normalized.author_family,
            "author_model": normalized.author_model,
            "authority_key": normalized.authority_key,
            "estimated_input_bytes": normalized.estimated_input_bytes,
            "requested_profile": normalized.requested_profile,
            "requested_reviewer": normalized.requested_reviewer,
            "requested_risk": normalized.requested_risk,
            "requested_role": normalized.requested_role,
            "route_mode": normalized.route_mode,
        }
        semantic_sha = hashlib.sha256(_canonical_json(semantic_payload).encode("utf-8")).hexdigest()
        request_sha = hashlib.sha256(
            _canonical_json({**semantic_payload, "initiator": normalized.initiator}).encode("utf-8")
        ).hexdigest()
        return normalized, request_sha, semantic_sha

    def _validate_selection(self, selection: RoutingSelection) -> RoutingSelection:
        if not isinstance(selection, RoutingSelection):
            raise RoutingReservationError("routing_selection_required")
        freshness = selection.quota_fresh_at
        if freshness is not None:
            _parse_iso(freshness, field="quota_fresh_at")
        return RoutingSelection(
            candidate=_required(selection.candidate, "resolved_candidate"),
            route=_required(selection.route, "resolved_route"),
            model=_required(selection.model, "resolved_model"),
            family=_required(selection.family, "resolved_family"),
            quota_bucket=_required(selection.quota_bucket, "quota_bucket"),
            credential_bucket=_required(selection.credential_bucket, "credential_bucket"),
            quota_limit=_positive_int(selection.quota_limit, "quota_limit"),
            credential_limit=_positive_int(selection.credential_limit, "credential_limit"),
            policy_version=_required(selection.policy_version, "policy_version"),
            quota_snapshot=_mapping(selection.quota_snapshot, field="quota_snapshot"),
            quota_fresh_at=freshness,
            trace=_mapping(selection.trace, field="trace"),
            fallback_from=(
                _required(selection.fallback_from, "fallback_from") if selection.fallback_from is not None else None
            ),
            retry_attempt=int(_nonnegative_int(selection.retry_attempt, "retry_attempt") or 0),
            quota_source=_required(selection.quota_source, "quota_source"),
            quota_headroom_band=_required(selection.quota_headroom_band, "quota_headroom_band"),
        )

    def _active_credential_count(self, credential_bucket: str) -> int:
        row = self._conn.execute(
            """SELECT COUNT(*) AS count FROM routing_reservations
               WHERE credential_bucket = ? AND status IN ('reserved', 'running')""",
            (credential_bucket,),
        ).fetchone()
        return int(row["count"])

    def _active_quota_count(self, quota_bucket: str) -> int:
        row = self._conn.execute(
            """SELECT COUNT(*) AS count FROM routing_reservations
               WHERE quota_bucket = ? AND status IN ('reserved', 'running')""",
            (quota_bucket,),
        ).fetchone()
        return int(row["count"])

    def _bucket_usage(self, quota_bucket: str, *, now_iso: str, rolling_window_seconds: int) -> RoutingBucketUsage:
        window_seconds = _positive_int(rolling_window_seconds, "rolling_window_seconds")
        window_start = _iso(_parse_iso(now_iso, field="now") - timedelta(seconds=window_seconds))
        row = self._conn.execute(
            """SELECT
                   SUM(CASE WHEN status IN ('reserved', 'running') THEN 1 ELSE 0 END) AS inflight,
                   SUM(CASE WHEN status IN ('reserved', 'running') THEN estimated_input_bytes ELSE 0 END) AS reserved_bytes,
                   SUM(CASE WHEN status = 'complete' AND settled_at >= ?
                       THEN COALESCE(actual_input_bytes, 0) + COALESCE(actual_output_bytes, 0)
                       ELSE 0 END) AS completed_bytes,
                   SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failures
               FROM routing_reservations WHERE quota_bucket = ?""",
            (window_start, quota_bucket),
        ).fetchone()
        return RoutingBucketUsage(
            quota_bucket=quota_bucket,
            rolling_window_seconds=window_seconds,
            inflight_reservations=int(row["inflight"] or 0),
            reserved_input_bytes=int(row["reserved_bytes"] or 0),
            completed_window_bytes=int(row["completed_bytes"] or 0),
            recent_failures=int(row["failures"] or 0),
        )

    def _recover_expired_tx(self, now_iso: str) -> tuple[str, ...]:
        rows = self._conn.execute(
            """SELECT reservation_id FROM routing_reservations
               WHERE status IN ('reserved', 'running') AND expires_at <= ?
               ORDER BY created_at, reservation_id LIMIT 256""",
            (now_iso,),
        ).fetchall()
        recovered: list[str] = []
        for row in rows:
            rid = str(row["reservation_id"])
            payload = {
                "failure_classification": "ttl_expired_orphan",
                "status": "expired",
            }
            terminal_sha = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
            cursor = self._conn.execute(
                """UPDATE routing_reservations
                   SET status = 'expired', settled_at = ?, failure_classification = ?,
                       terminal_sha256 = ?
                   WHERE reservation_id = ? AND status IN ('reserved', 'running')""",
                (now_iso, "ttl_expired_orphan", terminal_sha, rid),
            )
            if cursor.rowcount == 1:
                self._append_decision_tx(rid, "recovered_expired", "expired", payload, now_iso)
                self._record_failure_tx(
                    self._get_reservation_tx(rid),
                    "ttl_expired_orphan",
                    0,
                    now_iso,
                )
                recovered.append(rid)
        return tuple(recovered)

    def _record_failure_tx(
        self,
        reservation: RoutingReservation,
        classification: str,
        open_seconds: int,
        now_iso: str,
    ) -> None:
        circuit_key = self._circuit_key(reservation.quota_bucket, reservation.credential_bucket)
        prior = self._circuit_state(circuit_key)
        failures = 1 if prior is None else prior.recent_failure_count + 1
        open_until = _iso(_parse_iso(now_iso, field="now") + timedelta(seconds=open_seconds)) if open_seconds else None
        self._conn.execute(
            """INSERT INTO routing_circuit_state(
                route_key, recent_failure_count, last_failure_at,
                last_failure_classification, open_until, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(route_key) DO UPDATE SET
                recent_failure_count = excluded.recent_failure_count,
                last_failure_at = excluded.last_failure_at,
                last_failure_classification = excluded.last_failure_classification,
                open_until = excluded.open_until,
                updated_at = excluded.updated_at""",
            (circuit_key, failures, now_iso, classification, open_until, now_iso),
        )
        self._append_decision_tx(
            reservation.reservation_id,
            "circuit_recorded",
            "failed",
            {"open_until": open_until, "recent_failure_count": failures},
            now_iso,
        )

    def _append_decision_tx(
        self,
        reservation_id: str,
        event_type: str,
        state: str,
        evidence: Mapping[str, Any],
        created_at: str,
    ) -> None:
        self._conn.execute(
            """INSERT INTO routing_reservation_decisions(
                decision_id, reservation_id, event_type, state, evidence_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                new_id("routing-decision"),
                reservation_id,
                _required(event_type, "event_type"),
                _required(state, "state"),
                _canonical_json(_mapping(evidence, field="evidence")),
                created_at,
            ),
        )

    def _get_reservation_tx(self, reservation_id: str) -> RoutingReservation:
        row = self._conn.execute(
            "SELECT * FROM routing_reservations WHERE reservation_id = ?", (reservation_id,)
        ).fetchone()
        if row is None:
            raise RoutingReservationError("reservation_not_found")
        return self._reservation_from_row(row)

    def _circuit_state(self, route_key: str) -> RoutingCircuitState | None:
        row = self._conn.execute("SELECT * FROM routing_circuit_state WHERE route_key = ?", (route_key,)).fetchone()
        if row is None:
            return None
        return RoutingCircuitState(
            route_key=str(row["route_key"]),
            recent_failure_count=int(row["recent_failure_count"]),
            last_failure_at=str(row["last_failure_at"]) if row["last_failure_at"] is not None else None,
            last_failure_classification=(
                str(row["last_failure_classification"]) if row["last_failure_classification"] is not None else None
            ),
            open_until=str(row["open_until"]) if row["open_until"] is not None else None,
            updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _circuit_key(quota_bucket: str, credential_bucket: str) -> str:
        return f"{_required(quota_bucket, 'quota_bucket')}\x1f{_required(credential_bucket, 'credential_bucket')}"

    @staticmethod
    def _reservation_from_row(row: sqlite3.Row) -> RoutingReservation:
        return RoutingReservation(
            reservation_id=str(row["reservation_id"]),
            authority_key=str(row["authority_key"]),
            attempt=int(row["attempt"]),
            idempotency_key=str(row["idempotency_key"]),
            request_sha256=str(row["request_sha256"]),
            semantic_sha256=str(row["semantic_sha256"]),
            initiator=str(row["initiator"]),
            author_model=str(row["author_model"]),
            author_family=str(row["author_family"]),
            requested_role=str(row["requested_role"]),
            requested_profile=str(row["requested_profile"]),
            requested_risk=str(row["requested_risk"]),
            route_mode=str(row["route_mode"]),
            requested_reviewer=(str(row["requested_reviewer"]) if row["requested_reviewer"] is not None else None),
            resolved_candidate=str(row["resolved_candidate"]),
            resolved_route=str(row["resolved_route"]),
            resolved_model=str(row["resolved_model"]),
            resolved_family=str(row["resolved_family"]),
            quota_bucket=str(row["quota_bucket"]),
            credential_bucket=str(row["credential_bucket"]),
            policy_version=str(row["policy_version"]),
            estimated_input_bytes=int(row["estimated_input_bytes"]),
            quota_snapshot=json.loads(str(row["quota_snapshot_json"])),
            quota_fresh_at=str(row["quota_fresh_at"]) if row["quota_fresh_at"] is not None else None,
            fallback_from=str(row["fallback_from"]) if row["fallback_from"] is not None else None,
            retry_attempt=int(row["retry_attempt"]),
            quota_source=str(row["quota_source"]),
            quota_headroom_band=str(row["quota_headroom_band"]),
            trace=json.loads(str(row["trace_json"])),
            created_at=str(row["created_at"]),
            expires_at=str(row["expires_at"]),
            started_at=str(row["started_at"]) if row["started_at"] is not None else None,
            settled_at=str(row["settled_at"]) if row["settled_at"] is not None else None,
            status=str(row["status"]),
            actual_bytes=int(row["actual_bytes"]) if row["actual_bytes"] is not None else None,
            actual_tokens=int(row["actual_tokens"]) if row["actual_tokens"] is not None else None,
            actual_input_bytes=(int(row["actual_input_bytes"]) if row["actual_input_bytes"] is not None else None),
            actual_output_bytes=(int(row["actual_output_bytes"]) if row["actual_output_bytes"] is not None else None),
            actual_input_tokens=(int(row["actual_input_tokens"]) if row["actual_input_tokens"] is not None else None),
            actual_output_tokens=(
                int(row["actual_output_tokens"]) if row["actual_output_tokens"] is not None else None
            ),
            failure_classification=(
                str(row["failure_classification"]) if row["failure_classification"] is not None else None
            ),
        )

    @staticmethod
    def _decision_from_row(row: sqlite3.Row) -> RoutingReservationDecision:
        return RoutingReservationDecision(
            decision_id=str(row["decision_id"]),
            reservation_id=str(row["reservation_id"]),
            event_type=str(row["event_type"]),
            state=str(row["state"]),
            evidence=json.loads(str(row["evidence_json"])),
            created_at=str(row["created_at"]),
        )

    class _WriteTransaction:
        def __init__(self, ledger: RoutingReservationLedger) -> None:
            self.ledger = ledger

        def __enter__(self) -> None:
            self.ledger._conn.execute("BEGIN IMMEDIATE")

        def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
            if exc_type is None:
                try:
                    self.ledger._conn.commit()
                except Exception:
                    self.ledger._conn.rollback()
                    raise
            else:
                self.ledger._conn.rollback()
            return False

    def _write_transaction(self) -> _WriteTransaction:
        return self._WriteTransaction(self)


def open_routing_reservation_ledger(root: Path | None = None) -> RoutingReservationLedger:
    """Open the shared Fleet Comms routing-reservation ledger."""
    return RoutingReservationLedger(root=root)


def list_routing_decisions(*, root: Path | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """Read recent routing evidence without creating, migrating, or writing SQLite.

    A missing plane or pre-v6 schema is deliberately reported as an empty
    projection.  Runtime readers must never turn an observation into a writer.
    """
    bounded_limit = _positive_int(limit, "limit")
    plane_root = Path(root).resolve() if root is not None else default_plane_root()
    db_path = plane_root / "comms.sqlite3"
    if not db_path.is_file():
        return []
    try:
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
    except sqlite3.Error:
        return []
    try:
        required_tables = {"routing_reservations", "routing_reservation_decisions"}
        tables = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN (?, ?)",
                tuple(sorted(required_tables)),
            )
        }
        if tables != required_tables:
            return []
        rows = connection.execute(
            """SELECT d.decision_id, d.reservation_id, d.event_type, d.state,
                      d.evidence_json, d.created_at AS decision_created_at,
                      r.authority_key, r.attempt, r.idempotency_key, r.initiator,
                      r.author_model, r.author_family, r.requested_role,
                      r.requested_profile, r.requested_risk, r.route_mode, r.requested_reviewer,
                      r.estimated_input_bytes, r.resolved_candidate,
                      r.resolved_route, r.resolved_model, r.resolved_family,
                      r.quota_bucket, r.credential_bucket, r.policy_version, r.quota_snapshot_json,
                      r.quota_fresh_at, r.trace_json, r.created_at, r.expires_at,
                      r.started_at, r.settled_at, r.status, r.actual_bytes,
                      r.actual_tokens, r.actual_input_bytes, r.actual_output_bytes,
                      r.actual_input_tokens, r.actual_output_tokens, r.failure_classification,
                      r.fallback_from, r.retry_attempt, r.quota_source, r.quota_headroom_band
               FROM routing_reservation_decisions d
               JOIN routing_reservations r ON r.reservation_id = d.reservation_id
               ORDER BY d.created_at DESC, d.decision_id DESC LIMIT ?""",
            (bounded_limit,),
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        connection.close()
    return [_routing_decision_projection(row) for row in rows]


def _routing_decision_projection(row: sqlite3.Row) -> dict[str, Any]:
    """Return the dashboard allowlist; omit resolver inputs and any payload bodies."""
    return {
        "decision_id": str(row["decision_id"]),
        "reservation_id": str(row["reservation_id"]),
        "authority_key": str(row["authority_key"]),
        "event_type": str(row["event_type"]),
        "state": str(row["state"]),
        "evidence": json.loads(str(row["evidence_json"])),
        "created_at": str(row["decision_created_at"]),
        "requested": {
            "initiator": str(row["initiator"]),
            "author_model": str(row["author_model"]),
            "author_family": str(row["author_family"]),
            "role": str(row["requested_role"]),
            "profile": str(row["requested_profile"]),
            "risk": str(row["requested_risk"]),
            "route_mode": str(row["route_mode"]),
            "automatic": str(row["route_mode"]) == "auto",
            "requested_reviewer": (str(row["requested_reviewer"]) if row["requested_reviewer"] is not None else None),
            "exceptional_pin": str(row["route_mode"]) == "explicit",
            "estimated_input_bytes": int(row["estimated_input_bytes"]),
        },
        "resolved": {
            "candidate": str(row["resolved_candidate"]),
            "route": str(row["resolved_route"]),
            "model": str(row["resolved_model"]),
            "family": str(row["resolved_family"]),
            "policy_version": str(row["policy_version"]),
            "trace": json.loads(str(row["trace_json"])),
        },
        "quota": {
            "bucket": str(row["quota_bucket"]),
            "credential_bucket": str(row["credential_bucket"]),
            "snapshot": json.loads(str(row["quota_snapshot_json"])),
            "fresh_at": str(row["quota_fresh_at"]) if row["quota_fresh_at"] is not None else None,
            "source": str(row["quota_source"]),
            "headroom_band": str(row["quota_headroom_band"]),
        },
        "retry": {
            "attempt": int(row["attempt"]),
            "fallback_from": str(row["fallback_from"]) if row["fallback_from"] is not None else None,
            "retry_attempt": int(row["retry_attempt"]),
            "terminal_status": str(row["status"]),
            "failure_classification": (
                str(row["failure_classification"]) if row["failure_classification"] is not None else None
            ),
        },
        "replay": {
            "authority_key": str(row["authority_key"]),
            "idempotency_key": str(row["idempotency_key"]),
            "completed": str(row["status"]) == "complete",
        },
        "lifecycle": {
            "status": str(row["status"]),
            "created_at": str(row["created_at"]),
            "expires_at": str(row["expires_at"]),
            "started_at": str(row["started_at"]) if row["started_at"] is not None else None,
            "settled_at": str(row["settled_at"]) if row["settled_at"] is not None else None,
            "actual_bytes": int(row["actual_bytes"]) if row["actual_bytes"] is not None else None,
            "actual_tokens": int(row["actual_tokens"]) if row["actual_tokens"] is not None else None,
            "failure_classification": (
                str(row["failure_classification"]) if row["failure_classification"] is not None else None
            ),
            "actual_input_bytes": (int(row["actual_input_bytes"]) if row["actual_input_bytes"] is not None else None),
            "actual_output_bytes": (
                int(row["actual_output_bytes"]) if row["actual_output_bytes"] is not None else None
            ),
            "actual_input_tokens": (
                int(row["actual_input_tokens"]) if row["actual_input_tokens"] is not None else None
            ),
            "actual_output_tokens": (
                int(row["actual_output_tokens"]) if row["actual_output_tokens"] is not None else None
            ),
        },
    }


__all__ = [
    "RoutingBucketUsage",
    "RoutingCircuitState",
    "RoutingReservation",
    "RoutingReservationDecision",
    "RoutingReservationError",
    "RoutingReservationLedger",
    "RoutingReservationRequest",
    "RoutingReservationUnavailable",
    "RoutingSelection",
    "RoutingSelectionContext",
    "list_routing_decisions",
    "open_routing_reservation_ledger",
]
