"""Tests for ab ask-opencode bridge subcommand (PR-D1)."""

from unittest.mock import MagicMock, patch

import pytest

from scripts.ai_agent_bridge._opencode import OPENCODE_DEFAULT_MODEL, _invoke_opencode


def test_opencode_default_model_is_cheap_and_guard_allowed():
    from scripts.ai_agent_bridge.routing_guard import assert_model_routing_allowed

    assert OPENCODE_DEFAULT_MODEL == "openrouter/google/gemma-4-31b-it"
    assert_model_routing_allowed(OPENCODE_DEFAULT_MODEL, context="default-model test")


def test_invoke_opencode_constructs_correct_argv():
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value="/fake/opencode"):
        with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="response", stderr="")
            _invoke_opencode("hello", "openrouter/google/gemma-4-31b-it")
            argv = run_mock.call_args[0][0]
            assert argv[0] == "/fake/opencode"
            assert argv[1] == "run"
            assert "--model" in argv
            assert "openrouter/google/gemma-4-31b-it" in argv
            assert "hello" in argv


def test_invoke_opencode_attaches_file(tmp_path):
    data_file = tmp_path / "report.html"
    data_file.write_text("<html><body>data</body></html>")
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value="/fake/opencode"):
        with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            _invoke_opencode("review", "openrouter/google/gemma-4-31b-it", data=str(data_file))
            argv = run_mock.call_args[0][0]
            assert "--file" in argv
            # file path is in argv right after --file
            file_idx = argv.index("--file")
            assert str(data_file.resolve()) == argv[file_idx + 1]
            assert argv[file_idx + 2] == "--"


def test_invoke_opencode_raises_when_binary_missing():
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value=None):
        with pytest.raises(SystemExit, match="opencode CLI not found"):
            _invoke_opencode("hello", "openrouter/google/gemma-4-31b-it")
