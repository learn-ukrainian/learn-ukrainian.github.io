"""Review-round cleanup (#8495) and settle-time reap policy (#8536).

Earlier review rounds are removed when the next round is dispatched.

``ask-codex --review`` and ``ask-agy --review`` create their checkouts
through ``delegate.py dispatch --mode read-only --worktree``
(``scripts/ai_agent_bridge/_dispatch_wrappers.py``). They settle in
``_run_worker``. The sealed snapshot helper tears its temp root down in
``finally`` and is not a second worktree owner.

Removal itself (worktree gone, branch ref kept, dirty trees kept) is
covered in ``tests/test_delegate.py``.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

import scripts.delegate as delegate
from scripts.orchestration import reap_worktrees, worktree_artifacts, worktree_claims


@pytest.mark.parametrize("caller", ["superseded-review", "stale-holder"])
@pytest.mark.parametrize("record_exists", [True, False, "redispatched"])
def test_cleanup_requires_canonical_attribution_and_verified_retrieval(
    tmp_path, monkeypatch, capsys, caller, record_exists
):
    from tests.orchestration.test_worktree_claims_cli import _linked, _primary

    primary = _primary(tmp_path)
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary)
    tasks = primary / "batch_state/tasks"
    tasks.mkdir(parents=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    task_id = "review-output-r1"
    branch = f"codex/{task_id}"
    worktree = _linked(primary, branch)
    with (primary / ".git/info/exclude").open("a") as exclude:
        exclude.write(".cache/\n")
    source = worktree / ".cache/out/answer.txt"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"review output")
    record_path = tasks / f"{task_id}.json"
    if record_exists:
        record = {"task_id": task_id, "status": "done", "worktree_path": str(worktree)}
        if record_exists == "redispatched":
            other = primary / ".worktrees/dispatch/claude" / task_id
            other.mkdir(parents=True)
            record.update(worktree_path=str(other), started_at="2999-01-01T00:00:00Z")
        record_path.write_text(json.dumps(record))
    if caller == "superseded-review":
        monkeypatch.setattr(delegate, "_dispatch_worktree_components", lambda: [(worktree, task_id)])
        monkeypatch.setattr(delegate, "_superseded_review_release_proof", lambda _path: (True, "clean+contained"))
        released = delegate._release_superseded_review_worktrees("review-output-r2", dry_run=False)
    else:
        monkeypatch.setattr(delegate, "_stale_branch_holder_releasable", lambda *_args: (True, "clean+contained"))
        released = delegate._release_stale_branch_holders(branch=branch, holders=[worktree], dry_run=False)
    diagnostic = capsys.readouterr().err
    if record_exists is not True:
        assert released == [] and worktree.exists()
        assert source.read_bytes() == b"review output"
        assert not (primary / "batch_state/preserved" / task_id).exists()
        assert "missing canonical task attribution; refusing worktree removal" in diagnostic
        if record_exists == "redispatched":
            assert json.loads(record_path.read_text()) == record
        else:
            assert not record_path.exists()
        return
    assert released == [worktree] and not worktree.exists()
    receipt = json.loads(record_path.read_text())["preserved_artifacts"]
    assert receipt["count"] == 1 and receipt["bytes"] == len(b"review output")
    location = primary / receipt["location"]
    assert location.parent.name == task_id
    assert (location / ".cache/out/answer.txt").read_bytes() == b"review output"
    from scripts.fleet import ignored_task_output

    assert ignored_task_output.verify_retrieval(primary, receipt) == receipt["retrieval_proof_sha256"]
    assert receipt["retrieval_proof_sha256"] in diagnostic


@pytest.fixture(autouse=True)
def _isolated_worktree_removal(tmp_path, monkeypatch):
    """Keep removal locks and the task-claim scan off the host repository (#8610)."""
    monkeypatch.setattr(delegate, "_WORKTREE_LOCK_DIR", tmp_path / "lu-worktree-locks")
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))


@pytest.mark.parametrize(
    ("mode", "status", "returncode", "dirty", "keep", "expected"),
    [
        ("read-only", "done", 0, False, False, True),
        ("read-only", "failed", 1, False, False, True),
        ("read-only", "no_deliverable", 0, False, False, True),
        ("read-only", "timeout", None, False, False, True),
        ("read-only", "done", 0, True, False, False),
        ("read-only", "done", 0, None, False, False),
        ("read-only", "done", 0, False, True, False),
        ("workspace-write", "done", 0, False, False, True),
        ("workspace-write", "failed", 1, False, False, False),
        ("workspace-write", "done", 0, True, False, False),
        ("workspace-write", "done", 0, False, True, False),
        ("danger", "done", 0, False, False, True),
        ("danger", "failed", 1, False, False, False),
        ("danger", "done", 0, True, False, False),
        ("danger", "done", 0, False, True, False),
    ],
)
def test_settled_worktree_reap_policy(mode, status, returncode, dirty, keep, expected):
    assert (
        delegate._should_reap_settled_worktree(
            mode=mode,
            keep_worktree=keep,
            final_status=status,
            returncode=returncode,
            dirty_on_exit=dirty,
        )
        is expected
    )


def _git(cwd: Path, *args: str) -> str:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and not key.startswith("PRE_COMMIT") and key != "AGENT_NO_MERGE"
    }
    env.update(GIT_TERMINAL_PROMPT="0", GIT_ALLOW_PROTOCOL="file")
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


