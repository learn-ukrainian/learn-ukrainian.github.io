"""Read-only fleet worker map route."""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from scripts.api.fleet_workers_collect import WORKERS_SCHEMA, workers_payload

router = APIRouter(prefix="/workers/v1", tags=["fleet-workers"])


@router.get("")
async def get_workers(host_id: str | None = Query(default=None)) -> JSONResponse:
    payload = workers_payload(host_id=host_id)
    return JSONResponse(
        content=payload,
        headers={"Cache-Control": "no-store", "X-Workers-Schema": WORKERS_SCHEMA},
    )
