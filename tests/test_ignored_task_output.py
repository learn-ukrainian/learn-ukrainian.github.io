"""Ignored output inventory/copy boundaries, using only temporary repositories."""

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.fleet import regenerable_output as patterns
from scripts.orchestration import worktree_claims
from tests.orchestration import test_worktree_artifacts as fixtures
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree
from tests.test_continuation_worktree_reap import abandon_cohort as abandon_cohort
from tests.test_continuation_worktree_reap import same_branch_pending_cohort as same_branch_pending_cohort
from tests.test_reused_worktree_retention import cohort as cohort

checkout = fixtures.checkout
artifact = fixtures.artifact
assert_record_only = fixtures.assert_record_only


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
    assert receipt["count"] == 1 and receipt["bytes"] == len(payload)
    assert receipt["retention_disposition"] == "recorded"
    assert manifest.read_bytes() == payload
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", len(payload))
    ok, reason, receipt = preserve(checkout, record)
    assert ok and not reason
    assert receipt["count"] == 1 and receipt["bytes"] == len(payload)
    assert [entry["path"] for entry in receipt["paths"]] == [name]
    assert_record_only(receipt, {name: payload})


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
    original_open = Path.open

    def no_outside_read(path, *args, **kwargs):
        assert not path.is_relative_to(outside), "outside content opened"
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", no_outside_read)
    ok, reason, receipt = preserve(checkout)
    assert ok and not reason, reason
    relative = link.relative_to(repo).as_posix()
    entry = next(item for item in receipt["paths"] if item["path"] == relative)
    assert entry["type"] == "symlink" and entry["target"] == os.readlink(link)
    assert_record_only(receipt, {relative: b"symlink\n" + os.fsencode(os.readlink(link))})
    assert not (primary / "batch_state/preserved").exists()
    assert link.is_symlink() and source.stat().st_size == len(b"unique outside output")


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
        assert not ok and "non-zero exit status 128" in reason
        assert (repo / name).read_bytes() == payload
        assert not (primary / "batch_state/preserved").exists()
    else:
        assert ok and not reason
        assert_record_only(receipt, {name: payload, **({".gitignore": b"batch_state/\nignored/\n.pytest_cache/\n__pycache__/\n"} if empty_index else {})})
        named_probe = ["ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--", name]
        assert sum(args == named_probe for _, args in calls) == 2  # Initial inventory and post-copy recheck.


@pytest.mark.parametrize("status", ["done", "no_deliverable", "failed"])
def test_all_ignored_output_preserved_without_response_names(checkout, status):
    repo, _, tasks = checkout
    (repo / ".gitignore").write_text(".cache/\nignored/\n")
    artifact(checkout, ".cache/transcriptions/page.txt", b"transcription")
    artifact(checkout, "ignored/empty.txt", b"")
    ok, reason, receipt = preserve(checkout, {"status": status, "started_at": "2000-01-01T00:00:00Z"})
    assert ok and not reason
    assert receipt["count"] == 2 and receipt["bytes"] == 13
    assert_record_only(receipt, {".cache/transcriptions/page.txt": b"transcription", "ignored/empty.txt": b""})
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
    assert_record_only(receipt, {"ignored/old.txt": b"proof\x00\xff", "ignored/modified.txt": b"new version"})
    assert receipt["retention_disposition"] == "recorded"
    assert all(entry["class"] == "unknown_baseline" for entry in receipt["paths"])
    assert str(checkout[0]) not in json.dumps(receipt)


