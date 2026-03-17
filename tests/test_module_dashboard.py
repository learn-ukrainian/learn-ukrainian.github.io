"""Tests for module_dashboard.py (#970 AC5-AC7)."""

import json

import pytest
import yaml

from scripts.module_dashboard import (
    _count_frictions,
    _extract_review_score,
    _get_blocking_issues,
    _load_status,
    dashboard,
)


@pytest.fixture
def level_tree(tmp_path, monkeypatch):
    """Create a minimal level directory structure."""
    import scripts.module_dashboard as mod

    monkeypatch.setattr(mod, "CURRICULUM_ROOT", tmp_path)

    # curriculum.yaml
    manifest = tmp_path / "curriculum.yaml"
    manifest.write_text(yaml.dump({
        "levels": {
            "a1": {
                "modules": ["mod-pass", "mod-fail", "mod-nodata"]
            }
        }
    }))

    # status/
    status_dir = tmp_path / "a1" / "status"
    status_dir.mkdir(parents=True)

    (status_dir / "mod-pass.json").write_text(json.dumps({
        "overall": {"status": "pass"},
        "gates": {"lesson": {"status": "pass", "message": "1200/1200"}},
    }))

    (status_dir / "mod-fail.json").write_text(json.dumps({
        "overall": {"status": "fail"},
        "gates": {
            "activities": {"status": "fail", "message": "4/8"},
            "lesson": {"status": "pass", "message": "1200/1200"},
        },
    }))

    # review/
    review_dir = tmp_path / "a1" / "review"
    review_dir.mkdir(parents=True)

    (review_dir / "mod-pass-review.md").write_text(
        "**Overall Score:** 9.2/10\n\n**Status:** PASS"
    )
    (review_dir / "mod-fail-review.md").write_text(
        "**Overall Score:** 5.8/10\n\n**Status:** FAIL"
    )

    # orchestration/mod-pass/friction.yaml
    orch_dir = tmp_path / "a1" / "orchestration" / "mod-pass"
    orch_dir.mkdir(parents=True)
    (orch_dir / "friction.yaml").write_text(yaml.dump({
        "frictions": [
            {"id": "f1", "status": "resolved", "description": "fixed"},
        ]
    }))

    # orchestration/mod-fail/friction.yaml
    orch_dir2 = tmp_path / "a1" / "orchestration" / "mod-fail"
    orch_dir2.mkdir(parents=True)
    (orch_dir2 / "friction.yaml").write_text(yaml.dump({
        "frictions": [
            {"id": "f1", "status": "active", "description": "broken"},
            {"id": "f2", "status": "active", "description": "also broken"},
        ]
    }))

    return tmp_path


class TestLoadStatus:
    def test_existing(self, level_tree):
        status = _load_status("a1", "mod-pass")
        assert status["overall"]["status"] == "pass"

    def test_missing(self, level_tree):
        assert _load_status("a1", "mod-nodata") is None


class TestExtractReviewScore:
    def test_numeric_score(self, level_tree):
        assert _extract_review_score("a1", "mod-pass") == "9.2"

    def test_fail_score(self, level_tree):
        assert _extract_review_score("a1", "mod-fail") == "5.8"

    def test_missing(self, level_tree):
        assert _extract_review_score("a1", "mod-nodata") is None


class TestCountFrictions:
    def test_with_frictions(self, level_tree):
        active, resolved = _count_frictions("a1", "mod-fail")
        assert active == 2
        assert resolved == 0

    def test_resolved_frictions(self, level_tree):
        active, resolved = _count_frictions("a1", "mod-pass")
        assert active == 0
        assert resolved == 1

    def test_missing(self, level_tree):
        assert _count_frictions("a1", "mod-nodata") == (0, 0)


class TestGetBlockingIssues:
    def test_finds_failures(self):
        status = {
            "gates": {
                "activities": {"status": "fail", "message": "4/8"},
                "lesson": {"status": "pass", "message": "ok"},
            }
        }
        issues = _get_blocking_issues(status)
        assert len(issues) == 1
        assert "activities" in issues[0]

    def test_no_failures(self):
        status = {"gates": {"lesson": {"status": "pass", "message": "ok"}}}
        assert _get_blocking_issues(status) == []


class TestDashboard:
    def test_shows_all_modules(self, level_tree, capsys):
        dashboard("a1")
        out = capsys.readouterr().out
        assert "mod-pass" in out
        assert "mod-fail" in out
        assert "mod-nodata" in out

    def test_failing_only(self, level_tree, capsys):
        dashboard("a1", failing_only=True)
        out = capsys.readouterr().out
        # mod-pass has review 9.2 and audit pass — but still has 0a/1r frictions
        # All modules should show since none are truly shippable without review ≥8
        # Actually mod-pass has 9.2 review and audit pass — it IS shippable
        # So it should NOT appear with --failing-only
        assert "mod-fail" in out
        assert "mod-nodata" in out

    def test_first_n(self, level_tree, capsys):
        dashboard("a1", first_n=1)
        out = capsys.readouterr().out
        assert "mod-pass" in out
        assert "mod-fail" not in out

    def test_shippable_needs_review_8(self, level_tree, capsys):
        ret = dashboard("a1")
        out = capsys.readouterr().out
        # mod-fail has review 5.8 — should show as blocking
        assert "5.8/10 (need" in out
