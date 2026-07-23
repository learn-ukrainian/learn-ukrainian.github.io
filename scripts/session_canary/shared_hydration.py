"""Fail-closed, bounded hydration capsules for long-lived driver lanes.

The capsule is deliberately a small, JSON-only handoff surface.  It carries
only normalized stream evidence; it never embeds command output or local
absolute paths.  A slow optional observation marks a capsule ``degraded`` but
does not stop a driver whose critical lease evidence remains sound.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import time
from collections.abc import Sequence
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
HYDRATION_DEADLINE_SECONDS = 0.100
CRITICAL_FIELDS = (
    "driver_identity",
    "stream_id",
    "lease_state",
    "fencing_token",
    "next_drive_boundary",
)

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |PGP )?PRIVATE KEY-----"),
    re.compile(r"(?:gh[pousr]_|github_pat_|sk-|AIza)[A-Za-z0-9_-]{12,}", re.IGNORECASE),
    re.compile(r"(?i)\b(?:authorization|api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]{12,}"),
)
_FORBIDDEN_KEYS = frozenset(
    {
        "raw_stdout",
        "raw_stderr",
        "stdout",
        "stderr",
        "output",
        "credential",
        "credentials",
        "password",
        "secret",
        "access_token",
        "api_key",
    }
)

HYDRATION_CAPSULE_V1_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://learn-ukrainian.local/schemas/HydrationCapsuleV1-1.2.json",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_name",
        "schema_version",
        "generated_at",
        "deadline_ms",
        "elapsed_ms",
        "state",
        "blocked",
        "execution_allowed",
        *CRITICAL_FIELDS,
    ],
    "properties": {
        "schema_name": {"const": "HydrationCapsuleV1"},
        "schema_version": {"const": "1.2"},
        "generated_at": {"type": "string", "format": "date-time"},
        "deadline_ms": {"type": "number", "const": 100.0},
        "elapsed_ms": {"type": "number", "minimum": 0},
        "state": {"enum": ["ready", "degraded", "blocked"]},
        "blocked": {"type": "boolean"},
        "execution_allowed": {"type": "boolean"},
        "driver_identity": {"$ref": "#/$defs/critical"},
        "stream_id": {"$ref": "#/$defs/critical"},
        "lease_state": {"$ref": "#/$defs/critical"},
        "fencing_token": {"$ref": "#/$defs/critical"},
        "next_drive_boundary": {"$ref": "#/$defs/critical"},
        "degradation_reasons": {
            "type": "array",
            "items": {"type": "string", "pattern": "^[a-z0-9][a-z0-9_-]{0,79}$"},
            "uniqueItems": True,
        },
    },
    "$defs": {
        "critical": {
            "oneOf": [
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["status", "value"],
                    "properties": {"status": {"const": "ok"}, "value": {}},
                },
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["status", "reason"],
                    "properties": {
                        "status": {"const": "unavailable"},
                        "reason": {"type": "string", "pattern": "^[a-z0-9][a-z0-9_-]{0,79}$"},
                    },
                },
            ]
        }
    },
}

_CAPSULE_VALIDATOR = Draft202012Validator(HYDRATION_CAPSULE_V1_SCHEMA, format_checker=FormatChecker())


class HydrationSanitizationError(ValueError):
    """Raised without echoing an unsafe value into a capsule or diagnostic."""


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_identity(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}", value))


def _normalize_path(value: str, *, repo_root: Path) -> str:
    """Return only a repo-relative path; refuse absolute and traversal escapes."""
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError as exc:
            raise HydrationSanitizationError("out-of-repo-path") from exc
    looks_like_path = (
        value.startswith(("./", "../", ".agent/", ".claude/", "agents_extensions/", "docs/", "scripts/", "tests/"))
        or (" " not in value and "://" not in value and "/" in value)
    )
    if looks_like_path:
        normalized = (repo_root / candidate).resolve()
        try:
            return normalized.relative_to(repo_root.resolve()).as_posix()
        except ValueError as exc:
            raise HydrationSanitizationError("out-of-repo-path") from exc
    return value


def sanitize_hydration_value(value: Any, *, repo_root: Path = ROOT, key: str | None = None) -> Any:
    """Deep-copy safe JSON values, normalizing repo paths and rejecting secrets.

    This intentionally rejects raw command-output keys rather than attempting
    to redact them: redaction is not a sound way to make untrusted output a
    durable driver artifact.
    """
    if key is not None and key.lower() in _FORBIDDEN_KEYS:
        raise HydrationSanitizationError("forbidden-raw-output-key")
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, Path):
        return _normalize_path(str(value), repo_root=repo_root)
    if isinstance(value, str):
        if "\x00" in value or any(pattern.search(value) for pattern in _SECRET_PATTERNS):
            raise HydrationSanitizationError("secret-or-control-data")
        return _normalize_path(value, repo_root=repo_root)
    if isinstance(value, list):
        return [sanitize_hydration_value(item, repo_root=repo_root) for item in value]
    if isinstance(value, tuple):
        return [sanitize_hydration_value(item, repo_root=repo_root) for item in value]
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for raw_key, item in value.items():
            if not isinstance(raw_key, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_:-]{0,79}", raw_key):
                raise HydrationSanitizationError("unsafe-object-key")
            sanitized[raw_key] = sanitize_hydration_value(item, repo_root=repo_root, key=raw_key)
        return sanitized
    raise HydrationSanitizationError("non-json-value")


def _reap_pid(process: subprocess.Popen[str], *, timeout: float) -> bool:
    """Reap ``process.pid`` with waitpid; return whether the child exited."""
    end = time.monotonic() + timeout
    while True:
        try:
            pid, status = os.waitpid(process.pid, os.WNOHANG)
        except ChildProcessError:
            return True
        if pid:
            process.returncode = os.waitstatus_to_exitcode(status)
            return True
        if time.monotonic() >= end:
            return False
        time.sleep(min(0.01, max(0.0, end - time.monotonic())))


def terminate_process_group(process: subprocess.Popen[str]) -> None:
    """Terminate a detached child group and synchronously reap its leader."""
    with suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    if _reap_pid(process, timeout=0.200):
        return
    with suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGKILL)
    _reap_pid(process, timeout=0.200)


def run_gh_json(arguments: Sequence[str], *, deadline: float, cwd: Path = ROOT) -> dict[str, Any] | None:
    """Run a bounded ``gh`` query without allowing stdout into a capsule.

    This is an optional enrichment primitive.  Callers receive parsed,
    sanitized JSON only; timeouts return ``None`` after process-group cleanup.
    """
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return None
    process = subprocess.Popen(
        ["gh", *arguments],
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, _ = process.communicate(timeout=max(0.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        terminate_process_group(process)
        return None
    if process.returncode != 0 or time.monotonic() > deadline:
        return None
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    return sanitize_hydration_value(payload, repo_root=cwd)


def _unavailable(reason: str) -> dict[str, str]:
    return {"status": "unavailable", "reason": reason}


def _ok(value: Any) -> dict[str, Any]:
    return {"status": "ok", "value": sanitize_hydration_value(value)}


def _collect_stream_evidence(stream_id: str) -> dict[str, Any]:
    """Read the smallest trusted stream snapshot required by the v1.2 fields."""
    from agents_extensions.shared.session_streams.db import SessionStreamDatabase
    from agents_extensions.shared.session_streams.model import validate_stream_id
    from agents_extensions.shared.session_streams.store import SessionStreamStore

    canonical_stream_id = validate_stream_id(stream_id)
    database = SessionStreamDatabase()
    with database.connect(read_only=True) as connection:
        lease = connection.execute(
            "SELECT * FROM stream_leases WHERE stream_id = ?", (canonical_stream_id,)
        ).fetchone()
        if lease is None:
            raise LookupError("lease-unavailable")
        session = connection.execute(
            "SELECT state FROM sessions WHERE stream_id = ? AND session_id = ?",
            (canonical_stream_id, str(lease["session_id"])),
        ).fetchone()
    if session is None or str(lease["state"]) != "active" or str(session["state"]) not in {"open", "rolling"}:
        raise LookupError("lease-not-active")

    digest = SessionStreamStore(database).load_digest(canonical_stream_id, limit=40)
    boundary = next((entry for entry in reversed(digest.recent) if entry.type.value == "next_action"), None)
    if boundary is None:
        raise LookupError("next-drive-boundary-unavailable")
    return {
        "driver_identity": {
            "agent": str(lease["holder_agent"]),
            "harness": str(lease["holder_harness"]),
            "instance_id": str(lease["holder_instance_id"]),
        },
        "lease_state": {"lease": str(lease["state"]), "session": str(session["state"])},
        "fencing_token": int(lease["fencing_token"]),
        "next_drive_boundary": {"entry_id": boundary.entry_id, "instruction": boundary.body},
    }


def _validate_capsule(capsule: dict[str, Any]) -> None:
    errors = sorted(_CAPSULE_VALIDATOR.iter_errors(capsule), key=lambda error: list(error.path))
    if errors:
        raise ValueError(f"invalid hydration capsule: {errors[0].message}")
    has_bad_critical = any(capsule[field]["status"] != "ok" for field in CRITICAL_FIELDS)
    if capsule["blocked"] != has_bad_critical or capsule["execution_allowed"] == has_bad_critical:
        raise ValueError("hydration critical-field execution invariant violated")
    if capsule["blocked"] and capsule["state"] != "blocked":
        raise ValueError("blocked hydration capsule must use blocked state")
    if not capsule["blocked"] and capsule["state"] == "blocked":
        raise ValueError("unblocked hydration capsule cannot use blocked state")


def build_hydration_capsule(stream_id: str, lane_name: str) -> dict[str, Any]:
    """Build and validate a v1.2 capsule within one global monotonic deadline."""
    start = time.monotonic()
    deadline = start + HYDRATION_DEADLINE_SECONDS
    fields: dict[str, dict[str, Any]] = {field: _unavailable("not-collected") for field in CRITICAL_FIELDS}
    degradations: list[str] = []

    if not _safe_identity(lane_name):
        fields["driver_identity"] = _unavailable("invalid-lane-name")
    else:
        fields["driver_identity"] = _ok({"lane": lane_name})
    try:
        from agents_extensions.shared.session_streams.model import validate_stream_id

        fields["stream_id"] = _ok(validate_stream_id(stream_id))
    except (ValueError, TypeError):
        fields["stream_id"] = _unavailable("invalid-stream-id")

    if fields["stream_id"]["status"] == "ok":
        try:
            evidence = _collect_stream_evidence(stream_id)
            identity = evidence["driver_identity"]
            if identity["agent"] != lane_name:
                fields["driver_identity"] = _unavailable("lane-lease-identity-mismatch")
            else:
                fields["driver_identity"] = _ok(identity | {"lane": lane_name})
            for field in ("lease_state", "fencing_token", "next_drive_boundary"):
                fields[field] = _ok(evidence[field])
        except HydrationSanitizationError:
            degradations.append("unsafe-stream-evidence")
            for field in ("driver_identity", "lease_state", "fencing_token", "next_drive_boundary"):
                fields[field] = _unavailable("unsafe-stream-evidence")
        except (LookupError, OSError, RuntimeError, ValueError):
            for field in ("lease_state", "fencing_token", "next_drive_boundary"):
                fields[field] = _unavailable("stream-evidence-unavailable")

    elapsed_ms = (time.monotonic() - start) * 1000
    if time.monotonic() > deadline:
        degradations.append("deadline-exceeded")
    blocked = any(fields[field]["status"] != "ok" for field in CRITICAL_FIELDS)
    capsule: dict[str, Any] = {
        "schema_name": "HydrationCapsuleV1",
        "schema_version": "1.2",
        "generated_at": _utc_now(),
        "deadline_ms": HYDRATION_DEADLINE_SECONDS * 1000,
        "elapsed_ms": elapsed_ms,
        "state": "blocked" if blocked else "degraded" if degradations else "ready",
        "blocked": blocked,
        "execution_allowed": not blocked,
        **fields,
        "degradation_reasons": sorted(set(degradations)),
    }
    _validate_capsule(capsule)
    return capsule
