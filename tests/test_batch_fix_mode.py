"""
Tests for batch runner fix mode (layers 1-3: no Gemini calls).

Layer 1: Audit review gate in status JSON
Layer 2: Diagnosis logic + auto-mode routing
Layer 3: Fix apply_output safety guards
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.batch_gemini_runner import BatchRunner
from scripts.batch_gemini_config import get_module_paths, PROJECT_ROOT
from scripts.audit.report import save_status_cache


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

    def test_review_gate_skipped(self):
        """Review gate should be 'skipped' when content gates fail."""
        path = save_status_cache(
            str(self.md_file), "test-level", "test-module",
            results={}, has_critical_failure=True,
            critical_failure_reasons=["Word count too low"],
            review_violations=[],
            review_gate_status="skipped",
        )
        with open(path) as f:
            data = json.load(f)

        assert data["gates"]["review"]["status"] == "skipped"
        assert data["gates"]["review"]["violations"] == 0

    def test_review_gate_defaults(self):
        """Review gate should default to skipped when params omitted."""
        path = save_status_cache(
            str(self.md_file), "test-level", "test-module",
            results={}, has_critical_failure=False,
            critical_failure_reasons=[],
        )
        with open(path) as f:
            data = json.load(f)

        assert data["gates"]["review"]["status"] == "skipped"


# =============================================================================
# Layer 2: Diagnosis logic + auto-mode routing
# =============================================================================

class TestDiagnoseModule:
    """Test _diagnose_module decision tree."""

    def setup_method(self):
        """Create runner with mocked config and temp dirs."""
        self.tmpdir = tempfile.mkdtemp()
        self.track_dir = Path(self.tmpdir) / "c1-bio"
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
        (self.track_dir / "meta" / "test-slug.yaml").write_text("level: C1-BIO\n")

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
            self.runner.track = "c1-bio"
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

    def test_done_when_review_skipped(self):
        """Anti-gaming: review gate is ignored in fix mode."""
        status = self._make_status(
            {"meta": "pass", "lesson": "pass", "activities": "pass",
             "vocabulary": "pass", "naturalness": "pass", "review": "skipped"},
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

    def test_fix_mode_always_fixes(self):
        runner = self._make_runner("fix")
        assert runner._resolve_mode_for_module("s", {"md": self.md_path}) == "fix"

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
        self.track_dir = Path(self.tmpdir) / "c1-bio"
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

    def test_activities_fix_rejected_when_too_short(self):
        output = (
            "===ACTIVITIES_START===\nhi\n===ACTIVITIES_END===\n"
            "===CHANGES_START===\n## Applied\n===CHANGES_END===\n"
        )
        self.runner._apply_output("fix", output, self.paths)
        assert not self.paths["activities"].exists()

    def test_changes_report_saved(self):
        output = (
            "===CONTENT_START===\n" + "x " * 100 + "\n===CONTENT_END===\n"
            "===CHANGES_START===\n## Applied Fixes\n1. Fixed line 42\n===CHANGES_END===\n"
        )
        self.runner._apply_output("fix", output, self.paths)
        changes_file = self.paths["orchestration"] / "fix-changes.md"
        assert changes_file.exists()
        assert "Fixed line 42" in changes_file.read_text()

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

class TestFixTemplateRegistration:
    """Verify fix template is registered in all track configs."""

    def test_all_known_tracks_have_fix_template(self):
        from scripts.batch_gemini_config import get_track_config
        for track in ["c1-bio", "b2-hist", "c1-hist", "lit", "a1", "a2"]:
            config = get_track_config(track)
            assert "fix" in config["templates"], f"{track} missing fix template"

    def test_default_config_has_fix_template(self):
        from scripts.batch_gemini_config import get_track_config
        config = get_track_config("some-unknown-track")
        assert "fix" in config["templates"]

    def test_fix_template_file_exists(self):
        from scripts.batch_gemini_config import get_track_config
        config = get_track_config("c1-bio")
        assert config["templates"]["fix"].exists()

    def test_oes_and_ruth_have_seminar_type(self):
        """OES and RUTH must be seminar type to get correct activity examples."""
        from scripts.batch_gemini_config import get_track_config
        for track in ["oes", "ruth"]:
            config = get_track_config(track)
            assert config["type"] == "seminar", f"{track} should be seminar type"

    def test_all_seminar_tracks_have_fix_content_template(self):
        """All seminar tracks need fix-content and fix-activities templates."""
        from scripts.batch_gemini_config import get_track_config, SEMINAR_TRACKS
        for track in SEMINAR_TRACKS:
            config = get_track_config(track)
            assert "fix-content" in config["templates"], f"{track} missing fix-content template"
            assert "fix-activities" in config["templates"], f"{track} missing fix-activities template"


# =============================================================================
# Layer 4: Helper functions (schema filtering, activity examples, stall detection)
# =============================================================================

class TestFilterSchemaForTrack:
    """Test _filter_schema_for_track behavior."""

    def test_empty_allowed_types_returns_full_schema(self):
        """When allowed_types is empty (core tracks), return full schema unchanged."""
        from scripts.batch_gemini_runner import _filter_schema_for_track
        schema = "### quiz (8+ items)\nQuiz content\n### reading\nReading content\n"
        result = _filter_schema_for_track(schema, set())
        assert result == schema

    def test_none_allowed_types_returns_full_schema(self):
        """When allowed_types is None-ish, return full schema unchanged."""
        from scripts.batch_gemini_runner import _filter_schema_for_track
        schema = "### quiz\nContent\n"
        result = _filter_schema_for_track(schema, None)
        assert result == schema

    def test_empty_schema_returns_empty(self):
        """Empty schema input returns empty string."""
        from scripts.batch_gemini_runner import _filter_schema_for_track
        result = _filter_schema_for_track("", {"reading", "essay-response"})
        assert result == ""

    def test_filters_disallowed_types(self):
        """Should remove sections for types not in allowed_types."""
        from scripts.batch_gemini_runner import _filter_schema_for_track
        schema = (
            "# Activity Reference\n"
            "General intro text\n"
            "### quiz (8+ items)\n"
            "Quiz description and examples\n"
            "More quiz details\n"
            "### reading\n"
            "Reading description\n"
            "### fill-in\n"
            "Fill-in description\n"
        )
        result = _filter_schema_for_track(schema, {"reading"})
        assert "reading" in result.lower()
        assert "Reading description" in result
        assert "Quiz description" not in result
        assert "Fill-in description" not in result

    def test_keeps_allowed_types(self):
        """Should keep sections for types in allowed_types."""
        from scripts.batch_gemini_runner import _filter_schema_for_track
        schema = (
            "### reading\n"
            "Reading content here\n"
            "### essay-response\n"
            "Essay content here\n"
            "### quiz\n"
            "Quiz content here\n"
        )
        result = _filter_schema_for_track(schema, {"reading", "essay-response"})
        assert "Reading content here" in result
        assert "Essay content here" in result
        assert "Quiz content here" not in result

    def test_preserves_non_type_headers(self):
        """Headers that don't match any type should be preserved."""
        from scripts.batch_gemini_runner import _filter_schema_for_track
        schema = (
            "## Activity Type Reference\n"
            "Overview text\n"
            "### reading\n"
            "Reading content\n"
            "### quiz\n"
            "Quiz content\n"
            "## General Notes\n"
            "Notes text\n"
        )
        result = _filter_schema_for_track(schema, {"reading"})
        assert "Activity Type Reference" in result
        assert "Overview text" in result
        assert "Reading content" in result
        assert "General Notes" in result
        assert "Notes text" in result
        assert "Quiz content" not in result


