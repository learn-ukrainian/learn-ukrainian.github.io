"""Per-host project state read model and loopback-only reporter ingest."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from scripts.api.monitor_context import MonitorContext, get_ctx
from scripts.api.observer_presence import _direct_loopback_peer
from scripts.api.occupancy import DEFAULT_HOST_IDS, parse_host_id_map
from scripts.api.occupancy_local import resolve_launcher_host_id, self_host_opaque_ids
from scripts.api.occupancy_sanitize import opaque_host_id as _opaque_host_id
from scripts.api.project_state_collect import collect_local_document
from scripts.api.project_state_sanitize import ProjectStateValidationError, validate_report_document
from scripts.api.project_state_store import (
    PROJECT_STATE_SCHEMA,
    PROJECT_STATE_SCHEMA_V2,
    REPORT_TTL_SECONDS,
    CollectedAtError,
    StaleReportError,
    freshness_from_age,
    get_live_report,
    lane_usage_status_from_document,
    shape_host_payload,
    unknown_host_payload,
    upsert_report,
    workers_status_from_document,
)

router = APIRouter(prefix="/projects/v1", tags=["fleet-projects"])

EXTRA_REPORTER_HOST_IDS = frozenset({"mac-operator"})

# The API host is the only project-state reporter that is collected on the
# request path. Keep its snapshot short-lived, but retain a bounded last-good
# value while one refresh is in flight, matching the occupancy host-load
# stale-while-revalidate behavior.
LOCAL_DOCUMENT_FRESH_S = 30.0
LOCAL_DOCUMENT_MAX_STALE_S = 300.0
LOCAL_DOCUMENT_REFRESH_BACKOFF_S = 30.0


@dataclass(frozen=True)
class LocalDocumentSnapshot:
    document: dict[str, Any] | None
    age_s: float | None
    freshness: str


@dataclass(frozen=True)
class _LocalDocumentCacheEntry:
    document: dict[str, Any]
    stored_at_mono: float


_LOCAL_DOCUMENT_CACHE: dict[str, _LocalDocumentCacheEntry] = {}
_LOCAL_DOCUMENT_REFRESH_THREADS: dict[str, threading.Thread] = {}
_LOCAL_DOCUMENT_REFRESH_BACKOFF_UNTIL: dict[str, float] = {}
_LOCAL_DOCUMENT_MISS_EVENTS: dict[str, threading.Event] = {}
_LOCAL_DOCUMENT_GENERATION = 0
_LOCAL_DOCUMENT_LOCK = threading.Lock()


def _local_document_snapshot(
    entry: _LocalDocumentCacheEntry,
    *,
    now_mono: float,
) -> LocalDocumentSnapshot:
    age = max(0.0, now_mono - entry.stored_at_mono)
    age_s = round(age, 2)
    if age <= LOCAL_DOCUMENT_FRESH_S:
        return LocalDocumentSnapshot(entry.document, age_s, "fresh")
    if age <= LOCAL_DOCUMENT_MAX_STALE_S:
        return LocalDocumentSnapshot(entry.document, age_s, "stale")
    return LocalDocumentSnapshot(None, age_s, "unknown")


def _peek_local_document_snapshot(host_id: str) -> LocalDocumentSnapshot | None:
    now_mono = time.monotonic()
    with _LOCAL_DOCUMENT_LOCK:
        entry = _LOCAL_DOCUMENT_CACHE.get(host_id)
        if entry is None:
            return None
        return _local_document_snapshot(entry, now_mono=now_mono)


def _refresh_local_document(host_id: str, generation: int) -> None:
    document: dict[str, Any] | None = None
    try:
        collected = collect_local_document(host_id)
        if isinstance(collected, dict):
            document = collected
    except Exception:
        # A failed refresh must not take down a read that has a last-good
        # snapshot. The caller will expose its age and stale/unknown state.
        document = None

    current_thread = threading.current_thread()
    with _LOCAL_DOCUMENT_LOCK:
        if generation != _LOCAL_DOCUMENT_GENERATION:
            return
        if document is not None:
            _LOCAL_DOCUMENT_CACHE[host_id] = _LocalDocumentCacheEntry(document, time.monotonic())
            _LOCAL_DOCUMENT_REFRESH_BACKOFF_UNTIL.pop(host_id, None)
        else:
            _LOCAL_DOCUMENT_REFRESH_BACKOFF_UNTIL[host_id] = time.monotonic() + LOCAL_DOCUMENT_REFRESH_BACKOFF_S
        if _LOCAL_DOCUMENT_REFRESH_THREADS.get(host_id) is current_thread:
            _LOCAL_DOCUMENT_REFRESH_THREADS.pop(host_id, None)


def _schedule_local_document_refresh(host_id: str) -> None:
    now_mono = time.monotonic()
    with _LOCAL_DOCUMENT_LOCK:
        existing = _LOCAL_DOCUMENT_REFRESH_THREADS.get(host_id)
        if existing is not None and existing.is_alive():
            return
        backoff_until = _LOCAL_DOCUMENT_REFRESH_BACKOFF_UNTIL.get(host_id)
        if backoff_until is not None and now_mono < backoff_until:
            return
        thread = threading.Thread(
            target=_refresh_local_document,
            args=(host_id, _LOCAL_DOCUMENT_GENERATION),
            daemon=True,
            name=f"project-state-refresh-{host_id}",
        )
        _LOCAL_DOCUMENT_REFRESH_THREADS[host_id] = thread
        thread.start()


def _collect_missing_local_document(host_id: str) -> LocalDocumentSnapshot:
    """Synchronously fill a cold cache, with one collector per host."""
    with _LOCAL_DOCUMENT_LOCK:
        event = _LOCAL_DOCUMENT_MISS_EVENTS.get(host_id)
        owner = event is None
        if owner:
            event = threading.Event()
            _LOCAL_DOCUMENT_MISS_EVENTS[host_id] = event
            generation = _LOCAL_DOCUMENT_GENERATION

    if not owner:
        event.wait()
        snapshot = _peek_local_document_snapshot(host_id)
        if snapshot is not None:
            return snapshot
        return LocalDocumentSnapshot(None, None, "unknown")

    document: dict[str, Any] | None = None
    try:
        collected = collect_local_document(host_id)
        if isinstance(collected, dict):
            document = collected
    except Exception:
        document = None
    finally:
        with _LOCAL_DOCUMENT_LOCK:
            if generation == _LOCAL_DOCUMENT_GENERATION and document is not None:
                _LOCAL_DOCUMENT_CACHE[host_id] = _LocalDocumentCacheEntry(document, time.monotonic())
                _LOCAL_DOCUMENT_REFRESH_BACKOFF_UNTIL.pop(host_id, None)
            if _LOCAL_DOCUMENT_MISS_EVENTS.get(host_id) is event:
                _LOCAL_DOCUMENT_MISS_EVENTS.pop(host_id, None)
            event.set()

    snapshot = _peek_local_document_snapshot(host_id)
    if snapshot is not None:
        return snapshot
    return LocalDocumentSnapshot(None, None, "unknown")


def get_cached_local_document(host_id: str) -> LocalDocumentSnapshot:
    """Return the API host's cached report, refreshing stale data in background."""
    snapshot = _peek_local_document_snapshot(host_id)
    if snapshot is None:
        return _collect_missing_local_document(host_id)
    if snapshot.freshness != "fresh":
        _schedule_local_document_refresh(host_id)
    return snapshot


