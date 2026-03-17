"""Tests for the prompt preflight checker (single writer call)."""

import os
import sys
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from pipeline.prompt_preflight import (
    PreflightIssue,
    PreflightResult,
    build_audit_context,
    build_dimension_context,
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
        assert "ZERO" in ctx

    def test_b1_context(self):
        ctx = build_audit_context("b1", 10)
        assert "4000" in ctx

    def test_unknown_level_returns_something(self):
        ctx = build_audit_context("zz", 1)
        assert "Audit Gates" in ctx


class TestBuildDimensionContext:
    def test_beginner_tier(self):
        ctx = build_dimension_context("a2", 6)
        assert "Beginner" in ctx
        assert "Emotional Safety" in ctx

    def test_seminar_tier(self):
        ctx = build_dimension_context("hist", 1)
        assert "Decolonization" in ctx


# ==================== Prompt Builder Tests ====================


class TestBuildPreflightPrompt:
    def test_includes_rendered_prompt_and_gates(self):
        prompt = build_preflight_prompt("Hello content prompt", "a2", 6)
        assert "Hello content prompt" in prompt
        assert "Audit Gates" in prompt
        assert "False Friends" in prompt or "Russianisms" in prompt

    def test_long_prompt_truncated(self):
        long_prompt = "x" * 50000
        prompt = build_preflight_prompt(long_prompt, "a2", 6)
        assert "truncated" in prompt

    def test_without_plan(self):
        prompt = build_preflight_prompt("test prompt", "a1", 3)
        assert "The Plan" not in prompt
        assert "Plan-Prompt Coherence" not in prompt

    def test_with_plan(self):
        prompt = build_preflight_prompt("test prompt", "a1", 3, plan_yaml="word_target: 1200")
        assert "The Plan" in prompt
        assert "word_target: 1200" in prompt
        assert "Coherence" in prompt

    def test_plan_truncated_if_long(self):
        long_plan = "y" * 20000
        prompt = build_preflight_prompt("short prompt", "a1", 3, plan_yaml=long_plan)
        assert "truncated" in prompt


# ==================== PreflightResult Tests ====================


class TestPreflightResult:
    def test_high_issues_filter(self):
        result = PreflightResult(
            status="ISSUES_FOUND",
            issues=[
                PreflightIssue("CONTRADICTION", "", "prob1", "fix1", "HIGH"),
                PreflightIssue("UNCLEAR", "", "prob2", "fix2", "LOW"),
                PreflightIssue("RUSSICISM", "", "prob3", "fix3", "HIGH"),
            ],
        )
        assert len(result.high_issues) == 2
        assert all(i.severity == "HIGH" for i in result.high_issues)


# ==================== Runner Tests ====================


class TestRunPromptPreflight:
    def test_pass_result(self, tmp_path):
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("test prompt content")
        orch_dir = tmp_path / "orch"
        orch_dir.mkdir()

        pass_yaml = "prompt_preflight:\n  status: PASS\n  issues: []\n"

        def mock_dispatch(prompt_text):
            return True, pass_yaml

        result = run_prompt_preflight(
            prompt_path, "a1", 3, orch_dir,
            dispatch_fn=mock_dispatch,
        )

        assert isinstance(result, PreflightResult)
        assert result.status == "PASS"

    def test_with_plan(self, tmp_path):
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("test prompt content")
        plan_path = tmp_path / "plan.yaml"
        plan_path.write_text("word_target: 1200\n")
        orch_dir = tmp_path / "orch"
        orch_dir.mkdir()

        pass_yaml = "prompt_preflight:\n  status: PASS\n  issues: []\n"

        def mock_dispatch(prompt_text):
            # Verify plan content is included in the prompt
            assert "word_target: 1200" in prompt_text
            assert "Coherence" in prompt_text
            return True, pass_yaml

        result = run_prompt_preflight(
            prompt_path, "a1", 3, orch_dir,
            dispatch_fn=mock_dispatch,
            plan_path=plan_path,
        )
        assert result.status == "PASS"

    def test_result_yaml_saved(self, tmp_path):
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
        )

        result_yaml = orch_dir / "preflight-result.yaml"
        assert result_yaml.exists()
        import yaml
        data = yaml.safe_load(result_yaml.read_text())
        assert data["status"] == "PASS"

    def test_dispatch_failure(self, tmp_path):
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("test")
        orch_dir = tmp_path / "orch"
        orch_dir.mkdir()

        def mock_dispatch(prompt_text):
            return False, "error"

        result = run_prompt_preflight(
            prompt_path, "a1", 3, orch_dir,
            dispatch_fn=mock_dispatch,
        )
        assert result.status == "DISPATCH_ERROR"
