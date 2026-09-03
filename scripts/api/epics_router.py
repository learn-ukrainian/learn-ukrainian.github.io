"""Remote TTL-fenced epic lifecycle API (design #7178, M2 of #7177)."""

from __future__ import annotations

import asyncio
import base64
import binascii
import logging
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

import yaml
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from agents_extensions.shared.session_streams.inventory import resolve_streams_yaml, streams_yaml_sha256
from agents_extensions.shared.session_streams.model import (
    EntryRef,
    EntryType,
    HolderKind,
    Lease,
    LeaseHolder,
    SessionState,
    entry_as_dict,
    isoformat_z,
    parse_timestamp,
    utc_now,
    validate_stream_id,
)
from agents_extensions.shared.session_streams.receipts import register_manifest_inventory
from agents_extensions.shared.session_streams.store import (
    MAX_ROLLOVER_BUNDLE_BYTES,
    ContentRejectedError,
    LeaseConflictError,
    LifecycleError,
    NotFoundError,
    SessionStreamStore,
    validate_entry_body,
)
from scripts.api.monitor_context import MonitorContext, get_ctx, resolve_context
from scripts.api.observer_presence import _direct_loopback_peer
from scripts.api.occupancy_sanitize import opaque_host_id, safe_field
from scripts.orchestration import issue_stream_audit as audit
from scripts.orchestration.thread_handoff import _bundle_extract, _bundle_secret_hits

router = APIRouter()
logger = logging.getLogger(__name__)

SCHEMA = "remote-epic-lifecycle.v1"
GRAPH_SCHEMA = "epics-graph.v1"
DEFAULT_TTL_SECONDS = 15 * 60
MAX_DIGEST_LIMIT = 100
TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
REGISTRY_TEXT_MAX = 160
_REGISTRY_IPV4_RE = re.compile(r"(?<![A-Za-z0-9])(?:\d{1,3}\.){3}\d{1,3}(?![A-Za-z0-9])")
_REGISTRY_IPV6_RE = re.compile(r"(?i)(?<![A-Za-z0-9])(?:[0-9a-f]{0,4}:){2,}[0-9a-f:]{0,4}(?![A-Za-z0-9])")
_REGISTRY_HOSTNAME_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9_-])(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}(?![A-Za-z0-9_-])"
)
_REGISTRY_ABSOLUTE_PATH_RE = re.compile(r"(?<![A-Za-z0-9])(?:/|~[/\\]|[A-Za-z]:[\\/])")
_REGISTRY_SSH_ALIAS_RE = re.compile(
    r"(?i)(?:\b(?:ssh|scp|rsync)\s+[^\s]+|\b(?:git|[A-Za-z0-9._-]+)@[^\s:/]+:|"
    r"(?<![A-Za-z0-9])(atlas-runner|hramatka|vps)(?![A-Za-z0-9]))"
)
_REGISTRY_PRIVATE_TOKEN_RE = re.compile(
    r"(?ix)(?:\b(?:token|secret|password|passwd|api[_-]?key|bearer)\s*[:=]\s*\S+|"
    r"\b(?:sk|gh[pous]|xox[baprs]-)[A-Za-z0-9_-]{8,}|"
    r"-----BEGIN [^-]{0,40}PRIVATE KEY-----|"
    r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,})"
)

_REGISTRY_HEALTH_LOCK = Lock()
_REGISTRY_SNAPSHOT_SHA256: str | None = None
_REGISTRY_HEALTH: dict[str, Any] = {
    "status": "unavailable",
    "records": 0,
    "registered": 0,
    "skipped": 0,
    "source_sha256": None,
    "seeded_at": None,
}




def _store(ctx: MonitorContext | None = None) -> SessionStreamStore:
    """Return the API-host epic store; the path never crosses the HTTP boundary."""
    store = resolve_context(ctx).stores.epics_store
    if store is None:
        raise FileNotFoundError("epic store is unavailable")
    return store


def _response_registry_text(value: Any) -> str | None:
    """Bound registry labels before they cross the API boundary."""
    if value is None:
        return None
    if not isinstance(value, str):
        return "[redacted]"
    text = " ".join(value.split())
    if not text:
        return None
    if len(text) > REGISTRY_TEXT_MAX:
        return "[redacted]"
    if any(
        pattern.search(text)
        for pattern in (
            _REGISTRY_IPV4_RE,
            _REGISTRY_IPV6_RE,
            _REGISTRY_HOSTNAME_RE,
            _REGISTRY_ABSOLUTE_PATH_RE,
            _REGISTRY_SSH_ALIAS_RE,
            _REGISTRY_PRIVATE_TOKEN_RE,
        )
    ):
        return "[redacted]"
    return text


def registry_health_snapshot() -> dict[str, Any]:
    """Return the last startup seed outcome without exposing failure details."""
    with _REGISTRY_HEALTH_LOCK:
        return dict(_REGISTRY_HEALTH)


