"""Merged-reuse proofs retain the real superseded creator's identity (#11056)."""

from __future__ import annotations

import contextlib
import json

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.orchestration import reap_worktrees as rw
from scripts.orchestration import worktree_claims as claims
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
    repo, tree, _, path, _, _, _, _, _ = merged_cohort
    source = tree / "ignored/output.txt"
    source.parent.mkdir()
    source.write_bytes(b"output from the reused checkout")

    applied = next(r for r in rw.reap_worktrees(repo_root=repo, apply=True, live_cwds=set()) if r.path == str(tree))
    assert applied.action == "removed", applied.reason
    assert not tree.exists()
    receipt = applied.preserved_artifacts
    assert (repo / receipt["location"] / "ignored/output.txt").read_bytes() == b"output from the reused checkout"
    assert output.verify_retrieval(repo, receipt) == receipt["retrieval_proof_sha256"]
    proof = json.loads(path.read_text())["worktree_reap_proof"]
    assert proof["owner"] == "boundary" and proof["run_nonce"] == "creation-nonce"
    assert proof == receipt["merged_head_proof"]


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
