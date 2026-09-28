"""Primary data discovery for the read-only СУМ-11 audit."""

from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.lexicon.audit_sum11_relations import primary_data_dir


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, timeout=30)


def test_primary_data_uses_common_git_dir_for_shallow_worktree(tmp_path: Path) -> None:
    checkout = tmp_path / "primary"
    checkout.mkdir()
    _git(checkout, "init")
    _git(checkout, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "base")
    worktree = checkout / ".worktrees" / "short"
    _git(checkout, "worktree", "add", "--detach", str(worktree))

    assert primary_data_dir(worktree) == checkout / "data"
