"""Repository-context regressions for private review targets (#10557)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from scripts.common.git_context import sanitized_git_env
from scripts.common.repo_root import main_checkout_root
from scripts.orchestration.fleet_repos import load_fleet_repos
from scripts.review import target_resolution
from tests.test_review_closeout_cli import _run_cli

# Fallbacks let this module collect on a tree that does not have the fix yet.
PRIVATE_REVIEW_TARGET_UNRESOLVED = getattr(
    target_resolution,
    "PRIVATE_REVIEW_TARGET_UNRESOLVED",
    "PRIVATE_REVIEW_TARGET_UNRESOLVED: --repo infra-private checkout or target unavailable; "
    "use the private review trigger in the infra-private repository",
)
repository_target_error = getattr(target_resolution, "repository_target_error", None)
MissingReviewCommit = getattr(target_resolution, "MissingReviewCommit", None)
def _git(repo, *args, check=True):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=sanitized_git_env(),
        check=check,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _assert_neutral_private_refusal(error: str) -> None:
    refusal = next(line for line in error.splitlines() if "PRIVATE_REVIEW_TARGET_UNRESOLVED:" in line)
    start = refusal.index("PRIVATE_REVIEW_TARGET_UNRESOLVED:")
    assert refusal[start:] == PRIVATE_REVIEW_TARGET_UNRESOLVED
    assert "/" not in refusal


def _freeze(state, issue="#10557"):
    return _run_cli(
        state,
        "freeze",
        "--issue",
        issue,
        "--intended-behavior",
        "measure the stored repository",
        "--non-goals",
        "no other checkout",
        "--owner-boundary",
        "scripts/review",
    )


def _init_committed_repo(repo: Path, origin: str, filename: str) -> str:
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "core.hooksPath", "/dev/null")
    _git(repo, "remote", "add", "origin", origin)
    (repo / "base.txt").write_text(filename)
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    (repo / filename).write_text("value = 1\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "change\n\nX-Agent: codex/gpt-6.1-sol")
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "update-ref", "refs/remotes/origin/review", "HEAD")
    from tests.test_review_target_resolution import _publish_pr_branch

    _publish_pr_branch(repo, "review", head)
    return head


def test_typed_missing_commit_neutralizes_and_wrong_base_stays_specific():
    """Neutral refusal follows the exception type, not the wording of the message."""
    if repository_target_error is None or MissingReviewCommit is None:
        pytest.fail("typed missing-commit refusal is not implemented")
    neutralized = repository_target_error(
        "infra-private",
        MissingReviewCommit("cannot resolve ref 'deadbeef': absent"),
    )
    assert str(neutralized) == PRIVATE_REVIEW_TARGET_UNRESOLVED
    wrong_base = target_resolution.TargetResolutionError("cannot resolve ref 'no-such-base': unknown revision")
    kept = repository_target_error("infra-private", wrong_base)
    assert kept is wrong_base
    assert "no-such-base" in str(kept)
    assert "PRIVATE_REVIEW_TARGET_UNRESOLVED" not in str(kept)


def test_public_worktree_head_and_expansion_stay_in_the_worktree(tmp_path):
    """`--repo public --repo-root` a linked worktree reviews that worktree, not the primary."""
    catalog = load_fleet_repos()["public"].github
    primary = tmp_path / "primary"
    primary_head = _init_committed_repo(primary, f"https://github.com/{catalog}.git", "primary.py")
    worktree = tmp_path / "worktree"
    _git(primary, "worktree", "add", "-q", "-b", "review-wt", str(worktree), "HEAD")
    (worktree / "worktree.py").write_text("value = 1\n", encoding="utf-8")
    _git(worktree, "add", "worktree.py")
    _git(worktree, "commit", "-qm", "worktree only")
    worktree_head = _git(worktree, "rev-parse", "HEAD").stdout.strip()
    assert worktree_head != primary_head
    assert main_checkout_root(worktree) == primary.resolve()

    state = tmp_path / "worktree.json"
    proc = _run_cli(
        state,
        "target",
        "--mode",
        "commit",
        "--commit",
        "HEAD",
        "--repo-root",
        str(worktree),
        "--repo",
        "public",
    )
    assert proc.returncode == 0, proc.stderr
    body = json.loads(proc.stdout)
    assert body["head_sha"] == worktree_head
    assert body["changed_paths"] == ["worktree.py"]
    assert json.loads(state.read_text())["target_args"]["repo_root"] == str(worktree.resolve())
    assert _freeze(state).returncode == 0

    (worktree / "expanded.py").write_text("x = 1\n" * 40, encoding="utf-8")
    _git(worktree, "add", "expanded.py")
    _git(worktree, "commit", "-qm", "expand")
    expansion = _run_cli(state, "check-expansion", "--repo-root", str(worktree), "--current-head", "HEAD")
    assert expansion.returncode == 0, expansion.stderr
    assert json.loads(expansion.stdout)["triggered"] is True


def test_same_repo_pr_head_pins_catalog_repository(tmp_path, monkeypatch):
    from scripts.ai_agent_bridge import _agy

    repo = tmp_path / "public"
    catalog = load_fleet_repos()["public"].github
    _init_committed_repo(repo, f"https://github.com/{catalog}.git", "public.py")
    sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    seen = {}

    def capture(args, cwd, env=None):
        seen["args"] = args
        return json.dumps({"headRefName": "review", "headRefOid": sha, "isCrossRepository": False})

    monkeypatch.setattr(_agy, "_run_changed_path_command", capture)
    branch, resolved = _agy.resolve_same_repo_pr_head(9, repo_root=str(repo))
    assert branch == "review"
    assert resolved == sha
    assert seen["args"][seen["args"].index("--repo") + 1] == catalog


def test_empty_and_blank_repo_keys_are_the_same_refusal(tmp_path):
    """Empty and whitespace-only keys are one decision, and neither switches checkout."""
    catalog = load_fleet_repos()["public"].github
    primary = tmp_path / "primary"
    primary_head = _init_committed_repo(primary, f"https://github.com/{catalog}.git", "primary.py")
    worktree = tmp_path / "worktree"
    _git(primary, "worktree", "add", "-q", "-b", "review-wt", str(worktree), "HEAD")
    (worktree / "only.py").write_text("value = 1\n", encoding="utf-8")
    _git(worktree, "add", "only.py")
    _git(worktree, "commit", "-qm", "worktree only")
    worktree_head = _git(worktree, "rev-parse", "HEAD").stdout.strip()
    assert worktree_head != primary_head
    errors = []
    for repo_key in ("", "   "):
        state = tmp_path / f"empty-{len(errors)}.json"
        proc = _run_cli(
            state,
            "target",
            "--mode",
            "commit",
            "--commit",
            "HEAD",
            "--repo-root",
            str(worktree),
            "--repo",
            repo_key,
        )
        assert proc.returncode == 1, proc.stderr
        errors.append(json.loads(proc.stderr)["error"])
        assert primary_head not in proc.stdout
        assert worktree_head not in proc.stdout
        assert str(tmp_path) not in proc.stdout + proc.stderr
        assert not state.exists()
    assert errors[0] == errors[1]
    assert "unknown --repo" in errors[0]


def test_repository_target_error_hides_unavailable_root_oserror():
    if repository_target_error is None:
        pytest.fail("typed missing-checkout refusal is not implemented")
    error = str(
        repository_target_error(
            " infra-private ",
            FileNotFoundError(2, "No such file or directory", "/hidden/absent-root"),
        )
    )
    _assert_neutral_private_refusal(error)
    assert "absent-root" not in error
