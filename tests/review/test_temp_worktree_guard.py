"""Review scratch cleanup must retain linked checkouts and their ignored output (#9645)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.common.git_context import GIT_REDIRECT_ENV_KEYS
from scripts.review import isolation


def _git(repo: Path, *args: str) -> str:
    env = {key: value for key, value in os.environ.items() if key not in GIT_REDIRECT_ENV_KEYS}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout


@pytest.fixture
def linked_review_tree(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    (repo / ".gitignore").write_text("output/\n")
    _git(repo, "add", ".gitignore")
    _git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture")
    root = tmp_path / "lu-review-snap-linked"
    _git(repo, "worktree", "add", "--detach", str(root), "HEAD")
    output = root / "output" / "new.bin"
    output.parent.mkdir()
    output.write_bytes(b"new ignored review output\x00\xff")
    assert _git(root, "check-ignore", "output/new.bin").strip() == "output/new.bin"
    return repo, root, output


@pytest.mark.parametrize("marked", [False, True], ids=["legacy-orphan", "marked-root"])
def test_review_cleanup_refuses_registered_worktree_with_ignored_output(
    linked_review_tree: tuple[Path, Path, Path], marked: bool
) -> None:
    repo, root, output = linked_review_tree
    payload = output.read_bytes()
    registration = _git(repo, "worktree", "list", "--porcelain")
    if marked:
        isolation._write_review_temp_root_marker(root)
    cleanup = isolation.remove_review_temp_tree if marked else isolation._remove_review_temp_orphan

    with pytest.raises(OSError, match="Git checkout retained; use guarded worktree cleanup"):
        cleanup(root)

    assert output.read_bytes() == payload
    assert (root / ".git").is_file()
    assert _git(repo, "worktree", "list", "--porcelain") == registration


@pytest.mark.parametrize("marked", [False, True], ids=["legacy-orphan", "marked-root"])
def test_review_cleanup_removes_plain_temporary_tree(tmp_path: Path, marked: bool) -> None:
    root = tmp_path / "lu-review-snap-plain"
    (root / "nested").mkdir(parents=True)
    (root / "nested" / "output.bin").write_bytes(b"disposable review output")
    if marked:
        isolation._write_review_temp_root_marker(root)
    cleanup = isolation.remove_review_temp_tree if marked else isolation._remove_review_temp_orphan

    cleanup(root)

    assert not root.exists()


@pytest.mark.parametrize("cleanup", [isolation.remove_review_temp_tree, isolation._remove_review_temp_orphan])
def test_review_cleanup_refuses_symlink_to_worktree(
    linked_review_tree: tuple[Path, Path, Path], tmp_path: Path, cleanup
) -> None:
    repo, root, output = linked_review_tree
    payload = output.read_bytes()
    registration = _git(repo, "worktree", "list", "--porcelain")
    alias = tmp_path / "lu-review-snap-alias"
    alias.symlink_to(root, target_is_directory=True)

    with pytest.raises(OSError, match="not a private directory"):
        cleanup(alias)

    assert alias.is_symlink()
    assert output.read_bytes() == payload
    assert _git(repo, "worktree", "list", "--porcelain") == registration


def test_review_orphan_sweep_reports_retained_worktree(
    linked_review_tree: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, root, output = linked_review_tree
    payload = output.read_bytes()
    registration = _git(repo, "worktree", "list", "--porcelain")
    monkeypatch.setattr(isolation, "scratch_scan_roots", lambda: [tmp_path])
    monkeypatch.setattr(isolation, "_is_disk_pressure_active", lambda *args, **kwargs: False)
    os.utime(root, (1, 1))

    result = isolation.sweep_review_temp_orphans(now=100000)

    assert result == {"roots_reaped": 0, "bytes_freed": 0, "errors": 1, "disk_pressure": False}
    assert output.read_bytes() == payload
    assert _git(repo, "worktree", "list", "--porcelain") == registration


def test_review_cleanup_refuses_parent_of_linked_worktree(
    linked_review_tree: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    repo, root, output = linked_review_tree
    payload = output.read_bytes()
    parent = tmp_path / "lu-review-snap-parent"
    parent.mkdir()
    _git(repo, "worktree", "move", str(root), str(parent / "nested"))
    output = parent / "nested" / "output" / "new.bin"
    registration = _git(repo, "worktree", "list", "--porcelain")

    with pytest.raises(OSError, match="Git checkout retained; use guarded worktree cleanup"):
        isolation._remove_review_temp_orphan(parent)

    assert output.read_bytes() == payload
    assert _git(repo, "worktree", "list", "--porcelain") == registration


def test_review_cleanup_retains_worktree_after_permission_repair(linked_review_tree: tuple[Path, Path, Path]) -> None:
    repo, root, output = linked_review_tree
    payload = output.read_bytes()
    registration = _git(repo, "worktree", "list", "--porcelain")
    output.parent.chmod(0o000)

    try:
        with pytest.raises(OSError, match="Git checkout retained; use guarded worktree cleanup"):
            isolation._remove_review_temp_orphan(root)
        assert output.read_bytes() == payload
        assert _git(repo, "worktree", "list", "--porcelain") == registration
    finally:
        output.parent.chmod(0o700)
