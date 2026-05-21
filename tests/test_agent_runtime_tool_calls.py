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


def test_normalize_tool_calls_concatenates_codex_namespace_and_name() -> None:
    """Codex CLI 0.132.0+ emits `function_call` payloads for MCP calls
    with the canonical prefix split into a separate `namespace` field
    (e.g. ``{"name": "search_text", "namespace": "mcp__sources__"}``).

    Without concatenation, the writer-trace-isolation gate sees bare
    ``search_text`` (no prefix) and flags it wrong_tool_family even
    though it IS an MCP call from the allowed sources family. The
    2026-05-21 a1/my-morning codex-tools build (rollout-2026-05-21T01-37-06)
    contained 10 such calls — all misclassified pre-fix.
    """
    events = [
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "search_text",
                "namespace": "mcp__sources__",
                "arguments": (
                    '{"query":"Захарійчук 24","grade":1,"limit":10}'
                ),
                "call_id": "call_EW63246HqmzrZDz6wqavBene",
            },
        },
        # A codex-internal exec_command stays unprefixed (no namespace);
        # it's correctly flagged by wrong_tool_family downstream because
        # codex-tools writer should never shell out for curriculum work.
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "exec_command",
                "arguments": '{"cmd":"pwd"}',
                "call_id": "call_exec_1",
            },
        },
    ]

    calls = normalize_tool_calls(events)

    assert [call["name"] for call in calls] == [
        "mcp__sources__search_text",
        "exec_command",
    ]
    assert calls[0]["arguments"] == {
        "query": "Захарійчук 24",
        "grade": 1,
        "limit": 10,
    }


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
    assert calls[0]["result"] == [
        {
            "functionResponse": {
                "name": "mcp__sources__verify_words",
                "response": {"output": "ok"},
            }
        }
    ]
    assert calls[0]["timestamp"] == "2026-05-09T19:20:01Z"
