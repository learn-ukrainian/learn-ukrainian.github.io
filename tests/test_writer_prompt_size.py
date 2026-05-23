"""Tests for writer-prompt-size enforcer (PR-C 2026-05-23)."""

from pathlib import Path

from scripts.audit.check_writer_prompt_size import (
    FIXTURE_MODULES,
    WRITER_PROMPT_CEILING_BYTES,
    render_fixture_writer_prompt,
)


def test_ceiling_is_130kb() -> None:
    """Per PR-C 2026-05-23, ceiling is 130KB (120KB target + 10KB headroom)."""
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
