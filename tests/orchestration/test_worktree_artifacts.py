"""Byte preservation and fail-closed removal guards for #9449."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts.orchestration import worktree_artifacts as wa


@pytest.fixture
def checkout(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, env=env, timeout=30)
    (repo / ".gitignore").write_text("batch_state/\nignored/\n.pytest_cache/\n__pycache__/\n")
    # The helper only needs an index; this fixture does not commit or remove anything.
    subprocess.run(["git", "add", ".gitignore"], cwd=repo, check=True, env=env, timeout=30)
    primary = tmp_path / "primary"
    primary.mkdir()
    tasks = primary / "batch_state/tasks"
    tasks.mkdir(parents=True)
    return repo, primary, tasks


def guard(checkout, *, task_id="artifact-task", record=None):
    repo, primary, tasks = checkout
    return wa.preserve_worktree_artifacts(repo, primary=primary, task_id=task_id, tasks_dir=tasks, task_record=record)


def artifact(checkout, name="batch_state/sub/report.bin", payload=b"proof\x00\xff"):
    path = checkout[0] / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def test_preserved_bytes_record_and_idempotency(checkout):
    source = artifact(checkout)
    record = {"status": "done", "response": "Capture `batch_state/sub/report.bin`."}
    (checkout[2] / "artifact-task.json").write_text(json.dumps(record))
    ok, reason, metadata = guard(checkout, record=record)
    assert ok and not reason
    assert metadata["count"] == 1
    copy = Path(metadata["location"]) / "batch_state/sub/report.bin"
    assert copy.read_bytes() == source.read_bytes()
    assert wa._fingerprint(copy) == wa._fingerprint(source)
    saved = json.loads((checkout[2] / "artifact-task.json").read_text())
    assert saved["preserved_artifacts"] == record["preserved_artifacts"] == metadata
    assert guard(checkout)[0]  # Repeated guard retains verified existing bytes.


def test_empty_files_dirs_and_pycache_do_not_need_identity(checkout):
    artifact(checkout, payload=b"")
    artifact(checkout, "batch_state/__pycache__/worker.pyc")
    (checkout[0] / "batch_state/empty").mkdir()
    assert guard(checkout, task_id=None) == (True, "", None)
    assert not (checkout[1] / "batch_state/preserved").exists()


@pytest.mark.parametrize("task_id", [None, "../escape", "..", "bad/id"])
def test_missing_or_unsafe_identity_blocks_copy(checkout, task_id):
    source = artifact(checkout)
    ok, reason, _ = guard(checkout, task_id=task_id)
    assert not ok and "safe task identity" in reason
    assert source.exists()


@pytest.mark.parametrize("failure", ["copy", "corruption", "record"])
def test_failed_copy_verification_or_record_blocks_removal(checkout, monkeypatch, failure):
    source = artifact(checkout)
    (checkout[2] / "artifact-task.json").write_text(json.dumps({"status": "done"}))
    if failure == "copy":

        def fail_copy(*_args):
            raise OSError("copy denied")

        monkeypatch.setattr(wa.shutil, "copyfile", fail_copy)
    elif failure == "corruption":
        monkeypatch.setattr(wa.shutil, "copyfile", lambda _source, destination: destination.write_bytes(b"wrong"))
    else:

        def fail_record(*_args):
            raise OSError("record denied")

        monkeypatch.setattr(wa.reaper_lifecycle, "_atomic_write", fail_record)
    ok, reason, _ = guard(checkout)
    assert not ok and "artifact preservation failed" in reason
    assert source.read_bytes() == b"proof\x00\xff"
    assert not list((checkout[1] / "batch_state/preserved").rglob(".preserve-*"))


def test_different_existing_copy_is_never_overwritten(checkout):
    artifact(checkout)
    destination = checkout[1] / "batch_state/preserved/artifact-task/batch_state/sub/report.bin"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"previous evidence")
    ok, reason, _ = guard(checkout)
    assert not ok and "different bytes" in reason
    assert destination.read_bytes() == b"previous evidence"


@pytest.mark.parametrize("destination", [False, True])
def test_symlink_paths_block_preservation(checkout, destination):
    source = artifact(checkout)
    elsewhere = checkout[1] / "elsewhere"
    elsewhere.mkdir()
    if destination:
        (checkout[1] / "batch_state/preserved").symlink_to(elsewhere, target_is_directory=True)
    else:
        source.unlink()
        source.symlink_to(checkout[0] / ".gitignore")
    ok, reason, _ = guard(checkout)
    assert not ok and ("symlink" in reason or "regular file" in reason)
    assert not list(elsewhere.iterdir())


def test_primary_task_sidecar_is_not_copied(checkout):
    shared = checkout[2] / "artifact-task.result"
    shared.write_bytes(b"already durable")
    source = artifact(checkout)
    source.unlink()
    source.symlink_to(shared)
    assert guard(checkout) == (True, "", None)
    assert shared.read_bytes() == b"already durable"


@pytest.mark.parametrize(
    "reference",
    [
        "`ignored/a report.txt`",
        "[report](ignored/a report.txt)",
        "'ignored/a report.txt'",
        "`ignored/a report.txt:12`",
        "`batch_state/../ignored/a report.txt`",
    ],
)
def test_named_ignored_artifact_outside_batch_state_preserved(checkout, reference):
    source = artifact(checkout, "ignored/a report.txt")
    ok, _reason, metadata = guard(checkout, record={"response": f"Capture {reference}."})
    assert ok
    assert metadata["count"] == 1
    assert (Path(metadata["location"]) / "ignored/a report.txt").read_bytes() == source.read_bytes()


def test_result_sidecar_is_read_and_tracked_named_files_are_safe(checkout):
    sidecar = checkout[2] / "artifact-task.result"
    sidecar.write_text("Capture `ignored/note.txt`. Read `.gitignore`.")
    source = artifact(checkout, "ignored/note.txt")
    ok, _reason, metadata = guard(checkout, record={"result_file": str(sidecar)})
    assert ok
    assert (Path(metadata["location"]) / "ignored/note.txt").read_bytes() == source.read_bytes()
    source.unlink()
    assert guard(checkout, record={"result_file": str(sidecar)})[0]


def test_unreadable_inventory_retains_artifact(checkout, monkeypatch):
    source = artifact(checkout)

    def fail_inventory(*_args):
        raise subprocess.CalledProcessError(128, "git ls-files")

    monkeypatch.setattr(wa, "_git_paths", fail_inventory)
    assert not guard(checkout)[0]
    assert source.exists()


def test_malformed_task_record_is_not_overwritten(checkout):
    path = checkout[2] / "artifact-task.json"
    path.write_text("broken JSON")
    assert not guard(checkout)[0]
    assert path.read_text() == "broken JSON"


def test_batch_state_symlink_cannot_hide_local_artifacts(checkout):
    source = artifact(checkout, "ignored/hidden.txt")
    (checkout[0] / "batch_state").symlink_to(source.parent, target_is_directory=True)
    ok, reason, _ = guard(checkout)
    assert not ok and "batch_state is a symlink" in reason
    assert source.exists()


@pytest.mark.parametrize("reference", ["root", "./", "ignored", ".pytest_cache/cache.txt"])
def test_named_directory_or_cache_does_not_block(checkout, reference):
    artifact(checkout, "ignored/report.txt")
    cache = artifact(checkout, ".pytest_cache/cache.txt")
    reference = str(checkout[0]) if reference == "root" else reference
    assert guard(checkout, record={"response": f"Worked in `{reference}`."}) == (True, "", None)
    assert cache.exists()


def test_record_changed_during_copy_keeps_other_writers_fields(checkout, monkeypatch):
    artifact(checkout)
    path = checkout[2] / "artifact-task.json"
    path.write_text(json.dumps({"status": "done", "response": "original"}))
    copy = wa.shutil.copyfile

    def concurrent_writer(source, destination):
        from scripts.orchestration.dead_worker_state import task_state_lock

        with task_state_lock(path):
            path.write_text(json.dumps({"status": "failed", "response": "new", "other_writer": True}))
        return copy(source, destination)

    monkeypatch.setattr(wa.shutil, "copyfile", concurrent_writer)
    assert guard(checkout, record={"stale_field": "do not merge"})[0]
    saved = json.loads(path.read_text())
    assert saved["status"] == "failed"
    assert saved["response"] == "new"
    assert saved["other_writer"] is True
    assert "stale_field" not in saved
    assert saved["preserved_artifacts"]["count"] == 1


def test_missing_record_is_not_created(checkout):
    source = artifact(checkout)
    ok, reason, metadata = guard(checkout)
    assert ok
    assert "task record missing" in reason
    assert metadata["record_update"] == "skipped_missing_record"
    assert (Path(metadata["location"]) / "batch_state/sub/report.bin").read_bytes() == source.read_bytes()
    assert not (checkout[2] / "artifact-task.json").exists()


def test_named_symlink_does_not_block(checkout, tmp_path):
    target = tmp_path / "outside.txt"
    target.write_bytes(b"lives outside the checkout")
    (checkout[0] / "ignored").mkdir()
    (checkout[0] / "ignored/link.txt").symlink_to(target)
    assert guard(checkout, record={"response": "Wrote `ignored/link.txt`."}) == (True, "", None)


def test_success_clears_a_stale_preservation_error(checkout):
    artifact(checkout)
    path = checkout[2] / "artifact-task.json"
    path.write_text(json.dumps({"status": "done", "artifact_preservation_error": "earlier copy failed"}))
    record = {"artifact_preservation_error": "earlier copy failed"}
    assert guard(checkout, record=record)[0]
    assert "artifact_preservation_error" not in json.loads(path.read_text())
    assert "artifact_preservation_error" not in record
