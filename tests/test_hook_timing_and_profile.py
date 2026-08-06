"""Tests for hook timing logger and Grok hook profile applicator."""

from __future__ import annotations

import json
import os
from pathlib import Path

from scripts.hooks.apply_grok_hook_profile import ensure_compat_claude_hooks_false
from scripts.hooks.hook_timing import append_row, main as timing_main


def test_append_row_force(tmp_path: Path, monkeypatch) -> None:
    log = tmp_path / "t.jsonl"
    monkeypatch.delenv("HOOK_TIMING", raising=False)
    append_row({"event": "PreToolUse", "ms": 12.5, "rc": 0}, path=log, force=True)
    lines = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["event"] == "PreToolUse"
    assert row["ms"] == 12.5
    assert "ts" in row


def test_timing_log_cli(tmp_path: Path, monkeypatch) -> None:
    log = tmp_path / "cli.jsonl"
    monkeypatch.setenv("HOOK_TIMING_LOG", str(log))
    assert (
        timing_main(
            ["log", "--event", "SessionStart", "--ms", "100.5", "--rc", "0", "--command", "x"]
        )
        == 0
    )
    row = json.loads(log.read_text(encoding="utf-8").strip())
    assert row["event"] == "SessionStart"
    assert row["ms"] == 100.5


def test_ensure_compat_appends() -> None:
    text, changed = ensure_compat_claude_hooks_false("")
    assert changed
    assert "[compat.claude]" in text
    assert "hooks = false" in text


def test_ensure_compat_idempotent() -> None:
    base = "[compat.claude]\nhooks = false\n"
    text, changed = ensure_compat_claude_hooks_false(base)
    assert changed is False
    assert text == base


def test_ensure_compat_idempotent_with_inline_comment() -> None:
    """Trailing inline comments must not trigger a second hooks key (CF F1)."""
    base = "[compat.claude]\nhooks = false  # operator note\n"
    text, changed = ensure_compat_claude_hooks_false(base)
    assert changed is False
    assert text == base
    assert text.count("hooks") == 1


def test_ensure_compat_flips_true() -> None:
    base = "[models]\ndefault = \"grok-4.5\"\n\n[compat.claude]\nhooks = true\n"
    text, changed = ensure_compat_claude_hooks_false(base)
    assert changed
    assert "hooks = false" in text
    assert "hooks = true" not in text


def test_ensure_compat_flips_true_keeps_inline_comment() -> None:
    base = "[compat.claude]\nhooks = true  # was on\n"
    text, changed = ensure_compat_claude_hooks_false(base)
    assert changed
    assert "hooks = false" in text
    assert "hooks = true" not in text
    assert text.count("hooks") == 1
    assert "# was on" in text
