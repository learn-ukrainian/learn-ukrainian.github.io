"""Held worktree-lock identity includes the lock directory (#8663).

``worktree_lock`` refuses a reentry on this thread instead of waiting on
itself. Holding a path's lock in directory A must not count as holding it in
directory B, while the same directory spelled another way is the same lock.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.guardrails import worktree_containment
from scripts.orchestration import worktree_claims


@pytest.fixture
def registered_trees(tmp_path, monkeypatch):
    trees = [tmp_path]
    monkeypatch.setattr(worktree_containment, "resolve_main_root", lambda _path: tmp_path)
    monkeypatch.setattr(worktree_containment, "registered_worktrees", lambda _path: trees)
    return trees


def test_holding_a_lock_in_one_dir_is_not_holding_it_in_another(tmp_path: Path) -> None:
    worktree = tmp_path / "wt"

    with worktree_claims.worktree_lock(worktree, lock_dir=tmp_path / "locks-a"):
        # A different lock file is no reentry: nesting it cannot self-deadlock.
        with worktree_claims.worktree_lock(worktree, lock_dir=tmp_path / "locks-b", timeout_s=0.5):
            pass


def test_same_dir_through_another_spelling_is_a_reentry(tmp_path: Path) -> None:
    worktree = tmp_path / "wt"
    (tmp_path / "locks").mkdir()
    (tmp_path / "alias").symlink_to(tmp_path / "locks")

    with worktree_claims.worktree_lock(worktree, lock_dir=tmp_path / "locks"):
        with pytest.raises(worktree_claims.WorktreeLockReentry):
            with worktree_claims.worktree_lock(worktree, lock_dir=tmp_path / "alias", timeout_s=0.5):
                pass


@pytest.mark.parametrize("spelling", ["absolute", "relative", "subdir", "symlink", "parent"])
@pytest.mark.parametrize(
    "status", ["spawning", "running", "needs_finalize", "unknown", *sorted(worktree_claims.RELEASED_TASK_STATUSES)]
)
def test_review_input_claim_lifetime_and_real_paths(tmp_path, registered_trees, spelling, status):
    tree = tmp_path / "input-tree"
    tree.mkdir()
    registered_trees.append(tree)
    alias = tmp_path / "different-alias"
    alias.symlink_to(tree, target_is_directory=True)
    inputs = {
        "absolute": str(tree),
        "relative": tree.name,
        "subdir": str(tree / "inputs"),
        "symlink": str(alias),
        "parent": str(tmp_path),
    }[spelling]
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    state = tasks / "review.json"
    state.write_text(
        json.dumps(
            {
                "task_id": "review",
                "run_nonce": "run",
                "status": status,
                "worktree_path": str(tmp_path / "reviewer"),
                "review_contract": {"input_root": inputs},
            }
        )
    )
    # Neither owner exemption nor needs_finalize's settled proof can release inputs.
    refusal = worktree_claims.active_worktree_claim_refusal(
        tree,
        tasks_dir=tasks,
        repo_root=tmp_path,
        owner_task_id="review",
        settled_claim=lambda _record: True,
    )
    assert refusal == (
        None
        if spelling == "parent" or status in worktree_claims.RELEASED_TASK_STATUSES
        else "review input root claimed by active task review"
    )


@pytest.mark.parametrize("review_inputs_only", [False, True])
def test_primary_review_input_does_not_claim_unrelated_linked_tree(tmp_path, registered_trees, review_inputs_only):
    tree = tmp_path / ".worktrees/dispatch/codex/unrelated"
    registered_trees.append(tree)
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    (tasks / "review.json").write_text(
        json.dumps({"task_id": "review", "status": "running", "review_contract": {"input_root": str(tmp_path)}})
    )
    assert (
        worktree_claims.active_worktree_claim_refusal(
            tree, tasks_dir=tasks, repo_root=tmp_path, review_inputs_only=review_inputs_only
        )
        is None
    )


@pytest.mark.parametrize("inner_first", [False, True])
@pytest.mark.parametrize("review_inputs_only", [False, True])
def test_nested_review_input_claims_only_deepest_registered_tree(
    tmp_path, registered_trees, inner_first, review_inputs_only
):
    outer = tmp_path / ".worktrees/dispatch/codex/outer"
    inner = outer / ".worktrees/dispatch/codex/inner"
    registered_trees.extend([inner, outer] if inner_first else [outer, inner])
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    (tasks / "review.json").write_text(
        json.dumps({"task_id": "review", "status": "running", "review_contract": {"input_root": str(inner / "inputs")}})
    )
    for tree, expected in ((outer, None), (inner, "review input root claimed by active task review")):
        assert (
            worktree_claims.active_worktree_claim_refusal(
                tree, tasks_dir=tasks, repo_root=tmp_path, review_inputs_only=review_inputs_only
            )
            == expected
        )


@pytest.mark.parametrize(
    "contract", [[], "invalid", {}, {"input_root": 7}, {"input_root": ""}, {"input_root": "\u0000"}]
)
def test_malformed_active_review_contract_fails_closed(tmp_path, contract):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    (tasks / "review.json").write_text(json.dumps({"status": "running", "review_contract": contract}))
    assert (
        worktree_claims.active_worktree_claim_refusal(
            tmp_path / "inputs",
            tasks_dir=tasks,
            repo_root=tmp_path,
        )
        == "task record review.json unreadable; refusing worktree removal"
    )


@pytest.mark.parametrize("review_inputs_only", [False, True])
def test_rootless_isolated_contract_preserves_worker_claim(tmp_path, review_inputs_only):
    tree = tmp_path / "worker"
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    (tasks / "review.json").write_text(
        json.dumps(
            {
                "task_id": "review",
                "status": "running",
                "worktree_path": str(tree),
                "review_access": "isolated",
                "review_contract": {"prompt_sha256": "a" * 64},
            }
        )
    )
    refusal = worktree_claims.active_worktree_claim_refusal(
        tree,
        tasks_dir=tasks,
        repo_root=tmp_path,
        review_inputs_only=review_inputs_only,
    )
    assert refusal == (None if review_inputs_only else "worktree claimed by active task review")


def test_isolated_rendered_contract_missing_input_root_fails_closed(tmp_path):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    (tasks / "review.json").write_text(
        json.dumps(
            {
                "status": "running",
                "review_access": "isolated",
                "review_contract": {"render_checkout": str(tmp_path)},
            }
        )
    )
    assert worktree_claims.active_worktree_claim_refusal(tmp_path, tasks_dir=tasks, repo_root=tmp_path) == (
        "task record review.json unreadable; refusing worktree removal"
    )


@pytest.mark.parametrize("unreadable", ["invalid-json", "permission"])
def test_unreadable_review_record_fails_closed(tmp_path, monkeypatch, unreadable):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    state = tasks / "review.json"
    state.write_text('{"status": "running", "review_contract":')
    if unreadable == "permission":
        read = Path.read_bytes

        def denied(path):
            if path == state:
                raise PermissionError("test denial")
            return read(path)

        monkeypatch.setattr(Path, "read_bytes", denied)
    assert (
        worktree_claims.active_worktree_claim_refusal(
            tmp_path / "inputs",
            tasks_dir=tasks,
            repo_root=tmp_path,
        )
        == "task record review.json unreadable; refusing worktree removal"
    )


def test_shared_remover_preserves_review_inputs_then_releases(tmp_path, registered_trees):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    state = tasks / "review.json"
    tree = tmp_path / "inputs"
    registered_trees.append(tree)
    record = {"status": "running", "task_id": "review", "review_contract": {"input_root": str(tree)}}
    calls = []

    def git_runner(_cwd, argv):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    def remove():
        return worktree_claims.remove_unclaimed_worktree(
            tree,
            repo_root=tmp_path,
            tasks_dir=tasks,
            lock_dir=tmp_path / "locks",
            owner_task_id=None,
            reason="test",
            git_runner=git_runner,
        )

    state.write_text(json.dumps(record))
    assert remove().action == "skipped"
    assert not any(argv[:2] == ["worktree", "remove"] for argv in calls)
    record["status"] = "failed"
    state.write_text(json.dumps(record))
    assert remove().action == "removed"
    assert any(argv[:2] == ["worktree", "remove"] for argv in calls)


def test_plan_lock_probe_is_read_only_and_releases_its_probe(tmp_path):
    tree, locks = tmp_path / "inputs", tmp_path / "locks"
    assert worktree_claims.existing_worktree_lock_refusal(tree, lock_dir=locks) is None
    assert not locks.exists()
    with worktree_claims.worktree_lock(tree, lock_dir=locks):
        assert worktree_claims.existing_worktree_lock_refusal(tree, lock_dir=locks) == worktree_claims.LOCK_BUSY
    assert worktree_claims.existing_worktree_lock_refusal(tree, lock_dir=locks) is None
    with worktree_claims.worktree_lock(tree, lock_dir=locks, timeout_s=0):
        pass


@pytest.mark.parametrize("failure", ["open", "flock"])
def test_plan_lock_probe_fails_closed_on_unreadable_lock(tmp_path, monkeypatch, failure):
    tree, locks = tmp_path / "inputs", tmp_path / "locks"
    with worktree_claims.worktree_lock(tree, lock_dir=locks):
        pass

    def denied(*_args):
        raise PermissionError("fixture unreadable lock")

    if failure == "open":
        monkeypatch.setattr(worktree_claims.os, "open", denied)
    else:
        monkeypatch.setattr(worktree_claims.fcntl, "flock", denied)
    assert worktree_claims.existing_worktree_lock_refusal(tree, lock_dir=locks) == worktree_claims.LOCK_UNAVAILABLE
