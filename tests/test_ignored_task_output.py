"""Ignored output inventory/copy boundaries, using only temporary repositories."""

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.fleet import regenerable_output as patterns
from tests.orchestration import test_worktree_artifacts as fixtures

checkout = fixtures.checkout
artifact = fixtures.artifact


def tracked_lockfile(repo, directory):
    lock = repo / directory / "package-lock.json"
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text('{"lockfileVersion": 3}')
    subprocess.run(["git", "add", str(lock.relative_to(repo))], cwd=repo, check=True, timeout=30)
    return lock


def published_manifest(checkout, payload=b'{"entries": []}'):
    repo = checkout[0]
    manifest = artifact(checkout, patterns.GENERATED_MANIFEST, payload)
    ignore = repo / ".gitignore"
    ignore.write_text(ignore.read_text() + patterns.GENERATED_MANIFEST + "\n")
    pointer = artifact(
        checkout,
        patterns.MANIFEST_POINTER,
        json.dumps({"json_sha256": hashlib.sha256(payload).hexdigest()}).encode(),
    )
    env = output.artifacts._safe_git_env()
    subprocess.run(
        ["git", "add", "--", patterns.MANIFEST_POINTER, ".gitignore"],
        cwd=repo, env=env, check=True, capture_output=True, timeout=30,
    )
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "Release pointer"],
        cwd=repo, env=env, check=True, capture_output=True, timeout=30,
    )
    return manifest, pointer


@pytest.mark.parametrize(
    "name",
    [
        "node_modules/package/index.js",
        "site/node_modules/package/index.js",
        "nested/app/node_modules/package/index.js",
        *[f"nested/{cache}/state.bin" for cache in sorted(patterns.REGENERABLE_CACHE_DIRECTORIES)],
        patterns.GENERATED_MANIFEST,
    ],
)
def test_regenerable_patterns_skip_fingerprinting_and_cap(checkout, monkeypatch, name):
    repo, primary, _ = checkout
    (repo / ".gitignore").write_text("node_modules/\n__pycache__/\n.*_cache/\n" + patterns.GENERATED_MANIFEST + "\n")
    if "node_modules" in Path(name).parts:
        parent = name.split("node_modules")[0]
        tracked_lockfile(repo, parent)
    artifact(checkout, name, b"0123456789")
    if name == patterns.GENERATED_MANIFEST:
        published_manifest(checkout, b"0123456789")
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 1)
    monkeypatch.setattr(output.artifacts, "_fingerprint", lambda _path: pytest.fail("regenerable bytes read"))
    assert preserve(checkout, {"response": f"Generated `{name}`."}) == (True, "", None)
    assert not (primary / "batch_state/preserved").exists()


def test_mixed_regenerable_paths_preserve_only_output(checkout, monkeypatch):
    repo, primary, _ = checkout
    (repo / ".gitignore").write_text("ignored/\nnode_modules/\n__pycache__/\n" + patterns.GENERATED_MANIFEST + "\n")
    tracked_lockfile(repo, "site")
    artifact(checkout, "site/node_modules/package/index.js", b"x" * 100)
    artifact(checkout, "__pycache__/module.pyc", b"x" * 100)
    published_manifest(checkout, b"x" * 100)
    artifact(checkout, "ignored/answer.txt", b"answer")
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 6)
    ok, reason, receipt = preserve(checkout)
    assert ok and not reason and receipt["bytes"] == 6
    assert [entry["path"] for entry in receipt["paths"]] == ["ignored/answer.txt"]
    assert (primary / receipt["location"] / "ignored/answer.txt").read_bytes() == b"answer"


def test_published_manifest_is_regenerable_and_hashed_once_per_inventory(checkout, monkeypatch):
    repo, primary, _ = checkout
    manifest, _ = published_manifest(checkout)
    original_digest = hashlib.file_digest
    hashes = []

    def count_hashes(handle, algorithm):
        hashes.append(handle.name)
        return original_digest(handle, algorithm)

    monkeypatch.setattr(patterns.hashlib, "file_digest", count_hashes)
    record = {"response": f"Generated `{patterns.GENERATED_MANIFEST}`."}
    assert output._ignored_output_files(repo, primary, record) == []
    assert hashes == [str(manifest)]
    manifest.write_bytes(b'{"entries": ["promoted-by-task"]}')
    assert output._ignored_output_files(repo, primary, record) == [patterns.GENERATED_MANIFEST]
    assert hashes == [str(manifest), str(manifest)]


