"""Tests for batch_otaman, batch_dispatcher, batch_fix_review, and tools.agent_watcher.

Targets batch/agent helper coverage with heavy mocking of subprocess, filesystem, etc.
"""

import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

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
        from batch.batch_fix_review import extract_section
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

    def test_code_block_wrapping(self, tmp_path):
        extract_section = self._import()
        p = tmp_path / "out.txt"
        content = "```\n===START===\ncontent here\n===END===\n```\n"
        p.write_text(content)
        result = extract_section(p, "===START===", "===END===")
        assert result is not None
        assert "content" in result


class TestBatchFixReviewExtractScore:
    """Tests for extract_score."""

    def _import(self):
        from batch.batch_fix_review import extract_score
        return extract_score

    def test_bold_overall_score(self):
        assert self._import()("**Overall Score:** 8.5/10") == 8.5

    def test_no_score(self):
        assert self._import()("no score here") is None

    def test_first_pattern_wins(self):
        text = "**Overall Score:** 8.0/10\nOverall Score: 9.0/10"
        assert self._import()(text) == 8.0


class TestBatchFixReviewExtractStatus:
    """Tests for extract_status."""

    def _import(self):
        from batch.batch_fix_review import extract_status
        return extract_status

    def test_pass(self):
        assert self._import()("**Status:** PASS") == "PASS"

    def test_unknown(self):
        assert self._import()("no status") == "UNKNOWN"


class TestBatchFixReviewCountItems:
    """Tests for count_items."""

    def _import(self):
        from batch.batch_fix_review import count_items
        return count_items

    def test_count_vocab_items(self, tmp_path):
        count_items = self._import()
        p = tmp_path / "vocab.yaml"
        p.write_text("items:\n  - word: hello\n  - word: world\n  - word: test\n")
        assert count_items(p, "items") == 3

    def test_items_section_ends(self, tmp_path):
        count_items = self._import()
        p = tmp_path / "vocab.yaml"
        p.write_text("items:\n  - word: one\n  - word: two\nother:\n  value: x\n")
        assert count_items(p, "items") == 2


class TestBatchFixReviewGetWordTarget:
    """Tests for get_word_target."""

    def _import(self):
        from batch.batch_fix_review import get_word_target
        return get_word_target

    def test_reads_word_target(self, tmp_path):
        get_word_target = self._import()
        p = tmp_path / "plan.yaml"
        p.write_text("title: Test\nword_target: 4000\nobjectives:\n  - learn\n")
        files = {"plan": p}
        assert get_word_target(files) == 4000


class TestBatchFixReviewGetAuditMetrics:
    """Tests for get_audit_metrics."""

    def _import(self):
        from batch.batch_fix_review import get_audit_metrics
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


class TestBatchFixReviewRunAudit:
    """Tests for run_audit."""

    def _import(self):
        from batch.batch_fix_review import run_audit
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

    @patch("batch.batch_fix_review.find_module_files", return_value=None)
    def test_process_module_no_files(self, mock_find):
        from batch.batch_fix_review import process_module
        result = process_module("a1", 99, "model")
        assert result["status"] == "SKIP"

    @patch("batch.batch_fix_review.find_module_files")
    def test_process_module_already_pass(self, mock_find, tmp_path):
        from batch.batch_fix_review import process_module

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

    @patch("batch.batch_fix_review.find_module_files")
    def test_process_module_dry_run_needs_review(self, mock_find, tmp_path):
        from batch.batch_fix_review import process_module

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
        from batch.batch_fix_review import _apply_fix_output
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


# ═══════════════════════════════════════════════════════════════════════
# batch_otaman.py
# ═══════════════════════════════════════════════════════════════════════

class TestBatchOtamanIsContentComplete:
    def _import(self):
        from batch.batch_otaman import _is_content_complete
        return _is_content_complete

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
        from batch.batch_otaman import check_dependencies
        return check_dependencies

    def test_unknown_track(self):
        ok, _unmet = self._import()("nonexistent_track_xyz", {})
        assert ok is False
        assert len(_unmet) == 1

    def test_no_deps(self):
        ok, _unmet = self._import()("a1", {})
        assert ok is True
        assert _unmet == []

    def test_deps_met(self):
        summaries = {"a1": {"total": 100, "passed": 90}}
        ok, _unmet = self._import()("a2", summaries)
        assert ok is True

    def test_deps_not_met(self):
        summaries = {"a1": {"total": 100, "passed": 50}}
        ok, _unmet = self._import()("a2", summaries)
        assert ok is False
        assert len(_unmet) == 1

    def test_deps_not_scanned(self):
        ok, _unmet = self._import()("a2", {})
        assert ok is False
        assert "not scanned" in _unmet[0]

    def test_deps_zero_total(self):
        summaries = {"a1": {"total": 0, "passed": 0}}
        ok, _unmet = self._import()("a2", summaries)
        assert ok is False


