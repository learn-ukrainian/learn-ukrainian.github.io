"""Monitor occupancy: opaque host_id plus occupants, reusing atlas load cache.

Sibling of ``GET /api/atlas-jobs/load`` — one occupancy board, no second probe
path. Canonical SSH aliases never appear as JSON keys. Map them with
``MONITOR_OCCUPANCY_HOST_IDS`` (``alias=opaque-id,...``). Occupants come from
the atlas-job registry, the cached job unit, local session-stream driver
leases, and optional occupancy markers. Observer heartbeats from
``POST /api/observer/presence`` are partitioned by opaque host id; legacy rows
remain under ``cloud-observer`` and reuse the same ``burn_state`` /
``burn_sources`` occupancy shape (no RAM lease, no host probe).
"""

from __future__ import annotations

import asyncio
import math
import os
import sys
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from scripts.api import atlas_jobs_router as load_mod
from scripts.api import config
from scripts.api.monitor_context import MonitorContext, get_ctx
from scripts.api.observer_presence import (
    PRESENCE_FRESHNESS_SECONDS,
    ObserverPresence,
    PresenceStore,
    list_live,
)
from scripts.api.occupancy_local import OccupancyRead, read_markers, read_session_streams
from scripts.api.occupancy_sanitize import CLOUD_OBSERVER_HOST_ID
from scripts.api.occupancy_sanitize import occupant as _occupant
from scripts.api.occupancy_sanitize import opaque_host_id as _opaque_host_id
from scripts.api.project_state_store import (
    REPORT_TTL_SECONDS,
    ReportStore,
    all_weekly_lanes_at_or_over_pace,
    any_lane_under_weekly_pace,
    get_freshest_lane_usage,
)
from scripts.lexicon.runner import atlas_job

router = APIRouter(tags=["occupancy"])

OCCUPANCY_SCHEMA = "monitor-occupancy.v1"
_LOAD_METRIC_KEYS = ("cpu_count", "loadavg", "mem", "disk")
_FOUNDRY_AGENTS = frozenset({"foundry", "evidence-compiler"})
_FOUNDRY_TASK_IDS = frozenset({"ukrainian-data-foundry", "phase3-cycle007-evidence-compiler"})


# Default glance: one production Linux host + Mac observer. ``host-job`` remains
# queryable only when mapped; it is never a ghost glance row.
DEFAULT_GLANCE_HOST_IDS = ("host-teacher",)
# Back-compat alias: callers that enumerate the default glance use this name.
DEFAULT_HOST_IDS = DEFAULT_GLANCE_HOST_IDS
# Production Linux opaque id (empty-map API host fills this row in-process).
PRODUCTION_LINUX_HOST_ID = DEFAULT_GLANCE_HOST_IDS[0]
# Unmapped ``host-job`` is not queryable; mapped values come from the env map.
QUERYABLE_DEFAULT_HOST_IDS = frozenset({PRODUCTION_LINUX_HOST_ID})
MAC_OPERATOR_HOST_ID = "mac-operator"
_BURN_SOURCE_NAMES = ("atlas_job", "driver", "foundry", "service", "observer")
_BURN_SOURCE_STATES = frozenset({"active", "clear", "unknown"})
EMPTY_HOST_IDLE_THRESHOLD_S = 15 * 60
_BOOT_MONO = time.monotonic()
_IDLE_LOCK = threading.Lock()
_idle_since_mono: dict[str, float] = {}
_ever_had_activity: dict[str, bool] = {}


@dataclass(frozen=True)
class OccupancySnapshot:
    """Immutable per-request inputs shared across every host shape."""

    host_id_map: dict[str, str]
    live_presence: tuple[ObserverPresence, ...]
    now_mono: float
    now: datetime


def reset_empty_host_tracking() -> None:
    """Test helper: clear idle-since memo state."""
    with _IDLE_LOCK:
        _idle_since_mono.clear()
        _ever_had_activity.clear()


def _idle_duration_s(host_id: str, idle_or_empty: bool, *, now_mono: float) -> float:
    with _IDLE_LOCK:
        if not idle_or_empty:
            _idle_since_mono.pop(host_id, None)
            _ever_had_activity[host_id] = True
            return 0.0
        if host_id not in _idle_since_mono:
            _idle_since_mono[host_id] = now_mono if _ever_had_activity.get(host_id) else _BOOT_MONO
        return max(0.0, now_mono - _idle_since_mono[host_id])


