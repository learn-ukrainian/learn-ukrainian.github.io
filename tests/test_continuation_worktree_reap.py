"""Continuation cohorts from #10008, using disposable records and Git trees."""

import contextlib
import json
import os

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.fleet import post_task_reap as reap
from scripts.orchestration import merge_closeout
from scripts.orchestration import worktree_claims as claims
from tests.orchestration.test_worktree_claims_cli import _git
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree
from tests.test_reused_worktree_retention import cohort as cohort
from tests.test_reused_worktree_retention import save


def continuation(cohort, case):
    repo, tree, tasks, creator, successor, source = cohort
    creator.update(keep_worktree=False, status="needs_finalize" if case == "E" else "done")
    if case == "E":
        creator["final_branch_head_commit"] = "a" * 40
    successor.update(keep_worktree=False, attribution_source="session_env" if case == "E" else "explicit")
    third = dict(successor, task_id="third", run_nonce="third-run")
    for record in (creator, successor, third):
        save(tasks, record)
    historical = creator if case == "C" else successor
    archived = dict(historical, status="failed", run_nonce="prior-run", worktree_reused=False)
    if case == "E":
        archived.update(worktree_branch=None, pid=None)
    (tasks / f"{historical['task_id']}.20261007T130120593046Z.archived.json").write_text(json.dumps(archived))
    return repo, tree, tasks, creator, successor, source


@pytest.mark.parametrize("case", ["C", "E"])
@pytest.mark.parametrize("ignored_output", [False, True])
def test_merged_continuations_closeout_without_force(cohort, monkeypatch, case, ignored_output):
    repo, tree, tasks, creator, _, source = continuation(cohort, case)
    if not ignored_output:
        source.unlink()
    path, owner = output.resolve_worktree_record(tree, tasks, repo_root=repo)
    assert path == tasks / "boundary.json" and owner == creator
    expected_head = _git(tree, "rev-parse", "HEAD")
    before = {p: p.read_bytes() for p in tasks.glob("*.json")}
    dry = merge_closeout.run_merge_closeout(repo, 9645, apply=False, live_cwds=set())
    assert dry.reap_results[0]["action"] == "would_remove", dry
    assert {p: p.read_bytes() for p in before} == before
    calls = []
    original = claims.git_worktree_remove

    def remove(*args, **kwargs):
        calls.append(kwargs["force"])
        return original(*args, **kwargs)

    monkeypatch.setattr(claims, "git_worktree_remove", remove)
    result = merge_closeout.run_merge_closeout(repo, 9645, apply=True, live_cwds=set())
    row = result.reap_results[0]
    assert row["action"] == "removed", row
    assert calls == [False] and not tree.exists()
    record = json.loads(path.read_text())
    assert record["status"] == creator["status"]
    proof = record["worktree_reap_proof"]
    assert proof == row["preserved_artifacts"]["merged_head_proof"]
    assert proof["owner"] == "boundary" and proof["head_sha"] == expected_head
    assert proof["pr_number"] == 9645 and proof["clean"] is True
    assert len(proof["members"]) == 3
    if ignored_output:
        receipt = row["preserved_artifacts"]
        assert output.verify_retrieval(repo, receipt) == receipt["retrieval_proof_sha256"]
        assert (repo / receipt["location"] / "ignored/output.txt").read_bytes() == b"current output"


