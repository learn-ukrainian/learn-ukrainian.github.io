"""Tests for fresh build engine Part E2 immersion payload (#8414, #8431 §6/§7)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from scripts.build.fresh import immersion as fresh_immersion
from scripts.build.fresh import prompt as fresh_prompt
from scripts.build.fresh.immersion import (
    FIELD_ROLES,
    ImmersionPayload,
    compute_immersion_payload,
    get_immersion_table,
    load_immersion_table,
)
from scripts.config import IMMERSION_POLICIES
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
    payload = compute_immersion_payload("a1", arc_position=1, lesson_n=1, cumulative_core_count=10)
    assert isinstance(payload, ImmersionPayload)
    assert payload.band_key == "a1-m01-03"
    assert payload.advisory_uk_share == (40, 55)

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
    assert "min_uk_dialogue_lines" in targets
    assert "min_uk_example_sentences" in targets
    assert "min_vocab_entries" in targets


def test_a1_immersion_payload_late_band():
    """A1 late band (a1-m35-54 and a1-m55+): bilingual narration and instructions per contract table."""
    table = get_immersion_table()
    assert "a1-m35-54" in table
    assert table["a1-m35-54"]["roles"]["narration"] == ["en", "uk"]
    assert table["a1-m35-54"]["roles"]["activity_instruction"] == ["en", "uk"]

    assert "a1-m55+" in table
    assert table["a1-m55+"]["roles"]["narration"] == ["en", "uk"]
    assert table["a1-m55+"]["roles"]["activity_instruction"] == ["en", "uk"]


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


def test_b1_immersion_payload():
    """B1 onward is full immersion for narration and activities."""
    payload = compute_immersion_payload("b1", arc_position=1, lesson_n=1, arc_loader=synthetic_arc_loader)
    assert payload.permitted_languages["narration"] == ("uk",)
    assert payload.permitted_languages["activity_instruction"] == ("uk",)
    assert payload.permitted_languages["activity_item"] == ("uk",)
    assert payload.permitted_languages["dialogue_line"] == ("uk",)
    assert payload.permitted_languages["quote"] == ("uk",)
    assert payload.permitted_languages["gloss"] == ("en",)


ALL_CONFIG_BAND_KEYS = [entry["key"] for entries in IMMERSION_POLICIES.values() for entry in entries]


@pytest.mark.parametrize("band_key", ALL_CONFIG_BAND_KEYS)
def test_all_contract_bands_tied_to_table_rows(band_key: str):
    """Test per band key tying it to its contract citation and role mapping (#8431 §6/§7, Finding 6)."""
    table = load_immersion_table()
    assert set(table.keys()) == set(ALL_CONFIG_BAND_KEYS), "Table keys do not match config keys"
    assert band_key in table, f"Band key {band_key} missing from immersion_table.yaml"
    row = table[band_key]
    assert "contract_citation" in row, f"Band {band_key} missing contract_citation"
    assert "scripts/config.py IMMERSION_POLICIES" in row["contract_citation"]

    roles = row.get("roles", {})
    for field_role in FIELD_ROLES:
        assert field_role in roles, f"Band {band_key} missing role {field_role}"
        assert isinstance(roles[field_role], list)
        assert len(roles[field_role]) > 0


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


def test_payload_pin_consumed_by_both():
    """Payload pin: writer prompt and E3 gate consume the exact same compute_immersion_payload function.

    # E3: The gate-side half of this pin belongs to E3's test suite once the E3 gate is implemented.
    """
    # 1. Verify compute_immersion_payload reads compute_lesson_immersion_band
    with patch("scripts.build.fresh.immersion.compute_lesson_immersion_band") as mock_band:
        mock_band.return_value = LessonBand(
            band_key="a1-m01-03",
            advisory_uk_share=(20, 40),
            module_structural={"min_uk_dialogue_lines": 5, "min_uk_example_sentences": 8, "min_vocab_entries": 12},
            source="ulp_vocab",
            not_checked=["lesson_structural_minimums_not_calibrated"],
        )
        res = compute_immersion_payload("a1", 1, 1, cumulative_core_count=10)
        assert mock_band.called
        assert res.band_key == "a1-m01-03"

    # 2. Verify prompt module imports compute_immersion_payload from immersion.py
    assert fresh_prompt.compute_immersion_payload is fresh_immersion.compute_immersion_payload

    # 3. Verify to_dict serializability
    d = res.to_dict()
    assert d["band_key"] == "a1-m01-03"
    assert d["advisory_uk_share"] == [20, 40]
    assert d["structural_targets"]["min_uk_dialogue_lines"] == 5
