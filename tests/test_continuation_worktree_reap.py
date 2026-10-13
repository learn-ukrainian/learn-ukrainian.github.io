"""Continuation cohorts from #10008, using disposable records and Git trees."""

import contextlib
import json
import os
import shutil
import subprocess

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.fleet import post_task_reap as reap
from scripts.orchestration import merge_closeout
from scripts.orchestration import worktree_claims as claims
from tests.orchestration.test_worktree_claims_cli import _git
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree
from tests.test_reused_worktree_retention import cohort as cohort
from tests.test_reused_worktree_retention import save


@pytest.fixture
def earlier_cohort(cohort, monkeypatch):
    """Three real commits: creator, settled successor, and later reviewed PR head."""
    from tests.orchestration.test_merge_closeout import git, patch_gh

    repo, tree, tasks, creator, successor, source = cohort
    creator.update(
        keep_worktree=False, status="needs_finalize", final_branch_head_commit=_git(tree, "rev-parse", "HEAD")
    )
    _git(tree, "commit", "--allow-empty", "-m", "successor")
    head = _git(tree, "rev-parse", "HEAD")
    successor.update(keep_worktree=False, final_branch_head_commit=head)
    _git(tree, "commit", "--allow-empty", "-m", "review fixes")
    reviewed = _git(tree, "rev-parse", "HEAD")
    _git(tree, "push", "origin", "codex/boundary")
    _git(repo, "merge", "--no-ff", "codex/boundary", "-m", "merge reviewed PR")
    git(repo, "push", "origin", "main")
    _git(tree, "checkout", "--detach", head)
    for record in (creator, successor):
        save(tasks, record)
    patch_gh(
        monkeypatch,
        pr_number=9645,
        state="MERGED",
        head_ref_name="codex/boundary",
        head_sha=reviewed,
        branch_prs={"codex/boundary": [{"number": 9645, "state": "MERGED", "headRefOid": reviewed}]},
    )
    return repo, tree, tasks, creator, successor, source, reviewed


@pytest.mark.parametrize("ignored_output", [False, True])
@pytest.mark.parametrize("entry", ["reaper", "post_task"])
def test_detached_earlier_cohort_settles_through_common_reaper(earlier_cohort, monkeypatch, ignored_output, entry):
    repo, tree, tasks, creator, successor, source, reviewed = earlier_cohort
    if not ignored_output:
        source.unlink()
    before = {p: p.read_bytes() for p in tasks.glob("*.json")}
    dry = next(
        r
        for r in reap.reap_worktrees.reap_worktrees(repo_root=repo, apply=False, live_cwds=set())
        if r.path == str(tree)
    )
    assert dry.action == "would_remove", dry
    assert {p: p.read_bytes() for p in before} == before
    calls = []
    original = claims.git_worktree_remove

    def remove(*args, **kwargs):
        calls.append(kwargs["force"])
        return original(*args, **kwargs)

    monkeypatch.setattr(claims, "git_worktree_remove", remove)
    if entry == "reaper":
        result = next(
            r
            for r in reap.reap_worktrees.reap_worktrees(repo_root=repo, apply=True, live_cwds=set())
            if r.path == str(tree)
        )
        row = {"action": result.action, "preserved_artifacts": result.preserved_artifacts}
    else:
        row = reap.post_task_reap("boundary", tasks_dir=tasks, repo_root=repo, apply=True, include_acp_runtime=False)[
            "main_worktree"
        ]
    assert row["action"] == "removed", row
    assert calls == [False] and not tree.exists()
    current = json.loads((tasks / "boundary.json").read_text())
    assert current["status"] == creator["status"]
    proof = current["worktree_reap_proof"]
    assert proof["head_sha"] == successor["final_branch_head_commit"]
    assert proof["pr_head_sha"] == reviewed and proof["head_relation"] == "ancestor"
    assert proof == row["preserved_artifacts"]["merged_head_proof"]
    if ignored_output:
        receipt = row["preserved_artifacts"]
        assert output.verify_retrieval(repo, receipt) == receipt["retrieval_proof_sha256"]
        assert (repo / receipt["location"] / "ignored/output.txt").read_bytes() == b"current output"


@pytest.mark.parametrize(
    "failure",
    [
        "live_creator",
        "live_successor",
        "unknown_pid",
        "missing_pid",
        "missing_nonce",
        "missing_commit",
        "creator_diverged",
        "successor_head",
        "branch",
        "two_creators",
        "running",
        "retained",
        "dirty",
        "attached",
        "unmerged",
        "pr_unknown",
        "pr_diverged",
        "preservation",
    ],
)
def test_earlier_cohort_uncertainty_retains_checkout(earlier_cohort, monkeypatch, failure):
    repo, tree, tasks, creator, successor, source, reviewed = earlier_cohort
    rw = reap.reap_worktrees
    if failure == "live_creator":
        creator["pid"] = os.getpid()
    elif failure == "live_successor":
        successor["pid"] = os.getpid()
    elif failure == "unknown_pid":

        def unknown(*_args):
            raise PermissionError("process probe denied")

        monkeypatch.setattr(rw.os, "kill", unknown)
    elif failure == "missing_pid":
        successor.pop("pid")
    elif failure == "missing_nonce":
        successor.pop("run_nonce")
    elif failure == "missing_commit":
        creator["final_branch_head_commit"] = "f" * 40
    elif failure in {"creator_diverged", "pr_diverged"}:
        _git(tree, "checkout", "--detach", creator["final_branch_head_commit"])
        _git(tree, "commit", "--allow-empty", "-m", "unmerged sibling")
        divergent = _git(tree, "rev-parse", "HEAD")
        _git(tree, "checkout", "--detach", successor["final_branch_head_commit"])
        if failure == "creator_diverged":
            creator["final_branch_head_commit"] = divergent
        else:
            monkeypatch.setattr(
                rw, "_query_pr_states", lambda *_: ([rw.PullRequestState(9645, "MERGED", divergent)], None)
            )
    elif failure == "successor_head":
        successor["final_branch_head_commit"] = reviewed
    elif failure == "branch":
        successor["worktree_branch"] = "codex/conflict"
    elif failure == "two_creators":
        successor["worktree_reused"] = False
    elif failure == "running":
        successor["status"] = "running"
    elif failure == "retained":
        creator["keep_worktree"] = True
    elif failure == "dirty":
        (tree / "README.md").write_text("unique work")
    elif failure == "attached":
        _git(tree, "checkout", "-B", "codex/boundary", successor["final_branch_head_commit"])
    elif failure == "unmerged":
        monkeypatch.setattr(rw, "_query_pr_states", lambda *_: ([rw.PullRequestState(9645, "OPEN", reviewed)], None))
    elif failure == "pr_unknown":
        monkeypatch.setattr(rw, "_query_pr_states", lambda *_: ([], "PR lookup unavailable"))
    else:
        monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 0)
    for record in (creator, successor):
        save(tasks, record)
    before = {p: p.read_bytes() for p in tasks.glob("*.json")}
    row = next(r for r in rw.reap_worktrees(repo_root=repo, apply=True, live_cwds=set()) if r.path == str(tree))
    assert row.action == "skipped", row
    assert tree.exists() and source.read_bytes() == b"current output"
    for path, data in before.items():
        current = json.loads(path.read_text())
        if failure == "preservation":
            if path.name == "boundary.json":
                assert "exceeds preservation cap" in current.pop("artifact_preservation_error")
                current.pop("worktree_reap_proof")
            current.pop("preserved_artifacts", None)
        assert current == json.loads(data)


