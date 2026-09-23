"""Tests for scripts/pipeline/dispatch.py: model selection and fallback rules.

Operator rule (2026-09-22):
Flash High is the default for routine and deep; Pro is used ONLY when a caller
explicitly asks for it. Default calls must never reach Pro through fallback chains.
"""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.pipeline.dispatch import dispatch_gemini


def test_dispatch_gemini_default_never_reaches_pro_on_rate_limit():
    """Default dispatch (model=None) must never attempt Pro when Flash rungs are rate-limited."""
    attempts = []

    def fake_dispatch_raw(prompt, task_id, model=None, **kwargs):
        attempts.append(model)
        return False, "429 Resource has been exhausted (e.g. check quota)."

    with patch("scripts.pipeline.dispatch.dispatch_gemini_raw", side_effect=fake_dispatch_raw):
        ok, _ = dispatch_gemini("test prompt", "task-default-rl")

    assert ok is False
    assert len(attempts) >= 1
    # Verify the initial model was Flash
    assert "flash" in attempts[0].lower()
    # Verify no attempted model was Pro
    for attempted in attempts:
        assert "pro" not in attempted.lower(), f"Pro model {attempted!r} was attempted in default fallback chain"


def test_dispatch_gemini_default_never_reaches_pro_on_timeout():
    """Default dispatch (model=None) must never attempt Pro when Flash rungs time out / hang."""
    attempts = []

    def fake_dispatch_raw(prompt, task_id, model=None, **kwargs):
        attempts.append(model)
        return False, ""

    with patch("scripts.pipeline.dispatch.dispatch_gemini_raw", side_effect=fake_dispatch_raw):
        ok, _ = dispatch_gemini("test prompt", "task-default-timeout")


    assert ok is False
    assert len(attempts) >= 1
    assert "flash" in attempts[0].lower()
    for attempted in attempts:
        assert "pro" not in attempted.lower(), f"Pro model {attempted!r} was attempted in default fallback chain"


def test_dispatch_gemini_explicit_pro_uses_pro():
    """Explicit Pro request (model='gemini-3.1-pro-high') uses Pro on initial dispatch."""
    attempts = []

    def fake_dispatch_raw(prompt, task_id, model=None, **kwargs):
        attempts.append(model)
        return True, "pro response"

    with patch("scripts.pipeline.dispatch.dispatch_gemini_raw", side_effect=fake_dispatch_raw):
        ok, output = dispatch_gemini("test prompt", "task-explicit-pro", model="gemini-3.1-pro-high")

    assert ok is True
    assert output == "pro response"
    assert len(attempts) == 1
    assert attempts[0] == "gemini-3.1-pro-high"


def test_dispatch_gemini_explicit_pro_preview_uses_pro():
    """Explicit Pro request with legacy preview slug uses Pro on initial dispatch."""
    attempts = []

    def fake_dispatch_raw(prompt, task_id, model=None, **kwargs):
        attempts.append(model)
        return True, "pro preview response"

    with patch("scripts.pipeline.dispatch.dispatch_gemini_raw", side_effect=fake_dispatch_raw):
        ok, output = dispatch_gemini("test prompt", "task-explicit-pro-prev", model="gemini-3.1-pro-preview")

    assert ok is True
    assert output == "pro preview response"
    assert len(attempts) == 1
    assert attempts[0] == "gemini-3.1-pro-preview"
