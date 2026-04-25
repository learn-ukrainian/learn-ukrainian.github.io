from pathlib import Path

import pytest

from scripts.build.prompt_builder import PLACEHOLDERS, render_prompt

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "scripts" / "build" / "phases"


@pytest.mark.parametrize("template", sorted(PROMPTS_DIR.glob("v6-*.md")))
def test_no_unfilled_placeholders(template: Path) -> None:
    rendered = render_prompt(template)
    for placeholder in PLACEHOLDERS:
        assert placeholder not in rendered, (
            f"Template {template.name} still has {placeholder} after render"
        )


def test_north_star_loaded() -> None:
    rendered = render_prompt(PROMPTS_DIR / "v6-write.md")
    assert "WHO — the learner" in rendered
    assert "B1 onwards is uniformly 100 % Ukrainian" in rendered


def test_lesson_contract_loaded() -> None:
    rendered = render_prompt(PROMPTS_DIR / "v6-write.md")
    assert "Tab 3 — Вправи" in rendered
    assert "Deprecated; subsumed by `mark-the-words`" in rendered
