"""Unit tests for merge-group docs/skills landing-class classifier (#7018)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ci.landing_class import (
    CLASS_DOCS_SKILLS,
    CLASS_FULL,
    classify,
    main,
    path_allowed,
    write_github_output,
)


def test_skill_only_is_docs_skills() -> None:
    assert (
        classify(["agents_extensions/shared/skills/drive-epic/SKILL.md"])
        == CLASS_DOCS_SKILLS
    )


def test_skill_plus_scripts_is_full() -> None:
    assert (
        classify(
            [
                "agents_extensions/shared/skills/drive-epic/SKILL.md",
                "scripts/api/foo.py",
            ]
        )
        == CLASS_FULL
    )


def test_empty_paths_fail_closed_to_full() -> None:
    assert classify([]) == CLASS_FULL


def test_docs_markdown_only_is_docs_skills() -> None:
    assert classify(["docs/foo.md"]) == CLASS_DOCS_SKILLS


def test_github_workflow_is_full() -> None:
    assert classify([".github/workflows/ci.yml"]) == CLASS_FULL


def test_repo_root_markdown_is_docs_skills() -> None:
    assert classify(["README.md"]) == CLASS_DOCS_SKILLS


def test_docs_non_markdown_is_full() -> None:
    assert classify(["docs/schema.yaml"]) == CLASS_FULL


def test_path_allowed_deny_by_omission() -> None:
    assert not path_allowed("scripts/ci/landing_class.py")
    assert not path_allowed("tests/test_landing_class.py")
    assert not path_allowed("site/package.json")
    assert path_allowed("agents_extensions/shared/skills/x/SKILL.md")
    assert path_allowed("docs/best-practices/gitflow.md")
    assert path_allowed("AGENTS.md")


def test_main_no_inputs_fail_closed(capsys: pytest.CaptureFixture[str]) -> None:
    # No --base and empty/tty stdin → fail closed to full.
    assert main(["--json"]) == 0
    out = capsys.readouterr().out.strip()
    assert json.loads(out)["class"] == CLASS_FULL


def test_main_bogus_git_range_fail_closed(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--base", "not-a-real-ref-zzz", "--head", "also-fake", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["class"] == CLASS_FULL
    assert payload["changed_files"] == -1


def test_write_github_output(tmp_path: Path) -> None:
    out = tmp_path / "github_output"
    write_github_output(CLASS_DOCS_SKILLS, path=out)
    write_github_output(CLASS_FULL, path=out)
    assert out.read_text(encoding="utf-8") == "class=docs_skills\nclass=full\n"


def test_ci_gate_still_rejects_skipped_on_merge_group() -> None:
    """Regression: docs_skills must not teach the gate to accept skipped (#5762)."""
    from scripts.ci.gate_required_results import FULL_REQUIRED, evaluate_gate

    results = {job: "success" for job in FULL_REQUIRED}
    results["python"] = "skipped"
    failures = evaluate_gate("merge_group", results)
    assert any("python: skipped" in item for item in failures)
