"""Tests for step_check auto-fix integration in v6_build.py.

Verifies that step_check:
1. Calls fix_russianisms_in_plan when RUSSICISM issues found
2. Calls auto_fix_plan when VESUM issues found
3. Re-checks the plan after auto-fixes
4. Returns True when auto-fixes resolve all errors

Issue: #985
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# Ensure scripts/ is on the path (same as v6_build.py does)
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from audit.check_plan import PlanIssue


@pytest.fixture
def plan_dir(tmp_path):
    """Create a minimal plan + curriculum.yaml structure."""
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    plans = curriculum / "plans" / "a1"
    plans.mkdir(parents=True)

    # Curriculum manifest
    manifest = curriculum / "curriculum.yaml"
    manifest.write_text(yaml.dump({
        "levels": {"a1": {"modules": ["test-slug"]}}
    }))

    return tmp_path, plans


def _make_plan(plans_dir: Path, slug: str = "test-slug", **overrides) -> Path:
    """Write a minimal valid plan YAML."""
    plan = {
        "module": 1,
        "slug": slug,
        "version": "1.0",
        "level": "a1",
        "sequence": 1,
        "title": "Test Module",
        "word_target": 1200,
        "phase": "A1.1",
        "content_outline": [{"section": "Intro", "words": 1200}],
        "vocabulary_hints": {"required": ["дім (house)", "кіт (cat)"]},
        **overrides,
    }
    path = plans_dir / f"{slug}.yaml"
    path.write_text(yaml.dump(plan, allow_unicode=True, default_flow_style=False))
    return path


class TestStepCheckAutofix:
    """Test auto-fix wiring in step_check."""

    @patch("build.v6_build.CURRICULUM_ROOT")
    def test_russicism_autofix_called(self, mock_root, plan_dir):
        """When check_plan finds RUSSICISM, fix_russianisms_in_plan is called."""
        tmp_path, plans = plan_dir
        mock_root.__truediv__ = (tmp_path / "curriculum" / "l2-uk-en").__truediv__
        mock_root.return_value = tmp_path / "curriculum" / "l2-uk-en"

        _make_plan(plans)

        russicism_issue = PlanIssue("RUSSICISM", "ERROR", "Possible Russicism: 'кот'", "кіт (cat)")

        with (
            patch("build.v6_build.CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en"),
            patch("audit.check_plan.check_plan") as mock_check,
            patch("tools.plan_autofix.fix_russianisms_in_plan") as mock_fix_r,
            patch("tools.plan_autofix.auto_fix_plan") as mock_fix_v,
        ):
            # First call: returns russicism error; second call (re-check): clean
            mock_check.side_effect = [
                [russicism_issue],
                [],  # after fix, re-check passes
            ]
            mock_fix_r.return_value = (1, ["Replaced кот → кіт"])

            from build.v6_build import step_check
            result = step_check("a1", 1, "test-slug")

            assert result is True
            mock_fix_r.assert_called_once()
            # VESUM fix should NOT be called (no VESUM issues)
            mock_fix_v.assert_not_called()

    def test_vesum_autofix_called(self, plan_dir):
        """When check_plan finds VESUM warnings, auto_fix_plan is called."""
        tmp_path, plans = plan_dir
        _make_plan(plans)

        vesum_issue = PlanIssue("VESUM", "WARNING", "Vocabulary word 'блаблабла' not found in VESUM")

        with (
            patch("build.v6_build.CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en"),
            patch("audit.check_plan.check_plan") as mock_check,
            patch("tools.plan_autofix.fix_russianisms_in_plan") as mock_fix_r,
            patch("tools.plan_autofix.auto_fix_plan") as mock_fix_v,
        ):
            mock_check.side_effect = [
                [vesum_issue],
                [],  # re-check clean
            ]
            mock_fix_v.return_value = (1, ["v1.0 → v1.0.1: removed 1 word"])

            from build.v6_build import step_check
            result = step_check("a1", 1, "test-slug")

            assert result is True
            mock_fix_v.assert_called_once()
            # Verify the word was extracted correctly from the message
            call_kwargs = mock_fix_v.call_args
            vesum_list = call_kwargs.kwargs.get("vesum_not_found") or call_kwargs[1].get("vesum_not_found")
            assert vesum_list[0]["original"] == "блаблабла"
            assert vesum_list[0]["status"] == "❌"

    def test_no_issues_no_autofix(self, plan_dir):
        """When check_plan finds no issues, no auto-fix is attempted."""
        tmp_path, plans = plan_dir
        _make_plan(plans)

        with (
            patch("build.v6_build.CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en"),
            patch("audit.check_plan.check_plan") as mock_check,
            patch("tools.plan_autofix.fix_russianisms_in_plan") as mock_fix_r,
            patch("tools.plan_autofix.auto_fix_plan") as mock_fix_v,
        ):
            mock_check.return_value = []

            from build.v6_build import step_check
            result = step_check("a1", 1, "test-slug")

            assert result is True
            mock_fix_r.assert_not_called()
            mock_fix_v.assert_not_called()
            # check_plan should only be called once (no re-check needed)
            mock_check.assert_called_once()

    def test_unfixable_errors_still_fail(self, plan_dir):
        """When errors remain after auto-fix, step_check returns False."""
        tmp_path, plans = plan_dir
        _make_plan(plans)

        russicism = PlanIssue("RUSSICISM", "ERROR", "Possible Russicism: 'кот'", "кіт")
        budget_error = PlanIssue("BUDGET", "ERROR", "Section budgets sum to 500w, target is 1200w")

        with (
            patch("build.v6_build.CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en"),
            patch("audit.check_plan.check_plan") as mock_check,
            patch("tools.plan_autofix.fix_russianisms_in_plan") as mock_fix_r,
            patch("tools.plan_autofix.auto_fix_plan"),
        ):
            # Russicism fixed, but budget error persists
            mock_check.side_effect = [
                [russicism, budget_error],
                [budget_error],  # budget error still there after re-check
            ]
            mock_fix_r.return_value = (1, ["fixed"])

            from build.v6_build import step_check
            result = step_check("a1", 1, "test-slug")

            assert result is False