@pytest.mark.parametrize("named", [False, True], ids=["unnamed", "named-in-report"])
def test_differing_manifest_is_counted_and_preserved(checkout, monkeypatch, named):
    manifest, _ = published_manifest(checkout)
    payload = b'{"entries": ["promoted-by-task"]}'
    manifest.write_bytes(payload)
    record = {"response": f"Output `{patterns.GENERATED_MANIFEST}`."} if named else {}
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", len(payload) - 1)
    ok, reason, receipt = preserve(checkout, record)
    assert not ok and "cap" in reason
    assert receipt["bytes"] == len(payload) and receipt["retention_disposition"] == "retained"
    assert manifest.read_bytes() == payload
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", len(payload))
    ok, reason, receipt = preserve(checkout, record)
    assert ok and not reason and receipt["bytes"] == len(payload)
    assert [entry["path"] for entry in receipt["paths"]] == [patterns.GENERATED_MANIFEST]
    assert (checkout[1] / receipt["location"] / patterns.GENERATED_MANIFEST).read_bytes() == payload


@pytest.mark.parametrize(
    "pointer_kind",
    ["modified", "staged", "staged-restored", "untracked", "absent", "symlink", "invalid-json", "invalid-shape", "missing-hash"],
)
def test_manifest_without_clean_tracked_pointer_is_preserved(checkout, pointer_kind):
    repo, primary, _ = checkout
    manifest, pointer = published_manifest(checkout)
    env = output.artifacts._safe_git_env()
    if pointer_kind in {"modified", "staged", "staged-restored"}:
        published_pointer = pointer.read_bytes()
        pointer.write_bytes(published_pointer + b"\n")
        if pointer_kind in {"staged", "staged-restored"}:
            subprocess.run(
                ["git", "add", "--", patterns.MANIFEST_POINTER],
                cwd=repo, env=env, check=True, capture_output=True, timeout=30,
            )
            if pointer_kind == "staged-restored":
                pointer.write_bytes(published_pointer)
    elif pointer_kind == "untracked":
        subprocess.run(
            ["git", "rm", "--cached", "--", patterns.MANIFEST_POINTER],
            cwd=repo, env=env, check=True, capture_output=True, timeout=30,
        )
    elif pointer_kind == "absent":
        pointer.unlink()
    else:
        if pointer_kind == "symlink":
            target = repo.parent / "release-pointer.json"
            target.write_bytes(pointer.read_bytes())
            pointer.unlink()
            pointer.symlink_to(target)
        else:
            pointer.write_text({"invalid-json": "{", "invalid-shape": "[]", "missing-hash": "{}"}[pointer_kind])
        subprocess.run(
            ["git", "add", "--", patterns.MANIFEST_POINTER],
            cwd=repo, env=env, check=True, capture_output=True, timeout=30,
        )
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "Invalid pointer"],
            cwd=repo, env=env, check=True, capture_output=True, timeout=30,
        )
    ok, reason, receipt = preserve(checkout)
    assert ok and not reason
    assert [entry["path"] for entry in receipt["paths"]] == [patterns.GENERATED_MANIFEST]
    assert (primary / receipt["location"] / patterns.GENERATED_MANIFEST).read_bytes() == manifest.read_bytes()


def test_symlinked_manifest_is_not_regenerable(checkout, monkeypatch):
    repo = checkout[0]
    manifest, _ = published_manifest(checkout)
    target = repo / "tracked-manifest.json"
    target.write_bytes(manifest.read_bytes())
    manifest.unlink()
    manifest.symlink_to(target)
    monkeypatch.setattr(patterns.hashlib, "file_digest", lambda *_: pytest.fail("symlink target hashed"))
    assert not patterns.is_regenerable_ignored_path(
        patterns.GENERATED_MANIFEST, worktree=repo, tracked={patterns.MANIFEST_POINTER}
    )


