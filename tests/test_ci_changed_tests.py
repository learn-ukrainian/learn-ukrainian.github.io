"""Unit tests for the advisory changed-test fastlane selector."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ci import changed_tests

pytestmark = pytest.mark.repo_invariant

REPO_INVARIANT_TESTS = [
    "tests/test_ci_changed_tests.py",
    "tests/test_cyrillic_roundtrip_invariant.py",
    "tests/test_fleet_routing_open_model_data_import_guard.py",
    "tests/test_frontend_change_scope.py",
    "tests/test_lint_test_assertions.py",
    "tests/test_subprocess_timeout_guard.py",
    "tests/test_threshold_source_of_truth.py",
]


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


def test_code_only_change_can_opt_into_repo_invariant_manifest() -> None:
    selected = changed_tests.select_test_modules(
        ["scripts/ci/changed_tests.py"], include_repo_invariants=True
    )

    assert selected == REPO_INVARIANT_TESTS


def test_docs_only_change_stays_empty_with_repo_invariant_opt_in() -> None:
    assert changed_tests.select_test_modules(["docs/foo.md"], include_repo_invariants=True) == []


def test_config_and_fixture_changes_trigger_repo_invariant_manifest() -> None:
    for path in (
        "pyproject.toml",
        "requirements-dev.txt",
        ".github/workflows/ci.yml",
        "scripts/ci/fastlane_always_tests.txt",
        "tests/fixtures/example.json",
    ):
        assert changed_tests.select_test_modules([path], include_repo_invariants=True) == REPO_INVARIANT_TESTS


def test_repo_invariant_manifest_entries_are_not_duplicated() -> None:
    selected = changed_tests.select_test_modules(
        ["tests/test_threshold_source_of_truth.py", "pyproject.toml"],
        include_repo_invariants=True,
    )

    assert selected == [
        "tests/test_ci_changed_tests.py",
        "tests/test_cyrillic_roundtrip_invariant.py",
        "tests/test_fleet_routing_open_model_data_import_guard.py",
        "tests/test_frontend_change_scope.py",
        "tests/test_lint_test_assertions.py",
        "tests/test_subprocess_timeout_guard.py",
        "tests/test_threshold_source_of_truth.py",
    ]
    assert len(selected) == len(set(selected))