class TestActivityExamples:
    """Test _get_seminar_activity_examples and _get_core_activity_examples."""

    def test_seminar_examples_contain_seminar_types(self):
        """Seminar examples should include reading, critical-analysis, essay-response."""
        from scripts.batch_gemini_runner import _get_seminar_activity_examples
        result = _get_seminar_activity_examples("c1-bio")
        assert "type: reading" in result
        assert "type: critical-analysis" in result
        assert "type: essay-response" in result
        assert "type: comparative-study" in result

    def test_seminar_examples_exclude_core_types(self):
        """Seminar examples should NOT include quiz or fill-in."""
        from scripts.batch_gemini_runner import _get_seminar_activity_examples
        result = _get_seminar_activity_examples("c1-bio")
        assert "type: quiz" not in result
        assert "type: fill-in" not in result

    def test_core_examples_contain_core_types(self):
        """Core examples should include quiz, fill-in, match-up, mark-the-words."""
        from scripts.batch_gemini_runner import _get_core_activity_examples
        result = _get_core_activity_examples()
        assert "type: quiz" in result
        assert "type: fill-in" in result
        assert "type: match-up" in result
        assert "type: mark-the-words" in result

    def test_core_examples_exclude_seminar_types(self):
        """Core examples should NOT include essay-response or critical-analysis."""
        from scripts.batch_gemini_runner import _get_core_activity_examples
        result = _get_core_activity_examples()
        assert "type: essay-response" not in result
        assert "type: critical-analysis" not in result

    def test_seminar_examples_have_delimiters(self):
        """Activity examples must include the standard delimiters."""
        from scripts.batch_gemini_runner import _get_seminar_activity_examples
        result = _get_seminar_activity_examples("b2-hist")
        assert "===ACTIVITIES_START===" in result
        assert "===ACTIVITIES_END===" in result
        assert "===VOCABULARY_START===" in result
        assert "===VOCABULARY_END===" in result

    def test_core_examples_have_delimiters(self):
        """Core activity examples must include the standard delimiters."""
        from scripts.batch_gemini_runner import _get_core_activity_examples
        result = _get_core_activity_examples()
        assert "===ACTIVITIES_START===" in result
        assert "===ACTIVITIES_END===" in result


