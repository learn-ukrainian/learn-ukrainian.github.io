"""Tests for the workbook-presence and activity-placement plan-validate rules
(issue #8889 r5 §A1, §B2; A1-P2's package of the implementation header).

End-to-end cases reuse the a1 fixture world of tests/curriculum/test_plan_validate.py
(build_base/write_world) so they exercise the real, committed
scripts/curriculum/validate/placement_table.yaml. Edge cases the real a1
table cannot reach (an unavailable or malformed table file, a level the
table does not cover) are unit-tested directly against the check functions.
"""

from __future__ import annotations

from pathlib import Path

from scripts.curriculum.validate import codes
from scripts.curriculum.validate.report import Report
from scripts.curriculum.validate.validate import (
    _check_activity_placement,
    _check_workbook_presence,
    validate_plan,
)
from tests.curriculum.test_plan_validate import LEVEL, SLUG, build_base, write_world


def produced_workbook_and_placement_codes(tmp_path: Path) -> set[str]:
    """Every code this module's fixtures exercise, for the cross-file registry
    check in tests/curriculum/test_plan_validate.py::test_code_registry_matches_produced_codes."""
    produced: set[str] = set()

    plan, pack, words = build_base()
    plan["lessons"][0]["activities"][1]["placement"] = "inline"  # was the only workbook activity
    world = write_world(tmp_path / "missing", plan, pack, words)
    produced |= validate_plan(LEVEL, SLUG, plan_path=world.plan_path).codes()

    plan, pack, words = build_base()
    plan["lessons"][0]["activities"].append(
        {"id": "a4", "type": "translate", "placement": "inline", "focus": "Translate."}
    )
    world = write_world(tmp_path / "forbidden-placement", plan, pack, words)
    produced |= validate_plan(LEVEL, SLUG, plan_path=world.plan_path).codes()

    plan, pack, words = build_base()
    plan["lessons"][0]["activities"].append({"id": "a4", "type": "reading", "placement": "workbook", "focus": "Read."})
    world = write_world(tmp_path / "forbidden-type", plan, pack, words)
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    # "reading" fails schema validation at a1 (not in the a1 allowlist) before
    # the placement check ever runs; UNKNOWN_ACTIVITY_TYPE is the code, and the
    # placement-forbidden path is exercised directly below instead.
    produced |= report.codes()

    empty_report = Report(level="a1", slug="x")
    _check_activity_placement(empty_report, plan, "a1", allowlist={"reading"}, placement_table_path=None)
    produced |= empty_report.codes()

    bad_table_report = Report(level="a1", slug="x")
    _check_activity_placement(
        bad_table_report, plan, "a1", allowlist={"reading"}, placement_table_path=tmp_path / "does-not-exist.yaml"
    )
    produced |= bad_table_report.codes()

    uncovered_report = Report(level="zz", slug="x")
    _check_activity_placement(uncovered_report, plan, "zz", allowlist=None, placement_table_path=None)
    produced |= uncovered_report.codes()

    return produced


# --- end-to-end: workbook presence -----------------------------------------


def test_valid_plan_needs_no_change() -> None:
    pass  # sanity anchor; the shared base_plan fixture's workbook presence is
    # already exercised by every VALID_CASES run in test_plan_validate.py


def test_non_recap_lesson_without_workbook_fails(tmp_path: Path) -> None:
    plan, pack, words = build_base()
    plan["lessons"][0]["activities"][1]["placement"] = "inline"  # a2 was the only workbook activity
    world = write_world(tmp_path, plan, pack, words)
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    outcome = next(o for o in report.failures if o.code == codes.WORKBOOK_ACTIVITY_MISSING)
    assert outcome.lesson == 1


