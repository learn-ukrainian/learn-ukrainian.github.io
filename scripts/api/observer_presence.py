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

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, field_validator

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

ALLOWED_AGENTS = frozenset({"grok-bot", "qa-engineer", "cursor", "codex"})
ALLOWED_STATUSES = frozenset({"working", "blocked", "idle"})
PRESENCE_TTL_SECONDS = 15 * 60
KIND_OBSERVER = "observer"

_STORE_LOCK = threading.Lock()
_STORE: dict[str, ObserverPresence] = {}


@dataclass(frozen=True)
class ObserverPresence:
    agent: str
    kind: str
    task_id: str
    epic: str | None
    status: str
    summary: str | None
    updated_at: str
    expires_at_mono: float


class PresenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: str
    kind: Literal["observer"] = "observer"
    task_id: str
    epic: str | None = None
    status: Literal["working", "blocked", "idle"]
    summary: str | None = None

    @field_validator("agent", "task_id", "epic", "summary", mode="before")
    @classmethod
    def _strip_optional(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip() or None
        return value


class PresenceRequestForbidden(ValueError):
    """Loopback or field validation failed after pydantic parsing."""


def reset_observer_presence() -> None:
    """Test helper: drop every heartbeat."""
    with _STORE_LOCK:
        _STORE.clear()


def list_live(*, now_mono: float | None = None) -> list[ObserverPresence]:
    deadline = time.monotonic() if now_mono is None else now_mono
    with _STORE_LOCK:
        stale = [agent for agent, row in _STORE.items() if row.expires_at_mono <= deadline]
        for agent in stale:
            del _STORE[agent]
        return list(_STORE.values())


def upsert_presence(
    payload: PresenceRequest,
    *,
    now_mono: float | None = None,
    ttl_seconds: int = PRESENCE_TTL_SECONDS,
) -> ObserverPresence:
    agent = _safe_field(payload.agent, role="agent")
    if agent not in ALLOWED_AGENTS:
        raise PresenceRequestForbidden("unknown observer agent")
    task_id = _safe_field(payload.task_id, role="task_id")
    if task_id is None:
        raise PresenceRequestForbidden("invalid task_id")
    epic = _safe_field(payload.epic, role="agent") if payload.epic else None
    if payload.epic and epic is None:
        raise PresenceRequestForbidden("invalid epic")
    if payload.status not in ALLOWED_STATUSES:
        raise PresenceRequestForbidden("invalid status")
    summary = _safe_summary(payload.summary)
    if payload.summary and summary is None:
        raise PresenceRequestForbidden("invalid summary")

    stamp = time.monotonic() if now_mono is None else now_mono
    row = ObserverPresence(
        agent=agent,
        kind=KIND_OBSERVER,
        task_id=task_id,
        epic=epic,
        status=payload.status,
        summary=summary,
        updated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        expires_at_mono=stamp + ttl_seconds,
    )
    with _STORE_LOCK:
        _STORE[agent] = row
    return row


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
    return {
        "agent": row.agent,
        "kind": row.kind,
        "task_id": row.task_id,
        "epic": row.epic,
        "status": row.status,
        "summary": row.summary,
        "updated_at": row.updated_at,
        "ttl_seconds": PRESENCE_TTL_SECONDS,
        "host_id": CLOUD_OBSERVER_HOST_ID,
    }


@router.post("/presence")
async def post_presence(request: Request, body: PresenceRequest) -> JSONResponse:
    no_store = {"Cache-Control": "no-store"}
    if not _direct_loopback_peer(request):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"}, headers=no_store)
    try:
        row = upsert_presence(body)
    except PresenceRequestForbidden:
        return JSONResponse(status_code=400, content={"detail": "invalid observer presence"}, headers=no_store)
    return JSONResponse(content=_row_payload(row), headers=no_store)