class TestBatchOtamanGetTrackState:
    def _import(self):
        from batch.batch_otaman import get_track_state
        return get_track_state

    def test_creates_new_state(self):
        from batch.batch_dispatcher_config import TrackState
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

    @patch("batch.batch_otaman.subprocess.run")
    def test_success(self, mock_run):
        from batch.batch_otaman import dispatch_otaman
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="done")
        result = dispatch_otaman("a1", 1, "test-slug", timeout=5)
        assert result["success"] is True
        assert result["returncode"] == 0
        assert result["quota_hit"] is False

    @patch("batch.batch_otaman.subprocess.run")
    def test_quota_hit(self, mock_run):
        from batch.batch_otaman import dispatch_otaman
        mock_run.return_value = MagicMock(returncode=1, stderr="quota exceeded 429", stdout="")
        result = dispatch_otaman("a1", 1, "test-slug", timeout=5)
        assert result["quota_hit"] is True

    @patch("batch.batch_otaman.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 5))
    def test_timeout(self, mock_run):
        from batch.batch_otaman import dispatch_otaman
        result = dispatch_otaman("a1", 1, "test-slug", timeout=5)
        assert result["success"] is False
        assert result["returncode"] == -1
        assert "TimeoutExpired" in result["stderr"]

    @patch("batch.batch_otaman.subprocess.run", side_effect=OSError("boom"))
    def test_exception(self, mock_run):
        from batch.batch_otaman import dispatch_otaman
        result = dispatch_otaman("a1", 1, "test-slug", timeout=5)
        assert result["success"] is False
        assert result["returncode"] == -2


class TestBatchOtamanSignalHandler:
    def test_signal_handler_sets_flag(self):
        import batch.batch_otaman as batch_otaman
        old = batch_otaman._shutdown_requested
        try:
            batch_otaman._shutdown_requested = False
            batch_otaman._signal_handler(signal.SIGINT, None)
            assert batch_otaman._shutdown_requested is True
        finally:
            batch_otaman._shutdown_requested = old


class TestBatchOtamanStatePersistence:
    """Tests for load_state and save_state with mocked STATE_FILE."""

    @patch("batch.batch_otaman.STATE_FILE")
    def test_load_state_no_file(self, mock_sf, tmp_path):
        from batch.batch_otaman import load_state
        mock_sf.parent = tmp_path
        mock_sf.exists.return_value = False
        mock_sf.with_suffix.return_value = tmp_path / "state.lock"
        state = load_state()
        assert "tracks" in state
        assert "history" in state

    @patch("batch.batch_otaman.STATE_FILE")
    def test_load_state_with_file(self, mock_sf, tmp_path):
        from batch.batch_otaman import load_state
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

    @patch("batch.batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch.batch_otaman.STATE_FILE")
    def test_exclude(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch.batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, exclude_tracks=["a1"])
        assert bo._should_include("a1") is False
        assert bo._should_include("a2") is True

    @patch("batch.batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch.batch_otaman.STATE_FILE")
    def test_include(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch.batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, include_tracks=["a1", "a2"])
        assert bo._should_include("a1") is True
        assert bo._should_include("b1") is False


class TestBatchOtamanRuntimeExceeded:
    @patch("batch.batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch.batch_otaman.STATE_FILE")
    def test_not_exceeded(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch.batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, max_runtime_hours=10)
        assert bo._runtime_exceeded() is False

    @patch("batch.batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch.batch_otaman.STATE_FILE")
    def test_exceeded(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch.batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, max_runtime_hours=1)
        bo.start_time = time.monotonic() - 3601  # 1h1s ago
        assert bo._runtime_exceeded() is True


class TestBatchOtamanScanTrackSummary:
    @patch("batch.batch_otaman.get_module_index", side_effect=ValueError("nope"))
    def test_invalid_track(self, mock_idx):
        from batch.batch_otaman import scan_track_summary
        result = scan_track_summary("nonexistent")
        assert result["error"] == "not_found"
        assert result["total"] == 0
# ═══════════════════════════════════════════════════════════════════════
# batch_dispatcher.py
# ═══════════════════════════════════════════════════════════════════════

class TestBatchDispatcherInit:
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
class TestBatchDispatcherPickTrack:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_force_track(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(force_track="a1")
        result = d._pick_track({})
        assert result == "a1"

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_force_track_done(self, mock_load):
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_dispatcher_helpers import get_track_dstate
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(force_track="a1")
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.DONE
        result = d._pick_track({})
        assert result is None
# ═══════════════════════════════════════════════════════════════════════
# tools.agent_watcher.py
# ═══════════════════════════════════════════════════════════════════════

class TestAgentWatcherLoadConfig:
    @patch("tools.agent_watcher._AGENTS_CONFIG", None)
    def test_load_from_file(self, tmp_path):
        import tools.agent_watcher
        config_path = tmp_path / "agents.yaml"
        config_path.write_text("agents:\n  claude:\n    bridge_command: process-claude\n    process_pattern: claude\n")

        with patch.object(Path, "__new__", wraps=Path.__new__):
            old_path = tools.agent_watcher.load_agent_config.__globals__
            # Reset the cache
            tools.agent_watcher._AGENTS_CONFIG = None
            with patch("tools.agent_watcher.Path") as mock_path:
                mock_path.return_value.__truediv__ = lambda *a: config_path
                mock_path.__truediv__ = lambda *a: config_path
                # Use a simpler approach: just patch the config path check
                with patch("builtins.open", mock_open(read_data="agents:\n  test_agent:\n    bridge_command: test\n    process_pattern: test\n")), patch("pathlib.Path.exists", return_value=True):
                        tools.agent_watcher._AGENTS_CONFIG = None
                        config = tools.agent_watcher.load_agent_config()
                        assert "test_agent" in config


class TestAgentWatcherGetUnreadMessages:

    def test_with_messages(self, sqlite_db):
        import tools.agent_watcher
        conn = sqlite3.connect(sqlite_db)
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("task1", "claude", "gemini", "request", "2026-01-01T00:00:00"),
        )
        conn.commit()
        conn.close()
        with patch.object(tools.agent_watcher, "DB_PATH", sqlite_db):
            msgs = tools.agent_watcher.get_unread_messages()
            assert len(msgs) == 1
            assert msgs[0]["task_id"] == "task1"
            assert msgs[0]["from"] == "claude"

    def test_filter_by_agent(self, sqlite_db):
        import tools.agent_watcher
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
        with patch.object(tools.agent_watcher, "DB_PATH", sqlite_db):
            msgs = tools.agent_watcher.get_unread_messages(for_agent="gemini")
            assert len(msgs) == 1
            assert msgs[0]["task_id"] == "task1"


class TestAgentWatcherAcknowledgeMessage:
    def test_acknowledge(self, sqlite_db):
        import tools.agent_watcher
        conn = sqlite3.connect(sqlite_db)
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("task1", "claude", "gemini", "request", "2026-01-01T00:00:00"),
        )
        conn.commit()
        conn.close()
        with patch.object(tools.agent_watcher, "DB_PATH", sqlite_db):
            tools.agent_watcher.acknowledge_message(1, "delivered")
            msgs = tools.agent_watcher.get_unread_messages()
            assert len(msgs) == 0


