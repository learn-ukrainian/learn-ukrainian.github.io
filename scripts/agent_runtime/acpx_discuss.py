"""Bounded, durable ACPX Codex↔Grok discussion controller (#6078).

This is intentionally a small finite DAG, not a new message-plane router. It
accepts ``LU_ACPX_TRANSPORT=active`` only here; participants are the two fixed
direct-only ACPX seats, while the final synthesis is a fresh native Codex call.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, wait
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
    TRANSPORT_ENV,
    _require_local_metadata_field,
    active_discussion_scope,
)
from scripts.agent_runtime.errors import AgentStalledError, AgentTimeoutError, RateLimitedError
from scripts.agent_runtime.result import Result
from scripts.agent_runtime.runner import _invoke_direct_only, _invoke_native_once
from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.contracts import new_id
from scripts.fleet_comms.message_plane import default_plane_root
from scripts.guardrails.worktree_containment import classify_repo_path

PARTICIPANTS = ("codex", "grok")
MAX_ROUNDS = 3
DEFAULT_ROUNDS = 2
CALL_TIMEOUT_SECONDS = 300
WHOLE_TIMEOUT_SECONDS = 1200
TOKEN_BUDGET = 160_000
CONTENT_BUDGET_BYTES = 512 * 1024

_TERMINAL = frozenset({"COMPLETE", "PARTIAL_COMPLETE", "FAILED", "CANCELLED"})
_PARTICIPANT_SLOTS = threading.BoundedSemaphore(2)
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
    if not result.ok:
        return str(result.usage_record.get("outcome") or "error")
    return "ok"


def _safe_tokens(value: object) -> int | None:
    """Accept only explicit non-negative token totals, never context capacity."""
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


class AcpxDiscussionController:
    """Append-only controller; every DB transaction is committed before I/O."""

    def __init__(
        self,
        *,
        root: Path,
        participant_call: Callable[..., Result] = _invoke_direct_only,
        synthesis_call: Callable[..., Result] = _invoke_native_once,
        clock: Callable[[], float] = time.monotonic,
        cancelled: Callable[[], bool] | None = None,
    ) -> None:
        self.store = ArtifactStore(root=root)
        self.conn = self.store.connection
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
            if transition and current is not None and state not in _NEXT.get(current, set()):
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
        artifact = self.store.store_text(
            body,
            producer=f"acpx-discuss:{sender}",
            retention_class="acpx-discussion",
            logical_filename=f"{sender}-message.txt",
        )
        message_id = new_id("message")
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
        self.conn.commit()
        self.store.reference(message_id, artifact.artifact_id, relation="body")
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
                 json.dumps(PARTICIPANTS), _now(), deadline_at, TOKEN_BUDGET, CONTENT_BUDGET_BYTES),
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
                "SELECT conversation_id FROM acp_conversations WHERE idempotency_digest = ?",
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
            # A prior process reserved but did not finish. No retry is legal.
            self._append(existing, event_type="ORPHAN_RESERVATION", state="PARTIAL_COMPLETE", outcome="orphan", transition=True)
            return existing, self._replay(existing)
        return conversation_id, None

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
        deliveries: dict[str, tuple[str, str, str | None]],
        state: str,
        deadline: float,
    ) -> list[ParticipantOutcome]:
        reservations: dict[str, str] = {}
        request_messages: dict[str, str] = {}
        for participant in PARTICIPANTS:
            leg = _leg_digest(conversation_id, str(round_no), participant, _digest(prompts[participant]))
            reservations[participant] = leg
            sender, body, reply_to = deliveries[participant]
            request_messages[participant] = self._message(
                conversation_id,
                sender=sender,
                recipient=participant,
                body=body,
                reply_to=reply_to,
                kind="request" if sender == "root" else "reply",
            )
            self._append(
                conversation_id,
                event_type="CALL_RESERVED",
                state=state,
                sender=sender,
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
                with active_discussion_scope():
                    result = self.participant_call(
                        f"acpx-{participant}-shadow", prompts[participant], cwd=cwd, model=None,
                        task_id=task_id,
                        tool_config={"acpx_discussion": True, "target_agent": participant,
                                     "correlation_id": correlation_id, "idempotency_key": idempotency_key},
                        hard_timeout=max(1, min(CALL_TIMEOUT_SECONDS, int(deadline - self.clock()))),
                        entrypoint="acpx-discuss",
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
        pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="acpx-discuss")
        futures = {pool.submit(invoke, p): p for p in PARTICIPANTS}
        done, pending = wait(futures, timeout=max(0, deadline - self.clock()))
        for future in done:
            outcome = future.result()
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
            outcomes.append(ParticipantOutcome(outcome.participant, outcome.outcome, outcome.response, outcome.duration_ms, outcome.tokens, message_id))
        for future in pending:
            participant = futures[future]
            future.cancel()
            outcome = ParticipantOutcome(participant, "timeout", None, 0, None, None)
            self._append(
                conversation_id,
                event_type="CALL_TERMINAL",
                state=state,
                sender=participant,
                recipient="root",
                round_no=round_no,
                outcome="timeout",
                leg_key_digest=reservations[participant],
            )
            outcomes.append(outcome)
        pool.shutdown(wait=False, cancel_futures=True)
        return sorted(outcomes, key=lambda item: item.participant)

    def run(self, *, prompt: str, cwd: Path, task_id: str, correlation_id: str, idempotency_key: str, rounds: int = DEFAULT_ROUNDS) -> dict[str, Any]:
        if os.environ.get(TRANSPORT_ENV, "off").strip().lower() != "active":
            raise AcpxDiscussionError("LU_ACPX_TRANSPORT=active is required by acp-discuss")
        if not prompt.strip():
            raise AcpxDiscussionError("prompt must be non-empty")
        if len(prompt.encode("utf-8")) * len(PARTICIPANTS) > CONTENT_BUDGET_BYTES:
            raise AcpxDiscussionError("prompt exceeds the deterministic ACPX content budget")
        if rounds < 1 or rounds > MAX_ROUNDS:
            raise AcpxDiscussionError(f"rounds must be between 1 and {MAX_ROUNDS}")
        resolved_cwd = cwd.resolve()
        if classify_repo_path(resolved_cwd, cwd=resolved_cwd) not in {"dispatch_worktree", "other_worktree"}:
            raise AcpxDiscussionError("ACPX discussion cwd must be a registered worktree")
        task_id = _require_local_metadata_field("task_id", task_id, adapter_label="AcpxDiscuss")
        correlation_id = _require_local_metadata_field("correlation_id", correlation_id, adapter_label="AcpxDiscuss")
        idempotency_key = _require_local_metadata_field("idempotency_key", idempotency_key, adapter_label="AcpxDiscuss")
        started = self.clock()
        deadline = started + WHOLE_TIMEOUT_SECONDS
        deadline_at = (datetime.now(UTC) + timedelta(seconds=WHOLE_TIMEOUT_SECONDS)).strftime("%Y-%m-%dT%H:%M:%SZ")
        conversation_id, replay = self._reserve(task_digest=_digest(task_id), correlation_digest=_digest(correlation_id), idempotency_digest=_digest(idempotency_key), rounds=rounds, deadline_at=deadline_at)
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
        content_used = sum(len(prompt.encode("utf-8")) for _participant in PARTICIPANTS)
        outcomes = self._call_wave(
            conversation_id=conversation_id, task_id=task_id, correlation_id=correlation_id,
            idempotency_key=idempotency_key, cwd=resolved_cwd, round_no=1,
            prompts={p: prompt for p in PARTICIPANTS},
            deliveries={p: ("root", prompt, None) for p in PARTICIPANTS},
            state="INITIAL_FANOUT", deadline=deadline,
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
            prompts = {
                "codex": f"Original task:\n{prompt}\n\nGrok's prior response:\n{prior.get('grok') or '[unavailable]'}\n\nRespond with your critique or refinement.",
                "grok": f"Original task:\n{prompt}\n\nCodex's prior response:\n{prior.get('codex') or '[unavailable]'}\n\nRespond with your critique or refinement.",
            }
            prior_messages = {item.participant: item.message_id for item in outcomes}
            outcomes = self._call_wave(
                conversation_id=conversation_id, task_id=task_id, correlation_id=correlation_id,
                idempotency_key=idempotency_key, cwd=resolved_cwd, round_no=round_no,
                prompts=prompts,
                deliveries={
                    "codex": ("grok", prior.get("grok") or "[unavailable]", prior_messages.get("grok")),
                    "grok": ("codex", prior.get("codex") or "[unavailable]", prior_messages.get("codex")),
                },
                state="CROSS_EXCHANGE", deadline=deadline,
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
                synthesis_result = self.synthesis_call("codex", synthesis_prompt, mode="read-only", cwd=resolved_cwd, task_id=task_id, session_id=None, entrypoint="acpx-discuss-synthesis", hard_timeout=max(1, min(CALL_TIMEOUT_SECONDS, int(deadline - self.clock()))))
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
        return controller.run(**kwargs)
    finally:
        controller.close()