@pytest.mark.parametrize("lock_kind", ["absent", "untracked", "symlink", "vanished"])
def test_dependencies_without_local_tracked_lock_remain_output(checkout, lock_kind):
    repo, _, _ = checkout
    (repo / ".gitignore").write_text("node_modules/\n")
    lock = repo / "package-lock.json"
    if lock_kind == "untracked":
        lock.write_text("{}")
    elif lock_kind == "vanished":
        tracked_lockfile(repo, "")
        lock.unlink()
    elif lock_kind == "symlink":
        target = repo.parent / "outside-lock.json"
        target.write_text("{}")
        lock.symlink_to(target)
        subprocess.run(["git", "add", "package-lock.json"], cwd=repo, check=True, timeout=30)
    artifact(checkout, "node_modules/package/only-copy.txt", b"task output")
    ok, reason, receipt = preserve(checkout)
    assert ok and not reason
    assert [entry["path"] for entry in receipt["paths"]] == ["node_modules/package/only-copy.txt"]


@pytest.mark.parametrize("name", ["node_modules", "site/node_modules", patterns.GENERATED_MANIFEST])
def test_regenerable_symlinks_never_read_outside(checkout, monkeypatch, name):
    repo, _, _ = checkout
    (repo / ".gitignore").write_text("node_modules\n" + patterns.GENERATED_MANIFEST + "\n")
    outside = repo.parent / "outside"
    outside.mkdir()
    source = outside / "answer.txt"
    source.write_bytes(b"unique outside output")
    link = repo / name
    link.parent.mkdir(parents=True, exist_ok=True)
    if "node_modules" in name:
        tracked_lockfile(repo, link.parent.relative_to(repo))
    link.symlink_to(source if name == patterns.GENERATED_MANIFEST else outside)
    original_open = Path.open

    def no_outside_read(path, *args, **kwargs):
        assert not path.is_relative_to(outside), "outside content opened"
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", no_outside_read)
    ok, reason, _ = preserve(checkout)
    assert not ok and "links outside" in reason
    assert link.is_symlink() and source.stat().st_size == len(b"unique outside output")


def test_regenerable_classifier_keeps_regular_cache_names_and_environment_output(checkout):
    repo = checkout[0]
    artifact(checkout, "__pycache__", b"task output")
    artifact(checkout, ".venv/__pycache__/only-copy.pyc", b"task output")
    for name in ["__pycache__", ".venv/__pycache__/only-copy.pyc", "../outside", "/outside", ""]:
        assert not patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=set())


@pytest.mark.parametrize("move", ["archive", "redispatch", "staging"])
def test_record_moved_between_listing_and_open_retries_complete_inventory(checkout, monkeypatch, capsys, move):
    repo, primary, tasks = checkout
    source = tasks / "output-task.json"
    record = {"task_id": "output-task", "worktree_path": str(repo), "keep_worktree": True}
    source.write_text(json.dumps(record))
    if move in {"archive", "staging"}:
        (tasks / "archive").mkdir()
        destination = tasks / "archive/output-task.json"
    else:
        destination = tasks / "output-task.20261006T020000Z.archived.json"
    original_read = Path.read_bytes
    original_glob = Path.glob
    moved = False
    staged = tasks / ".output-task.json.moving"

    def finish_staging(path, pattern):
        # The archive writer publishes after the first failed open, before
        # the second listing. The missing name must not be silently skipped.
        if path == tasks and pattern == "*.json" and move == "staging" and staged.exists():
            staged.replace(destination)
        return original_glob(path, pattern)

    def race(path):
        nonlocal moved
        if path == source and not moved:
            moved = True
            source.replace(staged if move == "staging" else destination)
        return original_read(path)  # The real ENOENT from a stale glob entry.

    monkeypatch.setattr(Path, "read_bytes", race)
    monkeypatch.setattr(Path, "glob", finish_staging)
    assert output.resolve_worktree_record(repo, tasks, repo_root=primary) == (destination, record)
    assert "retrying complete inventory once" in capsys.readouterr().err


