from __future__ import annotations

from scripts.agent_runtime.tool_calls import TRUNCATION_SUFFIX
from scripts.audit.runtime_tool_events import map_runtime_tool_calls


def test_map_runtime_tool_calls_normalizes_agy_shape() -> None:
    events = map_runtime_tool_calls(
        [
            {
                "name": "mcp__sources__query_wikipedia",
                "arguments": {"query": "Веснянки"},
                "result": [{"type": "text", "text": "Веснянки — обрядові пісні"}],
            }
        ]
    )
    assert len(events) == 1
    event = events[0]
    assert event["tool"] == "mcp__sources__query_wikipedia"
    assert event["input"] == {"query": "Веснянки"}
    assert event["status"] == "completed"
    assert event["tool_call_id"] == "runtime-0"
    assert "обрядові" in str(event["output"])


def test_map_runtime_tool_calls_prefers_full_result_over_truncated_summary() -> None:
    long_text = "Веснянки — назва старовинних слов'янських обрядових пісень " + ("x" * 600)
    events = map_runtime_tool_calls(
        [
            {
                "name": "mcp__sources__query_wikipedia",
                "arguments": {"query": "Веснянки"},
                "output_summary": long_text[:500] + "[...truncated]",
                "result": [{"type": "text", "text": long_text}],
            }
        ]
    )
    assert len(events) == 1
    assert TRUNCATION_SUFFIX not in str(events[0]["output"])
    assert len(str(events[0]["output"])) > 500
