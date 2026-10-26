"""Record-only output inventories and custody guards in temporary repositories."""

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
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree
from tests.test_continuation_worktree_reap import abandon_cohort as abandon_cohort
from tests.test_continuation_worktree_reap import same_branch_pending_cohort as same_branch_pending_cohort
from tests.test_reused_worktree_retention import cohort as cohort

checkout = fixtures.checkout
artifact = fixtures.artifact


def assert_entry(receipt, name, payload):
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
    assert "location" not in receipt
    assert next(entry for entry in receipt["paths"] if entry["path"] == name) == {
        "path": name,
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def tracked_lockfile(repo, directory):
    lock = repo / directory / "package-lock.json"
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text('{"lockfileVersion": 3}')
    subprocess.run(["git", "add", str(lock.relative_to(repo))], cwd=repo, check=True, timeout=30)
    return lock


@pytest.mark.parametrize(
    "name",
    [
        "node_modules/package/index.js",
        "site/node_modules/package/index.js",
        "nested/app/node_modules/package/index.js",
        *[f"nested/{cache}/state.bin" for cache in sorted(patterns.REGENERABLE_CACHE_DIRECTORIES)],
    ],
)
def test_regenerable_patterns_skip_fingerprinting_and_cap(checkout, monkeypatch, name):
    repo, primary, _ = checkout
    (repo / ".gitignore").write_text("node_modules/\n__pycache__/\n.*_cache/\n")
    if "node_modules" in Path(name).parts:
        parent = name.split("node_modules")[0]
        tracked_lockfile(repo, parent)
    artifact(checkout, name, b"0123456789")
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 1)
    monkeypatch.setattr(
        output.artifacts, "_fingerprint", lambda _path, **_kwargs: pytest.fail("regenerable bytes read")
    )
    assert preserve(checkout, {"response": f"Generated `{name}`."}) == (True, "", None)
    assert not (primary / "batch_state/preserved").exists()


@pytest.mark.parametrize("payload", [b'{"entries": []}', b'{"entries": ["promoted"]}', b"arbitrary bytes"])
@pytest.mark.parametrize(
    "pointer_kind",
    ["clean", "modified", "staged", "staged-restored", "untracked", "absent", "symlink", "invalid-json"],
)
@pytest.mark.parametrize("named", [False, True], ids=["unnamed", "named-in-report"])
def test_lexicon_manifest_is_counted_and_preserved_as_ignored_output(
    checkout, monkeypatch, payload, pointer_kind, named
):
    repo, primary, _ = checkout
    name = "site/src/data/lexicon-manifest.json"
    pointer_name = "site/src/data/lexicon-manifest.pointer.json"
    manifest = artifact(checkout, name, payload)
    (repo / ".gitignore").write_text(name + "\n")
    pointer = artifact(
        checkout, pointer_name, json.dumps({"json_sha256": hashlib.sha256(payload).hexdigest()}).encode()
    )
    env = output.artifacts._safe_git_env()

    def git(*args):
        subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True, timeout=30)

    git("add", "--", pointer_name, ".gitignore")
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "Fixture pointer")
    if pointer_kind in {"modified", "staged", "staged-restored"}:
        original = pointer.read_bytes()
        pointer.write_bytes(original + b"\n")
        if pointer_kind in {"staged", "staged-restored"}:
            git("add", "--", pointer_name)
        if pointer_kind == "staged-restored":
            pointer.write_bytes(original)
    elif pointer_kind == "untracked":
        git("rm", "--cached", "--", pointer_name)
    elif pointer_kind == "absent":
        pointer.unlink()
    elif pointer_kind == "symlink":
        target = repo.parent / "outside-pointer.json"
        target.write_bytes(pointer.read_bytes())
        pointer.unlink()
        pointer.symlink_to(target)
    elif pointer_kind == "invalid-json":
        pointer.write_bytes(b"{")

    record = {"response": f"Output `{name}`."} if named else {}
    assert output._ignored_output_files(repo, primary, record) == [name]
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", len(payload) - 1)
    ok, reason, receipt = preserve(checkout, record)
    assert ok and not reason
    assert receipt["paths_truncated"]
    assert receipt["count"] == (2 if pointer_kind == "untracked" else 1)
    assert receipt["bytes"] == len(payload) + (pointer.stat().st_size if pointer_kind == "untracked" else 0)
    assert receipt["retention_disposition"] == "record-only"
    assert manifest.read_bytes() == payload
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 4096)
    ok, reason, receipt = preserve(checkout, record)
    assert ok and not reason
    assert receipt["count"] == (2 if pointer_kind == "untracked" else 1)
    assert receipt["bytes"] == len(payload) + (pointer.stat().st_size if pointer_kind == "untracked" else 0)
    assert [entry["path"] for entry in receipt["paths"]] == sorted(
        [name, pointer_name] if pointer_kind == "untracked" else [name]
    )
    assert_entry(receipt, name, payload)


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
    assert [entry["path"] for entry in receipt["paths"]] == (
        ["node_modules/package/only-copy.txt", "package-lock.json"]
        if lock_kind == "untracked"
        else ["node_modules/package/only-copy.txt"]
    )


