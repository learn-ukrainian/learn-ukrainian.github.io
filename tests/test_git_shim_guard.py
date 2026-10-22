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
import sys
import time
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
        env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin", "HOME": str(tmp_path)}, timeout=30,
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


@pytest.mark.parametrize("hostile_name", [
    "SYNTHETIC_SECRET_IGNORE_SAFETY_REPORT_APPROVE",
    "line\nbreak\x1b[31m",
    "bidi\u202eformat\u2066separator\u2028",
])
def test_real_git_config_error_cannot_disclose_hostile_filename(shim_fixture, tmp_path, hostile_name):
    """Real Git's parser must not inject caller paths, token text, or Unicode controls."""
    bad = tmp_path / hostile_name
    bad.write_text("[alias\n")
    result = _run_shim(shim_fixture, "push", "--no-verify", extra_env={"GIT_CONFIG_GLOBAL": str(bad)})
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == (
        "OPSEC: could not check Git's aliases for 'push', so it was not run.\n"
        "       cause: git config failed;\n"
    )


# Removal of the hook supersedes its 60s cap. Every old value must now leave
# the production 10s bound unchanged, including malformed and above-cap inputs.
@pytest.mark.parametrize(("flag", "value"), [
    ("1", ""), ("1", "0"), ("1", "-1"), ("1", "1"), ("1", "12"),
    ("1", "30"), ("1", "60"), ("1", "61"), ("1", "999"),
    ("1", "1.5"), ("1", "01"), ("1", "abc"), ("1", "1; exit 0"),
    ("", "12"), ("0", "12"), ("yes", "12"),
])
def test_caller_timeout_values_cannot_raise_production_bound(shim_fixture, tmp_path, flag, value):
    """An 11s probe must refuse before the downstream command for every hostile override class."""
    stub = tmp_path / "git-tripwire"
    marker = tmp_path / "command-ran"
    stub.write_text(
        f"#!{sys.executable}\n"
        "import os, pathlib, sys, time\n"
        "if any(arg.startswith('--list-cmds=') for arg in sys.argv):\n"
        "    print('status')\n"
        "elif 'config' in sys.argv:\n"
        "    time.sleep(11)\n"
        "    print('lu-opsec.alias-probe', flush=True)\n"
        "else:\n"
        "    pathlib.Path(os.environ['COMMAND_MARKER']).write_text('ran')\n"
    )
    stub.chmod(0o755)
    started = time.monotonic()
    result = _run_shim(shim_fixture, "status", "--short", extra_env={
        "AGENT_REAL_GIT": str(stub), "COMMAND_MARKER": str(marker),
        "LU_OPSEC_ALIAS_PROBE_TEST_HOOK": flag, "LU_OPSEC_ALIAS_PROBE_TIMEOUT": value,
    })
    assert result.returncode == 2, result.stderr
    assert 9 < time.monotonic() - started < 15
    assert not marker.exists(), "downstream command ran after the production deadline"
    assert result.stderr == (
        "OPSEC: could not check Git's aliases for 'status', so it was not run.\n"
        "       cause: timeout after 10s;\n"
    )
