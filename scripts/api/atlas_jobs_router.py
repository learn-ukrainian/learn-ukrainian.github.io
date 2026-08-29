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

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from scripts.lexicon.runner import atlas_job

from .monitor_context import MonitorContext, get_ctx, production_context

router = APIRouter(tags=["atlas-jobs"])

LOAD_SCHEMA = "atlas-jobs-load.v1"
RESULTS_SCHEMA = "atlas-jobs-results.v1"

HOST_LOAD_FRESH_S = 30.0
HOST_LOAD_REFRESH_AFTER_S = 15.0
HOST_LOAD_IN_FLIGHT_GRACE_S = 15.0
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
_HOST_LOAD_TIMERS: dict[str, asyncio.TimerHandle] = {}
# Failed-probe backoff: host -> monotonic deadline. Ordinary reads must not
# start a new collect before this instant; the armed timer owns the retry.
_HOST_LOAD_BACKOFF_UNTIL: dict[str, float] = {}


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
    _HOST_LOAD_BACKOFF_UNTIL.pop(canonical, None)
    _arm_host_load_timer(canonical)


def clear_host_load_cache() -> None:
    """Clear in-process host load cache, in-flight tasks, and armed timers."""
    _HOST_LOAD_CACHE.clear()
    for task in _HOST_LOAD_TASKS.values():
        if not task.done():
            task.cancel()
    _HOST_LOAD_TASKS.clear()
    for handle in _HOST_LOAD_TIMERS.values():
        handle.cancel()
    _HOST_LOAD_TIMERS.clear()
    _HOST_LOAD_BACKOFF_UNTIL.clear()


class SubmitBody(BaseModel):
    plan: dict[str, Any]
    dry_run: bool = False


class CloseBody(BaseModel):
    summary: dict[str, Any] | None = None
    skip_pull: bool = False
    skip_restic: bool = False


def _resolve_context(ctx: MonitorContext | None = None) -> MonitorContext:
    """Fall back to the live production context for plain-Python callers.

    Mirrors ``runtime_router._resolve_context`` (#7324 / #7393 / #6849).
    """
    if isinstance(ctx, MonitorContext):
        return ctx
    return production_context()


def _registry_dir(ctx: MonitorContext | None = None) -> Path:
    """Resolve the atlas-jobs registry the same way ``atlas_job.registry_dir`` does.

    ``ATLAS_JOB_REGISTRY`` remains the operator/test override. Otherwise the
    path is ``ctx.roots.batch_state_dir / "atlas-jobs"`` so a fixture context
    never walks the production checkout.
    """
    override = os.environ.get("ATLAS_JOB_REGISTRY")
    if override:
        return Path(override)
    return _resolve_context(ctx).roots.batch_state_dir / "atlas-jobs"


def _registry_display(ctx: MonitorContext | None = None) -> str:
    """Registry path for HTTP responses.

    A fixture context must not echo its disposable root (the former
    ``atlas_job.registry_dir`` sweep seam returned this canary-free relative
    path). Production still reports the live registry location.
    """
    resolved = _resolve_context(ctx)
    if resolved.root is not None:
        return "atlas-jobs-fixture"
    return str(_registry_dir(resolved))


