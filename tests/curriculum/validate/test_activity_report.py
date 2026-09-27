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


def test_draft_report_pick_syllables_counts_one_response_unit_per_activity() -> None:
    # Driver resolution on #8889: pick-syllables is one puzzle (no "items"
    # list), so the item and the activity coincide at A1 — one unit, not a
    # count of syllables or of correctIndices.
    plan = _plan_with_one_lesson([_activity("a1", "pick-syllables", "workbook")])
    drafts = [
        {
            "lesson": {"n": 1},
            "activities": [
                {
                    "id": "a1",
                    "syllables": ["мо", "ло", "ко"],
                    "correctIndices": [0, 2],
                    "explanation": "why these syllables",
                }
            ],
        }
    ]
    report = draft_report(plan, drafts)
    assert report["lessons"][0]["response_opportunities"] == {"total": 1, "by_type": {"pick-syllables": 1}}
    assert report["lessons"][0]["explanation_coverage"] == {"explained": 1, "total": 1}


def test_draft_report_complete_option_why_counts_as_explained() -> None:
    # Regression for finding 5: a per-option option_why array with one entry
    # per option is a valid explanation, not only the single "explanation" or
    # "why" string.
    plan = _plan_with_one_lesson([_activity("a1", "quiz", "workbook")])
    drafts = [
        {
            "lesson": {"n": 1},
            "activities": [
                {
                    "id": "a1",
                    "items": [
                        {
                            "prompt": "?",
                            "options": ["x", "y", "z"],
                            "option_why": ["x is right", "y is wrong", "z is wrong"],
                        },
                        {
                            "prompt": "?",
                            "options": ["a", "b"],
                            "option_why": ["a is right", ""],  # partial: one entry is empty
                        },
                        {
                            "prompt": "?",
                            "options": ["p", "q"],
                            "option_why": ["p is right"],  # partial: shorter than options
                        },
                    ],
                }
            ],
        }
    ]
    report = draft_report(plan, drafts)
    assert report["lessons"][0]["explanation_coverage"] == {"explained": 1, "total": 3}


def test_draft_report_true_false_option_why_counts_as_explained() -> None:
    # Regression for finding 2 (r2): true-false carries neither "options" nor
    # "words", so it fell through _option_list to None and every option_why
    # was treated as incomplete. Its two implicit options are the statement
    # being true or false, so a complete option_why is the two-entry
    # [why_if_true, why_if_false] (header §3).
    plan = _plan_with_one_lesson([_activity("a1", "true-false", "workbook")])
    drafts = [
        {
            "lesson": {"n": 1},
            "activities": [
                {
                    "id": "a1",
                    "items": [
                        {
                            "statement": "Кияни їдять борщ.",
                            "correct": True,
                            "option_why": ["true reason", "false reason"],
                        },
                        {"statement": "Собаки літають.", "correct": False, "option_why": ["only one entry"]},
                        {"statement": "Кава гаряча.", "correct": True, "option_why": []},
                    ],
                }
            ],
        }
    ]
    report = draft_report(plan, drafts)
    assert report["lessons"][0]["explanation_coverage"] == {"explained": 1, "total": 3}


def test_draft_report_odd_one_out_option_why_aligns_to_words() -> None:
    plan = _plan_with_one_lesson([_activity("a1", "odd-one-out", "workbook")])
    drafts = [
        {
            "lesson": {"n": 1},
            "activities": [
                {
                    "id": "a1",
                    "items": [
                        {
                            "prompt": "?",
                            "words": ["кіт", "собака", "стіл"],
                            "option_why": ["animal", "animal", "not an animal"],
                        }
                    ],
                }
            ],
        }
    ]
    report = draft_report(plan, drafts)
    assert report["lessons"][0]["explanation_coverage"] == {"explained": 1, "total": 1}


def test_draft_report_missing_lesson_draft_is_not_available() -> None:
    plan = _plan_with_one_lesson([_activity("a1", "quiz", "inline")])
    report = draft_report(plan, drafts=[])
    assert report["lessons"][0]["response_opportunities"] == NOT_AVAILABLE
    assert report["lessons"][0]["explanation_coverage"] == NOT_AVAILABLE
    assert report["rendered"] == NOT_AVAILABLE


def test_draft_report_activity_missing_the_expected_key_is_not_available() -> None:
    # An uncomputable activity must not silently drop to 0 (issue #8889 r5 §A2
    # r1 finding 1): the lesson and module totals that depend on it become
    # not_available_at_this_stage instead.
    plan = _plan_with_one_lesson([_activity("a1", "quiz", "inline")])
    drafts = [{"lesson": {"n": 1}, "activities": [{"id": "a1"}]}]  # no "items"
    report = draft_report(plan, drafts)
    assert report["lessons"][0]["response_opportunities"] == NOT_AVAILABLE
    assert report["lessons"][0]["explanation_coverage"] == NOT_AVAILABLE
    assert report["module"]["response_opportunities_total"] == NOT_AVAILABLE
    assert report["module"]["workbook_response_opportunities_total"] == NOT_AVAILABLE
    assert report["module"]["inline_response_opportunities_total"] == NOT_AVAILABLE
    assert report["module"]["explanation_coverage"] == NOT_AVAILABLE


