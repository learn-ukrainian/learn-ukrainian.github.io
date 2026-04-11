"""Channel bridge — Phase B.1 (#1190).

This module provides the storage-layer primitives for the channel-based
agent bridge. It is INTENTIONALLY decoupled from the legacy 1:1 message
bus in ``_messaging.py`` — both subsystems share the same SQLite DB
(``_db.py``) but operate on disjoint tables, so ``ab ask-claude`` keeps
working throughout the migration.

See issue #1190 for the design rationale and acceptance criteria.

## Key design choices (post-Gemini critique)

- **Three tables, not one.** ``channels`` holds static topic metadata;
  ``channel_messages`` holds immutable prose (posts and replies, both
  linked by ``parent_id``); ``deliveries`` is an outbound state machine
  (pending → dispatched → delivered → failed) per (message, recipient).
  Replies are NEW ``channel_messages`` rows with ``parent_id`` pointing
  at the original — they do NOT update the delivery row.

- **BEGIN IMMEDIATE for fanout inserts.** Writing 1 message + N delivery
  rows needs a write lock upfront to avoid SQLITE_BUSY under concurrency.
  ``busy_timeout=5000`` then queues concurrent writers gracefully.

- **Context snapshots are SHA256 hex, not counters.** Bumping a manual
  integer after every ``context.md`` edit invites human error. Hashing
  the file contents at post-time is automatic, deterministic, and
  survives git pulls across machines.

- **Monitor state is captured per message.** When we POST, we fetch
  ``GET /api/state/summary`` (Monitor API, see ``docs/MONITOR-API.md``)
  and store the JSON blob verbatim in ``monitor_state_snapshot``. This
  gives deterministic replay of the project state that the agent saw.

## Module API surface

The functions in this module are deliberately small and imperative.
They return plain dicts / lists of dicts, not ORM objects — the channel
bridge is a message log, not a domain model.

High-level:
    create_channel(name, *, description, include, subscribers)
    post(channel, from_agent, body, *, to_agents, parent_id, ...)
    read(channel, *, tail, thread_id)
    list_channels()
    get_channel(name)
    mark_delivery(delivery_id, status, *, error, delivered_at)
    context_sha256(path)
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ._db import get_db

# ── Constants ──────────────────────────────────────────────────────────

VALID_AGENTS = ("claude", "gemini", "codex", "user")
VALID_KINDS = ("post", "reply", "system", "fanout_start", "fanout_end")
VALID_DELIVERY_STATUSES = ("pending", "dispatched", "delivered", "failed")

# Default channel that every other channel includes unless overridden.
# Holds project-wide pinned context that agents need on every message
# (coding conventions, current sprint summary, etc.).
SHARED_CHANNEL = "shared"


# ── Helpers ────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _new_id() -> str:
    """Generate a new opaque ID for messages/deliveries/etc."""
    return uuid.uuid4().hex


def context_sha256(path: Path) -> str:
    """Compute sha256 hex of a context.md file.

    Returns empty string if the file doesn't exist or is unreadable —
    we'd rather log an empty rev than block a post on a missing
    context file. The absence itself is meaningful signal during debug.
    """
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, FileNotFoundError):
        return ""


def _validate_agent(agent: str) -> None:
    if agent not in VALID_AGENTS:
        raise ValueError(
            f"Unknown agent '{agent}'. Expected one of {VALID_AGENTS}."
        )


def _validate_kind(kind: str) -> None:
    if kind not in VALID_KINDS:
        raise ValueError(
            f"Unknown kind '{kind}'. Expected one of {VALID_KINDS}."
        )


# ── Channel management ────────────────────────────────────────────────


def create_channel(
    name: str,
    *,
    description: str = "",
    include: list[str] | None = None,
    subscribers: list[str] | None = None,
    exist_ok: bool = True,
) -> dict[str, Any]:
    """Create a new channel (topic).

    ``include`` lists other channel names whose context should be
    auto-prepended to posts in this channel (commonly ``["shared"]``).
    ``subscribers`` lists which agents can be default recipients of
    broadcast posts; it does NOT restrict who can post.

    Raises ValueError on duplicate if ``exist_ok=False``. Otherwise,
    this is an upsert — already-existing channels are left untouched
    and the current row is returned.
    """
    if not name or not name.strip():
        raise ValueError("channel name cannot be empty")
    if name != name.strip().lower().replace(" ", "-"):
        raise ValueError(
            f"channel name must be lowercase-kebab-case; got '{name}'"
        )

    include = include or []
    subscribers = subscribers or []
    for agent in subscribers:
        _validate_agent(agent)

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT name, description, include, subscribers, created_at "
            "FROM channels WHERE name = ?",
            (name,),
        ).fetchone()
        if existing:
            if not exist_ok:
                raise ValueError(f"channel '{name}' already exists")
            return _row_to_channel(existing)

        conn.execute(
            "INSERT INTO channels (name, created_at, description, include, "
            "subscribers, context_sha256) VALUES (?, ?, ?, ?, ?, ?)",
            (
                name,
                _now_iso(),
                description,
                ",".join(include),
                ",".join(subscribers),
                "",
            ),
        )
        conn.commit()
        return {
            "name": name,
            "description": description,
            "include": include,
            "subscribers": subscribers,
            "created_at": _now_iso(),
        }
    finally:
        conn.close()


def get_channel(name: str) -> dict[str, Any] | None:
    """Fetch a channel by name, or return None if it doesn't exist."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, description, include, subscribers, created_at "
            "FROM channels WHERE name = ?",
            (name,),
        ).fetchone()
        return _row_to_channel(row) if row else None
    finally:
        conn.close()


