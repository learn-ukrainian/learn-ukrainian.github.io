"""Lightweight Monitor HTTP facade for the Atlas VPS job protocol.

Wraps ``scripts.lexicon.runner.atlas_job`` — no new daemon / message bus.
Prefix: ``/api/atlas-jobs``.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from scripts.lexicon.runner import atlas_job

router = APIRouter(tags=["atlas-jobs"])


class SubmitBody(BaseModel):
    plan: dict[str, Any]
    dry_run: bool = False


class CloseBody(BaseModel):
    summary: dict[str, Any] | None = None
    skip_pull: bool = False
    skip_restic: bool = False


@router.get("")
def list_jobs() -> dict[str, Any]:
    rows = atlas_job.list_registry()
    return {"count": len(rows), "jobs": rows}


@router.get("/health")
def atlas_jobs_health() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": atlas_job.SCHEMA,
        "restic_sink_blocked": atlas_job.restic_sink_blocked(),
        "registry": str(atlas_job.registry_dir()),
    }


@router.post("/submit")
def submit_job(body: SubmitBody) -> dict[str, Any]:
    errors = atlas_job.validate_plan(body.plan)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})
    rc = atlas_job.submit(body.plan, dry_run=body.dry_run)
    job_id = str(body.plan.get("id"))
    row = atlas_job.load_registry(job_id)
    if rc != 0:
        raise HTTPException(
            status_code=409,
            detail={"exit_code": rc, "job": row, "message": "submit refused or launch failed"},
        )
    return {"exit_code": rc, "job": row, "dry_run": body.dry_run}


@router.get("/{job_id}")
def job_status(job_id: str, host: str = "atlas-runner", audit: bool = False) -> dict[str, Any]:
    row = atlas_job.load_registry(job_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"no registry row for {job_id}")
    # Reconcile the journal against host systemd truth.
    rc = atlas_job.status(host=host, audit=audit)
    row = atlas_job.load_registry(job_id) or row
    result = None
    result_file = atlas_job.result_path(job_id)
    if result_file.is_file():
        result = json.loads(result_file.read_text(encoding="utf-8"))
    return {
        "job": row,
        "result": result,
        "status_exit_code": rc,
        "restic_sink_blocked": atlas_job.restic_sink_blocked(),
    }


@router.post("/{job_id}/close")
def close_job(job_id: str, body: CloseBody | None = None) -> dict[str, Any]:
    payload = body or CloseBody()
    rc = atlas_job.close_job(
        job_id,
        summary=payload.summary,
        skip_pull=payload.skip_pull,
        skip_restic=payload.skip_restic,
    )
    row = atlas_job.load_registry(job_id)
    result = None
    result_file = atlas_job.result_path(job_id)
    if result_file.is_file():
        result = json.loads(result_file.read_text(encoding="utf-8"))
    if rc == 2:
        raise HTTPException(status_code=404, detail={"exit_code": rc, "message": "no registry row"})
    response = {"exit_code": rc, "job": row, "result": result}
    if rc != 0:
        # Fail-closed: non-success still returns the receipt under 409.
        raise HTTPException(status_code=409, detail=response)
    return response
