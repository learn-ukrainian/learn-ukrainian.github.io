"""Per-level per-dimension LLM QG threshold schema tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from common.thresholds import (
    LEVEL_THRESHOLDS,
    QG_DIMS,
    REVIEW_REJECT_FLOOR,
    DimensionFloor,
    LevelThresholds,
    aggregate_review,
)

EXPECTED_PASS_FLOORS = {
    "A1": {
        "pedagogical": 9.0,
        "naturalness": 9.0,
        "decolonization": 9.0,
        "engagement": 8.0,
        "tone": 8.0,
    },
    "A2": {
        "pedagogical": 9.0,
        "naturalness": 9.0,
        "decolonization": 9.0,
        "engagement": 8.0,
        "tone": 8.0,
    },
    "B1": {
        "pedagogical": 9.0,
        "naturalness": 9.0,
        "decolonization": 9.0,
        "engagement": 8.0,
        "tone": 8.0,
    },
    "B2": {
        "pedagogical": 8.0,
        "naturalness": 8.0,
        "decolonization": 9.0,
        "engagement": 8.0,
        "tone": 8.0,
    },
    "C1": {
        "pedagogical": 8.0,
        "naturalness": 8.0,
        "decolonization": 9.0,
        "engagement": 8.0,
        "tone": 8.0,
    },
    "C2": {
        "pedagogical": 8.0,
        "naturalness": 8.0,
        "decolonization": 9.0,
        "engagement": 8.0,
        "tone": 8.0,
    },
}


def _valid_floors() -> dict[str, DimensionFloor]:
    return {
        dim: DimensionFloor(pass_floor=8.0, reject_floor=REVIEW_REJECT_FLOOR)
        for dim in QG_DIMS
    }


def test_level_thresholds_rejects_missing_dim_keys() -> None:
    floors = _valid_floors()
    floors.pop("tone")

    with pytest.raises(ValueError, match="review_floors must cover exactly QG_DIMS"):
        LevelThresholds(target_words=1200, review_floors=floors)


def test_level_thresholds_rejects_extra_dim_keys() -> None:
    floors = _valid_floors()
    floors["language"] = DimensionFloor(pass_floor=8.0, reject_floor=REVIEW_REJECT_FLOOR)

    with pytest.raises(ValueError, match="review_floors must cover exactly QG_DIMS"):
        LevelThresholds(target_words=1200, review_floors=floors)


def test_dimension_floor_rejects_reject_above_pass() -> None:
    with pytest.raises(ValueError, match="DimensionFloor invariant"):
        DimensionFloor(pass_floor=6.0, reject_floor=7.0)


def test_aggregate_review_passes_when_all_dims_clear_pass_floors() -> None:
    verdict = aggregate_review(
        {
            "pedagogical": 9.0,
            "naturalness": 9.0,
            "decolonization": 9.0,
            "engagement": 8.0,
            "tone": 8.0,
        },
        "A1",
    )

    assert verdict.verdict == "PASS"
    assert verdict.failing_dims == ()
    assert verdict.rejected_dims == ()
    assert verdict.min_score == 8.0
    assert verdict.min_dim == "engagement"


def test_aggregate_review_revises_when_one_dim_between_reject_and_pass() -> None:
    verdict = aggregate_review(
        {
            "pedagogical": 9.0,
            "naturalness": 8.5,
            "decolonization": 9.0,
            "engagement": 8.0,
            "tone": 8.0,
        },
        "A1",
    )

    assert verdict.verdict == "REVISE"
    assert verdict.failing_dims == ("naturalness",)
    assert verdict.rejected_dims == ()
    assert verdict.min_score == 8.0
    assert verdict.min_dim == "engagement"


def test_aggregate_review_rejects_when_any_dim_below_reject_floor() -> None:
    verdict = aggregate_review(
        {
            "pedagogical": 10.0,
            "naturalness": 10.0,
            "decolonization": 5.9,
            "engagement": 10.0,
            "tone": 10.0,
        },
        "B2",
    )

    assert verdict.verdict == "REJECT"
    assert verdict.failing_dims == ("decolonization",)
    assert verdict.rejected_dims == ("decolonization",)
    assert verdict.min_score == 5.9
    assert verdict.min_dim == "decolonization"


def test_aggregate_review_tolerates_extra_legacy_dims() -> None:
    verdict = aggregate_review(
        {
            "pedagogical": 8.0,
            "naturalness": 8.0,
            "decolonization": 9.0,
            "engagement": 8.0,
            "tone": 8.0,
            "language": 0.0,
        },
        "B2",
    )

    assert verdict.verdict == "PASS"
    assert verdict.failing_dims == ()
    assert verdict.rejected_dims == ()
    assert verdict.min_score == 8.0
    assert verdict.min_dim == "pedagogical"


@pytest.mark.parametrize("scores", [{}, {"language": 10.0}])
def test_aggregate_review_raises_when_no_qg_dims_are_scored(
    scores: dict[str, float],
) -> None:
    with pytest.raises(ValueError, match="No QG dims found in scores"):
        aggregate_review(scores, "A1")


def test_per_level_default_floor_table_matches_design() -> None:
    assert set(LEVEL_THRESHOLDS) == set(EXPECTED_PASS_FLOORS)
    for level, expected in EXPECTED_PASS_FLOORS.items():
        thresholds = LEVEL_THRESHOLDS[level]
        assert set(thresholds.review_floors) == set(QG_DIMS)
        for dim, pass_floor in expected.items():
            floor = thresholds.review_floors[dim]
            assert floor.pass_floor == pass_floor
            assert floor.reject_floor == REVIEW_REJECT_FLOOR
        assert thresholds.naturalness_min == expected["naturalness"]
