"""
Tests for status cache correctness fixes (#539).

Fix 1: Plan mtime populated for seminar-track paths (b2-hist, c1-bio, etc.)
Fix 2: Freshness invalidation when meta/activities/vocabulary change
"""

import json
import os
import sys
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit.report import save_status_cache
from scripts.generate_level_status import get_json_cache


# =============================================================================
# Fix 1: Plan path uses track directory, not level_code
# =============================================================================

class TestPlanMtimePopulated:
    """Verify plan mtime is populated for seminar-like track paths."""

    def setup_method(self):
        """Create temp directory mimicking curriculum/l2-uk-en/b2-hist/."""
        self.tmpdir = tempfile.mkdtemp()
        # Simulate: curriculum/l2-uk-en/b2-hist/
        self.l2_dir = Path(self.tmpdir) / "curriculum" / "l2-uk-en"
        self.track_dir = self.l2_dir / "b2-hist"
        self.track_dir.mkdir(parents=True)
        (self.track_dir / "status").mkdir()

        # Create plans directory at sibling level
        self.plans_dir = self.l2_dir / "plans" / "b2-hist"
        self.plans_dir.mkdir(parents=True)

        # Create a plan file (bare slug, no numeric prefix)
        self.plan_file = self.plans_dir / "bohdan-khmelnytskyi.yaml"
        self.plan_file.write_text("title: Bohdan Khmelnytskyi\n")

        # Create the module .md file (with numeric prefix)
        self.md_file = self.track_dir / "05-bohdan-khmelnytskyi.md"
        self.md_file.write_text("# Bohdan Khmelnytskyi\nContent here.")

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_plan_mtime_populated_for_seminar_track(self):
        """Plan mtime should NOT be null when plan exists under plans/b2-hist/."""
        path = save_status_cache(
            str(self.md_file), "B2", "05-bohdan-khmelnytskyi",
            results={}, has_critical_failure=False,
            critical_failure_reasons=[],
        )
        with open(path) as f:
            data = json.load(f)

        assert data["source_mtimes"]["plan"] is not None, \
            "Plan mtime should be populated for seminar tracks"

    def test_plan_mtime_null_when_no_plan_exists(self):
        """Plan mtime should be null when no plan file exists."""
        # Remove the plan file
        self.plan_file.unlink()

        path = save_status_cache(
            str(self.md_file), "B2", "05-bohdan-khmelnytskyi",
            results={}, has_critical_failure=False,
            critical_failure_reasons=[],
        )
        with open(path) as f:
            data = json.load(f)

        assert data["source_mtimes"]["plan"] is None

    def test_plan_path_resolves_for_core_track(self):
        """Plan mtime works for core tracks too (e.g., a1)."""
        # Create a1 structure
        a1_dir = self.l2_dir / "a1"
        a1_dir.mkdir(parents=True)
        (a1_dir / "status").mkdir()

        plans_a1 = self.l2_dir / "plans" / "a1"
        plans_a1.mkdir(parents=True)
        plan = plans_a1 / "01-basics.yaml"
        plan.write_text("title: Basics\n")

        md = a1_dir / "01-basics.md"
        md.write_text("# Basics\nContent.")

        path = save_status_cache(
            str(md), "A1", "01-basics",
            results={}, has_critical_failure=False,
            critical_failure_reasons=[],
        )
        with open(path) as f:
            data = json.load(f)

        assert data["source_mtimes"]["plan"] is not None

    def test_plan_resolves_via_bare_slug_fallback(self):
        """Plan should resolve when module_slug has prefix but plan file doesn't."""
        # Plan is "bohdan-khmelnytskyi.yaml" (bare), slug is "05-bohdan-khmelnytskyi"
        # This is already the main test case, but let's be explicit:
        # The plan file exists as bare slug, module_slug has numeric prefix
        path = save_status_cache(
            str(self.md_file), "B2", "05-bohdan-khmelnytskyi",
            results={}, has_critical_failure=False,
            critical_failure_reasons=[],
        )
        with open(path) as f:
            data = json.load(f)

        assert data["source_mtimes"]["plan"] is not None


# =============================================================================
# Fix 2: Multi-file freshness in get_json_cache()
# =============================================================================

