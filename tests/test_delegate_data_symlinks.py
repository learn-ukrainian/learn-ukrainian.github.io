"""Tests for delegate.py worktree local-file provisioning."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate


def test_main_checkout_root_resolves_primary_checkout_from_worktree(tmp_path):
    main_repo = tmp_path / "main"
    worktree = main_repo / ".worktrees" / "codex-task"
    git_dir = main_repo / ".git" / "worktrees" / "codex-task"
    git_dir.mkdir(parents=True)
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n")

    assert delegate._main_checkout_root(worktree) == main_repo


def test_provision_data_symlinks_links_heavy_dbs_and_is_idempotent(tmp_path):
    main_repo = tmp_path / "main"
    worktree = tmp_path / "worktree"
    data_dir = main_repo / "data"
    data_dir.mkdir(parents=True)
    vesum_db = data_dir / "vesum.db"
    sources_db = data_dir / "sources.db"
    vesum_db.touch()
    sources_db.touch()
    venv_dir = main_repo / ".venv"
    node_modules_dir = main_repo / "node_modules"
    site_node_modules_dir = main_repo / "site" / "node_modules"
    venv_dir.mkdir()
    node_modules_dir.mkdir()
    site_node_modules_dir.mkdir(parents=True)

    delegate._provision_data_symlinks(worktree, main_repo)

    vesum_link = worktree / "data" / "vesum.db"
    sources_link = worktree / "data" / "sources.db"
    venv_link = worktree / ".venv"
    node_modules_link = worktree / "node_modules"
    site_node_modules_link = worktree / "site" / "node_modules"
    assert vesum_link.is_symlink()
    assert sources_link.is_symlink()
    assert venv_link.is_symlink()
    assert node_modules_link.is_symlink()
    assert site_node_modules_link.is_symlink()
    assert vesum_link.readlink() == vesum_db.resolve()
    assert sources_link.readlink() == sources_db.resolve()
    assert venv_link.readlink() == venv_dir.resolve()
    assert node_modules_link.readlink() == node_modules_dir.resolve()
    assert site_node_modules_link.readlink() == site_node_modules_dir.resolve()

    delegate._provision_data_symlinks(worktree, main_repo)

    assert vesum_link.is_symlink()
    assert sources_link.is_symlink()
    assert venv_link.is_symlink()
    assert node_modules_link.is_symlink()
    assert site_node_modules_link.is_symlink()
    assert vesum_link.readlink() == vesum_db.resolve()
    assert sources_link.readlink() == sources_db.resolve()
    assert venv_link.readlink() == venv_dir.resolve()
    assert node_modules_link.readlink() == node_modules_dir.resolve()
    assert site_node_modules_link.readlink() == site_node_modules_dir.resolve()


def test_provision_data_symlinks_skips_missing_main_files(tmp_path, capsys):
    main_repo = tmp_path / "main"
    worktree = tmp_path / "worktree"
    main_repo.mkdir()

    delegate._provision_data_symlinks(worktree, main_repo)

    captured = capsys.readouterr()
    assert "skipping worktree link for missing" in captured.err
    assert not (worktree / "data" / "vesum.db").exists()
    assert not (worktree / "data" / "sources.db").exists()
    assert not (worktree / ".venv").exists()
    assert not (worktree / "node_modules").exists()
    assert not (worktree / "site" / "node_modules").exists()


def test_provision_data_symlinks_refuses_when_worktree_is_main(tmp_path, capsys):
    """Guard against the node_modules ELOOP footgun: provisioning the main
    checkout into itself would create `node_modules -> node_modules` self-loops
    that break every later npm build with spawn ELOOP."""
    main_repo = tmp_path / "main"
    (main_repo / "node_modules").mkdir(parents=True)

    delegate._provision_data_symlinks(main_repo, main_repo)

    captured = capsys.readouterr()
    assert "refusing to provision symlinks into the main checkout" in captured.err
    # node_modules stays a real directory — no self-referential symlink created.
    assert (main_repo / "node_modules").is_dir()
    assert not (main_repo / "node_modules").is_symlink()


def test_resolve_repo_root_hops_to_primary_from_worktree_script_copy(tmp_path):
    # #5171: every dispatch worktree carries its own scripts/delegate.py copy;
    # running that copy must still anchor state to the PRIMARY checkout.
    main_repo = tmp_path / "main"
    worktree = main_repo / ".worktrees" / "dispatch" / "cursor" / "fix-123"
    git_dir = main_repo / ".git" / "worktrees" / "fix-123"
    git_dir.mkdir(parents=True)
    (worktree / "scripts").mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n")

    assert delegate.resolve_repo_root(worktree / "scripts" / "delegate.py", 1) == main_repo


def test_resolve_repo_root_is_identity_in_primary_checkout(tmp_path):
    main_repo = tmp_path / "main"
    (main_repo / ".git").mkdir(parents=True)
    (main_repo / "scripts").mkdir()
    assert delegate.resolve_repo_root(main_repo / "scripts" / "delegate.py", 1) == main_repo


def test_repo_root_constant_is_wired_through_the_resolver():
    # Revert guard for #5171: in the primary checkout raw parents[1] and the
    # resolver agree, so behavior alone can't detect a revert — pin the wiring.
    from pathlib import Path as _P

    source = _P(delegate.__file__).read_text(encoding="utf-8")
    assert "_REPO_ROOT = resolve_repo_root(Path(__file__), 1)" in source
