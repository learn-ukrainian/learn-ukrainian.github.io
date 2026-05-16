"""Tests for the /goal driver Stop hook (scripts/goal_driver/stop_hook.py)."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.goal_driver import stop_hook


def _write_transcript(path: Path, assistant_chunks: list[str]) -> None:
    """Write a minimal Claude Code JSONL transcript with N assistant turns."""
    lines = []
    for chunk in assistant_chunks:
        lines.append(
            json.dumps(
                {
                    "role": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [{"type": "text", "text": chunk}],
                    },
                }
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run(monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any]) -> tuple[int, str]:
    """Invoke stop_hook.main with captured stdout."""
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    try:
        rc = stop_hook.main(stdin=json.dumps(payload))
    finally:
        monkeypatch.undo()
    return rc, captured.getvalue()


def test_main_exits_zero_on_empty_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    rc = stop_hook.main(stdin="")
    assert rc == 0
    assert captured.getvalue() == ""


def test_main_exits_zero_on_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    rc = stop_hook.main(stdin="not-json{")
    assert rc == 0
    assert captured.getvalue() == ""


def test_main_handles_missing_transcript(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    rc, out = _run(
        monkeypatch,
        {"transcript_path": str(tmp_path / "does-not-exist.jsonl")},
    )
    assert rc == 0
    assert out == ""


def test_goal_wait_emits_signal_annotation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    transcript = tmp_path / "session.jsonl"
    _write_transcript(
        transcript,
        [
            "Running build…",
            'GOAL_WAIT signal=watcher-codex-done reason="Codex dispatch ETA 30 min" eta_s=1800',
        ],
    )
    rc, out = _run(monkeypatch, {"transcript_path": str(transcript)})
    assert rc == 0
    payload = json.loads(out)
    msg = payload["hookSpecificOutput"]["additionalContext"]
    assert "watcher-codex-done" in msg
    assert "1800s" in msg
    assert "do NOT increment no_progress" in msg


def test_goal_status_with_active_dispatch_emits_annotation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    transcript = tmp_path / "session.jsonl"
    _write_transcript(
        transcript,
        [
            "GOAL_STATUS turn=12/30 blocked=0/3 no_progress=2/3 queue_head=ship-mdx",
        ],
    )
    monkeypatch.setattr(
        stop_hook,
        "_query_active_dispatches",
        lambda: {
            "total": 2,
            "tasks": [
                {"task_id": "claude-2026-05-17-001"},
                {"task_id": "codex-2026-05-17-002"},
            ],
        },
    )
    rc, out = _run(monkeypatch, {"transcript_path": str(transcript)})
    assert rc == 0
    payload = json.loads(out)
    msg = payload["hookSpecificOutput"]["additionalContext"]
    assert "2 in-flight task(s)" in msg
    assert "claude-2026-05-17-001" in msg
    assert "codex-2026-05-17-002" in msg
    assert "do NOT increment no_progress" in msg


def test_goal_status_with_no_active_dispatch_emits_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    transcript = tmp_path / "session.jsonl"
    _write_transcript(
        transcript,
        ["GOAL_STATUS turn=1/30 blocked=0/3 no_progress=0/3 queue_head=item-a"],
    )
    monkeypatch.setattr(stop_hook, "_query_active_dispatches", lambda: {"total": 0, "tasks": []})
    rc, out = _run(monkeypatch, {"transcript_path": str(transcript)})
    assert rc == 0
    assert out == ""


def test_goal_status_with_api_down_emits_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    transcript = tmp_path / "session.jsonl"
    _write_transcript(
        transcript,
        ["GOAL_STATUS turn=3/30 blocked=0/3 no_progress=0/3 queue_head=item-c"],
    )
    monkeypatch.setattr(stop_hook, "_query_active_dispatches", lambda: None)
    rc, out = _run(monkeypatch, {"transcript_path": str(transcript)})
    assert rc == 0
    assert out == ""


def test_goal_done_emits_nothing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    transcript = tmp_path / "session.jsonl"
    _write_transcript(
        transcript,
        ['GOAL_DONE reason="all 5 modules audit-green per audit/INDEX.md"'],
    )
    rc, out = _run(monkeypatch, {"transcript_path": str(transcript)})
    assert rc == 0
    assert out == ""


def test_picks_last_status_when_transcript_has_multiple(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    transcript = tmp_path / "session.jsonl"
    _write_transcript(
        transcript,
        [
            "GOAL_STATUS turn=1/30 blocked=0/3 no_progress=0/3 queue_head=item-a",
            "GOAL_STATUS turn=2/30 blocked=0/3 no_progress=0/3 queue_head=item-b",
            'GOAL_WAIT signal=watcher-pr-merge reason="awaiting PR merge"',
        ],
    )
    rc, out = _run(monkeypatch, {"transcript_path": str(transcript)})
    assert rc == 0
    payload = json.loads(out)
    msg = payload["hookSpecificOutput"]["additionalContext"]
    assert "watcher-pr-merge" in msg
