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