def _set_registry_health(
    *,
    status: str,
    records: int,
    registered: int,
    skipped: int,
    source_sha256: str | None,
    seeded_at: str | None,
    snapshot_sha256: str | None = None,
) -> dict[str, Any]:
    global _REGISTRY_SNAPSHOT_SHA256
    if status not in {"ok", "unavailable", "invalid"}:
        raise ValueError("invalid registry status")
    with _REGISTRY_HEALTH_LOCK:
        if snapshot_sha256 is not None:
            _REGISTRY_SNAPSHOT_SHA256 = snapshot_sha256
        _REGISTRY_HEALTH.update(
            {
                "status": status,
                "records": records,
                "registered": registered,
                "skipped": skipped,
                "source_sha256": source_sha256,
                "seeded_at": seeded_at,
            }
        )
        return dict(_REGISTRY_HEALTH)


def seed_manifest_inventory(
    registry_root: Path,
    *,
    store: SessionStreamStore | None = None,
    handoff_root: Path | None = None,
    now: datetime | None = None,
    ctx: MonitorContext | None = None,
) -> dict[str, Any]:
    """Fail-open startup seed from the release registry into the live store."""
    if store is None or handoff_root is None:
        resolved = resolve_context(ctx)
        store = store or _store(resolved)
        handoff_root = handoff_root or resolved.roots.live_repo_root
    registry_path: Path | None = None
    source_sha256: str | None = None
    try:
        registry_path = resolve_streams_yaml(registry_root)
        source_sha256 = streams_yaml_sha256(registry_root, streams_yaml=registry_path)
    except (FileNotFoundError, OSError):
        logger.warning("Epic registry startup seed unavailable; existing rows remain served")
        return _set_registry_health(
            status="unavailable",
            records=0,
            registered=0,
            skipped=0,
            source_sha256=None,
            seeded_at=None,
        )
    except Exception:
        logger.warning("Epic registry startup seed invalid; existing rows remain served")
        return _set_registry_health(
            status="invalid",
            records=0,
            registered=0,
            skipped=1,
            source_sha256=source_sha256,
            seeded_at=None,
        )

    try:
        result = register_manifest_inventory(
            store,
            registry_root,
            streams_yaml=registry_path,
            handoff_root=handoff_root,
            read_handoff_files=False,
            now=now,
        )
    except (FileNotFoundError, PermissionError, OSError):
        logger.warning("Epic registry startup seed unavailable; existing rows remain served")
        return _set_registry_health(
            status="unavailable",
            records=0,
            registered=0,
            skipped=0,
            source_sha256=source_sha256,
            seeded_at=None,
        )
    except (TypeError, ValueError):
        logger.warning("Epic registry startup seed invalid; existing rows remain served")
        return _set_registry_health(
            status="invalid",
            records=0,
            registered=0,
            skipped=1,
            source_sha256=source_sha256,
            seeded_at=None,
        )
    except Exception:
        logger.warning("Epic registry startup seed unavailable; existing rows remain served")
        return _set_registry_health(
            status="unavailable",
            records=0,
            registered=0,
            skipped=0,
            source_sha256=source_sha256,
            seeded_at=None,
        )

    status = "invalid" if result.skipped else "ok"
    seeded_at = isoformat_z(now or utc_now())
    logger.info(
        "Epic registry startup seed status=%s records=%d registered=%d skipped=%d",
        status,
        result.records,
        len(result.registered_stream_ids),
        result.skipped,
    )
    return _set_registry_health(
        status=status,
        records=result.records,
        registered=len(result.registered_stream_ids),
        skipped=result.skipped,
        source_sha256=result.source_sha256,
        seeded_at=seeded_at,
        snapshot_sha256=result.source_sha256,
    )


def _registry_snapshot_for_response(store: SessionStreamStore) -> str | None:
    with _REGISTRY_HEALTH_LOCK:
        marker = _REGISTRY_SNAPSHOT_SHA256
    if marker is not None:
        return marker
    try:
        return store.latest_inventory_source_sha()
    except Exception:
        return None


def _registry_fields(store: SessionStreamStore, stream_id: str) -> dict[str, Any]:
    metadata = store.remote_registry_projection(
        stream_id,
        snapshot_sha256=_registry_snapshot_for_response(store),
    )
    return {
        "registered": bool(metadata["registered"]),
        "stream_name": _response_registry_text(metadata["stream_name"]),
        "title": _response_registry_text(metadata["title"]),
    }


def _error(status: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"schema": SCHEMA, "error": "request_refused", "detail": detail},
        headers={"Cache-Control": "no-store"},
    )


def _server_error() -> JSONResponse:
    return _error(503, "Monitor session-stream store unavailable")


def _token(value: Any, label: str) -> str:
    if not isinstance(value, str) or not TOKEN_RE.fullmatch(value) or safe_field(value, role="task_id") != value:
        raise ValueError(f"{label} is invalid")
    return value


def _host(value: Any) -> str:
    if not isinstance(value, str) or not opaque_host_id(value):
        raise ValueError("host_id is invalid")
    return value