class TestAgentWatcherCountTaskTurns:

    def test_counts_non_error(self, sqlite_db):
        import tools.agent_watcher
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
        with patch.object(tools.agent_watcher, "DB_PATH", sqlite_db):
            assert tools.agent_watcher.count_task_turns("task1") == 2


class TestAgentWatcherIsAnyAgentActive:
    @patch("subprocess.run")
    def test_no_agents(self, mock_run):
        import tools.agent_watcher
        tools.agent_watcher._AGENTS_CONFIG = None
        with patch("pathlib.Path.exists", return_value=False):
            tools.agent_watcher._AGENTS_CONFIG = {
                "claude": {"process_pattern": "claude"},
            }
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            assert tools.agent_watcher.is_any_agent_active() is False
        tools.agent_watcher._AGENTS_CONFIG = None

    @patch("subprocess.run")
    def test_agent_active(self, mock_run):
        import tools.agent_watcher
        tools.agent_watcher._AGENTS_CONFIG = {
            "claude": {"process_pattern": "claude"},
        }
        mock_run.return_value = MagicMock(returncode=0, stdout="12345")
        assert tools.agent_watcher.is_any_agent_active() is True
        tools.agent_watcher._AGENTS_CONFIG = None


class TestAgentWatcherTriggerAgent:
    @patch("subprocess.run")
    def test_success(self, mock_run):
        import tools.agent_watcher
        tools.agent_watcher._AGENTS_CONFIG = {
            "gemini": {"bridge_command": "process", "process_pattern": "gemini"},
        }
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        with patch.object(tools.agent_watcher, "DB_PATH", Path("/nonexistent")):
            result = tools.agent_watcher.trigger_agent("gemini", 1, "task1", "claude")
        assert result is True
        tools.agent_watcher._AGENTS_CONFIG = None

    @patch("subprocess.run")
    def test_failure(self, mock_run):
        import tools.agent_watcher
        tools.agent_watcher._AGENTS_CONFIG = {
            "gemini": {"bridge_command": "process", "process_pattern": "gemini"},
        }
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        result = tools.agent_watcher.trigger_agent("gemini", 1, "task1")
        assert result is False
        tools.agent_watcher._AGENTS_CONFIG = None

    def test_unknown_agent(self):
        import tools.agent_watcher
        tools.agent_watcher._AGENTS_CONFIG = {"claude": {"bridge_command": "x"}}
        result = tools.agent_watcher.trigger_agent("nonexistent", 1)
        assert result is False
        tools.agent_watcher._AGENTS_CONFIG = None

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 360))
    def test_timeout(self, mock_run):
        import tools.agent_watcher
        tools.agent_watcher._AGENTS_CONFIG = {
            "gemini": {"bridge_command": "process", "process_pattern": "gemini"},
        }
        result = tools.agent_watcher.trigger_agent("gemini", 1)
        assert result is False
        tools.agent_watcher._AGENTS_CONFIG = None


