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
from scripts.fleet import post_task_reap
from scripts.orchestration import dispatch_settle as ds
from scripts.orchestration import merge_closeout
from scripts.orchestration import reap_worktrees as rw
from scripts.orchestration import stale_task_records as stale
from scripts.orchestration import worktree_claims as wc
from scripts.orchestration.task_family import git_safety

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
    remote = tmp_path / "origin.git"
    git(repo, "init", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    (repo / ".git/info/exclude").write_text("batch_state/\n.cache/\n.worktrees/\n")
    tree = repo / ".worktrees/dispatch/codex/interrupted"
    git(repo, "worktree", "add", "-b", "codex/interrupted", str(tree), "main")
    (tree / "unique.txt").write_bytes(b"unique commit\x00\xff")
    git(tree, "add", "unique.txt")
    git(tree, "commit", "-m", "unique work")
    tasks = repo / "batch_state/tasks"
    tasks.mkdir(parents=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    record = tasks / "interrupted.json"
    result = record.with_suffix(".result")
    result.write_text("Український звіт\u2028recoverable result\n", encoding="utf-8")
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


def test_guarded_remove_non_utf8_result_retains_and_reports(interrupted_checkout):
    """Corrupt textual receipts fail closed; neither output nor result is lost."""
    repo, tree, _tasks, record, result, output = interrupted_checkout
    result.write_bytes(b"corrupt result\x00\xff")
    state = {
        "task_id": "interrupted",
        "status": "done",
        "run_nonce": "attempt",
        "worktree_path": str(tree),
        "result_file": str(result),
        "result_sha256": hashes([result])[0],
    }
    record.write_text(json.dumps(state))
    before = hashes([record, result, output])
    head = git(tree, "rev-parse", "HEAD")
    for _ in range(2):
        row = wc.remove_unclaimed_worktree(
            tree, repo_root=repo, reason="corrupt result qualification", owner_task_id=None
        )
        assert row.action == "skipped" and "utf-8" in row.reason
        assert hashes([result, output]) == before[1:]
        current = json.loads(record.read_text())
        error = current.pop("artifact_preservation_error")
        receipt = current.pop("preserved_artifacts")
        assert current == state and "utf-8" in error
        assert receipt["retention_disposition"] == "retained"
        assert receipt["owner"] and receipt["next_condition"]
        assert tree.exists() and git(tree, "rev-parse", "HEAD") == head


@pytest.mark.parametrize("writer", ["settle", "locked_healer"])
@pytest.mark.parametrize(
    "case", ["cancelled", "unpushed", "needs_finalize", "retention", "unknown", "rate_limited", "retry", "late"]
)
def test_missing_tree_caller_matrix(interrupted_checkout, monkeypatch, writer, case):
    from scripts.orchestration.dead_worker_state import mark_missing_worktree_failed

    repo, tree, tasks, record, result, output = interrupted_checkout
    # Move, rather than destroy, the registered tree. The caller sees its old
    # path missing while every unique commit and ignored byte stays measurable.
    moved = tree.with_name("relocated")
    head = git(tree, "rev-parse", "HEAD")
    git(repo, "worktree", "move", str(tree), str(moved))
    output = moved / output.relative_to(tree)
    state = {
        "task_id": "interrupted",
        "status": case if case in {"cancelled", "rate_limited"} else "needs_finalize",
        "run_nonce": "current",
        "pid": 999_999_999,
        "worktree_path": str(tree),
        "final_branch_head_commit": head,
        "worktree_reused": None if case == "unknown" else False,
        "result_file": str(result),
        "result_sha256": hashes([result])[0],
        "keep_worktree": case == "retention",
    }
    observed = state.copy()
    if case == "late":
        observed.update(status="running", run_nonce="stale")
        state["status"] = "spawning"
        monkeypatch.setattr(ds, "_load_task", lambda *_a: observed)
    record.write_text(json.dumps(state))
    before = hashes([record, result, output])
    for _ in range(2):
        if writer == "settle":
            assert ds.settle_missing_worktree(tasks, "interrupted") == []
        else:
            current, changed = mark_missing_worktree_failed(record, observed, pid_alive=lambda _: False)
            assert not changed and current == state
        assert hashes([record, result, output]) == before
        assert git(moved, "rev-parse", "HEAD") == head


@pytest.mark.parametrize(
    "caller",
    [
        "cancel",
        "claim_scan",
        "husk_sweep",
        "archive",
        "merge_closeout",
        "dead_worker_healer",
        "push_settle",
        "worker_exit_settle",
        "guarded_remove",
        "post_task_reap",
        "scheduled_reaper",
        "success_reaper",
        "task_family_cleanup",
        "stale_settle",
    ],
)
@pytest.mark.parametrize("case", CASES)
def test_interrupted_caller_preserves_bytes_on_repeated_call(interrupted_checkout, caller, case, capsys, monkeypatch):
    repo, tree, tasks, record, result, output = interrupted_checkout
    status = case if case in {"cancelled", "needs_finalize", "rate_limited"} else "done"
    if case == "retry":
        status = "needs_finalize"
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
        "mode": "read-only",
        "worktree_base_sha": git(repo, "rev-parse", "main"),
    }
    if case == "unknown":
        state["status"] = "unknown"
    record.write_text(json.dumps(state, indent=2))
    before = hashes([record, result, output])
    head = git(tree, "rev-parse", "HEAD")
    monkeypatch.setattr(ds, "default_ledger_path", lambda: repo / "ownership.sqlite3")
    monkeypatch.setattr(ds, "_find_pr", lambda *_args: (None, None))
    # These readers consume the current canonical record, not caller snapshots.
    # The two snapshot-taking callers below receive obsolete attempt evidence.
    hint = {**state, "run_nonce": "stale"} if case == "late" else state.copy()
    first_disposition = None
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
        elif caller == "dead_worker_healer":
            assert ds.heal_zombie_task(tasks, "interrupted") == []
        elif caller == "push_settle":
            report = ds.settle_task("interrupted", task_dir=tasks, repo_root=repo, release_stale=False)
            assert report.status == state["status"]
        elif caller == "worker_exit_settle":
            row = delegate._settle_worktree_reap(
                tree,
                created_by_this_dispatch=True,
                settling_task_id="interrupted",
                task_record=hint,
            )
            assert row["action"] == "skipped" and "owner interrupted" in row["reason"], row
        elif caller == "guarded_remove":
            row = wc.remove_unclaimed_worktree(
                tree,
                repo_root=repo,
                reason="caller qualification",
                owner_task_id=None,
                task_record=hint,
            )
            assert row.action in {"removed", "skipped"}, row
        elif caller == "post_task_reap":
            report = post_task_reap.post_task_reap(
                "interrupted",
                tasks_dir=tasks,
                repo_root=repo,
                apply=True,
                include_acp_runtime=False,
            )
            assert report["main_worktree"]["action"] in {"retained", "skipped"}, report
            assert report["main_worktree"]["reason"]
        elif caller == "scheduled_reaper":
            rows = rw.reap_worktrees(
                repo_root=repo,
                target_paths=[tree],
                apply=True,
                include_terminal_dispatches=True,
                live_cwds=set(),
            )
            row = next(row for row in rows if row.path == str(tree))
            assert row.action == "skipped" and row.reason and row.owner, row
        elif caller == "task_family_cleanup":
            if not tree.exists() or state["status"] in {"needs_finalize", "unknown"} or state["keep_worktree"]:
                with pytest.raises(git_safety.GitSafetyError):
                    git_safety.remove_unclaimed_worktree(repo, tree)
            else:
                git_safety.remove_unclaimed_worktree(repo, tree)
        elif caller == "success_reaper":
            row = rw.reap_success_worktree(
                repo_root=repo,
                worktree_path=tree,
                reason="settled dispatch qualification",
                apply=True,
            )
            assert row.action == "skipped" and row.reason and row.owner, row
        elif caller == "stale_settle":
            report = stale.settle_stale(tasks, min_age_days=0, apply=True, repo_checkouts={}, pager=lambda *_a: [])
            assert all(row["action"] == "report" for row in report["records"]), report
        else:
            info = next(info for info in rw.list_git_worktrees(repo) if info.path == tree)
            rows = merge_closeout.reap_matched_worktrees(repo, [info], apply=True, live_cwds=set())
            row = next(row for row in rows if row.path == str(tree))
            assert row.action == "skipped", row
            assert row.reason and row.owner
        current = json.loads(record.read_text())
        receipt = current.pop("preserved_artifacts", None)
        assert current == state
        assert hashes([result]) == (before[1],)
        if receipt:
            assert hashes([repo / receipt["location"] / ".cache/output.bin"]) == (before[2],)
            assert receipt["retrieval_proof_sha256"] == receipt["content_sha256"]
            assert receipt["owner"] == "interrupted" and receipt["next_condition"]
        else:
            assert hashes([record]) == (before[0],)
        if tree.exists():
            assert hashes([output]) == (before[2],)
            assert git(tree, "rev-parse", "HEAD") == head
        else:
            assert caller in {"guarded_remove", "task_family_cleanup"} and receipt
        # Removal retains the branch; commit bytes stay recoverable after both calls.
        assert git(repo, "rev-parse", "codex/interrupted") == head
        disposition = (tree.exists(), current)
        if first_disposition is None:
            first_disposition = disposition
        else:
            assert disposition == first_disposition
