"""
Integration tests for the batch runner fix loop (process_module_fix).

TD-3: Tests exercise the full audit → diagnose → fix → re-audit flow
using mocks for external dependencies (audit runner, Gemini calls).
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.batch_gemini_runner import BatchRunner, MAX_FIX_ITERATIONS


def _make_status(gate_statuses, overall_status="fail", blocking_issues=None):
    """Build a synthetic status JSON."""
    gates = {}
    for name, status in gate_statuses.items():
        gates[name] = {
            "status": status,
            "violations": 1 if status == "fail" else 0,
            "message": "",
        }
    return {
        "overall": {
            "status": overall_status,
            "blocking_issues": blocking_issues or [],
        },
        "gates": gates,
    }


STATUS_ALL_PASS = _make_status(
    {"meta": "pass", "lesson": "pass", "activities": "pass",
     "vocabulary": "pass", "naturalness": "pass", "review": "pass"},
    overall_status="pass",
)

STATUS_LESSON_FAIL = _make_status(
    {"meta": "pass", "lesson": "fail", "activities": "pass",
     "vocabulary": "pass", "naturalness": "pass", "review": "skipped"},
)

STATUS_ACTIVITIES_FAIL = _make_status(
    {"meta": "pass", "lesson": "pass", "activities": "fail",
     "vocabulary": "pass", "naturalness": "pass", "review": "skipped"},
)


class _FixLoopTestBase:
    """Shared setup for fix loop integration tests."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.track_dir = Path(self.tmpdir) / "c1-bio"
        self.track_dir.mkdir(parents=True)

        for subdir in ("audit", "review", "status", "meta", "activities",
                        "vocabulary", "research"):
            (self.track_dir / subdir).mkdir()
        orch = self.track_dir / "orchestration" / "test-slug"
        orch.mkdir(parents=True)

        # Content file (>200 words to pass precondition)
        self.md_path = self.track_dir / "test-slug.md"
        self.md_path.write_text("# Test Module\n" + "word " * 500)

        # Meta file
        (self.track_dir / "meta" / "test-slug.yaml").write_text(
            "level: C1-BIO\nword_target: 3000\n"
        )

        # Plan file
        plans_dir = Path(self.tmpdir) / "plans" / "c1-bio"
        plans_dir.mkdir(parents=True)
        (plans_dir / "test-slug.yaml").write_text("title: Test\nword_target: 3000\n")

        # Status file (written by _read_status_json)
        self.status_file = self.track_dir / "status" / "test-slug.json"

        # Failures dir
        self.failures_dir = Path(self.tmpdir) / "batch_state" / "failures" / "c1-bio"

        # Build paths dict matching get_module_paths() output
        self.paths = {
            "md": self.md_path,
            "meta": self.track_dir / "meta" / "test-slug.yaml",
            "plan": plans_dir / "test-slug.yaml",
            "activities": self.track_dir / "activities" / "test-slug.yaml",
            "vocabulary": self.track_dir / "vocabulary" / "test-slug.yaml",
            "research": self.track_dir / "research" / "test-slug-research.md",
            "orchestration": orch,
        }

        # Create runner with mocked init
        with patch.object(BatchRunner, '__init__', lambda self, *a, **kw: None):
            self.runner = BatchRunner.__new__(BatchRunner)
            self.runner.track = "c1-bio"
            self.runner.config = {"type": "seminar", "templates": {}, "phases": []}
            self.runner.state = {"modules": {"test-slug": {}}}

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def _write_status(self, status_data):
        """Write status JSON so _read_status_json can find it."""
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.status_file, "w") as f:
            json.dump(status_data, f)


