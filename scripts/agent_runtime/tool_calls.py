"""Tool-call telemetry parsing helpers for agent CLI traces.

The normalized records are intentionally small and PII-bearing. Arguments are
kept because downstream honesty checks need them, but raw tool output is never
stored: only a capped summary is retained.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

OUTPUT_SUMMARY_LIMIT = 500
TRUNCATION_SUFFIX = "[...truncated]"
ARGUMENT_ITEM_LIMIT = 50


def summarize_tool_output(value: Any, *, limit: int = OUTPUT_SUMMARY_LIMIT) -> str:
    """Return a bounded, human-readable summary of a tool output value."""
    if value is None:
        summary = ""
    elif isinstance(value, str):
        summary = value
    else:
        try:
            summary = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):
            summary = str(value)
    summary = " ".join(summary.split())
    if len(summary) <= limit:
        return summary
    keep = max(0, limit - len(TRUNCATION_SUFFIX))
    return f"{summary[:keep]}{TRUNCATION_SUFFIX}"


def parse_json_events(text: str, *, source: str, logger: logging.Logger) -> list[dict[str, Any]]:
    """Parse tolerant JSON/JSONL events from CLI output.

    Each line may be a JSON object, or a debug line containing one JSON object.
    Malformed candidate lines are logged and skipped so CLI version drift does
    not crash the adapter parse path.

    Gemini session traces are JSONL in current CLI versions, for example:
        {"type":"user","content":[{"text":"..."}]}
        {"type":"gemini","toolCalls":[{"name":"mcp__sources__verify_words",
         "args":{"words":["кіт"]}}]}
    """
    stripped = text.strip()
    if stripped:
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            return [parsed]
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]

    events: list[dict[str, Any]] = []
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        candidate = line
        if not candidate.startswith("{"):
            start = candidate.find("{")
            end = candidate.rfind("}")
            if start == -1:
                continue
            if end <= start:
                if _looks_like_tool_line(line):
                    logger.warning(
                        "%s tool-call trace line %d was not parseable JSON: incomplete object",
                        source,
                        lineno,
                    )
                continue
            candidate = candidate[start : end + 1]
        try:
            event = json.loads(candidate)
        except json.JSONDecodeError as exc:
            if _looks_like_tool_line(line):
                logger.warning(
                    "%s tool-call trace line %d was not parseable JSON: %s",
                    source,
                    lineno,
                    exc,
                )
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def normalize_tool_calls(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Extract normalized tool-call records from provider-specific events."""
    calls: list[dict[str, Any]] = []
    # Tool-result correlation is best-effort and scoped to one parse_response
    # call. Provider ids are not assumed globally unique across invocations.
    by_id: dict[str, dict[str, Any]] = {}

    for event in events:
        for payload in _candidate_payloads(event):
            if not _is_tool_use_payload(payload):
                continue
            name = _tool_name(payload)
            if not name:
                continue
            output = _tool_output(payload)
            call = {
                "name": name,
                "arguments": _tool_arguments(payload),
                "output_summary": summarize_tool_output(output),
                "timestamp": _timestamp(payload, event),
            }
            if output is not None:
                call["result"] = output
            calls.append(call)
            # Guard note: codex's dual-id (id vs call_id) events need id-set registration.
            for cid in _tool_call_ids(payload):
                by_id[cid] = call

        result_payloads = [payload for payload in _candidate_payloads(event) if _is_tool_result_payload(payload)]
        for payload in result_payloads:
            call_id = _tool_result_id(payload)
            if call_id and call_id in by_id:
                output = _tool_output(payload)
                by_id[call_id]["output_summary"] = summarize_tool_output(output)
                if output is not None:
                    by_id[call_id]["result"] = output

    return calls


def _looks_like_tool_line(line: str) -> bool:
    return bool(re.search(r"tool[_ -]?(call|use|result)|function[_ -]?call", line, re.I))


