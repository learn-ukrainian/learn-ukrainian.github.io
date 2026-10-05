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
    if record is None and task_id is not None and not (tasks / f"{task_id}.json").exists():
        record = {}
    if record is not None:
        record.setdefault("task_id", task_id)
        record.setdefault("worktree_path", str(repo))
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
    assert ((checkout[1] / receipt["location"]) / ".cache/transcriptions/page.txt").read_bytes() == b"transcription"
    assert ((checkout[1] / receipt["location"]) / "ignored/empty.txt").is_file()
    assert json.loads((tasks / "output-task.json").read_text())["preserved_artifacts"] == receipt


@pytest.mark.parametrize(
    "start",
    ["2000-01-01T00:00:00Z", None, "bad", "2000-01-01T00:00:00", "2999-01-01T00:00:00Z"],
    ids=["old", "missing", "malformed", "naive", "future"],
)
def test_start_values_are_irrelevant_to_selection(checkout, start):
    old = artifact(checkout, "ignored/old.txt")
    modified = artifact(checkout, "ignored/modified.txt", b"new version")
    os.utime(old, (946684799, 946684799))
    record = {} if start is None else {"started_at": start}
    ok, _, receipt = preserve(checkout, record)
    assert ok and receipt["count"] == 2
    location = checkout[1] / receipt["location"]
    assert (location / "ignored/old.txt").read_bytes() == old.read_bytes()
    assert (location / "ignored/modified.txt").read_bytes() == modified.read_bytes()
    assert receipt["retrieval_proof_sha256"] == receipt["content_sha256"]
    assert receipt["retention_disposition"] == "retrieved"
    assert all(entry["class"] == "unknown_baseline" for entry in receipt["paths"])
    assert str(checkout[0]) not in json.dumps(receipt)


@pytest.mark.parametrize("cache", sorted(output.artifacts._DISPOSABLE_DIRECTORIES - {".git"}))
def test_known_caches_excluded(checkout, cache):
    artifact(checkout, f"ignored/{cache}/tool.bin")
    assert preserve(checkout) == (True, "", None)