@pytest.mark.parametrize("name", ["node_modules", "site/node_modules", "site/src/data/lexicon-manifest.json"])
def test_ignored_symlinks_never_read_outside(checkout, monkeypatch, name):
    repo, primary, _ = checkout
    (repo / ".gitignore").write_text("node_modules\nsite/src/data/lexicon-manifest.json\n")
    outside = repo.parent / "outside"
    outside.mkdir()
    source = outside / "answer.txt"
    source.write_bytes(b"unique outside output")
    link = repo / name
    link.parent.mkdir(parents=True, exist_ok=True)
    if "node_modules" in name:
        tracked_lockfile(repo, link.parent.relative_to(repo))
    link.symlink_to(source if name == "site/src/data/lexicon-manifest.json" else outside)
    original = os.open

    def no_follow(path, flags, *args, **kwargs):
        if str(path) == link.name:
            assert flags & os.O_NOFOLLOW
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", no_follow)
    ok, reason, receipt = preserve(checkout)
    assert ok and not reason
    assert receipt["inventory_error"] == "inventory_incomplete"
    assert name not in {entry["path"] for entry in receipt["paths"]}
    assert not (primary / "batch_state/preserved").exists()
    assert link.is_symlink() and source.read_bytes() == b"unique outside output"


def test_regenerable_classifier_keeps_regular_cache_names_and_environment_output(checkout):
    repo = checkout[0]
    artifact(checkout, "__pycache__", b"task output")
    artifact(checkout, ".venv/__pycache__/only-copy.pyc", b"task output")
    for name in ["__pycache__", ".venv/__pycache__/only-copy.pyc", "../outside", "/outside", ""]:
        assert not patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=set())


@pytest.mark.parametrize("move", ["archive", "redispatch", "staging"])
@pytest.mark.parametrize("publish_cache", [True, False])
def test_record_moved_between_listing_and_open_retries_complete_inventory(
    checkout, monkeypatch, capsys, move, publish_cache
):
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
    assert output.resolve_worktree_record(repo, tasks, repo_root=primary, publish_cache=publish_cache) == (
        destination,
        record,
    )
    assert output._identity_cache_path(tasks).exists() is publish_cache
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


@pytest.mark.parametrize("empty_index", [False, True])
@pytest.mark.parametrize("returncode", [0, 128])
def test_preservation_uses_isolated_environment_for_all_inventory(checkout, monkeypatch, empty_index, returncode):
    repo, primary, tasks = checkout
    name = "ignored/answer.txt"
    payload = b"preserved answer"
    artifact(checkout, name, payload)
    if empty_index:
        subprocess.run(["git", "read-tree", "--empty"], cwd=repo, check=True, timeout=30)
    record = {"task_id": "output-task", "worktree_path": str(repo), "response": f"Saved `{name}`."}
    (tasks / "output-task.json").write_text(json.dumps(record))
    run = output.artifacts.safe_git
    calls = []

    def runner(args, **kwargs):
        assert kwargs["env"] == output.artifacts._safe_git_env()
        calls.append((kwargs["cwd"], args))
        if returncode:
            raise subprocess.CalledProcessError(returncode, args, stderr="inventory unavailable")
        return run(args, **kwargs)

    monkeypatch.setattr(output.artifacts, "safe_git", runner)
    ok, reason, receipt = output.preserve_worktree_artifacts(
        repo, primary=primary, task_id="output-task", tasks_dir=tasks
    )
    assert calls and all(cwd == repo for cwd, _ in calls)
    if returncode:
        assert ok and not reason
        assert receipt["inventory_error"] == "inventory_failed"
        assert (repo / name).read_bytes() == payload
        assert not (primary / "batch_state/preserved").exists()
    else:
        assert ok and not reason
        assert_entry(receipt, name, payload)
        named_probe = ["ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--", name]
        assert sum(args == named_probe for _, args in calls) == 1  # One record-only inventory.
        if empty_index:
            assert_entry(receipt, ".gitignore", (repo / ".gitignore").read_bytes())


@pytest.mark.parametrize("status", ["done", "no_deliverable", "failed"])
def test_all_ignored_output_preserved_without_response_names(checkout, status):
    repo, _, tasks = checkout
    (repo / ".gitignore").write_text(".cache/\nignored/\n")
    artifact(checkout, ".cache/transcriptions/page.txt", b"transcription")
    artifact(checkout, "ignored/empty.txt", b"")
    ok, reason, receipt = preserve(checkout, {"status": status, "started_at": "2000-01-01T00:00:00Z"})
    assert ok and not reason
    assert receipt["count"] == 2 and receipt["bytes"] == 13
    assert_entry(receipt, ".cache/transcriptions/page.txt", b"transcription")
    assert_entry(receipt, "ignored/empty.txt", b"")
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
    assert_entry(receipt, "ignored/old.txt", old.read_bytes())
    assert_entry(receipt, "ignored/modified.txt", modified.read_bytes())
    assert receipt["retrieval_proof_sha256"] == receipt["content_sha256"]
    assert receipt["retention_disposition"] == "record-only"
    assert all("class" not in entry for entry in receipt["paths"])
    assert str(checkout[0]) not in json.dumps(receipt)