def reset_local_document_cache() -> None:
    """Clear cached self-reports and wait briefly for test refreshes to finish."""
    global _LOCAL_DOCUMENT_GENERATION
    with _LOCAL_DOCUMENT_LOCK:
        _LOCAL_DOCUMENT_GENERATION += 1
        threads = list(_LOCAL_DOCUMENT_REFRESH_THREADS.values())
        _LOCAL_DOCUMENT_CACHE.clear()
        _LOCAL_DOCUMENT_REFRESH_THREADS.clear()
        _LOCAL_DOCUMENT_REFRESH_BACKOFF_UNTIL.clear()
        _LOCAL_DOCUMENT_MISS_EVENTS.clear()
    for thread in threads:
        thread.join(timeout=2.0)


def allowed_reporter_host_ids(ctx: MonitorContext | None = None) -> frozenset[str]:
    # A fixture-built context is a disposable, isolated instance: it must never
    # resolve a reporter host id from the real process environment, mirroring
    # the outside-root guard MonitorContext already applies to db paths.
    if ctx is not None and ctx.root is not None:
        return frozenset()
    ids = set(parse_host_id_map().values())
    ids.update(EXTRA_REPORTER_HOST_IDS)
    return {host_id for host_id in ids if _opaque_host_id(host_id)}


def _selected_host_ids(host_id: str | None, ctx: MonitorContext | None = None) -> list[str]:
    allowed = allowed_reporter_host_ids(ctx)
    if host_id is not None:
        if host_id not in allowed and host_id not in DEFAULT_HOST_IDS:
            raise HTTPException(status_code=400, detail="unknown host_id")
        return [host_id]
    selected: list[str] = []
    for default_id in DEFAULT_HOST_IDS:
        if default_id not in selected:
            selected.append(default_id)
    for mapped_id in sorted(allowed):
        if mapped_id not in selected:
            selected.append(mapped_id)
    return selected


