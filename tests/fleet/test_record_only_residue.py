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
    repo, primary, tasks = checkout
    artifact(checkout, "ignored/residue.bin", b"x" * size)
    bound_record(checkout, {"status": "done"})
    ok, reason, receipt = output.preserve_worktree_artifacts(
        repo, primary=primary, task_id="artifact-task", tasks_dir=tasks, extra_files=["ignored/residue.bin"]
    )
    assert ok and not reason
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
    assert receipt["bytes"] == size
    assert (primary / receipt["manifest_path"]).is_file()
    assert output.verify_retrieval(primary, receipt) == receipt["content_sha256"] == receipt["retrieval_proof_sha256"]
    assert receipt["paths"][0]["sha256"] == hashlib.sha256(b"x" * size).hexdigest()
    assert not (primary / "batch_state/preserved").exists()
    assert (tasks / "artifact-task.json").stat().st_size < 10 * 1024 * 1024


def test_failed_residue_inventory_never_retains_worktree(checkout, monkeypatch):
    bound_record(checkout, {"status": "done"})
    monkeypatch.setattr(output, "_ignored_output_files", lambda *a, **kw: (_ for _ in ()).throw(OSError()))
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
    state = json.loads(record.read_text())
    state["keep_worktree"] = True
    record.write_text(json.dumps(state))
    assert not output.preserve_worktree_artifacts(tree, primary=repo, task_id="interrupted", tasks_dir=tasks)[0]
    assert post_task_reap._release_retention("interrupted", tasks_dir=tasks, repo_root=repo, apply=True) is None
    log = tasks / "interrupted.log"
    log.write_text("small task log")
    report = post_task_reap.post_task_reap(
        "interrupted", tasks_dir=tasks, repo_root=repo, apply=True, include_acp_runtime=False
    )
    assert report["main_worktree"]["action"] == "removed", report
    assert not tree.exists() and result.exists() and log.read_text() == "small task log"
    receipt = json.loads(record.read_text())["preserved_artifacts"]
    assert receipt["mode"] == "record-only"
    assert "leftover.bin" in {entry["path"] for entry in receipt["paths"]}
    assert not (repo / "batch_state/preserved").exists()


def test_receipt_inventory_cannot_grow_past_the_per_task_write_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 4096)
    names = [f"residue-{n}" for n in range(100)]
    for name in names:
        (tmp_path / name).write_bytes(b"x")
    receipt = output.record_only_receipt(tmp_path, names, {"task_id": "test"})
    assert receipt["count"] == 100 and receipt["bytes"] == 100
    assert receipt["paths_truncated"] and len(json.dumps(receipt).encode()) < 4096


@pytest.mark.parametrize("kept", [False, True])
def test_receipt_write_failure_keeps_ownership_guards_without_retaining_residue(checkout, monkeypatch, kept):
    artifact(checkout, "ignored/residue.bin")
    bound_record(checkout, {"status": "done", "keep_worktree": kept})
    monkeypatch.setattr(output.artifacts.reaper_lifecycle, "_atomic_write", lambda *a: (_ for _ in ()).throw(OSError()))
    assert guard(checkout)[0] == (not kept)
