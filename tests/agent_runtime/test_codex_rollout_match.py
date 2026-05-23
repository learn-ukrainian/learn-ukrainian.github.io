"""Regression tests for Codex rollout binding (#2239)."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.codex import CodexAdapter


def _plan(tmp_path: Path, stdin_payload: str) -> InvocationPlan:
    return InvocationPlan(cmd=["codex"], cwd=tmp_path, stdin_payload=stdin_payload)


def _write_rollout(tmp_path: Path, user_message: str) -> Path:
    rollout = tmp_path / "rollout.jsonl"
    rollout.write_text(
        json.dumps(
            {
                "type": "event_msg",
                "payload": {"type": "user_message", "message": user_message},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return rollout


def test_rollout_matches_with_trailing_newline(tmp_path: Path) -> None:
    """Codex CLI may add or strip a final newline when storing rollouts."""
    adapter = CodexAdapter()
    rollout = _write_rollout(tmp_path, "hello world\n")

    assert adapter._rollout_matches_plan(rollout, _plan(tmp_path, "hello world")) is True


def test_rollout_matches_with_crlf_normalization(tmp_path: Path) -> None:
    """CRLF in rollout storage matches LF in the invocation payload."""
    adapter = CodexAdapter()
    rollout = _write_rollout(tmp_path, "line1\r\nline2\r\nline3\r\n")

    assert (
        adapter._rollout_matches_plan(
            rollout,
            _plan(tmp_path, "line1\nline2\nline3"),
        )
        is True
    )


def test_rollout_matches_with_unicode_normalization(tmp_path: Path) -> None:
    """NFD prompt storage matches the invocation's NFC payload."""
    adapter = CodexAdapter()
    rollout = _write_rollout(tmp_path, unicodedata.normalize("NFD", "їжак"))

    assert adapter._rollout_matches_plan(rollout, _plan(tmp_path, "їжак")) is True


def test_rollout_rejects_unrelated_message(tmp_path: Path) -> None:
    """Different content should still reject."""
    adapter = CodexAdapter()
    rollout = _write_rollout(tmp_path, "goodbye")

    assert adapter._rollout_matches_plan(rollout, _plan(tmp_path, "hello")) is False


def test_rollout_matches_response_item_shape(tmp_path: Path) -> None:
    """response_item events with content-list shape also match."""
    rollout = tmp_path / "rollout.jsonl"
    rollout.write_text(
        json.dumps(
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"text": "the prompt body"}],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    adapter = CodexAdapter()

    assert adapter._rollout_matches_plan(rollout, _plan(tmp_path, "the prompt body")) is True
