"""Tests for ab ask-cursor bridge subcommand (Phase 1)."""

from unittest.mock import MagicMock, patch

import pytest

from scripts.ai_agent_bridge._cursor import CURSOR_DEFAULT_MODEL, _invoke_cursor


def test_cursor_default_model_is_auto():
    # Cursor's default model is "auto" so cursor-agent picks the best available
    # model from the user's plan without burning the per-model composer-2.5
    # quota. Pass `--model composer-2.5` explicitly only when you specifically
    # need that model (judge-calibration, A/B comparisons, etc.).
    assert CURSOR_DEFAULT_MODEL == "auto"


def test_invoke_cursor_constructs_correct_argv():
    """Cursor subprocess is invoked with -p PROMPT --model MODEL --output-format text --trust."""
    with patch("scripts.ai_agent_bridge._cursor.shutil.which", return_value="/fake/agent"):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="response body", stderr="")
            _invoke_cursor("hello", "composer-2.5")
            argv = run_mock.call_args[0][0]
            assert argv[0] == "/fake/agent"
            assert "-p" in argv
            assert "hello" in argv
            assert "--model" in argv
            assert "composer-2.5" in argv
            assert "--output-format" in argv
            assert "text" in argv
            assert "--trust" in argv


def test_invoke_cursor_falls_back_to_cursor_agent():
    """If 'agent' binary is missing, it should try 'cursor-agent'."""
    def which_side_effect(name):
        if name == "agent":
            return None
        if name == "cursor-agent":
            return "/fake/cursor-agent"
        return None

    with patch("scripts.ai_agent_bridge._cursor.shutil.which", side_effect=which_side_effect):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="response body", stderr="")
            _invoke_cursor("hello", "composer-2.5")
            argv = run_mock.call_args[0][0]
            assert argv[0] == "/fake/cursor-agent"


def test_invoke_cursor_attaches_data_file(tmp_path):
    data_file = tmp_path / "context.md"
    data_file.write_text("# Context\nSome content.")
    with patch("scripts.ai_agent_bridge._cursor.shutil.which", return_value="/fake/agent"):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            _invoke_cursor("review this", "composer-2.5", data=str(data_file))
            argv = run_mock.call_args[0][0]
            # data should be in the prompt, not as a separate flag
            prompt_arg = argv[argv.index("-p") + 1]
            assert "Some content." in prompt_arg
            assert "review this" in prompt_arg


def test_invoke_cursor_raises_when_binary_missing():
    with patch("scripts.ai_agent_bridge._cursor.shutil.which", return_value=None):
        with pytest.raises(SystemExit, match="cursor-agent CLI not found"):
            _invoke_cursor("hello", "composer-2.5")


def test_invoke_cursor_raises_on_nonzero_exit():
    with patch("scripts.ai_agent_bridge._cursor.shutil.which", return_value="/fake/agent"):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=1, stdout="", stderr="auth failed")
            with pytest.raises(SystemExit, match="cursor-agent exited 1"):
                _invoke_cursor("hello", "composer-2.5")


def test_invoke_cursor_strips_output():
    with patch("scripts.ai_agent_bridge._cursor.shutil.which", return_value="/fake/agent"):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="  response with spaces  \n", stderr="")
            result = _invoke_cursor("hello", "composer-2.5")
            assert result == "response with spaces"
