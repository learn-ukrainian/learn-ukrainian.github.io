"""Bounded, durable ACPX multi-seat discussion controller (#6078, #6130).

This is intentionally a small finite DAG, not a new message-plane router. It
requires ``LU_ACPX_TRANSPORT=active``; two to six participants resolve through
the runner-owned normal ACP boundary into enabled direct-only ACPX seats, while
the final synthesis is a fresh native Codex call.
"""

from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import threading
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# runner.py retains historical sibling imports such as ai_llm; support both
# package invocation and the legacy scripts-on-PYTHONPATH form.
_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from scripts.agent_runtime.adapters.acpx import (
    ACPX_SUPPORTED_PARTICIPANTS,
    TRANSPORT_ENV,
    _require_local_metadata_field,
    active_discussion_scope,
)
from scripts.agent_runtime.errors import AgentStalledError, AgentTimeoutError, RateLimitedError
from scripts.agent_runtime.result import Result
from scripts.agent_runtime.runner import (
    _invoke_native_once,
    invoke_inter_agent,
    resolve_inter_agent_route,
)
from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.contracts import new_id
from scripts.fleet_comms.message_plane import default_plane_root
from scripts.guardrails.worktree_containment import classify_repo_path

logger = logging.getLogger(__name__)

PARTICIPANTS = ("codex", "grok")
SUPPORTED_PARTICIPANTS = frozenset(ACPX_SUPPORTED_PARTICIPANTS)
MIN_PARTICIPANTS = 2
MAX_PARTICIPANTS = 6
MAX_ROUNDS = 3
DEFAULT_ROUNDS = 2
CALL_TIMEOUT_SECONDS = 300
WHOLE_TIMEOUT_SECONDS = 1200
TOKEN_BUDGET = 160_000
CONTENT_BUDGET_BYTES = 512 * 1024
PARTICIPANT_CONCURRENCY = 3

_TERMINAL = frozenset({"COMPLETE", "PARTIAL_COMPLETE", "FAILED", "CANCELLED"})
_PARTICIPANT_SLOTS = threading.BoundedSemaphore(PARTICIPANT_CONCURRENCY)
_LOCAL_ADMISSION = threading.Lock()
_CONVERSATION_ID = re.compile(r"conversation_[0-9a-f]{32}")
_NEXT = {
    # A CREATED reservation may be recovered after a crash only as terminal
    # partial; it is never re-executed.
    "CREATED": {"INITIAL_FANOUT", "PARTIAL_COMPLETE", "CANCELLED"},
    "INITIAL_FANOUT": {"INITIAL_COMPLETE", "PARTIAL"},
    "INITIAL_COMPLETE": {"CROSS_EXCHANGE", "SYNTHESIS", "CANCELLED"},
    "PARTIAL": {"CROSS_EXCHANGE", "SYNTHESIS", "CANCELLED"},
    "CROSS_EXCHANGE": {"CROSS_EXCHANGE_COMPLETE", "PARTIAL"},
    "CROSS_EXCHANGE_COMPLETE": {"CROSS_EXCHANGE", "SYNTHESIS", "CANCELLED"},
    "SYNTHESIS": _TERMINAL,
}


class AcpxDiscussionError(RuntimeError):
    """Typed refusal or state-machine failure for the bounded controller."""


class AcpxDiscussionBusyError(AcpxDiscussionError):
    """Another ACP discussion owns the repository-wide single-host admission."""


class AcpxDiscussionNotFoundError(AcpxDiscussionError):
    """The requested durable ACP discussion receipt does not exist."""


@dataclass(frozen=True, slots=True)
class ParticipantOutcome:
    participant: str
    outcome: str
    response: str | None
    duration_ms: int
    tokens: int | None
    message_id: str | None


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _leg_digest(*parts: str) -> str:
    return _digest("\x1f".join(parts))


def _result_outcome(result: Result | None, error: BaseException | None) -> str:
    if isinstance(error, (AgentTimeoutError, AgentStalledError)):
        return "timeout"
    if isinstance(error, RateLimitedError):
        return "rate_limited"
    if error is not None or result is None:
        return "error"
    if result.transport_outcome in {"ok", "error", "rate_limited"}:
        return result.transport_outcome
    if not result.ok:
        return str(result.usage_record.get("outcome") or "error")
    return "ok"


def _safe_tokens(value: object) -> int | None:
    """Accept only explicit non-negative token totals, never context capacity."""
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _safe_receipt_timestamp(value: object) -> str | None:
    """Allow only the controller's normalized UTC timestamp representation."""
    if not isinstance(value, str):
        return None
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    return value


def _safe_receipt_outcome(value: object) -> str:
    """Collapse untrusted persisted outcomes into a fixed body-free vocabulary."""
    if value == "ok":
        return "ok"
    if value in {"timeout", "rate_limited", "error", "busy", "orphan"}:
        return str(value)
    return "other_failure"


def _expired_deadline(value: object) -> bool:
    """Fail closed unless a persisted UTC deadline is valid and in the past."""
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return False
    return datetime.now(UTC) > parsed