@pytest.mark.parametrize("probe", [None, "error", "empty", "attached"])
def test_detached_attribution_requires_positive_branch_probe(earlier_cohort, monkeypatch, probe):
    import subprocess

    repo, tree, tasks, *_ = earlier_cohort
    result = (
        None
        if probe is None
        else subprocess.CompletedProcess(
            [], 128 if probe == "error" else 0, "codex/boundary" if probe == "attached" else "", ""
        )
    )
    monkeypatch.setattr(claims, "checked_out_branch", lambda _tree: None)
    monkeypatch.setattr(claims, "_git_probe", lambda *_args, **_kwargs: result)
    with pytest.raises(ValueError, match="ambiguous"):
        output.reused_worktree_creator(
            output.matching_worktree_records(tree, tasks, repo_root=repo, publish_cache=False),
            tree,
            repo_root=repo,
            tasks_dir=tasks,
        )


def test_earlier_cohort_reattached_at_task_lock_retains_tree(earlier_cohort, monkeypatch):
    repo, tree, tasks, _, successor, _, reviewed = earlier_cohort
    rw = reap.reap_worktrees
    info = rw.WorktreeInfo(tree, None, successor["final_branch_head_commit"], detached=True)
    original = output.artifacts.task_state_lock
    changed = []

    @contextlib.contextmanager
    def reattach(path):
        if not changed:
            changed.append(True)
            _git(tree, "checkout", "-B", "codex/boundary", info.head)
        with original(path):
            yield

    monkeypatch.setattr(output.artifacts, "task_state_lock", reattach)
    with claims.worktree_lock(tree, lock_dir=claims.repository_lock_dir(repo)):
        with pytest.raises(ValueError, match="ancestry changed"):
            rw._record_merged_reuse_proof(repo, info, rw.PullRequestState(9645, "MERGED", reviewed), tasks_dir=tasks)
    assert tree.exists()
    assert "worktree_reap_proof" not in json.loads((tasks / "boundary.json").read_text())


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
    dry = next(row for row in reap.reap_worktrees.reap_worktrees(repo_root=repo, apply=False) if row.path == str(tree))
    assert dry.action == "skipped" and "keep_worktree" in dry.reason
    assert "existing passing retrieval receipt" in reap._release_retention(
        "boundary", tasks_dir=tasks, repo_root=repo, apply=True
    )
    report = reap.post_task_reap("boundary", tasks_dir=tasks, repo_root=repo, apply=True, include_acp_runtime=False)
    assert report["main_worktree"]["preserved_artifacts"]["owner"] == "boundary"
    assert reap._release_retention("boundary", tasks_dir=tasks, repo_root=repo, apply=True) is None
    released_archive = json.loads(archive.read_text())
    assert released_archive["status"] == "failed" and released_archive["run_nonce"] == "old-run"
    assert released_archive["keep_worktree"] is False
    assert released_archive["preserved_artifacts"]["retention_release"]["owner"] == "boundary"
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


@pytest.mark.parametrize("archived_reuse", [False, True])
def test_H1_force_new_archive_retention_survives_closeout(cohort, archived_reuse):
    repo, tree, tasks, _, successor, source = continuation(cohort, "C")
    archive = tasks / "successor.20261007T140000Z.archived.json"
    archive.write_text(
        json.dumps(
            dict(successor, status="failed", run_nonce="old-run", keep_worktree=True, worktree_reused=archived_reuse)
        )
    )
    result = merge_closeout.run_merge_closeout(repo, 9645, apply=True, live_cwds=set())
    row = result.reap_results[0]
    assert row["action"] == "skipped", row
    assert "keep_worktree" in row["reason"]
    assert tree.exists() and source.read_bytes() == b"current output"
    assert json.loads(archive.read_text())["keep_worktree"] is True
    assert not any("worktree_reap_proof" in json.loads(p.read_text()) for p in tasks.glob("*.json"))
    # Retention remains releasable only through the existing verified receipt.
    assert reap._release_retention("boundary", tasks_dir=tasks, repo_root=repo, apply=True) is None
    assert json.loads(archive.read_text())["keep_worktree"] is False
    row = merge_closeout.run_merge_closeout(repo, 9645, apply=True, live_cwds=set()).reap_results[0]
    assert row["action"] == "removed" and not tree.exists(), row


def test_H7_single_needs_finalize_owner_keeps_main_behavior(boundary_tree):
    repo, tree, tasks, creator = boundary_tree
    creator.update(
        status="needs_finalize", pid=999_999_999, final_branch_head_commit="a" * 40, worktree_branch="codex/boundary"
    )
    save(tasks, creator)
    row = merge_closeout.run_merge_closeout(repo, 9645, apply=True, live_cwds=set()).reap_results[0]
    assert row["action"] == "removed" and not tree.exists(), row


