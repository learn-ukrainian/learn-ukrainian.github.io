"""#9742 qualification of caller seams without their own owned test module.

The empty-reservation column is blocked on #9668 (DevOps). These fixtures
qualify interruption handling; they do not supply AC-03's independent controls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import delegate
from scripts.orchestration import merge_closeout
from scripts.orchestration import reap_worktrees as rw
from scripts.orchestration import stale_task_records as stale
from scripts.orchestration import worktree_claims as wc

CASES = ("cancelled", "unpushed", "needs_finalize", "retention", "unknown", "rate_limited", "retry", "late")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()


def hashes(paths):
    return tuple(hashlib.sha256(path.read_bytes()).hexdigest() for path in paths)


@pytest.fixture
def interrupted_checkout(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Caller Test")
    git(repo, "config", "user.email", "caller@example.invalid")
    (repo / "base").write_text("base")
    git(repo, "add", "base")
    git(repo, "commit", "-m", "base")
    (repo / ".git/info/exclude").write_text("batch_state/\n.cache/\n.worktrees/\n")
    tree = repo / ".worktrees/dispatch/codex/interrupted"
    git(repo, "worktree", "add", "-b", "codex/interrupted", str(tree), "main")
    (tree / "unique.txt").write_bytes(b"unique commit\x00\xff")
    git(tree, "add", "unique.txt")
    git(tree, "commit", "-m", "unique work")
    tasks = repo / "batch_state/tasks"
    tasks.mkdir(parents=True)
    record = tasks / "interrupted.json"
    result = record.with_suffix(".result")
    result.write_bytes(b"recoverable result\x00\xff")
    output = tree / ".cache/output.bin"
    output.parent.mkdir()
    output.write_bytes(b"ignored output\x00\xff")
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo)
    monkeypatch.setattr(delegate, "tasks_dir", lambda: tasks)
    monkeypatch.setattr(rw, "_active_task_ids", lambda: set())
    monkeypatch.setattr(rw, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(rw, "_query_pr_states", lambda *_args: ([], None))
    monkeypatch.setattr(rw, "_query_prs_by_head_sha", lambda *_args, **_kw: ([], None))
    return repo, tree, tasks, record, result, output


@pytest.mark.parametrize("caller", ["cancel", "claim_scan", "husk_sweep", "archive", "merge_closeout"])
@pytest.mark.parametrize("case", CASES)
def test_interrupted_caller_preserves_bytes_on_repeated_call(interrupted_checkout, caller, case, capsys):
    repo, tree, tasks, record, result, output = interrupted_checkout
    status = case if case in {"cancelled", "needs_finalize", "rate_limited"} else "done"
    state = {
        "task_id": "interrupted",
        "run_nonce": "current",
        "pid": 999_999_999,
        "status": status,
        "worktree_path": str(tree),
        "worktree_branch": "codex/interrupted",
        "worktree_reused": False,
        "finished_at": "2000-01-01T00:00:00Z",
        "result_file": str(result),
        "result_sha256": hashes([result])[0],
        "keep_worktree": case == "retention",
    }
    if case == "unknown":
        state["status"] = "unknown"
    record.write_text(json.dumps(state, indent=2))
    before = hashes([record, result, output])
    head = git(tree, "rev-parse", "HEAD")
    for _ in range(2):
        if caller == "cancel":
            assert (
                delegate.cmd_cancel(
                    argparse.Namespace(
                        task_id="interrupted",
                        run_nonce="stale" if case == "late" else "current",
                    )
                )
                == 1
            )
            assert "refusing" in capsys.readouterr().err
        elif caller == "claim_scan":
            refusal = wc.active_worktree_claim_refusal(tree, tasks_dir=tasks, repo_root=repo)
            assert (refusal is not None) == (status == "needs_finalize" or case == "unknown")
        elif caller == "husk_sweep":
            assert (
                rw._reap_dispatch_husks(
                    repo,
                    registered={tree},
                    apply=True,
                    live_cwds=set(),
                    targets={tree},
                )
                == []
            )
        elif caller == "archive":
            report = stale.archive_terminal(tasks, min_age_days=0, apply=True)
            assert not report["records"]
        else:
            info = next(info for info in rw.list_git_worktrees(repo) if info.path == tree)
            rows = merge_closeout.reap_matched_worktrees(repo, [info], apply=True, live_cwds=set())
            row = next(row for row in rows if row.path == str(tree))
            assert row.action == "skipped", row
            assert row.reason and row.owner
        assert tree.exists()
        assert hashes([record, result, output]) == before
        assert git(tree, "rev-parse", "HEAD") == head
