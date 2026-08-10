"""Uniform model, effort, and reply-provenance contract for ``ask-*`` lanes."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

EFFORT_CHOICES = ("low", "medium", "high", "xhigh", "max")

NATIVE_ASK_TOOL_CONTRACT = (
    "shell commands are unavailable in this mode; answer from attached material and file reads."
)

# Documented bound for total automatic re-fires of a single ask across all hardening
# mechanisms (retry-once watchdog + cancel-and-retell).
MAX_TOTAL_ASK_RETRIES = 2


def resolve_model_selection(
    *,
    lane: str,
    to_model: str | None,
    model: str | None,
    default: str,
) -> str:
    """Resolve the canonical flag while rejecting ambiguous legacy input."""
    if to_model and model and to_model != model:
        raise ValueError(
            f"{lane}: --to-model ({to_model}) conflicts with deprecated --model ({model}); "
            "provide one model value or make them identical"
        )
    return to_model or model or default


def request_metadata(message: Mapping[str, Any]) -> dict[str, Any]:
    """Return the JSON metadata persisted with an ask row, or an empty mapping."""
    data = message.get("data")
    if not data:
        return {}
    if isinstance(data, Mapping):
        return dict(data)
    try:
        decoded = json.loads(data)
    except (TypeError, json.JSONDecodeError):
        return {}
    return dict(decoded) if isinstance(decoded, Mapping) else {}


def requested_model(message: Mapping[str, Any], default: str) -> str:
    """Read the effective model stored at ask creation time."""
    value = request_metadata(message).get("to_model")
    return str(value) if value else default


def requested_effort(message: Mapping[str, Any]) -> str | None:
    """Read the requested uniform effort value from an ask row."""
    value = request_metadata(message).get("effort")
    return str(value) if value else None


def unsupported_effort_note(*, lane: str, effort: str | None, reason: str) -> tuple[None, str | None]:
    """Make an unavailable provider control visible and serializable."""
    if effort:
        print(f"NOTE: {lane} cannot apply requested effort={effort}; {reason}")
        return None, reason
    return None, None


def response_provenance(
    message: Mapping[str, Any],
    *,
    actual_model: str,
    harness: str,
    effort_applied: str | None,
    effort_reason: str | None = None,
) -> tuple[str, str]:
    """Return data JSON and ``from_model`` for a reply from one ask lane."""
    req_meta = request_metadata(message)
    metadata: dict[str, Any] = {
        "from_model": actual_model,
        "model_requested": requested_model(message, actual_model),
        "effort_requested": requested_effort(message),
        "effort_applied": effort_applied,
        "harness": harness,
    }
    if req_meta.get("auto_retried") or req_meta.get("auto-retried"):
        metadata["auto_retried"] = True
    if req_meta.get("cancel_retried") or req_meta.get("cancel-retried"):
        metadata["cancel_retried"] = True
    if effort_reason:
        metadata["effort_reason"] = effort_reason
    return json.dumps(metadata, sort_keys=True), actual_model


def failed_response_provenance(
    message: Mapping[str, Any],
    *,
    bridge_model: str,
    harness: str,
) -> tuple[str, str]:
    """Stamp a terminal bridge error without inventing an applied effort."""
    return response_provenance(
        message,
        actual_model=bridge_model,
        harness=harness,
        effort_applied=None,
        effort_reason="bridge execution failed before the requested effort could be applied",
    )
