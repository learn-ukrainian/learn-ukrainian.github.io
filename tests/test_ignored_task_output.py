"""Ignored output inventory/copy boundaries, using only temporary repositories."""

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.fleet import ignored_task_output as output
from tests.orchestration import test_worktree_artifacts as fixtures

checkout = fixtures.checkout
artifact = fixtures.artifact


def preserve(checkout, record=None, task_id="output-task"):
    repo, primary, tasks = checkout
    if record is not None:
        (tasks / f"{task_id}.json").write_text(json.dumps(record))
    return output.preserve_worktree_artifacts(
        repo, primary=primary, task_id=task_id, tasks_dir=tasks, task_record=record
    )


@pytest.mark.parametrize("status", ["done", "no_deliverable", "failed"])
def test_all_ignored_output_preserved_without_response_names(checkout, status):
    repo, _, tasks = checkout
    (repo / ".gitignore").write_text(".cache/\nignored/\n")
    artifact(checkout, ".cache/transcriptions/page.txt", b"transcription")
    artifact(checkout, "ignored/empty.txt", b"")
    ok, reason, receipt = preserve(checkout, {"status": status, "started_at": "2000-01-01T00:00:00Z"})
    assert ok and not reason
    assert receipt["count"] == 2 and receipt["bytes"] == 13
    assert (Path(receipt["location"]) / ".cache/transcriptions/page.txt").read_bytes() == b"transcription"
    assert (Path(receipt["location"]) / "ignored/empty.txt").is_file()
    assert json.loads((tasks / "output-task.json").read_text())["preserved_artifacts"] == receipt


def test_start_boundary_includes_modified_and_equal_timestamps_only(checkout):
    old = artifact(checkout, "ignored/old.txt")
    cutoff = int(old.stat().st_ctime) + 2
    equal = artifact(checkout, "ignored/equal.txt")
    modified = artifact(checkout, "ignored/modified.txt", b"new version")
    os.utime(old, (946684799, 946684799))
    os.utime(equal, (cutoff, cutoff))
    os.utime(modified, (cutoff + 1, cutoff + 1))
    ok, _, receipt = preserve(checkout, {"started_at": datetime.fromtimestamp(cutoff, UTC).isoformat()})
    assert ok and receipt["count"] == 2
    location = Path(receipt["location"])
    assert not (location / "ignored/old.txt").exists()
    assert (location / "ignored/equal.txt").exists()
    assert (location / "ignored/modified.txt").read_bytes() == b"new version"


@pytest.mark.parametrize("cache", sorted(output.artifacts._DISPOSABLE_DIRECTORIES - {".git"}))
def test_known_caches_excluded(checkout, cache):
    artifact(checkout, f"ignored/{cache}/tool.bin")
    assert preserve(checkout) == (True, "", None)


@pytest.mark.parametrize("failure", ["cap", "copy", "record", "inventory", "changed", "added", "invalid_start"])
def test_failure_retains_sources(checkout, monkeypatch, failure):
    source = artifact(checkout, "ignored/report.txt", b"task output")
    record = {"status": "done"}
    if failure == "cap":
        monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 10)
    elif failure == "invalid_start":
        record["started_at"] = "bad"
    elif failure == "inventory":
        monkeypatch.setattr(
            output.artifacts, "_git_paths", lambda *args: (_ for _ in ()).throw(subprocess.SubprocessError())
        )
    elif failure == "record":
        monkeypatch.setattr(
            output.artifacts,
            "_update_existing_task_record",
            lambda *args, **kwargs: (_ for _ in ()).throw(OSError("record denied")),
        )
    else:
        copy = output.artifacts._copy_verified

        def faulty_copy(src, dst):
            if failure == "copy":
                raise OSError("copy denied")
            copy(src, dst)
            if failure == "changed":
                source.write_bytes(b"changed")
            else:
                artifact(checkout, "ignored/added.txt")

        monkeypatch.setattr(output.artifacts, "_copy_verified", faulty_copy)
    ok, reason, _ = preserve(checkout, record)
    assert not ok and "refusing worktree removal" in reason
    assert source.exists()
    if failure == "cap":
        assert not (checkout[1] / "batch_state/preserved").exists()


