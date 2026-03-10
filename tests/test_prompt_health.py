"""Tests for pre-dispatch prompt health check."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

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

    def test_healthy_content_prompt(self):
        ctx = _make_ctx()
        prompt = "Write a lesson about greetings. Target: 1200 words."
        issues = check_prompt_health(ctx, prompt, "content")
        assert not any(i.startswith("ERROR:") for i in issues)

    def test_no_sandbox_warning_after_removal(self):
        """Sandbox health check removed in #820 — no warnings expected."""
        ctx = _make_ctx(module_num=20)
        prompt = "Write a lesson."
        issues = check_prompt_health(ctx, prompt, "content")
        sandbox_issues = [i for i in issues if "LEXICAL_SANDBOX" in i]
        assert len(sandbox_issues) == 0

    def test_unfilled_immersion_rule_error(self):
        ctx = _make_ctx()
        prompt = "Immersion: {IMMERSION_RULE}. Write content."
        issues = check_prompt_health(ctx, prompt, "content")
        errors = [i for i in issues if i.startswith("ERROR:") and "IMMERSION_RULE" in i]
        assert len(errors) == 1

    def test_empty_immersion_rule_warning(self):
        ctx = _make_ctx(immersion_rule="")
        prompt = "Write content with immersion."
        issues = check_prompt_health(ctx, prompt, "content")
        warnings = [i for i in issues if "IMMERSION_RULE" in i and "empty" in i.lower()]
        assert len(warnings) == 1

    def test_unfilled_section_budget_error(self):
        ctx = _make_ctx()
        prompt = "Budget: {SECTION_BUDGET_TABLE}. Write."
        issues = check_prompt_health(ctx, prompt, "content")
        errors = [i for i in issues if i.startswith("ERROR:") and "SECTION_BUDGET" in i]
        assert len(errors) == 1

    def test_unfilled_word_target_error(self):
        ctx = _make_ctx()
        prompt = "Target: {WORD_TARGET} words."
        issues = check_prompt_health(ctx, prompt, "content")
        errors = [i for i in issues if i.startswith("ERROR:") and "WORD_TARGET" in i]
        assert len(errors) == 1

    def test_unfilled_required_types_in_activities(self):
        ctx = _make_ctx()
        prompt = "Types: {REQUIRED_TYPES}. Build activities."
        issues = check_prompt_health(ctx, prompt, "activities")
        errors = [i for i in issues if i.startswith("ERROR:") and "REQUIRED_TYPES" in i]
        assert len(errors) == 1

    def test_generic_unfilled_placeholder_warning(self):
        ctx = _make_ctx()
        prompt = "Content: {SOME_CUSTOM_PLACEHOLDER}. Write lesson."
        issues = check_prompt_health(ctx, prompt, "content")
        warnings = [i for i in issues if "unfilled placeholder" in i]
        assert len(warnings) == 1
        assert "SOME_CUSTOM_PLACEHOLDER" in warnings[0]

    def test_false_positive_placeholders_ignored(self):
        ctx = _make_ctx()
        prompt = "Output as JSON format. Check YAML validity. Use VESUM for verification."
        issues = check_prompt_health(ctx, prompt, "content")
        placeholder_issues = [i for i in issues if "unfilled placeholder" in i]
        assert len(placeholder_issues) == 0


class TestLogPromptHealth:
    """Tests for log_prompt_health."""

    def test_no_issues_returns_true(self):
        assert log_prompt_health([], "content") is True

    def test_warnings_only_returns_true(self):
        assert log_prompt_health(["WARNING: minor thing"], "content") is True

    def test_error_returns_false(self):
        assert log_prompt_health(["ERROR: critical thing"], "content") is False

    def test_mixed_returns_false(self):
        issues = ["WARNING: minor", "ERROR: critical"]
        assert log_prompt_health(issues, "content") is False
