"""A dispatched task hears about an owned-path violation at commit time, not only at settlement (#12113)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from tests.helpers.python import project_python

REPO_ROOT = Path(__file__).resolve().parents[2]


def _git(repo: Path, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, env=env, capture_output=True, text=True, timeout=60)


def test_dispatched_commit_outside_owned_paths_is_refused_at_commit_time(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copytree(REPO_ROOT / ".githooks", repo / ".githooks", ignore=shutil.ignore_patterns("__pycache__"))
    # The tracked hooks resolve the project interpreter and the dispatcher package from the worktree.
    (repo / "scripts").symlink_to(REPO_ROOT / "scripts", target_is_directory=True)
    (repo / ".venv").symlink_to(Path(project_python()).parents[1], target_is_directory=True)
    (repo / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.pop("LEARN_UKRAINIAN_DISPATCH_TASK_ID", None)
    # The base commit is made before the tracked hooks are enabled; only the commit under test runs them.
    for args in (("init", "-q", "-b", "main"), ("config", "user.email", "hook-test@example.invalid"),
                 ("config", "user.name", "Hook Test"), ("commit", "-q", "--allow-empty", "-m", "base"),
                 ("config", "core.hooksPath", ".githooks")):
        assert _git(repo, *args, env=env).returncode == 0
    base = _git(repo, "rev-parse", "HEAD", env=env).stdout.strip()

    tasks = tmp_path / "tasks"
    tasks.mkdir()
    (tasks / "owned-paths-task.json").write_text(json.dumps({
        "task_id": "owned-paths-task", "mode": "workspace-write", "owned_paths": ["owned"],
        "worktree_path": str(repo), "worktree_base_ref": "main", "worktree_base_sha": base,
    }), encoding="utf-8")
    (repo / "outside.txt").write_text("out of scope\n", encoding="utf-8")
    assert _git(repo, "add", "outside.txt", env=env).returncode == 0

    task_env = {**env, "LEARN_UKRAINIAN_DISPATCH_TASK_ID": "owned-paths-task", "LU_TASKS_DIR": str(tasks)}
    commit = _git(repo, "commit", "-q", "-m", "outside change", env=task_env)

    assert commit.returncode != 0
    assert "outside.txt" in commit.stderr
    assert "Drop the change" in commit.stderr and "start a new task with wider owned paths" in commit.stderr
    assert _git(repo, "rev-parse", "HEAD", env=env).stdout.strip() == base
