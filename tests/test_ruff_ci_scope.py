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


def _local_hooks() -> dict[str, dict]:
    config = yaml.safe_load(_PRE_COMMIT.read_text(encoding="utf-8"))
    local_repos = [repo for repo in config["repos"] if repo.get("repo") == "local"]
    assert len(local_repos) == 1, "expected one local repository in .pre-commit-config.yaml"
    return {hook["id"]: hook for hook in local_repos[0]["hooks"]}


# CI Gate's pytest shards run these two on every pull request and merge group (#11315); the
# push gate runs no tests of its own (#11276), so a pytest hook at any stage here only adds
# local wall time. A hook with no `stages` runs at every stage, so absence is the only pin.
_CI_COVERED_PYTEST_GUARDS = ("repo-wide-marker-invariant", "task-store-resolver-guard")


def test_pre_commit_pytest_guards_covered_by_ci_are_absent() -> None:
    """A CI-sharded pytest guard re-added to pre-commit (any stage) re-adds ~85 s to every push (#11315)."""
    hooks = _local_hooks()
    present = [hook_id for hook_id in _CI_COVERED_PYTEST_GUARDS if hook_id in hooks]
    assert not present, f"{present} run in CI shards already; remove them from .pre-commit-config.yaml (#11315)"
    stray = [
        hook_id
        for hook_id, hook in hooks.items()
        if any(
            target in hook.get("entry", "")
            for target in ("tests/test_repo_wide_marker_invariant.py", "tests/test_conftest_task_store_guard.py")
        )
    ]
    assert not stray, f"hooks {stray} run a CI-covered guard test under another id (#11315)"


def test_pre_commit_sparse_collection_guard_stays_at_pre_push() -> None:
    """The sparse guard's test is `slow`, which no CI shard runs, so it must stay at pre-push (#11315)."""
    hook = _local_hooks().get("sparse-collection-guard")
    assert hook is not None, "sparse-collection-guard is missing; no CI shard runs its test (marked slow) (#11315)"
    assert hook.get("stages") == ["pre-push"], "sparse-collection-guard stages mismatch"
    assert hook.get("pass_filenames") is False, "sparse-collection-guard pass_filenames must be False"
    assert hook.get("files") == r"^tests/.*\.py$", "sparse-collection-guard files filter mismatch"
    target = "tests/test_sparse_collection_guard.py::test_tree_referencing_modules_collect_when_sparse_trees_are_absent"
    assert target in hook.get("entry", ""), f"sparse-collection-guard entry must reference {target}"
    assert "--override-ini addopts=-q" in hook.get("entry", ""), "sparse-collection-guard entry must override addopts"
