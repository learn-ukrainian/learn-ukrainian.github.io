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


def test_provision_data_symlinks_links_data_and_node_modules_but_not_venv(tmp_path):
    main_repo = tmp_path / "main"
    worktree = tmp_path / "worktree"
    data_dir = main_repo / "data"
    data_dir.mkdir(parents=True)
    vesum_db = data_dir / "vesum.db"
    sources_db = data_dir / "sources.db"
    vesum_db.touch()
    sources_db.touch()
    primary_venv = main_repo / ".venv"
    node_modules_dir = main_repo / "node_modules"
    site_node_modules_dir = main_repo / "site" / "node_modules"
    primary_venv.mkdir()
    node_modules_dir.mkdir()
    site_node_modules_dir.mkdir(parents=True)

    delegate._provision_data_symlinks(worktree, main_repo)

    vesum_link = worktree / "data" / "vesum.db"
    sources_link = worktree / "data" / "sources.db"
    node_modules_link = worktree / "node_modules"
    site_node_modules_link = worktree / "site" / "node_modules"
    assert vesum_link.is_symlink()
    assert sources_link.is_symlink()
    assert not (worktree / ".venv").exists()
    assert not (worktree / ".venv").is_symlink()
    assert node_modules_link.is_symlink()
    assert site_node_modules_link.is_symlink()
    assert vesum_link.readlink() == vesum_db.resolve()
    assert sources_link.readlink() == sources_db.resolve()
    assert node_modules_link.readlink() == node_modules_dir.resolve()
    assert site_node_modules_link.readlink() == site_node_modules_dir.resolve()

    delegate._provision_data_symlinks(worktree, main_repo)

    assert vesum_link.is_symlink()
    assert sources_link.is_symlink()
    assert not (worktree / ".venv").exists()
    assert not (worktree / ".venv").is_symlink()
    assert node_modules_link.is_symlink()
    assert site_node_modules_link.is_symlink()
    assert vesum_link.readlink() == vesum_db.resolve()
    assert sources_link.readlink() == sources_db.resolve()
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


def test_provision_data_symlinks_read_only_withdraws_only_primary_database_links(tmp_path):
    """#9421: read-only provisioning drops primary DB links, keeps other links, and a later write restores them."""
    main_repo = tmp_path / "main"
    worktree = tmp_path / "worktree"
    (main_repo / "data").mkdir(parents=True)
    (main_repo / "data" / "vesum.db").touch()
    (main_repo / "node_modules").mkdir()
    other = tmp_path / "elsewhere.db"
    other.touch()
    delegate._provision_data_symlinks(worktree, main_repo)
    # A dangling link to the primary's absent sources.db would create it on write.
    (worktree / "data" / "sources.db").symlink_to(main_repo / "data" / "sources.db")

    delegate._provision_data_symlinks(worktree, main_repo, read_only=True)

    assert not (worktree / "data" / "vesum.db").is_symlink()
    assert not (worktree / "data" / "sources.db").is_symlink()
    assert (worktree / "node_modules").resolve() == (main_repo / "node_modules").resolve()
    (worktree / "data" / "vesum.db").symlink_to(other)
    delegate._provision_data_symlinks(worktree, main_repo, read_only=True)
    assert (worktree / "data" / "vesum.db").resolve() == other.resolve()

    (worktree / "data" / "vesum.db").unlink()
    delegate._provision_data_symlinks(worktree, main_repo)
    assert (worktree / "data" / "vesum.db").resolve() == (main_repo / "data" / "vesum.db").resolve()


def test_read_only_stray_database_file_is_displaced_before_write_capable_relink(tmp_path, capsys):
    """A read-only run leaves a regular file at a database path; a write-capable reuse must still link the primary.

    The stray file is renamed aside with its bytes intact, never deleted.
    """
    main_repo = tmp_path / "main"
    worktree = tmp_path / "worktree"
    (main_repo / "data").mkdir(parents=True)
    (main_repo / "data" / "vesum.db").write_bytes(b"primary vesum")
    (main_repo / "data" / "sources.db").write_bytes(b"primary sources")
    delegate._provision_data_symlinks(worktree, main_repo, read_only=True)
    # The read-only worker opens the path, which has no link, and creates a regular file.
    (worktree / "data").mkdir(parents=True, exist_ok=True)
    (worktree / "data" / "vesum.db").write_bytes(b"stray worker bytes")

    delegate._provision_data_symlinks(worktree, main_repo)

    vesum_link = worktree / "data" / "vesum.db"
    assert vesum_link.is_symlink()
    assert vesum_link.resolve() == (main_repo / "data" / "vesum.db").resolve()
    assert (main_repo / "data" / "vesum.db").read_bytes() == b"primary vesum"
    displaced = [p for p in (worktree / "data").iterdir() if p.name.startswith("vesum.db.displaced-")]
    assert len(displaced) == 1
    assert not displaced[0].is_symlink()
    assert displaced[0].read_bytes() == b"stray worker bytes"
    assert "moved stray" in capsys.readouterr().err


def test_write_capable_provisioning_displaces_wrong_database_symlink(tmp_path):
    """A wrong symlink at a database path is moved aside, not kept and not followed into the wrong file."""
    main_repo = tmp_path / "main"
    worktree = tmp_path / "worktree"
    (main_repo / "data").mkdir(parents=True)
    (main_repo / "data" / "sources.db").write_bytes(b"primary sources")
    wrong = tmp_path / "wrong.db"
    wrong.write_bytes(b"wrong target")
    (worktree / "data").mkdir(parents=True)
    (worktree / "data" / "sources.db").symlink_to(wrong)

    delegate._provision_data_symlinks(worktree, main_repo)

    assert (worktree / "data" / "sources.db").resolve() == (main_repo / "data" / "sources.db").resolve()
    assert wrong.read_bytes() == b"wrong target"
    displaced = list((worktree / "data").glob("sources.db.displaced-*"))
    assert len(displaced) == 1
    assert displaced[0].is_symlink()
    assert displaced[0].resolve() == wrong.resolve()


def test_write_capable_provisioning_keeps_correct_database_link(tmp_path, capsys):
    """An already-correct link is left as is: nothing is displaced on repeat provisioning."""
    main_repo = tmp_path / "main"
    worktree = tmp_path / "worktree"
    (main_repo / "data").mkdir(parents=True)
    (main_repo / "data" / "vesum.db").touch()
    delegate._provision_data_symlinks(worktree, main_repo)

    delegate._provision_data_symlinks(worktree, main_repo)

    assert (worktree / "data" / "vesum.db").resolve() == (main_repo / "data" / "vesum.db").resolve()
    assert not list((worktree / "data").glob("*.displaced-*"))
    assert "moved stray" not in capsys.readouterr().err


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
