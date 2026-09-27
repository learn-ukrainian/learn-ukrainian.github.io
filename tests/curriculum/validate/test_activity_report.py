"""Tests for the activity report (issue #8889 r5 §A2–A3; header §4).

Fixtures are small hand-built plan/draft/built-page dicts — plan_report only
needs the fields it reads (n, kind, activities: [{id, type, placement}]), so
fixtures here are deliberately minimal, not full schema-valid module plans
(those live in tests/curriculum/test_plan_validate.py).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.curriculum.validate.activity_report import (
    NOT_AVAILABLE,
    RESPONSE_UNIT_TABLE,
    compare_v1,
    draft_report,
    load_v1_activities,
    plan_report,
    rendered_report,
)


def _lesson(n: int, kind: str, activities: list[dict]) -> dict:
    return {"n": n, "kind": kind, "activities": activities}


def _activity(id_: str, activity_type: str, placement: str) -> dict:
    return {"id": id_, "type": activity_type, "placement": placement}


def test_plan_report_counts_by_lesson_and_placement() -> None:
    plan = {
        "slug": "mod-one",
        "lessons": [
            _lesson(
                1,
                "teach",
                [
                    _activity("a1", "quiz", "inline"),
                    _activity("a2", "error-correction", "workbook"),
                    _activity("a3", "match-up", "inline"),
                ],
            ),
            _lesson(2, "recap", [_activity("a1", "quiz", "inline")]),
        ],
    }
    report = plan_report(plan)
    assert report["stage"] == "plan"
    assert report["module_slug"] == "mod-one"
    lesson1 = report["lessons"][0]
    assert lesson1["activities"]["inline"]["total"] == 2
    assert lesson1["activities"]["workbook"]["total"] == 1
    assert lesson1["activities"]["inline"]["by_type"] == {"match-up": 1, "quiz": 1}
    assert lesson1["distinct_types"] == ["error-correction", "match-up", "quiz"]
    assert lesson1["has_workbook"] is True
    lesson2 = report["lessons"][1]
    assert lesson2["is_recap"] is True
    assert lesson2["has_workbook"] is False
    assert report["response_opportunities"] == NOT_AVAILABLE
    assert report["rendered"] == NOT_AVAILABLE


def test_plan_report_workbook_presence_ignores_the_recap() -> None:
    plan = {
        "slug": "mod-one",
        "lessons": [
            _lesson(1, "teach", [_activity("a1", "quiz", "inline")]),
            _lesson(2, "recap", [_activity("a1", "quiz", "inline")]),
        ],
    }
    module = plan_report(plan)["module"]
    assert module["non_recap_lessons"] == 1
    assert module["non_recap_lessons_with_workbook"] == 0
    assert module["workbook_presence_complete"] is False


def test_plan_report_largest_share_and_longest_run() -> None:
    plan = {
        "slug": "mod-one",
        "lessons": [
            _lesson(
                1,
                "teach",
                [
                    _activity("a1", "quiz", "workbook"),
                    _activity("a2", "quiz", "workbook"),
                    _activity("a3", "match-up", "workbook"),
                ],
            ),
        ],
    }
    module = plan_report(plan)["module"]
    assert module["largest_workbook_type"] == "quiz"
    assert module["largest_workbook_type_share"] == 2 / 3
    assert module["longest_same_type_workbook_run"] == 2
    assert module["longest_same_type_workbook_run_type"] == "quiz"


def test_plan_report_empty_module_has_zero_share_and_run() -> None:
    plan = {"slug": "mod-one", "lessons": [_lesson(1, "recap", [])]}
    module = plan_report(plan)["module"]
    assert module["largest_workbook_type_share"] == 0.0
    assert module["largest_workbook_type"] is None
    assert module["longest_same_type_workbook_run"] == 0


def _plan_with_one_lesson(activities: list[dict]) -> dict:
    return {"slug": "mod-one", "lessons": [_lesson(1, "teach", activities)]}


def test_draft_report_counts_items_and_explanations() -> None:
    plan = _plan_with_one_lesson([_activity("a1", "quiz", "workbook")])
    drafts = [
        {
            "lesson": {"n": 1},
            "activities": [
                {
                    "id": "a1",
                    "items": [
                        {"prompt": "?", "options": ["x"], "explanation": "why"},
                        {"prompt": "?", "options": ["y"], "explanation": ""},
                    ],
                }
            ],
        }
    ]
    report = draft_report(plan, drafts)
    lesson = report["lessons"][0]
    assert lesson["response_opportunities"] == {"total": 2, "by_type": {"quiz": 2}}
    assert lesson["explanation_coverage"] == {"explained": 1, "total": 2}
    assert report["module"]["response_opportunities_total"] == 2
    assert report["module"]["workbook_activities"] == 1


def test_draft_report_match_up_counts_pairs_with_why() -> None:
    plan = _plan_with_one_lesson([_activity("a1", "match-up", "inline")])
    drafts = [
        {
            "lesson": {"n": 1},
            "activities": [
                {"id": "a1", "pairs": [{"left": "a", "right": "b", "why": "matches"}, {"left": "c", "right": "d"}]}
            ],
        }
    ]
    report = draft_report(plan, drafts)
    assert report["lessons"][0]["response_opportunities"] == {"total": 2, "by_type": {"match-up": 2}}
    assert report["lessons"][0]["explanation_coverage"] == {"explained": 1, "total": 2}


def test_draft_report_group_sort_counts_entries_new_and_legacy_shape() -> None:
    plan = _plan_with_one_lesson([_activity("a1", "group-sort", "workbook")])
    drafts = [
        {
            "lesson": {"n": 1},
            "activities": [
                {
                    "id": "a1",
                    "groups": [
                        {"label": "masc", "entries": [{"text": "кіт", "why": "m"}]},
                        {"label": "fem", "items": ["книга"]},
                    ],
                }
            ],
        }
    ]
    report = draft_report(plan, drafts)
    assert report["lessons"][0]["response_opportunities"] == {"total": 2, "by_type": {"group-sort": 2}}
    assert report["lessons"][0]["explanation_coverage"] == {"explained": 1, "total": 2}


def test_draft_report_sequence_types_count_one_with_whole_activity_explanation() -> None:
    plan = _plan_with_one_lesson([_activity("a1", "order", "inline"), _activity("a2", "unjumble", "inline")])
    drafts = [
        {
            "lesson": {"n": 1},
            "activities": [
                {"id": "a1", "items": ["a", "b", "c"], "correct_order": [1, 2, 3], "explanation": "why this order"},
                {"id": "a2", "items": ["x", "y"]},
            ],
        }
    ]
    report = draft_report(plan, drafts)
    assert report["lessons"][0]["response_opportunities"] == {"total": 2, "by_type": {"order": 1, "unjumble": 1}}
    assert report["lessons"][0]["explanation_coverage"] == {"explained": 1, "total": 2}


def test_draft_report_missing_lesson_draft_is_not_available() -> None:
    plan = _plan_with_one_lesson([_activity("a1", "quiz", "inline")])
    report = draft_report(plan, drafts=[])
    assert report["lessons"][0]["response_opportunities"] == NOT_AVAILABLE
    assert report["lessons"][0]["explanation_coverage"] == NOT_AVAILABLE
    assert report["rendered"] == NOT_AVAILABLE


def test_draft_report_activity_missing_the_expected_key_is_not_counted() -> None:
    plan = _plan_with_one_lesson([_activity("a1", "quiz", "inline")])
    drafts = [{"lesson": {"n": 1}, "activities": [{"id": "a1"}]}]  # no "items"
    report = draft_report(plan, drafts)
    assert report["lessons"][0]["response_opportunities"] == {"total": 0, "by_type": {}}


def test_rendered_report_counts_rendered_and_playable_only() -> None:
    plan = _plan_with_one_lesson(
        [
            _activity("a1", "quiz", "workbook"),
            _activity("a2", "match-up", "workbook"),
            _activity("a3", "quiz", "inline"),
        ]
    )
    built_pages = [
        {
            "n": 1,
            "workbook_tasks": [
                {"id": "a1", "rendered": True, "playable": True},
                {"id": "a2", "rendered": True, "playable": False},
            ],
        }
    ]
    report = rendered_report(plan, built_pages)
    assert report["lessons"][0]["planned_workbook"] == 2
    assert report["lessons"][0]["rendered_and_playable"] == 1
    assert report["module"]["planned_workbook_total"] == 2
    assert report["module"]["rendered_and_playable_total"] == 1


def test_rendered_report_missing_page_is_not_available() -> None:
    plan = _plan_with_one_lesson([_activity("a1", "quiz", "workbook")])
    report = rendered_report(plan, built_pages=[])
    assert report["lessons"][0]["rendered_and_playable"] == NOT_AVAILABLE


def test_load_v1_activities_dict_shape(tmp_path: Path) -> None:
    path = tmp_path / "activities.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "inline": [{"id": "act-1", "type": "quiz", "items": [1]}],
                "workbook": [{"id": "act-2", "type": "error-correction", "items": [1, 2]}],
            }
        ),
        encoding="utf-8",
    )
    v1 = load_v1_activities(path)
    assert len(v1["inline"]) == 1
    assert len(v1["workbook"]) == 1


def test_load_v1_activities_flat_list_shape_is_all_inline(tmp_path: Path) -> None:
    path = tmp_path / "activities.yaml"
    path.write_text(yaml.safe_dump([{"id": "act-1", "type": "quiz", "items": [1, 2, 3]}]), encoding="utf-8")
    v1 = load_v1_activities(path)
    assert v1["workbook"] == []
    assert len(v1["inline"]) == 1


def test_compare_v1_prints_fresh_and_v1_side_by_side(tmp_path: Path) -> None:
    path = tmp_path / "activities.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "inline": [],
                "workbook": [
                    {"id": "act-1", "type": "quiz", "items": [{"prompt": "p", "explanation": "e"}] * 3},
                    {"id": "act-2", "type": "match-up", "pairs": [{"left": "a", "right": "b"}]},
                ],
            }
        ),
        encoding="utf-8",
    )
    plan = _plan_with_one_lesson([_activity("a1", "quiz", "workbook")])
    drafts = [{"lesson": {"n": 1}, "activities": [{"id": "a1", "items": [{"prompt": "p", "explanation": "e"}]}]}]
    fresh = draft_report(plan, drafts)
    comparison = compare_v1(fresh, path)
    assert comparison["v1"]["workbook_activities"] == 2
    assert comparison["v1"]["workbook_response_opportunities"] == 4
    assert comparison["fresh"]["workbook_activities"] == 1
    assert comparison["fresh"]["workbook_response_opportunities"] == 1
    assert comparison["workbook_activities_delta"] == -1
    assert comparison["workbook_response_opportunities_delta"] == -3


def test_compare_v1_with_a_plan_stage_report_marks_units_not_available(tmp_path: Path) -> None:
    path = tmp_path / "activities.yaml"
    path.write_text(
        yaml.safe_dump({"inline": [], "workbook": [{"id": "act-1", "type": "quiz", "items": [1]}]}), encoding="utf-8"
    )
    plan = _plan_with_one_lesson([_activity("a1", "quiz", "workbook")])
    fresh = plan_report(plan)
    comparison = compare_v1(fresh, path)
    assert comparison["fresh"]["workbook_response_opportunities"] == NOT_AVAILABLE
    assert comparison["workbook_response_opportunities_delta"] == NOT_AVAILABLE
    assert comparison["workbook_activities_delta"] == 0


def test_response_unit_table_covers_every_a1_choice_type() -> None:
    for activity_type in (
        "quiz",
        "fill-in",
        "true-false",
        "error-correction",
        "odd-one-out",
        "translate",
        "match-up",
        "group-sort",
        "order",
        "unjumble",
        "anagram",
        "count-syllables",
        "divide-words",
        "pick-syllables",
    ):
        assert activity_type in RESPONSE_UNIT_TABLE
