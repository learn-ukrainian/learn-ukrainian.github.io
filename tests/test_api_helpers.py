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
from pathlib import Path
from unittest.mock import patch

# ==================== review_parsing ====================


class TestExtractReviewScore:
    """extract_review_score parses various score formats."""

    def test_bold_overall_score(self):
        from scripts.api.review_parsing import extract_review_score

        text = "Some text\n**Overall Score:** 8.5/10\nMore text"
        assert extract_review_score(text) == 8.5

    def test_plain_overall_score(self):
        from scripts.api.review_parsing import extract_review_score

        text = "Overall Score: 7/10"
        assert extract_review_score(text) == 7.0

    def test_bold_fraction_on_line(self):
        from scripts.api.review_parsing import extract_review_score

        text = "The score is **9/10**"
        assert extract_review_score(text) == 9.0

    def test_equals_bold_fraction(self):
        from scripts.api.review_parsing import extract_review_score

        text = "= **6.5/10**"
        assert extract_review_score(text) == 6.5

    def test_no_score_returns_none(self):
        from scripts.api.review_parsing import extract_review_score

        assert extract_review_score("No score here") is None

    def test_empty_string(self):
        from scripts.api.review_parsing import extract_review_score

        assert extract_review_score("") is None


class TestExtractReviewVerdict:
    """extract_review_verdict parses PASS/FAIL."""

    def test_pass_verdict(self):
        from scripts.api.review_parsing import extract_review_verdict

        assert extract_review_verdict("**Status:** PASS") == "PASS"

    def test_fail_verdict(self):
        from scripts.api.review_parsing import extract_review_verdict

        assert extract_review_verdict("Status: FAIL") == "FAIL"

    def test_case_insensitive(self):
        from scripts.api.review_parsing import extract_review_verdict

        assert extract_review_verdict("Status: pass") == "PASS"

    def test_no_verdict(self):
        from scripts.api.review_parsing import extract_review_verdict

        assert extract_review_verdict("No verdict here") is None


class TestExtractPlanVerdict:
    """extract_plan_verdict parses plan review verdicts."""

    def test_pass(self):
        from scripts.api.review_parsing import extract_plan_verdict

        assert extract_plan_verdict("**Verdict:** PASS") == "PASS"

    def test_needs_fixes(self):
        from scripts.api.review_parsing import extract_plan_verdict

        assert extract_plan_verdict("Verdict: NEEDS FIXES") == "NEEDS FIXES"

    def test_fail(self):
        from scripts.api.review_parsing import extract_plan_verdict

        assert extract_plan_verdict("**Verdict**: FAIL") == "FAIL"

    def test_no_verdict(self):
        from scripts.api.review_parsing import extract_plan_verdict

        assert extract_plan_verdict("no verdict") is None


class TestCountReviewIssues:
    """count_review_issues counts issue headers."""

    def test_counts_issues(self):
        from scripts.api.review_parsing import count_review_issues

        text = "# Issue #1\ntext\n## Issue #2\ntext\n### Issue 3\ntext"
        assert count_review_issues(text) == 3

    def test_no_issues(self):
        from scripts.api.review_parsing import count_review_issues

        assert count_review_issues("No issues here") == 0

    def test_empty_string(self):
        from scripts.api.review_parsing import count_review_issues

        assert count_review_issues("") == 0


# ==================== state_helpers ====================


class TestToBareSlug:
    """to_bare_slug strips numeric prefix."""

    def test_strips_numeric_prefix(self):
        from scripts.api.state_helpers import to_bare_slug

        assert to_bare_slug("01-the-cyrillic-code") == "the-cyrillic-code"

    def test_no_prefix(self):
        from scripts.api.state_helpers import to_bare_slug

        assert to_bare_slug("greetings") == "greetings"

    def test_strips_comment(self):
        from scripts.api.state_helpers import to_bare_slug

        assert to_bare_slug("my-slug # comment") == "my-slug"

    def test_empty_string(self):
        from scripts.api.state_helpers import to_bare_slug

        assert to_bare_slug("") == ""

    def test_prefix_with_comment(self):
        from scripts.api.state_helpers import to_bare_slug

        assert to_bare_slug("05-lesson # note") == "lesson"


class TestDetectPipelineVersionHelpers:
    """detect_pipeline_version from state_helpers."""

    def test_v5_from_state_json(self, tmp_path):
        from scripts.api.state_helpers import detect_pipeline_version

        (tmp_path / "state.json").write_text('{"mode": "v5", "phases": {}}')
        assert detect_pipeline_version(tmp_path) == "v5"

    def test_state_v4_is_ignored(self, tmp_path):
        from scripts.api.state_helpers import detect_pipeline_version

        (tmp_path / "state-v4.json").write_text('{"mode": "v4"}')
        assert detect_pipeline_version(tmp_path) == "unbuilt"

    def test_v3_from_state_v3(self, tmp_path):
        from scripts.api.state_helpers import detect_pipeline_version

        (tmp_path / "state-v3.json").write_text('{"phases": {}}')
        assert detect_pipeline_version(tmp_path) == "v3"

    def test_unbuilt_empty_dir(self, tmp_path):
        from scripts.api.state_helpers import detect_pipeline_version

        assert detect_pipeline_version(tmp_path) == "unbuilt"

    def test_v5_takes_priority(self, tmp_path):
        from scripts.api.state_helpers import detect_pipeline_version

        (tmp_path / "state.json").write_text('{"mode": "v5"}')
        (tmp_path / "state-v4.json").write_text('{"mode": "v4"}')
        assert detect_pipeline_version(tmp_path) == "v5"

    def test_v4_mode_in_state_json_is_ignored(self, tmp_path):
        from scripts.api.state_helpers import detect_pipeline_version

        (tmp_path / "state.json").write_text('{"mode": "v4"}')
        assert detect_pipeline_version(tmp_path) == "unbuilt"

    def test_invalid_json_returns_unbuilt(self, tmp_path):
        from scripts.api.state_helpers import detect_pipeline_version

        (tmp_path / "state.json").write_text("not json{{{")
        assert detect_pipeline_version(tmp_path) == "unbuilt"


