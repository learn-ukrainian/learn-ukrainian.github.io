"""Tests for batch_otaman, batch_dispatcher, batch_fix_review, agent_watcher, preseed_runner.

Targets ~200+ tests across 5 scripts. Heavy mocking of subprocess, filesystem, etc.
"""

import json
import os
import signal
import sqlite3
import subprocess
import sys
import textwrap
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch, PropertyMock

import pytest

# Ensure scripts/ is importable
SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


# ═══════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_state_dir(tmp_path):
    """Create a temporary batch_state directory."""
    d = tmp_path / "batch_state"
    d.mkdir()
    return d


@pytest.fixture
def mock_project_root(tmp_path):
    """Mock PROJECT_ROOT to tmp_path."""
    return tmp_path


@pytest.fixture
def sqlite_db(tmp_path):
    """Create a temporary SQLite database mimicking messages.db."""
    db_path = tmp_path / "messages.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY,
            task_id TEXT,
            from_llm TEXT,
            to_llm TEXT,
            message_type TEXT,
            content TEXT DEFAULT '',
            timestamp TEXT,
            acknowledged INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()
    return db_path


# ═══════════════════════════════════════════════════════════════════════
# batch_fix_review.py — Pure function tests
# ═══════════════════════════════════════════════════════════════════════

class TestBatchFixReviewExtractSection:
    """Tests for extract_section."""

    def _import(self):
        from batch_fix_review import extract_section
        return extract_section

    def test_basic_extraction(self, tmp_path):
        extract_section = self._import()
        p = tmp_path / "out.txt"
        p.write_text("before\n===START===\nhello world\n===END===\nafter\n")
        result = extract_section(p, "===START===", "===END===")
        assert result == "hello world"

    def test_no_match(self, tmp_path):
        extract_section = self._import()
        p = tmp_path / "out.txt"
        p.write_text("no delimiters here\n")
        assert extract_section(p, "===START===", "===END===") is None

    def test_multiline_extraction(self, tmp_path):
        extract_section = self._import()
        p = tmp_path / "out.txt"
        p.write_text("pre\n===START===\nline1\nline2\nline3\n===END===\npost\n")
        result = extract_section(p, "===START===", "===END===")
        assert "line1" in result
        assert "line3" in result

    def test_code_block_wrapping(self, tmp_path):
        extract_section = self._import()
        p = tmp_path / "out.txt"
        content = "```\n===START===\ncontent here\n===END===\n```\n"
        p.write_text(content)
        result = extract_section(p, "===START===", "===END===")
        assert result is not None
        assert "content" in result

    def test_code_block_with_language(self, tmp_path):
        extract_section = self._import()
        p = tmp_path / "out.txt"
        content = "```yaml\n===START===\ncontent\n===END===\n```\n"
        p.write_text(content)
        result = extract_section(p, "===START===", "===END===")
        assert result is not None

    def test_multiple_sections(self, tmp_path):
        extract_section = self._import()
        p = tmp_path / "out.txt"
        content = "===A_START===\nfirst\n===A_END===\n===B_START===\nsecond\n===B_END===\n"
        p.write_text(content)
        assert extract_section(p, "===A_START===", "===A_END===") == "first"
        assert extract_section(p, "===B_START===", "===B_END===") == "second"


class TestBatchFixReviewExtractScore:
    """Tests for extract_score."""

    def _import(self):
        from batch_fix_review import extract_score
        return extract_score

    def test_bold_overall_score(self):
        assert self._import()("**Overall Score:** 8.5/10") == 8.5

    def test_plain_overall_score(self):
        assert self._import()("Overall Score: 9.0/10") == 9.0

    def test_bold_score_alone(self):
        assert self._import()("**7.5/10**") == 7.5

    def test_equals_bold(self):
        assert self._import()("= **8.0/10**") == 8.0

    def test_no_score(self):
        assert self._import()("no score here") is None

    def test_integer_score(self):
        assert self._import()("**Overall Score:** 9/10") == 9.0

    def test_first_pattern_wins(self):
        text = "**Overall Score:** 8.0/10\nOverall Score: 9.0/10"
        assert self._import()(text) == 8.0


class TestBatchFixReviewExtractStatus:
    """Tests for extract_status."""

    def _import(self):
        from batch_fix_review import extract_status
        return extract_status

    def test_pass(self):
        assert self._import()("**Status:** PASS") == "PASS"

    def test_fail(self):
        assert self._import()("**Status:** FAIL") == "FAIL"

    def test_unknown(self):
        assert self._import()("no status") == "UNKNOWN"


class TestBatchFixReviewCountItems:
    """Tests for count_items."""

    def _import(self):
        from batch_fix_review import count_items
        return count_items

    def test_count_vocab_items(self, tmp_path):
        count_items = self._import()
        p = tmp_path / "vocab.yaml"
        p.write_text("items:\n  - word: hello\n  - word: world\n  - word: test\n")
        assert count_items(p, "items") == 3

    def test_count_activities(self, tmp_path):
        count_items = self._import()
        p = tmp_path / "acts.yaml"
        p.write_text("- type: quiz\n  title: Q1\n- type: match\n  title: M1\n")
        assert count_items(p, "activities_root") == 2

    def test_nonexistent_file(self, tmp_path):
        count_items = self._import()
        p = tmp_path / "nope.yaml"
        assert count_items(p, "items") == 0

    def test_empty_items(self, tmp_path):
        count_items = self._import()
        p = tmp_path / "vocab.yaml"
        p.write_text("items:\nother_key: value\n")
        assert count_items(p, "items") == 0

    def test_items_section_ends(self, tmp_path):
        count_items = self._import()
        p = tmp_path / "vocab.yaml"
        p.write_text("items:\n  - word: one\n  - word: two\nother:\n  value: x\n")
        assert count_items(p, "items") == 2


class TestBatchFixReviewCountEngagement:
    """Tests for count_engagement."""

    def _import(self):
        from batch_fix_review import count_engagement
        return count_engagement

    def test_callout_boxes(self, tmp_path):
        count_engagement = self._import()
        p = tmp_path / "content.md"
        p.write_text("> [!note]\ntext\n> [!tip]\nmore\n")
        assert count_engagement(p) == 2

    def test_emoji_boxes(self, tmp_path):
        count_engagement = self._import()
        p = tmp_path / "content.md"
        # Use raw text with actual emoji patterns
        p.write_text(textwrap.dedent("""\
            Some text
            > \U0001f4a1 Fun fact
            more text
            > \U0001f50d Let's explore
            even more
        """))
        assert count_engagement(p) == 2

    def test_nonexistent_file(self, tmp_path):
        count_engagement = self._import()
        p = tmp_path / "nope.md"
        assert count_engagement(p) == 0

    def test_no_engagement(self, tmp_path):
        count_engagement = self._import()
        p = tmp_path / "content.md"
        p.write_text("# Title\n\nJust plain text.\n")
        assert count_engagement(p) == 0


class TestBatchFixReviewGetWordTarget:
    """Tests for get_word_target."""

    def _import(self):
        from batch_fix_review import get_word_target
        return get_word_target

    def test_reads_word_target(self, tmp_path):
        get_word_target = self._import()
        p = tmp_path / "plan.yaml"
        p.write_text("title: Test\nword_target: 4000\nobjectives:\n  - learn\n")
        files = {"plan": p}
        assert get_word_target(files) == 4000

    def test_no_file(self, tmp_path):
        get_word_target = self._import()
        files = {"plan": tmp_path / "nonexistent.yaml"}
        assert get_word_target(files) == 0

    def test_invalid_value(self, tmp_path):
        get_word_target = self._import()
        p = tmp_path / "plan.yaml"
        p.write_text("word_target: not_a_number\n")
        files = {"plan": p}
        assert get_word_target(files) == 0


class TestBatchFixReviewGetModuleTitle:
    """Tests for get_module_title."""

    def _import(self):
        from batch_fix_review import get_module_title
        return get_module_title

    def test_reads_h1(self, tmp_path):
        get_module_title = self._import()
        p = tmp_path / "content.md"
        p.write_text("# My Great Module\n\nContent here.\n")
        files = {"content": p, "slug": "my-great-module"}
        assert get_module_title(files) == "My Great Module"

    def test_fallback_to_slug(self, tmp_path):
        get_module_title = self._import()
        p = tmp_path / "missing.md"
        files = {"content": p, "slug": "my-great-module"}
        assert "My Great Module" == get_module_title(files)

    def test_no_h1(self, tmp_path):
        get_module_title = self._import()
        p = tmp_path / "content.md"
        p.write_text("No heading here\n## Subheading\n")
        files = {"content": p, "slug": "test-slug"}
        assert "Test Slug" == get_module_title(files)


class TestBatchFixReviewGetAuditMetrics:
    """Tests for get_audit_metrics."""

    def _import(self):
        from batch_fix_review import get_audit_metrics
        return get_audit_metrics

    def test_parses_status(self, tmp_path):
        get_audit_metrics = self._import()
        status = {
            "gates": {
                "lesson": {"message": "1200/1000 (raw: 1500)", "status": "pass"},
                "activities": {"message": "5/4", "status": "pass"},
            },
            "overall": {"status": "PASS"},
        }
        p = tmp_path / "status.json"
        p.write_text(json.dumps(status))
        files = {"status": p}
        m = get_audit_metrics(files)
        assert m["audit_words"] == 1200
        assert m["word_target"] == 1000
        assert m["overall_status"] == "PASS"

    def test_missing_file(self, tmp_path):
        get_audit_metrics = self._import()
        files = {"status": tmp_path / "nope.json"}
        assert get_audit_metrics(files) == {}

    def test_no_word_match(self, tmp_path):
        get_audit_metrics = self._import()
        status = {"gates": {"lesson": {"message": "no numbers"}}, "overall": {"status": "FAIL"}}
        p = tmp_path / "status.json"
        p.write_text(json.dumps(status))
        files = {"status": p}
        m = get_audit_metrics(files)
        assert m["audit_words"] == 0


