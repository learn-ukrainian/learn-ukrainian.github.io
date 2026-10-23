"""Checked-in lane addresses and bounded metadata-only inbox reads (#10800).

The authority database owns the installed registry. This manifest supplies its
five approved lanes; launcher selectors and slot inference never create aliases.
"""

from __future__ import annotations

import re
import shlex
import sqlite3
import time
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.lib.readonly_sqlite import open_readonly

# area, stream, explicit aliases. `data` is the mailbox for open-model-data.
LANES = (
    (
        "infra",
        "epic:6943",
        ("infra", "claude-infra", "codex-infra", "gemini-infra", "grok-infra", "kimi-infra", "cursor-infra"),
    ),
    ("epics", "epic:10453", ("epics", "claude-epics", "codex-epics", "cto", "claude-cto", "codex-cto")),
    (
        "devops",
        "epic:5703",
        (
            "devops",
            "claude-devops",
            "codex-devops",
            "gemini-devops",
            "grok-devops",
            "kimi-devops",
            "cursor-devops",
            "muse-devops",
        ),
    ),
    (
        "data",
        "epic:6321",
        (
            "open-model-data",
            "claude-open-model-data",
            "codex-open-model-data",
            "gemini-open-model-data",
            "grok-open-model-data",
            "codex-data",
        ),
    ),
    (
        "atlas",
        "epic:4387",
        ("atlas", "claude-atlas", "codex-atlas", "gemini-atlas", "grok-atlas", "kimi-atlas", "cursor-atlas"),
    ),
)
LANE_STREAMS = {f"lane:{name}": stream for name, stream, _aliases in LANES}
ALIASES = {alias: f"lane:{name}" for name, _stream, aliases in LANES for alias in aliases}
READ_TIMEOUT_SECONDS = 0.5
BUSY_TIMEOUT_MS = 200
DRAIN = '.venv/bin/python -m scripts.fleet_comms deliveries claim --recipient {recipient} --worker-id "$SESSION_STREAM_SESSION_ID"'


class LaneMailboxError(RuntimeError):
    """A typed refusal that contains no private store details."""


def lane_address(recipient: str) -> str | None:
    """Resolve only explicit aliases and lane names; retain unrelated recipients."""
    if recipient.startswith("lane:"):
        if recipient not in LANE_STREAMS:
            raise LaneMailboxError("lane_unknown_recipient")
        return recipient
    return ALIASES.get(recipient)


def verify_registry(conn: Any) -> None:
    """Reject missing, partial, or drifted installed mappings, never infer aliases."""
    try:
        from scripts.fleet_comms.migrations import verify_applied_migrations

        if verify_applied_migrations(conn) < 11:
            raise LaneMailboxError("lane_registry_stale")
        lanes = dict(conn.execute("SELECT recipient, stream_id FROM lane_mailboxes").fetchall())
        aliases = dict(conn.execute("SELECT alias, recipient FROM lane_mailbox_aliases").fetchall())
    except Exception as exc:
        raise LaneMailboxError("lane_registry_stale") from exc
    if lanes != LANE_STREAMS or aliases != ALIASES:
        raise LaneMailboxError("lane_registry_stale")


def resolve_lane(conn: Any, recipient: str) -> str | None:
    """Validate installed alias entries as well as the checked-in lane names."""
    lane = lane_address(recipient)
    try:
        row = conn.execute("SELECT recipient FROM lane_mailbox_aliases WHERE alias=?", (recipient,)).fetchone()
    except sqlite3.Error as exc:
        if lane:
            raise LaneMailboxError("lane_registry_stale") from exc
        return None
    if lane or row is not None:
        verify_registry(conn)
    return lane


def recipients_for(recipient: str) -> tuple[str, ...]:
    lane = lane_address(recipient)
    if lane is None:
        return (recipient,)
    return (lane, *(alias for alias, target in ALIASES.items() if target == lane))


def recipient_filter(column: str, recipient: str, *, placeholder: str = "?") -> tuple[str, tuple[str, ...]]:
    """SQL fragment for a trusted internal column and parameterized read addresses."""
    try:
        names = recipients_for(recipient)
    except LaneMailboxError:
        names = (recipient,)
    return f"{column} IN ({','.join(placeholder for _ in names)})", names


