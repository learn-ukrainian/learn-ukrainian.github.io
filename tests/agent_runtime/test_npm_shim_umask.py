"""Tests for umask 022 enforcement in the npm shim for install-class subcommands (#10249)."""

import os
import subprocess
from pathlib import Path

import pytest

from tests.agent_runtime.test_npm_shim import _build_layout, _make_real

FAKE_TOOL_UMASK = r"""#!/usr/bin/env bash
umask > "$FAKE_NPM_LOG"
echo "hello" > "$PWD/created_file.txt"
"""

@pytest.fixture()
def layout(tmp_path: Path) -> dict[str, Path]:
    lo = _build_layout(tmp_path)
    # Overwrite the fake npm to just record umask and create a file
    (lo["fake_bin"] / "npm").write_text(FAKE_TOOL_UMASK, encoding="utf-8")
    (lo["fake_bin"] / "npm").chmod(0o755)
    return lo


def _run_with_umask(layout: dict[str, Path], args: list[str], caller_umask: int):
    cwd = layout["worktree"]
    path_entries = [str(layout["shim_dir"]), str(layout["fake_bin"]), "/usr/bin", "/bin"]
    env = {
        "PATH": os.pathsep.join(path_entries),
        "HOME": str(layout["tmp"]),
        "FAKE_NPM_LOG": str(layout["log"]),
    }

    def preexec():
        os.umask(caller_umask)

    layout["log"].unlink(missing_ok=True)
    created_file = cwd / "created_file.txt"
    created_file.unlink(missing_ok=True)

    proc = subprocess.run(
        [str(layout["shim_dir"] / "npm"), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        preexec_fn=preexec,
    )
    return proc, created_file

@pytest.mark.parametrize("subcommand", ["ci", "install", "i", "add", "update", "up"])
def test_install_subcommands_apply_umask_022(layout, subcommand):
    _make_real(layout) # bypass guard refusal
    proc, created_file = _run_with_umask(layout, [subcommand], 0o002)
    assert proc.returncode == 0, proc.stderr

    # Check umask recorded by the fake
    recorded_umask = layout["log"].read_text(encoding="utf-8").strip()
    assert recorded_umask == "0022"

    # Check file mode
    assert created_file.exists()
    mode = created_file.stat().st_mode
    # Under umask 022, 666 becomes 644, which is not group writable
    assert not (mode & 0o020), f"File mode {oct(mode)} should not be group-writable"

def test_install_subcommand_with_leading_flag_applies_umask_022(layout):
    _make_real(layout)
    proc, created_file = _run_with_umask(layout, ["--prefix", "x", "ci"], 0o002)
    assert proc.returncode == 0, proc.stderr

    recorded_umask = layout["log"].read_text(encoding="utf-8").strip()
    assert recorded_umask == "0022"
    mode = created_file.stat().st_mode
    assert not (mode & 0o020)

@pytest.mark.parametrize("args", [["run", "build"], ["ls"], ["--version"]])
def test_non_install_calls_keep_caller_umask(layout, args):
    _make_real(layout)
    proc, _created_file = _run_with_umask(layout, args, 0o002)
    assert proc.returncode == 0, proc.stderr

    recorded_umask = layout["log"].read_text(encoding="utf-8").strip()
    assert recorded_umask == "0002"

def test_existing_refusal_behavior_unchanged(layout):
    proc, _ = _run_with_umask(layout, ["ci"], 0o002)
    assert proc.returncode == 1
    assert "agent npm shim refused" in proc.stderr
    assert not layout["log"].exists(), "Fake npm should not have been reached"
