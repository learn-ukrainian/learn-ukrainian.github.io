"""Loopback-only observer presence — no RAM lease, not a dispatch seat.

Grok Bot / QA Engineer / Cursor-driver / Codex-UI heartbeats land here so
occupancy can show the current task without ``POST /api/agent-monitor/register``.
In-process TTL store; a Monitor restart drops rows (callers heartbeat). Never
writes fleet-comms. A live ``/api/fleet/agents`` row is not occupancy evidence.
"""

from __future__ import annotations

import ipaddress
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, StrictInt, field_validator

from scripts.api.monitor_context import MonitorContext, get_ctx
from scripts.api.occupancy_sanitize import (
    CLOUD_OBSERVER_HOST_ID,
)
from scripts.api.occupancy_sanitize import (
    safe_field as _safe_field,
)
from scripts.api.occupancy_sanitize import (
    safe_summary as _safe_summary,
)

router = APIRouter(tags=["observer"])

ALLOWED_AGENTS = frozenset({"grok-bot", "qa-engineer", "cursor", "codex", "claude"})
ALLOWED_STATUSES = frozenset({"working", "blocked", "idle"})
PRESENCE_TTL_SECONDS = 15 * 60
PRESENCE_HEARTBEAT_INTERVAL_SECONDS = 5 * 60
PRESENCE_FRESHNESS_GRACE_SECONDS = 2 * 60
PRESENCE_FRESHNESS_SECONDS = PRESENCE_HEARTBEAT_INTERVAL_SECONDS + PRESENCE_FRESHNESS_GRACE_SECONDS
MAX_TELEMETRY_TOKENS = 10_000_000
KIND_OBSERVER = "observer"
MAC_OPERATOR_HOST_ID = "mac-operator"
NOTEBOOK_SESSION_AGENTS = frozenset({"claude", "codex", "cursor"})

_STORE_LOCK = threading.Lock()
_STORE: dict[tuple[str, str, str], ObserverPresence] = {}

PresenceStore = dict[tuple[str, str, str], "ObserverPresence"]


def _resolve_store(store: PresenceStore | None) -> PresenceStore:
    """Use the injected store when provided; otherwise the production singleton.

    ``production_context().stores.presence_store`` is this same object; fixture
    contexts own a fresh dict. Callers must never look up a module-global app.
    """
    return store if store is not None else _STORE


@dataclass(frozen=True)
class ObserverPresence:
    agent: str
    kind: str
    task_id: str | None
    epic: str | None
    status: str
    summary: str | None
    host_id: str
    instance_id: str | None
    ctx_tokens: int | None
    window_tokens: int | None
    updated_at: str
    updated_at_mono: float
    expires_at_mono: float


class PresenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: str
    kind: Literal["observer"] = "observer"
    task_id: str | None = None
    epic: str | None = None
    status: Literal["working", "blocked", "idle"]
    summary: str | None = None
    host_id: str | None = None
    instance_id: str | None = None
    ctx_tokens: StrictInt | None = None
    window_tokens: StrictInt | None = None

    @field_validator("agent", "task_id", "epic", "summary", "host_id", "instance_id", mode="before")
    @classmethod
    def _strip_optional(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("ctx_tokens", "window_tokens")
    @classmethod
    def _validate_token_count(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 0 or value > MAX_TELEMETRY_TOKENS:
            raise ValueError("token count is outside the accepted bound")
        return value


class PresenceRequestForbidden(ValueError):
    """Loopback or field validation failed after pydantic parsing."""


def reset_observer_presence(store: PresenceStore | None = None) -> None:
    """Test helper: drop every heartbeat in the given (or production) store."""
    target = _resolve_store(store)
    with _STORE_LOCK:
        target.clear()


def list_live(
    *,
    now_mono: float | None = None,
    store: PresenceStore | None = None,
) -> list[ObserverPresence]:
    deadline = time.monotonic() if now_mono is None else now_mono
    target = _resolve_store(store)
    with _STORE_LOCK:
        stale = [key for key, row in target.items() if row.expires_at_mono <= deadline]
        for key in stale:
            del target[key]
        return list(target.values())


def _allowed_host_ids() -> set[str]:
    allowed = {CLOUD_OBSERVER_HOST_ID, MAC_OPERATOR_HOST_ID}
    try:
        from scripts.api.occupancy import parse_host_id_map  # noqa: PLC0415 — # lazy-ok: occupancy cycle breaker

        allowed.update(parse_host_id_map().values())
    except Exception:
        pass
    return allowed


def _presence_host_id(value: str | None) -> str:
    if value is None:
        return CLOUD_OBSERVER_HOST_ID
    if value == CLOUD_OBSERVER_HOST_ID:
        return value
    host_id = _safe_field(value, role="host_id")
    if host_id is None or host_id not in _allowed_host_ids():
        raise PresenceRequestForbidden("invalid host_id")
    return host_id


def _presence_instance_id(value: str | None) -> str | None:
    if value is None:
        return None
    instance_id = _safe_field(value, role="task_id")
    if instance_id is None:
        raise PresenceRequestForbidden("invalid instance_id")
    return instance_id


def upsert_presence(
    payload: PresenceRequest,
    *,
    now_mono: float | None = None,
    ttl_seconds: int = PRESENCE_TTL_SECONDS,
    store: PresenceStore | None = None,
) -> ObserverPresence:
    agent = _safe_field(payload.agent, role="agent")
    if agent not in ALLOWED_AGENTS:
        raise PresenceRequestForbidden("unknown observer agent")
    task_id = _safe_field(payload.task_id, role="task_id") if payload.task_id else None
    if payload.task_id and task_id is None:
        raise PresenceRequestForbidden("invalid task_id")
    epic = _safe_field(payload.epic, role="agent") if payload.epic else None
    if payload.epic and epic is None:
        raise PresenceRequestForbidden("invalid epic")
    if payload.status not in ALLOWED_STATUSES:
        raise PresenceRequestForbidden("invalid status")
    summary = _safe_summary(payload.summary)
    if payload.summary and summary is None:
        raise PresenceRequestForbidden("invalid summary")
    host_id = _presence_host_id(payload.host_id)
    # Cloud observer rows predate notebook Claude seats. Preserve that legacy
    # contract while allowing the explicit opaque notebook host.
    if agent == "claude" and host_id == CLOUD_OBSERVER_HOST_ID:
        raise PresenceRequestForbidden("claude requires an explicit notebook host")
    instance_id = _presence_instance_id(payload.instance_id)

    stamp = time.monotonic() if now_mono is None else now_mono
    row = ObserverPresence(
        agent=agent,
        kind=KIND_OBSERVER,
        task_id=task_id,
        epic=epic,
        status=payload.status,
        summary=summary,
        host_id=host_id,
        instance_id=instance_id,
        ctx_tokens=payload.ctx_tokens,
        window_tokens=payload.window_tokens,
        updated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        updated_at_mono=stamp,
        expires_at_mono=stamp + ttl_seconds,
    )
    key = (host_id, agent, instance_id or "default")
    target = _resolve_store(store)
    with _STORE_LOCK:
        target[key] = row
    return row


def fresh_presence_for_session(
    session_id: str,
    *,
    now_mono: float | None = None,
    max_age_seconds: float = PRESENCE_FRESHNESS_SECONDS,
    store: PresenceStore | None = None,
) -> tuple[ObserverPresence, float] | None:
    """Return only a fresh row whose instance id exactly matches the caller."""
    deadline = time.monotonic() if now_mono is None else now_mono
    for row in list_live(now_mono=deadline, store=store):
        if row.instance_id != session_id:
            continue
        age = max(0.0, deadline - row.updated_at_mono)
        if age <= max_age_seconds:
            return row, age
    return None


def fresh_notebook_presence_for_session(
    session_id: str,
    *,
    now_mono: float | None = None,
    max_age_seconds: float = PRESENCE_FRESHNESS_SECONDS,
    store: PresenceStore | None = None,
) -> tuple[ObserverPresence, float] | None:
    """Return a fresh eligible notebook session without cross-host shadowing."""
    deadline = time.monotonic() if now_mono is None else now_mono
    for row in list_live(now_mono=deadline, store=store):
        if (
            row.instance_id != session_id
            or row.host_id != MAC_OPERATOR_HOST_ID
            or row.agent not in NOTEBOOK_SESSION_AGENTS
            or row.instance_id == "gui"
        ):
            continue
        age = max(0.0, deadline - row.updated_at_mono)
        if age <= max_age_seconds:
            return row, age
    return None


def _direct_loopback_peer(request: Request) -> bool:
    """Accept only a direct loopback peer addressed through a loopback host.

    ``request.client`` is the accepted connection, not a forwarding header.
    Requiring a loopback URL host closes DNS-rebinding from a non-local origin.
    """
    client = request.client
    client_host = client.host if client else None
    if not isinstance(client_host, str):
        return False
    try:
        client_address = ipaddress.ip_address(client_host)
    except ValueError:
        return False
    client_mapped = getattr(client_address, "ipv4_mapped", None)
    if not client_address.is_loopback and not (client_mapped and client_mapped.is_loopback):
        return False

    url_host = request.url.hostname
    if url_host == "localhost":
        return True
    if not isinstance(url_host, str):
        return False
    try:
        url_address = ipaddress.ip_address(url_host)
    except ValueError:
        return False
    url_mapped = getattr(url_address, "ipv4_mapped", None)
    return url_address.is_loopback or bool(url_mapped and url_mapped.is_loopback)


def _row_payload(row: ObserverPresence) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "agent": row.agent,
        "kind": row.kind,
        "task_id": row.task_id,
        "epic": row.epic,
        "status": row.status,
        "summary": row.summary,
        "updated_at": row.updated_at,
        "ttl_seconds": PRESENCE_TTL_SECONDS,
        "host_id": row.host_id,
    }
    if row.instance_id is not None:
        payload["instance_id"] = row.instance_id
    if row.ctx_tokens is not None:
        payload["ctx_tokens"] = row.ctx_tokens
    if row.window_tokens is not None:
        payload["window_tokens"] = row.window_tokens
    return payload


@router.post("/presence")
async def post_presence(
    request: Request,
    body: PresenceRequest,
    ctx: MonitorContext = Depends(get_ctx),
) -> JSONResponse:
    no_store = {"Cache-Control": "no-store"}
    if not _direct_loopback_peer(request):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"}, headers=no_store)
    store = ctx.stores.presence_store
    if store is None:
        return JSONResponse(
            status_code=503,
            content={"detail": "presence store unavailable"},
            headers=no_store,
        )
    try:
        row = upsert_presence(body, store=store)
    except PresenceRequestForbidden:
        return JSONResponse(status_code=400, content={"detail": "invalid observer presence"}, headers=no_store)
    return JSONResponse(content=_row_payload(row), headers=no_store)