@pytest.mark.parametrize("case", ["C", "E"])
@pytest.mark.parametrize(
    "failure", ["dirty", "unpushed", "unmerged", "head_not_merged", "running", "branch", "two_creators", "live_pid"]
)
def test_continuation_failures_keep_tree_and_records(cohort, monkeypatch, case, failure):
    repo, tree, tasks, _, successor, source = continuation(cohort, case)
    if failure == "dirty":
        (tree / "untracked.txt").write_text("unique bytes")
    elif failure in {"unpushed", "unmerged", "head_not_merged"}:
        _git(tree, "commit", "--allow-empty", "-m", "unique commit")
        if failure != "unpushed":
            _git(tree, "push", "origin", "codex/boundary")
        if failure == "unmerged":
            monkeypatch.setattr(reap.reap_worktrees, "_query_pr_states", lambda *_args: ([], None))
            monkeypatch.setattr(reap.reap_worktrees, "_query_prs_by_head_sha", lambda *_args: ([], None))
    else:
        if failure == "running":
            successor["status"] = "running"
        elif failure == "branch":
            successor["worktree_branch"] = "codex/other"
        elif failure == "two_creators":
            successor["worktree_reused"] = False
        else:
            successor["pid"] = os.getpid()
        save(tasks, successor)
    before = {p: p.read_bytes() for p in tasks.glob("*.json")}
    rows = reap.reap_worktrees.reap_worktrees(repo_root=repo, apply=True, live_cwds=set())
    row = next(r for r in rows if r.path == str(tree))
    assert row.action == "skipped", row
    assert tree.exists() and source.read_bytes() == b"current output"
    assert {p: p.read_bytes() for p in before} == before


def test_D_force_new_history_does_not_replace_creator_or_release_proof(cohort):
    repo, tree, tasks, creator, successor, _ = cohort
    creator.update(status="needs_finalize", final_branch_head_commit="a" * 40)
    save(tasks, creator)
    for task in ("second", "third"):
        save(tasks, dict(successor, task_id=task, run_nonce=f"{task}-run"))
    archive = tasks / "successor.20261007T130120593046Z.archived.json"
    archive.write_text(
        json.dumps(dict(successor, status="failed", worktree_reused=False, run_nonce="old-run", pid=None))
    )
    path, owner = output.resolve_worktree_record(tree, tasks, repo_root=repo)
    assert path == tasks / "boundary.json" and owner == creator
    archived_bytes = archive.read_bytes()
    dry = next(row for row in reap.reap_worktrees.reap_worktrees(repo_root=repo, apply=False) if row.path == str(tree))
    assert dry.action == "skipped" and "keep_worktree" in dry.reason
    assert "existing passing retrieval receipt" in reap._release_retention(
        "boundary", tasks_dir=tasks, repo_root=repo, apply=True
    )
    report = reap.post_task_reap("boundary", tasks_dir=tasks, repo_root=repo, apply=True, include_acp_runtime=False)
    assert report["main_worktree"]["preserved_artifacts"]["owner"] == "boundary"
    assert reap._release_retention("boundary", tasks_dir=tasks, repo_root=repo, apply=True) is None
    assert archive.read_bytes() == archived_bytes
    assert all(
        not member.get("keep_worktree") for _, member in output.matching_worktree_records(tree, tasks, repo_root=repo)
    )
    report = reap.post_task_reap("boundary", tasks_dir=tasks, repo_root=repo, apply=True, include_acp_runtime=False)
    assert report["main_worktree"]["action"] == "removed", report


@pytest.mark.parametrize("failure", ["ordinary_archive", "no_replacement", "same_nonce", "active", "missing_nonce"])
def test_unproven_archive_stays_ambiguous(cohort, failure):
    repo, tree, tasks, _, successor, _ = cohort
    archive = tasks / "successor.20261007T130120593046Z.archived.json"
    old = dict(successor, worktree_reused=False, status="failed", run_nonce="old-run")
    if failure == "ordinary_archive":
        archive = tasks / "archive/successor.json"
        archive.parent.mkdir()
    elif failure == "no_replacement":
        old["task_id"] = "other"
        archive = tasks / "other.20261007T130120593046Z.archived.json"
    elif failure == "same_nonce":
        old["run_nonce"] = successor["run_nonce"]
    elif failure == "active":
        old["status"] = "running"
    else:
        old.pop("run_nonce")
    archive.write_text(json.dumps(old))
    with pytest.raises(ValueError, match="ambiguous"):
        output.resolve_worktree_record(tree, tasks, repo_root=repo)


