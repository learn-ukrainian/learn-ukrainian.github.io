"""Earlier review rounds are removed when the next round is dispatched."""

from __future__ import annotations

from pathlib import Path

import scripts.delegate as delegate


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
