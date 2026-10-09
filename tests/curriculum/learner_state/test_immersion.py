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

from dataclasses import replace
from pathlib import Path

import pytest

import scripts.config as cfg
from scripts.curriculum.arc.loader import ArcPosition, ArcStaleError, load_arc
from scripts.curriculum.learner_state import codes
from scripts.curriculum.learner_state.immersion import ImmersionError, compute_lesson_immersion_band

pytestmark = pytest.mark.reads_content


@pytest.mark.parametrize(
    ("count", "expected_key"),
    [(0, 'a1-m01-03'), (24, 'a1-m01-03'), (25, 'a1-m04-06'), (59, 'a1-m04-06'), (60, 'a1-m07-14'), (139, 'a1-m07-14'), (140, 'a1-m15-24'), (241, 'a1-m15-24'), (242, 'a1-m25-34'), (399, 'a1-m25-34'), (400, 'a1-m35-54'), (599, 'a1-m35-54'), (600, 'a1-m55+'), (1000, 'a1-m55+')],
)
def test_a1_band_parametrised_seven_knees(count: int, expected_key: str) -> None:
    """A1 band derives from cumulative count using the seven editorial vocabulary thresholds, matching compute_immersion_band."""
    ordinary = load_arc("a1")[1]
    assert ordinary.band_key is None
    band = compute_lesson_immersion_band("a1", arc_position=ordinary.position, lesson_n=1, cumulative_core_count=count)
    assert band.band_key == expected_key
    assert band.source == "ulp_vocab"
    assert codes.LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED in band.not_checked

    assert band.module_structural == {}
    # Byte/value identical to existing config.compute_immersion_band
    config_band = cfg.compute_immersion_band("a1", 1, {"cumulative_vocabulary": count})
    assert band.band_key == config_band["key"]
    assert band.advisory_uk_share == (int(config_band["advisory_pct_min"]), int(config_band["advisory_pct_max"]))


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


def test_unknown_band_key_fails_arc_band_table_missing() -> None:
    """An unknown band_key must fail with arc_band_table_missing, never falling through to top band."""
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
            band_key="nonexistent_band_xyz",
        )
    ]
    with pytest.raises(ImmersionError) as exc_info:
        compute_lesson_immersion_band(
            "a2",
            arc_position=1,
            lesson_n=1,
            arc_loader=lambda _track: synthetic_positions,
        )
    assert exc_info.value.code == codes.ARC_BAND_TABLE_MISSING
    assert "unknown band_key" in exc_info.value.message


def test_a1_fails_closed_when_derivation_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """When USE_ULP_IMMERSION_DERIVATION is False, A1 fails closed with ulp_derivation_disabled."""
    monkeypatch.setattr(cfg, "USE_ULP_IMMERSION_DERIVATION", False)
    with pytest.raises(ImmersionError) as exc_info:
        compute_lesson_immersion_band("a1", arc_position=1, lesson_n=1, cumulative_core_count=100)
    assert exc_info.value.code == codes.ULP_DERIVATION_DISABLED
    assert "USE_ULP_IMMERSION_DERIVATION" in exc_info.value.message