class TestReadStateFiles:
    """read_v3_state and read_v2_state."""

    def test_read_v3_state_valid(self, tmp_path):
        from scripts.api.state_helpers import read_v3_state

        data = {"phases": {"v3-A": {"status": "complete"}}}
        (tmp_path / "state-v3.json").write_text(json.dumps(data))
        assert read_v3_state(tmp_path) == data

    def test_read_v3_state_missing(self, tmp_path):
        from scripts.api.state_helpers import read_v3_state

        assert read_v3_state(tmp_path) == {}

    def test_read_v2_state_valid(self, tmp_path):
        from scripts.api.state_helpers import read_v2_state

        data = {"mode": "v5", "phases": {"research": {"status": "complete"}}}
        (tmp_path / "state.json").write_text(json.dumps(data))
        assert read_v2_state(tmp_path) == data

    def test_read_v2_state_missing(self, tmp_path):
        from scripts.api.state_helpers import read_v2_state

        assert read_v2_state(tmp_path) == {}


class TestParsePhaseStatus:
    """Phase status parsing functions."""

    def test_v5_complete(self):
        from scripts.api.state_helpers import parse_v5_phase_status

        v5 = {"phases": {"sandbox": {"status": "complete", "ts": "2026-02-01"}}}
        result = parse_v5_phase_status(v5, "sandbox")
        assert result["status"] == "complete"

    def test_v5_missing(self):
        from scripts.api.state_helpers import parse_v5_phase_status

        assert parse_v5_phase_status({"phases": {}}, "sandbox")["status"] == "pending"

    def test_v3_with_mode_and_attempts(self):
        from scripts.api.state_helpers import parse_v3_phase_status

        v3 = {"phases": {"v3-A": {"status": "complete", "mode": "gemini", "ts": "t1", "attempts": 2}}}
        result = parse_v3_phase_status(v3, "v3-A")
        assert result["status"] == "complete"
        assert result["mode"] == "gemini"
        assert result["attempts"] == 2

    def test_v3_missing(self):
        from scripts.api.state_helpers import parse_v3_phase_status

        assert parse_v3_phase_status({}, "v3-A")["status"] == "pending"

    def test_parse_phase_from_unified_state(self):
        from scripts.api.state_helpers import parse_phase_status_from_state

        state = {"phases": {"research": {"status": "complete", "ts": "t1", "mode": "gemini"}}}
        result = parse_phase_status_from_state(state, "research")
        assert result["status"] == "complete"
        assert result["ts"] == "t1"
        assert result["mode"] == "gemini"

    def test_parse_phase_missing(self):
        from scripts.api.state_helpers import parse_phase_status_from_state

        result = parse_phase_status_from_state({"phases": {}}, "research")
        assert result["status"] == "pending"
        assert "ts" not in result


class TestCacheFunctions:
    """TTL cache get/set."""

    def test_cache_hit(self):
        from scripts.api.state_helpers import cache_get, cache_set

        cache_set("test_key_1", "value1")
        assert cache_get("test_key_1", ttl=60.0) == "value1"

    def test_cache_miss(self):
        from scripts.api.state_helpers import cache_get

        assert cache_get("nonexistent_key_xyz", ttl=60.0) is None

    def test_cache_expired(self):
        from scripts.api.state_helpers import _ttl_cache, cache_get

        # TTL timestamps use time.monotonic() (GH #1309 / reviewer
        # BLOCKER B4 — resilience to wall-clock jumps / NTP skew), so
        # a simulated "old" entry must also be on the monotonic clock.
        _ttl_cache["test_expired"] = (time.monotonic() - 100, "old_value")
        assert cache_get("test_expired", ttl=10.0) is None

    def test_cache_invalidate_by_prefix(self):
        """cache_invalidate(prefix) drops matching keys only.

        Used by `/api/orient?fresh=true` (BLOCKER B3 / GH #1309) to
        bypass its own section caches without touching unrelated
        caches in other routers.
        """
        from scripts.api.state_helpers import (
            _ttl_cache,
            cache_get,
            cache_invalidate,
            cache_set,
        )

        cache_set("orient_git", "g")
        cache_set("orient_issues", "i")
        cache_set("summary", "s")

        dropped = cache_invalidate("orient_")

        assert dropped == 2
        assert cache_get("orient_git", ttl=60.0) is None
        assert cache_get("orient_issues", ttl=60.0) is None
        # Unrelated key must survive.
        assert cache_get("summary", ttl=60.0) == "s"

        # Cleanup — prefix="" clears everything, used by tests.
        _ttl_cache.clear()

    def test_cache_invalidate_default_clears_all(self):
        from scripts.api.state_helpers import (
            _ttl_cache,
            cache_invalidate,
            cache_set,
        )

        cache_set("a", 1)
        cache_set("b", 2)
        assert cache_invalidate() == 2
        assert _ttl_cache == {}


class TestFindContentFile:
    """find_content_file locates markdown files."""

    def test_exact_match(self, tmp_path):
        from scripts.api.state_helpers import find_content_file

        (tmp_path / "my-slug.md").write_text("content")
        assert find_content_file(tmp_path, "my-slug") == tmp_path / "my-slug.md"

    def test_numbered_match(self, tmp_path):
        from scripts.api.state_helpers import find_content_file

        (tmp_path / "01-my-slug.md").write_text("content")
        assert find_content_file(tmp_path, "my-slug") == tmp_path / "01-my-slug.md"

    def test_no_match(self, tmp_path):
        from scripts.api.state_helpers import find_content_file

        assert find_content_file(tmp_path, "nonexistent") is None


