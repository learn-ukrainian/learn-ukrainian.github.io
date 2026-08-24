"""Per-host project state read model and loopback-only reporter ingest."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

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


def allowed_reporter_host_ids() -> frozenset[str]:
    ids = set(parse_host_id_map().values())
    ids.update(EXTRA_REPORTER_HOST_IDS)
    return {host_id for host_id in ids if _opaque_host_id(host_id)}


def _selected_host_ids(host_id: str | None) -> list[str]:
    allowed = allowed_reporter_host_ids()
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
    return collect_local_document(host_id)


def _payload_for_host(host_id: str, *, now_mono: float) -> dict[str, Any]:
    if host_id in _self_host_ids():
        document = _live_local_document(host_id)
        if document is None:
            return unknown_host_payload(host_id)
        return shape_host_payload(
            document,
            age_s=0.0,
            freshness="fresh",
            collected_at=document["collected_at"],
        )

    stored = get_live_report(host_id, now_mono=now_mono)
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


def projects_payload(*, host_id: str | None = None) -> dict[str, Any]:
    now_mono = time.monotonic()
    hosts: dict[str, Any] = {}
    for opaque in _selected_host_ids(host_id):
        hosts[opaque] = _payload_for_host(opaque, now_mono=now_mono)
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
async def get_projects(host_id: str | None = Query(default=None)) -> JSONResponse:
    payload = projects_payload(host_id=host_id)
    return JSONResponse(content=payload, headers={"Cache-Control": "no-store"})


@router.post("/report")
async def post_project_report(request: Request, body: ProjectStateReport) -> JSONResponse:
    no_store = {"Cache-Control": "no-store"}
    if not _direct_loopback_peer(request):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"}, headers=no_store)

    allowed = allowed_reporter_host_ids()
    if body.host_id not in allowed:
        return JSONResponse(status_code=400, content={"detail": "unknown host_id"}, headers=no_store)

    document = body.model_dump(exclude_none=True)
    try:
        validate_report_document(document)
    except ProjectStateValidationError:
        return JSONResponse(status_code=400, content={"detail": "invalid project state report"}, headers=no_store)

    try:
        row = upsert_report(document)
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
