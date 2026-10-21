"""
Tests for batch runner fix mode (layers 1-3: no Gemini calls).

Layer 1: Audit review gate in status JSON
Layer 2: Diagnosis logic + auto-mode routing
Layer 3: Fix apply_output safety guards
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit.report import save_status_cache
from scripts.batch_gemini_runner import BatchRunner

# =============================================================================
# Layer 1: Review gate in status JSON
# =============================================================================

class TestReviewGateInStatusJSON:
    """Verify save_status_cache writes review gate correctly."""

    def setup_method(self):
        """Create temp directory structure for status cache."""
        self.tmpdir = tempfile.mkdtemp()
        self.level_dir = Path(self.tmpdir) / "test-level"
        self.level_dir.mkdir()
        self.status_dir = self.level_dir / "status"
        self.status_dir.mkdir()
        # Create a fake md file
        self.md_file = self.level_dir / "test-module.md"
        self.md_file.write_text("# Test\nSome content here.")

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_review_gate_pass(self):
        """Review gate should be 'pass' when no violations."""
        path = save_status_cache(
            str(self.md_file), "test-level", "test-module",
            results={}, has_critical_failure=False,
            critical_failure_reasons=[],
            review_violations=[],
            review_gate_status="pass",
        )
        with open(path) as f:
            data = json.load(f)

        assert "review" in data["gates"]
        assert data["gates"]["review"]["status"] == "pass"
        assert data["gates"]["review"]["violations"] == 0

    def test_review_gate_fail(self):
        """Review gate should be 'fail' with critical violations."""
        violations = [
            {"severity": "critical", "type": "FAKE_REVIEW", "message": "Review is fake"},
        ]
        path = save_status_cache(
            str(self.md_file), "test-level", "test-module",
            results={}, has_critical_failure=True,
            critical_failure_reasons=["Review is fake"],
            review_violations=violations,
            review_gate_status="fail",
        )
        with open(path) as f:
            data = json.load(f)

        assert data["gates"]["review"]["status"] == "fail"
        assert data["gates"]["review"]["violations"] == 1
        assert "fake" in data["gates"]["review"]["message"].lower()


# =============================================================================
# Layer 2: Diagnosis logic + auto-mode routing
# =============================================================================

class TestDiagnoseModule:
    """Test _diagnose_module decision tree."""

    def setup_method(self):
        """Create runner with mocked config and temp dirs."""
        self.tmpdir = tempfile.mkdtemp()
        self.track_dir = Path(self.tmpdir) / "bio"
        self.track_dir.mkdir(parents=True)
        (self.track_dir / "audit").mkdir()
        (self.track_dir / "review").mkdir()
        (self.track_dir / "status").mkdir()
        (self.track_dir / "meta").mkdir()
        (self.track_dir / "orchestration" / "test-slug").mkdir(parents=True)

        # Create fake md file
        self.md_file = self.track_dir / "test-slug.md"
        self.md_file.write_text("# Test\n" + "word " * 500)

        # Create fake meta + plan
        (self.track_dir / "meta" / "test-slug.yaml").write_text("level: BIO\n")

        self.paths = {
            "md": self.md_file,
            "meta": self.track_dir / "meta" / "test-slug.yaml",
            "plan": self.track_dir / "plan.yaml",  # doesn't need to exist for diagnosis
            "activities": self.track_dir / "activities" / "test-slug.yaml",
            "vocabulary": self.track_dir / "vocabulary" / "test-slug.yaml",
            "research": self.track_dir / "research" / "test-slug-research.md",
            "orchestration": self.track_dir / "orchestration" / "test-slug",
        }

        # Create a runner (we only use its methods, not actual batch)
        with patch.object(BatchRunner, '__init__', lambda self, *a, **kw: None):
            self.runner = BatchRunner.__new__(BatchRunner)
            self.runner.track = "bio"
            self.runner.config = {"type": "seminar", "templates": {}, "phases": []}

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def _make_status(self, gate_statuses, overall_status="fail"):
        """Build a synthetic status JSON."""
        gates = {}
        for name, status in gate_statuses.items():
            gates[name] = {"status": status, "violations": 1 if status == "fail" else 0, "message": ""}
        return {
            "overall": {"status": overall_status, "blocking_issues": []},
            "gates": gates,
        }

    def test_done_when_all_pass(self):
        status = self._make_status(
            {"meta": "pass", "lesson": "pass", "activities": "pass",
             "vocabulary": "pass", "naturalness": "pass", "review": "pass"},
            overall_status="pass"
        )
        assert self.runner._diagnose_module(status, self.paths, "test-slug") == "done"

    def test_done_when_only_review_fails(self):
        """Anti-gaming: review gate is ignored in fix mode."""
        status = self._make_status(
            {"meta": "pass", "lesson": "pass", "activities": "pass",
             "vocabulary": "pass", "naturalness": "pass", "review": "fail"},
        )
        assert self.runner._diagnose_module(status, self.paths, "test-slug") == "done"

    def test_fix_content_when_content_fails_and_review_has_fix_plan(self):
        # Create review with Fix Plan
        review_path = self.track_dir / "review" / "test-slug-review.md"
        review_path.write_text("# Review\n\n## Fix Plan to Reach 9/10\n\n1. Fix X\n2. Fix Y\n")

        status = self._make_status(
            {"meta": "pass", "lesson": "fail", "activities": "pass",
             "vocabulary": "pass", "naturalness": "pass", "review": "pass"},
        )
        assert self.runner._diagnose_module(status, self.paths, "test-slug") == "fix_content"

    def test_generate_fix_plan_when_content_fails_and_no_review(self):
        status = self._make_status(
            {"meta": "pass", "lesson": "fail", "activities": "pass",
             "vocabulary": "pass", "naturalness": "pass", "review": "skipped"},
        )
        assert self.runner._diagnose_module(status, self.paths, "test-slug") == "generate_fix_plan"

    def test_generate_fix_plan_when_content_fails_and_review_lacks_fix_plan(self):
        # Create review WITHOUT Fix Plan
        review_path = self.track_dir / "review" / "test-slug-review.md"
        review_path.write_text("# Review\n\nLooks good overall.\n")

        status = self._make_status(
            {"meta": "pass", "lesson": "fail", "activities": "pass",
             "vocabulary": "pass", "naturalness": "pass", "review": "pass"},
        )
        assert self.runner._diagnose_module(status, self.paths, "test-slug") == "generate_fix_plan"


class TestAutoModeRouting:
    """Test _resolve_mode_for_module auto-detection."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.md_path = Path(self.tmpdir) / "test.md"

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def _make_runner(self, mode):
        with patch.object(BatchRunner, '__init__', lambda self, *a, **kw: None):
            runner = BatchRunner.__new__(BatchRunner)
            runner.mode = mode
            return runner

    def test_build_mode_always_builds(self):
        self.md_path.write_text("x" * 1000)
        runner = self._make_runner("build")
        assert runner._resolve_mode_for_module("s", {"md": self.md_path}) == "build"

    def test_auto_mode_builds_when_no_md(self):
        runner = self._make_runner("auto")
        assert runner._resolve_mode_for_module("s", {"md": self.md_path}) == "build"

    def test_auto_mode_builds_when_md_tiny(self):
        self.md_path.write_text("small")
        runner = self._make_runner("auto")
        assert runner._resolve_mode_for_module("s", {"md": self.md_path}) == "build"

    def test_auto_mode_fixes_when_md_exists(self):
        self.md_path.write_text("x" * 600)
        runner = self._make_runner("auto")
        assert runner._resolve_mode_for_module("s", {"md": self.md_path}) == "fix"


