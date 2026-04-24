"""Regression tests for deploy-script idempotency checks."""

from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
DEPLOY_SCRIPT = Path("scripts/deploy_prompts.sh")
CHECK_SCRIPT = Path("scripts/check_rules_deployment.sh")
DRIFT_TARGET = Path(".claude/rules/critical-rules.md")


def _copy_repo_subset(target: Path) -> None:
    for directory in ("claude_extensions", "gemini_extensions"):
        shutil.copytree(REPO_ROOT / directory, target / directory, symlinks=True)

    for relative_path in (
        DEPLOY_SCRIPT,
        CHECK_SCRIPT,
        Path("scripts/lint_prompts.py"),
        Path("scripts/lint/lint_prompts.py"),
    ):
        destination = target / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative_path, destination)

    bin_dir = target / ".venv" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    python_wrapper = bin_dir / "python"
    python_wrapper.write_text(
        "#!/usr/bin/env bash\n"
        f"exec {shlex.quote(str(PROJECT_PYTHON))} \"$@\"\n",
        encoding="utf-8",
    )
    python_wrapper.chmod(0o755)


def _init_checkout(tmp_path: Path) -> Path:
    assert PROJECT_PYTHON.exists(), f"Expected interpreter missing: {PROJECT_PYTHON}"
    repo = tmp_path / "repo"
    repo.mkdir()
    _copy_repo_subset(repo)
    return repo


def _run(repo: Path, script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script)],
        cwd=repo,
        capture_output=True,
        check=False,
        text=True,
    )


def test_fresh_deploy_produces_synced_output(tmp_path: Path) -> None:
    """A clean checkout should deploy successfully and pass drift checks."""
    repo = _init_checkout(tmp_path)

    deploy_result = _run(repo, DEPLOY_SCRIPT)
    assert deploy_result.returncode == 0, (
        f"deploy failed:\nstdout: {deploy_result.stdout}\nstderr: {deploy_result.stderr}"
    )

    check_result = _run(repo, CHECK_SCRIPT)
    assert check_result.returncode == 0, (
        "drift check failed after fresh deploy:\n"
        f"stdout: {check_result.stdout}\nstderr: {check_result.stderr}"
    )


def test_drift_is_caught(tmp_path: Path) -> None:
    """Post-deploy edits to a target tree must be reported as drift."""
    repo = _init_checkout(tmp_path)

    deploy_result = _run(repo, DEPLOY_SCRIPT)
    assert deploy_result.returncode == 0, (
        f"deploy failed:\nstdout: {deploy_result.stdout}\nstderr: {deploy_result.stderr}"
    )

    drifted_file = repo / DRIFT_TARGET
    assert drifted_file.exists(), f"Expected deployed file missing: {drifted_file}"
    drifted_file.write_text(
        drifted_file.read_text(encoding="utf-8") + "\n# drift injected by test\n",
        encoding="utf-8",
    )

    check_result = _run(repo, CHECK_SCRIPT)
    combined_output = f"{check_result.stdout}\n{check_result.stderr}"
    assert check_result.returncode != 0
    assert "Deploy-script drift between claude_extensions and .claude" in combined_output
    assert "critical-rules.md" in combined_output
