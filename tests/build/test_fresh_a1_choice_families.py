"""Schema-backed check-7 routing witnesses, including non-object containers.

These are structural stimuli, not held-out Ukrainian or learner evidence.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft7Validator

from scripts.build.fresh import runner
from tests.curriculum.resolver.evidence_helpers import receipt_sources  # noqa: F401

SCHEMA = json.loads((Path(__file__).resolve().parents[2] / "schemas/activities-a1.schema.json").read_text())
EXPLANATION = "Follow the displayed model."
CHOICE = {
    "kind": "comprehension",
    "host": {"kind": "dialogue"},
    "options": ["first", "second"],
    "option_why": ["Matches the model.", "Differs from the model."],
    "explanation": EXPLANATION,
}
# Minimal equivalents of the report's family stimuli; every entry is validated
# against the actual A1 array schema before it reaches check 7.
FAMILIES = {
    "anagram": {"items": [{"letters": ["a", "b"], "answer": "ab", "explanation": EXPLANATION}]},
    "classify": {"categories": [{"label": "one", "items": ["a"]}, {"label": "two", "items": ["b"]}]},
    "count-syllables": {"items": [{"word": "model", "correct": 2, "explanation": EXPLANATION}]},
    "divide-words": {"items": [{"word": "model", "answer": "mo-del", "explanation": EXPLANATION}]},
    "error-correction": {
        "items": [{**CHOICE, "sentence": "second", "error": "second", "correction": "first", "error_ref": "E-001"}]
    },
    "fill-in": {"items": [{**CHOICE, "sentence": "___", "answer": "first"}]},
    "group-sort": {"groups": [{"label": "one", "items": ["a"]}, {"label": "two", "items": ["b"]}]},
    "image-to-letter": {"items": [{**CHOICE, "image": "model.png", "letter": "first"}]},
    "letter-grid": {"letters": [{"upper": "A", "lower": "a"}]},
    "match-up": {
        "left_role": "question",
        "right_role": "answer",
        "pairs": [
            {"left": "one?", "right": "one", "why": EXPLANATION},
            {"left": "two?", "right": "two", "why": EXPLANATION},
        ],
    },
    "observe": {"examples": ["first", "second"], "prompt": "Notice the pattern."},
    "odd-one-out": {
        "items": [
            {
                k: v
                for k, v in {
                    **CHOICE,
                    "words": ["first", "second", "third"],
                    "correct": 0,
                    "option_why": ["Matches the model.", "Differs from the model.", "Differs from the model."],
                }.items()
                if k != "options"
            }
        ]
    },
    "order": {"items": ["first", "second"], "correct_order": [1, 0], "explanation": EXPLANATION},
    "phrase-table": {"groups": [{"label": "one", "phrases": ["first"]}]},
    "pick-syllables": {
        "syllables": ["first", "second"],
        "correctIndices": [0, 1],
        "category": "model",
        "explanation": EXPLANATION,
    },
    "quiz": {"items": [{**CHOICE, "question": "Choose the model.", "correct": 0}]},
    "translate": {
        "items": [
            {
                **CHOICE,
                "source": "model",
                "options": [{"text": "first", "correct": True}, {"text": "second", "correct": False}],
            }
        ]
    },
    "true-false": {
        "items": [{k: v for k, v in {**CHOICE, "statement": "model", "correct": True}.items() if k != "options"}]
    },
    "unjumble": {"items": [{"words": ["first", "second"], "answer": "second first", "explanation": EXPLANATION}]},
    "watch-and-repeat": {"items": [{"video": "https://example.org/model", "explanation": EXPLANATION}]},
}
CHOICE_FAMILIES = ("error-correction", "fill-in", "image-to-letter", "odd-one-out", "quiz", "translate", "true-false")


def _activity(typ: str) -> dict:
    return copy.deepcopy({"id": "a1", "type": typ, "instruction": "Follow the model.", **FAMILIES[typ]})


def _check(tmp_path: Path, activity: dict, *, planned: bool = False, host: bool = True) -> dict:
    Draft7Validator(SCHEMA).validate([activity])
    typ = activity["type"]
    draft_activity = {key: value for key, value in activity.items() if not (planned and key == "type")}
    return runner.check_7_a1_choices(
        {
            "activities": [draft_activity],
            "steps": [
                {
                    "blocks": [
                        *([{"kind": "dialogue"}, {"kind": "quote", "ref": "T-1"}] if host else []),
                        {"kind": "activity", "ref": "a1"},
                    ]
                }
            ],
        },
        {"activities": [{"id": "a1", "type": typ}], "dialogue": {"step": "s1"}},
        {"words": []},
        SimpleNamespace(tokens=[]),
        state_dir=tmp_path,
        lesson_n=1,
        vesum_lookup=lambda forms: {form: [] for form in forms},
    )


@pytest.mark.parametrize("typ", FAMILIES)
@pytest.mark.parametrize("planned", [False, True], ids=["inline-type", "planned-type"])
def test_schema_family_witness_passes_check_7(tmp_path: Path, typ: str, planned: bool) -> None:
    assert _check(tmp_path, _activity(typ), planned=planned)["status"] == "passed"


@pytest.mark.parametrize("typ", CHOICE_FAMILIES)
@pytest.mark.parametrize("planned", [False, True], ids=["inline-type", "planned-type"])
def test_choice_family_is_checked_instead_of_skipped(tmp_path: Path, typ: str, planned: bool) -> None:
    activity = _activity(typ)
    # Put an unmarked item first: it must not hide the later marked choice.
    unmarked = copy.deepcopy(activity["items"][0])
    unmarked.pop("kind")
    activity["items"].insert(0, unmarked)
    row = _check(tmp_path, activity, planned=planned, host=False)
    assert (row["status"], row["code"], row["token"]) == ("failed", "comprehension_host_ineligible", "1")


@pytest.mark.parametrize("typ", ["fill-in", "error-correction", "translate"])
def test_production_item_without_options_has_no_choice_semantics(tmp_path: Path, typ: str) -> None:
    activity = _activity(typ)
    item = activity["items"][0]
    item.pop("options")
    item.pop("kind")
    assert _check(tmp_path, activity)["status"] == "passed"


def test_group_sort_string_items_with_form_feature_fail_without_record(tmp_path: Path) -> None:
    activity = _activity("group-sort")
    activity["grouping_feature"] = "Case"
    for group, value in zip(activity["groups"], ["Nom", "Gen"], strict=True):
        group["value"] = value
    assert _check(tmp_path, activity)["code"] == "group_entry_record_missing"


@pytest.mark.parametrize("key", ["words", "jumbled", "prompt", "scrambled"])
@pytest.mark.parametrize("value", ["first second", ["first", "second"]])
def test_unjumble_string_and_array_aliases_pass_check_7(tmp_path: Path, key: str, value) -> None:
    activity = _activity("unjumble")
    item = activity["items"][0]
    item.pop("words")
    item[key] = value
    assert _check(tmp_path, activity)["status"] == "passed"


def test_schema_allowed_classify_remains_forbidden_by_fresh_check_4(tmp_path: Path) -> None:
    activity = _activity("classify")
    assert _check(tmp_path, activity)["status"] == "passed"
    row, _ = runner.check_4_activities(
        {"activities": [activity]}, {"activities": [{"id": "a1", "type": "classify"}]}, {}, {}, level="a1"
    )
    assert row["code"] == "classify_forbidden"


def test_unknown_family_fails_closed(tmp_path: Path) -> None:
    row = runner.check_7_a1_choices(
        {"activities": [{"id": "a1", "items": []}]},
        {"activities": [{"id": "a1", "type": "unknown"}]},
        {},
        SimpleNamespace(tokens=[]),
        state_dir=tmp_path,
        lesson_n=1,
    )
    assert row["code"] == "choice_activity_type_invalid"


def test_multiple_choice_alias_keeps_existing_quiz_checks(tmp_path: Path) -> None:
    activity = _activity("quiz")
    row = runner.check_7_a1_choices(
        {"activities": [{key: value for key, value in activity.items() if key != "type"}]},
        {"activities": [{"id": "a1", "type": "multiple-choice"}]},
        {},
        SimpleNamespace(tokens=[]),
        state_dir=tmp_path,
        lesson_n=1,
    )
    assert row["code"] == "comprehension_host_ineligible"
