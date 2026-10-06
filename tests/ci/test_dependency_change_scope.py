"""Unit coverage for dependency-input changed-path scope (#9871)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.ci import dependency_change_scope as scope

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DENOMINATOR = _REPO_ROOT / scope.DENOMINATOR_REL


def test_denominator_is_loadable_and_covers_required_inputs() -> None:
    data = scope.load_denominator(_DENOMINATOR)
    assert data["schema_version"] == "dependency_change_denominator_v1"
    assert data["version"]
    paths = data["paths"]
    for expected in (
        "requirements*.txt",
        "pyproject.toml",
        "uv.lock",
        "poetry.lock",
        "package.json",
        "package-lock.json",
        "site/package.json",
        "site/package-lock.json",
        "scripts/config/pip-audit-ignore.yaml",
        "scripts/config/npm-audit-ignore.yaml",
        "scripts/ci/audit_dependencies.py",
        "scripts/ci/dependency_change_denominator.json",
        "scripts/ci/dependency_change_scope.py",
    ):
        assert expected in paths


def test_path_matching_dependency_vs_non_dependency() -> None:
    patterns = scope.load_denominator()["paths"]
    assert scope.path_in_denominator("requirements-lock.txt", patterns)
    assert scope.path_in_denominator("requirements.txt", patterns)
    assert scope.path_in_denominator("pyproject.toml", patterns)
    assert scope.path_in_denominator("site/package-lock.json", patterns)
    assert scope.path_in_denominator("scripts/ci/audit_dependencies.py", patterns)
    assert not scope.path_in_denominator("docs/runbooks/ci-gate.md", patterns)
    assert not scope.path_in_denominator("scripts/ci/frontend_change_scope.py", patterns)
    assert not scope.path_in_denominator("site/src/App.tsx", patterns)


def test_glob_without_slash_matches_basename_only() -> None:
    patterns = scope.load_denominator()["paths"]
    assert scope.path_in_denominator("requirements-dev.txt", patterns)
    # A root-level glob must not reach into subdirectories.
    assert not scope.path_in_denominator("scripts/requirements-dev.txt", patterns)


def test_name_status_parsing_covers_add_modify_delete_rename() -> None:
    raw = b"A\0docs/new.md\0M\0scripts/ci/audit_dependencies.py\0D\0requirements-old.txt\0"
    assert scope._parse_name_status_z(raw) == [
        "docs/new.md",
        "requirements-old.txt",
        "scripts/ci/audit_dependencies.py",
    ]


def test_rename_contributes_both_sides() -> None:
    raw = b"R100\0docs/old-name.md\0requirements.txt\0"
    assert scope._parse_name_status_z(raw) == ["docs/old-name.md", "requirements.txt"]


def test_rename_into_manifest_runs_audit() -> None:
    run, lines, matched = scope.decide_from_changed(["docs/old-name.md", "requirements.txt"])
    assert run is True
    assert matched == ["requirements.txt"]
    assert all(scope.NOT_APPLICABLE_LINE not in line for line in lines)


def test_rename_out_of_manifest_runs_audit() -> None:
    run, _lines, matched = scope.decide_from_changed(["requirements.txt", "docs/archived-requirements.txt"])
    assert run is True
    assert matched == ["requirements.txt"]


def test_deleted_manifest_runs_audit() -> None:
    run, _lines, matched = scope.decide_from_changed(["requirements-lock.txt"])
    assert run is True
    assert matched == ["requirements-lock.txt"]


def test_non_dependency_change_is_not_applicable() -> None:
    run, lines, matched = scope.decide_from_changed(
        ["docs/runbooks/ci-gate.md", "scripts/ci/frontend_change_scope.py"]
    )
    assert run is False
    assert matched == []
    assert scope.NOT_APPLICABLE_LINE in lines


def test_missing_base_fails_closed(tmp_path: Path, monkeypatch, capsys) -> None:
    output = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary"))
    assert scope.main(["--base", "", "--event", "pull_request"]) == 0
    assert "run=true" in output.read_text(encoding="utf-8")
    assert "reason=missing_base_sha" in capsys.readouterr().out


def test_zero_base_fails_closed(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary"))
    assert scope.main(["--base", "0" * 40, "--event", "merge_group"]) == 0
    assert "run=true" in output.read_text(encoding="utf-8")


def test_unresolvable_merge_base_fails_closed(tmp_path: Path, monkeypatch, capsys) -> None:
    output = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary"))
    # A base that cannot exist makes git merge-base fail inside the real repo.
    assert scope.main(["--base", "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", "--event", "pull_request"]) == 0
    assert "run=true" in output.read_text(encoding="utf-8")
    captured = capsys.readouterr()
    assert "reason=merge_base_unresolvable" in captured.err


def test_denominator_roundtrip_json() -> None:
    data = json.loads(_DENOMINATOR.read_text(encoding="utf-8"))
    assert scope.matching_paths(["uv.lock"], data["paths"]) == ["uv.lock"]
