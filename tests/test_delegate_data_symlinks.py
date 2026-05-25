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
    starlight_node_modules_dir = main_repo / "starlight" / "node_modules"
    venv_dir.mkdir()
    node_modules_dir.mkdir()
    starlight_node_modules_dir.mkdir(parents=True)

    delegate._provision_data_symlinks(worktree, main_repo)

    vesum_link = worktree / "data" / "vesum.db"
    sources_link = worktree / "data" / "sources.db"
    venv_link = worktree / ".venv"
    node_modules_link = worktree / "node_modules"
    starlight_node_modules_link = worktree / "starlight" / "node_modules"
    assert vesum_link.is_symlink()
    assert sources_link.is_symlink()
    assert venv_link.is_symlink()
    assert node_modules_link.is_symlink()
    assert starlight_node_modules_link.is_symlink()
    assert vesum_link.readlink() == vesum_db.resolve()
    assert sources_link.readlink() == sources_db.resolve()
    assert venv_link.readlink() == venv_dir.resolve()
    assert node_modules_link.readlink() == node_modules_dir.resolve()
    assert starlight_node_modules_link.readlink() == starlight_node_modules_dir.resolve()

    delegate._provision_data_symlinks(worktree, main_repo)

    assert vesum_link.is_symlink()
    assert sources_link.is_symlink()
    assert venv_link.is_symlink()
    assert node_modules_link.is_symlink()
    assert starlight_node_modules_link.is_symlink()
    assert vesum_link.readlink() == vesum_db.resolve()
    assert sources_link.readlink() == sources_db.resolve()
    assert venv_link.readlink() == venv_dir.resolve()
    assert node_modules_link.readlink() == node_modules_dir.resolve()
    assert starlight_node_modules_link.readlink() == starlight_node_modules_dir.resolve()


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
    assert not (worktree / "starlight" / "node_modules").exists()
