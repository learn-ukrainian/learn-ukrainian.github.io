"""Tests for Monitor API state_compute + state_build new fields (#971)."""

import json

import pytest


@pytest.fixture
def module_tree(tmp_path):
    """Create minimal module directory structure for API testing."""
    track_dir = tmp_path / "a1"
    orch_dir = track_dir / "orchestration" / "test-module"
    review_dir = track_dir / "review"
    status_dir = track_dir / "status"
    for d in [orch_dir, review_dir, status_dir]:
        d.mkdir(parents=True)
    return track_dir, orch_dir


class TestGetReviewScore:
    def test_with_score(self, module_tree):
        from scripts.api.state_compute import _get_review_score
        track_dir, _ = module_tree
        review_dir = track_dir / "review"
        (review_dir / "test-module-review.md").write_text(
            "**Overall Score:** 8.7/10\n\n**Status:** PASS"
        )
        result = _get_review_score(track_dir, "test-module")
        assert result["exists"] is True
        assert result["score"] == 8.7
        assert result["verdict"] == "PASS"


class TestComputeShippable:
    def test_pass_and_good_score(self):
        from scripts.api.state_compute import _compute_shippable
        assert _compute_shippable("pass", 8.7) is True

    def test_pass_but_low_score(self):
        from scripts.api.state_compute import _compute_shippable
        assert _compute_shippable("pass", 7.9) is False

    def test_fail_audit(self):
        from scripts.api.state_compute import _compute_shippable
        assert _compute_shippable("fail", 9.0) is False

    def test_no_review(self):
        from scripts.api.state_compute import _compute_shippable
        assert _compute_shippable("pass", None) is False


class TestPlanRevisionLog:
    def test_block_style_plan_fixes_count_as_enriched(self, tmp_path):
        from scripts.api.state_helpers import plan_has_revision_log

        plan = tmp_path / "plan.yaml"
        plan.write_text(
            "module: a2-001\n"
            "plan_fixes:\n"
            "- version: 1.2.4\n"
            "  changes:\n"
            "  - Added readiness metadata.\n",
            encoding="utf-8",
        )

        assert plan_has_revision_log(plan) is True


class TestGetStressIssues:
    def test_with_stress_issues(self, module_tree):
        from scripts.api.state_compute import _get_stress_issues
        _, orch_dir = module_tree
        (orch_dir / "screen-result.json").write_text(json.dumps({
            "deterministic_issues": [
                {"type": "STRESS_MISMATCH", "text": "Wrong: моло́ко → молоко́"},
                {"type": "STRESS_MISMATCH", "text": "Wrong: ї́жак → їжа́к"},
                {"type": "STRESS_UNKNOWN", "text": "Unknown: за́мок"},
                {"type": "RUSSIANISM", "text": "Not stress related"},
            ]
        }))
        result = _get_stress_issues(orch_dir)
        assert result["mismatches"] == 2
        assert result["unknown"] == 1
        assert len(result["details"]) == 2
