"""E1.2 of the create-path engine (#8431 r3 §1c; absorbs #8214): `explanation` on every item, `error_ref` on error items."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

REPO = Path(__file__).resolve().parents[2]
LEVELS = ("a1", "a2", "b1", "b2")
ERROR_REF_PATTERN = "^E-[0-9]{3,}$"


def level_schema(level: str) -> dict:
    return json.loads((REPO / "schemas" / f"activities-{level}.schema.json").read_text(encoding="utf-8"))


def item_definitions(level: str):
    """Every `<type>-<level>` definition whose `items[]` elements are objects — the item definitions."""
    for name, definition in level_schema(level)["definitions"].items():
        items = definition.get("properties", {}).get("items")
        if isinstance(items, dict) and isinstance(items.get("items"), dict) and items["items"].get("type") == "object":
            yield name, items["items"]


@pytest.mark.parametrize("level", LEVELS)
def test_every_item_definition_requires_a_non_empty_explanation(level: str) -> None:
    seen = 0
    for name, item in item_definitions(level):
        seen += 1
        assert "explanation" in item["required"], name
        assert item["properties"]["explanation"]["type"] == "string", name
        assert item["properties"]["explanation"].get("minLength", 0) >= 1, name
    assert seen >= 7, level


@pytest.mark.parametrize("level", LEVELS)
def test_error_correction_items_require_error_ref(level: str) -> None:
    item = dict(item_definitions(level))[f"error-correction-{level}"]
    assert "error_ref" in item["required"]
    assert item["properties"]["error_ref"] == {
        "type": "string",
        "pattern": ERROR_REF_PATTERN,
        "description": item["properties"]["error_ref"]["description"],
    }


def _validator(level: str, type_name: str) -> Draft7Validator:
    schema = level_schema(level)
    return Draft7Validator({**schema, "type": "object", "items": None, "$ref": f"#/definitions/{type_name}-{level}"})


def _quiz(level: str, item_count: int, **item_extra) -> dict:
    schema = level_schema(level)["definitions"][f"quiz-{level}"]
    if level == "b1":  # b1 quiz items: string options and a 0-based `correct` index
        base = {"question": "Q?", "options": ["a", "b", "c", "d"], "correct": 0, **item_extra}
    else:
        base = {"question": "Q?", "options": [{"text": "a", "correct": True}, {"text": "b", "correct": False}, {"text": "c", "correct": False}, {"text": "d", "correct": False}], **item_extra}
    activity = {"type": "quiz", "title": "T", "instruction": "Choose.", "items": [dict(base) for _ in range(item_count)]}
    if "id" in schema.get("required", []):
        activity["id"] = "q1"
    return activity


@pytest.mark.parametrize("level", LEVELS)
def test_quiz_fixture_without_explanation_fails_and_with_passes(level: str) -> None:
    validator = _validator(level, "quiz")
    count = level_schema(level)["definitions"][f"quiz-{level}"]["properties"]["items"].get("minItems", 1)
    assert any("explanation" in e.message for e in validator.iter_errors(_quiz(level, count)))
    assert any("non-empty" in e.message or "too short" in e.message for e in validator.iter_errors(_quiz(level, count, explanation="")))
    assert list(validator.iter_errors(_quiz(level, count, explanation="because"))) == []


@pytest.mark.parametrize("level", LEVELS)
def test_error_correction_fixture_needs_error_ref(level: str) -> None:
    validator = _validator(level, "error-correction")
    definition = level_schema(level)["definitions"][f"error-correction-{level}"]
    count = definition["properties"]["items"].get("minItems", 1)
    item = {"sentence": "s", "error": "e", "correction": "c", "explanation": "x"}
    if definition["properties"]["items"]["items"]["properties"]["options"].get("minItems", 0) >= 4 and level == "b2":
        item["options"] = ["a", "b", "c", "d"]
    activity = {"type": "error-correction", "title": "T", "instruction": "Fix.", "items": [dict(item) for _ in range(count)]}
    assert any("error_ref" in e.message for e in validator.iter_errors(activity))
    for it in activity["items"]:
        it["error_ref"] = "E-12"
    assert any("E-12" in e.message for e in validator.iter_errors(activity))
    for it in activity["items"]:
        it["error_ref"] = "E-012"
    assert list(validator.iter_errors(activity)) == []