@pytest.mark.parametrize("failure", ["cap", "copy", "record", "inventory", "changed", "added"])
def test_residue_failures_allow_disposal_without_copying_sources(checkout, monkeypatch, failure):
    source = artifact(checkout, "ignored/report.txt", b"task output")
    if failure == "cap":
        monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 10)
    elif failure == "inventory":
        monkeypatch.setattr(output.artifacts, "_git_paths", lambda *args: (_ for _ in ()).throw(OSError()))
    elif failure == "record":
        monkeypatch.setattr(
            output.artifacts.reaper_lifecycle, "_atomic_write", lambda *a: (_ for _ in ()).throw(OSError())
        )
    else:
        monkeypatch.setattr(output.artifacts, "_copy_verified", lambda *a, **kw: pytest.fail("residue copied"))
    ok, reason, receipt = preserve(checkout, {"status": "done"})
    assert ok and not reason
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
    if failure == "cap":
        assert receipt["paths_truncated"]
    elif failure == "inventory":
        assert receipt["inventory_error"] == "inventory_failed"
    elif failure == "record":
        assert receipt["receipt_publication_error"]
    else:
        assert_entry(receipt, "ignored/report.txt", b"task output")
    assert source.read_bytes() == b"task output"
    assert not (checkout[1] / "batch_state/preserved").exists()


def test_missing_record_retains_unknown_output_without_fallback_attribution(checkout):
    artifact(checkout, "ignored/report.txt")
    ok, _, receipt = preserve(checkout, task_id=None)
    assert not ok
    assert receipt["retention_disposition"] == "retained"
    assert receipt["owner"] == "infra lane"
    assert not (checkout[1] / "batch_state/preserved").exists()


def test_touch_old_mtime_during_task_is_preserved(checkout):
    started = datetime.now(UTC)
    source = artifact(checkout, "ignored/touched.txt", b"new task output")
    subprocess.run(["touch", "-d", "2000-01-01 UTC", str(source)], check=True, timeout=30)
    assert source.stat().st_mtime < started.timestamp() <= source.stat().st_ctime
    ok, _, receipt = preserve(checkout, {"started_at": started.isoformat()})
    assert ok and receipt["count"] == 1
    assert_entry(receipt, "ignored/touched.txt", b"new task output")


def test_retry_records_new_digest_without_mutating_first_receipt(checkout):
    source = artifact(checkout, "ignored/report.txt", b"first attempt")
    ok, _, first = preserve(checkout, {"status": "done"})
    assert ok
    source.write_bytes(b"second attempt")
    ok, _, second = preserve(checkout)
    assert ok and first["inventory_sha256"] != second["inventory_sha256"]
    assert_entry(first, "ignored/report.txt", b"first attempt")
    assert_entry(second, "ignored/report.txt", b"second attempt")
    assert json.loads((checkout[2] / "output-task.json").read_text())["preserved_artifacts"] == second


def test_retry_records_identical_inventory_without_copying(checkout, monkeypatch):
    artifact(checkout, "ignored/report.txt", b"same attempt")
    ok, _, first = preserve(checkout, {"status": "done"})
    assert ok and first["copied_bytes"] == 0
    monkeypatch.setattr(
        output.artifacts,
        "_copy_verified",
        lambda *_args, **_kwargs: pytest.fail("identical output copied again"),
    )
    ok, _, second = preserve(checkout)
    assert ok and second["inventory_sha256"] == first["inventory_sha256"]
    assert "location" not in second and second["copied_bytes"] == 0
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
    if binding in {"cwd", "alias"}:
        assert ok
        assert_entry(receipt, "ignored/old.txt", b"old output")
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
    assert ok and receipt["count"] == 2 and receipt["copied_bytes"] == 0
    assert_entry(receipt, "ignored/old.txt", old.read_bytes())
    assert_entry(receipt, "ignored/new.txt", new.read_bytes())
    assert json.loads(archive.read_text())["preserved_artifacts"] == receipt
    assert json.loads((tasks / "output-task.json").read_text()) == hot


def test_record_redispatched_during_inventory_refuses_removal_without_updating_new_record(checkout, monkeypatch):
    repo, _, tasks = checkout
    artifact(checkout, "ignored/report.txt")
    other = repo.parent / "other"
    other.mkdir()
    replacement = {"worktree_path": str(other), "status": "running"}
    original = output.record_only_receipt

    def redispatch(*args, **kwargs):
        result = original(*args, **kwargs)
        (tasks / "output-task.json").write_text(json.dumps(replacement))
        return result

    monkeypatch.setattr(output, "record_only_receipt", redispatch)
    ok, reason, receipt = preserve(checkout, {"status": "done"})
    assert not ok and receipt["count"] == 1
    assert receipt["retention_disposition"] == "retained"
    assert "task-state guard failed" in reason
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
    baseline = output.creation_inventory(repo, primary=primary, task_id="output-task", run_nonce="creator-run")
    source = artifact(checkout, "ignored/report.txt", b"redispatched output")
    current = {"task_id": "output-task", "worktree_path": str(repo), "worktree_reused": True, "status": "done"}
    creator = dict(current, worktree_reused=False, status="cancelled", ignored_output_baseline=baseline)
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
        # Retention now requires a resolved branch shared by creator and successor.
        # This uncommitted fixture intentionally has no such branch evidence.
        if variant not in {"same_task", "missing_creator"}:
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
        assert not ok and "task-state guard failed" in reason


