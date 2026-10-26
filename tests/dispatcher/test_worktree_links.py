"""Dispatch dependencies must be present without overwriting or escaping either checkout."""

import errno
import subprocess
from pathlib import Path

import pytest

from scripts.dispatcher import git
from scripts.orchestration.worktree_artifacts import is_disposable_path

LINKS = ("data/sources.db", "data/vesum.db", "node_modules", "site/node_modules")


@pytest.fixture
def layout(tmp_path):
    primary, worktree = tmp_path / "primary", tmp_path / "worktree"
    primary.mkdir()
    worktree.mkdir()
    for relative in LINKS:
        target = primary / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative.endswith(".db"):
            target.write_text("database sentinel")
        else:
            target.mkdir()
    return primary, worktree


def run_git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()


@pytest.mark.parametrize("full_checkout", [False, True])
def test_creation_and_recreation_provision_clean_reapable_links(layout, full_checkout):
    """Missing dependencies, dirty ignored links, and fix-round omissions must fail."""
    primary, _unused = layout
    run_git(primary, "init", "-b", "main")
    run_git(primary, "config", "user.name", "Fixture")
    run_git(primary, "config", "user.email", "fixture@example.invalid")
    ignore = Path(__file__).resolve().parents[2] / ".gitignore"
    (primary / ".gitignore").write_bytes(ignore.read_bytes())
    run_git(primary, "add", ".gitignore")
    run_git(primary, "commit", "-m", "fixture")
    sha = run_git(primary, "rev-parse", "HEAD")
    worktree = primary / ".worktrees/dispatch/codex/fixture"
    for round_number in range(2):
        git.create_worktree(primary, worktree, f"codex/fixture-{round_number}", sha, full_checkout=full_checkout)
        git.provision_links(primary, worktree)
        for relative in LINKS:
            link = worktree / relative
            assert link.is_symlink()
            assert link.readlink() == primary / relative
            assert run_git(worktree, "check-ignore", relative) == relative
            assert is_disposable_path(Path(relative), worktree=worktree, primary=primary)
        assert run_git(worktree, "status", "--porcelain") == ""
        run_git(primary, "worktree", "remove", str(worktree))
        assert (primary / "data/sources.db").read_text() == "database sentinel"
        assert (primary / "node_modules").is_dir()
        assert not (primary / "node_modules").is_symlink()


@pytest.mark.parametrize("kind", ["file", "directory", "link", "dangling"])
def test_existing_destination_is_never_overwritten(layout, kind):
    """Provisioning must preserve real entries and both live and dangling links."""
    primary, worktree = layout
    entry = worktree / "node_modules"
    if kind == "file":
        entry.write_text("keep")
    elif kind == "directory":
        entry.mkdir()
    else:
        entry.symlink_to(primary / ("node_modules" if kind == "link" else "absent"))
    before = entry.lstat()
    git.provision_links(primary, worktree)
    assert entry.lstat() == before


def test_missing_targets_are_not_linked(tmp_path):
    """Absent primary dependencies must not become dangling worktree links."""
    primary, worktree = tmp_path / "primary", tmp_path / "worktree"
    primary.mkdir()
    worktree.mkdir()
    git.provision_links(primary, worktree)
    assert list(worktree.iterdir()) == []


@pytest.mark.parametrize("side,relative", [("source", "node_modules"), ("source", "data"), ("destination", "data")])
def test_symlink_escape_is_refused(layout, tmp_path, side, relative):
    """Source symlinks and destination ancestor links must not escape checkout boundaries."""
    primary, worktree = layout
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sources.db").write_text("outside sentinel")
    root = primary if side == "source" else worktree
    entry = root / relative
    if entry.exists():
        entry.rename(root / "saved")
    entry.symlink_to(outside)
    git.provision_links(primary, worktree)
    assert (outside / "sources.db").read_text() == "outside sentinel"
    assert sorted(p.name for p in outside.iterdir()) == ["sources.db"]
    if side == "source":
        assert not (worktree / relative).exists()


def test_atomic_creation_preserves_racing_entry(layout, monkeypatch):
    """A competing creator between inspection and symlink creation must never lose its entry."""
    primary, worktree = layout
    original = git.os.symlink

    def competing_creator(source, destination, *, dir_fd):
        if destination == "node_modules" and source == primary / "node_modules":
            (worktree / "node_modules").write_text("racing writer")
        return original(source, destination, dir_fd=dir_fd)

    monkeypatch.setattr(git.os, "symlink", competing_creator)
    git.provision_links(primary, worktree)
    assert (worktree / "node_modules").read_text() == "racing writer"


def test_unexpected_io_failure_is_reported(layout, monkeypatch):
    """Permission and I/O failures must not silently produce incomplete provisioning."""
    primary, worktree = layout

    def denied(*args, **kwargs):
        raise PermissionError(errno.EACCES, "denied")

    monkeypatch.setattr(git.os, "symlink", denied)
    with pytest.raises(PermissionError):
        git.provision_links(primary, worktree)