class TestFixLoopHappyPath(_FixLoopTestBase):
    """Fix loop: audit fails once, fix applied, second audit passes."""

    @patch.object(BatchRunner, '_save_failure')
    @patch.object(BatchRunner, '_save_state', return_value=None)
    def test_fix_loop_succeeds_after_one_fix(self, mock_save_state, mock_save_failure):
        """Loop should: audit(fail) → generate_fix_plan → audit(fail) → fix_content → audit(pass)."""
        audit_calls = [0]

        def mock_run_audit(md_path):
            audit_calls[0] += 1
            if audit_calls[0] <= 2:
                # First two audits fail (lesson gate)
                self._write_status(STATUS_LESSON_FAIL)
                return {"passed": False, "errors": "lesson gate fail"}
            else:
                # Third audit passes
                self._write_status(STATUS_ALL_PASS)
                return {"passed": True, "errors": ""}

        def mock_run_phase(phase, slug, paths, error_msg=None):
            if phase == 5:
                # Generate review with Fix Plan
                review_dir = paths["md"].parent / "review"
                review_dir.mkdir(parents=True, exist_ok=True)
                review_file = review_dir / "test-slug-review.md"
                review_file.write_text("# Review\n\n## Fix Plan to Reach 9/10\n\n1. Expand section 3\n")
            return True

        with patch.object(BatchRunner, '_run_audit', side_effect=mock_run_audit), \
             patch.object(BatchRunner, 'run_phase', side_effect=mock_run_phase), \
             patch('scripts.batch_gemini_runner.get_module_paths', return_value=self.paths):

            result = self.runner.process_module_fix("test-slug")

        assert result is True
        assert audit_calls[0] == 3  # fail, fail (after fix plan gen), pass (after content fix)

        # Verify fix-state was saved
        fix_state_file = self.paths["orchestration"] / "fix-state.json"
        assert fix_state_file.exists()
        fix_state = json.loads(fix_state_file.read_text())
        assert fix_state["result"] == "success"

    @patch.object(BatchRunner, '_save_failure')
    @patch.object(BatchRunner, '_save_state', return_value=None)
    def test_fix_loop_done_on_first_audit(self, mock_save_state, mock_save_failure):
        """If first audit passes, loop returns True immediately."""

        def mock_run_audit(md_path):
            self._write_status(STATUS_ALL_PASS)
            return {"passed": True, "errors": ""}

        with patch.object(BatchRunner, '_run_audit', side_effect=mock_run_audit), \
             patch('scripts.batch_gemini_runner.get_module_paths', return_value=self.paths):

            result = self.runner.process_module_fix("test-slug")

        assert result is True


class TestFixLoopStallBreak(_FixLoopTestBase):
    """Fix loop detects stall when same gates fail repeatedly."""

    @patch.object(BatchRunner, '_save_failure')
    @patch.object(BatchRunner, '_save_state', return_value=None)
    def test_stall_breaks_at_iteration_3(self, mock_save_state, mock_save_failure):
        """Same gate failing 3+ times in a row should trigger stall break."""
        audit_call_count = [0]
        phase_calls = []

        def mock_run_audit(md_path):
            audit_call_count[0] += 1
            # Always fail with lesson gate
            self._write_status(STATUS_LESSON_FAIL)
            return {"passed": False, "errors": "lesson gate fail"}

        def mock_run_phase(phase, slug, paths, error_msg=None):
            phase_calls.append(phase)
            if phase == 5:
                # Generate review with Fix Plan
                review_dir = paths["md"].parent / "review"
                review_dir.mkdir(parents=True, exist_ok=True)
                review_file = review_dir / "test-slug-review.md"
                review_file.write_text("# Review\n\n## Fix Plan to Reach 9/10\n\n1. Fix X\n")
            return True

        with patch.object(BatchRunner, '_run_audit', side_effect=mock_run_audit), \
             patch.object(BatchRunner, 'run_phase', side_effect=mock_run_phase), \
             patch('scripts.batch_gemini_runner.get_module_paths', return_value=self.paths):

            result = self.runner.process_module_fix("test-slug")

        assert result is False

        # Verify fix-state records stall
        fix_state_file = self.paths["orchestration"] / "fix-state.json"
        assert fix_state_file.exists()
        fix_state = json.loads(fix_state_file.read_text())
        stall_iterations = [
            it for it in fix_state["iterations"]
            if it.get("result") == "stall_detected"
        ]
        assert len(stall_iterations) >= 1, "Should have at least one stall_detected iteration"