def _integer(value: Any, label: str, *, minimum: int = 1, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} is invalid")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} is invalid")
    return value


def _digest_limit(value: Any) -> int:
    return _integer(value, "digest_limit", minimum=0, maximum=MAX_DIGEST_LIMIT)


def _epic_stream(value: Any) -> str:
    stream_id = validate_stream_id(value)
    if not stream_id.startswith("epic:"):
        raise ValueError("remote lifecycle requires an epic:<positive-number> stream")
    return stream_id


def _holder(payload: dict[str, Any], *, default_host: str | None = None) -> LeaseHolder:
    nested = payload.get("holder")
    source = nested if isinstance(nested, dict) else payload
    kind = HolderKind(source.get("holder_kind", HolderKind.PROCESS.value))
    task_id = source.get("task_id")
    if task_id is not None:
        task_id = _token(task_id, "task_id")
    process_id = source.get("process_id", 1)
    if process_id is not None:
        process_id = _integer(process_id, "process_id")
    host_id = source.get("host_id", default_host)
    if host_id is not None:
        host_id = _host(host_id)
    holder = LeaseHolder(
        agent=_token(source.get("agent"), "agent"),
        harness=_token(source.get("harness"), "harness"),
        instance_id=_token(source.get("instance_id"), "instance_id"),
        process_id=process_id,
        task_id=task_id,
        holder_kind=kind,
        host_id=host_id,
    )
    holder.validate()
    return holder


def _lease_from_payload(payload: dict[str, Any]) -> Lease:
    source = payload.get("lease") if isinstance(payload.get("lease"), dict) else payload
    if not isinstance(source, dict):
        raise ValueError("lease is invalid")
    holder = _holder(source)
    stream_value = source.get("stream_id")
    if not isinstance(stream_value, str):
        raise ValueError("stream_id is invalid")
    return Lease(
        stream_id=validate_stream_id(stream_value),
        session_id=_token(source.get("session_id"), "session_id"),
        lease_id=_token(source.get("lease_id"), "lease_id"),
        generation=_integer(source.get("generation"), "generation"),
        fencing_token=_integer(source.get("fencing_token"), "fencing_token"),
        holder=holder,
        heartbeat_at=str(source.get("heartbeat_at", "1970-01-01T00:00:00Z")),
        expires_at=str(source.get("expires_at", "1970-01-01T00:00:00Z")),
        ttl_seconds=_integer(source.get("ttl_seconds", DEFAULT_TTL_SECONDS), "ttl_seconds", maximum=86_400),
        version=_integer(source.get("version", 1), "version"),
    )


def _lease_payload(lease: Lease, *, projection_state: str, session_state: str, now: datetime) -> dict[str, Any]:
    expired = projection_state == "active" and now >= parse_timestamp(lease.expires_at)
    return {
        "stream_id": lease.stream_id,
        "session_id": _response_token(lease.session_id),
        "lease_id": _response_token(lease.lease_id),
        "generation": lease.generation,
        "fencing_token": lease.fencing_token,
        "state": "expired" if expired else projection_state,
        "session_state": session_state,
        "heartbeat_at": lease.heartbeat_at,
        "expires_at": lease.expires_at,
        "ttl_seconds": lease.ttl_seconds,
        "version": lease.version,
        "age_seconds": max(0, int((now - parse_timestamp(lease.heartbeat_at)).total_seconds())),
        "holder": {
            "agent": _response_token(lease.holder.agent),
            "harness": _response_token(lease.holder.harness),
            "instance_id": _response_token(lease.holder.instance_id),
            "task_id": _response_optional_token(lease.holder.task_id),
            "process_id": lease.holder.process_id,
            "holder_kind": lease.holder.holder_kind.value,
            "host_id": _response_host(lease.holder.host_id),
        },
    }


def _digest_payload(store: SessionStreamStore, stream_id: str, limit: int) -> dict[str, Any]:
    digest = store.load_remote_digest(stream_id, limit=limit)
    return {
        "stream_id": digest.stream_id,
        "limit": digest.limit,
        "high_water_entry_id": digest.high_water_entry_id,
        "digest_sha256": digest.digest_sha256,
        "pinned": [_safe_entry(entry_as_dict(entry)) for entry in digest.pinned],
        "recent": [_safe_entry(entry_as_dict(entry)) for entry in digest.recent],
    }


def _safe_entry(payload: dict[str, Any]) -> dict[str, Any]:
    """Never echo legacy unsafe text or URI references through the remote API."""
    safe = {
        **payload,
        "stream": _response_stream(payload.get("stream")),
        "session_id": _response_token(payload.get("session_id")),
        "agent": _response_token(payload.get("agent")),
        "harness": _response_token(payload.get("harness")),
        "idempotency_key": _response_token(payload.get("idempotency_key")),
        "refs": [
            {
                "kind": _response_token(ref.get("kind")),
                "uri": None,
                "target_entry_id": ref.get("target_entry_id"),
            }
            for ref in payload.get("refs", ())
            if isinstance(ref, dict) and ref.get("uri") is None
        ],
    }
    try:
        validate_entry_body(str(safe.get("body", "")))
    except (ContentRejectedError, ValueError):
        safe["body"] = "[redacted]"
    return safe