@pytest.mark.parametrize("failure", ["cap", "copy", "record", "inventory", "changed", "added"])
def test_failure_retains_sources(checkout, monkeypatch, failure):
    source = artifact(checkout, "ignored/report.txt", b"task output")
    record = {"status": "done"}
    if failure == "cap":
        monkeypatch.setattr(output, "MAX_RESIDUE_RECEIPT_BYTES", 10)
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
        extras = []
        if failure in {"changed", "added"}:
            extras = [
                f"ignored/receipt-cap-{index:02d}-{'x' * 64}.txt"
                for index in range(32)
            ]
            for name in extras:
                artifact(checkout, name, b"padding")
            monkeypatch.setattr(output, "MAX_RESIDUE_RECEIPT_BYTES", 2048)
        copy = output._classified_inventory

        def faulty_copy(*args, **kwargs):
            if failure == "copy":
                raise OSError("copy denied")
            entries = copy(*args, **kwargs)
            if failure == "changed":
                source.write_bytes(b"changed")
            else:
                artifact(checkout, "ignored/added.txt")
            return entries

        monkeypatch.setattr(output, "_classified_inventory", faulty_copy)
    ok, reason, receipt = preserve(checkout, record)
    assert not ok and "refusing worktree removal" in reason
    assert source.exists()
    if failure == "cap":
        state = json.loads((checkout[2] / "output-task.json").read_text())
        assert receipt is None
        assert "artifact_preservation_error" in state
        assert "preserved_artifacts" not in state
        assert not (checkout[1] / "batch_state/preserved").exists()
    elif failure in {"changed", "added"}:
        expected_source = b"changed" if failure == "changed" else b"task output"
        assert source.read_bytes() == expected_source
        for name in extras:
            assert (checkout[0] / name).read_bytes() == b"padding"
        if failure == "added":
            assert (checkout[0] / "ignored/added.txt").exists()
        assert receipt["mode"] == "record_only"
        assert receipt["copied_bytes"] == 0
        assert receipt["retention_disposition"] == "retained"
        assert receipt["entries_truncated"] is True
        assert len(json.dumps(receipt, sort_keys=True).encode()) <= 2048
        state = json.loads((checkout[2] / "output-task.json").read_text())
        assert state["preserved_artifacts"] == receipt
        assert len(json.dumps(state["preserved_artifacts"], sort_keys=True).encode()) <= 2048


def test_missing_record_retains_unknown_output_without_fallback_attribution(checkout):
    artifact(checkout, "ignored/report.txt")
    ok, _, receipt = preserve(checkout, task_id=None)
    assert not ok and receipt["count"] == 1
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
    assert_record_only(receipt, {"ignored/touched.txt": b"new task output"})


def test_retry_preserves_different_bytes_without_overwriting_first_attempt(checkout):
    source = artifact(checkout, "ignored/report.txt", b"first attempt")
    ok, _, first = preserve(checkout, {"status": "done"})
    assert ok
    source.write_bytes(b"second attempt")
    ok, _, second = preserve(checkout)
    assert ok and first["inventory_sha256"] != second["inventory_sha256"]
    assert_record_only(first, {"ignored/report.txt": b"first attempt"})
    assert_record_only(second, {"ignored/report.txt": b"second attempt"})
    assert json.loads((checkout[2] / "output-task.json").read_text())["preserved_artifacts"] == second