@pytest.mark.parametrize("failure", ["cap", "copy", "record", "inventory", "changed", "added"])
def test_failure_retains_sources(checkout, monkeypatch, failure):
    source = artifact(checkout, "ignored/report.txt", b"task output")
    record = {"status": "done"}
    if failure == "cap":
        monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 10)
    elif failure == "inventory":
        monkeypatch.setattr(
            output.artifacts, "_git_paths", lambda *args: (_ for _ in ()).throw(subprocess.SubprocessError())
        )
    elif failure == "record":
        monkeypatch.setattr(
            output.artifacts.reaper_lifecycle,
            "_atomic_write",
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


def test_missing_record_retains_unknown_output_without_fallback_attribution(checkout):
    artifact(checkout, "ignored/report.txt")
    ok, _, receipt = preserve(checkout, task_id=None)
    assert not ok and receipt["count"] == 1
    assert receipt["retention_disposition"] == "retained"
    assert receipt["owner"] == "infra lane"
    assert not (checkout[1] / "batch_state/preserved").exists()


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
    assert ((checkout[1] / receipt["location"]) / "ignored/touched.txt").read_bytes() == b"new task output"


def test_retry_preserves_different_bytes_without_overwriting_first_attempt(checkout):
    source = artifact(checkout, "ignored/report.txt", b"first attempt")
    ok, _, first = preserve(checkout, {"status": "done"})
    assert ok
    source.write_bytes(b"second attempt")
    ok, _, second = preserve(checkout)
    assert ok and first["location"] != second["location"]
    assert ((checkout[1] / first["location"]) / "ignored/report.txt").read_bytes() == b"first attempt"
    assert ((checkout[1] / second["location"]) / "ignored/report.txt").read_bytes() == b"second attempt"
    assert json.loads((checkout[2] / "output-task.json").read_text())["preserved_artifacts"] == second


def test_retry_reuses_identical_copy_without_copying(checkout, monkeypatch):
    artifact(checkout, "ignored/report.txt", b"same attempt")
    ok, _, first = preserve(checkout, {"status": "done"})
    assert ok and not first["reused"]
    monkeypatch.setattr(output.artifacts, "_copy_verified", lambda *_args: pytest.fail("identical output copied again"))
    ok, _, second = preserve(checkout)
    assert ok and second["reused"] and second["location"] == first["location"]
    assert json.loads((checkout[2] / "output-task.json").read_text())["preserved_artifacts"] == second


@pytest.mark.parametrize("binding", ["missing", "other", "cwd", "alias"])
def test_only_real_path_bound_record_receives_receipt(checkout, binding):
    repo, _, tasks = checkout
    artifact(checkout, "ignored/old.txt", b"old output")
    record = {"task_id": "output-task", "started_at": "2999-01-01T00:00:00Z"}
    if binding == "other":
        other = repo.parent / "other"
        other.mkdir()
        record["worktree_path"] = str(other)
    elif binding == "cwd":
        record["cwd"] = str(repo)
    elif binding == "alias":
        alias = repo.parent / "alias"
        alias.symlink_to(repo, target_is_directory=True)
        record["worktree_path"] = str(alias)
    path = tasks / "output-task.json"
    path.write_text(json.dumps(record))
    ok, _, receipt = output.preserve_worktree_artifacts(
        repo, primary=checkout[1], task_id="output-task", tasks_dir=tasks, task_record=record
    )
    assert receipt["count"] == 1
    if binding in {"cwd", "alias"}:
        assert ok
        assert (checkout[1] / receipt["location"] / "ignored/old.txt").read_bytes() == b"old output"
        assert json.loads(path.read_text())["preserved_artifacts"] == receipt
        assert record["preserved_artifacts"] == receipt
    else:
        assert not ok and receipt["retention_disposition"] == "retained"
        assert json.loads(path.read_text()) == record and "preserved_artifacts" not in record


def test_matching_archive_wins_over_unrelated_hot_record(checkout):
    repo, primary, tasks = checkout
    old = artifact(checkout, "ignored/old.txt", b"old")
    new = artifact(checkout, "ignored/new.txt", b"new")
    other = repo.parent / "other"
    other.mkdir()
    hot = {"worktree_path": str(other), "started_at": "2999-01-01T00:00:00Z"}
    (tasks / "output-task.json").write_text(json.dumps(hot))
    archive = tasks / "archive/output-task.json"
    archive.parent.mkdir()
    archive.write_text(json.dumps({"task_id": "output-task", "cwd": str(repo), "started_at": "2999-01-01T00:00:00Z"}))
    ok, _, receipt = output.preserve_worktree_artifacts(repo, primary=primary, task_id="output-task", tasks_dir=tasks)
    assert ok and receipt["count"] == 2 and not receipt["reused"]
    assert ((checkout[1] / receipt["location"]) / "ignored/new.txt").read_bytes() == b"new"
    assert ((checkout[1] / receipt["location"]) / "ignored/old.txt").read_bytes() == old.read_bytes()
    assert ((checkout[1] / receipt["location"]) / "ignored/new.txt").read_bytes() == new.read_bytes()
    assert json.loads(archive.read_text())["preserved_artifacts"] == receipt
    assert json.loads((tasks / "output-task.json").read_text()) == hot


def test_record_redispatched_during_copy_refuses_removal_without_updating_new_record(checkout, monkeypatch):
    repo, _, tasks = checkout
    artifact(checkout, "ignored/report.txt")
    other = repo.parent / "other"
    other.mkdir()
    replacement = {"worktree_path": str(other), "status": "running"}
    original = output.artifacts._copy_verified

    def redispatch(src, dst):
        original(src, dst)
        (tasks / "output-task.json").write_text(json.dumps(replacement))

    monkeypatch.setattr(output.artifacts, "_copy_verified", redispatch)
    ok, _, receipt = preserve(checkout, {"status": "done"})
    assert not ok and receipt["count"] == 1 and receipt["retention_disposition"] == "retained"
    assert json.loads((tasks / "output-task.json").read_text()) == replacement


@pytest.mark.parametrize("change", ["corrupt", "extra", "symlink", "other_worktree", "invalid_manifest"])
def test_unverified_previous_copy_is_not_reused(checkout, change):
    artifact(checkout, "ignored/report.txt", b"original")
    ok, _, first = preserve(checkout)
    assert ok
    location = checkout[1] / first["location"]
    if change == "corrupt":
        (location / "ignored/report.txt").write_bytes(b"corrupt!")
    elif change == "extra":
        (location / "extra.txt").write_bytes(b"extra")
    elif change == "symlink":
        (location / "link").symlink_to(checkout[0], target_is_directory=True)
    elif change == "other_worktree":
        manifest = location.with_suffix(".manifest.json")
        saved = json.loads(manifest.read_text())
        saved["worktree_sha256"] = "other"
        manifest.write_text(json.dumps(saved))
    else:
        location.with_suffix(".manifest.json").write_text("not json")
    ok, _, second = preserve(checkout)
    assert ok and not second["reused"] and first["location"] != second["location"]
    assert ((checkout[1] / second["location"]) / "ignored/report.txt").read_bytes() == b"original"


def test_missing_record_identical_retry_remains_retained_without_copy(checkout):
    artifact(checkout, "ignored/report.txt")
    ok, _, first = preserve(checkout, task_id=None)
    assert not ok and first["retention_disposition"] == "retained"
    ok, _, second = preserve(checkout, task_id=None)
    assert not ok and second == first
    assert not (checkout[1] / "batch_state/preserved").exists()


def test_same_bytes_with_different_file_list_get_new_attempt(checkout):
    source = artifact(checkout, "ignored/first.txt", b"same bytes")
    ok, _, first = preserve(checkout)
    assert ok
    source.rename(source.with_name("second.txt"))
    ok, _, second = preserve(checkout)
    assert ok and not second["reused"] and second["location"] != first["location"]
    assert second["content_sha256"] != first["content_sha256"]


def test_same_task_and_bytes_in_another_worktree_get_new_attempt(checkout):
    repo, primary, tasks = checkout
    artifact(checkout, "ignored/report.txt", b"same bytes")
    ok, _, first = preserve(checkout)
    assert ok
    other = repo.parent / "other"
    other.mkdir()
    subprocess.run(["git", "init", str(other)], check=True, capture_output=True, timeout=30)
    (other / ".gitignore").write_text("ignored/\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=other, check=True, capture_output=True, timeout=30)
    artifact((other, primary, tasks), "ignored/report.txt", b"same bytes")
    (tasks / "output-task.json").write_text(json.dumps({"task_id": "output-task", "worktree_path": str(other)}))
    ok, _, second = output.preserve_worktree_artifacts(other, primary=primary, task_id="output-task", tasks_dir=tasks)
    assert ok and not second["reused"] and second["location"] != first["location"]
    assert second["content_sha256"] == first["content_sha256"]


def test_source_change_during_reuse_refuses_removal(checkout, monkeypatch):
    source = artifact(checkout, "ignored/report.txt", b"original")
    assert preserve(checkout)[0]
    original = output._reusable_copy

    def mutate(*args):
        location = original(*args)
        source.write_bytes(b"different")
        return location

    monkeypatch.setattr(output, "_reusable_copy", mutate)
    ok, reason, _ = preserve(checkout)
    assert not ok and "changed during preservation" in reason
    assert source.read_bytes() == b"different"


def test_preservation_error_never_updates_an_unbound_record(checkout, monkeypatch):
    repo, primary, tasks = checkout
    artifact(checkout, "ignored/report.txt", b"old output")
    record = {"worktree_path": str(primary), "started_at": "2999-01-01T00:00:00Z"}
    path = tasks / "output-task.json"
    path.write_text(json.dumps(record))
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 1)
    ok, reason, _ = output.preserve_worktree_artifacts(
        repo, primary=primary, task_id="output-task", tasks_dir=tasks, task_record=record
    )
    assert not ok and "missing canonical task attribution" in reason
    assert json.loads(path.read_text()) == record and "artifact_preservation_error" not in record


def test_manifest_write_failure_retains_sources(checkout, monkeypatch):
    source = artifact(checkout, "ignored/report.txt", b"task output")
    original_open = Path.open

    def fail_receipt(path, *args, **kwargs):
        if path.name.endswith(".manifest.json"):
            raise OSError("receipt denied")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_receipt)
    ok, reason, _ = preserve(checkout)
    assert not ok and "receipt denied" in reason and "refusing worktree removal" in reason
    assert source.read_bytes() == b"task output"


def test_entire_exclusion_is_limited_to_logs(checkout):
    (checkout[0] / ".gitignore").write_text(".entire/\n")
    artifact(checkout, ".entire/logs/diagnostic.log", b"tool state")
    artifact(checkout, ".entire/report.txt", b"task output")
    ok, _, receipt = preserve(checkout)
    assert ok and receipt["count"] == 1
    assert ((checkout[1] / receipt["location"]) / ".entire/report.txt").read_bytes() == b"task output"


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
    assert ((checkout[1] / receipt["location"]) / ".cache/out/answer.txt").read_bytes() == b"task output"
    assert not ((checkout[1] / receipt["location"]) / cache).exists()
