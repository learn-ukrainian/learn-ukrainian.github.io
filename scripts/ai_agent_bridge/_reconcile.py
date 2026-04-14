"""Normalize stuck channel deliveries after timeouts and retries."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from . import _channels
from ._broker import _is_task_locked
from ._config import REPO_ROOT
from ._db import get_db

_DEFAULT_HARD_TIMEOUT_SECONDS = 900


@dataclass(frozen=True)
class ReconcileChange:
    delivery_id: str
    from_status: str
    to_status: str
    error: str


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _task_id(channel: str, thread_id: str) -> str:
    return f"bridge:{channel}:{thread_id}"


def _has_active_worker(row: Any) -> bool:
    return _is_task_locked(
        str(row["to_agent"]),
        _task_id(str(row["channel"]), str(row["thread_id"])),
    )


def _find_timeout_recovery_commit(delivery_id: str) -> str | None:
    commands = (
        ["log", "main", f"-S{delivery_id}", "--format=%H%x00%B%x1e"],
        [
            "log",
            "main",
            "--format=%H%x00%B%x1e",
            "--grep=^\\[TIMEOUT RECOVERY\\]",
        ],
    )
    for args in commands:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0 or not result.stdout.strip():
            continue
        chunks = [chunk for chunk in result.stdout.split("\x1e") if chunk.strip()]
        for chunk in chunks:
            sha, _, body = chunk.partition("\x00")
            if "[TIMEOUT RECOVERY]" in body and delivery_id in body:
                return sha.strip()
    return None


def _planned_change(row: Any, *, now: datetime) -> ReconcileChange | None:
    status = str(row["status"])
    delivery_id = str(row["delivery_id"])

    if str(row["mode"]) == "workspace-write" and status in {"pending", "processing"}:
        commit_sha = _find_timeout_recovery_commit(delivery_id)
        if commit_sha:
            return ReconcileChange(
                delivery_id=delivery_id,
                from_status=status,
                to_status="delivered",
                error=f"reconcile:git-commit-found:{commit_sha}",
            )

    if status == "processing" and not _has_active_worker(row):
        lease_until = _parse_iso(str(row["lease_until"]) if row["lease_until"] else None)
        if lease_until is not None:
            started_at = lease_until - timedelta(
                seconds=_channels.DEFAULT_DELIVERY_LEASE_SECONDS
            )
            hard_timeout = int(row["deadline_seconds"] or _DEFAULT_HARD_TIMEOUT_SECONDS)
            if now - started_at > timedelta(seconds=hard_timeout * 2):
                return ReconcileChange(
                    delivery_id=delivery_id,
                    from_status=status,
                    to_status="failed",
                    error="reconcile:worker-disappeared",
                )

    if status == "pending":
        retry_after = _parse_iso(str(row["retry_after"]) if row["retry_after"] else None)
        if (
            retry_after is not None
            and retry_after < now
            and int(row["attempt_count"]) >= _channels.DEFAULT_MAX_DELIVERY_ATTEMPTS
        ):
            return ReconcileChange(
                delivery_id=delivery_id,
                from_status=status,
                to_status="failed",
                error="reconcile:max-attempts-exceeded",
            )

    return None


def reconcile_deliveries(
    *,
    dry_run: bool = False,
    now: str | None = None,
) -> tuple[ReconcileChange, ...]:
    """Return or apply deterministic state fixes for stuck deliveries."""
    now_iso = now or _now_iso()
    now_dt = datetime.fromisoformat(now_iso)

    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT d.delivery_id, d.status, d.lease_until, d.attempt_count,
                   d.retry_after, d.mode, d.deadline_seconds, d.to_agent,
                   cm.channel, cm.thread_id
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE d.status IN ('pending', 'processing')
            ORDER BY cm.created_at ASC, d.delivery_id ASC
            """
        ).fetchall()
    finally:
        conn.close()

    planned = tuple(
        change
        for row in rows
        if (change := _planned_change(row, now=now_dt)) is not None
    )
    if dry_run or not planned:
        return planned

    applied: list[ReconcileChange] = []
    conn = get_db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        for change in planned:
            if change.to_status == "delivered":
                cursor = conn.execute(
                    """
                    UPDATE deliveries
                    SET status='delivered',
                        delivered_at=?,
                        error=?,
                        lease_until=NULL,
                        retry_after=NULL
                    WHERE delivery_id=? AND status=?
                    """,
                    (now_iso, change.error, change.delivery_id, change.from_status),
                )
            else:
                cursor = conn.execute(
                    """
                    UPDATE deliveries
                    SET status='failed',
                        error=?,
                        lease_until=NULL,
                        retry_after=NULL
                    WHERE delivery_id=? AND status=?
                    """,
                    (change.error, change.delivery_id, change.from_status),
                )
            if cursor.rowcount:
                applied.append(change)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return tuple(applied)