class TestHasResearchFile:
    """has_research_file checks for research markdown."""

    def test_exists(self, tmp_path):
        from scripts.api.state_helpers import has_research_file

        (tmp_path / "research").mkdir()
        (tmp_path / "research" / "my-slug-research.md").write_text("research content")
        assert has_research_file(tmp_path, "my-slug") is True

    def test_not_exists(self, tmp_path):
        from scripts.api.state_helpers import has_research_file

        assert has_research_file(tmp_path, "nonexistent") is False


class TestGetAuditStatus:
    """get_audit_status reads status JSON files."""

    def test_not_run(self, tmp_path):
        from scripts.api.state_helpers import get_audit_status

        result = get_audit_status(tmp_path, "missing-slug")
        assert result["status"] == "not_run"
        assert result["word_count"] == 0

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

    def test_stale_audit(self, tmp_path):
        import time as t

        from scripts.api.state_helpers import get_audit_status

        (tmp_path / "status").mkdir()
        status_file = tmp_path / "status" / "test.json"
        status_file.write_text(json.dumps({"overall": {"status": "pass"}, "gates": {}}))
        # Make content file newer
        t.sleep(0.05)
        (tmp_path / "test.md").write_text("newer content here with many words")
        result = get_audit_status(tmp_path, "test")
        assert result["status"] == "stale"

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

    def test_no_hash(self, tmp_path):
        from scripts.api.state_helpers import extract_content_hash

        review = tmp_path / "review.md"
        review.write_text("# Review\nNo hash here")
        assert extract_content_hash(review) is None

    def test_missing_file(self, tmp_path):
        from scripts.api.state_helpers import extract_content_hash

        assert extract_content_hash(tmp_path / "missing.md") is None


class TestIsReviewStale:
    """is_review_stale checks if review is older than content."""

    def test_no_content_not_stale(self, tmp_path):
        from scripts.api.state_helpers import is_review_stale

        review = tmp_path / "review.md"
        review.write_text("review")
        assert is_review_stale(review, None) is False

    def test_stale_by_mtime(self, tmp_path):
        import time as t

        from scripts.api.state_helpers import is_review_stale

        review = tmp_path / "review.md"
        review.write_text("old review")
        t.sleep(0.05)
        content = tmp_path / "content.md"
        content.write_text("new content")
        assert is_review_stale(review, content) is True

    def test_not_stale_by_hash_match(self, tmp_path):
        import hashlib

        from scripts.api.state_helpers import is_review_stale

        content = tmp_path / "content.md"
        content.write_text("some content")
        content_hash = hashlib.md5(content.read_bytes(), usedforsecurity=False).hexdigest()[:12]
        review = tmp_path / "review.md"
        review.write_text(f"<!-- content-hash: {content_hash} -->\n# Review")
        assert is_review_stale(review, content) is False

    def test_missing_review_not_stale(self, tmp_path):
        from scripts.api.state_helpers import is_review_stale

        content = tmp_path / "content.md"
        content.write_text("some content")

        assert is_review_stale(tmp_path / "missing-review.md", content) is False

    def test_hash_read_oserror_returns_not_stale(self, tmp_path):
        from scripts.api.state_helpers import is_review_stale

        content = tmp_path / "content.md"
        content.write_text("some content")
        review = tmp_path / "review.md"
        review.write_text("<!-- content-hash: abc123def456 -->\n# Review")

        with patch.object(Path, "read_bytes", side_effect=OSError("boom")):
            assert is_review_stale(review, content) is False


class TestGetWordTargetFromPlan:
    """get_word_target_from_plan reads plan YAML."""

    def test_reads_target(self, tmp_path):
        from scripts.api.state_helpers import get_word_target_from_plan

        with patch("scripts.api.state_helpers.PLANS_ROOT", tmp_path):
            plan_dir = tmp_path / "a1"
            plan_dir.mkdir()
            (plan_dir / "test.yaml").write_text("word_target: 1200\ntitle: Test")
            assert get_word_target_from_plan("a1", "test") == 1200

    def test_missing_plan(self, tmp_path):
        from scripts.api.state_helpers import get_word_target_from_plan

        with patch("scripts.api.state_helpers.PLANS_ROOT", tmp_path):
            assert get_word_target_from_plan("a1", "missing") == 0


class TestGetFinalReviewInfo:
    """get_final_review_info parses final review files."""

    def test_no_review_file(self, tmp_path):
        from scripts.api.state_helpers import get_final_review_info

        assert get_final_review_info(tmp_path, "missing") is None

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
        with patch("scripts.api.state_helpers.CURRICULUM_ROOT", tmp_path):
            result = get_final_review_info(tmp_path, "test")
        assert result is not None
        assert result["verdict"] == "APPROVE"
        assert result["issue_count"] == 2
        assert len(result["issues"]) == 2

    def test_review_no_verdict(self, tmp_path):
        from scripts.api.state_helpers import get_final_review_info

        review_dir = tmp_path / "review"
        review_dir.mkdir()
        (review_dir / "test-final-review.md").write_text("Some review without verdict")
        with patch("scripts.api.state_helpers.CURRICULUM_ROOT", tmp_path):
            result = get_final_review_info(tmp_path, "test")
        assert result is not None
        assert result["verdict"] is None


# ==================== state_coverage ====================


