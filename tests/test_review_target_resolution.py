"""Tests for scripts/review/target_resolution.py — deterministic target selection."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common.git_context import sanitized_git_env
from scripts.review.target_resolution import (
    TargetResolutionError,
    is_test_path,
    resolve_branch_target,
    resolve_commit_target,
    resolve_local_target,
    resolve_pr_target,
    resolve_review_target,
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # sanitized_git_env() strips GIT_DIR/GIT_WORK_TREE/etc — without it, running
    # this suite from inside a `git commit` pre-commit hook leaks the OUTER
    # repo's git env into these calls and silently operates on the wrong repo.
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        check=True,
        capture_output=True,
        text=True,
        env=sanitized_git_env(),
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    # Non-protected initial branch name: this repo is an unrelated tmp fixture,
    # but the project's global git-checkout guard (scripts/agent_runtime/shims/git)
    # blocks `checkout`/`switch` off of any branch literally named main/master —
    # it doesn't check repo identity. Naming it "trunk" avoids tripping that guard.
    _git(repo, "init", "-q", "-b", "trunk")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "app.py").write_text("print('v1')\n", encoding="utf-8")
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


# --- is_test_path -----------------------------------------------------------

def test_is_test_path_recognizes_common_shapes():
    assert is_test_path("tests/test_foo.py")
    assert is_test_path("scripts/tests/test_bar.py")
    assert is_test_path("src/__tests__/thing.test.ts")
    assert is_test_path("src/component.spec.tsx")
    assert not is_test_path("scripts/build/v7_build.py")
    assert not is_test_path("docs/best-practices/code-quality.md")


# --- local mode --------------------------------------------------------------

def test_resolve_local_target_clean_tree(tmp_path):
    repo = _init_repo(tmp_path)
    target = resolve_local_target(repo)
    assert target.mode == "local"
    assert target.clean_tree is True
    assert target.changed_paths == ()
    assert target.base_sha is None
    assert target.head_sha is None
    assert "nothing to review" in target.description


def test_resolve_local_target_clean_tree_is_not_evidence_of_commit_review(tmp_path):
    """A clean local tree must never be presented as proof a commit/PR was reviewed.

    The mode field plus None SHAs are the structural guard: a report built from
    this target can't claim it verified a specific commit/PR, because there is
    no base/head SHA to point at.
    """
    repo = _init_repo(tmp_path)
    # Commit further work — tree is clean, but real committed changes exist.
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    _git(repo, "commit", "-aq", "-m", "v2")

    target = resolve_local_target(repo)
    assert target.clean_tree is True
    assert target.mode == "local"
    assert target.base_sha is None and target.head_sha is None
    # A caller wanting proof of the v2 commit must use mode=commit explicitly.
    committed = resolve_commit_target(repo, "HEAD")
    assert committed.base_sha is not None and committed.head_sha is not None
    assert "app.py" in committed.changed_paths


def test_resolve_local_target_counts_staged_unstaged_and_untracked(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nprint('v2')\n", encoding="utf-8")
    _git(repo, "add", "app.py")
    (repo / "unstaged.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "unstaged.py")
    _git(repo, "commit", "-q", "-m", "staged change")
    (repo / "unstaged.py").write_text("x = 1\ny = 2\n", encoding="utf-8")
    (repo / "new_untracked.py").write_text("z = 3\n", encoding="utf-8")

    target = resolve_local_target(repo)
    assert target.clean_tree is False
    assert set(target.changed_paths) >= {"unstaged.py", "new_untracked.py"}
    assert target.non_test_loc > 0


def test_resolve_local_target_excludes_test_files_from_loc(tmp_path):
    repo = _init_repo(tmp_path)
    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text("def test_x():\n    assert True\n", encoding="utf-8")

    target = resolve_local_target(repo)
    assert "tests/test_app.py" in target.changed_paths
    assert target.non_test_loc == 0


# --- commit mode ---------------------------------------------------------------

def test_resolve_commit_target(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    _git(repo, "commit", "-aq", "-m", "v2 change")

    target = resolve_commit_target(repo, "HEAD")
    assert target.mode == "commit"
    assert target.base_sha != target.head_sha
    assert target.changed_paths == ("app.py",)
    assert target.non_test_loc == 2  # one line removed, one added
    assert target.clean_tree is False


def test_resolve_commit_target_root_commit_raises(tmp_path):
    repo = _init_repo(tmp_path)
    root = _git(repo, "rev-list", "--max-parents=0", "HEAD").stdout.strip()
    with __import__("pytest").raises(TargetResolutionError):
        resolve_commit_target(repo, root)


# --- branch mode -----------------------------------------------------------------

def test_resolve_branch_target_against_explicit_base(tmp_path):
    repo = _init_repo(tmp_path)
    trunk_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "branch", "feature")
    _git(repo, "checkout", "-q", "feature")
    (repo / "feature.py").write_text("value = 1\n", encoding="utf-8")
    _git(repo, "add", "feature.py")
    _git(repo, "commit", "-q", "-m", "add feature")
    _git(repo, "checkout", "-q", "trunk")

    target = resolve_branch_target(repo, "feature", trunk_sha)
    assert target.mode == "branch"
    assert target.changed_paths == ("feature.py",)
    assert target.base_sha is not None and target.head_sha is not None
    assert target.base_sha != target.head_sha


def test_resolve_branch_target_no_merge_base_raises(tmp_path):
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-q", "--orphan", "orphan-branch")
    _git(repo, "rm", "-rq", "--cached", ".")
    (repo / "orphan.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "orphan.py")
    _git(repo, "commit", "-q", "-m", "orphan root")

    with __import__("pytest").raises(TargetResolutionError):
        resolve_branch_target(repo, "orphan-branch", "trunk")


# --- pr mode (gh calls stubbed) ---------------------------------------------------

def test_resolve_pr_target_uses_actual_pr_base_not_assumed_default(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    base_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / "pr_change.py").write_text("value = 1\n", encoding="utf-8")
    _git(repo, "add", "pr_change.py")
    _git(repo, "commit", "-q", "-m", "pr change")
    head_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()

    import scripts.review.target_resolution as tr

    payload = {
        "number": 5283,
        "baseRefName": "release/whatever",  # deliberately NOT "main"
        "baseRefOid": base_sha,
        "headRefName": "feature-branch",
        "headRefOid": head_sha,
    }

    def fake_run_gh(args, cwd, timeout=30.0):
        assert "view" in args
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(tr, "_run_gh", fake_run_gh)

    target = resolve_pr_target(repo, 5283)
    assert target.mode == "pr"
    assert target.base_sha == base_sha
    assert target.head_sha == head_sha
    assert "release/whatever" in target.description
    assert target.changed_paths == ("pr_change.py",)


def test_resolve_pr_target_missing_sha_raises(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    import scripts.review.target_resolution as tr

    def fake_run_gh(args, cwd, timeout=30.0):
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps({"number": 1}), stderr="")

    monkeypatch.setattr(tr, "_run_gh", fake_run_gh)
    with __import__("pytest").raises(TargetResolutionError):
        resolve_pr_target(repo, 1)


# --- dispatch ---------------------------------------------------------------------

def test_resolve_review_target_requires_explicit_mode_args(tmp_path):
    repo = _init_repo(tmp_path)
    with __import__("pytest").raises(TargetResolutionError):
        resolve_review_target("commit", repo)
    with __import__("pytest").raises(TargetResolutionError):
        resolve_review_target("branch", repo, branch="feature")
    with __import__("pytest").raises(TargetResolutionError):
        resolve_review_target("pr", repo)
    with __import__("pytest").raises(TargetResolutionError):
        resolve_review_target("bogus-mode", repo)


def test_resolve_review_target_local_dispatch(tmp_path):
    repo = _init_repo(tmp_path)
    target = resolve_review_target("local", repo)
    assert target.mode == "local"
