"""Tests for writer-prompt-size enforcer (PR-C 2026-05-23)."""

from pathlib import Path

from scripts.audit.check_writer_prompt_size import (
    FIXTURE_MODULES,
    WRITER_PROMPT_CEILING_BYTES,
    render_fixture_writer_prompt,
)


def test_ceiling_is_135kb() -> None:
    """Ceiling is 135KB after the 2026-05-28 V7.1 charter bump.

    Original PR-C 2026-05-23: 130KB (120KB target + 10KB headroom).
    Bumped 2026-05-27 (Path B / PR #2372): 132KB to accommodate 4 hardening PRs
    (#2366, #2367, #2370, #2371) that added load-bearing #R-* rules.
    Bumped 2026-05-28 (V7.1 Day 1 / PR #2377): 135KB to accommodate the V7.1
    Renderer Charter at the top of linear-write.md + the #R-ACTIVITY-COMPOSITION
    cluster. The charter adds ~3KB; a1/sounds-letters-and-hello was already
    right at the previous 132KB ceiling.

    Aggressive trim (cursor r1: "PR #2260 proved -118 lines viable") is queued
    as a follow-up — see issue #2378. After that lands, the ceiling can drop
    back below 130KB and this test's literal will follow.
    """
    assert WRITER_PROMPT_CEILING_BYTES == 135 * 1024


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
