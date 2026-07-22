"""Canonical seat-id normalization for agent lanes.

The durable native-CLI seat is ``grok``. Historical records, trailers, and
dispatch flags may still say ``grok-build`` (the dead xAI model name that
was reused as a lane id). That string is a **permanent alias**, never a
rewrite target for attestations or past-run evidence.

The Hermes/OpenRouter Grok path is demoted to ``grok-hermes`` so the clean
name ``grok`` can mean the preferred native CLI seat.

Dual-READ / prefer-WRITE:
- **Normalize** on every live lookup (budget, registry, inbox, tool_config).
- **Write** the canonical seat id (``grok``) for new messages and telemetry.
- **Never rewrite** frozen history strings in attestations, audit fixtures,
  or decision docs describing past runs.
"""

from __future__ import annotations

# Permanent backward-compat aliases: historical lane id → canonical seat.
# Keep forever: old X-Agent trailers, inbox rows, budget usage records, and
# ``--agent grok-build`` dispatches must keep resolving.
SEAT_ALIASES: dict[str, str] = {
    "grok-build": "grok",
}

# Canonical native CLI seat (preferred Grok transport).
NATIVE_GROK_SEAT = "grok"

# Demoted Hermes/OpenRouter Grok path (disfavored for judges; still live).
HERMES_GROK_SEAT = "grok-hermes"

# Historical alias that must remain dual-readable with the native seat.
LEGACY_NATIVE_GROK_ALIAS = "grok-build"


def normalize_seat(name: str | None) -> str | None:
    """Return the canonical seat id for a caller-facing lane/agent name.

    Unknown names pass through unchanged (callers validate against registries).
    Empty / None stays None.
    """
    if name is None:
        return None
    stripped = str(name).strip()
    if not stripped:
        return None
    key = stripped.lower()
    return SEAT_ALIASES.get(key, key)


def seat_read_aliases(name: str | None) -> tuple[str, ...]:
    """Ids that should match when dual-reading historical + canonical rows.

    For the native Grok seat this is ``("grok", "grok-build")`` so old inbox
    and usage rows addressed to ``grok-build`` are not orphaned after the
    rename. For other seats this is a single-element tuple of the canonical id.
    """
    canonical = normalize_seat(name)
    if canonical is None:
        return ()
    if canonical == NATIVE_GROK_SEAT:
        return (NATIVE_GROK_SEAT, LEGACY_NATIVE_GROK_ALIAS)
    return (canonical,)


def is_native_grok_seat(name: str | None) -> bool:
    """True for the native grok CLI seat (canonical or permanent alias)."""
    return normalize_seat(name) == NATIVE_GROK_SEAT


def is_hermes_grok_seat(name: str | None) -> bool:
    """True for the demoted Hermes-backed Grok path."""
    return normalize_seat(name) == HERMES_GROK_SEAT


def tools_writer_runtime_agent(writer_or_reviewer: str) -> str:
    """Map a V7 ``*-tools`` label to a registry seat without ``split('-')[0]``.

    ``grok-tools`` must stay on the Hermes content path (``grok-hermes``).
    After the seat swap, ``"grok-tools".split("-", 1)[0]`` would wrongly
    resolve to the native ``grok`` seat.
    """
    label = writer_or_reviewer.strip().lower()
    explicit = {
        "claude-tools": "claude",
        "gemini-tools": "gemini",
        "codex-tools": "codex",
        "cursor-tools": "cursor",
        "agy-tools": "agy",
        "deepseek-tools": "deepseek",
        "qwen-tools": "glm",
        "grok-tools": NATIVE_GROK_SEAT,
    }
    if label in explicit:
        return explicit[label]
    if label.endswith("-tools"):
        return label.removesuffix("-tools")
    return normalize_seat(label) or label
