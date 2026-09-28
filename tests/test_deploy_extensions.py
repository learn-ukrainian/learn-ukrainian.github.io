"""Run the launcher deploy fail-honest fixtures under the required pytest gate.

``scripts/audit/test_deploy_extensions.sh`` exercises
``scripts/lib/deploy_extensions.sh`` — the helper both launchers
(``start-claude.sh``, ``start-codex.sh``) use to deploy
``agents_extensions/shared`` into the gitignored runtime dirs at startup.
The old inline blocks ran the deploy behind ``2>/dev/null || true`` and then
unconditionally printed a success line, so a failing deploy (orphan-path
guard trip, prompt-lint violation, rsync error) silently launched against a
STALE ``.claude``/``.codex``. This wrapper makes the failure banner and the
launcher wiring load-bearing in the required ``Test (pytest)`` job.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = _REPO_ROOT / "scripts" / "audit" / "test_deploy_extensions.sh"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_deploy_extensions_fixtures() -> None:
    assert _FIXTURES.is_file(), f"missing deploy fixtures: {_FIXTURES}"
    result = subprocess.run(
        ["bash", str(_FIXTURES)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"deploy fixtures failed (rc={result.returncode})\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    assert "ok - deploy extensions fixtures passed" in result.stdout


# --- interpreter resolution from a linked worktree (#9118) -------------------

_GIT_ENV_KEYS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")


def _git(cwd: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_KEYS}
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd, check=True, capture_output=True, env=env, timeout=30,
    )


def _make_worktree_fixture(tmp_path: Path, *, primary_venv: bool) -> tuple[Path, Path]:
    """Primary git checkout + linked worktree carrying only the deploy helper.

    The worktree has no ``.venv`` (as dispatch worktrees never do); the primary
    optionally has one whose ``python`` is the interpreter running this test.
    """
    primary = tmp_path / "primary"
    worktree = tmp_path / "worktree"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    (primary / "README").write_text("x\n")
    _git(primary, "add", "README")
    _git(primary, "commit", "-q", "-m", "init")
    _git(primary, "worktree", "add", "-q", "-b", "wt", str(worktree))
    for rel in (
        "scripts/lib/deploy_extensions.sh",
        "scripts/deploy/update_agent_deploy_status.py",
        "scripts/deploy/agent_directory.py",
    ):
        (worktree / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / rel, worktree / rel)
    (worktree / "package.json").write_text('{"scripts": {"agents:deploy": "true"}}\n')
    if primary_venv:
        (primary / ".venv" / "bin").mkdir(parents=True)
        (primary / ".venv" / "bin" / "python").symlink_to(sys.executable)
    return primary, worktree


def _run_deploy(worktree: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir(exist_ok=True)
    npm = fake_bin / "npm"
    npm.write_text("#!/usr/bin/env bash\nexit 0\n")
    npm.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_KEYS}
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    script = (
        f'source "{worktree}/scripts/lib/deploy_extensions.sh"; '
        f'deploy_agent_extensions "{worktree}" agents:deploy'
    )
    return subprocess.run(
        ["bash", "-c", script], cwd=tmp_path, capture_output=True, text=True,
        timeout=60, env=env,
    )


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_deploy_status_helper_uses_primary_interpreter_from_worktree(tmp_path: Path) -> None:
    _primary, worktree = _make_worktree_fixture(tmp_path, primary_venv=True)
    stale = worktree / ".agent"
    stale.mkdir()
    (stale / "last-deploy-status").write_text("FAILED\n")

    result = _run_deploy(worktree, tmp_path)

    assert not (worktree / ".venv").exists()
    assert result.returncode == 0, result.stderr
    assert "Agent extensions deployed" in result.stdout
    assert not (stale / "last-deploy-status").exists(), "breadcrumb was not cleared"
    assert "unsafe .agent root" not in result.stderr


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_deploy_status_helper_reports_missing_interpreter_not_unsafe_root(tmp_path: Path) -> None:
    primary, worktree = _make_worktree_fixture(tmp_path, primary_venv=False)

    result = _run_deploy(worktree, tmp_path)

    assert result.returncode == 1
    assert "project interpreter not found:" in result.stderr
    assert f"{worktree}/.venv/bin/python" in result.stderr
    assert f"{primary.resolve()}/.venv/bin/python" in result.stderr
    assert "unsafe .agent root" not in result.stderr
    assert "Agent extensions deployed" not in result.stdout


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_deploy_status_helper_still_reports_unsafe_agent_root(tmp_path: Path) -> None:
    _primary, worktree = _make_worktree_fixture(tmp_path, primary_venv=True)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (worktree / ".agent").symlink_to(elsewhere)

    result = _run_deploy(worktree, tmp_path)

    assert result.returncode == 1
    assert "refused an unsafe .agent root" in result.stderr
    assert "project interpreter not found" not in result.stderr