class TestComputePipelineTrack:
    """compute_pipeline_track exposes canonical v6 phase shape."""

    def test_v6_phase_order_and_labels(self):
        from scripts.api.state_coverage import compute_pipeline_track
        from scripts.build.v6_build import PHASE_LABELS, PHASES

        level_cfg = {"id": "a1", "path": "l2-uk-en/a1"}
        plan_slugs = [(1, "test-slug")]
        state = {
            "mode": "v6",
            "phases": {
                "check": {"status": "complete"},
                "review": {"status": "running"},
            },
        }

        with (
            patch("scripts.api.state_coverage.get_plan_slugs", return_value=plan_slugs),
            patch("scripts.api.state_coverage.detect_pipeline_version", return_value="v6"),
            patch("scripts.api.state_coverage.load_module_state", return_value=state),
            patch(
                "scripts.api.state_coverage.get_audit_status",
                return_value={"status": "pass", "word_count": 1234, "word_target": 1500},
            ),
            patch("scripts.api.state_coverage.get_research_score", return_value=8),
        ):
            result = compute_pipeline_track("a1", level_cfg)

        module = result["modules"][0]
        assert result["phase_order"] == PHASES
        assert result["phase_labels"]["review"] == PHASE_LABELS["review"]
        assert list(module["phases"]) == PHASES
        assert module["phases"]["check"]["status"] == "complete"
        assert module["phases"]["review"]["status"] == "running"
        assert module["phases"]["audit"]["status"] == "pending"
        assert module["needs_rebuild"] is False


# ==================== state_compute ====================


class TestSeverityKey:
    """severity_key sorts weak-point modules."""

    def test_audit_fail_highest(self):
        from scripts.api.state_compute import severity_key

        m = {"issues": ["audit_fail", "low_words"]}
        assert severity_key(m) == -110

    def test_research_score_medium(self):
        from scripts.api.state_compute import severity_key

        m = {"issues": ["research_score"]}
        assert severity_key(m) == -50

    def test_low_words_lowest(self):
        from scripts.api.state_compute import severity_key

        m = {"issues": ["low_words"]}
        assert severity_key(m) == -10

    def test_empty_issues(self):
        from scripts.api.state_compute import severity_key

        m = {"issues": []}
        assert severity_key(m) == 0



class TestGetPhasesForVersion:
    """get_phases_for_version returns correct phase dict per version."""

    def test_v5_phases(self, tmp_path):
        from scripts.api.state_compute import get_phases_for_version

        (tmp_path / "state.json").write_text(json.dumps({
            "mode": "v5",
            "phases": {"research": {"status": "complete"}, "content": {"status": "running"}},
        }))
        phases = get_phases_for_version(tmp_path, "v5")
        assert phases["research"]["status"] == "complete"
        assert phases["content"]["status"] == "running"

    def test_unknown_version_falls_back_to_pending_v3_shape(self, tmp_path):
        from scripts.api.state_compute import get_phases_for_version

        (tmp_path / "state-v4.json").write_text(json.dumps({
            "phases": {"v4-research": {"status": "complete"}},
        }))
        phases = get_phases_for_version(tmp_path, "v4")
        assert set(phases) == {"A", "B", "C", "audit", "D", "E", "F"}
        assert all(phase["status"] == "pending" for phase in phases.values())

    def test_v3_phases(self, tmp_path):
        from scripts.api.state_compute import get_phases_for_version

        (tmp_path / "state-v3.json").write_text(json.dumps({
            "phases": {"v3-A": {"status": "complete"}},
        }))
        phases = get_phases_for_version(tmp_path, "v3")
        assert phases["A"]["status"] == "complete"

    def test_unbuilt_phases(self, tmp_path):
        from scripts.api.state_compute import get_phases_for_version

        phases = get_phases_for_version(tmp_path, "unbuilt")
        # v3 fallback — all pending
        for key in phases:
            assert phases[key]["status"] == "pending"


# ==================== state_build ====================


class TestComputeETA:
    """compute_eta calculates remaining time."""

    def test_sufficient_timestamps(self):
        from scripts.api.state_build import compute_eta

        # 3 completions over 30 minutes → rate = 2/30 per min
        times = [
            "2026-03-01T10:00:00Z",
            "2026-03-01T10:15:00Z",
            "2026-03-01T10:30:00Z",
        ]
        eta = compute_eta(times, 10)
        assert eta is not None
        assert eta > 0

    def test_insufficient_timestamps(self):
        from scripts.api.state_build import compute_eta

        assert compute_eta(["2026-03-01T10:00:00Z"], 10) is None

    def test_empty_timestamps(self):
        from scripts.api.state_build import compute_eta

        assert compute_eta([], 10) is None

    def test_two_timestamps_insufficient(self):
        from scripts.api.state_build import compute_eta

        assert compute_eta(["2026-03-01T10:00:00Z", "2026-03-01T10:15:00Z"], 10) is None


class TestScanModulePhases:
    """scan_module_phases reads pipeline progress."""

    def test_v6_uses_full_phase_order(self, tmp_path):
        from scripts.api.state_build import scan_module_phases

        (tmp_path / "state.json").write_text(json.dumps({
            "mode": "v6",
            "phases": {
                "check": {"status": "complete", "ts": "t1"},
                "review": {"status": "complete", "ts": "t2"},
                "audit": {"status": "running", "ts": "t3"},
            },
        }))
        furthest, running, _latest_ts, audit_status = scan_module_phases(tmp_path, "v6")
        assert furthest == "review"
        assert running == "audit"
        assert audit_status == "running"

    def test_v5_complete_phases(self, tmp_path):
        from scripts.api.state_build import scan_module_phases

        (tmp_path / "state.json").write_text(json.dumps({
            "mode": "v5",
            "phases": {
                "research": {"status": "complete", "ts": "t1"},
                "content": {"status": "complete", "ts": "t2"},
                "validate": {"status": "complete", "ts": "t3"},
            },
        }))
        furthest, running, _latest_ts, audit_status = scan_module_phases(tmp_path, "v5")
        assert furthest == "validate"
        assert running is None
        assert audit_status == "complete"

    def test_v5_running_phase(self, tmp_path):
        from scripts.api.state_build import scan_module_phases

        (tmp_path / "state.json").write_text(json.dumps({
            "mode": "v5",
            "phases": {
                "research": {"status": "complete"},
                "content": {"status": "running"},
            },
        }))
        furthest, running, _, _ = scan_module_phases(tmp_path, "v5")
        assert furthest == "research"
        assert running == "content"

    def test_v3_phases(self, tmp_path):
        from scripts.api.state_build import scan_module_phases

        (tmp_path / "state-v3.json").write_text(json.dumps({
            "phases": {
                "v3-A": {"status": "complete"},
                "v3-B": {"status": "failed"},
            },
        }))
        furthest, running, _, _ = scan_module_phases(tmp_path, "v3")
        assert furthest == "A"
        assert running == "B(FAIL)"

    def test_unknown_version_is_ignored(self, tmp_path):
        from scripts.api.state_build import scan_module_phases

        (tmp_path / "state-v4.json").write_text(json.dumps({
            "phases": {
                "v4-research": {"status": "complete"},
                "v4-validate": {"status": "complete"},
            },
        }))
        furthest, running, _latest_ts, audit_status = scan_module_phases(tmp_path, "v4")
        assert furthest is None
        assert running is None
        assert audit_status is None

    def test_empty_phases(self, tmp_path):
        from scripts.api.state_build import scan_module_phases

        (tmp_path / "state.json").write_text('{"mode":"v5","phases":{}}')
        furthest, running, _latest_ts, _audit_status = scan_module_phases(tmp_path, "v5")
        assert furthest is None
        assert running is None