def unknown_inbox(recipient: str) -> dict[str, Any]:
    try:
        address = lane_address(recipient) or recipient
    except LaneMailboxError:
        address = recipient
    return {
        "probe": "unknown",
        "count": None,
        "oldest_age_seconds": None,
        "drain_command": DRAIN.format(recipient=shlex.quote(address)),
        "by_correlation": None,
        "content_included": False,
    }


def read_inbox(path: Path, recipient: str, *, limit: int = 5) -> dict[str, Any]:
    """One bounded read-only snapshot, including residual alias rows, never bodies.

    SQLite busy timeout bounds lock waits; the progress handler bounds query
    work. A slow completed query is UNKNOWN too, never a false empty inbox.
    """
    result = unknown_inbox(recipient)
    deadline = time.monotonic() + READ_TIMEOUT_SECONDS
    try:
        from scripts.control_plane.storage import StoreId, assert_component_supported

        assert_component_supported(StoreId.FLEET_COMMS, "authority_service")
        if not path.is_file():
            return result
        with closing(open_readonly(path, timeout=BUSY_TIMEOUT_MS / 1000)) as conn:
            conn.row_factory = sqlite3.Row
            conn.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
            conn.execute("BEGIN")
            from scripts.fleet_comms.migrations import verify_applied_migrations

            verify_applied_migrations(conn)
            resolve_lane(conn, recipient)
            clause, names = recipient_filter("d.recipient", recipient)
            now = datetime.now(UTC)
            where = f"""{clause} AND d.state IN ('queued', 'running')
                AND (d.deadline_at IS NULL OR d.deadline_at > ?)
                AND (d.state = 'queued' OR NOT EXISTS (SELECT 1 FROM authority_idempotency i
                    WHERE i.namespace = 'supervisory-consumption:' || d.delivery_id
                      AND i.idempotency_key = CAST(d.fence_token AS TEXT)))"""
            params = (*names, now.strftime("%Y-%m-%dT%H:%M:%SZ"))
            # Preserve uncertainty if required receiver-observation schema is absent.
            conn.execute("SELECT delivery_id, state FROM authority_wake_receipts LIMIT 0")
            row = conn.execute(
                f"SELECT COUNT(*), MIN(d.created_at) FROM authority_deliveries d WHERE {where}", params
            ).fetchone()
            count, oldest = row
            age = None
            if count:
                when = datetime.fromisoformat(oldest.replace("Z", "+00:00"))
                if when.tzinfo is None:
                    return result
                age = max(0, int((now - when).total_seconds()))
            rows = conn.execute(
                f"SELECT d.delivery_id, d.message_id, d.recipient, d.state, d.attempt_count, d.created_at, d.updated_at FROM authority_deliveries d WHERE {where} ORDER BY d.created_at, d.delivery_id LIMIT ?",
                (*params, limit),
            ).fetchall()
            groups = conn.execute(
                f"SELECT d.pr_number, d.task_id, COUNT(*) AS count FROM authority_deliveries d WHERE {where} GROUP BY d.pr_number, d.task_id",
                params,
            ).fetchall()
            if time.monotonic() >= deadline:
                return result
            if any(
                not isinstance(row["message_id"], str)
                or not re.fullmatch(r"(?:[a-z][a-z0-9-]*_|legacy-message-)[0-9a-f]{32}", row["message_id"])
                for row in rows
            ):
                return result
            return {
                **result,
                "probe": "ok",
                "count": count,
                "oldest_age_seconds": age,
                "ids": [row["message_id"] for row in rows],
                "deliveries": [dict(row) for row in rows],
                "by_correlation": [dict(row) for row in groups],
            }
    except Exception:
        # Boundary errors can include SQL, paths or data. Expose only UNKNOWN.
        return result


