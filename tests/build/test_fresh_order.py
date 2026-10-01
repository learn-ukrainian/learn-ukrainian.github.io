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


@pytest.mark.parametrize("level", ["a1", "a2", "b1"])
def test_order_string_items_pass_full_draft_and_constraints(level):
    from scripts.build.fresh.draft_schema import validate_draft
    from tests.build.test_fresh_draft_schema import load_fixture

    draft, _ = load_fixture(level)
    # The integration case has all 33 letters; strings are schema-owned items.
    items = list("АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ")
    draft["activities"] = [
        {
            "id": "a99",
            "instruction": "Order the alphabet.",
            "items": items,
            "correct_order": list(range(33)),
            "explanation": "Follow the alphabet.",
        }
    ]
    if level != "a1":
        draft["activities"][0].pop("explanation")
    draft["steps"] = [{"id": "s1", "blocks": [{"kind": "activity", "ref": "a99"}]}]
    draft.pop("dialogue", None)
    draft["consolidation"] = {"activities": []}
    assert validate_draft(draft, level, activity_types={"a99": "order"}) == []
    for malformed in ("", 12, {"text": "broken"}):
        draft["activities"][0]["items"][0] = malformed
        assert validate_draft(draft, level, activity_types={"a99": "order"})


@pytest.mark.parametrize("level", ["a1", "a2", "b1"])
@pytest.mark.parametrize("order", [[1, 0], [0, 0], [0, "1"]])
def test_schema_valid_order_key_keeps_semantic_gate(level, order):
    from scripts.build.fresh.draft_schema import validate_draft
    from tests.build.test_fresh_draft_schema import load_fixture

    draft, _ = load_fixture(level)
    draft["activities"] = [
        {
            "id": "a99",
            "instruction": "Order.",
            "items": ["first", "second"],
            "correct_order": order,
            "explanation": "Follow the sequence.",
        }
    ]
    if level != "a1":
        draft["activities"][0].pop("explanation")
    draft["steps"] = [{"id": "s1", "blocks": [{"kind": "activity", "ref": "a99"}]}]
    draft.pop("dialogue", None)
    draft["consolidation"] = {"activities": []}
    errors = validate_draft(draft, level, activity_types={"a99": "order"})
    # A2/B1 schemas require integers. A1 permits strings, but check 4 refuses them.
    if level == "a1" or all(type(i) is int for i in order):
        assert errors == []
    else:
        assert errors
    row, _ = check_4_activities(draft, {"activities": [{"id": "a99", "type": "order"}]}, {}, {}, level=level)
    assert row["status"] == ("passed" if order == [1, 0] else "failed")
