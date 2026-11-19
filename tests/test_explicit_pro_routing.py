"""Explicit model preservation and the catalog default for the Otaman dispatch.

The default is the review seat the installed catalog assigns (the AGY ACP pin);
an explicit --model / model= value must always win.
"""

from unittest.mock import MagicMock, patch

from lu_machinery.agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

from scripts.batch.batch_otaman import dispatch_otaman


def test_dispatch_otaman_default_and_explicit_model():
    """dispatch_otaman defaults to the catalog review seat and respects an explicit model."""
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
    # The default is the AGY ACP participant pin, the only model the ask-gemini bridge admits
    cmd_default = captured[0]
    idx_default = cmd_default.index("--model")
    assert cmd_default[idx_default + 1] == ACPX_SUPPORTED_PARTICIPANTS["agy"]["model"]

    # Check explicit Pro uses gemini-3.1-pro-high
    cmd_pro = captured[1]
    idx_pro = cmd_pro.index("--model")
    assert cmd_pro[idx_pro + 1] == "gemini-3.1-pro-high"
