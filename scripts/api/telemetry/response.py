"""Response helpers for opt-in Monitor API context telemetry."""

from __future__ import annotations

import os
from typing import Any

from scripts.api.config import PROJECT_ROOT

from .footer import PREMIUM_THRESHOLD_TOKENS, render_footer
from .transcript_tokens import TranscriptTelemetry, current_context_telemetry


def telemetry_footer_enabled() -> bool:
    """Return whether Monitor API responses should include context telemetry."""
    if os.environ.get("AGENT_NO_TELEMETRY_FOOTER") == "1":
        return False
    return os.environ.get("LEARN_UKRAINIAN_TELEMETRY_FOOTER") == "1"


def current_telemetry() -> TranscriptTelemetry | None:
    """Return current context telemetry when the footer is enabled and parseable."""
    if not telemetry_footer_enabled():
        return None
    return current_context_telemetry(PROJECT_ROOT)


def append_telemetry_footer(text: str) -> str:
    """Append the telemetry footer to a text response when enabled."""
    telemetry = current_telemetry()
    if telemetry is None:
        return text
    footer = render_footer(
        tokens=telemetry.tokens,
        prev_tokens=telemetry.prev_tokens,
        turn=telemetry.turn,
    )
    return text.rstrip() + f"\n\n{footer}\n"


def telemetry_dict(telemetry: TranscriptTelemetry) -> dict[str, Any]:
    """Return the structured JSON telemetry payload."""
    tier = "premium" if telemetry.tokens > PREMIUM_THRESHOLD_TOKENS else "base"
    distance_tokens = (
        PREMIUM_THRESHOLD_TOKENS - telemetry.tokens
        if tier == "base"
        else telemetry.tokens - PREMIUM_THRESHOLD_TOKENS
    )
    return {
        "ctx": telemetry.tokens,
        "prev_ctx": telemetry.prev_tokens,
        "delta": (
            telemetry.tokens - telemetry.prev_tokens
            if telemetry.prev_tokens is not None
            else None
        ),
        "tier": tier,
        "distance_tokens": distance_tokens,
        "distance_label": "to premium" if tier == "base" else "over premium",
        "turn": telemetry.turn,
        "source": "transcript-jsonl",
    }


def add_json_telemetry(payload: dict[str, Any]) -> dict[str, Any]:
    """Add top-level ``_telemetry`` to a JSON-compatible dict when enabled."""
    telemetry = current_telemetry()
    if telemetry is None:
        return payload
    return {**payload, "_telemetry": telemetry_dict(telemetry)}