def _require_job_id(job_id: str) -> str:
    try:
        return atlas_job.require_safe_job_id(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _read_result_receipt(job_id: str, ctx: MonitorContext | None = None) -> dict[str, Any] | None:
    """Load ``{job_id}.result.json`` only when contained under the registry root."""
    try:
        safe_id = atlas_job.require_safe_job_id(job_id)
        root = _registry_dir(ctx)
        result_file = atlas_job._path_under(root, f"{safe_id}.result.json")
        root_real = os.path.realpath(str(root))
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
    task = asyncio.current_task()
    ok = False
    try:
        data, now_iso = await asyncio.to_thread(_probe_host_load_sync, host)
        if data is not None:
            _HOST_LOAD_CACHE[host] = (data, time.monotonic(), now_iso)
            ok = True
            _HOST_LOAD_BACKOFF_UNTIL.pop(host, None)
        else:
            _HOST_LOAD_BACKOFF_UNTIL[host] = time.monotonic() + HOST_LOAD_REFRESH_AFTER_S
    finally:
        if _HOST_LOAD_TASKS.get(host) is task:
            _HOST_LOAD_TASKS.pop(host, None)
        if host in _HOST_LOAD_CACHE:
            # Re-arm after success or failure while a sample remains. A failed
            # probe restarts the full interval so a dead host is not hot-looped.
            _arm_host_load_timer(host, from_now=not ok)


def _fire_host_load_timer(host: str) -> None:
    """Timer callback: start an autonomous refresh without waiting for a GET."""
    _HOST_LOAD_TIMERS.pop(host, None)
    if host in _HOST_LOAD_CACHE:
        _schedule_host_load_refresh(host)


def _arm_host_load_timer(host: str, *, from_now: bool = False) -> None:
    """Arm a one-shot loop timer for the next refresh of a cached sample.

    Fires at ``max(0, HOST_LOAD_REFRESH_AFTER_S - age)`` so the next collect
    runs autonomously even when no reader hits within the fresh window.
    No running loop -> skip, matching ``_schedule_host_load_refresh``.
    """
    handle = _HOST_LOAD_TIMERS.pop(host, None)
    if handle is not None:
        handle.cancel()
    entry = _HOST_LOAD_CACHE.get(host)
    if entry is None:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    age = 0.0 if from_now else max(0.0, time.monotonic() - entry[1])
    delay = max(0.0, HOST_LOAD_REFRESH_AFTER_S - age)
    _HOST_LOAD_TIMERS[host] = loop.call_later(delay, _fire_host_load_timer, host)


def _schedule_host_load_refresh(host: str) -> asyncio.Task[None] | None:
    task = _HOST_LOAD_TASKS.get(host)
    if task is None or task.done():
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return None
        handle = _HOST_LOAD_TIMERS.pop(host, None)
        if handle is not None:
            handle.cancel()
        task = loop.create_task(_refresh_host_load_job(host))
        _HOST_LOAD_TASKS[host] = task
    return task


def _host_load_refresh_in_flight(host: str) -> bool:
    task = _HOST_LOAD_TASKS.get(host)
    return task is not None and not task.done()


def _host_load_in_failure_backoff(host: str, now_mono: float) -> bool:
    until = _HOST_LOAD_BACKOFF_UNTIL.get(host)
    return until is not None and now_mono < until


def _cached_load_status(age: float, *, in_flight: bool) -> str:
    """Classify a cached sample. In-flight probes stay fresh across one heartbeat."""
    if age <= HOST_LOAD_FRESH_S or (
        in_flight and age <= HOST_LOAD_FRESH_S + HOST_LOAD_IN_FLIGHT_GRACE_S
    ):
        return "fresh"
    if age <= HOST_LOAD_MAX_STALE_S:
        return "stale"
    return "unavailable"


def _get_host_load_entry(host: str, *, fresh: bool = False) -> dict[str, Any]:
    now_mono = time.monotonic()
    entry = _HOST_LOAD_CACHE.get(host)

    if fresh:
        _schedule_host_load_refresh(host)

    if entry is not None:
        metrics, mono_ts, iso_ts = entry
        age = max(0.0, round(now_mono - mono_ts, 2))
        if (
            not fresh
            and age > HOST_LOAD_REFRESH_AFTER_S
            and not _host_load_in_failure_backoff(host, now_mono)
        ):
            _schedule_host_load_refresh(host)
        status = _cached_load_status(age, in_flight=_host_load_refresh_in_flight(host))
        if status == "fresh":
            res: dict[str, Any] = {
                "status": "fresh",
                "observed_at": iso_ts,
                "age_seconds": age,
            }
            res.update(metrics)
            return res
        if status == "stale":
            res = {
                "status": "stale",
                "observed_at": iso_ts,
                "age_seconds": age,
            }
            res.update(metrics)
            return res
        return {
            "status": "unavailable",
            "error": "unreachable",
            "observed_at": iso_ts,
            "age_seconds": age,
        }

    if fresh or not _host_load_in_failure_backoff(host, now_mono):
        _schedule_host_load_refresh(host)
    now_iso = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return {
        "status": "unavailable",
        "error": "unreachable",
        "observed_at": now_iso,
        "age_seconds": 0.0,
    }


async def _get_host_load_entry_async(host: str, *, fresh: bool = False) -> dict[str, Any]:
    """Read host load, awaiting the shared probe when no usable cache exists."""
    now_mono = time.monotonic()
    entry = _HOST_LOAD_CACHE.get(host)
    in_backoff = _host_load_in_failure_backoff(host, now_mono)
    needs_probe_result = bool(fresh)
    if not needs_probe_result and not in_backoff:
        if entry is None:
            needs_probe_result = True
        else:
            _, mono_ts, _ = entry
            needs_probe_result = now_mono - mono_ts > HOST_LOAD_MAX_STALE_S

    if needs_probe_result:
        task = _schedule_host_load_refresh(host)
        if task is not None:
            await asyncio.shield(task)

    return _get_host_load_entry(host)


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
def list_jobs(ctx: MonitorContext = Depends(get_ctx)) -> dict[str, Any]:
    del ctx
    rows = atlas_job.list_registry()
    return {"count": len(rows), "jobs": rows}


@router.get("/health")
def atlas_jobs_health(ctx: MonitorContext = Depends(get_ctx)) -> dict[str, Any]:
    return {
        "ok": True,
        "schema": atlas_job.SCHEMA,
        "restic_sink_blocked": atlas_job.restic_sink_blocked(),
        "registry": _registry_display(ctx),
    }


@router.get("/load")
async def load_jobs(
    host: str | None = None,
    fresh: bool = False,
    ctx: MonitorContext = Depends(get_ctx),
) -> JSONResponse:
    del ctx
    all_hosts = _canonical_allowed_hosts()
    if host is not None:
        canonical = atlas_job._canonical_host(host)
        if canonical not in all_hosts:
            raise HTTPException(status_code=400, detail=f"unknown host: {host}")
        target_hosts = [canonical]
    else:
        target_hosts = all_hosts

    entries = await asyncio.gather(*(_get_host_load_entry_async(h, fresh=fresh) for h in target_hosts))
    hosts_data = dict(zip(target_hosts, entries, strict=True))

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
    ctx: MonitorContext = Depends(get_ctx),
) -> dict[str, Any]:
    target_host = atlas_job._canonical_host(host) if host is not None else None
    root = _registry_dir(ctx)
    all_results: list[dict[str, Any]] = []

    if root.is_dir():
        for path in sorted(root.glob("*.result.json")):
            job_id = path.name[: -len(".result.json")]
            try:
                safe_id = atlas_job.require_safe_job_id(job_id)
            except ValueError:
                continue
            receipt = _read_result_receipt(safe_id, ctx=ctx)
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
def submit_job(body: SubmitBody, ctx: MonitorContext = Depends(get_ctx)) -> dict[str, Any]:
    del ctx
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
def job_status(
    job_id: str,
    host: str = "atlas-runner",
    audit: bool = False,
    ctx: MonitorContext = Depends(get_ctx),
) -> dict[str, Any]:
    job_id = _require_job_id(job_id)
    row = atlas_job.load_registry(job_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"no registry row for {job_id}")
    # Reconcile the journal against host systemd truth.
    rc = atlas_job.status(host=host, audit=audit)
    row = atlas_job.load_registry(job_id) or row
    return {
        "job": row,
        "result": _read_result_receipt(job_id, ctx=ctx),
        "status_exit_code": rc,
        "restic_sink_blocked": atlas_job.restic_sink_blocked(),
    }


@router.post("/{job_id}/close")
def close_job(
    job_id: str,
    body: CloseBody | None = None,
    ctx: MonitorContext = Depends(get_ctx),
) -> dict[str, Any]:
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
    result = _read_result_receipt(job_id, ctx=ctx)
    if rc == 2:
        raise HTTPException(status_code=404, detail={"exit_code": rc, "message": "no registry row"})
    response = {"exit_code": rc, "job": row, "result": result}
    if rc != 0:
        # Fail-closed: non-success still returns the receipt under 409.
        raise HTTPException(status_code=409, detail=response)
    return response