def test_a1_band_source_not_ulp_vocab_when_derivation_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test alias retained for compatibility."""
    test_a1_fails_closed_when_derivation_disabled(monkeypatch)


def test_a1_requires_cumulative_core_count() -> None:
    """For A1, cumulative_core_count is required; passing None or omitting raises cumulative_core_count_missing."""
    with pytest.raises(ImmersionError) as exc_info:
        compute_lesson_immersion_band("a1", arc_position=1, lesson_n=1, cumulative_core_count=None)
    assert exc_info.value.code == codes.CUMULATIVE_CORE_COUNT_MISSING
    assert "cumulative_core_count" in exc_info.value.message

    with pytest.raises(ImmersionError) as exc_info:
        compute_lesson_immersion_band("a1", arc_position=1, lesson_n=1)
    assert exc_info.value.code == codes.CUMULATIVE_CORE_COUNT_MISSING


def test_lesson_band_waiver_carried_to_dict_and_text() -> None:
    band = compute_lesson_immersion_band(
        "a1",
        arc_position=1,
        lesson_n=1,
        cumulative_core_count=100,
        waiver="waived: prior_plans_missing",
    )
    assert band.waiver == "waived: prior_plans_missing"
    assert band.to_dict()["waiver"] == "waived: prior_plans_missing"
    assert "Waiver: waived: prior_plans_missing" in band.render_text()


def test_a2_band_does_not_require_cumulative_core_count() -> None:
    """For A2, cumulative_core_count is optional and not needed."""
    band = compute_lesson_immersion_band("a2", arc_position=1, lesson_n=1)
    assert band.band_key == "a2-bridge"
    assert band.source == "arc_table"


@pytest.mark.parametrize("error_type", [ArcStaleError, ValueError, FileNotFoundError, RuntimeError])
def test_a1_injected_loader_failure_has_named_error(error_type: type[Exception]) -> None:
    error = error_type("arc unavailable")

    def failing_loader(track: str) -> list[ArcPosition]:
        assert track == "a1"
        raise error

    with pytest.raises(ImmersionError) as exc_info:
        compute_lesson_immersion_band("a1", 1, 1, 0, arc_loader=failing_loader)
    assert exc_info.value.code == codes.ARC_BAND_TABLE_MISSING
    assert exc_info.value.message == "failed loading arc for track 'a1': arc unavailable"
    assert exc_info.value.__cause__ is error


@pytest.mark.parametrize("failure", ["stale", "malformed", "missing", "refused"])
def test_a1_real_loader_failure_has_named_error(tmp_path: Path, failure: str) -> None:
    root = Path(__file__).resolve().parents[3]
    kwargs = {}
    expected_type: type[Exception]
    if failure == "stale":
        changed_doc = tmp_path / "changed-arc.md"
        changed_doc.write_bytes((root / "docs/epics/fresh-build-a1-arc.md").read_bytes() + b"\nChanged.\n")
        kwargs["doc_path"] = changed_doc
        expected_type = ArcStaleError
    elif failure == "malformed":
        malformed_arc = tmp_path / "malformed-arc.yaml"
        malformed_arc.write_text("positions: []\n", encoding="utf-8")
        kwargs["arc_path"] = malformed_arc
        expected_type = ValueError
    elif failure == "missing":
        kwargs["arc_path"] = tmp_path / "missing-arc.yaml"
        expected_type = FileNotFoundError
    else:
        kwargs["arc_path"] = root / "curriculum/l2-uk-en/plans/a1/_arc.yaml"
        expected_type = ValueError

    with pytest.raises(expected_type):
        load_arc("a1", **kwargs)
    with pytest.raises(ImmersionError) as exc_info:
        compute_lesson_immersion_band("a1", 1, 1, 0, **kwargs)
    assert exc_info.value.code == codes.ARC_BAND_TABLE_MISSING
    assert isinstance(exc_info.value.__cause__, expected_type)
    assert exc_info.value.message.startswith("failed loading arc for track 'a1': ")


@pytest.mark.parametrize("injected", [False, True])
def test_a1_missing_position_never_selects_vocabulary_band(monkeypatch: pytest.MonkeyPatch, injected: bool) -> None:
    def forbidden_band(*args, **kwargs):
        pytest.fail("missing position must never select a vocabulary band")

    monkeypatch.setattr(cfg, "compute_immersion_band", forbidden_band)
    kwargs = {"arc_loader": lambda _: load_arc("a1")} if injected else {}
    with pytest.raises(ImmersionError) as exc_info:
        compute_lesson_immersion_band("a1", 999, 1, 0, **kwargs)
    assert exc_info.value.code == codes.POSITION_NOT_FOUND
    assert exc_info.value.message == "position 999 not found in arc for a1"


@pytest.mark.parametrize("count", [True, False, -1, 1.5, "0", [], {}])
def test_a1_invalid_count_keeps_named_error(count) -> None:
    with pytest.raises(ImmersionError) as exc_info:
        compute_lesson_immersion_band("a1", 1, 1, count)
    assert exc_info.value.code == codes.CUMULATIVE_CORE_COUNT_INVALID


@pytest.mark.parametrize("count", [0, 100])
def test_a1_only_explicit_orientation_has_no_share(count: int) -> None:
    ordinary = load_arc("a1")[1]
    assert ordinary.band_key is None
    declared = replace(ordinary, position=17, band_key="a1-orientation")
    band = compute_lesson_immersion_band(
        "a1", 17, 2, count, arc_loader=lambda _: [ordinary, declared], waiver="explicit waiver",
    )
    assert band.to_dict() == {
        "band_key": "a1-orientation",
        "advisory_uk_share": None,
        "module_structural": {},
        "source": "arc_table",
        "not_checked": [codes.LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED],
        "waiver": "explicit waiver",
    }
    assert "No advisory share (English orientation)" in band.render_text()
    assert "Waiver: explicit waiver" in band.render_text()
    normal = compute_lesson_immersion_band("a1", ordinary.position, 1, 0, arc_loader=lambda _: [ordinary, declared])
    assert normal.band_key == "a1-m01-03"
    assert normal.advisory_uk_share == (0, 15)
    assert normal.module_structural == {}


def test_a2_real_loader_failure_keeps_named_error(tmp_path: Path) -> None:
    with pytest.raises(ImmersionError) as exc_info:
        compute_lesson_immersion_band("a2", 1, 1, arc_path=tmp_path / "missing.yaml")
    assert exc_info.value.code == codes.ARC_BAND_TABLE_MISSING
    assert isinstance(exc_info.value.__cause__, FileNotFoundError)


def test_a2_missing_position_keeps_named_error() -> None:
    with pytest.raises(ImmersionError) as exc_info:
        compute_lesson_immersion_band("a2", 999, 1)
    assert exc_info.value.code == codes.POSITION_NOT_FOUND
