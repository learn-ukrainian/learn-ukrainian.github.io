"""FastAPI router for local telemetry persistence.

This router owns two telemetry families:

- per-tool timing telemetry from local hooks
- module-build token telemetry, including explicit swarm/solo reporting
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .config import PROJECT_ROOT
from .resilience import connect_sqlite

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])

_DB_PATH = PROJECT_ROOT / "data" / "telemetry" / "tool_timings.db"
_MODULE_BUILD_DB_PATH = PROJECT_ROOT / "data" / "telemetry" / "module_builds.db"
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


class ModuleBuildParticipantIngest(BaseModel):
    role: str = Field(..., min_length=1)
    agent: str = Field(..., min_length=1)
    model: str | None = None
    effort: str | None = None
    label: str | None = None
    calls: int | None = Field(None, ge=0)
    prompt_tokens: int | None = Field(None, ge=0)
    response_tokens: int | None = Field(None, ge=0)
    total_tokens: int | None = Field(None, ge=0)
    token_source: str = Field("unavailable", min_length=1)
    cost_usd_est: float | None = Field(None, ge=0)
    notes: str | None = None


class ModuleBuildTelemetryIngest(BaseModel):
    run_id: str = Field(default_factory=lambda: f"mbt-{uuid4().hex}", min_length=1)
    recorded_at: datetime | None = None
    level: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1)
    module_title: str | None = None
    branch: str | None = None
    commit_sha: str | None = None
    pr_number: int | None = Field(None, ge=1)
    pr_url: str | None = None
    status: str = Field("recorded", min_length=1)
    swarm_used: bool
    swarm_label: str = Field("none", min_length=1)
    swarm_note: str = Field(..., min_length=1)
    wall_clock_minutes: float | None = Field(None, ge=0)
    source: str = Field(..., min_length=1)
    notes: str | None = None
    participants: list[ModuleBuildParticipantIngest] = Field(default_factory=list)


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


def _computed_total_tokens(participant: ModuleBuildParticipantIngest) -> int | None:
    if participant.total_tokens is not None:
        return int(participant.total_tokens)
    prompt = participant.prompt_tokens
    response = participant.response_tokens
    if prompt is None and response is None:
        return None
    return int(prompt or 0) + int(response or 0)


def _init_db(db_path: Path | None = None) -> None:
    path = db_path or _DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect_sqlite(str(path))) as conn:
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


def _init_module_build_db(db_path: Path | None = None) -> None:
    path = db_path or _MODULE_BUILD_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect_sqlite(str(path))) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS module_build_runs (
                run_id             TEXT PRIMARY KEY,
                created_at         TEXT NOT NULL,
                updated_at         TEXT NOT NULL,
                level              TEXT NOT NULL,
                slug               TEXT NOT NULL,
                module_title       TEXT,
                branch             TEXT,
                commit_sha         TEXT,
                pr_number          INTEGER,
                pr_url             TEXT,
                status             TEXT NOT NULL DEFAULT 'recorded',
                swarm_used         INTEGER NOT NULL,
                swarm_label        TEXT NOT NULL DEFAULT 'none',
                swarm_note         TEXT NOT NULL,
                wall_clock_minutes REAL,
                source             TEXT NOT NULL,
                notes              TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_mbr_level_slug
                ON module_build_runs(level, slug, updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_mbr_updated
                ON module_build_runs(updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_mbr_swarm
                ON module_build_runs(swarm_used, updated_at DESC);

            CREATE TABLE IF NOT EXISTS module_build_participants (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          TEXT NOT NULL,
                role            TEXT NOT NULL,
                agent           TEXT NOT NULL,
                model           TEXT,
                effort          TEXT,
                label           TEXT,
                calls           INTEGER,
                prompt_tokens   INTEGER,
                response_tokens INTEGER,
                total_tokens    INTEGER,
                token_source    TEXT NOT NULL DEFAULT 'unavailable',
                cost_usd_est    REAL,
                notes           TEXT,
                FOREIGN KEY(run_id) REFERENCES module_build_runs(run_id)
                    ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_mbp_run
                ON module_build_participants(run_id, id);
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


def _participant_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "role": row["role"],
        "agent": row["agent"],
        "model": row["model"],
        "effort": row["effort"],
        "label": row["label"],
        "calls": row["calls"],
        "prompt_tokens": row["prompt_tokens"],
        "response_tokens": row["response_tokens"],
        "total_tokens": row["total_tokens"],
        "token_source": row["token_source"],
        "cost_usd_est": row["cost_usd_est"],
        "notes": row["notes"],
    }


def _participant_totals(participants: list[dict[str, Any]]) -> dict[str, Any]:
    prompt = sum(int(item["prompt_tokens"] or 0) for item in participants)
    response = sum(int(item["response_tokens"] or 0) for item in participants)
    total = sum(int(item["total_tokens"] or 0) for item in participants)
    cost = sum(float(item["cost_usd_est"] or 0.0) for item in participants)
    return {
        "participants": len(participants),
        "prompt_tokens": prompt,
        "response_tokens": response,
        "total_tokens": total,
        "cost_usd_est": round(cost, 6),
    }


def _run_row_to_dict(row: sqlite3.Row, participants: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": row["run_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "level": row["level"],
        "slug": row["slug"],
        "module_title": row["module_title"],
        "branch": row["branch"],
        "commit_sha": row["commit_sha"],
        "pr_number": row["pr_number"],
        "pr_url": row["pr_url"],
        "status": row["status"],
        "swarm_used": bool(row["swarm_used"]),
        "swarm_label": row["swarm_label"],
        "swarm_note": row["swarm_note"],
        "wall_clock_minutes": row["wall_clock_minutes"],
        "source": row["source"],
        "notes": row["notes"],
        "participants": participants,
        "totals": _participant_totals(participants),
    }


def _load_participants(conn: sqlite3.Connection, run_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    if not run_ids:
        return {}
    placeholders = ",".join("?" for _ in run_ids)
    rows = conn.execute(
        f"""
        SELECT run_id, role, agent, model, effort, label, calls, prompt_tokens,
               response_tokens, total_tokens, token_source, cost_usd_est, notes
        FROM module_build_participants
        WHERE run_id IN ({placeholders})
        ORDER BY run_id, id
        """,
        run_ids,
    ).fetchall()
    participants: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        participants[str(row["run_id"])].append(_participant_row_to_dict(row))
    return participants


def _runs_summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    prompt = sum(int(run["totals"]["prompt_tokens"]) for run in runs)
    response = sum(int(run["totals"]["response_tokens"]) for run in runs)
    total = sum(int(run["totals"]["total_tokens"]) for run in runs)
    participants = sum(int(run["totals"]["participants"]) for run in runs)
    cost = sum(float(run["totals"]["cost_usd_est"]) for run in runs)
    swarm_runs = sum(1 for run in runs if run["swarm_used"])
    return {
        "runs": len(runs),
        "swarm_runs": swarm_runs,
        "solo_runs": len(runs) - swarm_runs,
        "participants": participants,
        "prompt_tokens": prompt,
        "response_tokens": response,
        "total_tokens": total,
        "cost_usd_est": round(cost, 6),
    }


@router.post("/tool-timings")
def ingest_tool_timing(payload: ToolTimingIngest) -> dict[str, bool]:
    _init_db()
    with closing(connect_sqlite(str(_DB_PATH))) as conn:
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
    with closing(connect_sqlite(str(_DB_PATH))) as conn:
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


@router.post("/module-builds")
def ingest_module_build_telemetry(payload: ModuleBuildTelemetryIngest) -> dict[str, Any]:
    _init_module_build_db()
    created_at = _isoformat_z(payload.recorded_at) if payload.recorded_at else _now_z()
    updated_at = _now_z()
    run_id = _required_text(payload.run_id, "run_id")
    level = _required_text(payload.level, "level").lower()
    slug = _required_text(payload.slug, "slug")
    status = _required_text(payload.status, "status")
    swarm_label = _clean_text(payload.swarm_label) or "none"
    swarm_note = _required_text(payload.swarm_note, "swarm_note")
    source = _required_text(payload.source, "source")
    participant_rows = [
        (
            run_id,
            _required_text(participant.role, "participant.role"),
            _required_text(participant.agent, "participant.agent"),
            _clean_text(participant.model),
            _clean_text(participant.effort),
            _clean_text(participant.label),
            participant.calls,
            participant.prompt_tokens,
            participant.response_tokens,
            _computed_total_tokens(participant),
            _required_text(participant.token_source, "participant.token_source"),
            participant.cost_usd_est,
            _clean_text(participant.notes),
        )
        for participant in payload.participants
    ]

    with closing(connect_sqlite(str(_MODULE_BUILD_DB_PATH))) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            INSERT INTO module_build_runs (
                run_id, created_at, updated_at, level, slug, module_title,
                branch, commit_sha, pr_number, pr_url, status, swarm_used,
                swarm_label, swarm_note, wall_clock_minutes, source, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                created_at = module_build_runs.created_at,
                updated_at = excluded.updated_at,
                level = excluded.level,
                slug = excluded.slug,
                module_title = excluded.module_title,
                branch = excluded.branch,
                commit_sha = excluded.commit_sha,
                pr_number = excluded.pr_number,
                pr_url = excluded.pr_url,
                status = excluded.status,
                swarm_used = excluded.swarm_used,
                swarm_label = excluded.swarm_label,
                swarm_note = excluded.swarm_note,
                wall_clock_minutes = excluded.wall_clock_minutes,
                source = excluded.source,
                notes = excluded.notes
            """,
            (
                run_id,
                created_at,
                updated_at,
                level,
                slug,
                _clean_text(payload.module_title),
                _clean_text(payload.branch),
                _clean_text(payload.commit_sha),
                payload.pr_number,
                _clean_text(payload.pr_url),
                status,
                1 if payload.swarm_used else 0,
                swarm_label,
                swarm_note,
                payload.wall_clock_minutes,
                source,
                _clean_text(payload.notes),
            ),
        )
        conn.execute("DELETE FROM module_build_participants WHERE run_id = ?", (run_id,))
        conn.executemany(
            """
            INSERT INTO module_build_participants (
                run_id, role, agent, model, effort, label, calls, prompt_tokens,
                response_tokens, total_tokens, token_source, cost_usd_est, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            participant_rows,
        )
        conn.commit()

    return {"ok": True, "run_id": run_id}


@router.get("/module-builds")
def read_module_build_telemetry(
    level: str | None = Query(None),
    slug: str | None = Query(None),
    swarm_used: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    _init_module_build_db()
    conditions: list[str] = []
    params: list[Any] = []
    if level:
        conditions.append("level = ?")
        params.append(level.strip().lower())
    if slug:
        conditions.append("slug = ?")
        params.append(slug.strip())
    if swarm_used is not None:
        conditions.append("swarm_used = ?")
        params.append(1 if swarm_used else 0)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    with closing(connect_sqlite(str(_MODULE_BUILD_DB_PATH))) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT *
            FROM module_build_runs
            {where}
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        run_ids = [str(row["run_id"]) for row in rows]
        participants = _load_participants(conn, run_ids)

    runs = [_run_row_to_dict(row, participants.get(str(row["run_id"]), [])) for row in rows]
    return {
        "generated_at": _now_z(),
        "records_total": len(runs),
        "totals": _runs_summary(runs),
        "runs": runs,
    }


@router.get("/module-builds/{level}/{slug}")
def read_module_build_telemetry_for_module(
    level: str,
    slug: str,
    limit: int = Query(20, ge=1, le=200),
) -> dict[str, Any]:
    payload = read_module_build_telemetry(level=level, slug=slug, swarm_used=None, limit=limit)
    return {
        "generated_at": payload["generated_at"],
        "level": level.strip().lower(),
        "slug": slug.strip(),
        "records_total": payload["records_total"],
        "totals": payload["totals"],
        "latest": payload["runs"][0] if payload["runs"] else None,
        "runs": payload["runs"],
    }