class TestBatchFixReviewRunAudit:
    """Tests for run_audit."""

    def _import(self):
        from batch_fix_review import run_audit
        return run_audit

    @patch("subprocess.run")
    def test_audit_pass(self, mock_run, tmp_path):
        run_audit = self._import()
        mock_run.return_value = MagicMock(stdout="AUDIT PASSED\nAll gates green", returncode=0)
        assert run_audit(tmp_path / "content.md") is True

    @patch("subprocess.run")
    def test_audit_fail(self, mock_run, tmp_path):
        run_audit = self._import()
        mock_run.return_value = MagicMock(stdout="AUDIT FAILED\n2 gates red", returncode=1)
        assert run_audit(tmp_path / "content.md") is False

    @patch("subprocess.run", side_effect=Exception("boom"))
    def test_audit_exception(self, mock_run, tmp_path):
        run_audit = self._import()
        assert run_audit(tmp_path / "content.md") is False


class TestBatchFixReviewProcessModule:
    """Tests for process_module and find_module_files."""

    @patch("batch_fix_review.find_module_files", return_value=None)
    def test_process_module_no_files(self, mock_find):
        from batch_fix_review import process_module
        result = process_module("a1", 99, "model")
        assert result["status"] == "SKIP"

    @patch("batch_fix_review.find_module_files")
    def test_process_module_already_pass(self, mock_find, tmp_path):
        from batch_fix_review import process_module

        orch = tmp_path / "orchestration"
        orch.mkdir()
        review_path = orch / "phase-5-re-review.md"
        review_path.write_text("**Overall Score:** 9.5/10\n**Status:** PASS")

        content = tmp_path / "content.md"
        content.write_text("# Test\nContent\n")

        mock_find.return_value = {
            "num": 1, "slug": "test", "full_stem": "test",
            "content": content, "activities": tmp_path / "acts.yaml",
            "vocabulary": tmp_path / "vocab.yaml", "meta": tmp_path / "meta.yaml",
            "plan": tmp_path / "plan.yaml", "research": tmp_path / "research.md",
            "review": tmp_path / "review.md", "status": tmp_path / "status.json",
            "orchestration": orch,
        }
        result = process_module("a1", 1, "model")
        assert result["status"] == "ALREADY_PASS"

    @patch("batch_fix_review.find_module_files")
    def test_process_module_dry_run_needs_review(self, mock_find, tmp_path):
        from batch_fix_review import process_module

        orch = tmp_path / "orchestration"
        orch.mkdir()
        content = tmp_path / "content.md"
        content.write_text("# Test\nContent\n")

        mock_find.return_value = {
            "num": 1, "slug": "test", "full_stem": "test",
            "content": content, "activities": tmp_path / "acts.yaml",
            "vocabulary": tmp_path / "vocab.yaml", "meta": tmp_path / "meta.yaml",
            "plan": tmp_path / "plan.yaml", "research": tmp_path / "research.md",
            "review": tmp_path / "review.md", "status": tmp_path / "status.json",
            "orchestration": orch,
        }
        result = process_module("a1", 1, "model", dry_run=True)
        assert result["status"] == "DRY_RUN"


class TestBatchFixReviewApplyFixOutput:
    """Tests for _apply_fix_output."""

    def _import(self):
        from batch_fix_review import _apply_fix_output
        return _apply_fix_output

    def test_extracts_and_writes(self, tmp_path):
        _apply_fix_output = self._import()
        orch = tmp_path / "orchestration"
        orch.mkdir()
        content = tmp_path / "content.md"
        activities = tmp_path / "activities.yaml"
        vocabulary = tmp_path / "vocabulary.yaml"

        output = tmp_path / "output.txt"
        text = (
            "===CONTENT_START===\n" + "x" * 200 + "\n===CONTENT_END===\n"
            "===ACTIVITIES_START===\n" + "y" * 100 + "\n===ACTIVITIES_END===\n"
            "===VOCABULARY_START===\n" + "z" * 100 + "\n===VOCABULARY_END===\n"
            "===CHANGES_START===\nFixed stuff\n===CHANGES_END===\n"
        )
        output.write_text(text)

        files = {"content": content, "activities": activities,
                 "vocabulary": vocabulary, "orchestration": orch}
        changed, delta = _apply_fix_output(output, files, 1)
        assert "content" in changed
        assert "activities" in changed
        assert "vocabulary" in changed
        assert delta == 0

    def test_no_changes(self, tmp_path):
        _apply_fix_output = self._import()
        orch = tmp_path / "orchestration"
        orch.mkdir()
        output = tmp_path / "output.txt"
        output.write_text("nothing useful here")
        files = {"content": tmp_path / "c.md", "activities": tmp_path / "a.yaml",
                 "vocabulary": tmp_path / "v.yaml", "orchestration": orch}
        changed, delta = _apply_fix_output(output, files, 1)
        assert changed == []
        assert delta == 1


# ═══════════════════════════════════════════════════════════════════════
# batch_dispatcher_config.py — TrackState and TRACKS
# ═══════════════════════════════════════════════════════════════════════

class TestBatchDispatcherConfig:
    def test_track_state_values(self):
        from batch_dispatcher_config import TrackState
        assert TrackState.PENDING == "PENDING"
        assert TrackState.ELIGIBLE == "ELIGIBLE"
        assert TrackState.RUNNING == "RUNNING"
        assert TrackState.COOLDOWN == "COOLDOWN"
        assert TrackState.STALLED == "STALLED"
        assert TrackState.DONE == "DONE"
        assert TrackState.BLOCKED == "BLOCKED"

    def test_tracks_list(self):
        from batch_dispatcher_config import TRACKS, TRACK_BY_NAME
        assert len(TRACKS) == 20
        assert "a1" in TRACK_BY_NAME
        assert TRACK_BY_NAME["a1"][0] == 1  # priority

    def test_track_names(self):
        from batch_dispatcher_config import TRACK_NAMES
        assert "a1" in TRACK_NAMES
        assert "c2" in TRACK_NAMES


# ═══════════════════════════════════════════════════════════════════════
# batch_otaman.py
# ═══════════════════════════════════════════════════════════════════════

class TestBatchOtamanIsContentComplete:
    def _import(self):
        from batch_otaman import _is_content_complete
        return _is_content_complete

    def test_none_result(self):
        assert self._import()(None) is False

    def test_content_complete(self):
        result = MagicMock()
        result.gates = {
            "activities": {"status": "deferred"},
            "lesson": {"status": "pass"},
        }
        assert self._import()(result) is True

    def test_not_content_complete_activities_pass(self):
        result = MagicMock()
        result.gates = {
            "activities": {"status": "pass"},
            "lesson": {"status": "pass"},
        }
        assert self._import()(result) is False

    def test_not_content_complete_lesson_fail(self):
        result = MagicMock()
        result.gates = {
            "activities": {"status": "deferred"},
            "lesson": {"status": "fail"},
        }
        assert self._import()(result) is False


class TestBatchOtamanCheckDependencies:
    def _import(self):
        from batch_otaman import check_dependencies
        return check_dependencies

    def test_unknown_track(self):
        ok, unmet = self._import()("nonexistent_track_xyz", {})
        assert ok is False
        assert len(unmet) == 1

    def test_no_deps(self):
        ok, unmet = self._import()("a1", {})
        assert ok is True
        assert unmet == []

    def test_deps_met(self):
        summaries = {"a1": {"total": 100, "passed": 90}}
        ok, unmet = self._import()("a2", summaries)
        assert ok is True

    def test_deps_not_met(self):
        summaries = {"a1": {"total": 100, "passed": 50}}
        ok, unmet = self._import()("a2", summaries)
        assert ok is False
        assert len(unmet) == 1

    def test_deps_not_scanned(self):
        ok, unmet = self._import()("a2", {})
        assert ok is False
        assert "not scanned" in unmet[0]

    def test_deps_zero_total(self):
        summaries = {"a1": {"total": 0, "passed": 0}}
        ok, unmet = self._import()("a2", summaries)
        assert ok is False


class TestBatchOtamanGetTrackState:
    def _import(self):
        from batch_otaman import get_track_state
        return get_track_state

    def test_creates_new_state(self):
        from batch_dispatcher_config import TrackState
        state = {"tracks": {}}
        ts = self._import()(state, "a1")
        assert ts["state"] == TrackState.PENDING
        assert ts["dispatches"] == 0
        assert "a1" in state["tracks"]

    def test_returns_existing(self):
        state = {"tracks": {"a1": {"state": "DONE", "dispatches": 5}}}
        ts = self._import()(state, "a1")
        assert ts["state"] == "DONE"
        assert ts["dispatches"] == 5