def list_channels() -> list[dict[str, Any]]:
    """Return all channels, ordered by creation time (oldest first)."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT name, description, include, subscribers, created_at "
            "FROM channels ORDER BY created_at ASC"
        ).fetchall()
        return [_row_to_channel(r) for r in rows]
    finally:
        conn.close()


def _row_to_channel(row: tuple) -> dict[str, Any]:
    return {
        "name": row[0],
        "description": row[1],
        "include": [s for s in row[2].split(",") if s],
        "subscribers": [s for s in row[3].split(",") if s],
        "created_at": row[4],
    }


# ── Posting ───────────────────────────────────────────────────────────


def post(
    channel: str,
    from_agent: str,
    body: str,
    *,
    to_agents: list[str] | None = None,
    parent_id: str | None = None,
    correlation_id: str | None = None,
    kind: str = "post",
    from_model: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
    context_rev_shared: str = "",
    context_rev_channel: str = "",
    monitor_state_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new channel_messages row + N deliveries rows atomically.

    Returns ``{"message_id": ..., "thread_id": ..., "delivery_ids": [...]}``.

    Atomicity is enforced by ``BEGIN IMMEDIATE`` — under concurrent posts,
    the second caller queues on the 5-second ``busy_timeout`` rather than
    racing. This matches Gemini's #1 correction in the B.1 design review.

    ``to_agents`` may be an empty list; in that case no deliveries are
    created and the message is a pure "log entry" (useful for
    system/audit posts). ``parent_id`` links a reply to its origin;
    the reply's ``thread_id`` is inherited from the parent.
    """
    _validate_agent(from_agent)
    _validate_kind(kind)
    for agent in to_agents or []:
        _validate_agent(agent)

    message_id = _new_id()
    created_at = _now_iso()
    attachments_json = json.dumps(attachments) if attachments else None
    monitor_json = (
        json.dumps(monitor_state_snapshot) if monitor_state_snapshot else None
    )

    conn = get_db()
    try:
        # Verify the channel exists before inserting — the FK would catch
        # it, but an explicit check gives a better error message.
        ch = conn.execute(
            "SELECT name FROM channels WHERE name = ?", (channel,)
        ).fetchone()
        if not ch:
            raise ValueError(f"channel '{channel}' does not exist")

        # Resolve thread_id: inherit from parent if replying, else
        # self-reference (Gemini's correction — avoids NULL edge cases).
        if parent_id:
            parent = conn.execute(
                "SELECT thread_id, round_index FROM channel_messages WHERE message_id = ?",
                (parent_id,),
            ).fetchone()
            if not parent:
                raise ValueError(f"parent message '{parent_id}' not found")
            thread_id = parent[0]
            round_index = parent[1] + 1
        else:
            thread_id = message_id
            round_index = 0

        # BEGIN IMMEDIATE: acquire the write lock upfront so concurrent
        # fanouts queue on busy_timeout instead of deadlocking mid-txn.
        conn.execute("BEGIN IMMEDIATE")

        conn.execute(
            """
            INSERT INTO channel_messages (
                message_id, channel, thread_id, parent_id, correlation_id,
                round_index, from_agent, from_model, kind, body,
                attachments, context_rev_shared, context_rev_channel,
                monitor_state_snapshot, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id, channel, thread_id, parent_id, correlation_id,
                round_index, from_agent, from_model, kind, body,
                attachments_json, context_rev_shared, context_rev_channel,
                monitor_json, created_at,
            ),
        )

        delivery_ids = []
        for agent in to_agents or []:
            dlv_id = _new_id()
            delivery_ids.append(dlv_id)
            conn.execute(
                """
                INSERT INTO deliveries (
                    delivery_id, message_id, to_agent, status
                ) VALUES (?, ?, ?, 'pending')
                """,
                (dlv_id, message_id, agent),
            )

        conn.commit()

        return {
            "message_id": message_id,
            "thread_id": thread_id,
            "parent_id": parent_id,
            "correlation_id": correlation_id,
            "round_index": round_index,
            "delivery_ids": delivery_ids,
            "created_at": created_at,
        }
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Reading ───────────────────────────────────────────────────────────


def read(
    channel: str,
    *,
    tail: int = 20,
    thread_id: str | None = None,
) -> list[dict[str, Any]]:
    """Read messages from a channel.

    If ``thread_id`` is given, returns all messages in that thread
    (ordered by round_index, then created_at). Otherwise returns the
    last ``tail`` messages in the channel ordered oldest→newest.
    """
    conn = get_db()
    try:
        if thread_id:
            rows = conn.execute(
                """
                SELECT message_id, channel, thread_id, parent_id, correlation_id,
                       round_index, from_agent, from_model, kind, body,
                       attachments, context_rev_shared, context_rev_channel,
                       monitor_state_snapshot, created_at
                FROM channel_messages
                WHERE channel = ? AND thread_id = ?
                ORDER BY round_index ASC, created_at ASC
                """,
                (channel, thread_id),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT message_id, channel, thread_id, parent_id, correlation_id,
                       round_index, from_agent, from_model, kind, body,
                       attachments, context_rev_shared, context_rev_channel,
                       monitor_state_snapshot, created_at
                FROM (
                    SELECT * FROM channel_messages
                    WHERE channel = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                )
                ORDER BY created_at ASC
                """,
                (channel, tail),
            ).fetchall()
        return [_row_to_message(r) for r in rows]
    finally:
        conn.close()


