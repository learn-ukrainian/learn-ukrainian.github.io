"""Tests for lesson immersion band and structural minimums (issue #8414).

Verifies:
- A1 band equals compute_immersion_band for the same count, parametrised across the 7 knees
- A2 band equals the arc's band_key for the position
- B1 -> b1-core
- B2 -> b2+
- Fixture arc without band_key fails arc_band_table_missing
- Every call carries the not_checked code (lesson_structural_minimums_not_calibrated)
- Structural minimums carried unchanged
"""

from __future__ import annotations

import pytest

import scripts.config as cfg
from scripts.curriculum.arc.loader import ArcPosition
from scripts.curriculum.learner_state import codes
from scripts.curriculum.learner_state.immersion import ImmersionError, compute_lesson_immersion_band

pytestmark = pytest.mark.reads_content


@pytest.mark.parametrize(
    ("count", "expected_key"),
    [
        (0, "a1-m01-03"),
        (139, "a1-m01-03"),
        (140, "a1-m04-06"),
        (241, "a1-m04-06"),
        (242, "a1-m07-14"),
        (572, "a1-m07-14"),
        (573, "a1-m15-24"),
        (592, "a1-m15-24"),
        (593, "a1-m25-34"),
        (620, "a1-m25-34"),
        (621, "a1-m35-54"),
        (646, "a1-m35-54"),
        (647, "a1-m55+"),
        (1000, "a1-m55+"),
    ],
)
def test_a1_band_parametrised_seven_knees(count: int, expected_key: str) -> None:
    """A1 band derives from cumulative count using the seven ULP knees, matching compute_immersion_band."""
    band = compute_lesson_immersion_band("a1", arc_position=1, lesson_n=1, cumulative_core_count=count)
    assert band.band_key == expected_key
    assert band.source == "ulp_vocab"
    assert codes.LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED in band.not_checked

    # Byte/value identical to existing config.compute_immersion_band
    config_band = cfg.compute_immersion_band("a1", 1, {"cumulative_vocabulary": count})
    assert band.band_key == config_band["key"]
    assert band.advisory_uk_share == (int(config_band["advisory_pct_min"]), int(config_band["advisory_pct_max"]))
    assert band.module_structural["min_uk_dialogue_lines"] == int(config_band["min_uk_dialogue_lines"])
    assert band.module_structural["min_uk_example_sentences"] == int(config_band["min_uk_example_sentences"])
    assert band.module_structural["min_vocab_entries"] == int(config_band["min_vocab_entries"])


def test_a2_band_equals_arc_band_key() -> None:
    """A2 band equals ArcPosition.band_key for the position."""
    # From curriculum/l2-uk-en/lesson-plans/a2/_arc.yaml:
    # pos 1 -> a2-bridge, pos 4 -> a2-ramp, pos 8 -> a2-m01-20
    b1 = compute_lesson_immersion_band("a2", arc_position=1, lesson_n=1, cumulative_core_count=0)
    assert b1.band_key == "a2-bridge"
    assert b1.source == "arc_table"
    assert codes.LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED in b1.not_checked

    b4 = compute_lesson_immersion_band("a2", arc_position=4, lesson_n=1, cumulative_core_count=0)
    assert b4.band_key == "a2-ramp"

    b8 = compute_lesson_immersion_band("a2", arc_position=8, lesson_n=1, cumulative_core_count=0)
    assert b8.band_key == "a2-m01-20"


def test_b1_band_equals_b1_core() -> None:
    """B1 positions map to b1-core from arc."""
    band = compute_lesson_immersion_band("b1", arc_position=1, lesson_n=1, cumulative_core_count=0)
    assert band.band_key == "b1-core"
    assert band.source == "arc_table"
    assert codes.LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED in band.not_checked


def test_b2_band_equals_b2_plus() -> None:
    """B2 positions map to b2+ from arc."""
    band = compute_lesson_immersion_band("b2", arc_position=1, lesson_n=1, cumulative_core_count=0)
    assert band.band_key == "b2+"
    assert band.source == "arc_table"
    assert codes.LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED in band.not_checked


def test_fixture_arc_without_band_key_fails() -> None:
    """A level whose arc has no band_key fails with arc_band_table_missing, never falls back to a module number."""
    synthetic_positions = [
        ArcPosition(
            position=1,
            slug="synth-slug",
            est_lessons=4,
            job="Synthetic job",
            inventory_text=None,
            phase="Phase 1",
            skills_text="L",
            skills=["L"],
            standard_line_refs=[],
            band_key=None,  # missing band_key
        )
    ]

    with pytest.raises(ImmersionError) as exc_info:
        compute_lesson_immersion_band(
            "a2",
            arc_position=1,
            lesson_n=1,
            cumulative_core_count=0,
            arc_loader=lambda _track: synthetic_positions,
        )
    assert exc_info.value.code == codes.ARC_BAND_TABLE_MISSING
    assert "no band_key" in exc_info.value.message


def test_structural_minimums_carried_unchanged() -> None:
    band = compute_lesson_immersion_band("a2", arc_position=1, lesson_n=1, cumulative_core_count=0)
    # Check that module_structural has exactly the three required keys and valid ints
    assert set(band.module_structural.keys()) == {
        "min_uk_dialogue_lines",
        "min_uk_example_sentences",
        "min_vocab_entries",
    }
    for val in band.module_structural.values():
        assert isinstance(val, int)
        assert val >= 0