# =============================================================================
# Layer 3: Fix apply_output safety guards
# =============================================================================

class TestFixApplyOutput:
    """Test _apply_output for phase='fix' with safety guards."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.track_dir = Path(self.tmpdir) / "bio"
        self.track_dir.mkdir(parents=True)
        (self.track_dir / "activities").mkdir()
        (self.track_dir / "vocabulary").mkdir()
        orch = self.track_dir / "orchestration" / "test-slug"
        orch.mkdir(parents=True)

        self.md_path = self.track_dir / "test-slug.md"
        self.md_path.write_text("# Original content\n" + "word " * 500)

        self.paths = {
            "md": self.md_path,
            "activities": self.track_dir / "activities" / "test-slug.yaml",
            "vocabulary": self.track_dir / "vocabulary" / "test-slug.yaml",
            "orchestration": orch,
        }

        with patch.object(BatchRunner, '__init__', lambda self, *a, **kw: None):
            self.runner = BatchRunner.__new__(BatchRunner)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_content_fix_applied_when_long_enough(self):
        output = (
            "Some preamble\n"
            "===CONTENT_START===\n"
            "# Fixed content\n" + "fixed " * 50 + "\n"
            "===CONTENT_END===\n"
            "===CHANGES_START===\n## Applied Fixes\n1. Fixed stuff\n===CHANGES_END===\n"
        )
        self.runner._apply_output("fix", output, self.paths)
        content = self.md_path.read_text()
        assert "Fixed content" in content
        assert "Original content" not in content

    def test_content_fix_rejected_when_too_short(self):
        original = self.md_path.read_text()
        output = (
            "===CONTENT_START===\nshort\n===CONTENT_END===\n"
            "===CHANGES_START===\n## Applied\n===CHANGES_END===\n"
        )
        self.runner._apply_output("fix", output, self.paths)
        assert self.md_path.read_text() == original  # Not overwritten

    def test_activities_fix_applied(self):
        activities_yaml = "- type: quiz\n  title: Test\n  questions:\n    - q: What?\n      a: This\n"
        output = (
            f"===ACTIVITIES_START===\n{activities_yaml}\n===ACTIVITIES_END===\n"
            "===CHANGES_START===\n## Applied\n===CHANGES_END===\n"
        )
        self.runner._apply_output("fix", output, self.paths)
        assert self.paths["activities"].exists()
        data = yaml.safe_load(self.paths["activities"].read_text())
        assert isinstance(data, list)
        assert data[0]["type"] == "quiz"

    def test_no_content_block_leaves_file_unchanged(self):
        """If fix output has no CONTENT block, md should not be touched."""
        original = self.md_path.read_text()
        output = (
            "===CHANGES_START===\n## No content changes\n===CHANGES_END===\n"
        )
        self.runner._apply_output("fix", output, self.paths)
        assert self.md_path.read_text() == original


# =============================================================================
# Layer 2b: Fix template registration
# =============================================================================


# =============================================================================
# Layer 4: Helper functions (schema filtering, activity examples, stall detection)
# =============================================================================


class TestDiagnoseModuleActivitiesRouting:
    """Test _diagnose_module routes to fix_activities when only activities/vocabulary fail."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.track_dir = Path(self.tmpdir) / "bio"
        self.track_dir.mkdir(parents=True)
        (self.track_dir / "audit").mkdir()
        (self.track_dir / "review").mkdir()
        (self.track_dir / "status").mkdir()
        (self.track_dir / "meta").mkdir()
        (self.track_dir / "orchestration" / "test-slug").mkdir(parents=True)

        self.md_file = self.track_dir / "test-slug.md"
        self.md_file.write_text("# Test\n" + "word " * 500)
        (self.track_dir / "meta" / "test-slug.yaml").write_text("level: BIO\n")

        self.paths = {
            "md": self.md_file,
            "meta": self.track_dir / "meta" / "test-slug.yaml",
            "plan": self.track_dir / "plan.yaml",
            "activities": self.track_dir / "activities" / "test-slug.yaml",
            "vocabulary": self.track_dir / "vocabulary" / "test-slug.yaml",
            "research": self.track_dir / "research" / "test-slug-research.md",
            "orchestration": self.track_dir / "orchestration" / "test-slug",
        }

        with patch.object(BatchRunner, '__init__', lambda self, *a, **kw: None):
            self.runner = BatchRunner.__new__(BatchRunner)
            self.runner.track = "bio"
            self.runner.config = {"type": "seminar", "templates": {}, "phases": []}

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def _make_status(self, gate_statuses, overall_status="fail", blocking_issues=None):
        gates = {}
        for name, status in gate_statuses.items():
            gates[name] = {"status": status, "violations": 1 if status == "fail" else 0, "message": ""}
        return {
            "overall": {"status": overall_status, "blocking_issues": blocking_issues or []},
            "gates": gates,
        }

    def test_fix_activities_when_only_activities_fail(self):
        status = self._make_status(
            {"meta": "pass", "lesson": "pass", "activities": "fail",
             "vocabulary": "pass", "naturalness": "pass"},
        )
        assert self.runner._diagnose_module(status, self.paths, "test-slug") == "fix_activities"

    def test_content_priority_over_activities(self):
        """When both content and activities fail, content gets priority."""
        status = self._make_status(
            {"meta": "pass", "lesson": "fail", "activities": "fail",
             "vocabulary": "pass", "naturalness": "pass"},
        )
        # Content failed + no review → generate_fix_plan
        assert self.runner._diagnose_module(status, self.paths, "test-slug") == "generate_fix_plan"

    def test_blocking_issues_trigger_content_fix(self):
        """Blocking issues (outline compliance) should route to content fix."""
        status = self._make_status(
            {"meta": "pass", "lesson": "pass", "activities": "pass",
             "vocabulary": "pass", "naturalness": "pass"},
            blocking_issues=["Outline compliance: missing 3 subsections"],
        )
        assert self.runner._diagnose_module(status, self.paths, "test-slug") == "generate_fix_plan"

    def test_review_blocking_issues_are_ignored(self):
        """Blocking issues about reviews should be filtered out (anti-gaming)."""
        status = self._make_status(
            {"meta": "pass", "lesson": "pass", "activities": "pass",
             "vocabulary": "pass", "naturalness": "pass"},
            blocking_issues=["Review validation: GAMING_LANGUAGE_DETECTED"],
        )
        assert self.runner._diagnose_module(status, self.paths, "test-slug") == "done"


