"""Monitor occupancy: opaque host_id plus occupants, reusing atlas load cache.

Sibling of ``GET /api/atlas-jobs/load`` — one occupancy board, no second probe
path. Canonical SSH aliases never appear as JSON keys. Map them with
``MONITOR_OCCUPANCY_HOST_IDS`` (``alias=opaque-id,...``).
"""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from scripts.api import atlas_jobs_router as load_mod
from scripts.lexicon.runner import atlas_job

router = APIRouter(tags=["occupancy"])

OCCUPANCY_SCHEMA = "monitor-occupancy.v1"
OCCUPANT_KINDS = frozenset({"driver", "worker", "job", "service"})
_OPAQUE_HOST_ID = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_IPV4 = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_CANONICAL_ALIASES = frozenset({"atlas-runner", "hramatka", "vps"})
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


def _opaque_host_id(value: str) -> bool:
    if not _OPAQUE_HOST_ID.fullmatch(value):
        return False
    if value in _CANONICAL_ALIASES:
        return False
    return not _IPV4.search(value)


def _safe_field(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or _IPV4.search(text) or "/" in text or "\\" in text:
        return None
    if not _SAFE_TOKEN.fullmatch(text):
        return None
    return text


def _occupant(*, kind: str, agent: Any = None, task_id: Any = None, epic: Any = None) -> dict[str, str | None] | None:
    if kind not in OCCUPANT_KINDS:
        return None
    task = _safe_field(task_id)
    if task is None:
        return None
    return {
        "kind": kind,
        "agent": _safe_field(agent),
        "task_id": task,
        "epic": _safe_field(epic),
    }


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


def occupancy_payload(*, host_id: str | None = None, fresh: bool = False) -> dict[str, Any]:
    mapping = parse_host_id_map()
    if not mapping:
        return {
            "schema": OCCUPANCY_SCHEMA,
            "observed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "hosts": {},
        }

    reverse = {opaque: canonical for canonical, opaque in mapping.items()}
    if host_id is not None:
        if host_id not in reverse:
            raise HTTPException(status_code=400, detail="unknown host_id")
        selected = {host_id: reverse[host_id]}
    else:
        selected = {opaque: canonical for canonical, opaque in mapping.items()}

    hosts: dict[str, Any] = {}
    for opaque, canonical in selected.items():
        load_entry = load_mod._get_host_load_entry(canonical, fresh=fresh)
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


@router.get("")
async def occupancy(
    host_id: str | None = Query(default=None),
    fresh: bool = False,
) -> JSONResponse:
    payload = occupancy_payload(host_id=host_id, fresh=fresh)
    return JSONResponse(content=payload, headers={"Cache-Control": "no-store"})
