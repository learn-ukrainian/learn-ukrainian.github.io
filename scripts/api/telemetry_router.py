"""FastAPI router for per-tool timing telemetry (#1541)."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .config import PROJECT_ROOT

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])

_DB_PATH = PROJECT_ROOT / "data" / "telemetry" / "tool_timings.db"
_WINDOWS = {
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
}


class ToolTimingIngest(BaseModel):
    ts: datetime
    tool_name: str = Field(..., min_length=1)
    duration_ms: int = Field(..., ge=0)
    tool_use_id: str | None = None
    session_id: str | None = None
    failed: bool = False


def _isoformat_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _init_db(db_path: Path | None = None) -> None:
    path = db_path or _DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(str(path))) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tool_timings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ts          TEXT NOT NULL,
                tool_name   TEXT NOT NULL,
                duration_ms INTEGER NOT NULL,
                tool_use_id TEXT,
                session_id  TEXT,
                failed      INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_tt_ts ON tool_timings(ts);
            CREATE INDEX IF NOT EXISTS idx_tt_name_ts ON tool_timings(tool_name, ts);
        """)
        conn.commit()


def _percentile_ms(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    if len(values) == 1:
        return values[0]

    rank = (len(values) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(values) - 1)
    fraction = rank - lower
    return round(values[lower] + (values[upper] - values[lower]) * fraction)


def _window_start(window: str) -> str:
    delta = _WINDOWS.get(window)
    if delta is None:
        allowed = ", ".join(_WINDOWS)
        raise HTTPException(status_code=422, detail=f"window must be one of: {allowed}")
    return _isoformat_z(datetime.now(UTC) - delta)


@router.post("/tool-timings")
def ingest_tool_timing(payload: ToolTimingIngest) -> dict[str, bool]:
    _init_db()
    with closing(sqlite3.connect(str(_DB_PATH))) as conn:
        conn.execute(
            """
            INSERT INTO tool_timings (ts, tool_name, duration_ms, tool_use_id, session_id, failed)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                _isoformat_z(payload.ts),
                payload.tool_name,
                int(payload.duration_ms),
                payload.tool_use_id,
                payload.session_id,
                1 if payload.failed else 0,
            ),
        )
        conn.commit()
    return {"ok": True}


@router.get("/tool-timings")
def read_tool_timings(
    window: str = Query("1h"),
    tool: str | None = Query(None),
) -> list[dict[str, Any]]:
    _init_db()
    conditions = ["ts >= ?"]
    params: list[Any] = [_window_start(window)]
    if tool:
        conditions.append("tool_name = ?")
        params.append(tool)

    where = " AND ".join(conditions)
    with closing(sqlite3.connect(str(_DB_PATH))) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT tool_name, duration_ms, failed
            FROM tool_timings
            WHERE {where}
            ORDER BY tool_name, duration_ms
            """,
            params,
        ).fetchall()

    durations: dict[str, list[int]] = defaultdict(list)
    failures: dict[str, int] = defaultdict(int)
    for row in rows:
        tool_name = str(row["tool_name"])
        durations[tool_name].append(int(row["duration_ms"]))
        failures[tool_name] += int(row["failed"])

    results = []
    for tool_name, values in durations.items():
        count = len(values)
        results.append({
            "tool_name": tool_name,
            "count": count,
            "p50_ms": _percentile_ms(values, 0.50),
            "p95_ms": _percentile_ms(values, 0.95),
            "p99_ms": _percentile_ms(values, 0.99),
            "mean_ms": round(sum(values) / count),
            "failure_count": failures[tool_name],
        })

    return sorted(results, key=lambda item: (-item["count"], item["tool_name"]))
