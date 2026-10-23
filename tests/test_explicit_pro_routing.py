"""Comprehensive tests for explicit Pro model preservation and Flash defaults.

Rule (operator 2026-09-22):
Flash High is the default for routine and deep; Pro is used ONLY when a caller
explicitly asks for it. An explicit --model / model= value must always win.
"""

from unittest.mock import MagicMock, patch

from scripts.ai_agent_bridge._acp_compat import resolve_compat_model
from scripts.batch.batch_otaman import dispatch_otaman


def test_resolve_compat_model_legacy_flash_maps_to_pin():
    """Compatibility aliases follow the pin; retired generations are refused (#9301)."""
    import pytest

    from agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    pin = ACPX_SUPPORTED_PARTICIPANTS["agy"]["model"]
    assert resolve_compat_model("gemini", "gemini-3-flash-preview") == pin
    assert resolve_compat_model("gemini", "gemini-3.0-flash-preview") == pin
    with pytest.raises(ValueError, match=r"gemini-3\.7-flash.*retired.*use gemini-3\.8-flash-high"):
        resolve_compat_model("gemini", "gemini-3.7-flash")
    assert resolve_compat_model("gemini", None) is None


def test_dispatch_otaman_default_and_explicit_model():
    """dispatch_otaman defaults to Flash High and respects explicit Pro model."""
    captured = []

    def fake_run(cmd, *args, **kwargs):
        captured.append(cmd)
        return MagicMock(returncode=0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        # Default call
        dispatch_otaman("a1", 1, "test-mod-default")
        # Explicit Pro call
        dispatch_otaman("a1", 2, "test-mod-pro", model="gemini-3.1-pro-high")

    assert len(captured) == 2
    # Check default uses gemini-3.8-flash-high
    cmd_default = captured[0]
    idx_default = cmd_default.index("--model")
    assert cmd_default[idx_default + 1] == "gemini-3.8-flash-high"

    # Check explicit Pro uses gemini-3.1-pro-high
    cmd_pro = captured[1]
    idx_pro = cmd_pro.index("--model")
    assert cmd_pro[idx_pro + 1] == "gemini-3.1-pro-high"
