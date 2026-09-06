"""Compact fleet overview projection (private #670 AC-OVERVIEW).

Read-only, fail-open overview of session streams, leases, and holders across the fleet.
"""

from __future__ import annotations

import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.api.occupancy_sanitize import opaque_host_id, safe_field

try:
    from agents_extensions.shared.session_streams.db import (
        SessionStreamDatabase,
        default_database_path,
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
    default_database_path = None  # type: ignore[assignment]
    SessionState = None  # type: ignore[assignment]
    parse_timestamp = None  # type: ignore[assignment]
    utc_now = None  # type: ignore[assignment]
    SessionStreamStore = None  # type: ignore[assignment]
    SessionStreamDatabase = None  # type: ignore[assignment]

SESSION_STREAMS_REL = Path(".agent/session-streams/v1/session-streams.sqlite3")
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


def _resolve_session_streams_db(repo_root: Path | None) -> Path:
    """Resolve primary-checkout session-streams DB (not worktree-local Path.cwd())."""
    if repo_root is not None:
        repo_root_path = Path(repo_root)
        if repo_root_path.is_file():
            return repo_root_path

    if HAS_SESSION_STREAMS and default_database_path is not None:
        try:
            return default_database_path(repo_root)
        except Exception:
            pass

    active = (Path(repo_root) if repo_root else Path.cwd()).resolve()
    if active.is_file():
        return active
    if (active / SESSION_STREAMS_REL).is_file():
        return active / SESSION_STREAMS_REL

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=active,
            check=False,
            capture_output=True,
            text=True,
            timeout=2.0,
        )
        common_dir_text = result.stdout.strip()
        if result.returncode == 0 and common_dir_text:
            common_dir = Path(common_dir_text)
            if common_dir.is_absolute() and common_dir.name == ".git":
                return common_dir.parent.resolve() / SESSION_STREAMS_REL
    except Exception:
        pass
    return active / SESSION_STREAMS_REL


def build_fleet_overview(
    repo_root: Path | None = None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build a compact, read-only overview of fleet session streams and leases.

    Fail-open: returns available=False on missing DB or error without raising.
    """
    if not HAS_SESSION_STREAMS:
        return {"available": False, "streams": []}

    try:
        db_path = _resolve_session_streams_db(repo_root)
    except Exception:
        return {"available": False, "streams": []}

    if not db_path.is_file():
        return {"available": False, "streams": []}

    try:
        store = SessionStreamStore(SessionStreamDatabase(db_path))
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
        stream_id = str(row["stream_id"])

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
            elif raw_state == "released":
                lease_state = "released"
            elif raw_state == "active":
                lease_state = "active"
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
