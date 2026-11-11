"""Tests for ab ask-cursor bridge subcommand (Phase 1)."""

import json
import re
import sys
from unittest.mock import MagicMock, patch

import pytest

from scripts.agent_runtime.adapters.cursor import CursorAgentMissingError
from scripts.ai_agent_bridge import _cursor
from scripts.ai_agent_bridge._cursor import _invoke_cursor
from scripts.lib import rules_core

_RESOLVE = "scripts.ai_agent_bridge._cursor.resolve_cursor_agent_binary"
_CURSOR_BIN = "/usr/local/bin/cursor-agent"
# Cursor has no approved model pin while Grok is retired (GROK-CANCEL-1110). Bridge mechanism
# tests install this stand-in as the only approved pin.
STAND_IN_PIN = "stand-in-cursor-pin-high"


@pytest.fixture
def stand_in_pin(monkeypatch):
    monkeypatch.setattr("scripts.review.model_catalog.CURSOR_APPROVED_WIRE_PINS", frozenset({STAND_IN_PIN}))
    monkeypatch.setattr("scripts.review.model_catalog.cursor_pinned_models", lambda catalog=None: (STAND_IN_PIN,))
    return STAND_IN_PIN


@pytest.mark.parametrize(
    ("model", "code"),
    [
        (None, "cursor_model_unpinned"),
        ("", "cursor_model_unpinned"),
        ("auto", "cursor_auto_outside_coding_task"),
        ("AUTO", "cursor_auto_outside_coding_task"),
        ("cursor/auto", "cursor_auto_outside_coding_task"),
        ("grok-4.7-fast", "CURSOR_MODEL_NOT_APPROVED"),
        ("grok-4.7", "CURSOR_MODEL_NOT_APPROVED"),
        ("grok-4.7-high", "CURSOR_MODEL_NOT_APPROVED"),
        ("grok-4.6", "CURSOR_MODEL_NOT_APPROVED"),
    ],
)
def test_invoke_cursor_refuses_non_pinned_models_before_spawn(model, code, stand_in_pin):
    with patch("shutil.which", side_effect=AssertionError("resolved the binary before refusing")):
        with patch("subprocess.run", side_effect=AssertionError("spawned before refusing")):
            with pytest.raises(SystemExit, match=rf"ask-cursor: refused: .*{code}.*"):
                _invoke_cursor("hello", model)


def test_ask_cursor_refuses_explicit_auto_before_any_send(monkeypatch, stand_in_pin):
    calls: list[str] = []
    for name in ("send_message", "register_ask", "launch_background_ask", "_invoke_cursor"):
        monkeypatch.setattr(_cursor, name, lambda *_a, _n=name, **_k: calls.append(_n))
    for kwargs in ({"model": "auto"}, {"to_model": "Auto"}):
        with pytest.raises(SystemExit, match=r"\(cursor_auto_outside_coding_task\)"):
            _cursor.ask_cursor("hello", "t-9274", msg_type="review", **kwargs)
    assert calls == []
    # With the real catalog there is no approved Cursor pin (GROK-CANCEL-1110): every ask is refused.
    monkeypatch.undo()
    for name in ("send_message", "register_ask", "launch_background_ask", "_invoke_cursor"):
        monkeypatch.setattr(_cursor, name, lambda *_a, _n=name, **_k: calls.append(_n))
    for kwargs in ({}, {"model": "grok-4.7-high"}, {"model": "auto"}):
        with pytest.raises(SystemExit, match=r"\(cursor_no_approved_model_pin\)"):
            _cursor.ask_cursor("hello", "t-9274", msg_type="review", **kwargs)
    assert calls == []


def test_invoke_cursor_constructs_correct_argv(stand_in_pin):
    """Print mode receives the prepared prompt on stdin without a positional."""
    with patch(_RESOLVE, return_value=_CURSOR_BIN):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="response body", stderr="")
            _invoke_cursor("hello", stand_in_pin)
            argv = run_mock.call_args[0][0]
            assert argv[0] == _CURSOR_BIN
            assert "-p" in argv
            assert argv[argv.index("-p") + 1] == "--model"
            assert run_mock.call_args.kwargs["input"] == rules_core.with_core("hello")
            assert "--model" in argv
            assert stand_in_pin in argv
            assert "--output-format" in argv
            assert "text" in argv
            assert "--trust" in argv


