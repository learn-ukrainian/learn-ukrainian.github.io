"""Guard: the CI Ruff check (scripts/ci/checks.sh) must lint scripts/, tests/, and agents_extensions/ (#7262)."""

from __future__ import annotations

import re
import shlex
import tomllib
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.repo_invariant

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / "scripts" / "ci" / "checks.sh"
_PRE_COMMIT = _REPO_ROOT / ".pre-commit-config.yaml"
_LOCK = _REPO_ROOT / "requirements-lock.txt"

# Required trees for the PR-tier Ruff job (dashboards/ may be empty).
_REQUIRED_RUFF_PATHS = ("scripts/", "tests/", "agents_extensions/")


def _ruff_check_invocation(ci_text: str) -> str:
    """Return the `ruff check …` command line from the ruff job step."""
    match = re.search(
        r"(?m)^check \"Ruff\" \.venv/bin/python -m ruff check[^\n]*$",
        ci_text,
    )
    assert match is not None, (
        f"{_CI.as_posix()} has no `check \"Ruff\" .venv/bin/python -m ruff check …` line — "
        "the Checks job must run ruff check against the repo Python trees"
    )
    return match.group(0).removeprefix('check "Ruff" ')


def test_ci_ruff_job_lints_required_python_trees() -> None:
    """Fail if the Ruff job reverts to scripts-only (or drops tests/)."""
    ci_text = _CI.read_text(encoding="utf-8")
    invocation = _ruff_check_invocation(ci_text)
    missing = [path for path in _REQUIRED_RUFF_PATHS if path not in invocation]
    assert not missing, (
        f"Ruff CI invocation is missing required path(s) {missing!r}: {invocation!r}. "
        "Expected `python -m ruff check` to include scripts/, tests/, and agents_extensions/ "
        "(see #7262)."
    )


def _pre_commit_ruff() -> tuple[dict, dict]:
    config = yaml.safe_load(_PRE_COMMIT.read_text(encoding="utf-8"))
    matches = [repo for repo in config["repos"] if repo["repo"] == "https://github.com/astral-sh/ruff-pre-commit"]
    assert len(matches) == 1, "expected one ruff-pre-commit repository"
    hooks = [hook for hook in matches[0]["hooks"] if hook["id"] == "ruff"]
    assert len(hooks) == 1, "expected one Ruff lint hook"
    return matches[0], hooks[0]


def test_pre_commit_ruff_version_matches_ci_lock() -> None:
    """A pre-commit Ruff upgrade must move with CI's lockfile pin."""
    pins = re.findall(r"(?m)^ruff==([^\s#]+)", _LOCK.read_text(encoding="utf-8"))
    assert len(pins) == 1, "requirements-lock.txt must have one Ruff pin"
    repo, _ = _pre_commit_ruff()
    assert repo["rev"] == f"v{pins[0]}"


def test_pre_commit_ruff_checks_the_same_trees_as_ci() -> None:
    """Pre-commit must lint staged files in CI's trees with config discovery."""
    _, hook = _pre_commit_ruff()
    ci_argv = shlex.split(_ruff_check_invocation(_CI.read_text(encoding="utf-8")))
    assert ci_argv[:4] == [".venv/bin/python", "-m", "ruff", "check"]
    assert "args" not in hook
    assert hook.get("pass_filenames", True) is True
    assert hook.get("always_run", False) is False
    assert "stages" not in hook or "pre-commit" in hook["stages"]
    allowed = re.compile(hook["files"])
    for path in ci_argv[4:]:
        assert allowed.search(f"{path}example.py")
    assert not allowed.search("docs/example.md")


def test_ruff_import_roots_are_checkout_independent() -> None:
    """Ruff must classify imports without probing sparse tree presence."""
    config = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert config["tool"]["ruff"]["src"] == [".", "scripts"]
    assert "known-first-party" not in config["tool"]["ruff"].get("lint", {}).get("isort", {})


def test_pre_commit_cheap_guards_configuration() -> None:
    """The three B19 cheap repo-wide guards must be declared in .pre-commit-config.yaml at pre-push."""
    config = yaml.safe_load(_PRE_COMMIT.read_text(encoding="utf-8"))
    local_repos = [repo for repo in config["repos"] if repo.get("repo") == "local"]
    assert len(local_repos) == 1, "expected one local repository in .pre-commit-config.yaml"
    local_hooks = {hook["id"]: hook for hook in local_repos[0]["hooks"]}

    expected_guards = {
        "repo-wide-marker-invariant": {
            "stages": ["pre-push"],
            "pass_filenames": False,
            "files": r"^tests/.*\.py$",
            "test_target": "tests/test_repo_wide_marker_invariant.py",
        },
        "task-store-resolver-guard": {
            "stages": ["pre-push"],
            "pass_filenames": False,
            "files": r"^(scripts|tests)/.*\.py$",
            "test_target": "tests/test_conftest_task_store_guard.py",
        },
        "sparse-collection-guard": {
            "stages": ["pre-push"],
            "pass_filenames": False,
            "files": r"^tests/.*\.py$",
            "test_target": "tests/test_sparse_collection_guard.py::test_tree_referencing_modules_collect_when_sparse_trees_are_absent",
        },
    }

    for hook_id, expected in expected_guards.items():
        assert hook_id in local_hooks, f"missing expected B19 guard hook {hook_id!r}"
        hook = local_hooks[hook_id]
        assert hook.get("stages") == expected["stages"], f"{hook_id} stages mismatch"
        assert hook.get("pass_filenames") is False, f"{hook_id} pass_filenames must be False"
        assert hook.get("files") == expected["files"], f"{hook_id} files filter mismatch"
        assert expected["test_target"] in hook.get("entry", ""), f"{hook_id} entry must reference {expected['test_target']}"
        assert "--override-ini addopts=-q" in hook.get("entry", ""), f"{hook_id} entry must override addopts"
