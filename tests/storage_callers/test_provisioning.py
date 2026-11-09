"""Both real worktree creation paths leave stores in the primary checkout."""

import subprocess

import pytest

from scripts.build import v7_build
from scripts.dispatcher import git
from scripts.storage.topology import StoreBinding, resolve_store


@pytest.mark.parametrize("creator", ["dispatcher", "v7"])
def test_new_worktree_resolves_primary_stores_without_provisioning(tmp_path, monkeypatch, creator):
    primary = tmp_path / "primary"
    primary.mkdir()

    def run(*args):
        return subprocess.run(["git", "-C", str(primary), *args], check=True, capture_output=True,
                              text=True, timeout=30).stdout.strip()
    run("init", "-b", "main")
    run("config", "user.name", "Fixture")
    run("config", "user.email", "fixture@example.invalid")
    (primary / ".gitignore").write_text("data/\n.worktrees/\nnode_modules/\nsite/node_modules/\n")
    run("add", ".gitignore")
    run("commit", "-m", "fixture")
    (primary / "data").mkdir()
    for store in ("sources", "vesum"):
        (primary / "data" / f"{store}.db").write_bytes(b"store sentinel")
    (primary / "node_modules").mkdir()
    worktree = primary / ".worktrees" / "dispatch" / "codex" / "fixture"
    monkeypatch.chdir(primary)
    if creator == "dispatcher":
        git.create_worktree(primary, worktree, "codex/fixture", "main")
    else:
        monkeypatch.setattr(v7_build, "PROJECT_ROOT", primary)
        monkeypatch.setattr(v7_build, "_fetch_origin_main", lambda repo: False)
        assert v7_build._setup_worktree("a1", "fixture", str(worktree)).path == worktree
    for store in ("sources", "vesum"):
        slot = worktree / "data" / f"{store}.db"
        assert not slot.exists() and not slot.is_symlink()
        binding = resolve_store(store, worktree, env={})
        assert isinstance(binding, StoreBinding)
        assert binding.path == primary / "data" / f"{store}.db"
        assert binding.path.read_bytes() == b"store sentinel"
    for relative in git.NODE_LINKS:
        assert not (worktree / relative).is_symlink()
    assert run("-C", str(worktree), "status", "--porcelain") == ""
