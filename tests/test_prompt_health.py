"""Tests for pre-dispatch prompt health check."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pipeline_lib import check_prompt_health, log_prompt_health


def _make_ctx(track="a1", module_num=20, immersion_rule="Write 35-55% Ukrainian"):
    ctx = MagicMock()
    ctx.track = track
    ctx.module_num = module_num
    ctx.immersion_rule = immersion_rule
    return ctx


class TestCheckPromptHealth:
    """Tests for check_prompt_health."""

    def test_unfilled_immersion_rule_error(self):
        ctx = _make_ctx()
        prompt = "Immersion: {IMMERSION_RULE}. Write content."
        issues = check_prompt_health(ctx, prompt, "content")
        errors = [i for i in issues if i.startswith("ERROR:") and "IMMERSION_RULE" in i]
        assert len(errors) == 1


class TestLogPromptHealth:
    """Tests for log_prompt_health."""

    def test_error_returns_false(self):
        assert log_prompt_health(["ERROR: critical thing"], "content") is False
