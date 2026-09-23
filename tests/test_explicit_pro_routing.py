"""Comprehensive tests for explicit Pro model preservation and Flash defaults.

Rule (operator 2026-09-22):
Flash High is the default for routine and deep; Pro is used ONLY when a caller
explicitly asks for it. An explicit --model / model= value must always win.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.ai_agent_bridge._acp_compat import resolve_compat_model
from scripts.audit.naturalness_check import call_agy, check_naturalness
from scripts.batch.batch_otaman import BatchOtaman, dispatch_otaman


def test_resolve_compat_model_legacy_flash_maps_to_pin():
    """Legacy Flash slugs map to the AGY live registry pin."""
    from agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    pin = ACPX_SUPPORTED_PARTICIPANTS["agy"]["model"]
    assert resolve_compat_model("gemini", "gemini-3-flash-preview") == pin
    assert resolve_compat_model("gemini", "gemini-3.0-flash-preview") == pin
    assert resolve_compat_model("gemini", "gemini-3.7-flash") == pin
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


def test_batch_otaman_class_propagates_model():
    """BatchOtaman scheduler propagates model parameter to dispatch_otaman."""
    with patch("scripts.batch.batch_otaman.dispatch_otaman") as mock_dispatch, \
         patch("scripts.batch.batch_otaman.load_state", return_value={"tracks": {}, "running_tracks": []}), \
         patch("scripts.batch.batch_otaman.save_state"):
        mock_dispatch.return_value = {"success": True}
        bot = BatchOtaman(dry_run=True, model="gemini-3.1-pro-high")
        assert bot.model == "gemini-3.1-pro-high"


def test_naturalness_check_call_agy_model_propagation():
    """call_agy in naturalness_check defaults to Flash and respects explicit model."""
    captured = []

    def fake_run(cmd, *args, **kwargs):
        captured.append(cmd)
        return MagicMock(returncode=0, stdout='{"score": 9, "status": "PASS"}', stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        call_agy("prompt 1", "t1")
        call_agy("prompt 2", "t2", model="gemini-3.1-pro-high")

    assert len(captured) == 2
    cmd1 = captured[0]
    idx1 = cmd1.index("--to-model")
    assert cmd1[idx1 + 1] == "gemini-3.8-flash-high"

    cmd2 = captured[1]
    idx2 = cmd2.index("--to-model")
    assert cmd2[idx2 + 1] == "gemini-3.1-pro-high"


def test_check_naturalness_forwards_model():
    """check_naturalness forwards model parameter to call_agy."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        md_file = tmp_path / "test-lesson.md"
        md_file.write_text("# Урок\n" + ("Привіт! Це змістовний український текст для перевірки природності мови.\n" * 10), "utf-8")
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()

        with patch("scripts.audit.naturalness_check.call_agy", return_value=("", {"score": 9, "status": "PASS"})) as mock_agy, \
             patch("scripts.audit.naturalness_check.call_claude_headless", return_value=("", {"score": 9, "status": "PASS"})):
            score, status = check_naturalness(str(md_file), update_meta=False, force=True, model="gemini-3.1-pro-high")

        assert status == "PASS"
        assert score == 9
        mock_agy.assert_called_once()
        assert mock_agy.call_args[1].get("model") == "gemini-3.1-pro-high"
