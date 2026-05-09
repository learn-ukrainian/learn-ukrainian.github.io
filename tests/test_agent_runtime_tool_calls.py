from __future__ import annotations

import logging

from scripts.agent_runtime.tool_calls import normalize_tool_calls, parse_json_events


def test_parse_json_events_accepts_pretty_printed_json_object() -> None:
    events = parse_json_events(
        """
        {
          "messages": [
            {"type": "gemini", "toolCalls": [{"name": "read_file", "args": {}}]}
          ]
        }
        """,
        source="fixture",
        logger=logging.getLogger(__name__),
    )

    assert len(events) == 1
    assert events[0]["messages"][0]["toolCalls"][0]["name"] == "read_file"


def test_normalize_tool_calls_extracts_gemini_toolcalls_shape() -> None:
    events = [
        {
            "type": "gemini",
            "toolCalls": [
                {
                    "id": "mcp__sources__verify_words_fixture",
                    "name": "mcp__sources__verify_words",
                    "args": {"words": ["кіт"]},
                    "timestamp": "2026-05-09T19:20:01Z",
                    "result": [
                        {
                            "functionResponse": {
                                "name": "mcp__sources__verify_words",
                                "response": {"output": "ok"},
                            }
                        }
                    ],
                }
            ],
        }
    ]

    calls = normalize_tool_calls(events)

    assert calls[0]["name"] == "mcp__sources__verify_words"
    assert calls[0]["arguments"] == {"words": ["кіт"]}
    assert calls[0]["timestamp"] == "2026-05-09T19:20:01Z"