def _row_to_message(row: tuple) -> dict[str, Any]:
    return {
        "message_id": row[0],
        "channel": row[1],
        "thread_id": row[2],
        "parent_id": row[3],
        "correlation_id": row[4],
        "round_index": row[5],
        "from_agent": row[6],
        "from_model": row[7],
        "kind": row[8],
        "body": row[9],
        "attachments": json.loads(row[10]) if row[10] else None,
        "context_rev_shared": row[11],
        "context_rev_channel": row[12],
        "monitor_state_snapshot": (
            json.loads(row[13]) if row[13] else None
        ),
        "created_at": row[14],
    }


# ── Delivery state ────────────────────────────────────────────────────


def mark_delivery(
    delivery_id: str,
    status: str,
    *,
    error: str | None = None,
    delivered_at: str | None = None,
) -> None:
    """Update a delivery's status (outbound state machine)."""
    if status not in VALID_DELIVERY_STATUSES:
        raise ValueError(
            f"invalid delivery status '{status}'. "
            f"Expected one of {VALID_DELIVERY_STATUSES}."
        )

    now = _now_iso()
    conn = get_db()
    try:
        if status == "dispatched":
            conn.execute(
                "UPDATE deliveries SET status=?, dispatched_at=?, error=? WHERE delivery_id=?",
                (status, now, error, delivery_id),
            )
        elif status == "delivered":
            conn.execute(
                "UPDATE deliveries SET status=?, delivered_at=?, error=? WHERE delivery_id=?",
                (status, delivered_at or now, error, delivery_id),
            )
        elif status == "failed":
            conn.execute(
                "UPDATE deliveries SET status=?, error=? WHERE delivery_id=?",
                (status, error, delivery_id),
            )
        else:  # pending — should not usually be explicit, but allow
            conn.execute(
                "UPDATE deliveries SET status=?, error=? WHERE delivery_id=?",
                (status, error, delivery_id),
            )
        conn.commit()
    finally:
        conn.close()


def deliveries_for_message(message_id: str) -> list[dict[str, Any]]:
    """Return all deliveries for a message (pending or otherwise)."""
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT delivery_id, message_id, to_agent, to_model, status,
                   dispatched_at, delivered_at, error
            FROM deliveries
            WHERE message_id = ?
            ORDER BY delivery_id
            """,
            (message_id,),
        ).fetchall()
        return [
            {
                "delivery_id": r[0],
                "message_id": r[1],
                "to_agent": r[2],
                "to_model": r[3],
                "status": r[4],
                "dispatched_at": r[5],
                "delivered_at": r[6],
                "error": r[7],
            }
            for r in rows
        ]
    finally:
        conn.close()


def pending_deliveries_for(agent: str) -> list[dict[str, Any]]:
    """Return pending deliveries for an agent, oldest-first.

    Uses the compound index ``idx_deliveries_agent_queue`` on
    ``(to_agent, status, dispatched_at)``.
    """
    _validate_agent(agent)
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT d.delivery_id, d.message_id, d.to_agent, d.to_model,
                   d.status, d.dispatched_at, d.delivered_at, d.error,
                   cm.body, cm.from_agent, cm.channel, cm.created_at
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE d.to_agent = ? AND d.status = 'pending'
            ORDER BY cm.created_at ASC
            """,
            (agent,),
        ).fetchall()
        return [
            {
                "delivery_id": r[0],
                "message_id": r[1],
                "to_agent": r[2],
                "to_model": r[3],
                "status": r[4],
                "dispatched_at": r[5],
                "delivered_at": r[6],
                "error": r[7],
                "body": r[8],
                "from_agent": r[9],
                "channel": r[10],
                "created_at": r[11],
            }
            for r in rows
        ]
    finally:
        conn.close()
