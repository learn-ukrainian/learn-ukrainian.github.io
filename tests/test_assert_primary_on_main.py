"""Tests for scripts/guardrails/assert_primary_on_main.py (#4857)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.guardrails.assert_primary_on_main import heal_primary_to_main, primary_head_state


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_PREFIX",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        env.pop(name, None)
    return subprocess.run(
        list(args),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


@pytest.fixture
def primary_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    assert _run(root, "git", "init", "-b", "main").returncode == 0
    assert _run(root, "git", "config", "user.name", "Test").returncode == 0
    assert _run(root, "git", "config", "user.email", "t@example.invalid").returncode == 0
    assert _run(root, "git", "commit", "--allow-empty", "-m", "init").returncode == 0
    return root


def test_on_main_ok(primary_repo: Path) -> None:
    state = primary_head_state(primary_repo)
    assert state["ok"] is True
    assert state["branch"] == "main"


def test_detached_detected(primary_repo: Path) -> None:
    r = _run(primary_repo, "git", "switch", "--detach", "HEAD")
    assert r.returncode == 0, r.stderr
    state = primary_head_state(primary_repo)
    assert state["ok"] is False
    assert state["reason"] == "detached_head"


def test_heal_reattaches_main(primary_repo: Path) -> None:
    assert _run(primary_repo, "git", "switch", "--detach", "HEAD").returncode == 0
    ok, _detail = heal_primary_to_main(primary_repo)
    assert ok is True
    state = primary_head_state(primary_repo)
    assert state["ok"] is True
    assert state["branch"] == "main"
