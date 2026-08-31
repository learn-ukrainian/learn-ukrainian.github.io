"""Read-only fleet worker map route."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from scripts.api import fleet_workers_collect as workers_collect
from scripts.api.fleet_workers_collect import WORKERS_SCHEMA, workers_payload
from scripts.api.monitor_context import MonitorContext, get_ctx
from scripts.api.project_state_router import LocalDocumentSnapshot, get_cached_local_document

router = APIRouter(prefix="/workers/v1", tags=["fleet-workers"])


@router.get("")
async def get_workers(
    host_id: str | None = Query(default=None),
    ctx: MonitorContext = Depends(get_ctx),
) -> JSONResponse:
    self_report_ids = workers_collect._self_host_ids()
    if host_id is not None:
        self_report_ids &= {host_id}
    self_reports: dict[str, LocalDocumentSnapshot] = {
        opaque: get_cached_local_document(opaque) for opaque in self_report_ids
    }
    payload = workers_payload(
        host_id=host_id,
        presence_store=ctx.stores.presence_store,
        report_store=ctx.stores.report_store,
    )
    for host in payload.get("hosts", []):
        snapshot = self_reports.get(host.get("host_id"))
        if snapshot is None:
            continue
        host["freshness"] = snapshot.freshness
        host["age_s"] = snapshot.age_s
    return JSONResponse(
        content=payload,
        headers={"Cache-Control": "no-store", "X-Workers-Schema": WORKERS_SCHEMA},
    )