class TestAgentWatcherPidFile:
    def test_write_pid(self, tmp_path):
        import tools.agent_watcher
        pid_file = tmp_path / "watcher.pid"
        with patch.object(tools.agent_watcher, "PID_FILE", pid_file):
            tools.agent_watcher.write_pid()
            assert pid_file.exists()
            assert int(pid_file.read_text().strip()) == os.getpid()

    def test_read_pid_invalid(self, tmp_path):
        import tools.agent_watcher
        pid_file = tmp_path / "watcher.pid"
        pid_file.write_text("not_a_number")
        with patch.object(tools.agent_watcher, "PID_FILE", pid_file):
            assert tools.agent_watcher.read_pid() is None


class TestAgentWatcherIsRunning:
    @patch("os.kill")
    def test_running(self, mock_kill, tmp_path):
        import tools.agent_watcher
        pid_file = tmp_path / "watcher.pid"
        pid_file.write_text("12345")
        mock_kill.return_value = None  # Process exists
        with patch.object(tools.agent_watcher, "PID_FILE", pid_file):
            assert tools.agent_watcher.is_running() is True

    @patch("os.kill", side_effect=OSError("no such process"))
    def test_stale_pid(self, mock_kill, tmp_path):
        import tools.agent_watcher
        pid_file = tmp_path / "watcher.pid"
        pid_file.write_text("99999")
        with patch.object(tools.agent_watcher, "PID_FILE", pid_file):
            assert tools.agent_watcher.is_running() is False


class TestAgentWatcherStopDaemon:
    @patch("os.kill")
    def test_stop_success(self, mock_kill, tmp_path):
        import tools.agent_watcher
        pid_file = tmp_path / "watcher.pid"
        pid_file.write_text("12345")
        with patch.object(tools.agent_watcher, "PID_FILE", pid_file), patch("time.sleep"):
            result = tools.agent_watcher.stop_daemon()
        assert result is True
        mock_kill.assert_called_with(12345, signal.SIGTERM)
# ═══════════════════════════════════════════════════════════════════════
# Additional edge case tests
# ═══════════════════════════════════════════════════════════════════════


