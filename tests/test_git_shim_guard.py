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


DISCOVERY_REFUSAL = "OPSEC: could not list Git's commands, so the command was not run.\n"


@pytest.fixture()
def discovery_fixture(shim_fixture: dict[str, Path], tmp_path: Path) -> dict[str, Path]:
    """Real Git behind a discovery-only fault injector and downstream execution tripwire."""
    real_git = shutil.which("git", path="/usr/bin:/bin")
    assert real_git is not None
    probe = tmp_path / "discovery-git"
    probe.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "${*: -1}" == --list-cmds=builtins,main ]]; then
  if [[ "${UNIT_DISCOVERY_MODE:-real}" == real ]]; then
    exec "$UNIT_REAL_GIT" "$@"
  fi
  cat "$UNIT_DISCOVERY_NOISE" >&2
  printf 'status\nrev-parse\n'
  exit "$UNIT_DISCOVERY_EXIT"
fi
for arg in "$@"; do
  if [[ "$arg" == config ]]; then
    exec "$UNIT_REAL_GIT" "$@"
  fi
done
printf 'downstream\n' >> "$UNIT_DOWNSTREAM_MARKER"
exec "$UNIT_REAL_GIT" "$@"
""",
        encoding="utf-8",
    )
    probe.chmod(0o755)
    return {**shim_fixture, "probe": probe, "real_git": Path(real_git), "marker": tmp_path / "downstream"}


def _discovery_env(fx: dict[str, Path]) -> dict[str, str]:
    return {
        "AGENT_REAL_GIT": str(fx["probe"]),
        "UNIT_REAL_GIT": str(fx["real_git"]),
        "UNIT_DOWNSTREAM_MARKER": str(fx["marker"]),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
    }


@pytest.mark.parametrize("scope", ["global", "local", "conditional"])
@pytest.mark.parametrize(
    "filename",
    ["synthetic-token.gitconfig", "synthetic-\u202e-token.gitconfig", "synthetic-\x1b[31m-token.gitconfig", "synthetic-" + "x" * 200],
    ids=["plain", "unicode-control", "terminal-control", "long"],
)
def test_discovery_config_diagnostics_do_not_disclose_or_execute(discovery_fixture, tmp_path, scope, filename):
    """Malformed configuration must not disclose filenames or reach the requested command."""
    fx = discovery_fixture
    broken = tmp_path / filename
    broken.write_text("[broken\n", encoding="utf-8")
    env = _discovery_env(fx)
    if scope == "global":
        env["GIT_CONFIG_GLOBAL"] = str(broken)
    else:
        key = "include.path" if scope == "local" else f"includeIf.gitdir:{fx['workdir']}/.git.path"
        subprocess.run(
            [str(fx["real_git"]), "config", key, str(broken)],
            cwd=fx["workdir"], env={**_discovery_env(fx), "PATH": "/usr/bin:/bin"}, check=True, timeout=15,
        )
    control = subprocess.run(
        [str(fx["real_git"]), "--list-cmds=builtins,main"],
        cwd=fx["workdir"], env={**env, "PATH": "/usr/bin:/bin"}, capture_output=True, timeout=15,
    )
    if scope == "global":
        assert control.returncode == 128 and b"synthetic-" in control.stderr
    else:
        # Git's early command listing does not read the repository configuration.
        # The subsequent alias probe must refuse it without disclosing diagnostics.
        assert control.returncode == 0 and control.stderr == b""
    result = _run_shim(fx, "status", "--porcelain", extra_env=env)
    assert result.returncode == 2
    refusal = DISCOVERY_REFUSAL if scope == "global" else "OPSEC: could not check Git's aliases for 'status', so it was not run.\n       cause: git config failed;\n"
    assert result.stdout == "" and result.stderr == refusal
    assert not fx["marker"].exists()


@pytest.mark.parametrize("exit_code", [0, 73], ids=["success", "failure"])
@pytest.mark.parametrize("size", [80, 256 * 1024], ids=["small", "oversized"])
def test_discovery_noise_is_suppressed_without_changing_execution(discovery_fixture, tmp_path, exit_code, size):
    """Noisy discovery must not disclose bytes or turn a failed listing into permission to run."""
    fx = discovery_fixture
    noise = tmp_path / "noise"
    noise.write_bytes((b"synthetic-token\x1b[31m\xe2\x80\xae\r\n" * (size // 20 + 1))[:size])
    env = {
        **_discovery_env(fx), "UNIT_DISCOVERY_MODE": "synthetic", "UNIT_DISCOVERY_NOISE": str(noise),
        "UNIT_DISCOVERY_EXIT": str(exit_code),
    }
    result = _run_shim(fx, "status", "--porcelain", extra_env=env)
    assert result.returncode == (2 if exit_code else 0)
    assert result.stdout == "" and result.stderr == (DISCOVERY_REFUSAL if exit_code else "")
    assert fx["marker"].exists() == (exit_code == 0)
    if not exit_code:
        assert fx["marker"].read_text() == "downstream\n"


def test_discovery_suppression_preserves_legitimate_downstream_stderr(discovery_fixture, tmp_path):
    """Suppressing preflight stderr must not silence a real Git command's diagnostic or exit status."""
    fx = discovery_fixture
    noise = tmp_path / "noise"
    noise.write_text("synthetic-preflight-secret\n")
    env = {
        **_discovery_env(fx), "UNIT_DISCOVERY_MODE": "synthetic", "UNIT_DISCOVERY_NOISE": str(noise),
        "UNIT_DISCOVERY_EXIT": "0",
    }
    args = ("rev-parse", "--verify", "refs/heads/synthetic-missing")
    control = subprocess.run(
        [str(fx["real_git"]), *args], cwd=fx["workdir"], env={**env, "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True, timeout=15,
    )
    assert control.returncode == 128
    assert control.stdout == "" and control.stderr == "fatal: Needed a single revision\n"
    result = _run_shim(fx, *args, extra_env=env)
    assert (result.returncode, result.stdout, result.stderr) == (128, "", "fatal: Needed a single revision\n")
    assert fx["marker"].read_text() == "downstream\n"


REENTRY_REFUSAL = "error: git shim re-entry refused (recursion limit).\n"


@pytest.mark.parametrize("selection", ["explicit", "original-path"])
@pytest.mark.parametrize("command", ["--version", "status"])
@pytest.mark.parametrize("invoke", ["exec git", "git"])
def test_wrapper_reentry_is_bounded_with_hard_timeout(shim_fixture, tmp_path, selection, command, invoke):
    """Both exec loops and child-spawning wrappers must stop, including discovery probes."""
    fx = shim_fixture
    wrapper_dir = tmp_path / "bin"
    wrapper_dir.mkdir()
    wrapper = wrapper_dir / "git"
    calls = tmp_path / "wrapper-calls"
    wrapper.write_text(
        '#!/bin/sh\n'
        'printf "%s:%s\\n" "$LU_GIT_SHIM_ACTIVE" "$LU_GIT_SHIM_DEPTH" >> "$UNIT_CALLS"\n'
        f'{invoke} "$@"\n'
    )
    wrapper.chmod(0o755)
    env = {
        "HOME": str(tmp_path),
        "PATH": f"{fx['shim'].parent}:{wrapper_dir}:/usr/bin:/bin",
        "AGENT_ORIGINAL_PATH": f"{wrapper_dir}:/usr/bin:/bin",
        "UNIT_CALLS": str(calls),
    }
    if selection == "explicit":
        env["AGENT_REAL_GIT"] = str(wrapper)
    result = subprocess.run(
        ["timeout", "--kill-after=1s", "3s", str(fx["shim"]), command],
        cwd=fx["workdir"], env=env, capture_output=True, text=True, timeout=5, check=False,
    )
    # Discovery intentionally hides child diagnostics; the final exec preserves them.
    assert (result.returncode, result.stderr) == (
        (126, REENTRY_REFUSAL) if command == "--version" else (2, DISCOVERY_REFUSAL)
    )
    assert result.stdout == ""
    assert calls.read_text().splitlines() == [f"1:{depth}" for depth in range(1, 9)]


@pytest.mark.parametrize("depth", [None, "", "0", "8", "999999999999999999999", "1+1", "01"])
def test_reentry_marker_without_valid_depth_fails_closed(shim_fixture, depth):
    """Missing, malformed and exhausted inherited depths must refuse before any helper runs."""
    env = {"LU_GIT_SHIM_ACTIVE": "1"}
    if depth is not None:
        env["LU_GIT_SHIM_DEPTH"] = depth
    result = _run_shim(shim_fixture, "checkout", "some-branch", extra_env=env)
    assert (result.returncode, result.stdout, result.stderr) == (126, "", REENTRY_REFUSAL)
    assert not shim_fixture["log"].exists()


def test_real_git_hook_can_invoke_git_through_shim(shim_fixture, tmp_path):
    """A real pre-commit hook must retain nested Git access despite the inherited marker."""
    fx = shim_fixture
    hook_output = tmp_path / "hook-output"
    push_output = tmp_path / "push-output"
    hook = fx["workdir"] / ".git" / "hooks" / "pre-commit"
    hook.write_text(
        '#!/bin/sh\nset -eu\n'
        'test "$LU_GIT_SHIM_ACTIVE:$LU_GIT_SHIM_DEPTH" = "1:1"\n'
        'PATH="${UNIT_SHIM%/*}:$PATH"; export PATH\n'
        'test "$(command -v git)" = "$UNIT_SHIM"\n'
        'git rev-parse --is-inside-work-tree > "$UNIT_HOOK_OUT"\n'
        'if git push origin main > "$UNIT_PUSH_OUT" 2>&1; then exit 93; fi\n'
    )
    hook.chmod(0o755)
    result = _run_shim(
        fx, "-c", "user.name=Shim Test", "-c", "user.email=shim@example.com",
        "commit", "--allow-empty", "-m", "Nested hook Git",
        extra_env={
            "PATH": f"{fx['shim'].parent}:/usr/bin:/bin",
            "UNIT_SHIM": str(fx["shim"]), "UNIT_HOOK_OUT": str(hook_output),
            "UNIT_PUSH_OUT": str(push_output),
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
        },
    )
    assert result.returncode == 0, result.stderr
    assert hook_output.read_text() == "true\n"
    assert "cannot push directly to main" in push_output.read_text()


def test_reentry_markers_are_not_exported_to_containment_helper(shim_fixture, tmp_path):
    """A non-Git shim helper must receive neither new nor inherited recursion markers."""
    helper = tmp_path / "guard-python"
    helper.write_text(
        '#!/bin/sh\n'
        'test "${LU_GIT_SHIM_ACTIVE+set}" != set || exit 91\n'
        'test "${LU_GIT_SHIM_DEPTH+set}" != set || exit 92\n'
        'printf "GUARD_ALLOW\\n"\n'
    )
    helper.chmod(0o755)
    for markers in ({}, {"LU_GIT_SHIM_ACTIVE": "1", "LU_GIT_SHIM_DEPTH": "1"}):
        result = _run_shim(
            shim_fixture, "checkout", "--orphan", "fresh",
            extra_env={"AGENT_GIT_SHIM_PYTHON": str(helper), **markers},
        )
        assert result.returncode == 0, result.stderr
