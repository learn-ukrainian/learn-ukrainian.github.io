"""#10404: direct branch reviews preserve occupied author checkouts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_authoring_review_feasibility import SOL, mini_repo, pin_review_target
from tests.test_delegate import (
    _fixture_runtime_tmp_root,  # noqa: F401 - shared pytest fixture
    _fixture_worktree_lock_dir,  # noqa: F401 - shared pytest fixture
    _patch_worker_popen,
    _rendered_attempt_prompt,
    _review_code,
    _sanitize_git_env_for_test,
    _stub_node_modules_integrity_sweep,  # noqa: F401 - shared pytest fixture
    _stub_venv_integrity_sweep,  # noqa: F401 - shared pytest fixture
    _write_args,
    delegate,
)

pytestmark = pytest.mark.usefixtures(
    "hermetic_monitor", "_fixture_runtime_tmp_root", "_fixture_worktree_lock_dir",
    "_stub_node_modules_integrity_sweep", "_stub_venv_integrity_sweep",
)


@pytest.fixture
def review_repo(tmp_path, monkeypatch):
    _sanitize_git_env_for_test(monkeypatch)
    repo = mini_repo(tmp_path, monkeypatch)
    (repo.root / ".gitignore").write_text(".worktrees/\nbatch_state/\nignored/\n")
    repo.git("add", ".gitignore")
    repo.git("commit", "-qm", f"ignore local output\n\nX-Agent: {SOL}")
    repo.commit(SOL, path="src/app.py", text="reviewed = True\n")
    head = repo.publish()
    repo.git("checkout", "-q", "-B", "main", "origin/main")
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo.root)
    monkeypatch.setattr(delegate, "_local_repo_root", repo.root)
    monkeypatch.chdir(repo.root)
    monkeypatch.setenv("LU_TASKS_DIR", str(repo.root / "batch_state/tasks"))
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch"))
    pin_review_target(monkeypatch, repo.sha("main"))
    _patch_worker_popen(monkeypatch)
    launches = []
    spawn = delegate.dispatch_isolation.spawn_detached_worker

    def observe_spawn(cmd, **kwargs):
        launches.append(cmd)
        return spawn(cmd, **kwargs)

    monkeypatch.setattr(delegate.dispatch_isolation, "spawn_detached_worker", observe_spawn)
    repo.launches = launches
    return repo, head


def author_state(repo, author):
    return {
        "head": repo.git("-C", str(author), "rev-parse", "HEAD"),
        "branch": repo.git("-C", str(author), "symbolic-ref", "HEAD"),
        "status": repo.git("-C", str(author), "status", "--porcelain=v1", "--ignored", "--untracked-files=all"),
        "refs": repo.git("for-each-ref", "--format=%(refname) %(objectname)", "refs/heads"),
        "files": {str(p.relative_to(author)): p.read_bytes() for p in author.rglob("*") if p.is_file()},
    }


def review_args(head, **overrides):
    return _write_args(
        agent="grok", model="grok-4.7", task_id="snapshot-review", mode="read-only",
        branch="feature", pinned_head=head, review=True, review_profile="code",
        review_author_model="gpt-6.1-sol", review_risk="medium", prompt="Review the exact branch head.",
        **overrides,
    )


@pytest.mark.parametrize("condition", ["clean", "dirty", "unattributed"])
@pytest.mark.parametrize("explicit_path", [False, True])
def test_direct_review_dry_run_plans_new_snapshot_without_touching_author(
    review_repo, monkeypatch, capsys, condition, explicit_path,
):
    repo, head = review_repo
    author = repo.root / ".worktrees/dispatch/codex/author"
    repo.git("worktree", "add", str(author), "feature")
    (author / "ignored").mkdir()
    (author / "ignored/output.bin").write_bytes(b"retained output\x00\xff")
    if condition == "dirty":
        (author / "src/app.py").write_bytes(b"staged author bytes\x00\xff")
        repo.git("-C", str(author), "add", "src/app.py")
        (author / "src/app.py").write_bytes(b"unstaged author bytes\x00\xfe")
        (author / "untracked.bin").write_bytes(b"untracked author bytes\x00\xfd")
    author_record = delegate._state_path("author")
    if condition != "unattributed":
        delegate._write_state_atomic(author_record, {
            "task_id": "author", "status": "done", "mode": "workspace-write",
            "worktree_path": str(author), "worktree_branch": "feature", "keep_worktree": True,
            "worktree_reused": False,
        })
    record_before = author_record.read_bytes() if author_record.exists() else None
    before = author_state(repo, author)
    index = Path(repo.git("-C", str(author), "rev-parse", "--git-path", "index"))
    index_before = index.read_bytes()
    refs_before = repo.git("for-each-ref", "--format=%(refname) %(objectname)")
    trees_before = repo.git("worktree", "list", "--porcelain")
    snapshot = repo.root / ".worktrees/dispatch/grok" / (
        "explicit-review-snapshot" if explicit_path else "snapshot-review"
    )
    if explicit_path:
        snapshot.parent.mkdir(parents=True)
    git_commands = []
    run = subprocess.run

    def observe_git(command, *args, **kwargs):
        if command[0] == "git":
            git_commands.append(command)
        return run(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", observe_git)

    assert delegate.cmd_dispatch(review_args(
        head, dry_run=True, worktree=str(snapshot) if explicit_path else None,
    )) == 0

    output = capsys.readouterr().err
    assert f"planned new detached snapshot: path={snapshot} pinned_head={head}" in output
    assert "remote pin has not been fetched or validated" in output
    assert "branch reuse validated" not in output
    assert "[reused]" not in output
    record = json.loads(delegate._state_path("snapshot-review").read_text())
    assert record["status"] == "dry_run"
    assert record["cwd"] == record["worktree_path"] == str(snapshot)
    assert record["pinned_head"] == head
    assert record["worktree_branch"] is None
    assert record["worktree_base_sha"] is None
    assert record["worktree_reused"] is False
    assert not snapshot.exists()
    assert repo.launches == []
    assert not any("fetch" in command[1:] for command in git_commands)
    assert not any("worktree" in command and "add" in command for command in git_commands)
    assert author_state(repo, author) == before
    assert index.read_bytes() == index_before
    assert repo.git("for-each-ref", "--format=%(refname) %(objectname)") == refs_before
    assert repo.git("worktree", "list", "--porcelain") == trees_before
    assert (author_record.read_bytes() if author_record.exists() else None) == record_before
    assert (author / "ignored/output.bin").read_bytes() == b"retained output\x00\xff"
    if condition == "dirty":
        assert (author / "src/app.py").read_bytes() == b"unstaged author bytes\x00\xfe"
        assert (author / "untracked.bin").read_bytes() == b"untracked author bytes\x00\xfd"
        assert subprocess.run(
            ["git", "-C", str(author), "show", ":src/app.py"], capture_output=True, check=True, timeout=30,
        ).stdout == b"staged author bytes\x00\xff"
    else:
        assert (author / "src/app.py").read_bytes() == b"reviewed = True\n"


@pytest.mark.parametrize("condition", ["clean", "dirty", "unattributed", "unoccupied"])
@pytest.mark.parametrize("explicit_path", [False, True])
def test_direct_review_preserves_author_and_reaps_only_its_snapshot(review_repo, monkeypatch, condition, explicit_path):
    repo, head = review_repo
    author = repo.root / ".worktrees/dispatch/codex/author"
    before = None
    if condition != "unoccupied":
        repo.git("worktree", "add", str(author), "feature")
        (author / "ignored").mkdir()
        (author / "ignored/output.bin").write_bytes(b"retained output\x00\xff")
        if condition == "dirty":
            (author / "src/app.py").write_bytes(b"staged author bytes\x00\xff")
            repo.git("-C", str(author), "add", "src/app.py")
            (author / "src/app.py").write_bytes(b"unstaged author bytes\x00\xfe")
            (author / "untracked.bin").write_bytes(b"untracked author bytes\x00\xfd")
        if condition != "unattributed":
            delegate._write_state_atomic(delegate._state_path("author"), {
                "task_id": "author", "status": "done", "mode": "workspace-write",
                "worktree_path": str(author), "worktree_branch": "feature", "keep_worktree": True,
                "worktree_reused": False,
            })
        before = author_state(repo, author)
    author_record = delegate._state_path("author")
    record_before = author_record.read_bytes() if author_record.exists() else None
    snapshot = repo.root / ".worktrees/dispatch/grok/snapshot-review"
    if explicit_path:
        snapshot.parent.mkdir(parents=True)
    args = review_args(head, worktree=str(snapshot) if explicit_path else None)

    assert delegate.cmd_dispatch(args) == 0

    record = json.loads(delegate._state_path("snapshot-review").read_text())
    assert Path(record["cwd"]) == snapshot
    assert record["worktree_path"] == str(snapshot)
    assert record["worktree_branch"] is None
    assert record["worktree_base_sha"] == record["pinned_head"] == head
    assert record["worktree_reused"] is False
    assert record["worktree_layout"] == "dispatch"
    assert repo.git("-C", str(snapshot), "rev-parse", "HEAD") == head
    assert repo.git("-C", str(snapshot), "symbolic-ref", "-q", "HEAD", check=False) == ""
    assert (snapshot / "src/app.py").read_bytes() == b"reviewed = True\n"
    assert record["agent"] == "grok" and record["model"] == "grok-4.7"
    assert record["review_author_model"] == "gpt-6.1-sol"
    assert len(repo.launches) == 1
    assert before is None or author_state(repo, author) == before
    record.update(status="done")
    delegate._write_state_atomic(delegate._state_path("snapshot-review"), record)
    removal = delegate._settle_worktree_reap(
        snapshot, created_by_this_dispatch=True, settling_task_id="snapshot-review", task_record=record,
    )
    assert removal["action"] == "removed", removal
    assert removal["branch"] is None
    assert not snapshot.exists()
    assert repo.sha("feature") == head
    if before is not None:
        assert author_state(repo, author) == before
    assert (author_record.read_bytes() if author_record.exists() else None) == record_before


def test_remote_moves_after_admission_refuses_before_provider_start(review_repo, monkeypatch, capsys):
    repo, head = review_repo
    author = repo.root / ".worktrees/dispatch/codex/author"
    repo.git("worktree", "add", str(author), "feature")
    before = author_state(repo, author)
    fetch = delegate._fetch_existing_branch

    def fetch_moved_branch(branch):
        repo.advance_remote(branch, SOL, path="src/app.py")
        fetch(branch)

    monkeypatch.setattr(delegate, "_fetch_existing_branch", fetch_moved_branch)

    assert delegate.cmd_dispatch(review_args(head)) == 1

    assert f"differs from the pinned head SHA {head}" in capsys.readouterr().err
    assert repo.launches == []
    assert author_state(repo, author) == before
    assert not (repo.root / ".worktrees/dispatch/grok/snapshot-review").exists()
    record = json.loads(delegate._state_path("snapshot-review").read_text())
    assert record["status"] == "failed"
    assert record["worktree_branch"] is None


def test_write_branch_continuation_reuses_the_existing_attached_tree(review_repo):
    repo, head = review_repo
    author = repo.root / ".worktrees/dispatch/codex/author"
    repo.git("worktree", "add", str(author), "feature")
    before = author_state(repo, author)
    args = _write_args(
        agent="codex", model="gpt-6.1-sol", task_id="write-continuation", branch="feature",
        worktree=str(author), owned_path=["src/app.py"], prompt="Continue the existing task.",
    )

    assert delegate.cmd_dispatch(args) == 0

    record = json.loads(delegate._state_path("write-continuation").read_text())
    assert record["worktree_path"] == record["cwd"] == str(author)
    assert record["worktree_branch"] == "feature"
    assert record["worktree_reused"] is True
    assert record["worktree_base_sha"] == head
    assert author_state(repo, author) == before
    assert len(repo.launches) == 1


@pytest.mark.parametrize("pinned", [False, True])
def test_ordinary_read_only_branch_continuation_keeps_attached_tree(review_repo, pinned):
    repo, head = review_repo
    target = repo.root / ".worktrees/dispatch/codex/continuation"
    repo.git("worktree", "add", str(target), "feature")
    before = author_state(repo, target)
    args = _write_args(
        task_id="continuation", mode="read-only", branch="feature", worktree=str(target),
        pinned_head=head if pinned else None, prompt="Inspect the existing task checkout.",
    )

    assert delegate.cmd_dispatch(args) == 0

    record = json.loads(delegate._state_path("continuation").read_text())
    assert record["worktree_path"] == record["cwd"] == str(target)
    assert record["worktree_branch"] == "feature"
    assert record["worktree_reused"] is True
    assert record["worktree_base_sha"] == head
    assert repo.git("-C", str(target), "symbolic-ref", "HEAD") == "refs/heads/feature"
    assert author_state(repo, target) == before
    assert len(repo.launches) == 1


@pytest.mark.parametrize("explicit_path", [False, True])
def test_review_attempt_preserves_attached_input_and_prepares_in_that_tree(review_repo, monkeypatch, explicit_path):
    repo, head = review_repo
    target = repo.root / ".worktrees/dispatch/claude/attempt-review"
    repo.git("worktree", "add", str(target), "feature")
    _review_code(repo.root)
    _review_code(target)
    manifest = target / "local_state/manifest.yaml"
    manifest.parent.mkdir()
    manifest.write_text("review: test\n")
    repo.git("-C", str(target), "add", ".mcp", "requirements-lock.txt", "scripts/review", "local_state")
    repo.git("-C", str(target), "commit", "-qm", f"admitted attempt inputs\n\nX-Agent: {SOL}")
    head = repo.publish()
    prompt = _rendered_attempt_prompt(repo.root, repo.root / "batch_state/prompt.md", input_root=target)
    monkeypatch.setattr("scripts.agent_runtime.review_mcp.review_server_checkout", lambda: repo.root)
    prepared = []

    def prepare_attempt(**kwargs):
        prepared.append(kwargs)
        return SimpleNamespace(
            config_path=repo.root / "batch_state/attempt.json",
            manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        )

    monkeypatch.setattr("scripts.agent_runtime.review_mcp.prepare_review_attempt", prepare_attempt)
    before = author_state(repo, target)
    args = _write_args(
        agent="claude", model="claude-opus-5-5", task_id="attempt-review", mode="read-only",
        branch="feature", worktree=str(target) if explicit_path else "auto",
        prompt=None, prompt_file=str(prompt), review_attempt=str(manifest),
        review_id="rev-test", attempt_id="att-test",
    )

    assert delegate.cmd_dispatch(args) == 0

    record = json.loads(delegate._state_path("attempt-review").read_text())
    assert record["worktree_path"] == record["cwd"] == str(target)
    assert record["worktree_branch"] == "feature"
    assert record["worktree_reused"] is True
    assert record["worktree_base_sha"] == head
    assert record["review_attempt"]["review_id"] == "rev-test"
    assert len(prepared) == 1
    assert prepared[0]["checkout_root"] == target
    assert prepared[0]["manifest_path"] == manifest
    assert author_state(repo, target) == before
    assert len(repo.launches) == 1
