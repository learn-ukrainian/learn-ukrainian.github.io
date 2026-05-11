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
DRIFT_TARGET = Path(".claude/rules/pipeline.md")
CODEX_HOOK_TARGET = Path(".codex/hooks/session-setup.sh")
UNSCOPED_RULE_FILES = (
    "critical-rules.md",
    "non-negotiable-rules.md",
    "workflow.md",
    "delegate-must-use-worktree.md",
    "cli-help-standard.md",
    "model-assignment.md",
)
CLAUDE_RULE_FILES = (
    "_load-via-api.md",
    "activity-yaml.md",
    "goal-driven-runs.md",
    "mcp-sources-and-dictionaries.md",
    "pipeline.md",
    "ukrainian-linguistics.md",
)


def _copy_repo_subset(target: Path) -> None:
    for directory in ("claude_extensions", "gemini_extensions"):
        shutil.copytree(REPO_ROOT / directory, target / directory, symlinks=True)

    for relative_path in (
        DEPLOY_SCRIPT,
        CHECK_SCRIPT,
        Path("scripts/lint_prompts.py"),
        Path("scripts/lint/lint_prompts.py"),
        Path("scripts/lint/lint_agent_skills.py"),
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


def _run_command(repo: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
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
    assert (repo / CODEX_HOOK_TARGET).exists()
    deployed_claude_rules = sorted(
        path.name for path in (repo / ".claude" / "rules").glob("*.md")
    )
    assert deployed_claude_rules == sorted(CLAUDE_RULE_FILES)
    for filename in UNSCOPED_RULE_FILES:
        assert not (repo / ".claude" / "rules" / filename).exists()
        assert (repo / ".agent" / "rules" / filename).exists()
        assert (repo / ".gemini" / "rules" / filename).exists()
        assert (repo / ".codex" / "rules" / filename).exists()

    codex_hooks_diff = _run_command(
        repo,
        ["diff", "-rq", "claude_extensions/hooks", ".codex/hooks"],
    )
    assert codex_hooks_diff.returncode == 0, (
        "Codex hooks drift after fresh deploy:\n"
        f"stdout: {codex_hooks_diff.stdout}\nstderr: {codex_hooks_diff.stderr}"
    )


def test_claude_rule_exclusion_list_covers_unscoped_files() -> None:
    """The Claude-only exclusion list must cover every always-load rule."""
    script = (REPO_ROOT / DEPLOY_SCRIPT).read_text(encoding="utf-8")
    for filename in UNSCOPED_RULE_FILES:
        assert f'"rules/{filename}"' in script


def test_second_deploy_is_noop_for_codex_target(tmp_path: Path) -> None:
    """Two consecutive deploys should leave the Codex target unchanged."""
    repo = _init_checkout(tmp_path)

    first_result = _run(repo, DEPLOY_SCRIPT)
    assert first_result.returncode == 0, (
        f"first deploy failed:\nstdout: {first_result.stdout}\nstderr: {first_result.stderr}"
    )

    second_result = _run(repo, DEPLOY_SCRIPT)
    assert second_result.returncode == 0, (
        f"second deploy failed:\nstdout: {second_result.stdout}\nstderr: {second_result.stderr}"
    )
    assert "claude_extensions → .codex: no changes" in second_result.stdout
    assert "No changes to deploy." in second_result.stdout


def test_codex_orphan_is_caught(tmp_path: Path) -> None:
    """Undeclared destination-only Codex paths must abort the deploy."""
    repo = _init_checkout(tmp_path)
    orphan = repo / ".codex" / "stale-only.txt"
    orphan.parent.mkdir(parents=True)
    orphan.write_text("stale\n", encoding="utf-8")

    deploy_result = _run(repo, DEPLOY_SCRIPT)
    combined_output = f"{deploy_result.stdout}\n{deploy_result.stderr}"

    assert deploy_result.returncode != 0
    assert "claude_extensions → .codex" in combined_output
    assert "undeclared orphan 'stale-only.txt'" in combined_output


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
    assert "pipeline.md" in combined_output
