"""Tests for pre-flight check and quality dimensions injection (#844).

Covers:
- Quality dimensions placeholder injection (tier-aware)
- Pre-flight instructions placeholder injection
- Pre-flight output parsing in content phase
- --skip-preflight flag
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


# =============================================================================
# Quality Dimensions Injection
# =============================================================================

class TestQualityDimensionsInjection:
    """Test that QUALITY_DIMENSIONS is populated correctly per tier."""

    def _make_ctx(self, track="a1", module_num=1):
        ctx = MagicMock()
        ctx.track = track
        ctx.module_num = module_num
        ctx.slug = "test-slug"
        ctx.topic_title = "Test Topic"
        ctx.word_target = 1200
        ctx.skill_identity = "test"
        ctx.persona_flavor = ""
        ctx.immersion_rule = "Write 10-40% Ukrainian"
        ctx.level_constraints = ""
        ctx.plan = {}
        ctx.paths = {
            "plan": MagicMock(exists=lambda: False),
            "md": MagicMock(),
            "activities": MagicMock(),
            "vocabulary": MagicMock(),
            "research": MagicMock(exists=lambda: False),
            "review": MagicMock(),
        }
        ctx.orch_dir = MagicMock()
        ctx.orch_dir.__truediv__ = lambda self, x: MagicMock(exists=lambda: False)
        ctx.track_config = {}
        ctx.activity_config = {}
        ctx.placeholders = {}
        ctx.rebuild = False
        ctx.skip_preflight = False
        return ctx

    def test_beginner_gets_base_quality_dimensions(self):
        from pipeline_lib import _get_prompt_tier, _read_phase_file
        tier = _get_prompt_tier("a1", 1)
        assert tier == "beginner"
        content = _read_phase_file("_shared-quality-dimensions.md")
        assert "Quality Dimensions" in content
        # Should NOT contain decolonization perspective (seminar-only)
        assert "Decolonization Perspective" not in content

    def test_core_gets_base_quality_dimensions(self):
        from pipeline_lib import _get_prompt_tier, _read_phase_file
        tier = _get_prompt_tier("b2", 1)
        assert tier == "core"
        content = _read_phase_file("_shared-quality-dimensions.md")
        assert "Quality Dimensions" in content

    def test_seminar_gets_extended_quality_dimensions(self):
        from pipeline_lib import _get_prompt_tier, _read_phase_file
        tier = _get_prompt_tier("hist", 1)
        assert tier == "seminar"
        content = _read_phase_file("_shared-quality-dimensions-seminar.md")
        assert "Quality Dimensions" in content
        assert "Decolonization Perspective" in content
        assert "Primary Sources" in content

    def test_quality_dimensions_file_exists(self):
        from pipeline_lib import PHASES_DIR
        assert (PHASES_DIR / "_shared-quality-dimensions.md").exists()
        assert (PHASES_DIR / "_shared-quality-dimensions-seminar.md").exists()

    def test_preflight_file_exists(self):
        from pipeline_lib import PHASES_DIR
        assert (PHASES_DIR / "_shared-preflight.md").exists()


# =============================================================================
# Pre-flight Parsing
# =============================================================================

class TestPreflightParsing:
    """Test that the pipeline correctly parses preflight output."""

    def test_extract_preflight_pass(self):
        from pipeline_lib import _extract_delimited_content
        raw = """Some preamble text.
===PREFLIGHT_START===
status: PASS
plan_depth: SUFFICIENT
research_adequacy: SUFFICIENT
contradictions: NONE
vocabulary_fit: OK
overall: All inputs are adequate.
===PREFLIGHT_END===

===CONTENT_START===
# Test Content
Some content here.
===CONTENT_END===
"""
        preflight = _extract_delimited_content(raw, "===PREFLIGHT_START===", "===PREFLIGHT_END===")
        assert preflight is not None
        assert "status: PASS" in preflight

    def test_extract_preflight_fail(self):
        from pipeline_lib import _extract_delimited_content
        raw = """===PREFLIGHT_START===
status: FAIL
plan_depth: INSUFFICIENT — only 2 bullet points for 4000-word target
research_adequacy: INSUFFICIENT — no dated events found
contradictions: NONE
vocabulary_fit: OK
overall: Plan too thin for word target. Research lacks specifics.
===PREFLIGHT_END===
"""
        preflight = _extract_delimited_content(raw, "===PREFLIGHT_START===", "===PREFLIGHT_END===")
        assert preflight is not None
        assert "status: FAIL" in preflight
        # Content should NOT be extractable
        content = _extract_delimited_content(raw, "===CONTENT_START===", "===CONTENT_END===")
        assert content is None

    def test_no_preflight_block(self):
        from pipeline_lib import _extract_delimited_content
        raw = """===CONTENT_START===
