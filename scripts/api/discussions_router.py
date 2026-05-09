"""Active discussion API for the Monitor dashboard (#1820)."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from .config import MESSAGE_DB
from .resilience import connect_sqlite

router = APIRouter(tags=["discussions"])


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _latest_agent_states(messages: list[sqlite3.Row], last_round: int) -> dict[str, str]:
    states: dict[str, str] = {}
    for row in messages:
        agent = row["from_agent"]
        if not agent:
            continue
        round_index = int(row["round_index"] or 0)
        if round_index <= 0:
            continue
        body = str(row["body"] or "").strip()
        if round_index < last_round:
            states[agent] = "pending"
            continue
        states[agent] = "agreed" if body.upper().endswith("[AGREE]") else "done"
    return states


def _discussion_status(messages: list[sqlite3.Row], last_message_at: datetime, last_round: int) -> str:
    bodies = "\n".join(str(row["body"] or "") for row in messages).upper()
    if "[TIMEOUT]" in bodies:
        return "timed_out"
    if datetime.now(UTC) - last_message_at > timedelta(minutes=30):
        return "timed_out"
    states = _latest_agent_states(messages, last_round)
    if states and all(state == "agreed" for state in states.values()):
        return "converged"
    return "running"


def collect_active_discussions(limit: int = 25) -> dict[str, Any]:
    """Return recent ab-discuss-style threads grouped from channel messages."""
    if not MESSAGE_DB.exists():
        return {"discussions": [], "count": 0, "error": "Broker DB not found"}

    conn = connect_sqlite(f"file:{MESSAGE_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT message_id, channel, thread_id, round_index, from_agent, body, created_at
            FROM channel_messages
            WHERE thread_id IS NOT NULL AND thread_id != ''
            ORDER BY created_at ASC
            """
        ).fetchall()
    finally:
        conn.close()

    grouped: dict[tuple[str, str], list[sqlite3.Row]] = {}
    for row in rows:
        grouped.setdefault((row["channel"], row["thread_id"]), []).append(row)

    discussions = []
    for (channel, thread_id), messages in grouped.items():
        last_round = max(int(row["round_index"] or 0) for row in messages)
        if last_round <= 0:
            continue
        started_at = _parse_ts(messages[0]["created_at"])
        last_message_at = _parse_ts(messages[-1]["created_at"])
        if started_at is None or last_message_at is None:
            continue
        agents = sorted({row["from_agent"] for row in messages if row["from_agent"]})
        status = _discussion_status(messages, last_message_at, last_round)
        discussions.append(
            {
                "thread_id": thread_id,
                "channel": channel,
                "started_at": started_at.isoformat().replace("+00:00", "Z"),
                "agents": agents,
                "last_round": last_round,
                "last_message_at": last_message_at.isoformat().replace("+00:00", "Z"),
                "status": status,
                "round_count": len({int(row["round_index"] or 0) for row in messages if int(row["round_index"] or 0) > 0}),
                "message_count": len(messages),
            }
        )

    discussions.sort(key=lambda item: item["last_message_at"], reverse=True)
    return {"discussions": discussions[:limit], "count": min(len(discussions), limit)}


@router.get("/active")
async def active_discussions(limit: int = Query(25, ge=1, le=100)):
    """Recent discussion threads with running/converged/timed_out status."""
    try:
        return collect_active_discussions(limit=limit)
    except sqlite3.Error as exc:
        return JSONResponse(status_code=500, content={"error": "broker_query_failed", "detail": str(exc)})
