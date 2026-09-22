"""Fresh-build constraints for fill-in and true-false (R-19, WP 23)."""

from __future__ import annotations

import copy

from jsonschema import Draft7Validator

from scripts.build.fresh.draft_schema import (
    FRESH_CONSTRAINTS_META,
    activity_payload_schema,
    load_fresh_constraints,
    validate_draft,
)
from scripts.build.fresh.gen_draft_schemas import SCHEMAS_DIR
from tests.build.test_fresh_draft_schema import load_fixture


def _item(draft: dict, activity_id: str) -> dict:
    activity = next(candidate for candidate in draft["activities"] if candidate["id"] == activity_id)
    return activity["items"][0]


def _reasons(draft: dict, level: str, types: dict[str, str]) -> list[str]:
    return [error.reason for error in validate_draft(draft, level, activity_types=types) if error.check == "activity_fresh_constraints"]


def test_constraints_file_loads_once_and_matches_its_meta_schema() -> None:
    load_fresh_constraints.cache_clear()
    loaded = load_fresh_constraints(str(SCHEMAS_DIR))
    Draft7Validator(FRESH_CONSTRAINTS_META).validate(loaded)
    assert load_fresh_constraints(str(SCHEMAS_DIR)) is loaded
    info = load_fresh_constraints.cache_info()
    assert info.misses == 1
    assert info.hits == 1
    assert set(loaded["by_type"]) == {
        "fill-in-a1",
        "fill-in-a2",
        "fill-in-b1",
        "fill-in-b2",
        "true-false-a1",
        "true-false-a2",
        "true-false-b1",
        "true-false-b2",
    }
    assert loaded["by_type"]["true-false-b2"]["items_max"] is None
    assert loaded["b2_true_false_cap"]["applied"] is False
    assert len(loaded["orthography_lists"]) == 6


def test_activity_payload_schema_does_not_express_the_constraint_file() -> None:
    rule = load_fresh_constraints(str(SCHEMAS_DIR))["by_type"]["fill-in-a1"]
    derived = activity_payload_schema(rule)
    assert derived["properties"] == {}
    assert "sentence_blanks" not in derived["properties"]


def test_form_choice_without_record_fails() -> None:
    draft, types = load_fixture("a1")
    del _item(draft, "a3")["record"]
    reasons = _reasons(draft, "a1", types)
    assert any("record" in reason for reason in reasons)


def test_form_choice_with_one_option_fails() -> None:
    draft, types = load_fixture("a1")
    _item(draft, "a3")["options"] = ["only"]
    reasons = _reasons(draft, "a1", types)
    assert any("options" in reason for reason in reasons)


def test_form_choice_with_five_options_fails() -> None:
    draft, types = load_fixture("a1")
    _item(draft, "a3")["options"] = ["a", "b", "c", "d", "e"]
    reasons = _reasons(draft, "a1", types)
    assert reasons and all("options" in reason for reason in reasons)


def test_sentence_with_zero_or_two_blanks_fails() -> None:
    draft, types = load_fixture("a1")
    _item(draft, "a3")["sentence"] = "no blank here"
    assert any("blank" in reason for reason in _reasons(draft, "a1", types))
    draft, types = load_fixture("a1")
    _item(draft, "a3")["sentence"] = "aa___bb___cc"
    assert any("blank" in reason for reason in _reasons(draft, "a1", types))


def test_orthography_at_a2_fails() -> None:
    draft, types = load_fixture("a2")
    activity = next(candidate for candidate in draft["activities"] if candidate["id"] == "a4")
    activity.clear()
    activity.update(
        {
            "id": "a4",
            "instruction": "Fill the blank.",
            "items": [
                {
                    "sentence": "aa___bb",
                    "answer": "x",
                    "mode": "orthography",
                    "options": ["x", "y"],
                    "explanation": "A placeholder explanation.",
                }
            ],
        }
    )
    types = dict(types, a4="fill-in")
    reasons = _reasons(draft, "a2", types)
    assert any("orthography is admitted only at a1" in reason for reason in reasons)


def test_orthography_options_must_be_one_closed_list() -> None:
    draft, types = load_fixture("a1")
    item = _item(draft, "a3")
    item.update({"mode": "orthography", "sentence": "aa___bb", "options": ["x", "y"], "answer": "x"})
    item.pop("record", None)
    item.pop("answer_tags", None)
    reasons = _reasons(draft, "a1", types)
    assert any("exactly one closed list" in reason for reason in reasons)


def test_orthography_answer_outside_its_list_fails() -> None:
    draft, types = load_fixture("a1")
    lists = load_fresh_constraints(str(SCHEMAS_DIR))["orthography_lists"]
    item = _item(draft, "a3")
    item.update(
        {
            "mode": "orthography",
            "sentence": "aa___bb",
            "options": list(lists[0]["options"]),
            "answer": "not-in-the-list",
        }
    )
    item.pop("record", None)
    item.pop("answer_tags", None)
    reasons = _reasons(draft, "a1", types)
    assert any("outside its option list" in reason for reason in reasons)


def _true_false_items(count: int) -> list[dict]:
    return [
        {"statement": f"Statement {index}.", "correct": True, "explanation": "The text says so."}
        for index in range(1, count + 1)
    ]


def _as_true_false(draft: dict, types: dict[str, str], count: int) -> tuple[dict, dict[str, str]]:
    activity = next(candidate for candidate in draft["activities"] if candidate["id"] == "a3")
    activity.clear()
    activity.update({"id": "a3", "instruction": "True or false?", "items": _true_false_items(count)})
    return draft, dict(types, a3="true-false")


def test_true_false_five_items_at_a1_fail_and_four_pass() -> None:
    draft, types = _as_true_false(*load_fixture("a1"), 5)
    assert any("exceeds the cap of 4" in reason for reason in _reasons(draft, "a1", types))
    draft, types = _as_true_false(*load_fixture("a1"), 4)
    assert validate_draft(draft, "a1", activity_types=types) == []


def test_b2_true_false_is_not_capped() -> None:
    draft, types = load_fixture("b2")
    activity = next(candidate for candidate in draft["activities"] if types[candidate["id"]] == "true-false")
    assert len(activity["items"]) == 10
    assert _reasons(draft, "b2", types) == []
    activity["items"].append(copy.deepcopy(activity["items"][0]))
    assert len(activity["items"]) == 11
    assert _reasons(draft, "b2", types) == []
    assert validate_draft(draft, "b2", activity_types=types) == []


def test_valid_form_choice_and_orthography_pass() -> None:
    draft, types = load_fixture("a1")
    assert validate_draft(draft, "a1", activity_types=types) == []
    lists = load_fresh_constraints(str(SCHEMAS_DIR))["orthography_lists"]
    item = _item(draft, "a3")
    item.clear()
    item.update(
        {
            "sentence": "aa___bb",
            "answer": lists[0]["options"][0],
            "mode": "orthography",
            "options": list(lists[0]["options"]),
            "explanation": "The list names the mark.",
        }
    )
    assert validate_draft(draft, "a1", activity_types=types) == []
