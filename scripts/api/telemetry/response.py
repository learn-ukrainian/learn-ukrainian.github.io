"""Response helpers for opt-in Monitor API context telemetry."""

from __future__ import annotations

import os
from typing import Any

from scripts.api.config import PROJECT_ROOT

from .footer import PREMIUM_THRESHOLD_TOKENS, render_footer
from .transcript_tokens import (
    TranscriptTelemetry,
    current_context_telemetry,
    session_context_telemetry,
)


def telemetry_footer_enabled() -> bool:
    """Return whether Monitor API responses should include context telemetry."""
    if os.environ.get("AGENT_NO_TELEMETRY_FOOTER") == "1":
        return False
    return os.environ.get("LEARN_UKRAINIAN_TELEMETRY_FOOTER") == "1"


def resolve_session_id(
    *,
    session_query: str | None = None,
    session_header: str | None = None,
) -> str | None:
    """Return the caller session id; query param wins over header."""
    if session_query is not None and session_query.strip():
        return session_query.strip()
    if session_header is not None and session_header.strip():
        return session_header.strip()
    return None


def session_id_from_request(request) -> str | None:
    """Extract session id from ``?session=`` (wins) or ``X-Session-Id``."""
    return resolve_session_id(
        session_query=request.query_params.get("session"),
        session_header=request.headers.get("X-Session-Id"),
    )


def current_telemetry() -> TranscriptTelemetry | None:
    """Return newest-checkout context telemetry when footer is enabled."""
    if not telemetry_footer_enabled():
        return None
    return current_context_telemetry(PROJECT_ROOT)


def telemetry_dict(telemetry: TranscriptTelemetry) -> dict[str, Any]:
    """Return the structured JSON telemetry payload."""
    tier = "premium" if telemetry.tokens > PREMIUM_THRESHOLD_TOKENS else "base"
    distance_tokens = (
        PREMIUM_THRESHOLD_TOKENS - telemetry.tokens if tier == "base" else telemetry.tokens - PREMIUM_THRESHOLD_TOKENS
    )
    return {
        "ctx": telemetry.tokens,
        "prev_ctx": telemetry.prev_tokens,
        "delta": (telemetry.tokens - telemetry.prev_tokens if telemetry.prev_tokens is not None else None),
        "tier": tier,
        "distance_tokens": distance_tokens,
        "distance_label": "to premium" if tier == "base" else "over premium",
        "turn": telemetry.turn,
        "source": "transcript-jsonl",
    }


def _newest_transcript_sidecar(telemetry: TranscriptTelemetry) -> dict[str, Any]:
    return {
        "ctx": telemetry.tokens,
        "prev_ctx": telemetry.prev_tokens,
        "turn": telemetry.turn,
        "transcript": telemetry.transcript_path.name,
        "caveat": "newest transcript in checkout — may not be the caller's session",
    }


def build_telemetry_payload(session_id: str | None = None) -> dict[str, Any] | None:
    """Build the ``_telemetry`` block for JSON responses."""
    if not telemetry_footer_enabled():
        return None

    if session_id:
        telemetry = session_context_telemetry(PROJECT_ROOT, session_id)
        if telemetry is not None:
            return {
                **telemetry_dict(telemetry),
                "caller_match": True,
                "transcript": telemetry.transcript_path.name,
            }
        return {
            "ctx": None,
            "prev_ctx": None,
            "turn": None,
            "caller_match": False,
            "reason": "session-transcript-not-found",
        }

    newest = current_context_telemetry(PROJECT_ROOT)
    payload: dict[str, Any] = {
        "ctx": None,
        "prev_ctx": None,
        "turn": None,
        "caller_match": False,
        "reason": "no-session-param",
        "hint": "pass ?session=<uuid> or X-Session-Id",
    }
    if newest is not None:
        payload["newest_transcript"] = _newest_transcript_sidecar(newest)
    return payload


def append_telemetry_footer(text: str, session_id: str | None = None) -> str:
    """Append the telemetry footer to a text response when enabled."""
    if not telemetry_footer_enabled():
        return text
    telemetry = (
        session_context_telemetry(PROJECT_ROOT, session_id) if session_id else current_context_telemetry(PROJECT_ROOT)
    )
    if telemetry is None:
        return text
    footer = render_footer(
        tokens=telemetry.tokens,
        prev_tokens=telemetry.prev_tokens,
        turn=telemetry.turn,
    )
    return text.rstrip() + f"\n\n{footer}\n"


def add_json_telemetry(
    payload: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Add top-level ``_telemetry`` to a JSON-compatible dict when enabled."""
    telemetry = build_telemetry_payload(session_id)
    if telemetry is None:
        return payload
    return {**payload, "_telemetry": telemetry}
