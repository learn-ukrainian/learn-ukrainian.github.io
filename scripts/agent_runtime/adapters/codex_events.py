"""Typed outcome of one ``codex exec --json`` invocation (#9532).

``codex exec --json`` prints one JSON event per line on stdout (codex-cli
0.159.3 ``exec/src/exec_events.rs``). Before serializing, exec forwards only
the notifications whose thread and turn ids are this invocation's own
(``should_process_notification`` in ``exec/src/lib.rs``), so this stream is the
only evidence that belongs to this call. The lifecycle is ``thread.started``,
``turn.started``, ``item.*`` events, then exactly one terminal
``turn.completed`` or ``turn.failed``; an interrupted turn emits no terminal.

Only top-level envelopes classify an outcome: ``turn.failed.error.message`` is
the terminal provider failure and a top-level ``error`` is a notice (one
followed by ``turn.completed`` was retried). Agent text, reasoning, command
output, MCP results and ``item.type="error"`` warnings live inside item fields
and are never searched. The emitter keeps only the message, not the provider's
error class, so recognisers match the provider's own message wording and
anything unfamiliar or conflicting stays ``provider_error``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

from ..jsonl import jsonl_lines
from ..tool_calls import tool_call_record

_SESSION_ID_VALUE_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# Provider messages as codex-cli 0.159.3 renders them (protocol/src/error.rs,
# codex-api/src/sse/responses.rs). Each pattern is anchored at the start of
# the full message; the emitter may append " (<details>)".
_APOSTROPHE = "['’]"
_PROVIDER_MESSAGE_PATTERNS: dict[str, tuple[str, ...]] = {
    "rate_limited": (
        rf"You{_APOSTROPHE}ve hit your usage limit\b",
        r"Quota exceeded\. Check your plan and billing details\.",
        r"Your workspace is out of credits\.",
        r"You hit your spend cap\b",
        r"rate limit exceeded: ",
        r"exceeded retry limit, last status: 429\b",
        r"unexpected status 429\b",
    ),
    "provider_overloaded": (
        r"Selected model is at capacity\.",
        r"Flex capacity unavailable\.",
        rf"We{_APOSTROPHE}re currently experiencing high demand\b",
        r"exceeded retry limit, last status: 5(?:00|02|03|04|29)\b",
        r"unexpected status 5(?:00|02|03|04|29)\b",
    ),
    "provider_auth": (r"unexpected status 401\b",),
    "provider_policy_refusal": (
        r"This (?:request|content) (?:was|has been) flagged for (?:possible )?(?:cyber|biological\b|bio\b)",
        r"This request violated the misalignment policy\.",
        r"This request was blocked due to a misalignment policy violation\.",
    ),
}
_PROVIDER_MESSAGE_RES = {
    code: tuple(re.compile(pattern) for pattern in patterns) for code, patterns in _PROVIDER_MESSAGE_PATTERNS.items()
}

INCOMPLETE_FAILURE_CODE = "provider_stream_incomplete"


def classify_provider_message(message: str) -> str:
    """Return the failure code one provider failure message names.

    The full message is matched before any display truncation. A message that
    matches no recogniser, or more than one, is ``provider_error``.
    """
    text = message.lstrip()
    matched = {code for code, patterns in _PROVIDER_MESSAGE_RES.items() if any(p.match(text) for p in patterns)}
    return matched.pop() if len(matched) == 1 else "provider_error"


@dataclass(frozen=True)
class CodexExecStream:
    """The typed top-level events of one ``codex exec --json`` stdout."""

    thread_ids: tuple[str, ...] = ()
    turns_started: int = 0
    # ("completed" | "failed", the turn.failed message or None).
    terminals: tuple[tuple[str, str | None], ...] = ()
    # Messages of top-level ``error`` notices, in order.
    notices: tuple[str, ...] = ()
    # ``turn.completed.usage``: the thread's cumulative totals.
    usage: Mapping[str, Any] | None = None
    completed_items: tuple[Mapping[str, Any], ...] = ()
    malformed_lines: int = 0
    events_after_terminal: int = 0

    @property
    def last_event_is_completion(self) -> bool:
        return bool(self.terminals) and self.terminals[-1][0] == "completed" and not self.events_after_terminal


def parse_exec_stream(stdout: str) -> CodexExecStream:
    """Parse ``codex exec --json`` stdout; every non-blank LF-delimited line must be one event."""
    thread_ids: list[str] = []
    terminals: list[tuple[str, str | None]] = []
    notices: list[str] = []
    items: list[Mapping[str, Any]] = []
    usage: Mapping[str, Any] | None = None
    turns_started = malformed = after_terminal = 0
    for line in jsonl_lines(stdout or ""):
        # Only JSON whitespace makes a line blank; json.loads rejects the rest.
        if not line.strip(" \t\r"):
            continue
        try:
            event = json.loads(line)
        except (ValueError, RecursionError):
            malformed += 1
            continue
        event_type = event.get("type") if isinstance(event, dict) else None
        if not isinstance(event_type, str):
            malformed += 1
            continue
        if terminals:
            after_terminal += 1
        if event_type == "thread.started":
            thread_id = event.get("thread_id")
            thread_ids.append(thread_id if isinstance(thread_id, str) else "")
        elif event_type == "turn.started":
            turns_started += 1
        elif event_type == "turn.completed":
            terminals.append(("completed", None))
            raw_usage = event.get("usage")
            usage = raw_usage if isinstance(raw_usage, dict) else None
        elif event_type == "turn.failed":
            error = event.get("error")
            message = error.get("message") if isinstance(error, dict) else None
            terminals.append(("failed", message if isinstance(message, str) else None))
        elif event_type == "error":
            message = event.get("message")
            notices.append(message if isinstance(message, str) else "")
        elif event_type == "item.completed":
            item = event.get("item")
            if isinstance(item, dict):
                items.append(item)
    return CodexExecStream(
        thread_ids=tuple(thread_ids),
        turns_started=turns_started,
        terminals=tuple(terminals),
        notices=tuple(notices),
        usage=usage,
        completed_items=tuple(items),
        malformed_lines=malformed,
        events_after_terminal=after_terminal,
    )


@dataclass(frozen=True)
class CodexOutcome:
    """What the stream proves about this invocation's single turn."""

    state: Literal["completed", "failed", "incomplete"]
    # None when completed; the classified code when failed;
    # ``provider_stream_incomplete`` when the stream proves neither.
    failure_code: str | None
    # The full ``turn.failed`` message; empty unless failed.
    provider_message: str = ""
    # Body-free reason the stream is incomplete; empty otherwise.
    detail: str = ""
    # ``thread.started.thread_id`` once the stream binds it to this invocation.
    thread_id: str | None = None


