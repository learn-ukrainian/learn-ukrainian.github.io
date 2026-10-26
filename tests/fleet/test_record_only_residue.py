"""C-2481: settled residue must never regrow the deleted archive."""

import hashlib
import json

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.fleet import post_task_reap, runtime_held_work
from tests.orchestration.test_worktree_artifacts import artifact, bound_record, guard
from tests.orchestration.test_worktree_artifacts import checkout as checkout
from tests.test_fleet_post_task_reap import _run
from tests.test_fleet_post_task_reap import interrupted_checkout as interrupted_checkout
from tests.test_fleet_post_task_reap import interrupted_reap as interrupted_reap


@pytest.mark.parametrize("size", [4, 10 * 1024 * 1024 + 1])
def test_settled_task_residue_is_never_copied_into_batch_state_preserved(checkout, size):
    _repo, primary, tasks = checkout
    artifact(checkout, "ignored/residue.bin", b"x" * size)
    bound_record(checkout, {"status": "done"})
    ok, reason, receipt = guard(checkout)
    assert ok and not reason
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
    assert receipt["bytes"] == size
    assert receipt["paths"][0]["sha256"] == hashlib.sha256(b"x" * size).hexdigest()
    assert not (primary / "batch_state/preserved").exists()
    assert (tasks / "artifact-task.json").stat().st_size < 10 * 1024 * 1024


def test_failed_residue_inventory_never_retains_worktree(checkout, monkeypatch):
    bound_record(checkout, {"status": "done"})
    monkeypatch.setattr(output, "_classified_inventory", lambda *a, **kw: (_ for _ in ()).throw(OSError()))
    artifact(checkout, "ignored/residue.bin")
    assert guard(checkout)[0]


@pytest.mark.parametrize("writer", ["evidence", "held", "abandon"])
def test_no_per_task_preserve_write_exceeds_10_mib(tmp_path, writer):
    root = tmp_path / "lease"
    (root / "evidence").mkdir(parents=True)
    (root / "evidence/large.bin").write_bytes(b"x" * (10 * 1024 * 1024 + 1))
    record = {"task_id": "test", "held_work": ["evidence/large.bin"]}
    if writer == "evidence":
        receipt = runtime_held_work.preserve_evidence(root, primary=tmp_path, record=record)
        assert runtime_held_work.evidence_matches_receipt(root, receipt)
    elif writer == "held":
        receipt = runtime_held_work.preserve(root, primary=tmp_path, record=record, response="")
    else:
        receipt, created = output.capture_abandon_output(root, primary=tmp_path, record=record)
        assert created is None
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
    assert len(json.dumps(receipt).encode()) < 10 * 1024 * 1024
    assert not (tmp_path / "batch_state/preserved").exists()


def test_reaper_removes_a_worktree_whose_residue_is_untracked(interrupted_reap):
    repo, tree, tasks, record, result, _log = interrupted_reap
    _run(["git", "push", "-u", "origin", "codex/interrupted"], cwd=tree)
    (tree / "leftover.bin").write_bytes(b"untracked")
    report = post_task_reap.post_task_reap(
        "interrupted", tasks_dir=tasks, repo_root=repo, apply=True, include_acp_runtime=False
    )
    assert report["main_worktree"]["action"] == "removed", report
    assert not tree.exists() and result.exists()
    assert json.loads(record.read_text())["preserved_artifacts"]["mode"] == "record-only"
    assert not (repo / "batch_state/preserved").exists()
