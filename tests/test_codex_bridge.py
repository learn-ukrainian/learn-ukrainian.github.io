"""Focused tests for Codex bridge behavior."""

from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_agent_bridge._cli import _handle_ask_codex
from ai_agent_bridge._codex import _build_codex_exec_cmd, _build_codex_resume_cmd, _codex_bridge_flags
from ai_agent_bridge._messaging import detect_sender


def test_detect_sender_codex():
    env = {k: v for k, v in os.environ.items() if k not in ("GEMINI_SESSION", "GOOGLE_API_KEY", "CLAUDE_PROJECT_DIR", "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS")}
    with patch.dict(os.environ, {**env, "CODEX_SESSION": "1"}, clear=True), \
         patch("ai_agent_bridge._messaging.Path.exists", return_value=False):
        assert detect_sender() == "codex"


def test_detect_sender_claude_beats_codex_session():
    with patch.dict(os.environ, {"CODEX_SESSION": "1", "CLAUDE_PROJECT_DIR": "/tmp/project"}, clear=True):
        assert detect_sender() == "claude"


def test_detect_sender_gemini_beats_codex_session():
    with patch.dict(os.environ, {"CODEX_SESSION": "1", "GEMINI_SESSION": "1"}, clear=True):
        assert detect_sender() == "gemini"


def test_handle_ask_codex_reads_stdin():
    args = argparse.Namespace(
        content="-",
        task_id="issue-1177",
        type="query",
        data=None,
        new_session=False,
        from_llm="gemini",
        from_model=None,
        to_model=None,
    )
    with patch("ai_agent_bridge._cli.ask_codex") as ask_codex_mock, \
         patch("sys.stdin", io.StringIO("stdin prompt")):
        _handle_ask_codex(args)
    ask_codex_mock.assert_called_once()
    assert ask_codex_mock.call_args[0][0] == "stdin prompt"


def test_codex_bridge_flags_invalid_mode_falls_back_safe():
    with patch.dict(os.environ, {"CODEX_BRIDGE_MODE": "weird"}, clear=True):
        assert _codex_bridge_flags() == ["-s", "read-only"]


def test_build_codex_exec_cmd_uses_stdin_prompt(tmp_path):
    cmd = _build_codex_exec_cmd(tmp_path / "out.txt", "gpt-5.4")
    assert Path(cmd[0]).name == "codex"
    assert cmd[1] == "exec"
    assert cmd[-1] == "-"
    assert "-C" in cmd
    assert "-m" in cmd


def test_build_codex_resume_cmd_safe_falls_back_to_exec(tmp_path):
    with patch.dict(os.environ, {"CODEX_BRIDGE_MODE": "safe"}, clear=True):
        cmd = _build_codex_resume_cmd("session-123", tmp_path / "out.txt", "gpt-5.4")
    assert Path(cmd[0]).name == "codex"
    assert cmd[1] == "exec"
    assert "resume" not in cmd
    assert cmd[-1] == "-"
