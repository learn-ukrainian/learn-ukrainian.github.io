"""Separate assistant messages stay separate (#10005).

Recorded stream shapes, not private transcripts. The verdict parser is unchanged:
a line must start with the label, so a glued ``behavior.VERDICT:`` does not match.
"""

from __future__ import annotations

import json

from scripts.agent_runtime.adapters.acpx import AcpxAdapter
from scripts.agent_runtime.adapters.grok_build import GrokBuildAdapter
from scripts.review.verdict_parser import recognized_verdicts

_REVIEW = (
    "I'll review the pinned head only: confirm the SHA, read the findings schema, "
    "and inspect the one-file diff against the freeze-validator behavior."
)
_FOLLOWUP = (
    "The pinned head matches. Next I'll read the verifier and the full test so the "
    "fixture's Git objects can be checked against real rejection behavior."
)
_VERDICT = "VERDICT: APPROVE\n\nThe exact reviewed head is pinned.\n"
_USAGE = {"grok-4.7-build": {"modelCalls": 1}}
_CHUNKS = ("Hel", "lo world\n")


def _parse_grok(stdout: str):
    return GrokBuildAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None)


def _ndjson(events: list[dict]) -> str:
    return "".join(json.dumps(event) + "\n" for event in events)


def _legacy(text: str):
    return _parse_grok(
        json.dumps({"text": text, "stopReason": "end_turn", "sessionId": "s", "modelUsage": _USAGE})
    )


def _assistant(message_id: str, text: str, *, extra_blocks: list[dict] | None = None) -> dict:
    content: list[dict] = [{"type": "text", "text": text}]
    if extra_blocks:
        content.extend(extra_blocks)
    return {
        "type": "assistant",
        "message": {"id": message_id, "role": "assistant", "content": content},
        "session_id": "s",
    }


def _result(**extra: object) -> dict:
    event = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "result": "ONLY-THE-LAST",
        "stop_reason": "end_turn",
        "session_id": "s",
        "modelUsage": _USAGE,
    }
    event.update(extra)
    return event


def test_separate_assistant_messages_keep_a_parseable_verdict_line():
    glued = "".join((_REVIEW, _FOLLOWUP, _VERDICT))
    stdout = _ndjson(
        [
            _assistant("msg_1", _REVIEW),
            _assistant("msg_2", _FOLLOWUP),
            _assistant("msg_3", _VERDICT),
            _result(),
        ]
    )
    result = _parse_grok(stdout)
    assert result.ok
    assert result.response == "\n".join((_REVIEW, _FOLLOWUP, _VERDICT)).strip()
    assert recognized_verdicts(result.response) == ["APPROVE"]
    assert recognized_verdicts(glued) == []
    assert "ONLY-THE-LAST" not in result.response
    assert result.session_id == "s"
    assert result.substitution["actual_model"] == "grok-4.7-build"


def test_one_message_split_into_chunks_matches_todays_json_text():
    legacy = _legacy("".join(_CHUNKS))
    blocks = _parse_grok(
        _ndjson(
            [
                {
                    "type": "assistant",
                    "message": {
                        "id": "msg_1",
                        "content": [{"type": "text", "text": chunk} for chunk in _CHUNKS],
                    },
                },
                _result(result="".join(_CHUNKS)),
            ]
        )
    )
    deltas = _parse_grok(
        _ndjson(
            [
                {"type": "message_start", "message": {"id": "msg_1", "role": "assistant", "content": []}},
                *[
                    {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": chunk}}
                    for chunk in _CHUNKS
                ],
                {"type": "message_stop"},
                _result(result="".join(_CHUNKS)),
            ]
        )
    )
    updates = _parse_grok(
        _ndjson(
            [
                {"type": "text", "data": chunk, "messageId": "resp_1"}
                for chunk in _CHUNKS
            ]
            + [
                {"type": "usage", "messageId": "resp_1", "stopReason": "end_turn"},
                {"type": "end", "stopReason": "end_turn", "sessionId": "s", "modelUsage": _USAGE},
            ]
        )
    )
    assert legacy.response == "Hello world"
    assert blocks.response == legacy.response
    assert deltas.response == legacy.response
    assert updates.response == legacy.response
    assert blocks.response.count("Hello") == 1


def test_assistant_frame_replaces_deltas_for_the_same_message():
    stdout = _ndjson(
        [
            {"type": "message_start", "message": {"id": "msg_1", "role": "assistant", "content": []}},
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": "NOT-THE-FRAME"},
            },
            {"type": "message_stop"},
            _assistant("msg_1", _VERDICT),
            _result(),
        ]
    )
    result = _parse_grok(stdout)
    assert result.ok
    assert result.response.count("VERDICT: APPROVE") == 1
    assert "NOT-THE-FRAME" not in result.response
    assert "ONLY-THE-LAST" not in result.response


