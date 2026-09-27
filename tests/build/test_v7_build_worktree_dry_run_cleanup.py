"""#8890: ``v7_build --dry-run --worktree`` must not leak a branch per run.

Unit-level coverage for ``_setup_worktree``/``_discard_worktree`` against a
throwaway git repository (never the shared repo) — the same-second branch
collision and the discard-on-dry-run mechanics are exercised directly here;
the end-to-end "invoked from a primary checkout" contract lives in
``test_v7_build_e2e.py``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.build import v7_build


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, timeout=30)
    (repo / "README.md").write_text("temp repo for v7_build worktree tests\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True, timeout=30)
    return repo


def _repo_state(repo: Path) -> tuple[str, str]:
    refs = subprocess.run(
        ["git", "for-each-ref", "refs/heads"], cwd=repo, text=True, capture_output=True, check=True, timeout=30
    ).stdout
    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain"], cwd=repo, text=True, capture_output=True, check=True, timeout=30
    ).stdout
    return refs, worktrees


def _use_temp_repo(temp_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point ``_setup_worktree`` at ``temp_repo`` instead of this checkout.

    ``_repo_root_from_cwd`` refuses to operate outside ``v7_build.PROJECT_ROOT``
    by design (it is the guard ``--worktree`` itself relies on); ``chdir`` alone
    is not enough, ``PROJECT_ROOT`` must move too. The temp repo has no
    ``origin``, so also skip straight to the local ``main`` fallback.
    """
    monkeypatch.chdir(temp_repo)
    monkeypatch.setattr(v7_build, "PROJECT_ROOT", temp_repo)
    monkeypatch.setattr(v7_build, "_fetch_origin_main", lambda repo_root: False)


def test_dry_run_setup_and_discard_leaves_repo_unchanged(temp_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _use_temp_repo(temp_repo, monkeypatch)
    before = _repo_state(temp_repo)

    worktree = v7_build._setup_worktree("a1", "my-morning", None, dry_run=True)
    result = v7_build._discard_worktree(worktree)

    assert result.action == "discarded"
    assert result.branch_pruned is True
    assert not worktree.path.exists()
    assert _repo_state(temp_repo) == before


def test_setup_worktree_dry_run_same_second_branch_names_are_unique(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_temp_repo(temp_repo, monkeypatch)
    monkeypatch.setattr(v7_build, "_utc_timestamp", lambda: "20260927-120000")

    first = v7_build._setup_worktree("a1", "my-morning", None, dry_run=True)
    second = v7_build._setup_worktree("a1", "my-morning", None, dry_run=True)

    assert first.branch != second.branch
    assert first.path != second.path

    v7_build._discard_worktree(first)
    v7_build._discard_worktree(second)
    refs, _ = _repo_state(temp_repo)
    assert first.branch not in refs
    assert second.branch not in refs


def test_setup_worktree_real_build_branch_name_unaffected_by_dry_run_uniqueness(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-dry-run branch names keep the exact ``build/<level>/<slug>-<stamp>``
    shape ``scripts/sync/promote_module.py`` parses — only dry runs gain the
    extra uniqueness suffix."""
    _use_temp_repo(temp_repo, monkeypatch)
    monkeypatch.setattr(v7_build, "_utc_timestamp", lambda: "20260927-120000")

    worktree = v7_build._setup_worktree("a1", "my-morning", None)

    assert worktree.branch == "build/a1/my-morning-20260927-120000"
    subprocess.run(["git", "worktree", "remove", "--force", str(worktree.path)], cwd=temp_repo, check=True, timeout=30)
    subprocess.run(["git", "branch", "-D", worktree.branch], cwd=temp_repo, check=True, timeout=30)