def test_draft_report_module_total_is_not_available_when_any_lesson_draft_is_missing() -> None:
    # Regression for finding 1: a missing lesson draft must not let the module
    # total silently equal the sum of the *other* lessons.
    plan = {
        "slug": "mod-one",
        "lessons": [
            _lesson(1, "teach", [_activity("a1", "quiz", "workbook")]),
            _lesson(2, "teach", [_activity("a2", "quiz", "workbook")]),
        ],
    }
    drafts = [
        {
            "lesson": {"n": 1},
            "activities": [{"id": "a1", "items": [{"prompt": "?", "options": ["x"], "explanation": "why"}]}],
        }
    ]  # lesson 2 has no draft yet
    report = draft_report(plan, drafts)
    assert report["lessons"][0]["response_opportunities"] == {"total": 1, "by_type": {"quiz": 1}}
    assert report["lessons"][1]["response_opportunities"] == NOT_AVAILABLE
    assert report["module"]["response_opportunities_total"] == NOT_AVAILABLE
    assert report["module"]["workbook_response_opportunities_total"] == NOT_AVAILABLE
    assert report["module"]["explanation_coverage"] == NOT_AVAILABLE


def test_draft_report_omitted_planned_activity_is_not_available() -> None:
    # Regression for finding 1 (r2): a lesson draft that exists but has no
    # payload at all for one of the plan's activities must not silently total
    # only the activities it does have — an omitted planned activity makes
    # the lesson (and every module total depending on it)
    # not_available_at_this_stage, same as a malformed one.
    plan = _plan_with_one_lesson(
        [
            _activity("a1", "quiz", "workbook"),
            _activity("a2", "match-up", "inline"),
        ]
    )
    drafts = [
        {
            "lesson": {"n": 1},
            "activities": [
                {"id": "a1", "items": [{"prompt": "?", "options": ["x"], "explanation": "why"}]}
                # a2 is entirely absent from the draft's activities
            ],
        }
    ]
    report = draft_report(plan, drafts)
    assert report["lessons"][0]["response_opportunities"] == NOT_AVAILABLE
    assert report["lessons"][0]["explanation_coverage"] == NOT_AVAILABLE
    assert report["module"]["response_opportunities_total"] == NOT_AVAILABLE
    assert report["module"]["workbook_response_opportunities_total"] == NOT_AVAILABLE
    assert report["module"]["inline_response_opportunities_total"] == NOT_AVAILABLE
    assert report["module"]["explanation_coverage"] == NOT_AVAILABLE


def test_rendered_report_omitted_planned_activity_does_not_count_as_rendered() -> None:
    # Regression for finding 1 (r2), rendered stage: a built page that omits
    # a planned workbook activity's task entry entirely (not merely
    # unrendered/unplayable) is a known fact, not an unknown one — the page
    # was built, so the omission legitimately counts as not rendered, and the
    # module total stays a real number rather than not_available_at_this_stage.
    plan = _plan_with_one_lesson(
        [
            _activity("a1", "quiz", "workbook"),
            _activity("a2", "match-up", "workbook"),
        ]
    )
    built_pages = [{"n": 1, "workbook_tasks": [{"id": "a1", "rendered": True, "playable": True}]}]  # a2 absent
    report = rendered_report(plan, built_pages)
    assert report["lessons"][0]["planned_workbook"] == 2
    assert report["lessons"][0]["rendered_and_playable"] == 1
    assert report["module"]["planned_workbook_total"] == 2
    assert report["module"]["rendered_and_playable_total"] == 1


