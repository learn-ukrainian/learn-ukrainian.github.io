"""Unit coverage for dependency-input changed-path scope (#9871)."""

from __future__ import annotations

import itertools
import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.ci import dependency_change_scope as scope

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DENOMINATOR = _REPO_ROOT / scope.DENOMINATOR_REL

_FIXTURE_DENOMINATOR = {
    "schema_version": "dependency_change_denominator_v1",
    "version": "fixture-1",
    "paths": [
        "requirements*.txt",
        "pyproject.toml",
        "package.json",
        "package-lock.json",
        "packages/*/package.json",
        "site/package.json",
        "site/package-lock.json",
    ],
}

_call_counter = itertools.count()


def _git(cwd: Path, *args: str) -> str:
    env = os.environ | {"AGENT_NO_MERGE": "0"}
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, timeout=30, env=env).strip()


def _init_repo(root: Path, *, with_site_manifest: bool = True) -> str:
    """Build a mini repo with a fixture denominator; return the root commit SHA."""
    _git(root, "init")
    _git(root, "config", "user.email", "ci@example.com")
    _git(root, "config", "user.name", "ci")
    (root / "docs").mkdir()
    (root / "site").mkdir()
    (root / "docs" / "a.md").write_text("docs\n", encoding="utf-8")
    if with_site_manifest:
        (root / "site" / "package.json").write_text('{"name":"fixture"}\n', encoding="utf-8")
    (root / "scripts" / "ci").mkdir(parents=True)
    (root / "scripts" / "ci" / "dependency_change_denominator.json").write_text(
        json.dumps(_FIXTURE_DENOMINATOR),
        encoding="utf-8",
    )
    _git(root, "add", ".")
    _git(root, "commit", "-m", "root")
    _git(root, "branch", "-M", "main")
    return _git(root, "rev-parse", "HEAD")


def _commit_all(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _run_main(
    repo: Path,
    *,
    base: str,
    head: str = "HEAD",
    event: str = "pull_request",
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str, str, str]:
    """Run scope.main in the fixture repo; return (rc, stdout, stderr, github_output)."""
    monkeypatch.chdir(repo)
    tag = next(_call_counter)
    output = tmp_path / f"github_output_{tag}"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / f"summary_{tag}.md"))
    rc = scope.main(
        [
            "--base",
            base,
            "--head",
            head,
            "--event",
            event,
            "--denominator",
            str(repo / "scripts" / "ci" / "dependency_change_denominator.json"),
        ]
    )
    captured = capsys.readouterr()
    return rc, captured.out, captured.err, output.read_text(encoding="utf-8")


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
        "packages/*/package.json",
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


def test_workspace_manifest_matches_packages_glob() -> None:
    """Root package.json declares npm workspaces under packages/* (#9871)."""
    patterns = scope.load_denominator(_DENOMINATOR)["paths"]
    assert scope.path_in_denominator("packages/activity-kit/package.json", patterns)
    assert scope.path_in_denominator("packages/v4-runtime/package.json", patterns)
    assert not scope.path_in_denominator("packages/activity-kit/package-lock.json", patterns)
    assert not scope.path_in_denominator("packages/v4-runtime/pyproject.toml", patterns)


def test_resolve_git_range_two_dot_passthrough(tmp_path: Path) -> None:
    assert scope.resolve_git_range("aaa", "bbb", mode="two-dot", cwd=tmp_path) == "aaa..bbb"
    assert scope.resolve_git_range("aaa..bbb", mode="two-dot", cwd=tmp_path) == "aaa..bbb"
    assert scope.resolve_git_range("aaa...bbb", mode="merge-base", cwd=tmp_path) == "aaa...bbb"


