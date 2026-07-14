from __future__ import annotations

import json
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from ai_agent_bridge import _cli
from ai_agent_bridge import _review_worktree as review_worktree


def test_provision_review_worktree_fetches_origin_head_and_reaps_on_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A failing reviewer cannot strand the fetched detached checkout."""
    checkout_path = tmp_path / "review-checkout"
    checkout_path.mkdir()
    calls: list[tuple[list[str], Path]] = []
    sha = "a" * 40

    monkeypatch.setattr(review_worktree.tempfile, "mkdtemp", lambda **_kwargs: str(checkout_path))

    def fake_run(command: list[str], *, cwd: Path) -> str:
        calls.append((command, cwd))
        if command[:4] == ["git", "worktree", "add", "--detach"]:
            path = Path(command[4])
            path.mkdir()
            (path / "tracked.py").write_text("value = 1\n", encoding="utf-8")
        if command == ["git", "rev-parse", "--verify", "origin/feature/review"]:
            return sha
        if command == ["git", "rev-parse", "HEAD"]:
            return sha
        return ""

    monkeypatch.setattr(review_worktree, "_run_command", fake_run)

    with pytest.raises(RuntimeError, match="reviewer failed"):
        with review_worktree.provision_review_worktree(
            review_worktree.ReviewTarget(branch="feature/review"), repo_root=tmp_path
        ) as checkout:
            assert checkout is not None
            assert checkout.branch == "feature/review"
            assert checkout.sha == sha
            assert not (checkout.path / "tracked.py").stat().st_mode & stat.S_IWUSR
            raise RuntimeError("reviewer failed")

    commands = [command for command, _cwd in calls]
    assert ["git", "fetch", "origin", "feature/review"] in commands
    assert ["git", "rev-parse", "--verify", "origin/feature/review"] in commands
    assert ["git", "worktree", "add", "--detach", str(checkout_path), sha] in commands
    assert ["git", "worktree", "remove", "--force", str(checkout_path)] in commands
    assert not any(command == ["git", "rev-parse", "feature/review"] for command in commands)


def test_pr_review_target_resolves_head_then_fetches_origin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    checkout_path = tmp_path / "review-checkout"
    checkout_path.mkdir()
    calls: list[list[str]] = []
    sha = "b" * 40

    monkeypatch.setattr(review_worktree.tempfile, "mkdtemp", lambda **_kwargs: str(checkout_path))

    def fake_run(command: list[str], *, cwd: Path) -> str:
        calls.append(command)
        if command[:4] == ["git", "worktree", "add", "--detach"]:
            Path(command[4]).mkdir()
        if command == ["gh", "pr", "view", "5150", "--json", "headRefName"]:
            return json.dumps({"headRefName": "codex/5150-review"})
        if command == ["git", "rev-parse", "--verify", "origin/codex/5150-review"]:
            return sha
        if command == ["git", "rev-parse", "HEAD"]:
            return sha
        return ""

    monkeypatch.setattr(review_worktree, "_run_command", fake_run)

    with review_worktree.provision_review_worktree(
        review_worktree.ReviewTarget(pr_number=5150), repo_root=tmp_path
    ) as checkout:
        assert checkout is not None
        assert checkout.branch == "codex/5150-review"
        assert checkout.pr_number == 5150

    assert calls.index(["git", "fetch", "origin", "codex/5150-review"]) > calls.index(
        ["gh", "pr", "view", "5150", "--json", "headRefName"]
    )


def test_review_target_metadata_rejects_ambiguous_or_malformed_values() -> None:
    assert review_worktree.review_target_payload(branch="feature/review") == {
        "branch": "feature/review"
    }
    assert review_worktree.review_target_from_message(
        {"data": json.dumps({"review_target": {"pr": 123}})}
    ) == review_worktree.ReviewTarget(pr_number=123)
    with pytest.raises(ValueError, match="exactly one"):
        review_worktree.review_target_payload(branch="feature/review", pr_number=123)
    with pytest.raises(ValueError, match="non-empty"):
        review_worktree.review_target_payload(branch="")
    with pytest.raises(review_worktree.ReviewWorktreeError, match="must be an integer"):
        review_worktree.review_target_from_message(
            {"data": json.dumps({"review_target": {"pr": "123"}})}
        )


def test_review_cli_accepts_explicit_branch_only_with_review() -> None:
    parser = _cli._build_parser()
    args = parser.parse_args(
        [
            "ask-agy",
            "Review the branch.",
            "--task-id",
            "review-5150",
            "--review",
            "--branch",
            "feature/review",
        ]
    )

    assert _cli._review_target_kwargs(args) == {
        "review_branch": "feature/review",
        "review_pr_number": None,
    }

    args.review = False
    with pytest.raises(SystemExit, match="require --review"):
        _cli._review_target_kwargs(args)