def test_streaming_json_usage_boundary_starts_a_new_line():
    stdout = _ndjson(
        [
            {"type": "text", "data": _FOLLOWUP},
            {"type": "usage", "messageId": "resp_1", "stopReason": "tool_use"},
            {"type": "text", "data": _VERDICT},
            {"type": "usage", "messageId": "resp_2", "stopReason": "end_turn"},
            {"type": "end", "stopReason": "end_turn", "sessionId": "s", "modelUsage": _USAGE},
        ]
    )
    result = _parse_grok(stdout)
    assert result.ok
    assert result.response == "\n".join((_FOLLOWUP, _VERDICT)).strip()
    assert recognized_verdicts(result.response) == ["APPROVE"]
    assert recognized_verdicts(_FOLLOWUP + _VERDICT) == []


def test_message_id_change_without_usage_is_still_a_boundary():
    stdout = _ndjson(
        [
            {"type": "text", "data": "behavior.", "messageId": "resp_1"},
            {"type": "text", "data": "VERDICT: APPROVE\n", "messageId": "resp_2"},
            {"type": "end", "stopReason": "end_turn", "sessionId": "s"},
        ]
    )
    result = _parse_grok(stdout)
    assert recognized_verdicts(result.response) == ["APPROVE"]


def test_tool_call_does_not_split_one_message():
    messages = _parse_grok(
        _ndjson(
            [
                _assistant(
                    "msg_1",
                    "Hello ",
                    extra_blocks=[
                        {"type": "tool_use", "id": "call_1", "name": "read_file", "input": {}},
                        {"type": "text", "text": "world."},
                    ],
                ),
                _result(result="ignored"),
            ]
        )
    )
    updates = _parse_grok(
        _ndjson(
            [
                {"type": "text", "data": "Hello "},
                {"type": "tool_call", "toolCallId": "call_1", "toolName": "read_file", "status": "in_progress"},
                {"type": "text", "data": "world."},
                {"type": "end", "stopReason": "end_turn", "sessionId": "s"},
            ]
        )
    )
    assert messages.response == "Hello world."
    assert updates.response == "Hello world."


def test_tool_only_assistant_message_adds_no_blank_line():
    stdout = _ndjson(
        [
            _assistant("msg_1", "Hello"),
            {
                "type": "assistant",
                "message": {
                    "id": "msg_tool",
                    "content": [{"type": "tool_use", "id": "call_1", "name": "read_file", "input": {}}],
                },
            },
            _assistant("msg_2", "VERDICT: APPROVE"),
            _result(result="VERDICT: APPROVE"),
        ]
    )
    result = _parse_grok(stdout)
    assert result.response == "Hello\nVERDICT: APPROVE"
    assert recognized_verdicts(result.response) == ["APPROVE"]


def test_verdict_quoted_mid_line_still_does_not_parse():
    commentary = "The commentary mentions VERDICT: APPROVE as an example, then continues."
    result = _parse_grok(_ndjson([_assistant("msg_1", commentary), _result(result=commentary)]))
    assert result.ok
    assert result.response == commentary
    assert recognized_verdicts(result.response) == []


def test_log_noise_around_a_stream_is_ignored():
    stdout = "startup log\n" + _ndjson([_assistant("msg_1", "final report"), _result(result="nope")]) + "trailing\n"
    result = _parse_grok(stdout)
    assert result.ok
    assert result.response == "final report"


def test_pretty_printed_json_object_stays_on_the_legacy_parser():
    stdout = json.dumps({"text": "final report", "stopReason": "end_turn", "sessionId": "s"}, indent=2)
    result = _parse_grok(stdout)
    assert result.ok
    assert result.response == "final report"
    assert result.session_id == "s"


def test_stream_error_event_stays_a_provider_failure():
    stdout = _ndjson(
        [
            {"type": "text", "data": "partial"},
            {"type": "error", "message": "Error code: 429"},
        ]
    )
    result = _parse_grok(stdout)
    assert not result.ok
    assert result.response == ""
    assert result.failure_code == "rate_limited"
    assert result.provider_error_text == "Error code: 429"


