"""Tests for writer-prompt-size enforcer (PR-C 2026-05-23)."""

from pathlib import Path

from scripts.audit.check_writer_prompt_size import (
    FIXTURE_MODULES,
    WRITER_PROMPT_CEILING_BYTES,
    render_fixture_writer_prompt,
)
from scripts.build import linear_pipeline


def test_ceiling_is_130kb() -> None:
    """Ceiling is back to 130KB after the 2026-06-07 #2378 prompt trim.

    Original PR-C 2026-05-23: 130KB (120KB target + 10KB headroom).
    Bumped 2026-05-27 (Path B / PR #2372): 132KB to accommodate 4 hardening PRs
    (#2366, #2367, #2370, #2371) that added load-bearing #R-* rules.
    Bumped 2026-05-28 (V7.1 Day 1 / PR #2377): 135KB to accommodate the V7.1
    Renderer Charter at the top of linear-write.md + the #R-ACTIVITY-COMPOSITION
    cluster. The charter adds ~3KB; a1/sounds-letters-and-hello was already
    right at the previous 132KB ceiling.

    Issue #2378 trims repeated linear-writer instructions while preserving
    load-bearing rule anchors, so the enforced ceiling returns to 130KB.
    """
    assert WRITER_PROMPT_CEILING_BYTES == 130 * 1024


def test_fixture_modules_includes_a1_my_morning() -> None:
    """The A1 anchor module is the canonical fixture."""
    assert ("a1", "my-morning") in FIXTURE_MODULES


def test_fixture_module_path_resolves() -> None:
    project_root = Path(__file__).resolve().parents[1]
    for level, slug in FIXTURE_MODULES:
        expected = project_root / "curriculum" / "l2-uk-en" / level / slug
        assert expected.exists(), f"Fixture path {expected} should exist"


def test_fixture_writer_prompts_under_ceiling() -> None:
    for level, slug in FIXTURE_MODULES:
        rendered = render_fixture_writer_prompt(level, slug)
        assert len(rendered.encode("utf-8")) <= WRITER_PROMPT_CEILING_BYTES


def test_prompt_plan_content_omits_review_history_metadata() -> None:
    plan = {
        "module": "a1-999",
        "title": "Letters",
        "content_outline": [{"section": "Core", "words": 100, "points": ["Teach letters."]}],
        "activity_hints": [{"type": "quiz", "focus": "letters"}],
        "references": [{"title": "Reference"}],
        "review_notes": "Long audit narrative that belongs in the source plan only.",
        "plan_fixes": [{"version": "1.0.1", "changes": ["historical fix"]}],
        "changelog": [{"version": "1.0.0", "changes": ["historical note"]}],
    }

    rendered = linear_pipeline._prompt_plan_content(plan, "raw plan")

    assert "content_outline:" in rendered
    assert "activity_hints:" in rendered
    assert "references:" in rendered
    assert "review_notes" not in rendered
    assert "plan_fixes" not in rendered
    assert "changelog" not in rendered