class TestStallDetection:
    """Test the stall detection logic in process_module_fix."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.track_dir = Path(self.tmpdir) / "c1-bio"
        self.track_dir.mkdir(parents=True)
        for subdir in ("audit", "review", "status", "meta", "activities",
                       "vocabulary", "research"):
            (self.track_dir / subdir).mkdir()
        orch = self.track_dir / "orchestration" / "test-slug"
        orch.mkdir(parents=True)

        self.md_path = self.track_dir / "test-slug.md"
        self.md_path.write_text("# Test Module\n" + "word " * 500)

        (self.track_dir / "meta" / "test-slug.yaml").write_text(
            "level: C1-BIO\nword_target: 3000\n"
        )

        # Plan file is required by process_module_fix
        plans_dir = Path(self.tmpdir) / "plans" / "c1-bio"
        plans_dir.mkdir(parents=True)
        (plans_dir / "test-slug.yaml").write_text("title: Test\nword_target: 3000\n")

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_stall_count_increments_on_same_gates(self):
        """Stall counter should increment when same gates fail repeatedly."""
        # Test the stall logic directly (extracted from process_module_fix)
        previous_failing_gates = ["lesson"]
        stall_count = 0

        # Iteration 1: lesson fails
        current_failing = ["lesson"]
        if current_failing == previous_failing_gates and current_failing:
            stall_count += 1
        else:
            stall_count = 0
        previous_failing_gates = current_failing
        assert stall_count == 1

        # Iteration 2: same gate fails
        current_failing = ["lesson"]
        if current_failing == previous_failing_gates and current_failing:
            stall_count += 1
        else:
            stall_count = 0
        previous_failing_gates = current_failing
        assert stall_count == 2

        # Iteration 3: stall threshold reached
        current_failing = ["lesson"]
        if current_failing == previous_failing_gates and current_failing:
            stall_count += 1
        else:
            stall_count = 0
        assert stall_count >= 3  # Would trigger break

    def test_stall_count_resets_on_different_gates(self):
        """Stall counter should reset when different gates fail."""
        previous_failing_gates = ["lesson"]
        stall_count = 2  # Almost stalled

        # Different gate fails — should reset
        current_failing = ["activities"]
        if current_failing == previous_failing_gates and current_failing:
            stall_count += 1
        else:
            stall_count = 0
        assert stall_count == 0

    def test_stall_count_resets_on_empty_gates(self):
        """Stall counter should not increment when no gates fail."""
        previous_failing_gates = ["lesson"]
        stall_count = 2

        current_failing = []
        if current_failing == previous_failing_gates and current_failing:
            stall_count += 1
        else:
            stall_count = 0
        assert stall_count == 0

    def test_stall_count_handles_multiple_gates(self):
        """Stall detection works with multiple simultaneous gate failures."""
        previous_failing_gates = sorted(["activities", "lesson"])
        stall_count = 0

        # Same two gates fail again
        current_failing = sorted(["activities", "lesson"])
        if current_failing == previous_failing_gates and current_failing:
            stall_count += 1
        else:
            stall_count = 0
        assert stall_count == 1

        # One gate changes — not stalled
        current_failing = sorted(["activities", "vocabulary"])
        if current_failing == previous_failing_gates and current_failing:
            stall_count += 1
        else:
            stall_count = 0
        previous_failing_gates = current_failing
        assert stall_count == 0


class TestDiagnoseModuleActivitiesRouting:
    """Test _diagnose_module routes to fix_activities when only activities/vocabulary fail."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.track_dir = Path(self.tmpdir) / "c1-bio"
        self.track_dir.mkdir(parents=True)
        (self.track_dir / "audit").mkdir()
        (self.track_dir / "review").mkdir()
        (self.track_dir / "status").mkdir()
        (self.track_dir / "meta").mkdir()
        (self.track_dir / "orchestration" / "test-slug").mkdir(parents=True)

        self.md_file = self.track_dir / "test-slug.md"
        self.md_file.write_text("# Test\n" + "word " * 500)
        (self.track_dir / "meta" / "test-slug.yaml").write_text("level: C1-BIO\n")

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
            self.runner.track = "c1-bio"
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

    def test_fix_activities_when_only_vocabulary_fails(self):
        status = self._make_status(
            {"meta": "pass", "lesson": "pass", "activities": "pass",
             "vocabulary": "fail", "naturalness": "pass"},
        )
        assert self.runner._diagnose_module(status, self.paths, "test-slug") == "fix_activities"

    def test_fix_activities_when_both_activities_and_vocabulary_fail(self):
        status = self._make_status(
            {"meta": "pass", "lesson": "pass", "activities": "fail",
             "vocabulary": "fail", "naturalness": "pass"},
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

    def test_all_priority_types_exist_in_all_types(self):
        """Every priority_type in LEVEL_CONFIG must be in the filter's ALL_TYPES set."""
        from scripts.audit.config import LEVEL_CONFIG
        from scripts.batch_gemini_runner import _filter_schema_for_track

        # ALL_TYPES is defined inside the function; extract by checking all known types
        ALL_TYPES = {
            'quiz', 'fill-in', 'match-up', 'true-false', 'group-sort',
            'unjumble', 'error-correction', 'anagram', 'select',
            'translate', 'cloze', 'mark-the-words', 'reading',
            'essay-response', 'critical-analysis', 'comparative-study',
            'authorial-intent', 'creative-writing', 'transcription',
            'etymology-trace', 'grammar-identify', 'phonology-lab',
            'grammar-lab', 'parallel-text', 'paleography-analysis',
            'historical-writing', 'register-identify', 'loanword-trace',
            'comparative-style',
        }

        missing = set()
        for config_key, config in LEVEL_CONFIG.items():
            for ptype in config.get('priority_types', set()):
                if ptype not in ALL_TYPES:
                    missing.add(ptype)

        assert not missing, f"priority_types not in ALL_TYPES: {missing}"

    def test_seminar_priority_types_have_h3_headers_in_schema(self):
        """Seminar track priority types must have parseable H3 headers in the schema file."""
        schema_path = Path(__file__).parent.parent / "docs" / "ACTIVITY-YAML-REFERENCE.md"
        assert schema_path.exists(), f"Schema file missing: {schema_path}"
        schema_content = schema_path.read_text()

        # Extract all H3 header type names from the schema
        h3_types_found = set()
        for line in schema_content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('### '):
                header_text = stripped[4:].strip().lower()
                # Match the same heuristic used in _filter_schema_for_track
                from scripts.batch_gemini_runner import _filter_schema_for_track
                ALL_TYPES = {
                    'quiz', 'fill-in', 'match-up', 'true-false', 'group-sort',
                    'unjumble', 'error-correction', 'anagram', 'select',
                    'translate', 'cloze', 'mark-the-words', 'reading',
                    'essay-response', 'critical-analysis', 'comparative-study',
                    'authorial-intent', 'creative-writing', 'transcription',
                    'etymology-trace', 'grammar-identify', 'phonology-lab',
                    'grammar-lab', 'parallel-text', 'paleography-analysis',
                    'historical-writing', 'register-identify', 'loanword-trace',
                    'comparative-style',
                }
                for atype in ALL_TYPES:
                    if header_text.startswith(atype):
                        h3_types_found.add(atype)

        # Seminar tracks' priority types that the filter must be able to find
        seminar_priority = {'reading', 'essay-response', 'critical-analysis', 'comparative-study'}
        missing = seminar_priority - h3_types_found
        assert not missing, (
            f"Seminar priority types missing H3 headers in schema: {missing}. "
            f"Found headers for: {h3_types_found & seminar_priority}"
        )

    def test_filter_produces_nonempty_for_seminar_priority_types(self):
        """_filter_schema_for_track must return non-empty output for each seminar track."""
        from scripts.batch_gemini_runner import _filter_schema_for_track
        from scripts.audit.config import LEVEL_CONFIG

        schema_path = Path(__file__).parent.parent / "docs" / "ACTIVITY-YAML-REFERENCE.md"
        schema_content = schema_path.read_text()

        seminar_configs = {
            'B2-history': LEVEL_CONFIG.get('B2-history', {}),
            'C1-biography': LEVEL_CONFIG.get('C1-biography', {}),
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