def _self_host_ids() -> set[str]:
    self_id = resolve_launcher_host_id()
    ids: set[str] = set()
    if self_id and self_id != "local" and _opaque_host_id(self_id):
        ids.add(self_id)
    ids.update(self_host_opaque_ids(parse_host_id_map()))
    return ids


def _live_local_document(host_id: str) -> dict[str, Any] | None:
    return get_cached_local_document(host_id).document


def _local_document_metadata(host_id: str, document: dict[str, Any]) -> tuple[float, str]:
    snapshot = _peek_local_document_snapshot(host_id)
    if snapshot is not None and snapshot.document is document:
        return snapshot.age_s or 0.0, snapshot.freshness
    # Keep the existing private seam useful for tests and callers that inject
    # a document without going through the in-process cache.
    return 0.0, "fresh"


def _payload_for_host(
    host_id: str,
    *,
    now_mono: float,
    store: Any = None,
) -> dict[str, Any]:
    if host_id in _self_host_ids():
        document = _live_local_document(host_id)
        if document is None:
            return unknown_host_payload(host_id)
        age_s, freshness = _local_document_metadata(host_id, document)
        return shape_host_payload(
            document,
            age_s=age_s,
            freshness=freshness,
            collected_at=document["collected_at"],
        )

    stored = get_live_report(host_id, now_mono=now_mono, store=store)
    if stored is None:
        return unknown_host_payload(host_id)
    age_s = now_mono - stored.received_at_mono
    freshness = freshness_from_age(age_s)
    return shape_host_payload(
        stored.document,
        age_s=age_s,
        freshness=freshness,
        collected_at=stored.document["collected_at"],
    )


def projects_payload(*, host_id: str | None = None, ctx: MonitorContext | None = None) -> dict[str, Any]:
    now_mono = time.monotonic()
    report_store = None if ctx is None else ctx.stores.report_store
    hosts: dict[str, Any] = {}
    for opaque in _selected_host_ids(host_id, ctx):
        hosts[opaque] = _payload_for_host(opaque, now_mono=now_mono, store=report_store)
    return {
        "schema": PROJECT_STATE_SCHEMA,
        "observed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "hosts": hosts,
    }


class ProjectStateReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host_id: str
    primary: dict[str, Any]
    worktrees: dict[str, Any]
    services: list[dict[str, Any]]
    collected_at: str
    workers: list[dict[str, Any]] | None = None
    lane_usage: list[dict[str, Any]] | None = None


@router.get("")
async def get_projects(
    host_id: str | None = Query(default=None),
    ctx: MonitorContext = Depends(get_ctx),
) -> JSONResponse:
    payload = projects_payload(host_id=host_id, ctx=ctx)
    return JSONResponse(content=payload, headers={"Cache-Control": "no-store"})


@router.post("/report")
async def post_project_report(
    request: Request,
    body: ProjectStateReport,
    ctx: MonitorContext = Depends(get_ctx),
) -> JSONResponse:
    no_store = {"Cache-Control": "no-store"}
    if not _direct_loopback_peer(request):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"}, headers=no_store)

    allowed = allowed_reporter_host_ids(ctx)
    if body.host_id not in allowed:
        return JSONResponse(status_code=400, content={"detail": "unknown host_id"}, headers=no_store)

    document = body.model_dump(exclude_none=True)
    try:
        validate_report_document(document)
    except ProjectStateValidationError:
        return JSONResponse(status_code=400, content={"detail": "invalid project state report"}, headers=no_store)

    try:
        row = upsert_report(document, store=ctx.stores.report_store)
    except CollectedAtError:
        return JSONResponse(status_code=400, content={"detail": "invalid collected_at"}, headers=no_store)
    except StaleReportError:
        return JSONResponse(status_code=409, content={"detail": "stale_report"}, headers=no_store)

    schema = PROJECT_STATE_SCHEMA_V2 if "workers" in document else PROJECT_STATE_SCHEMA
    return JSONResponse(
        content={
            "host_id": row.host_id,
            "received": True,
            "ttl_seconds": REPORT_TTL_SECONDS,
            "schema": schema,
            "workers_status": workers_status_from_document(document),
            "lane_usage_status": lane_usage_status_from_document(document),
        },
        headers=no_store,
    )
