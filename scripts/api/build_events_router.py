"""Build event observability API router."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from .config import CURRICULUM_ROOT

router = APIRouter(tags=["build-events"])

BUILD_EVENTS_SCAN_CAP = 5000


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


def _scan_dispatch_meta_files(level: str | None = None, slug: str | None = None) -> list[Path]:
    level_part = level or "*"
    slug_part = slug or "*"
    pattern = f"{level_part}/orchestration/{slug_part}/dispatch/*-meta.json"
    paths: list[Path] = []
    for idx, path in enumerate(CURRICULUM_ROOT.glob(pattern)):
        if idx >= BUILD_EVENTS_SCAN_CAP:
            break
        paths.append(path)
    return paths


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _event_from_meta(path: Path, meta: dict[str, Any]) -> dict[str, Any]:
    track = path.parents[3].name
    slug = path.parents[1].name
    ts = _parse_iso_datetime(meta.get("timestamp"))
    return {
        "ts": _isoformat_z(ts) if ts else meta.get("timestamp"),
        "level": track,
        "slug": slug,
        "phase": meta.get("phase"),
        "agent": meta.get("agent"),
        "duration_s": meta.get("duration_s"),
        "ok": meta.get("ok"),
        "prompt_chars": meta.get("prompt_chars"),
        "response_chars": meta.get("response_chars"),
    }


def recent_build_events(*, level: str | None = None, slug: str | None = None, limit: int = 100) -> dict[str, Any]:
    event_limit = min(max(1, int(limit)), 1000)
    events: list[dict[str, Any]] = []
    for path in _scan_dispatch_meta_files(level=level, slug=slug):
        meta = _read_json(path)
        if meta is None:
            continue
        events.append(_event_from_meta(path, meta))
    events.sort(key=lambda item: _parse_iso_datetime(item.get("ts")) or datetime.min.replace(tzinfo=UTC), reverse=True)
    return {"events": events[:event_limit]}


def _latest_dispatch_meta_by_module(level: str | None = None) -> dict[tuple[str, str], tuple[Path, dict[str, Any]]]:
    latest: dict[tuple[str, str], tuple[Path, dict[str, Any]]] = {}
    for path in _scan_dispatch_meta_files(level=level):
        meta = _read_json(path)
        if meta is None:
            continue
        key = (path.parents[3].name, path.parents[1].name)
        ts = _parse_iso_datetime(meta.get("timestamp")) or datetime.min.replace(tzinfo=UTC)
        prev = latest.get(key)
        if prev is None:
            latest[key] = (path, meta)
            continue
        prev_ts = _parse_iso_datetime(prev[1].get("timestamp")) or datetime.min.replace(tzinfo=UTC)
        if ts > prev_ts:
            latest[key] = (path, meta)
    return latest


def _current_phase_from_state(state: dict[str, Any]) -> str | None:
    phases = state.get("phases")
    if not isinstance(phases, dict):
        return None
    for phase, info in phases.items():
        if not isinstance(info, dict):
            continue
        if info.get("status") != "complete":
            return phase
    return "publish"


def active_build_events(*, level: str | None = None) -> dict[str, Any]:
    now = datetime.now(UTC)
    cutoff = now - timedelta(minutes=10)
    active: list[dict[str, Any]] = []
    for (track, slug), (_path, meta) in _latest_dispatch_meta_by_module(level=level).items():
        ts = _parse_iso_datetime(meta.get("timestamp"))
        if ts is None or ts < cutoff:
            continue
        state_path = CURRICULUM_ROOT / track / "orchestration" / slug / "state.json"
        state = _read_json(state_path)
        if state is None:
            continue
        publish = state.get("phases", {}).get("publish", {})
        if isinstance(publish, dict) and publish.get("status") == "complete":
            continue
        active.append({
            "level": track,
            "slug": slug,
            "current_phase": _current_phase_from_state(state) or meta.get("phase"),
            "started_at": _isoformat_z(ts),
            "age_s": round((now - ts).total_seconds(), 1),
        })
    active.sort(key=lambda item: _parse_iso_datetime(item.get("started_at")) or datetime.min.replace(tzinfo=UTC), reverse=True)
    return {"active": active}


@router.get("/recent")
async def build_events_recent(
    level: str | None = Query(None),
    slug: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    return await asyncio.to_thread(recent_build_events, level=level, slug=slug, limit=limit)


@router.get("/active")
async def build_events_active(level: str | None = Query(None)):
    return await asyncio.to_thread(active_build_events, level=level)
