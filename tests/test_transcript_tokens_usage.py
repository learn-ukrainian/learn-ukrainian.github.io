"""Context-size telemetry must follow the last main-model pass (#10476).

Fixtures carry usage numbers only. The incident shape is an assistant message
produced with the advisor tool: its top-level ``usage`` aggregates the executor
iterations, while ``iterations[]`` splits main passes (``message``) from the
advisor's separate pass (``advisor_message``), whose input is not session context.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.api.telemetry.transcript_tokens import (
    parse_transcript_tokens,
    usage_input_tokens,
)


def _pass(kind: str, input_tokens: Any, cache_read: Any, cache_creation: Any) -> dict[str, Any]:
    return {
        "type": kind,
        "input_tokens": input_tokens,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_creation,
        "output_tokens": 999,
        "cache_creation": {"ephemeral_5m_input_tokens": 777, "ephemeral_1h_input_tokens": 555},
    }


def _incident_usage() -> dict[str, Any]:
    return {
        "input_tokens": 4,
        "cache_read_input_tokens": 1172621,
        "cache_creation_input_tokens": 3325,
        "output_tokens": 4321,
        "iterations": [
            _pass("message", 2, 586222, 177),
            _pass("advisor_message", 593221, 0, 0),
            _pass("message", 2, 586399, 3148),
        ],
    }


def _write_transcript(path: Path, usages: list[dict[str, Any]]) -> Path:
    lines = [json.dumps({"type": "assistant", "message": {"usage": usage}}) for usage in usages]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_advisor_incident_reports_final_main_pass() -> None:
    assert usage_input_tokens(_incident_usage()) == 589549


@pytest.mark.parametrize("iterations", [None, []])
def test_absent_or_empty_iterations_keep_additive_sum(iterations: list[Any] | None) -> None:
    usage: dict[str, Any] = {
        "input_tokens": 6,
        "cache_read_input_tokens": 70000,
        "cache_creation_input_tokens": 7340,
    }
    if iterations is not None:
        usage["iterations"] = iterations
    assert usage_input_tokens(usage) == 77346


def test_advisor_entry_last_still_uses_last_message_pass() -> None:
    usage = {
        "input_tokens": 9,
        "cache_read_input_tokens": 9,
        "cache_creation_input_tokens": 9,
        "iterations": [
            _pass("message", 3, 40000, 100),
            _pass("advisor_message", 900000, 0, 0),
        ],
    }
    assert usage_input_tokens(usage) == 40103


def test_only_advisor_entries_fall_back_to_top_level_sum() -> None:
    usage = {
        "input_tokens": 5,
        "cache_read_input_tokens": 24000,
        "cache_creation_input_tokens": 927,
        "iterations": [_pass("advisor_message", 593221, 0, 0)],
    }
    assert usage_input_tokens(usage) == 24932


def test_null_and_missing_fields_count_as_zero() -> None:
    usage = {
        "input_tokens": 4,
        "iterations": [
            _pass("message", 2, 500, 10),
            {"type": "message", "input_tokens": None, "cache_read_input_tokens": 1200},
        ],
    }
    assert usage_input_tokens(usage) == 1200


def test_null_top_level_fields_count_as_zero() -> None:
    assert usage_input_tokens({"input_tokens": None, "cache_read_input_tokens": 8}) == 8


def test_non_numeric_garbage_does_not_raise() -> None:
    usage = {
        "input_tokens": "abc",
        "cache_read_input_tokens": 100,
        "iterations": [
            "not-a-dict",
            {
                "type": "message",
                "input_tokens": "abc",
                "cache_read_input_tokens": [1],
                "cache_creation_input_tokens": 25,
            },
        ],
    }
    assert usage_input_tokens(usage) == 25
    assert usage_input_tokens({"input_tokens": {"x": 1}, "cache_read_input_tokens": 100}) == 100


def test_non_list_iterations_fall_back_to_top_level_sum() -> None:
    usage = {"input_tokens": 1, "cache_read_input_tokens": 2, "cache_creation_input_tokens": 3, "iterations": "bad"}
    assert usage_input_tokens(usage) == 6


def test_output_and_cache_creation_breakdown_are_never_added() -> None:
    usage = {
        "input_tokens": 1,
        "cache_read_input_tokens": 2,
        "cache_creation_input_tokens": 3,
        "output_tokens": 10000,
        "cache_creation": {"ephemeral_5m_input_tokens": 3},
    }
    assert usage_input_tokens(usage) == 6


def test_parse_transcript_tokens_follows_rule_for_tokens_and_prev(tmp_path: Path) -> None:
    first = {
        "input_tokens": 6,
        "cache_read_input_tokens": 70000,
        "cache_creation_input_tokens": 7340,
    }
    path = _write_transcript(tmp_path / "session.jsonl", [first, _incident_usage()])

    telemetry = parse_transcript_tokens(path)

    assert telemetry is not None
    assert telemetry.tokens == 589549
    assert telemetry.prev_tokens == 77346
    assert telemetry.turn == 2


def test_parse_transcript_tokens_advisor_turn_then_plain_turn(tmp_path: Path) -> None:
    plain = {"input_tokens": 3, "cache_read_input_tokens": 589549, "cache_creation_input_tokens": 400}
    path = _write_transcript(tmp_path / "session.jsonl", [_incident_usage(), plain])

    telemetry = parse_transcript_tokens(path)

    assert telemetry is not None
    assert telemetry.tokens == 589952
    assert telemetry.prev_tokens == 589549