@pytest.mark.parametrize("stage", ["git_inventory", "after_lstat", "fingerprint", "copy"])
def test_vanished_output_is_omitted_without_blocking_disposal(checkout, monkeypatch, stage):
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
    else:
        original = os.open

        def disappear(path, *args, **kwargs):
            if str(path) == missing.name:
                missing.unlink(missing_ok=True)
            return original(path, *args, **kwargs)

        monkeypatch.setattr(os, "open", disappear)
    ok, reason, receipt = preserve(checkout, {"status": "done"})
    assert ok and not reason
    assert receipt["count"] == 1 and receipt["bytes"] == len(survivor.read_bytes())
    assert_entry(receipt, "ignored/report.txt", b"retain these bytes")
    assert not (primary / "batch_state/preserved").exists()
    assert json.loads((tasks / "output-task.json").read_text())["preserved_artifacts"] == receipt


@pytest.mark.parametrize("failure", ["changed_before_copy", "false_enoent", "reappeared", "permission"])
def test_inventory_read_errors_do_not_block_disposal(checkout, monkeypatch, failure):
    source = artifact(checkout, "ignored/report.txt", b"original")
    original = os.open

    def changed(path, *args, **kwargs):
        if str(path) == source.name:
            if failure == "changed_before_copy":
                source.write_bytes(b"modified")
            elif failure == "false_enoent":
                raise FileNotFoundError("fixture")
            elif failure == "permission":
                raise PermissionError("fixture")
            else:
                source.unlink(missing_ok=True)
                source.write_bytes(b"new output")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", changed)
    ok, reason, receipt = preserve(checkout, {"status": "done"})
    assert ok and not reason
    if failure in {"false_enoent", "permission"}:
        assert receipt["inventory_error"] == "inventory_incomplete"
    else:
        assert_entry(receipt, "ignored/report.txt", b"modified" if failure == "changed_before_copy" else b"new output")
    assert source.exists() and not (checkout[1] / "batch_state/preserved").exists()


@pytest.mark.parametrize("kind", ["directory-inside", "file-inside", "relative", "dangling", "outside"])
def test_ignored_output_symlink_is_omitted_from_record_only_receipt(checkout, monkeypatch, kind):
    """Record-only inventory never follows or publishes symlink targets."""
    repo, primary, _ = checkout
    payload = b"payload-not-copied-through-link"
    outside = repo.parent / "outside-target"
    if kind == "outside":
        outside.write_bytes(payload)
        link = repo / "ignored/outside-link"
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(outside)
        expected = str(outside)
    elif kind == "dangling":
        link = repo / "ignored/dangling"
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to("missing-target")
        expected = "missing-target"
    elif kind == "relative":
        (repo / "ignored/releases/sha").mkdir(parents=True)
        (repo / "ignored/releases/sha/file.txt").write_bytes(b"snapshot")
        link = repo / "ignored/releases/current"
        link.symlink_to("sha", target_is_directory=True)
        expected = "sha"
    elif kind == "file-inside":
        target = repo / "ignored/note.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        link = repo / "ignored/note-link"
        link.symlink_to("note.txt")
        expected = "note.txt"
    else:
        target_dir = repo / "ignored/site"
        target_dir.mkdir(parents=True)
        (target_dir / "marker.txt").write_bytes(payload)
        link = repo / "ignored/site-link"
        link.symlink_to(target_dir, target_is_directory=True)
        expected = str(target_dir)
    outside_before = outside.read_bytes() if kind == "outside" else None
    if kind == "outside":
        original_open = Path.open

        def no_outside_read(path, *args, **kwargs):
            assert not Path(path).is_relative_to(outside), "followed symlink"
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr(Path, "open", no_outside_read)
    ok, reason, receipt = preserve(checkout, {"status": "done"})
    if kind == "outside":
        monkeypatch.undo()
    assert ok and not reason, reason
    relative = link.relative_to(repo).as_posix()
    assert relative not in {item["path"] for item in receipt["paths"]}
    assert receipt["inventory_error"] == "inventory_incomplete"
    assert receipt["copied_bytes"] == 0
    assert not (primary / "batch_state/preserved").exists()
    assert link.is_symlink() and os.readlink(link) == expected
    if kind == "outside":
        assert outside.read_bytes() == outside_before == payload
    elif kind == "directory-inside":
        assert_entry(receipt, "ignored/site/marker.txt", payload)
    elif kind == "file-inside":
        assert_entry(receipt, "ignored/note.txt", payload)
    elif kind == "relative":
        assert_entry(receipt, "ignored/releases/sha/file.txt", b"snapshot")


