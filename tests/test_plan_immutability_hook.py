"""Tests for the staged plan immutability hook."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_SCRIPT = REPO_ROOT / "scripts" / "pre_commit" / "check_plan_immutability.py"
PLAN_PATH = Path("curriculum/l2-uk-en/plans/a1/test-plan.yaml")


def _clean_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        env=_clean_env(),
        text=True,
    )


def _project_python() -> str:
    """Return the Python interpreter that should invoke the hook.

    Tests must run both locally (where ``.venv/bin/python`` exists) and on
    CI (which uses the actions/setup-python runner — no ``.venv``). Using
    ``sys.executable`` picks up whichever Python is running pytest, so
    both environments work without special-casing.
    """
    return sys.executable


def _write_plan(path: Path, version: str, title: str) -> str:
    content = yaml.safe_dump(
        {
            "module": 1,
            "slug": "test-plan",
            "version": version,
            "level": "a1",
            "sequence": 1,
            "title": title,
            "word_target": 1200,
            "phase": "A1.1",
            "content_outline": [
                {"section": "Intro", "words": 900},
                {"section": "Summary", "words": 300},
            ],
        },
        allow_unicode=True,
        sort_keys=False,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return content


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")

    plan_file = repo / PLAN_PATH
    _write_plan(plan_file, "1.0", "Base plan")
    _git(repo, "add", str(PLAN_PATH))
    _git(repo, "commit", "-m", "init")
    return repo


def _run_hook(repo: Path, commit_message: str) -> subprocess.CompletedProcess[str]:
    commit_msg_file = repo / ".git" / "COMMIT_EDITMSG"
    commit_msg_file.write_text(commit_message, encoding="utf-8")
    return subprocess.run(
        [_project_python(), str(HOOK_SCRIPT), str(commit_msg_file)],
        cwd=repo,
        check=False,
        capture_output=True,
        env=_clean_env(),
        text=True,
    )


def test_plan_edit_with_bumped_version_and_bak_passes(tmp_path: Path):
    repo = _init_repo(tmp_path)
    plan_file = repo / PLAN_PATH
    old_content = plan_file.read_text(encoding="utf-8")

    _write_plan(plan_file, "1.1", "Updated plan")
    (repo / f"{PLAN_PATH}.bak").write_text(old_content, encoding="utf-8")

    _git(repo, "add", str(PLAN_PATH), f"{PLAN_PATH}.bak")
    result = _run_hook(repo, "feat: update plan\n")

    assert result.returncode == 0
    assert result.stderr == ""


def test_plan_edit_without_version_bump_fails(tmp_path: Path):
    repo = _init_repo(tmp_path)
    plan_file = repo / PLAN_PATH
    old_content = plan_file.read_text(encoding="utf-8")

    _write_plan(plan_file, "1.0", "Updated plan")
    (repo / f"{PLAN_PATH}.bak").write_text(old_content, encoding="utf-8")

    _git(repo, "add", str(PLAN_PATH), f"{PLAN_PATH}.bak")
    result = _run_hook(repo, "feat: mutate plan\n")

    assert result.returncode == 1
    assert "version not bumped" in result.stderr


def test_plan_edit_without_bak_fails(tmp_path: Path):
    repo = _init_repo(tmp_path)
    plan_file = repo / PLAN_PATH

    _write_plan(plan_file, "1.1", "Updated plan")

    _git(repo, "add", str(PLAN_PATH))
    result = _run_hook(repo, "feat: mutate plan\n")

    assert result.returncode == 1
    assert "missing" in result.stderr
    assert ".bak" in result.stderr


def test_autofix_commit_tag_bypasses_hook(tmp_path: Path):
    repo = _init_repo(tmp_path)
    plan_file = repo / PLAN_PATH

    _write_plan(plan_file, "1.0", "Updated plan")
    _git(repo, "add", str(PLAN_PATH))
    result = _run_hook(repo, "chore: pipeline repair [auto-fix-plan-vocab]\n")

    assert result.returncode == 0
    assert result.stderr == ""
