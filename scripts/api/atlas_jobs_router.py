"""Lightweight Monitor HTTP facade for the Atlas VPS job protocol.

Wraps ``scripts.lexicon.runner.atlas_job`` — no new daemon / message bus.
Prefix: ``/api/atlas-jobs``.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from scripts.lexicon.runner import atlas_job

router = APIRouter(tags=["atlas-jobs"])

LOAD_SCHEMA = "atlas-jobs-load.v1"
RESULTS_SCHEMA = "atlas-jobs-results.v1"

HOST_LOAD_FRESH_S = 30.0
HOST_LOAD_MAX_STALE_S = 300.0

RESULTS_DEFAULT_LIMIT = 50
RESULTS_MAX_LIMIT = 200

RESULTS_ALLOWLIST = frozenset(
    {
        "id",
        "host",
        "kind",
        "state",
        "closed_at",
        "issue",
        "denominator",
        "delivery",
        "pulled",
        "targets",
        "filled_translation",
        "circuit_breaker_tripped",
    }
)

# In-process cache: host -> (metrics_dict, monotonic_ts, iso_observed_at)
_HOST_LOAD_CACHE: dict[str, tuple[dict[str, Any], float, str]] = {}
_HOST_LOAD_TASKS: dict[str, asyncio.Task[None]] = {}


def set_host_load_cache(
    host: str,
    data: dict[str, Any],
    mono_ts: float | None = None,
    iso_ts: str | None = None,
) -> None:
    """Explicitly set host load cache entry (used by tests and manual warmers)."""
    canonical = atlas_job._canonical_host(host)
    m_ts = time.monotonic() if mono_ts is None else mono_ts
    i_ts = datetime.now(UTC).isoformat().replace("+00:00", "Z") if iso_ts is None else iso_ts
    _HOST_LOAD_CACHE[canonical] = (data, m_ts, i_ts)


def clear_host_load_cache() -> None:
    """Clear in-process host load cache and in-flight tasks."""
    _HOST_LOAD_CACHE.clear()
    for task in _HOST_LOAD_TASKS.values():
        if not task.done():
            task.cancel()
    _HOST_LOAD_TASKS.clear()


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
    try:
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
    except Exception:
        return None


def _canonical_allowed_hosts() -> list[str]:
    return sorted({atlas_job._canonical_host(h) for hosts in atlas_job.ALLOWED_HOSTS.values() for h in hosts})


def _probe_host_load_sync(host: str) -> tuple[dict[str, Any] | None, str]:
    adapter = atlas_job.get_host_adapter()
    now_iso = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    try:
        data = adapter.host_load(host)
        return data, now_iso
    except Exception:
        return None, now_iso


async def _refresh_host_load_job(host: str) -> None:
    try:
        data, now_iso = await asyncio.to_thread(_probe_host_load_sync, host)
        if data is not None:
            _HOST_LOAD_CACHE[host] = (data, time.monotonic(), now_iso)
    finally:
        _HOST_LOAD_TASKS.pop(host, None)


def _schedule_host_load_refresh(host: str) -> asyncio.Task[None] | None:
    task = _HOST_LOAD_TASKS.get(host)
    if task is None or task.done():
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return None
        task = loop.create_task(_refresh_host_load_job(host))
        _HOST_LOAD_TASKS[host] = task
    return task


def _get_host_load_entry(host: str, *, fresh: bool = False) -> dict[str, Any]:
    now_mono = time.monotonic()
    entry = _HOST_LOAD_CACHE.get(host)

    if fresh:
        _schedule_host_load_refresh(host)

    if entry is not None:
        metrics, mono_ts, iso_ts = entry
        age = max(0.0, round(now_mono - mono_ts, 2))
        if age <= HOST_LOAD_FRESH_S:
            res: dict[str, Any] = {
                "status": "fresh",
                "observed_at": iso_ts,
                "age_seconds": age,
            }
            res.update(metrics)
            return res
        elif age <= HOST_LOAD_MAX_STALE_S:
            _schedule_host_load_refresh(host)
            res = {
                "status": "stale",
                "observed_at": iso_ts,
                "age_seconds": age,
            }
            res.update(metrics)
            return res
        else:
            _schedule_host_load_refresh(host)
            return {
                "status": "unavailable",
                "error": "unreachable",
                "observed_at": iso_ts,
                "age_seconds": age,
            }

    _schedule_host_load_refresh(host)
    now_iso = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return {
        "status": "unavailable",
        "error": "unreachable",
        "observed_at": now_iso,
        "age_seconds": 0.0,
    }


def _encode_cursor(closed_at: str | None, job_id: str) -> str:
    payload = json.dumps([closed_at or "", job_id])
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: str) -> tuple[str, str] | None:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        data = json.loads(raw)
        if isinstance(data, list) and len(data) == 2 and isinstance(data[0], str) and isinstance(data[1], str):
            return data[0], data[1]
    except Exception:
        pass
    return None


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


@router.get("/load")
async def load_jobs(
    host: str | None = None,
    fresh: bool = False,
) -> JSONResponse:
    all_hosts = _canonical_allowed_hosts()
    if host is not None:
        canonical = atlas_job._canonical_host(host)
        if canonical not in all_hosts:
            raise HTTPException(status_code=400, detail=f"unknown host: {host}")
        target_hosts = [canonical]
    else:
        target_hosts = all_hosts

    hosts_data: dict[str, Any] = {}
    for h in target_hosts:
        hosts_data[h] = _get_host_load_entry(h, fresh=fresh)

    now_iso = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    payload = {
        "schema": LOAD_SCHEMA,
        "observed_at": now_iso,
        "hosts": hosts_data,
    }
    return JSONResponse(content=payload, headers={"Cache-Control": "no-store"})


@router.get("/results")
def results_jobs(
    host: str | None = None,
    state: str | None = None,
    limit: int = Query(RESULTS_DEFAULT_LIMIT, ge=1, le=RESULTS_MAX_LIMIT),
    cursor: str | None = None,
) -> dict[str, Any]:
    target_host = atlas_job._canonical_host(host) if host is not None else None
    root = atlas_job.registry_dir()
    all_results: list[dict[str, Any]] = []

    if root.is_dir():
        for path in sorted(root.glob("*.result.json")):
            job_id = path.name[: -len(".result.json")]
            try:
                safe_id = atlas_job.require_safe_job_id(job_id)
            except ValueError:
                continue
            receipt = _read_result_receipt(safe_id)
            if receipt is None:
                continue

            item_host = atlas_job._canonical_host(receipt.get("host"))
            item_state = receipt.get("state")

            if target_host is not None and item_host != target_host:
                continue
            if state is not None and item_state != state:
                continue

            summary_data = receipt.get("summary") if isinstance(receipt.get("summary"), dict) else {}
            summary_row: dict[str, Any] = {
                "id": safe_id,
                "host": item_host,
                "kind": receipt.get("kind"),
                "state": item_state,
                "closed_at": receipt.get("closed_at"),
                "issue": receipt.get("issue"),
                "denominator": receipt.get("denominator"),
                "delivery": receipt.get("delivery"),
                "pulled": receipt.get("pulled"),
                "targets": summary_data.get("targets"),
                "filled_translation": summary_data.get("filled_translation"),
                "circuit_breaker_tripped": summary_data.get("circuit_breaker_tripped"),
            }
            all_results.append(summary_row)

    # Sort descending by (closed_at, id)
    all_results.sort(
        key=lambda x: (str(x.get("closed_at") or ""), str(x.get("id") or "")),
        reverse=True,
    )

    items = all_results
    if cursor is not None:
        decoded = _decode_cursor(cursor)
        if decoded is None:
            raise HTTPException(status_code=400, detail="invalid cursor")
        cur_closed, cur_id = decoded
        items = [x for x in items if (str(x.get("closed_at") or ""), str(x.get("id") or "")) < (cur_closed, cur_id)]

    page = items[:limit]
    next_cursor = None
    if len(items) > limit:
        last_item = page[-1]
        next_cursor = _encode_cursor(last_item.get("closed_at"), last_item["id"])

    return {
        "count": len(page),
        "total": len(all_results),
        "results": page,
        "next_cursor": next_cursor,
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
