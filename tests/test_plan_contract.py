"""Tests for contract generation and wiki compression."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.phases.plan_contract import build_contract
from build.v6_build import _build_wiki_packet


@pytest.mark.parametrize(
    ("level", "slug"),
    [
        ("a1", "sounds-letters-and-hello"),
        ("a2", "a2-bridge"),
        ("b1", "verb-formation-suffixes"),
    ],
)
def test_real_plan_and_wiki_pairs_produce_contract(level: str, slug: str) -> None:
    plan_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / level / f"{slug}.yaml"
    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    packet = _build_wiki_packet(level, slug)

    contract, excerpts = build_contract(
        plan,
        packet,
        level=level,
        slug=slug,
        module_num=int(plan["sequence"]),
    )

    assert contract["module"]["slug"] == slug
    assert contract["teaching_beats"]["section_order"]
    assert "dialogue_acts" in contract  # may be [] for phonetics/skills modules
    assert contract["activity_obligations"]
    assert contract["section_word_budgets"]
    assert excerpts["sections"]
    assert excerpts["factual_anchors"]

    first_section = contract["teaching_beats"]["sections"][0]
    assert first_section["factual_anchors"]
    assert first_section["word_budget"]["min"] <= first_section["word_budget"]["target"]


def test_contract_builder_fails_fast_without_required_plan_fields() -> None:
    # content_outline is required
    with pytest.raises(Exception, match="content_outline"):
        build_contract(
            {
                "dialogue_situations": [],
                "activity_hints": [{"id": "quiz", "type": "quiz", "focus": "x"}],
                "word_target": 100,
            },
            "",
            level="a1",
            slug="broken",
            module_num=1,
        )


def test_contract_builder_accepts_plan_without_dialogue_situations() -> None:
    """Phonetics/skills modules legitimately have no dialogue situations.
    The contract should produce dialogue_acts: [] rather than failing.
    """
    contract, _ = build_contract(
        {
            "content_outline": [{"section": "Syllables", "words": 200, "points": ["Count vowels."]}],
            "activity_hints": [{"id": "quiz", "type": "quiz", "focus": "syllable count"}],
            "word_target": 200,
        },
        "",
        level="a1",
        slug="reading-ukrainian",
        module_num=2,
    )
    assert contract["dialogue_acts"] == []
    assert contract["module"]["slug"] == "reading-ukrainian"