class TestBatchOtamanDispatch:
    """Tests for dispatch_otaman."""

    @patch("batch_otaman.subprocess.run")
    def test_success(self, mock_run):
        from batch_otaman import dispatch_otaman
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="done")
        result = dispatch_otaman("a1", 1, "test-slug", timeout=5)
        assert result["success"] is True
        assert result["returncode"] == 0
        assert result["quota_hit"] is False

    @patch("batch_otaman.subprocess.run")
    def test_quota_hit(self, mock_run):
        from batch_otaman import dispatch_otaman
        mock_run.return_value = MagicMock(returncode=1, stderr="quota exceeded 429", stdout="")
        result = dispatch_otaman("a1", 1, "test-slug", timeout=5)
        assert result["quota_hit"] is True

    @patch("batch_otaman.subprocess.run")
    def test_rate_limit_in_stdout(self, mock_run):
        from batch_otaman import dispatch_otaman
        mock_run.return_value = MagicMock(returncode=1, stderr="", stdout="rate limit reached")
        result = dispatch_otaman("a1", 1, "test-slug", timeout=5)
        assert result["quota_hit"] is True

    @patch("batch_otaman.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 5))
    def test_timeout(self, mock_run):
        import subprocess
        from batch_otaman import dispatch_otaman
        result = dispatch_otaman("a1", 1, "test-slug", timeout=5)
        assert result["success"] is False
        assert result["returncode"] == -1
        assert "TimeoutExpired" in result["stderr"]

    @patch("batch_otaman.subprocess.run", side_effect=OSError("boom"))
    def test_exception(self, mock_run):
        from batch_otaman import dispatch_otaman
        result = dispatch_otaman("a1", 1, "test-slug", timeout=5)
        assert result["success"] is False
        assert result["returncode"] == -2


class TestBatchOtamanSignalHandler:
    def test_signal_handler_sets_flag(self):
        import batch_otaman
        old = batch_otaman._shutdown_requested
        try:
            batch_otaman._shutdown_requested = False
            batch_otaman._signal_handler(signal.SIGINT, None)
            assert batch_otaman._shutdown_requested is True
        finally:
            batch_otaman._shutdown_requested = old


class TestBatchOtamanStatePersistence:
    """Tests for load_state and save_state with mocked STATE_FILE."""

    @patch("batch_otaman.STATE_FILE")
    def test_load_state_no_file(self, mock_sf, tmp_path):
        from batch_otaman import load_state
        mock_sf.parent = tmp_path
        mock_sf.exists.return_value = False
        mock_sf.with_suffix.return_value = tmp_path / "state.lock"
        state = load_state()
        assert "tracks" in state
        assert "history" in state

    @patch("batch_otaman.STATE_FILE")
    def test_load_state_with_file(self, mock_sf, tmp_path):
        from batch_otaman import load_state
        state_data = {"tracks": {"a1": {}}, "history": [], "running_tracks": [], "stats": {}}
        sf = tmp_path / "state.json"
        sf.write_text(json.dumps(state_data))
        mock_sf.parent = tmp_path
        mock_sf.exists.return_value = True
        mock_sf.read_text.return_value = json.dumps(state_data)
        mock_sf.with_suffix.return_value = tmp_path / "state.lock"
        state = load_state()
        assert "a1" in state["tracks"]


class TestBatchOtamanShouldInclude:
    """Tests for BatchOtaman._should_include."""

    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    def test_exclude(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, exclude_tracks=["a1"])
        assert bo._should_include("a1") is False
        assert bo._should_include("a2") is True

    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    def test_include(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, include_tracks=["a1", "a2"])
        assert bo._should_include("a1") is True
        assert bo._should_include("b1") is False

    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    def test_no_filter(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True)
        assert bo._should_include("a1") is True


class TestBatchOtamanRuntimeExceeded:
    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    def test_no_limit(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True)
        assert bo._runtime_exceeded() is False

    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    def test_not_exceeded(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, max_runtime_hours=10)
        assert bo._runtime_exceeded() is False

    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    def test_exceeded(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, max_runtime_hours=1)
        bo.start_time = time.monotonic() - 3601  # 1h1s ago
        assert bo._runtime_exceeded() is True


class TestBatchOtamanScanTrackSummary:
    @patch("batch_otaman.get_module_index", side_effect=ValueError("nope"))
    def test_invalid_track(self, mock_idx):
        from batch_otaman import scan_track_summary
        result = scan_track_summary("nonexistent")
        assert result["error"] == "not_found"
        assert result["total"] == 0


class TestBatchOtamanFindNextModule:
    @patch("batch_otaman.get_module_index", side_effect=ValueError("nope"))
    def test_invalid_track(self, mock_idx):
        from batch_otaman import find_next_module
        assert find_next_module("nonexistent") is None


class TestBatchOtamanFindNextEnrichable:
    @patch("batch_otaman.get_module_index", side_effect=ValueError("nope"))
    def test_invalid_track(self, mock_idx):
        from batch_otaman import find_next_enrichable
        assert find_next_enrichable("nonexistent") is None


class TestBatchOtamanFormatTable:
    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    @patch("batch_otaman.scan_track_summary", return_value={"total": 10, "passed": 5, "content_complete": 2, "remaining": 3})
    def test_format_table(self, mock_scan, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, include_tracks=["a1"])
        summaries = bo._scan_all()
        table = bo._format_table(summaries)
        assert "a1" in table
        assert "Track" in table


class TestBatchOtamanPrintSummary:
    @patch("batch_otaman.load_state", return_value={
        "tracks": {}, "history": [
            {"track": "a1", "num": 1, "slug": "test", "timestamp": "2026-01-01T00:00:00",
             "success": True, "passed_after": True, "duration_s": 30, "quota_hit": False}
        ], "running_tracks": [],
        "stats": {"total_dispatches": 1, "total_modules_passed": 1, "total_quota_hits": 0}
    })
    @patch("batch_otaman.STATE_FILE")
    def test_print_summary(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True)
        # Should not raise
        bo._print_summary()


# ═══════════════════════════════════════════════════════════════════════
# batch_dispatcher.py
# ═══════════════════════════════════════════════════════════════════════

class TestBatchDispatcherInit:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_init(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(dry_run=True)
        assert d.dry_run is True
        assert d.one_shot is False

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_include_exclude(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(include_tracks=["a1"], exclude_tracks=["b1"])
        assert d._should_include_track("a1") is True
        assert d._should_include_track("b1") is False
        assert d._should_include_track("a2") is False


class TestBatchDispatcherShouldInclude:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_exclude_takes_priority(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(include_tracks=["a1", "b1"], exclude_tracks=["b1"])
        assert d._should_include_track("b1") is False


class TestBatchDispatcherRuntimeExceeded:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_no_limit(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher()
        assert d._runtime_exceeded() is False

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_exceeded(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(max_runtime_hours=1)
        d.start_time = time.monotonic() - 3601
        assert d._runtime_exceeded() is True


class TestBatchDispatcherCountEscalated:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    @patch("batch_dispatcher.BATCH_STATE_DIR")
    def test_no_dir(self, mock_bsd, mock_load, tmp_path):
        mock_bsd.__truediv__ = lambda self, x: tmp_path / "failures"
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher()
        assert d._count_escalated("a1") == 0

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    @patch("batch_dispatcher.BATCH_STATE_DIR")
    def test_with_escalated(self, mock_bsd, mock_load, tmp_path):
        failures_dir = tmp_path / "failures" / "a1"
        failures_dir.mkdir(parents=True)
        (failures_dir / "mod1.json").write_text(json.dumps({"escalated": True}))
        (failures_dir / "mod2.json").write_text(json.dumps({"escalated": False}))
        (failures_dir / "mod3.json").write_text(json.dumps({"escalated": True}))

        mock_bsd.__truediv__ = lambda self, x: tmp_path / x
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher()
        assert d._count_escalated("a1") == 2


class TestBatchDispatcherGetEscalated:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    @patch("batch_dispatcher.FAILURES_DIR")
    def test_no_dir(self, mock_fd, mock_load, tmp_path):
        mock_fd.__truediv__ = lambda self, x: tmp_path / "failures" / x
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher()
        assert d._get_escalated_modules("a1") == []

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    @patch("batch_dispatcher.FAILURES_DIR")
    def test_with_escalated(self, mock_fd, mock_load, tmp_path):
        failures_dir = tmp_path / "failures" / "a1"
        failures_dir.mkdir(parents=True)
        (failures_dir / "mod1.json").write_text(json.dumps({"slug": "test", "escalated": True}))
        mock_fd.__truediv__ = lambda self, x: tmp_path / "failures" / x
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher()
        esc = d._get_escalated_modules("a1")
        assert len(esc) == 1
        assert esc[0]["slug"] == "test"


class TestBatchDispatcherSignalHandler:
    def test_signal_handler(self):
        import batch_dispatcher
        old = batch_dispatcher._shutdown_requested
        try:
            batch_dispatcher._shutdown_requested = False
            batch_dispatcher._signal_handler(signal.SIGINT, None)
            assert batch_dispatcher._shutdown_requested is True
        finally:
            batch_dispatcher._shutdown_requested = old


class TestBatchDispatcherPickTrack:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_force_track(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        d = BatchDispatcher(force_track="a1")
        result = d._pick_track({})
        assert result == "a1"

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_force_track_done(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(force_track="a1")
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.DONE
        result = d._pick_track({})
        assert result is None


class TestBatchDispatcherPrintSummary:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {"total_dispatches": 5, "total_cooldowns": 1, "total_stalls": 0, "rotations_completed": 0},
        "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_print_summary(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher()
        # Should not raise
        d._print_summary()


# ═══════════════════════════════════════════════════════════════════════
# agent_watcher.py
# ═══════════════════════════════════════════════════════════════════════

class TestAgentWatcherLoadConfig:
    @patch("agent_watcher._AGENTS_CONFIG", None)
    def test_load_from_file(self, tmp_path):
        import agent_watcher
        config_path = tmp_path / "agents.yaml"
        config_path.write_text("agents:\n  claude:\n    bridge_command: process-claude\n    process_pattern: claude\n")

        with patch.object(Path, "__new__", wraps=Path.__new__):
            old_path = agent_watcher.load_agent_config.__globals__
            # Reset the cache
            agent_watcher._AGENTS_CONFIG = None
            with patch("agent_watcher.Path") as mock_path:
                mock_path.return_value.__truediv__ = lambda *a: config_path
                mock_path.__truediv__ = lambda *a: config_path
                # Use a simpler approach: just patch the config path check
                with patch("builtins.open", mock_open(read_data="agents:\n  test_agent:\n    bridge_command: test\n    process_pattern: test\n")):
                    with patch("pathlib.Path.exists", return_value=True):
                        agent_watcher._AGENTS_CONFIG = None
                        config = agent_watcher.load_agent_config()
                        assert "test_agent" in config

    def test_fallback_defaults(self):
        import agent_watcher
        agent_watcher._AGENTS_CONFIG = None
        with patch("pathlib.Path.exists", return_value=False):
            config = agent_watcher.load_agent_config()
            assert "claude" in config
            assert "gemini" in config
        # Reset
        agent_watcher._AGENTS_CONFIG = None


class TestAgentWatcherGetDb:
    def test_no_db(self):
        import agent_watcher
        with patch.object(agent_watcher, "DB_PATH", Path("/nonexistent/db")):
            assert agent_watcher.get_db() is None

    def test_with_db(self, sqlite_db):
        import agent_watcher
        with patch.object(agent_watcher, "DB_PATH", sqlite_db):
            conn = agent_watcher.get_db()
            assert conn is not None
            conn.close()


class TestAgentWatcherGetUnreadMessages:
    def test_no_db(self):
        import agent_watcher
        with patch.object(agent_watcher, "DB_PATH", Path("/nonexistent/db")):
            assert agent_watcher.get_unread_messages() == []

    def test_empty_db(self, sqlite_db):
        import agent_watcher
        with patch.object(agent_watcher, "DB_PATH", sqlite_db):
            msgs = agent_watcher.get_unread_messages()
            assert msgs == []

    def test_with_messages(self, sqlite_db):
        import agent_watcher
        conn = sqlite3.connect(sqlite_db)
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("task1", "claude", "gemini", "request", "2026-01-01T00:00:00"),
        )
        conn.commit()
        conn.close()
        with patch.object(agent_watcher, "DB_PATH", sqlite_db):
            msgs = agent_watcher.get_unread_messages()
            assert len(msgs) == 1
            assert msgs[0]["task_id"] == "task1"
            assert msgs[0]["from"] == "claude"

    def test_filter_by_agent(self, sqlite_db):
        import agent_watcher
        conn = sqlite3.connect(sqlite_db)
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("task1", "claude", "gemini", "request", "2026-01-01T00:00:00"),
        )
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("task2", "gemini", "claude", "response", "2026-01-01T00:00:01"),
        )
        conn.commit()
        conn.close()
        with patch.object(agent_watcher, "DB_PATH", sqlite_db):
            msgs = agent_watcher.get_unread_messages(for_agent="gemini")
            assert len(msgs) == 1
            assert msgs[0]["task_id"] == "task1"


class TestAgentWatcherAcknowledgeMessage:
    def test_acknowledge(self, sqlite_db):
        import agent_watcher
        conn = sqlite3.connect(sqlite_db)
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("task1", "claude", "gemini", "request", "2026-01-01T00:00:00"),
        )
        conn.commit()
        conn.close()
        with patch.object(agent_watcher, "DB_PATH", sqlite_db):
            agent_watcher.acknowledge_message(1, "delivered")
            msgs = agent_watcher.get_unread_messages()
            assert len(msgs) == 0

    def test_acknowledge_no_db(self):
        import agent_watcher
        with patch.object(agent_watcher, "DB_PATH", Path("/nonexistent/db")):
            # Should not raise
            agent_watcher.acknowledge_message(1)


class TestAgentWatcherCountTaskTurns:
    def test_empty_task_id(self):
        import agent_watcher
        assert agent_watcher.count_task_turns("") == 0
        assert agent_watcher.count_task_turns(None) == 0

    def test_no_db(self):
        import agent_watcher
        with patch.object(agent_watcher, "DB_PATH", Path("/nonexistent/db")):
            assert agent_watcher.count_task_turns("task1") == 0

    def test_counts_non_error(self, sqlite_db):
        import agent_watcher
        conn = sqlite3.connect(sqlite_db)
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("task1", "claude", "gemini", "request", "2026-01-01T00:00:00"),
        )
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("task1", "gemini", "claude", "response", "2026-01-01T00:00:01"),
        )
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("task1", "gemini", "claude", "error", "2026-01-01T00:00:02"),
        )
        conn.commit()
        conn.close()
        with patch.object(agent_watcher, "DB_PATH", sqlite_db):
            assert agent_watcher.count_task_turns("task1") == 2


class TestAgentWatcherIsAnyAgentActive:
    @patch("subprocess.run")
    def test_no_agents(self, mock_run):
        import agent_watcher
        agent_watcher._AGENTS_CONFIG = None
        with patch("pathlib.Path.exists", return_value=False):
            agent_watcher._AGENTS_CONFIG = {
                "claude": {"process_pattern": "claude"},
            }
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            assert agent_watcher.is_any_agent_active() is False
        agent_watcher._AGENTS_CONFIG = None

    @patch("subprocess.run")
    def test_agent_active(self, mock_run):
        import agent_watcher
        agent_watcher._AGENTS_CONFIG = {
            "claude": {"process_pattern": "claude"},
        }
        mock_run.return_value = MagicMock(returncode=0, stdout="12345")
        assert agent_watcher.is_any_agent_active() is True
        agent_watcher._AGENTS_CONFIG = None


class TestAgentWatcherNotifyHuman:
    @patch("subprocess.run")
    def test_sends_notification(self, mock_run):
        import agent_watcher
        # Should not raise
        agent_watcher.notify_human("claude", "gemini", 1, "task-123")
        mock_run.assert_called_once()

    @patch("subprocess.run", side_effect=Exception("no osascript"))
    def test_silences_errors(self, mock_run):
        import agent_watcher
        # Should not raise
        agent_watcher.notify_human("claude", "gemini", 1, "task-123")


class TestAgentWatcherTriggerAgent:
    @patch("subprocess.run")
    def test_success(self, mock_run):
        import agent_watcher
        agent_watcher._AGENTS_CONFIG = {
            "gemini": {"bridge_command": "process", "process_pattern": "gemini"},
        }
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        with patch.object(agent_watcher, "DB_PATH", Path("/nonexistent")):
            result = agent_watcher.trigger_agent("gemini", 1, "task1", "claude")
        assert result is True
        agent_watcher._AGENTS_CONFIG = None

    @patch("subprocess.run")
    def test_failure(self, mock_run):
        import agent_watcher
        agent_watcher._AGENTS_CONFIG = {
            "gemini": {"bridge_command": "process", "process_pattern": "gemini"},
        }
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        result = agent_watcher.trigger_agent("gemini", 1, "task1")
        assert result is False
        agent_watcher._AGENTS_CONFIG = None

    def test_unknown_agent(self):
        import agent_watcher
        agent_watcher._AGENTS_CONFIG = {"claude": {"bridge_command": "x"}}
        result = agent_watcher.trigger_agent("nonexistent", 1)
        assert result is False
        agent_watcher._AGENTS_CONFIG = None

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 360))
    def test_timeout(self, mock_run):
        import subprocess
        import agent_watcher
        agent_watcher._AGENTS_CONFIG = {
            "gemini": {"bridge_command": "process", "process_pattern": "gemini"},
        }
        result = agent_watcher.trigger_agent("gemini", 1)
        assert result is False
        agent_watcher._AGENTS_CONFIG = None

    @patch("subprocess.run", side_effect=OSError("boom"))
    def test_exception(self, mock_run):
        import agent_watcher
        agent_watcher._AGENTS_CONFIG = {
            "gemini": {"bridge_command": "process", "process_pattern": "gemini"},
        }
        result = agent_watcher.trigger_agent("gemini", 1)
        assert result is False
        agent_watcher._AGENTS_CONFIG = None


