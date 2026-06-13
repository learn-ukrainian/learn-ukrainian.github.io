"""Tests for the node_modules ELOOP canary (scripts/audit/check_self_symlinks.py).

The lethal bug: a self-referential ``node_modules`` symlink (``X -> X``) makes
every ``npm`` build die with ``spawn ELOOP``. The canary must detect and remove
it while leaving valid symlinks and real directories untouched.
"""

from __future__ import annotations

import os
from pathlib import Path

from scripts.audit.check_self_symlinks import (
    check_self_symlinks,
    find_looping_symlinks,
)


def _make_self_loop(path: Path) -> None:
    """Create a self-referential symlink at ``path`` (``path -> path``)."""
    os.symlink(str(path), str(path))


def test_clean_repo_is_ok(tmp_path: Path) -> None:
    (tmp_path / "site").mkdir()
    ok, message = check_self_symlinks(tmp_path, fix=False)
    assert ok is True
    assert "no looping" in message
    assert find_looping_symlinks(tmp_path) == []


def test_real_node_modules_directory_untouched(tmp_path: Path) -> None:
    nm = tmp_path / "node_modules"
    nm.mkdir()
    (nm / "astro").mkdir()
    ok, _ = check_self_symlinks(tmp_path, fix=True)
    assert ok is True
    assert nm.is_dir() and not nm.is_symlink()
    assert (nm / "astro").is_dir()


def test_valid_symlink_untouched(tmp_path: Path) -> None:
    real = tmp_path / "shared_node_modules"
    real.mkdir()
    link = tmp_path / "node_modules"
    link.symlink_to(real)
    assert find_looping_symlinks(tmp_path) == []
    ok, _ = check_self_symlinks(tmp_path, fix=True)
    assert ok is True
    assert link.is_symlink()  # left alone — it resolves fine


def test_detects_self_referential_loop_without_fix(tmp_path: Path) -> None:
    loop = tmp_path / "node_modules"
    _make_self_loop(loop)
    found = find_looping_symlinks(tmp_path)
    assert loop in found
    ok, message = check_self_symlinks(tmp_path, fix=False)
    assert ok is False
    assert "BROKEN" in message and "ELOOP" in message
    assert loop.is_symlink()  # not removed without --fix


def test_fix_removes_self_referential_loop(tmp_path: Path) -> None:
    loop = tmp_path / "node_modules"
    _make_self_loop(loop)
    ok, message = check_self_symlinks(tmp_path, fix=True)
    assert ok is True
    assert "removed 1" in message
    assert not loop.is_symlink() and not loop.exists()
    # idempotent: a second run is clean
    ok2, message2 = check_self_symlinks(tmp_path, fix=True)
    assert ok2 is True and "no looping" in message2


def test_fix_removes_site_loop(tmp_path: Path) -> None:
    (tmp_path / "site").mkdir()
    loop = tmp_path / "site" / "node_modules"
    _make_self_loop(loop)
    ok, _ = check_self_symlinks(tmp_path, fix=True)
    assert ok is True
    assert not loop.is_symlink()


def test_sweeps_worktree_loops(tmp_path: Path) -> None:
    wt = tmp_path / ".worktrees" / "dispatch" / "codex" / "some-task"
    wt.mkdir(parents=True)
    loop = wt / "node_modules"
    _make_self_loop(loop)
    found = find_looping_symlinks(tmp_path)
    assert loop in found
    ok, _ = check_self_symlinks(tmp_path, fix=True)
    assert ok is True
    assert not loop.is_symlink()


def test_dangling_symlink_is_left_alone(tmp_path: Path) -> None:
    # A merely-dangling link (target missing) is a different, less-severe
    # problem — not an ELOOP — and is intentionally NOT removed.
    link = tmp_path / "node_modules"
    link.symlink_to(tmp_path / "does_not_exist")
    assert find_looping_symlinks(tmp_path) == []
    ok, _ = check_self_symlinks(tmp_path, fix=True)
    assert ok is True
    assert link.is_symlink()
