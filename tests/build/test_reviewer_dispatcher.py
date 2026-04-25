"""Tests for per-dim reviewer dispatcher hardening (#1550 unit 1).

Two reviewer-side bugs surfaced on a1/1:
1. Factual dim flagged stress marks added by the deterministic annotator
   AFTER review — invalid findings dropped score 8.2.
2. Dialogue dim held A1 M1-M3 to advanced-richness standards and scored
   7.0 on appropriate beginner greetings — a calibration miss, not a
   content failure.

These tests pin the fix:
- Stress marks (U+0301 combining acute) are stripped from reviewer prose
  before placeholder substitution.
- `{learner_level}`, `{module_index}`, `{module_total}` substitute in
  every dim prompt template.
- The Dialogue prompt carries a `<pedagogical-stage>` block that
  references the level.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

WORKTREE_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = WORKTREE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

v6_build = importlib.import_module("build.v6_build")

PROMPT_DIR = SCRIPTS_DIR / "build" / "phases" / "v6-review"

STRESS = "́"


def test_prepare_reviewer_prose_strips_combining_acute():
    """Stress marks must be removed before the prose reaches the reviewer."""
    raw = "Приві" + STRESS + "т! Я Ма" + STRESS + "рко."
    cleaned = v6_build._prepare_reviewer_prose(raw)
    assert STRESS not in cleaned
    assert cleaned == "Привіт! Я Марко."


def test_prepare_reviewer_prose_passthrough_when_no_stress():
    """Plain Ukrainian without stress is returned unchanged."""
    raw = "Як тебе звати?"
    assert v6_build._prepare_reviewer_prose(raw) == raw


def test_resolve_module_total_returns_positive_count_for_a1():
    """Curriculum manifest is the source of truth for `{module_total}`."""
    total = v6_build._resolve_module_total("a1")
    assert total > 0


def test_level_placeholders_substitute_into_dim_prompt():
    """`{learner_level}`, `{module_index}`, `{module_total}` must be
    substitutable across every dim template."""
    replacements = {
        "{learner_level}": "A1",
        "{module_index}": "2",
        "{module_total}": "55",
    }
    for path in sorted(PROMPT_DIR.glob("v6-review-*.md")):
        text = path.read_text("utf-8")
        for key in replacements:
            assert key in text, f"missing placeholder {key} in {path.name}"
        for key, value in replacements.items():
            text = text.replace(key, value)
        for key in replacements:
            assert key not in text, f"residual placeholder {key} in {path.name}"
        assert "Learner level: A1" in text, f"module-context not bound in {path.name}"
        assert "Module index: 2 of 55" in text, f"module-context not bound in {path.name}"


def test_dialogue_prompt_carries_pedagogical_stage_block():
    """The dialogue dim alone gets the pedagogical-stage calibration block,
    and the block resolves to the learner level after substitution."""
    text = (PROMPT_DIR / "v6-review-dialogue.md").read_text("utf-8")
    assert "<pedagogical-stage>" in text
    assert "</pedagogical-stage>" in text
    assert "M1–M3" in text
    bound = text.replace("{learner_level}", "A1")
    assert "For A1 M1–M3" in bound
    assert "For A1 M4 and later" in bound


def test_factual_prompt_carries_factual_scope_block():
    """The factual dim alone gets the factual-scope block carving
    stress / IPA / activity wording out of factual scope."""
    text = (PROMPT_DIR / "v6-review-factual.md").read_text("utf-8")
    assert "<factual-scope>" in text
    assert "</factual-scope>" in text
    assert "Stress marks" in text
    assert "Pronunciation IPA notation (Language dim)" in text


def test_all_dim_prompts_carry_stress_marks_block():
    """The defensive stress-marks rule must be present in every dim prompt."""
    for path in sorted(PROMPT_DIR.glob("v6-review-*.md")):
        text = path.read_text("utf-8")
        assert "<stress-marks>" in text, f"missing <stress-marks> in {path.name}"
        assert "</stress-marks>" in text, f"missing </stress-marks> in {path.name}"
        assert "U+0301" in text, f"missing U+0301 reference in {path.name}"