class TestCheckBuildPhase:
    """_check_build_phase checks v3-B completion."""

    def test_complete(self, tmp_path):
        from scripts.api.state_build import _check_build_phase

        (tmp_path / "state-v3.json").write_text(json.dumps({
            "phases": {"v3-B": {"status": "complete", "ts": "2026-01-01"}},
        }))
        built, ts = _check_build_phase(tmp_path)
        assert built == 1
        assert ts == "2026-01-01"

    def test_not_complete(self, tmp_path):
        from scripts.api.state_build import _check_build_phase

        (tmp_path / "state-v3.json").write_text(json.dumps({"phases": {}}))
        built, ts = _check_build_phase(tmp_path)
        assert built == 0
        assert ts is None

    def test_v4_no_longer_counts_as_built(self, tmp_path):
        from scripts.api.state_build import _check_build_phase

        (tmp_path / "state-v4.json").write_text(json.dumps({
            "phases": {"v4-content": {"status": "complete", "ts": "2026-01-02"}},
        }))
        built, ts = _check_build_phase(tmp_path)
        assert built == 0
        assert ts is None


class TestCheckAuditHealth:
    """_check_audit_health categorizes audit results."""

    def test_pass(self):
        from scripts.api.state_build import _check_audit_health

        ap, af, att = _check_audit_health({"status": "pass"}, 1, "slug")
        assert ap == 1
        assert af == 0
        assert att is None

    def test_fail(self):
        from scripts.api.state_build import _check_audit_health

        audit = {"status": "fail", "blocking_issues": [{"gate": "words"}]}
        ap, af, att = _check_audit_health(audit, 1, "slug")
        assert ap == 0
        assert af == 1
        assert att is not None
        assert att["reason"] == "audit_fail"

    def test_other_status(self):
        from scripts.api.state_build import _check_audit_health

        ap, af, att = _check_audit_health({"status": "not_run"}, 1, "slug")
        assert ap == 0
        assert af == 0
        assert att is None


class TestCheckFinalReviewHealth:
    """_check_final_review_health checks final review outcomes."""

    def test_approved(self, tmp_path):
        from scripts.api.state_build import _check_final_review_health

        review_dir = tmp_path / "review"
        review_dir.mkdir()
        (review_dir / "test-final-review.md").write_text(
            "===VERDICT=== APPROVE ===END_VERDICT==="
        )
        with patch("scripts.api.state_build.get_final_review_info") as mock_fri:
            mock_fri.return_value = {"verdict": "APPROVE", "issue_count": 0, "issues": []}
            r, a, att = _check_final_review_health(tmp_path, 1, "test")
        assert r == 1
        assert a == 1
        assert att is None

    def test_rejected(self, tmp_path):
        from scripts.api.state_build import _check_final_review_health

        with patch("scripts.api.state_build.get_final_review_info") as mock_fri:
            mock_fri.return_value = {"verdict": "REJECT", "issue_count": 3, "issues": []}
            r, a, att = _check_final_review_health(tmp_path, 1, "test")
        assert r == 1
        assert a == 0
        assert att is not None

    def test_no_review(self, tmp_path):
        from scripts.api.state_build import _check_final_review_health

        with patch("scripts.api.state_build.get_final_review_info") as mock_fri:
            mock_fri.return_value = None
            r, a, _att = _check_final_review_health(tmp_path, 1, "test")
        assert r == 0
        assert a == 0


# ==================== state_issues ====================


class TestCountIssuePatterns:
    """count_issue_patterns counts keyword occurrences."""

    def test_counts_keywords(self):
        from scripts.api.state_issues import count_issue_patterns

        issues = [
            {"summary": "FACTUAL error found"},
            {"summary": "FACTUAL mistake in section 2"},
            {"summary": "ACTIVITY incorrectly designed"},
            {"summary": "RUSSICISM: кот instead of кіт"},
        ]
        counts = count_issue_patterns(issues)
        assert counts["FACTUAL"] == 2
        assert counts["ACTIVITY"] == 1
        assert counts["RUSSICISM"] == 1

    def test_empty_list(self):
        from scripts.api.state_issues import count_issue_patterns

        assert count_issue_patterns([]) == {}

    def test_no_matching_keywords(self):
        from scripts.api.state_issues import count_issue_patterns

        issues = [{"summary": "Something unrelated"}]
        assert count_issue_patterns(issues) == {}


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

    def test_final_review_source(self):
        from scripts.api.state_issues import _parse_single_issue_block

        block = "## Issue #1: Minor note\nSome description\n"
        result = _parse_single_issue_block(block, "test-final-review.md", "a1", "test", 1)
        assert result["source"] == "final-review"

    def test_warning_severity(self):
        from scripts.api.state_issues import _parse_single_issue_block

        block = "## Issue #1: Style suggestion\nMinor style concern\n"
        result = _parse_single_issue_block(block, "test-review.md", "a1", "test", 1)
        assert result["severity"] == "warning"


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

    def test_no_issues(self):
        from scripts.api.state_issues import parse_review_blocks

        issues = []
        parse_review_blocks("Just text, no issues", "test-review.md", "a1", "test", 1, issues)
        assert len(issues) == 0


