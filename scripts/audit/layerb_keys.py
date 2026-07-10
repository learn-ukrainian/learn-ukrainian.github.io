"""Pure identity helpers shared by offline Layer B tooling.

This module is deliberately stdlib-only.  Label handoff tools use these
helpers without importing the shadow runner, which owns reviewer dispatch and
other runtime-facing concerns.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import Path
from typing import Any

EVENT_OUTPUT_IDENTITY_VERSION = "qg-event-output.v1"
_STABLE_SOURCE_FIELDS = ("document_id", "source_id", "url", "revision", "section_id", "item_id")


def _canonical_json(value: Any) -> str:
    """Serialize identity material in the established canonical form."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_text(value: str) -> str:
    """Return the lowercase SHA-256 of UTF-8 text."""
    return sha256(value.encode("utf-8")).hexdigest()


def _event_output_text(event: Mapping[str, Any]) -> str | None:
    """Extract output text using Layer A's established deterministic form."""
    output = event.get("output")
    if output is None:
        return None
    if isinstance(output, str):
        return output
    if isinstance(output, (Mapping, list)):
        return json.dumps(output, ensure_ascii=False, default=str)
    return str(output)


def _canonical_tool_name(name: Any) -> str:
    """Canonicalize tool identity without widening malformed names."""
    canonical = str(name or "").strip()
    if not canonical:
        return ""
    for prefix in ("mcp__", "mcp_"):
        if canonical.startswith(prefix):
            canonical = canonical[len(prefix) :]
            break
    if "." in canonical:
        server, _separator, tool = canonical.partition(".")
        if server and tool:
            canonical = tool
    else:
        for prefix in ("sources__", "sources_"):
            if canonical.startswith(prefix):
                canonical = canonical[len(prefix) :]
                break
    return canonical.casefold()


def _capture_complete(event: Mapping[str, Any]) -> bool:
    """Return explicit capture completeness; unknown is treated as complete."""
    return (
        not any(event.get(key) is True for key in ("output_truncated", "truncated", "capture_truncated"))
        and event.get("output_capture_complete") is not False
    )


def _stable_source_material(event: Mapping[str, Any]) -> dict[str, Any]:
    """Extract only declared stable source fields; never infer IDs from prose."""
    material: dict[str, Any] = {}
    for container in (event, event.get("input")):
        if isinstance(container, Mapping):
            for key in _STABLE_SOURCE_FIELDS:
                value = container.get(key)
                if value not in (None, ""):
                    material[key] = value
    return material


def _stable_grounding_key(path: Path, fact_index: int, fact_check: Mapping[str, Any]) -> str:
    """Return the persistent fact-check identity used by the shadow runner."""
    explicit = fact_check.get("fact_check_id")
    if isinstance(explicit, str) and explicit.strip():
        suffix = explicit.strip()
    else:
        suffix = _sha256_text(_canonical_json(fact_check))[:16]
    return f"{path.name}#fact_checks[{fact_index}]::{suffix}"


def _build_event_index(events: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    """Map materializer-derived event IDs to captured raw output safely."""
    index: dict[str, str] = {}
    for event in events:
        raw = _event_output_text(event)
        if raw is None:
            continue
        material = {
            "version": EVENT_OUTPUT_IDENTITY_VERSION,
            "tool": _canonical_tool_name(event.get("tool")),
            "query": _canonical_json(event.get("input") if "input" in event else {}),
            "status_envelope": {
                "status": event.get("status"),
                "error": event.get("error"),
                "errors": event.get("errors"),
            },
            "stable_source": _stable_source_material(event),
            "raw_output_sha256": _sha256_text(raw),
            "output_capture_complete": _capture_complete(event),
        }
        event_id = _sha256_text(_canonical_json(material))
        previous = index.get(event_id)
        if previous is not None and previous != raw:
            # An identity collision with different bytes is unsafe to use.
            index.pop(event_id, None)
            continue
        index[event_id] = raw
    return index