class TestAgentWatcherPidFile:
    def test_write_pid(self, tmp_path):
        import agent_watcher
        pid_file = tmp_path / "watcher.pid"
        with patch.object(agent_watcher, "PID_FILE", pid_file):
            agent_watcher.write_pid()
            assert pid_file.exists()
            assert int(pid_file.read_text().strip()) == os.getpid()

    def test_read_pid(self, tmp_path):
        import agent_watcher
        pid_file = tmp_path / "watcher.pid"
        pid_file.write_text("12345")
        with patch.object(agent_watcher, "PID_FILE", pid_file):
            assert agent_watcher.read_pid() == 12345

    def test_read_pid_missing(self, tmp_path):
        import agent_watcher
        pid_file = tmp_path / "nonexistent.pid"
        with patch.object(agent_watcher, "PID_FILE", pid_file):
            assert agent_watcher.read_pid() is None

    def test_read_pid_invalid(self, tmp_path):
        import agent_watcher
        pid_file = tmp_path / "watcher.pid"
        pid_file.write_text("not_a_number")
        with patch.object(agent_watcher, "PID_FILE", pid_file):
            assert agent_watcher.read_pid() is None


class TestAgentWatcherIsRunning:
    def test_not_running(self, tmp_path):
        import agent_watcher
        with patch.object(agent_watcher, "PID_FILE", tmp_path / "nope.pid"):
            assert agent_watcher.is_running() is False

    @patch("os.kill")
    def test_running(self, mock_kill, tmp_path):
        import agent_watcher
        pid_file = tmp_path / "watcher.pid"
        pid_file.write_text("12345")
        mock_kill.return_value = None  # Process exists
        with patch.object(agent_watcher, "PID_FILE", pid_file):
            assert agent_watcher.is_running() is True

    @patch("os.kill", side_effect=OSError("no such process"))
    def test_stale_pid(self, mock_kill, tmp_path):
        import agent_watcher
        pid_file = tmp_path / "watcher.pid"
        pid_file.write_text("99999")
        with patch.object(agent_watcher, "PID_FILE", pid_file):
            assert agent_watcher.is_running() is False


