"""Compact fleet overview projection (private #670 AC-OVERVIEW).

Read-only, fail-open overview of session streams, leases, and holders across the fleet.
Uses authoritative remote GET /api/epics/v1 (or injected epics_store in Monitor facade).
Never opens local session-stream SQLite.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.api.occupancy_sanitize import opaque_host_id, safe_field

try:
    from agents_extensions.shared.session_streams.db import (
        SessionStreamDatabase,
    )
    from agents_extensions.shared.session_streams.model import (
        SessionState,
        parse_timestamp,
        utc_now,
    )
    from agents_extensions.shared.session_streams.store import SessionStreamStore

    HAS_SESSION_STREAMS = True
except ImportError:
    HAS_SESSION_STREAMS = False
    SessionState = None  # type: ignore[assignment]
    parse_timestamp = None  # type: ignore[assignment]
    utc_now = None  # type: ignore[assignment]
    SessionStreamStore = None  # type: ignore[assignment]
    SessionStreamDatabase = None  # type: ignore[assignment]

DEFAULT_MONITOR_URL = "http://127.0.0.1:8765"
DEFAULT_TIMEOUT_SECONDS = 3.0
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

OMITTED = object()


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


def _response_token(value: Any) -> str:
    return value if isinstance(value, str) and safe_field(value, role="task_id") == value else "[redacted]"


def _response_host(value: Any) -> str | None:
    return None if value is None else value if isinstance(value, str) and opaque_host_id(value) else "[redacted]"


def resolve_monitor_url(raw: str | None = None) -> str:
    """Resolve configured Monitor base URL without exposing internal credentials."""
    candidate = (
        raw
        or os.environ.get("LU_MONITOR_LOOPBACK")
        or os.environ.get("MONITOR_API_BASE_URL")
        or os.environ.get("MONITOR_API_URL")
        or DEFAULT_MONITOR_URL
    ).strip()
    try:
        from scripts.session_supervisor.remote import monitor_url

        return monitor_url(candidate)
    except Exception:
        parsed = urllib.parse.urlparse(candidate)
        port = parsed.port or 8765
        return f"http://127.0.0.1:{port}"


def _project_stream_from_remote(
    stream: dict[str, Any],
    *,
    current_time: datetime,
) -> dict[str, Any]:
    stream_id = str(stream.get("stream_id") or "")
    stream_name = _response_registry_text(stream.get("stream_name"))
    lease = stream.get("lease")
    if not isinstance(lease, dict):
        return {
            "stream_id": stream_id,
            "stream_name": stream_name,
            "lease_state": "unleased",
            "holder": None,
            "heartbeat_age_seconds": None,
            "expires_at": None,
            "session_state": None,
            "unknown": True,
            "stale": False,
        }

    raw_state = str(lease.get("state") or "")
    expires_at = lease.get("expires_at")
    if expires_at is not None:
        expires_at = str(expires_at)

    is_expired = False
    if parse_timestamp is not None and expires_at:
        try:
            exp_dt = parse_timestamp(expires_at)
            is_expired = raw_state == "active" and current_time >= exp_dt
        except Exception:
            is_expired = False

    if is_expired:
        lease_state = "expired"
    elif raw_state in ("active", "released", "expired"):
        lease_state = raw_state
    else:
        lease_state = raw_state or "expired"

    heartbeat_age_seconds = None
    heartbeat_at = lease.get("heartbeat_at")
    if parse_timestamp is not None and heartbeat_at:
        try:
            hb_dt = parse_timestamp(str(heartbeat_at))
            heartbeat_age_seconds = max(0, int((current_time - hb_dt).total_seconds()))
        except Exception:
            heartbeat_age_seconds = None
    if heartbeat_age_seconds is None and lease.get("age_seconds") is not None:
        with contextlib.suppress(ValueError, TypeError):
            heartbeat_age_seconds = max(0, int(lease["age_seconds"]))

    holder_payload = lease.get("holder")
    holder = None
    if isinstance(holder_payload, dict):
        holder = {
            "agent": _response_token(holder_payload.get("agent")),
            "harness": _response_token(holder_payload.get("harness")),
            "instance_id": _response_token(holder_payload.get("instance_id")),
            "host_id": _response_host(holder_payload.get("host_id")),
        }

    expired_session_val = SessionState.EXPIRED.value if SessionState is not None else "expired"
    session_state = (
        str(stream["session_state"])
        if stream.get("session_state") is not None
        else (str(lease["session_state"]) if lease.get("session_state") is not None else None)
    )

    is_stale = lease_state == "expired" or session_state == expired_session_val

    return {
        "stream_id": stream_id,
        "stream_name": stream_name,
        "lease_state": lease_state,
        "holder": holder,
        "heartbeat_age_seconds": heartbeat_age_seconds,
        "expires_at": expires_at,
        "session_state": session_state,
        "unknown": False,
        "stale": is_stale,
    }


def fetch_remote_fleet_overview(
    *,
    monitor_url: str | None = None,
    now: datetime | None = None,
    opener: Callable[..., Any] | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Read existing GET /api/epics/v1 from configured Monitor endpoint (fail-open)."""
    try:
        base = resolve_monitor_url(monitor_url)
        url = f"{base}/api/epics/v1"
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "fleet-comms-overview/1.0",
            },
            method="GET",
        )
        urlopen = opener or urllib.request.urlopen
        with urlopen(req, timeout=timeout_seconds) as resp:
            status_code = int(getattr(resp, "status", getattr(resp, "code", 200)))
            if status_code != 200:
                return {"available": False, "streams": []}
            raw = resp.read()
            text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
            data = json.loads(text)
    except Exception:
        return {"available": False, "streams": []}

    if not isinstance(data, dict):
        return {"available": False, "streams": []}

    raw_streams = data.get("streams")
    if not isinstance(raw_streams, list):
        return {"available": False, "streams": []}

    current_time = now or (utc_now() if utc_now is not None else datetime.now(UTC))
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=UTC)

    streams: list[dict[str, Any]] = []
    for item in raw_streams:
        if isinstance(item, dict):
            try:
                streams.append(_project_stream_from_remote(item, current_time=current_time))
            except Exception:
                streams.append(
                    {
                        "stream_id": str(item.get("stream_id") or ""),
                        "stream_name": _response_registry_text(item.get("stream_name")),
                        "lease_state": "unleased",
                        "holder": None,
                        "heartbeat_age_seconds": None,
                        "expires_at": None,
                        "session_state": None,
                        "unknown": True,
                        "stale": False,
                    }
                )

    return {
        "available": True,
        "streams": streams,
    }


