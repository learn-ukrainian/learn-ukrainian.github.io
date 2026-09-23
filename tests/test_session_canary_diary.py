"""Diary dual-write helpers for Grok lane canary recovery."""

from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path

import pytest

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
        lambda repo, epic, override=None, preferred=None: handoff,
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


def test_resolve_handoff_path_default_order_unchanged(tmp_path: Path) -> None:
    epic_dir = tmp_path / ".claude" / "harness-epic"
    epic_dir.mkdir(parents=True)
    kimi = epic_dir / "KIMI-DRIVER-HANDOFF.md"
    claude = epic_dir / "CLAUDE-DRIVER-HANDOFF.md"
    kimi.write_text("KIMI handoff", encoding="utf-8")
    claude.write_text("CLAUDE handoff", encoding="utf-8")

    resolved = d.resolve_handoff_path(tmp_path, "harness")
    assert resolved == claude


def test_concurrent_edit_and_stamp_both_survive(tmp_path: Path) -> None:
    """A locked editor and a stamp cannot drop each other's bytes."""
    path = tmp_path / "CLAUDE-DRIVER-HANDOFF.md"
    path.write_text(
        "# Handoff\n\n**Last diary stamp:** never\n\n"
        "## Next Drive\n1. old\n\n"
        "## 📔 Diary — reverse chrono (newest first)\n\n",
        encoding="utf-8",
    )
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def editor() -> None:
        try:
            barrier.wait(timeout=5)
            d.rewrite_handoff_locked(path, lambda text: text + "\nEDITOR_SENTINEL\n")
        except Exception as exc:
            errors.append(exc)

    def stamper() -> None:
        try:
            barrier.wait(timeout=5)
            d.append_diary_stamp(
                path,
                title="canary score PASS",
                bullets=["STAMP_SENTINEL"],
                stamp="2026-09-23T00:00Z",
            )
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=editor), threading.Thread(target=stamper)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert errors == []
    assert all(not thread.is_alive() for thread in threads)
    text = path.read_text(encoding="utf-8")
    assert "EDITOR_SENTINEL" in text
    assert "STAMP_SENTINEL" in text


def _install_editor_on_first_skeleton_calls(
    monkeypatch: pytest.MonkeyPatch,
    path: Path,
    versions: list[str],
) -> dict[str, int]:
    """Atomically replace ``path`` from inside the read-modify-write transform."""
    real_ensure = d.ensure_diary_skeleton
    calls = {"n": 0}

    def _wrapped(text: str, **kwargs: object) -> str:
        calls["n"] += 1
        index = calls["n"] - 1
        if index < len(versions):
            editor = path.with_name(f".editor-{calls['n']}")
            editor.write_text(versions[index], encoding="utf-8")
            os.replace(editor, path)
        return real_ensure(text, **kwargs)

    monkeypatch.setattr(d, "ensure_diary_skeleton", _wrapped)
    return calls


def _write_original(path: Path) -> None:
    path.write_text(
        "# Handoff\n\n**Last diary stamp:** never\n\n"
        "ORIGINAL_SENTINEL\n\n"
        "## Next Drive\n1. old\n\n"
        "## Diary — reverse chrono (newest first)\n\n",
        encoding="utf-8",
    )


def _apply_stamp_or_handback(path: Path, kind: str) -> None:
    if kind == "stamp":
        d.append_diary_stamp(
            path,
            title="canary score PASS",
            bullets=["STAMP_SENTINEL"],
            stamp="2026-09-23T00:00Z",
        )
        return
    d.append_handback(
        path,
        epic="harness",
        stream_id="epic:4707",
        reason="clean end",
        pins=["pin"],
        open_prs=["none"],
        next_drive=["keep editor"],
        hands_off=["lane"],
        pending_user=["none"],
        worktrees=[".worktrees/dispatch/cursor/x"],
        canary_line="STAMP_SENTINEL",
        stamp="2026-09-23T00:00Z",
    )


@pytest.mark.parametrize("kind", ["stamp", "handback"])
def test_atomic_rename_between_read_and_write_keeps_editor_and_stamp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """An editor that replaces the path after the read is retried, not lost."""
    path = tmp_path / "CLAUDE-DRIVER-HANDOFF.md"
    _write_original(path)
    editor = (
        "# Handoff\n\n**Last diary stamp:** never\n\n"
        "EDITOR_SENTINEL\n\n"
        "## Next Drive\n1. from editor\n\n"
        "## Diary — reverse chrono (newest first)\n\n"
    )
    _install_editor_on_first_skeleton_calls(monkeypatch, path, [editor])

    _apply_stamp_or_handback(path, kind)

    text = path.read_text(encoding="utf-8")
    assert "EDITOR_SENTINEL" in text
    assert "STAMP_SENTINEL" in text
    assert "ORIGINAL_SENTINEL" not in text
    assert sorted(item.name for item in path.parent.iterdir()) == [path.name]


def test_editor_that_changes_every_attempt_raises_without_writing_stamp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exhausting the compare-and-replace bound leaves the editor's last bytes."""
    path = tmp_path / "CLAUDE-DRIVER-HANDOFF.md"
    _write_original(path)
    versions = [f"EDITOR_VERSION_{n}\n" for n in range(1, d.REWRITE_ATTEMPTS + 1)]
    calls = _install_editor_on_first_skeleton_calls(monkeypatch, path, versions)

    with pytest.raises(d.HandoffRewriteConflictError, match=re.escape(str(path))):
        d.append_diary_stamp(
            path,
            title="canary score PASS",
            bullets=["STAMP_SENTINEL"],
            stamp="2026-09-23T00:00Z",
        )

    assert calls["n"] == d.REWRITE_ATTEMPTS
    assert path.read_text(encoding="utf-8") == versions[-1]
    assert "STAMP_SENTINEL" not in path.read_text(encoding="utf-8")
    assert sorted(item.name for item in path.parent.iterdir()) == [path.name]


def test_resolve_handoff_path_glm_preferred(tmp_path: Path) -> None:
    epic_dir = tmp_path / ".claude" / "harness-epic"
    epic_dir.mkdir(parents=True)
    glm = epic_dir / "GLM-DRIVER-HANDOFF.md"
    claude = epic_dir / "CLAUDE-DRIVER-HANDOFF.md"
    glm.write_text("GLM handoff", encoding="utf-8")
    claude.write_text("CLAUDE handoff", encoding="utf-8")

    resolved = d.resolve_handoff_path(tmp_path, "harness", preferred=["GLM-DRIVER-HANDOFF.md"])
    assert resolved == glm
