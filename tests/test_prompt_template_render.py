from pathlib import Path

import pytest

from scripts.build.prompt_builder import render_prompt

PHASES_DIR = Path(__file__).resolve().parents[1] / "scripts" / "build" / "phases"


@pytest.mark.parametrize("template_path", sorted(PHASES_DIR.rglob("*.md")))
def test_phase_template_renders_without_unknown_tokens(template_path: Path) -> None:
    render_prompt(template_path)
