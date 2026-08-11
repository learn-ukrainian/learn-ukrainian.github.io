"""Unit tests for the advisory changed-test fastlane selector."""

from __future__ import annotations

from pathlib import Path

from scripts.ci import changed_tests


def test_comparison_range_accepts_base_ref_or_explicit_range() -> None:
    assert changed_tests.comparison_range("abc123", "def456") == "abc123...def456"
    assert changed_tests.comparison_range("origin/main...HEAD", "ignored") == "origin/main...HEAD"


def test_select_test_modules_is_sorted_deduplicated_and_test_only() -> None:
    selected = changed_tests.select_test_modules(
        [
            "docs/runbooks/ci-gate.md",
            "tests/helpers.py",
            "tests/unit/widget_test.py",
            "tests/test_zebra.py",
            "tests/test_alpha.py",
            "tests/test_zebra.py",
            "tests/test_data.json",
            "scripts/ci/changed_tests.py",
        ]
    )

    assert selected == ["tests/test_alpha.py", "tests/test_zebra.py", "tests/unit/widget_test.py"]


def test_write_plan_is_newline_delimited_and_empty_for_docs_only_change(tmp_path: Path) -> None:
    output = tmp_path / "plan.txt"

    changed_tests.write_plan(str(output), ["tests/test_b.py", "tests/test_a.py"])
    assert output.read_text(encoding="utf-8") == "tests/test_b.py\ntests/test_a.py\n"

    changed_tests.write_plan(str(output), [])
    assert output.read_text(encoding="utf-8") == ""
