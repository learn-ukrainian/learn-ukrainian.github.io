"""
Tests for decomposed API helper modules.

Covers:
  1. review_parsing.py — score/verdict/issue extraction
  2. state_helpers.py — pipeline detection, state readers, cache, audit, research
  3. state_coverage.py — summary, pipeline track, research/review coverage
  4. state_compute.py — research detail, module detail, legacy compat, severity
  5. state_build.py — build status, ETA, track health, enrichment
  6. state_issues.py — issue collection, review analysis, patterns
  7. dashboard_helpers.py — parse_slug, scan_track_cached, find_active_builds
  8. dashboard_comms.py — watcher health, stuck tasks, dispatcher state, broker
"""

import json
import time
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.reads_content

# ==================== review_parsing ====================


class TestExtractReviewScore:
    """extract_review_score parses various score formats."""

    def test_bold_overall_score(self):
        from scripts.api.review_parsing import extract_review_score

        text = "Some text\n**Overall Score:** 8.5/10\nMore text"
        assert extract_review_score(text) == 8.5


class TestExtractReviewVerdict:
    """extract_review_verdict parses PASS/FAIL."""

    def test_pass_verdict(self):
        from scripts.api.review_parsing import extract_review_verdict

        assert extract_review_verdict("**Status:** PASS") == "PASS"


class TestExtractPlanVerdict:
    """extract_plan_verdict parses plan review verdicts."""

    def test_pass(self):
        from scripts.api.review_parsing import extract_plan_verdict

        assert extract_plan_verdict("**Verdict:** PASS") == "PASS"


class TestCountReviewIssues:
    """count_review_issues counts issue headers."""

    def test_counts_issues(self):
        from scripts.api.review_parsing import count_review_issues

        text = "# Issue #1\ntext\n## Issue #2\ntext\n### Issue 3\ntext"
        assert count_review_issues(text) == 3


# ==================== state_helpers ====================


class TestDetectPipelineVersionHelpers:
    """detect_pipeline_version from state_helpers."""

    def test_v5_from_state_json(self, tmp_path):
        from scripts.api.state_helpers import detect_pipeline_version

        (tmp_path / "state.json").write_text('{"mode": "v5", "phases": {}}')
        assert detect_pipeline_version(tmp_path) == "v5"

    def test_invalid_json_returns_unbuilt(self, tmp_path):
        from scripts.api.state_helpers import detect_pipeline_version

        (tmp_path / "state.json").write_text("not json{{{")
        assert detect_pipeline_version(tmp_path) == "unbuilt"


class TestGetAuditStatus:
    """get_audit_status reads status JSON files."""

    def test_pass_status(self, tmp_path):
        from scripts.api.state_helpers import get_audit_status

        (tmp_path / "status").mkdir()
        data = {
            "overall": {"status": "pass"},
            "gates": {"lesson": {"status": "pass", "message": "1200 / 1500 words"}},
        }
        (tmp_path / "status" / "test.json").write_text(json.dumps(data))
        result = get_audit_status(tmp_path, "test")
        assert result["status"] == "pass"
        assert result["word_count"] == 1200
        assert result["word_target"] == 1500

    def test_fail_status_with_blocking(self, tmp_path):
        from scripts.api.state_helpers import get_audit_status

        (tmp_path / "status").mkdir()
        data = {
            "overall": {"status": "fail"},
            "gates": {
                "lesson": {"status": "fail", "message": "800 / 1200 words"},
                "activities": {"status": "fail", "message": "too few"},
            },
        }
        (tmp_path / "status" / "test.json").write_text(json.dumps(data))
        result = get_audit_status(tmp_path, "test")
        assert result["status"] == "fail"
        assert len(result["blocking_issues"]) == 2

    def test_invalid_json(self, tmp_path):
        from scripts.api.state_helpers import get_audit_status

        (tmp_path / "status").mkdir()
        (tmp_path / "status" / "test.json").write_text("broken json{{{")
        result = get_audit_status(tmp_path, "test")
        assert result["status"] == "error"


class TestExtractContentHash:
    """extract_content_hash reads hash from review header."""

    def test_valid_hash(self, tmp_path):
        from scripts.api.state_helpers import extract_content_hash

        review = tmp_path / "review.md"
        review.write_text("<!-- content-hash: abc123def456 -->\n# Review")
        assert extract_content_hash(review) == "abc123def456"


class TestIsReviewStale:
    """is_review_stale checks if review is older than content."""

    def test_not_stale_by_hash_match(self, tmp_path):
        import hashlib

        from scripts.api.state_helpers import is_review_stale

        content = tmp_path / "content.md"
        content.write_text("some content")
        content_hash = hashlib.md5(content.read_bytes(), usedforsecurity=False).hexdigest()[:12]
        review = tmp_path / "review.md"
        review.write_text(f"<!-- content-hash: {content_hash} -->\n# Review")
        assert is_review_stale(review, content) is False


class TestGetWordTargetFromPlan:
    """get_word_target_from_plan reads plan YAML."""

    def test_reads_target(self, tmp_path):
        from scripts.api.state_helpers import get_word_target_from_plan

        plan_dir = tmp_path / "a1"
        plan_dir.mkdir()
        (plan_dir / "test.yaml").write_text("word_target: 1200\ntitle: Test")
        assert get_word_target_from_plan("a1", "test", plans_root=tmp_path) == 1200


