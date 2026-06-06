"""Tests for module archetype contract resolution."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline.module_archetypes import format_module_archetype, resolve_module_archetype


def test_a1_m1_is_zero_script_onboarding():
    contract = resolve_module_archetype("a1", 1)

    assert contract["id"] == "a1-zero-script-onboarding"
    assert contract["must_introduce_before_use"] is True
    assert "zero Cyrillic" in " ".join(contract["learner_assumptions"])
    assert "no internal wiki links" in contract["review_gates"]


def test_a1_early_modules_have_distinct_archetypes():
    assert resolve_module_archetype("a1", 2)["id"] == "a1-script-building"
    assert resolve_module_archetype("a1", 5)["id"] == "a1-first-contact-survival"
    assert resolve_module_archetype("a1", 8)["id"] == "a1-grammar-first-contact"
    assert resolve_module_archetype("a1", 25)["id"] == "a1-a2-expansion-ramp"


def test_b1_core_is_ukrainian_body_with_vocab_carveout():
    contract = resolve_module_archetype("b1", 44)

    assert contract["id"] == "b1-plus-core"
    assert "Ukrainian-only body" in contract["teaching_language"]
    assert "100 percent Ukrainian outside Vocabulary" in contract["review_gates"]


def test_seminar_tracks_use_source_analysis_archetype():
    contract = resolve_module_archetype("hist", 12)

    assert contract["id"] == "seminar-source-analysis"
    assert "source-evaluation" in contract["activity_families"]
    assert "critical-analysis" in contract["activity_families"]
    assert "seminar activity family" in contract["review_gates"]


def test_folk_uses_experiential_archetype():
    contract = resolve_module_archetype("folk", 4)

    assert contract["id"] == "folk-experiential"
    assert "#40 Aural Genre-ID" in contract["activity_families"]
    assert "#45 Performance" in contract["activity_families"]
    assert any("audio-block" in block for block in contract["lesson_blocks"])
    assert any("myth-box" in block for block in contract["lesson_blocks"])


def test_other_seminar_tracks_remain_source_analysis():
    seminar_tracks = ("bio", "hist", "istorio", "oes", "ruth", "lit", "lit-drama")

    for track in seminar_tracks:
        assert resolve_module_archetype(track, 1)["id"] == "seminar-source-analysis"


def test_format_module_archetype_is_prompt_ready():
    text = format_module_archetype(resolve_module_archetype("a1", 1))

    assert "MODULE ARCHETYPE: a1-zero-script-onboarding" in text
    assert "Product tabs: Lesson, Workbook, Vocabulary, Resources" in text
    assert "Current Starlight tabs: Lesson, Vocabulary, Activities, Resources" in text
    assert "Allowed activity families:" in text


def test_format_folk_archetype_includes_lesson_blocks():
    text = format_module_archetype(resolve_module_archetype("folk", 1))

    assert "MODULE ARCHETYPE: folk-experiential" in text
    assert "Required lesson blocks:" in text
    assert "audio-block" in text
    assert "symbolic-decode" in text
    assert "high-culture bridge" in text
    assert "myth-box" in text