def test_added_manifest_runs_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    fork = _init_repo(repo)
    _git(repo, "checkout", "-b", "feature")
    (repo / "requirements-lock.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    head = _commit_all(repo, "add lockfile")

    rc, out, _err, gh_output = _run_main(
        repo, base=fork, head=head, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys
    )
    assert rc == 0
    assert "decision=run" in out
    assert scope.NOT_APPLICABLE_LINE not in out
    assert "run=true" in gh_output


def test_modified_site_manifest_runs_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    fork = _init_repo(repo)
    _git(repo, "checkout", "-b", "feature")
    (repo / "site" / "package.json").write_text('{"name":"fixture","version":"2"}\n', encoding="utf-8")
    head = _commit_all(repo, "modify site manifest")

    rc, out, _err, gh_output = _run_main(
        repo, base=fork, head=head, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys
    )
    assert rc == 0
    assert "decision=run" in out
    assert "run=true" in gh_output


def test_deleted_site_manifest_runs_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    fork = _init_repo(repo)
    _git(repo, "checkout", "-b", "feature")
    _git(repo, "rm", "site/package.json")
    head = _commit_all(repo, "delete site manifest")

    rc, out, _err, gh_output = _run_main(
        repo, base=fork, head=head, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys
    )
    assert rc == 0
    assert "decision=run" in out
    assert "run=true" in gh_output


def test_rename_away_from_site_manifest_runs_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    fork = _init_repo(repo)
    _git(repo, "checkout", "-b", "feature")
    _git(repo, "mv", "site/package.json", "site/pkg.json")
    head = _commit_all(repo, "rename manifest away")

    # Direct real-git coverage of changed_paths: both rename sides are reported.
    changed = scope.changed_paths(f"{fork}..{head}", cwd=repo)
    assert "site/package.json" in changed
    assert "site/pkg.json" in changed

    rc, out, _err, gh_output = _run_main(
        repo, base=fork, head=head, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys
    )
    assert rc == 0
    assert "decision=run" in out
    assert "run=true" in gh_output


def test_rename_onto_site_manifest_runs_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    fork = _init_repo(repo, with_site_manifest=False)
    (repo / "site" / "pkg.json").write_text('{"name":"fixture"}\n', encoding="utf-8")
    fork = _commit_all(repo, "seed pre-rename manifest")
    _git(repo, "checkout", "-b", "feature")
    _git(repo, "mv", "site/pkg.json", "site/package.json")
    head = _commit_all(repo, "rename onto site manifest")

    rc, out, _err, gh_output = _run_main(
        repo, base=fork, head=head, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys
    )
    assert rc == 0
    assert "decision=run" in out
    assert "run=true" in gh_output


def test_docs_only_change_is_not_applicable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    fork = _init_repo(repo)
    _git(repo, "checkout", "-b", "feature")
    (repo / "docs" / "b.md").write_text("more docs\n", encoding="utf-8")
    head = _commit_all(repo, "docs only")

    rc, out, _err, gh_output = _run_main(
        repo, base=fork, head=head, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys
    )
    assert rc == 0
    assert "decision=not_applicable" in out
    assert scope.NOT_APPLICABLE_LINE in out
    assert "run=false" in gh_output


def test_moved_base_docs_only_branch_is_not_applicable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Base moved with a dependency change while the PR is docs-only: merge-base semantics."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _git(repo, "checkout", "-b", "feature")
    (repo / "docs" / "feature.md").write_text("feature docs\n", encoding="utf-8")
    branch_head = _commit_all(repo, "feature docs only")

    _git(repo, "checkout", "main")
    (repo / "site" / "package.json").write_text('{"name":"moved-base"}\n', encoding="utf-8")
    base_tip = _commit_all(repo, "main advances with dependency input")

    # Two-dot sees main's dependency change; merge-base must not.
    two_dot = scope.changed_paths(f"{base_tip}..{branch_head}", cwd=repo)
    assert "site/package.json" in two_dot
    mb_range = scope.resolve_git_range(base_tip, branch_head, mode="merge-base", cwd=repo)
    assert scope.changed_paths(mb_range, cwd=repo) == ["docs/feature.md"]

    rc, out, _err, gh_output = _run_main(
        repo, base=base_tip, head=branch_head, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys
    )
    assert rc == 0
    assert "decision=not_applicable" in out
    assert scope.NOT_APPLICABLE_LINE in out
    assert "run=false" in gh_output


def test_merge_group_event_runs_audit_on_dependency_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    fork = _init_repo(repo)
    _git(repo, "checkout", "-b", "feature")
    (repo / "pyproject.toml").write_text("[project]\nname = 'fixture'\n", encoding="utf-8")
    head = _commit_all(repo, "add pyproject")

    rc, out, _err, gh_output = _run_main(
        repo, base=fork, head=head, event="merge_group", tmp_path=tmp_path,
        monkeypatch=monkeypatch, capsys=capsys,
    )
    assert rc == 0
    assert "decision=run" in out
    assert "run=true" in gh_output


def test_shallow_clone_missing_base_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    fork = _init_repo(repo)
    (repo / "docs" / "b.md").write_text("later\n", encoding="utf-8")
    _commit_all(repo, "advance main")

    clone = tmp_path / "shallow"
    env = os.environ | {"AGENT_NO_MERGE": "0"}
    subprocess.run(
        ["git", "clone", "--depth", "1", f"file://{repo}", str(clone)],
        check=True, capture_output=True, text=True, timeout=60, env=env,
    )

    rc, _out, err, gh_output = _run_main(
        clone, base=fork, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys
    )
    assert rc == 0
    assert "reason=merge_base_unresolvable" in err
    assert "run=true" in gh_output


def test_git_diff_failure_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    output = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary"))
    with (
        patch.object(scope, "resolve_git_range", return_value="abc123..HEAD"),
        patch.object(
            scope, "changed_paths", side_effect=subprocess.CalledProcessError(128, ["git", "diff"])
        ),
    ):
        assert scope.main(["--base", "abc123", "--event", "pull_request"]) == 0
    assert "run=true" in output.read_text(encoding="utf-8")
    assert "reason=git_diff_failed exit=128" in capsys.readouterr().err


def test_git_diff_timeout_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    output = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary"))
    with (
        patch.object(scope, "resolve_git_range", return_value="abc123..HEAD"),
        patch.object(
            scope, "changed_paths", side_effect=subprocess.TimeoutExpired(["git", "diff"], 30)
        ),
    ):
        assert scope.main(["--base", "abc123", "--event", "pull_request"]) == 0
    assert "run=true" in output.read_text(encoding="utf-8")
    assert "reason=git_diff_failed timeout=30s" in capsys.readouterr().err


def test_help_follows_cli_help_standard(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        scope.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for heading in ("Examples:", "Outputs:", "Exit codes:", "Related:"):
        assert heading in out
    assert ".venv/bin/python" in out