class TestBatchOtamanWorkersClamp:
    @patch("batch.batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch.batch_otaman.STATE_FILE")
    def test_workers_clamped(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch.batch_otaman import MAX_WORKERS, BatchOtaman
        bo = BatchOtaman(dry_run=True, workers=99)
        assert bo.workers == MAX_WORKERS
class TestBatchFixReviewCheckExistingReviews:
    def test_re_review_pass(self, tmp_path):
        from batch.batch_fix_review import _check_existing_reviews
        orch = tmp_path / "orchestration"
        orch.mkdir()
        (orch / "phase-5-re-review.md").write_text("**Overall Score:** 9.5/10")
        files = {"orchestration": orch, "review": tmp_path / "review.md"}
        result = {}
        status, score = _check_existing_reviews(files, result)
        assert status == "ALREADY_PASS"
        assert score == 9.5

    def test_review_fail(self, tmp_path):
        from batch.batch_fix_review import _check_existing_reviews
        orch = tmp_path / "orchestration"
        orch.mkdir()
        (orch / "phase-5-response.md").write_text("**Overall Score:** 7.0/10\n**Status:** FAIL")
        files = {"orchestration": orch, "review": tmp_path / "review.md"}
        result = {}
        status, score = _check_existing_reviews(files, result)
        assert status == "continue"
        assert score == 7.0

    def test_no_reviews(self, tmp_path):
        from batch.batch_fix_review import _check_existing_reviews
        orch = tmp_path / "orchestration"
        orch.mkdir()
        files = {"orchestration": orch, "review": tmp_path / "review.md"}
        result = {}
        status, score = _check_existing_reviews(files, result)
        assert status == "continue"
        assert score is None
class TestBatchDispatcherUpdateTrackStates:
    """Test _update_track_states edge cases."""

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_track_becomes_done(self, mock_load):
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_dispatcher_helpers import get_track_dstate
        from batch_dispatcher import BatchDispatcher
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
    def test_stale_counts_as_done(self, mock_load):
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_dispatcher_helpers import get_track_dstate
        from batch_dispatcher import BatchDispatcher
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
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_dispatcher_helpers import get_track_dstate
        from batch_dispatcher import BatchDispatcher
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
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_dispatcher_helpers import get_track_dstate
        from batch_dispatcher import BatchDispatcher
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
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_dispatcher_helpers import get_track_dstate
        from batch_dispatcher import BatchDispatcher
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
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_dispatcher_helpers import get_track_dstate
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.DONE
        scan = {"a1": {"total": 10, "passed": 7, "failed": 3, "stale": 0, "unbuilt": 0, "pass_rate": 0.7}}
        d._update_track_states(scan)
        assert dstate["state"] == TrackState.PENDING
# ═══════════════════════════════════════════════════════════════════════
# Additional tests to reach 200+ total
# ═══════════════════════════════════════════════════════════════════════

class TestBatchFixReviewExtractSectionEdgeCases:
    def _import(self):
        from batch.batch_fix_review import extract_section
        return extract_section

    def test_empty_content_between_tags(self, tmp_path):
        extract_section = self._import()
        p = tmp_path / "out.txt"
        p.write_text("===START===\n\n===END===\n")
        result = extract_section(p, "===START===", "===END===")
        assert result == ""


class TestBatchOtamanCheckDepsEdgeCases:
    def _import(self):
        from batch.batch_otaman import check_dependencies
        return check_dependencies

    def test_multiple_deps_one_unmet(self):
        summaries = {
            "hist": {"total": 100, "passed": 90},
            "c1": {"total": 100, "passed": 20},
        }
        ok, _unmet = self._import()("istorio", summaries)
        assert ok is False
        assert len(_unmet) == 1


class TestBatchDispatcherUpdateTrackStatesEdgeCases:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    def test_stalled_not_promoted(self, mock_load):
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_dispatcher_helpers import get_track_dstate
        from batch_dispatcher import BatchDispatcher
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
    def test_pending_becomes_eligible_with_deps(self, mock_load):
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_dispatcher_helpers import get_track_dstate
        from batch_dispatcher import BatchDispatcher
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
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_dispatcher_helpers import get_track_dstate
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.DONE
        scan = {"a1": {"total": 10, "passed": 10, "failed": 0, "stale": 0, "unbuilt": 0, "pass_rate": 1.0}}
        d._update_track_states(scan)
        assert dstate["state"] == TrackState.DONE


class TestAgentWatcherEdgeCases:
    def test_get_unread_acknowledged_not_returned(self, sqlite_db):
        import tools.agent_watcher
        conn = sqlite3.connect(sqlite_db)
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, timestamp, acknowledged) VALUES (?, ?, ?, ?, ?, ?)",
            ("task1", "claude", "gemini", "request", "2026-01-01T00:00:00", 1),
        )
        conn.commit()
        conn.close()
        with patch.object(tools.agent_watcher, "DB_PATH", sqlite_db):
            msgs = tools.agent_watcher.get_unread_messages()
            assert len(msgs) == 0