class TestFixLoopActivitiesRouting(_FixLoopTestBase):
    """Fix loop routes to fix_activities when only activities/vocabulary fail."""

    @patch.object(BatchRunner, '_save_failure')
    @patch.object(BatchRunner, '_save_state', return_value=None)
    def test_activities_only_failure_routes_to_fix_activities(self, mock_save_state, mock_save_failure):
        """When only activities gate fails, should route to fix_activities phase."""
        audit_call_count = [0]
        phase_calls = []

        def mock_run_audit(md_path):
            audit_call_count[0] += 1
            if audit_call_count[0] == 1:
                # First audit: activities fail
                self._write_status(STATUS_ACTIVITIES_FAIL)
                return {"passed": False, "errors": "activities gate fail"}
            else:
                # After fix: all pass
                self._write_status(STATUS_ALL_PASS)
                return {"passed": True, "errors": ""}

        def mock_run_phase(phase, slug, paths, error_msg=None):
            phase_calls.append(phase)
            return True

        # Mock _check_content_gates_pass to return True after activities fix
        def mock_check_gates(paths, slug):
            return True

        with patch.object(BatchRunner, '_run_audit', side_effect=mock_run_audit), \
             patch.object(BatchRunner, 'run_phase', side_effect=mock_run_phase), \
             patch.object(BatchRunner, '_check_content_gates_pass', side_effect=mock_check_gates), \
             patch('scripts.batch_gemini_runner.get_module_paths', return_value=self.paths):

            result = self.runner.process_module_fix("test-slug")

        assert result is True
        assert "fix-activities" in phase_calls, f"Expected fix-activities phase, got: {phase_calls}"


class TestFixLoopExhausted(_FixLoopTestBase):
    """Fix loop exhausts MAX_FIX_ITERATIONS without converging."""

    @patch.object(BatchRunner, '_save_failure')
    @patch.object(BatchRunner, '_save_state', return_value=None)
    def test_exhausted_iterations_returns_false(self, mock_save_state, mock_save_failure):
        """Loop should return False after MAX_FIX_ITERATIONS with no convergence."""
        audit_call_count = [0]
        # Alternate between different failing gates to avoid stall detection
        gate_sequence = [
            _make_status({"meta": "pass", "lesson": "fail", "activities": "pass",
                          "vocabulary": "pass", "naturalness": "pass", "review": "skipped"}),
            _make_status({"meta": "pass", "lesson": "pass", "activities": "fail",
                          "vocabulary": "pass", "naturalness": "pass", "review": "skipped"}),
            _make_status({"meta": "pass", "lesson": "fail", "activities": "pass",
                          "vocabulary": "fail", "naturalness": "pass", "review": "skipped"}),
            _make_status({"meta": "pass", "lesson": "pass", "activities": "fail",
                          "vocabulary": "fail", "naturalness": "pass", "review": "skipped"}),
            _make_status({"meta": "pass", "lesson": "fail", "activities": "pass",
                          "vocabulary": "pass", "naturalness": "fail", "review": "skipped"}),
        ]

        def mock_run_audit(md_path):
            audit_call_count[0] += 1
            idx = (audit_call_count[0] - 1) % len(gate_sequence)
            self._write_status(gate_sequence[idx])
            return {"passed": False, "errors": "some gate fail"}

        def mock_run_phase(phase, slug, paths, error_msg=None):
            if phase == 5:
                review_dir = paths["md"].parent / "review"
                review_dir.mkdir(parents=True, exist_ok=True)
                review_file = review_dir / "test-slug-review.md"
                review_file.write_text("# Review\n\n## Fix Plan to Reach 9/10\n\n1. Fix stuff\n")
            return True

        def mock_check_gates(paths, slug):
            return False

        with patch.object(BatchRunner, '_run_audit', side_effect=mock_run_audit), \
             patch.object(BatchRunner, 'run_phase', side_effect=mock_run_phase), \
             patch.object(BatchRunner, '_check_content_gates_pass', side_effect=mock_check_gates), \
             patch('scripts.batch_gemini_runner.get_module_paths', return_value=self.paths):

            result = self.runner.process_module_fix("test-slug")

        assert result is False

        # Verify failure was saved
        mock_save_failure.assert_called_once()

        # Verify fix-state records exhaustion
        fix_state_file = self.paths["orchestration"] / "fix-state.json"
        assert fix_state_file.exists()
        fix_state = json.loads(fix_state_file.read_text())
        assert fix_state["result"] == "exhausted"
