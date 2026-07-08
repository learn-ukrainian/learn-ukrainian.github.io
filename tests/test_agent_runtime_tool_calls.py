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
                "arguments": ('{"query":"Захарійчук 24","grade":1,"limit":10}'),
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


def test_normalize_tool_calls_joins_codex_0135_namespace_without_trailing_sep() -> None:
    """Codex CLI 0.135.0 dropped the trailing ``__`` from the namespace field:
    it emits ``{"name": "get_chunk_context", "namespace": "mcp__sources"}``
    (no separator) instead of 0.132.0's ``"mcp__sources__"``.

    Naive concatenation yields ``mcp__sourcesget_chunk_context`` — still missing
    the ``__`` join — so the writer-trace-isolation gate flags wrong_tool_family
    and the tools_writer_runtime_gate HARD-fails ``mcp_tools_never_invoked`` for
    EVERY codex build under 0.135.0, even though the calls fired. Reference:
    rollout-2026-05-29T09-59-48 a1/my-morning build (15 valid sources calls
    misclassified as 0). The join must normalize to exactly one ``__``.
    """
    events = [
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "get_chunk_context",
                "namespace": "mcp__sources",
                "arguments": '{"chunk_id":"1-klas-bukvar_s0024","window":1}',
                "call_id": "call_0135_a",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "verify_words",
                "namespace": "mcp__sources",
                "arguments": '{"words":["вмиваюся"]}',
                "call_id": "call_0135_b",
            },
        },
    ]

    calls = normalize_tool_calls(events)

    assert [call["name"] for call in calls] == [
        "mcp__sources__get_chunk_context",
        "mcp__sources__verify_words",
    ]


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


def test_normalize_tool_calls_correlates_codex_function_call_output() -> None:
    """Codex CLI emits ``function_call_output`` events with ``call_id`` as
    the correlation key (not ``tool_call_id``/``tool_use_id``).

    Without recognising both, codex rollouts pair the function_call with no
    output, leaving ``writer_tool_calls.json`` entries blank and the
    ``textbook_grounding`` gate reading ``textbook_result_hits: 0`` even
    when the writer's search_text/get_chunk_context calls returned grounded
    textbook chunks. Empirical reference: rollout-2026-05-22T22-58-38 for
    the post-#2233 codex-tools a1/my-morning build — 38 valid mcp__sources__*
    calls with full results in the rollout, all dropped on the floor by the
    result-correlation pass.
    """
    events = [
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "search_text",
                "namespace": "mcp__sources__",
                "arguments": '{"query":"Захарійчук 24","grade":1,"limit":10}',
                "call_id": "call_ujhILo8Q08B3NwugWTPbXbOm",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "function_call_output",
                "call_id": "call_ujhILo8Q08B3NwugWTPbXbOm",
                "output": ('Wall time: 0.0212 seconds\nOutput:\n[{"type":"text","text":"Found 10 results"}]'),
            },
        },
    ]

    calls = normalize_tool_calls(events)

    assert len(calls) == 1
    assert calls[0]["name"] == "mcp__sources__search_text"
    assert calls[0]["result"] == [{"type": "text", "text": "Found 10 results"}]
    assert "Found 10 results" in calls[0]["output_summary"]


def test_normalize_tool_calls_correlates_codex_mcp_output_by_call_id() -> None:
    # A function_call event: {"type":"function_call","id":"fc_ABC…","call_id":"call_XYZ…","namespace":"mcp__sources","name":"search_literary","arguments":"{\"query\":\"колядки\"}"}
    # A mcp_tool_call_end event: {"type":"mcp_tool_call_end","call_id":"call_XYZ…","result":"…Класичною величальною поезією укр. народу є колядки, щедрівки…"}
    events = [
        {
            "type": "function_call",
            "id": "fc_ABC123",
            "call_id": "call_XYZ789",
            "namespace": "mcp__sources",
            "name": "search_literary",
            "arguments": '{"query":"колядки"}',
        },
        {
            "type": "mcp_tool_call_end",
            "call_id": "call_XYZ789",
            "result": "…Класичною величальною поезією укр. народу є колядки, щедрівки…",
        },
    ]

    calls = normalize_tool_calls(events)

    # Assert normalize_tool_calls([...]) yields exactly one call with name == "mcp__sources__search_literary"
    # AND a non-empty result (and output_summary).
    assert len(calls) == 1
    call = calls[0]
    assert call["name"] == "mcp__sources__search_literary"
    assert call["result"] == "…Класичною величальною поезією укр. народу є колядки, щедрівки…"
    assert "колядки" in call["output_summary"]

    # Add a second assertion through scripts.audit.runtime_tool_events.map_runtime_tool_calls([...]):
    # the gate-facing event has non-null output containing the excerpt substring.
    from scripts.audit.runtime_tool_events import map_runtime_tool_calls

    gate_events = map_runtime_tool_calls(calls)
    assert len(gate_events) == 1
    assert gate_events[0]["tool"] == "mcp__sources__search_literary"
    assert gate_events[0]["output"] == "…Класичною величальною поезією укр. народу є колядки, щедрівки…"

    # Include a NON-regression assertion: a function_call + function_call_output
    # (shell, correlates on call_id only, no separate item id) still correlates — so the change is a superset.
    shell_events = [
        {
            "type": "function_call",
            "name": "exec_command",
            "arguments": '{"cmd":"pwd"}',
            "call_id": "call_shell_123",
        },
        {
            "type": "function_call_output",
            "call_id": "call_shell_123",
            "output": "/Users/krisztiankoos/projects/learn-ukrainian",
        },
    ]
    shell_calls = normalize_tool_calls(shell_events)
    assert len(shell_calls) == 1
    assert shell_calls[0]["name"] == "exec_command"
    assert shell_calls[0]["result"] == "/Users/krisztiankoos/projects/learn-ukrainian"
    assert "/Users/krisztiankoos/projects/learn-ukrainian" in shell_calls[0]["output_summary"]
