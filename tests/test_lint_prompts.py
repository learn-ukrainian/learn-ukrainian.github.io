"""Tests for scripts/lint/lint_prompts.py — prompt template linting."""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "lint"))

from lint_prompts import (
    RULES,
    RESEARCH_RULES,
    check_line_rules,
    scan_prompts,
    scan_curriculum_research,
)


# ---------- Unit tests for individual rules ----------

class TestRules:
    """Test that lint rules catch what they should and pass what they shouldn't."""

    def _check_text(self, text: str, filename: str = "test.md") -> list[dict]:
        """Helper: write text to a temp file and run check_line_rules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir) / filename
            tmp.write_text(text)
            with patch("lint_prompts.PROJECT_ROOT", Path(tmpdir)):
                return check_line_rules(tmp)

    def test_helpful_neighbor_caught(self):
        violations = self._check_text("Use the Helpful Neighbor voice.")
        assert any(v["rule"] == "HELPFUL_NEIGHBOR" for v in violations)

    def test_helpful_neighbor_exception(self):
        violations = self._check_text("NEVER use 'Helpful Neighbor' — use 'Ukrainian Teacher'.")
        assert not any(v["rule"] == "HELPFUL_NEIGHBOR" for v in violations)

    def test_friendly_neighbour_caught(self):
        violations = self._check_text("As a friendly neighbour, explain grammar.")
        assert any(v["rule"] == "FRIENDLY_NEIGHBOUR_PERSONA" for v in violations)

    def test_friendly_neighbour_exception(self):
        violations = self._check_text("Do not use 'friendly neighbour' framing.")
        assert not any(v["rule"] == "FRIENDLY_NEIGHBOUR_PERSONA" for v in violations)

    def test_colleague_tone_caught(self):
        violations = self._check_text("Вітаю, колего! Давайте працювати.")
        assert any(v["rule"] == "COLLEAGUE_TONE" for v in violations)

    def test_clean_file_no_violations(self):
        violations = self._check_text("Write Ukrainian content using teacher-student framing.")
        assert len(violations) == 0


class TestResearchRules:
    """Test research-specific persona contamination rules."""

    def _check_research(self, text: str) -> list[dict]:
        """Check text against research rules."""
        violations = []
        lines = text.splitlines()
        for rule_id, severity, description, pattern, exception in RESEARCH_RULES:
            for i, line in enumerate(lines, 1):
                if pattern.search(line):
                    if exception and exception.search(line):
                        continue
                    violations.append({"rule": rule_id, "line": i})
        return violations

    def test_persona_name_caught(self):
        violations = self._check_research("Use the Village Storyteller voice for this module.")
        assert any(v["rule"] == "RESEARCH_PERSONA_NAME" for v in violations)

    def test_persona_keyword_caught(self):
        violations = self._check_research("The persona should guide the learner.")
        assert any(v["rule"] == "RESEARCH_PERSONA_KEYWORD" for v in violations)

    def test_persona_flavor_caught(self):
        violations = self._check_research("Insert PERSONA_FLAVOR here.")
        assert any(v["rule"] == "RESEARCH_PERSONA_FLAVOR" for v in violations)

    def test_persona_guard_exception(self):
        violations = self._check_research("Do NOT reference persona in research files.")
        assert not any(v["rule"] == "RESEARCH_PERSONA_KEYWORD" for v in violations)

    def test_clean_research(self):
        violations = self._check_research("This module covers Cossack history from 1648 to 1667.")
        assert len(violations) == 0


# ---------- Template variable tests ----------

class TestTemplateVariables:
    """Verify all active templates have resolvable placeholders."""

    ACTIVE_TEMPLATES_DIR = ROOT / "claude_extensions" / "phases" / "gemini"

    # Known valid placeholders — extracted from all active templates.
    # If a new placeholder is added to a template, add it here too.
    VALID_PLACEHOLDERS = {
        "ACTIVITIES_FILE_CONTENT", "ACTIVITIES_PATH",
        "ACTIVITY_COUNT_TARGET", "ACTIVITY_MAX", "ACTIVITY_MIN",
        "ALLOWED_ACTIVITY_TYPES", "AVAILABLE_LETTERS",
        "CHECKPOINT_GUIDANCE",
        "COMPUTED_ACTIVITY_COUNT", "COMPUTED_AUDIT_STATUS",
        "COMPUTED_ENGAGEMENT_COUNT", "COMPUTED_H2_SECTIONS",
        "COMPUTED_IMMERSION_PERCENT", "COMPUTED_IMMERSION_TARGET",
        "COMPUTED_RICHNESS_GAPS", "COMPUTED_RICHNESS_SCORE",
        "COMPUTED_RICHNESS_THRESHOLD", "COMPUTED_VOCAB_COUNT",
        "COMPUTED_WORD_COUNT", "COMPUTED_WORD_PERCENT", "COMPUTED_WORD_TARGET",
        "CONTENT_FILE_CONTENT", "CONTENT_PATH", "CUMULATIVE_VOCAB",
        "D1_OUTPUT_FORMAT", "DECODABILITY_NOTE", "DECODABLE_VOCABULARY",
        "DETERMINISTIC_ISSUES",
        "ENGAGEMENT_MIN", "EXACT_SECTION_TITLES", "EXAMPLE_MIN",
        "EXPANSION_METHOD", "EXTRACTED_FIX_PLAN",
        "FILLER_PHRASES", "FORBIDDEN_ACTIVITY_TYPES",
        "FOLK_MATERIAL",
        "H3_WORD_RANGE",
        "IMMERSION_RULE", "INJECTED_AUDIT_FAILURES", "INTRO_HOOK",
        "ITEM_MINIMUMS_TABLE",
        "LEVEL", "LEXICAL_SANDBOX",
        "META_PATH", "MODULE_NUM", "MODULE_TYPE",
        "PEDAGOGICAL_CONSTRAINTS", "PERSONA_ROLE", "PERSONA_VOICE",
        "PLAN_CONTENT", "PLAN_PATH", "PLAN_YAML",
        "POSITION", "PRIMARY_SOURCE_EXCERPTS", "PRIORITY_TYPES",
        "PRIOR_WORDS", "PRONUNCIATION_VIDEOS",
        "QUICK_REF_PATH",
        "RAG_IMAGES", "RAG_LITERARY", "RAG_PRIMARY_SOURCES",
        "RAG_TEXT_CHUNKS", "RAG_WORD_VERIFICATION",
        "REQUIRED_TYPES", "RESEARCH_CONTENT", "RESEARCH_MD", "RESEARCH_PATH",
        "RUSSIANISM_TABLE",
        "SCHEMA_PATH", "SCORING_OUTPUT_TABLE", "SCORING_SECTION",
        "SECTION_BUDGET_TABLE", "SELF_AUDIT_SNIPPET", "SELF_CHECK_HEADING",
        "SHARED_ACTIVITY_RULES", "SHARED_CONTENT_RULES",
        "SKILL_IDENTITY", "SLUG", "STRUCTURAL_RULES", "SUMMARY_HEADING",
        "TEXTBOOK_ACTIVITY_EXAMPLES", "TEXTBOOK_EXAMPLES", "TEXTBOOK_GRADE",
        "TIER_GUIDANCE", "TOPIC_KEYWORDS", "TOPIC_TITLE", "TRACK",
        "TRACK_CALIBRATION",
        "VIDEO_DISCOVERY",
        "VOCAB_COUNT_TARGET", "VOCAB_FILE_CONTENT", "VOCAB_HINTS",
        "VOCAB_PATH", "VOCAB_TARGET",
        "WORD_CEILING", "WORD_TARGET", "WORD_TARGET_TOKENS",
        "WRITING_TONE_INSTRUCTION",
        "YAML_CONTENT", "YOUR_MODEL_ID",
    }

    def _extract_placeholders(self, text: str) -> set[str]:
        """Extract {UPPERCASE_PLACEHOLDER} patterns from text."""
        import re
        return set(re.findall(r"\{([A-Z][A-Z0-9_]+)\}", text))

    # Batch-system templates use legacy placeholder conventions
    BATCH_TEMPLATES = {
        "phase-0-research-seminar.md", "phase-5-review.md",
        "phase-fix.md", "phase-fix-content.md", "phase-fix-activities.md",
    }

    @pytest.mark.parametrize("template_file", sorted(
        (ROOT / "claude_extensions" / "phases" / "gemini").glob("*.md")
    ), ids=lambda p: p.name)
    def test_template_placeholders_known(self, template_file):
        """Every placeholder in active templates should be in the known set."""
        if template_file.name.startswith("_") or template_file.name == "README.md":
            pytest.skip("Not a phase template")
        if template_file.name in self.BATCH_TEMPLATES:
            pytest.skip("Batch-system template (legacy placeholder convention)")

        text = template_file.read_text()
        placeholders = self._extract_placeholders(text)

        unknown = placeholders - self.VALID_PLACEHOLDERS
        assert not unknown, (
            f"{template_file.name} has unknown placeholders: {unknown}\n"
            f"Add to VALID_PLACEHOLDERS if intentional."
        )


# ---------- Integration tests ----------

class TestScanIntegration:
    """Integration tests for scanning actual project files."""

    def test_scan_prompts_no_errors(self):
        """Active prompt files should have zero errors."""
        violations = scan_prompts()
        errors = [v for v in violations if v["severity"] == "error"]
        assert not errors, f"Prompt errors: {errors}"

    def test_retired_templates_exist(self):
        """Retired templates should be in _retired/ directory."""
        retired_dir = ROOT / "claude_extensions" / "phases" / "gemini" / "_retired"
        if not retired_dir.exists():
            pytest.skip("No retired directory yet")
        retired_files = list(retired_dir.glob("*.md"))
        assert len(retired_files) >= 5, (
            f"Expected 5+ retired templates, found {len(retired_files)}"
        )

    def test_no_retired_referenced_in_pipeline(self):
        """Pipeline v5 should not reference any retired template names."""
        retired_dir = ROOT / "claude_extensions" / "phases" / "gemini" / "_retired"
        if not retired_dir.exists():
            pytest.skip("No retired directory")

        retired_names = {f.stem for f in retired_dir.glob("*.md")}
        pipeline_path = ROOT / "scripts" / "build" / "pipeline_v5.py"
        if not pipeline_path.exists():
            pytest.skip("pipeline_v5.py not found")

        pipeline_text = pipeline_path.read_text()
        referenced = {name for name in retired_names if name in pipeline_text}
        assert not referenced, f"Pipeline references retired templates: {referenced}"
