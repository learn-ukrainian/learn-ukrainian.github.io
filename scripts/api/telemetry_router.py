"""FastAPI router for local telemetry persistence.

This router owns per-tool timing telemetry from local hooks and the legacy
comms/bridge usage summaries. Module-build token telemetry
(``/api/telemetry/module-builds*``) is a product route in
``scripts.project_api.module_builds`` under the same prefix (Monitor split,
C-4687).
"""

from __future__ import annotations

import os
import sqlite3
from collections import defaultdict
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from scripts.lib.readonly_sqlite import SQLiteConnection
except ModuleNotFoundError as exc:
    if exc.name != Path(os.path.abspath(__file__)).parents[1].name:
        raise
    from lib.readonly_sqlite import SQLiteConnection  # type: ignore[no-redef]

from scripts.telemetry.legacy_bridge import bridge_usage_summary

from .monitor_context import MonitorContext, get_ctx, resolve_context
from .telemetry.legacy_comms import db_path_for_root as legacy_comms_db_path_for_root
from .telemetry.legacy_comms import legacy_comms_summary

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])
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


def _tool_timings_path(ctx: MonitorContext | None = None) -> Path:
    return resolve_context(ctx).roots.project_root / "data" / "telemetry" / "tool_timings.db"


def _legacy_comms_db_path(ctx: MonitorContext | None = None) -> Path:
    return legacy_comms_db_path_for_root(resolve_context(ctx).roots.project_root)


def _open_telemetry_db(ctx: MonitorContext, path: Path) -> SQLiteConnection:
    path.parent.mkdir(parents=True, exist_ok=True)
    return ctx._open_db(path)


def _isoformat_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _now_z() -> str:
    return _isoformat_z(datetime.now(UTC))


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _required_text(value: str | None, field: str) -> str:
    cleaned = _clean_text(value)
    if cleaned is None:
        raise HTTPException(status_code=422, detail=f"{field} must not be blank")
    return cleaned


def _init_db(ctx: MonitorContext | None = None, db_path: Path | None = None) -> None:
    resolved = resolve_context(ctx)
    path = db_path or _tool_timings_path(resolved)
    with closing(_open_telemetry_db(resolved, path)) as conn:
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
def ingest_tool_timing(
    payload: ToolTimingIngest,
    ctx: MonitorContext = Depends(get_ctx),
) -> dict[str, bool]:
    _init_db(ctx)
    with closing(_open_telemetry_db(ctx, _tool_timings_path(ctx))) as conn:
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
    ctx: MonitorContext = Depends(get_ctx),
) -> list[dict[str, Any]]:
    _init_db(ctx)
    conditions = ["ts >= ?"]
    params: list[Any] = [_window_start(window)]
    if tool:
        conditions.append("tool_name = ?")
        params.append(tool)

    where = " AND ".join(conditions)
    with closing(_open_telemetry_db(ctx, _tool_timings_path(ctx))) as conn:
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


@router.get("/legacy-comms-routes")
def read_legacy_comms_routes(
    window: Literal["1h", "24h", "7d", "30d", "90d"] = Query("7d"),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Return body-free legacy-route aggregates with explicit coverage truth."""
    return legacy_comms_summary(window, db_path=_legacy_comms_db_path(ctx))


@router.get("/legacy-bridge-asks")
def read_legacy_bridge_asks(
    window: Literal["1h", "24h", "7d", "30d", "90d"] = Query("7d"),
    _ctx: MonitorContext = Depends(get_ctx),
):
    """Return body-free one-shot bridge usage and coverage truth."""
    return bridge_usage_summary(window)
