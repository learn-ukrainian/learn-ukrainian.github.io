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

    def test_no_score_returns_none(self):
        from scripts.api.review_parsing import extract_review_score

        assert extract_review_score("No score here") is None


class TestExtractReviewVerdict:
    """extract_review_verdict parses PASS/FAIL."""

    def test_pass_verdict(self):
        from scripts.api.review_parsing import extract_review_verdict

        assert extract_review_verdict("**Status:** PASS") == "PASS"

    def test_no_verdict(self):
        from scripts.api.review_parsing import extract_review_verdict

        assert extract_review_verdict("No verdict here") is None


class TestExtractPlanVerdict:
    """extract_plan_verdict parses plan review verdicts."""

    def test_pass(self):
        from scripts.api.review_parsing import extract_plan_verdict

        assert extract_plan_verdict("**Verdict:** PASS") == "PASS"

    def test_no_verdict(self):
        from scripts.api.review_parsing import extract_plan_verdict

        assert extract_plan_verdict("no verdict") is None


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

    def test_v3_from_state_v3(self, tmp_path):
        from scripts.api.state_helpers import detect_pipeline_version

        (tmp_path / "state-v3.json").write_text('{"phases": {}}')
        assert detect_pipeline_version(tmp_path) == "v3"

    def test_unbuilt_empty_dir(self, tmp_path):
        from scripts.api.state_helpers import detect_pipeline_version

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


class TestParsePhaseStatus:
    """Phase status parsing functions."""

    def test_v5_complete(self):
        from scripts.api.state_helpers import parse_v5_phase_status

        v5 = {"phases": {"sandbox": {"status": "complete", "ts": "2026-02-01"}}}
        result = parse_v5_phase_status(v5, "sandbox")
        assert result["status"] == "complete"

    def test_v3_with_mode_and_attempts(self):
        from scripts.api.state_helpers import parse_v3_phase_status

        v3 = {"phases": {"v3-A": {"status": "complete", "mode": "gemini", "ts": "t1", "attempts": 2}}}
        result = parse_v3_phase_status(v3, "v3-A")
        assert result["status"] == "complete"
        assert result["mode"] == "gemini"
        assert result["attempts"] == 2


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

    def test_review_no_verdict(self, tmp_path):
        from scripts.api.state_helpers import get_final_review_info

        review_dir = tmp_path / "review"
        review_dir.mkdir()
        (review_dir / "test-final-review.md").write_text("Some review without verdict")
        result = get_final_review_info(tmp_path, "test", curriculum_root=tmp_path.parent)
        assert result is not None
        assert result["verdict"] is None


# ==================== state_coverage ====================


class TestComputePipelineTrack:
    """compute_pipeline_track exposes canonical v6 phase shape."""

    def test_v6_phase_order_and_labels(self):
        from scripts.api.state_coverage import compute_pipeline_track
        from scripts.build.phase_constants import PHASE_LABELS, PHASES

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


# ==================== state_build ====================


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


class TestCheckAuditHealth:
    """_check_audit_health categorizes audit results."""

    def test_fail(self):
        from scripts.api.state_build import _check_audit_health

        audit = {"status": "fail", "blocking_issues": [{"gate": "words"}]}
        ap, af, att = _check_audit_health(audit, 1, "slug")
        assert ap == 0
        assert af == 1
        assert att is not None
        assert att["reason"] == "audit_fail"


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


def _dashboard_ctx(tmp_path):
    from scripts.api.monitor_context import fixture_context

    return fixture_context(tmp_path)


class TestReadDispatcherState:
    """read_dispatcher_state reads JSON from disk."""

    def test_valid_state(self, tmp_path):
        from scripts.api.dashboard_comms import read_dispatcher_state

        ctx = _dashboard_ctx(tmp_path)
        ctx.roots.batch_state_dir.mkdir(parents=True, exist_ok=True)
        (ctx.roots.batch_state_dir / "dispatcher_state.json").write_text(
            '{"running": true, "queue": []}'
        )
        result = read_dispatcher_state(ctx)
        assert result["running"] is True

    def test_invalid_json(self, tmp_path):
        from scripts.api.dashboard_comms import read_dispatcher_state

        ctx = _dashboard_ctx(tmp_path)
        ctx.roots.batch_state_dir.mkdir(parents=True, exist_ok=True)
        (ctx.roots.batch_state_dir / "dispatcher_state.json").write_text("broken{{{")
        result = read_dispatcher_state(ctx)
        assert result == {}


# ==================== YAML escape (from test_api_v4.py pattern) ====================


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
            patch("scripts.api.state_build.get_plan_slugs", return_value=plan_slugs),
        ):
            result = compute_build_status_all(curriculum_root=tmp_path / "curriculum")

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
            patch("scripts.api.state_build.get_plan_slugs", return_value=plan_slugs),
        ):
            result = compute_build_status_all(curriculum_root=tmp_path / "curriculum")

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


class TestLoadCurriculum:
    """load_curriculum parses YAML safely with mtime caching and error handling."""

    def test_load_valid_curriculum(self, tmp_path):
        from scripts.api.state_helpers import load_curriculum

        yaml_file = tmp_path / "curriculum.yaml"
        yaml_file.write_text("levels:\n  a1:\n    modules:\n      - demo\n", encoding="utf-8")
        data = load_curriculum(curriculum_yaml=yaml_file)
        assert "levels" in data
        assert data["levels"]["a1"]["modules"] == ["demo"]

    def test_load_corrupted_yaml_returns_empty(self, tmp_path):
        from scripts.api.state_helpers import load_curriculum

        yaml_file = tmp_path / "curriculum.yaml"
        yaml_file.write_text("broken: [unclosed list", encoding="utf-8")
        data = load_curriculum(curriculum_yaml=yaml_file)
        assert data == {}


class TestGetBrokerMessagesForSlug:
    """get_broker_messages_for_slug queries database with limit."""

    def test_respects_limit_and_order(self, tmp_path):
        import sqlite3

        from scripts.api.monitor_context import DatabaseHandle
        from scripts.api.resilience import connect_sqlite
        from scripts.api.state_helpers import get_broker_messages_for_slug

        db_path = tmp_path / "messages.sqlite3"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE messages (id INTEGER PRIMARY KEY, task_id TEXT, from_llm TEXT, to_llm TEXT, message_type TEXT, content TEXT, timestamp TEXT)"
        )
        for i in range(1, 10):
            conn.execute(
                "INSERT INTO messages VALUES (?, ?, 'agent1', 'agent2', 'chat', ?, '2026-08-26T12:00:00Z')",
                (i, "task-test-module-slug", f"content {i}"),
            )
        conn.commit()
        conn.close()

        handle = DatabaseHandle(db_path, lambda path, **kw: connect_sqlite(str(path)))
        results = get_broker_messages_for_slug("test-module-slug", limit=3, message_db=handle)
        assert len(results) == 3
        # Ordered by id DESC
        assert results[0]["id"] == 9
        assert results[1]["id"] == 8
        assert results[2]["id"] == 7
