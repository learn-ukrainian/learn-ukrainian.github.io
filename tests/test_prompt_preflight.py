"""Tests for the prompt preflight checker."""

import os
import sys
import textwrap

# Ensure scripts/ is on path (same as conftest.py pattern)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from pipeline.prompt_preflight import (
    PreflightIssue,
    PreflightResult,
    build_audit_context,
    build_dimension_context,
    build_preflight_prompt,
    parse_preflight_response,
)

# ==================== Parser Tests ====================


class TestParsePreflightResponse:
    def test_pass_response(self):
        yaml_text = textwrap.dedent("""\
            prompt_preflight:
              status: PASS
              issues: []
        """)
        result = parse_preflight_response(yaml_text)
        assert result.status == "PASS"
        assert result.issues == []

    def test_issues_found(self):
        yaml_text = textwrap.dedent("""\
            prompt_preflight:
              status: ISSUES_FOUND
              issues:
                - type: CONTRADICTION
                  location: "Section 3"
                  problem: "Tables claimed as high density but stripped from immersion"
                  suggested_fix: "Remove density claim"
                  severity: HIGH
                - type: MISSING_INSTRUCTION
                  location: "Section 4"
                  problem: "No mention of Summary section"
                  suggested_fix: "Add Summary requirement"
                  severity: MEDIUM
        """)
        result = parse_preflight_response(yaml_text)
        assert result.status == "ISSUES_FOUND"
        assert len(result.issues) == 2
        assert result.issues[0].issue_type == "CONTRADICTION"
        assert result.issues[0].severity == "HIGH"
        assert result.issues[1].severity == "MEDIUM"
        assert len(result.high_issues) == 1

    def test_markdown_code_fence_stripped(self):
        text = textwrap.dedent("""\
            Here's my analysis:

            ```yaml
            prompt_preflight:
              status: PASS
              issues: []
            ```
        """)
        result = parse_preflight_response(text)
        assert result.status == "PASS"

    def test_empty_response(self):
        result = parse_preflight_response("")
        assert result.status == "PASS"

    def test_malformed_yaml(self):
        result = parse_preflight_response("{{{{not yaml at all [[[")
        assert result.status == "PARSE_ERROR"

    def test_status_auto_corrected(self):
        """If issues exist but status says PASS, correct to ISSUES_FOUND."""
        yaml_text = textwrap.dedent("""\
            prompt_preflight:
              status: PASS
              issues:
                - type: UNCLEAR
                  location: "Section 1"
                  problem: "Ambiguous instruction"
                  suggested_fix: "Clarify"
                  severity: LOW
        """)
        result = parse_preflight_response(yaml_text)
        assert result.status == "ISSUES_FOUND"
        assert len(result.issues) == 1

    def test_missing_fields_handled(self):
        yaml_text = textwrap.dedent("""\
            prompt_preflight:
              status: ISSUES_FOUND
              issues:
                - type: CONTRADICTION
                  problem: "Something wrong"
        """)
        result = parse_preflight_response(yaml_text)
        assert len(result.issues) == 1
        assert result.issues[0].location == ""
        assert result.issues[0].suggested_fix == ""
        assert result.issues[0].severity == "MEDIUM"


# ==================== Context Builder Tests ====================


class TestBuildAuditContext:
    def test_a2_context_has_word_target(self):
        ctx = build_audit_context("a2", 6)
        assert "2000" in ctx
        assert "15" in ctx  # max words per sentence
        assert "ZERO" in ctx  # tables = zero immersion

    def test_b1_context(self):
        ctx = build_audit_context("b1", 10)
        assert "4000" in ctx
        assert "30" in ctx  # max words per sentence

    def test_unknown_level_returns_something(self):
        ctx = build_audit_context("zz", 1)
        assert "Audit Gates" in ctx


class TestBuildDimensionContext:
    def test_beginner_tier(self):
        ctx = build_dimension_context("a2", 6)
        assert "Beginner" in ctx
        assert "7" in ctx
        assert "Emotional Safety" in ctx

    def test_seminar_tier(self):
        ctx = build_dimension_context("hist", 1)
        assert "Seminar" in ctx or "12" in ctx
        assert "Decolonization" in ctx


# ==================== Prompt Builder Tests ====================


class TestBuildPreflightPrompt:
    def test_includes_rendered_prompt(self):
        prompt = build_preflight_prompt("Hello this is the content prompt", "a2", 6)
        assert "Hello this is the content prompt" in prompt
        assert "Audit Gates" in prompt
        assert "Scoring Dimensions" in prompt

    def test_long_prompt_truncated(self):
        long_prompt = "x" * 50000
        prompt = build_preflight_prompt(long_prompt, "a2", 6)
        assert "truncated" in prompt
        assert len(prompt) < 60000


# ==================== PreflightResult Tests ====================


class TestPreflightResult:
    def test_high_issues_filter(self):
        result = PreflightResult(
            status="ISSUES_FOUND",
            issues=[
                PreflightIssue("CONTRADICTION", "", "prob1", "fix1", "HIGH"),
                PreflightIssue("UNCLEAR", "", "prob2", "fix2", "LOW"),
                PreflightIssue("MISSING_INSTRUCTION", "", "prob3", "fix3", "HIGH"),
            ],
        )
        assert len(result.high_issues) == 2
        assert all(i.severity == "HIGH" for i in result.high_issues)