class TestCollectAuditIssues:
    """collect_audit_issues adds audit failures."""

    def test_fail_adds_issues(self, tmp_path):
        from scripts.api.state_issues import collect_audit_issues

        (tmp_path / "status").mkdir()
        data = {
            "overall": {"status": "fail"},
            "gates": {
                "lesson": {"status": "fail", "message": "800 / 1200 words"},
                "activities": {"status": "pass", "message": "ok"},
            },
        }
        (tmp_path / "status" / "test.json").write_text(json.dumps(data))
        issues = []
        collect_audit_issues(tmp_path, "a1", "test", 1, issues)
        assert len(issues) == 1
        assert issues[0]["severity"] == "critical"
        assert "lesson" in issues[0]["title"]

    def test_pass_adds_nothing(self, tmp_path):
        from scripts.api.state_issues import collect_audit_issues

        (tmp_path / "status").mkdir()
        (tmp_path / "status" / "test.json").write_text(
            json.dumps({"overall": {"status": "pass"}, "gates": {}})
        )
        issues = []
        collect_audit_issues(tmp_path, "a1", "test", 1, issues)
        assert len(issues) == 0


class TestCriticalKeywords:
    """CRITICAL_KEYWORDS are properly defined."""

    def test_critical_keywords_is_frozenset(self):
        from scripts.api.state_issues import CRITICAL_KEYWORDS

        assert isinstance(CRITICAL_KEYWORDS, frozenset)
        assert "factual error" in CRITICAL_KEYWORDS
        assert "grammar error" in CRITICAL_KEYWORDS

    def test_issue_pattern_keywords_is_list(self):
        from scripts.api.state_issues import ISSUE_PATTERN_KEYWORDS

        assert isinstance(ISSUE_PATTERN_KEYWORDS, list)
        assert "FACTUAL" in ISSUE_PATTERN_KEYWORDS
        assert "RUSSICISM" in ISSUE_PATTERN_KEYWORDS


# ==================== dashboard_helpers ====================


class TestParseSlug:
    """parse_slug extracts slug from manifest entries."""

    def test_string_entry(self):
        from scripts.api.dashboard_helpers import parse_slug

        assert parse_slug("my-slug") == "my-slug"

    def test_string_with_comment(self):
        from scripts.api.dashboard_helpers import parse_slug

        assert parse_slug("my-slug # comment") == "my-slug"

    def test_non_string_entry(self):
        from scripts.api.dashboard_helpers import parse_slug

        assert parse_slug(42) == "42"


class TestScanTrackCached:
    """scan_track_cached returns cached results within TTL."""

    def test_cache_returns_same_result(self):
        from scripts.api.dashboard_helpers import _track_cache, scan_track_cached

        # Pre-populate cache
        cached_data = {"track_id": "test", "modules": []}
        _track_cache["test_track"] = (time.time(), cached_data)
        result = scan_track_cached("test_track", "test_path", [])
        assert result == cached_data

    def test_expired_cache_calls_scan(self):
        from scripts.api.dashboard_helpers import _track_cache

        # Set expired cache entry
        _track_cache["expired_track"] = (time.time() - 100, {"old": True})
        # Don't actually call scan_track — just verify cache is expired
        entry = _track_cache.get("expired_track")
        assert entry is not None
        assert (time.time() - entry[0]) > 30  # past TTL


class TestScanTrackSummaryCached:
    """scan_track_summary_cached returns cached results within TTL."""

    def test_cache_returns_same_result(self):
        from scripts.api.dashboard_helpers import _summary_cache, scan_track_summary_cached

        cached_data = {"track_id": "test", "modules": []}
        _summary_cache["test_summary"] = (time.time(), cached_data)
        result = scan_track_summary_cached("test_summary", "test_path", [])
        assert result == cached_data

    def test_expired_cache_is_stale(self):
        from scripts.api.dashboard_helpers import _summary_cache

        _summary_cache["expired_summary"] = (time.time() - 100, {"old": True})
        entry = _summary_cache.get("expired_summary")
        assert entry is not None
        assert (time.time() - entry[0]) > 60  # past TTL


class TestBuildModuleSummary:
    """build_module_summary returns lightweight module info."""

    def test_missing_module(self, tmp_path):
        from scripts.api.dashboard_helpers import build_module_summary

        track_dir = tmp_path / "track"
        track_dir.mkdir()
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()

        result = build_module_summary(track_dir, plans_dir, "test", "nonexistent", 0)
        assert result["slug"] == "nonexistent"
        assert result["num"] == 1
        assert result["status"] == "missing"
        assert result["pipeline_version"] == "unbuilt"
        assert result["has_review"] is False

    def test_summary_has_expected_keys(self, tmp_path):
        from scripts.api.dashboard_helpers import build_module_summary

        track_dir = tmp_path / "track"
        track_dir.mkdir()
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()

        result = build_module_summary(track_dir, plans_dir, "test", "slug", 2)
        expected_keys = {"slug", "num", "status", "pipeline_version", "has_review",
                         "has_final_review", "has_plan_review", "plan_review_verdict"}
        assert set(result.keys()) == expected_keys
        assert result["num"] == 3  # idx + 1


# ==================== dashboard_comms ====================


