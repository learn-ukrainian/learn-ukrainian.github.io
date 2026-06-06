from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.phases.plan_contract import build_contract


def _plan(title: str) -> dict:
    return {
        "module": 1,
        "slug": "demo",
        "level": "a1",
        "title": title,
        "word_target": 200,
        "content_outline": [
            {
                "section": "Intro",
                "words": 200,
                "points": ["Teach привіт with a grounded dialogue."],
            }
        ],
        "dialogue_situations": [
            {
                "setting": "classroom",
                "speakers": ["Вчитель", "Учень"],
                "motivation": "basic greeting",
            }
        ],
        "vocabulary_hints": {"required": ["привіт"]},
        "activity_hints": [{"id": "intro-quiz", "type": "quiz", "focus": "intro"}],
    }


def test_build_contract_returns_live_contract_and_excerpts() -> None:
    packet = (
        "### Вікі: pedagogy/a1/demo.md\n\n"
        "## Overview\n\n"
        "Привіт у класі. Вчитель і учень вітаються.\n"
    )

    contract, excerpts = build_contract(
        _plan("Original"),
        packet,
        level="a1",
        slug="demo",
        module_num=1,
    )

    assert contract["module"]["title"] == "Original"
    assert contract["teaching_beats"]["section_order"] == ["Intro"]
    assert excerpts["sections"]["Intro"]


def test_build_contract_reflects_plan_title_changes() -> None:
    first, _ = build_contract(_plan("Before"), "", level="a1", slug="demo", module_num=1)
    second, _ = build_contract(_plan("After"), "", level="a1", slug="demo", module_num=1)

    assert first["module"]["title"] == "Before"
    assert second["module"]["title"] == "After"
