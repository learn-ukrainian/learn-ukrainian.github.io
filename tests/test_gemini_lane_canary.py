"""Gemini canary control-flow tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.session_canary import gemini_lane


def _allowed_capsule() -> dict[str, object]:
    return {"execution_allowed": True}


def test_score_pass_hydrates_then_continues(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(gemini_lane, "_with_gemini_handoffs", lambda function, args: 0)
    monkeypatch.setattr(gemini_lane.shared_hydration, "build_hydration_capsule", lambda stream, lane: _allowed_capsule())

    assert gemini_lane.main(["score", "--epic", "harness", "--answers", "answers.json"]) == 0
    assert "hydration ready — continue" in capsys.readouterr().out


def test_score_fail_handoff_closes_exact_lease_and_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(gemini_lane, "_with_gemini_handoffs", lambda function, args: 2)
    monkeypatch.setattr(gemini_lane, "_close_exact_lease", lambda repo, epic: True)

    assert gemini_lane.main(["score", "--epic", "harness", "--answers", "answers.json"]) == 2
    assert "FAIL-HANDOFF — exact lease closed" in capsys.readouterr().out


def test_hydrate_refuses_to_continue_when_capsule_is_blocked(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        gemini_lane.shared_hydration,
        "build_hydration_capsule",
        lambda stream, lane: {"execution_allowed": False},
    )

    assert gemini_lane.main(["hydrate", "--epic", "harness"]) == 2
    assert "hydration blocked" in capsys.readouterr().err


def test_score_closes_lease_when_post_pass_hydration_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[tuple[object, str]] = []
    monkeypatch.setattr(gemini_lane, "_with_gemini_handoffs", lambda function, args: 0)
    monkeypatch.setattr(gemini_lane, "cmd_hydrate", lambda args: 2)
    monkeypatch.setattr(gemini_lane, "_close_exact_lease", lambda repo, epic: closed.append((repo, epic)) or True)

    assert gemini_lane.main(["score", "--epic", "harness", "--answers", "answers.json"]) == 2
    assert closed and closed[0][1] == "harness"


def test_lease_environment_parser_accepts_launcher_quotes(tmp_path: Path) -> None:
    env_path = tmp_path / "session-lease.env"
    env_path.write_text(
        "export SESSION_STREAM_PROCESS_ID=\"1234\"\n"
        "export SESSION_STREAM_GENERATION='2'\n"
        "unrelated=value\n",
        encoding="utf-8",
    )

    assert gemini_lane._read_lease_environment(env_path) == {
        "SESSION_STREAM_PROCESS_ID": "1234",
        "SESSION_STREAM_GENERATION": "2",
    }


def test_bootstrap_uses_normalized_epic_for_default_stream_id(tmp_path: Path) -> None:
    assert gemini_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", " HARNESS "]) == 0

    board = (tmp_path / ".claude" / "harness-epic" / "GEMINI-COLD-START.md").read_text(encoding="utf-8")
    assert "**Stream:** `epic:4707`" in board