def test_swapped_ancestor_cannot_publish_an_outside_symlink_target(checkout, monkeypatch, tmp_path):
    """Swapping an ancestor before the descriptor walk cannot expose its target."""
    repo, _primary, tasks = checkout
    gitignore = repo / ".gitignore"
    gitignore.write_text(gitignore.read_text() + "out/\n")
    link = repo / "out" / "lnk"
    link.parent.mkdir()
    link.symlink_to("inside-target")
    outside = tmp_path / "outside-dir"
    outside.mkdir()
    outside_target = "/OUTSIDE/secret-target"
    (outside / "lnk").symlink_to(outside_target)
    real_walk = output.artifacts._walk_parent
    swapped = False

    def swap_before_walk(fd, parts):
        nonlocal swapped
        if not swapped and parts == ("out",):
            swapped = True
            out = repo / "out"
            os.rename(out, tmp_path / "real-out")
            out.symlink_to(outside, target_is_directory=True)
        return real_walk(fd, parts)

    monkeypatch.setattr(output.artifacts, "_walk_parent", swap_before_walk)
    ok, reason, metadata = preserve(checkout, {"status": "done"})
    assert swapped and ok and not reason
    assert metadata["inventory_error"] == "inventory_incomplete"
    assert not metadata["paths"]
    published = json.dumps(metadata) + (tasks / "output-task.json").read_text()
    assert outside_target not in published


def test_removal_does_not_follow_symlink(tmp_path):
    from scripts.orchestration import worktree_claims as claims
    from tests.orchestration.test_worktree_claims_cli import _linked, _primary, _record

    primary = _primary(tmp_path)
    tree = _linked(primary, "codex/output-task")
    (primary / ".git/info/exclude").write_text("ignored/\n")
    outside = tmp_path / "outside-dir"
    outside.mkdir()
    marker = outside / "marker.txt"
    marker.write_bytes(b"do-not-follow")
    identity = marker.stat().st_ino
    link = tree / "ignored/outside"
    link.parent.mkdir()
    link.symlink_to(outside, target_is_directory=True)
    (tree / "ignored/report.txt").write_bytes(b"preserve me")
    _record(primary, "output-task", status="done", worktree_path=str(tree), worktree_reused=True)
    result = claims.remove_unclaimed_worktree(
        tree, repo_root=primary, reason="test #9889", owner_task_id=None, force=True
    )
    assert result.action == "removed", result.reason
    assert not tree.exists()
    assert outside.is_dir() and marker.read_bytes() == b"do-not-follow" and marker.stat().st_ino == identity
    record = json.loads((primary / "batch_state/tasks/output-task.json").read_text())
    receipt = record["preserved_artifacts"]
    assert receipt["inventory_error"] == "inventory_incomplete"
    assert "ignored/outside" not in {entry["path"] for entry in receipt["paths"]}
    assert_entry(receipt, "ignored/report.txt", b"preserve me")
    assert not (primary / "batch_state/preserved").exists()


def test_sole_creator_wins_with_different_task_reuser_without_retention(checkout):
    from tests.orchestration.test_worktree_claims_cli import _git

    repo, primary, tasks = checkout
    baseline = output.creation_inventory(repo, primary=primary, task_id="output-task", run_nonce="creator-run")
    source = artifact(checkout, "ignored/report.txt")
    _git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "branch proof")
    creator = {
        "task_id": "output-task",
        "worktree_path": str(repo),
        "worktree_reused": False,
        "status": "done",
        "run_nonce": "creator-run",
        "ignored_output_baseline": baseline,
        "worktree_branch": _git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
    }
    canonical = tasks / "output-task.json"
    canonical.write_text(json.dumps(creator))
    reuser = dict(creator, task_id="other-task", worktree_reused=True, run_nonce="reuser-run")
    reused_record = tasks / "other-task.json"
    reused_record.write_text(json.dumps(reuser))
    for _ in range(2):  # Exercise both fresh and content-verified cached lookups.
        assert output.resolve_worktree_record(repo, tasks, repo_root=primary) == (canonical, creator)
    ok, reason, receipt = output.preserve_worktree_artifacts(repo, primary=primary, tasks_dir=tasks, task_id=None)
    assert ok and not reason and receipt["task_id"] == "output-task"
    assert_entry(receipt, "ignored/report.txt", source.read_bytes())
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
    baseline = output.creation_inventory(tree, primary=primary, task_id="output-task", run_nonce="creator-run")
    source = tree / "ignored/report.txt"
    source.parent.mkdir()
    source.write_bytes(b"preserve me")
    _record(primary, "output-task", status="done", worktree_path=str(tree), worktree_reused=True)
    if case == "force_new":
        archive = primary / "batch_state/tasks/output-task.20261005T120000Z.archived.json"
        archive.write_text(
            json.dumps(
                {
                    "task_id": "output-task",
                    "status": "cancelled",
                    "worktree_path": str(tree),
                    "worktree_reused": False,
                    "ignored_output_baseline": baseline,
                }
            )
        )
    elif case == "internal_link":
        release = tree / ".runtime/api/releases/test-release"
        release.mkdir(parents=True)
        (release / ".pids").symlink_to(tree / ".pids")
    else:
        transient = tree / "ignored/transient.txt"
        transient.write_bytes(b"transient")
        original = output.record_only_receipt

        def mutate(root, names, record, **kwargs):
            if case == "vanished_copy":
                transient.unlink()
            else:
                transient.write_bytes(b"modified")
            return original(root, names, record, **kwargs)

        monkeypatch.setattr(output, "record_only_receipt", mutate)
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
    assert result.action == "removed" and not tree.exists()
    record = json.loads((primary / "batch_state/tasks/output-task.json").read_text())
    receipt = record["preserved_artifacts"]
    assert_entry(receipt, "ignored/report.txt", b"preserve me")
    assert not (primary / "batch_state/preserved").exists()
    if case in {"vanished_copy", "internal_link"}:
        assert receipt["inventory_error"] == "inventory_incomplete"
    elif case == "changed_copy":
        assert_entry(receipt, "ignored/transient.txt", b"modified")


