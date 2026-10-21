"""Order answer keys are checked independently of level and choice routing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from scripts.build.fresh.runner import _structural_activity_error, check_4_activities

SCHEMAS = Path(__file__).resolve().parents[2] / "schemas"


@pytest.mark.parametrize("level", ["a1", "a2", "b1"])
@pytest.mark.parametrize(
    ("order", "expected"),
    [
        ([2, 0, 1], "passed"),
        ([0, 0, 1], "failed"),
        ([0, 1], "failed"),
        ([0, 1, 3], "failed"),
        ([0, 1, 2, 3], "failed"),
    ],
    ids=["permutation", "duplicate", "missing", "out-of-range", "extra"],
)
def test_order_answer_key_at_every_supported_level(level: str, order: list[int], expected: str) -> None:
    activity = {
        "id": "a1",
        "type": "order",
        "instruction": "Put the steps in order.",
        "items": ["first", "second", "third"],
        "correct_order": order,
    }
    schema = json.loads((SCHEMAS / f"activities-{level}.schema.json").read_text())
    Draft7Validator(schema).validate([activity])
    row, _ = check_4_activities(
        {"activities": [activity]}, {"activities": [{"id": "a1", "type": "order"}]}, {}, {}, level=level
    )
    assert row["status"] == expected, row
    if expected == "failed":
        assert row["code"] == "order_index_coverage"
        assert row["activity"] == "a1"


@pytest.mark.parametrize("level", ["a1", "a2", "b1"])
@pytest.mark.parametrize("index", [False, True, "1", 1.0], ids=["false", "true", "string", "float"])
def test_non_integer_order_index_is_rejected_before_sorting(level: str, index) -> None:
    activity = {"id": "a1", "items": ["first", "second", "third"], "correct_order": [0, index, 2]}
    assert _structural_activity_error(activity, "order", {}) == "order_index_coverage"
    row, _ = check_4_activities(
        {"activities": [activity]}, {"activities": [{"id": "a1", "type": "order"}]}, {}, {}, level=level
    )
    assert (row["status"], row["code"]) == ("failed", "order_index_coverage")
