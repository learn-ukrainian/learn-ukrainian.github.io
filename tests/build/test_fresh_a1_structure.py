"""A1 structural keys use the frozen spelling and option contracts.

The Ukrainian words in these fixtures were checked in VESUM:
слово 5682038-5682052, книга 2614480-2614493.
"""

from __future__ import annotations

import copy

import pytest

from scripts.build.fresh.draft_schema import load_fresh_constraints
from scripts.build.fresh.gen_draft_schemas import SCHEMAS_DIR
from scripts.build.fresh.runner import _VOWELS, _structural_activity_error, check_4_activities

WORD = {"W-1": {"id": "W-1", "forms": [{"form": "слово", "tags": "noun:inanim:n:v_naz", "learner": True}]}}


@pytest.mark.parametrize(
    ("typ", "activity", "defect", "code"),
    [
        (
            "divide-words",
            {"items": [{"word": "слово", "answer": "сло-во"}]},
            lambda activity: activity["items"][0].update(answer="сл-ово"),
            "divide_words_parts_invalid",
        ),
        (
            "count-syllables",
            {"items": [{"word": "слово", "correct": 2}]},
            lambda activity: activity["items"][0].update(correct=3),
            "count_syllables_key_invalid",
        ),
        (
            "anagram",
            {"items": [{"letters": list("слово"), "answer": "слово"}]},
            lambda activity: activity["items"][0].update(answer="книга"),
            "anagram_multiset_mismatch",
        ),
        (
            "unjumble",
            {"items": [{"words": list("слово"), "answer": "слово"}]},
            lambda activity: activity["items"][0].update(answer="книга"),
            "unjumble_multiset_mismatch",
        ),
        (
            "order",
            {"items": ["first", "second"], "correct_order": [1, 0], "explanation": "Second comes first."},
            lambda activity: activity.update(correct_order=[0, 0]),
            "order_index_coverage",
        ),
        (
            "match-up",
            {
                "left_role": "form",
                "right_role": "gloss",
                "pairs": [{"left": "слово", "left_record": "W-1", "right": "word", "why": "Matches."}],
            },
            lambda activity: activity["pairs"][0].update(left_record="W-2"),
            "match_up_form_record_invalid",
        ),
        (
            "pick-syllables",
            {"explanation": "The two parts have one vowel each."},
            lambda activity: activity.update(explanation=""),
            "pick_syllables_explanation_missing",
        ),
        (
            "quiz",
            {"items": [{"options": ["first", "second"], "correct": 0, "option_why": ["Works", "Fails"]}]},
            lambda activity: activity["items"][0].update(option_why=["Works"]),
            "option_why_alignment",
        ),
    ],
)
def test_valid_structure_and_named_defect(typ: str, activity: dict, defect, code: str) -> None:
    assert _structural_activity_error(activity, typ, WORD) is None
    bad = copy.deepcopy(activity)
    defect(bad)
    assert _structural_activity_error(bad, typ, WORD) == code


@pytest.mark.parametrize(
    ("typ", "activity"),
    [
        ("classify", {"items": []}),
        ("order", {"items": ["first", "second"], "correct_order": [0]}),
        ("match-up", {"pairs": [{"left": "first", "right": "second"}]}),
        ("divide-words", {"items": [{"word": "слово", "answer": "сл-ово"}]}),
        ("count-syllables", {"items": [{"word": "слово", "correct": 3}]}),
        ("anagram", {"items": [{"letters": ["с"], "answer": "слово"}]}),
        ("unjumble", {"items": [{"words": ["с"], "answer": "слово"}]}),
        ("pick-syllables", {}),
        ("quiz", {"items": [{"options": ["first", "second"], "correct": 0}]}),
    ],
)
def test_a2_fresh_draft_does_not_inherit_a1_structural_rules(typ: str, activity: dict) -> None:
    activity = {"id": "a1", **activity}
    row, _ = check_4_activities(
        {"lesson": {"module": "a2/sample"}, "activities": [activity]},
        {"activities": [{"id": "a1", "type": typ}], "level": "a2"},
        {"words": []},
        {"errors": []},
        level="a2",
    )
    assert row["status"] == "passed", row


def test_a1_vowels_match_both_constraints_and_header() -> None:
    expected = frozenset("аеіиоуяюєї")
    assert len(expected) == 10
    rules = load_fresh_constraints(str(SCHEMAS_DIR))["by_type"]
    assert expected == _VOWELS
    assert frozenset(rules["divide-words-a1"]["one_vowel_parts"]) == expected
    assert frozenset(rules["count-syllables-a1"]["correct_equals_vowel_count"]) == expected