def _response_token(value: Any) -> str:
    return value if isinstance(value, str) and safe_field(value, role="task_id") == value else "[redacted]"


def _response_stream(value: Any) -> str:
    try:
        return _epic_stream(value)
    except (TypeError, ValueError):
        return "[redacted]"


def _response_optional_token(value: Any) -> str | None:
    return None if value is None else _response_token(value)


def _response_host(value: Any) -> str | None:
    return None if value is None else value if isinstance(value, str) and opaque_host_id(value) else "[redacted]"


def _stream_response(store: SessionStreamStore, stream_id: str, limit: int) -> dict[str, Any]:
    projection = store.remote_stream_projection(stream_id)
    row = projection.get("lease")
    now = utc_now()
    lease_payload = None
    session_state = None
    if row is not None:
        lease = store._lease_from_row(row)  # the router is a typed projection consumer
        session_state = SessionState.EXPIRED.value if row.get("session_expired_at") else str(row["session_state"])
        lease_payload = _lease_payload(lease, projection_state=str(row["state"]), session_state=session_state, now=now)
    return {
        "schema": SCHEMA,
        "stream_id": stream_id,
        **_registry_fields(store, stream_id),
        "registry_status": registry_health_snapshot()["status"],
        "lease": lease_payload,
        "session_state": session_state,
        "digest": _digest_payload(store, stream_id, limit),
    }


def _check_mutation_peer(request: Request) -> JSONResponse | None:
    if not _direct_loopback_peer(request):
        return _error(403, "loopback mutation required")
    return None


def _bundle_blob_from_body(body: dict[str, Any]) -> bytes:
    encoded = body.get("blob")
    if not isinstance(encoded, str) or not encoded:
        raise ValueError("bundle blob must be base64 text")
    try:
        blob = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError) as exc:
        raise ValueError("bundle blob is not valid base64") from exc
    if not blob or len(blob) > MAX_ROLLOVER_BUNDLE_BYTES:
        raise ContentRejectedError("rollover bundle exceeds the 4 MiB cap")
    return blob


def _bundle_api_payload(row: dict[str, Any], *, include_blob: bool) -> dict[str, Any]:
    payload = dict(row)
    blob = payload.pop("blob", None)
    if include_blob:
        if not isinstance(blob, bytes):
            raise ValueError("stored rollover bundle blob is malformed")
        payload["blob"] = base64.b64encode(blob).decode("ascii")
    return payload


def _claim_values(body: dict[str, Any]) -> tuple[str, str, str, LeaseHolder, int, int]:
    session_id = _token(body.get("session_id"), "session_id")
    lease_id = _token(body.get("lease_id"), "lease_id")
    lineage_id = _token(body.get("lineage_id"), "lineage_id")
    holder = _holder(body)
    ttl = _integer(body.get("ttl_seconds", DEFAULT_TTL_SECONDS), "ttl_seconds", maximum=86_400)
    limit = _digest_limit(body.get("digest_limit", 20))
    return session_id, lease_id, lineage_id, holder, ttl, limit


