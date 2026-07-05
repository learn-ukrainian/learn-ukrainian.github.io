"""Regression tests for the agent git shim's branch-switch guard.

INCIDENT 2026-07-05 (fork bomb): the shim spawned the worktree-containment
python guard for EVERY git subcommand, and the guard's own ``_run_git`` calls
bare ``git`` which PATH-resolves back to the shim — infinite bash+python
recursion until the per-user process limit (~2,200 stuck processes observed,
machine-wide fork failures).

Contract under test (scripts/agent_runtime/shims/git):
1. Non-checkout/switch subcommands NEVER spawn the python guard (bash pre-filter).
2. checkout/switch DO consult the guard.
3. With AGENT_GIT_SHIM_GUARD_ACTIVE=1 (set by the shim around the guard call),
   even checkout/switch skip the guard — breaking any nested recursion.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SHIM_SOURCE = REPO_ROOT / "scripts" / "agent_runtime" / "shims" / "git"

PYTHON_STUB = """#!/usr/bin/env bash
# Records that the containment guard python was invoked, then declines to block.
echo invoked >> "$(dirname "$0")/../guard-invocations.log"
exit 1
"""


@pytest.fixture()
def shim_fixture(tmp_path: Path) -> dict[str, Path]:
    """Copy the shim into an isolated fake repo root with a stub guard python.

    The shim derives repo_root from its own location (shim_dir/../../..), so a
    copy rooted at tmp_path uses tmp_path/.venv/bin/python — our stub — instead
    of the real containment guard.
    """
    shim_dir = tmp_path / "scripts" / "agent_runtime" / "shims"
    shim_dir.mkdir(parents=True)
    shim_copy = shim_dir / "git"
    shutil.copy2(SHIM_SOURCE, shim_copy)

    stub_dir = tmp_path / ".venv" / "bin"
    stub_dir.mkdir(parents=True)
    stub = stub_dir / "python"
    stub.write_text(PYTHON_STUB, encoding="utf-8")
    stub.chmod(0o755)

    workdir = tmp_path / "repo"
    workdir.mkdir()
    # Clean env: when this test runs under a git hook (pre-commit), inherited
    # GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE would redirect `git init` out of the
    # fixture directory.
    subprocess.run(
        ["git", "init", "-q", str(workdir)],
        check=True,
        env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin", "HOME": str(tmp_path)},
    )

    return {"shim": shim_copy, "workdir": workdir, "log": tmp_path / ".venv" / "guard-invocations.log"}


def _run_shim(fx: dict[str, Path], *args: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        "HOME": str(fx["workdir"]),
        "AGENT_NO_MERGE": "1",
    }
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [str(fx["shim"]), *args],
        cwd=fx["workdir"],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def test_non_switch_subcommand_never_spawns_guard(shim_fixture: dict[str, Path]) -> None:
    """`git status` through the shim must not fork the python guard (fork-bomb vector)."""
    result = _run_shim(shim_fixture, "status", "--porcelain")
    assert result.returncode == 0, result.stderr
    assert not shim_fixture["log"].exists(), "guard python was spawned for a non-checkout subcommand"


def test_checkout_consults_guard(shim_fixture: dict[str, Path]) -> None:
    """checkout/switch still route through the containment guard."""
    _run_shim(shim_fixture, "checkout", "some-branch")
    assert shim_fixture["log"].exists(), "guard python was NOT consulted for checkout"


def test_sentinel_fails_closed_on_branch_switch(shim_fixture: dict[str, Path]) -> None:
    """checkout/switch under the sentinel is DENIED without spawning the guard.

    Fail-closed design (codex review msg 2014): the guard's subtree only runs
    read-only plumbing, so a sentinel-bearing checkout/switch is recursion or
    spoofing — both must be blocked, never allowed and never recursed into.
    """
    result = _run_shim(
        shim_fixture,
        "checkout",
        "some-branch",
        extra_env={"AGENT_GIT_SHIM_GUARD_ACTIVE": "1"},
    )
    assert not shim_fixture["log"].exists(), "guard python spawned under sentinel — recursion possible"
    assert result.returncode == 1
    assert "fail-closed sentinel" in result.stderr


def test_sentinel_passes_readonly_plumbing(shim_fixture: dict[str, Path]) -> None:
    """Non-switch commands under the sentinel pass through without the guard."""
    result = _run_shim(
        shim_fixture,
        "status",
        "--porcelain",
        extra_env={"AGENT_GIT_SHIM_GUARD_ACTIVE": "1"},
    )
    assert result.returncode == 0, result.stderr
    assert not shim_fixture["log"].exists()


def test_push_deny_still_active_with_sentinel(shim_fixture: dict[str, Path]) -> None:
    """The push-to-main deny is bash-only and must survive the sentinel path."""
    result = _run_shim(
        shim_fixture,
        "push",
        "origin",
        "main",
        extra_env={"AGENT_GIT_SHIM_GUARD_ACTIVE": "1"},
    )
    assert result.returncode == 1
    assert "cannot push directly to main" in result.stderr
