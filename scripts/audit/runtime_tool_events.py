"""Map agent-runtime ``tool_calls`` telemetry to bakeoff grounding gate events.

Opencode bakeoff cells already emit ``{tool, input, status, tool_call_id, output}``.
Subscription-runtime lanes (agy/claude/codex) surface provider-specific
``tool_calls`` on :class:`agent_runtime.result.RunResult`; this module normalizes
them into the gate-facing event shape so ``enforce_grounding_against_tool_events``
can run unchanged.
"""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from scripts.agent_runtime.tool_calls import OUTPUT_SUMMARY_LIMIT, TRUNCATION_SUFFIX, summarize_tool_output


def _text_from_result_value(result: Any) -> str | None:
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        parts: list[str] = []
        for item in result:
            if isinstance(item, Mapping):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text)
        if parts:
            return "\n".join(parts)
    if isinstance(result, Mapping):
        for key in ("text", "content", "output"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return json.dumps(result, ensure_ascii=False, default=str)
    if result is not None:
        return summarize_tool_output(result, limit=50_000)
    return None


def _coerce_output_text(call: Mapping[str, Any]) -> str | None:
    # Gate admissibility needs FULL captured tool output. Runtime telemetry may
    # also carry a 500-char output_summary — never prefer that over result.
    from_result = _text_from_result_value(call.get("result"))
    if from_result and from_result.strip():
        return from_result
    value = call.get("output")
    if (
        isinstance(value, str)
        and value.strip()
        and (TRUNCATION_SUFFIX not in value or len(value) >= OUTPUT_SUMMARY_LIMIT)
    ):
        return value
    summary = call.get("output_summary")
    if isinstance(summary, str) and summary.strip():
        return summary
    return None


def _tool_name(call: Mapping[str, Any]) -> str:
    for key in ("tool", "name"):
        value = call.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _tool_input(call: Mapping[str, Any]) -> Any:
    for key in ("input", "arguments", "args"):
        if key in call:
            return call.get(key)
    return {}


def _tool_status(call: Mapping[str, Any]) -> str | None:
    value = call.get("status")
    return value if isinstance(value, str) and value.strip() else "completed"


def _tool_call_id(call: Mapping[str, Any], *, index: int) -> str:
    for key in ("tool_call_id", "id", "call_id"):
        value = call.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"runtime-{index}"


def map_runtime_tool_calls(tool_calls: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Normalize runtime ``tool_calls`` into opencode-shaped gate events."""
    events: list[dict[str, Any]] = []
    for index, call in enumerate(tool_calls):
        if not isinstance(call, Mapping):
            continue
        tool = _tool_name(call)
        if not tool:
            continue
        events.append(
            {
                "tool": tool,
                "input": _tool_input(call),
                "status": _tool_status(call),
                "tool_call_id": _tool_call_id(call, index=index),
                "output": _coerce_output_text(call),
            }
        )
    return tuple(events)
