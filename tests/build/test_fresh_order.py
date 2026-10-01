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


@pytest.mark.parametrize("order", [[0, "1", 2], ["0", "1", "2"]], ids=["mixed", "strings"])
def test_schema_valid_a1_non_integer_order_returns_typed_refusal(order: list) -> None:
    activity = {
        "id": "a1",
        "type": "order",
        "instruction": "Put the steps in order.",
        "items": ["first", "second", "third"],
        "correct_order": order,
    }
    schema = json.loads((SCHEMAS / "activities-a1.schema.json").read_text())
    Draft7Validator(schema).validate([activity])
    row, _ = check_4_activities(
        {"activities": [activity]}, {"activities": [{"id": "a1", "type": "order"}]}, {}, {}, level="a1"
    )
    assert (row["status"], row["code"]) == ("failed", "order_index_coverage")


@pytest.mark.parametrize("level", ["a1", "a2", "b1"])
@pytest.mark.parametrize("index", [False, True, "1", 1.0], ids=["false", "true", "string", "float"])
def test_non_integer_order_index_is_rejected_before_sorting(level: str, index) -> None:
    activity = {"id": "a1", "items": ["first", "second", "third"], "correct_order": [0, index, 2]}
    assert _structural_activity_error(activity, "order", {}) == "order_index_coverage"
    row, _ = check_4_activities(
        {"activities": [activity]}, {"activities": [{"id": "a1", "type": "order"}]}, {}, {}, level=level
    )
    assert (row["status"], row["code"]) == ("failed", "order_index_coverage")


def test_b2_schema_has_no_order_activity() -> None:
    schema = json.loads((SCHEMAS / "activities-b2.schema.json").read_text())
    allowed_types = {
        schema["definitions"][ref["$ref"].rsplit("/", 1)[-1]]["properties"]["type"]["const"]
        for ref in schema["items"]["oneOf"]
    }
    assert "order" not in allowed_types
