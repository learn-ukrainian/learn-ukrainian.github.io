"""Best-effort central JSONL telemetry emitter.

This module is intentionally file-only: no network calls, no API posts. The
durable source of truth for this PR is the append-only JSONL log under
``batch_state/telemetry/events/``.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from secret_redactor import redact_text, redact_value
except ImportError:  # pragma: no cover - package import path
    from scripts.secret_redactor import redact_text, redact_value

SCHEMA_VERSION = 1
_DISABLED_ENV = "LU_TELEMETRY_DISABLED"
_RUN_ID_ENV = "LU_RUN_ID"
_SESSION_ID_ENV = "LU_SESSION_ID"
_SOURCE_ENV = "LU_TELEMETRY_SOURCE"
_RECURSION_GUARD_ENV = "LU_TELEMETRY_EMITTING"
_logger = logging.getLogger(__name__)
_emitting = False


def current_run_id() -> str:
    """Return the current run id, minting and exporting one if absent."""
    return _current_or_new_env_id(_RUN_ID_ENV, "run")


def current_session_id() -> str:
    """Return the current telemetry session id, minting and exporting one if absent."""
    return _current_or_new_env_id(_SESSION_ID_ENV, "session")


def emit_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    run_id: str | None = None,
) -> None:
    """Append one central telemetry event.

    Telemetry is best-effort observability. This function must never fail the
    caller, even on serialization errors, missing directories, permission
    errors, or accidental recursive emission.
    """
    global _emitting
    try:
        if os.environ.get(_DISABLED_ENV) == "1":
            return None
        if _emitting or os.environ.get(_RECURSION_GUARD_ENV) == "1":
            return None

        _emitting = True
        previous_guard = os.environ.get(_RECURSION_GUARD_ENV)
        os.environ[_RECURSION_GUARD_ENV] = "1"
        try:
            event = {
                "schema_version": SCHEMA_VERSION,
                "ts": datetime.now(UTC).isoformat(),
                "event_type": str(event_type),
                "run_id": str(run_id or current_run_id()),
                "session_id": current_session_id(),
                "source": os.environ.get(_SOURCE_ENV) or "local",
            }
            event.update(payload)
            event = redact_value(event)

            path = _event_file()
            line = (
                json.dumps(event, ensure_ascii=False, default=str) + "\n"
            ).encode("utf-8")
            _write_line(path, line)
        finally:
            if previous_guard is None:
                os.environ.pop(_RECURSION_GUARD_ENV, None)
            else:
                os.environ[_RECURSION_GUARD_ENV] = previous_guard
            _emitting = False
    except Exception as exc:  # pragma: no cover - degraded mode only
        safe_exc = redact_text(str(exc)) or ""
        _logger.debug(
            "failed to emit telemetry event: %s: %s",
            type(exc).__name__,
            safe_exc,
        )
    return None


def _current_or_new_env_id(env_name: str, prefix: str) -> str:
    value = os.environ.get(env_name)
    if value:
        return value
    value = f"{prefix}_{uuid.uuid4().hex}"
    os.environ[env_name] = value
    return value


def _event_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "batch_state" / "telemetry" / "events"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _event_file(day: datetime | None = None) -> Path:
    if day is None:
        day = datetime.now(UTC)
    return _event_dir() / f"{day:%Y-%m-%d}.jsonl"


def _write_line(path: Path, line: bytes) -> None:
    fd = os.open(str(path), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)