class TestGetFinalReviewInfo:
    """get_final_review_info parses final review files."""

    def test_review_with_verdict_and_issues(self, tmp_path):
        from scripts.api.state_helpers import get_final_review_info

        review_dir = tmp_path / "review"
        review_dir.mkdir()
        text = (
            "===VERDICT=== APPROVE ===END_VERDICT===\n"
            "**ISSUE 1 — Grammar problem**\n"
            "**ISSUE 2 — Missing section**\n"
        )
        (review_dir / "test-final-review.md").write_text(text)
        result = get_final_review_info(tmp_path, "test", curriculum_root=tmp_path.parent)
        assert result is not None
        assert result["verdict"] == "APPROVE"
        assert result["issue_count"] == 2
        assert len(result["issues"]) == 2


# ==================== state_coverage ====================


# ==================== state_compute ====================


# ==================== state_build ====================


# ==================== state_issues ====================


class TestParseSingleIssueBlock:
    """_parse_single_issue_block extracts issue details."""

    def test_full_block(self):
        from scripts.api.state_issues import _parse_single_issue_block

        block = (
            "### Issue #1: Grammar error in section 3\n"
            "**Location** Section 3, paragraph 2\n"
            "**Fix** Change verb form to perfective\n\n"
        )
        result = _parse_single_issue_block(block, "test-review.md", "a1", "test", 1)
        assert result["title"] == "Grammar error in section 3"
        assert result["location"] == "Section 3, paragraph 2"
        assert "perfective" in result["fix"]
        assert result["severity"] == "critical"  # "grammar error" is critical
        assert result["source"] == "review"


class TestParseReviewBlocks:
    """parse_review_blocks splits text into issues."""

    def test_multiple_issues(self):
        from scripts.api.state_issues import parse_review_blocks

        text = (
            "# Review\n"
            "## Issue #1: First problem\nDetails\n"
            "## Issue #2: Second problem\nDetails\n"
        )
        issues = []
        parse_review_blocks(text, "test-review.md", "a1", "test", 1, issues)
        assert len(issues) == 2


# ==================== dashboard_helpers ====================


class TestScanTrackCached:
    """scan_track_cached returns cached results within TTL."""

    def test_cache_returns_same_result(self, tmp_path):
        from scripts.api.dashboard_helpers import _track_cache, _track_cache_key, scan_track_cached
        from scripts.api.monitor_context import fixture_context

        ctx = fixture_context(tmp_path)
        # Pre-populate cache under the ctx-scoped key the lookup uses (#7494)
        cached_data = {"track_id": "test", "modules": []}
        _track_cache[_track_cache_key("test_track", ctx)] = (time.time(), cached_data)
        result = scan_track_cached("test_track", "test_path", [], ctx=ctx)
        assert result == cached_data


# ==================== dashboard_comms ====================


# ==================== YAML escape (from test_api_v4.py pattern) ====================


# ==================== v5 pipeline state handling (#814) ====================


class TestComputeFinalReviewsV5:
    """compute_final_reviews detects v5 modules pending review."""

    def test_v5_validate_complete_is_pending(self, tmp_path):
        from scripts.api.state_issues import compute_final_reviews

        track_dir = tmp_path / "curriculum" / "l2-uk-en" / "a1"
        orch_dir = track_dir / "orchestration" / "test-slug"
        orch_dir.mkdir(parents=True)
        (track_dir / "review").mkdir(parents=True)
        (orch_dir / "state.json").write_text(json.dumps({
            "mode": "v5",
            "phases": {"validate": {"status": "complete"}},
        }))

        plan_slugs = [(1, "test-slug")]
        level_cfg = {"id": "a1", "path": "l2-uk-en/a1"}

        with (
            patch("scripts.api.state_issues.get_plan_slugs", return_value=plan_slugs),
            patch("scripts.api.state_issues.get_final_review_info", return_value=None),
        ):
            result = compute_final_reviews("a1", level_cfg, curriculum_root=tmp_path / "curriculum")

        assert result["pending_review"] == 1
        assert result["pending_modules"][0]["slug"] == "test-slug"


class TestComputeFinalReviewsV6:
    """compute_final_reviews detects v6 modules pending review."""

    def test_v6_audit_complete_is_pending(self, tmp_path):
        from scripts.api.state_issues import compute_final_reviews

        track_dir = tmp_path / "curriculum" / "l2-uk-en" / "a1"
        orch_dir = track_dir / "orchestration" / "test-slug"
        orch_dir.mkdir(parents=True)
        (track_dir / "review").mkdir(parents=True)
        (orch_dir / "state.json").write_text(json.dumps({
            "mode": "v6",
            "phases": {"audit": {"status": "complete"}},
        }))

        plan_slugs = [(1, "test-slug")]
        level_cfg = {"id": "a1", "path": "l2-uk-en/a1"}

        with (
            patch("scripts.api.state_issues.get_plan_slugs", return_value=plan_slugs),
            patch("scripts.api.state_issues.get_final_review_info", return_value=None),
        ):
            result = compute_final_reviews("a1", level_cfg, curriculum_root=tmp_path / "curriculum")

        assert result["pending_review"] == 1
        assert result["pending_modules"][0]["slug"] == "test-slug"