@contextmanager
def _discussion_admission(root: Path) -> Iterator[None]:
    """Acquire one no-wait ACP slot for this repository on the current host.

    The local mutex closes same-process platform differences in ``flock``
    semantics. The file lock covers independent worktree processes sharing the
    canonical fleet-comms root. A host crash releases both automatically; the
    persistent lock file is only an inode and contains no runtime data.
    """
    if not _LOCAL_ADMISSION.acquire(blocking=False):
        raise AcpxDiscussionBusyError("another ACP discussion is already running")
    descriptor: int | None = None
    locked = False
    try:
        flags = os.O_CREAT | os.O_RDWR
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(root / "acp-discuss.lock", flags, 0o600)
            os.fchmod(descriptor, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except OSError as exc:
            if exc.errno in {errno.EACCES, errno.EAGAIN}:
                raise AcpxDiscussionBusyError(
                    "another ACP discussion is already running"
                ) from None
            raise AcpxDiscussionError(
                f"unable to acquire the ACP admission lock: {exc}"
            ) from exc
        yield
    finally:
        if descriptor is not None:
            if locked:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
        _LOCAL_ADMISSION.release()


class AcpxDiscussionController:
    """Append-only controller; every DB transaction is committed before I/O."""

    def __init__(
        self,
        *,
        root: Path,
        participant_call: Callable[..., Result] | None = None,
        synthesis_call: Callable[..., Result] = _invoke_native_once,
        clock: Callable[[], float] = time.monotonic,
        cancelled: Callable[[], bool] | None = None,
    ) -> None:
        self.store = ArtifactStore(root=root)
        self.conn = self.store.connection
        # The default is the runner-owned normal ACP transport.  Test and
        # migration callers may inject the previous direct-only callback; that
        # compatibility seam remains read-only and cannot select a bridge.
        self.participant_call = participant_call
        self.synthesis_call = synthesis_call
        self.clock = clock
        self.cancelled = cancelled or (lambda: False)

    def close(self) -> None:
        self.store.close()

    def _append(
        self,
        conversation_id: str,
        *,
        event_type: str,
        state: str,
        sender: str | None = None,
        recipient: str | None = None,
        round_no: int | None = None,
        outcome: str | None = None,
        duration_ms: int | None = None,
        token_count: int | None = None,
        leg_key_digest: str | None = None,
        message_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        transition: bool = False,
    ) -> None:
        """Serialize one transition/event atomically; never held during model I/O."""
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            row = self.conn.execute(
                "SELECT state FROM acp_conversation_events WHERE conversation_id = ? ORDER BY sequence DESC LIMIT 1",
                (conversation_id,),
            ).fetchone()
            current = str(row[0]) if row is not None else None
            orphan_recovery = (
                event_type == "ORPHAN_RESERVATION"
                and state == "PARTIAL_COMPLETE"
                and current is not None
                and current not in _TERMINAL
            )
            if (
                transition
                and current is not None
                and state not in _NEXT.get(current, set())
                and not orphan_recovery
            ):
                raise AcpxDiscussionError(f"invalid ACPX transition {current} -> {state}")
            sequence = int(
                self.conn.execute(
                    "SELECT COALESCE(MAX(sequence), 0) + 1 FROM acp_conversation_events WHERE conversation_id = ?",
                    (conversation_id,),
                ).fetchone()[0]
            )
            self.conn.execute(
                """INSERT INTO acp_conversation_events(
                    event_id, conversation_id, sequence, event_type, state, sender, recipient,
                    round, outcome, duration_ms, token_count, leg_key_digest, message_id,
                    metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_id("acp-event"), conversation_id, sequence, event_type, state, sender,
                    recipient, round_no, outcome, duration_ms, token_count, leg_key_digest,
                    message_id, json.dumps(metadata or {}, sort_keys=True), _now(),
                ),
            )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def _state(self, conversation_id: str) -> str:
        row = self.conn.execute(
            "SELECT state FROM acp_conversation_events WHERE conversation_id = ? ORDER BY sequence DESC LIMIT 1",
            (conversation_id,),
        ).fetchone()
        if row is None:
            raise AcpxDiscussionError("conversation has no state event")
        return str(row[0])

    def _message(
        self,
        conversation_id: str,
        *,
        sender: str,
        recipient: str,
        body: str,
        reply_to: str | None,
        kind: str = "reply",
    ) -> str:
        """Persist directed content in the existing message/artifact mechanism."""
        message_id = new_id("message")
        try:
            # The blob itself is durable before its SQLite row is created. Keep
            # that row, the message, and its GC-visible reference in one SQLite
            # transaction: a crash exposes either all three records or none.
            self.conn.execute("BEGIN IMMEDIATE")
            artifact = self.store.store_text(
                body,
                producer=f"acpx-discuss:{sender}",
                retention_class="acpx-discussion",
                logical_filename=f"{sender}-message.txt",
                commit=False,
            )
            self.conn.execute(
                """INSERT INTO comms_messages(
                    message_id, conversation_id, in_reply_to, kind, sender, recipient, body_inline,
                    body_artifact_id, content_sha256, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    message_id, conversation_id, reply_to, kind, sender, recipient, body,
                    artifact.artifact_id, artifact.sha256, json.dumps({"acpx_discussion": True}), _now(),
                ),
            )
            self.store.reference(
                message_id,
                artifact.artifact_id,
                relation="body",
                commit=False,
            )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        return message_id

    def _replay(self, conversation_id: str) -> dict[str, Any]:
        synthesis = self.conn.execute(
            """SELECT body_inline FROM comms_messages
               WHERE conversation_id = ? AND kind = 'synthesis'
               ORDER BY created_at DESC LIMIT 1""",
            (conversation_id,),
        ).fetchone()
        if synthesis is None:
            # Backward-compatible recovery for conversations completed before
            # the synthesis-specific message kind was introduced.
            synthesis = self.conn.execute(
                """SELECT body_inline FROM comms_messages
                   WHERE conversation_id = ? AND sender = 'codex' AND recipient = 'root'
                   ORDER BY created_at DESC LIMIT 1""",
                (conversation_id,),
            ).fetchone()
        state = self._state(conversation_id)
        final_event = self.conn.execute(
            """SELECT metadata_json FROM acp_conversation_events
               WHERE conversation_id = ? AND event_type = 'STATE'
                 AND state IN ('COMPLETE', 'PARTIAL_COMPLETE', 'FAILED', 'CANCELLED')
               ORDER BY sequence DESC LIMIT 1""",
            (conversation_id,),
        ).fetchone()
        try:
            final_metadata = json.loads(str(final_event[0])) if final_event is not None else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            final_metadata = {}
        terminal_rows = self.conn.execute(
            """SELECT sender, outcome, duration_ms, token_count, round
               FROM acp_conversation_events
               WHERE conversation_id = ? AND event_type = 'CALL_TERMINAL'
               ORDER BY round,
                        CASE sender WHEN 'codex' THEN 0 WHEN 'grok' THEN 1 ELSE 2 END,
                        sequence""",
            (conversation_id,),
        ).fetchall()
        participant_outcomes = [
            {
                "participant": str(row[0]),
                "outcome": str(row[1]),
                "duration_ms": int(row[2] or 0),
                "tokens": _safe_tokens(row[3]),
            }
            for row in terminal_rows
        ]
        derived_rounds = max((int(row[4] or 0) for row in terminal_rows), default=0)
        derived_tokens = sum(item["tokens"] or 0 for item in participant_outcomes)

        def saved_count(name: str, fallback: int) -> int:
            value = final_metadata.get(name)
            return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else fallback

        return {
            "conversation_id": conversation_id,
            "state": state,
            "classification": (
                "complete"
                if state == "COMPLETE"
                else "cancelled"
                if state == "CANCELLED"
                else "partial"
            ),
            "participant_outcomes": participant_outcomes,
            "rounds_completed": saved_count("rounds_completed", derived_rounds),
            "duration_ms": saved_count("duration_ms", 0),
            "tokens": saved_count("tokens", derived_tokens),
            "synthesis": str(synthesis[0]) if synthesis else None,
            "duplicate_suppressed": True,
        }

    def _cancelled_payload(
        self,
        conversation_id: str,
        *,
        started: float,
        rounds_completed: int,
        token_used: int,
        outcomes: list[ParticipantOutcome],
    ) -> dict[str, Any]:
        """Persist an explicit terminal cancellation after in-flight work settles."""
        duration_ms = max(0, int((self.clock() - started) * 1000))
        participant_outcomes = [
            {
                "participant": item.participant,
                "outcome": item.outcome,
                "duration_ms": item.duration_ms,
                "tokens": item.tokens,
            }
            for item in outcomes
        ]
        self._append(
            conversation_id,
            event_type="STATE",
            state="CANCELLED",
            duration_ms=duration_ms,
            token_count=token_used,
            metadata={
                "rounds_completed": rounds_completed,
                "duration_ms": duration_ms,
                "tokens": token_used,
            },
            transition=True,
        )
        return {
            "conversation_id": conversation_id,
            "state": "CANCELLED",
            "classification": "cancelled",
            "participant_outcomes": participant_outcomes,
            "rounds_completed": rounds_completed,
            "duration_ms": duration_ms,
            "tokens": token_used,
            "synthesis": None,
            "duplicate_suppressed": False,
        }

    def _reserve(
        self,
        *,
        task_digest: str,
        correlation_digest: str,
        idempotency_digest: str,
        rounds: int,
        deadline_at: str,
        participants: tuple[str, ...] = PARTICIPANTS,
    ) -> tuple[str, dict[str, Any] | None]:
        """Durably create the conversation before spawning any participant."""
        conversation_id = new_id("conversation")
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            self.conn.execute(
                "INSERT INTO conversations(conversation_id, created_at, source, title) VALUES (?, ?, ?, ?)",
                (conversation_id, _now(), "acpx-discuss", "bounded ACPX discussion"),
            )
            self.conn.execute(
                """INSERT INTO acp_conversations(
                    conversation_id, task_digest, correlation_digest, idempotency_digest,
                    rounds_requested, participants_json, created_at, deadline_at, token_budget,
                    content_budget_bytes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (conversation_id, task_digest, correlation_digest, idempotency_digest, rounds,
                 json.dumps(participants), _now(), deadline_at, TOKEN_BUDGET, CONTENT_BUDGET_BYTES),
            )
            self.conn.execute(
                """INSERT INTO acp_conversation_events(
                    event_id, conversation_id, sequence, event_type, state, metadata_json, created_at
                ) VALUES (?, ?, 1, 'CREATED', 'CREATED', '{}', ?)""",
                (new_id("acp-event"), conversation_id, _now()),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            self.conn.rollback()
            row = self.conn.execute(
                """SELECT conversation_id, deadline_at
                   FROM acp_conversations WHERE idempotency_digest = ?""",
                (idempotency_digest,),
            ).fetchone()
            if row is None:
                raise
            existing = str(row[0])
            state = self._state(existing)
            if state in _TERMINAL:
                self._append(
                    existing,
                    event_type="DUPLICATE_SUPPRESSED",
                    state=state,
                    outcome="duplicate_suppressed",
                )
                return existing, self._replay(existing)
            if not _expired_deadline(row[1]):
                raise AcpxDiscussionError(
                    "a reservation for this idempotency key is still in progress"
                ) from None
            # An expired prior reservation did not finish. No retry is legal.
            try:
                self._append(
                    existing,
                    event_type="ORPHAN_RESERVATION",
                    state="PARTIAL_COMPLETE",
                    outcome="orphan",
                    transition=True,
                )
            except AcpxDiscussionError:
                # Another recovery caller may have won the serialized terminal
                # transition after our pre-check. That is an idempotent replay,
                # not a new error or permission to re-execute model calls.
                raced_state = self._state(existing)
                if raced_state not in _TERMINAL:
                    raise
                self._append(
                    existing,
                    event_type="DUPLICATE_SUPPRESSED",
                    state=raced_state,
                    outcome="duplicate_suppressed",
                )
            return existing, self._replay(existing)
        return conversation_id, None

    def _terminal_replay(self, idempotency_digest: str) -> dict[str, Any] | None:
        """Replay completed work before admission so duplicates never report busy."""
        row = self.conn.execute(
            "SELECT conversation_id FROM acp_conversations WHERE idempotency_digest = ?",
            (idempotency_digest,),
        ).fetchone()
        if row is None:
            return None
        conversation_id = str(row[0])
        state = self._state(conversation_id)
        if state not in _TERMINAL:
            return None
        self._append(
            conversation_id,
            event_type="DUPLICATE_SUPPRESSED",
            state=state,
            outcome="duplicate_suppressed",
        )
        return self._replay(conversation_id)

    def _adopt_authority_reservation(
        self,
        conversation_id: str,
        *,
        task_digest: str,
        correlation_digest: str,
        idempotency_digest: str,
        rounds: int,
        participants: tuple[str, ...],
        source: str | None,
    ) -> str:
        """Adopt the exact reservation created atomically with an authority job."""
        if _CONVERSATION_ID.fullmatch(conversation_id) is None:
            raise AcpxDiscussionError("reserved conversation_id is not canonical")
        row = self.conn.execute(
            """SELECT acp.task_digest, acp.correlation_digest,
                      acp.idempotency_digest, acp.rounds_requested,
                      acp.participants_json, conversation.source
               FROM acp_conversations AS acp
               JOIN conversations AS conversation
                 ON conversation.conversation_id = acp.conversation_id
               WHERE acp.conversation_id = ?""",
            (conversation_id,),
        ).fetchone()
        if row is None:
            raise AcpxDiscussionError("reserved ACP conversation was not found")
        try:
            reserved_participants = tuple(json.loads(str(row[4])))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise AcpxDiscussionError("reserved ACP participants are invalid") from exc
        expected = (
            task_digest,
            correlation_digest,
            idempotency_digest,
            rounds,
            tuple(sorted(participants)),
            source or "operator",
        )
        observed = (
            str(row[0]),
            str(row[1]),
            str(row[2]),
            int(row[3]),
            reserved_participants,
            str(row[5]),
        )
        if observed != expected:
            raise AcpxDiscussionError("reserved ACP conversation does not match invocation")
        events = self.conn.execute(
            """SELECT sequence, event_type, state
               FROM acp_conversation_events
               WHERE conversation_id = ? ORDER BY sequence""",
            (conversation_id,),
        ).fetchall()
        if len(events) != 1 or tuple(events[0]) != (1, "CREATED", "CREATED"):
            raise AcpxDiscussionError("reserved ACP conversation has invalid initial state")
        return conversation_id

    def recover_expired_reservations(self, *, now: datetime | None = None) -> list[str]:
        """Terminalize expired nonterminal reservations without provider I/O.

        The caller must hold :func:`_discussion_admission`.  Recovery is
        deliberately terminal-only: an expired reservation proves neither a
        safe retry nor a usable response, so it becomes partial evidence and
        is never re-executed.
        """
        observed_at = now or datetime.now(UTC)
        observed_at = (
            observed_at.replace(tzinfo=UTC)
            if observed_at.tzinfo is None
            else observed_at.astimezone(UTC)
        )
        rows = self.conn.execute(
            """SELECT acp.conversation_id, acp.deadline_at
               FROM acp_conversations AS acp
               JOIN conversations AS conversation
                 ON conversation.conversation_id = acp.conversation_id
               WHERE conversation.source = 'acpx-discuss'
                  OR EXISTS (
                      SELECT 1 FROM acp_conversation_events AS initial
                      WHERE initial.conversation_id = acp.conversation_id
                        AND initial.sequence = 1
                        AND initial.event_type = 'CREATED'
                        AND initial.metadata_json = '{"authority_reserved":true}'
                  )"""
        ).fetchall()
        recovered: list[str] = []
        for row in rows:
            conversation_id = str(row[0])
            deadline_at = row[1]
            if not isinstance(deadline_at, str):
                continue
            try:
                deadline = datetime.strptime(deadline_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            except ValueError:
                continue
            if observed_at <= deadline or self._state(conversation_id) in _TERMINAL:
                continue
            self._append(
                conversation_id,
                event_type="ORPHAN_RESERVATION",
                state="PARTIAL_COMPLETE",
                outcome="orphan",
                transition=True,
            )
            recovered.append(conversation_id)
        return recovered

    @staticmethod
    def _normalize_participant_overrides(
        label: str,
        overrides: Mapping[str, str] | None,
        participants: tuple[str, ...],
    ) -> dict[str, str]:
        """Accept only exact participant-keyed non-secret model/effort pins."""
        if overrides is None:
            return {}
        if not isinstance(overrides, Mapping):
            raise AcpxDiscussionError(f"{label} must be a participant-keyed mapping")
        normalized: dict[str, str] = {}
        for raw_participant, raw_value in overrides.items():
            participant = str(raw_participant).strip().lower()
            if participant not in participants or participant in normalized:
                raise AcpxDiscussionError(
                    f"{label} contains an unknown or duplicate participant {raw_participant!r}"
                )
            if not isinstance(raw_value, str) or not raw_value.strip():
                raise AcpxDiscussionError(
                    f"{label}[{participant!r}] must be a non-empty catalog identifier"
                )
            normalized[participant] = raw_value.strip()
        return normalized

    def _call_wave(
        self,
        *,
        conversation_id: str,
        task_id: str,
        correlation_id: str,
        idempotency_key: str,
        cwd: Path,
        round_no: int,
        prompts: dict[str, str],
        deliveries: Mapping[str, Sequence[tuple[str, str, str | None]] | tuple[str, str, str | None]],
        state: str,
        deadline: float,
        source: str | None = None,
        models: Mapping[str, str] | None = None,
        efforts: Mapping[str, str] | None = None,
        participants: tuple[str, ...] = PARTICIPANTS,
    ) -> list[ParticipantOutcome]:
        reservations: dict[str, str] = {}
        request_messages: dict[str, str] = {}
        model_overrides = models or {}
        effort_overrides = efforts or {}
        for participant in participants:
            leg = _leg_digest(conversation_id, str(round_no), participant, _digest(prompts[participant]))
            reservations[participant] = leg
            raw_deliveries = deliveries[participant]
            if (
                len(raw_deliveries) == 3
                and isinstance(raw_deliveries[0], str)
                and isinstance(raw_deliveries[1], str)
            ):
                delivery_items = (raw_deliveries,)
            else:
                delivery_items = tuple(raw_deliveries)
            if not delivery_items:
                raise AcpxDiscussionError(f"participant {participant!r} has no persisted delivery")
            message_ids: list[str] = []
            for sender, body, reply_to in delivery_items:
                message_ids.append(
                    self._message(
                        conversation_id,
                        sender=sender,
                        recipient=participant,
                        body=body,
                        reply_to=reply_to,
                        kind="request" if sender == "root" else "reply",
                    )
                )
            request_messages[participant] = message_ids[-1]
            self._append(
                conversation_id,
                event_type="CALL_RESERVED",
                state=state,
                sender=delivery_items[-1][0],
                recipient=participant,
                round_no=round_no,
                leg_key_digest=leg,
                message_id=request_messages[participant],
            )

        def invoke(participant: str) -> ParticipantOutcome:
            start = self.clock()
            result: Result | None = None
            error: BaseException | None = None
            if not _PARTICIPANT_SLOTS.acquire(blocking=False):
                return ParticipantOutcome(participant, "busy", None, 0, None, None)
            try:
                timeout = max(1, min(CALL_TIMEOUT_SECONDS, int(deadline - self.clock())))
                if self.participant_call is None:
                    result = invoke_inter_agent(
                        participant,
                        prompts[participant],
                        cwd=cwd,
                        task_id=task_id,
                        correlation_id=correlation_id,
                        idempotency_key=idempotency_key,
                        source=source,
                        model=model_overrides.get(participant),
                        effort=effort_overrides.get(participant),
                        hard_timeout=timeout,
                    )
                else:
                    # Preserve the injectable legacy callback contract for
                    # deterministic controller tests and migration consumers.
                    # It still enters only the read-only active ACP scope.
                    with active_discussion_scope():
                        route = ACPX_SUPPORTED_PARTICIPANTS[participant]
                        result = self.participant_call(
                            str(route["seat"]),
                            prompts[participant],
                            cwd=cwd,
                            model=model_overrides.get(participant),
                            task_id=task_id,
                            tool_config={
                                "acpx_discussion": True,
                                "target_agent": route["agent"],
                                "correlation_id": correlation_id,
                                "idempotency_key": idempotency_key,
                            },
                            hard_timeout=timeout,
                            effort=effort_overrides.get(participant),
                            entrypoint="acpx-discuss",
                            initiator=source,
                        )
            except BaseException as exc:  # preserve cancellation as typed partial evidence
                error = exc
            finally:
                _PARTICIPANT_SLOTS.release()
            duration = max(0, int((self.clock() - start) * 1000))
            outcome = _result_outcome(result, error)
            tokens = result.usage_record.get("tokens") if result is not None else None
            token_count = _safe_tokens(tokens)
            response = result.response if outcome == "ok" and result is not None else None
            return ParticipantOutcome(participant, outcome, response, duration, token_count, None)

        outcomes: list[ParticipantOutcome] = []

        def persist(outcome: ParticipantOutcome) -> None:
            """Persist a completed leg before waiting on another participant."""
            message_id = None
            if outcome.response is not None:
                message_id = self._message(
                    conversation_id,
                    sender=outcome.participant,
                    recipient="root",
                    body=outcome.response,
                    reply_to=request_messages[outcome.participant],
                )
            self._append(
                conversation_id,
                event_type="CALL_TERMINAL",
                state=state,
                sender=outcome.participant,
                recipient="root",
                round_no=round_no,
                outcome=outcome.outcome,
                duration_ms=outcome.duration_ms,
                token_count=outcome.tokens,
                leg_key_digest=reservations[outcome.participant],
                message_id=message_id,
            )
            outcomes.append(
                ParticipantOutcome(
                    outcome.participant,
                    outcome.outcome,
                    outcome.response,
                    outcome.duration_ms,
                    outcome.tokens,
                    message_id,
                )
            )

        pool = ThreadPoolExecutor(
            max_workers=min(PARTICIPANT_CONCURRENCY, len(participants)),
            thread_name_prefix="acpx-discuss",
        )
        futures = {pool.submit(invoke, participant): participant for participant in participants}
        pending = set(futures)
        while pending:
            done, pending = wait(
                pending,
                timeout=max(0, deadline - self.clock()),
                return_when=FIRST_COMPLETED,
            )
            if not done:
                break
            for future in done:
                persist(future.result())
        for future in pending:
            participant = futures[future]
            future.cancel()
            persist(ParticipantOutcome(participant, "timeout", None, 0, None, None))
        pool.shutdown(wait=False, cancel_futures=True)
        return sorted(outcomes, key=lambda item: item.participant)

    def run(
        self,
        *,
        prompt: str,
        cwd: Path,
        task_id: str,
        correlation_id: str,
        idempotency_key: str,
        rounds: int = DEFAULT_ROUNDS,
        participants: Sequence[str] = PARTICIPANTS,
        models: Mapping[str, str] | None = None,
        efforts: Mapping[str, str] | None = None,
        source: str | None = None,
        initiator: str | None = None,
        reserved_conversation_id: str | None = None,
    ) -> dict[str, Any]:
        if os.environ.get(TRANSPORT_ENV, "off").strip().lower() != "active":
            raise AcpxDiscussionError("LU_ACPX_TRANSPORT=active is required by acp-discuss")
        if not prompt.strip():
            raise AcpxDiscussionError("prompt must be non-empty")
        normalized_participants = tuple(str(item).strip().lower() for item in participants)
        if (
            not MIN_PARTICIPANTS <= len(normalized_participants) <= MAX_PARTICIPANTS
            or len(set(normalized_participants)) != len(normalized_participants)
            or any(item not in SUPPORTED_PARTICIPANTS for item in normalized_participants)
        ):
            raise AcpxDiscussionError(
                f"participants must name {MIN_PARTICIPANTS} to {MAX_PARTICIPANTS} distinct "
                "enabled ACP seats: "
                + ", ".join(sorted(SUPPORTED_PARTICIPANTS))
            )
        if len(prompt.encode("utf-8")) * len(normalized_participants) > CONTENT_BUDGET_BYTES:
            raise AcpxDiscussionError("prompt exceeds the deterministic ACPX content budget")
        if rounds < 1 or rounds > MAX_ROUNDS:
            raise AcpxDiscussionError(f"rounds must be between 1 and {MAX_ROUNDS}")
        resolved_cwd = cwd.resolve()
        if classify_repo_path(resolved_cwd, cwd=resolved_cwd) not in {"dispatch_worktree", "other_worktree"}:
            raise AcpxDiscussionError("ACPX discussion cwd must be a registered worktree")
        task_id = _require_local_metadata_field("task_id", task_id, adapter_label="AcpxDiscuss")
        correlation_id = _require_local_metadata_field("correlation_id", correlation_id, adapter_label="AcpxDiscuss")
        idempotency_key = _require_local_metadata_field("idempotency_key", idempotency_key, adapter_label="AcpxDiscuss")
        if source is not None and initiator is not None and source != initiator:
            raise AcpxDiscussionError("source and initiator disagree; provenance must be unambiguous")
        transport_source = source if source is not None else initiator
        model_overrides = self._normalize_participant_overrides(
            "models",
            models,
            normalized_participants,
        )
        effort_overrides = self._normalize_participant_overrides(
            "efforts",
            efforts,
            normalized_participants,
        )
        for participant in normalized_participants:
            try:
                resolve_inter_agent_route(
                    participant,
                    model=model_overrides.get(participant),
                    effort=effort_overrides.get(participant),
                )
            except Exception as exc:
                raise AcpxDiscussionError(
                    f"invalid ACP participant selection for {participant!r}: {exc}"
                ) from exc
        idempotency_digest = _digest(idempotency_key)
        replay = self._terminal_replay(idempotency_digest)
        if replay is not None:
            return replay
        with _discussion_admission(self.store.root):
            # Every admitted conversation first terminalizes any expired
            # reservations left by crashed processes. Recovery never invokes
            # a provider and never retries the abandoned task.
            self.recover_expired_reservations()
            return self._run_admitted(
                prompt=prompt,
                cwd=resolved_cwd,
                task_id=task_id,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                idempotency_digest=idempotency_digest,
                rounds=rounds,
                participants=normalized_participants,
                models=model_overrides,
                efforts=effort_overrides,
                source=transport_source,
                reserved_conversation_id=reserved_conversation_id,
            )

    def _run_admitted(
        self,
        *,
        prompt: str,
        cwd: Path,
        task_id: str,
        correlation_id: str,
        idempotency_key: str,
        idempotency_digest: str,
        rounds: int,
        participants: tuple[str, ...],
        models: Mapping[str, str],
        efforts: Mapping[str, str],
        source: str | None,
        reserved_conversation_id: str | None,
    ) -> dict[str, Any]:
        started = self.clock()
        deadline = started + WHOLE_TIMEOUT_SECONDS
        deadline_at = (datetime.now(UTC) + timedelta(seconds=WHOLE_TIMEOUT_SECONDS)).strftime("%Y-%m-%dT%H:%M:%SZ")
        task_digest = _digest(task_id)
        correlation_digest = _digest(correlation_id)
        if reserved_conversation_id is None:
            conversation_id, replay = self._reserve(
                task_digest=task_digest,
                correlation_digest=correlation_digest,
                idempotency_digest=idempotency_digest,
                rounds=rounds,
                participants=participants,
                deadline_at=deadline_at,
            )
        else:
            conversation_id = self._adopt_authority_reservation(
                reserved_conversation_id,
                task_digest=task_digest,
                correlation_digest=correlation_digest,
                idempotency_digest=idempotency_digest,
                rounds=rounds,
                participants=participants,
                source=source,
            )
            replay = None
        if replay is not None:
            return replay
        if self.cancelled():
            return self._cancelled_payload(
                conversation_id,
                started=started,
                rounds_completed=0,
                token_used=0,
                outcomes=[],
            )

        self._append(conversation_id, event_type="STATE", state="INITIAL_FANOUT", transition=True)
        content_used = sum(len(prompt.encode("utf-8")) for _participant in participants)
        outcomes = self._call_wave(
            conversation_id=conversation_id, task_id=task_id, correlation_id=correlation_id,
            idempotency_key=idempotency_key, cwd=cwd, round_no=1,
            participants=participants,
            prompts={p: prompt for p in participants},
            deliveries={p: (("root", prompt, None),) for p in participants},
            state="INITIAL_FANOUT", deadline=deadline,
            source=source,
            models=models,
            efforts=efforts,
        )
        all_outcomes = list(outcomes)
        content_used += sum(len(item.response.encode("utf-8")) for item in outcomes if item.response)
        token_used = sum(item.tokens or 0 for item in outcomes)
        budget_exhausted = content_used > CONTENT_BUDGET_BYTES or token_used > TOKEN_BUDGET
        if budget_exhausted:
            self._append(
                conversation_id,
                event_type="BUDGET_EXHAUSTED",
                state="INITIAL_FANOUT",
                outcome="content" if content_used > CONTENT_BUDGET_BYTES else "tokens",
                metadata={"content_used": content_used, "token_used": token_used},
            )
        initial_state = "INITIAL_COMPLETE" if all(item.outcome == "ok" for item in outcomes) else "PARTIAL"
        self._append(conversation_id, event_type="STATE", state=initial_state, transition=True)
        rounds_completed = 1
        if self.cancelled():
            return self._cancelled_payload(
                conversation_id,
                started=started,
                rounds_completed=rounds_completed,
                token_used=token_used,
                outcomes=all_outcomes,
            )

        for round_no in range(2, rounds + 1):
            if self.clock() >= deadline or budget_exhausted:
                break
            self._append(conversation_id, event_type="STATE", state="CROSS_EXCHANGE", transition=True)
            prior = {item.participant: item.response for item in outcomes}
            prompts: dict[str, str] = {}
            deliveries: dict[str, Sequence[tuple[str, str, str | None]]] = {}
            prior_messages = {item.participant: item.message_id for item in outcomes}
            for participant in participants:
                peers = tuple(peer for peer in participants if peer != participant)
                peer_evidence = "\n\n".join(
                    f"{peer}'s prior response:\n{prior.get(peer) or '[unavailable]'}"
                    for peer in peers
                )
                prompts[participant] = (
                    f"Original task:\n{prompt}\n\n{peer_evidence}\n\n"
                    "Respond with your critique or refinement."
                )
                deliveries[participant] = tuple(
                    (
                        peer,
                        prior.get(peer) or "[unavailable]",
                        prior_messages.get(peer),
                    )
                    for peer in peers
                )
            outcomes = self._call_wave(
                conversation_id=conversation_id, task_id=task_id, correlation_id=correlation_id,
                idempotency_key=idempotency_key, cwd=cwd, round_no=round_no,
                participants=participants,
                prompts=prompts,
                deliveries=deliveries,
                state="CROSS_EXCHANGE", deadline=deadline,
                source=source,
                models=models,
                efforts=efforts,
            )
            all_outcomes.extend(outcomes)
            content_used += sum(len(value.encode("utf-8")) for value in prompts.values())
            content_used += sum(len(item.response.encode("utf-8")) for item in outcomes if item.response)
            token_used += sum(item.tokens or 0 for item in outcomes)
            budget_exhausted = content_used > CONTENT_BUDGET_BYTES or token_used > TOKEN_BUDGET
            if budget_exhausted:
                self._append(
                    conversation_id,
                    event_type="BUDGET_EXHAUSTED",
                    state="CROSS_EXCHANGE",
                    outcome="content" if content_used > CONTENT_BUDGET_BYTES else "tokens",
                    metadata={"content_used": content_used, "token_used": token_used},
                )
            rounds_completed = round_no
            next_state = "CROSS_EXCHANGE_COMPLETE" if all(item.outcome == "ok" for item in outcomes) else "PARTIAL"
            self._append(conversation_id, event_type="STATE", state=next_state, transition=True)
            if self.cancelled():
                return self._cancelled_payload(
                    conversation_id,
                    started=started,
                    rounds_completed=rounds_completed,
                    token_used=token_used,
                    outcomes=all_outcomes,
                )

        self._append(conversation_id, event_type="STATE", state="SYNTHESIS", transition=True)
        evidence = "\n\n".join(f"{item.participant} round response:\n{item.response}" for item in all_outcomes if item.response)
        synthesis: str | None = None
        synthesis_error: BaseException | None = None
        synthesis_result: Result | None = None
        deadline_exhausted = self.clock() >= deadline
        if deadline_exhausted:
            self._append(
                conversation_id,
                event_type="DEADLINE_EXCEEDED",
                state="SYNTHESIS",
                outcome="timeout",
            )
        if self.clock() < deadline and not budget_exhausted:
            synthesis_prompt = (
                "Synthesize only the available evidence for this task. Do not claim missing participants succeeded."
                f"\n\nTask:\n{prompt}\n\nEvidence:\n{evidence or '[none]'}"
            )
            synthesis_request = self._message(
                conversation_id,
                sender="root",
                recipient="codex",
                body=synthesis_prompt,
                reply_to=None,
                kind="request",
            )
            try:
                synthesis_result = self.synthesis_call(
                    "codex",
                    synthesis_prompt,
                    mode="read-only",
                    cwd=cwd,
                    task_id=task_id,
                    session_id=None,
                    entrypoint="acpx-discuss-synthesis",
                    hard_timeout=max(
                        1,
                        min(CALL_TIMEOUT_SECONDS, int(deadline - self.clock())),
                    ),
                    initiator=source,
                )
                if synthesis_result.ok:
                    synthesis = synthesis_result.response
            except BaseException as exc:
                synthesis_error = exc
        if synthesis is not None:
            synth_message = self._message(
                conversation_id,
                sender="codex",
                recipient="root",
                body=synthesis,
                reply_to=synthesis_request,
                kind="synthesis",
            )
            self._append(
                conversation_id,
                event_type="SYNTHESIS_TERMINAL",
                state="SYNTHESIS",
                sender="codex",
                recipient="root",
                outcome="ok",
                token_count=_safe_tokens(synthesis_result.usage_record.get("tokens")) if synthesis_result else None,
                message_id=synth_message,
            )
        else:
            self._append(
                conversation_id,
                event_type="SYNTHESIS_TERMINAL",
                state="SYNTHESIS",
                sender="codex",
                recipient="root",
                outcome="timeout" if deadline_exhausted else _result_outcome(synthesis_result, synthesis_error),
            )
        complete = (
            synthesis is not None
            and not budget_exhausted
            and all(item.outcome == "ok" for item in all_outcomes)
            and rounds_completed == rounds
        )
        final_state = "COMPLETE" if complete else "PARTIAL_COMPLETE"
        synthesis_tokens = _safe_tokens(synthesis_result.usage_record.get("tokens")) if synthesis_result else None
        tokens = token_used + (synthesis_tokens or 0)
        duration_ms = max(0, int((self.clock() - started) * 1000))
        participant_outcomes = [
            {
                "participant": item.participant,
                "outcome": item.outcome,
                "duration_ms": item.duration_ms,
                "tokens": item.tokens,
            }
            for item in all_outcomes
        ]
        self._append(
            conversation_id,
            event_type="STATE",
            state=final_state,
            duration_ms=duration_ms,
            token_count=tokens,
            metadata={
                "rounds_completed": rounds_completed,
                "duration_ms": duration_ms,
                "tokens": tokens,
            },
            transition=True,
        )
        return {
            "conversation_id": conversation_id,
            "state": final_state,
            "classification": "complete" if final_state == "COMPLETE" else "partial",
            "participant_outcomes": participant_outcomes,
            "rounds_completed": rounds_completed,
            "duration_ms": duration_ms,
            "tokens": tokens,
            "synthesis": synthesis,
            "duplicate_suppressed": False,
        }


def run_discussion(**kwargs: Any) -> dict[str, Any]:
    root_arg = kwargs.pop("root", None)
    root = Path(root_arg) if root_arg is not None else default_plane_root(repo_root=Path(kwargs["cwd"]))
    controller = AcpxDiscussionController(root=root)
    try:
        result = controller.run(**kwargs)
    finally:
        controller.close()
    if result.get("state") == "COMPLETE":
        try:
            # Local import avoids making ACP depend on the optional projection
            # during module initialization. The authoritative ACP terminal
            # commit has already completed; this callback is strictly
            # best-effort and cannot change the discussion result.
            from scripts.entire_context.reconcile import project_terminal_acp_receipt

            projection = project_terminal_acp_receipt(
                conversation_id=str(result["conversation_id"]),
                acp_root=root,
                repo_root=Path(kwargs["cwd"]),
            )
            if projection.get("outcome") not in {"promoted", "already_promoted"}:
                logger.warning(
                    "optional ACP context projection skipped: %s",
                    projection.get("reason") or projection.get("outcome") or "unknown",
                )
        except Exception as exc:
            logger.warning(
                "optional ACP context projection failed: %s", type(exc).__name__
            )
    return result


def recover_expired_discussions(*, root: Path) -> list[str]:
    """Explicit, lock-safe orphan recovery for later CLI/API integration."""
    controller = AcpxDiscussionController(root=root)
    try:
        with _discussion_admission(controller.store.root):
            return controller.recover_expired_reservations()
    finally:
        controller.close()


def verify_discussion_receipt(
    *,
    root: Path,
    conversation_id: str,
    require_replay: bool = False,
) -> dict[str, Any]:
    """Verify a durable ACP receipt using metadata-only, read-only storage."""
    if _CONVERSATION_ID.fullmatch(conversation_id) is None:
        raise AcpxDiscussionError("conversation_id must be a canonical ACP conversation ID")
    db_path = root.expanduser().resolve() / "comms.sqlite3"
    if not db_path.is_file():
        raise AcpxDiscussionNotFoundError("ACP conversation storage was not found")
    try:
        connection = sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """SELECT conversation_id, rounds_requested, participants_json, created_at
               FROM acp_conversations WHERE conversation_id = ?""",
            (conversation_id,),
        ).fetchone()
        if row is None:
            raise AcpxDiscussionNotFoundError(
                f"ACP conversation {conversation_id} was not found"
            )
        events = connection.execute(
            """SELECT sequence, event_type, state, sender, round, outcome,
                      duration_ms, token_count, created_at
               FROM acp_conversation_events
               WHERE conversation_id = ? ORDER BY sequence""",
            (conversation_id,),
        ).fetchall()
    except AcpxDiscussionNotFoundError:
        raise
    except sqlite3.Error as exc:
        raise AcpxDiscussionError(f"unable to verify ACP conversation storage: {exc}") from exc
    finally:
        if "connection" in locals():
            connection.close()

    if not events:
        raise AcpxDiscussionError("ACP conversation has no lifecycle events")
    try:
        participants = json.loads(str(row["participants_json"]))
    except (TypeError, ValueError, json.JSONDecodeError):
        participants = None
    participants_valid = (
        isinstance(participants, list)
        and MIN_PARTICIPANTS <= len(participants) <= MAX_PARTICIPANTS
        and all(isinstance(item, str) and item in SUPPORTED_PARTICIPANTS for item in participants)
        and len(set(participants)) == len(participants)
    )
    participant_names: tuple[str, ...] = tuple(participants) if participants_valid else ()
    rounds_value = row["rounds_requested"]
    rounds_requested = (
        rounds_value
        if isinstance(rounds_value, int)
        and not isinstance(rounds_value, bool)
        and 1 <= rounds_value <= MAX_ROUNDS
        else 0
    )
    created_at = _safe_receipt_timestamp(row["created_at"])
    terminal_calls = [event for event in events if event["event_type"] == "CALL_TERMINAL"]
    outcome_counts: dict[str, dict[str, int]] = {
        participant: {} for participant in participant_names
    }
    successful_legs: set[tuple[int, str]] = set()
    rounds_observed = 0
    for event in terminal_calls:
        participant = str(event["sender"] or "")
        round_no = event["round"]
        outcome = _safe_receipt_outcome(event["outcome"])
        if participant not in outcome_counts:
            continue
        outcome_counts[participant][outcome] = (
            outcome_counts[participant].get(outcome, 0) + 1
        )
        if isinstance(round_no, int) and not isinstance(round_no, bool) and round_no > 0:
            rounds_observed = max(rounds_observed, round_no)
            if outcome == "ok":
                successful_legs.add((round_no, participant))
    successful_rounds = sum(
        all((round_no, participant) in successful_legs for participant in participant_names)
        for round_no in range(1, rounds_requested + 1)
    )
    synthesis_events = [
        event for event in events if event["event_type"] == "SYNTHESIS_TERMINAL"
    ]
    synthesis_outcome = (
        _safe_receipt_outcome(synthesis_events[-1]["outcome"])
        if synthesis_events
        else "missing"
    )
    replay_count = sum(
        event["event_type"] == "DUPLICATE_SUPPRESSED" for event in events
    )
    final_event = events[-1]
    final_state = (
        str(final_event["state"])
        if final_event["state"] in _TERMINAL
        else "UNKNOWN"
    )
    updated_at = _safe_receipt_timestamp(final_event["created_at"])
    terminal_state_event = next(
        (
            event
            for event in reversed(events)
            if event["event_type"] == "STATE" and event["state"] in _TERMINAL
        ),
        None,
    )
    storage_metadata_valid = (
        rounds_requested > 0
        and created_at is not None
        and updated_at is not None
        and terminal_state_event is not None
    )
    terminal_complete = final_state == "COMPLETE"
    rounds_complete = successful_rounds == rounds_requested
    synthesis_complete = synthesis_outcome == "ok"
    replay_complete = replay_count > 0 or not require_replay
    checks = {
        "storage_metadata_valid": storage_metadata_valid,
        # Kept under the v1 receipt key for compatibility. It now means the
        # conversation used one exact, supported two-seat participant set.
        "fixed_participants": participants_valid,
        "terminal_complete": terminal_complete,
        "all_rounds_succeeded": rounds_complete,
        "synthesis_succeeded": synthesis_complete,
        "replay_observed": replay_complete,
    }
    reasons = [name for name, passed in checks.items() if not passed]
    duration_ms = terminal_state_event["duration_ms"] if terminal_state_event else None
    token_count = terminal_state_event["token_count"] if terminal_state_event else None
    return {
        "conversation_id": conversation_id,
        "verified": not reasons,
        "content_included": False,
        "state": final_state,
        "participants": list(participant_names),
        "rounds_requested": rounds_requested,
        "rounds_observed": rounds_observed,
        "successful_rounds": successful_rounds,
        "participant_outcomes": [
            {
                "participant": participant,
                "terminal_calls": sum(outcome_counts[participant].values()),
                "outcomes": outcome_counts[participant],
            }
            for participant in participant_names
        ],
        "synthesis_outcome": synthesis_outcome,
        "duplicate_suppressed_count": replay_count,
        "created_at": created_at,
        "updated_at": updated_at,
        "duration_ms": _safe_tokens(duration_ms),
        "token_count": _safe_tokens(token_count),
        "checks": checks,
        "reasons": reasons,
    }
