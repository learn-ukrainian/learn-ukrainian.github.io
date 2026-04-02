"""Tests for #813: sandbox/immersion/level-constraint injection into fix prompts."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

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
# Sandbox extraction (removed in #820 — sandbox phase deprecated)
# ============================================================================

class TestSandboxInjection:
    """Verify sandbox section is absent now that sandbox is removed (#820)."""

    def test_empty_sandbox_no_section(self):
        """Empty sandbox → no sandbox section in prompt."""
        ctx = _make_ctx(_lexical_sandbox="")
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "Lexical Sandbox" not in prompt

    def test_no_sandbox_attr_no_section(self):
        """Missing _lexical_sandbox attr → no sandbox section in prompt."""
        ctx = _make_ctx()
        if hasattr(ctx, "_lexical_sandbox"):
            ctx._lexical_sandbox = ""
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
    """Verify immersion + level constraint sections coexist in the same prompt."""

    def test_immersion_and_level_sections_present(self):
        rule = "Target: 30-55% Ukrainian. Structural containment."
        constraints = "No dative case. No instrumental case. Max 10 words."
        ctx = _make_ctx(
            _lexical_sandbox="",  # sandbox removed in #820
            immersion_rule=rule,
            level_constraints=constraints,
        )
        prompt = _build_fix_prompt(ctx, MINIMAL_AUDIT, content_only=True)
        assert "Lexical Sandbox" not in prompt  # sandbox removed
        assert "Immersion Rules" in prompt
        assert "Level Constraints" in prompt
        # Verify order: immersion before level
        immersion_pos = prompt.index("Immersion Rules")
        level_pos = prompt.index("Level Constraints")
        assert immersion_pos < level_pos


# _ensure_sandbox_loaded removed in #820 — sandbox phase deprecated