def _candidate_payloads(event: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    payloads: list[Mapping[str, Any]] = []
    seen: set[int] = set()

    def visit(payload: Mapping[str, Any]) -> None:
        marker = id(payload)
        if marker in seen:
            return
        seen.add(marker)
        payloads.append(payload)
        for key in (
            "payload",
            "message",
            "messages",
            "data",
            "item",
            "items",
            "tool_call",
            "tool_calls",
            "toolCall",
            "toolCalls",
            "functionCall",
            "parts",
        ):
            nested = payload.get(key)
            if isinstance(nested, Mapping):
                visit(nested)
            elif isinstance(nested, list):
                for item in nested:
                    if isinstance(item, Mapping):
                        visit(item)
        content = payload.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, Mapping):
                    visit(item)
        elif isinstance(content, Mapping):
            visit(content)

    visit(event)
    return payloads


def _payload_type(payload: Mapping[str, Any]) -> str:
    raw = payload.get("type") or payload.get("event") or payload.get("kind") or ""
    return str(raw).strip().lower()


def _is_tool_use_payload(payload: Mapping[str, Any]) -> bool:
    payload_type = _payload_type(payload)
    return (
        payload_type
        in {
            "tool_use",
            "tool_call",
            "function_call",
            "mcp_tool_call",
            "response.function_call_arguments.done",
        }
        or "functionCall" in payload
        or "toolCall" in payload
        or (
            payload_type == "function"
            and isinstance(payload.get("function"), Mapping)
            and bool(_tool_name(payload))
        )
        or (
            bool(_tool_name(payload))
            and any(key in payload for key in ("arguments", "args", "input", "parameters"))
            and "result" not in payload_type
        )
    )


def _is_tool_result_payload(payload: Mapping[str, Any]) -> bool:
    # Codex CLI emits ``function_call_output`` as the result-event type with
    # ``call_id`` as the correlation key (not ``tool_call_id``/``tool_use_id``).
    # Without including both here, codex rollouts parse the function_call
    # but never correlate the output back, leaving ``writer_tool_calls.json``
    # entries with empty ``result`` / ``output_summary`` and breaking the
    # ``textbook_grounding`` gate (textbook_result_hits=0 even when the
    # writer's search_text/get_chunk_context calls returned grounded chunks).
    # Empirical reference: rollout-2026-05-22T22-58-38 for the codex-tools
    # a1/my-morning build at codex-cli 0.133.0 — 38 valid mcp__sources__*
    # calls fired with full results in the rollout, all dropped on the floor
    # by the result-correlation pass.
    payload_type = _payload_type(payload)
    return payload_type in {
        "tool_result",
        "tool_output",
        "function_result",
        "function_call_output",
        "mcp_tool_call_end",
    } or (
        any(key in payload for key in ("tool_use_id", "tool_call_id", "call_id"))
        and any(key in payload for key in ("content", "output", "result"))
    )


