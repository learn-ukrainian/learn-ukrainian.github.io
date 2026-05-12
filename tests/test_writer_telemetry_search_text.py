"""Regression tests for writer telemetry capture of search_text results.

The textbook_grounding gate reads writer telemetry. A search_text call with
non-empty MCP results must preserve enough attribution and text in the emitted
event for the gate-side reader to recover textbook hits.
"""
from __future__ import annotations

from typing import Any

from scripts.build.linear_pipeline import (
    _result_items_from_call,
    emit_writer_response_telemetry,
)


def test_search_text_results_preserved_in_telemetry() -> None:
    fake_search_result = [
        {
            "source_type": "textbook",
            "author": "karaman",
            "grade": "10",
            "page": "176",
            "title": "Сторінка 176",
            "text": "Дієслова із суфіксом -ся(-сь) означають дію, спрямовану на виконавця.",
        }
    ]
    tool_calls = [
        {
            "tool": "search_text",
            "args": {"query": "дієслова -ся"},
            "result": fake_search_result,
            "section": "Дієслова на -ся",
        }
    ]
    events: list[dict[str, Any]] = []

    def sink(event_name: str, **fields: Any) -> None:
        events.append({"event": event_name, **fields})

    emit_writer_response_telemetry(
        output="(writer output)",
        writer="claude-tools",
        module="a1/my-morning",
        sections=["Дієслова на -ся"],
        tool_calls=tool_calls,
        event_sink=sink,
    )

    tool_call_events = [
        event for event in events if event["event"] == "writer_tool_call"
    ]
    assert len(tool_call_events) == 1
    event = tool_call_events[0]

    assert event["result_summary"]
    summary_or_excerpt = str(event.get("result_summary")) + str(
        event.get("result_excerpt", "")
    )
    assert "karaman" in summary_or_excerpt or "Караман" in summary_or_excerpt
    assert "176" in summary_or_excerpt

    items = list(_result_items_from_call(event))
    textbook_items = [
        item
        for item in items
        if str(item.get("source_type") or item.get("corpus") or "").startswith(
            "textbook"
        )
    ]
    assert textbook_items, "gate cannot extract textbook items from telemetry"
    assert "Дієслова із суфіксом" in str(textbook_items[0].get("text"))

    loaded_jsonl_event = dict(event)
    loaded_jsonl_event["result"] = {"text": event["result_excerpt"]}
    loaded_items = list(_result_items_from_call(loaded_jsonl_event))
    assert loaded_items[0]["source_type"] == "textbook"