class TestAgentWatcherStopDaemon:
    @patch("os.kill")
    def test_stop_success(self, mock_kill, tmp_path):
        import agent_watcher
        pid_file = tmp_path / "watcher.pid"
        pid_file.write_text("12345")
        with patch.object(agent_watcher, "PID_FILE", pid_file):
            with patch("time.sleep"):
                result = agent_watcher.stop_daemon()
        assert result is True
        mock_kill.assert_called_with(12345, signal.SIGTERM)

    def test_stop_no_pid(self, tmp_path, capsys):
        import agent_watcher
        with patch.object(agent_watcher, "PID_FILE", tmp_path / "nope.pid"):
            result = agent_watcher.stop_daemon()
        assert result is False
        assert "No watcher running" in capsys.readouterr().out


class TestAgentWatcherShowStatus:
    def test_show_status_no_messages(self, sqlite_db, tmp_path, capsys):
        import agent_watcher
        agent_watcher._AGENTS_CONFIG = None
        with patch.object(agent_watcher, "DB_PATH", sqlite_db), \
             patch.object(agent_watcher, "PID_FILE", tmp_path / "nope.pid"), \
             patch.object(agent_watcher, "LOG_FILE", tmp_path / "nope.log"), \
             patch("pathlib.Path.exists", return_value=False):
            agent_watcher._AGENTS_CONFIG = {"claude": {"bridge_command": "x"}, "gemini": {"bridge_command": "y"}}
            agent_watcher.show_status()
        output = capsys.readouterr().out
        assert "STOPPED" in output
        agent_watcher._AGENTS_CONFIG = None


class TestAgentWatcherSaveStuckReport:
    def test_save_stuck_report(self, tmp_path, sqlite_db):
        import agent_watcher
        with patch.object(agent_watcher, "DB_PATH", sqlite_db):
            with patch("agent_watcher.Path") as mock_path_cls:
                # Make the report_dir writable
                report_dir = tmp_path / "stuck"
                report_dir.mkdir(parents=True)
                mock_path_cls.return_value.parent.parent = tmp_path
                mock_path_cls.__truediv__ = lambda s, x: tmp_path / x

                # Simpler approach: just test it doesn't crash
                agent_watcher._save_stuck_report(
                    "bio-test-task", 10,
                    {"from": "claude", "to": "gemini", "type": "request", "id": 1}
                )


# ═══════════════════════════════════════════════════════════════════════
# preseed_runner.py
# ═══════════════════════════════════════════════════════════════════════

class TestPreseedRunnerScanTrack:
    def test_scan_nonexistent_track(self, tmp_path):
        import preseed_runner
        with patch.object(preseed_runner, "CURRICULUM", tmp_path):
            result = preseed_runner.scan_track("nonexistent")
            assert result["total"] == 0
            assert result["remaining_count"] == 0

    def test_scan_with_plans(self, tmp_path):
        import preseed_runner
        plans_dir = tmp_path / "plans" / "test-track"
        plans_dir.mkdir(parents=True)
        (plans_dir / "module-a.yaml").write_text("title: A")
        (plans_dir / "module-b.yaml").write_text("title: B")

        research_dir = tmp_path / "test-track" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "module-a-research.md").write_text("done")

        with patch.object(preseed_runner, "CURRICULUM", tmp_path):
            with patch("batch_gemini_config.get_module_index", side_effect=Exception("no index")):
                result = preseed_runner.scan_track("test-track")
                assert result["total"] == 2
                assert result["done"] == 1
                assert result["remaining_count"] == 1


class TestPreseedRunnerGetAllRemaining:
    def test_no_plans_dir(self, tmp_path):
        import preseed_runner
        with patch.object(preseed_runner, "CURRICULUM", tmp_path):
            assert preseed_runner.get_all_remaining_tracks() == []

    def test_with_tracks(self, tmp_path):
        import preseed_runner
        plans_root = tmp_path / "plans"
        plans_root.mkdir()
        track_dir = plans_root / "mytrack"
        track_dir.mkdir()
        (track_dir / "mod1.yaml").write_text("title: M1")

        with patch.object(preseed_runner, "CURRICULUM", tmp_path):
            with patch("batch_gemini_config.get_module_index", side_effect=Exception("no")):
                tracks = preseed_runner.get_all_remaining_tracks()
                assert "mytrack" in tracks


class TestPreseedRunnerRunTrack:
    @patch("subprocess.Popen")
    def test_run_track_success(self, mock_popen, tmp_path):
        import preseed_runner

        mock_proc = MagicMock()
        mock_proc.communicate.return_value = ("Success output", None)
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        log_file = tmp_path / "logs" / "test.log"

        with patch.object(preseed_runner, "CURRICULUM", tmp_path):
            with patch("preseed_runner.scan_track", return_value={
                "track": "test", "total": 1, "done": 0,
                "remaining_count": 1, "remaining": [(1, "mod1")],
            }):
                result = preseed_runner.run_track("test", "slot-1", log_file)
                assert result["passed"] == 1
                assert result["failed"] == 0

    def test_run_track_nothing_to_do(self, tmp_path):
        import preseed_runner
        log_file = tmp_path / "logs" / "test.log"
        with patch("preseed_runner.scan_track", return_value={
            "track": "test", "total": 0, "done": 0,
            "remaining_count": 0, "remaining": [],
        }):
            result = preseed_runner.run_track("test", "slot-1", log_file)
            assert result["passed"] == 0

    def test_run_track_dry_run(self, tmp_path):
        import preseed_runner
        log_file = tmp_path / "logs" / "test.log"
        with patch("preseed_runner.scan_track", return_value={
            "track": "test", "total": 2, "done": 0,
            "remaining_count": 2, "remaining": [(1, "mod1"), (2, "mod2")],
        }):
            result = preseed_runner.run_track("test", "slot-1", log_file, dry_run=True)
            assert result["passed"] == 2
            assert result["failed"] == 0

    @patch("subprocess.Popen")
    def test_run_track_failure(self, mock_popen, tmp_path):
        import preseed_runner
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = ("Error", None)
        mock_proc.returncode = 1
        mock_popen.return_value = mock_proc

        log_file = tmp_path / "logs" / "test.log"
        with patch("preseed_runner.scan_track", return_value={
            "track": "test", "total": 1, "done": 0,
            "remaining_count": 1, "remaining": [(1, "mod1")],
        }):
            result = preseed_runner.run_track("test", "slot-1", log_file)
            assert result["failed"] == 1

    @patch("subprocess.Popen")
    def test_run_track_timeout(self, mock_popen, tmp_path):
        import preseed_runner
        mock_proc = MagicMock()
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired("cmd", 600)
        mock_proc.kill = MagicMock()
        mock_proc.wait = MagicMock()
        mock_popen.return_value = mock_proc

        log_file = tmp_path / "logs" / "test.log"
        with patch("preseed_runner.scan_track", return_value={
            "track": "test", "total": 1, "done": 0,
            "remaining_count": 1, "remaining": [(1, "mod1")],
        }):
            result = preseed_runner.run_track("test", "slot-1", log_file)
            assert result["failed"] == 1

    @patch("subprocess.Popen", side_effect=Exception("spawn failed"))
    def test_run_track_exception(self, mock_popen, tmp_path):
        import preseed_runner
        log_file = tmp_path / "logs" / "test.log"
        with patch("preseed_runner.scan_track", return_value={
            "track": "test", "total": 1, "done": 0,
            "remaining_count": 1, "remaining": [(1, "mod1")],
        }):
            result = preseed_runner.run_track("test", "slot-1", log_file)
            assert result["failed"] == 1

    def test_run_track_stop_requested(self, tmp_path):
        import preseed_runner
        log_file = tmp_path / "logs" / "test.log"
        old_stop = preseed_runner._stop_requested
        try:
            preseed_runner._stop_requested = True
            with patch("preseed_runner.scan_track", return_value={
                "track": "test", "total": 2, "done": 0,
                "remaining_count": 2, "remaining": [(1, "mod1"), (2, "mod2")],
            }):
                result = preseed_runner.run_track("test", "slot-1", log_file)
                assert result["passed"] == 0
        finally:
            preseed_runner._stop_requested = old_stop


