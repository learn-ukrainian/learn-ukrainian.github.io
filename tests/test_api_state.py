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
        (review_dir / "test-module-review.md").write_text("**Overall Score:** 8.7/10\n\n**Status:** PASS")
        result = _get_review_score(track_dir, "test-module")
        assert result["exists"] is True
        assert result["score"] == 8.7
        assert result["verdict"] == "PASS"


class TestComputeShippable:
    """Track health reports delivery stages from their own records.

    An audit pass plus a review score is not one of those stages.
    """

    def _health(self, tmp_path, *, mdx=None, verdict=None, write_complete=False, audit_pass=False):
        from scripts.api.state_build import compute_track_health

        root = tmp_path
        curriculum = root / "curriculum" / "l2-uk-en"
        track = curriculum / "a1"
        orch = track / "orchestration" / "alpha"
        review = track / "review"
        status = track / "status"
        plans = curriculum / "plans" / "a1"
        for path in (orch, review, status, plans):
            path.mkdir(parents=True)
        (plans / "alpha.yaml").write_text("slug: alpha\n", encoding="utf-8")
        state = {"mode": "v6", "phases": {}}
        if write_complete:
            state["phases"]["write"] = {"status": "complete", "ts": "2026-01-01T00:00:00+00:00"}
        (orch / "state.json").write_text(json.dumps(state), encoding="utf-8")
        if audit_pass:
            (status / "alpha.json").write_text(
                json.dumps({"overall": {"status": "pass"}, "gates": {}}),
                encoding="utf-8",
            )
        if verdict:
            (review / "alpha-final-review.md").write_text(
                f"===VERDICT===\n{verdict}\n===END_VERDICT===\n",
                encoding="utf-8",
            )
        if mdx == "flat":
            mdx_path = root / "site" / "src" / "content" / "docs" / "a1" / "alpha.mdx"
            mdx_path.parent.mkdir(parents=True)
            mdx_path.write_text("---\ntitle: Alpha\n---\n\nText\n", encoding="utf-8")
        elif mdx == "index":
            mdx_path = root / "site" / "src" / "content" / "docs" / "a1" / "alpha" / "index.mdx"
            mdx_path.parent.mkdir(parents=True)
            mdx_path.write_text("---\ntitle: Alpha\n---\n\nText\n", encoding="utf-8")
        (review / "alpha-review.md").write_text(
            "**Overall Score:** 9.2/10\n\n**Status:** PASS\n",
            encoding="utf-8",
        )
        return compute_track_health(
            "a1",
            {"id": "a1", "path": "a1"},
            curriculum_root=curriculum,
            plans_root=curriculum / "plans",
            project_root=root,
            git_root=root,
        )

    def test_pass_and_good_score(self, tmp_path):
        health = self._health(tmp_path, audit_pass=True)
        assert "shippable" not in health
        assert health["audit"]["passing"] == 1
        assert health["published"]["count"] == 0
        assert health["merged"]["count"] is None
        assert health["merged"]["available"] is False
        assert health["final_review"]["approved"] == 0

    def test_pass_but_low_score(self, tmp_path):
        health = self._health(tmp_path, audit_pass=True, mdx="index")
        assert health["published"]["count"] == 1
        assert "index.mdx" in health["published"]["source"]
        assert health["merged"]["available"] is False
        assert health["merged"]["count"] is None
        assert "shippable" not in health

    def test_fail_audit(self, tmp_path):
        health = self._health(tmp_path, write_complete=True, verdict="NEEDS_WORK")
        assert health["build"]["content_phase_complete"] == 1
        assert "done" not in health["build"]
        assert health["build"]["source"].startswith("curriculum/l2-uk-en/{track}/orchestration/")
        assert health["final_review"]["reviewed"] == 1
        assert health["final_review"]["approved"] == 0
        assert health["audit"]["passing"] == 0

    def test_no_review(self, tmp_path):
        health = self._health(tmp_path, verdict="APPROVE", mdx="flat")
        assert health["final_review"]["approved"] == 1
        assert "APPROVE" in health["final_review"]["source"]
        assert health["published"]["count"] == 1
        assert health["merged"]["count"] is None
        assert health["merged"]["source"].startswith("git ls-tree origin/main")


class TestPlanRevisionLog:
    def test_block_style_plan_fixes_count_as_enriched(self, tmp_path):
        from scripts.api.state_helpers import plan_has_revision_log

        plan = tmp_path / "plan.yaml"
        plan.write_text(
            "module: a2-001\nplan_fixes:\n- version: 1.2.4\n  changes:\n  - Added readiness metadata.\n",
            encoding="utf-8",
        )

        assert plan_has_revision_log(plan) is True


class TestGetStressIssues:
    def test_with_stress_issues(self, module_tree):
        from scripts.api.state_compute import _get_stress_issues

        _, orch_dir = module_tree
        (orch_dir / "screen-result.json").write_text(
            json.dumps(
                {
                    "deterministic_issues": [
                        {"type": "STRESS_MISMATCH", "text": "Wrong: моло́ко → молоко́"},
                        {"type": "STRESS_MISMATCH", "text": "Wrong: ї́жак → їжа́к"},
                        {"type": "STRESS_UNKNOWN", "text": "Unknown: за́мок"},
                        {"type": "RUSSIANISM", "text": "Not stress related"},
                    ]
                }
            )
        )
        result = _get_stress_issues(orch_dir)
        assert result["mismatches"] == 2
        assert result["unknown"] == 1
        assert len(result["details"]) == 2
