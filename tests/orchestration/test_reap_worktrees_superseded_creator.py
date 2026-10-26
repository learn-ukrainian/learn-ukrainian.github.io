"""Merged-reuse proofs retain the real superseded creator's identity (#11056)."""

from __future__ import annotations

import contextlib
import hashlib
import json
import subprocess

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.orchestration import reap_worktrees as rw
from scripts.orchestration import worktree_claims as claims
from tests.orchestration import test_merge_closeout as closeout
from tests.orchestration.test_worktree_claims_cli import _git
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree


@pytest.fixture
def merged_cohort(boundary_tree, monkeypatch):
    repo, tree, tasks, creator = boundary_tree
    head = _git(tree, "rev-parse", "HEAD")
    creator.update(worktree_branch="codex/boundary", pid=999_999_999, final_branch_head_commit=head)
    creator_path = tasks / "boundary.20261019T102455011045Z.archived.json"
    (tasks / "boundary.json").rename(creator_path)
    creator_path.write_text(json.dumps(creator))
    current = dict(creator, run_nonce="current-run", worktree_reused=True)
    current_path = tasks / "boundary.json"
    current_path.write_text(json.dumps(current))
    monkeypatch.setattr(rw, "_open_file_activity_reason", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(rw, "_foreign_scratch_roots", lambda: ())
    info = rw.WorktreeInfo(tree, "codex/boundary", head)
    pr = rw.PullRequestState(9645, "MERGED", head)
    return repo, tree, tasks, creator_path, creator, current_path, current, info, pr


def _proof(fixture):
    repo, tree, tasks, _, _, _, _, info, pr = fixture
    with claims.worktree_lock(tree, lock_dir=claims.repository_lock_dir(repo)):
        return rw._record_merged_reuse_proof(repo, info, pr, tasks_dir=tasks)


@pytest.mark.parametrize("location", ["canonical", "archive", "superseded", "superseded_pid"])
def test_merged_reuse_removes_tree_and_proves_creator(merged_cohort, location):
    repo, tree, tasks, path, creator, current_path, current, _, _ = merged_cohort
    if location == "canonical":
        current_path.unlink()
        current["task_id"] = "successor"
        current_path = tasks / "successor.json"
        current_path.write_text(json.dumps(current))
        target = tasks / "boundary.json"
    elif location == "archive":
        target = tasks / "archive/boundary.json"
        target.parent.mkdir()
    elif location == "superseded_pid":
        target = tasks / "boundary.20261019T102455Z.123.archived.json"
    else:
        target = path
    if target != path:
        path.rename(target)
    before = {p: p.read_bytes() for p in (target, current_path)}

    dry = next(r for r in rw.reap_worktrees(repo_root=repo, apply=False, live_cwds=set()) if r.path == str(tree))
    assert dry.action == "would_remove", dry
    assert tree.exists()
    assert {p: p.read_bytes() for p in before} == before

    applied = next(r for r in rw.reap_worktrees(repo_root=repo, apply=True, live_cwds=set()) if r.path == str(tree))
    assert applied.action == "removed", applied.reason
    assert not tree.exists()
    saved = json.loads(target.read_text())
    proof = saved.pop("worktree_reap_proof")
    assert saved == creator
    assert proof["owner"] == "boundary"
    assert proof["run_nonce"] == "creation-nonce"
    assert proof["run_nonce"] != current["run_nonce"]
    assert proof == applied.preserved_artifacts["merged_head_proof"]
    assert current_path.read_bytes() == before[current_path]


def test_superseded_creator_proof_survives_output_preservation(merged_cohort):
    repo, tree, _, path, _, current_path, current, info, _ = merged_cohort
    current["status"] = "needs_finalize"
    current_path.write_text(json.dumps(current))
    source = tree / "ignored/output.txt"
    source.parent.mkdir()
    source.write_bytes(b"output from the reused checkout")
    (tree / "README.md").write_bytes(b"current tracked bytes\n")
    (tree / "result.bin").write_bytes(b"\x00current binary bytes\xff")

    applied = next(
        r
        for r in rw.reap_worktrees(repo_root=repo, apply=True, preserve_then_reap=True, live_cwds=set())
        if r.path == str(tree)
    )
    assert applied.action == "preserved_then_removed", applied.reason
    assert not tree.exists()
    receipt = applied.preserved_artifacts
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
    entry = next(entry for entry in receipt["paths"] if entry["path"] == "ignored/output.txt")
    assert entry["sha256"] == hashlib.sha256(b"output from the reused checkout").hexdigest()
    assert not (repo / "batch_state/preserved").exists()
    assert output.verify_retrieval(repo, receipt) == receipt["retrieval_proof_sha256"]
    proof = json.loads(path.read_text())["worktree_reap_proof"]
    assert proof["owner"] == "boundary" and proof["run_nonce"] == "creation-nonce"
    assert proof == receipt["merged_head_proof"]
    preservation = proof["preservation"]
    assert proof["head_sha"] == preservation["parent_sha"] == info.head
    assert preservation["recovery_ref"] == applied.recovery_ref
    assert _git(repo, "rev-parse", applied.recovery_ref) == preservation["head_sha"]
    assert _git(repo, "rev-parse", f"{applied.recovery_ref}^{{tree}}") == preservation["tree_sha"]
    for name, expected in (("README.md", b"current tracked bytes\n"), ("result.bin", b"\x00current binary bytes\xff")):
        retrieved = subprocess.run(
            ["git", "show", f"{applied.recovery_ref}:{name}"], cwd=repo, capture_output=True, check=True, timeout=15
        ).stdout
        assert retrieved == expected


@pytest.mark.parametrize(
    "failure",
    ["task_id", "stamp", "directory", "canonical_missing", "canonical_task_id", "invalid_identity"],
)
def test_invalid_superseded_creator_path_refused(merged_cohort, failure):
    _, tree, tasks, path, creator, current_path, current, _, _ = merged_cohort
    if failure == "task_id":
        creator["task_id"] = "wrong-task"
        path.write_text(json.dumps(creator))
    elif failure == "stamp":
        path.rename(tasks / "boundary.yesterday.archived.json")
    elif failure == "directory":
        archive = tasks / "archive"
        archive.mkdir()
        path.rename(archive / path.name)
    elif failure == "canonical_missing":
        current_path.rename(tasks / "renamed.json")
    elif failure == "canonical_task_id":
        current["task_id"] = "other"
        current_path.write_text(json.dumps(current))
    else:
        identity = "invalid identity"
        creator["task_id"] = current["task_id"] = identity
        path.rename(tasks / f"{identity}.20261019T102455Z.archived.json")
        (tasks / f"{identity}.20261019T102455Z.archived.json").write_text(json.dumps(creator))
        current_path.rename(tasks / f"{identity}.json")
        (tasks / f"{identity}.json").write_text(json.dumps(current))
    before = {p: p.read_bytes() for p in tasks.rglob("*.json")}
    with pytest.raises(ValueError, match=r"^continuation creator has no canonical task record$"):
        _proof(merged_cohort)
    assert tree.exists()
    assert {p: p.read_bytes() for p in before} == before


def test_two_creators_refused(merged_cohort):
    _, tree, tasks, _, creator, _, _, _, _ = merged_cohort
    (tasks / "boundary.20261019T102455Z.123.archived.json").write_text(json.dumps(dict(creator, run_nonce="other-run")))
    with pytest.raises(ValueError, match=r"^continuation creator has no canonical task record$"):
        _proof(merged_cohort)
    assert tree.exists()
    assert all("worktree_reap_proof" not in json.loads(p.read_text()) for p in tasks.rglob("*.json"))


def test_current_record_must_be_reused(merged_cohort):
    _, tree, tasks, _, _, current_path, current, _, _ = merged_cohort
    current["worktree_reused"] = False
    current.pop("ignored_output_baseline")
    current_path.write_text(json.dumps(current))
    with pytest.raises(ValueError, match=r"^ambiguous worktree task attribution with retention intent$"):
        _proof(merged_cohort)
    assert tree.exists()
    assert all("worktree_reap_proof" not in json.loads(p.read_text()) for p in tasks.rglob("*.json"))


@pytest.mark.parametrize("member", ["creator", "current"])
def test_run_identity_changed_at_lock_refused(merged_cohort, monkeypatch, member):
    _, tree, tasks, path, creator, current_path, current, _, _ = merged_cohort
    original = output.artifacts.task_state_lock
    changed = []

    @contextlib.contextmanager
    def change_identity(locked_path):
        if not changed:
            changed.append(True)
            record, target = (creator, path) if member == "creator" else (current, current_path)
            target.write_text(json.dumps(dict(record, run_nonce="replacement-run")))
        with original(locked_path):
            yield

    monkeypatch.setattr(output.artifacts, "task_state_lock", change_identity)
    with pytest.raises(ValueError, match=r"^continuation records changed before merged-head proof$"):
        _proof(merged_cohort)
    assert tree.exists()
    assert all("worktree_reap_proof" not in json.loads(p.read_text()) for p in tasks.rglob("*.json"))


@pytest.fixture
def queue_merged_cohort(merged_cohort, monkeypatch):
    """A squash landing retains the PR ref after deleting its branch."""
    repo, tree, tasks, path, creator, current_path, current, _, _ = merged_cohort
    for name in ("first.txt", "last.txt"):
        (tree / name).write_text(name)
        closeout.git(tree, "add", name)
        closeout.git(tree, "commit", "-m", f"add {name}")
    head = closeout.git(tree, "rev-parse", "HEAD")
    closeout.publish_pr_head(repo, 9645, "codex/boundary", head)
    closeout.git(repo, "merge", "--squash", "codex/boundary")
    closeout.git(repo, "commit", "-m", "merge queue squash landing")
    closeout.git(repo, "push", "origin", "main")
    closeout.git(repo, "push", "origin", "--delete", "codex/boundary")
    closeout.git(repo, "fetch", "--prune", "origin")
    assert closeout.git(repo, "ls-remote", "--heads", "origin", "codex/boundary") == ""
    assert closeout.git(tree, "rev-parse", "HEAD") == head
    assert closeout.git(repo, "rev-parse", "origin/main") != head
    assert not rw._sha_is_ancestor(tree, head, "origin/main")
    for record, target in ((creator, path), (current, current_path)):
        record["final_branch_head_commit"] = head
        target.write_text(json.dumps(record))
    calls = closeout.patch_gh(
        monkeypatch,
        pr_number=9645,
        state="MERGED",
        head_ref_name="codex/boundary",
        head_sha=head,
        branch_prs={},
        sha_prs={head: [{"number": 9645, "state": "MERGED"}]},
    )
    return repo, tree, tasks, path, creator, current_path, current, head, calls


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("status", ["done", "needs_finalize"])
def test_queue_merged_deleted_branch_uses_recorded_pr_head(queue_merged_cohort, apply, status):
    repo, tree, tasks, path, creator, current_path, current, head, calls = queue_merged_cohort
    for record, target in ((creator, path), (current, current_path)):
        record["status"] = status
        target.write_text(json.dumps(record))
    before = {p: p.read_bytes() for p in tasks.glob("*.json")}

    result = next(r for r in rw.reap_worktrees(repo_root=repo, apply=apply, live_cwds=set()) if r.path == str(tree))

    assert result.action == ("removed" if apply else "would_remove"), result.reason
    assert tree.exists() is not apply
    assert any("repos/learn-ukrainian/learn-ukrainian.github.io/pulls/9645" in call for call in calls)
    if apply:
        proof = result.preserved_artifacts["merged_head_proof"]
        assert proof["head_sha"] == proof["pr_head_sha"] == head
        assert proof["pr_number"] == 9645
        assert proof["pr_state"] == "MERGED"
        assert proof["head_relation"] == "exact"
        assert proof["pr_head_source"] == "merged_pr_record"
        assert proof == json.loads(path.read_text())["worktree_reap_proof"]
        assert current_path.read_bytes() == before[current_path]
        assert {k: v for k, v in json.loads(path.read_text()).items() if k != "worktree_reap_proof"} == creator
    else:
        assert {p: p.read_bytes() for p in before} == before


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize(
    "unsafe",
    [
        "differing_head",
        "dirty",
        "unpushed",
        "lookup_error",
        "missing_head",
        "open",
        "closed",
        "wrong_pr",
        "uncontained_creator",
    ],
)
def test_queue_merged_deleted_branch_refuses_unproven_work(queue_merged_cohort, monkeypatch, apply, unsafe):
    repo, tree, tasks, path, creator, current_path, current, head, _ = queue_merged_cohort
    if unsafe == "dirty":
        (tree / "README.md").write_text("unique uncommitted work\n")
    elif unsafe == "uncontained_creator":
        foreign = closeout.git(tree, "commit-tree", f"{head}^{{tree}}", "-m", "uncontained creator history")
        creator["final_branch_head_commit"] = foreign
        for record, target in ((creator, path), (current, current_path)):
            record["status"] = "needs_finalize"
            target.write_text(json.dumps(record))
    elif unsafe == "unpushed":
        (tree / "unique.txt").write_text("unique unpushed work\n")
        closeout.git(tree, "add", "unique.txt")
        closeout.git(tree, "commit", "-m", "unpublished continuation")
        local = closeout.git(tree, "rev-parse", "HEAD")
        # Search membership is deliberately insufficient to establish a PR tip.
        closeout.patch_gh(
            monkeypatch,
            pr_number=9645,
            state="MERGED",
            head_ref_name="codex/boundary",
            head_sha=head,
            sha_prs={local: [{"number": 9645, "state": "MERGED"}]},
        )
    elif unsafe == "differing_head":
        # A search hit can name an earlier commit rather than the PR's last head.
        closeout.git(tree, "reset", "--hard", f"{head}^")
        local = closeout.git(tree, "rev-parse", "HEAD")
        closeout.patch_gh(
            monkeypatch,
            pr_number=9645,
            state="MERGED",
            head_ref_name="codex/boundary",
            head_sha=head,
            sha_prs={local: [{"number": 9645, "state": "MERGED"}]},
        )
    else:
        original = rw._run_gh

        def numbered_pr(args, **kwargs):
            if (args[1:3] == ["api", "-X"] and args[-1].endswith("/pulls/9645")) or args[1:3] == ["pr", "view"]:
                if unsafe == "lookup_error":
                    return subprocess.CompletedProcess(args, 1, "", "lookup unavailable")
                payload = {
                    "number": 9646 if unsafe == "wrong_pr" else 9645,
                    "state": "open" if unsafe == "open" else "closed",
                    "merged_at": None if unsafe in {"open", "closed"} else "2026-01-02T03:04:05Z",
                    "head": {"ref": "codex/boundary", "sha": None if unsafe == "missing_head" else head},
                }
                return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
            return original(args, **kwargs)

        monkeypatch.setattr(rw, "_run_gh", numbered_pr)
    before = {p: p.read_bytes() for p in tasks.glob("*.json")}

    result = next(r for r in rw.reap_worktrees(repo_root=repo, apply=apply, live_cwds=set()) if r.path == str(tree))

    assert result.action == "skipped", result
    assert tree.exists()
    assert {p: p.read_bytes() for p in before} == before
    assert all("worktree_reap_proof" not in json.loads(p.read_text()) for p in before)
    if unsafe == "dirty":
        assert (tree / "README.md").read_text() == "unique uncommitted work\n"
    if unsafe == "unpushed":
        assert (tree / "unique.txt").read_text() == "unique unpushed work\n"
