"""Regression tests for plan-patch parse failure handling (#1304).

Ensures that unparseable Gemini output produces explicit, deterministic
failure reasons rather than silently falling back to treating the entire
raw LLM response as YAML.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import yaml

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

plan_patch = importlib.import_module("build.phases.plan_patch")


class TestParsePlanPatchResponse:
    """parse_plan_patch_response must return structured failure reasons."""

    def test_missing_delimiters_returns_explicit_failure(self) -> None:
        raw = "Here is some prose from Gemini without any delimiters."
        outcome = plan_patch.parse_plan_patch_response(raw)
        assert not outcome.ok
        assert outcome.failure_reason == "missing_delimiters"
        assert outcome.data is None

    def test_empty_output_returns_explicit_failure(self) -> None:
        outcome = plan_patch.parse_plan_patch_response("")
        assert not outcome.ok
        assert outcome.failure_reason == "empty_output"

    def test_whitespace_only_returns_empty_output(self) -> None:
        outcome = plan_patch.parse_plan_patch_response("   \n\n  ")
        assert not outcome.ok
        assert outcome.failure_reason == "empty_output"

    def test_valid_delimiters_with_valid_yaml_succeeds(self) -> None:
        raw = (
            "noise\n"
            "===PLAN_PATCH_START===\n"
            "decision: noop\n"
            "complaint_summary: prose-only issue\n"
            "===PLAN_PATCH_END===\n"
            "more noise"
        )
        outcome = plan_patch.parse_plan_patch_response(raw)
        assert outcome.ok
        assert outcome.data["decision"] == "noop"
        assert outcome.failure_reason is None

    def test_valid_delimiters_with_invalid_yaml_returns_parse_error(self) -> None:
        raw = (
            "===PLAN_PATCH_START===\n"
            "not: valid: yaml: [unclosed\n"
            "===PLAN_PATCH_END===\n"
        )
        outcome = plan_patch.parse_plan_patch_response(raw)
        assert not outcome.ok
        assert outcome.failure_reason is not None
        assert outcome.failure_reason.startswith("yaml_parse_error")

    def test_valid_delimiters_with_non_dict_yaml_returns_type_error(self) -> None:
        raw = (
            "===PLAN_PATCH_START===\n"
            "- just a list item\n"
            "- another item\n"
            "===PLAN_PATCH_END===\n"
        )
        outcome = plan_patch.parse_plan_patch_response(raw)
        assert not outcome.ok
        assert outcome.failure_reason is not None
        assert "unexpected_payload_type" in outcome.failure_reason

    def test_empty_content_between_delimiters(self) -> None:
        raw = (
            "===PLAN_PATCH_START===\n"
            "\n"
            "===PLAN_PATCH_END===\n"
        )
        outcome = plan_patch.parse_plan_patch_response(raw)
        assert not outcome.ok
        assert outcome.failure_reason == "empty_payload_between_delimiters"

    def test_code_fence_stripping_within_delimiters(self) -> None:
        raw = (
            "===PLAN_PATCH_START===\n"
            "```yaml\n"
            "decision: patch\n"
            "complaint_summary: test\n"
            "changes: []\n"
            "```\n"
            "===PLAN_PATCH_END===\n"
        )
        outcome = plan_patch.parse_plan_patch_response(raw)
        assert outcome.ok
        assert outcome.data["decision"] == "patch"


class TestRunPlanPatchDiagnosticArtifact:
    """run_plan_patch must save diagnostic artifacts on parse failure."""

    def test_diagnostic_artifact_written_on_missing_delimiters(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        plan_path = tmp_path / "plan.yaml"
        plan_path.write_text("version: '1.0'\ntitle: Demo\n", "utf-8")
        orch_dir = tmp_path / "orch"
        orch_dir.mkdir()
        (orch_dir / "review-structured-r1.yaml").write_text(
            yaml.safe_dump(
                {
                    "round": 1,
                    "scores": [
                        {
                            "dimension": 2,
                            "name": "Linguistic accuracy",
                            "score": 8,
                            "evidence": "A few inflection errors remain.",
                        }
                    ],
                    "findings": [],
                },
                sort_keys=False,
            ),
            "utf-8",
        )

        # Gemini returns prose without delimiters
        monkeypatch.setattr(
            plan_patch,
            "_dispatch_gemini_plan_patch",
            lambda *args, **kwargs: (True, "I think the plan is fine as-is."),
        )

        result = plan_patch.run_plan_patch(
            level="a1",
            slug="demo",
            plan_path=plan_path,
            orch_dir=orch_dir,
            score_history=[8.3],
            contract_violations=[],
        )

        assert result.applied is False
        assert "missing_delimiters" in result.reason

        diag_path = orch_dir / "v6-plan-patch-diagnostic.yaml"
        assert diag_path.exists()
        diag = yaml.safe_load(diag_path.read_text("utf-8"))
        assert diag["failure_reason"] == "missing_delimiters"
        assert diag["raw_output_length"] > 0
