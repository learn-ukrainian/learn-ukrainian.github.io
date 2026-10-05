"""Tests for scripts/pipeline/dispatch.py: model selection and fallback rules.

Operator rule (2026-09-22):
Flash High is the default for routine and deep; Pro is used ONLY when a caller
explicitly asks for it. Default calls must never reach Pro through fallback chains.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

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


def test_dispatch_gemini_explicit_pro_fails_with_supported_route():
    with pytest.raises(ValueError, match=r"delegate\.py dispatch --agent agy --model"):
        dispatch_gemini("test prompt", "task-explicit-pro", model="gemini-3.1-pro-high")


def test_fallback_chain_deduplicates_real_effective_agy_routes(monkeypatch):
    """Different model spellings resolving to the AGY pin are attempted once."""
    from scripts.pipeline import dispatch as dispatch_module

    monkeypatch.setattr(dispatch_module, "_flash_model", lambda: "gemini-3.8-flash-high")
    monkeypatch.setattr(dispatch_module, "_flash_lite_model", lambda: "gemini-3.0-flash-preview")
    attempts = []

    def fake_dispatch_raw(prompt, task_id, model=None, **kwargs):
        attempts.append(model)
        return False, "429 rate limit"

    # _effective_agy_route calls the production resolver; only transport is stubbed.
    with patch("scripts.pipeline.dispatch.dispatch_gemini_raw", side_effect=fake_dispatch_raw):
        ok, _ = dispatch_gemini("test prompt", "task-deduplicated-fallback")

    assert not ok
    assert attempts == ["gemini-3.8-flash-high"]


def test_dispatch_claude_phase_runs_without_background_work(monkeypatch, tmp_path):
    """The headless Claude phase call carries the #9690 controls from the adapter (#9750)."""
    from scripts.agent_runtime.adapters.claude import HEADLESS_BACKGROUND_ENV, HEADLESS_BACKGROUND_TOOL_DENIES
    from scripts.pipeline import dispatch as dispatch_module

    seen = {}

    def fake_run(cmd, **kwargs):
        seen.update(cmd=cmd, env=kwargs["env"])
        return subprocess.CompletedProcess(cmd, 0, stdout="===CONTENT_START===\nx\n===CONTENT_END===", stderr="")

    monkeypatch.setattr(dispatch_module, "run_with_heartbeat", fake_run)
    monkeypatch.setattr(dispatch_module, "supports_exclude_dynamic_system_prompt_sections", lambda _bin: False)
    prompt_file = tmp_path / "phase.md"
    prompt_file.write_text("write the content", encoding="utf-8")

    ok, _ = dispatch_module.dispatch_claude_phase(prompt_file, "B content")

    assert ok
    cmd = seen["cmd"]
    assert cmd[cmd.index("--disallowedTools") + 1].split(",") == list(HEADLESS_BACKGROUND_TOOL_DENIES)
    assert seen["env"].items() >= HEADLESS_BACKGROUND_ENV.items()
