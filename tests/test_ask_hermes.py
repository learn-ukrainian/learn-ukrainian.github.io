"""Tests for ab ask-hermes bridge subcommand (PR-D1)."""

from unittest.mock import MagicMock, patch

import pytest

from scripts.ai_agent_bridge._hermes import HERMES_DEFAULT_MODEL, _invoke_hermes


def test_hermes_default_model_is_qwen_plus():
    assert HERMES_DEFAULT_MODEL == "qwen/qwen3.6-plus"


def test_invoke_hermes_constructs_correct_argv(tmp_path):
    """Hermes subprocess is invoked with -z PROMPT -m MODEL."""
    with patch("scripts.ai_agent_bridge._hermes.shutil.which", return_value="/fake/hermes"):
        with patch("scripts.ai_agent_bridge._hermes.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="response body", stderr="")
            _invoke_hermes("hello", "qwen/qwen3.6-plus")
            argv = run_mock.call_args[0][0]
            assert argv[0] == "/fake/hermes"
            assert "-z" in argv
            assert "hello" in argv
            assert "-m" in argv
            assert "qwen/qwen3.6-plus" in argv


def test_invoke_hermes_attaches_data_file(tmp_path):
    data_file = tmp_path / "context.md"
    data_file.write_text("# Context\nSome content.")
    with patch("scripts.ai_agent_bridge._hermes.shutil.which", return_value="/fake/hermes"):
        with patch("scripts.ai_agent_bridge._hermes.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            _invoke_hermes("review this", "qwen/qwen3.6-plus", data=str(data_file))
            argv = run_mock.call_args[0][0]
            # data should be in the prompt, not as a separate flag
            prompt_arg = argv[argv.index("-z") + 1]
            assert "Some content." in prompt_arg
            assert "review this" in prompt_arg


def test_invoke_hermes_raises_when_binary_missing():
    with patch("scripts.ai_agent_bridge._hermes.shutil.which", return_value=None):
        with pytest.raises(SystemExit, match="hermes CLI not found"):
            _invoke_hermes("hello", "qwen/qwen3.6-plus")


def test_invoke_hermes_raises_on_nonzero_exit():
    with patch("scripts.ai_agent_bridge._hermes.shutil.which", return_value="/fake/hermes"):
        with patch("scripts.ai_agent_bridge._hermes.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=1, stdout="", stderr="auth failed")
            with pytest.raises(SystemExit, match="hermes exited 1"):
                _invoke_hermes("hello", "qwen/qwen3.6-plus")
