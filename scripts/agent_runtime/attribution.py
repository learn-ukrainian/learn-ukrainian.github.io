"""Privacy-safe attribution for agent-runtime calls.

The target agent and the transport entrypoint cannot identify the caller.  This
module resolves that caller once, records how it was resolved, and deliberately
falls back to ``unknown`` instead of guessing from the destination.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,99}$")
_ATTRIBUTION_SOURCES = frozenset({"explicit", "session_env", "unknown"})


@dataclass(frozen=True)
class InvocationAttribution:
    """Bounded caller identity suitable for persisted runtime telemetry."""

    initiator: str
    source: str
    task_id: str | None


def _safe_id(value: object) -> str | None:
    candidate = str(value or "").strip().lower()
    return candidate if _SAFE_ID_RE.fullmatch(candidate) else None


def _safe_task_id(value: object) -> str | None:
    candidate = str(value or "").strip()
    return candidate if _SAFE_ID_RE.fullmatch(candidate) else None


def resolve_invocation_attribution(
    *,
    explicit: str | None = None,
    task_id: str | None = None,
    env: Mapping[str, str] | None = None,
) -> InvocationAttribution:
    """Resolve caller identity without inferring it from the target agent."""
    environ = os.environ if env is None else env
    if explicit is not None:
        initiator = _safe_id(explicit)
        if initiator is None:
            raise ValueError(
                "initiator must be a 1-100 character identifier containing only "
                "letters, digits, dot, underscore, colon, slash, or hyphen"
            )
        return InvocationAttribution(initiator, "explicit", _safe_task_id(task_id))

    forwarded = _safe_id(environ.get("LU_RUNTIME_INITIATOR"))
    forwarded_source = str(environ.get("LU_RUNTIME_INITIATOR_SOURCE") or "").strip()
    if forwarded and forwarded_source in _ATTRIBUTION_SOURCES - {"unknown"}:
        return InvocationAttribution(forwarded, forwarded_source, _safe_task_id(task_id))

    handoff = _safe_id(environ.get("SESSION_HANDOFF_AGENT"))
    if handoff:
        return InvocationAttribution(handoff, "session_env", _safe_task_id(task_id))
    if environ.get("CODEX_THREAD_ID") or environ.get("CODEX_SESSION"):
        return InvocationAttribution("codex", "session_env", _safe_task_id(task_id))
    claude = _safe_id(environ.get("CLAUDE_AGENT_NAME"))
    if claude:
        return InvocationAttribution(claude, "session_env", _safe_task_id(task_id))
    if environ.get("GROK_AGENT") == "1":
        return InvocationAttribution("grok", "session_env", _safe_task_id(task_id))
    if environ.get("GEMINI_SESSION"):
        return InvocationAttribution("gemini", "session_env", _safe_task_id(task_id))

    return InvocationAttribution("unknown", "unknown", _safe_task_id(task_id))
