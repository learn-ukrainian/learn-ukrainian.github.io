"""Guard: CI Ruff job must lint scripts/, tests/, and agents_extensions/ (#7262)."""

from __future__ import annotations

import re
import shlex
import tomllib
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.repo_invariant

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
_PRE_COMMIT = _REPO_ROOT / ".pre-commit-config.yaml"
_LOCK = _REPO_ROOT / "requirements-lock.txt"

# Required trees for the PR-tier Ruff job (dashboards/ may be empty).
_REQUIRED_RUFF_PATHS = ("scripts/", "tests/", "agents_extensions/")


def _ruff_check_invocation(ci_text: str) -> str:
    """Return the `ruff check …` command line from the ruff job step."""
    match = re.search(
        r"(?m)^[ \t]*python -m ruff check[^\n]*$",
        ci_text,
    )
    assert match is not None, (
        f"{_CI.as_posix()} has no `python -m ruff check …` invocation — "
        "the Ruff job must run ruff check against the repo Python trees"
    )
    return match.group(0)


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
    assert ci_argv[:4] == ["python", "-m", "ruff", "check"]
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