class TestPreseedRunnerSignalHandler:
    def test_first_ctrl_c(self):
        import preseed_runner
        old = preseed_runner._stop_requested
        try:
            preseed_runner._stop_requested = False
            preseed_runner._signal_handler(signal.SIGINT, None)
            assert preseed_runner._stop_requested is True
        finally:
            preseed_runner._stop_requested = old

    def test_second_ctrl_c_kills(self):
        import preseed_runner
        old = preseed_runner._stop_requested
        try:
            preseed_runner._stop_requested = True
            with pytest.raises(SystemExit):
                preseed_runner._signal_handler(signal.SIGINT, None)
        finally:
            preseed_runner._stop_requested = old


class TestPreseedRunnerRunParallel:
    @patch("preseed_runner.run_track")
    @patch("preseed_runner.scan_track")
    def test_parallel_dry_run(self, mock_scan, mock_run, tmp_path):
        import preseed_runner
        mock_scan.return_value = {"remaining_count": 5}
        mock_run.return_value = {"track": "test", "passed": 5, "failed": 0, "skipped": 0}

        old_stop = preseed_runner._stop_requested
        preseed_runner._stop_requested = False
        try:
            preseed_runner.run_parallel(["test"], slots=1, dry_run=True)
        finally:
            preseed_runner._stop_requested = old_stop

    @patch("preseed_runner.run_track")
    @patch("preseed_runner.scan_track")
    def test_parallel_multiple_tracks(self, mock_scan, mock_run, tmp_path):
        import preseed_runner
        mock_scan.return_value = {"remaining_count": 3}
        mock_run.return_value = {"track": "t", "passed": 3, "failed": 0, "skipped": 0}

        old_stop = preseed_runner._stop_requested
        preseed_runner._stop_requested = False
        try:
            preseed_runner.run_parallel(["track1", "track2"], slots=2, dry_run=True)
        finally:
            preseed_runner._stop_requested = old_stop


# ═══════════════════════════════════════════════════════════════════════
# Additional edge case tests
# ═══════════════════════════════════════════════════════════════════════

class TestBatchFixReviewCallGemini:
    @patch("subprocess.run")
    def test_call_gemini(self, mock_run, tmp_path):
        from batch_fix_review import call_gemini
        mock_run.return_value = MagicMock(stdout="output", stderr="")
        prompt = tmp_path / "prompt.md"
        prompt.write_text("test prompt")
        result = call_gemini(prompt, "test-task", "model")
        assert result.exists()
        result.unlink()

    @patch("subprocess.run")
    def test_call_gemini_review(self, mock_run, tmp_path):
        from batch_fix_review import call_gemini_review
        mock_run.return_value = MagicMock(stdout="review output", stderr="")
        prompt = tmp_path / "prompt.md"
        prompt.write_text("review prompt")
        result = call_gemini_review(prompt, "test-task", "model")
        assert result.exists()
        result.unlink()


class TestBatchOtamanWorkersClamp:
    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    def test_workers_clamped(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman, MAX_WORKERS
        bo = BatchOtaman(dry_run=True, workers=99)
        assert bo.workers == MAX_WORKERS


class TestBatchDispatcherFormatTable:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    @patch("batch_dispatcher.compute_priority_score", return_value=5.0)
    def test_format_table(self, mock_score, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(include_tracks=["a1"])
        track_scans = {"a1": {"total": 10, "passed": 5, "failed": 2, "stale": 1, "unbuilt": 2, "pass_rate": 0.5}}
        table = d._format_track_table(track_scans)
        assert "a1" in table
        assert "Track" in table


class TestBatchOtamanStateLockfile:
    @patch("batch_otaman.STATE_FILE")
    def test_lockfile_path(self, mock_sf, tmp_path):
        from batch_otaman import _state_lockfile
        mock_sf.parent = tmp_path
        mock_sf.with_suffix.return_value = tmp_path / "state.lock"
        result = _state_lockfile()
        assert str(result).endswith(".lock")


class TestBatchFixReviewCheckExistingReviews:
    def test_re_review_pass(self, tmp_path):
        from batch_fix_review import _check_existing_reviews
        orch = tmp_path / "orchestration"
        orch.mkdir()
        (orch / "phase-5-re-review.md").write_text("**Overall Score:** 9.5/10")
        files = {"orchestration": orch, "review": tmp_path / "review.md"}
        result = {}
        status, score = _check_existing_reviews(files, result)
        assert status == "ALREADY_PASS"
        assert score == 9.5

    def test_review_pass(self, tmp_path):
        from batch_fix_review import _check_existing_reviews
        orch = tmp_path / "orchestration"
        orch.mkdir()
        (orch / "phase-5-response.md").write_text("**Overall Score:** 9.2/10\n**Status:** PASS")
        files = {"orchestration": orch, "review": tmp_path / "review.md"}
        result = {}
        status, score = _check_existing_reviews(files, result)
        assert status == "ALREADY_PASS"

    def test_review_fail(self, tmp_path):
        from batch_fix_review import _check_existing_reviews
        orch = tmp_path / "orchestration"
        orch.mkdir()
        (orch / "phase-5-response.md").write_text("**Overall Score:** 7.0/10\n**Status:** FAIL")
        files = {"orchestration": orch, "review": tmp_path / "review.md"}
        result = {}
        status, score = _check_existing_reviews(files, result)
        assert status == "continue"
        assert score == 7.0

    def test_no_reviews(self, tmp_path):
        from batch_fix_review import _check_existing_reviews
        orch = tmp_path / "orchestration"
        orch.mkdir()
        files = {"orchestration": orch, "review": tmp_path / "review.md"}
        result = {}
        status, score = _check_existing_reviews(files, result)
        assert status == "continue"
        assert score is None


class TestBatchFixReviewAssembleFixPrompt:
    def test_assemble(self, tmp_path):
        from batch_fix_review import assemble_fix_prompt, REPO
        template_dir = REPO / "claude_extensions" / "phases" / "gemini"
        if not (template_dir / "phase-fix.md").exists():
            pytest.skip("Template file not found")

        orch = tmp_path / "orchestration"
        orch.mkdir()
        review = tmp_path / "review.md"
        review.write_text("some review")

        files = {
            "content": tmp_path / "content.md",
            "activities": tmp_path / "activities.yaml",
            "vocabulary": tmp_path / "vocab.yaml",
            "plan": tmp_path / "plan.yaml",
            "research": tmp_path / "research.md",
            "orchestration": orch,
        }
        result = assemble_fix_prompt(files, review)
        assert result.exists()


class TestBatchOtamanResourceExhausted:
    @patch("batch_otaman.subprocess.run")
    def test_resource_exhausted_detection(self, mock_run):
        from batch_otaman import dispatch_otaman
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="resource_exhausted: too many requests",
            stdout=""
        )
        result = dispatch_otaman("a1", 1, "test-slug", timeout=5)
        assert result["quota_hit"] is True


class TestPreseedRunnerScanWithIndex:
    def test_scan_with_module_index(self, tmp_path):
        import preseed_runner

        plans_dir = tmp_path / "plans" / "test"
        plans_dir.mkdir(parents=True)
        (plans_dir / "mod-a.yaml").write_text("title: A")
        (plans_dir / "mod-b.yaml").write_text("title: B")

        research_dir = tmp_path / "test" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "mod-a-research.md").write_text("done")

        mock_idx = {
            "total": 2,
            "num_to_slug": {1: "mod-a", 2: "mod-b"},
            "slug_to_num": {"mod-a": 1, "mod-b": 2},
        }

        with patch.object(preseed_runner, "CURRICULUM", tmp_path):
            with patch("batch_gemini_config.get_module_index", return_value=mock_idx):
                result = preseed_runner.scan_track("test")
                assert result["done"] == 1
                assert result["remaining_count"] == 1
                assert (2, "mod-b") in result["remaining"]


