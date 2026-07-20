"""Fleet Comms PR-B2: remaining adapter conformance fixture matrix (#5512).

Same acceptance matrix as B1 for each remaining adapter:
complete · length_limited · missing terminal · nonzero exit with output ·
multi-segment ordered. Exit 0 + text alone never yields ``complete``.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from scripts.fleet_comms.adapter_conformance import (
    REMAINING_ADAPTERS,
    CaptureInput,
    conform,
    raw_capture_matches,
)
from scripts.fleet_comms.contracts import CompletionState

B2_ADAPTERS = ("grok", "kimi", "cursor", "hermes", "opencode")
HERMES_ALIASES = ("hermes", "hermes-grok", "hermes-qwen", "hermes-deepseek", "grok-hermes")


def _lines(*events: dict[str, Any]) -> str:
    return "\n".join(json.dumps(event) for event in events)


# ── shared invariants ────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", B2_ADAPTERS)
def test_exit0_plain_text_without_terminal_is_unknown_not_complete(name: str) -> None:
    env = conform(CaptureInput(adapter=name, stdout="looks fine", returncode=0))
    assert env.completion_state is CompletionState.UNKNOWN
    assert env.terminal_event_observed is False
    assert env.is_formal_review_eligible is False


@pytest.mark.parametrize("name", HERMES_ALIASES)
def test_hermes_aliases_plain_stdout_unknown(name: str) -> None:
    env = conform(CaptureInput(adapter=name, stdout="assistant final message", returncode=0))
    assert env.completion_state is CompletionState.UNKNOWN
    assert env.is_formal_review_eligible is False


def test_remaining_adapters_set_covers_b2_targets() -> None:
    for name in (*B2_ADAPTERS, "hermes-grok", "hermes-qwen", "hermes-deepseek", "grok-build"):
        assert name in REMAINING_ADAPTERS or name in {"grok", "kimi", "cursor", "opencode"}


# ── grok ─────────────────────────────────────────────────────────────────────


def test_grok_complete_requires_stop_reason() -> None:
    stdout = json.dumps(
        {"text": "part-one part-two", "stopReason": "EndTurn", "sessionId": "g-1"}
    )
    raw = stdout.encode("utf-8")
    env = conform(CaptureInput(adapter="grok", stdout=stdout, returncode=0, raw_bytes=raw))
    assert env.completion_state is CompletionState.COMPLETE
    assert env.terminal_event_observed is True
    assert env.session_id == "g-1"
    assert env.response_text == "part-one part-two"
    assert env.is_formal_review_eligible is True
    assert raw_capture_matches(env, raw)


def test_grok_json_without_stop_reason_is_unknown() -> None:
    stdout = json.dumps({"text": "partial answer", "sessionId": "g-2"})
    env = conform(CaptureInput(adapter="grok", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.UNKNOWN
    assert env.terminal_event_observed is False
    assert "partial" in env.response_text
    assert env.is_formal_review_eligible is False


def test_grok_length_limited() -> None:
    stdout = json.dumps({"text": "truncated…", "stopReason": "max_tokens"})
    env = conform(CaptureInput(adapter="grok", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.LENGTH_LIMITED
    assert "truncated" in env.response_text


def test_grok_nonzero_exit_with_output_is_transport_incomplete() -> None:
    stdout = json.dumps({"text": "partial"})
    env = conform(CaptureInput(adapter="grok", stdout=stdout, returncode=1))
    assert env.completion_state is CompletionState.TRANSPORT_INCOMPLETE
    assert env.response_text == "partial"


def test_grok_multi_segment_ordered_events() -> None:
    events = (
        {"text": "first ", "sessionId": "g-3"},
        {"text": "second", "stopReason": "EndTurn", "sessionId": "g-3"},
    )
    env = conform(
        CaptureInput(adapter="grok-build", events=events, returncode=0)
    )
    assert env.completion_state is CompletionState.COMPLETE
    assert [s.text for s in env.segments] == ["first", "second"]
    assert [s.sequence for s in env.segments] == [0, 1]


# ── kimi ─────────────────────────────────────────────────────────────────────


def test_kimi_complete_requires_session_resume_hint() -> None:
    stdout = _lines(
        {"role": "assistant", "content": "part-one "},
        {"role": "assistant", "content": "part-two"},
        {"role": "meta", "type": "session.resume_hint", "session_id": "k-1"},
    )
    raw = stdout.encode("utf-8")
    env = conform(CaptureInput(adapter="kimi", stdout=stdout, returncode=0, raw_bytes=raw))
    assert env.completion_state is CompletionState.COMPLETE
    assert env.terminal_event_observed is True
    assert env.session_id == "k-1"
    assert env.response_text == "part-one part-two"
    assert [s.sequence for s in env.segments] == [0, 1]
    assert raw_capture_matches(env, raw)


def test_kimi_assistant_only_without_terminal_is_unknown() -> None:
    stdout = json.dumps({"role": "assistant", "content": "looks done"})
    env = conform(CaptureInput(adapter="kimi", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.UNKNOWN
    assert env.terminal_event_observed is False
    assert env.is_formal_review_eligible is False


def test_kimi_length_limited_via_finish_reason() -> None:
    stdout = _lines(
        {"role": "assistant", "content": "truncated…", "finish_reason": "length"},
        {"role": "meta", "type": "session.resume_hint", "session_id": "k-2"},
    )
    env = conform(CaptureInput(adapter="kimi", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.LENGTH_LIMITED
    assert "truncated" in env.response_text


def test_kimi_nonzero_exit_with_output_is_transport_incomplete() -> None:
    stdout = json.dumps({"role": "assistant", "content": "partial"})
    env = conform(CaptureInput(adapter="kimi", stdout=stdout, returncode=2))
    assert env.completion_state is CompletionState.TRANSPORT_INCOMPLETE
    assert env.response_text == "partial"


def test_kimi_status_done_is_terminal() -> None:
    stdout = _lines(
        {"role": "assistant", "content": "ok"},
        {"role": "meta", "type": "status", "state": "done"},
    )
    env = conform(CaptureInput(adapter="kimi", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.COMPLETE


# ── cursor ───────────────────────────────────────────────────────────────────


def test_cursor_complete_requires_turn_ended() -> None:
    stdout = _lines(
        {"type": "system", "session_id": "c-1"},
        {
            "role": "assistant",
            "message": {"content": [{"type": "text", "text": "first "}]},
        },
        {
            "role": "assistant",
            "message": {"content": [{"type": "text", "text": "second"}]},
        },
        {"type": "turn_ended", "status": "success"},
    )
    raw = stdout.encode("utf-8")
    env = conform(CaptureInput(adapter="cursor", stdout=stdout, returncode=0, raw_bytes=raw))
    assert env.completion_state is CompletionState.COMPLETE
    assert env.terminal_event_observed is True
    assert env.session_id == "c-1"
    assert env.segments[0].text == "first "
    assert env.segments[1].text == "second"
    assert raw_capture_matches(env, raw)


def test_cursor_message_stream_without_turn_ended_is_unknown() -> None:
    stdout = json.dumps(
        {"type": "message", "role": "assistant", "content": [{"type": "text", "text": "hi"}]}
    )
    env = conform(CaptureInput(adapter="cursor", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.UNKNOWN
    assert env.is_formal_review_eligible is False


def test_cursor_length_limited() -> None:
    stdout = _lines(
        {"type": "text", "content": "truncated…"},
        {"type": "turn_ended", "status": "max_tokens"},
    )
    env = conform(CaptureInput(adapter="cursor", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.LENGTH_LIMITED


def test_cursor_nonzero_exit_with_output_is_transport_incomplete() -> None:
    stdout = json.dumps({"type": "text", "content": "partial"})
    env = conform(CaptureInput(adapter="cursor", stdout=stdout, returncode=1))
    assert env.completion_state is CompletionState.TRANSPORT_INCOMPLETE
    assert env.response_text == "partial"


def test_cursor_turn_ended_error_is_failed() -> None:
    stdout = _lines(
        {"type": "message", "role": "assistant", "content": "oops"},
        {"type": "turn_ended", "status": "error"},
    )
    env = conform(CaptureInput(adapter="cursor", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.FAILED
    assert env.terminal_event_observed is True


def test_cursor_multi_segment_stream_chunks_ordered() -> None:
    stdout = _lines(
        {"type": "text", "content": "A"},
        {"type": "text", "content": "B"},
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "C"}],
        },
        {"type": "turn_ended", "status": "success"},
    )
    env = conform(CaptureInput(adapter="cursor", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.COMPLETE
    # stream chunks flush as one segment, then message segment
    assert env.response_text == "ABC"
    assert [s.sequence for s in env.segments] == [0, 1]


# ── opencode ─────────────────────────────────────────────────────────────────


def test_opencode_complete_requires_final_step_finish_stop() -> None:
    stdout = _lines(
        {"type": "text", "part": {"type": "text", "text": "preamble "}, "sessionID": "o-1"},
        {"type": "step_finish", "part": {"reason": "tool-calls"}, "sessionID": "o-1"},
        {"type": "text", "part": {"type": "text", "text": "final answer"}, "sessionID": "o-1"},
        {"type": "step_finish", "part": {"reason": "stop"}, "sessionID": "o-1"},
    )
    raw = stdout.encode("utf-8")
    env = conform(CaptureInput(adapter="opencode", stdout=stdout, returncode=0, raw_bytes=raw))
    assert env.completion_state is CompletionState.COMPLETE
    assert env.terminal_event_observed is True
    assert env.session_id == "o-1"
    # Ordered multi-turn segments retained (not last-message-only).
    assert [s.text for s in env.segments] == ["preamble ", "final answer"]
    assert raw_capture_matches(env, raw)


def test_opencode_tool_calls_step_finish_alone_is_unknown() -> None:
    stdout = _lines(
        {"type": "text", "part": {"text": "thinking…"}},
        {"type": "step_finish", "part": {"reason": "tool-calls"}},
    )
    env = conform(CaptureInput(adapter="opencode", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.UNKNOWN
    assert env.terminal_event_observed is False
    assert env.is_formal_review_eligible is False


def test_opencode_length_limited() -> None:
    stdout = _lines(
        {"type": "text", "part": {"text": "truncated…"}},
        {"type": "step_finish", "part": {"reason": "length"}},
    )
    env = conform(CaptureInput(adapter="opencode", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.LENGTH_LIMITED
    assert "truncated" in env.response_text


def test_opencode_nonzero_exit_with_output_is_transport_incomplete() -> None:
    stdout = _lines({"type": "text", "part": {"text": "partial"}})
    env = conform(CaptureInput(adapter="opencode", stdout=stdout, returncode=3))
    assert env.completion_state is CompletionState.TRANSPORT_INCOMPLETE
    assert env.response_text == "partial"


def test_opencode_text_without_step_finish_is_unknown() -> None:
    stdout = json.dumps({"type": "text", "part": {"text": "no finish"}})
    env = conform(CaptureInput(adapter="opencode", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.UNKNOWN


# ── hermes ───────────────────────────────────────────────────────────────────


def test_hermes_structured_result_is_complete() -> None:
    stdout = _lines(
        {"type": "assistant", "text": "a"},
        {"type": "done", "result": "a b"},
    )
    env = conform(CaptureInput(adapter="hermes", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.COMPLETE
    assert env.terminal_event_observed is True


def test_hermes_inband_http_error_is_failed() -> None:
    env = conform(
        CaptureInput(
            adapter="hermes-deepseek",
            stdout="HTTP 401: unauthorized provider",
            returncode=0,
        )
    )
    assert env.completion_state is CompletionState.FAILED
    assert env.terminal_event_observed is True
    assert env.response_text == ""


def test_hermes_length_limited_structured() -> None:
    stdout = json.dumps({"type": "result", "result": "cut", "reason": "max_tokens"})
    env = conform(CaptureInput(adapter="hermes-qwen", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.LENGTH_LIMITED


def test_hermes_nonzero_exit_with_output_is_transport_incomplete() -> None:
    env = conform(
        CaptureInput(adapter="hermes-grok", stdout="partial hermes", returncode=1)
    )
    assert env.completion_state is CompletionState.TRANSPORT_INCOMPLETE
    assert env.response_text == "partial hermes"


def test_hermes_empty_nonzero_is_failed() -> None:
    env = conform(CaptureInput(adapter="hermes", stdout="", returncode=1))
    assert env.completion_state is CompletionState.FAILED


def test_hermes_stop_reason_json_object_is_complete() -> None:
    stdout = json.dumps({"text": "via stopReason", "stopReason": "EndTurn"})
    env = conform(CaptureInput(adapter="grok-hermes", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.COMPLETE
    assert env.response_text == "via stopReason"
