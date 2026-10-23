"""Tests for scripts/review/target_resolution.py — deterministic target selection."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common.git_context import sanitized_git_env
from scripts.review.target_resolution import (
    TargetResolutionError,
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
        timeout=30,
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


def _publish_pr_branch(repo: Path, branch: str, sha: str) -> None:
    """Serve a synthetic PR ref through real Git at the fixture's canonical URL."""
    remote = repo.parent / f"{repo.name}-canonical.git"
    origin = _git(repo, "config", "--get", "remote.origin.url").stdout.strip()
    if not remote.exists():
        _git(repo, "init", "-q", "--bare", str(remote))
        _git(repo, "config", f"url.{remote}.insteadOf", origin)
    _git(repo, "update-ref", f"refs/heads/{branch}", sha)
    _git(repo, "--git-dir", str(remote), "fetch", "-q", str(repo), f"refs/heads/{branch}:refs/heads/{branch}")


# --- is_test_path -----------------------------------------------------------


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
    _git(repo, "remote", "add", "origin", "https://github.com/example/catalog.git")
    base_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / "pr_change.py").write_text("value = 1\n", encoding="utf-8")
    _git(repo, "add", "pr_change.py")
    _git(repo, "commit", "-q", "-m", "pr change")
    head_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()

    import scripts.review.target_resolution as tr

    _publish_pr_branch(repo, "feature-branch", head_sha)
    payload = {
        "number": 5283,
        "baseRefName": "release/whatever",  # deliberately NOT "main"
        "baseRefOid": base_sha,
        "headRefName": "feature-branch",
        "headRefOid": head_sha,
        "isCrossRepository": False,
    }

    def fake_run_gh(args, cwd, timeout=30.0):
        assert "view" in args
        assert args[args.index("--repo") + 1] == "example/catalog"
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(tr, "_run_gh", fake_run_gh)

    target = resolve_pr_target(repo, 5283)
    assert target.mode == "pr"
    assert target.base_sha == base_sha
    assert target.base_ref_name == "release/whatever"
    assert target.head_sha == head_sha
    assert "release/whatever" in target.description
    assert target.changed_paths == ("pr_change.py",)


