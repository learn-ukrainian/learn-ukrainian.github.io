"""Tests for ab ask-cursor bridge subcommand (Phase 1)."""

from unittest.mock import MagicMock, patch

import pytest

from scripts.agent_runtime.adapters.cursor import CursorAgentMissingError
from scripts.ai_agent_bridge import _cursor
from scripts.ai_agent_bridge._cursor import _invoke_cursor, cursor_default_model
from scripts.lib import rules_core

_RESOLVE = "scripts.ai_agent_bridge._cursor.resolve_cursor_agent_binary"
_CURSOR_BIN = "/usr/local/bin/cursor-agent"


def test_cursor_default_model_is_the_concrete_seat_pin():
    # A bridge ask is not a coding dispatch, so it never runs Auto (#9274): the
    # default is the catalog's concrete Cursor seat pin.
    assert cursor_default_model() == "grok-4.7"


@pytest.mark.parametrize(
    ("model", "code"),
    [
        (None, "cursor_model_unpinned"),
        ("", "cursor_model_unpinned"),
        ("auto", "cursor_auto_outside_coding_task"),
        ("AUTO", "cursor_auto_outside_coding_task"),
        ("cursor/auto", "cursor_auto_outside_coding_task"),
        ("grok-4.7-fast", "cursor_model_not_approved"),
        ("grok-4.6", "cursor_model_not_approved"),
    ],
)
def test_invoke_cursor_refuses_non_pinned_models_before_spawn(model, code):
    with patch("shutil.which", side_effect=AssertionError("resolved the binary before refusing")):
        with patch("subprocess.run", side_effect=AssertionError("spawned before refusing")):
            with pytest.raises(SystemExit, match=rf"ask-cursor: refused: .*\({code}\)"):
                _invoke_cursor("hello", model)


def test_ask_cursor_refuses_explicit_auto_before_any_send(monkeypatch):
    calls: list[str] = []
    for name in ("send_message", "register_ask", "launch_background_ask", "_invoke_cursor"):
        monkeypatch.setattr(_cursor, name, lambda *_a, _n=name, **_k: calls.append(_n))
    for kwargs in ({"model": "auto"}, {"to_model": "Auto"}):
        with pytest.raises(SystemExit, match=r"\(cursor_auto_outside_coding_task\)"):
            _cursor.ask_cursor("hello", "t-9274", msg_type="review", **kwargs)
    assert calls == []


def test_ask_cursor_defaults_to_the_concrete_seat_pin(monkeypatch):
    sent: list[dict] = []
    invoked: list[str] = []
    monkeypatch.setattr(_cursor, "send_message", lambda *a, **k: sent.append(k) or len(sent))
    monkeypatch.setattr(_cursor, "register_ask", lambda *_a, **_k: None)
    monkeypatch.setattr(_cursor, "acknowledge", lambda *_a, **_k: None)
    monkeypatch.setattr(_cursor, "record_ask_reply", lambda *_a, **_k: None)
    monkeypatch.setattr(_cursor, "_invoke_cursor", lambda _c, model, **_k: invoked.append(model) or "ok")

    _cursor.ask_cursor("hello", "t-9274")

    assert invoked == ["grok-4.7"]
    assert sent[0]["to_model"] == "grok-4.7"


def test_invoke_cursor_constructs_correct_argv():
    """Cursor subprocess is invoked with -p PROMPT --model MODEL --output-format text --trust."""
    with patch(_RESOLVE, return_value=_CURSOR_BIN):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="response body", stderr="")
            _invoke_cursor("hello", "composer-2.5")
            argv = run_mock.call_args[0][0]
            assert argv[0] == _CURSOR_BIN
            assert "-p" in argv
            assert argv[argv.index("-p") + 1] == rules_core.with_core("hello")
            assert "--model" in argv
            assert "composer-2.5" in argv
            assert "--output-format" in argv
            assert "text" in argv
            assert "--trust" in argv


def test_invoke_cursor_uses_resolved_cursor_agent():
    """The ask path spawns whatever ``resolve_cursor_agent_binary`` returns."""
    with patch(_RESOLVE, return_value=_CURSOR_BIN) as resolve:
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="response body", stderr="")
            _invoke_cursor("hello", "composer-2.5")
            resolve.assert_called_once_with()
            argv = run_mock.call_args[0][0]
            assert argv[0] == _CURSOR_BIN


def test_invoke_cursor_attaches_data_file(tmp_path):
    data_file = tmp_path / "context.md"
    data_file.write_text("# Context\nSome content.")
    with patch(_RESOLVE, return_value=_CURSOR_BIN):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            _invoke_cursor("review this", "composer-2.5", data=str(data_file))
            argv = run_mock.call_args[0][0]
            # data should be in the prompt, not as a separate flag
            prompt_arg = argv[argv.index("-p") + 1]
            assert "Some content." in prompt_arg
            assert "review this" in prompt_arg


def test_invoke_cursor_raises_when_binary_missing():
    with patch(_RESOLVE, side_effect=CursorAgentMissingError()):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run", side_effect=AssertionError("spawned")):
            with pytest.raises(CursorAgentMissingError, match="cursor-agent"):
                _invoke_cursor("hello", "composer-2.5")


def test_invoke_cursor_raises_on_nonzero_exit():
    with patch(_RESOLVE, return_value=_CURSOR_BIN):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=1, stdout="", stderr="auth failed")
            with pytest.raises(SystemExit, match="cursor-agent exited 1"):
                _invoke_cursor("hello", "composer-2.5")


def test_invoke_cursor_strips_output():
    with patch(_RESOLVE, return_value=_CURSOR_BIN):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="  response with spaces  \n", stderr="")
            result = _invoke_cursor("hello", "composer-2.5")
            assert result == "response with spaces"