@pytest.mark.parametrize("failure", ["vanished", "permission", "corrupt"])
def test_unreadable_inventory_still_fails_closed_after_bounded_retry(checkout, monkeypatch, capsys, failure):
    repo, primary, tasks = checkout
    source = tasks / "output-task.json"
    source.write_text(json.dumps({"worktree_path": str(repo), "keep_worktree": True}))
    original_read = Path.read_bytes
    reads = 0

    def unreadable(path):
        nonlocal reads
        if path == source:
            reads += 1
            if failure == "vanished":
                source.unlink()
            elif failure == "permission":
                raise PermissionError("inventory denied")
            else:
                return b'{"keep_worktree": true,'
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", unreadable)
    with pytest.raises(ValueError, match="task identity inventory unreadable"):
        output.resolve_worktree_record(repo, tasks, repo_root=primary)
    assert reads == (1 if failure == "vanished" else 2)
    assert capsys.readouterr().err.count("retrying complete inventory once") == 1


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


@pytest.mark.parametrize(
    "variant",
    [
        "same_task",
        "different_task",
        "missing_id",
        "missing_creator",
        "two_creators",
        "not_force_new",
        "wrong_prefix",
        "extra_prefix",
        "keep_archive",
        "keep_current",
        "keep_both",
    ],
)
def test_force_new_reuse_requires_one_same_task_archived_creator(checkout, variant):
    repo, primary, tasks = checkout
    source = artifact(checkout, "ignored/report.txt", b"redispatched output")
    current = {"task_id": "output-task", "worktree_path": str(repo), "worktree_reused": True, "status": "done"}
    creator = dict(current, worktree_reused=False, status="cancelled")
    archive_name = "output-task.20261005T120000Z.archived.json"
    if variant == "different_task":
        creator["task_id"] = "other-task"
        archive_name = "other-task.20261005T120000Z.archived.json"
    elif variant == "missing_id":
        creator.pop("task_id")
    elif variant == "missing_creator":
        creator["worktree_reused"] = True
    elif variant == "not_force_new":
        archive_name = "output-task.old.json"
    elif variant == "wrong_prefix":
        archive_name = "other-task.20261005T120000Z.archived.json"
    elif variant == "extra_prefix":
        archive_name = "output-task.extra.20261005T120000Z.archived.json"
    if variant in {"keep_archive", "keep_both"}:
        creator["keep_worktree"] = True
    if variant in {"keep_current", "keep_both"}:
        current["keep_worktree"] = True
    canonical = tasks / "output-task.json"
    canonical.write_text(json.dumps(current))
    archive = tasks / archive_name
    archive.write_text(json.dumps(creator))
    if variant == "two_creators":
        (tasks / "output-task.20261005T130000Z.archived.json").write_text(json.dumps(creator))
    for _ in range(2):  # Exercise both fresh and content-verified cached lookups.
        if variant == "keep_both":
            with pytest.raises(ValueError, match="retention intent"):
                output.resolve_worktree_record(repo, tasks, repo_root=primary)
            continue
        path, record = output.resolve_worktree_record(repo, tasks, repo_root=primary)
        if variant == "same_task":
            assert path == canonical and record == current
    ok, reason, receipt = output.preserve_worktree_artifacts(repo, primary=primary, task_id=None, tasks_dir=tasks)
    assert source.read_bytes() == b"redispatched output"
    if variant == "same_task":
        assert ok and not reason and receipt["task_id"] == "output-task"
        assert output.verify_retrieval(primary, receipt) == receipt["content_sha256"]
        assert json.loads(canonical.read_text())["preserved_artifacts"] == receipt
        assert json.loads(archive.read_text()) == creator
    else:
        assert not ok and "refusing worktree removal" in reason


