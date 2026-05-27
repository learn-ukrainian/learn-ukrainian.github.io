"""Tests for writer-prompt-size enforcer (PR-C 2026-05-23)."""

from pathlib import Path

from scripts.audit.check_writer_prompt_size import (
    FIXTURE_MODULES,
    WRITER_PROMPT_CEILING_BYTES,
    render_fixture_writer_prompt,
)


def test_ceiling_is_132kb() -> None:
    """Ceiling is 132KB after 2026-05-27 bump.

    Original PR-C 2026-05-23: 130KB (120KB target + 10KB headroom).
    Bumped 2026-05-27 (Path B / PR #2372): 132KB to accommodate 4 hardening PRs
    (#2366, #2367, #2370, #2371) that added load-bearing #R-* rules. Bumping
    vs trimming the hardening was the choice; the hardening rules are
    load-bearing per PR #2358's empirical calibration.

    The wiki-driven writer pivot (post-2026-05-27 Pt 11) is expected to
    collapse most rules and let the ceiling drop back to 130KB or below.
    """
    assert WRITER_PROMPT_CEILING_BYTES == 132 * 1024


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
