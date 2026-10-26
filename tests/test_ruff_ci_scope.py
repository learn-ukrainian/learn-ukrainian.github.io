"""Guard: the CI Ruff check (scripts/ci/checks.sh) must lint scripts/, tests/, and agents_extensions/ (#7262)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from tests.test_ci_pr_triggers import _EVENTS, _condition, _run_gate

pytestmark = pytest.mark.repo_invariant

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / "scripts" / "ci" / "checks.sh"
_PRE_COMMIT = _REPO_ROOT / ".pre-commit-config.yaml"
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


def _local_hooks() -> dict[str, dict]:
    config = yaml.safe_load(_PRE_COMMIT.read_text(encoding="utf-8"))
    local_repos = [repo for repo in config["repos"] if repo.get("repo") == "local"]
    assert len(local_repos) == 1, "expected one local repository in .pre-commit-config.yaml"
    return {hook["id"]: hook for hook in local_repos[0]["hooks"]}


# CI Gate's full-suite shards run these two; PR admission collects tests (#11315). The
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


def test_pre_commit_sparse_collection_guard_is_owned_by_required_ci() -> None:
    """Reject pytest returning to push hooks or the slow sparse guard losing required CI ownership."""
    hooks = _local_hooks()
    assert "sparse-collection-guard" not in hooks, "sparse collection belongs in required CI, not push hooks"
    target = "tests/test_sparse_collection_guard.py::test_tree_referencing_modules_collect_when_sparse_trees_are_absent"
    stray = [hook_id for hook_id, hook in hooks.items() if "pytest" in hook.get("entry", "")]
    assert not stray, f"pytest hooks {stray} must not run during a push, including through implicit stages"
    workflow = yaml.safe_load((_REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    jobs = workflow["jobs"]
    assert "checks" in jobs["ci-gate"]["needs"], "CI Gate must require Checks"
    verdict = next(step for step in jobs["ci-gate"]["steps"] if step.get("name") == "Require every job")
    assert verdict["run"] == '"$PYTHON_BIN" -m scripts.ci.gate'
    assert verdict["env"]["NEEDS_JSON"] == "${{ toJSON(needs) }}"
    result = _run_gate("pull_request", CHECKS="failure")
    assert result.returncode != 0, "Checks must participate in the gate verdict"
    assert "checks: failure, expected success" in result.stdout
    steps = [step for step in jobs["checks"]["steps"] if target in step.get("run", "")]
    assert len(steps) == 1, "Checks must explicitly run the existing sparse collection guard node once"
    step = steps[0]
    assert step["if"] == "github.event_name != 'pull_request'"
    for event, github in _EVENTS.items():
        assert _condition(step["if"], {"github": github}) == (event not in {"opened", "synchronize", "reopened"})
    assert not step.get("continue-on-error"), "the sparse guard must block required Checks on failure"
    invocation = step["run"]
    assert ".venv/bin/python -m pytest" in invocation
    assert "--override-ini addopts=-q" in invocation, "the sparse guard must override pytest defaults"
    assert "-m slow" in invocation, "the slow sparse guard must not inherit the shard's marker exclusion"
