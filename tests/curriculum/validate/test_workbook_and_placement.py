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
    # already exercised by every VALID_CASES run in test_plan_validate.py


# --- end-to-end: forbidden / mismatched placement ---------------------------


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


# --- the plan_report is printed by plan-validate ----------------------------
