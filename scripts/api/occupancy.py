"""Monitor occupancy: opaque host_id plus occupants, reusing atlas load cache.

Sibling of ``GET /api/atlas-jobs/load`` — one occupancy board, no second probe
path. Canonical SSH aliases never appear as JSON keys. Map them with
``MONITOR_OCCUPANCY_HOST_IDS`` (``alias=opaque-id,...``). Observer heartbeats
from ``POST /api/observer/presence`` appear under ``cloud-observer``.
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from scripts.api import atlas_jobs_router as load_mod
from scripts.api.observer_presence import list_live
from scripts.api.occupancy_sanitize import CLOUD_OBSERVER_HOST_ID
from scripts.api.occupancy_sanitize import occupant as _occupant
from scripts.api.occupancy_sanitize import opaque_host_id as _opaque_host_id
from scripts.lexicon.runner import atlas_job

router = APIRouter(tags=["occupancy"])

OCCUPANCY_SCHEMA = "monitor-occupancy.v1"
_LOAD_METRIC_KEYS = ("cpu_count", "loadavg", "mem", "disk")


def parse_host_id_map(raw: str | None = None) -> dict[str, str]:
    """Parse ``canonical=opaque`` pairs. Drop anything that is not opaque."""
    text = (raw if raw is not None else os.environ.get("MONITOR_OCCUPANCY_HOST_IDS", "")).strip()
    mapping: dict[str, str] = {}
    if not text:
        return mapping
    for part in text.split(","):
        item = part.strip()
        if not item or "=" not in item:
            continue
        canonical_raw, opaque_raw = item.split("=", 1)
        canonical = atlas_job._canonical_host(canonical_raw.strip())
        opaque = opaque_raw.strip().lower()
        if not _opaque_host_id(opaque):
            continue
        mapping[canonical] = opaque
    return mapping


def _occupants_from_registry(canonical: str) -> list[dict[str, str | None]]:
    occupants: list[dict[str, str | None]] = []
    seen: set[tuple[str, str]] = set()
    try:
        rows = atlas_job.list_registry()
    except Exception:
        rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if atlas_job._canonical_host(row.get("host")) != canonical:
            continue
        state = str(row.get("state") or "")
        if state not in {"running", "queued", "submitted", "needs_finalize"}:
            continue
        plan = row.get("plan") if isinstance(row.get("plan"), dict) else {}
        occupant = _occupant(
            kind="job",
            agent=row.get("agent") or plan.get("agent"),
            task_id=row.get("id"),
            epic=row.get("epic") or plan.get("epic"),
        )
        if occupant is None:
            continue
        key = (occupant["kind"], occupant["task_id"] or "")
        if key in seen:
            continue
        seen.add(key)
        occupants.append(occupant)
    return occupants


def _occupants_from_job_unit(canonical: str, load_entry: dict[str, Any]) -> list[dict[str, str | None]]:
    del canonical
    job_unit = load_entry.get("job_unit")
    if not isinstance(job_unit, dict):
        return []
    job_id = job_unit.get("job_id")
    occupant = _occupant(kind="job", task_id=job_id)
    return [occupant] if occupant is not None else []


def _merge_occupants(*groups: list[dict[str, str | None]]) -> list[dict[str, str | None]]:
    merged: list[dict[str, str | None]] = []
    seen: set[tuple[str, str]] = set()
    for group in groups:
        for occupant in group:
            key = (occupant["kind"], occupant["task_id"] or "")
            if key in seen:
                continue
            seen.add(key)
            merged.append(occupant)
    return merged


def _shape_host(host_id: str, load_entry: dict[str, Any], occupants: list[dict[str, str | None]]) -> dict[str, Any]:
    status = str(load_entry.get("status") or "unavailable")
    shaped: dict[str, Any] = {
        "host_id": host_id,
        "status": status if status in {"fresh", "stale", "unavailable"} else "unavailable",
        "observed_at": load_entry.get("observed_at"),
        "age_seconds": load_entry.get("age_seconds", 0.0),
        "occupants": occupants,
    }
    if shaped["status"] == "unavailable":
        shaped["error"] = "unreachable"
        return shaped
    for key in _LOAD_METRIC_KEYS:
        if key in load_entry:
            shaped[key] = load_entry[key]
    return shaped


def _occupants_from_observers() -> list[dict[str, str | None]]:
    occupants: list[dict[str, str | None]] = []
    for row in list_live():
        occupant = _occupant(
            kind="observer",
            agent=row.agent,
            task_id=row.task_id,
            epic=row.epic,
            status=row.status,
            summary=row.summary,
        )
        if occupant is not None:
            occupants.append(occupant)
    return occupants


def _shape_cloud_observer(occupants: list[dict[str, str | None]]) -> dict[str, Any]:
    return {
        "host_id": CLOUD_OBSERVER_HOST_ID,
        "status": "fresh",
        "observed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "age_seconds": 0.0,
        "occupants": occupants,
    }


def _attach_cloud_observer(payload: dict[str, Any], host_id: str | None) -> dict[str, Any]:
    if host_id is not None and host_id != CLOUD_OBSERVER_HOST_ID:
        return payload
    occupants = _occupants_from_observers()
    if not occupants and host_id is None:
        return payload
    payload["hosts"][CLOUD_OBSERVER_HOST_ID] = _shape_cloud_observer(occupants)
    return payload


def _selected_hosts(host_id: str | None) -> dict[str, str]:
    if host_id == CLOUD_OBSERVER_HOST_ID:
        return {}

    mapping = parse_host_id_map()
    if not mapping:
        return {}

    reverse = {opaque: canonical for canonical, opaque in mapping.items()}
    if host_id is not None:
        if host_id not in reverse:
            raise HTTPException(status_code=400, detail="unknown host_id")
        return {host_id: reverse[host_id]}
    return {opaque: canonical for canonical, opaque in mapping.items()}


def _empty_payload() -> dict[str, Any]:
    return {
        "schema": OCCUPANCY_SCHEMA,
        "observed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "hosts": {},
    }


def _payload_from_entries(selected: dict[str, str], load_entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    hosts: dict[str, Any] = {}
    for opaque, canonical in selected.items():
        load_entry = load_entries[canonical]
        occupants = _merge_occupants(
            _occupants_from_registry(canonical),
            _occupants_from_job_unit(canonical, load_entry),
        )
        hosts[opaque] = _shape_host(opaque, load_entry, occupants)

    return {
        "schema": OCCUPANCY_SCHEMA,
        "observed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "hosts": hosts,
    }


def occupancy_payload(*, host_id: str | None = None, fresh: bool = False) -> dict[str, Any]:
    """Build the synchronous cache-only payload for non-HTTP callers."""
    selected = _selected_hosts(host_id)
    if not selected:
        return _attach_cloud_observer(_empty_payload(), host_id)

    load_entries = {canonical: load_mod._get_host_load_entry(canonical, fresh=fresh) for canonical in selected.values()}
    return _attach_cloud_observer(_payload_from_entries(selected, load_entries), host_id)


async def _occupancy_payload_async(*, host_id: str | None = None, fresh: bool = False) -> dict[str, Any]:
    selected = _selected_hosts(host_id)
    if not selected:
        return _attach_cloud_observer(_empty_payload(), host_id)

    entries = await asyncio.gather(
        *(load_mod._get_host_load_entry_async(canonical, fresh=fresh) for canonical in selected.values())
    )
    load_entries = dict(zip(selected.values(), entries, strict=True))
    return _attach_cloud_observer(_payload_from_entries(selected, load_entries), host_id)


@router.get("")
async def occupancy(
    host_id: str | None = Query(default=None),
    fresh: bool = False,
) -> JSONResponse:
    payload = await _occupancy_payload_async(host_id=host_id, fresh=fresh)
    return JSONResponse(content=payload, headers={"Cache-Control": "no-store"})
