"""Current main-model context usage, including advisor executor iterations (#10471)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

LIB = Path(__file__).resolve().parents[1] / "agents_extensions/shared/hooks/context-rollover-lib.sh"


def incident_usage() -> dict:
    """Usage numbers from the measured main/advisor/main structure, without content."""
    return {
        "input_tokens": 4,
        "cache_read_input_tokens": 1_172_621,
        "cache_creation_input_tokens": 3325,
        "output_tokens": 2416,
        "cache_creation": {"ephemeral_1h_input_tokens": 177, "ephemeral_5m_input_tokens": 0},
        "iterations": [
            {
                "type": "message",
                "input_tokens": 2,
                "cache_read_input_tokens": 586_222,
                "cache_creation_input_tokens": 177,
                "output_tokens": 2086,
                "cache_creation": {"ephemeral_1h_input_tokens": 177, "ephemeral_5m_input_tokens": 0},
            },
            {
                "type": "advisor_message",
                "input_tokens": 593_221,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
                "output_tokens": 3421,
            },
            {
                "type": "message",
                "input_tokens": 2,
                "cache_read_input_tokens": 586_399,
                "cache_creation_input_tokens": 3148,
                "output_tokens": 330,
                "cache_creation": {"ephemeral_1h_input_tokens": 0, "ephemeral_5m_input_tokens": 3148},
            },
        ],
    }


def advisor_usage(tokens: int) -> dict:
    """Two cached main passes with an advisor between them and a doubled aggregate."""
    main = {
        "type": "message",
        "input_tokens": 2,
        "cache_read_input_tokens": tokens - 102,
        "cache_creation_input_tokens": 100,
        "output_tokens": 9_999_999,
    }
    return {
        "input_tokens": 4,
        "cache_read_input_tokens": 2 * (tokens - 102),
        "cache_creation_input_tokens": 200,
        "output_tokens": 19_999_998,
        "iterations": [
            main.copy(),
            {"type": "advisor_message", "input_tokens": tokens + 1000},
            main.copy(),
        ],
    }


def write_usage(path: Path, usage: dict) -> None:
    path.write_text(json.dumps({"type": "assistant", "message": {"id": "synthetic", "usage": usage}}) + "\n")


def latest_tokens(path: Path) -> int:
    result = subprocess.run(
        ["bash", "-c", 'source "$1"; context_latest_usage_tokens "$2"', "test", str(LIB), str(path)],
        check=True,
        text=True,
        capture_output=True,
        timeout=30,
    )
    return int(result.stdout)


def test_incident_uses_final_main_pass(tmp_path: Path) -> None:
    transcript = tmp_path / "usage.jsonl"
    write_usage(transcript, incident_usage())
    assert latest_tokens(transcript) == 589_549


def test_advisor_last_does_not_replace_final_main_pass(tmp_path: Path) -> None:
    usage = incident_usage()
    usage["iterations"].append({"type": "advisor_message", "input_tokens": 999_999})
    transcript = tmp_path / "usage.jsonl"
    write_usage(transcript, usage)
    assert latest_tokens(transcript) == 589_549


@pytest.mark.parametrize(
    ("usage", "expected"),
    [
        (
            {
                "input_tokens": 2,
                "cache_read_input_tokens": 42_109,
                "cache_creation_input_tokens": 35_235,
                "iterations": [],
                "output_tokens": 9_999_999,
                "cache_creation": {"ephemeral_1h_input_tokens": 35_235, "ephemeral_5m_input_tokens": 0},
            },
            77_346,
        ),
        (
            {
                "input_tokens": 2,
                "cache_read_input_tokens": 7793,
                "cache_creation_input_tokens": 17_137,
                "output_tokens": 9_999_999,
                "cache_creation": {"ephemeral_1h_input_tokens": 0, "ephemeral_5m_input_tokens": 17_137},
            },
            24_932,
        ),
        (
            {
                "input_tokens": 2,
                "cache_read_input_tokens": 7793,
                "cache_creation_input_tokens": 17_137,
                "iterations": [{"type": "advisor_message", "input_tokens": 999_999}],
            },
            24_932,
        ),
        (
            {
                "input_tokens": 2,
                "cache_read_input_tokens": 7793,
                "cache_creation_input_tokens": 17_137,
                "iterations": None,
            },
            24_932,
        ),
        ({"iterations": [{"type": "message", "output_tokens": 9_999_999}], "input_tokens": 999_999}, 0),
    ],
    ids=["empty-iterations", "no-iterations", "advisor-only", "non-array", "main-without-input"],
)
def test_usage_shapes_are_additive_without_main_iterations(tmp_path: Path, usage: dict, expected: int) -> None:
    transcript = tmp_path / "usage.jsonl"
    write_usage(transcript, usage)
    assert latest_tokens(transcript) == expected


def test_repeated_id_counts_only_last_usage_bearing_line(tmp_path: Path) -> None:
    usage = incident_usage()
    usage["output_tokens"] = 9_999_999
    usage["iterations"][-1]["output_tokens"] = 9_999_999
    lines = [{"type": "assistant", "message": {"id": "same", "usage": {"input_tokens": 100}}}]
    lines.extend({"type": "assistant", "message": {"id": "same", "usage": usage}} for _ in range(7))
    lines.extend(
        [
            {"type": "assistant", "message": {"id": "same"}},
            {"type": "assistant", "message": {"usage": None}},
            {"type": "user", "message": {"usage": {"input_tokens": 999_999}}},
        ]
    )
    transcript = tmp_path / "usage.jsonl"
    transcript.write_text("\n".join(map(json.dumps, lines)) + "\n")
    assert latest_tokens(transcript) == 589_549


@pytest.mark.parametrize(
    "content", ["", '{"type":"assistant","message":{}}\n', '{"type":"assistant","message":{"usage":null}}\n']
)
def test_no_usage_returns_zero(tmp_path: Path, content: str) -> None:
    transcript = tmp_path / "usage.jsonl"
    transcript.write_text(content)
    assert latest_tokens(transcript) == 0


def test_missing_transcript_returns_zero(tmp_path: Path) -> None:
    assert latest_tokens(tmp_path / "missing.jsonl") == 0