@pytest.mark.parametrize("change", ["corrupt", "extra", "symlink", "other_worktree", "invalid_manifest"])
def test_unverified_previous_receipt_is_replaced(checkout, change):
    artifact(checkout, "ignored/report.txt", b"original")
    ok, _, first = preserve(checkout)
    assert ok
    path = checkout[2] / "output-task.json"
    record = json.loads(path.read_text())
    record["preserved_artifacts"] = {"location": change, "paths": [], "inventory_sha256": "untrusted"}
    path.write_text(json.dumps(record))
    ok, _, second = preserve(checkout)
    assert ok and second["inventory_sha256"] == first["inventory_sha256"]
    assert_entry(second, "ignored/report.txt", b"original")
    assert not (checkout[1] / "batch_state/preserved").exists()


def test_source_change_refreshes_receipt_without_reusing_copy(checkout, monkeypatch):
    source = artifact(checkout, "ignored/report.txt", b"original")
    first = preserve(checkout)[2]
    source.write_bytes(b"different")
    monkeypatch.setattr(output, "_reusable_copy", lambda *a: pytest.fail("archive reuse attempted"))
    ok, reason, receipt = preserve(checkout)
    assert ok and not reason
    assert receipt["inventory_sha256"] != first["inventory_sha256"]
    assert_entry(receipt, "ignored/report.txt", b"different")


@pytest.mark.parametrize("cache", [".pytest_breadcrumbs", "site/.astro", ".entire/logs", ".hypothesis", ".tox", ".nox"])
def test_tool_state_excluded_but_cache_output_survives(checkout, cache):
    (checkout[0] / ".gitignore").write_text(".cache/\n" + cache + "/\n")
    artifact(checkout, f"{cache}/tool.bin", b"regenerable")
    artifact(checkout, ".cache/out/answer.txt", b"task output")
    ok, _, receipt = preserve(checkout, {"response": f"Tool state: `{cache}/tool.bin`."})
    assert ok and receipt["count"] == 1 and receipt["bytes"] == len(b"task output")
    assert_entry(receipt, ".cache/out/answer.txt", b"task output")
    assert not any(entry["path"].startswith(cache + "/") for entry in receipt["paths"])


def _stub_path_limit(monkeypatch, reported):
    real = os.pathconf

    def fake(path, name):
        if name != "PC_PATH_MAX":
            return real(path, name)
        if reported == "unavailable":
            raise OSError("pathconf unavailable")
        return reported

    monkeypatch.setattr(os, "pathconf", fake)


