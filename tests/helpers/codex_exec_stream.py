"""Synthetic ``codex exec --json`` stdout in the codex-cli 0.159.3 event schema (#9532).

Shapes follow ``codex-rs/exec/src/exec_events.rs`` at ``rust-v0.159.3``: one
JSON object per line, ``thread.started`` first, then ``turn.started``, item
events, and one terminal ``turn.completed`` (with cumulative ``usage``) or
``turn.failed`` (with ``error.message``). A top-level ``error`` is a notice.
"""

from __future__ import annotations

import json
from typing import Any

THREAD_ID = "01a0f98a-3b91-7230-92a5-83f18c0a4f40"
OTHER_THREAD_ID = "01a0f98a-3b91-7230-92a5-83f18c0a4f41"
USAGE = {
    "input_tokens": 1200,
    "cached_input_tokens": 300,
    "cache_write_input_tokens": 0,
    "output_tokens": 80,
    "reasoning_output_tokens": 20,
}


def thread_started(thread_id: str = THREAD_ID) -> dict[str, Any]:
    return {"type": "thread.started", "thread_id": thread_id}


def turn_started() -> dict[str, Any]:
    return {"type": "turn.started"}


def turn_completed(usage: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"type": "turn.completed", "usage": dict(USAGE if usage is None else usage)}


def turn_failed(message: str) -> dict[str, Any]:
    return {"type": "turn.failed", "error": {"message": message}}


def error_notice(message: str) -> dict[str, Any]:
    return {"type": "error", "message": message}


def item_completed(item_id: str, item_type: str, **fields: Any) -> dict[str, Any]:
    return {"type": "item.completed", "item": {"id": item_id, "type": item_type, **fields}}


def item_started(item_id: str, item_type: str, **fields: Any) -> dict[str, Any]:
    return {"type": "item.started", "item": {"id": item_id, "type": item_type, **fields}}


def agent_message(text: str, item_id: str = "item_9") -> dict[str, Any]:
    return item_completed(item_id, "agent_message", text=text)


def reasoning(text: str, item_id: str = "item_0") -> dict[str, Any]:
    return item_completed(item_id, "reasoning", text=text)


def command(command: str, output: str, *, exit_code: int = 0, item_id: str = "item_1") -> dict[str, Any]:
    return item_completed(
        item_id,
        "command_execution",
        command=command,
        aggregated_output=output,
        exit_code=exit_code,
        status="completed" if exit_code == 0 else "failed",
    )


def mcp_call(
    server: str,
    tool: str,
    arguments: dict[str, Any],
    *,
    text: str | None = None,
    error: str | None = None,
    item_id: str = "item_2",
) -> dict[str, Any]:
    result = None if text is None else {"content": [{"type": "text", "text": text}], "structured_content": None}
    return item_completed(
        item_id,
        "mcp_tool_call",
        server=server,
        tool=tool,
        arguments=arguments,
        result=result,
        error=None if error is None else {"message": error},
        status="failed" if error is not None else "completed",
    )


def warning_item(message: str, item_id: str = "item_3") -> dict[str, Any]:
    return item_completed(item_id, "error", message=message)


def jsonl(*events: dict[str, Any]) -> str:
    return "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events)


def completed_stream(*items: dict[str, Any], thread_id: str = THREAD_ID, usage: dict[str, Any] | None = None) -> str:
    return jsonl(thread_started(thread_id), turn_started(), *items, turn_completed(usage))


def failed_stream(message: str, *items: dict[str, Any], thread_id: str = THREAD_ID) -> str:
    return jsonl(thread_started(thread_id), turn_started(), *items, turn_failed(message))