def test_missing_record_uses_receipt_identity_and_all_ignored_files(checkout):
    artifact(checkout, "ignored/report.txt")
    ok, _, receipt = preserve(checkout, task_id=None)
    assert ok and receipt["count"] == 1
    assert receipt["record_update"] == "skipped_missing_record"
    assert Path(receipt["location"]).parent.name.startswith("worktree-")
    assert json.loads(Path(receipt["receipt_path"]).read_text()) == receipt


def test_cap_is_inclusive_and_existing_copies_are_verified(checkout, monkeypatch):
    artifact(checkout, "ignored/report.txt", b"0123456789")
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 10)
    assert preserve(checkout, {"status": "done"})[0]
    assert preserve(checkout)[0]


def test_touch_old_mtime_during_task_is_preserved(checkout):
    started = datetime.now(UTC)
    source = artifact(checkout, "ignored/touched.txt", b"new task output")
    subprocess.run(["touch", "-d", "2000-01-01 UTC", str(source)], check=True, timeout=30)
    assert source.stat().st_mtime < started.timestamp() <= source.stat().st_ctime
    ok, _, receipt = preserve(checkout, {"started_at": started.isoformat()})
    assert ok and receipt["count"] == 1
    assert (Path(receipt["location"]) / "ignored/touched.txt").read_bytes() == b"new task output"


def test_retry_preserves_different_bytes_without_overwriting_first_attempt(checkout):
    source = artifact(checkout, "ignored/report.txt", b"first attempt")
    ok, _, first = preserve(checkout, {"status": "done"})
    assert ok
    source.write_bytes(b"second attempt")
    ok, _, second = preserve(checkout)
    assert ok and first["location"] != second["location"]
    assert (Path(first["location"]) / "ignored/report.txt").read_bytes() == b"first attempt"
    assert (Path(second["location"]) / "ignored/report.txt").read_bytes() == b"second attempt"
    assert json.loads((checkout[2] / "output-task.json").read_text())["preserved_artifacts"] == second


def test_missing_record_receipt_write_failure_retains_sources(checkout, monkeypatch):
    source = artifact(checkout, "ignored/report.txt", b"task output")
    original_open = Path.open

    def fail_receipt(path, *args, **kwargs):
        if path.name.endswith(".receipt.json"):
            raise OSError("receipt denied")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_receipt)
    ok, reason, _ = preserve(checkout, task_id=None)
    assert not ok and "receipt denied" in reason and "refusing worktree removal" in reason
    assert source.read_bytes() == b"task output"


def test_entire_exclusion_is_limited_to_logs(checkout):
    (checkout[0] / ".gitignore").write_text(".entire/\n")
    artifact(checkout, ".entire/logs/diagnostic.log", b"tool state")
    artifact(checkout, ".entire/report.txt", b"task output")
    ok, _, receipt = preserve(checkout)
    assert ok and receipt["count"] == 1
    assert (Path(receipt["location"]) / ".entire/report.txt").read_bytes() == b"task output"


def test_directory_inventory_prunes_entire_logs_but_keeps_output(checkout):
    repo = checkout[0]
    artifact(checkout, ".entire/logs/diagnostic.log", b"tool state")
    artifact(checkout, ".entire/report.txt", b"task output")
    assert output.artifacts._inspect_directory_artifact(repo / ".entire", ".entire", worktree=repo) == [
        ".entire/report.txt"
    ]


@pytest.mark.parametrize("cache", [".pytest_breadcrumbs", "site/.astro", ".entire/logs", ".hypothesis", ".tox", ".nox"])
def test_tool_state_excluded_but_cache_output_survives(checkout, cache):
    (checkout[0] / ".gitignore").write_text(".cache/\n" + cache + "/\n")
    artifact(checkout, f"{cache}/tool.bin", b"regenerable")
    artifact(checkout, ".cache/out/answer.txt", b"task output")
    ok, _, receipt = preserve(checkout, {"response": f"Tool state: `{cache}/tool.bin`."})
    assert ok and receipt["count"] == 1 and receipt["bytes"] == len(b"task output")
    assert (Path(receipt["location"]) / ".cache/out/answer.txt").read_bytes() == b"task output"
    assert not (Path(receipt["location"]) / cache).exists()