class TestMultiFileFreshness:
    """Verify cache invalidation when meta/activities/vocabulary change."""

    def setup_method(self):
        """Create temp directory with status cache and source files."""
        self.tmpdir = tempfile.mkdtemp()
        # Wrap in a parent dir so plans/ is a sibling of the level dir
        self.l2_dir = Path(self.tmpdir) / "l2-uk-en"
        self.level_dir = self.l2_dir / "b1"
        self.level_dir.mkdir(parents=True)
        (self.level_dir / "status").mkdir()
        (self.level_dir / "meta").mkdir()
        (self.level_dir / "activities").mkdir()
        (self.level_dir / "vocabulary").mkdir()

        # Create plan file
        self.plans_dir = self.l2_dir / "plans" / "b1"
        self.plans_dir.mkdir(parents=True)
        self.plan_file = self.plans_dir / "06-test-module.yaml"
        self.plan_file.write_text("title: Test Module\n")

        # Create source files with old timestamps
        self.md_file = self.level_dir / "06-test-module.md"
        self.md_file.write_text("# Test\nContent here.")

        self.meta_file = self.level_dir / "meta" / "06-test-module.yaml"
        self.meta_file.write_text("word_target: 3000\n")

        self.activities_file = self.level_dir / "activities" / "06-test-module.yaml"
        self.activities_file.write_text("- type: quiz\n  title: Test\n")

        self.vocab_file = self.level_dir / "vocabulary" / "06-test-module.yaml"
        self.vocab_file.write_text("- word: тест\n")

        # Create a valid cache file with a recent audit timestamp
        self.cache_file = self.level_dir / "status" / "06-test-module.json"
        self.audit_time = datetime.now()
        cache_data = {
            "module": "06-test-module",
            "level": "B1",
            "plan_version": "2.0",
            "last_audit": self.audit_time.isoformat() + "Z",
            "source_mtimes": {
                "md": "2026-01-01T00:00:00Z",
                "meta": "2026-01-01T00:00:00Z",
                "activities": "2026-01-01T00:00:00Z",
                "vocabulary": "2026-01-01T00:00:00Z",
                "plan": None,
            },
            "gates": {
                "meta": {"status": "pass", "violations": 0, "message": ""},
                "lesson": {"status": "pass", "violations": 0, "message": "3000/3000"},
                "activities": {"status": "pass", "violations": 0, "message": "5/3"},
                "vocabulary": {"status": "pass", "violations": 0, "message": "25/20"},
                "naturalness": {"status": "pass", "violations": 0, "message": "9/10"},
                "review": {"status": "skipped", "violations": 0, "message": ""},
            },
            "overall": {
                "status": "pass",
                "blocking_issues": [],
                "pass_count": 5,
                "fail_count": 0,
            },
        }
        self.cache_file.write_text(json.dumps(cache_data, indent=2))

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_cache_fresh_when_all_sources_older(self):
        """Cache should be used when all source files are older than audit."""
        result = get_json_cache("b1", "06-test-module", self.md_file)
        assert result is not None
        assert result["cached"] is True

    def test_cache_stale_when_md_is_newer(self):
        """Cache should be stale when .md file is newer than last_audit."""
        # Touch md file to make it newer
        time.sleep(0.05)
        self.md_file.write_text("# Updated\nNew content.")
        result = get_json_cache("b1", "06-test-module", self.md_file)
        assert result is None

    def test_cache_stale_when_meta_is_newer(self):
        """Cache should be stale when meta yaml changes after audit."""
        time.sleep(0.05)
        self.meta_file.write_text("word_target: 4000\n")
        result = get_json_cache("b1", "06-test-module", self.md_file)
        assert result is None

    def test_cache_stale_when_activities_is_newer(self):
        """Cache should be stale when activities yaml changes after audit."""
        time.sleep(0.05)
        self.activities_file.write_text("- type: fill-in\n  title: New\n")
        result = get_json_cache("b1", "06-test-module", self.md_file)
        assert result is None

    def test_cache_stale_when_vocabulary_is_newer(self):
        """Cache should be stale when vocabulary yaml changes after audit."""
        time.sleep(0.05)
        self.vocab_file.write_text("- word: новий\n")
        result = get_json_cache("b1", "06-test-module", self.md_file)
        assert result is None

    def test_cache_fresh_when_missing_source_files(self):
        """Cache should still be valid when optional source files don't exist."""
        # Remove meta, activities, vocabulary (they're optional for cache validity)
        self.meta_file.unlink()
        self.activities_file.unlink()
        self.vocab_file.unlink()
        result = get_json_cache("b1", "06-test-module", self.md_file)
        assert result is not None
        assert result["cached"] is True

    def test_cache_stale_when_plan_is_newer(self):
        """Cache should be stale when plan yaml changes after audit."""
        time.sleep(0.05)
        self.plan_file.write_text("title: Updated Plan\nword_target: 4000\n")
        result = get_json_cache("b1", "06-test-module", self.md_file)
        assert result is None