def migration_plan(conn: Any) -> tuple[dict[str, Any], list[tuple[Any, str, str | None]]]:
    """Plan only queued alias moves. Terminal history never counts as a move."""
    verify_registry(conn)
    rows = conn.execute(
        "SELECT delivery_id, message_id, recipient, state FROM authority_deliveries ORDER BY created_at, delivery_id"
    ).fetchall()
    groups: dict[tuple[str, str], list[Any]] = {}
    report = {
        lane: {"queued_before": 0, "planned_moves": 0, "running_held": 0, "dead_lettered_held": 0, "collisions": 0}
        for lane in LANE_STREAMS
    }
    unmapped: dict[str, int] = {}
    for row in rows:
        recipient = row["recipient"]
        lane = ALIASES.get(recipient) or (recipient if recipient in LANE_STREAMS else None)
        if lane is None:
            if row["state"] in {"queued", "running"}:
                unmapped[recipient] = unmapped.get(recipient, 0) + 1
            continue
        groups.setdefault((row["message_id"], lane), []).append(row)
        if row["state"] == "queued":
            report[lane]["queued_before"] += 1
        if recipient in ALIASES:
            if row["state"] == "queued":
                report[lane]["planned_moves"] += 1
            elif row["state"] == "running":
                report[lane]["running_held"] += 1
            elif row["state"] == "dead_lettered":
                report[lane]["dead_lettered_held"] += 1
    moves: list[tuple[Any, str, str | None]] = []
    for (_mid, lane), group in groups.items():
        candidates = [row for row in group if row["recipient"] in ALIASES and row["state"] == "queued"]
        acknowledged = next((row for row in group if row["state"] == "acknowledged"), None)
        canonical = next((row for row in group if row["recipient"] == lane), None)
        survivor = acknowledged or canonical or (candidates[0] if candidates else None)
        for row in candidates:
            duplicate = survivor if survivor["delivery_id"] != row["delivery_id"] else None
            if duplicate:
                report[lane]["collisions"] += 1
            moves.append((row, lane, duplicate["delivery_id"] if duplicate else None))
    return {"lanes": report, "unmapped": unmapped, "content_included": False}, moves


def apply_alias_moves(conn: Any, *, now: str) -> dict[str, Any]:
    """Apply the plan inside the caller's authority write transaction."""
    report, moves = migration_plan(conn)
    if any(row["running_held"] for row in report["lanes"].values()):
        raise LaneMailboxError("lane_alias_running")
    moved = dead_lettered = 0
    for row, lane, duplicate in moves:
        did = row["delivery_id"]
        action = "moved"
        if duplicate:
            state = conn.execute("SELECT state FROM authority_deliveries WHERE delivery_id=?", (duplicate,)).fetchone()[
                0
            ]
            action = "lane_duplicate_of_acknowledged" if state == "acknowledged" else "lane_duplicate_queued"
            conn.execute(
                "UPDATE authority_deliveries SET state='dead_lettered', updated_at=?, completed_at=? WHERE delivery_id=?",
                (now, now, did),
            )
            from scripts.fleet_comms.contracts import new_id

            conn.execute(
                "INSERT INTO authority_dead_letters(dead_letter_id, delivery_id, reason_code, created_at) VALUES (?,?,?,?)",
                (new_id("authority-dead-letter"), did, action, now),
            )
            dead_lettered += 1
            report["lanes"][lane]["dead_lettered"] = report["lanes"][lane].get("dead_lettered", 0) + 1
        else:
            conn.execute(
                "UPDATE authority_deliveries SET recipient=?, updated_at=? WHERE delivery_id=?", (lane, now, did)
            )
            moved += 1
            report["lanes"][lane]["moved"] = report["lanes"][lane].get("moved", 0) + 1
        conn.execute(
            "INSERT INTO lane_mailbox_moves(delivery_id, old_recipient, lane_recipient, action, duplicate_of, moved_at) VALUES (?,?,?,?,?,?)",
            (did, row["recipient"], lane, action, duplicate, now),
        )
    for lane_report in report["lanes"].values():
        lane_report.setdefault("moved", 0)
        lane_report.setdefault("dead_lettered", 0)
    return {**report, "moved": moved, "dead_lettered": dead_lettered, "applied": True}


def correlation_counts(path: Path) -> dict[str, Any]:
    """Metadata-only queued delivery groups for bottleneck diagnostics."""
    deadline = time.monotonic() + READ_TIMEOUT_SECONDS
    try:
        from scripts.control_plane.storage import StoreId, assert_component_supported

        assert_component_supported(StoreId.FLEET_COMMS, "authority_service")
        with closing(open_readonly(path, timeout=BUSY_TIMEOUT_MS / 1000)) as conn:
            conn.row_factory = sqlite3.Row
            conn.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
            rows = conn.execute(
                "SELECT pr_number, task_id, COUNT(*) AS count FROM authority_deliveries WHERE state='queued' GROUP BY pr_number, task_id"
            ).fetchall()
            if time.monotonic() >= deadline:
                raise ValueError("slow")
            return {"probe": "ok", "groups": [dict(row) for row in rows], "content_included": False}
    except Exception:
        return {"probe": "unknown", "groups": None, "content_included": False}