def _tool_name(payload: Mapping[str, Any]) -> str:
    function = payload.get("function")
    if isinstance(function, Mapping) and isinstance(function.get("name"), str):
        return function["name"]
    # Codex CLI 0.132.0+ emits `function_call` payloads for MCP calls
    # with the canonical prefix split off into a separate `namespace`
    # field — e.g. ``{"type": "function_call", "name": "search_text",
    # "namespace": "mcp__sources__", "arguments": "..."}`` — and a
    # companion `mcp_tool_call_end` event with the full invocation +
    # response. Without concatenating namespace+name the writer-trace-
    # isolation gate sees bare ``search_text`` (no prefix) and tags it
    # wrong_tool_family. Empirical reference: rollout-2026-05-21T01-37-06
    # for the night a1/my-morning codex-tools build at codex-cli 0.132.0.
    #
    # Codex 0.135.0 CHANGED the namespace format: it now drops the trailing
    # ``__`` and emits ``"namespace": "mcp__sources"`` (no separator). Naive
    # concatenation then yields ``mcp__sourcessearch_text`` — still missing the
    # ``__`` join — so the same wrong_tool_family / mcp_tools_never_invoked
    # HARD-fail returns for EVERY codex build under 0.135.0. Normalize to
    # exactly one ``__`` between namespace and name so both CLI versions
    # produce the canonical ``mcp__sources__<tool>``. Empirical reference:
    # rollout-2026-05-29T09-59-48 a1/my-morning build at codex-cli 0.135.0.
    namespace = payload.get("namespace")
    name = payload.get("name")
    if isinstance(namespace, str) and isinstance(name, str) and namespace and name:
        separator = "" if namespace.endswith("__") else "__"
        return f"{namespace}{separator}{name}"
    for key in ("name", "tool_name", "toolName", "function_name", "server_tool_name"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _tool_arguments(payload: Mapping[str, Any]) -> dict[str, Any]:
    function = payload.get("function")
    if isinstance(function, Mapping) and "arguments" in function:
        return _coerce_arguments(function.get("arguments"))
    for key in ("arguments", "args", "input", "parameters"):
        if key in payload:
            return _coerce_arguments(payload.get(key))
    return {}


def _coerce_arguments(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        sanitized = _sanitize_argument_value(value)
        return sanitized if isinstance(sanitized, dict) else {}
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {"_raw": summarize_tool_output(value)}
        if isinstance(parsed, Mapping):
            sanitized = _sanitize_argument_value(parsed)
            return sanitized if isinstance(sanitized, dict) else {}
        return {"_value": _sanitize_argument_value(parsed)}
    return {}


def _tool_output(payload: Mapping[str, Any]) -> Any:
    for key in ("output", "result", "content", "observation"):
        if key in payload:
            return _coerce_tool_output(payload.get(key))
    return None


def _coerce_tool_output(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    parsed = _parse_codex_output_envelope(value)
    return parsed if parsed is not None else value


def _parse_codex_output_envelope(value: str) -> Any | None:
    """Decode Codex CLI ``function_call_output`` wrappers when possible."""
    candidates = [value.strip()]
    marker = "\nOutput:\n"
    if marker in value:
        candidates.insert(0, value.split(marker, 1)[1].strip())
    for candidate in candidates:
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, (dict, list)):
            return parsed
    return None


def _sanitize_argument_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        items = list(value.items())
        sanitized: dict[str, Any] = {}
        for key, nested in items[:ARGUMENT_ITEM_LIMIT]:
            sanitized[str(key)] = _sanitize_argument_value(nested)
        if len(items) > ARGUMENT_ITEM_LIMIT:
            sanitized["_truncated_keys"] = len(items) - ARGUMENT_ITEM_LIMIT
        return sanitized
    if isinstance(value, list | tuple | set):
        items = list(value)
        sanitized_items = [_sanitize_argument_value(item) for item in items[:ARGUMENT_ITEM_LIMIT]]
        if len(items) > ARGUMENT_ITEM_LIMIT:
            sanitized_items.append({"_truncated_items": len(items) - ARGUMENT_ITEM_LIMIT})
        return sanitized_items
    if isinstance(value, str):
        return summarize_tool_output(value)
    if value is None or isinstance(value, bool | int | float):
        return value
    return summarize_tool_output(value)


def _tool_call_id(payload: Mapping[str, Any]) -> str:
    for key in ("id", "tool_call_id", "toolUseId", "call_id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _tool_call_ids(payload: Mapping[str, Any]) -> list[str]:
    # Guard note: codex's dual-id (id vs call_id) events need id-set registration
    ids: list[str] = []
    for key in ("id", "tool_call_id", "toolUseId", "call_id"):
        value = payload.get(key)
        if isinstance(value, str) and value and value not in ids:
            ids.append(value)
    return ids


def _tool_result_id(payload: Mapping[str, Any]) -> str:
    for key in ("tool_use_id", "tool_call_id", "toolUseId", "call_id", "id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _timestamp(payload: Mapping[str, Any], event: Mapping[str, Any]) -> str:
    for source in (payload, event):
        for key in ("timestamp", "ts", "time", "created_at"):
            value = source.get(key)
            if isinstance(value, str) and value:
                return value
    return datetime.now(UTC).isoformat()
