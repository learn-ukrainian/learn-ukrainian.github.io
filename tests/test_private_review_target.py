"""Repository-context regressions for private review targets (#10557)."""

from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from scripts.common.git_context import sanitized_git_env
from scripts.common.repo_root import main_checkout_root
from scripts.orchestration import fleet_repos
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
REVIEW_ROOT_MISMATCH = getattr(
    target_resolution,
    "REVIEW_ROOT_MISMATCH",
    "REVIEW_ROOT_MISMATCH: --repo-root origin does not match the catalog repository; "
    "symbolic refs and local mode are refused",
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


def _assert_specific_private_refusal(error: str, phrase: str) -> None:
    assert phrase in error
    assert "PRIVATE_REVIEW_TARGET_UNRESOLVED" not in error
    assert "checkout or target unavailable" not in error


def _unrelated_commit(repo) -> str:
    tree = _git(repo, "rev-parse", "HEAD^{tree}").stdout.strip()
    return _git(repo, "commit-tree", tree, "-m", "unrelated").stdout.strip()


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


@pytest.fixture
def review_repositories(tmp_path, monkeypatch):
    public = tmp_path / "public"
    private = tmp_path / "private-checkout"
    catalog = load_fleet_repos()
    patched = dict(catalog)
    patched["infra-private"] = dataclasses.replace(catalog["infra-private"], local_name=private.name)
    original_load = fleet_repos.load_fleet_repos

    def _load(path=None):
        if path is not None:
            return original_load(path)
        return patched

    monkeypatch.setattr(fleet_repos, "load_fleet_repos", _load)
    monkeypatch.setattr(target_resolution, "load_fleet_repos", _load)
    origins = {
        public: f"https://github.com/{catalog['public'].github}.git",
        private: f"https://github.com/{catalog['infra-private'].github}.git",
    }
    heads = [
        _init_committed_repo(public, origins[public], "public.py"),
        _init_committed_repo(private, origins[private], "private.py"),
    ]
    assert _git(public, "cat-file", "-e", heads[1], check=False).returncode != 0
    return public, private, heads








def test_closeout_private_only_sha_resolves(review_repositories, tmp_path):
    public, private, heads = review_repositories
    state = tmp_path / "closeout.json"
    proc = _run_cli(
        state, "target", "--mode", "commit", "--commit", heads[1], "--repo-root", str(public), "--repo", "infra-private"
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["changed_paths"] == ["private.py"]
    saved = json.loads(state.read_text())
    assert saved["target"]["head_sha"] == heads[1]
    assert saved["target_args"]["repo_root"] == str(private)


@pytest.mark.parametrize("failure", ["missing_clone", "unknown_sha", "public_only_sha"])
def test_private_target_refusal_names_trigger(review_repositories, tmp_path, failure):
    public, private, heads = review_repositories
    head = heads[0] if failure == "public_only_sha" else "f" * 40
    if failure == "missing_clone":
        private.rename(tmp_path / "unavailable")
    state = tmp_path / "refused.json"
    proc = _run_cli(
        state, "target", "--mode", "commit", "--commit", head, "--repo-root", str(public), "--repo", "infra-private"
    )
    assert proc.returncode == 1
    error = json.loads(proc.stderr)["error"]
    assert not state.exists()
    _assert_neutral_private_refusal(error)
    assert str(tmp_path) not in error


def test_public_target_still_resolves(review_repositories, tmp_path):
    public, _private, heads = review_repositories
    proc = _run_cli(
        tmp_path / "public.json", "target", "--mode", "commit", "--commit", heads[0], "--repo-root", str(public)
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["changed_paths"] == ["public.py"]


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








def test_private_missing_merge_base_keeps_specific_text(review_repositories, tmp_path):
    public, private, _heads = review_repositories
    unrelated = _unrelated_commit(private)
    state = tmp_path / "merge-base.json"
    proc = _run_cli(
        state,
        "target",
        "--mode",
        "branch",
        "--branch",
        unrelated,
        "--base",
        "origin/main",
        "--repo-root",
        str(public),
        "--repo",
        "infra-private",
    )
    assert proc.returncode == 1
    error = json.loads(proc.stderr)["error"]
    assert not state.exists()
    _assert_specific_private_refusal(error, "no merge-base")


def test_private_wrong_base_keeps_specific_text(review_repositories, tmp_path):
    public, _private, _heads = review_repositories
    proc = _run_cli(
        tmp_path / "wrong-base.json",
        "target",
        "--mode",
        "branch",
        "--branch",
        "origin/review",
        "--base",
        "no-such-base",
        "--repo-root",
        str(public),
        "--repo",
        "infra-private",
    )
    assert proc.returncode == 1, proc.stderr
    error = json.loads(proc.stderr)["error"]
    _assert_specific_private_refusal(error, "no-such-base")
    assert "cannot resolve ref" in error


def test_closeout_repo_flag_refuses_contradictory_root(review_repositories, tmp_path):
    public, private, heads = review_repositories
    catalog_public = load_fleet_repos()["public"].github
    matched = _run_cli(
        tmp_path / "matched.json",
        "target",
        "--mode",
        "commit",
        "--commit",
        heads[0],
        "--repo-root",
        str(public),
        "--repo",
        "public",
    )
    assert matched.returncode == 0, matched.stderr
    assert json.loads(matched.stdout)["changed_paths"] == ["public.py"]

    refused = _run_cli(
        tmp_path / "refused.json",
        "target",
        "--mode",
        "commit",
        "--commit",
        heads[1],
        "--repo-root",
        str(private),
        "--repo",
        "public",
    )
    assert refused.returncode == 1
    error = json.loads(refused.stderr)["error"]
    assert "does not match catalog repository" in error
    assert catalog_public in error
    assert str(private) not in error
    assert str(tmp_path) not in refused.stderr
    assert "private.py" not in refused.stdout
    assert not (tmp_path / "refused.json").exists()


def test_check_expansion_uses_stored_repository_root(review_repositories, tmp_path):
    public, private, heads = review_repositories
    (private / "extra.py").write_text("value = 1\n", encoding="utf-8")
    state = tmp_path / "expansion.json"
    target = _run_cli(
        state,
        "target",
        "--mode",
        "local",
        "--repo-root",
        str(private),
        "--repo",
        "infra-private",
    )
    assert target.returncode == 0, target.stderr
    assert json.loads(target.stdout)["changed_paths"] == ["extra.py"]
    assert _freeze(state).returncode == 0
    for index in range(5):
        (public / f"extra{index}.py").write_text("x = 1\n" * 20, encoding="utf-8")

    expansion = _run_cli(state, "check-expansion", "--repo-root", str(public))
    assert expansion.returncode == 0, expansion.stderr
    assert json.loads(expansion.stdout)["triggered"] is False

    commit_state = tmp_path / "commit-expansion.json"
    commit_target = _run_cli(
        commit_state,
        "target",
        "--mode",
        "commit",
        "--commit",
        heads[1],
        "--repo-root",
        str(public),
        "--repo",
        "infra-private",
    )
    assert commit_target.returncode == 0, commit_target.stderr
    assert _freeze(commit_state, issue="#10557-commit").returncode == 0
    commit_expansion = _run_cli(commit_state, "check-expansion", "--repo-root", str(public), "--current-head", heads[1])
    assert commit_expansion.returncode == 0, commit_expansion.stderr
    assert json.loads(commit_expansion.stdout)["triggered"] is False


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


def test_mismatched_origin_refuses_symbolic_refs_and_local_mode(review_repositories, tmp_path):
    public, _private, heads = review_repositories
    symbolic_refs = ("HEAD", "HEAD~1", "origin/review^")
    for ref in symbolic_refs:
        proc = _run_cli(
            tmp_path / f"symbolic-{ref.replace('/', '-')}.json",
            "target",
            "--mode",
            "commit",
            "--commit",
            ref,
            "--repo-root",
            str(public),
            "--repo",
            "infra-private",
        )
        assert proc.returncode == 1, proc.stderr
        assert json.loads(proc.stderr)["error"] == REVIEW_ROOT_MISMATCH

    local = _run_cli(
        tmp_path / "local.json",
        "target",
        "--mode",
        "local",
        "--repo-root",
        str(public),
        "--repo",
        "infra-private",
    )
    assert local.returncode == 1, local.stderr
    assert json.loads(local.stderr)["error"] == REVIEW_ROOT_MISMATCH

    branch_relative = _run_cli(
        tmp_path / "branch-relative.json",
        "target",
        "--mode",
        "branch",
        "--branch",
        "origin/review^",
        "--base",
        "origin/main",
        "--repo-root",
        str(public),
        "--repo",
        "infra-private",
    )
    assert branch_relative.returncode == 1, branch_relative.stderr
    assert json.loads(branch_relative.stderr)["error"] == REVIEW_ROOT_MISMATCH

    resolved = _run_cli(
        tmp_path / "sha.json",
        "target",
        "--mode",
        "commit",
        "--commit",
        heads[1],
        "--repo-root",
        str(public),
        "--repo",
        "infra-private",
    )
    assert resolved.returncode == 0, resolved.stderr
    assert json.loads(resolved.stdout)["head_sha"] == heads[1]
    assert json.loads(resolved.stdout)["changed_paths"] == ["private.py"]

    named = _run_cli(
        tmp_path / "branch.json",
        "target",
        "--mode",
        "branch",
        "--branch",
        "origin/review",
        "--base",
        "origin/main",
        "--repo-root",
        str(public),
        "--repo",
        "infra-private",
    )
    assert named.returncode == 0, named.stderr
    assert json.loads(named.stdout)["head_sha"] == heads[1]


def test_missing_or_unparsable_origin_is_not_kept(review_repositories, tmp_path):
    public, _private, _heads = review_repositories
    _git(public, "remote", "remove", "origin")
    missing = _run_cli(
        tmp_path / "no-origin.json",
        "target",
        "--mode",
        "commit",
        "--commit",
        "HEAD",
        "--repo-root",
        str(public),
        "--repo",
        "public",
    )
    assert missing.returncode == 1, missing.stderr
    assert json.loads(missing.stderr)["error"] == REVIEW_ROOT_MISMATCH

    _git(public, "remote", "add", "origin", "not-a-github-remote")
    unparsable = _run_cli(
        tmp_path / "bad-origin.json",
        "target",
        "--mode",
        "local",
        "--repo-root",
        str(public),
        "--repo",
        "public",
    )
    assert unparsable.returncode == 1, unparsable.stderr
    assert json.loads(unparsable.stderr)["error"] == REVIEW_ROOT_MISMATCH




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


@pytest.mark.parametrize("repo_key", [" infra-private ", "INFRA-PRIVATE"])
@pytest.mark.parametrize(
    ("mode", "commit"),
    [("commit", "HEAD"), ("local", None)],
)
def test_noncanonical_private_key_hits_root_guard(review_repositories, tmp_path, repo_key, mode, commit):
    """Padding and case still take the symbolic-ref and local-mode guard."""
    public, _private, heads = review_repositories
    state = tmp_path / "guard.json"
    args = ["target", "--mode", mode, "--repo-root", str(public), "--repo", repo_key]
    if commit is not None:
        args.extend(["--commit", commit])
    proc = _run_cli(state, *args)
    assert proc.returncode == 1, proc.stderr
    assert json.loads(proc.stderr)["error"] == REVIEW_ROOT_MISMATCH
    combined = proc.stdout + proc.stderr
    assert heads[1] not in combined
    assert str(tmp_path) not in combined
    assert not state.exists()


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


def test_public_missing_repo_root_has_no_absolute_path(review_repositories, tmp_path):
    state = tmp_path / "public-absent.json"
    missing = tmp_path / "absent-public-root"
    proc = _run_cli(state, "target", "--mode", "local", "--repo-root", str(missing), "--repo", "public")
    assert proc.returncode == 1, proc.stderr
    error = json.loads(proc.stderr)["error"]
    assert error == "REVIEW_ROOT_UNAVAILABLE: --repo-root is not a checkout"
    assert "PRIVATE_REVIEW_TARGET_UNRESOLVED" not in error
    combined = proc.stdout + proc.stderr
    assert str(missing) not in combined
    assert "Errno" not in combined
    assert not state.exists()


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
