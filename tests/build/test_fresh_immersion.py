"""Tests for fresh build engine Part E2 immersion payload (#8414, #8431 §6/§7)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from scripts.build.fresh.immersion import (
    FIELD_ROLES,
    ImmersionPayload,
    compute_immersion_payload,
)
from scripts.curriculum.arc.loader import ArcPosition
from scripts.curriculum.learner_state.immersion import ImmersionError, LessonBand


def synthetic_arc_loader(level: str) -> list[ArcPosition]:
    """Synthetic arc loader for testing A2/B1/B2 without reading live arc files."""
    if level == "a2":
        return [
            ArcPosition(
                position=1,
                slug="a2-mod1",
                est_lessons=4,
                job="Job 1",
                inventory_text=None,
                phase="Phase 1",
                skills_text="Skill",
                skills=["Skill"],
                standard_line_refs=[],
                band_key="a2-bridge",
            ),
            ArcPosition(
                position=4,
                slug="a2-mod4",
                est_lessons=4,
                job="Job 4",
                inventory_text=None,
                phase="Phase 1",
                skills_text="Skill",
                skills=["Skill"],
                standard_line_refs=[],
                band_key="a2-ramp",
            ),
            ArcPosition(
                position=10,
                slug="a2-mod10",
                est_lessons=4,
                job="Job 10",
                inventory_text=None,
                phase="Phase 2",
                skills_text="Skill",
                skills=["Skill"],
                standard_line_refs=[],
                band_key="a2-m01-20",
            ),
        ]
    elif level == "b1":
        return [
            ArcPosition(
                position=1,
                slug="b1-mod1",
                est_lessons=4,
                job="Job 1",
                inventory_text=None,
                phase="Phase 1",
                skills_text="Skill",
                skills=["Skill"],
                standard_line_refs=[],
                band_key="b1-core",
            )
        ]
    elif level == "b2":
        return [
            ArcPosition(
                position=1,
                slug="b2-mod1",
                est_lessons=4,
                job="Job 1",
                inventory_text=None,
                phase="Phase 1",
                skills_text="Skill",
                skills=["Skill"],
                standard_line_refs=[],
                band_key="b2+",
            )
        ]
    return []


def test_a1_immersion_payload_early():
    """Early A1: English narration, dialogue in Ukrainian, all 7 roles present."""
    # Position 1 explicitly declares orientation; position 2 uses ordinary vocabulary bands.
    payload = compute_immersion_payload("a1", arc_position=2, lesson_n=1, cumulative_core_count=10)
    assert isinstance(payload, ImmersionPayload)
    assert payload.band_key == "a1-m01-03"
    assert payload.advisory_uk_share == (0, 15)

    roles = payload.permitted_languages
    for role in FIELD_ROLES:
        assert role in roles

    assert roles["dialogue_line"] == ("uk",)
    assert roles["quote"] == ("uk",)
    assert roles["gloss"] == ("en",)
    assert roles["narration"] == ("en",)
    assert roles["activity_instruction"] == ("en",)
    assert roles["activity_item"] == ("uk", "en")
    assert roles["resource_line"] == ("en", "uk")

    targets = payload.structural_targets
    assert targets == {}


def test_a2_immersion_payload():
    """From A2 on, never allow more English than contract allows (#8431 §6/§7, Finding 6).

    a2-bridge uses easy Ukrainian as default teaching voice (no English body scaffolding).
    """
    p_bridge = compute_immersion_payload("a2", arc_position=1, lesson_n=1, arc_loader=synthetic_arc_loader)
    assert p_bridge.band_key == "a2-bridge"
    assert p_bridge.permitted_languages["narration"] == ("uk",)
    assert p_bridge.permitted_languages["activity_instruction"] == ("uk",)
    assert p_bridge.permitted_languages["activity_item"] == ("uk",)

    p_ramp = compute_immersion_payload("a2", arc_position=4, lesson_n=1, arc_loader=synthetic_arc_loader)
    assert p_ramp.band_key == "a2-ramp"
    assert p_ramp.permitted_languages["narration"] == ("uk",)
    assert p_ramp.permitted_languages["activity_instruction"] == ("uk",)
    assert p_ramp.permitted_languages["activity_item"] == ("uk",)


def test_unsupported_band_key_fails_closed():
    """Where the contract gives no row, fail closed with unsupported_immersion_band (#8431, Finding 6)."""
    with patch("scripts.build.fresh.immersion.compute_lesson_immersion_band") as mock_band:
        mock_band.return_value = LessonBand(
            band_key="nonexistent-band",
            advisory_uk_share=(50, 50),
            module_structural={"min_uk_dialogue_lines": 1, "min_uk_example_sentences": 1, "min_vocab_entries": 1},
            source="arc_table",
            not_checked=[],
        )
        with pytest.raises(ImmersionError) as exc_info:
            compute_immersion_payload("a2", 1, 1)
        assert exc_info.value.code == "unsupported_immersion_band"