@router.get("/v1/health")
def remote_health(ctx: MonitorContext = Depends(get_ctx)) -> JSONResponse:
    try:
        store = _store(ctx)
        # A first health probe is allowed to initialize the API-host schema;
        # subsequent reads verify the committed migration receipt.
        connection = store.database.connect()
        connection.close()
        audit = store.audit()
    except Exception:
        return _server_error()
    return JSONResponse(
        content={
            "schema": SCHEMA,
            "ok": audit["integrity_check"] == "ok" and not audit["foreign_key_violations"],
            "store_reachable": True,
            "schema_versions": audit["schema_versions"],
            "registry": registry_health_snapshot(),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/v1")
def remote_epic_list(ctx: MonitorContext = Depends(get_ctx)) -> JSONResponse:
    try:
        store = _store(ctx)
        registry_status = registry_health_snapshot()["status"]
        rows = []
        for row in store.list_remote_projections():
            stream_id = str(row["stream_id"])
            lease_payload = None
            session_state = None
            if row.get("lease_id") is not None:
                lease = store._lease_from_row(row)
                session_state = (
                    SessionState.EXPIRED.value if row.get("session_expired_at") else str(row["session_state"])
                )
                lease_payload = _lease_payload(
                    lease,
                    projection_state=str(row["state"]),
                    session_state=session_state,
                    now=utc_now(),
                )
            digest = _digest_payload(store, stream_id, 3)
            latest = {entry["type"]: entry for entry in (*digest["pinned"], *digest["recent"])}
            rows.append(
                {
                    "stream_id": stream_id,
                    **_registry_fields(store, stream_id),
                    "registry_status": registry_status,
                    "lease": lease_payload,
                    "session_state": session_state,
                    "last_state": latest.get(EntryType.STATE.value),
                    "last_decision": latest.get(EntryType.DECISION.value),
                    "last_next_action": latest.get(EntryType.NEXT_ACTION.value),
                }
            )
    except Exception:
        return _server_error()
    return JSONResponse(
        content={"schema": SCHEMA, "registry_status": registry_status, "streams": rows},
        headers={"Cache-Control": "no-store"},
    )


def _load_issue_streams(ctx: MonitorContext | None = None) -> dict[str, Any]:
    try:
        path = resolve_streams_yaml(resolve_context(ctx).roots.live_repo_root)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("streams"), dict):
            return data["streams"]
    except Exception:
        logger.warning("Failed to load issue-stream registry", exc_info=True)
    return {}


_GRAPH_IDLE_REFRESH = {
    "schema_version": 1,
    "run_id": None,
    "phase": "idle",
    "requested_at": None,
    "started_at": None,
    "last_outcome": "none",
    "last_outcome_at": None,
    "failure_code": None,
    "cooldown_until": None,
}


def _graph_audit_inputs(*, fresh: bool) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any]]:
    """Load audit cache and refresh state without raising into the graph 503 wrapper.

    Isolated OPSEC and merge-group checkouts have no host audit sidecar and
    deny ``Popen``. ``schedule_refresh`` only swallows ``OSError``, so a denied
    spawn leaked ``AssertionError`` as GET /api/epics/graph/v1 503 (#7413).
    Degrade to the documented no-cache / idle envelope instead.
    """
    report: dict[str, Any] | None = None
    stale: dict[str, Any] | None = None
    try:
        report = audit.read_cache(max_age_s=3600)
        if report is None:
            stale = audit.read_cache(max_age_s=7 * 24 * 3600)
    except Exception:
        report = None
        stale = None
    try:
        state = (
            audit.schedule_refresh(force=fresh)
            if fresh or report is None
            else audit.read_refresh_state()
        )
    except Exception:
        state = dict(_GRAPH_IDLE_REFRESH)
    if not isinstance(state, dict):
        state = dict(_GRAPH_IDLE_REFRESH)
    return report, stale, state


@router.get("/graph/v1")
async def remote_epics_graph(
    fresh: bool = Query(False, description="Schedule a refresh instead of only serving the cache."),
    ctx: MonitorContext = Depends(get_ctx),
) -> JSONResponse:
    """Epics & Areas Relationship Map backing endpoint (#7295, M5 of #7177)."""

    def _load() -> dict[str, Any]:
        store = _store(ctx)
        report, stale, state = _graph_audit_inputs(fresh=fresh)

        streams_data = _load_issue_streams(ctx)
        audit_data = report if report is not None else (stale or {})
        effective_membership = audit_data.get("effective_membership") or {}
        open_issue_numbers = {int(n) for n in (audit_data.get("open_issue_numbers") or [])}
        open_issue_titles = {
            str(k): v for k, v in (audit_data.get("open_issue_titles") or {}).items()
        }

        registry_status = registry_health_snapshot()["status"]
        projections = {str(row["stream_id"]): row for row in store.list_remote_projections()}
        now = utc_now()

        all_epic_numbers: set[int] = set()
        areas: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        for stream_id, spec in streams_data.items():
            if not isinstance(spec, dict):
                continue
            epics = [int(n) for n in (spec.get("epics") or [])]
            for e in epics:
                all_epic_numbers.add(e)
            area_title = _response_registry_text(spec.get("title")) or str(stream_id)
            areas.append(
                {
                    "id": f"area:{stream_id}",
                    "stream_id": stream_id,
                    "title": area_title,
                    "epic_count": len(epics),
                }
            )
            for epic_num in epics:
                edges.append(
                    {
                        "kind": "contains",
                        "from": f"area:{stream_id}",
                        "to": f"epic:{epic_num}",
                    }
                )

        open_by_epic: dict[int, list[int]] = {e: [] for e in all_epic_numbers}
        closed_by_epic: dict[int, list[int]] = {e: [] for e in all_epic_numbers}

        for issue_str, entry in effective_membership.items():
            if not isinstance(entry, dict):
                continue
            try:
                issue_num = int(issue_str)
            except (TypeError, ValueError):
                continue
            for e in entry.get("epics", []):
                try:
                    e_int = int(e)
                except (TypeError, ValueError):
                    continue
                if e_int not in open_by_epic:
                    continue
                if issue_num in open_issue_numbers:
                    open_by_epic[e_int].append(issue_num)
                else:
                    closed_by_epic[e_int].append(issue_num)

        epics_nodes: list[dict[str, Any]] = []
        issues_by_epic: dict[str, Any] = {}

        for stream_id, spec in streams_data.items():
            if not isinstance(spec, dict):
                continue
            epics = [int(n) for n in (spec.get("epics") or [])]
            for epic_num in epics:
                stream_key = f"epic:{epic_num}"
                row = projections.get(stream_key)
                lease_payload = None
                session_state = None
                if row is not None and row.get("lease_id") is not None:
                    lease = store._lease_from_row(row)
                    session_state = (
                        SessionState.EXPIRED.value if row.get("session_expired_at") else str(row["session_state"])
                    )
                    lease_payload = _lease_payload(
                        lease,
                        projection_state=str(row["state"]),
                        session_state=session_state,
                        now=now,
                    )
                digest = _digest_payload(store, stream_key, 3) if row is not None else {"pinned": [], "recent": []}
                latest = {entry["type"]: entry for entry in (*digest["pinned"], *digest["recent"])}
                reg_fields = (
                    _registry_fields(store, stream_key)
                    if row is not None
                    else {"registered": False, "stream_name": None, "title": None}
                )

                epic_title = reg_fields.get("title") or _response_registry_text(open_issue_titles.get(str(epic_num)))
                epic_reg_status = registry_status if reg_fields.get("registered") else "unregistered"

                open_issues = sorted(open_by_epic.get(epic_num, []))
                closed_issues = closed_by_epic.get(epic_num, [])
                open_count = len(open_issues)
                closed_count = len(closed_issues)

                epics_nodes.append(
                    {
                        "id": f"epic:{epic_num}",
                        "number": epic_num,
                        "area_id": stream_id,
                        "title": epic_title,
                        "registry_status": epic_reg_status,
                        "lease": lease_payload,
                        "session_state": session_state,
                        "last_state": latest.get(EntryType.STATE.value),
                        "last_decision": latest.get(EntryType.DECISION.value),
                        "last_next_action": latest.get(EntryType.NEXT_ACTION.value),
                        "open_issue_count": open_count,
                        "closed_issue_count": closed_count,
                    }
                )

                capped_items = open_issues[:50]
                issues_by_epic[str(epic_num)] = {
                    "items": [
                        {
                            "number": n,
                            "title": " ".join(str(open_issue_titles.get(str(n)) or f"Issue #{n}").split()),
                            "state": "open",
                            "url": f"https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/{n}",
                        }
                        for n in capped_items
                    ],
                    "total_open": open_count,
                    "truncated": open_count > 50,
                }

        payload: dict[str, Any] = {
            "schema": GRAPH_SCHEMA,
            "generated_at": isoformat_z(now),
            "nodes": {
                "areas": areas,
                "epics": epics_nodes,
            },
            "edges": edges,
            "issues_by_epic": issues_by_epic,
        }

        if report is None:
            if stale is not None:
                payload["stale"] = True
            else:
                payload["status"] = "no-cache"
                payload["ok"] = None

        refresh = audit.public_refresh_view(state)
        payload["refreshing"] = refresh["phase"] in {"scheduled", "running"}
        payload["refresh"] = refresh

        return payload

    try:
        payload = await asyncio.to_thread(_load)
        return JSONResponse(content=payload, headers={"Cache-Control": "no-store"})
    except Exception:
        return _server_error()