def codex_outcome(stream: CodexExecStream, *, resumed_session_id: str | None) -> CodexOutcome:
    """Decide the turn outcome from the stream alone.

    A resumed invocation must report the thread it resumed. Anything that
    could let another thread or turn supply evidence, and any missing or
    duplicated terminal, is incomplete rather than guessed.
    """

    def incomplete(detail: str, thread_id: str | None = None) -> CodexOutcome:
        return CodexOutcome("incomplete", INCOMPLETE_FAILURE_CODE, detail=detail, thread_id=thread_id)

    if stream.malformed_lines:
        return incomplete("malformed_event")
    if not stream.thread_ids:
        return incomplete("no_thread_started")
    if len(stream.thread_ids) != 1:
        return incomplete("multiple_thread_started")
    thread_id = stream.thread_ids[0]
    if not _SESSION_ID_VALUE_RE.fullmatch(thread_id):
        return incomplete("invalid_thread_id")
    if resumed_session_id is not None and thread_id != resumed_session_id:
        return incomplete("resumed_thread_mismatch")
    if stream.turns_started > 1:
        return incomplete("multiple_turns", thread_id)
    if not stream.terminals:
        return incomplete("no_terminal_event", thread_id)
    if len(stream.terminals) > 1 or stream.events_after_terminal:
        return incomplete("events_after_terminal", thread_id)
    kind, message = stream.terminals[0]
    if kind == "completed":
        return CodexOutcome("completed", None, thread_id=thread_id)
    message = message or ""
    return CodexOutcome("failed", classify_provider_message(message), provider_message=message, thread_id=thread_id)


