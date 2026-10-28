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
from scripts.curriculum.learner_state.immersion import ImmersionError, LessonBand, compute_lesson_immersion_band


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


@pytest.mark.parametrize(
    "level,position,key,share,module_targets",
    [
        ("a2", 1, "a2-bridge", (75, 100), (2, 5, 5)),
        ("a2", 4, "a2-ramp", (85, 100), (3, 5, 6)),
        ("a2", 8, "a2-m01-20", (85, 100), (3, 6, 8)),
        ("a2", 21, "a2-m21-50", (90, 100), (4, 8, 8)),
        ("a2", 51, "a2-m51-70", (95, 100), (4, 8, 8)),
        ("b1", 1, "b1-core", (100, 100), (0, 0, 0)),
        ("b2", 1, "b2+", (100, 100), (0, 0, 0)),
    ],
)
def test_a2_immersion_payload(level, position, key, share, module_targets):
    """Module minima must not become lesson quotas or relax A2+ immersion (#10132)."""
    payload = compute_immersion_payload(level, position, 1)
    assert payload.band_key == key
    assert payload.advisory_uk_share == share
    assert payload.structural_targets == {}
    assert payload.not_checked == ["lesson_structural_minimums_not_calibrated"]
    assert payload.permitted_languages == {
        "narration": ("uk",),
        "dialogue_line": ("uk",),
        "activity_instruction": ("uk",),
        "activity_item": ("uk",),
        "gloss": ("en",),
        "quote": ("uk",),
        "resource_line": ("en", "uk"),
    }
    band = compute_lesson_immersion_band(level, position, 1)
    assert band.module_structural == dict(
        zip(("min_uk_dialogue_lines", "min_uk_example_sentences", "min_vocab_entries"), module_targets, strict=True)
    )


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
