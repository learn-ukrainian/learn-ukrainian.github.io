"""Tests for Monitor API context-window telemetry footers."""

from __future__ import annotations

import json

from scripts.api.telemetry.transcript_tokens import (
    current_context_telemetry,
    parse_transcript_tokens,
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
    # Exclusive server/test hooks must not leak into this fixture — when set,
    # resolve_transcript_paths returns only that path and never scans HOME.
    monkeypatch.delenv("LEARN_UKRAINIAN_TRANSCRIPT_PATH", raising=False)
    monkeypatch.delenv("CLAUDE_TRANSCRIPT_PATH", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    project_root = tmp_path / "learn-ukrainian"
    project_root.mkdir()
    # Match scripts.api.telemetry.transcript_tokens._claude_project_dir_name
    # (resolved path with "/" → "-") so candidates come from the exact dir,
    # not the *learn-ukrainian* fallback glob.
    project_dir = (
        tmp_path / ".claude" / "projects" / str(project_root.resolve()).replace("/", "-")
    )
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

    telemetry = current_context_telemetry(project_root)

    assert telemetry is not None
    assert telemetry.transcript_path == older
    assert telemetry.tokens == 187_000
