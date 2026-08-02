"""Explicit Entire 0.8.42 status refresh and read-only cache access."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .model import SchemaError, validate_identity
from .paths import provider_status_path

REQUIRED_ENTIRE_VERSION = "0.8.42"
PROVIDER_STATUS_MAX_AGE_SECONDS = 900


def _now_text() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _run(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["entire", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _agent_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = "-".join(value.strip().lower().split())
    try:
        validate_identity(normalized, field_name="agent")
    except SchemaError:
        return None
    return normalized


def refresh_provider_status(
    repo_root: Path,
    *,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Run an explicit bounded CLI probe and persist only allowlisted fields."""
    root = Path(repo_root).expanduser().resolve()
    target = output_path or provider_status_path(root)
    try:
        version_result = _run(root, "version")
    except (OSError, subprocess.TimeoutExpired):
        return {"available": False, "reason": "entire_cli_unavailable"}
    version_line = version_result.stdout.splitlines()[0] if version_result.stdout else ""
    version = version_line.removeprefix("Entire CLI ").strip()
    if version_result.returncode != 0 or version != REQUIRED_ENTIRE_VERSION:
        return {
            "available": False,
            "reason": "entire_version_mismatch",
            "required_version": REQUIRED_ENTIRE_VERSION,
        }
    try:
        status_result = _run(root, "status", "--json")
        raw = json.loads(status_result.stdout) if status_result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        raw = None
    if not isinstance(raw, dict):
        return {"available": False, "reason": "entire_status_unavailable"}
    agents = [agent_id for agent in raw.get("agents", []) if (agent_id := _agent_id(agent))]
    active_sessions = []
    for session in raw.get("active_sessions", []):
        if not isinstance(session, dict):
            continue
        agent = _agent_id(session.get("agent"))
        status = session.get("status")
        if agent is not None and status in {"active", "ended", "unknown"}:
            active_sessions.append({"agent": agent, "status": status})
    payload = {
        "schema": "entire-provider-status.v1",
        "available": True,
        "generated_at": _now_text(),
        "version": version,
        "required_version": REQUIRED_ENTIRE_VERSION,
        "enabled": raw.get("enabled") is True,
        "installed_agents": sorted(set(agents)),
        "active_sessions": sorted(
            active_sessions, key=lambda item: (item["agent"], item["status"])
        ),
        "source": "entire-cli",
    }
    _atomic_write(target, payload)
    return payload


def load_provider_status(
    repo_root: Path,
    *,
    status_path: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Read the sanitized local cache without invoking Entire or the network."""
    target = status_path or provider_status_path(repo_root)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"available": False, "reason": "provider_status_missing"}
    if not isinstance(payload, dict) or payload.get("schema") != "entire-provider-status.v1":
        return {"available": False, "reason": "provider_status_unreadable"}
    try:
        generated = datetime.fromisoformat(str(payload["generated_at"]).replace("Z", "+00:00"))
        age = max(0, int(((now or datetime.now(UTC)) - generated).total_seconds()))
    except (KeyError, TypeError, ValueError):
        return {"available": False, "reason": "provider_status_unreadable"}
    safe = {
        key: payload[key]
        for key in (
            "schema",
            "available",
            "generated_at",
            "version",
            "required_version",
            "enabled",
            "installed_agents",
            "active_sessions",
            "source",
        )
        if key in payload
    }
    safe.update(
        {
            "age_seconds": age,
            "stale": age > PROVIDER_STATUS_MAX_AGE_SECONDS,
        }
    )
    return safe