@pytest.mark.parametrize("stage", ["git_inventory", "after_lstat", "fingerprint", "copy"])
def test_vanished_output_is_rechecked_and_recorded_absent(checkout, monkeypatch, stage):
    _, primary, tasks = checkout
    missing = artifact(checkout, "ignored/vanished.txt", b"transient")
    survivor = artifact(checkout, "ignored/report.txt", b"retain these bytes")
    if stage == "git_inventory":
        original = output.artifacts._git_paths

        def stale_inventory(*args):
            names = original(*args)
            if "ignored/vanished.txt" in names:
                missing.unlink(missing_ok=True)
            return names

        monkeypatch.setattr(output.artifacts, "_git_paths", stale_inventory)
    elif stage == "after_lstat":
        original = Path.resolve

        def vanish_after_lstat(path, *args, **kwargs):
            if path == missing:
                missing.unlink(missing_ok=True)
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, "resolve", vanish_after_lstat)
    else:
        name = "_fingerprint" if stage == "fingerprint" else "_copy_verified"
        original = getattr(output.artifacts, name)

        def disappear(src, *args):
            if src == missing:
                missing.unlink(missing_ok=True)
            return original(src, *args)

        monkeypatch.setattr(output.artifacts, name, disappear)
    ok, reason, receipt = preserve(checkout, {"status": "done"})
    assert ok and not reason
    assert receipt["count"] == 1 and receipt["bytes"] == len(survivor.read_bytes())
    assert receipt["absent_paths"] == [{"path": "ignored/vanished.txt", "proof": "lstat_enoent"}]
    assert (primary / receipt["location"] / "ignored/report.txt").read_bytes() == survivor.read_bytes()
    assert output.verify_retrieval(primary, receipt) == receipt["retrieval_proof_sha256"]
    assert json.loads((tasks / "output-task.json").read_text())["preserved_artifacts"] == receipt


def test_vanished_pids_directory_after_git_inventory(checkout, monkeypatch):
    repo, _, _ = checkout
    (repo / ".gitignore").write_text(".pids/\nignored/\n")
    pids = repo / ".pids"
    pids.mkdir()
    original = output.artifacts._git_paths

    def stale_inventory(*args):
        names = original(*args)
        if "--ignored" in args:
            pids.rmdir()
            names.append(".pids/")
        return names

    # Only the first Git inventory is stale; the final inventory is fresh.
    calls = 0

    def once(*args):
        nonlocal calls
        if "--ignored" in args and calls == 0:
            calls += 1
            return stale_inventory(*args)
        return original(*args)

    monkeypatch.setattr(output.artifacts, "_git_paths", once)
    ok, reason, receipt = preserve(checkout, {"status": "done"})
    assert ok and not reason and receipt["count"] == 0
    assert receipt["absent_paths"] == [{"path": ".pids/", "proof": "lstat_enoent"}]