def fresh_invocation_tokens(stream: CodexExecStream, *, resumed: bool) -> int | None:
    """Return input plus output tokens when they are this invocation's alone.

    ``turn.completed.usage`` carries the thread's cumulative totals, so it is
    per-invocation usage only on a fresh thread. Exec reports zeros when it
    saw no usage update; zero is no evidence.
    """
    if resumed or stream.usage is None or not stream.last_event_is_completion:
        return None
    values = [stream.usage.get(key) for key in ("input_tokens", "output_tokens")]
    if not all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in values):
        return None
    total = sum(values)
    return total or None


def _mcp_output(item: Mapping[str, Any]) -> Any:
    error = item.get("error")
    if isinstance(error, dict) and isinstance(error.get("message"), str):
        return error["message"]
    result = item.get("result")
    if not isinstance(result, dict):
        return None
    content = result.get("content")
    if isinstance(content, list) and content:
        return content
    return result.get("structured_content")


def tool_calls_from_items(items: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Map completed exec items to the runtime's normalized tool-call records."""
    calls: list[dict[str, Any]] = []
    for item in items:
        item_type = item.get("type")
        if item_type == "mcp_tool_call":
            server, tool = item.get("server"), item.get("tool")
            if not (isinstance(server, str) and server and isinstance(tool, str) and tool):
                continue
            record = tool_call_record(
                name=f"mcp__{server}__{tool}", arguments=item.get("arguments"), output=_mcp_output(item)
            )
            result = item.get("result")
            # Internal evidence preserves the complete MCP envelope; legacy
            # consumers continue to receive _mcp_output in result.
            record["mcp_result"] = result
            record["paired"] = isinstance(result, Mapping)
            record["is_error"] = bool(
                item.get("status") != "completed" or item.get("error")
                or (isinstance(result, Mapping) and result.get("isError", False))
            )
        elif item_type == "command_execution":
            record = tool_call_record(
                name="exec_command", arguments={"cmd": item.get("command")}, output=item.get("aggregated_output")
            )
        elif item_type == "file_change":
            record = tool_call_record(name="apply_patch", arguments={"changes": item.get("changes")}, output=None)
        elif item_type == "web_search":
            record = tool_call_record(name="web_search", arguments={"query": item.get("query")}, output=None)
        elif item_type == "collab_tool_call":
            tool = item.get("tool")
            if not isinstance(tool, str) or not tool:
                continue
            record = tool_call_record(
                name=tool, arguments={"receiver_thread_ids": item.get("receiver_thread_ids")}, output=None
            )
        elif item_type == "todo_list":
            record = tool_call_record(name="update_plan", arguments={"items": item.get("items")}, output=None)
        else:
            continue
        status = item.get("status")
        if isinstance(status, str) and status:
            record["status"] = status
        calls.append(record)
    return calls


def mcp_tool_event(line: str) -> tuple[str, str] | None:
    """Return ``(server, tool)`` when one stdout line is a typed MCP call event."""
    try:
        event = json.loads(line)
    except (ValueError, RecursionError):
        return None
    if not isinstance(event, dict) or event.get("type") not in {"item.started", "item.completed"}:
        return None
    item = event.get("item")
    if not isinstance(item, dict) or item.get("type") != "mcp_tool_call":
        return None
    server, tool = item.get("server"), item.get("tool")
    if isinstance(server, str) and server and isinstance(tool, str) and tool:
        return server, tool
    return None