def test_recap_lesson_without_workbook_passes(tmp_path: Path) -> None:
    plan, pack, words = build_base()
    plan["lessons"][1]["activities"] = [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Review quiz."}]
    world = write_world(tmp_path, plan, pack, words)
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    assert codes.WORKBOOK_ACTIVITY_MISSING not in report.codes()


def test_lesson_with_no_activities_at_all_fails_workbook_presence() -> None:
    report = Report(level="a1", slug="x")
    plan = {"lessons": [{"n": 1, "kind": "teach", "activities": []}]}
    _check_workbook_presence(report, plan)
    assert report.failures[0].code == codes.WORKBOOK_ACTIVITY_MISSING


def test_checkpoint_lesson_needs_a_workbook_activity_too() -> None:
    """checkpoint is not the recap; §A1 exempts only the recap lesson."""
    report = Report(level="a1", slug="x")
    plan = {
        "lessons": [{"n": 1, "kind": "checkpoint", "activities": [{"id": "a1", "type": "quiz", "placement": "inline"}]}]
    }
    _check_workbook_presence(report, plan)
    assert report.failures[0].code == codes.WORKBOOK_ACTIVITY_MISSING


# --- end-to-end: forbidden / mismatched placement ---------------------------


def test_translate_inline_at_a1_fails_placement_not_allowed(tmp_path: Path) -> None:
    """translate is workbook-only at a1 (issue #8889 r5 §B2)."""
    plan, pack, words = build_base()
    plan["lessons"][0]["activities"].append(
        {"id": "a4", "type": "translate", "placement": "inline", "focus": "Translate a sentence."}
    )
    world = write_world(tmp_path, plan, pack, words)
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    outcome = next(o for o in report.failures if o.code == codes.ACTIVITY_PLACEMENT_NOT_ALLOWED)
    assert "translate" in outcome.message
    assert outcome.lesson == 1


def test_translate_workbook_at_a1_passes(tmp_path: Path) -> None:
    plan, pack, words = build_base()
    plan["lessons"][0]["activities"].append(
        {"id": "a4", "type": "translate", "placement": "workbook", "focus": "Translate a sentence."}
    )
    world = write_world(tmp_path, plan, pack, words)
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    assert codes.ACTIVITY_PLACEMENT_NOT_ALLOWED not in report.codes()
    assert codes.ACTIVITY_PLACEMENT_FORBIDDEN not in report.codes()


def test_classify_at_a1_fails_placement_forbidden() -> None:
    """classify is deprecated in favour of group-sort and forbidden in new plans (§B2)."""
    report = Report(level="a1", slug="x")
    plan = {
        "lessons": [
            {
                "n": 1,
                "kind": "teach",
                "activities": [{"id": "a1", "type": "classify", "placement": "inline"}],
            }
        ]
    }
    _check_activity_placement(report, plan, "a1", allowlist={"classify"}, placement_table_path=None)
    outcome = report.failures[0]
    assert outcome.code == codes.ACTIVITY_PLACEMENT_FORBIDDEN
    assert outcome.lesson == 1


def test_type_outside_the_allowlist_is_skipped_not_double_reported() -> None:
    """UNKNOWN_ACTIVITY_TYPE (schema check) already covers this; no second failure."""
    report = Report(level="a1", slug="x")
    plan = {
        "lessons": [
            {"n": 1, "kind": "teach", "activities": [{"id": "a1", "type": "not-a-type", "placement": "inline"}]}
        ]
    }
    _check_activity_placement(report, plan, "a1", allowlist={"quiz"}, placement_table_path=None)
    assert report.failures == []


# --- unit tests: table-loading edge cases -----------------------------------


def test_missing_placement_table_file_fails_closed(tmp_path: Path) -> None:
    report = Report(level="a1", slug="x")
    plan = {"lessons": []}
    _check_activity_placement(report, plan, "a1", allowlist=None, placement_table_path=tmp_path / "does-not-exist.yaml")
    assert report.failures[0].code == codes.PLACEMENT_TABLE_UNAVAILABLE


def test_malformed_placement_table_file_fails_closed(tmp_path: Path) -> None:
    bad = tmp_path / "placement_table.yaml"
    bad.write_text("not_levels: {}\n", encoding="utf-8")
    report = Report(level="a1", slug="x")
    plan = {"lessons": []}
    _check_activity_placement(report, plan, "a1", allowlist=None, placement_table_path=bad)
    assert report.failures[0].code == codes.PLACEMENT_TABLE_UNAVAILABLE


def test_level_not_covered_by_table_is_not_checked_not_failed() -> None:
    report = Report(level="zz", slug="x")
    plan = {"lessons": [{"n": 1, "kind": "teach", "activities": [{"id": "a1", "type": "quiz", "placement": "inline"}]}]}
    _check_activity_placement(report, plan, "zz", allowlist=None, placement_table_path=None)
    assert report.failures == []
    outcome = next(o for o in report.not_checked if o.code == codes.PLACEMENT_LEVEL_NOT_COVERED)
    assert "zz" in outcome.message


# --- the plan_report is printed by plan-validate ----------------------------


def test_plan_validate_attaches_the_plan_report(tmp_path: Path) -> None:
    plan, pack, words = build_base()
    world = write_world(tmp_path, plan, pack, words)
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    assert report.activity_report["stage"] == "plan"
    assert report.activity_report["module_slug"] == SLUG
    payload = report.to_json()
    assert payload["activity_report"]["module"]["workbook_activities"] >= 1
    assert "activity_report (plan stage)" in report.render_text()


def test_plan_validate_reports_empty_activity_report_when_the_plan_fails_to_load(tmp_path: Path) -> None:
    plan, pack, words = build_base()
    world = write_world(tmp_path, plan, pack, words)
    world.plan_path.write_text("x: [unclosed", encoding="utf-8")
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    assert report.activity_report == {}
