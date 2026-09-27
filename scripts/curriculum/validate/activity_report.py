"""The activity report (issue #8889 r5 §A2–A3; header comment 5855658208 §4).

Volume, variety and correctness are protected at module grain, not by a
per-lesson numeric floor (none is calibrated yet — the plan schema's own
``not_checked: lesson_activity_minimums_not_calibrated`` stands). Instead a
deterministic report is produced at three build stages, each reporting only
what that stage can know:

* :func:`plan_report` — plan-validate, from the plan alone: activities per
  lesson by placement and type, distinct types per lesson and across the
  module's workbook, the largest single-type share and the longest same-type
  run in the workbook, and workbook presence.
* :func:`draft_report` — the check runner, after the writer: response
  opportunities per the per-type unit table (:data:`RESPONSE_UNIT_TABLE`) and
  explanation coverage per scored unit.
* :func:`rendered_report` — the built pages: how many planned workbook tasks
  are actually rendered and playable, not cross-references.

A field a stage cannot know is the string ``"not_available_at_this_stage"``,
never a guessed number and never silently omitted. :func:`compare_v1` prints
a v1 module's workbook activities and response opportunities beside a fresh
module's report of any stage, for the plan-review v1 comparison (§A3).

Every function here is pure: dicts and lists in, a plain (YAML/JSON
serialisable) dict out. Nothing here reads or writes a file — the callers
(plan-validate for :func:`plan_report`; the fresh-build check runner for
:func:`draft_report`; the built-output test for :func:`rendered_report`) own
where their inputs come from.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

#: Activity types with no per-item "explanation" or per-unit response list:
#: each activity is exactly one sequencing task, regardless of how many
#: shuffled units (words, tokens) it holds to build that one task (issue
#: #8889 r5 §A2: "order and unjumble: one per sequence").
SEQUENCE_ACTIVITY_TYPES = frozenset({"order", "unjumble"})

#: A single puzzle per activity: schemas/activities-<level>.schema.json gives
#: pick-syllables its own top-level "syllables"/"correctIndices", never an
#: "items" list, so one activity is one response opportunity.
SINGLE_UNIT_ACTIVITY_TYPES = frozenset({"pick-syllables"})

#: Never a response opportunity (issue #8889 r5 §A2, "unscored types").
UNSCORED_ACTIVITY_TYPES = frozenset({"letter-grid", "observe", "phrase-table", "watch-and-repeat"})

#: The per-type response-unit table (issue #8889 r5 §A2), one constant as the
#: header requires. Value names which draft-payload key the unit count comes
#: from; ``_response_units`` is the one place that reads it. Types not listed
#: fall back to counting ``items`` (the shape most choice/production types
#: share), so a new type needs no code change unless it needs a different key.
RESPONSE_UNIT_TABLE: dict[str, str] = {
    "quiz": "items",
    "fill-in": "items",
    "true-false": "items",
    "error-correction": "items",
    "odd-one-out": "items",
    "select": "items",
    "translate": "items",
    "anagram": "items",  # words
    "count-syllables": "items",  # words
    "divide-words": "items",  # words
    "image-to-letter": "items",
    "pick-syllables": "single",
    "match-up": "pairs",
    "group-sort": "entries",
    "order": "sequence",
    "unjumble": "sequence",
    "cloze": "blanks",  # A2+, not built at A1
    "mark-the-words": "targets",  # A2+, not built at A1
    "letter-grid": "unscored",
    "observe": "unscored",
    "phrase-table": "unscored",
    "watch-and-repeat": "unscored",
}

NOT_AVAILABLE = "not_available_at_this_stage"


def _group_sort_entries(payload: dict) -> list | None:
    groups = payload.get("groups")
    if not isinstance(groups, list):
        return None
    entries: list = []
    for group in groups:
        if not isinstance(group, dict):
            return None
        # "items" is the current schema key; "entries" is what A1-P1 renames it
        # to for the {text, record, why} shape (issue #8889 r5 §3 group-sort row).
        group_entries = group.get("entries", group.get("items"))
        if not isinstance(group_entries, list):
            return None
        entries.extend(group_entries)
    return entries


def _unit_list(activity_type: str, payload: dict) -> list | None:
    """The list of individually-explainable response units, or None when the
    type has no such list (a sequence/single-puzzle type; see
    ``_response_units`` and ``_explained_units``)."""
    kind = RESPONSE_UNIT_TABLE.get(activity_type, "items")
    if kind in ("sequence", "single", "unscored"):
        return None
    if kind == "pairs":
        pairs = payload.get("pairs")
        return pairs if isinstance(pairs, list) else None
    if kind == "entries":
        return _group_sort_entries(payload)
    if kind == "blanks":
        blanks = payload.get("blanks")
        return blanks if isinstance(blanks, list) else None
    if kind == "targets":
        targets = payload.get("targets", payload.get("target_tokens"))
        return targets if isinstance(targets, list) else None
    items = payload.get("items")
    return items if isinstance(items, list) else None


def _response_units(activity_type: str, payload: dict) -> int | None:
    """One draft activity's response-opportunity count (issue #8889 r5 §A2).

    None means the payload does not carry the field the type needs — the
    caller reports ``not_available_at_this_stage`` for that activity, never a
    guessed count.
    """
    kind = RESPONSE_UNIT_TABLE.get(activity_type, "items")
    if kind == "unscored":
        return 0
    if kind == "sequence" or kind == "single":
        return 1
    unit_list = _unit_list(activity_type, payload)
    return len(unit_list) if unit_list is not None else None


def _has_explanation(unit: object) -> bool:
    if not isinstance(unit, dict):
        return False
    return bool(unit.get("explanation")) or bool(unit.get("why"))


def _explained_units(activity_type: str, payload: dict, units: int) -> int:
    """How many of an activity's response units carry a non-empty explanation.

    Sequence and single-puzzle types keep one whole-activity ``explanation``
    string (§3: "order/unjumble/pick-syllables: activity `explanation`
    required"); every other type is explained per unit (``explanation`` or,
    once #8889 lands, the per-option/per-entry/per-pair ``why``).
    """
    kind = RESPONSE_UNIT_TABLE.get(activity_type, "items")
    if kind in ("sequence", "single"):
        return units if payload.get("explanation") else 0
    unit_list = _unit_list(activity_type, payload)
    if unit_list is None:
        return 0
    return sum(1 for unit in unit_list if _has_explanation(unit))


def _lesson_activities(lesson: dict) -> list[dict]:
    return lesson.get("activities") or []


def _module_workbook_stats(plan: dict) -> dict:
    """Placement-derived module totals shared by all three report stages."""
    workbook_total = 0
    inline_total = 0
    for lesson in plan["lessons"]:
        for activity in _lesson_activities(lesson):
            if activity["placement"] == "workbook":
                workbook_total += 1
            else:
                inline_total += 1
    return {"workbook_activities": workbook_total, "inline_activities": inline_total}


def plan_report(plan: dict) -> dict:
    """The plan-stage activity report (issue #8889 r5 §A2, first bullet).

    Per lesson: activity counts by placement and type, distinct types, and
    workbook presence. Per module: distinct workbook types, the largest
    single-type share and the longest same-type run among the module's
    workbook activities (the plan reviewer's variety inputs, §B1), and
    whether every non-recap lesson has a workbook activity.
    """
    lessons: list[dict] = []
    module_workbook_types: Counter[str] = Counter()
    module_all_types: Counter[str] = Counter()
    workbook_type_sequence: list[str] = []
    non_recap_lessons = 0
    non_recap_with_workbook = 0

    for lesson in plan["lessons"]:
        activities = _lesson_activities(lesson)
        by_placement: dict[str, Counter[str]] = {"inline": Counter(), "workbook": Counter()}
        for activity in activities:
            by_placement[activity["placement"]][activity["type"]] += 1
            module_all_types[activity["type"]] += 1
        for activity in activities:
            if activity["placement"] == "workbook":
                workbook_type_sequence.append(activity["type"])
        module_workbook_types.update(by_placement["workbook"])

        workbook_count = sum(by_placement["workbook"].values())
        inline_count = sum(by_placement["inline"].values())
        is_recap = lesson["kind"] == "recap"
        if not is_recap:
            non_recap_lessons += 1
            if workbook_count:
                non_recap_with_workbook += 1

        lessons.append(
            {
                "n": lesson["n"],
                "kind": lesson["kind"],
                "is_recap": is_recap,
                "activities": {
                    "inline": {"total": inline_count, "by_type": dict(sorted(by_placement["inline"].items()))},
                    "workbook": {"total": workbook_count, "by_type": dict(sorted(by_placement["workbook"].items()))},
                },
                "distinct_types": sorted({activity["type"] for activity in activities}),
                "has_workbook": workbook_count > 0,
            }
        )

    largest_share = 0.0
    largest_share_type = None
    workbook_total = sum(module_workbook_types.values())
    if workbook_total:
        largest_share_type, top_count = module_workbook_types.most_common(1)[0]
        largest_share = top_count / workbook_total

    longest_run = 0
    longest_run_type = None
    current_type: str | None = None
    current_run = 0
    for activity_type in workbook_type_sequence:
        if activity_type == current_type:
            current_run += 1
        else:
            current_type, current_run = activity_type, 1
        if current_run > longest_run:
            longest_run, longest_run_type = current_run, current_type

    module = _module_workbook_stats(plan)
    module.update(
        {
            "workbook_distinct_types": sorted(module_workbook_types),
            "all_distinct_types": sorted(module_all_types),
            "largest_workbook_type_share": largest_share,
            "largest_workbook_type": largest_share_type,
            "longest_same_type_workbook_run": longest_run,
            "longest_same_type_workbook_run_type": longest_run_type,
            "non_recap_lessons": non_recap_lessons,
            "non_recap_lessons_with_workbook": non_recap_with_workbook,
            "workbook_presence_complete": non_recap_with_workbook == non_recap_lessons,
        }
    )

    return {
        "stage": "plan",
        "module_slug": plan.get("slug"),
        "lessons": lessons,
        "module": module,
        "response_opportunities": NOT_AVAILABLE,
        "explanation_coverage": NOT_AVAILABLE,
        "rendered": NOT_AVAILABLE,
    }


def draft_report(plan: dict, drafts: list[dict]) -> dict:
    """The draft-stage activity report (issue #8889 r5 §A2, second bullet).

    ``drafts`` is one lesson-draft payload per built lesson (the
    ``schemas/lesson-draft-<level>-v1.schema.json`` shape: ``{"lesson": {"n":
    ...}, "activities": [...], ...}``); a lesson the writer has not reached
    yet is simply absent from the list. Response units and explanation
    coverage are counted per :data:`RESPONSE_UNIT_TABLE` and reported
    ``not_available_at_this_stage`` for a lesson with no draft yet, or for one
    activity whose payload does not carry the field its type needs.
    """
    drafts_by_lesson = {draft["lesson"]["n"]: draft for draft in drafts}
    lessons: list[dict] = []
    module_units = 0
    module_explained = 0
    module_by_type: Counter[str] = Counter()

    for lesson in plan["lessons"]:
        n = lesson["n"]
        draft = drafts_by_lesson.get(n)
        if draft is None:
            lessons.append({"n": n, "response_opportunities": NOT_AVAILABLE, "explanation_coverage": NOT_AVAILABLE})
            continue
        plan_activities = {activity["id"]: activity for activity in _lesson_activities(lesson)}
        lesson_units = 0
        lesson_explained = 0
        by_type: Counter[str] = Counter()
        for activity in draft.get("activities") or []:
            plan_activity = plan_activities.get(activity.get("id"))
            if plan_activity is None:
                continue  # id/type/placement agreement with the plan is the structure gate's, not this report's
            activity_type = plan_activity["type"]
            units = _response_units(activity_type, activity)
            if units is None:
                continue
            lesson_units += units
            by_type[activity_type] += units
            lesson_explained += _explained_units(activity_type, activity, units)
        module_units += lesson_units
        module_explained += lesson_explained
        module_by_type.update(by_type)
        lessons.append(
            {
                "n": n,
                "response_opportunities": {"total": lesson_units, "by_type": dict(sorted(by_type.items()))},
                "explanation_coverage": {"explained": lesson_explained, "total": lesson_units},
            }
        )

    module = _module_workbook_stats(plan)
    module.update(
        {
            "response_opportunities_total": module_units,
            "response_opportunities_by_type": dict(sorted(module_by_type.items())),
            "explanation_coverage": {"explained": module_explained, "total": module_units},
        }
    )
    return {
        "stage": "draft",
        "module_slug": plan.get("slug"),
        "lessons": lessons,
        "module": module,
        "rendered": NOT_AVAILABLE,
    }


def rendered_report(plan: dict, built_pages: list[dict]) -> dict:
    """The rendered-stage activity report (issue #8889 r5 §A2, third bullet; §D).

    ``built_pages`` is one ``{"n": <lesson n>, "workbook_tasks": [{"id":
    <activity id>, "rendered": bool, "playable": bool}, ...]}`` per built
    lesson page. A planned workbook activity absent from ``workbook_tasks``,
    or present but not both rendered and playable, does not count — a
    cross-reference is not a rendered task (§D).
    """
    pages_by_lesson = {page["n"]: page for page in built_pages}
    lessons: list[dict] = []
    module_planned = 0
    module_rendered = 0

    for lesson in plan["lessons"]:
        n = lesson["n"]
        planned_ids = {activity["id"] for activity in _lesson_activities(lesson) if activity["placement"] == "workbook"}
        module_planned += len(planned_ids)
        page = pages_by_lesson.get(n)
        if page is None:
            lessons.append({"n": n, "planned_workbook": len(planned_ids), "rendered_and_playable": NOT_AVAILABLE})
            continue
        tasks = {task["id"]: task for task in page.get("workbook_tasks") or []}
        rendered = sum(
            1
            for activity_id in planned_ids
            if activity_id in tasks and tasks[activity_id].get("rendered") and tasks[activity_id].get("playable")
        )
        module_rendered += rendered
        lessons.append({"n": n, "planned_workbook": len(planned_ids), "rendered_and_playable": rendered})

    module = _module_workbook_stats(plan)
    module.update({"planned_workbook_total": module_planned, "rendered_and_playable_total": module_rendered})
    return {"stage": "rendered", "module_slug": plan.get("slug"), "lessons": lessons, "module": module}


def load_v1_activities(path: Path) -> dict[str, list[dict]]:
    """A v1 module's activities.yaml as ``{"inline": [...], "workbook": [...]}``.

    Most v1 modules use the dict shape (``inline``/``workbook`` keys); a few
    (e.g. ``sounds-letters-and-hello``) are a flat list with no placement
    marker at all — treated as entirely ``inline`` (that module ships no
    workbook, matching the baseline survey of issue #8889 r5 "Why").
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {"inline": list(data), "workbook": []}
    if isinstance(data, dict):
        return {"inline": list(data.get("inline") or []), "workbook": list(data.get("workbook") or [])}
    raise ValueError(f"{path} holds neither a list nor a mapping at the top level")


def compare_v1(fresh_module_report: dict, v1_module_path: Path) -> dict:
    """The v1 comparison (issue #8889 r5 §A3): v1's workbook activities and
    response opportunities beside a fresh module's report of any stage.

    ``fresh_module_report`` is the return value of :func:`plan_report`,
    :func:`draft_report` or :func:`rendered_report`; response-opportunity
    figures are ``not_available_at_this_stage`` when the fresh report's stage
    does not carry them (only :func:`draft_report` does).
    """
    v1 = load_v1_activities(v1_module_path)
    v1_by_type: Counter[str] = Counter()
    v1_units = 0
    for activity in v1["workbook"]:
        units = _response_units(activity.get("type", ""), activity)
        if units is not None:
            v1_units += units
            v1_by_type[activity.get("type", "")] += units

    fresh_module = fresh_module_report.get("module", {})
    fresh_workbook_activities = fresh_module.get("workbook_activities")
    fresh_units = fresh_module.get("response_opportunities_total", NOT_AVAILABLE)

    workbook_delta: int | str = NOT_AVAILABLE
    units_delta: int | str = NOT_AVAILABLE
    if isinstance(fresh_workbook_activities, int):
        workbook_delta = fresh_workbook_activities - len(v1["workbook"])
    if isinstance(fresh_units, int):
        units_delta = fresh_units - v1_units

    return {
        "v1_module_path": str(v1_module_path),
        "v1": {
            "workbook_activities": len(v1["workbook"]),
            "inline_activities": len(v1["inline"]),
            "workbook_response_opportunities": v1_units,
            "workbook_response_opportunities_by_type": dict(sorted(v1_by_type.items())),
        },
        "fresh": {
            "stage": fresh_module_report.get("stage"),
            "workbook_activities": fresh_workbook_activities,
            "workbook_response_opportunities": fresh_units,
        },
        "workbook_activities_delta": workbook_delta,
        "workbook_response_opportunities_delta": units_delta,
    }