def test_resolve_pr_target_diffs_merge_base_not_moved_base_tip(tmp_path, monkeypatch):
    """The base branch can advance after the PR branch diverged from it.

    ``baseRefOid`` from ``gh pr view`` is the base branch's *current* tip,
    not the commit the PR actually forked from. Diffing straight against
    that tip would pull in the base's own post-divergence commits as if the
    PR introduced them. The target must diff against the merge-base (the
    fork point) instead, and store the merge-base — not the moved tip — as
    ``base_sha``.
    """
    repo = _init_repo(tmp_path)
    _git(repo, "remote", "add", "origin", "https://github.com/example/catalog.git")
    merge_base_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()

    _git(repo, "checkout", "-q", "-b", "feature")
    (repo / "pr_change.py").write_text("value = 1\n", encoding="utf-8")
    _git(repo, "add", "pr_change.py")
    _git(repo, "commit", "-q", "-m", "pr change")
    head_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()

    _git(repo, "checkout", "-q", "trunk")
    # Base branch advances AFTER the feature branch forked off it.
    (repo / "unrelated.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "unrelated.py")
    _git(repo, "commit", "-q", "-m", "base moves on after divergence")
    base_tip_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert base_tip_sha != merge_base_sha

    import scripts.review.target_resolution as tr

    _publish_pr_branch(repo, "feature", head_sha)
    payload = {
        "number": 9001,
        "baseRefName": "trunk",
        "baseRefOid": base_tip_sha,
        "headRefName": "feature",
        "headRefOid": head_sha,
        "isCrossRepository": False,
    }

    def fake_run_gh(args, cwd, timeout=30.0):
        assert "view" in args
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(tr, "_run_gh", fake_run_gh)

    target = resolve_pr_target(repo, 9001)
    assert target.mode == "pr"
    # base_sha is the merge-base (fork point), NOT the base's moved-on tip.
    assert target.base_sha == merge_base_sha
    assert target.base_sha != base_tip_sha
    assert target.head_sha == head_sha
    # Diff must cover only the PR's own change — not the base's post-fork commit.
    assert target.changed_paths == ("pr_change.py",)
    assert "unrelated.py" not in target.changed_paths
    # Base tip is retained for provenance in the description.
    assert base_tip_sha[:12] in target.description
    assert merge_base_sha[:12] in target.description


def test_resolve_pr_target_missing_sha_raises(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    _git(repo, "remote", "add", "origin", "https://github.com/example/catalog.git")
    import scripts.review.target_resolution as tr

    def fake_run_gh(args, cwd, timeout=30.0):
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps({"number": 1}), stderr="")

    monkeypatch.setattr(tr, "_run_gh", fake_run_gh)
    with __import__("pytest").raises(TargetResolutionError):
        resolve_pr_target(repo, 1)


@pytest.mark.parametrize("base_name", ["  ", ["main"], None, 1])
def test_resolve_pr_target_missing_base_name_raises(tmp_path, monkeypatch, base_name):
    repo = _init_repo(tmp_path)
    _git(repo, "remote", "add", "origin", "https://github.com/example/catalog.git")
    sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    import scripts.review.target_resolution as tr

    payload = {"number": 1, "baseRefOid": sha, "headRefOid": sha, "baseRefName": base_name, "isCrossRepository": False}

    def fake_run_gh(args, cwd, timeout=30.0):
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(tr, "_run_gh", fake_run_gh)
    with __import__("pytest").raises(TargetResolutionError, match="base ref name"):
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


@pytest.fixture
def live_pr_boundary(tmp_path, monkeypatch):
    """Real canonical Git plus fake forge metadata; every non-Git process is a tripwire."""
    from types import SimpleNamespace

    import delegate
    from scripts.ai_agent_bridge import _agy, _cli
    from scripts.common import github_client
    from scripts.review import record_cf_verdict as recorder
    from tests.test_authoring_review_feasibility import mini_repo

    repo = mini_repo(tmp_path, monkeypatch)
    monkeypatch.setenv("GIT_ALLOW_PROTOCOL", "file")
    stale = repo.sha("HEAD")
    live = repo.commit("codex/gpt-6.1-sol")
    repo.publish()
    state = SimpleNamespace(
        repo=repo, live=live, stale=stale, author_commits=1, observe=None, forge_hook=None, before_facts=None,
        observations=[], commands=[],
        payload={
            "number": 42,
            "baseRefName": "main",
            "baseRefOid": repo.sha("origin/main"),
            "headRefName": "feature",
            "headRefOid": stale,
            "isCrossRepository": False,
        },
    )
    real_run, real_popen = subprocess.run, subprocess.Popen

    def git_popen(command, *args, **kwargs):
        assert command[0] == "git", "provider or other external process reached"
        kwargs["env"] = {**(kwargs.get("env") or os.environ), "GIT_ALLOW_PROTOCOL": "file"}
        return real_popen(command, *args, **kwargs)

    def git_only(command, *args, **kwargs):
        state.commands.append(tuple(command))
        assert command[0] == "git", "provider or other external process reached"
        kwargs["env"] = {**(kwargs.get("env") or os.environ), "GIT_ALLOW_PROTOCOL": "file"}
        proc = real_run(command, *args, **kwargs)
        if command[:2] == ["git", "ls-remote"]:
            assert command[-2:] == [
                "https://github.com/learn-ukrainian/learn-ukrainian.github.io.git", "refs/heads/feature"
            ]
            assert kwargs["timeout"] == 60.0
            assert "GIT_DIR" not in kwargs["env"] and "GIT_WORK_TREE" not in kwargs["env"]
            state.observations.append(proc)
            if state.observe is not None:
                return state.observe(command, proc)
        return proc

    def forge(command, *args, **kwargs):
        if command[0] == "gh":
            assert command[command.index("--repo") + 1] == "learn-ukrainian/learn-ukrainian.github.io"
            if state.forge_hook is not None:
                state.forge_hook()
            return subprocess.CompletedProcess(command, 0, json.dumps(state.payload), "")
        kwargs.pop("fresh", None)
        return git_only(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", git_only)
    monkeypatch.setattr(subprocess, "Popen", git_popen)
    monkeypatch.setattr(github_client, "run", forge)
    monkeypatch.setattr(recorder, "_run_json", lambda *_a, **_k: state.payload)
    monkeypatch.setattr(_cli, "REPO_ROOT", repo.root)
    monkeypatch.setattr(delegate, "_local_repo_root", repo.root)
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo.root)
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))

    def invoke(entry):
        if entry in {"cli", "agy"}:
            if entry == "cli":
                branch, head = _cli._resolve_same_repo_pr_head(42)
            else:
                branch, head = _agy.resolve_same_repo_pr_head(42, repo_root=str(repo.root))
            assert branch == "feature"
            assert _agy.list_commit_changed_paths(head, repo_root=str(repo.root)) == ["docs/a.md"]
            # Exercise the actual fetch/recheck shared by both ask dispatches,
            # stopping before worktree creation and every provider side effect.
            return delegate._resolve_worktree_base_sha(
                agent="codex", task_id="live-head-fixture", base="main", branch=branch,
                pinned_head_sha=head, detached=True, validated_path=tmp_path / "review",
            )
        if entry == "target":
            target = resolve_pr_target(repo.root, 42)
        else:
            args = delegate.build_parser().parse_args([
                "dispatch", "--agent", "claude", "--model", "claude-opus-5-5",
                "--mode", "read-only", "--task-id", "live-head-fixture", "--pr", "42",
                "--review-mode", "red_team", "--review-risk", "critical",
            ])
            delegate._dispatch_review_changed_paths(args)
            if state.before_facts is not None:
                state.before_facts()
            facts = delegate._dispatch_review_facts(args, ())
            assert facts.author_models == ("gpt-6.1-sol",) * state.author_commits
            target = args._review_target
            assert facts.head_sha == target.head_sha
        assert target.base_sha == repo.sha("origin/main")
        assert target.changed_paths == ("docs/a.md",)
        return target.head_sha

    state.invoke = invoke
    yield state
    assert all(command[0] == "git" for command in state.commands)
    assert not (tmp_path / "tasks").exists()
    assert not (tmp_path / "review").exists()


