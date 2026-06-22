"""Tests for scripts/lint/lint_prompts.py — prompt template linting."""
from __future__ import annotations

import re
import sys
import tempfile
import typing
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "lint"))

from lint_prompts import (
    RESEARCH_RULES,
    check_line_rules,
    check_orchestrator_suite_file,
    extract_curriculum_level_keys,
    extract_curriculum_level_types,
    scan_orchestrator_suites,
    scan_prompts,
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
        for rule_id, _severity, _description, pattern, exception in RESEARCH_RULES:
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

    ACTIVE_TEMPLATES_DIR = ROOT / "agents_extensions/shared" / "phases" / "gemini"

    # Known valid placeholders — extracted from all active templates.
    # If a new placeholder is added to a template, add it here too.
    VALID_PLACEHOLDERS: typing.ClassVar[set[str]] = {
        "ACTIVITIES_FILE_CONTENT", "ACTIVITIES_PATH",
        "ACTIVITY_COUNT", "ACTIVITY_COUNT_TARGET", "ACTIVITY_EXAMPLES",
        "ACTIVITY_MAX", "ACTIVITY_MIN", "ACTIVITY_PLANS",
        "ALLOWED_ACTIVITY_TYPES", "AUDIT_ERRORS", "AUDIT_STATUS", "AUDIT_WORD_COUNT",
        "AVAILABLE_LETTERS",
        "CHECKPOINT_GUIDANCE", "CHECKPOINT_REVIEW_GUIDANCE",
        "COMPUTED_ACTIVITY_COUNT", "COMPUTED_AUDIT_STATUS",
        "COMPUTED_ENGAGEMENT_COUNT", "COMPUTED_H2_SECTIONS",
        "COMPUTED_IMMERSION_PERCENT", "COMPUTED_IMMERSION_TARGET",
        "COMPUTED_RICHNESS_GAPS", "COMPUTED_RICHNESS_SCORE",
        "COMPUTED_RICHNESS_THRESHOLD", "COMPUTED_VOCAB_COUNT",
        "COMPUTED_WORD_COUNT", "COMPUTED_WORD_PERCENT", "COMPUTED_WORD_TARGET",
        "CONTENT_FILE_CONTENT", "CONTENT_PATH", "CUMULATIVE_VOCAB",
        "D1_OUTPUT_FORMAT", "DECODABILITY_NOTE", "DECODABLE_VOCABULARY",
        "DETERMINISTIC_ISSUES",
        "ENGAGEMENT_COUNT", "ENGAGEMENT_MIN", "EXACT_SECTION_TITLES", "EXAMPLE_MIN",
        "EXPANSION_METHOD", "EXTRACTED_FIX_PLAN",
        "FILLER_PHRASES", "FORBIDDEN_ACTIVITY_TYPES",
        "FOLK_MATERIAL",
        "H3_WORD_RANGE",
        "IMMERSION_PERCENT", "IMMERSION_RULE", "IMMERSION_TARGET",
        "INJECTED_AUDIT_FAILURES", "INTRO_HOOK",
        "ITEM_MINIMUMS_TABLE",
        "LEVEL", "LEXICAL_SANDBOX",
        "MODULE_NUM", "MODULE_TYPE",
        "PEDAGOGICAL_CONSTRAINTS", "PERSONA_ROLE", "PERSONA_VOICE", "PREFLIGHT_INSTRUCTIONS", "PREV_MODULE",
        "PLAN_CONTENT", "PLAN_PATH", "PLAN_YAML",
        "POSITION", "PRIMARY_SOURCE_EXCERPTS", "PRIORITY_TYPES",
        "PRIOR_WORDS", "PRONUNCIATION_VIDEOS",
        "QUALITY_DIMENSIONS",
        "QUICK_REF_CONTENT", "QUICK_REF_PATH",
        "RAG_IMAGES", "RAG_LITERARY", "RAG_PRIMARY_SOURCES",
        "RAG_TEXT_CHUNKS", "RAG_WORD_VERIFICATION",
        "REQUIRED_TYPES", "RESEARCH_CONTENT", "RESEARCH_MD", "RESEARCH_PATH", "REVIEW_PATH",
        "RUSSIANISM_TABLE",
        "SCHEMA_PATH", "SCORING_OUTPUT_TABLE", "SCORING_SECTION",
        "SECTION_BUDGET_TABLE", "SELF_AUDIT_SNIPPET", "SELF_CHECK_HEADING",
        "SHARED_ACTIVITY_RULES", "SHARED_CONTENT_RULES",
        "SKILL_IDENTITY", "SLUG", "STRUCTURAL_RULES", "SUMMARY_HEADING",
        "TEXTBOOK_ACTIVITY_EXAMPLES", "TEXTBOOK_CONTEXT",
        "TEXTBOOK_EXAMPLES", "TEXTBOOK_EXERCISES", "TEXTBOOK_GRADE",
        "TIER_GUIDANCE", "TOPIC_KEYWORDS", "TOPIC_TITLE", "TRACK",
        "TRACK_CALIBRATION",
        "VIDEO_DISCOVERY",
        "VOCABULARY_HINTS",
        "VOCAB_COUNT", "VOCAB_COUNT_TARGET", "VOCAB_FILE_CONTENT", "VOCAB_HINTS",
        "VOCAB_PATH", "VOCAB_TARGET",
        "WORD_CEILING", "WORD_PERCENT", "WORD_TARGET", "WORD_TARGET_TOKENS",
        "WRITING_STYLE", "WRITING_TONE_INSTRUCTION",
        "YAML_CONTENT", "YOUR_MODEL_ID",
        # Added after the initial set was frozen — actively used by
        # the current v6 and review templates. Keep sorted with the
        # rest above when adding new entries.
        "BASE_TEMPLATE_PATH", "BUILDER_NOTES_BLOCK",
        "DIALOGUE_SITUATIONS",
        "FRICTION_CONSTRAINTS",
        "GENERATED_CONTENT", "GOLDEN_FRAGMENT",
        "IMMERSION_TARGET_SHORT", "INJECTION_MARKERS",
        "INLINE_ALLOWED_TYPES", "INLINE_MAX", "INLINE_MIN",
        "INLINE_PRIORITY_TYPES",
        "KNOWLEDGE_PACKET",
        "LEARNER_STATE", "LEVEL_CONSTRAINTS", "LEVEL_CONTEXT",
        "MODULE_CONTENT", "MODULE_OUTPUT_PATH", "MODULE_SLUG",
        "PEDAGOGY_PATTERNS", "PHASE", "PLAN_ACTIVITY_HINTS",
        "PLAN_VOCABULARY", "PRE_VERIFIED_FACTS",
        "RENDERED_PROMPT_PATH", "REVIEW_FAILURES",
        "TOOL_INSTRUCTIONS", "TOTAL_TARGET",
        "VOCABULARY_BANK",
        "WORD_OVERSHOOT", "WORKBOOK_ALLOWED_TYPES",
        "WORKBOOK_MAX", "WORKBOOK_MIN", "WORKBOOK_PRIORITY_TYPES",
        "WRITER_MODEL",
    }

    def _extract_placeholders(self, text: str) -> set[str]:
        """Extract {UPPERCASE_PLACEHOLDER} patterns from text."""
        return set(re.findall(r"\{([A-Z][A-Z0-9_]+)\}", text))

    # Batch-system templates use legacy placeholder conventions
    BATCH_TEMPLATES: typing.ClassVar[set[str]] = {
        "research-seminar-v0.md", "review-legacy.md",
        "fix.md", "fix-content.md", "fix-activities.md",
    }

    @pytest.mark.parametrize("template_file", sorted(
        (ROOT / "agents_extensions/shared" / "phases" / "gemini").glob("*.md")
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
        retired_dir = ROOT / "agents_extensions/shared" / "phases" / "gemini" / "_retired"
        if not retired_dir.exists():
            pytest.skip("No retired directory yet")
        retired_files = list(retired_dir.glob("*.md"))
        assert len(retired_files) >= 5, (
            f"Expected 5+ retired templates, found {len(retired_files)}"
        )


# ---------- Orchestrator suite contract tests ----------

def _valid_suite_text(track: str, *, seminar: bool = True) -> str:
    """Return a minimal valid suite prompt for contract tests."""
    seminar_refs = ""
    reading_line = ""
    if seminar:
        seminar_refs = "\n".join([
            "- `docs/prompts/orchestrators/shared/seminar-source-rules.md`",
            "- `docs/prompts/orchestrators/shared/reading-section-rules.md`",
        ])
        reading_line = "Reading coverage: <hosted/link-only/excerpt-only/omit/needed counts>\n"
    return f"""# {track.upper()} Orchestrator Suite

Prompt version: 0.1

## Source Assumptions

Current source assumptions.

## Goal

Build the scoped track.

## WORKTREE_ROOT Setup

```bash
git worktree add -b codex/{track}-<stage> .worktrees/dispatch/codex/{track}-<stage> origin/main
cd .worktrees/dispatch/codex/{track}-<stage>
pwd
git status --short --branch
git rev-parse --show-toplevel
```

## Read First

- `docs/prompts/orchestrators/shared/repo-rules.md`
- `docs/prompts/orchestrators/shared/validation-checklist.md`
- `docs/prompts/orchestrators/shared/telemetry-and-pr.md`
- `docs/prompts/orchestrators/shared/review-output-schema.md`
{seminar_refs}

## Allowed Writes

- Scoped files only.

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, curriculum `review/`, and `data/telemetry/**` artifacts

## Lifecycle Rules

- Run the right stage.

## Helpers And Headroom

Use helpers sparingly.

## Validation Commands

```bash
git diff --check
```

## Expected Final Response

```text
{track.upper()} stage: <preflight | production | quality-audit | remediation>
Scope: <slugs or audit report>
{reading_line}Files changed: <paths>
Validation run: <commands and outcomes>
Telemetry: <posted | not module-build | unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
"""


class TestOrchestratorSuiteContracts:
    """Tests for docs/prompts/orchestrators suite hardening."""

    def test_extract_curriculum_level_keys(self, tmp_path: Path):
        manifest = tmp_path / "curriculum.yaml"
        manifest.write_text(
            "version: '1.0'\n"
            "levels:\n"
            "  c1:\n"
            "    type: core\n"
            "# column-zero comments should not end levels parsing\n"
            "  lit-humor:\n"
            "    type: seminar\n"
            "other: ignored\n",
            encoding="utf-8",
        )
        assert extract_curriculum_level_keys(manifest) == {"c1", "lit-humor"}
        assert extract_curriculum_level_types(manifest) == {
            "c1": "core",
            "lit-humor": "seminar",
        }

    def test_seminar_suite_requires_reading_coverage(self, tmp_path: Path):
        suite_path = tmp_path / "lit" / "suite-orchestrator.md"
        suite_path.parent.mkdir()
        suite_path.write_text(
            _valid_suite_text("lit").replace(
                "Reading coverage: <hosted/link-only/excerpt-only/omit/needed counts>\n",
                "",
            ),
            encoding="utf-8",
        )
        violations = check_orchestrator_suite_file(suite_path)
        assert any(v["rule"] == "ORCH_SUITE_READING_COVERAGE" for v in violations)

    def test_scan_orchestrator_suites_rejects_stale_lit_track(self, tmp_path: Path):
        root = tmp_path / "orchestrators"
        (root / "lit-doc").mkdir(parents=True)
        manifest = tmp_path / "curriculum.yaml"
        manifest.write_text("levels:\n  lit:\n    type: seminar\n", encoding="utf-8")

        violations = scan_orchestrator_suites(root=root, manifest_path=manifest)
        assert any(v["rule"] == "ORCH_TRACK_NOT_ACTIVE" for v in violations)
        assert any(v["rule"] == "ORCH_STALE_LIT_TRACK" for v in violations)

    def test_scan_orchestrator_suites_requires_active_suite(self, tmp_path: Path):
        root = tmp_path / "orchestrators"
        (root / "c1").mkdir(parents=True)
        manifest = tmp_path / "curriculum.yaml"
        manifest.write_text("levels:\n  c1:\n    type: core\n", encoding="utf-8")

        violations = scan_orchestrator_suites(root=root, manifest_path=manifest)
        assert any(v["rule"] == "ORCH_ACTIVE_TRACK_MISSING_SUITE" for v in violations)

    def test_scan_orchestrator_suites_derives_seminar_type(self, tmp_path: Path):
        root = tmp_path / "orchestrators"
        suite_path = root / "new-seminar" / "suite-orchestrator.md"
        suite_path.parent.mkdir(parents=True)
        suite_path.write_text(
            _valid_suite_text("new-seminar", seminar=False),
            encoding="utf-8",
        )
        manifest = tmp_path / "curriculum.yaml"
        manifest.write_text(
            "levels:\n  new-seminar:\n    type: seminar\n",
            encoding="utf-8",
        )

        violations = scan_orchestrator_suites(root=root, manifest_path=manifest)
        rules = {v["rule"] for v in violations}
        assert "ORCH_SUITE_READING_COVERAGE" in rules
        assert "ORCH_SUITE_SEMINAR_REFERENCE" in rules

    def test_manifest_seminar_type_is_additive_to_curated_set(self, tmp_path: Path):
        root = tmp_path / "orchestrators"
        new_suite = root / "new-seminar" / "suite-orchestrator.md"
        lit_suite = root / "lit" / "suite-orchestrator.md"
        new_suite.parent.mkdir(parents=True)
        lit_suite.parent.mkdir(parents=True)
        new_suite.write_text(_valid_suite_text("new-seminar"), encoding="utf-8")
        lit_suite.write_text(
            _valid_suite_text("lit", seminar=False),
            encoding="utf-8",
        )
        manifest = tmp_path / "curriculum.yaml"
        manifest.write_text(
            "levels:\n"
            "  new-seminar:\n"
            "    type: seminar\n"
            "  lit:\n"
            "    type: track\n",
            encoding="utf-8",
        )

        violations = scan_orchestrator_suites(root=root, manifest_path=manifest)
        assert any(
            v["rule"] == "ORCH_SUITE_READING_COVERAGE"
            and v["file"].endswith("lit/suite-orchestrator.md")
            for v in violations
        )

    def test_scan_orchestrator_suites_accepts_valid_active_suite(self, tmp_path: Path):
        root = tmp_path / "orchestrators"
        suite_path = root / "lit" / "suite-orchestrator.md"
        suite_path.parent.mkdir(parents=True)
        suite_path.write_text(_valid_suite_text("lit"), encoding="utf-8")
        manifest = tmp_path / "curriculum.yaml"
        manifest.write_text("levels:\n  lit:\n    type: seminar\n", encoding="utf-8")

        assert scan_orchestrator_suites(root=root, manifest_path=manifest) == []
