"""#9742 qualification of caller seams without their own owned test module.

The empty-reservation column is blocked on #9668 (DevOps). These fixtures
qualify interruption handling; they do not supply AC-03's independent controls.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.orchestration import dispatch_settle as ds
from scripts.orchestration import stale_task_records as stale
from scripts.orchestration import worktree_claims as wc
from scripts.orchestration.task_family import git_safety
from tests.helpers.interrupted_checkout import hashes
from tests.helpers.interrupted_checkout import interrupted_checkout as interrupted_checkout
from tests.orchestration.test_worktree_artifacts import assert_record_only

CASES = ("cancelled", "unpushed", "needs_finalize", "retention", "unknown", "rate_limited", "retry", "late")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()


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
        "claim_scan",
        "archive",
        "dead_worker_healer",
        "push_settle",
        "guarded_remove",
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
        if caller == "claim_scan":
            refusal = wc.active_worktree_claim_refusal(tree, tasks_dir=tasks, repo_root=repo)
            assert (refusal is not None) == (status == "needs_finalize" or case == "unknown")
        elif caller == "archive":
            report = stale.archive_terminal(tasks, min_age_days=0, apply=True)
            assert not report["records"]
        elif caller == "dead_worker_healer":
            assert ds.heal_zombie_task(tasks, "interrupted") == []
        elif caller == "push_settle":
            report = ds.settle_task("interrupted", task_dir=tasks, repo_root=repo, release_stale=False)
            assert report.status == state["status"]
        elif caller == "guarded_remove":
            row = wc.remove_unclaimed_worktree(
                tree,
                repo_root=repo,
                reason="caller qualification",
                owner_task_id=None,
                task_record=hint,
            )
            assert row.action in {"removed", "skipped"}, row
        elif caller == "task_family_cleanup":
            if not tree.exists() or state["status"] in {"needs_finalize", "unknown"} or state["keep_worktree"]:
                with pytest.raises(git_safety.GitSafetyError):
                    git_safety.remove_unclaimed_worktree(repo, tree)
            else:
                git_safety.remove_unclaimed_worktree(repo, tree)
        elif caller == "stale_settle":
            report = stale.settle_stale(tasks, min_age_days=0, apply=True, repo_checkouts={}, pager=lambda *_a: [])
            assert all(row["action"] == "report" for row in report["records"]), report
        else:
            raise AssertionError(f"unhandled caller {caller}")
        current = json.loads(record.read_text())
        receipt = current.pop("preserved_artifacts", None)
        assert current == state
        assert hashes([result]) == (before[1],)
        if receipt:
            assert_record_only(receipt, {".cache/output.bin": b"ignored output\x00\xff"})
            assert not (repo / "batch_state/preserved").exists()
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
