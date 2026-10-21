"""Creation evidence shared by the derived-leaf and cohort proofs (#10486)."""

import json
import os

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.orchestration.task_record_store import archived_task_record_path, task_record_path
from tests.test_fleet_post_task_reap import _reuse_cohort
from tests.test_fleet_post_task_reap import hermetic_reap as hermetic_reap


@pytest.mark.parametrize(
    "record,expected",
    [
        ({}, False),
        ({"worktree_reused": False}, False),
        ({"worktree_reused": False, "ignored_output_baseline": None}, False),
        ({"worktree_reused": False, "ignored_output_baseline": False}, False),
        ({"worktree_reused": False, "ignored_output_baseline": []}, False),
        ({"worktree_reused": False, "ignored_output_baseline": "inventory"}, False),
        ({"worktree_reused": False, "ignored_output_baseline": {}}, True),
        ({"worktree_reused": True, "ignored_output_baseline": {}}, False),
        ({"worktree_reused": 0, "ignored_output_baseline": {}}, False),
        ({"worktree_reused": "false", "ignored_output_baseline": {}}, False),
        ({"ignored_output_baseline": {}}, False),
    ],
)
def test_record_created_worktree_requires_both_creation_fields(record, expected):
    assert output.record_created_worktree(record) is expected


@pytest.mark.parametrize("archived", [False, True], ids=["hot", "archived"])
@pytest.mark.parametrize("status", ["failed", "done", "running"])
def test_false_record_without_inventory_is_never_cohort_creator(hermetic_reap, archived, status):
    repo, tasks = hermetic_reap
    task_id = "codex-shared-leaf"
    tree = _reuse_cohort(repo, tasks, creator_task=task_id, successor_task="codex-reuser-r2")
    path = task_record_path(tasks, task_id)
    state = json.loads(path.read_text())
    state.pop("ignored_output_baseline")
    state.update(status=status, pid=os.getpid() if status == "running" else None)
    if archived:
        path.unlink()
        path = archived_task_record_path(tasks, task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state))
    matches = output.matching_worktree_records(tree, tasks, repo_root=repo, publish_cache=False)

    with pytest.raises(ValueError, match="ambiguous worktree task attribution"):
        output.reused_worktree_creator(matches, tree, repo_root=repo, tasks_dir=tasks)
    for publish_cache in (False, True, True):
        assert output.resolve_worktree_record(tree, tasks, repo_root=repo, publish_cache=publish_cache) == (None, {})
    assert tree.exists()


@pytest.mark.parametrize("archived", [False, True], ids=["hot", "archived"])
def test_inventory_backed_creator_with_settled_reuser_is_resolved(hermetic_reap, archived):
    repo, tasks = hermetic_reap
    task_id = "codex-creator-r1"
    tree = _reuse_cohort(repo, tasks, creator_task=task_id, successor_task="codex-reuser-r2")
    path = task_record_path(tasks, task_id)
    if archived:
        archive = archived_task_record_path(tasks, task_id)
        archive.parent.mkdir(parents=True, exist_ok=True)
        path.rename(archive)
        path = archive
    state = json.loads(path.read_text())
    matches = output.matching_worktree_records(tree, tasks, repo_root=repo, publish_cache=False)

    assert output.reused_worktree_creator(matches, tree, repo_root=repo, tasks_dir=tasks) == (path, state)