def test_draft_and_rendered_reports_expose_the_same_module_and_lesson_fields() -> None:
    # Regression for finding 3 (r2) and its r3 follow-up: rendered_report's
    # module dict omitted response_opportunities_total,
    # response_opportunities_by_type and explanation_coverage entirely, and
    # draft_report's module and lesson dicts likewise lacked
    # planned_workbook(_total)/rendered_and_playable(_total) — unlike
    # rendered_report's. The frozen §4 interface requires the full field set
    # at both grains on both sides: a field a stage cannot know is
    # not_available_at_this_stage, never silently omitted.
    plan = _plan_with_one_lesson([_activity("a1", "quiz", "workbook")])
    drafts = [
        {
            "lesson": {"n": 1},
            "activities": [{"id": "a1", "items": [{"prompt": "?", "options": ["x"], "explanation": "why"}]}],
        }
    ]
    draft = draft_report(plan, drafts)
    rendered = rendered_report(plan, built_pages=[])

    assert draft["module"].keys() == rendered["module"].keys()
    assert draft["lessons"][0].keys() == rendered["lessons"][0].keys()

    assert rendered["module"]["response_opportunities_total"] == NOT_AVAILABLE
    assert rendered["module"]["response_opportunities_by_type"] == NOT_AVAILABLE
    assert rendered["module"]["explanation_coverage"] == NOT_AVAILABLE
    assert rendered["lessons"][0]["response_opportunities"] == NOT_AVAILABLE
    assert rendered["lessons"][0]["explanation_coverage"] == NOT_AVAILABLE

    assert draft["module"]["planned_workbook_total"] == 1
    assert draft["module"]["rendered_and_playable_total"] == NOT_AVAILABLE
    assert draft["lessons"][0]["planned_workbook"] == 1
    assert draft["lessons"][0]["rendered_and_playable"] == NOT_AVAILABLE


def test_rendered_report_module_total_is_not_available_when_any_page_is_missing() -> None:
    # Regression for finding 1, rendered stage.
    plan = {
        "slug": "mod-one",
        "lessons": [
            _lesson(1, "teach", [_activity("a1", "quiz", "workbook")]),
            _lesson(2, "teach", [_activity("a2", "quiz", "workbook")]),
        ],
    }
    built_pages = [{"n": 1, "workbook_tasks": [{"id": "a1", "rendered": True, "playable": True}]}]  # no page for 2
    report = rendered_report(plan, built_pages)
    assert report["module"]["planned_workbook_total"] == 2
    assert report["module"]["rendered_and_playable_total"] == NOT_AVAILABLE


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


def test_compare_v1_counts_workbook_only_not_inline_plus_workbook(tmp_path: Path) -> None:
    # Regression for finding 2: a fresh module with large inline activity
    # (which contributes nothing to v1's workbook baseline) must not inflate
    # the "fresh" workbook response-opportunities figure.
    path = tmp_path / "activities.yaml"
    path.write_text(
        yaml.safe_dump({"inline": [], "workbook": [{"id": "act-1", "type": "quiz", "items": [1]}]}), encoding="utf-8"
    )
    plan = _plan_with_one_lesson(
        [
            _activity("a1", "quiz", "workbook"),
            _activity("a2", "quiz", "inline"),
        ]
    )
    drafts = [
        {
            "lesson": {"n": 1},
            "activities": [
                {"id": "a1", "items": [{"prompt": "p", "options": ["x"], "explanation": "e"}]},
                {
                    "id": "a2",
                    "items": [{"prompt": "p", "options": ["x"], "explanation": "e"}] * 5,
                },
            ],
        }
    ]
    fresh = draft_report(plan, drafts)
    assert fresh["module"]["response_opportunities_total"] == 6  # 1 workbook + 5 inline
    comparison = compare_v1(fresh, path)
    assert comparison["fresh"]["workbook_response_opportunities"] == 1
    assert comparison["workbook_response_opportunities_delta"] == 0


def test_compare_v1_reads_activities_yaml_from_the_module_directory(tmp_path: Path) -> None:
    # Regression for finding 6: v1_module_path is normally a module directory,
    # not the activities.yaml file directly.
    module_dir = tmp_path / "sounds-letters-and-hello"
    module_dir.mkdir()
    (module_dir / "activities.yaml").write_text(
        yaml.safe_dump({"inline": [], "workbook": [{"id": "act-1", "type": "quiz", "items": [1, 2]}]}),
        encoding="utf-8",
    )
    plan = _plan_with_one_lesson([_activity("a1", "quiz", "workbook")])
    drafts = [{"lesson": {"n": 1}, "activities": [{"id": "a1", "items": [{"prompt": "p", "options": ["x"]}]}]}]
    fresh = draft_report(plan, drafts)
    comparison = compare_v1(fresh, module_dir)
    assert comparison["v1"]["workbook_activities"] == 1
    assert comparison["v1"]["workbook_response_opportunities"] == 2


def test_compare_v1_reads_flat_list_v1_module_from_the_module_directory(tmp_path: Path) -> None:
    # The flat-list v1 shape (no inline/workbook split, e.g. sounds-letters-and-hello)
    # also resolves through the directory form.
    module_dir = tmp_path / "sounds-letters-and-hello"
    module_dir.mkdir()
    (module_dir / "activities.yaml").write_text(
        yaml.safe_dump([{"id": "act-1", "type": "quiz", "items": [1, 2, 3]}]), encoding="utf-8"
    )
    plan = _plan_with_one_lesson([])
    fresh = plan_report(plan)
    comparison = compare_v1(fresh, module_dir)
    assert comparison["v1"]["workbook_activities"] == 0
    assert comparison["v1"]["inline_activities"] == 1


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
