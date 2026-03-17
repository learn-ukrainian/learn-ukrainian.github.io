"""Tests for the prompt preflight checker (split feasibility + coherence)."""

import os
import sys
import textwrap

# Ensure scripts/ is on path (same as conftest.py pattern)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from pipeline.prompt_preflight import (
    CombinedPreflightResult,
    PreflightIssue,
    PreflightResult,
    build_audit_context,
    build_coherence_prompt,
    build_dimension_context,
    build_feasibility_prompt,
    build_preflight_prompt,
    parse_preflight_response,
    run_prompt_preflight,
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


# ==================== Source Field Tests ====================


class TestPreflightIssueSource:
    def test_source_propagated_from_parser(self):
        yaml_text = textwrap.dedent("""\
            prompt_preflight:
              status: ISSUES_FOUND
              issues:
                - type: CONTRADICTION
                  location: "Section 1"
                  problem: "A problem"
                  suggested_fix: "A fix"
                  severity: HIGH
        """)
        result = parse_preflight_response(yaml_text, source="feasibility")
        assert result.issues[0].source == "feasibility"

        result2 = parse_preflight_response(yaml_text, source="coherence")
        assert result2.issues[0].source == "coherence"

    def test_default_source_is_unknown(self):
        yaml_text = textwrap.dedent("""\
            prompt_preflight:
              status: ISSUES_FOUND
              issues:
                - type: UNCLEAR
                  problem: "Something"
                  severity: LOW
        """)
        result = parse_preflight_response(yaml_text)
        assert result.issues[0].source == "unknown"


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


class TestBuildFeasibilityPrompt:
    def test_includes_rendered_prompt_and_gates(self):
        prompt = build_feasibility_prompt("Hello this is the content prompt", "a2", 6)
        assert "Hello this is the content prompt" in prompt
        assert "Audit Gates" in prompt
        assert "Scoring Dimensions" in prompt
        # Feasibility = writer self-check, should say "you are about to build"
        assert "build a module" in prompt

    def test_no_plan_yaml(self):
        """Feasibility prompt should NOT contain plan YAML."""
        prompt = build_feasibility_prompt("test prompt", "a1", 3)
        assert "The Plan" not in prompt

    def test_long_prompt_truncated(self):
        long_prompt = "x" * 50000
        prompt = build_feasibility_prompt(long_prompt, "a2", 6)
        assert "truncated" in prompt


class TestBuildCoherencePrompt:
    def test_includes_plan_and_prompt(self):
        prompt = build_coherence_prompt(
            "rendered prompt content",
            "plan: yaml content here",
            "a1", 3,
        )
        assert "rendered prompt content" in prompt
        assert "plan: yaml content here" in prompt
        assert "Audit Gates" in prompt
        assert "reviewer" in prompt.lower() or "plan" in prompt.lower()

    def test_plan_truncated_if_long(self):
        long_plan = "y" * 20000
        prompt = build_coherence_prompt("short prompt", long_plan, "a1", 3)
        assert "truncated" in prompt


class TestBuildPreflightPrompt:
    """Backward compat alias should still work."""
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


# ==================== CombinedPreflightResult Tests ====================


