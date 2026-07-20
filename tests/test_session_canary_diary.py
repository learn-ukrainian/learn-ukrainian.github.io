"""Diary dual-write helpers for Grok lane canary recovery."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.session_canary import diary as d
from scripts.session_canary import grok_lane as gl


def test_append_diary_stamp_and_next_drive(tmp_path: Path) -> None:
    path = tmp_path / "INTERIM-DRIVER-HANDOFF.md"
    d.append_diary_stamp(
        path,
        title="merged PR",
        bullets=["#5532 MERGED", "scorecard on /api/rules"],
        next_drive=["Dispatch Terra B1", "Start Grok PR-C"],
        stamp="2026-07-20T12:00Z",
    )
    text = path.read_text(encoding="utf-8")
    assert "**Last diary stamp:** 2026-07-20T12:00Z" in text
    assert "### 2026-07-20T12:00Z — merged PR" in text
    assert "#5532 MERGED" in text
    assert "## Next Drive" in text
    assert "1. Dispatch Terra B1" in text
    assert "2. Start Grok PR-C" in text
    assert "No secrets" in text


def test_handback_block_and_next_drive(tmp_path: Path) -> None:
    path = tmp_path / "CLAUDE-DRIVER-HANDOFF.md"
    d.append_handback(
        path,
        epic="harness",
        stream_id="epic:4707",
        reason="canary FAIL-HANDOFF",
        pins=["Sol SHIP binding"],
        open_prs=["none"],
        next_drive=["Load handback", "Mint canary"],
        hands_off=["Atlas #5496"],
        pending_user=["lift hold"],
        worktrees=[".worktrees/dispatch/grok/x"],
        canary_line="canary FAIL-HANDOFF 7/10 @ ~300000 tok",
        stamp="2026-07-20T13:00Z",
    )
    text = path.read_text(encoding="utf-8")
    assert "## STATE AT HANDBACK — 2026-07-20T13:00Z" in text
    assert "canary FAIL-HANDOFF 7/10" in text
    assert "1. Load handback" in text
    assert "### 2026-07-20T13:00Z — STATE AT HANDBACK" in text
    assert "Successor: load this block" in text


def test_format_canary_score_line() -> None:
    line = d.format_canary_score_line(
        verdict="PASS",
        score_line="SCORE 9/10 pass_ratio=0.8",
        context_tokens=250_000,
        pass_ratio=0.8,
    )
    assert "PASS" in line
    assert "9/10" in line
    assert "250000" in line


def test_stamp_cli(tmp_path: Path) -> None:
    handoff = tmp_path / "INTERIM-DRIVER-HANDOFF.md"
    # epic dir layout not required — pass --handoff
    rc = gl.main(
        [
            "--repo",
            str(tmp_path),
            "stamp",
            "--epic",
            "harness",
            "--handoff",
            str(handoff),
            "--title",
            "batch",
            "--bullet",
            "did X",
            "--next",
            "do Y",
        ]
    )
    assert rc == 0
    text = handoff.read_text(encoding="utf-8")
    assert "did X" in text
    assert "1. do Y" in text


def test_handback_cli(tmp_path: Path) -> None:
    handoff = tmp_path / "INTERIM-DRIVER-HANDOFF.md"
    rc = gl.main(
        [
            "--repo",
            str(tmp_path),
            "handback",
            "--epic",
            "harness",
            "--stream",
            "epic:4707",
            "--handoff",
            str(handoff),
            "--reason",
            "clean end",
            "--next",
            "resume B1",
            "--canary-line",
            "canary PASS 10/10 @ ~100k tok",
        ]
    )
    assert rc == 0
    text = handoff.read_text(encoding="utf-8")
    assert "STATE AT HANDBACK" in text
    assert "clean end" in text
    assert "resume B1" in text


def test_score_fail_writes_handback(tmp_path: Path, monkeypatch) -> None:
    """score FAIL path should write STATE AT HANDBACK even if context_canary is mocked."""
    canary = tmp_path / "canary"
    canary.mkdir()
    (canary / "probe.json").write_text("{}", encoding="utf-8")
    answers = canary / "answers.json"
    answers.write_text("{}", encoding="utf-8")
    handoff = tmp_path / "INTERIM-DRIVER-HANDOFF.md"
    handoff.write_text("## Next Drive\n1. x\n## Hands-off\n- y\n", encoding="utf-8")

    class FakeProc:
        returncode = 2
        stdout = "SCORE 6/10 (failed)\n"
        stderr = ""

    monkeypatch.setattr(gl.subprocess, "run", lambda *a, **k: FakeProc())
    monkeypatch.setattr(
        "scripts.session_canary.diary.resolve_handoff_path",
        lambda repo, epic, override=None: handoff,
    )
    rc = gl.main(
        [
            "--repo",
            str(tmp_path),
            "score",
            "--epic",
            "harness",
            "--out-dir",
            str(canary),
            "--answers",
            str(answers),
            "--context-tokens",
            "999",
            "--handoff",
            str(handoff),
            "--next-drive",
            "Load handback; mint",
        ]
    )
    assert rc == 2
    text = handoff.read_text(encoding="utf-8")
    assert "STATE AT HANDBACK" in text
    assert "FAIL-HANDOFF" in text or "canary" in text.lower()
    verdict = json.loads((canary / "last_verdict.json").read_text(encoding="utf-8"))
    assert verdict["verdict"] == "FAIL-HANDOFF"