@pytest.mark.parametrize("entry", ["cli", "agy", "target", "delegate"])
@pytest.mark.parametrize("remote_only", [False, True], ids=["local-commit", "unfetched-commit"])
def test_stale_payload_pins_live_canonical_branch(live_pr_boundary, entry, remote_only):
    """Stale forge metadata must not pin an older commit than the live branch (#9666)."""
    state = live_pr_boundary
    if remote_only:
        state.live = state.repo.advance_remote("feature", "codex/gpt-6.1-sol")
        state.author_commits = 2
        with pytest.raises(subprocess.CalledProcessError):
            state.repo.git("cat-file", "-e", state.live)
    assert state.invoke(entry) == state.live
    assert state.observations


_REMOTE_REF_FAILURES = [
    "deleted", "duplicate", "conflicting", "wrong-ref", "empty", "malformed-sha", "zero-sha",
    "space-delimiter", "extra-text", "unicode-terminator", "missing-terminator",
    "command-error", "timeout", "oserror", "unavailable-commit",
]


@pytest.mark.parametrize("entry", ["cli", "agy", "target", "delegate"])
@pytest.mark.parametrize("failure", _REMOTE_REF_FAILURES)
def test_untrusted_live_ref_refuses_before_provider(live_pr_boundary, entry, failure):
    """Ambiguous, unavailable or malformed live refs cannot fall back to payload/main."""
    state = live_pr_boundary
    sentinel = "REMOTE_DIAGNOSTIC_MUST_STAY_PRIVATE"
    if failure == "deleted":
        state.repo.git("--git-dir", str(state.repo.remote), "update-ref", "-d", "refs/heads/feature")

    def observe(command, proc):
        raw = proc.stdout
        replacements = {
            "duplicate": raw + raw,
            "conflicting": raw + f"{state.stale}\trefs/heads/feature\n",
            "wrong-ref": raw.replace("refs/heads/feature", "refs/heads/main"),
            "empty": "",
            "malformed-sha": f"{'z' * 40}\trefs/heads/feature\n",
            "zero-sha": f"{'0' * 40}\trefs/heads/feature\n",
            "space-delimiter": raw.replace("\t", " "),
            "extra-text": "unexpected diagnostic\n" + raw,
            "unicode-terminator": raw.replace("\n", "\u2028"),
            "missing-terminator": raw.rstrip("\n"),
            "unavailable-commit": f"{'e' * 40}\trefs/heads/feature\n",
        }
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 60.0, stderr=sentinel)
        if failure == "oserror":
            raise OSError(sentinel)
        if failure == "command-error":
            return subprocess.CompletedProcess(command, 128, raw, sentinel)
        return subprocess.CompletedProcess(command, proc.returncode, replacements.get(failure, raw), sentinel)

    state.observe = observe
    with pytest.raises((SystemExit, RuntimeError)) as refused:
        state.invoke(entry)
    assert str(refused.value)
    assert sentinel not in str(refused.value)
    assert state.observations


