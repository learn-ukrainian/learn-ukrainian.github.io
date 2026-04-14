"""Thread-coalesced inbox draining for the channel bridge.

Why this exists: Phase C.1 added leased deliveries, but draining them
one row at a time would fragment thread context, duplicate replies, and
throw away Claude's bridge-session cache warmth. Phase C.2 instead
claims one whole thread-group per invocation so the worker can emit one
reply, update one delivery cohort, and reuse the same Claude session for
that thread on the next wake. See #1192.
"""

from __future__ import annotations

import sys
import threading
import time
import uuid
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any

from batch_gemini_config import PRO_MODEL

try:
    from agent_runtime.errors import (
        AgentStalledError,
        AgentTimeoutError,
        AgentUnavailableError,
        RateLimitedError,
    )
    from agent_runtime.result import Result
    from agent_runtime.runner import invoke as runtime_invoke

    _HAS_RUNTIME = True
except ImportError:
    class RateLimitedError(Exception):
        """Fallback used when agent_runtime is not importable."""


    class AgentStalledError(Exception):
        """Fallback used when agent_runtime is not importable."""


    class AgentTimeoutError(Exception):
        """Fallback used when agent_runtime is not importable."""


    class AgentUnavailableError(Exception):
        """Fallback used when agent_runtime is not importable."""


    runtime_invoke = None
    Result = Any
    _HAS_RUNTIME = False

from . import _channels
from ._channels_watch import (
    emit_delivery_delivered,
    emit_delivery_failed,
    emit_heartbeat,
    emit_reply_complete,
    emit_reply_started,
)
from ._config import CLAUDE_CMD, REPO_ROOT
from ._db import get_db
from ._gemini import (
    _is_gemini_capacity_error,
    _next_gemini_model,
    _prefix_gemini_response,
    _uses_gemini_capacity_cascade,
)
from ._gemini_session_link import (
    GeminiSessionRecovery,
    find_session_recovery,
    format_recovered_reply,
)
from ._orphan_recovery import RecoveryCandidate, RecoveryResult, recover_orphan_commit
from ._reconcile import reconcile_deliveries

_DEFAULT_HARD_TIMEOUT_SECONDS = 900
_DEFAULT_STALL_TIMEOUT_SECONDS = 600
_DEFAULT_GLOBAL_RETRY_SECONDS = 120
_HEARTBEAT_INTERVAL_SECONDS = 60
_MIN_HARD_TIMEOUT_SECONDS = 60
_MAX_HARD_TIMEOUT_SECONDS = 3600
_SESSION_COLUMNS = {
    "claude": "claude_session_id",
    "gemini": "gemini_session_id",
    "codex": "codex_session_id",
}


@dataclass(frozen=True)
class InboxRunSummary:
    """Compact counters so callers can verify drain behavior in tests.

    The worker is intentionally retry-heavy and non-interactive. A small,
    immutable summary makes it obvious whether a wake delivered work,
    terminal-failed a thread, or aborted early because the provider was
    unavailable and the lease was released for a later retry.
    """

    agent: str
    threads_processed: int = 0
    deliveries_claimed: int = 0
    deliveries_delivered: int = 0
    deliveries_failed: int = 0
    deliveries_released: int = 0
    replies_posted: int = 0
    aborted: bool = False
    abort_reason: str | None = None


@dataclass(frozen=True)
class _ClaimedDelivery:
    delivery_id: str
    message_id: str
    thread_id: str
    channel: str
    to_agent: str
    to_model: str | None
    deadline_seconds: int | None
    from_agent: str
    body: str
    round_index: int
    created_at: str
    mode: str = "read-only"


@dataclass(frozen=True)
class _ClaimedThread:
    channel: str
    thread_id: str
    deliveries: tuple[_ClaimedDelivery, ...]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _iso_after(value: str, *, seconds: int) -> str:
    return (datetime.fromisoformat(value) + timedelta(seconds=seconds)).isoformat()


def _validate_agent(agent: str) -> None:
    if agent not in _channels.VALID_AGENTS:
        raise ValueError(
            f"Unknown agent '{agent}'. Expected one of {_channels.VALID_AGENTS}."
        )