class TestCombinedPreflightResult:
    def test_both_pass(self):
        feas = PreflightResult(status="PASS")
        coh = PreflightResult(status="PASS")
        combined = CombinedPreflightResult(feasibility=feas, coherence=coh)
        assert combined.status == "PASS"
        assert combined.issues == []
        assert combined.high_issues == []

    def test_feasibility_issues(self):
        feas = PreflightResult(
            status="ISSUES_FOUND",
            issues=[PreflightIssue("CONTRADICTION", "", "prob", "fix", "HIGH", "feasibility")],
        )
        coh = PreflightResult(status="PASS")
        combined = CombinedPreflightResult(feasibility=feas, coherence=coh)
        assert combined.status == "ISSUES_FOUND"
        assert len(combined.issues) == 1
        assert len(combined.feasibility_high_issues) == 1
        assert len(combined.coherence_high_issues) == 0

    def test_coherence_issues(self):
        feas = PreflightResult(status="PASS")
        coh = PreflightResult(
            status="ISSUES_FOUND",
            issues=[PreflightIssue("MISSING_PLAN_SECTION", "", "prob", "fix", "HIGH", "coherence")],
        )
        combined = CombinedPreflightResult(feasibility=feas, coherence=coh)
        assert combined.status == "ISSUES_FOUND"
        assert len(combined.coherence_high_issues) == 1
        assert len(combined.feasibility_high_issues) == 0

    def test_coherence_none_skipped(self):
        feas = PreflightResult(status="PASS")
        combined = CombinedPreflightResult(feasibility=feas, coherence=None)
        assert combined.status == "PASS"
        assert combined.coherence_high_issues == []

    def test_both_issues_merged(self):
        feas = PreflightResult(
            status="ISSUES_FOUND",
            issues=[PreflightIssue("CONTRADICTION", "", "p1", "f1", "HIGH", "feasibility")],
        )
        coh = PreflightResult(
            status="ISSUES_FOUND",
            issues=[PreflightIssue("MISSING_PLAN_SECTION", "", "p2", "f2", "MEDIUM", "coherence")],
        )
        combined = CombinedPreflightResult(feasibility=feas, coherence=coh)
        assert combined.status == "ISSUES_FOUND"
        assert len(combined.issues) == 2
        assert len(combined.high_issues) == 1

    def test_dispatch_error_not_masked_as_pass(self):
        """Gemini review bug: PASS + DISPATCH_ERROR should NOT return PASS."""
        feas = PreflightResult(status="PASS")
        coh = PreflightResult(status="DISPATCH_ERROR")
        combined = CombinedPreflightResult(feasibility=feas, coherence=coh)
        assert combined.status == "DISPATCH_ERROR"

    def test_parse_error_propagated(self):
        feas = PreflightResult(status="PASS")
        coh = PreflightResult(status="PARSE_ERROR")
        combined = CombinedPreflightResult(feasibility=feas, coherence=coh)
        assert combined.status == "PARSE_ERROR"


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


# ==================== Runner Tests ====================


class TestRunPromptPreflightCombined:
    """Test that run_prompt_preflight dispatches both checks."""

    def test_feasibility_only_when_no_plan(self, tmp_path):
        """When plan_path is None, only feasibility runs."""
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("test prompt content")
        orch_dir = tmp_path / "orch"
        orch_dir.mkdir()

        # Mock dispatch that returns PASS
        pass_yaml = "prompt_preflight:\n  status: PASS\n  issues: []\n"

        def mock_dispatch(prompt_text):
            return True, pass_yaml

        result = run_prompt_preflight(
            prompt_path, "a1", 3, orch_dir,
            dispatch_fn=mock_dispatch,
            plan_path=None,
        )

        assert isinstance(result, CombinedPreflightResult)
        assert result.feasibility.status == "PASS"
        assert result.coherence is None
        assert result.status == "PASS"

    def test_both_checks_when_plan_exists(self, tmp_path):
        """When plan_path exists, both checks run."""
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("test prompt content")
        plan_path = tmp_path / "plan.yaml"
        plan_path.write_text("word_target: 1200\ncontent_outline:\n  - title: Intro\n")
        orch_dir = tmp_path / "orch"
        orch_dir.mkdir()

        pass_yaml = "prompt_preflight:\n  status: PASS\n  issues: []\n"

        def mock_gemini_dispatch(prompt_text):
            return True, pass_yaml

        def mock_claude_dispatch(prompt_text):
            return True, pass_yaml

        result = run_prompt_preflight(
            prompt_path, "a1", 3, orch_dir,
            dispatch_fn=mock_gemini_dispatch,
            coherence_dispatch_fn=mock_claude_dispatch,
            plan_path=plan_path,
        )

        assert isinstance(result, CombinedPreflightResult)
        assert result.feasibility.status == "PASS"
        assert result.coherence is not None
        assert result.coherence.status == "PASS"
        assert result.status == "PASS"

    def test_combined_result_yaml_saved(self, tmp_path):
        """Combined preflight-result.yaml saved for backward compat."""
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("test prompt")
        orch_dir = tmp_path / "orch"
        orch_dir.mkdir()

        pass_yaml = "prompt_preflight:\n  status: PASS\n  issues: []\n"

        def mock_dispatch(prompt_text):
            return True, pass_yaml

        run_prompt_preflight(
            prompt_path, "a1", 3, orch_dir,
            dispatch_fn=mock_dispatch,
            plan_path=None,
        )

        combined_yaml = orch_dir / "preflight-result.yaml"
        assert combined_yaml.exists()
        import yaml
        data = yaml.safe_load(combined_yaml.read_text())
        assert data["status"] == "PASS"
        assert data["coherence_status"] == "SKIPPED"