class TestIsWatcherRunning:
    """is_watcher_running checks PID file."""

    def test_no_pid_file(self, tmp_path):
        from scripts.api.dashboard_comms import is_watcher_running

        with patch("scripts.api.dashboard_comms.WATCHER_PID_FILE", tmp_path / "nonexistent.pid"):
            result = is_watcher_running()
        assert result["running"] is False
        assert result["pid"] is None

    def test_invalid_pid(self, tmp_path):
        from scripts.api.dashboard_comms import is_watcher_running

        pid_file = tmp_path / "watcher.pid"
        pid_file.write_text("not_a_number")
        with patch("scripts.api.dashboard_comms.WATCHER_PID_FILE", pid_file):
            result = is_watcher_running()
        assert result["running"] is False

    def test_dead_process(self, tmp_path):
        from scripts.api.dashboard_comms import is_watcher_running

        pid_file = tmp_path / "watcher.pid"
        pid_file.write_text("999999999")  # very unlikely to be running
        with patch("scripts.api.dashboard_comms.WATCHER_PID_FILE", pid_file):
            result = is_watcher_running()
        assert result["running"] is False
        assert result["pid"] == 999999999


class TestCollectStuckTasks:
    """collect_stuck_tasks reads stuck markdown files."""

    def test_no_stuck_dir(self, tmp_path):
        from scripts.api.dashboard_comms import collect_stuck_tasks

        with patch("scripts.api.dashboard_comms.STUCK_DIR", tmp_path / "nonexistent"), \
             patch("scripts.api.dashboard_comms.CURRICULUM_ROOT", tmp_path):
            result = collect_stuck_tasks()
        assert result == []

    def test_stuck_files_collected(self, tmp_path):
        from scripts.api.dashboard_comms import collect_stuck_tasks

        stuck_dir = tmp_path / "stuck"
        stuck_dir.mkdir()
        (stuck_dir / "task-1.md").write_text("Stuck on word count")
        (stuck_dir / "task-2.md").write_text("Stuck on activities")
        with patch("scripts.api.dashboard_comms.STUCK_DIR", stuck_dir), \
             patch("scripts.api.dashboard_comms.CURRICULUM_ROOT", tmp_path):
            result = collect_stuck_tasks()
        assert len(result) == 2
        assert result[0]["task_id"] == "task-1"
        assert "Stuck on word count" in result[0]["preview"]

    def test_track_stuck_dirs(self, tmp_path):
        from scripts.api.dashboard_comms import collect_stuck_tasks

        track = tmp_path / "a1"
        track.mkdir()
        stuck = track / "stuck"
        stuck.mkdir()
        (stuck / "issue.md").write_text("track-level stuck task")
        with patch("scripts.api.dashboard_comms.STUCK_DIR", tmp_path / "nonexistent"), \
             patch("scripts.api.dashboard_comms.CURRICULUM_ROOT", tmp_path):
            result = collect_stuck_tasks()
        assert len(result) == 1
        assert "a1/" in result[0]["file"]


class TestGetWatcherLogTail:
    """get_watcher_log_tail reads last N lines."""

    def test_no_log_file(self, tmp_path):
        from scripts.api.dashboard_comms import get_watcher_log_tail

        with patch("scripts.api.dashboard_comms.WATCHER_LOG_FILE", tmp_path / "missing.log"):
            assert get_watcher_log_tail() == []

    def test_reads_last_lines(self, tmp_path):
        from scripts.api.dashboard_comms import get_watcher_log_tail

        log_file = tmp_path / "watcher.log"
        log_file.write_text("\n".join(f"line {i}" for i in range(50)))
        with patch("scripts.api.dashboard_comms.WATCHER_LOG_FILE", log_file):
            lines = get_watcher_log_tail(5)
        assert len(lines) == 5
        assert lines[-1] == "line 49"


class TestReadDispatcherState:
    """read_dispatcher_state reads JSON from disk."""

    def test_valid_state(self, tmp_path):
        from scripts.api.dashboard_comms import read_dispatcher_state

        state_dir = tmp_path / "batch_state"
        state_dir.mkdir()
        (state_dir / "dispatcher_state.json").write_text('{"running": true, "queue": []}')
        with patch("scripts.api.dashboard_comms.BATCH_STATE_DIR", state_dir):
            result = read_dispatcher_state()
        assert result["running"] is True

    def test_missing_state(self, tmp_path):
        from scripts.api.dashboard_comms import read_dispatcher_state

        with patch("scripts.api.dashboard_comms.BATCH_STATE_DIR", tmp_path):
            result = read_dispatcher_state()
        assert result == {}

    def test_invalid_json(self, tmp_path):
        from scripts.api.dashboard_comms import read_dispatcher_state

        state_dir = tmp_path / "batch_state"
        state_dir.mkdir()
        (state_dir / "dispatcher_state.json").write_text("broken{{{")
        with patch("scripts.api.dashboard_comms.BATCH_STATE_DIR", state_dir):
            result = read_dispatcher_state()
        assert result == {}


class TestGetBrokerDb:
    """get_broker_db returns connection or None."""

    def test_missing_db(self, tmp_path):
        from scripts.api.dashboard_comms import get_broker_db

        with patch("scripts.api.dashboard_comms.MESSAGE_DB", tmp_path / "missing.db"):
            assert get_broker_db() is None


class TestEnsureBrokerCols:
    """ensure_broker_cols caches column names."""

    def test_caches_columns(self, tmp_path):
        import sqlite3

        from scripts.api.dashboard_comms import ensure_broker_cols

        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE messages (id INTEGER, task_id TEXT, content TEXT)")

        # Reset cache
        import scripts.api.dashboard_comms as dc
        dc._BROKER_COLS = None

        cols = ensure_broker_cols(conn)
        assert "id" in cols
        assert "task_id" in cols
        assert "content" in cols
        conn.close()

        # Reset for other tests
        dc._BROKER_COLS = None