@pytest.mark.parametrize("failure", ["changed_before_copy", "false_enoent", "reappeared", "permission"])
def test_disappearance_neighbours_refuse_removal(checkout, monkeypatch, failure):
    source = artifact(checkout, "ignored/report.txt", b"original")
    original = output.artifacts._copy_verified

    def copy(src, dst):
        if failure == "changed_before_copy":
            source.write_bytes(b"modified")
        elif failure == "false_enoent":
            raise FileNotFoundError("destination vanished")
        elif failure == "permission":
            raise PermissionError("copy denied")
        else:
            source.unlink()
            raise FileNotFoundError("source vanished")
        original(src, dst)

    monkeypatch.setattr(output.artifacts, "_copy_verified", copy)
    if failure == "reappeared":
        inventory = output._ignored_output_files
        calls = 0

        def reappear(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                source.write_bytes(b"new output")
            return inventory(*args, **kwargs)

        monkeypatch.setattr(output, "_ignored_output_files", reappear)
    ok, reason, receipt = preserve(checkout, {"status": "done"})
    assert not ok and "refusing worktree removal" in reason
    assert receipt["retention_disposition"] == "retained"
    assert source.exists()


def test_dangling_link_is_not_absence_proof(checkout):
    repo, _, _ = checkout
    (repo / ".gitignore").write_text(".pids\n")
    (repo / ".pids").symlink_to(repo.parent / "missing-outside-target")
    ok, reason, _ = preserve(checkout, {"status": "done"})
    assert not ok and "changed during preservation" in reason
    assert (repo / ".pids").is_symlink()


def test_internal_release_link_to_vanished_pids_records_target_absence(checkout):
    repo, primary, _ = checkout
    (repo / ".gitignore").write_text(".runtime/\nignored/\n")
    release = repo / ".runtime/api/releases/test-release"
    release.mkdir(parents=True)
    link = release / ".pids"
    link.symlink_to(repo / ".pids")
    source = artifact(checkout, "ignored/report.txt", b"preserve this")
    ok, reason, receipt = preserve(checkout, {"status": "done"})
    assert ok and not reason and receipt["count"] == 1
    assert receipt["absent_paths"] == [{"path": ".pids", "proof": "lstat_enoent"}]
    assert link.is_symlink() and source.exists()
    assert output.verify_retrieval(primary, receipt) == receipt["retrieval_proof_sha256"]


def test_sole_creator_wins_with_different_task_reuser_without_retention(checkout):
    repo, primary, tasks = checkout
    source = artifact(checkout, "ignored/report.txt")
    creator = {"task_id": "output-task", "worktree_path": str(repo), "worktree_reused": False, "status": "done"}
    canonical = tasks / "output-task.json"
    canonical.write_text(json.dumps(creator))
    reuser = dict(creator, task_id="other-task", worktree_reused=True)
    reused_record = tasks / "other-task.json"
    reused_record.write_text(json.dumps(reuser))
    for _ in range(2):  # Exercise both fresh and content-verified cached lookups.
        assert output.resolve_worktree_record(repo, tasks, repo_root=primary) == (canonical, creator)
    ok, reason, receipt = output.preserve_worktree_artifacts(repo, primary=primary, tasks_dir=tasks, task_id=None)
    assert ok and not reason and receipt["task_id"] == "output-task"
    assert (primary / receipt["location"] / "ignored/report.txt").read_bytes() == source.read_bytes()
    assert output.verify_retrieval(primary, receipt) == receipt["content_sha256"]
    assert json.loads(canonical.read_text())["preserved_artifacts"] == receipt
    assert json.loads(reused_record.read_text()) == reuser


@pytest.mark.parametrize("case", ["force_new", "vanished_copy", "internal_link", "changed_copy"])
def test_normal_removal_preserves_or_proves_absence_under_existing_lock(tmp_path, monkeypatch, case):
    from scripts.orchestration import worktree_claims as claims
    from tests.orchestration.test_worktree_claims_cli import _linked, _primary, _record

    primary = _primary(tmp_path)
    tree = _linked(primary, "codex/output-task")
    (primary / ".git/info/exclude").write_text("ignored/\n.runtime/\n.pids/\n")
    source = tree / "ignored/report.txt"
    source.parent.mkdir()
    source.write_bytes(b"preserve me")
    _record(primary, "output-task", status="done", worktree_path=str(tree), worktree_reused=True)
    if case == "force_new":
        archive = primary / "batch_state/tasks/output-task.20261005T120000Z.archived.json"
        archive.write_text(
            json.dumps(
                {"task_id": "output-task", "status": "cancelled", "worktree_path": str(tree), "worktree_reused": False}
            )
        )
    elif case == "internal_link":
        release = tree / ".runtime/api/releases/test-release"
        release.mkdir(parents=True)
        (release / ".pids").symlink_to(tree / ".pids")
    else:
        transient = tree / "ignored/transient.txt"
        transient.write_bytes(b"transient")
        original = output.artifacts._copy_verified

        def copy(src, dst):
            if src == transient:
                if case == "vanished_copy":
                    transient.unlink()
                else:
                    transient.write_bytes(b"modified")
            original(src, dst)

        monkeypatch.setattr(output.artifacts, "_copy_verified", copy)
    record_absence = output._record_absence

    def locked_absence(*args):
        with pytest.raises(claims.WorktreeLockReentry):
            with claims.worktree_lock(tree, lock_dir=claims.repository_lock_dir(primary)):
                pytest.fail("absence proof was taken outside the existing worktree lock")
        record_absence(*args)

    monkeypatch.setattr(output, "_record_absence", locked_absence)
    result = claims.remove_unclaimed_worktree(
        tree, repo_root=primary, reason="test #9785", owner_task_id=None, force=True
    )
    if case == "changed_copy":
        assert result.action == "skipped" and tree.exists()
        assert "changed during preservation" in result.reason
        return
    assert result.action == "removed" and not tree.exists()
    record = json.loads((primary / "batch_state/tasks/output-task.json").read_text())
    receipt = record["preserved_artifacts"]
    assert (primary / receipt["location"] / "ignored/report.txt").read_bytes() == b"preserve me"
    assert output.verify_retrieval(primary, receipt) == receipt["retrieval_proof_sha256"]
    if case == "vanished_copy":
        assert receipt["absent_paths"] == [{"path": "ignored/transient.txt", "proof": "lstat_enoent"}]
    elif case == "internal_link":
        assert receipt["absent_paths"] == [{"path": ".pids", "proof": "lstat_enoent"}]


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
