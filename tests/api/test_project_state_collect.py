"""Unit tests for offline project-state collection helpers (#7188)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.api.project_state_collect import (
    classify_serving_root,
    collect_primary_state,
    collect_worktree_count,
    resolve_primary_repo_root,
)
from scripts.common.release_layout import MANIFEST_NAME

SHA_MAIN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
SHA_HEAD = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, timeout=30)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "primary"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(
        repo,
        "remote",
        "add",
        "origin",
        "https://github.com/learn-ukrainian/learn-ukrainian.github.io.git",
    )
    (repo / "tracked.txt").write_text("v1\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "init")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout.strip()
    _git(repo, "update-ref", "refs/remotes/origin/main", head)
    return repo


def test_collect_primary_state_fixture_repo(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    state = collect_primary_state(repo)
    assert state is not None
    assert len(state["head_sha"]) == 40
    assert state["origin_main_sha"] == state["head_sha"]
    assert state["dirty_count"] == 0


def test_collect_primary_dirty_count(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    state = collect_primary_state(repo)
    assert state is not None
    assert state["dirty_count"] == 1


def test_classify_release_root(tmp_path: Path) -> None:
    release = tmp_path / ".runtime" / "api" / "releases" / SHA_MAIN
    release.mkdir(parents=True)
    (release / MANIFEST_NAME).write_text("{}", encoding="utf-8")
    classified = classify_serving_root(release)
    assert classified["serving_mode"] == "release"
    assert classified["serving_sha"] == SHA_MAIN


def test_classify_checkout_root(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    classified = classify_serving_root(repo)
    assert classified["serving_mode"] == "checkout"
    assert classified["checkout_sha"] is not None


def test_worktree_count(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    assert collect_worktree_count(repo) >= 1


def test_resolve_primary_from_dispatch_worktree(tmp_path: Path) -> None:
    primary = _init_repo(tmp_path)
    worktree = tmp_path / "dispatch-worktree"
    _git(primary, "worktree", "add", str(worktree), "-b", "feature/test")
    resolved = resolve_primary_repo_root(worktree)
    assert resolved.resolve() == primary.resolve()