@pytest.mark.parametrize("number_head", ["different", "unavailable", "exact"])
def test_commit_search_requires_real_pr_head(cohort, monkeypatch, number_head):
    repo, tree, tasks, _, _, source = continuation(cohort, "C")
    head = _git(tree, "rev-parse", "HEAD")
    # Search includes this commit but does not report the PR's actual head.
    hit, error = reap.reap_worktrees._parse_search_pr_item({"number": 9645, "state": "MERGED"}, head)
    assert error is None
    monkeypatch.setattr(reap.reap_worktrees, "_query_pr_states", lambda *_args: ([], None))
    monkeypatch.setattr(reap.reap_worktrees, "_query_prs_by_head_sha", lambda *_args: ([hit], None))
    monkeypatch.setattr(reap.reap_worktrees, "_is_ancestor_of_origin_main", lambda *_args, **_kwargs: False)
    calls = []

    def by_number(_repo, number):
        calls.append(number)
        if number_head == "unavailable":
            return [], "PR lookup unavailable"
        real_head = head if number_head == "exact" else "b" * 40
        return [reap.reap_worktrees.PullRequestState(number, "MERGED", real_head)], None

    monkeypatch.setattr(reap.reap_worktrees, "_query_pr_by_number", by_number)
    row = next(
        r
        for r in reap.reap_worktrees.reap_worktrees(repo_root=repo, apply=True, live_cwds=set())
        if r.path == str(tree)
    )
    if number_head == "exact":
        assert row.action == "removed" and not tree.exists(), row
        assert calls == [9645]
        assert row.preserved_artifacts["merged_head_proof"]["head_sha"] == head
    else:
        assert row.action == "skipped", row
        assert tree.exists() and source.read_bytes() == b"current output"
        assert not any("worktree_reap_proof" in json.loads(p.read_text()) for p in tasks.glob("*.json"))


def test_nonforce_cohort_removal_runs_delete_target_guard(cohort, monkeypatch):
    monkeypatch.delenv("TMPDIR", raising=False)
    repo, tree, _, _, _, source = continuation(cohort, "C")
    calls = []

    def refuse(target, **kwargs):
        calls.append((target, kwargs["repo_root"]))
        raise ValueError("held-out delete-target refusal")

    monkeypatch.setattr(reap.reap_worktrees, "assert_delete_target", refuse)
    row = merge_closeout.run_merge_closeout(repo, 9645, apply=True, live_cwds=set()).reap_results[0]
    assert row["action"] == "error", row
    assert "delete guard refused" in row["error"]
    assert calls == [(tree, repo)]
    assert tree.exists() and source.read_bytes() == b"current output"


def test_nonforce_scratch_cohort_uses_approved_delete_root(cohort, monkeypatch):
    monkeypatch.delenv("TMPDIR", raising=False)
    repo, tree, tasks, *_ = continuation(cohort, "C")
    scratch = repo.parent / "scratch-cohort"
    _git(repo, "worktree", "move", str(tree), str(scratch))
    for path in tasks.glob("*.json"):
        record = json.loads(path.read_text())
        for field in ("worktree_path", "cwd"):
            if record.get(field) == str(tree):
                record[field] = str(scratch)
        path.write_text(json.dumps(record))
    monkeypatch.setattr(reap.reap_worktrees, "_foreign_scratch_roots", lambda: (repo.parent,))
    guard = reap.reap_worktrees.assert_delete_target
    calls = []

    def check(target, **kwargs):
        calls.append((target, kwargs["approved_temp_roots"]))
        return guard(target, **kwargs)

    monkeypatch.setattr(reap.reap_worktrees, "assert_delete_target", check)
    head = _git(scratch, "rev-parse", "HEAD")
    row = reap.reap_worktrees._reap_qualified_worktree(
        repo_root=repo,
        info=reap.reap_worktrees.WorktreeInfo(scratch, "codex/boundary", head),
        reason="PR #9645 MERGED",
        dirty=False,
        pr_state=reap.reap_worktrees.PullRequestState(9645, "MERGED", head),
        apply=True,
        preserve_then_reap=False,
        prune_merged_branches=False,
        require_terminal_dispatch_guards=False,
    )

    assert row.action == "removed", (row.reason, row.error)
    assert calls == [(scratch, (repo.parent,))]
    assert not scratch.exists()


@pytest.mark.parametrize("created_evidence", [False, True])
def test_failed_preparation_without_no_checkout_proof_stays_ambiguous(cohort, created_evidence):
    repo, tree, tasks, _, _, source = cohort
    record = {
        "task_id": "failed-validation",
        "run_nonce": "validation-run",
        "status": "failed",
        "last_error": "worktree_preparation_failed",
        "returncode_reason": "worktree preparation failed",
        "worktree_path": str(tree),
        "worktree_reused": False,
        "keep_worktree": True,
        "pid": None,
        "worktree_base_sha": None,
        "worktree_branch": None,
        # The failure writer snapshots existing HEAD too; this is not creation proof.
        "final_branch_head_commit": _git(tree, "rev-parse", "HEAD"),
    }
    if created_evidence:
        record.update(
            worktree_base_sha=record["final_branch_head_commit"],
            worktree_branch="codex/boundary",
            worktree_prep={"reserved_by_mkdir": True, "git_pid": 999_999_999},
        )
    save(tasks, record)
    with pytest.raises(ValueError, match="ambiguous"):
        output.resolve_worktree_record(tree, tasks, repo_root=repo)
    report = reap.post_task_reap(
        "failed-validation", tasks_dir=tasks, repo_root=repo, apply=True, include_acp_runtime=False
    )
    assert report["main_worktree"]["action"] in {"skipped", "retained"}, report
    assert tree.exists() and source.read_bytes() == b"current output"
    assert json.loads((tasks / "failed-validation.json").read_text()) == record


def _switched_branch_cohort(cohort, monkeypatch, *, head_status="needs_finalize"):
    """Creator of one family, three later rounds of another, checkout on a new branch.

    Records keep the dispatch-time branch name. The last round's recorded head
    is the clean checkout, which equals the merged PR head.
    """
    from tests.orchestration.test_merge_closeout import git, patch_gh

    repo, tree, tasks, creator, successor, source = cohort
    dispatch_branch = "codex/boundary"
    fresh_branch = "cursor/fresh-gate"
    creator_head = _git(tree, "rev-parse", "HEAD")
    creator.update(
        agent="gemini",
        status="needs_finalize",
        keep_worktree=False,
        worktree_branch=dispatch_branch,
        final_branch_head_commit=creator_head,
        pid=999_999_991,
        run_nonce="creation-nonce",
    )
    _git(tree, "commit", "--allow-empty", "-m", "round one")
    round_one = _git(tree, "rev-parse", "HEAD")
    _git(tree, "commit", "--allow-empty", "-m", "round two")
    round_two = _git(tree, "rev-parse", "HEAD")
    _git(tree, "checkout", "-b", fresh_branch)
    _git(tree, "commit", "--allow-empty", "-m", "round three switched branch")
    merged_head = _git(tree, "rev-parse", "HEAD")
    _git(tree, "push", "-u", "origin", fresh_branch)
    git(repo, "merge", "--no-ff", fresh_branch, "-m", "merge switched PR")
    git(repo, "push", "origin", "main")

    def round_record(task_id, nonce, status, commit, pid, branch=dispatch_branch):
        return dict(
            successor,
            task_id=task_id,
            agent="cursor",
            run_nonce=nonce,
            status=status,
            worktree_reused=True,
            keep_worktree=False,
            worktree_branch=branch,
            final_branch_head_commit=commit,
            pid=pid,
        )

    rounds = [
        round_record("round-one", "round-one", "needs_finalize", round_one, 999_999_992),
        round_record("round-two", "round-two", "needs_finalize", round_two, 999_999_993),
        round_record("round-three", "round-three", head_status, merged_head, 999_999_994),
        round_record("round-failed", "round-failed", "failed", round_one, 999_999_995),
    ]
    (tasks / "successor.json").unlink()
    for record in (creator, *rounds):
        save(tasks, record)
    patch_gh(
        monkeypatch,
        pr_number=10548,
        state="MERGED",
        head_ref_name=fresh_branch,
        head_sha=merged_head,
        branch_prs={fresh_branch: [{"number": 10548, "state": "MERGED", "headRefOid": merged_head}]},
    )
    return repo, tree, tasks, creator, rounds, source, fresh_branch, merged_head