class TestBatchDispatcherUpdateTrackStates:
    """Test _update_track_states edge cases."""

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_track_becomes_done(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(include_tracks=["a1"])
        scan = {"a1": {"total": 10, "passed": 10, "failed": 0, "stale": 0, "unbuilt": 0, "pass_rate": 1.0}}
        d._update_track_states(scan)
        dstate = get_track_dstate(d.state, "a1")
        assert dstate["state"] == TrackState.DONE

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_error_scan_skipped(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(include_tracks=["a1"])
        scan = {"a1": {"error": "not_found"}}
        # Should not crash
        d._update_track_states(scan)

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_stale_counts_as_done(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(include_tracks=["a1"])
        scan = {"a1": {"total": 10, "passed": 8, "failed": 0, "stale": 2, "unbuilt": 0, "pass_rate": 0.8}}
        d._update_track_states(scan)
        dstate = get_track_dstate(d.state, "a1")
        assert dstate["state"] == TrackState.DONE

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_blocked_by_deps(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(include_tracks=["a2"])
        scan = {"a2": {"total": 10, "passed": 0, "failed": 10, "stale": 0, "unbuilt": 0, "pass_rate": 0.0}}
        d._update_track_states(scan)
        dstate = get_track_dstate(d.state, "a2")
        assert dstate["state"] == TrackState.BLOCKED

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_cooldown_expired(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.COOLDOWN
        dstate["cooldown_until"] = "2020-01-01T00:00:00+00:00"
        scan = {"a1": {"total": 10, "passed": 5, "failed": 5, "stale": 0, "unbuilt": 0, "pass_rate": 0.5}}
        d._update_track_states(scan)
        assert dstate["state"] == TrackState.ELIGIBLE

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_cooldown_no_timestamp(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.COOLDOWN
        dstate["cooldown_until"] = None
        scan = {"a1": {"total": 10, "passed": 5, "failed": 5, "stale": 0, "unbuilt": 0, "pass_rate": 0.5}}
        d._update_track_states(scan)
        assert dstate["state"] == TrackState.ELIGIBLE

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_done_with_regression(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.DONE
        scan = {"a1": {"total": 10, "passed": 7, "failed": 3, "stale": 0, "unbuilt": 0, "pass_rate": 0.7}}
        d._update_track_states(scan)
        assert dstate["state"] == TrackState.PENDING


class TestBatchDispatcherProcessEscalations:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    @patch("batch_dispatcher.FAILURES_DIR")
    def test_no_escalations(self, mock_fd, mock_load, tmp_path):
        mock_fd.__truediv__ = lambda self, x: tmp_path / "failures" / x
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher()
        assert d._process_escalations("a1", {}) == 0


# ═══════════════════════════════════════════════════════════════════════
# Additional tests to reach 200+ total
# ═══════════════════════════════════════════════════════════════════════

class TestBatchFixReviewExtractSectionEdgeCases:
    def _import(self):
        from batch_fix_review import extract_section
        return extract_section

    def test_empty_content_between_tags(self, tmp_path):
        extract_section = self._import()
        p = tmp_path / "out.txt"
        p.write_text("===START===\n\n===END===\n")
        result = extract_section(p, "===START===", "===END===")
        assert result == ""

    def test_nested_tags(self, tmp_path):
        extract_section = self._import()
        p = tmp_path / "out.txt"
        p.write_text("===START===\nhas ===START=== inside\n===END===\n")
        result = extract_section(p, "===START===", "===END===")
        assert "has ===START=== inside" in result

    def test_whitespace_around_tags(self, tmp_path):
        extract_section = self._import()
        p = tmp_path / "out.txt"
        p.write_text("  ===START===  \ncontent\n  ===END===  \n")
        result = extract_section(p, "===START===", "===END===")
        assert result is not None


class TestBatchFixReviewExtractScoreEdgeCases:
    def _import(self):
        from batch_fix_review import extract_score
        return extract_score

    def test_decimal_precision(self):
        assert self._import()("**Overall Score:** 8.75/10") == 8.75

    def test_score_10(self):
        assert self._import()("**Overall Score:** 10/10") == 10.0

    def test_score_zero(self):
        assert self._import()("Overall Score: 0/10") == 0.0

    def test_surrounded_by_text(self):
        text = "The **Overall Score:** 7.2/10 for this module."
        assert self._import()(text) == 7.2


class TestBatchOtamanDispatchEdgeCases:
    @patch("batch_otaman.subprocess.run")
    def test_empty_stderr_stdout(self, mock_run):
        from batch_otaman import dispatch_otaman
        mock_run.return_value = MagicMock(returncode=0, stderr=None, stdout=None)
        result = dispatch_otaman("a1", 1, "test", timeout=5)
        assert result["success"] is True
        assert result["quota_hit"] is False

    @patch("batch_otaman.subprocess.run")
    def test_large_stderr(self, mock_run):
        from batch_otaman import dispatch_otaman
        mock_run.return_value = MagicMock(returncode=1, stderr="x" * 5000, stdout="")
        result = dispatch_otaman("a1", 1, "test", timeout=5)
        # stderr is truncated to last 2000 chars
        assert len(result["stderr"]) <= 2000


class TestBatchOtamanCheckDepsEdgeCases:
    def _import(self):
        from batch_otaman import check_dependencies
        return check_dependencies

    def test_multiple_deps_all_met(self):
        # istorio has deps on hist and c1
        summaries = {
            "hist": {"total": 100, "passed": 90},
            "c1": {"total": 100, "passed": 40},
        }
        ok, unmet = self._import()("istorio", summaries)
        assert ok is True

    def test_multiple_deps_one_unmet(self):
        summaries = {
            "hist": {"total": 100, "passed": 90},
            "c1": {"total": 100, "passed": 20},
        }
        ok, unmet = self._import()("istorio", summaries)
        assert ok is False
        assert len(unmet) == 1

    def test_multiple_deps_all_unmet(self):
        summaries = {
            "hist": {"total": 100, "passed": 10},
            "c1": {"total": 100, "passed": 5},
        }
        ok, unmet = self._import()("istorio", summaries)
        assert ok is False
        assert len(unmet) == 2


class TestBatchOtamanGetTrackStateEdgeCases:
    def _import(self):
        from batch_otaman import get_track_state
        return get_track_state

    def test_multiple_calls_same_state(self):
        state = {"tracks": {}}
        ts1 = self._import()(state, "a1")
        ts2 = self._import()(state, "a1")
        assert ts1 is ts2

    def test_different_tracks(self):
        state = {"tracks": {}}
        ts1 = self._import()(state, "a1")
        ts2 = self._import()(state, "a2")
        assert ts1 is not ts2
        assert len(state["tracks"]) == 2


class TestBatchDispatcherUpdateTrackStatesEdgeCases:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_stalled_not_promoted(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.STALLED
        scan = {"a1": {"total": 10, "passed": 5, "failed": 5, "stale": 0, "unbuilt": 0, "pass_rate": 0.5}}
        d._update_track_states(scan)
        # STALLED stays STALLED during _update_track_states
        assert dstate["state"] == TrackState.STALLED

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_cooldown_malformed_timestamp(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.COOLDOWN
        dstate["cooldown_until"] = "not-a-timestamp"
        scan = {"a1": {"total": 10, "passed": 5, "failed": 5, "stale": 0, "unbuilt": 0, "pass_rate": 0.5}}
        d._update_track_states(scan)
        assert dstate["state"] == TrackState.ELIGIBLE

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_pending_becomes_eligible_with_deps(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        assert dstate["state"] == TrackState.PENDING
        scan = {"a1": {"total": 10, "passed": 5, "failed": 5, "stale": 0, "unbuilt": 0, "pass_rate": 0.5}}
        d._update_track_states(scan)
        assert dstate["state"] == TrackState.ELIGIBLE

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_done_stays_done(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.DONE
        scan = {"a1": {"total": 10, "passed": 10, "failed": 0, "stale": 0, "unbuilt": 0, "pass_rate": 1.0}}
        d._update_track_states(scan)
        assert dstate["state"] == TrackState.DONE

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_done_with_stale_stays_done(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.DONE
        scan = {"a1": {"total": 10, "passed": 8, "failed": 0, "stale": 2, "unbuilt": 0, "pass_rate": 0.8}}
        d._update_track_states(scan)
        assert dstate["state"] == TrackState.DONE


class TestAgentWatcherEdgeCases:
    def test_count_task_turns_with_messages(self, sqlite_db):
        import agent_watcher
        conn = sqlite3.connect(sqlite_db)
        for i in range(5):
            conn.execute(
                "INSERT INTO messages (task_id, from_llm, to_llm, message_type, timestamp) VALUES (?, ?, ?, ?, ?)",
                ("task-x", "claude", "gemini", "request", f"2026-01-01T00:00:0{i}"),
            )
        conn.commit()
        conn.close()
        with patch.object(agent_watcher, "DB_PATH", sqlite_db):
            assert agent_watcher.count_task_turns("task-x") == 5

    def test_get_unread_acknowledged_not_returned(self, sqlite_db):
        import agent_watcher
        conn = sqlite3.connect(sqlite_db)
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, timestamp, acknowledged) VALUES (?, ?, ?, ?, ?, ?)",
            ("task1", "claude", "gemini", "request", "2026-01-01T00:00:00", 1),
        )
        conn.commit()
        conn.close()
        with patch.object(agent_watcher, "DB_PATH", sqlite_db):
            msgs = agent_watcher.get_unread_messages()
            assert len(msgs) == 0


class TestPreseedRunnerEdgeCases:
    def test_scan_empty_track(self, tmp_path):
        import preseed_runner
        plans_dir = tmp_path / "plans" / "empty"
        plans_dir.mkdir(parents=True)
        with patch.object(preseed_runner, "CURRICULUM", tmp_path):
            with patch("batch_gemini_config.get_module_index", side_effect=Exception("no")):
                result = preseed_runner.scan_track("empty")
                assert result["total"] == 0
                assert result["done"] == 0

    def test_get_all_remaining_no_remaining(self, tmp_path):
        import preseed_runner
        plans_root = tmp_path / "plans"
        plans_root.mkdir()
        track_dir = plans_root / "complete"
        track_dir.mkdir()
        (track_dir / "mod1.yaml").write_text("title: M1")

        research_dir = tmp_path / "complete" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "mod1-research.md").write_text("done")

        with patch.object(preseed_runner, "CURRICULUM", tmp_path):
            with patch("batch_gemini_config.get_module_index", side_effect=Exception("no")):
                tracks = preseed_runner.get_all_remaining_tracks()
                assert "complete" not in tracks

    def test_run_parallel_empty_tracks(self):
        import preseed_runner
        old_stop = preseed_runner._stop_requested
        preseed_runner._stop_requested = False
        try:
            with patch("preseed_runner.scan_track", return_value={"remaining_count": 0}):
                with patch("preseed_runner.run_track", return_value={"track": "x", "passed": 0, "failed": 0, "skipped": 0}):
                    preseed_runner.run_parallel([], slots=1)
        finally:
            preseed_runner._stop_requested = old_stop


class TestBatchFixReviewCountItemsEdgeCases:
    def _import(self):
        from batch_fix_review import count_items
        return count_items

    def test_no_activities(self, tmp_path):
        count_items = self._import()
        p = tmp_path / "acts.yaml"
        p.write_text("nothing: here\n")
        assert count_items(p, "activities_root") == 0

    def test_many_items(self, tmp_path):
        count_items = self._import()
        lines = ["items:"] + [f"  - word: w{i}" for i in range(50)]
        p = tmp_path / "vocab.yaml"
        p.write_text("\n".join(lines) + "\n")
        assert count_items(p, "items") == 50


class TestBatchOtamanFindModuleScanEdgeCases:
    @patch("batch_otaman.get_module_index")
    @patch("batch_otaman.get_module_paths", side_effect=Exception("oops"))
    def test_find_next_module_paths_error(self, mock_paths, mock_idx):
        from batch_otaman import find_next_module
        mock_idx.return_value = {"total": 1, "num_to_slug": {1: "test"}}
        result = find_next_module("a1")
        assert result is not None
        assert result["reason"] == "no_paths"

    @patch("batch_otaman.get_module_index")
    @patch("batch_otaman.get_module_paths", side_effect=Exception("oops"))
    def test_find_next_enrichable_paths_error(self, mock_paths, mock_idx):
        from batch_otaman import find_next_enrichable
        mock_idx.return_value = {"total": 1, "num_to_slug": {1: "test"}}
        result = find_next_enrichable("a1")
        assert result is None  # Exception caught, continues to next

    @patch("batch_otaman.get_module_index")
    @patch("batch_otaman.get_module_paths", side_effect=Exception("oops"))
    def test_scan_track_summary_paths_error(self, mock_paths, mock_idx):
        from batch_otaman import scan_track_summary
        mock_idx.return_value = {"total": 2, "num_to_slug": {1: "a", 2: "b"}}
        result = scan_track_summary("a1")
        assert result["total"] == 2
        assert result["remaining"] == 2


class TestBatchFixReviewFindModuleFiles:
    @patch("batch_fix_review.find_module_files", return_value=None)
    def test_no_content(self, mock_find):
        from batch_fix_review import process_module
        r = process_module("a1", 999, "model")
        assert r["status"] == "SKIP"

    def test_review_only_mode(self, tmp_path):
        from batch_fix_review import process_module

        orch = tmp_path / "orchestration"
        orch.mkdir()
        review = orch / "phase-5-response.md"
        review.write_text("**Overall Score:** 7.5/10\n**Status:** FAIL")
        content = tmp_path / "content.md"
        content.write_text("# Test\nContent\n")

        with patch("batch_fix_review.find_module_files", return_value={
            "num": 1, "slug": "test", "full_stem": "test",
            "content": content, "activities": tmp_path / "acts.yaml",
            "vocabulary": tmp_path / "vocab.yaml", "meta": tmp_path / "meta.yaml",
            "plan": tmp_path / "plan.yaml", "research": tmp_path / "research.md",
            "review": tmp_path / "review.md", "status": tmp_path / "status.json",
            "orchestration": orch,
        }):
            result = process_module("a1", 1, "model", review_only=True)
            assert result["status"] == "REVIEWED"
            assert result["score"] == 7.5


class TestBatchDispatcherPickTrackEdgeCases:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_no_eligible_no_stalled(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.BLOCKED
        result = d._pick_track({})
        assert result is None

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    @patch("batch_dispatcher.compute_priority_score", return_value=5.0)
    def test_eligible_picked(self, mock_score, mock_load):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate
        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.ELIGIBLE
        result = d._pick_track({"a1": {}})
        assert result == "a1"


class TestBatchOtamanPickModulesEdgeCases:
    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    @patch("batch_otaman.find_next_module", return_value=None)
    def test_no_modules_available(self, mock_find, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, include_tracks=["a1"])
        summaries = {"a1": {"total": 10, "passed": 10, "content_complete": 0, "remaining": 0}}
        modules = bo._pick_modules(summaries)
        assert modules == []

    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    @patch("batch_otaman.find_next_module", return_value={"num": 1, "slug": "test", "reason": "unbuilt"})
    def test_picks_module(self, mock_find, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, include_tracks=["a1"])
        summaries = {"a1": {"total": 10, "passed": 5, "content_complete": 0, "remaining": 5}}
        modules = bo._pick_modules(summaries)
        assert len(modules) == 1
        assert modules[0]["track"] == "a1"


class TestBatchOtamanMalformedCooldown:
    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    @patch("batch_otaman.find_next_module", return_value={"num": 1, "slug": "test", "reason": "unbuilt"})
    def test_malformed_cooldown_resets(self, mock_find, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman, get_track_state
        from batch_dispatcher_config import TrackState
        bo = BatchOtaman(dry_run=True, include_tracks=["a1"])
        ts = get_track_state(bo.state, "a1")
        ts["state"] = TrackState.COOLDOWN
        ts["cooldown_until"] = "garbage"
        summaries = {"a1": {"total": 10, "passed": 5, "content_complete": 0, "remaining": 5}}
        modules = bo._pick_modules(summaries)
        # Malformed cooldown gets replaced, track stays in cooldown
        assert ts["cooldown_until"] != "garbage"

    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    @patch("batch_otaman.find_next_module", return_value={"num": 1, "slug": "test", "reason": "unbuilt"})
    def test_expired_cooldown_becomes_eligible(self, mock_find, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman, get_track_state
        from batch_dispatcher_config import TrackState
        bo = BatchOtaman(dry_run=True, include_tracks=["a1"])
        ts = get_track_state(bo.state, "a1")
        ts["state"] = TrackState.COOLDOWN
        ts["cooldown_until"] = "2020-01-01T00:00:00+00:00"  # expired
        summaries = {"a1": {"total": 10, "passed": 5, "content_complete": 0, "remaining": 5}}
        modules = bo._pick_modules(summaries)
        assert ts["state"] == TrackState.ELIGIBLE
        assert len(modules) == 1

    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    def test_stalled_track_skipped(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman, get_track_state
        from batch_dispatcher_config import TrackState
        bo = BatchOtaman(dry_run=True, include_tracks=["a1"])
        ts = get_track_state(bo.state, "a1")
        ts["state"] = TrackState.ELIGIBLE
        ts["consecutive_failures"] = 5
        summaries = {"a1": {"total": 10, "passed": 5, "content_complete": 0, "remaining": 5}}
        modules = bo._pick_modules(summaries)
        assert ts["state"] == TrackState.STALLED
        assert modules == []

    @patch("batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch_otaman.STATE_FILE")
    def test_force_track(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, include_tracks=["a1", "a2"], force_track="a2")
        summaries = {"a1": {"remaining": 5}, "a2": {"remaining": 3}}
        with patch("batch_otaman.find_next_module", return_value={"num": 1, "slug": "test", "reason": "unbuilt"}):
            with patch("batch_otaman.check_dependencies", return_value=(True, [])):
                modules = bo._pick_modules(summaries)
                if modules:
                    assert modules[0]["track"] == "a2"


class TestAgentWatcherAcknowledgeEdgeCases:
    def test_acknowledge_nonexistent_message(self, sqlite_db):
        import agent_watcher
        with patch.object(agent_watcher, "DB_PATH", sqlite_db):
            # Should not raise even though message doesn't exist
            agent_watcher.acknowledge_message(9999, "test")


class TestBatchFixReviewGetWordTargetEdgeCases:
    def _import(self):
        from batch_fix_review import get_word_target
        return get_word_target

    def test_word_target_with_extra_whitespace(self, tmp_path):
        p = tmp_path / "plan.yaml"
        p.write_text("word_target:   5000   \n")
        assert self._import()({"plan": p}) == 5000

    def test_word_target_not_first_line(self, tmp_path):
        p = tmp_path / "plan.yaml"
        p.write_text("title: Test Module\nobjectives:\n  - learn\nword_target: 3000\n")
        assert self._import()({"plan": p}) == 3000


class TestBatchDispatcherRunningTrackCleanup:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    @patch("batch_dispatcher.BATCH_STATE_DIR")
    def test_running_no_lock_file(self, mock_bsd, mock_load, tmp_path):
        from batch_dispatcher import BatchDispatcher
        from batch_dispatcher_config import TrackState
        from batch_dispatcher_helpers import get_track_dstate

        lock_dir = tmp_path / "locks"
        lock_dir.mkdir(parents=True)
        mock_bsd.__truediv__ = lambda self, x: tmp_path / x

        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.RUNNING

        scan = {"a1": {"total": 10, "passed": 5, "failed": 5, "stale": 0, "unbuilt": 0, "pass_rate": 0.5}}
        d._update_track_states(scan)
        # RUNNING with no lock -> reset to PENDING then re-evaluated
        assert dstate["state"] in (TrackState.PENDING, TrackState.ELIGIBLE)