def test_retry_reuses_identical_copy_without_copying(checkout, monkeypatch):
    artifact(checkout, "ignored/report.txt", b"same attempt")
    ok, _, first = preserve(checkout, {"status": "done"})
    assert ok and first["copied_bytes"] == 0
    monkeypatch.setattr(
        output.artifacts,
        "_copy_verified",
        lambda *_args, **_kwargs: pytest.fail("identical output copied again"),
    )
    ok, _, second = preserve(checkout)
    assert ok and second == first and second["copied_bytes"] == 0
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
        non_directory = repo.parent / "somefile"
        non_directory.write_text("not a directory")
        record["cwd"] = str(non_directory / ".." / repo.name)
    elif binding == "alias":
        alias = repo.parent / "alias"
        alias.symlink_to(repo.parent / "missing" / ".." / repo.name, target_is_directory=True)
        record["worktree_path"] = os.path.relpath(alias, checkout[1])
    path = tasks / "output-task.json"
    path.write_text(json.dumps(record))
    ok, _, receipt = output.preserve_worktree_artifacts(
        repo, primary=checkout[1], task_id="output-task", tasks_dir=tasks, task_record=record
    )
    assert receipt["count"] == 1
    if binding in {"cwd", "alias"}:
        assert ok
        assert_record_only(receipt, {"ignored/old.txt": b"old output"})
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
    missing = repo.parent / "missing"
    hot["acp_runtime_paths"] = [str(other), str(other), str(missing), str(missing)]
    (tasks / "output-task.json").write_text(json.dumps(hot))
    archive = tasks / "archive/output-task.json"
    archive.parent.mkdir()
    canonical_spelling = str(repo / "missing" / "..")
    archive.write_text(
        json.dumps({"task_id": "output-task", "cwd": canonical_spelling, "started_at": "2999-01-01T00:00:00Z"})
    )
    with (
        patch.object(output, "_matching_worktree_records_once", wraps=output._matching_worktree_records_once) as scan,
        patch.object(worktree_claims, "resolve_claim_path", wraps=worktree_claims.resolve_claim_path) as resolve,
        patch.object(Path, "samefile", autospec=True, side_effect=Path.samefile) as samefile,
    ):
        ok, _, receipt = output.preserve_worktree_artifacts(repo, primary=primary, task_id="output-task", tasks_dir=tasks)
    assert scan.call_count == 3  # Keep every existing current-byte inventory.
    assert sum(call.args[0] == other for call in samefile.call_args_list) == 3
    assert sum(call.args[0] == missing for call in samefile.call_args_list) == 3
    assert all(call.args[0] not in (str(other), str(missing)) for call in resolve.call_args_list)
    assert any(call.args[0] == canonical_spelling for call in resolve.call_args_list)
    assert ok and receipt["count"] == 2 and receipt["copied_bytes"] == 0
    assert_record_only(receipt, {"ignored/new.txt": b"new", "ignored/old.txt": b"old"})
    assert json.loads(archive.read_text())["preserved_artifacts"] == receipt
    assert json.loads((tasks / "output-task.json").read_text()) == hot


def test_record_redispatched_during_copy_refuses_removal_without_updating_new_record(checkout, monkeypatch):
    repo, _, tasks = checkout
    artifact(checkout, "ignored/report.txt")
    other = repo.parent / "other"
    other.mkdir()
    replacement = {"worktree_path": str(other), "status": "running"}
    original = output._classified_inventory

    def redispatch(*args, **kwargs):
        entries = original(*args, **kwargs)
        (tasks / "output-task.json").write_text(json.dumps(replacement))
        return entries

    monkeypatch.setattr(output, "_classified_inventory", redispatch)
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
        assert_record_only(receipt, {"ignored/report.txt": b"redispatched output"})
        assert json.loads(canonical.read_text())["preserved_artifacts"] == receipt
        assert json.loads(archive.read_text()) == creator
    else:
        assert not ok and "refusing worktree removal" in reason


@pytest.mark.parametrize("stage", ["git_inventory", "after_lstat", "fingerprint", "copy"])
def test_vanished_output_is_rechecked_and_recorded_absent(checkout, monkeypatch, stage):
    _, _primary, tasks = checkout
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
        # Inventory reads the descriptor-walk record, which is what the fingerprint hashes.
        name = "_read_preserved_bytes"
        original = getattr(output.artifacts, name)

        def disappear(src, *args, **kwargs):
            if src == missing:
                missing.unlink(missing_ok=True)
            return original(src, *args, **kwargs)

        monkeypatch.setattr(output.artifacts, name, disappear)
    ok, reason, receipt = preserve(checkout, {"status": "done"})
    assert ok and not reason
    assert receipt["count"] == 1 and receipt["bytes"] == len(survivor.read_bytes())
    assert receipt["absent_paths"] == [{"path": "ignored/vanished.txt", "proof": "lstat_enoent"}]
    assert_record_only(receipt, {"ignored/report.txt": b"retain these bytes"})
    assert json.loads((tasks / "output-task.json").read_text())["preserved_artifacts"] == receipt


