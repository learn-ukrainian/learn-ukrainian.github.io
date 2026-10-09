from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from agent_runtime.adapters.claude import ClaudeAdapter, _extract_stream_json_response


def test_claude_stream_single_turn_byte_identical() -> None:
    events = [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Thinking..."}]}},
        {"type": "result", "subtype": "success", "result": "Substantive report with findings.\n\nVERDICT: APPROVE"},
    ]
    extracted = _extract_stream_json_response(events)
    assert extracted == "Substantive report with findings.\n\nVERDICT: APPROVE"


def test_claude_stream_multi_turn_two_turns_preserves_substantive_report() -> None:
    turn1_report = (
        "## Review Findings\n\n"
        "- Finding 1: Unhandled exception on empty input\n"
        "- Finding 2: Missing test coverage for edge cases\n\n"
        "VERDICT: REQUEST_CHANGES"
    )
    turn2_followup = "my verdict stays the same, for the bypass reported above"
    events = [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Reviewing..."}]}},
        {"type": "result", "subtype": "success", "result": turn1_report},
        {"type": "user", "message": {"content": [{"type": "text", "text": "Notification: background job finished"}]}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Checking notification..."}]}},
        {"type": "result", "subtype": "success", "result": turn2_followup},
    ]
    extracted = _extract_stream_json_response(events)
    expected = f"{turn1_report}\n\n{turn2_followup}"
    assert extracted == expected


def test_claude_stream_multi_turn_three_turns_preserves_all_reports() -> None:
    turn1 = "Phase 1: Initial analysis completed successfully."
    turn2 = "Phase 2: Fix implemented and verified locally."
    turn3 = "Phase 3: Cleaned up worktree and final checks passed."
    events = [
        {"type": "result", "subtype": "success", "result": turn1},
        {"type": "result", "subtype": "success", "result": turn2},
        {"type": "result", "subtype": "success", "result": turn3},
    ]
    extracted = _extract_stream_json_response(events)
    assert extracted == f"{turn1}\n\n{turn2}\n\n{turn3}"


def test_claude_stream_consecutive_duplicate_results_deduped() -> None:
    report = "Single substantive report"
    events = [
        {"type": "result", "subtype": "success", "result": report},
        {"type": "result", "subtype": "success", "result": report},
    ]
    extracted = _extract_stream_json_response(events)
    assert extracted == report


def test_claude_stream_structured_output_unchanged() -> None:
    events = [
        {"type": "result", "subtype": "success", "result": "Some text"},
        {"type": "result", "structured_output": {"verdict": "APPROVE", "score": 9.5}},
    ]
    extracted = _extract_stream_json_response(events)
    expected = json.dumps({"verdict": "APPROVE", "score": 9.5}, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    assert extracted == expected


def test_claude_stream_empty_result_fallback_to_text_parts() -> None:
    events = [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Part 1"}]}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Part 2"}]}},
    ]
    extracted = _extract_stream_json_response(events)
    assert extracted == "Part 1\nPart 2"


def test_claude_parse_response_multiturn_integration() -> None:
    turn1_report = (
        "## Review Findings\n\n"
        "P1: Bug in error handling\n\n"
        "VERDICT: REQUEST_CHANGES"
    )
    turn2_followup = "Confirmed findings remain valid."
    stdout = "\n".join([
        json.dumps({"type": "result", "subtype": "success", "result": turn1_report, "session_id": "sess-123"}),
        json.dumps({"type": "user", "message": {"content": [{"type": "text", "text": "ping"}]}}),
        json.dumps({"type": "result", "subtype": "success", "result": turn2_followup, "session_id": "sess-123"}),
    ])
    result = ClaudeAdapter().parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is True
    assert result.session_id == "sess-123"
    assert result.response == f"{turn1_report}\n\n{turn2_followup}"
