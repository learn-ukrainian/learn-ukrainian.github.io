"""Tests for the core.bare repo-health canary (#2842)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from audit.check_core_bare import check_core_bare, main

_GIT_REDIRECT = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_PREFIX",
    }
)


def _clean_env() -> dict[str, str]:
    """Drop git redirect env so fixtures are not the outer commit hook repo."""
    return {k: v for k, v in os.environ.items() if k not in _GIT_REDIRECT}


def _init_repo(path: Path) -> Path:
    subprocess.run(
        ["git", "init", "-q", str(path)],
        check=True,
        env=_clean_env(),
    )
    return path


def _core_bare(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "config", "--get", "core.bare"],
        capture_output=True,
        text=True,
        env=_clean_env(),
    ).stdout.strip()


def _set_bare(repo: Path, value: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "config", "--local", "core.bare", value],
        check=True,
        env=_clean_env(),
    )


def _set_worktree_config(repo: Path, value: str = "true") -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "config",
            "--local",
            "extensions.worktreeConfig",
            value,
        ],
        check=True,
        env=_clean_env(),
    )


def test_ok_when_core_bare_false(tmp_path):
    repo = _init_repo(tmp_path)
    _set_worktree_config(repo, "true")
    ok, message = check_core_bare(repo, fix=False)
    assert ok
    assert "ok" in message


def test_detects_core_bare_true_without_fix(tmp_path):
    repo = _init_repo(tmp_path)
    _set_worktree_config(repo, "true")
    _set_bare(repo, "true")
    ok, message = check_core_bare(repo, fix=False)
    assert not ok
    assert "BROKEN" in message
    # check-only must NOT mutate the repo
    assert _core_bare(repo) == "true"


def test_fix_resets_core_bare_true(tmp_path):
    repo = _init_repo(tmp_path)
    _set_bare(repo, "true")
    ok, message = check_core_bare(repo, fix=True)
    assert ok
    assert "reset" in message
    assert _core_bare(repo) == "false"
    # fix also asserts worktreeConfig
    wtc = subprocess.run(
        ["git", "-C", str(repo), "config", "--get", "extensions.worktreeConfig"],
        capture_output=True,
        text=True,
        env=_clean_env(),
    ).stdout.strip()
    assert wtc == "true"


def test_detects_missing_worktree_config_without_fix(tmp_path):
    repo = _init_repo(tmp_path)
    ok, message = check_core_bare(repo, fix=False)
    assert not ok
    assert "worktreeConfig" in message


def test_main_exit_codes(tmp_path):
    repo = _init_repo(tmp_path)
    _set_worktree_config(repo, "true")
    # healthy → exit 0
    assert main(["--repo", str(repo), "--quiet"]) == 0
    # drifted, no --fix → exit 1, still broken
    _set_bare(repo, "true")
    assert main(["--repo", str(repo)]) == 1
    assert _core_bare(repo) == "true"
    # drifted, --fix → exit 0, healed and stays healed
    assert main(["--repo", str(repo), "--fix"]) == 0
    assert _core_bare(repo) == "false"
    assert main(["--repo", str(repo)]) == 0