@router.get("/v1/{stream_id}")
def remote_epic_status(
    stream_id: str, limit: int = 20, ctx: MonitorContext = Depends(get_ctx)
) -> JSONResponse:
    try:
        stream_id = _epic_stream(stream_id)
        limit = _digest_limit(limit)
        return JSONResponse(
            content=_stream_response(_store(ctx), stream_id, limit), headers={"Cache-Control": "no-store"}
        )
    except NotFoundError:
        return _error(404, "epic stream not found")
    except (ValueError, ContentRejectedError):
        return _error(400, "invalid epic stream request")
    except Exception:
        return _server_error()


@router.post("/v1/{stream_id}/claim")
def remote_claim(
    stream_id: str, request: Request, body: dict[str, Any], ctx: MonitorContext = Depends(get_ctx)
) -> JSONResponse:
    denied = _check_mutation_peer(request)
    if denied is not None:
        return denied
    try:
        stream_id = _epic_stream(stream_id)
        session_id, lease_id, lineage_id, holder, ttl, limit = _claim_values({**body, "stream_id": stream_id})
        store = _store(ctx)
        _lease, outcome = store.claim_remote_session(
            stream_id=stream_id,
            holder=holder,
            lineage_id=lineage_id,
            ttl_seconds=ttl,
            session_id=session_id,
            lease_id=lease_id,
        )
        response = _stream_response(store, stream_id, limit)
        response["outcome"] = outcome
        return JSONResponse(content=response, headers={"Cache-Control": "no-store"})
    except LeaseConflictError:
        try:
            projection = _stream_response(store, stream_id, limit)
        except Exception:
            return _error(409, "lease conflict")
        lease = projection.get("lease")
        if not isinstance(lease, dict) or lease.get("state") != "active":
            return _error(409, "lease conflict")
        holder = lease.get("holder") or {}
        return _error(
            409,
            "epic stream already has live session; "
            f"current holder={holder.get('agent', '?')}/{holder.get('harness', '?')} "
            f"instance_id={holder.get('instance_id', '?')}; "
            f"expires_at={lease.get('expires_at', '?')}",
        )
    except (ValueError, ContentRejectedError):
        return _error(400, "invalid epic claim request")
    except (sqlite3.IntegrityError, LifecycleError):
        logger.exception("Remote epic claim rejected by a session-stream invariant")
        return _error(409, "epic claim rejected by a session-stream invariant")
    except Exception:
        return _server_error()