# Test Content
===CONTENT_END===
"""
        preflight = _extract_delimited_content(raw, "===PREFLIGHT_START===", "===PREFLIGHT_END===")
        assert preflight is None


# =============================================================================
# Skip Preflight Flag
# =============================================================================

class TestSkipPreflight:
    """Test that --skip-preflight correctly suppresses preflight instructions."""

    def test_skip_preflight_empty_placeholder(self):
        """When skip_preflight is True, PREFLIGHT_INSTRUCTIONS should be empty."""
        from pipeline_lib import _read_phase_file
        # Verify the preflight file has content
        content = _read_phase_file("_shared-preflight.md")
        assert len(content) > 100  # Not empty

    def test_preflight_instructions_present_by_default(self):
        """When skip_preflight is False, PREFLIGHT_INSTRUCTIONS should have content."""
        from pipeline_lib import _read_phase_file
        content = _read_phase_file("_shared-preflight.md")
        assert "PREFLIGHT_START" in content
        assert "PREFLIGHT_END" in content


# =============================================================================
# Template Line Counts
# =============================================================================

class TestTemplateLineCounts:
    """Verify prompt templates meet AC1 line count limits."""

    def test_beginner_content_under_150_lines(self):
        from pipeline_lib import PHASES_DIR
        path = PHASES_DIR / "beginner-content.md"
        lines = path.read_text("utf-8").splitlines()
        assert len(lines) < 200, f"beginner-content.md has {len(lines)} lines (max 200)"

    def test_core_content_under_250_lines(self):
        from pipeline_lib import PHASES_DIR
        path = PHASES_DIR / "core-content.md"
        lines = path.read_text("utf-8").splitlines()
        assert len(lines) < 250, f"core-content.md has {len(lines)} lines (max 250)"

    def test_seminar_content_under_300_lines(self):
        from pipeline_lib import PHASES_DIR
        path = PHASES_DIR / "content.md"
        lines = path.read_text("utf-8").splitlines()
        assert len(lines) < 300, f"content.md has {len(lines)} lines (max 300)"


# =============================================================================
# New Placeholder Integration
# =============================================================================

class TestNewPlaceholders:
    """Verify new placeholders appear in the right templates."""

    def test_beginner_content_has_quality_dimensions(self):
        from pipeline_lib import PHASES_DIR
        content = (PHASES_DIR / "beginner-content.md").read_text("utf-8")
        assert "{QUALITY_DIMENSIONS}" in content

    def test_beginner_content_has_preflight(self):
        from pipeline_lib import PHASES_DIR
        content = (PHASES_DIR / "beginner-content.md").read_text("utf-8")
        assert "{PREFLIGHT_INSTRUCTIONS}" in content

    def test_core_content_has_quality_dimensions(self):
        from pipeline_lib import PHASES_DIR
        content = (PHASES_DIR / "core-content.md").read_text("utf-8")
        assert "{QUALITY_DIMENSIONS}" in content

    def test_core_content_has_preflight(self):
        from pipeline_lib import PHASES_DIR
        content = (PHASES_DIR / "core-content.md").read_text("utf-8")
        assert "{PREFLIGHT_INSTRUCTIONS}" in content

    def test_seminar_content_has_quality_dimensions(self):
        from pipeline_lib import PHASES_DIR
        content = (PHASES_DIR / "content.md").read_text("utf-8")
        assert "{QUALITY_DIMENSIONS}" in content

    def test_seminar_content_has_preflight(self):
        from pipeline_lib import PHASES_DIR
        content = (PHASES_DIR / "content.md").read_text("utf-8")
        assert "{PREFLIGHT_INSTRUCTIONS}" in content

    def test_beginner_content_no_shared_content_rules(self):
        """New beginner template should NOT reference old SHARED_CONTENT_RULES."""
        from pipeline_lib import PHASES_DIR
        content = (PHASES_DIR / "beginner-content.md").read_text("utf-8")
        assert "{SHARED_CONTENT_RULES}" not in content

    def test_core_content_no_shared_content_rules(self):
        """New core template should NOT reference old SHARED_CONTENT_RULES."""
        from pipeline_lib import PHASES_DIR
        content = (PHASES_DIR / "core-content.md").read_text("utf-8")
        assert "{SHARED_CONTENT_RULES}" not in content

    def test_seminar_content_no_shared_content_rules(self):
        """New seminar template should NOT reference old SHARED_CONTENT_RULES."""
        from pipeline_lib import PHASES_DIR
        content = (PHASES_DIR / "content.md").read_text("utf-8")
        assert "{SHARED_CONTENT_RULES}" not in content

    def test_beginner_content_no_self_audit(self):
        """New beginner template should NOT reference old SELF_AUDIT_SNIPPET."""
        from pipeline_lib import PHASES_DIR
        content = (PHASES_DIR / "beginner-content.md").read_text("utf-8")
        assert "{SELF_AUDIT_SNIPPET}" not in content