def test_invoke_cursor_attaches_data_file(tmp_path, stand_in_pin):
    data_file = tmp_path / "context.md"
    data_file.write_text("# Context\nSome content.")
    with patch(_RESOLVE, return_value=_CURSOR_BIN):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            _invoke_cursor("review this", stand_in_pin, data=str(data_file))
            argv = run_mock.call_args[0][0]
            # data should be in the prompt, not as a separate flag
            prompt_input = run_mock.call_args.kwargs["input"]
            assert "Some content." in prompt_input
            assert "review this" in prompt_input
            assert prompt_input not in argv


def test_large_prepared_prompt_avoids_e2big_and_reaches_non_tty_stdin(tmp_path, stand_in_pin):
    """A real child receives every byte of a >128 KiB prompt, including attached data."""
    binary = tmp_path / "cursor-agent"
    binary.write_text(
        f"#!{sys.executable}\nimport json, sys\n"
        f"assert sys.argv[1:] == ['-p', '--model', '{STAND_IN_PIN}', '--output-format', 'text', '--trust']\n"
        "print(json.dumps([sys.stdin.isatty(), sys.stdin.read()]))\n"
    )
    binary.chmod(0o700)
    data = tmp_path / "context.md"
    attached = "large transport payload\n" * 7000 + "END-12852"
    data.write_text(attached)
    expected = rules_core.with_core(f"- review\n\n## Attached data: context.md\n\n```\n{attached}\n```")
    assert len(expected.encode("utf-8")) > 128 * 1024
    with patch(_RESOLVE, return_value=str(binary)):
        result = _invoke_cursor("- review", stand_in_pin, data=str(data))
    assert json.loads(result) == [False, expected]


def test_invoke_cursor_raises_when_binary_missing(stand_in_pin):
    with patch(_RESOLVE, side_effect=CursorAgentMissingError()):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run", side_effect=AssertionError("spawned")):
            with pytest.raises(CursorAgentMissingError, match="cursor-agent"):
                _invoke_cursor("hello", stand_in_pin)


def test_invoke_cursor_raises_on_nonzero_exit(stand_in_pin):
    with patch(_RESOLVE, return_value=_CURSOR_BIN):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=1, stdout="", stderr="auth failed")
            with pytest.raises(SystemExit, match="cursor-agent exited 1"):
                _invoke_cursor("hello", stand_in_pin)

def test_ask_cursor_regression_wire_normalization(monkeypatch, stand_in_pin):
    sent = []
    invoked = []
    monkeypatch.setattr(_cursor, "send_message", lambda *a, **k: sent.append(k) or len(sent))
    monkeypatch.setattr(_cursor, "register_ask", lambda *_a, **_k: None)
    monkeypatch.setattr(_cursor, "acknowledge", lambda *_a, **_k: None)
    monkeypatch.setattr(_cursor, "record_ask_reply", lambda *_a, **_k: None)

    # Mock the subprocess inside _invoke_cursor
    with patch(_RESOLVE, return_value=_CURSOR_BIN):
        with patch("scripts.ai_agent_bridge._cursor.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

            for m in [None, stand_in_pin]:
                run_mock.reset_mock()
                _cursor.ask_cursor("hello", "t-9274", model=m)
                argv = run_mock.call_args[0][0]
                model_idx = argv.index("--model")
                assert argv[model_idx + 1] == stand_in_pin

    # Refusals
    with patch("scripts.agent_runtime.adapters.claude._default_claude_bin", return_value="/bin/claude"):
        # Grok is retired (GROK-CANCEL-1110): the ask's model selection refuses every Grok id and variant.
        for m in ("grok-4.7", "grok-4.7-high", "grok-4.7[fast=false]", "grok-4.7-low", "grok-4.7-medium",
                  "grok-4.7-xhigh"):
            with pytest.raises(ValueError, match=rf"model '{re.escape(m)}' is retired in the model catalog"):
                _cursor.ask_cursor("hello", "t-9274", model=m)
        for m, code in [
            ("opus", "CURSOR_CLAUDE_REFUSED"),
            ("sonnet", "CURSOR_CLAUDE_REFUSED"),
        ]:
            with pytest.raises(SystemExit, match=rf"ask-cursor: refused: {code}"):
                _cursor.ask_cursor("hello", "t-9274", model=m)