def _acp_stdout(params_list: list[dict]) -> str:
    events: list[dict] = [
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "session/prompt",
            "params": {"sessionId": "sess", "prompt": [{"type": "text", "text": "ping"}]},
        }
    ]
    events.extend({"jsonrpc": "2.0", "method": "session/update", "params": params} for params in params_list)
    events.append({"jsonrpc": "2.0", "id": 2, "result": {"stopReason": "end_turn"}})
    return "".join(json.dumps(event) + "\n" for event in events)


def _acp_chunk(
    text: str,
    *,
    message_id: str | None = None,
    stream_start_ms: int | str | bool | None = None,
    chunk_id: int | None = None,
) -> dict:
    update: dict = {"sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": text}}
    if message_id is not None:
        update["messageId"] = message_id
    params: dict = {"sessionId": "sess", "update": update}
    meta: dict = {}
    if stream_start_ms is not None:
        meta["streamStartMs"] = stream_start_ms
    if chunk_id is not None:
        meta["chunkId"] = chunk_id
    if meta:
        params["_meta"] = meta
    return params


def _parse_acp(stdout: str):
    return AcpxAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None)


def test_acp_chunks_without_a_message_id_stay_one_message():
    stdout = _acp_stdout([_acp_chunk("Hello "), _acp_chunk("world.")])
    assert _parse_acp(stdout).response == "Hello world."


def test_acp_same_message_id_joins_even_when_stream_start_changes():
    stdout = _acp_stdout(
        [
            _acp_chunk("Hello ", message_id="m1", stream_start_ms=1),
            _acp_chunk("world.", message_id="m1", stream_start_ms=2),
        ]
    )
    assert _parse_acp(stdout).response == "Hello world."


def test_acp_stream_start_boundary_makes_the_verdict_a_line():
    stdout = _acp_stdout(
        [
            _acp_chunk(_FOLLOWUP, stream_start_ms=1791402125670, chunk_id=30),
            _acp_chunk(_VERDICT, stream_start_ms=1791402901932, chunk_id=442),
        ]
    )
    result = _parse_acp(stdout)
    assert result.ok
    assert result.response == f"{_FOLLOWUP}\n{_VERDICT}"
    assert recognized_verdicts(result.response) == ["APPROVE"]
    assert recognized_verdicts(_FOLLOWUP + _VERDICT) == []


def test_acp_same_stream_start_ignores_chunk_id_and_tool_calls():
    stdout = _acp_stdout(
        [
            _acp_chunk("Hello ", stream_start_ms=10, chunk_id=1),
            {
                "sessionId": "sess",
                "update": {"sessionUpdate": "tool_call", "toolCallId": "call-1", "name": "read", "status": "pending"},
                "_meta": {"streamStartMs": 99, "chunkId": 7},
            },
            _acp_chunk("world.", stream_start_ms=10, chunk_id=2),
        ]
    )
    assert _parse_acp(stdout).response == "Hello world."


def test_acp_message_id_change_inserts_a_newline():
    stdout = _acp_stdout(
        [
            _acp_chunk("behavior.", message_id="m1", stream_start_ms=1),
            _acp_chunk("VERDICT: APPROVE", message_id="m2", stream_start_ms=1),
        ]
    )
    result = _parse_acp(stdout)
    assert result.response == "behavior.\nVERDICT: APPROVE"
    assert recognized_verdicts(result.response) == ["APPROVE"]


def test_acp_bool_stream_start_is_not_a_message_id():
    stdout = _acp_stdout(
        [
            _acp_chunk("Hello ", stream_start_ms=True),
            _acp_chunk("world.", stream_start_ms=False),
        ]
    )
    assert _parse_acp(stdout).response == "Hello world."


def test_acp_empty_message_id_falls_through_to_stream_start():
    stdout = _acp_stdout(
        [
            _acp_chunk("behavior.", message_id="", stream_start_ms=1),
            _acp_chunk("VERDICT: APPROVE", message_id="", stream_start_ms=2),
        ]
    )
    result = _parse_acp(stdout)
    assert recognized_verdicts(result.response) == ["APPROVE"]


def test_acp_mid_line_verdict_in_one_message_does_not_parse():
    commentary = "The commentary mentions VERDICT: APPROVE as an example, then continues."
    result = _parse_acp(_acp_stdout([_acp_chunk(commentary, stream_start_ms=5, chunk_id=1)]))
    assert result.response == commentary
    assert recognized_verdicts(result.response) == []