@router.post("/v1/{stream_id}/heartbeat")
def remote_heartbeat(
    stream_id: str, request: Request, body: dict[str, Any], ctx: MonitorContext = Depends(get_ctx)
) -> JSONResponse:
    denied = _check_mutation_peer(request)
    if denied is not None:
        return denied
    try:
        stream_id = _epic_stream(stream_id)
        lease = _lease_from_payload({**body, "stream_id": stream_id})
        if lease.stream_id != stream_id:
            raise ValueError("stream mismatch")
        store = _store(ctx)
        renewed = store.heartbeat(lease)
        projection = store.remote_stream_projection(stream_id)["lease"]
        return JSONResponse(
            content={
                "schema": SCHEMA,
                "lease": _lease_payload(
                    renewed,
                    projection_state=str(projection["state"]),
                    session_state=str(projection["session_state"]),
                    now=utc_now(),
                ),
            },
            headers={"Cache-Control": "no-store"},
        )
    except LeaseConflictError:
        return _error(409, "LEASE LOST")
    except (ValueError, ContentRejectedError):
        return _error(400, "invalid epic heartbeat request")
    except Exception:
        return _server_error()


@router.post("/v1/{stream_id}/handoff")
def remote_handoff(
    stream_id: str, request: Request, body: dict[str, Any], ctx: MonitorContext = Depends(get_ctx)
) -> JSONResponse:
    denied = _check_mutation_peer(request)
    if denied is not None:
        return denied
    try:
        stream_id = _epic_stream(stream_id)
        lease = _lease_from_payload({**body, "stream_id": stream_id})
        if lease.stream_id != stream_id:
            raise ValueError("stream mismatch")
        entry_type = EntryType(body.get("type"))
        body_text = body.get("body")
        if not isinstance(body_text, str):
            raise ValueError("body is invalid")
        # Idempotency-Key alias (#603 Phase 0b): a caller may supply the key via the
        # HTTP header instead of (or identically alongside) body.idempotency_key. A
        # header that disagrees with a supplied body value is refused outright rather
        # than silently preferring one — the two must name the same retry.
        header_key = request.headers.get("Idempotency-Key")
        body_key = body.get("idempotency_key")
        if header_key is not None and body_key is not None and header_key != body_key:
            raise ValueError("Idempotency-Key header conflicts with body.idempotency_key")
        idempotency_key = _token(header_key if header_key is not None else body_key, "idempotency_key")
        refs = []
        for ref in body.get("refs", []):
            if not isinstance(ref, dict) or ref.get("uri") is not None:
                raise ValueError("remote refs must use target_entry_id")
            refs.append(
                {
                    "kind": _token(ref.get("kind"), "reference kind"),
                    "target_entry_id": _integer(ref.get("target_entry_id"), "target_entry_id"),
                }
            )
        store = _store(ctx)
        # Snapshot the stream's high-water entry id before the append so a same-key
        # replay (append_entry returns the pre-existing entry rather than inserting)
        # can be told apart from a genuinely new entry for the ``Idempotent-Replayed``
        # response header, without adding a new store method for this slice.
        high_water_before = store.load_remote_digest(stream_id, limit=0).high_water_entry_id
        entry = store.append_entry(
            lease,
            entry_type=entry_type,
            body=body_text,
            idempotency_key=idempotency_key,
            refs=tuple(EntryRef(**ref) for ref in refs),
        )
        limit = _digest_limit(body.get("digest_limit", 20))
        headers = {"Cache-Control": "no-store"}
        if entry.entry_id <= high_water_before:
            headers["Idempotent-Replayed"] = "true"
        return JSONResponse(
            content={
                "schema": SCHEMA,
                "entry": _safe_entry(entry_as_dict(entry)),
                "digest": _digest_payload(store, stream_id, limit),
            },
            headers=headers,
        )
    except LeaseConflictError:
        return _error(409, "LEASE LOST")
    except (ValueError, ContentRejectedError):
        return _error(400, "invalid epic handoff request")
    except Exception:
        return _server_error()