def _empty_host_attention_item(
    host_id: str,
    *,
    now_mono: float,
    now: datetime | None = None,
    report_store: ReportStore | None = None,
) -> str | None:
    freshest = get_freshest_lane_usage(now_mono=now_mono, store=report_store)
    if freshest is None or freshest.age_s > REPORT_TTL_SECONDS:
        return f"empty_host_unknown_capacity:{host_id}"
    if any_lane_under_weekly_pace(freshest.lanes, now=now):
        return f"empty_host_underused:{host_id}"
    if all_weekly_lanes_at_or_over_pace(freshest.lanes, now=now):
        return None
    return f"empty_host_unknown_capacity:{host_id}"


def _evaluate_attention(
    hosts: dict[str, Any],
    *,
    now_mono: float | None = None,
    now: datetime | None = None,
    report_store: ReportStore | None = None,
) -> list[str]:
    stamp = time.monotonic() if now_mono is None else now_mono
    clock = now or datetime.now(UTC)
    attention: list[str] = []
    for host_id, host in hosts.items():
        if host_id == CLOUD_OBSERVER_HOST_ID:
            continue
        if host.get("status") == "unavailable":
            continue
        if not host.get("idle_or_empty"):
            _idle_duration_s(host_id, False, now_mono=stamp)
            continue
        idle_s = _idle_duration_s(host_id, True, now_mono=stamp)
        if idle_s < EMPTY_HOST_IDLE_THRESHOLD_S:
            continue
        item = _empty_host_attention_item(
            host_id, now_mono=stamp, now=clock, report_store=report_store
        )
        if item is not None:
            attention.append(item)
    return attention


def _unavailable_load_entry(*, now: datetime | None = None) -> dict[str, Any]:
    clock = now or datetime.now(UTC)
    return {
        "status": "unavailable",
        "error": "unreachable",
        "observed_at": clock.isoformat().replace("+00:00", "Z"),
        "age_seconds": 0.0,
    }


def fills_in_process_api_host(opaque: str, mapping: dict[str, str]) -> bool:
    """True when empty-map Linux API should collect this glance row locally."""
    if mapping:
        return False
    if opaque != PRODUCTION_LINUX_HOST_ID:
        return False
    return sys.platform != "darwin"


def _in_process_load_run_root() -> Path:
    """Disk root for in-process load. Prefer ATLAS_RUN_ROOT; else checkout.

    The API systemd unit does not set ``ATLAS_RUN_ROOT``. ``collect_host_load``
    only uses the path for local disk_usage, so the Monitor checkout is a safe
    checkout-mode default — never call ``atlas_job._run_root()`` here.
    """
    override = os.environ.get("ATLAS_RUN_ROOT", "").strip()
    if override:
        return Path(override)
    return Path(config.PROJECT_ROOT)


def _in_process_api_host_load(*, now: datetime | None = None) -> dict[str, Any]:
    """Collect load for the empty-map production Linux glance row (no SSH)."""
    clock = now or datetime.now(UTC)
    try:
        metrics = atlas_job.collect_host_load(run_root=_in_process_load_run_root())
    except Exception:
        return _unavailable_load_entry(now=clock)
    if not isinstance(metrics, dict):
        return _unavailable_load_entry(now=clock)
    shaped: dict[str, Any] = {
        "status": "fresh",
        "observed_at": clock.isoformat().replace("+00:00", "Z"),
        "age_seconds": 0.0,
    }
    shaped.update(metrics)
    return shaped


def _load_entry_for_selected(
    opaque: str,
    canonical: str | None,
    *,
    mapping: dict[str, str],
    fresh: bool,
    now: datetime,
) -> dict[str, Any]:
    if canonical is not None:
        return load_mod._get_host_load_entry(canonical, fresh=fresh)
    if fills_in_process_api_host(opaque, mapping):
        return _in_process_api_host_load(now=now)
    return _unavailable_load_entry(now=now)


async def _load_entry_for_selected_async(
    opaque: str,
    canonical: str | None,
    *,
    mapping: dict[str, str],
    fresh: bool,
    now: datetime,
) -> dict[str, Any]:
    if canonical is not None:
        return await load_mod._get_host_load_entry_async(canonical, fresh=fresh)
    if fills_in_process_api_host(opaque, mapping):
        return await asyncio.to_thread(_in_process_api_host_load, now=now)
    return _unavailable_load_entry(now=now)


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