@pytest.mark.parametrize("failure", ["changed_before_copy", "false_enoent", "reappeared", "permission"])
def test_disappearance_neighbours_refuse_removal(checkout, monkeypatch, failure):
    source = artifact(checkout, "ignored/report.txt", b"original")
    original = output._classified_inventory

    def copy(*args, **kwargs):
        entries = original(*args, **kwargs)
        if failure == "changed_before_copy":
            source.write_bytes(b"modified")
        elif failure == "false_enoent":
            raise FileNotFoundError("destination vanished")
        elif failure == "permission":
            raise PermissionError("copy denied")
        else:
            source.unlink()
        return entries

    monkeypatch.setattr(output, "_classified_inventory", copy)
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


@pytest.mark.parametrize("kind", ["directory-inside", "file-inside", "relative", "dangling", "outside"])
def test_ignored_output_symlink_is_a_link_record(checkout, monkeypatch, kind):
    """Inventory, copy, digest and retrieval keep the raw target and never follow it."""
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
    entry = next(item for item in receipt["paths"] if item["path"] == relative)
    assert entry["type"] == "symlink" and entry["target"] == expected == os.readlink(link)
    expected_files = {relative: b"symlink\n" + os.fsencode(expected)}
    if kind == "directory-inside":
        expected_files["ignored/site/marker.txt"] = payload
    elif kind == "file-inside":
        expected_files["ignored/note.txt"] = payload
    elif kind == "relative":
        expected_files["ignored/releases/sha/file.txt"] = b"snapshot"
    assert_record_only(receipt, expected_files)
    assert not (primary / "batch_state/preserved").exists()
    if kind == "outside":
        assert outside.read_bytes() == outside_before == payload
    assert receipt["absent_paths"] == []


def test_swapped_ancestor_cannot_publish_an_outside_symlink_target(checkout, monkeypatch, tmp_path):
    """After the safe read, swapping an ancestor must not change the stored target.

    ``out/lnk`` points at ``inside-target``. Once the descriptor walk has returned
    that record, replace ``out`` with a symlink to a directory whose ``lnk``
    points at an outside target. The inventory may keep the inside target or
    refuse; the outside target string must not reach the metadata or the task record.
    """
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
    real_read = output.artifacts._read_preserved_bytes
    swapped = False

    def swap_after_read(path, *, root):
        nonlocal swapped
        payload = real_read(path, root=root)
        if not swapped and path == link:
            swapped = True
            out = repo / "out"
            os.rename(out, tmp_path / "real-out")
            out.symlink_to(outside, target_is_directory=True)
        return payload

    monkeypatch.setattr(output.artifacts, "_read_preserved_bytes", swap_after_read)
    _ok, _reason, metadata = preserve(checkout, {"status": "done"})
    assert swapped
    entry = next(item for item in metadata["paths"] if item["path"] == "out/lnk")
    inside = b"symlink\n" + os.fsencode("inside-target")
    assert entry["type"] == "symlink"
    assert entry["target"] == "inside-target"
    assert entry["size"] == len(inside)
    assert entry["sha256"] == hashlib.sha256(inside).hexdigest()
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
    entry = next(item for item in receipt["paths"] if item["path"] == "ignored/outside")
    assert entry["type"] == "symlink" and entry["target"] == str(outside)
    assert_record_only(receipt, {"ignored/outside": b"symlink\n" + os.fsencode(str(outside)), "ignored/report.txt": b"preserve me"})
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
    assert_record_only(receipt, {"ignored/report.txt": b"proof\x00\xff"})
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
        original = output._classified_inventory

        def copy(*args, **kwargs):
            if case == "vanished_copy":
                transient.unlink()
            entries = original(*args, **kwargs)
            if case == "changed_copy":
                transient.write_bytes(b"modified")
            return entries

        monkeypatch.setattr(output, "_classified_inventory", copy)
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
    assert_record_only(receipt, {"ignored/report.txt": b"preserve me", **({".runtime/api/releases/test-release/.pids": b"symlink\n" + os.fsencode(str(tree / ".pids"))} if case == "internal_link" else {})})
    if case == "vanished_copy":
        assert receipt["absent_paths"] == [{"path": "ignored/transient.txt", "proof": "lstat_enoent"}]
    elif case == "internal_link":
        assert receipt["absent_paths"] == []
        entry = next(item for item in receipt["paths"] if item["path"].endswith("/.pids"))
        assert entry["type"] == "symlink" and entry["target"] == str(tree / ".pids")
        assert entry["sha256"] == hashlib.sha256(b"symlink\n" + os.fsencode(str(tree / ".pids"))).hexdigest()


