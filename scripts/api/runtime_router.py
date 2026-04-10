"""Runtime observability API router."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import sys
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from .config import BATCH_STATE_DIR

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_runtime.usage import has_headroom

router = APIRouter(tags=["runtime"])

ADAPTERS_DIR = Path(__file__).resolve().parent.parent / "agent_runtime" / "adapters"
USAGE_DIR = BATCH_STATE_DIR / "api_usage"
_KNOWN_OUTCOMES = ("ok", "error", "timeout", "rate_limited")


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _usage_day_from_name(path: Path) -> date | None:
    stem = path.stem
    if not stem.startswith("usage_"):
        return None
    try:
        day_str = stem.rsplit("_", 1)[1]
        return date.fromisoformat(day_str)
    except (IndexError, ValueError):
        return None


def _usage_files(*, days: int, agent: str | None = None, entrypoint: str | None = None) -> list[Path]:
    if not USAGE_DIR.exists():
        return []
    today = datetime.now(UTC).date()
    earliest = today - timedelta(days=max(1, days) - 1)
    files: list[Path] = []
    for path in sorted(USAGE_DIR.glob("usage_*.jsonl")):
        day = _usage_day_from_name(path)
        if day is None or day < earliest or day > today:
            continue
        name = path.stem.removeprefix("usage_")
        prefix = name.rsplit("_", 1)[0]
        if "-" not in prefix:
            continue
        file_agent, file_entrypoint = prefix.split("-", 1)
        if agent and file_agent != agent:
            continue
        if entrypoint and file_entrypoint != entrypoint:
            continue
        files.append(path)
    return files


def _today_usage_files() -> list[Path]:
    return _usage_files(days=1)


def _iter_usage_records(paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        try:
            with open(path, encoding="utf-8") as handle:
                for raw in handle:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(data, dict):
                        records.append(data)
        except OSError:
            continue
    return records


def _new_outcome_bucket() -> dict[str, Any]:
    bucket: dict[str, Any] = {"total": 0, "total_duration_s": 0.0}
    for key in _KNOWN_OUTCOMES:
        bucket[key] = 0
    return bucket


def _update_outcome_bucket(bucket: dict[str, Any], record: dict[str, Any]) -> None:
    bucket["total"] += 1
    outcome = str(record.get("outcome") or "")
    if outcome in _KNOWN_OUTCOMES:
        bucket[outcome] += 1
    duration = record.get("duration_s")
    if isinstance(duration, (int, float)):
        bucket["total_duration_s"] = round(bucket["total_duration_s"] + float(duration), 3)


def list_runtime_agents() -> list[dict[str, Any]]:
    agents: list[dict[str, Any]] = []
    for path in sorted(ADAPTERS_DIR.glob("*.py")):
        if path.stem in {"__init__", "base"} or path.stem.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"agent_runtime.adapters.{path.stem}")
        except Exception:
            continue

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ != module.__name__:
                continue
            if not all(hasattr(obj, attr) for attr in ("name", "default_model", "supported_modes")):
                continue
            if not callable(getattr(obj, "build_invocation", None)):
                continue
            if not callable(getattr(obj, "parse_response", None)):
                continue
            try:
                source = inspect.getsource(obj.build_invocation)
            except (OSError, TypeError):
                source = ""
            if "@anthropic-ai/claude-code@latest" in source:
                binary = "npx @anthropic-ai/claude-code@latest"
            elif 'shutil.which("gemini")' in source:
                binary = "gemini"
            elif 'shutil.which("codex")' in source:
                binary = "codex"
            else:
                binary = str(obj.name)
            agents.append({
                "name": str(obj.name),
                "binary": binary,
                "default_model": getattr(obj, "default_model", None),
                "supported_modes": sorted(str(mode) for mode in getattr(obj, "supported_modes", [])),
            })
            break
    return agents


def summarize_runtime_usage(
    *, days: int = 7, agent: str | None = None, entrypoint: str | None = None
) -> dict[str, Any]:
    window_days = min(max(1, int(days)), 30)
    by_agent: dict[str, dict[str, Any]] = defaultdict(_new_outcome_bucket)
    by_entrypoint: dict[str, dict[str, Any]] = defaultdict(_new_outcome_bucket)
    total = 0

    for record in _iter_usage_records(_usage_files(days=window_days, agent=agent, entrypoint=entrypoint)):
        record_agent = record.get("agent")
        record_entrypoint = record.get("entrypoint")
        if agent and record_agent != agent:
            continue
        if entrypoint and record_entrypoint != entrypoint:
            continue
        total += 1
        if record_agent:
            _update_outcome_bucket(by_agent[str(record_agent)], record)
        if record_entrypoint:
            _update_outcome_bucket(by_entrypoint[str(record_entrypoint)], record)

    return {
        "window_days": window_days,
        "records_total": total,
        "by_agent": dict(by_agent),
        "by_entrypoint": dict(by_entrypoint),
    }


def recent_runtime_records(*, limit: int = 50) -> dict[str, Any]:
    record_limit = min(max(1, int(limit)), 500)
    summaries: list[dict[str, Any]] = []
    for record in _iter_usage_records(_today_usage_files()):
        ts = _parse_iso_datetime(record.get("ts"))
        summaries.append({
            "ts": _isoformat_z(ts) if ts else record.get("ts"),
            "agent": record.get("agent"),
            "entrypoint": record.get("entrypoint"),
            "model": record.get("model"),
            "outcome": record.get("outcome"),
            "duration_s": record.get("duration_s"),
        })
    summaries.sort(key=lambda item: _parse_iso_datetime(item.get("ts")) or datetime.min.replace(tzinfo=UTC), reverse=True)
    return {"records": summaries[:record_limit]}


def runtime_recent_outcomes_today() -> dict[str, int]:
    counts = {key: 0 for key in _KNOWN_OUTCOMES}
    for record in _iter_usage_records(_today_usage_files()):
        outcome = str(record.get("outcome") or "")
        if outcome in counts:
            counts[outcome] += 1
    return counts


@router.get("/agents")
async def runtime_agents():
    agents = await asyncio.to_thread(list_runtime_agents)
    return {"agents": agents}


@router.get("/usage")
async def runtime_usage(
    agent: str | None = Query(None),
    entrypoint: str | None = Query(None),
    days: int = Query(7, ge=1, le=30),
):
    return await asyncio.to_thread(summarize_runtime_usage, days=days, agent=agent, entrypoint=entrypoint)


@router.get("/headroom")
async def runtime_headroom(
    agent: str | None = Query(None),
    model: str | None = Query(None),
):
    if not agent or not model:
        raise HTTPException(status_code=400, detail="Both 'agent' and 'model' query params are required")
    ok, reason = await asyncio.to_thread(has_headroom, agent, model)
    return {"agent": agent, "model": model, "has_headroom": ok, "reason": reason}


@router.get("/recent")
async def runtime_recent(limit: int = Query(50, ge=1, le=500)):
    return await asyncio.to_thread(recent_runtime_records, limit=limit)