def _build_snapshot(
    *,
    presence_store: PresenceStore | None = None,
    host_id_map: dict[str, str] | None = None,
    now_mono: float | None = None,
    now: datetime | None = None,
) -> OccupancySnapshot:
    stamp = time.monotonic() if now_mono is None else now_mono
    return OccupancySnapshot(
        host_id_map=dict(host_id_map if host_id_map is not None else parse_host_id_map()),
        live_presence=tuple(list_live(now_mono=stamp, store=presence_store)),
        now_mono=stamp,
        now=now or datetime.now(UTC),
    )


def _read_occupants_from_registry(
    canonical: str,
) -> tuple[list[dict[str, str | None]], bool]:
    occupants: list[dict[str, str | None]] = []
    seen: set[tuple[str, str, str]] = set()
    try:
        rows = atlas_job.list_registry()
    except Exception:
        return [], False
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
        key = (occupant["kind"], occupant["task_id"] or "", occupant.get("instance_id") or "")
        if key in seen:
            continue
        seen.add(key)
        occupants.append(occupant)
    return occupants, True


def _occupants_from_registry(canonical: str) -> list[dict[str, str | None]]:
    """Compatibility list-only view of the Atlas registry source."""
    return _read_occupants_from_registry(canonical)[0]


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
    seen: set[tuple[str, str, str]] = set()
    for group in groups:
        for occupant in group:
            key = (
                occupant["kind"],
                occupant["task_id"] or "",
                occupant.get("instance_id") or "",
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(occupant)
    return merged


def _safe_age(value: Any) -> float:
    try:
        age = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(age):
        return 0.0
    return round(max(0.0, age), 2)


def _source_state(*, readable: bool, occupants: list[dict[str, str | None]], active: bool = False) -> str:
    if not readable:
        return "unknown"
    state = "active" if active or occupants else "clear"
    return state if state in _BURN_SOURCE_STATES else "unknown"


def _atlas_load_is_active(load_entry: dict[str, Any]) -> bool:
    job_unit = load_entry.get("job_unit")
    if isinstance(job_unit, dict):
        try:
            if int(job_unit.get("active_count") or 0) > 0:
                return True
        except (TypeError, ValueError):
            pass
    loadavg = load_entry.get("loadavg")
    if isinstance(loadavg, list) and loadavg:
        try:
            return float(loadavg[0]) >= 1.0
        except (TypeError, ValueError, IndexError):
            return False
    return False


def _atlas_job_read(
    canonical: str | None,
    load_entry: dict[str, Any],
) -> tuple[list[dict[str, str | None]], dict[str, Any]]:
    if canonical is None:
        registry_occupants: list[dict[str, str | None]] = []
        registry_readable = False
    else:
        registry_occupants, registry_readable = _read_occupants_from_registry(canonical)
    job_unit_occupants = _occupants_from_job_unit(canonical or "", load_entry)
    occupants = _merge_occupants(registry_occupants, job_unit_occupants)
    load_readable = str(load_entry.get("status") or "") in {"fresh", "stale"}
    readable = registry_readable and load_readable
    source = {
        "state": _source_state(
            readable=readable,
            occupants=occupants,
            active=_atlas_load_is_active(load_entry),
        ),
        "observation_age_s": _safe_age(load_entry.get("age_seconds")),
    }
    return occupants, source


def _local_source_payload(
    read: OccupancyRead,
    *,
    occupants: list[dict[str, str | None]] | None = None,
) -> dict[str, Any]:
    source_occupants = read.occupants if occupants is None else occupants
    return {
        "state": _source_state(readable=read.readable, occupants=source_occupants),
        "observation_age_s": _safe_age(read.observation_age_s),
    }


def _is_foundry_occupant(occupant: dict[str, str | None]) -> bool:
    return occupant.get("agent") in _FOUNDRY_AGENTS or occupant.get("task_id") in _FOUNDRY_TASK_IDS


def _active_observer_occupants(
    occupants: list[dict[str, str | None]],
) -> list[dict[str, str | None]]:
    return [
        occupant
        for occupant in occupants
        if occupant.get("kind") == "observer" and occupant.get("status") != "idle"
    ]


def _burn_state(burn_sources: dict[str, dict[str, Any]]) -> str:
    states = {str(source.get("state")) for source in burn_sources.values()}
    if "active" in states:
        return "active"
    if "unknown" in states:
        return "unknown"
    return "idle"


def _shape_host(
    host_id: str,
    load_entry: dict[str, Any],
    occupants: list[dict[str, str | None]],
    burn_state: str,
    burn_sources: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    status = str(load_entry.get("status") or "unavailable")
    valid_status = status if status in {"fresh", "stale", "unavailable"} else "unavailable"
    ai_seats: list[str] = []
    for o in occupants:
        agent = o.get("agent")
        if agent and agent not in ai_seats:
            ai_seats.append(str(agent))
    shaped: dict[str, Any] = {
        "host_id": host_id,
        "status": valid_status,
        "observed_at": load_entry.get("observed_at"),
        "age_seconds": load_entry.get("age_seconds", 0.0),
        "occupants": occupants,
        "occupant_count": len(occupants),
        "ai_seats": ai_seats,
        "burn_state": burn_state,
        "burn_sources": burn_sources,
        "idle_or_empty": burn_state == "idle",
    }
    if shaped["status"] == "unavailable":
        shaped["error"] = "unreachable"
        return shaped
    for key in _LOAD_METRIC_KEYS:
        if key in load_entry:
            shaped[key] = load_entry[key]
    return shaped


def _occupants_from_observers(
    host_id: str,
    *,
    snapshot: OccupancySnapshot,
) -> list[dict[str, str | None]]:
    occupants: list[dict[str, str | None]] = []
    for row in snapshot.live_presence:
        if row.host_id != host_id:
            continue
        occupant = _occupant(
            kind="observer",
            agent=row.agent,
            task_id=row.task_id,
            epic=row.epic,
            status=row.status,
            instance_id=row.instance_id,
        )
        if occupant is not None:
            occupants.append(occupant)
    return occupants


def _presence_age_s(host_id: str, *, snapshot: OccupancySnapshot) -> float:
    ages = [
        max(0.0, snapshot.now_mono - row.updated_at_mono)
        for row in snapshot.live_presence
        if row.host_id == host_id
    ]
    if not ages:
        return 0.0
    return _safe_age(min(ages))


def _observer_source_payload(
    observer_occupants: list[dict[str, str | None]],
    *,
    observation_age_s: float,
) -> dict[str, Any]:
    return {
        "state": _source_state(
            readable=True,
            occupants=_active_observer_occupants(observer_occupants),
        ),
        "observation_age_s": _safe_age(observation_age_s),
    }


def _clear_probe_sources(*, observation_age_s: float = 0.0) -> dict[str, dict[str, Any]]:
    """Atlas/driver/foundry/service do not apply to the presence-only observer bucket."""
    age = _safe_age(observation_age_s)
    return {
        name: {"state": "clear", "observation_age_s": age}
        for name in ("atlas_job", "driver", "foundry", "service")
    }


def _presence_load_entry(
    host_id: str,
    *,
    snapshot: OccupancySnapshot,
) -> dict[str, Any]:
    rows = [row for row in snapshot.live_presence if row.host_id == host_id]
    if not rows:
        return _unavailable_load_entry(now=snapshot.now)
    newest = max(rows, key=lambda row: row.updated_at_mono)
    age = _safe_age(snapshot.now_mono - newest.updated_at_mono)
    status = "fresh" if age <= PRESENCE_FRESHNESS_SECONDS else "stale"
    return {
        "status": status,
        "observed_at": newest.updated_at,
        "age_seconds": age,
    }


def _shape_cloud_observer(
    occupants: list[dict[str, str | None]],
    *,
    snapshot: OccupancySnapshot,
) -> dict[str, Any]:
    """Presence-gated observer bucket — same occupancy shape as probed hosts.

    No host probe, no RAM lease, no load metrics. Burn derives only from
    ``burn_sources``: probe sources stay clear, and the ``observer`` source
    explains working/blocked heartbeats.
    """
    load_entry = _presence_load_entry(CLOUD_OBSERVER_HOST_ID, snapshot=snapshot)
    age = _safe_age(load_entry.get("age_seconds"))
    burn_sources = _clear_probe_sources(observation_age_s=age)
    burn_sources["observer"] = _observer_source_payload(occupants, observation_age_s=age)
    return _shape_host(
        CLOUD_OBSERVER_HOST_ID,
        load_entry,
        occupants,
        _burn_state(burn_sources),
        burn_sources,
    )


def _attach_cloud_observer(
    payload: dict[str, Any],
    host_id: str | None,
    *,
    snapshot: OccupancySnapshot,
) -> dict[str, Any]:
    if host_id is not None and host_id != CLOUD_OBSERVER_HOST_ID:
        return payload
    occupants = _occupants_from_observers(CLOUD_OBSERVER_HOST_ID, snapshot=snapshot)
    if not occupants and host_id is None:
        return payload
    payload["hosts"][CLOUD_OBSERVER_HOST_ID] = _shape_cloud_observer(
        occupants, snapshot=snapshot
    )
    return payload


def _selected_hosts(
    host_id: str | None,
    *,
    snapshot: OccupancySnapshot,
) -> dict[str, str | None]:
    if host_id == CLOUD_OBSERVER_HOST_ID:
        return {}

    mapping = snapshot.host_id_map
    reverse = {opaque: canonical for canonical, opaque in mapping.items()}
    if host_id is not None:
        if host_id == MAC_OPERATOR_HOST_ID:
            return {host_id: None}
        if host_id in reverse:
            return {host_id: reverse[host_id]}
        if host_id in QUERYABLE_DEFAULT_HOST_IDS:
            return {host_id: reverse.get(host_id)}
        raise HTTPException(status_code=400, detail="unknown host_id")

    selected: dict[str, str | None] = {}
    for default_id in DEFAULT_GLANCE_HOST_IDS:
        selected[default_id] = reverse.get(default_id)
    for opaque, canonical in reverse.items():
        if opaque not in selected:
            selected[opaque] = canonical
    # Always keep the Mac glance row. Observer presence is an in-process TTL
    # store, so a quiet or freshly restarted Monitor must not drop the seat.
    # Load stays unknown unless a later occupant/load source exists.
    selected[MAC_OPERATOR_HOST_ID] = None
    return selected


def _empty_payload(*, now: datetime) -> dict[str, Any]:
    return {
        "schema": OCCUPANCY_SCHEMA,
        "observed_at": now.isoformat().replace("+00:00", "Z"),
        "hosts": {},
        "attention": [],
    }


def _burn_sources_for_host(
    *,
    atlas_source: dict[str, Any],
    driver_read: OccupancyRead,
    marker_read: OccupancyRead,
    foundry_occupants: list[dict[str, str | None]],
    service_occupants: list[dict[str, str | None]],
    observer_occupants: list[dict[str, str | None]],
    observer_age_s: float,
) -> dict[str, dict[str, Any]]:
    return dict(
        zip(
            _BURN_SOURCE_NAMES,
            (
                atlas_source,
                _local_source_payload(driver_read),
                _local_source_payload(marker_read, occupants=foundry_occupants),
                _local_source_payload(marker_read, occupants=service_occupants),
                _observer_source_payload(observer_occupants, observation_age_s=observer_age_s),
            ),
            strict=True,
        )
    )


def _payload_from_entries(
    selected: dict[str, str | None],
    load_entries: dict[str, dict[str, Any]],
    *,
    snapshot: OccupancySnapshot,
) -> dict[str, Any]:
    hosts: dict[str, Any] = {}
    mapping = snapshot.host_id_map
    for opaque, canonical in selected.items():
        load_entry = load_entries.get(opaque) or _unavailable_load_entry(now=snapshot.now)
        if canonical is None and fills_in_process_api_host(opaque, mapping):
            # Empty-map API host: no remote registry key; load is local.
            # Do not treat whole-machine loadavg as atlas_job burn — that signal
            # is for remote atlas runners with SSH load samples.
            # Match remote atlas_job honesty: unavailable/failed load => unknown,
            # never clear (which would imply a readable idle glance).
            atlas_occupants: list[dict[str, str | None]] = []
            load_readable = str(load_entry.get("status") or "") in {"fresh", "stale"}
            job_unit = load_entry.get("job_unit")
            job_active = False
            if isinstance(job_unit, dict):
                try:
                    job_active = int(job_unit.get("active_count") or 0) > 0
                except (TypeError, ValueError):
                    job_active = False
            atlas_source = {
                "state": _source_state(
                    readable=load_readable,
                    occupants=atlas_occupants,
                    active=job_active,
                ),
                "observation_age_s": _safe_age(load_entry.get("age_seconds")),
            }
        else:
            atlas_occupants, atlas_source = _atlas_job_read(canonical, load_entry)
        driver_read = read_session_streams(
            host_id=opaque,
            mapping=mapping,
            selected=selected,
            now=snapshot.now,
        )
        marker_read = read_markers(host_id=opaque, now=snapshot.now)
        observer_occupants = _occupants_from_observers(opaque, snapshot=snapshot)
        groups = [atlas_occupants, driver_read.occupants, marker_read.occupants, observer_occupants]
        occupants = _merge_occupants(*groups)
        foundry_occupants = [
            occupant for occupant in marker_read.occupants if _is_foundry_occupant(occupant)
        ]
        service_occupants = [
            occupant for occupant in marker_read.occupants if not _is_foundry_occupant(occupant)
        ]
        burn_sources = _burn_sources_for_host(
            atlas_source=atlas_source,
            driver_read=driver_read,
            marker_read=marker_read,
            foundry_occupants=foundry_occupants,
            service_occupants=service_occupants,
            observer_occupants=observer_occupants,
            observer_age_s=_presence_age_s(opaque, snapshot=snapshot),
        )
        hosts[opaque] = _shape_host(
            opaque,
            load_entry,
            occupants,
            _burn_state(burn_sources),
            burn_sources,
        )

    return {
        "schema": OCCUPANCY_SCHEMA,
        "observed_at": snapshot.now.isoformat().replace("+00:00", "Z"),
        "hosts": hosts,
    }


def _finalize_payload(
    payload: dict[str, Any],
    host_id: str | None,
    *,
    snapshot: OccupancySnapshot,
    report_store: ReportStore | None = None,
) -> dict[str, Any]:
    payload = _attach_cloud_observer(payload, host_id, snapshot=snapshot)
    payload["attention"] = _evaluate_attention(
        payload.get("hosts", {}),
        now_mono=snapshot.now_mono,
        now=snapshot.now,
        report_store=report_store,
    )
    return payload


def occupancy_payload(
    *,
    host_id: str | None = None,
    fresh: bool = False,
    ctx: MonitorContext | None = None,
) -> dict[str, Any]:
    """Build the synchronous cache-only payload for non-HTTP callers."""
    presence_store = None if ctx is None else ctx.stores.presence_store
    report_store = None if ctx is None else ctx.stores.report_store
    snapshot = _build_snapshot(presence_store=presence_store)
    selected = _selected_hosts(host_id, snapshot=snapshot)
    if not selected:
        return _finalize_payload(
            _empty_payload(now=snapshot.now),
            host_id,
            snapshot=snapshot,
            report_store=report_store,
        )

    load_entries: dict[str, dict[str, Any]] = {}
    for opaque, canonical in selected.items():
        load_entries[opaque] = _load_entry_for_selected(
            opaque,
            canonical,
            mapping=snapshot.host_id_map,
            fresh=fresh,
            now=snapshot.now,
        )
    return _finalize_payload(
        _payload_from_entries(selected, load_entries, snapshot=snapshot),
        host_id,
        snapshot=snapshot,
        report_store=report_store,
    )


async def _occupancy_payload_async(
    *,
    host_id: str | None = None,
    fresh: bool = False,
    ctx: MonitorContext | None = None,
) -> dict[str, Any]:
    presence_store = None if ctx is None else ctx.stores.presence_store
    report_store = None if ctx is None else ctx.stores.report_store
    snapshot = _build_snapshot(presence_store=presence_store)
    selected = _selected_hosts(host_id, snapshot=snapshot)
    if not selected:
        return _finalize_payload(
            _empty_payload(now=snapshot.now),
            host_id,
            snapshot=snapshot,
            report_store=report_store,
        )

    tasks = []
    keys = []
    for opaque, canonical in selected.items():
        keys.append(opaque)
        tasks.append(
            _load_entry_for_selected_async(
                opaque,
                canonical,
                mapping=snapshot.host_id_map,
                fresh=fresh,
                now=snapshot.now,
            )
        )

    entries = await asyncio.gather(*tasks)
    load_entries = dict(zip(keys, entries, strict=True))
    return _finalize_payload(
        _payload_from_entries(selected, load_entries, snapshot=snapshot),
        host_id,
        snapshot=snapshot,
        report_store=report_store,
    )


@router.get("")
async def occupancy(
    host_id: str | None = Query(default=None),
    fresh: bool = False,
    ctx: MonitorContext = Depends(get_ctx),
) -> JSONResponse:
    payload = await _occupancy_payload_async(host_id=host_id, fresh=fresh, ctx=ctx)
    return JSONResponse(content=payload, headers={"Cache-Control": "no-store"})
