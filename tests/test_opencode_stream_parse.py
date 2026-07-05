"""Tests for the opencode NDJSON stream parser (#2156 tool telemetry).

``_parse_opencode_stream`` parses an ``opencode run --format json`` stream ONCE
into assistant text PLUS the deduped tool-call telemetry the tool-theatre and
grounding gates are built on. ``_parse_opencode_ndjson`` stays a thin ``.text``
wrapper so the ~8 bridge call sites keep receiving ``str``.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.ai_agent_bridge._opencode import (
    OpencodeStreamParse,
    _parse_opencode_ndjson,
    _parse_opencode_stream,
)

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "opencode" / "gemma_reviewer_run.ndjson"


def test_real_fixture_extracts_seven_tool_events() -> None:
    stdout = FIXTURE.read_text(encoding="utf-8")
    parse = _parse_opencode_stream(stdout)

    assert isinstance(parse, OpencodeStreamParse)
    # The step-1 «Веснянки» run made 7 sources-MCP calls (design table).
    assert len(parse.tool_events) == 7
    assert [event["tool"] for event in parse.tool_events] == [
        "sources_search_definitions",
        "sources_query_wikipedia",
        "sources_search_heritage",
        "sources_search_text",
        "sources_search_text",
        "sources_search_literary",
        "sources_search_definitions",
    ]


def test_each_tool_event_has_the_five_normalized_keys() -> None:
    parse = _parse_opencode_stream(FIXTURE.read_text(encoding="utf-8"))

    for event in parse.tool_events:
        assert set(event) == {"tool", "input", "status", "tool_call_id", "output"}
        assert event["status"] == "completed"
        assert isinstance(event["tool_call_id"], str) and event["tool_call_id"]
        assert isinstance(event["input"], dict)
        assert isinstance(event["output"], str)


def test_assistant_text_is_recovered_and_wrapper_matches() -> None:
    stdout = FIXTURE.read_text(encoding="utf-8")
    parse = _parse_opencode_stream(stdout)

    assert parse.text.startswith("CLAIM:")
    # Thin wrapper returns exactly the parsed text (str, not the parse object).
    assert _parse_opencode_ndjson(stdout) == parse.text
    assert isinstance(_parse_opencode_ndjson(stdout), str)


def test_dedupes_repeated_tool_call_keeping_final_status() -> None:
    # opencode can emit the same call twice as it transitions pending -> completed.
    stream = "\n".join(
        [
            json.dumps(
                {
                    "type": "tool_use",
                    "part": {
                        "type": "tool",
                        "tool": "sources_verify_word",
                        "callID": "call_1",
                        "state": {"status": "pending", "input": {"word": "гаї"}},
                    },
                }
            ),
            json.dumps(
                {
                    "type": "tool_use",
                    "part": {
                        "type": "tool",
                        "tool": "sources_verify_word",
                        "callID": "call_1",
                        "state": {"status": "completed", "input": {"word": "гаї"}},
                    },
                }
            ),
            json.dumps({"type": "text", "part": {"type": "text", "text": "done"}}),
        ]
    )
    parse = _parse_opencode_stream(stream)

    assert len(parse.tool_events) == 1
    assert parse.tool_events[0]["status"] == "completed"
    assert parse.tool_events[0]["output"] is None
    assert parse.text == "done"


def test_distinct_inputs_are_not_deduped() -> None:
    stream = "\n".join(
        json.dumps(
            {
                "type": "tool_use",
                "part": {
                    "type": "tool",
                    "tool": "sources_search_text",
                    "callID": f"call_{i}",
                    "state": {"status": "completed", "input": {"query": query}},
                },
            }
        )
        for i, query in enumerate(("веснянки", "гаївки"))
    )
    parse = _parse_opencode_stream(stream)

    assert len(parse.tool_events) == 2


def test_no_tool_events_and_raw_fallback_text() -> None:
    # Robust to format drift: never silently return empty text.
    parse = _parse_opencode_stream("not json at all\n")
    assert parse.tool_events == ()
    assert parse.text == "not json at all"


def test_garbage_and_non_tool_events_are_ignored() -> None:
    stream = "\n".join(
        [
            "",
            "garbage",
            "{bad json}",
            json.dumps({"type": "reasoning", "part": {"type": "reasoning", "text": "THINK"}}),
            json.dumps({"type": "step_start", "part": {"type": "step-start"}}),
            json.dumps({"type": "text", "part": {"type": "text", "text": "ok"}}),
        ]
    )
    parse = _parse_opencode_stream(stream)

    assert parse.text == "ok"
    assert parse.tool_events == ()


def test_dedupe_prefers_tool_call_id() -> None:
    """codex review of #4401 (Low): distinct repeated identical calls must be
    COUNTED (retry/redundancy signal for the theatre gate); pending->completed
    transitions of ONE call (same id) still collapse to the final status."""
    lines = [
        # one call transitioning pending -> completed (same id): collapses
        '{"type": "tool", "part": {"tool": "sources_verify_word", "callID": "c1", "state": {"input": {"word": "гай"}, "status": "pending"}}}',
        '{"type": "tool", "part": {"tool": "sources_verify_word", "callID": "c1", "state": {"input": {"word": "гай"}, "status": "completed"}}}',
        # a DISTINCT second call with identical input (different id): counted
        '{"type": "tool", "part": {"tool": "sources_verify_word", "callID": "c2", "state": {"input": {"word": "гай"}, "status": "completed"}}}',
        # id-less event with same input: falls back to (tool, input) key —
        # collapses into ONE id-less entry
        '{"type": "tool", "part": {"tool": "sources_verify_word", "state": {"input": {"word": "гай"}, "status": "completed"}}}',
        '{"type": "text", "part": {"text": "done"}}',
    ]
    parse = _parse_opencode_stream("\n".join(lines))
    assert parse.text == "done"
    assert len(parse.tool_events) == 3  # c1 (collapsed), c2, id-less
    c1 = next(e for e in parse.tool_events if e.get("tool_call_id") == "c1")
    assert c1["status"] == "completed"
