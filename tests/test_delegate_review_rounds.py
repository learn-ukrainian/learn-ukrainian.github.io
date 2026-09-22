"""Earlier review rounds are removed when the next round is dispatched."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import scripts.delegate as delegate


def _git(cwd: Path, *args: str) -> str:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and not key.startswith("PRE_COMMIT") and key != "AGENT_NO_MERGE"
    }
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        env=env,
        timeout=30,
    )
    return proc.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    remote = tmp_path / "origin.git"
    repo = tmp_path / "repo"
    _git(tmp_path, "init", "--bare", str(remote))
    _git(tmp_path, "init", "--initial-branch=main", str(repo))
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-u", "origin", "main")
    return repo


def _topic_tip(repo: Path) -> str:
    """Push a review topic branch and return its tip SHA."""
    _git(repo, "checkout", "-b", "codex/review-topic-r2")
    (repo / "topic.txt").write_text("review work\n", encoding="utf-8")
    _git(repo, "add", "topic.txt")
    _git(repo, "commit", "-m", "review round work")
    _git(repo, "push", "-u", "origin", "codex/review-topic-r2")
    _git(repo, "checkout", "main")
    return _git(repo, "rev-parse", "codex/review-topic-r2")


def test_containment_counts_live_remote_ref(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    tip = _topic_tip(repo)

    assert delegate._commit_is_durably_contained(repo, tip) is True


def test_containment_counts_live_remote_ref_that_moved_forward(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    tip = _topic_tip(repo)
    # The remote branch advances past the cached tracking ref; the tip is
    # still contained in the live remote head.
    _git(repo, "checkout", "codex/review-topic-r2")
    (repo / "more.txt").write_text("later round\n", encoding="utf-8")
    _git(repo, "add", "more.txt")
    _git(repo, "commit", "-m", "remote moved forward")
    _git(repo, "push", "origin", "codex/review-topic-r2")
    _git(repo, "checkout", "main")
    _git(repo, "update-ref", "refs/remotes/origin/codex/review-topic-r2", tip)

    assert delegate._commit_is_durably_contained(repo, tip) is True


def test_containment_rejects_stale_tracking_ref(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    tip = _topic_tip(repo)
    # The remote branch is deleted but the local tracking ref is never pruned:
    # refs/remotes/origin/codex/review-topic-r2 is now a stale cache and must
    # not count as containment proof.
    _git(tmp_path / "origin.git", "update-ref", "-d", "refs/heads/codex/review-topic-r2")

    assert delegate._commit_is_durably_contained(repo, tip) is False


def test_containment_ls_remote_error_is_not_contained(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    tip = _topic_tip(repo)
    _git(repo, "remote", "set-url", "origin", str(tmp_path / "missing.git"))

    assert delegate._commit_is_durably_contained(repo, tip) is False


def test_review_series_round_numbers() -> None:
    assert delegate._review_series("review-gpt6-routing") == ("review-gpt6-routing", 0)
    assert delegate._review_series("review-gpt6-routing-r7") == ("review-gpt6-routing", 7)
    assert delegate._review_series("review-8340-cf-r10") == ("review-8340-cf", 10)
    assert delegate._review_series("impl-8414") is None


def test_later_round_removes_only_earlier_clean_rounds(monkeypatch, tmp_path: Path) -> None:
    earlier = tmp_path / "codex" / "review-topic-r2"
    same = tmp_path / "agy" / "review-topic-r4"
    other = tmp_path / "codex" / "review-other-r1"
    removed: list[str] = []

    monkeypatch.setattr(
        delegate,
        "_dispatch_worktree_components",
        lambda: [(earlier, "review-topic-r2"), (same, "review-topic-r4"), (other, "review-other-r1")],
    )
    monkeypatch.setattr(delegate, "_superseded_review_releasable", lambda _path: (True, "clean; task status=done"))

    def fake_run(cmd, **_kwargs):
        if "worktree" in cmd and "remove" in cmd:
            removed.append(cmd[-1])

        class Proc:
            returncode = 0
            stdout = "HEAD\n"
            stderr = ""

        return Proc()

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    released = delegate._release_superseded_review_worktrees("review-topic-r4", dry_run=False)

    assert released == [earlier]
    assert removed == [str(earlier)]


class _Proc:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _git_reply(cmd: list[str], *, contained: bool | None) -> _Proc:
    """``contained=True`` is an ancestor of origin/main; ``None`` is a git error."""
    if cmd[:3] == ["git", "rev-parse", "--abbrev-ref"]:
        return _Proc(stdout="codex/review-topic-r2\n")
    if cmd[:2] == ["git", "rev-parse"]:
        return _Proc(stdout="abc123def\n")
    if "merge-base" in cmd:
        if contained is None:
            return _Proc(returncode=128, stderr="fatal: containment check failed")
        return _Proc(returncode=0 if contained else 1)
    if "--contains" in cmd:
        return _Proc(stdout="")
    return _Proc()


def test_uncontained_review_round_is_kept(monkeypatch, tmp_path: Path) -> None:
    earlier = tmp_path / "codex" / "review-topic-r2"
    commands: list[list[str]] = []
    monkeypatch.setattr(delegate, "_dispatch_worktree_components", lambda: [(earlier, "review-topic-r2")])
    monkeypatch.setattr(delegate, "_superseded_review_releasable", lambda _path: (True, "clean; task status=done"))

    def fake_run(cmd, **_kwargs):
        commands.append(list(cmd))
        return _git_reply(list(cmd), contained=False)

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    released = delegate._release_superseded_review_worktrees("review-topic-r4", dry_run=False)

    assert released == []
    assert not any("remove" in cmd for cmd in commands)
    assert not any(cmd[1:3] == ["branch", "-D"] for cmd in commands)


def test_review_round_containment_git_error_is_kept(monkeypatch, tmp_path: Path) -> None:
    earlier = tmp_path / "codex" / "review-topic-r2"
    commands: list[list[str]] = []
    monkeypatch.setattr(delegate, "_dispatch_worktree_components", lambda: [(earlier, "review-topic-r2")])
    monkeypatch.setattr(delegate, "_superseded_review_releasable", lambda _path: (True, "clean; task status=done"))

    def fake_run(cmd, **_kwargs):
        commands.append(list(cmd))
        return _git_reply(list(cmd), contained=None)

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    released = delegate._release_superseded_review_worktrees("review-topic-r4", dry_run=False)

    assert released == []
    assert not any("remove" in cmd for cmd in commands)
    assert not any("--contains" in cmd for cmd in commands)


def test_contained_review_round_deletes_scratch_branch(monkeypatch, tmp_path: Path) -> None:
    earlier = tmp_path / "codex" / "review-topic-r2"
    commands: list[list[str]] = []
    monkeypatch.setattr(delegate, "_dispatch_worktree_components", lambda: [(earlier, "review-topic-r2")])
    monkeypatch.setattr(delegate, "_superseded_review_releasable", lambda _path: (True, "clean; task status=done"))

    def fake_run(cmd, **_kwargs):
        commands.append(list(cmd))
        return _git_reply(list(cmd), contained=True)

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    released = delegate._release_superseded_review_worktrees("review-topic-r4", dry_run=False)

    assert released == [earlier]
    assert any(cmd[1:3] == ["worktree", "remove"] for cmd in commands)
    assert ["git", "branch", "-D", "codex/review-topic-r2"] in commands