def test_regular_file_beginning_with_symlink_prefix_has_no_target(tmp_path):
    payload = b"symlink\n" + b"x" * 100_000
    (tmp_path / "note.txt").write_bytes(payload)
    entry = output._path_inventory(tmp_path, ["note.txt"])[0]
    assert entry == {
        "path": "note.txt",
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def test_symlink_target_longer_than_the_path_limit_is_refused(tmp_path, monkeypatch):
    target = "too-long-target"
    (tmp_path / "link").symlink_to(target)
    _stub_path_limit(monkeypatch, 4)
    with pytest.raises(output.artifacts.SymlinkTargetRefusal) as caught:
        output._path_inventory(tmp_path, ["link"])
    assert caught.value.kind == "target-too-long"
    assert target not in str(caught.value)


@pytest.mark.parametrize("reported", [-1, 0, "unavailable"])
def test_unusable_path_limit_keeps_a_normal_symlink(tmp_path, monkeypatch, reported):
    (tmp_path / "link").symlink_to("inside-target")
    _stub_path_limit(monkeypatch, reported)
    entry = output._path_inventory(tmp_path, ["link"])[0]
    assert entry["type"] == "symlink"
    assert entry["target"] == "inside-target"


def test_longest_legal_symlink_target_is_kept(tmp_path):
    target = "t" * 4095
    (tmp_path / "link").symlink_to(target)
    entry = output._path_inventory(tmp_path, ["link"])[0]
    assert entry["type"] == "symlink"
    assert entry["target"] == target
    assert len(os.fsencode(entry["target"])) <= os.pathconf(tmp_path, "PC_PATH_MAX")


def test_record_only_inventory_omits_symlink_without_publishing_target(checkout, monkeypatch):
    repo, primary, tasks = checkout
    link = repo / "ignored" / "link"
    link.parent.mkdir()
    target = "too-long-target"
    link.symlink_to(target)
    _stub_path_limit(monkeypatch, 4)
    ok, reason, receipt = preserve(checkout, {"status": "done"})
    assert ok and not reason
    assert receipt["inventory_error"] == "inventory_incomplete" and receipt["paths"] == []
    assert target not in (tasks / "output-task.json").read_text()
    assert not (primary / "batch_state/preserved").exists()
    assert link.is_symlink() and os.readlink(link) == target


@pytest.mark.parametrize("failure", [None, "missing", "head", "member", "pid", "keep"])
def test_10303_preservation_consumes_current_merged_cohort_proof(same_branch_pending_cohort, failure):
    from scripts.orchestration import reap_worktrees as rw
    from scripts.orchestration import worktree_claims as claims
    from tests.orchestration.test_worktree_claims_cli import _git
    from tests.test_reused_worktree_retention import save

    repo, tree, tasks, _, successor, source = same_branch_pending_cohort
    head = _git(tree, "rev-parse", "HEAD")
    with claims.worktree_lock(tree, lock_dir=claims.repository_lock_dir(repo)):
        rw._record_merged_reuse_proof(
            repo,
            rw.WorktreeInfo(tree, "codex/boundary", head),
            rw.PullRequestState(9645, "MERGED", head),
            tasks_dir=tasks,
        )
        path = tasks / "boundary.json"
        creator = json.loads(path.read_text())
        if failure == "missing":
            creator.pop("worktree_reap_proof")
        elif failure == "head":
            creator["worktree_reap_proof"]["head_sha"] = "0" * 40
        elif failure == "member":
            successor["run_nonce"] = "changed"
        elif failure == "pid":
            successor["pid"] = os.getpid()
        elif failure == "keep":
            successor["keep_worktree"] = True
        save(tasks, creator)
        save(tasks, successor)
        ok, reason, receipt = output.preserve_worktree_artifacts(
            tree,
            primary=repo,
            tasks_dir=tasks,
            task_id="boundary",
            repo_root=repo,
        )
    assert ok is (failure is None), reason
    assert tree.exists() and source.read_bytes() == b"current output"
    if failure is None:
        assert output.verify_retrieval(repo, receipt) == receipt["retrieval_proof_sha256"]
        assert_entry(receipt, "ignored/output.txt", b"current output")


@pytest.mark.parametrize("mutation", ["pid", "keep", "head", "patch", "new_claim", "dirty"])
def test_10303_abandon_rechecks_after_inventory(abandon_cohort, monkeypatch, mutation):
    from scripts.orchestration import worktree_claims as claims
    from tests.orchestration.test_worktree_claims_cli import _git
    from tests.test_reused_worktree_retention import save

    repo, tree, tasks, creator, successor, source = abandon_cohort
    copy = output.record_only_receipt
    changed = []

    def change_after_copy(*args, **kwargs):
        result = copy(*args, **kwargs)
        if not changed:
            changed.append(True)
            if mutation == "pid":
                successor["pid"] = os.getpid()
                save(tasks, successor)
            elif mutation == "keep":
                successor["keep_worktree"] = True
                save(tasks, successor)
            elif mutation == "head":
                _git(tree, "commit", "--allow-empty", "-m", "changed")
            elif mutation == "patch":
                manifest = json.loads((repo / creator["worktree_abandon"]["preservation"]["path"]).read_bytes())
                (repo / manifest["head_patch"]["path"]).write_bytes(b"changed patch")
            elif mutation == "new_claim":
                save(tasks, dict(successor, task_id="new-claim", status="running"))
            else:
                (tree / "README.md").write_bytes(b"new dirty bytes")
        return result

    monkeypatch.setattr(output, "record_only_receipt", change_after_copy)
    with claims.worktree_lock(tree, lock_dir=claims.repository_lock_dir(repo)):
        ok, reason, _ = output.preserve_worktree_artifacts(
            tree,
            primary=repo,
            tasks_dir=tasks,
            task_id="boundary",
            repo_root=repo,
        )
    assert not ok and "task-state guard failed" in reason
    assert tree.exists() and source.read_bytes() == b"current output"


def test_10303_abandon_inventory_counts_untracked_not_ordinary_tracked_bytes(abandon_cohort, monkeypatch):
    from tests.orchestration.test_worktree_claims_cli import _git
    from tests.test_continuation_worktree_reap import _write_abandon_receipt
    from tests.test_reused_worktree_retention import save

    repo, tree, tasks, creator, successor, source = abandon_cohort
    (tree / "large-tracked.bin").write_bytes(b"x" * 4096)
    _git(tree, "add", "large-tracked.bin")
    _git(tree, "commit", "-m", "large tracked fixture")
    for member in (creator, successor):
        member["final_branch_head_commit"] = _git(tree, "rev-parse", "HEAD")
        save(tasks, member)
    _write_abandon_receipt(repo, tree, tasks, creator)
    (tree / "untracked.txt").write_bytes(b"unique")
    expected = len(source.read_bytes()) + len(b"unique")
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 4096)
    ok, reason, receipt = output.preserve_worktree_artifacts(
        tree, primary=repo, tasks_dir=tasks, task_id="boundary", repo_root=repo
    )
    assert ok and not reason, (reason, receipt)
    assert receipt["bytes"] == expected
    assert [entry["path"] for entry in receipt["paths"]] == ["ignored/output.txt", "untracked.txt"]
    assert_entry(receipt, "untracked.txt", b"unique")
    assert "large-tracked.bin" not in {entry["path"] for entry in receipt["paths"]}
    assert output.verify_retrieval(repo, receipt) == receipt["retrieval_proof_sha256"]


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
@pytest.mark.parametrize("present", [False, True])
def test_10303_abandon_preserves_present_hidden_tracked_bytes(abandon_cohort, flag, present):
    from tests.orchestration.test_worktree_claims_cli import _git

    repo, tree, tasks, _, _, _ = abandon_cohort
    _git(tree, "update-index", flag, "README.md")
    if present:
        (tree / "README.md").write_bytes(b"hidden local bytes")
    else:
        (tree / "README.md").unlink()
    ok, reason, receipt = output.preserve_worktree_artifacts(
        tree, primary=repo, tasks_dir=tasks, task_id="boundary", repo_root=repo
    )
    assert ok and not reason, (reason, receipt)
    assert output.verify_retrieval(repo, receipt) == receipt["retrieval_proof_sha256"]
    if present:
        assert_entry(receipt, "README.md", b"hidden local bytes")
    else:
        assert "README.md" not in {entry["path"] for entry in receipt["paths"]}