@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize("release_reason", ["dirty", "live task", "tip not contained in main or a remote ref"])
def test_superseded_review_dependency_is_kept_without_refusing_dispatch(
    monkeypatch, tmp_path, capsys, dry_run, release_reason
):
    earlier = tmp_path / "review-topic-r2"
    earlier.mkdir()
    manifest = earlier / "manifest.yaml"
    manifest.write_text("review: test\n", encoding="utf-8")
    monkeypatch.setattr(delegate, "_dispatch_worktree_components", lambda: [(earlier, "review-topic-r2")])

    with (
        patch.object(delegate, "_superseded_review_release_proof", return_value=(False, release_reason)) as proof,
        patch.object(delegate, "_remove_dispatch_worktree") as remove,
    ):
        released = delegate._release_superseded_review_worktrees(
            "review-topic-r4", dry_run=dry_run, review_dependencies=(("manifest", manifest),)
        )

    assert released == []
    proof.assert_not_called()
    remove.assert_not_called()
    assert manifest.is_file()
    err = capsys.readouterr().err
    assert f"earlier review {earlier} kept: review dependency (manifest)" in err
    assert "would remove" not in err


def test_detached_review_dependency_refusal_remedy_requires_a_separate_retained_checkout(tmp_path):
    holder = tmp_path / "detached-review"
    with pytest.raises(ValueError) as exc:
        delegate._refuse_review_attempt_branch_holders(None, [holder], (("input_root", holder),))
    assert "render from a separate retained worktree at the exact commit" in str(exc.value)
    assert "render from a detached worktree" not in str(exc.value)


def test_later_round_removes_only_earlier_clean_rounds(monkeypatch, tmp_path: Path) -> None:
    from tests.orchestration.test_worktree_claims_cli import _linked, _primary

    primary = _primary(tmp_path)
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary)
    earlier = _linked(primary, "codex/review-topic-r2")
    real_run = subprocess.run
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
        if cmd[:2] == ["git", "ls-files"]:
            return real_run(cmd, **_kwargs)
        if "worktree" in cmd and "remove" in cmd:
            removed.append(cmd[-1])

        class Proc:
            returncode = 0
            stdout = "HEAD\n"
            stderr = ""

        return Proc()

    def fake_safe_git(args, **kwargs):
        assert kwargs["text"] is True
        return fake_run(["git", *args])

    monkeypatch.setattr(reap_worktrees, "safe_git", fake_safe_git)
    monkeypatch.setattr(worktree_claims, "safe_git", fake_safe_git)

    def inventory_git(args, **kwargs):
        # Keep the original real, binary inventory at its new runner seam.
        return real_run(["git", *args], **kwargs)

    monkeypatch.setattr(worktree_artifacts, "safe_git", inventory_git)
    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    released = delegate._release_superseded_review_worktrees("review-topic-r4", dry_run=False)

    assert released == [earlier]
    assert removed == [str(earlier)]


def test_later_round_keeps_an_earlier_round_another_task_still_claims(monkeypatch, tmp_path: Path) -> None:
    """#8610: the release proof and the claim scan run under the earlier round's worktree lock."""
    earlier = tmp_path / "codex" / "review-topic-r2"
    removed: list[str] = []
    proofs_under_lock: list[bool] = []
    monkeypatch.setattr(delegate, "_dispatch_worktree_components", lambda: [(earlier, "review-topic-r2")])

    def releasable(path: Path) -> tuple[bool, str]:
        _canonical, lock_file = delegate._worktree_lock_path(path)
        proofs_under_lock.append(worktree_claims._held_lock_key(lock_file) in worktree_claims._HELD_LOCKS)
        return True, "clean; task status=done"

    monkeypatch.setattr(delegate, "_superseded_review_releasable", releasable)
    delegate._write_state_atomic(
        delegate._state_path("impl-attached"),
        {"task_id": "impl-attached", "status": "running", "worktree_path": str(earlier)},
    )

    def fake_run(cmd, **_kwargs):
        if "worktree" in cmd and "remove" in cmd:
            removed.append(cmd[-1])
        return _git_reply(list(cmd), contained=True)

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    released = delegate._release_superseded_review_worktrees("review-topic-r4", dry_run=False)

    assert released == []
    assert removed == []
    assert proofs_under_lock == [True]


class _Proc:
    def __init__(self, returncode: int = 0, stdout: str | bytes = "", stderr: str | bytes = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _git_reply(cmd: list[str], *, contained: bool | None) -> _Proc:
    """``contained=True`` is an ancestor of origin/main; ``None`` is a git error."""
    if cmd[:2] == ["git", "ls-files"]:
        return _Proc(stdout=b"", stderr=b"")
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
    from tests.orchestration.test_worktree_claims_cli import _linked, _primary

    primary = _primary(tmp_path)
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary)
    earlier = _linked(primary, "codex/review-topic-r2")
    real_run = subprocess.run
    commands: list[list[str]] = []
    monkeypatch.setattr(delegate, "_dispatch_worktree_components", lambda: [(earlier, "review-topic-r2")])
    monkeypatch.setattr(delegate, "_superseded_review_releasable", lambda _path: (True, "clean; task status=done"))

    def fake_run(cmd, **_kwargs):
        if cmd[:2] == ["git", "ls-files"]:
            return real_run(cmd, **_kwargs)
        commands.append(list(cmd))
        return _git_reply(list(cmd), contained=True)

    def fake_safe_git(args, **kwargs):
        assert kwargs["text"] is True
        return fake_run(["git", *args])

    monkeypatch.setattr(reap_worktrees, "safe_git", fake_safe_git)
    monkeypatch.setattr(worktree_claims, "safe_git", fake_safe_git)

    def inventory_git(args, **kwargs):
        return real_run(["git", *args], **kwargs)

    monkeypatch.setattr(worktree_artifacts, "safe_git", inventory_git)
    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    released = delegate._release_superseded_review_worktrees("review-topic-r4", dry_run=False)

    assert released == [earlier]
    assert any(cmd[1:3] == ["worktree", "remove"] for cmd in commands)
    assert ["git", "branch", "-D", "codex/review-topic-r2"] in commands