def _validate_hard_timeout_seconds(value: int, *, field_name: str) -> None:
    if not _MIN_HARD_TIMEOUT_SECONDS <= value <= _MAX_HARD_TIMEOUT_SECONDS:
        raise ValueError(
            f"{field_name} must be between "
            f"{_MIN_HARD_TIMEOUT_SECONDS} and {_MAX_HARD_TIMEOUT_SECONDS} seconds"
        )


def _thread_session_key(channel: str, thread_id: str) -> str:
    return f"bridge:{channel}:{thread_id}"


def _get_session_id(task_id: str, agent: str) -> str | None:
    column = _SESSION_COLUMNS[agent]
    conn = get_db()
    try:
        row = conn.execute(
            f"SELECT {column} FROM sessions WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        return str(row[column]) if row and row[column] else None
    finally:
        conn.close()


def _set_session_id(task_id: str, agent: str, session_id: str) -> None:
    column = _SESSION_COLUMNS[agent]
    now = _now_iso()
    conn = get_db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(
            "SELECT task_id FROM sessions WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        if existing:
            conn.execute(
                f"UPDATE sessions SET {column} = ?, updated_at = ? WHERE task_id = ?",
                (session_id, now, task_id),
            )
        else:
            conn.execute(
                f"INSERT INTO sessions (task_id, {column}, created_at, updated_at) "
                f"VALUES (?, ?, ?, ?)",
                (task_id, session_id, now, now),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _claim_next_thread(
    agent: str,
    *,
    max_attempts: int,
    lease_seconds: int,
    delivery_budget: int | None,
    now: str,
) -> tuple[_ClaimedThread | None, bool]:
    """Claim one whole thread so #1192 never invokes per delivery row."""

    lease_until = _iso_after(now, seconds=lease_seconds)
    conn = get_db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        candidate = conn.execute(
            """
            SELECT cm.thread_id, cm.channel
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE d.to_agent = ?
              AND d.attempt_count < ?
              AND (d.retry_after IS NULL OR d.retry_after <= ?)
              AND (
                    d.status = 'pending'
                    OR (d.status = 'processing' AND d.lease_until <= ?)
              )
              AND NOT EXISTS (
                    SELECT 1
                    FROM deliveries d2
                    JOIN channel_messages cm2 ON cm2.message_id = d2.message_id
                    WHERE d2.to_agent = d.to_agent
                      AND cm2.thread_id = cm.thread_id
                      AND d2.status = 'processing'
                      AND d2.lease_until > ?
              )
            ORDER BY cm.created_at ASC, d.delivery_id ASC
            LIMIT 1
            """,
            (agent, max_attempts, now, now, now),
        ).fetchone()
        if not candidate:
            conn.commit()
            return None, False

        thread_id = str(candidate["thread_id"])
        channel = str(candidate["channel"])
        count_row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE d.to_agent = ?
              AND cm.thread_id = ?
              AND d.attempt_count < ?
              AND (d.retry_after IS NULL OR d.retry_after <= ?)
              AND (
                    d.status = 'pending'
                    OR (d.status = 'processing' AND d.lease_until <= ?)
              )
            """,
            (agent, thread_id, max_attempts, now, now),
        ).fetchone()
        claim_count = int(count_row["count"]) if count_row else 0
        if claim_count == 0:
            conn.commit()
            return None, False
        if delivery_budget is not None and claim_count > delivery_budget:
            conn.commit()
            return None, True

        conn.execute(
            """
            UPDATE deliveries
            SET status = 'processing',
                lease_until = ?,
                attempt_count = attempt_count + 1
            WHERE delivery_id IN (
                SELECT d.delivery_id
                FROM deliveries d
                JOIN channel_messages cm ON cm.message_id = d.message_id
                WHERE d.to_agent = ?
                  AND cm.thread_id = ?
                  AND d.attempt_count < ?
                  AND (d.retry_after IS NULL OR d.retry_after <= ?)
                  AND (
                        d.status = 'pending'
                        OR (d.status = 'processing' AND d.lease_until <= ?)
                  )
            )
            """,
            (lease_until, agent, thread_id, max_attempts, now, now),
        )

        rows = conn.execute(
            """
            SELECT d.delivery_id, d.message_id, d.to_agent, d.to_model,
                   d.deadline_seconds,
                   d.mode,
                   cm.thread_id, cm.channel, cm.from_agent, cm.body,
                   cm.round_index, cm.created_at
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE d.to_agent = ?
              AND cm.thread_id = ?
              AND d.status = 'processing'
              AND d.lease_until = ?
            ORDER BY cm.created_at ASC, d.delivery_id ASC
            """,
            (agent, thread_id, lease_until),
        ).fetchall()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    deliveries = tuple(
        _ClaimedDelivery(
            delivery_id=str(row["delivery_id"]),
            message_id=str(row["message_id"]),
            thread_id=str(row["thread_id"]),
            channel=str(row["channel"]),
            to_agent=str(row["to_agent"]),
            to_model=str(row["to_model"]) if row["to_model"] else None,
            deadline_seconds=int(row["deadline_seconds"]) if row["deadline_seconds"] else None,
            from_agent=str(row["from_agent"]),
            body=str(row["body"]),
            round_index=int(row["round_index"]),
            created_at=str(row["created_at"]),
            mode=str(row["mode"]) if row["mode"] else "read-only",
        )
        for row in rows
    )
    if not deliveries:
        return None, False
    return _ClaimedThread(channel=channel, thread_id=thread_id, deliveries=deliveries), False


def _update_claimed_status(
    claimed: _ClaimedThread,
    *,
    status: str,
    error_text: str | None = None,
    error_kind: str | None = None,
    retry_after: str | None = None,
    delivered_at: str | None = None,
    to_model: str | None = None,
) -> None:
    delivery_ids = [delivery.delivery_id for delivery in claimed.deliveries]
    placeholders = ", ".join("?" for _ in delivery_ids)
    to_model_sql = ", to_model = ?" if to_model is not None else ""
    conn = get_db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        if status == "delivered":
            params: list[Any] = [delivered_at or _now_iso(), error_text]
            if to_model is not None:
                params.append(to_model)
            params.extend(delivery_ids)
            conn.execute(
                f"""
                UPDATE deliveries
                SET status = 'delivered',
                    delivered_at = ?,
                    error = ?,
                    lease_until = NULL,
                    retry_after = NULL,
                    last_error_kind = NULL
                    {to_model_sql}
                WHERE delivery_id IN ({placeholders})
                """,
                params,
            )
        elif status == "failed":
            params = [error_text or "", error_kind]
            if to_model is not None:
                params.append(to_model)
            params.extend(delivery_ids)
            conn.execute(
                f"""
                UPDATE deliveries
                SET status = 'failed',
                    error = ?,
                    lease_until = NULL,
                    retry_after = NULL,
                    last_error_kind = ?
                    {to_model_sql}
                WHERE delivery_id IN ({placeholders})
                """,
                params,
            )
        else:
            params = [error_text or "", retry_after, error_kind]
            if to_model is not None:
                params.append(to_model)
            params.extend(delivery_ids)
            conn.execute(
                f"""
                UPDATE deliveries
                SET status = 'pending',
                    error = ?,
                    lease_until = NULL,
                    retry_after = ?,
                    last_error_kind = ?
                    {to_model_sql}
                WHERE delivery_id IN ({placeholders})
                """,
                params,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _render_messages(messages: list[dict[str, object]]) -> str:
    return "\n".join(
        (
            f"[{str(message['created_at'])[:19]}] "
            f"{message['from_agent']} (round {message['round_index']}): "
            f"{message['body']}"
        )
        for message in messages
    )


def _build_thread_prompt(
    agent: str,
    claimed: _ClaimedThread,
    *,
    has_session: bool,
) -> str:
    thread_messages = _channels.read(claimed.channel, thread_id=claimed.thread_id)
    if not thread_messages:
        raise ValueError(
            f"thread '{claimed.thread_id}' in channel '{claimed.channel}' has no messages"
        )

    claimed_ids = {delivery.message_id for delivery in claimed.deliveries}
    unseen = [message for message in thread_messages if message["message_id"] in claimed_ids]
    if not unseen:
        raise ValueError(
            f"claimed deliveries for thread '{claimed.thread_id}' did not map to messages"
        )

    latest_message = unseen[-1]
    if agent == "claude" and has_session:
        sections = [
            f"Continue the existing bridge session for channel #{claimed.channel}.",
            "Respond with one plain-text reply as the target agent.",
            "Address the latest unseen message directly.",
            "--- unseen messages ---",
            _render_messages(unseen),
        ]
        return "\n\n".join(section for section in sections if section.strip())

    context = _channels.load_channel_context(claimed.channel)["body"].strip()
    root = thread_messages[0]
    # NIT from Gemini c2-review r1: when a thread JUST started, the root
    # message is also in unseen[]. Don't render it twice in the cold prompt.
    root_in_unseen = root["message_id"] in claimed_ids
    prior_messages = [
        message
        for message in thread_messages[1:]
        if message["message_id"] not in claimed_ids
    ]
    sections = [
        context,
        f"You are {agent} replying on the #{claimed.channel} channel bridge.",
        # Skip the root section entirely if root is also in unseen — the
        # unseen block below will render it once and only once.
        ("--- root question ---\n" + _render_messages([root])) if not root_in_unseen else "",
        (
            "--- thread so far ---\n" + _render_messages(prior_messages)
            if prior_messages
            else ""
        ),
        "--- unseen messages to answer now ---",
        _render_messages(unseen),
        (
            "Reply once, in plain text, with the message you want posted as a "
            f"channel reply to {latest_message['message_id']}."
        ),
    ]
    return "\n\n".join(section for section in sections if section.strip())


def _resolve_model(claimed: _ClaimedThread) -> str | None:
    models = {delivery.to_model for delivery in claimed.deliveries if delivery.to_model}
    if len(models) > 1:
        raise ValueError(
            f"thread '{claimed.thread_id}' has conflicting to_model values: {sorted(models)}"
        )
    return next(iter(models), None)


def _resolve_mode(claimed: _ClaimedThread) -> str:
    """Resolve execution mode from delivery metadata.

    If any delivery in the thread requests a write mode, use the most
    permissive one. Priority: danger > workspace-write > read-only.
    """
    modes = {delivery.mode for delivery in claimed.deliveries if delivery.mode}
    if "danger" in modes:
        return "danger"
    if "workspace-write" in modes:
        return "workspace-write"
    return "read-only"


def _resolve_hard_timeout(claimed: _ClaimedThread, *, worker_hard_timeout: int) -> int:
    deadlines = [
        delivery.deadline_seconds
        for delivery in claimed.deliveries
        if delivery.deadline_seconds is not None
    ]
    return max(worker_hard_timeout, *(deadlines or [0]))


def _maybe_recover_orphan_commit(
    agent: str,
    claimed: _ClaimedThread,
) -> RecoveryResult:
    if agent != "codex" or _resolve_mode(claimed) != "workspace-write":
        return RecoveryResult(commit_sha=None, reason="not-eligible")

    thread_messages = _channels.read(claimed.channel, thread_id=claimed.thread_id)
    recovery = recover_orphan_commit(
        RecoveryCandidate(
            delivery_id=claimed.deliveries[-1].delivery_id,
            thread_id=claimed.thread_id,
            latest_message_body=claimed.deliveries[-1].body,
            thread_bodies=tuple(str(message["body"]) for message in thread_messages),
        )
    )
    if recovery.reason not in {None, "clean-tree"}:
        print(
            "orphan recovery skipped "
            f"for delivery {claimed.deliveries[-1].delivery_id}: "
            f"{recovery.reason} ({', '.join(recovery.changed_files)})",
            file=sys.stderr,
        )
    return recovery


def _thread_has_agent_reply_after_claimed_message(
    claimed: _ClaimedThread,
    *,
    agent: str,
) -> bool:
    """Avoid double-posting a recovered reply into an already-answered thread."""
    thread_messages = _channels.read(claimed.channel, thread_id=claimed.thread_id)
    after_claimed = False
    latest_claimed_id = claimed.deliveries[-1].message_id
    for message in thread_messages:
        if after_claimed and message["from_agent"] == agent:
            return True
        if message["message_id"] == latest_claimed_id:
            after_claimed = True
    return False


def _link_gemini_session(
    claimed: _ClaimedThread,
    *,
    started_at: datetime | None,
) -> GeminiSessionRecovery | None:
    if started_at is None:
        return None
    task_id = _thread_session_key(claimed.channel, claimed.thread_id)
    recovery = find_session_recovery(
        delivery_brief=claimed.deliveries[-1].body,
        started_at=started_at,
        session_id=_get_session_id(task_id, "gemini"),
        project_name=REPO_ROOT.name,
    )
    if recovery and recovery.session_id:
        _set_session_id(task_id, "gemini", recovery.session_id)
    return recovery


def _maybe_post_recovered_gemini_reply(
    claimed: _ClaimedThread,
    *,
    started_at: datetime | None,
    fallback_model: str,
    recovery: GeminiSessionRecovery | None = None,
) -> tuple[str, str] | None:
    recovery = recovery or _link_gemini_session(claimed, started_at=started_at)
    if recovery is None:
        return None
    if _thread_has_agent_reply_after_claimed_message(claimed, agent="gemini"):
        return None

    reply_body = format_recovered_reply(recovery, fallback_model=fallback_model)
    try:
        _channels.post(
            claimed.channel,
            "gemini",
            reply_body,
            parent_id=claimed.deliveries[-1].message_id,
            from_model=recovery.model or fallback_model,
            auto_snapshot=False,
        )
    except Exception:
        return None
    return reply_body, (recovery.model or fallback_model)


def _mark_claimed_delivered(
    claimed: _ClaimedThread,
    *,
    agent: str,
    reply_body: str,
    model: str,
    error_text: str | None = None,
) -> None:
    emit_reply_complete(
        claimed.thread_id,
        agent=agent,
        chars=len(reply_body),
    )
    _update_claimed_status(
        claimed,
        status="delivered",
        error_text=error_text,
        delivered_at=_now_iso(),
        to_model=model,
    )
    for delivery in claimed.deliveries:
        emit_delivery_delivered(
            claimed.thread_id,
            delivery_id=delivery.delivery_id,
        )


def _invoke_thread(
    agent: str,
    claimed: _ClaimedThread,
    *,
    worker_hard_timeout: int,
) -> Any:
    task_id = _thread_session_key(claimed.channel, claimed.thread_id)
    existing_session = _get_session_id(task_id, agent) if agent == "claude" else None
    has_session = existing_session is not None
    prompt = _build_thread_prompt(agent, claimed, has_session=has_session)
    session_id = existing_session
    session_to_store: str | None = None
    tool_config: dict[str, object] | None = None
    requested_model = _resolve_model(claimed)
    if agent == "gemini" and requested_model is None:
        requested_model = PRO_MODEL

    if agent == "claude":
        tool_config = {"cmd_prefix": CLAUDE_CMD, "is_new_session": False}
        if session_id is None:
            session_id = str(uuid.uuid4())
            session_to_store = session_id
            tool_config["is_new_session"] = True

    hard_timeout = _resolve_hard_timeout(
        claimed,
        worker_hard_timeout=worker_hard_timeout,
    )

    emit_reply_started(claimed.thread_id, agent=agent, model=requested_model)
    stop_heartbeats = threading.Event()
    heartbeat_start = time.perf_counter()
    heartbeat_delivery_ids = tuple(
        delivery.delivery_id for delivery in claimed.deliveries
    )

    def _heartbeat_loop() -> None:
        while not stop_heartbeats.wait(_HEARTBEAT_INTERVAL_SECONDS):
            elapsed_s = int(time.perf_counter() - heartbeat_start)
            for delivery_id in heartbeat_delivery_ids:
                emit_heartbeat(
                    claimed.thread_id,
                    delivery_id=delivery_id,
                    elapsed_s=elapsed_s,
                )

    heartbeat_thread = threading.Thread(
        target=_heartbeat_loop,
        name=f"ab-heartbeat-{claimed.thread_id[:8]}",
        daemon=True,
    )
    heartbeat_thread.start()
    try:
        if agent == "gemini":
            result = _invoke_gemini_thread_with_fallback(
                claimed,
                prompt=prompt,
                requested_model=requested_model,
                task_id=task_id,
                hard_timeout=hard_timeout,
            )
        else:
            result = runtime_invoke(
                agent,
                prompt,
                mode=_resolve_mode(claimed),
                cwd=REPO_ROOT,
                model=requested_model,
                task_id=task_id,
                session_id=session_id if agent == "claude" else None,
                tool_config=tool_config,
                entrypoint="bridge",
                hard_timeout=hard_timeout,
                stall_timeout=_DEFAULT_STALL_TIMEOUT_SECONDS,
            )
    finally:
        stop_heartbeats.set()
        heartbeat_thread.join(timeout=1.0)

    if agent == "claude" and result.ok:
        persisted_session = result.session_id or session_to_store or existing_session
        if persisted_session:
            _set_session_id(task_id, agent, persisted_session)

    return result


def _invoke_gemini_thread_with_fallback(
    claimed: _ClaimedThread,
    *,
    prompt: str,
    requested_model: str | None,
    task_id: str,
    hard_timeout: int,
) -> Result:
    mode = _resolve_mode(claimed)
    effective_requested_model = requested_model or PRO_MODEL
    current_model = effective_requested_model

    while True:
        try:
            result = runtime_invoke(
                "gemini",
                prompt,
                mode=mode,
                cwd=REPO_ROOT,
                model=current_model,
                task_id=task_id,
                session_id=None,
                tool_config=None,
                entrypoint="bridge",
                hard_timeout=hard_timeout,
                stall_timeout=_DEFAULT_STALL_TIMEOUT_SECONDS,
            )
        except RateLimitedError as exc:
            next_model = _next_gemini_model(current_model)
            if next_model is not None:
                current_model = next_model
                continue
            return Result(
                ok=False,
                agent="gemini",
                model=current_model,
                mode=mode,
                response="",
                stderr_excerpt=str(exc),
                duration_s=0.0,
                session_id=None,
                rate_limited=True,
                stalled=False,
                returncode=None,
                usage_record={},
            )

        if not result.ok and _uses_gemini_capacity_cascade(current_model):
            next_model = (
                _next_gemini_model(current_model)
                if _is_gemini_capacity_error(result.stderr_excerpt or "")
                else None
            )
            if next_model is not None:
                current_model = next_model
                continue

        if result.ok:
            response = _prefix_gemini_response(
                result.response.strip(),
                requested_model=effective_requested_model,
                final_model=result.model,
            )
            return replace(result, response=response, model=result.model)
        return result


def run_inbox(
    agent: str,
    *,
    max_messages: int | None = None,
    until_idle: bool = True,
    stop_after_seconds: int | None = None,
    hard_timeout: int = _DEFAULT_HARD_TIMEOUT_SECONDS,
) -> InboxRunSummary:
    """Drain one agent inbox without splitting a live thread across calls.

    The worker stops on global provider failures because those are not
    specific to one delivery row; releasing the current lease with a
    retry_after preserves the thread cohort for the next wake instead of
    falsely terminal-failing work that would likely succeed once the
    provider recovers. See #1192.
    """
    if not _HAS_RUNTIME or runtime_invoke is None:
        raise RuntimeError(
            "agent_runtime is required for inbox draining. "
            "Install it or add scripts/ to PYTHONPATH."
        )

    _validate_agent(agent)
    if max_messages is not None and max_messages <= 0:
        raise ValueError("max_messages must be > 0 when provided")
    if stop_after_seconds is not None and stop_after_seconds <= 0:
        raise ValueError("stop_after_seconds must be > 0 when provided")
    _validate_hard_timeout_seconds(hard_timeout, field_name="hard_timeout")

    claimed_total = 0
    delivered_total = 0
    failed_total = 0
    released_total = 0
    replies_total = 0
    threads_total = 0
    abort_reason: str | None = None
    start_time = time.monotonic()

    while True:
        if (
            stop_after_seconds is not None
            and threads_total > 0
            and time.monotonic() - start_time >= stop_after_seconds
        ):
            break

        remaining_budget = (
            None if max_messages is None else max_messages - claimed_total
        )
        if remaining_budget is not None and remaining_budget <= 0:
            break

        # Soft-cap: never enforce delivery_budget on the FIRST claim of
        # a run. Otherwise an oldest-thread larger than max_messages
        # would permanently deadlock the queue — every wake would bail
        # without processing anything. Subsequent claims still enforce
        # the budget so a single run can't blow past max_messages by
        # multiple threads. (Gemini issue-1192-c2-review r1 BLOCKER.)
        hard_budget = remaining_budget if claimed_total > 0 else None

        claimed, _blocked_by_budget = _claim_next_thread(
            agent,
            max_attempts=_channels.DEFAULT_MAX_DELIVERY_ATTEMPTS,
            lease_seconds=_channels.DEFAULT_DELIVERY_LEASE_SECONDS,
            delivery_budget=hard_budget,
            now=_now_iso(),
        )
        if claimed is None:
            break

        claimed_total += len(claimed.deliveries)
        gemini_started_at = datetime.now(UTC) if agent == "gemini" else None
        fallback_model = _resolve_model(claimed) or PRO_MODEL
        try:
            result = _invoke_thread(
                agent,
                claimed,
                worker_hard_timeout=hard_timeout,
            )
        # Note: transient global failures (rate limit, timeout, unavailable)
        # release the lease back to pending with a retry_after, but DO NOT
        # decrement attempt_count. The agent WAS attempted (it just hit a
        # provider-side fault), so the attempt is real. Eventually a
        # genuinely-down provider will exhaust DEFAULT_MAX_DELIVERY_ATTEMPTS
        # and the deliveries will reach terminal `failed` — that's the
        # right behavior, not infinite retry.
        # (Gemini issue-1192-c2-review r1 BLOCKER caught the original
        # decrement_attempts=True path which net-zero'd attempts.)
        except RateLimitedError as exc:
            recovered = None
            if agent == "gemini":
                recovered = _maybe_post_recovered_gemini_reply(
                    claimed,
                    started_at=gemini_started_at,
                    fallback_model=fallback_model,
                )
            if recovered is not None:
                reply_body, recovered_model = recovered
                _mark_claimed_delivered(
                    claimed,
                    agent=agent,
                    reply_body=reply_body,
                    model=recovered_model,
                    error_text="session-recovery",
                )
                delivered_total += len(claimed.deliveries)
                replies_total += 1
                threads_total += 1
                if not until_idle:
                    break
                continue
            _update_claimed_status(
                claimed,
                status="pending",
                error_text=str(exc),
                error_kind="rate_limited",
                retry_after=_iso_after(
                    _now_iso(),
                    seconds=_channels.DEFAULT_RATE_LIMIT_RETRY_SECONDS,
                ),
            )
            for delivery in claimed.deliveries:
                emit_delivery_failed(
                    claimed.thread_id,
                    delivery_id=delivery.delivery_id,
                    error_kind="rate_limited",
                )
            released_total += len(claimed.deliveries)
            abort_reason = str(exc)
            break
        except (AgentStalledError, AgentTimeoutError) as exc:
            recovered = None
            if agent == "gemini":
                recovered = _maybe_post_recovered_gemini_reply(
                    claimed,
                    started_at=gemini_started_at,
                    fallback_model=fallback_model,
                )
            if recovered is not None:
                reply_body, recovered_model = recovered
                _mark_claimed_delivered(
                    claimed,
                    agent=agent,
                    reply_body=reply_body,
                    model=recovered_model,
                    error_text="session-recovery",
                )
                delivered_total += len(claimed.deliveries)
                replies_total += 1
                threads_total += 1
                if not until_idle:
                    break
                continue
            recovery = _maybe_recover_orphan_commit(agent, claimed)
            if recovery.commit_sha:
                _update_claimed_status(
                    claimed,
                    status="delivered",
                    error_text=f"timeout-recovered:{recovery.commit_sha}",
                    delivered_at=_now_iso(),
                )
                for delivery in claimed.deliveries:
                    emit_delivery_delivered(
                        claimed.thread_id,
                        delivery_id=delivery.delivery_id,
                    )
                delivered_total += len(claimed.deliveries)
                threads_total += 1
                if not until_idle:
                    break
                continue
            _update_claimed_status(
                claimed,
                status="pending",
                error_text=str(exc),
                error_kind="timeout",
                retry_after=_iso_after(
                    _now_iso(),
                    seconds=_DEFAULT_GLOBAL_RETRY_SECONDS,
                ),
            )
            for delivery in claimed.deliveries:
                emit_delivery_failed(
                    claimed.thread_id,
                    delivery_id=delivery.delivery_id,
                    error_kind="timeout",
                )
            released_total += len(claimed.deliveries)
            abort_reason = str(exc)
            break
        except AgentUnavailableError as exc:
            _update_claimed_status(
                claimed,
                status="pending",
                error_text=str(exc),
                error_kind="unavailable",
                retry_after=_iso_after(
                    _now_iso(),
                    seconds=_DEFAULT_GLOBAL_RETRY_SECONDS,
                ),
            )
            for delivery in claimed.deliveries:
                emit_delivery_failed(
                    claimed.thread_id,
                    delivery_id=delivery.delivery_id,
                    error_kind="unavailable",
                )
            released_total += len(claimed.deliveries)
            abort_reason = str(exc)
            break
        except Exception as exc:
            _update_claimed_status(
                claimed,
                status="failed",
                error_text=f"{type(exc).__name__}: {exc}",
                error_kind="tool_error",
            )
            for delivery in claimed.deliveries:
                emit_delivery_failed(
                    claimed.thread_id,
                    delivery_id=delivery.delivery_id,
                    error_kind="tool_error",
                )
            failed_total += len(claimed.deliveries)
            threads_total += 1
            if not until_idle:
                break
            continue

        linked_recovery = (
            _link_gemini_session(claimed, started_at=gemini_started_at)
            if agent == "gemini"
            else None
        )
        reply_body = result.response.strip()
        if not result.ok or not reply_body:
            recovered = None
            if agent == "gemini":
                recovered = _maybe_post_recovered_gemini_reply(
                    claimed,
                    started_at=gemini_started_at,
                    fallback_model=fallback_model,
                    recovery=linked_recovery,
                )
            if recovered is not None:
                reply_body, recovered_model = recovered
                _mark_claimed_delivered(
                    claimed,
                    agent=agent,
                    reply_body=reply_body,
                    model=recovered_model,
                    error_text="session-recovery",
                )
                delivered_total += len(claimed.deliveries)
                replies_total += 1
                threads_total += 1
                if not until_idle:
                    break
                continue
            if agent == "gemini" and result.rate_limited:
                _update_claimed_status(
                    claimed,
                    status="pending",
                    error_text=result.stderr_excerpt or "rate limited",
                    error_kind="rate_limited",
                    retry_after=_iso_after(
                        _now_iso(),
                        seconds=_channels.DEFAULT_RATE_LIMIT_RETRY_SECONDS,
                    ),
                    to_model=result.model,
                )
                for delivery in claimed.deliveries:
                    emit_delivery_failed(
                        claimed.thread_id,
                        delivery_id=delivery.delivery_id,
                        error_kind="rate_limited",
                    )
                released_total += len(claimed.deliveries)
                abort_reason = result.stderr_excerpt or "rate limited"
                break
            _update_claimed_status(
                claimed,
                status="failed",
                error_text=result.stderr_excerpt or "agent returned no reply",
                error_kind="parse_error",
                to_model=result.model,
            )
            for delivery in claimed.deliveries:
                emit_delivery_failed(
                    claimed.thread_id,
                    delivery_id=delivery.delivery_id,
                    error_kind="parse_error",
                )
            failed_total += len(claimed.deliveries)
            threads_total += 1
            if not until_idle:
                break
            continue

        recovery = _maybe_recover_orphan_commit(agent, claimed)

        try:
            # Reply linkage lives in channel_messages.parent_id, not the
            # deliveries table — we don't need the returned message_id.
            _channels.post(
                claimed.channel,
                agent,
                reply_body,
                parent_id=claimed.deliveries[-1].message_id,
                from_model=result.model,
                auto_snapshot=False,
            )
        except Exception as exc:
            _update_claimed_status(
                claimed,
                status="failed",
                error_text=f"reply post failed: {type(exc).__name__}: {exc}",
                error_kind="tool_error",
            )
            for delivery in claimed.deliveries:
                emit_delivery_failed(
                    claimed.thread_id,
                    delivery_id=delivery.delivery_id,
                    error_kind="tool_error",
                )
            failed_total += len(claimed.deliveries)
            threads_total += 1
            if not until_idle:
                break
            continue

        # Reply linkage lives in channel_messages.parent_id, not in the
        # deliveries table — no separate linkage step needed here.
        _mark_claimed_delivered(
            claimed,
            agent=agent,
            reply_body=reply_body,
            model=result.model,
            error_text=(
                f"timeout-recovered:{recovery.commit_sha}"
                if recovery.commit_sha
                else None
            ),
        )
        delivered_total += len(claimed.deliveries)
        replies_total += 1
        threads_total += 1

        if not until_idle:
            break

    reconcile_deliveries()

    return InboxRunSummary(
        agent=agent,
        threads_processed=threads_total,
        deliveries_claimed=claimed_total,
        deliveries_delivered=delivered_total,
        deliveries_failed=failed_total,
        deliveries_released=released_total,
        replies_posted=replies_total,
        aborted=abort_reason is not None,
        abort_reason=abort_reason,
    )