# ==================== YAML escape (from test_api_v4.py pattern) ====================


class TestYamlEscape:
    """YAML special characters in values are safely handled."""

    def test_no_escaping_needed(self, tmp_path):
        from scripts.api.dashboard_helpers import read_yaml_file

        f = tmp_path / "simple.yaml"
        f.write_text("key: simple value\nother: 123")
        result = read_yaml_file(f)
        assert result["key"] == "simple value"

    def test_combined_escaping(self, tmp_path):
        from scripts.api.dashboard_helpers import read_yaml_file

        f = tmp_path / "escape.yaml"
        f.write_text('key: "value: with colon"\nother: "[brackets]"')
        result = read_yaml_file(f)
        assert result["key"] == "value: with colon"


# ==================== v5 pipeline state handling (#814) ====================


class TestCheckBuildPhaseV5:
    """_check_build_phase handles v5 content phase."""

    def test_v5_content_complete(self, tmp_path):
        from scripts.api.state_build import _check_build_phase

        (tmp_path / "state.json").write_text(json.dumps({
            "mode": "v5",
            "phases": {"content": {"status": "complete", "ts": "2026-03-01"}},
        }))
        built, ts = _check_build_phase(tmp_path)
        assert built == 1
        assert ts == "2026-03-01"

    def test_v5_content_not_complete(self, tmp_path):
        from scripts.api.state_build import _check_build_phase

        (tmp_path / "state.json").write_text(json.dumps({
            "mode": "v5",
            "phases": {"research": {"status": "complete"}},
        }))
        built, ts = _check_build_phase(tmp_path)
        assert built == 0
        assert ts is None


class TestComputeBuildStatusAllV5:
    """compute_build_status_all counts v5 modules."""

    def test_v5_module_counted_as_done(self, tmp_path):
        from scripts.api.state_build import compute_build_status_all

        track_dir = tmp_path / "curriculum" / "l2-uk-en" / "a1"
        orch_dir = track_dir / "orchestration" / "test-slug"
        orch_dir.mkdir(parents=True)
        (orch_dir / "state.json").write_text(json.dumps({
            "mode": "v5",
            "phases": {
                "research": {"status": "complete"},
                "content": {"status": "complete"},
                "validate": {"status": "complete", "ts": "t1"},
            },
        }))

        plan_slugs = [(1, "test-slug")]
        level_cfg = {"id": "a1", "path": "l2-uk-en/a1"}

        with (
            patch("scripts.api.state_build.LEVELS", [level_cfg]),
            patch("scripts.api.state_build.CURRICULUM_ROOT", tmp_path / "curriculum"),
            patch("scripts.api.state_build.get_plan_slugs", return_value=plan_slugs),
        ):
            result = compute_build_status_all()

        assert result["tracks"]["a1"]["done"] == 1
        assert result["tracks"]["a1"]["building"] == 0

    def test_v5_running_module_counted_as_building(self, tmp_path):
        from scripts.api.state_build import compute_build_status_all

        track_dir = tmp_path / "curriculum" / "l2-uk-en" / "a1"
        orch_dir = track_dir / "orchestration" / "test-slug"
        orch_dir.mkdir(parents=True)
        (orch_dir / "state.json").write_text(json.dumps({
            "mode": "v5",
            "phases": {
                "research": {"status": "complete"},
                "content": {"status": "running"},
            },
        }))

        plan_slugs = [(1, "test-slug")]
        level_cfg = {"id": "a1", "path": "l2-uk-en/a1"}

        with (
            patch("scripts.api.state_build.LEVELS", [level_cfg]),
            patch("scripts.api.state_build.CURRICULUM_ROOT", tmp_path / "curriculum"),
            patch("scripts.api.state_build.get_plan_slugs", return_value=plan_slugs),
        ):
            result = compute_build_status_all()

        assert result["tracks"]["a1"]["done"] == 0
        assert result["tracks"]["a1"]["building"] == 1


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
            patch("scripts.api.state_issues.CURRICULUM_ROOT", tmp_path / "curriculum"),
            patch("scripts.api.state_issues.get_plan_slugs", return_value=plan_slugs),
            patch("scripts.api.state_issues.get_final_review_info", return_value=None),
        ):
            result = compute_final_reviews("a1", level_cfg)

        assert result["pending_review"] == 1
        assert result["pending_modules"][0]["slug"] == "test-slug"

    def test_v5_validate_not_complete_not_pending(self, tmp_path):
        from scripts.api.state_issues import compute_final_reviews

        track_dir = tmp_path / "curriculum" / "l2-uk-en" / "a1"
        orch_dir = track_dir / "orchestration" / "test-slug"
        orch_dir.mkdir(parents=True)
        (orch_dir / "state.json").write_text(json.dumps({
            "mode": "v5",
            "phases": {"content": {"status": "complete"}},
        }))

        plan_slugs = [(1, "test-slug")]
        level_cfg = {"id": "a1", "path": "l2-uk-en/a1"}

        with (
            patch("scripts.api.state_issues.CURRICULUM_ROOT", tmp_path / "curriculum"),
            patch("scripts.api.state_issues.get_plan_slugs", return_value=plan_slugs),
            patch("scripts.api.state_issues.get_final_review_info", return_value=None),
        ):
            result = compute_final_reviews("a1", level_cfg)

        assert result["pending_review"] == 0


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
            patch("scripts.api.state_issues.CURRICULUM_ROOT", tmp_path / "curriculum"),
            patch("scripts.api.state_issues.get_plan_slugs", return_value=plan_slugs),
            patch("scripts.api.state_issues.get_final_review_info", return_value=None),
        ):
            result = compute_final_reviews("a1", level_cfg)

        assert result["pending_review"] == 1
        assert result["pending_modules"][0]["slug"] == "test-slug"
