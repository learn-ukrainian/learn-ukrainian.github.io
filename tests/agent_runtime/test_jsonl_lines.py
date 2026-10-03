"""Runtime JSONL readers split records at physical LF only (#9532).

``json.dumps(ensure_ascii=False)`` and serde_json leave U+0085, U+2028 and
U+2029 unescaped inside strings, where ``str.splitlines()`` would cut one
valid record into two malformed fragments.
"""

from __future__ import annotations

import json
import logging

import pytest

from scripts.agent_runtime import acpx_pilot, codex_hook_probe
from scripts.agent_runtime.adapters.acpx import AcpxAdapter
from scripts.agent_runtime.adapters.claude import _tool_calls_from_claude_session_jsonl
from scripts.agent_runtime.jsonl import jsonl_lines
from scripts.agent_runtime.tool_calls import parse_json_events

UNICODE_LINE_BREAKS = pytest.mark.parametrize("sep", ["\u0085", " ", " "], ids=["NEL", "LS", "PS"])


def _jsonl(*records: dict) -> str:
    return "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)


@UNICODE_LINE_BREAKS
def test_jsonl_lines_splits_at_lf_only(sep):
    assert jsonl_lines(f"a{sep}b\nc\r\n\nd") == [f"a{sep}b", "c", "", "d"]
    assert jsonl_lines("a\n") == ["a", ""]
    assert jsonl_lines("") == [""]


def test_jsonl_lines_drops_only_one_trailing_cr():
    assert jsonl_lines("a\r\r\nb\rc") == ["a\r", "b\rc"]


@UNICODE_LINE_BREAKS
def test_tool_call_trace_keeps_records_with_unicode_line_breaks(sep):
    text = _jsonl(
        {"type": "user", "content": [{"text": f"hi{sep}there"}]},
        {"type": "tool", "name": "mcp__sources__verify_words", "args": {"words": [f"кіт{sep}"]}},
    )
    events = parse_json_events(text, source="test", logger=logging.getLogger(__name__))

    assert [event["type"] for event in events] == ["user", "tool"]
    assert events[1]["args"]["words"] == [f"кіт{sep}"]


@UNICODE_LINE_BREAKS
def test_acpx_stream_with_unicode_line_breaks_completes(sep):
    session = "sess-fixture-001"
    stdout = _jsonl(
        {"jsonrpc": "2.0", "id": 1, "result": {"sessionId": session}},
        {"jsonrpc": "2.0", "id": 2, "method": "session/prompt", "params": {"sessionId": session, "prompt": []}},
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "sessionId": session,
                "update": {"sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": f"a{sep}b"}},
            },
        },
        {"jsonrpc": "2.0", "id": 2, "result": {"stopReason": "end_turn"}},
    )
    result = AcpxAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None)

    assert result.ok is True and result.response == f"a{sep}b"


@UNICODE_LINE_BREAKS
def test_acpx_stream_joined_by_unicode_line_breaks_fails_closed(sep):
    records = (
        {"jsonrpc": "2.0", "id": 1, "result": {}},
        {"jsonrpc": "2.0", "id": 2, "result": {"stopReason": "end_turn"}},
    )
    stdout = sep.join(json.dumps(record) for record in records) + "\n"
    result = AcpxAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None)

    assert result.ok is False and "malformed NDJSON at line 1" in result.stderr_excerpt


@UNICODE_LINE_BREAKS
def test_claude_session_jsonl_keeps_tool_calls_with_unicode_line_breaks(tmp_path, sep):
    path = tmp_path / "session.jsonl"
    path.write_text(
        _jsonl(
            {"type": "user", "message": {"content": f"q{sep}q"}},
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": f"echo a{sep}b"}},
                    ]
                },
            },
        ),
        encoding="utf-8",
    )

    calls = _tool_calls_from_claude_session_jsonl(path)

    assert [call["name"] for call in calls] == ["Bash"]


@UNICODE_LINE_BREAKS
def test_codex_hook_probe_log_keeps_records_with_unicode_line_breaks(tmp_path, sep):
    log_path = tmp_path / "hooks.jsonl"
    log_path.write_text(_jsonl({"tool_name": "Bash", "note": f"a{sep}b"}, {"tool_name": "Read"}), encoding="utf-8")

    assert [event["tool_name"] for event in codex_hook_probe._load_events(log_path)] == ["Bash", "Read"]


@UNICODE_LINE_BREAKS
def test_acpx_pilot_finds_executed_digest_after_unicode_line_breaks(tmp_path, sep):
    path = tmp_path / f"usage_{acpx_pilot.PILOT_AGENT}-{acpx_pilot.PILOT_ENTRYPOINT}_1.jsonl"
    path.write_text(
        _jsonl(
            {"event": "other", "note": f"a{sep}b"},
            {"event": acpx_pilot.PILOT_EVENT, "idempotency_digest": "d1", "executed": True, "note": f"c{sep}d"},
        ),
        encoding="utf-8",
    )

    assert acpx_pilot._has_executed_digest(tmp_path, "d1") is True
    assert acpx_pilot._has_executed_digest(tmp_path, "d2") is False
