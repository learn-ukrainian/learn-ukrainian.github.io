"""Tests for Monitor API state_compute + state_build new fields (#971)."""

import json

import pytest
import yaml


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


class TestGetFrictionData:
    def test_no_file(self, module_tree):
        from scripts.api.state_compute import _get_friction_data
        _, orch_dir = module_tree
        result = _get_friction_data(orch_dir)
        assert result["active"] == 0
        assert result["resolved"] == 0
        assert result["items"] == []

    def test_with_frictions(self, module_tree):
        from scripts.api.state_compute import _get_friction_data
        _, orch_dir = module_tree
        (orch_dir / "friction.yaml").write_text(yaml.dump({
            "frictions": [
                {"id": "f1", "status": "active", "type": "linguistic",
                 "description": "Wrong stress on молоко"},
                {"id": "f2", "status": "resolved", "type": "structural",
                 "description": "Fixed schema"},
                {"id": "f3", "status": "active", "type": "pedagogical",
                 "description": "Missing vocab word"},
            ]
        }))
        result = _get_friction_data(orch_dir)
        assert result["active"] == 2
        assert result["resolved"] == 1
        assert len(result["items"]) == 2
        assert result["items"][0]["id"] == "f1"


class TestGetReviewScore:
    def test_no_file(self, module_tree):
        from scripts.api.state_compute import _get_review_score
        track_dir, _ = module_tree
        result = _get_review_score(track_dir, "test-module")
        assert result["exists"] is False
        assert result["score"] is None

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

    def test_fail_verdict(self, module_tree):
        from scripts.api.state_compute import _get_review_score
        track_dir, _ = module_tree
        review_dir = track_dir / "review"
        (review_dir / "test-module-review.md").write_text(
            "**Overall Score:** 5.8/10\n\n**Status:** FAIL"
        )
        result = _get_review_score(track_dir, "test-module")
        assert result["score"] == 5.8
        assert result["verdict"] == "FAIL"


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


class TestGetStressIssues:
    def test_no_screen_result(self, module_tree):
        from scripts.api.state_compute import _get_stress_issues
        _, orch_dir = module_tree
        result = _get_stress_issues(orch_dir)
        assert result["mismatches"] == 0

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
