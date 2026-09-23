"""Tests for scripts/batch/batch_fix_review.py: model selection and propagation.

Rule (operator 2026-09-22):
Flash High is the default; Pro is used ONLY when a caller explicitly asks for it.
Explicit --model / model= parameter must always win.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.batch.batch_fix_review import call_gemini, call_gemini_review, process_module


def test_call_gemini_passes_explicit_pro_model():
    """call_gemini must forward explicit Pro model to ask-gemini command line."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("fix this content", "utf-8")

        captured_cmd = []

        def fake_run(cmd, *args, **kwargs):
            captured_cmd.extend(cmd)
            return MagicMock(returncode=0, stdout="===CONTENT_START===\nfixed\n===CONTENT_END===\n", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            output = call_gemini(prompt_path, "task-pro", "gemini-3.1-pro-high")

        assert output.exists()
        assert "--model" in captured_cmd
        model_idx = captured_cmd.index("--model")
        assert captured_cmd[model_idx + 1] == "gemini-3.1-pro-high"
        output.unlink()


def test_call_gemini_review_passes_explicit_pro_model():
    """call_gemini_review must forward explicit Pro model to ask-gemini command line."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        prompt_path = tmp_path / "review_prompt.md"
        prompt_path.write_text("review this content", "utf-8")

        captured_cmd = []

        def fake_run(cmd, *args, **kwargs):
            captured_cmd.extend(cmd)
            return MagicMock(returncode=0, stdout="===REVIEW_START===\nPASS (8/10)\n===REVIEW_END===\n", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            output = call_gemini_review(prompt_path, "task-review-pro", "gemini-3.1-pro-high")

        assert output.exists()
        assert "--model" in captured_cmd
        model_idx = captured_cmd.index("--model")
        assert captured_cmd[model_idx + 1] == "gemini-3.1-pro-high"
        output.unlink()


def test_call_gemini_default_uses_flash_high():
    """call_gemini with default Flash High model passes gemini-3.8-flash-high."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("fix this content", "utf-8")

        captured_cmd = []

        def fake_run(cmd, *args, **kwargs):
            captured_cmd.extend(cmd)
            return MagicMock(returncode=0, stdout="===CONTENT_START===\nfixed\n===CONTENT_END===\n", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            output = call_gemini(prompt_path, "task-flash", "gemini-3.8-flash-high")

        assert output.exists()
        assert "--model" in captured_cmd
        model_idx = captured_cmd.index("--model")
        assert captured_cmd[model_idx + 1] == "gemini-3.8-flash-high"
        output.unlink()


def test_process_module_propagates_explicit_pro_model():
    """process_module must propagate the explicit model to review/fix functions."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        content = tmp_path / "content.md"
        content.write_text("# Test\nContent\n")
        orch = tmp_path / "orch"
        orch.mkdir(parents=True)

        with patch("scripts.batch.batch_fix_review.find_module_files", return_value={
            "num": 1, "slug": "test", "full_stem": "test",
            "content": content, "activities": tmp_path / "acts.yaml",
            "vocabulary": tmp_path / "vocab.yaml", "meta": tmp_path / "meta.yaml",
            "plan": tmp_path / "plan.yaml", "research": tmp_path / "research.md",
            "review": tmp_path / "review.md", "status": tmp_path / "status.json",
            "orchestration": orch,
        }), patch("scripts.batch.batch_fix_review._run_initial_review", return_value=("continue", 9.0)) as mock_initial:
            result = process_module(level="a1", num=1, model="gemini-3.1-pro-high", review_only=True)

        assert result["status"] == "REVIEWED"
        assert result["score"] == 9.0
        mock_initial.assert_called_once()
        args = mock_initial.call_args[0]
        assert "gemini-3.1-pro-high" in args