def test_explicit_receipt_release_keeps_existing_nonmerge_reap_path(cohort, monkeypatch):
    repo, tree, tasks, _, _, _ = cohort
    retrieved = reap.post_task_reap("boundary", tasks_dir=tasks, repo_root=repo, apply=True)
    assert retrieved["main_worktree"]["preserved_artifacts"]["retrieval_proof_sha256"]
    assert reap._release_retention("boundary", tasks_dir=tasks, repo_root=repo, apply=True) is None
    monkeypatch.setattr(reap.reap_worktrees, "_query_pr_states", lambda *_args: ([], None))
    monkeypatch.setattr(reap.reap_worktrees, "_query_prs_by_head_sha", lambda *_args: ([], None))
    row = next(r for r in reap.reap_worktrees.reap_worktrees(repo_root=repo, apply=True) if r.path == str(tree))
    assert row.action == "removed", row
    receipt = row.preserved_artifacts
    assert receipt["retention_release"]["owner"] == "boundary"
    assert output.verify_retrieval(repo, receipt) == receipt["retrieval_proof_sha256"]


def test_merged_cohort_change_at_lock_keeps_claim(cohort, monkeypatch):
    repo, tree, tasks, creator, successor, _ = continuation(cohort, "E")
    lock = claims.worktree_lock

    @contextlib.contextmanager
    def change(path, **kwargs):
        successor["run_nonce"] = "new-run"
        save(tasks, successor)
        with lock(path, **kwargs):
            yield

    monkeypatch.setattr(claims, "worktree_lock", change)
    info = reap.reap_worktrees.WorktreeInfo(tree, "codex/boundary", _git(tree, "rev-parse", "HEAD"))
    with contextlib.ExitStack() as stack:
        refusal = reap.reap_worktrees._enter_dispatch_worktree_guard(stack, repo_root=repo, info=info)
    assert refusal is not None and "needs_finalize owner boundary attempt changed" in refusal
    assert json.loads((tasks / "boundary.json").read_text())["status"] == creator["status"]
    assert tree.exists()


@pytest.mark.parametrize("failure", ["nonce", "canonical", "record", "member", "head", "dirty", "late_live"])
def test_merged_proof_refuses_identity_and_checkout_changes(cohort, monkeypatch, failure):
    repo, tree, tasks, _, successor, _ = continuation(cohort, "C")
    info = reap.reap_worktrees.WorktreeInfo(tree, "codex/boundary", _git(tree, "rev-parse", "HEAD"))
    pr = reap.reap_worktrees.PullRequestState(9645, "MERGED", info.head)
    if failure == "nonce":
        successor["run_nonce"] = " "
        save(tasks, successor)
    elif failure == "canonical":
        (tasks / "boundary.json").rename(tasks / "unbound.json")
    elif failure == "late_live":
        calls = []

        def absent(_record):
            calls.append(1)
            return len(calls) <= 3

        monkeypatch.setattr(reap.reap_worktrees, "_pid_proven_absent", absent)
    else:
        original = output.artifacts.task_state_lock
        changed = []

        @contextlib.contextmanager
        def change(path):
            if not changed:
                changed.append(True)
                if failure == "record":
                    successor["run_nonce"] = "new-run"
                    save(tasks, successor)
                elif failure == "member":
                    save(tasks, dict(successor, task_id="new-member", run_nonce="new-member-run"))
                elif failure == "head":
                    _git(tree, "commit", "--allow-empty", "-m", "checkout changed")
                else:
                    (tree / "untracked.txt").write_text("unique bytes")
            with original(path):
                yield

        monkeypatch.setattr(output.artifacts, "task_state_lock", change)
    with claims.worktree_lock(tree, lock_dir=claims.repository_lock_dir(repo)):
        with pytest.raises(ValueError):
            reap.reap_worktrees._record_merged_reuse_proof(repo, info, pr, tasks_dir=tasks)
    assert tree.exists()
    assert not any("worktree_reap_proof" in json.loads(p.read_text()) for p in tasks.glob("*.json"))