def build_fleet_overview_from_store(
    store: Any,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build fleet overview from the injected SessionStreamStore (no local DB construction)."""
    if store is None or not HAS_SESSION_STREAMS:
        return {"available": False, "streams": []}

    try:
        projections = store.list_remote_projections()
    except Exception:
        return {"available": False, "streams": []}

    current_time = now or (utc_now() if utc_now is not None else datetime.now(UTC))
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=UTC)

    try:
        snapshot_sha256 = store.latest_inventory_source_sha()
    except Exception:
        snapshot_sha256 = None

    streams: list[dict[str, Any]] = []
    for row in projections:
        stream_id = str(row.get("stream_id") or "")

        stream_name = None
        try:
            registry_meta = store.remote_registry_projection(stream_id, snapshot_sha256=snapshot_sha256)
            stream_name = _response_registry_text(registry_meta.get("stream_name"))
        except Exception:
            stream_name = None

        has_lease = row.get("lease_id") is not None
        if not has_lease:
            streams.append(
                {
                    "stream_id": stream_id,
                    "stream_name": stream_name,
                    "lease_state": "unleased",
                    "holder": None,
                    "heartbeat_age_seconds": None,
                    "expires_at": None,
                    "session_state": None,
                    "unknown": True,
                    "stale": False,
                }
            )
            continue

        try:
            lease = store._lease_from_row(row)
            raw_state = str(row.get("state") or "")
            expires_at = lease.expires_at

            is_expired = False
            if parse_timestamp is not None:
                try:
                    exp_dt = parse_timestamp(expires_at)
                    is_expired = raw_state == "active" and current_time >= exp_dt
                except Exception:
                    is_expired = False

            if is_expired:
                lease_state = "expired"
            elif raw_state in ("active", "released", "expired"):
                lease_state = raw_state
            else:
                lease_state = raw_state or "expired"

            heartbeat_age_seconds = None
            if parse_timestamp is not None and lease.heartbeat_at:
                try:
                    hb_dt = parse_timestamp(lease.heartbeat_at)
                    heartbeat_age_seconds = max(0, int((current_time - hb_dt).total_seconds()))
                except Exception:
                    heartbeat_age_seconds = None

            holder = {
                "agent": _response_token(lease.holder.agent),
                "harness": _response_token(lease.holder.harness),
                "instance_id": _response_token(lease.holder.instance_id),
                "host_id": _response_host(lease.holder.host_id),
            }

            expired_session_val = SessionState.EXPIRED.value if SessionState is not None else "expired"
            session_state = (
                expired_session_val
                if row.get("session_expired_at")
                else (str(row["session_state"]) if row.get("session_state") is not None else None)
            )

            is_stale = lease_state == "expired" or session_state == expired_session_val

            streams.append(
                {
                    "stream_id": stream_id,
                    "stream_name": stream_name,
                    "lease_state": lease_state,
                    "holder": holder,
                    "heartbeat_age_seconds": heartbeat_age_seconds,
                    "expires_at": expires_at,
                    "session_state": session_state,
                    "unknown": False,
                    "stale": is_stale,
                }
            )
        except Exception:
            streams.append(
                {
                    "stream_id": stream_id,
                    "stream_name": stream_name,
                    "lease_state": "unleased",
                    "holder": None,
                    "heartbeat_age_seconds": None,
                    "expires_at": None,
                    "session_state": None,
                    "unknown": True,
                    "stale": False,
                }
            )

    return {
        "available": True,
        "streams": streams,
    }


def build_fleet_overview(
    repo_root: Path | None = None,
    *,
    epics_store: Any = OMITTED,
    monitor_url: str | None = None,
    now: datetime | None = None,
    opener: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Build a compact, read-only overview of fleet session streams and leases.

    Authority order:
    1. If an epics_store is injected (Monitor facade), project from the store.
       If explicitly passed as None, returns available=False.
    2. Otherwise (CLI fleet status / remote callers), query GET /api/epics/v1
       against the configured Monitor loopback endpoint.
    3. Fail-open: returns available=False if unreachable or error.
       Never constructs or opens local session-stream SQLite.
    """
    if epics_store is not OMITTED:
        return build_fleet_overview_from_store(epics_store, now=now)

    return fetch_remote_fleet_overview(
        monitor_url=monitor_url,
        now=now,
        opener=opener,
    )