def test_10303_abandon_refuses_unmerged_index(abandon_cohort):
    from scripts.orchestration import worktree_claims as claims
    from tests.orchestration.test_worktree_claims_cli import _git
    from tests.test_continuation_worktree_reap import _write_abandon_receipt

    repo, tree, tasks, creator, _, source = abandon_cohort
    base = _git(tree, "rev-parse", "main:README.md")
    head = _git(tree, "rev-parse", "HEAD:README.md")
    unique = (
        subprocess.run(
            ["git", "hash-object", "-w", "--stdin"],
            cwd=tree,
            input=b"unique conflict-stage bytes\n",
            capture_output=True,
            check=True,
            timeout=30,
        )
        .stdout.decode()
        .strip()
    )
    entries = (
        f"0 {'0' * 40}\tREADME.md\n100644 {base} 1\tREADME.md\n"
        f"100644 {head} 2\tREADME.md\n100644 {unique} 3\tREADME.md\n"
    )
    subprocess.run(["git", "update-index", "--index-info"], cwd=tree, input=entries.encode(), check=True, timeout=30)
    _write_abandon_receipt(repo, tree, tasks, creator)
    with claims.worktree_lock(tree, lock_dir=claims.repository_lock_dir(repo)):
        ok, reason, _ = output.preserve_worktree_artifacts(
            tree,
            primary=repo,
            tasks_dir=tasks,
            task_id="boundary",
            repo_root=repo,
        )
    assert not ok and "unmerged index" in reason
    assert tree.exists() and source.read_bytes() == b"current output"
    assert unique in _git(tree, "ls-files", "--stage", "README.md")


def test_10303_abandon_patch_base_must_be_on_main(abandon_cohort):
    from scripts.orchestration import worktree_claims as claims
    from tests.test_reused_worktree_retention import save

    repo, tree, tasks, creator, _, source = abandon_cohort
    receipt = creator["worktree_abandon"]
    locator = receipt["preservation"]
    path = repo / locator["path"]
    manifest = json.loads(path.read_bytes())
    # Hash-valid empty diffs against the abandoned head omit its unique changes.
    manifest["base_sha"] = receipt["head_sha"]
    patch = repo / manifest["head_patch"]["path"]
    patch.write_bytes(b"")
    manifest["head_patch"]["sha256"] = hashlib.sha256(b"").hexdigest()
    path.write_bytes(json.dumps(manifest).encode())
    locator["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    save(tasks, creator)
    with claims.worktree_lock(tree, lock_dir=claims.repository_lock_dir(repo)):
        ok, reason, _ = output.preserve_worktree_artifacts(
            tree,
            primary=repo,
            tasks_dir=tasks,
            task_id="boundary",
            repo_root=repo,
        )
    assert not ok and "preservation manifest identity invalid" in reason
    assert tree.exists() and source.read_bytes() == b"current output"