@pytest.mark.parametrize("head_status", ["needs_finalize", "done"])
def test_switched_branch_cohort_is_reaped_with_branch_deleted(cohort, monkeypatch, head_status):
    repo, tree, tasks, creator, _rounds, source, fresh_branch, merged_head = _switched_branch_cohort(
        cohort, monkeypatch, head_status=head_status
    )
    source.unlink()
    result = merge_closeout.run_merge_closeout(repo, 10548, apply=True, live_cwds=set())
    row = result.reap_results[0]
    assert row["action"] == "removed", result
    assert not tree.exists()
    proof = json.loads((tasks / "boundary.json").read_text())["worktree_reap_proof"]
    assert proof["schema"] == "merged-reuse-reap.v1"
    assert proof["owner"] == creator["task_id"]
    assert proof["head_sha"] == merged_head
    assert proof["pr_head_sha"] == merged_head and proof["head_relation"] == "exact"
    assert proof["pr_number"] == 10548
    assert proof == row["preserved_artifacts"]["merged_head_proof"]
    missing = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{fresh_branch}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert missing.returncode != 0 and missing.stdout.strip() == ""


@pytest.mark.parametrize(
    "failure",
    ["unpushed", "dirty", "live_pid", "unknown_pid", "unmerged", "not_contained", "unknown_object", "retention"],
)
def test_switched_branch_cohort_uncertainty_retains_checkout(cohort, monkeypatch, failure):
    repo, tree, tasks, creator, rounds, source, fresh_branch, merged_head = _switched_branch_cohort(cohort, monkeypatch)
    rw = reap.reap_worktrees
    if failure == "unpushed":
        _git(tree, "commit", "--allow-empty", "-m", "unpushed continuation")
    elif failure == "dirty":
        (tree / "unique-work.txt").write_text("unique bytes\n")
    elif failure == "live_pid":
        rounds[-2]["pid"] = os.getpid()
        save(tasks, rounds[-2])
    elif failure == "unknown_pid":

        def unknown(*_args):
            raise PermissionError("process probe denied")

        monkeypatch.setattr(rw.os, "kill", unknown)
    elif failure == "unmerged":
        monkeypatch.setattr(
            rw, "_query_pr_states", lambda *_args: ([rw.PullRequestState(10548, "OPEN", merged_head)], None)
        )
    elif failure == "not_contained":
        side = repo / "side.txt"
        side.write_text("side\n")
        from tests.orchestration.test_merge_closeout import git

        git(repo, "add", "side.txt")
        git(repo, "commit", "-m", "side commit not on the PR")
        rounds[0]["final_branch_head_commit"] = _git(repo, "rev-parse", "HEAD")
        save(tasks, rounds[0])
    elif failure == "unknown_object":
        rounds[0]["final_branch_head_commit"] = "f" * 40
        save(tasks, rounds[0])
    else:
        creator["keep_worktree"] = True
        save(tasks, creator)
    before = {path: path.read_bytes() for path in tasks.glob("*.json")}
    result = merge_closeout.run_merge_closeout(repo, 10548, apply=True, live_cwds=set())
    row = result.reap_results[0]
    assert row["action"] == "skipped", result
    assert tree.exists() and source.read_bytes() == b"current output"
    local = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{fresh_branch}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert local.returncode == 0
    if failure != "unpushed":
        assert local.stdout.strip() == merged_head
    if failure != "retention":
        assert {path: path.read_bytes() for path in before} == before