@pytest.mark.parametrize("entry", ["cli", "agy", "target", "delegate"])
@pytest.mark.parametrize("failure", ["foreign", "unknown-repository", "repository-changed", "unsafe-branch", "invalid-sha"])
def test_untrusted_pr_metadata_refuses_before_provider(live_pr_boundary, entry, failure):
    """Live observation never licenses foreign, unknown or malformed forge targets."""
    state = live_pr_boundary
    if failure == "foreign":
        state.payload["isCrossRepository"] = True
    elif failure == "unknown-repository":
        del state.payload["isCrossRepository"]
    elif failure == "repository-changed":
        state.forge_hook = lambda: state.repo.git("config", "remote.origin.url", "https://github.com/foreign/repo.git")
    elif failure == "unsafe-branch":
        state.payload["headRefName"] = "feature~1"
    else:
        state.payload["headRefOid"] = "invalid"
    with pytest.raises((SystemExit, RuntimeError)):
        state.invoke(entry)
    assert not state.observations


@pytest.mark.parametrize("entry", ["cli", "agy", "target", "delegate"])
def test_live_branch_movement_after_pinning_refuses_before_provider(live_pr_boundary, entry):
    """A canonical ref moving after the first observation cannot replace the pin."""
    state = live_pr_boundary

    def move_after_observation(command, proc):
        if len(state.observations) == 1:
            state.repo.advance_remote("feature", "codex/gpt-6.1-sol")
        return proc

    state.observe = move_after_observation
    with pytest.raises((SystemExit, RuntimeError), match=r"moved|pinned head"):
        state.invoke(entry)
    assert state.observations[0].stdout == f"{state.live}\trefs/heads/feature\n"


def test_delegate_live_branch_movement_after_resolution_refuses_before_provider(live_pr_boundary):
    """A stale payload cannot hide movement between target resolution and admission."""
    state = live_pr_boundary
    state.before_facts = lambda: state.repo.advance_remote("feature", "codex/gpt-6.1-sol")
    with pytest.raises(RuntimeError, match="PR head moved"):
        state.invoke("delegate")
    assert len(state.observations) == 3


@pytest.mark.parametrize("failure", ["timeout", "oserror"])
def test_cli_forge_failure_refuses_before_observing_a_live_pin(live_pr_boundary, failure):
    """An unavailable forge must not fall back to a branch or reach a provider."""
    state = live_pr_boundary

    def unavailable_forge():
        if failure == "timeout":
            raise subprocess.TimeoutExpired(["gh", "pr", "view"], 60)
        raise OSError("forge unavailable")

    state.forge_hook = unavailable_forge
    with pytest.raises(SystemExit, match="could not resolve the PR head"):
        state.invoke("cli")
    assert not state.observations


@pytest.mark.parametrize("failure", ["missing-checkout", "unrecognized-origin"])
def test_cli_unbound_canonical_repository_refuses_before_forge(live_pr_boundary, monkeypatch, failure):
    """A missing or unrecognized canonical repository cannot authorize a forge lookup."""
    from scripts.ai_agent_bridge import _cli

    state = live_pr_boundary
    if failure == "missing-checkout":
        monkeypatch.setattr(_cli, "REPO_ROOT", state.repo.root / "missing")
    else:
        state.repo.git("config", "remote.origin.url", "https://example.invalid/unknown.git")
    state.forge_hook = lambda: pytest.fail("unbound repository reached forge")
    with pytest.raises(SystemExit, match="canonical repository unavailable"):
        state.invoke("cli")
    assert not state.observations
