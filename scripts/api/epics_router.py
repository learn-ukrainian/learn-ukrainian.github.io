"""Remote TTL-fenced epic lifecycle API (design #7178, M1 of #7177)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from agents_extensions.shared.session_streams.db import SessionStreamDatabase, default_database_path
from agents_extensions.shared.session_streams.model import (
    EntryRef,
    EntryType,
    HolderKind,
    Lease,
    LeaseHolder,
    SessionState,
    entry_as_dict,
    parse_timestamp,
    utc_now,
    validate_stream_id,
)
from agents_extensions.shared.session_streams.store import (
    ContentRejectedError,
    LeaseConflictError,
    NotFoundError,
    SessionStreamStore,
    validate_entry_body,
)
from scripts.api.config import LIVE_REPO_ROOT
from scripts.api.observer_presence import _direct_loopback_peer
from scripts.api.occupancy_sanitize import opaque_host_id, safe_field

router = APIRouter()

SCHEMA = "remote-epic-lifecycle.v1"
DEFAULT_TTL_SECONDS = 15 * 60
MAX_DIGEST_LIMIT = 100
TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _store() -> SessionStreamStore:
    """Open the API-host store; the path never crosses the HTTP boundary."""
    return SessionStreamStore(SessionStreamDatabase(default_database_path(LIVE_REPO_ROOT)))


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
        "stream": _response_token(payload.get("stream")),
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
        "lease": lease_payload,
        "session_state": session_state,
        "digest": _digest_payload(store, stream_id, limit),
    }


def _check_mutation_peer(request: Request) -> JSONResponse | None:
    if not _direct_loopback_peer(request):
        return _error(403, "loopback mutation required")
    return None


def _claim_values(body: dict[str, Any]) -> tuple[str, str, str, LeaseHolder, int, int]:
    session_id = _token(body.get("session_id"), "session_id")
    lease_id = _token(body.get("lease_id"), "lease_id")
    lineage_id = _token(body.get("lineage_id"), "lineage_id")
    holder = _holder(body)
    ttl = _integer(body.get("ttl_seconds", DEFAULT_TTL_SECONDS), "ttl_seconds", maximum=86_400)
    limit = _digest_limit(body.get("digest_limit", 20))
    return session_id, lease_id, lineage_id, holder, ttl, limit


@router.get("/v1/health")
def remote_health() -> JSONResponse:
    try:
        store = _store()
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
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/v1")
def remote_epic_list() -> JSONResponse:
    try:
        store = _store()
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
                    "lease": lease_payload,
                    "session_state": session_state,
                    "last_state": latest.get(EntryType.STATE.value),
                    "last_decision": latest.get(EntryType.DECISION.value),
                    "last_next_action": latest.get(EntryType.NEXT_ACTION.value),
                }
            )
    except Exception:
        return _server_error()
    return JSONResponse(content={"schema": SCHEMA, "streams": rows}, headers={"Cache-Control": "no-store"})


@router.get("/v1/{stream_id}")
def remote_epic_status(stream_id: str, limit: int = 20) -> JSONResponse:
    try:
        stream_id = _epic_stream(stream_id)
        limit = _digest_limit(limit)
        return JSONResponse(content=_stream_response(_store(), stream_id, limit), headers={"Cache-Control": "no-store"})
    except NotFoundError:
        return _error(404, "epic stream not found")
    except (ValueError, ContentRejectedError):
        return _error(400, "invalid epic stream request")
    except Exception:
        return _server_error()


@router.post("/v1/{stream_id}/claim")
def remote_claim(stream_id: str, request: Request, body: dict[str, Any]) -> JSONResponse:
    denied = _check_mutation_peer(request)
    if denied is not None:
        return denied
    try:
        stream_id = _epic_stream(stream_id)
        session_id, lease_id, lineage_id, holder, ttl, limit = _claim_values({**body, "stream_id": stream_id})
        store = _store()
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
        return _error(409, "live holder or fenced claim conflict")
    except (ValueError, ContentRejectedError):
        return _error(400, "invalid epic claim request")
    except Exception:
        return _server_error()


@router.post("/v1/{stream_id}/heartbeat")
def remote_heartbeat(stream_id: str, request: Request, body: dict[str, Any]) -> JSONResponse:
    denied = _check_mutation_peer(request)
    if denied is not None:
        return denied
    try:
        stream_id = _epic_stream(stream_id)
        lease = _lease_from_payload({**body, "stream_id": stream_id})
        if lease.stream_id != stream_id:
            raise ValueError("stream mismatch")
        store = _store()
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
def remote_handoff(stream_id: str, request: Request, body: dict[str, Any]) -> JSONResponse:
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
        idempotency_key = _token(body.get("idempotency_key"), "idempotency_key")
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
        store = _store()
        entry = store.append_entry(
            lease,
            entry_type=entry_type,
            body=body_text,
            idempotency_key=idempotency_key,
            refs=tuple(EntryRef(**ref) for ref in refs),
        )
        limit = _digest_limit(body.get("digest_limit", 20))
        return JSONResponse(
            content={
                "schema": SCHEMA,
                "entry": _safe_entry(entry_as_dict(entry)),
                "digest": _digest_payload(store, stream_id, limit),
            },
            headers={"Cache-Control": "no-store"},
        )
    except LeaseConflictError:
        return _error(409, "LEASE LOST")
    except (ValueError, ContentRejectedError):
        return _error(400, "invalid epic handoff request")
    except Exception:
        return _server_error()


@router.post("/v1/{stream_id}/release")
def remote_release(stream_id: str, request: Request, body: dict[str, Any]) -> JSONResponse:
    denied = _check_mutation_peer(request)
    if denied is not None:
        return denied
    try:
        stream_id = _epic_stream(stream_id)
        store = _store()
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
