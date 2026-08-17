"""Lightweight Monitor HTTP facade for the Atlas VPS job protocol.

Wraps ``scripts.lexicon.runner.atlas_job`` — no new daemon / message bus.
Prefix: ``/api/atlas-jobs``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
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


def _require_job_id(job_id: str) -> str:
    try:
        return atlas_job.require_safe_job_id(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _read_result_receipt(job_id: str) -> dict[str, Any] | None:
    """Load ``{job_id}.result.json`` only when contained under the registry root."""
    result_file = atlas_job.result_path(job_id)
    root_real = os.path.realpath(str(atlas_job.registry_dir()))
    candidate = os.path.realpath(str(result_file))
    if not candidate.startswith(root_real + os.sep):
        return None
    path = Path(candidate)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


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
    job_id = atlas_job.require_safe_job_id(str(body.plan.get("id")))
    row = atlas_job.load_registry(job_id)
    if rc != 0:
        raise HTTPException(
            status_code=409,
            detail={"exit_code": rc, "job": row, "message": "submit refused or launch failed"},
        )
    return {"exit_code": rc, "job": row, "dry_run": body.dry_run}


@router.get("/{job_id}")
def job_status(job_id: str, host: str = "atlas-runner", audit: bool = False) -> dict[str, Any]:
    job_id = _require_job_id(job_id)
    row = atlas_job.load_registry(job_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"no registry row for {job_id}")
    # Reconcile the journal against host systemd truth.
    rc = atlas_job.status(host=host, audit=audit)
    row = atlas_job.load_registry(job_id) or row
    return {
        "job": row,
        "result": _read_result_receipt(job_id),
        "status_exit_code": rc,
        "restic_sink_blocked": atlas_job.restic_sink_blocked(),
    }


@router.post("/{job_id}/close")
def close_job(job_id: str, body: CloseBody | None = None) -> dict[str, Any]:
    job_id = _require_job_id(job_id)
    payload = body or CloseBody()
    try:
        rc = atlas_job.close_job(
            job_id,
            summary=payload.summary,
            skip_pull=payload.skip_pull,
            skip_restic=payload.skip_restic,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    row = atlas_job.load_registry(job_id)
    result = _read_result_receipt(job_id)
    if rc == 2:
        raise HTTPException(status_code=404, detail={"exit_code": rc, "message": "no registry row"})
    response = {"exit_code": rc, "job": row, "result": result}
    if rc != 0:
        # Fail-closed: non-success still returns the receipt under 409.
        raise HTTPException(status_code=409, detail=response)
    return response