@pytest.mark.parametrize("change", ["corrupt", "extra", "symlink", "other_worktree", "invalid_manifest"])
def test_unverified_previous_copy_is_not_reused(checkout, change):
    artifact(checkout, "ignored/report.txt", b"original")
    first, _ = output.capture_abandon_output(checkout[0], primary=checkout[1], record={"task_id": "output-task"})
    location = checkout[1] / first["location"]
    location.with_suffix(".manifest.json").write_text(json.dumps({**first, "worktree_sha256": hashlib.sha256(str(checkout[0]).encode()).hexdigest()}))
    assert output._reusable_copy(location.parent, checkout[0], ["ignored/report.txt"], first["content_sha256"]) == location
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
    assert output._reusable_copy(location.parent, checkout[0], ["ignored/report.txt"], first["content_sha256"]) is None
    assert ok
    assert_record_only(second, {"ignored/report.txt": b"original"})


def test_source_change_during_reuse_refuses_removal(checkout, monkeypatch):
    source = artifact(checkout, "ignored/report.txt", b"original")
    assert preserve(checkout)[0]
    original = output._classified_inventory

    def mutate(*args, **kwargs):
        entries = original(*args, **kwargs)
        source.write_bytes(b"different")
        return entries

    monkeypatch.setattr(output, "_classified_inventory", mutate)
    ok, reason, _ = preserve(checkout)
    assert not ok and "changed during preservation" in reason
    assert source.read_bytes() == b"different"


@pytest.mark.parametrize("cache", [".pytest_breadcrumbs", "site/.astro", ".entire/logs", ".hypothesis", ".tox", ".nox"])
def test_tool_state_excluded_but_cache_output_survives(checkout, cache):
    (checkout[0] / ".gitignore").write_text(".cache/\n" + cache + "/\n")
    artifact(checkout, f"{cache}/tool.bin", b"regenerable")
    artifact(checkout, ".cache/out/answer.txt", b"task output")
    ok, _, receipt = preserve(checkout, {"response": f"Tool state: `{cache}/tool.bin`."})
    assert ok and receipt["count"] == 1 and receipt["bytes"] == len(b"task output")
    assert_record_only(receipt, {".cache/out/answer.txt": b"task output"})
    assert not (checkout[1] / "batch_state/preserved").exists()


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


def test_preserved_overlong_symlink_target_is_refused(checkout, monkeypatch):
    repo, _primary, tasks = checkout
    link = repo / "ignored" / "link"
    link.parent.mkdir()
    target = "too-long-target"
    link.symlink_to(target)
    _stub_path_limit(monkeypatch, 4)
    ok, reason, _metadata = preserve(checkout, {"status": "done"})
    assert not ok
    assert "target-too-long" in reason
    assert target not in reason
    published = (tasks / "output-task.json").read_text()
    assert "target-too-long" in published
    assert target not in published
    assert link.is_symlink() and os.readlink(link) == target


def _write_legacy_merged_reuse_proof(repo, tree, tasks, head):
    """Write the ``merged-reuse-reap.v1`` proof the retired reaper left on creator records."""
    from scripts.orchestration import worktree_git as wg

    matches = output.matching_worktree_records(tree, tasks, repo_root=repo, publish_cache=False)
    cohort = output._current_reuse_records(matches, tasks)
    info = wg.WorktreeInfo(tree, "codex/boundary", head)
    pr = wg.PullRequestState(9645, "MERGED", head)
    path = tasks / "boundary.json"
    creator = json.loads(path.read_text())
    proof = {
        "schema": "merged-reuse-reap.v1",
        "owner": creator["task_id"],
        "run_nonce": creator["run_nonce"],
        "head_sha": head,
        "pr_head_sha": head,
        "head_relation": wg._merged_head_relation(info, pr),
        "pr_number": pr.number,
        "pr_repository": pr.repository,
        "pr_state": pr.state,
        "pr_head_source": "merged_pr_record",
        "clean": True,
        "members": [
            {
                "task_id": member["task_id"],
                "run_nonce": member["run_nonce"],
                "branch": member.get("worktree_branch"),
                "head_sha": member.get("final_branch_head_commit"),
                "pid": member["pid"],
            }
            for _, member in cohort
        ],
    }
    path.write_text(json.dumps(dict(creator, worktree_reap_proof=proof)))


