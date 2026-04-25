from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_llm.fallback import CallResult
from wiki.compiler import _call_writer


def _call_result() -> CallResult:
    return CallResult(
        response_text="ok",
        model_used="model",
        auth_mode_used=None,
        elapsed_s=1.0,
    )


def test_call_writer_routes_gemini_to_call_gemini():
    with patch(
        "wiki.compiler.call_gemini_with_fallback",
        return_value=_call_result(),
    ) as call:
        result = _call_writer("prompt", writer="gemini")

    assert result.response_text == "ok"
    call.assert_called_once()


def test_call_writer_routes_claude_to_call_claude():
    with patch(
        "wiki.compiler.call_claude_with_fallback",
        return_value=_call_result(),
    ) as call:
        result = _call_writer("prompt", writer="claude")

    assert result.response_text == "ok"
    call.assert_called_once()


def test_call_writer_routes_gpt55_to_call_codex():
    with patch(
        "wiki.compiler.call_codex_with_fallback",
        return_value=_call_result(),
    ) as call:
        result = _call_writer("prompt", writer="gpt-5.5")

    assert result.response_text == "ok"
    call.assert_called_once()


def test_call_writer_rejects_unknown_writer():
    with pytest.raises(ValueError, match="Unknown writer"):
        _call_writer("prompt", writer="bogus")
