"""Installed git hooks refuse, never pass, when a hook resource is missing (machinery #100, C-5041 R5).

Each test builds a disposable product repository, installs the real delegators with
``scripts/install_git_hooks.sh`` and commits through them. Defect classes covered: a deleted
tracked hook turning the delegator into a silent ``exit 0``; a missing or uninstalled owned-path
checker (or an in-tree package shadowing it) skipping enforcement inside a dispatched task; and a
crashing checker passing. Handled checker exceptions also refuse the commit when the task
record is missing or damaged (machinery #274, C-5045).
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from tests.helpers.python import project_python

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / "scripts" / "install_git_hooks.sh"
MISSING_HOOK = "Git hook error: tracked hook is missing or not executable:"
MISSING_CHECKER = "Git hook error: owned-path checker is not installed; refusing to skip enforcement."
_HIDDEN = {
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONSAFEPATH",
    "VIRTUAL_ENV",
    "LEARN_UKRAINIAN_DISPATCH_TASK_ID",
    "LEARN_UKRAINIAN_PYTHON",
    "LU_TASKS_DIR",
}


def _env(python: str) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_") and key not in _HIDDEN}
    # No agent git shim and no checkout on PATH: the delegator and hooks run as in a plain clone.
    env["PATH"] = "/usr/bin:/bin"
    env["LEARN_UKRAINIAN_PYTHON"] = python
    return env


def _run(argv: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=120)


def _git(repo: Path, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return _run(["/usr/bin/git", *args], repo, env)


def _head(repo: Path, env: dict[str, str]) -> str:
    return _git(repo, "rev-parse", "HEAD", env=env).stdout.strip()


def _product_repo(tmp_path: Path, env: dict[str, str]) -> Path:
    """A product repository with the tracked hooks and the delegators the real installer writes."""
    repo = (tmp_path / "product").resolve()
    repo.mkdir()
    shutil.copytree(REPO_ROOT / ".githooks", repo / ".githooks", ignore=shutil.ignore_patterns("__pycache__"))
    launcher = repo / "scripts" / "pre_commit" / "project_python.sh"
    launcher.parent.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "scripts" / "pre_commit" / "project_python.sh", launcher)
    resolver = repo / "scripts" / "lib" / "project_interpreter.sh"
    resolver.parent.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "scripts" / "lib" / "project_interpreter.sh", resolver)
    (repo / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    for args in (
        ("init", "-q", "-b", "main"),
        ("config", "user.email", "hook-test@example.invalid"),
        ("config", "user.name", "Hook Test"),
        ("commit", "-q", "--allow-empty", "-m", "base"),
    ):
        assert _git(repo, *args, env=env).returncode == 0
    installed = _run(["/usr/bin/bash", str(INSTALLER)], repo, env)
    assert installed.returncode == 0, installed.stderr
    assert "pre-commit: installed" in installed.stdout
    assert _git(repo, "config", "--get", "core.hooksPath", env=env).returncode != 0
    return repo


def _task_env(tmp_path: Path, repo: Path, env: dict[str, str], **fields: object) -> dict[str, str]:
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    record = {
        "task_id": "hook-task",
        "mode": "workspace-write",
        "owned_paths": ["owned"],
        "worktree_path": str(repo),
        "worktree_base_ref": "main",
        "worktree_base_sha": _head(repo, env),
        **fields,
    }
    (tasks / "hook-task.json").write_text(json.dumps(record), encoding="utf-8")
    return {**env, "LEARN_UKRAINIAN_DISPATCH_TASK_ID": "hook-task", "LU_TASKS_DIR": str(tasks)}


def _stage_outside(repo: Path, env: dict[str, str]) -> None:
    (repo / "outside.txt").write_text("out of scope\n", encoding="utf-8")
    assert _git(repo, "add", "outside.txt", env=env).returncode == 0


def _venv(tmp_path: Path, ownership_source: str | None) -> str:
    """A fresh interpreter without lu-machinery, or with a stub checker whose source is given."""
    venv = tmp_path / "venv"
    created = _run([project_python(), "-m", "venv", "--without-pip", str(venv)], tmp_path, _env(project_python()))
    assert created.returncode == 0, created.stderr
    python = venv / "bin" / "python"
    if ownership_source is not None:
        site = _run(
            [str(python), "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"], tmp_path, _env(str(python))
        )
        package = Path(site.stdout.strip()) / "lu_machinery" / "dispatcher"
        package.mkdir(parents=True)
        (package.parent / "__init__.py").write_text("", encoding="utf-8")
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "ownership.py").write_text(ownership_source, encoding="utf-8")
    return str(python)


@pytest.mark.parametrize("damage", ["deleted", "not_executable"])
def test_installed_delegator_refuses_when_the_tracked_hook_is_gone(tmp_path, damage):
    env = _env(project_python())
    repo = _product_repo(tmp_path, env)
    (repo / "note.txt").write_text("note\n", encoding="utf-8")
    assert _git(repo, "add", "note.txt", env=env).returncode == 0
    hook = repo / ".githooks" / "pre-commit"
    if damage == "deleted":
        hook.unlink()
    else:
        hook.chmod(hook.stat().st_mode & ~(stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    base = _head(repo, env)

    commit = _git(repo, "commit", "-q", "-m", "hook gone", env=env)

    assert commit.returncode != 0
    assert f"{MISSING_HOOK} {hook}" in commit.stderr
    assert _head(repo, env) == base


def test_outside_a_task_the_owned_path_check_still_skips(tmp_path):
    env = _env(project_python())
    repo = _product_repo(tmp_path, env)
    _stage_outside(repo, env)

    # The installed pre-commit delegator alone: the commit-msg OPSEC gate needs the full checkout.
    hook = _git(repo, "hook", "run", "pre-commit", env=env)

    assert hook.returncode == 0, hook.stderr
    assert "owned-path" not in hook.stderr


def test_installed_checker_refuses_an_outside_path_inside_a_task(tmp_path):
    env = _env(project_python())
    repo = _product_repo(tmp_path, env)
    # An in-tree package must not stand in for the installed release: this one would pass everything.
    shadow = repo / "lu_machinery" / "dispatcher"
    shadow.mkdir(parents=True)
    for init in (shadow.parent / "__init__.py", shadow / "__init__.py"):
        init.write_text("", encoding="utf-8")
    (shadow / "ownership.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    task_env = _task_env(tmp_path, repo, env)
    _stage_outside(repo, env)
    base = _head(repo, env)

    commit = _git(repo, "commit", "-q", "-m", "outside change", env=task_env)

    assert commit.returncode != 0
    assert "owned-path check refused this commit" in commit.stderr and "outside.txt" in commit.stderr
    assert _head(repo, env) == base


@pytest.mark.parametrize("shadowed", [False, True])
def test_unavailable_ownership_module_refuses_inside_a_task(tmp_path, shadowed):
    python = _venv(tmp_path, ownership_source=None)
    env = _env(python)
    repo = _product_repo(tmp_path, env)
    if shadowed:
        # A passing in-tree copy does not satisfy the check when the installed release is absent.
        shadow = repo / "lu_machinery" / "dispatcher"
        shadow.mkdir(parents=True)
        for init in (shadow.parent / "__init__.py", shadow / "__init__.py"):
            init.write_text("", encoding="utf-8")
        (shadow / "ownership.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    task_env = _task_env(tmp_path, repo, env)
    _stage_outside(repo, env)
    base = _head(repo, env)

    commit = _git(repo, "commit", "-q", "-m", "outside change", env=task_env)

    assert commit.returncode != 0
    assert MISSING_CHECKER in commit.stderr
    assert "No module named 'lu_machinery'" in commit.stderr
    assert _head(repo, env) == base


def test_a_crashing_checker_refuses_inside_a_task(tmp_path):
    python = _venv(tmp_path, ownership_source='raise RuntimeError("checker crashed")\n')
    env = _env(python)
    repo = _product_repo(tmp_path, env)
    task_env = _task_env(tmp_path, repo, env)
    _stage_outside(repo, env)
    base = _head(repo, env)

    commit = _git(repo, "commit", "-q", "-m", "outside change", env=task_env)

    assert commit.returncode != 0
    assert "RuntimeError: checker crashed" in commit.stderr
    assert _head(repo, env) == base


@pytest.mark.parametrize("damage", ["malformed_grants", "record_missing"])
def test_a_handled_checker_exception_refuses_the_commit_and_preserves_head(tmp_path, damage):
    """A missing or damaged task record must not let an out-of-scope commit through."""
    env = _env(project_python())
    repo = _product_repo(tmp_path, env)
    fields = {"owned_path_grants": "not-a-list"} if damage == "malformed_grants" else {}
    task_env = _task_env(tmp_path, repo, env, **fields)
    if damage == "record_missing":
        (Path(task_env["LU_TASKS_DIR"]) / "hook-task.json").unlink()
    _stage_outside(repo, env)
    base = _head(repo, env)

    commit = _git(repo, "commit", "-q", "-m", "outside change", env=task_env)

    assert commit.returncode != 0
    assert "owned-path check could not run (" in commit.stderr
    assert "task record or ownership verification failed); refusing" in commit.stderr
    assert _head(repo, env) == base