# =============================================================================
# TD-2: Schema filter verification (heuristic header matching)
# =============================================================================

class TestSchemaFilterVerification:
    """Verify _filter_schema_for_track heuristic stays in sync with actual schema file.

    TD-2: The filter uses header matching. If ACTIVITY-YAML-REFERENCE.md changes
    header format, the filter breaks silently. These tests catch that.
    """

    def test_filter_produces_nonempty_for_seminar_priority_types(self):
        """_filter_schema_for_track must return non-empty output for each seminar track."""
        from scripts.audit.config import LEVEL_CONFIG
        from scripts.batch_gemini_runner import _filter_schema_for_track

        schema_path = Path(__file__).parent.parent / "docs" / "ACTIVITY-YAML-REFERENCE.md"
        schema_content = schema_path.read_text()

        seminar_configs = {
            'history': LEVEL_CONFIG.get('history', {}),
            'biography': LEVEL_CONFIG.get('biography', {}),
            'LIT': LEVEL_CONFIG.get('LIT', {}),
            'OES': LEVEL_CONFIG.get('OES', {}),
            'RUTH': LEVEL_CONFIG.get('RUTH', {}),
        }

        for config_key, config in seminar_configs.items():
            priority = config.get('priority_types', set())
            if not priority:
                continue
            result = _filter_schema_for_track(schema_content, priority)
            assert result.strip(), (
                f"_filter_schema_for_track returned empty for {config_key} "
                f"with priority_types={priority}"
            )