@router.post("/v1/{stream_id}/bundles")
def remote_bundle_upload(
    stream_id: str, request: Request, body: dict[str, Any], ctx: MonitorContext = Depends(get_ctx)
) -> JSONResponse:
    """Upload one cross-host bundle through the same fenced loopback mutation path."""
    denied = _check_mutation_peer(request)
    if denied is not None:
        return denied
    try:
        stream_id = _epic_stream(stream_id)
        lease = _lease_from_payload({**body, "stream_id": stream_id})
        if lease.stream_id != stream_id:
            raise ValueError("stream mismatch")
        manifest = body.get("manifest")
        if not isinstance(manifest, dict):
            raise ValueError("bundle manifest must be an object")
        blob = _bundle_blob_from_body(body)
        _, members = _bundle_extract(blob, manifest_override=manifest)
        secret_hits = _bundle_secret_hits(members)
        if secret_hits:
            member, rule = secret_hits[0]
            raise ContentRejectedError(f"bundle member {member} matched {rule} rule")
        store = _store(ctx)
        stored = store.upload_bundle(lease, manifest=manifest, blob=blob)
        return JSONResponse(
            content={"schema": SCHEMA, **_bundle_api_payload(stored, include_blob=False)},
            headers={"Cache-Control": "no-store"},
        )
    except LeaseConflictError:
        return _error(409, "lease conflict")
    except (ValueError, ContentRejectedError, binascii.Error):
        return _error(400, "invalid rollover bundle upload request")
    except Exception:
        return _server_error()


@router.get("/v1/{stream_id}/bundles")
def remote_bundle_list(
    stream_id: str,
    agent: str | None = None,
    lineage_id: str | None = None,
    limit: int = 20,
    ctx: MonitorContext = Depends(get_ctx),
) -> JSONResponse:
    try:
        stream_id = _epic_stream(stream_id)
        bundles = _store(ctx).list_rollover_bundles(
            stream_id,
            agent=agent,
            lineage_id=lineage_id,
            limit=limit,
        )
        return JSONResponse(
            content={"schema": SCHEMA, "stream_id": stream_id, "bundles": bundles},
            headers={"Cache-Control": "no-store"},
        )
    except NotFoundError:
        return _error(404, "epic stream not found")
    except (ValueError, ContentRejectedError):
        return _error(400, "invalid rollover bundle list request")
    except Exception:
        return _server_error()


@router.get("/v1/{stream_id}/bundles/latest")
def remote_bundle_latest(
    stream_id: str,
    agent: str | None = None,
    lineage_id: str | None = None,
    ctx: MonitorContext = Depends(get_ctx),
) -> JSONResponse:
    try:
        stream_id = _epic_stream(stream_id)
        stored = _store(ctx).latest_rollover_bundle(stream_id, agent=agent, lineage_id=lineage_id)
        return JSONResponse(
            content={"schema": SCHEMA, "stream_id": stream_id, **_bundle_api_payload(stored, include_blob=True)},
            headers={"Cache-Control": "no-store"},
        )
    except NotFoundError:
        return _error(404, "rollover bundle not found")
    except (ValueError, ContentRejectedError):
        return _error(400, "invalid latest rollover bundle request")
    except Exception:
        return _server_error()


@router.get("/v1/{stream_id}/bundles/{upload_seq}")
def remote_bundle_by_upload_seq(
    stream_id: str, upload_seq: int, ctx: MonitorContext = Depends(get_ctx)
) -> JSONResponse:
    try:
        stream_id = _epic_stream(stream_id)
        stored = _store(ctx).rollover_bundle_by_upload_seq(stream_id, upload_seq)
        return JSONResponse(
            content={"schema": SCHEMA, "stream_id": stream_id, **_bundle_api_payload(stored, include_blob=True)},
            headers={"Cache-Control": "no-store"},
        )
    except NotFoundError:
        return _error(404, "rollover bundle not found")
    except (ValueError, ContentRejectedError):
        return _error(400, "invalid rollover bundle sequence request")
    except Exception:
        return _server_error()


@router.post("/v1/{stream_id}/release")
def remote_release(
    stream_id: str, request: Request, body: dict[str, Any], ctx: MonitorContext = Depends(get_ctx)
) -> JSONResponse:
    denied = _check_mutation_peer(request)
    if denied is not None:
        return denied
    try:
        stream_id = _epic_stream(stream_id)
        store = _store(ctx)
        if body.get("force") is True:
            actor_agent = _token(body.get("actor_agent"), "actor_agent")
            actor_host_id = _host(body.get("actor_host_id"))
            reason = body.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("reason is required")
            validate_entry_body(reason.strip())
            released = store.force_release_remote_session(
                stream_id=stream_id,
                actor_agent=actor_agent,
                actor_host_id=actor_host_id,
                reason=reason.strip(),
            )
            return JSONResponse(
                content={
                    "schema": SCHEMA,
                    "outcome": "force_released",
                    "lease": _lease_payload(
                        released, projection_state="released", session_state="closed", now=utc_now()
                    ),
                },
                headers={"Cache-Control": "no-store"},
            )
        lease = _lease_from_payload({**body, "stream_id": stream_id})
        if lease.stream_id != stream_id:
            raise ValueError("stream mismatch")
        store.release_remote_session(lease)
        return JSONResponse(
            content={
                "schema": SCHEMA,
                "outcome": "released",
                "lease": _lease_payload(lease, projection_state="released", session_state="closed", now=utc_now()),
            },
            headers={"Cache-Control": "no-store"},
        )
    except LeaseConflictError:
        return _error(409, "LEASE LOST")
    except (ValueError, ContentRejectedError):
        return _error(400, "invalid epic release request")
    except Exception:
        return _server_error()
