"""Sol PR-M: efficiency metrics from durable broker timestamps (no content)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(r[1]) for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def collect_delivery_backlog(
    db_path: Path,
    *,
    limit: int = 100,
    exclude_retired: bool = True,
) -> dict[str, Any]:
    """Pending/dispatched delivery backlog without message bodies."""
    retired = {"gemini"}
    with _connect(db_path) as conn:
        if not _table_exists(conn, "deliveries"):
            return {"total": 0, "by_agent": {}, "by_status": {}, "rows": []}
        cols = _column_names(conn, "deliveries")
        # Schema varies across migrations; only SELECT columns that exist.
        select_cols = [
            c
            for c in (
                "delivery_id",
                "message_id",
                "to_agent",
                "status",
                "attempt_count",
                "dispatched_at",
                "created_at",
            )
            if c in cols
        ]
        if not select_cols:
            return {"total": 0, "by_agent": {}, "by_status": {}, "rows": []}
        order_col = (
            "dispatched_at"
            if "dispatched_at" in cols
            else ("created_at" if "created_at" in cols else select_cols[0])
        )
        status_filter = "('pending', 'dispatched')"
        rows = conn.execute(
            f"""
            SELECT {", ".join(select_cols)}
            FROM deliveries
            WHERE status IN {status_filter}
            ORDER BY COALESCE({order_col}, '') DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        by_agent: dict[str, int] = {}
        by_status: dict[str, int] = {}
        out_rows: list[dict[str, Any]] = []
        for r in rows:
            agent = str(r["to_agent"] if "to_agent" in cols else "") or ""
            if exclude_retired and agent in retired:
                continue
            status = str(r["status"] if "status" in cols else "") or ""
            by_agent[agent] = by_agent.get(agent, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
            out_rows.append(
                {
                    "delivery_id": r["delivery_id"] if "delivery_id" in cols else None,
                    "message_id": r["message_id"] if "message_id" in cols else None,
                    "to_agent": agent,
                    "status": status,
                    "attempt_count": r["attempt_count"] if "attempt_count" in cols else 0,
                    "dispatched_at": r["dispatched_at"] if "dispatched_at" in cols else None,
                }
            )
        return {
            "total": len(out_rows),
            "by_agent": by_agent,
            "by_status": by_status,
            "exclude_retired": sorted(retired) if exclude_retired else [],
            "rows": out_rows,
        }


def collect_dead_letters(db_path: Path, *, limit: int = 100) -> dict[str, Any]:
    """Dead-letter counts and metadata rows (no message content)."""
    with _connect(db_path) as conn:
        if not _table_exists(conn, "dead_letters"):
            return {"total": 0, "by_reason": {}, "rows": []}
        total = conn.execute("SELECT COUNT(*) AS c FROM dead_letters").fetchone()["c"]
        by_reason_rows = conn.execute(
            "SELECT reason, COUNT(*) AS c FROM dead_letters GROUP BY reason ORDER BY c DESC"
        ).fetchall()
        rows = conn.execute(
            """
            SELECT dead_letter_id, request_id, delivery_id, reason, successor,
                   original_expires_at, created_at
            FROM dead_letters
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return {
            "total": int(total),
            "by_reason": {str(r["reason"]): int(r["c"]) for r in by_reason_rows},
            "rows": [dict(r) for r in rows],
        }


def collect_efficiency_metrics(db_path: Path) -> dict[str, Any]:
    """Aggregate ask/reply efficiency from durable timestamps only."""
    with _connect(db_path) as conn:
        metrics: dict[str, Any] = {
            "content_included": False,
            "deliveries": {},
            "requests": {},
            "messages_legacy": {},
            "dead_letters": 0,
            "latency_seconds": {},
        }

        if _table_exists(conn, "deliveries"):
            for r in conn.execute(
                "SELECT status, COUNT(*) AS c FROM deliveries GROUP BY status"
            ):
                metrics["deliveries"][str(r["status"])] = int(r["c"])
            # latency for delivered rows with both timestamps
            lat = conn.execute(
                """
                SELECT
                  COUNT(*) AS n,
                  AVG(
                    (julianday(delivered_at) - julianday(dispatched_at)) * 86400.0
                  ) AS avg_s,
                  MIN(
                    (julianday(delivered_at) - julianday(dispatched_at)) * 86400.0
                  ) AS min_s,
                  MAX(
                    (julianday(delivered_at) - julianday(dispatched_at)) * 86400.0
                  ) AS max_s
                FROM deliveries
                WHERE status = 'delivered'
                  AND delivered_at IS NOT NULL
                  AND dispatched_at IS NOT NULL
                  AND delivered_at != ''
                  AND dispatched_at != ''
                """
            ).fetchone()
            if lat and lat["n"]:
                metrics["latency_seconds"]["delivery_dispatch_to_done"] = {
                    "n": int(lat["n"]),
                    "avg": round(float(lat["avg_s"] or 0.0), 3),
                    "min": round(float(lat["min_s"] or 0.0), 3),
                    "max": round(float(lat["max_s"] or 0.0), 3),
                }

        if _table_exists(conn, "requests"):
            for r in conn.execute(
                "SELECT state, COUNT(*) AS c FROM requests GROUP BY state"
            ):
                metrics["requests"][str(r["state"])] = int(r["c"])

        if _table_exists(conn, "messages"):
            for r in conn.execute(
                "SELECT status, COUNT(*) AS c FROM messages GROUP BY status"
            ):
                metrics["messages_legacy"][str(r["status"])] = int(r["c"])
            # ask/reply pairs by task_id count only
            pair = conn.execute(
                """
                SELECT COUNT(DISTINCT task_id) AS tasks
                FROM messages
                WHERE task_id IS NOT NULL AND task_id != ''
                """
            ).fetchone()
            metrics["messages_legacy"]["distinct_task_ids"] = int(pair["tasks"] or 0)

        if _table_exists(conn, "dead_letters"):
            metrics["dead_letters"] = int(
                conn.execute("SELECT COUNT(*) AS c FROM dead_letters").fetchone()["c"]
            )

        # retired endpoint backlog should be zero for gemini inserts going forward
        if _table_exists(conn, "deliveries"):
            gemini_pending = conn.execute(
                """
                SELECT COUNT(*) AS c FROM deliveries
                WHERE to_agent = 'gemini' AND status IN ('pending', 'dispatched')
                """
            ).fetchone()["c"]
            metrics["retired_endpoint_pending"] = {
                "gemini": int(gemini_pending),
            }

        return metrics
