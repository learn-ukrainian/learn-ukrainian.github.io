"""Tests for Monitor API context-window telemetry footers."""

from __future__ import annotations

import json

from scripts.api.telemetry.footer import render_footer
from scripts.api.telemetry.transcript_tokens import (
    current_context_telemetry,
    parse_transcript_tokens,
)


def test_render_footer_base_tier() -> None:
    assert (
        render_footer(tokens=187_000, prev_tokens=165_000, turn=47)
        == "[ctx: 187K (+22K this turn), tier: base, 13K to premium, turn: 47]"
    )


def test_render_footer_premium_tier() -> None:
    assert (
        render_footer(tokens=222_000, prev_tokens=187_000, turn=48)
        == "[ctx: 222K (+35K this turn), tier: premium, 22K over premium, turn: 48]"
    )


def test_render_footer_without_previous_tokens() -> None:
    assert (
        render_footer(tokens=13_000, prev_tokens=None, turn=1)
        == "[ctx: 13K, tier: base, 187K to premium, turn: 1]"
    )


def test_render_footer_without_turn() -> None:
    assert (
        render_footer(tokens=13_000, prev_tokens=None, turn=None)
        == "[ctx: 13K, tier: base, 187K to premium]"
    )


def test_render_footer_exact_200k_boundary_is_base() -> None:
    assert (
        render_footer(tokens=200_000, prev_tokens=187_000, turn=48)
        == "[ctx: 200K (+13K this turn), tier: base, 0K to premium, turn: 48]"
    )


def test_render_footer_exact_zero_delta() -> None:
    assert (
        render_footer(tokens=187_000, prev_tokens=187_000, turn=48)
        == "[ctx: 187K (+0K this turn), tier: base, 13K to premium, turn: 48]"
    )


def test_parse_transcript_tokens_uses_latest_assistant_usage(tmp_path) -> None:
    transcript = tmp_path / "session.jsonl"
    transcript.write_text(
        "\n".join(
            [
                json.dumps({"type": "user", "message": {"content": "hello"}}),
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "usage": {
                                "input_tokens": 100_000,
                                "cache_read_input_tokens": 20_000,
                                "cache_creation_input_tokens": 5_000,
                                "output_tokens": 1_000,
                            }
                        },
                    }
                ),
                "{not json",
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "usage": {
                                "input_tokens": 150_000,
                                "cache_read_input_tokens": 30_000,
                                "cache_creation_input_tokens": 7_000,
                                "output_tokens": 2_000,
                            }
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    telemetry = parse_transcript_tokens(transcript)

    assert telemetry is not None
    assert telemetry.tokens == 187_000
    assert telemetry.prev_tokens == 125_000
    assert telemetry.turn == 2


def test_current_context_telemetry_skips_newest_transcript_without_usage(
    tmp_path,
    monkeypatch,
) -> None:
    projects = tmp_path / ".claude" / "projects"
    project_dir = projects / "-tmp-learn-ukrainian"
    project_dir.mkdir(parents=True)
    older = project_dir / "older.jsonl"
    older.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "usage": {
                        "input_tokens": 187_000,
                        "cache_read_input_tokens": 0,
                        "cache_creation_input_tokens": 0,
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    newer = project_dir / "newer.jsonl"
    newer.write_text(
        json.dumps({"type": "user", "message": {"content": "hi"}}),
        encoding="utf-8",
    )
    newer.touch()
    monkeypatch.setenv("HOME", str(tmp_path))

    telemetry = current_context_telemetry(tmp_path / "learn-ukrainian")

    assert telemetry is not None
    assert telemetry.transcript_path == older
    assert telemetry.tokens == 187_000