def test_private_clone_switched_cohort_reaps_under_its_dispatch_root(tmp_path, monkeypatch):
    """A private clone's worktree is under that clone's dispatch root, not the public one."""
    from scripts.fleet import post_task_reap
    from scripts.orchestration.task_record_store import task_record_path
    from tests.orchestration.test_merge_closeout import git, init_repo, patch_gh
    from tests.orchestration.test_worktree_output_chokepoint import _git as git_ok

    repo = init_repo(tmp_path)
    with (repo / ".git/info/exclude").open("a") as exclude:
        exclude.write("ignored/\n.cache/\nbatch_state/\n")
    tree = repo / ".worktrees/dispatch/gemini/switched-cohort"
    tree.parent.mkdir(parents=True)
    git_ok(repo, "worktree", "add", "-b", "gemini/old-gate", str(tree), "main")
    tasks = repo / "batch_state/tasks"
    tasks.mkdir(parents=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_active_task_ids", lambda: set())
    creator_head = git_ok(tree, "rev-parse", "HEAD")
    git_ok(tree, "commit", "--allow-empty", "-m", "later round")
    git_ok(tree, "checkout", "-b", "cursor/private-gate")
    git_ok(tree, "commit", "--allow-empty", "-m", "switched")
    merged_head = git_ok(tree, "rev-parse", "HEAD")
    git_ok(tree, "push", "-u", "origin", "cursor/private-gate")
    git(repo, "merge", "--no-ff", "cursor/private-gate", "-m", "merge private PR")
    git(repo, "push", "origin", "main")
    creator = {
        "task_id": "gemini-creator",
        "agent": "gemini",
        "run_nonce": "creation-nonce",
        "status": "needs_finalize",
        "worktree_reused": False,
        "worktree_path": str(tree),
        "worktree_branch": "gemini/old-gate",
        "final_branch_head_commit": creator_head,
        "keep_worktree": False,
        "pid": 999_999_981,
    }
    creator["ignored_output_baseline"] = output.creation_inventory(
        tree, primary=repo, task_id=creator["task_id"], run_nonce=creator["run_nonce"]
    )
    successors = []
    for index, commit in enumerate((creator_head, merged_head, merged_head), start=1):
        successors.append(
            {
                "task_id": f"cursor-round-{index}",
                "agent": "cursor",
                "run_nonce": f"round-{index}",
                "status": "needs_finalize" if index < 3 else "done",
                "worktree_reused": True,
                "worktree_path": str(tree),
                "worktree_branch": "gemini/old-gate",
                "final_branch_head_commit": commit,
                "keep_worktree": False,
                "pid": 999_999_981 + index,
            }
        )
    for record in (creator, *successors):
        task_record_path(tasks, record["task_id"]).write_text(json.dumps(record))
    patch_gh(
        monkeypatch,
        pr_number=878,
        state="MERGED",
        head_ref_name="cursor/private-gate",
        head_sha=merged_head,
        branch_prs={"cursor/private-gate": [{"number": 878, "state": "MERGED", "headRefOid": merged_head}]},
    )
    report = post_task_reap.post_task_reap(
        "gemini-creator", tasks_dir=tasks, repo_root=repo, apply=False, include_acp_runtime=False
    )
    assert "outside .worktrees/dispatch/" not in report["main_worktree"]["reason"]
    result = merge_closeout.run_merge_closeout(repo, 878, apply=True, live_cwds=set())
    assert result.reap_results[0]["action"] == "removed", result
    assert not tree.exists()
    missing = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "refs/heads/cursor/private-gate"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert missing.returncode != 0 and missing.stdout.strip() == ""


def _init_named_repo(parent, name: str):
    """Bare-origin checkout named so a fleet sibling can sit beside a public primary."""
    from tests.orchestration.test_merge_closeout import git

    repo = parent / name
    remote = parent / f"{name}-origin.git"
    git(parent, "init", "--bare", str(remote))
    git(parent, "init", "--initial-branch=main", str(repo))
    git(repo, "config", "user.email", "tester@example.com")
    git(repo, "config", "user.name", "Test User")
    (repo / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git(repo, "add", ".gitignore", "README.md")
    git(repo, "commit", "-m", "base")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    return repo


def _split_plane_switched_cohort(tmp_path, monkeypatch, *, owning_repo_resolvable: bool):
    """Public control plane holds the task records; a sibling clone holds the checkout.

    Pull-request answers depend on which repository is queried. The public
    repository never has this branch's merged head when the owning remote
    resolves. When it does not, the public repository *does* report a merged
    pull request, so guessing that repository would delete the checkout.
    """
    from pathlib import Path

    from scripts.fleet import post_task_reap
    from scripts.orchestration.task_record_store import task_record_path
    from tests.orchestration.test_merge_closeout import git
    from tests.orchestration.test_worktree_output_chokepoint import _git as git_ok

    public = _init_named_repo(tmp_path, "learn-ukrainian")
    sibling = _init_named_repo(tmp_path, "learn-ukrainian-infra-private")
    monkeypatch.setattr(claims, "public_primary_root", lambda: public)
    with (sibling / ".git/info/exclude").open("a", encoding="utf-8") as exclude:
        exclude.write("ignored/\n.cache/\nbatch_state/\n")
    tree = sibling / ".worktrees/dispatch/gemini/switched-cohort"
    tree.parent.mkdir(parents=True)
    git_ok(sibling, "worktree", "add", "-b", "gemini/old-gate", str(tree), "main")
    tasks = public / "batch_state/tasks"
    tasks.mkdir(parents=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_active_task_ids", lambda: set())
    creator_head = git_ok(tree, "rev-parse", "HEAD")
    git_ok(tree, "commit", "--allow-empty", "-m", "later round")
    git_ok(tree, "checkout", "-b", "cursor/private-gate")
    git_ok(tree, "commit", "--allow-empty", "-m", "switched")
    merged_head = git_ok(tree, "rev-parse", "HEAD")
    git_ok(tree, "push", "-u", "origin", "cursor/private-gate")
    git(sibling, "merge", "--no-ff", "cursor/private-gate", "-m", "merge private PR")
    git(sibling, "push", "origin", "main")
    creator = {
        "task_id": "gemini-creator",
        "agent": "gemini",
        "run_nonce": "creation-nonce",
        "status": "needs_finalize",
        "worktree_reused": False,
        "worktree_path": str(tree),
        "worktree_branch": "gemini/old-gate",
        "final_branch_head_commit": creator_head,
        "keep_worktree": False,
        "pid": 999_999_981,
    }
    creator["ignored_output_baseline"] = output.creation_inventory(
        tree, primary=sibling, task_id=creator["task_id"], run_nonce=creator["run_nonce"]
    )
    successors = []
    for index, commit in enumerate((creator_head, merged_head, merged_head), start=1):
        successors.append(
            {
                "task_id": f"cursor-round-{index}",
                "agent": "cursor",
                "run_nonce": f"round-{index}",
                "status": "needs_finalize" if index < 3 else "done",
                "worktree_reused": True,
                "worktree_path": str(tree),
                "worktree_branch": "gemini/old-gate",
                "final_branch_head_commit": commit,
                "keep_worktree": False,
                "pid": 999_999_981 + index,
            }
        )
    for record in (creator, *successors):
        task_record_path(tasks, record["task_id"]).write_text(json.dumps(record), encoding="utf-8")

    private_slug = "acme/private-clone"
    public_slug = "learn-ukrainian/learn-ukrainian.github.io"
    calls: list[list[str]] = []

    def owner_repo(root):
        resolved = Path(root).resolve()
        if resolved == sibling.resolve():
            return ("acme", "private-clone") if owning_repo_resolvable else None
        if resolved == public.resolve():
            return ("learn-ukrainian", "learn-ukrainian.github.io")
        return None

    def merged_item():
        return {
            "number": 878,
            "state": "closed",
            "merged_at": "2026-01-02T03:04:05Z",
            "head": {"ref": "cursor/private-gate", "sha": merged_head},
        }

    def fake_run(args, **_kwargs):
        calls.append(list(args))
        blob = " ".join(args)
        on_private_branch = "cursor/private-gate" in blob or "cursor%2Fprivate-gate" in blob
        if args[1:3] == ["pr", "list"]:
            # GraphQL has no repository flag. Qualification of an unresolvable
            # owning remote still reaches it; a proof must not treat that as
            # the owning repository.
            payload = (
                [{"number": 878, "state": "MERGED", "headRefOid": merged_head}]
                if args[args.index("--head") + 1] == "cursor/private-gate"
                else []
            )
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        if "--paginate" in args:
            owns_merged_head = private_slug in blob or (public_slug in blob and not owning_repo_resolvable)
            payload = [[merged_item()]] if owns_merged_head and on_private_branch else []
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        if args[1:3] == ["api", "-X"] and "/pulls/" in blob:
            if private_slug in blob or (public_slug in blob and not owning_repo_resolvable):
                return subprocess.CompletedProcess(args, 0, json.dumps(merged_item()), "")
            return subprocess.CompletedProcess(args, 1, "", "pull request not in this repository")
        return subprocess.CompletedProcess(args, 1, "", "unexpected gh invocation")

    monkeypatch.setattr(reap.reap_worktrees, "_github_owner_repo", owner_repo)
    monkeypatch.setattr(reap.reap_worktrees.github_client, "run", fake_run)
    assert reap.reap_worktrees.control_plane_root(sibling).resolve() == public.resolve()
    return public, sibling, tree, tasks, merged_head, calls


def test_public_task_records_reap_private_clone_at_its_merged_head(tmp_path, monkeypatch):
    """Task records stay on the public control plane; the merged PR is the clone's."""
    from scripts.fleet import post_task_reap

    _public, sibling, tree, tasks, _merged_head, calls = _split_plane_switched_cohort(
        tmp_path, monkeypatch, owning_repo_resolvable=True
    )
    report = post_task_reap.post_task_reap(
        "gemini-creator", tasks_dir=tasks, repo_root=sibling, apply=False, include_acp_runtime=False
    )
    assert "outside .worktrees/dispatch/" not in report["main_worktree"]["reason"]
    result = merge_closeout.run_merge_closeout(sibling, 878, apply=True, live_cwds=set())
    assert result.reap_results[0]["action"] == "removed", result
    assert not tree.exists()
    assert any("acme/private-clone" in " ".join(call) for call in calls)
    assert not any("learn-ukrainian.github.io" in " ".join(call) and "cursor" in " ".join(call) for call in calls)
    missing = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "refs/heads/cursor/private-gate"],
        cwd=sibling,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert missing.returncode != 0 and missing.stdout.strip() == ""


def test_unresolvable_owning_repository_skips_merged_continuation(tmp_path, monkeypatch):
    """No owning GitHub repository means the needs_finalize claim stays and the tree is kept.

    The public repository would report this head as merged. Querying it would
    delete the checkout, so an unresolvable owner must not fall through to it.
    """
    from pathlib import Path

    _public, sibling, tree, _tasks, _merged_head, _calls = _split_plane_switched_cohort(
        tmp_path, monkeypatch, owning_repo_resolvable=False
    )
    results = reap.reap_worktrees.reap_worktrees(
        repo_root=sibling,
        apply=True,
        merged_pr_only=True,
        prune_merged_branches=True,
        safe_only=True,
        live_cwds=set(),
    )
    row = next(item for item in results if Path(item.path).resolve() == tree.resolve())
    assert row.action == "skipped", row
    assert "worktree claimed by active task" in row.reason
    assert tree.exists()


def _real_switched_checkout(tmp_path, monkeypatch):
    """Switched cohort on a real linked worktree. The origin parser is not mocked."""
    from tests.orchestration.test_merge_closeout import git, init_repo

    repo = init_repo(tmp_path)
    tree = repo / ".worktrees/dispatch/cursor/switched-proof"
    tree.parent.mkdir(parents=True)
    git(repo, "worktree", "add", "-b", "cursor/old-gate", str(tree), "main")
    tasks = repo / "batch_state/tasks"
    tasks.mkdir(parents=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setattr(reap.reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(reap.reap_worktrees, "_active_task_ids", lambda: set())
    creator_head = git(tree, "rev-parse", "HEAD")
    git(tree, "commit", "--allow-empty", "-m", "later round")
    middle = git(tree, "rev-parse", "HEAD")
    git(tree, "checkout", "-b", "cursor/fresh-gate")
    git(tree, "commit", "--allow-empty", "-m", "switched")
    merged_head = git(tree, "rev-parse", "HEAD")
    git(tree, "push", "-u", "origin", "cursor/fresh-gate")
    git(repo, "merge", "--no-ff", "cursor/fresh-gate", "-m", "merge switched PR")
    git(repo, "push", "origin", "main")
    creator = {
        "task_id": "cursor-creator",
        "agent": "cursor",
        "run_nonce": "creation-nonce",
        "status": "needs_finalize",
        "worktree_reused": False,
        "worktree_path": str(tree),
        "worktree_branch": "cursor/old-gate",
        "final_branch_head_commit": creator_head,
        "keep_worktree": False,
        "pid": 999_999_981,
    }
    creator["ignored_output_baseline"] = output.creation_inventory(
        tree, primary=repo, task_id=creator["task_id"], run_nonce=creator["run_nonce"]
    )
    successors = [
        {
            "task_id": "cursor-round-1",
            "agent": "cursor",
            "run_nonce": "round-1",
            "status": "needs_finalize",
            "worktree_reused": True,
            "worktree_path": str(tree),
            "worktree_branch": "cursor/old-gate",
            "final_branch_head_commit": middle,
            "keep_worktree": False,
            "pid": 999_999_982,
        },
        {
            "task_id": "cursor-round-2",
            "agent": "cursor",
            "run_nonce": "round-2",
            "status": "done",
            "worktree_reused": True,
            "worktree_path": str(tree),
            "worktree_branch": "cursor/old-gate",
            "final_branch_head_commit": merged_head,
            "keep_worktree": False,
            "pid": 999_999_983,
        },
    ]
    for record in (creator, *successors):
        save(tasks, record)
    cohort = [(tasks / f"{record['task_id']}.json", record) for record in (creator, *successors)]
    return repo, tree, tasks, cohort, merged_head


def _merged_gh(monkeypatch, *, head: str, branch: str) -> list[list[str]]:
    """Answer every gh read as the merged head. Does not replace the origin parser."""
    calls: list[list[str]] = []
    page = {
        "number": 10548,
        "state": "closed",
        "merged_at": "2026-01-02T03:04:05Z",
        "head": {"ref": branch, "sha": head},
    }
    listed = [{"number": 10548, "state": "MERGED", "headRefOid": head}]

    def fake_run_gh(args, **_kwargs):
        calls.append(list(args))
        if "--paginate" in args:
            return subprocess.CompletedProcess(args, 0, json.dumps([[page]]), "")
        if args[1:3] == ["api", "-X"]:
            return subprocess.CompletedProcess(args, 0, json.dumps(page), "")
        if args[1:3] == ["pr", "list"]:
            return subprocess.CompletedProcess(args, 0, json.dumps(listed), "")
        if args[1:3] == ["pr", "view"]:
            payload = {"number": 10548, "state": "MERGED", "headRefName": branch, "headRefOid": head}
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        if args[1:3] == ["search", "prs"]:
            return subprocess.CompletedProcess(args, 0, "[]", "")
        return subprocess.CompletedProcess(args, 1, "", "unexpected gh invocation")

    monkeypatch.setattr(reap.reap_worktrees, "_run_gh", fake_run_gh)
    return calls


@pytest.mark.parametrize(
    "origin",
    [
        "https://notgithub.com/unrelated/repo.git",
        "https://notgithub.com/unrelated/repo",
        "git@notgithub.com:unrelated/repo.git",
        "git@notgithub.com:unrelated/repo",
        "ssh://git@notgithub.com/unrelated/repo.git",
        "ssh://git@notgithub.com/unrelated/repo",
        "https://prefix.github.com/unrelated/repo.git",
        "https://github.com/bad owner/repo.git",
        "https://github.com/-bad/repo.git",
        "https://github.com/unrelated/repo?.git",
    ],
)
def test_real_origin_parser_refuses_non_github_host_and_illegal_slug(tmp_path, origin):
    """The configured origin is read from git. A lookalike host or a bad slug is not a repository."""
    from tests.orchestration.test_merge_closeout import git, init_repo

    repo = init_repo(tmp_path)
    git(repo, "remote", "set-url", "origin", origin)
    assert reap.reap_worktrees._github_owner_repo(repo) is None


def test_lookalike_github_host_does_not_prove_or_reap_switched_checkout(tmp_path, monkeypatch):
    """A host that only contains the GitHub name must not query that embedded owner/repo or delete."""
    from pathlib import Path

    from tests.orchestration.test_merge_closeout import git

    repo, tree, _tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://notgithub.com/unrelated/repo.git")
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    proven = reap.reap_worktrees._switched_branch_merge_proven(repo, tree, cohort)
    assert proven is False
    assert not any("unrelated/repo" in " ".join(call) for call in calls)
    results = reap.reap_worktrees.reap_worktrees(
        repo_root=repo,
        apply=True,
        merged_pr_only=True,
        prune_merged_branches=True,
        safe_only=True,
        live_cwds=set(),
    )
    row = next(item for item in results if Path(item.path).resolve() == tree.resolve())
    assert row.action == "skipped", row
    assert "worktree claimed by active task" in row.reason
    assert tree.exists()
    assert not any("unrelated/repo" in " ".join(call) for call in calls)


def _assert_unproven_path_cannot_authorize_removal(repo, tree, tasks, cohort, merged_head, doubtful):
    """An unproven path must not resolve a repository or authorize removal."""
    rw = reap.reap_worktrees
    assert rw._checkout_pr_repository(doubtful) is None
    assert rw._switched_branch_merge_proven(repo, doubtful, cohort) is False
    info = rw.WorktreeInfo(doubtful, "cursor/fresh-gate", merged_head, detached=False)
    pr = rw.PullRequestState(10548, "MERGED", merged_head)
    try:
        authorized = rw._record_merged_reuse_proof(repo, info, pr, tasks_dir=tasks)
    except ValueError:
        authorized = None
    assert authorized is None
    assert tree.exists() and doubtful.exists()


def test_symlinked_checkout_cannot_authorize_switched_removal(tmp_path, monkeypatch):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widget.git")
    _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    link = tmp_path / "linked-checkout"
    link.symlink_to(tree, target_is_directory=True)
    _assert_unproven_path_cannot_authorize_removal(repo, tree, tasks, cohort, merged_head, link)


def test_traversal_checkout_cannot_authorize_switched_removal(tmp_path, monkeypatch):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widget.git")
    _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    traversal = tree.parent / tree.name / ".." / tree.name
    _assert_unproven_path_cannot_authorize_removal(repo, tree, tasks, cohort, merged_head, traversal)


def test_forged_gitdir_cannot_authorize_switched_removal(tmp_path, monkeypatch):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widget.git")
    _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    forged = tmp_path / "forged-checkout"
    forged.mkdir()
    (forged / ".git").write_text(f"gitdir: {repo}/.git/worktrees/does-not-exist\n", encoding="utf-8")
    _assert_unproven_path_cannot_authorize_removal(repo, tree, tasks, cohort, merged_head, forged)


def _hide_worktree_gitdir_behind_symlink(repo, tree, other_origin: str, *, absolute=False):
    """Rewrite the checkout gitdir to ``.git/jump/../worktrees/<id>``.

    ``jump`` is a symlink to another repository's worktree metadata. Lexical
    collapse names ``repo``. Git follows ``jump`` and reports ``other_origin``.
    """
    from pathlib import Path

    from tests.orchestration.test_merge_closeout import git

    original = (tree / ".git").read_text(encoding="utf-8").strip()
    prefix = "gitdir:"
    assert original.startswith(prefix)
    admin = Path(original[len(prefix) :].strip())
    other = repo.parent / "other-primary"
    git(repo.parent, "init", "--initial-branch=main", str(other))
    git(other, "remote", "add", "origin", other_origin)
    alternates = other / ".git" / "objects" / "info"
    alternates.mkdir(parents=True, exist_ok=True)
    (alternates / "alternates").write_text(f"{repo / '.git' / 'objects'}\n", encoding="utf-8")
    shutil.copytree(repo / ".git" / "refs", other / ".git" / "refs", dirs_exist_ok=True)
    packed = repo / ".git" / "packed-refs"
    if packed.is_file():
        shutil.copy(packed, other / ".git" / "packed-refs")
    other_admin = other / ".git" / "worktrees" / admin.name
    shutil.copytree(admin, other_admin)
    (other_admin / "commondir").write_text("../..\n", encoding="utf-8")
    (other_admin / "gitdir").write_text(f"{tree / '.git'}\n", encoding="utf-8")
    (repo / ".git" / "jump").symlink_to(other / ".git" / "worktrees", target_is_directory=True)
    relative = str(repo / ".git") if absolute else os.path.relpath(repo / ".git", tree)
    (tree / ".git").write_text(
        f"gitdir: {relative}/jump/../worktrees/{admin.name}\n",
        encoding="utf-8",
    )
    return other


@pytest.mark.parametrize("absolute", [False, True])
def test_dotdot_hidden_symlink_gitdir_cannot_authorize_switched_removal(tmp_path, monkeypatch, absolute):
    """A ``..`` that hides a symlink must not query primary A or write a reap receipt.

    Git follows ``jump`` into the other primary. The proof has to refuse before
    it asks for A's pull request.
    """
    from tests.orchestration.test_merge_closeout import git

    repo, tree, tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widget.git")
    other = _hide_worktree_gitdir_behind_symlink(
        repo, tree, "https://github.com/other/elsewhere.git", absolute=absolute
    )
    assert git(tree, "remote", "get-url", "origin") == "https://github.com/other/elsewhere.git"
    assert git(tree, "rev-parse", "--path-format=absolute", "--git-common-dir") == str(other / ".git")
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    rw = reap.reap_worktrees
    assert rw._proven_linked_worktree_primary(tree) is None
    assert rw._checkout_pr_repository(tree) is None
    assert rw._switched_branch_merge_proven(repo, tree, cohort) is False
    assert not any("acme/widget" in " ".join(call) or "other/elsewhere" in " ".join(call) for call in calls)
    _assert_unproven_path_cannot_authorize_removal(repo, tree, tasks, cohort, merged_head, tree)
    creator = json.loads((tasks / "cursor-creator.json").read_text(encoding="utf-8"))
    assert "worktree_reap_proof" not in creator


@pytest.mark.parametrize(
    "origin",
    [
        "https://github.com:abc/acme/widget.git",
        "https://github.com:99999/acme/widget.git",
        "https://github.com:-1/acme/widget.git",
        "https://github.com:65536/acme/widget",
        "https://github.com:80abc/acme/widget.git",
        "ssh://git@github.com:notaport/acme/widget.git",
        "https://user:token@github.com:abc/acme/widget.git",
    ],
)
def test_malformed_origin_port_is_unknown(origin):
    """A port GitHub's URL parser cannot read is an unknown origin, not an exception."""
    assert reap.reap_worktrees._parse_github_origin(origin) is None


def test_malformed_origin_port_fails_closed_without_aborting_the_sweep(tmp_path, monkeypatch):
    """One checkout with a malformed origin port stays unproven; the sweep still reports the rest."""
    from pathlib import Path

    from tests.orchestration.test_merge_closeout import git, init_repo

    repo = init_repo(tmp_path)
    trees = []
    for name in ("one", "two"):
        tree = repo / ".worktrees" / "dispatch" / "cursor" / name
        tree.parent.mkdir(parents=True, exist_ok=True)
        git(repo, "worktree", "add", "-b", f"cursor/{name}", str(tree), "main")
        trees.append(tree)
    git(repo, "remote", "set-url", "origin", "https://github.com:abc/acme/widget.git")
    monkeypatch.setattr(reap.reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(reap.reap_worktrees, "_active_task_ids", lambda: set())
    monkeypatch.setattr(
        reap.reap_worktrees,
        "_run_gh",
        lambda args, **_kwargs: subprocess.CompletedProcess(args, 1, "", "gh unavailable"),
    )
    results = reap.reap_worktrees.reap_worktrees(
        repo_root=repo,
        apply=True,
        merged_pr_only=True,
        safe_only=True,
        live_cwds=set(),
    )
    by_path = {Path(row.path).resolve(): row for row in results}
    for tree in trees:
        row = by_path[tree.resolve()]
        assert row.action == "skipped", row
        assert "origin owner/repo could not be determined" in row.reason
        assert tree.exists()


def test_copied_common_directory_with_trailing_space_cannot_authorize_removal(tmp_path, monkeypatch):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widget.git")
    copied = repo / ".git "
    shutil.copytree(repo / ".git", copied)
    admin = repo / ".git/worktrees/switched-proof"
    (admin / "commondir").write_text(f"{copied}\n", encoding="utf-8")
    raw = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=tree,
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout
    assert raw == os.fsencode(copied) + b"\n"
    assert git(tree, "config", "--get", "remote.origin.url") == "https://github.com/acme/widget.git"
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    _assert_unproven_path_cannot_authorize_removal(repo, tree, tasks, cohort, merged_head, tree)
    assert calls == []
    assert "worktree_reap_proof" not in json.loads((tasks / "cursor-creator.json").read_text())


def test_unregistered_copied_worktree_cannot_authorize_removal(tmp_path, monkeypatch):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widget.git")
    copied = tree.parent / "unregistered"
    shutil.copytree(tree, copied)
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    _assert_unproven_path_cannot_authorize_removal(repo, tree, tasks, cohort, merged_head, copied)
    assert calls == []


@pytest.mark.parametrize("command", ["rev-parse", "config", "worktree"])
@pytest.mark.parametrize("fault", ["nonzero", "unreadable", "text", "empty", "extra", "unterminated"])
def test_git_identity_failure_refuses_before_pr_or_removal(tmp_path, monkeypatch, command, fault):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widget.git")
    rw = reap.reap_worktrees
    original = rw.safe_git
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")

    def probe(args, **kwargs):
        if args[0] != command:
            return original(args, **kwargs)
        if fault == "unreadable":
            raise OSError("identity output unavailable")
        proc = original(args, **kwargs)
        if fault == "nonzero":
            return subprocess.CompletedProcess(args, 128, proc.stdout, b"refused")
        stdout = {
            "text": "unexpected decoded output",
            "empty": b"",
            "extra": proc.stdout + b"unexpected\n\n",
            "unterminated": proc.stdout[:-1],
        }[fault]
        return subprocess.CompletedProcess(args, 0, stdout, b"")

    monkeypatch.setattr(rw, "safe_git", probe)
    _assert_unproven_path_cannot_authorize_removal(repo, tree, tasks, cohort, merged_head, tree)
    assert calls == []


@pytest.mark.parametrize("origin", [" https://github.com/acme/widget.git", "https://github.com/acme/widget.git "])
def test_origin_whitespace_is_not_normalized(tmp_path, monkeypatch, origin):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "config", "remote.origin.url", origin)
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    _assert_unproven_path_cannot_authorize_removal(repo, tree, tasks, cohort, merged_head, tree)
    assert calls == []


def test_worktree_origin_override_cannot_authorize_primary_pr(tmp_path, monkeypatch):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "config", "remote.origin.url", "https://github.com/acme/widget.git")
    git(repo, "config", "extensions.worktreeConfig", "true")
    git(tree, "config", "--worktree", "remote.origin.url", "https://github.com/other/elsewhere.git")
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    _assert_unproven_path_cannot_authorize_removal(repo, tree, tasks, cohort, merged_head, tree)
    assert calls == []


def test_git_only_resolver_never_reads_pointer_files(tmp_path, monkeypatch):
    from pathlib import Path

    from tests.orchestration.test_merge_closeout import git

    repo, tree, _tasks, _cohort, _merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "config", "remote.origin.url", "https://github.com/acme/widget.git")

    def refuse(*_args, **_kwargs):
        pytest.fail("the identity resolver read a pointer file")

    monkeypatch.setattr(Path, "read_text", refuse)
    monkeypatch.setattr(Path, "read_bytes", refuse)
    assert reap.reap_worktrees._checkout_pr_repository(tree) == repo
