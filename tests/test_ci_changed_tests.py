"""Unit tests for the advisory changed-test fastlane selector.

Rule of thumb for every guard in this file: assert an invariant, not a
snapshot; if changing X legitimately requires editing >1 test, the test is a
snapshot. The fastlane manifest content is owned by
``scripts/ci/fastlane_always_tests.txt`` and its property guards (sorted, no
dupes, marker parity, slim-deps satisfiable, work-privacy excluded) live in
``tests/test_subprocess_timeout_guard.py`` — nothing here restates the list.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.ci import changed_tests

pytestmark = pytest.mark.repo_invariant


def _manifest() -> list[str]:
    """Read the fastlane repo-invariant manifest from its source of truth."""
    return changed_tests.load_repo_invariant_tests()


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
    selected = changed_tests.select_test_modules(["scripts/ci/changed_tests.py"], include_repo_invariants=True)

    assert selected == sorted(_manifest())


def test_docs_only_change_stays_empty_with_repo_invariant_opt_in() -> None:
    assert changed_tests.select_test_modules(["docs/foo.md"], include_repo_invariants=True) == []


def test_shell_changes_trigger_repo_invariant_manifest_but_docs_do_not() -> None:
    for path in ("scripts/cleanup.sh", "services.sh"):
        assert changed_tests.select_test_modules([path], include_repo_invariants=True) == sorted(_manifest())

    assert changed_tests.select_test_modules(["docs/cleanup.md"], include_repo_invariants=True) == []


def test_monitor_opsec_surface_changes_trigger_repo_invariant_manifest() -> None:
    for path in (
        "dashboards/index.html",
        "tests/api/opsec_sweep/registry.py",
    ):
        assert changed_tests.select_test_modules([path], include_repo_invariants=True) == sorted(_manifest())


def test_api_script_changes_trigger_repo_invariant_manifest_and_select_release_snapshot() -> None:
    manifest = _manifest()
    assert "tests/api/test_release_snapshot.py" not in manifest, (
        "release snapshot test is exempted from fastlane_always_tests.txt to preserve PR-tier budget"
    )
    for path in (
        "scripts/api/docs_router.py",
        "scripts/api/release_snapshot.py",
        "scripts/api/opsec_scan.py",
        "scripts/api/session_streams_router.py",
    ):
        selected = changed_tests.select_test_modules([path], include_repo_invariants=True)
        assert selected == sorted(set(manifest).union({"tests/api/test_release_snapshot.py"}))
        assert "tests/api/test_release_snapshot.py" in selected

    deduped = changed_tests.select_test_modules(
        ["tests/api/test_release_snapshot.py", "scripts/api/docs_router.py"],
        include_repo_invariants=True,
    )
    assert deduped == sorted(set(manifest).union({"tests/api/test_release_snapshot.py"}))
    assert len(deduped) == len(set(deduped))


def test_config_and_fixture_changes_trigger_repo_invariant_manifest() -> None:
    for path in (
        "pyproject.toml",
        "requirements-dev.txt",
        ".github/workflows/ci.yml",
        ".github/workflows/hygiene.yml",
        "scripts/ci/fastlane_always_tests.txt",
        "site/src/data/lexicon-manifest.fingerprint.json",
        "site/src/data/lexicon-manifest.pointer.json",
        "tests/fixtures/example.json",
    ):
        assert changed_tests.select_test_modules([path], include_repo_invariants=True) == sorted(_manifest())


def test_workflow_changes_trigger_repo_invariant_manifest_and_select_queue_starvation() -> None:
    for path in (
        ".github/workflows/ci.yml",
        ".github/workflows/hygiene.yml",
        ".github/workflows/integration-sweep.yml",
        ".github/workflows/security-audit.yml",
        ".github/workflows/ui-policy-gate.yml",
    ):
        selected = changed_tests.select_test_modules([path], include_repo_invariants=True)
        assert selected == sorted(_manifest())
        assert "tests/test_ci_queue_starvation.py" in selected


def test_repo_invariant_manifest_entries_are_not_duplicated() -> None:
    manifest = _manifest()
    assert manifest, "the repo-invariant manifest must not be empty"
    selected = changed_tests.select_test_modules(
        [manifest[0], "pyproject.toml"],
        include_repo_invariants=True,
    )

    assert selected == sorted(manifest)
    assert len(selected) == len(set(selected))


def test_changed_files_passes_timeout() -> None:
    fake = MagicMock()
    fake.stdout = "tests/test_a.py\n"
    with patch("subprocess.run", return_value=fake) as run_mock:
        files = changed_tests.changed_files("origin/main...HEAD")

    assert files == ["tests/test_a.py"]
    assert run_mock.call_args.kwargs.get("timeout") == changed_tests.GIT_DIFF_TIMEOUT_SECONDS


def test_main_handles_git_timeout(capsys: pytest.CaptureFixture[str]) -> None:
    with patch(
        "scripts.ci.changed_tests.changed_files",
        side_effect=subprocess.TimeoutExpired(["git", "diff"], 30),
    ):
        code = changed_tests.main(["--base", "origin/main"])

    assert code == 1
    err = capsys.readouterr().err
    assert "changed-test selection failed: git timed out after 30s" in err
