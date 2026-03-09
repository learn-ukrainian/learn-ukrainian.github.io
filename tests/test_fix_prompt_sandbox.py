"""Tests for #813: sandbox/immersion/level-constraint injection into fix prompts."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "build"))


# ---------------------------------------------------------------------------
# Lightweight stub for ModuleContext — avoids importing the full pipeline
# ---------------------------------------------------------------------------
@dataclass
class _StubCtx:
    track: str = "a1"
    module_num: int = 47
    slug: str = "imperative-and-requests"
    plan: dict = field(default_factory=dict)
    paths: dict = field(default_factory=dict)
    orch_dir: Path = field(default_factory=lambda: Path("/tmp/test-orch"))
    immersion_rule: str = ""
    level_constraints: str = ""
    _lexical_sandbox: str = ""


# ---------------------------------------------------------------------------
# Import the function under test
# ---------------------------------------------------------------------------
from pipeline_v5 import _build_fix_prompt


def _make_ctx(**overrides) -> _StubCtx:
    ctx = _StubCtx()
    # Provide a minimal md path that doesn't exist (handled gracefully)
    ctx.paths = {"md": Path("/tmp/nonexistent.md"), "activities": Path("/tmp/nonexistent.yaml")}
    for k, v in overrides.items():
        setattr(ctx, k, v)
    return ctx


MINIMAL_AUDIT = "❌ WORDS: 800 / 1200 (67%)"


# ============================================================================
# Sandbox extraction
# ============================================================================

class TestSandboxInjection:
    """Verify lexical sandbox is extracted and injected into fix prompts."""

    def test_sandbox_table_format_extracted(self):
        """Sandbox in markdown table format → lemmas extracted."""
        sandbox = (
            "| Lemma | POS | Forms |\n"
            "|-------|-----|-------|\n"
            "| бути | verb | є, був, буде |\n"
            "| хліб | noun | хліба, хлібом |\n"
            "| добрий | adj | добра, добре |\n"
        )
        ctx = _make_ctx(_lexical_sandbox=sandbox)
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "Lexical Sandbox" in prompt
        assert "бути" in prompt
        assert "хліб" in prompt
        assert "добрий" in prompt
        assert "CRITICAL" in prompt  # constraint language

    def test_sandbox_bullet_format_extracted(self):
        """Sandbox in bullet format → lemmas extracted."""
        sandbox = (
            "- **бути** (verb) — є, був, буде\n"
            "- **хліб** (noun) — хліба, хлібом\n"
        )
        ctx = _make_ctx(_lexical_sandbox=sandbox)
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "бути" in prompt
        assert "хліб" in prompt

    def test_empty_sandbox_no_section(self):
        """Empty sandbox → no sandbox section in prompt."""
        ctx = _make_ctx(_lexical_sandbox="")
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "Lexical Sandbox" not in prompt

    def test_tiny_sandbox_no_section(self):
        """Sandbox with <50 chars → treated as empty."""
        ctx = _make_ctx(_lexical_sandbox="short")
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "Lexical Sandbox" not in prompt


# ============================================================================
# Immersion rules
# ============================================================================

class TestImmersionInjection:
    """Verify immersion rules are injected into fix prompts."""

    def test_immersion_rule_injected(self):
        """Non-empty immersion rule → section with structural containment."""
        rule = "Target: 30-55% Ukrainian. English paragraphs, Ukrainian in containers."
        ctx = _make_ctx(immersion_rule=rule)
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "Immersion Rules" in prompt
        assert "30-55%" in prompt
        assert "Structural containment" in prompt

    def test_empty_immersion_no_section(self):
        """Empty immersion rule → no section."""
        ctx = _make_ctx(immersion_rule="")
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "Immersion Rules" not in prompt

    def test_short_immersion_no_section(self):
        """Immersion rule <20 chars → treated as empty."""
        ctx = _make_ctx(immersion_rule="short rule")
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "Immersion Rules" not in prompt

    def test_multiline_immersion_uses_first_line(self):
        """Only the first line of immersion rule used as target."""
        rule = "Target: 30-55% Ukrainian.\nDetailed rules here.\nMore rules."
        ctx = _make_ctx(immersion_rule=rule)
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "30-55%" in prompt
        assert "Detailed rules here" not in prompt


# ============================================================================
# Level constraints
# ============================================================================

class TestLevelConstraintInjection:
    """Verify level constraints are injected into fix prompts."""

    def test_level_constraints_injected(self):
        """Non-empty level constraints → section in prompt."""
        constraints = "No dative case. No instrumental. Max 10 words per Ukrainian sentence."
        ctx = _make_ctx(level_constraints=constraints)
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "Level Constraints" in prompt
        assert "No dative case" in prompt

    def test_empty_constraints_no_section(self):
        """Empty constraints → no section."""
        ctx = _make_ctx(level_constraints="")
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "Level Constraints" not in prompt

    def test_short_constraints_no_section(self):
        """Constraints ≤10 chars → treated as empty."""
        ctx = _make_ctx(level_constraints="short")
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "Level Constraints" not in prompt


# ============================================================================
# Combined: all three sections together
# ============================================================================

class TestCombinedInjection:
    """Verify all three sections coexist in the same prompt."""

    def test_all_three_sections_present(self):
        sandbox = (
            "| Lemma | POS |\n|---|---|\n| бути | verb |\n| хліб | noun |\n"
        )
        rule = "Target: 30-55% Ukrainian. Structural containment."
        constraints = "No dative case. No instrumental case. Max 10 words."
        ctx = _make_ctx(
            _lexical_sandbox=sandbox,
            immersion_rule=rule,
            level_constraints=constraints,
        )
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "Lexical Sandbox" in prompt
        assert "Immersion Rules" in prompt
        assert "Level Constraints" in prompt
        # Verify order: sandbox before immersion before level
        sandbox_pos = prompt.index("Lexical Sandbox")
        immersion_pos = prompt.index("Immersion Rules")
        level_pos = prompt.index("Level Constraints")
        assert sandbox_pos < immersion_pos < level_pos


# ============================================================================
# _ensure_sandbox_loaded
# ============================================================================

class TestEnsureSandboxLoaded:
    """Verify _ensure_sandbox_loaded reads from disk when needed."""

    def test_already_loaded_returns_cached(self, tmp_path):
        from pipeline_v5 import _ensure_sandbox_loaded
        ctx = _StubCtx(orch_dir=tmp_path)
        ctx._lexical_sandbox = "already loaded content"
        result = _ensure_sandbox_loaded(ctx)
        assert result == "already loaded content"

    def test_loads_from_disk(self, tmp_path):
        from pipeline_v5 import _ensure_sandbox_loaded
        sandbox_file = tmp_path / "lexical-sandbox.md"
        sandbox_file.write_text("| Lemma | POS |\n|---|---|\n| слово | noun |\n")
        ctx = _StubCtx(orch_dir=tmp_path)
        ctx._lexical_sandbox = ""
        result = _ensure_sandbox_loaded(ctx)
        assert "слово" in result
        assert ctx._lexical_sandbox == result

    def test_missing_file_returns_empty(self, tmp_path):
        from pipeline_v5 import _ensure_sandbox_loaded
        ctx = _StubCtx(orch_dir=tmp_path)
        ctx._lexical_sandbox = ""
        result = _ensure_sandbox_loaded(ctx)
        assert result == ""