@pytest.mark.parametrize("failure", [None, "missing", "head", "member", "pid", "keep"])
def test_10303_preservation_consumes_current_merged_cohort_proof(same_branch_pending_cohort, failure):
    from scripts.orchestration import worktree_claims as claims
    from tests.orchestration.test_worktree_claims_cli import _git
    from tests.test_reused_worktree_retention import save

    repo, tree, tasks, _, successor, source = same_branch_pending_cohort
    head = _git(tree, "rev-parse", "HEAD")
    with claims.worktree_lock(tree, lock_dir=claims.repository_lock_dir(repo)):
        _write_legacy_merged_reuse_proof(repo, tree, tasks, head)
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
        assert_record_only(receipt, {"ignored/output.txt": b"current output"})


@pytest.mark.parametrize("mutation", ["pid", "keep", "head", "patch", "new_claim", "dirty"])
def test_10303_abandon_rechecks_after_copy(abandon_cohort, monkeypatch, mutation):
    from scripts.orchestration import worktree_claims as claims
    from tests.orchestration.test_worktree_claims_cli import _git
    from tests.test_reused_worktree_retention import save

    repo, tree, tasks, creator, successor, source = abandon_cohort
    copy = output.artifacts._copy_verified
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

    monkeypatch.setattr(output.artifacts, "_copy_verified", change_after_copy)
    with claims.worktree_lock(tree, lock_dir=claims.repository_lock_dir(repo)):
        ok, reason, _ = output.preserve_worktree_artifacts(
            tree,
            primary=repo,
            tasks_dir=tasks,
            task_id="boundary",
            repo_root=repo,
        )
    assert not ok and "artifact preservation failed" in reason
    assert changed
    assert tree.exists() and source.read_bytes() == b"current output"


def test_10303_abandon_cap_counts_untracked_not_ordinary_tracked_bytes(abandon_cohort, monkeypatch):
    from tests.orchestration.test_worktree_claims_cli import _git
    from tests.test_continuation_worktree_reap import _write_abandon_receipt
    from tests.test_reused_worktree_retention import save

    repo, tree, tasks, creator, successor, _source = abandon_cohort
    (tree / "large-tracked.bin").write_bytes(b"x" * 4096)
    _git(tree, "add", "large-tracked.bin")
    _git(tree, "commit", "-m", "large tracked fixture")
    for member in (creator, successor):
        member["final_branch_head_commit"] = _git(tree, "rev-parse", "HEAD")
        save(tasks, member)
    _write_abandon_receipt(repo, tree, tasks, creator)
    (tree / "untracked.txt").write_bytes(b"unique")
    expected = len(b"current output") + len(b"unique")
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", expected)
    ok, reason, receipt = output.preserve_worktree_artifacts(
        tree, primary=repo, tasks_dir=tasks, task_id="boundary", repo_root=repo
    )
    assert ok and not reason, (reason, receipt)
    assert receipt["bytes"] == expected
    assert [entry["path"] for entry in receipt["paths"]] == ["ignored/output.txt", "untracked.txt"]
    copy = repo / receipt["location"]
    assert (copy / "ignored/output.txt").read_bytes() == b"current output"
    assert (copy / "untracked.txt").read_bytes() == b"unique"
    assert not (copy / "large-tracked.bin").exists()
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
    copy = repo / receipt["location"]
    assert (copy / "ignored/output.txt").read_bytes() == b"current output"
    if present:
        assert (copy / "README.md").read_bytes() == b"hidden local bytes"
    else:
        assert not (copy / "README.md").exists()


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