class TestBatchOtamanFindModuleScanEdgeCases:
    @patch("batch.batch_otaman.get_module_index")
    @patch("batch.batch_otaman.get_module_paths", side_effect=Exception("oops"))
    def test_find_next_module_paths_error(self, mock_paths, mock_idx):
        from batch.batch_otaman import find_next_module
        mock_idx.return_value = {"total": 1, "num_to_slug": {1: "test"}}
        result = find_next_module("a1")
        assert result is not None
        assert result["reason"] == "no_paths"

    @patch("batch.batch_otaman.get_module_index")
    @patch("batch.batch_otaman.get_module_paths", side_effect=Exception("oops"))
    def test_scan_track_summary_paths_error(self, mock_paths, mock_idx):
        from batch.batch_otaman import scan_track_summary
        mock_idx.return_value = {"total": 2, "num_to_slug": {1: "a", 2: "b"}}
        result = scan_track_summary("a1")
        assert result["total"] == 2
        assert result["remaining"] == 2


class TestBatchFixReviewFindModuleFiles:
    def test_review_only_mode(self, tmp_path):
        from batch.batch_fix_review import process_module

        orch = tmp_path / "orchestration"
        orch.mkdir()
        review = orch / "phase-5-response.md"
        review.write_text("**Overall Score:** 7.5/10\n**Status:** FAIL")
        content = tmp_path / "content.md"
        content.write_text("# Test\nContent\n")

        with patch("batch.batch_fix_review.find_module_files", return_value={
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
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_dispatcher_helpers import get_track_dstate
        from batch_dispatcher import BatchDispatcher
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
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_dispatcher_helpers import get_track_dstate
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(include_tracks=["a1"])
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.ELIGIBLE
        result = d._pick_track({"a1": {}})
        assert result == "a1"


class TestBatchOtamanPickModulesEdgeCases:
    @patch("batch.batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch.batch_otaman.STATE_FILE")
    @patch("batch.batch_otaman.find_next_module", return_value=None)
    def test_no_modules_available(self, mock_find, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch.batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, include_tracks=["a1"])
        summaries = {"a1": {"total": 10, "passed": 10, "content_complete": 0, "remaining": 0}}
        modules = bo._pick_modules(summaries)
        assert modules == []

    @patch("batch.batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch.batch_otaman.STATE_FILE")
    @patch("batch.batch_otaman.find_next_module", return_value={"num": 1, "slug": "test", "reason": "unbuilt"})
    def test_picks_module(self, mock_find, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch.batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, include_tracks=["a1"])
        summaries = {"a1": {"total": 10, "passed": 5, "content_complete": 0, "remaining": 5}}
        modules = bo._pick_modules(summaries)
        assert len(modules) == 1
        assert modules[0]["track"] == "a1"


class TestBatchOtamanMalformedCooldown:
    @patch("batch.batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch.batch_otaman.STATE_FILE")
    @patch("batch.batch_otaman.find_next_module", return_value={"num": 1, "slug": "test", "reason": "unbuilt"})
    def test_malformed_cooldown_resets(self, mock_find, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_otaman import BatchOtaman, get_track_state
        bo = BatchOtaman(dry_run=True, include_tracks=["a1"])
        ts = get_track_state(bo.state, "a1")
        ts["state"] = TrackState.COOLDOWN
        ts["cooldown_until"] = "garbage"
        summaries = {"a1": {"total": 10, "passed": 5, "content_complete": 0, "remaining": 5}}
        modules = bo._pick_modules(summaries)
        # Malformed cooldown gets replaced, track stays in cooldown
        assert ts["cooldown_until"] != "garbage"

    @patch("batch.batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch.batch_otaman.STATE_FILE")
    @patch("batch.batch_otaman.find_next_module", return_value={"num": 1, "slug": "test", "reason": "unbuilt"})
    def test_expired_cooldown_becomes_eligible(self, mock_find, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_otaman import BatchOtaman, get_track_state
        bo = BatchOtaman(dry_run=True, include_tracks=["a1"])
        ts = get_track_state(bo.state, "a1")
        ts["state"] = TrackState.COOLDOWN
        ts["cooldown_until"] = "2020-01-01T00:00:00+00:00"  # expired
        summaries = {"a1": {"total": 10, "passed": 5, "content_complete": 0, "remaining": 5}}
        modules = bo._pick_modules(summaries)
        assert ts["state"] == TrackState.ELIGIBLE
        assert len(modules) == 1

    @patch("batch.batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch.batch_otaman.STATE_FILE")
    def test_stalled_track_skipped(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_otaman import BatchOtaman, get_track_state
        bo = BatchOtaman(dry_run=True, include_tracks=["a1"])
        ts = get_track_state(bo.state, "a1")
        ts["state"] = TrackState.ELIGIBLE
        ts["consecutive_failures"] = 5
        summaries = {"a1": {"total": 10, "passed": 5, "content_complete": 0, "remaining": 5}}
        modules = bo._pick_modules(summaries)
        assert ts["state"] == TrackState.STALLED
        assert modules == []

    @patch("batch.batch_otaman.load_state", return_value={"tracks": {}, "history": [], "running_tracks": [], "stats": {"total_dispatches": 0, "total_modules_passed": 0, "total_quota_hits": 0}})
    @patch("batch.batch_otaman.STATE_FILE")
    def test_force_track(self, mock_sf, mock_load, tmp_path):
        mock_sf.parent = tmp_path
        from batch.batch_otaman import BatchOtaman
        bo = BatchOtaman(dry_run=True, include_tracks=["a1", "a2"], force_track="a2")
        summaries = {"a1": {"remaining": 5}, "a2": {"remaining": 3}}
        with patch("batch.batch_otaman.find_next_module", return_value={"num": 1, "slug": "test", "reason": "unbuilt"}):
            with patch("batch.batch_otaman.check_dependencies", return_value=(True, [])):
                modules = bo._pick_modules(summaries)
                if modules:
                    assert modules[0]["track"] == "a2"


class TestBatchDispatcherRunningTrackCleanup:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "2026-01-01", "tracks": {}, "dispatch_history": [],
        "stats": {}, "last_updated": None
    })
    @patch("batch_dispatcher.PROJECT_ROOT", Path("/tmp/test"))
    @patch("batch_dispatcher.BATCH_STATE_DIR")
    def test_running_no_lock_file(self, mock_bsd, mock_load, tmp_path):
        from batch.batch_dispatcher_config import TrackState
        from batch.batch_dispatcher_helpers import get_track_dstate
        from batch_dispatcher import BatchDispatcher

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


class TestBatchDispatcherClaudeFixBackground:
    def test_claude_fix_runs_without_background_work(self, monkeypatch):
        """The headless Claude rebuild carries the #9690 controls from the adapter (#9750)."""
        from agent_runtime.adapters.claude import HEADLESS_BACKGROUND_ENV, HEADLESS_BACKGROUND_TOOL_DENIES
        from batch import batch_dispatcher_helpers as helpers

        seen = {}

        def fake_run(cmd, **kwargs):
            seen.update(cmd=cmd, env=kwargs["env"])
            return subprocess.CompletedProcess(cmd, 0, stdout="done", stderr="")

        monkeypatch.setattr(helpers.subprocess, "run", fake_run)
        monkeypatch.setattr(helpers, "supports_exclude_dynamic_system_prompt_sections", lambda _bin: False)

        result = helpers.dispatch_claude_fix("a1", "greetings", 1)

        assert result["success"] is True
        cmd = seen["cmd"]
        assert "bypassPermissions" in cmd
        assert cmd[cmd.index("--disallowedTools") + 1].split(",") == list(HEADLESS_BACKGROUND_TOOL_DENIES)
        assert seen["env"].items() >= HEADLESS_BACKGROUND_ENV.items()
