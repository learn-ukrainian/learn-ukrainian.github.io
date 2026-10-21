"""Tests for the prompt preflight checker (single writer call)."""

import os
import sys
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from pipeline.prompt_preflight import (
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


# ==================== Prompt Builder Tests ====================


# ==================== PreflightResult Tests ====================
# ==================== Runner Tests ====================


class TestRunPromptPreflight:

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
