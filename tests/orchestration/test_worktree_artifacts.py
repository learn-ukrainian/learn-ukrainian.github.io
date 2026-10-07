"""Byte preservation and fail-closed removal guards for #9449."""

from __future__ import annotations

import json
import os
import subprocess
import threading
from pathlib import Path

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.orchestration import worktree_artifacts as wa
from tests import _worktree_artifact_links as links


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


def bound_record(checkout, record=None):
    record = {} if record is None else record
    record.setdefault("task_id", "artifact-task")
    record.setdefault("worktree_path", str(checkout[0]))
    record.setdefault("run_nonce", "artifact-run")
    (checkout[2] / "artifact-task.json").write_text(json.dumps(record))
    return record


def guard(checkout, *, task_id="artifact-task", record=None):
    repo, primary, tasks = checkout
    path = tasks / "artifact-task.json"
    if record is not None:
        record.setdefault("task_id", task_id)
        record.setdefault("worktree_path", str(repo))
        record.setdefault("run_nonce", "artifact-run")
        if path.exists():
            stored = json.loads(path.read_text())
            # Response references belong to the canonical record, not hints.
            stored.update({key: record[key] for key in ("response", "result_file") if key in record})
            bound_record(checkout, stored)
        else:
            bound_record(checkout, record)
    elif not path.exists() and task_id is not None:
        bound_record(checkout)
    return output.preserve_worktree_artifacts(
        repo, primary=primary, task_id=task_id, tasks_dir=tasks, task_record=record
    )


def artifact(checkout, name="batch_state/sub/report.bin", payload=b"proof\x00\xff"):
    path = checkout[0] / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


@pytest.mark.parametrize("returncode", [0, 128])
def test_git_path_inventory_uses_isolated_environment(checkout, monkeypatch, returncode):
    calls = []

    def runner(args, **kwargs):
        calls.append((kwargs["cwd"], args))
        assert kwargs["env"] == wa._safe_git_env()
        assert kwargs["check"] is True and kwargs["timeout"] == 30
        if returncode:
            raise subprocess.CalledProcessError(returncode, args, stderr="unavailable")
        return subprocess.CompletedProcess(args, 0, "ignored/spaced файл.txt\0".encode(), b"")

    monkeypatch.setattr(wa.subprocess, "run", runner)
    if returncode:
        with pytest.raises(subprocess.CalledProcessError):
            wa._git_paths(checkout[0], "--cached")
    else:
        assert wa._git_paths(checkout[0], "--cached") == ["ignored/spaced файл.txt"]
    assert calls == [(checkout[0], ["git", "ls-files", "-z", "--cached"])]


def test_named_artifact_inventory_uses_isolated_environment(checkout, monkeypatch):
    name = "batch_state/sub/report.bin"
    artifact(checkout, name)
    calls = []

    def runner(args, **kwargs):
        calls.append((kwargs["cwd"], args))
        assert kwargs["env"] == wa._safe_git_env()
        return subprocess.CompletedProcess(args, 0, (name + "\0").encode(), b"")

    monkeypatch.setattr(wa.subprocess, "run", runner)
    assert wa._named_artifact_files(
        checkout[0], {"response": f"Capture `{name}`."}, primary=checkout[1]
    ) == {name}
    assert calls == [(checkout[0], ["git", "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--", name])]


def test_preserved_bytes_record_and_idempotency(checkout):
    source = artifact(checkout)
    record = {"status": "done", "response": "Capture `batch_state/sub/report.bin`."}
    bound_record(checkout, record)
    ok, reason, metadata = guard(checkout, record=record)
    assert ok and not reason
    assert metadata["count"] == 1
    location = checkout[1] / metadata["location"]
    copy = location / "batch_state/sub/report.bin"
    assert copy.read_bytes() == source.read_bytes()
    assert wa._fingerprint(copy, root=location) == wa._fingerprint(source, root=checkout[0])
    saved = json.loads((checkout[2] / "artifact-task.json").read_text())
    assert saved["preserved_artifacts"] == record["preserved_artifacts"] == metadata
    assert guard(checkout)[0]  # Repeated guard retains verified existing bytes.


def test_empty_dirs_and_pycache_do_not_need_identity(checkout):
    artifact(checkout, "batch_state/__pycache__/worker.pyc")
    (checkout[0] / "batch_state/empty").mkdir()
    assert guard(checkout, task_id=None) == (True, "", None)
    assert not (checkout[1] / "batch_state/preserved").exists()


def test_empty_ignored_file_is_preserved_with_identity(checkout):
    artifact(checkout, payload=b"")
    artifact(checkout, "batch_state/__pycache__/worker.pyc")
    ok, reason, receipt = guard(checkout)
    assert ok and not reason
    assert receipt["count"] == 1 and receipt["bytes"] == 0
    location = checkout[1] / receipt["location"]
    assert (location / "batch_state/sub/report.bin").read_bytes() == b""
    assert not (location / "batch_state/__pycache__").exists()


@pytest.mark.parametrize("task_id", [None, "../escape", "..", "bad/id"])
def test_missing_or_unsafe_identity_blocks_copy(checkout, task_id):
    source = artifact(checkout)
    bound_record(checkout, {"task_id": task_id})
    ok, reason, _ = guard(checkout, task_id=task_id)
    assert not ok and "canonical task attribution" in reason
    assert source.exists()


@pytest.mark.parametrize("failure", ["copy", "corruption", "record"])
def test_failed_copy_verification_or_record_blocks_removal(checkout, monkeypatch, failure):
    source = artifact(checkout)
    bound_record(checkout, {"status": "done"})
    if failure == "copy":

        def fail_copy(*_args):
            raise OSError("copy denied")

        monkeypatch.setattr(wa, "_write_verified_bytes", fail_copy)
    elif failure == "corruption":
        monkeypatch.setattr(
            wa, "_write_verified_bytes", lambda _payload, destination: destination.write_bytes(b"wrong")
        )
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
    assert ok and not reason
    assert destination.read_bytes() == b"previous evidence"
    receipt = json.loads((checkout[2] / "artifact-task.json").read_text())["preserved_artifacts"]
    assert (checkout[1] / receipt["location"] / "batch_state/sub/report.bin").read_bytes() == b"proof\x00\xff"


def test_preservation_root_symlink_blocks_copy(checkout):
    source = artifact(checkout)
    elsewhere = checkout[1] / "elsewhere"
    elsewhere.mkdir()
    (checkout[1] / "batch_state/preserved").symlink_to(elsewhere, target_is_directory=True)
    ok, reason, _ = guard(checkout)
    assert not ok and ("symlink" in reason or "retrieval location" in reason)
    assert not any(entry.is_file() for entry in elsewhere.rglob("*"))
    assert source.read_bytes() == b"proof\x00\xff"


def test_source_symlink_is_preserved_as_link_record(checkout):
    source = artifact(checkout)
    source.unlink()
    external = checkout[1] / "external.bin"
    external.write_bytes(b"external bytes")
    source.symlink_to(external)
    ok, reason, metadata = guard(checkout)
    assert ok and not reason, reason
    entry = metadata["paths"][0]
    assert entry["type"] == "symlink" and entry["target"] == str(external)
    copied = checkout[1] / metadata["location"] / entry["path"]
    assert copied.is_file() and not copied.is_symlink()
    assert copied.read_bytes() != b"external bytes"
    assert os.fsencode(str(external)) in copied.read_bytes()
    assert external.read_bytes() == b"external bytes"


def _swap_regular_file_for_outside_symlink(monkeypatch, source: Path, outside: Path) -> None:
    """After ``fstat`` classifies a regular file, replace it with a link to ``outside``.

    The type check is the ``O_PATH`` descriptor. The later read opens the name
    again and must refuse that link instead of following it.
    """
    real_open = wa.open_leaf_descriptor

    def raced(dir_fd: int, name: str):
        fd, info = real_open(dir_fd, name)
        if name == source.name and source.is_file() and not source.is_symlink():
            source.unlink()
            source.symlink_to(outside)
        return fd, info

    monkeypatch.setattr(wa, "open_leaf_descriptor", raced)


def test_copy_refuses_symlink_swapped_in_between_check_and_copy(tmp_path, monkeypatch):
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"OUTSIDE-SECRET")
    source = tmp_path / "checkout" / "evidence.bin"
    source.parent.mkdir()
    source.write_bytes(b"inside-bytes")
    destination = tmp_path / "preserved" / "evidence.bin"
    _swap_regular_file_for_outside_symlink(monkeypatch, source, outside)

    with pytest.raises(ValueError, match="changed during preservation"):
        wa._copy_verified(
            source,
            destination,
            source_root=source.parent,
            destination_root=destination.parent,
        )

    assert os.path.islink(source)
    assert os.readlink(source) == str(outside)
    assert outside.read_bytes() == b"OUTSIDE-SECRET"
    assert not destination.exists()
    if destination.parent.exists():
        leaked = [
            path for path in destination.parent.rglob("*") if path.is_file() and b"OUTSIDE-SECRET" in path.read_bytes()
        ]
        assert leaked == []


def test_fingerprint_refuses_symlink_swapped_in_between_check_and_open(tmp_path, monkeypatch):
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"OUTSIDE-SECRET")
    source = tmp_path / "evidence.bin"
    source.write_bytes(b"inside-bytes")
    _swap_regular_file_for_outside_symlink(monkeypatch, source, outside)

    with pytest.raises(ValueError, match="changed during preservation"):
        wa._fingerprint(source, root=source.parent)

    assert os.path.islink(source)
    assert outside.read_bytes() == b"OUTSIDE-SECRET"


_OUTSIDE_SECRET = b"OUTSIDE-SECRET"


def _ancestor_swapped_file(tmp_path: Path) -> tuple[Path, Path, Path]:
    """``worktree/batch_state/sub/report.bin`` whose ``batch_state`` is an outside symlink.

    The leaf's parent on the outside is a real directory, so an open of the
    full parent path follows the earlier link. ``O_NOFOLLOW`` on the last
    component does not see it.
    """
    outside = tmp_path / "outside"
    (outside / "sub").mkdir(parents=True)
    outside_file = outside / "sub" / "report.bin"
    outside_file.write_bytes(_OUTSIDE_SECRET)
    worktree = tmp_path / "worktree"
    source = worktree / "batch_state" / "sub" / "report.bin"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"inside-bytes")
    batch = worktree / "batch_state"
    os.rename(batch, tmp_path / "real-batch")
    batch.symlink_to(outside, target_is_directory=True)
    return worktree, source, outside_file


def _preserved_outside_bytes(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [path for path in root.rglob("*") if path.is_file() and _OUTSIDE_SECRET in path.read_bytes()]


def _fingerprint_anchored(path: Path, *, root: Path) -> tuple[int, str]:
    """Call the anchored fingerprint. The pre-fix signature had no root."""
    try:
        return wa._fingerprint(path, root=root)
    except TypeError as exc:
        if "root" not in str(exc):
            raise
        return wa._fingerprint(path)


def _copy_anchored(source: Path, destination: Path, *, source_root: Path, destination_root: Path) -> None:
    """Call the anchored copy. The pre-fix signature had no roots."""
    try:
        wa._copy_verified(source, destination, source_root=source_root, destination_root=destination_root)
    except TypeError as exc:
        if "source_root" not in str(exc):
            raise
        wa._copy_verified(source, destination)


def test_fingerprint_refuses_ancestor_directory_symlink(tmp_path: Path) -> None:
    worktree, source, outside_file = _ancestor_swapped_file(tmp_path)
    try:
        _fingerprint_anchored(source, root=worktree)
    except ValueError as exc:
        assert "symlink" in str(exc)
    else:
        pytest.fail("ancestor symlink was followed and outside bytes were read")
    assert outside_file.read_bytes() == _OUTSIDE_SECRET
    assert (tmp_path / "real-batch" / "sub" / "report.bin").read_bytes() == b"inside-bytes"


def test_copy_verified_refuses_ancestor_directory_symlink(tmp_path: Path) -> None:
    worktree, source, outside_file = _ancestor_swapped_file(tmp_path)
    destination_root = tmp_path / "preserved"
    destination = destination_root / "batch_state" / "sub" / "report.bin"
    try:
        _copy_anchored(source, destination, source_root=worktree, destination_root=destination_root)
    except ValueError as exc:
        assert "symlink" in str(exc)
    else:
        pytest.fail("ancestor symlink was followed and outside bytes were copied")
    assert _preserved_outside_bytes(destination_root) == []
    assert outside_file.read_bytes() == _OUTSIDE_SECRET


def test_ancestor_swap_after_inventory_does_not_publish_outside_bytes(checkout, monkeypatch, tmp_path: Path) -> None:
    """Swap an earlier directory after the inventory has seen a real file.

    Refusal has to happen on the read. A later check that only blocks removal
    still leaves the outside bytes in the preservation copy.
    """
    source = artifact(checkout)
    outside = tmp_path / "outside"
    (outside / "sub").mkdir(parents=True)
    outside_file = outside / "sub" / "report.bin"
    outside_file.write_bytes(_OUTSIDE_SECRET)
    real_resolve = Path.resolve
    swapped = False

    def swapping_resolve(self: Path, *args: object, **kwargs: object) -> Path:
        nonlocal swapped
        resolved = real_resolve(self, *args, **kwargs)
        if not swapped and self == source:
            swapped = True
            batch = checkout[0] / "batch_state"
            os.rename(batch, tmp_path / "real-batch")
            batch.symlink_to(outside, target_is_directory=True)
        return resolved

    monkeypatch.setattr(Path, "resolve", swapping_resolve)
    ok, reason, _metadata = guard(checkout)

    preserved = checkout[1] / "batch_state" / "preserved"
    assert swapped
    assert _preserved_outside_bytes(preserved) == []
    assert not ok
    assert "symlink" in reason
    assert outside_file.read_bytes() == _OUTSIDE_SECRET
    assert (tmp_path / "real-batch" / "sub" / "report.bin").read_bytes() == b"proof\x00\xff"


def test_directory_walk_records_symlinks_without_following(checkout, tmp_path):
    repo = checkout[0]
    root = repo / "ignored"
    root.mkdir()
    (root / "real.txt").write_bytes(b"real")
    (root / "file-link").symlink_to("real.txt")
    (root / "sub").mkdir()
    (root / "dir-link").symlink_to("sub", target_is_directory=True)
    (root / "dangling").symlink_to("missing")
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"outside-only")
    (root / "out-link").symlink_to(outside)
    names = wa._inspect_directory_artifact(root, "ignored", worktree=repo)
    assert set(names) == {
        "ignored/real.txt",
        "ignored/file-link",
        "ignored/dir-link",
        "ignored/dangling",
        "ignored/out-link",
    }
    dest = tmp_path / "copy"
    wa._copy_verified(root / "out-link", dest, source_root=root, destination_root=dest.parent)
    assert dest.is_file() and not dest.is_symlink()
    assert dest.read_bytes() != b"outside-only"
    assert os.fsencode(str(outside)) in dest.read_bytes()
    assert outside.read_bytes() == b"outside-only"


def test_primary_task_sidecar_is_not_copied(checkout):
    shared = checkout[2] / "artifact-task.result"
    shared.write_bytes(b"already durable")
    source = artifact(checkout)
    source.unlink()
    source.symlink_to(shared)
    ok, reason, metadata = guard(checkout)
    assert ok and not reason, reason
    entry = metadata["paths"][0]
    assert entry["type"] == "symlink" and entry["target"] == str(shared)
    copied = checkout[1] / metadata["location"] / entry["path"]
    assert copied.is_file() and not copied.is_symlink()
    assert b"already durable" not in copied.read_bytes()
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
    assert ((checkout[1] / metadata["location"]) / "ignored/a report.txt").read_bytes() == source.read_bytes()


def test_result_sidecar_is_read_and_tracked_named_files_are_safe(checkout):
    sidecar = checkout[2] / "artifact-task.result"
    sidecar.write_text("Capture `ignored/note.txt`. Read `.gitignore`.")
    source = artifact(checkout, "ignored/note.txt")
    ok, _reason, metadata = guard(checkout, record={"result_file": str(sidecar)})
    assert ok
    assert ((checkout[1] / metadata["location"]) / "ignored/note.txt").read_bytes() == source.read_bytes()
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
    raw = '{"keep_worktree": true, broken JSON'
    path.write_text(raw)
    assert not guard(checkout)[0]
    assert path.read_text() == raw


def test_batch_state_symlink_cannot_hide_local_artifacts(checkout):
    source = artifact(checkout, "ignored/hidden.txt")
    (checkout[0] / "batch_state").symlink_to(source.parent, target_is_directory=True)
    ok, reason, _ = guard(checkout)
    assert ok and not reason
    receipt = json.loads((checkout[2] / "artifact-task.json").read_text())["preserved_artifacts"]
    assert (checkout[1] / receipt["location"] / "ignored/hidden.txt").read_bytes() == source.read_bytes()
    assert source.exists()


def test_batch_state_link_loop_is_preserved_without_resolving(checkout):
    bound_record(checkout, {"status": "done"})
    (checkout[0] / "batch_state").mkdir()
    (checkout[0] / "batch_state/loop").symlink_to("loop")
    ok, reason, metadata = guard(checkout)
    assert ok and not reason, reason
    entry = metadata["paths"][0]
    assert entry == {**entry, "path": "batch_state/loop", "type": "symlink", "target": "loop"}
    copied = checkout[1] / metadata["location"] / "batch_state/loop"
    assert copied.is_file() and not copied.is_symlink()
    assert copied.read_bytes() == b"symlink\nloop"


@pytest.mark.parametrize(
    ("reference", "refused"),
    [
        ("../outside.txt", False),
        ("absolute", False),
        ("ignored/sub/../../link", True),
        ("ignored/dir/../../link", True),
    ],
)
def test_outbound_refusal_needs_a_link_inside_the_checkout(checkout, tmp_path, reference, refused):
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"lives outside the checkout")
    (checkout[0] / "ignored/sub").mkdir(parents=True)
    (checkout[0] / "ignored/dir").symlink_to("sub", target_is_directory=True)
    (checkout[0] / "link").symlink_to(outside)
    reference = str(outside) if reference == "absolute" else reference
    ok, reason, metadata = guard(checkout, record={"response": f"Read `{reference}`."})
    assert ok is not refused
    if refused:
        assert metadata["retention_disposition"] == "retained"
    else:
        assert ok and metadata["count"] == 1
        assert metadata["paths"][0]["type"] == "symlink"
        assert metadata["paths"][0]["path"] == "ignored/dir"
        assert metadata["paths"][0]["target"] == "sub"
    assert (links.REFUSAL in reason) is refused
    assert outside.read_bytes() == b"lives outside the checkout"


@pytest.mark.parametrize("reference", ["root", "./", "ignored", ".pytest_cache/cache.txt"])
def test_named_directory_or_cache_does_not_block(checkout, reference):
    artifact(checkout, "ignored/report.txt")
    cache = artifact(checkout, ".pytest_cache/cache.txt")
    reference = str(checkout[0]) if reference == "root" else reference
    ok, reason, metadata = guard(checkout, record={"response": f"Worked in `{reference}`."})
    assert ok and not reason
    assert metadata["count"] == 1
    assert (checkout[1] / metadata["location"] / "ignored/report.txt").read_bytes() == b"proof\x00\xff"
    assert not (checkout[1] / metadata["location"] / ".pytest_cache/cache.txt").exists()
    assert cache.exists()


def test_record_changed_during_copy_keeps_other_writers_fields(checkout, monkeypatch):
    artifact(checkout)
    path = checkout[2] / "artifact-task.json"
    initial = bound_record(checkout, {"status": "done", "response": "original"})
    write = wa._write_verified_bytes

    def concurrent_writer(payload, destination):
        from scripts.orchestration.dead_worker_state import task_state_lock

        with task_state_lock(path):
            path.write_text(json.dumps({**initial, "status": "failed", "response": "new", "other_writer": True}))
        return write(payload, destination)

    monkeypatch.setattr(wa, "_write_verified_bytes", concurrent_writer)
    assert guard(checkout, record={"stale_field": "do not merge"})[0]
    saved = json.loads(path.read_text())
    assert saved["status"] == "failed"
    assert saved["response"] == "new"
    assert saved["other_writer"] is True
    assert "stale_field" not in saved
    assert saved["preserved_artifacts"]["count"] == 1


def test_missing_record_is_not_created(checkout):
    source = artifact(checkout)
    ok, reason, metadata = guard(checkout, task_id=None)
    assert not ok and "missing canonical task attribution" in reason
    assert metadata["retention_disposition"] == "retained"
    assert source.read_bytes() == b"proof\x00\xff"
    assert not (checkout[1] / "batch_state/preserved").exists()
    assert not (checkout[2] / "artifact-task.json").exists()


def test_named_external_symlink_refuses_removal(checkout, tmp_path):
    target = tmp_path / "outside.txt"
    target.write_bytes(b"lives outside the checkout")
    (checkout[0] / "ignored").mkdir()
    (checkout[0] / "ignored/link.txt").symlink_to(target)
    path = checkout[2] / "artifact-task.json"
    bound_record(checkout, {"status": "done"})
    ok, reason, metadata = guard(checkout, record={"response": "Wrote `ignored/link.txt`."})
    assert not ok and links.REFUSAL in reason and metadata["retention_disposition"] == "retained"
    assert links.REFUSAL in json.loads(path.read_text())["artifact_preservation_error"]
    assert target.read_bytes() == b"lives outside the checkout"
    assert not (checkout[1] / "batch_state/preserved").exists()


@pytest.mark.parametrize("scenario", links.SCENARIOS)
def test_named_symlink_preserves_or_refuses(checkout, tmp_path, scenario):
    repo, primary, tasks = checkout
    outside = tmp_path / "outside"
    named, preserved, target = links.build_named_link(repo, primary, outside, scenario)
    bound_record(checkout, {"status": "done"})
    ok, reason, metadata = guard(checkout, record={"response": links.worker_response(named)})
    links.restore_access(repo)
    saved = json.loads((tasks / "artifact-task.json").read_text())
    assert target is None or target.read_bytes() == links.PAYLOAD
    if scenario in links.REFUSALS:
        assert not ok and links.REFUSALS[scenario] in reason
        assert links.REFUSALS[scenario] in saved["artifact_preservation_error"]
        assert "\x00" not in reason and "x" * 300 not in reason
    elif scenario == "outbound_batch_state":
        assert ok and not reason and metadata["count"] == 1
        entry = metadata["paths"][0]
        assert entry["type"] == "symlink" and entry["path"] == "ignored/link" and entry["target"] == str(target)
        copied = primary / metadata["location"] / "ignored/link"
        assert copied.is_file() and not copied.is_symlink() and links.PAYLOAD not in copied.read_bytes()
        assert saved["preserved_artifacts"] == metadata
    elif preserved is None:
        assert (ok, reason, metadata) == (True, "", None)
        assert not (primary / "batch_state/preserved").exists()
        assert "artifact_preservation_error" not in saved
    else:
        link_path, link_target = links.IGNORED_LINK[scenario]
        assert ok and not reason and metadata["count"] == 2
        copied_root = checkout[1] / metadata["location"]
        assert (copied_root / preserved).read_bytes() == links.PAYLOAD
        entry = next(item for item in metadata["paths"] if item["path"] == link_path)
        assert entry["type"] == "symlink" and entry["target"] == link_target
        assert (copied_root / link_path).is_file() and not (copied_root / link_path).is_symlink()
        assert saved["preserved_artifacts"] == metadata


def test_record_update_waits_for_the_shared_writer_lock(checkout):
    """Removing ``task_state_lock`` from the update lets it race and lose the other writer's fields."""
    from scripts.orchestration.dead_worker_state import task_state_lock

    path = checkout[2] / "artifact-task.json"
    initial = bound_record(checkout, {"status": "running"})
    held, release = threading.Event(), threading.Event()

    def other_writer():
        # A locked read-modify-write: an unlocked update landing mid-section is overwritten.
        with task_state_lock(path):
            record = json.loads(path.read_text())
            held.set()
            release.wait(10)
            path.write_text(json.dumps({**record, "status": "done", "other_writer": True}))

    holder = threading.Thread(target=other_writer)
    holder.start()
    assert held.wait(10)
    updater = threading.Thread(
        target=output._update_bound_task_record,
        args=(path, checkout[0], {"preserved_artifacts": {"count": 1}}),
        kwargs={"repo_root": checkout[1]},
    )
    updater.start()
    updater.join(0.5)
    waited = updater.is_alive()
    release.set()
    holder.join(10)
    updater.join(10)
    assert waited, "update did not wait for the task-record writer lock"
    saved = json.loads(path.read_text())
    assert saved == {**initial, "status": "done", "other_writer": True, "preserved_artifacts": {"count": 1}}


def test_success_clears_a_stale_preservation_error(checkout):
    artifact(checkout)
    path = checkout[2] / "artifact-task.json"
    bound_record(checkout, {"status": "done", "artifact_preservation_error": "earlier copy failed"})
    record = {"artifact_preservation_error": "earlier copy failed"}
    assert guard(checkout, record=record)[0]
    assert "artifact_preservation_error" not in json.loads(path.read_text())
    assert "artifact_preservation_error" not in record


_GIT_ENV = {
    **{k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "AGENT_NO_MERGE"},
    "GIT_AUTHOR_NAME": "Test Worker",
    "GIT_AUTHOR_EMAIL": "worker@example.com",
    "GIT_COMMITTER_NAME": "Test Worker",
    "GIT_COMMITTER_EMAIL": "worker@example.com",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
}


def test_ignored_artifact_directory_of_regular_files(checkout):
    """Denominator row 2: a directory of regular files has its files discovered and preserved."""
    bound_record(checkout, {"status": "done"})
    f1 = artifact(checkout, "batch_state/reports/probe/report1.json", payload=b'{"metric": 1}')
    f2 = artifact(checkout, "batch_state/reports/probe/report2.json", payload=b'{"metric": 2}')
    (checkout[0] / "batch_state/reports/probe/__pycache__").mkdir(parents=True, exist_ok=True)
    (checkout[0] / "batch_state/reports/probe/__pycache__/cached.pyc").write_bytes(b"disposable")

    ok, reason, metadata = guard(checkout)
    assert ok and not reason
    assert metadata["count"] == 2
    location = checkout[1] / metadata["location"]
    assert (location / "batch_state/reports/probe/report1.json").read_bytes() == f1.read_bytes()
    assert (location / "batch_state/reports/probe/report2.json").read_bytes() == f2.read_bytes()
    assert not (location / "batch_state/reports/probe/__pycache__").exists()


def test_ignored_artifact_nested_repo_no_unpushed_commits(checkout, tmp_path):
    """Denominator row 3 & AC-01: nested repo with no unpushed commits refuses removal with actionable command."""
    # Create upstream remote
    upstream = tmp_path / "upstream"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    # Clone upstream into batch_state
    scratch_dir = checkout[0] / "batch_state/reports/scratch_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(scratch_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    # Add and push a commit so there are zero unpushed commits
    (scratch_dir / "probe.txt").write_text("probe output\n")
    subprocess.run(["git", "add", "probe.txt"], cwd=scratch_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init probe"], cwd=scratch_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=scratch_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(
        ["git", "fetch", "origin"], cwd=scratch_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30
    )

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact is a nested git repository with no unpushed commits" in reason
    assert "files" in reason and "bytes" in reason
    assert "batch_state/reports/scratch_repo" in reason
    assert "clear with: rm -rf batch_state/reports/scratch_repo" in reason

    # AC-01: Actionable single command removes the scratch repo and allows worktree release
    import shutil

    shutil.rmtree(scratch_dir)
    ok_after, reason_after, _ = guard(checkout)
    assert ok_after and not reason_after


def test_ignored_artifact_nested_repo_with_unpushed_commits_never_discarded(checkout):
    """Denominator row 4 & AC-02: nested repo with unpushed commits refuses and is never discarded."""
    unpushed_dir = checkout[0] / "batch_state/reports/unpushed_repo"
    unpushed_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", str(unpushed_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (unpushed_dir / "unpushed_work.txt").write_text("valuable local probe data\n")
    subprocess.run(["git", "add", "unpushed_work.txt"], cwd=unpushed_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "commit", "-m", "valuable unpushed probe"], cwd=unpushed_dir, check=True, env=_GIT_ENV, timeout=30
    )

    rev_proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=unpushed_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        text=True,
        timeout=30,
    )
    commit_sha = rev_proc.stdout.strip()

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact is a nested git repository with unpushed commits" in reason
    assert "unpushed work must not be discarded" in reason
    assert commit_sha[:7] in reason or commit_sha in reason
    assert "files" in reason and "bytes" in reason

    # AC-02: The unpushed repo and its commits are preserved intact on disk
    assert unpushed_dir.exists()
    assert (unpushed_dir / "unpushed_work.txt").read_text() == "valuable local probe data\n"
    log_proc = subprocess.run(
        ["git", "log", "-1", "--oneline"],
        cwd=unpushed_dir,
        check=True,
        capture_output=True,
        text=True,
        env=_GIT_ENV,
        timeout=30,
    )
    assert "valuable unpushed probe" in log_proc.stdout


def test_ignored_artifact_nested_linked_worktree_pointing_at_another_artifact(checkout):
    """Denominator row 5: nested linked worktree pointing at another artifact refuses removal."""
    primary_repo = checkout[0] / "batch_state/reports/primary_repo"
    primary_repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", str(primary_repo)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (primary_repo / "initial.txt").write_text("seed\n")
    subprocess.run(["git", "add", "initial.txt"], cwd=primary_repo, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=primary_repo, check=True, env=_GIT_ENV, timeout=30)

    linked_wt = checkout[0] / "batch_state/reports/linked_wt"
    subprocess.run(
        ["git", "worktree", "add", str(linked_wt), "-b", "wt-branch"],
        cwd=primary_repo,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact is a nested linked worktree whose gitdir pointer points at another artifact" in reason
    assert "batch_state/reports/primary_repo" in reason


def test_ignored_artifact_nested_repo_symlink_dot_git(checkout, tmp_path):
    """A directory whose .git is a symlink fails closed."""
    real_git_repo = tmp_path / "real_git_repo"
    subprocess.run(["git", "init", str(real_git_repo)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    bad_repo = checkout[0] / "batch_state/reports/bad_repo"
    bad_repo.mkdir(parents=True, exist_ok=True)
    (bad_repo / ".git").symlink_to(real_git_repo / ".git")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact has a symlinked .git entry" in reason


def test_ignored_artifact_nested_repo_corrupt_fails_closed(checkout):
    """A nested repo with corrupted git internals fails closed."""
    corrupt_dir = checkout[0] / "batch_state/reports/corrupt_repo"
    subprocess.run(["git", "init", str(corrupt_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (corrupt_dir / ".git/config").write_text("bad config syntax [[[")
    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact is an invalid nested git repository" in reason


def test_ignored_artifact_nested_repo_detached_head_unpushed_never_discarded(checkout):
    """AC-02 & P1: unpushed commits on a detached HEAD must refuse without a cleanup command."""
    detached_dir = checkout[0] / "batch_state/reports/detached_unpushed"
    detached_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", str(detached_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (detached_dir / "unpushed.txt").write_text("detached unpushed data\n")
    subprocess.run(["git", "add", "unpushed.txt"], cwd=detached_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "detached commit"], cwd=detached_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "checkout", "--detach", "HEAD"],
        cwd=detached_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact is a nested git repository with unpushed commits" in reason
    assert "unpushed work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_shell_quoting_in_cleanup_recommendation(checkout, tmp_path):
    """P1: paths with apostrophes or spaces in cleanup recommendations are safely shell-quoted."""
    upstream = tmp_path / "upstream"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    scratch_dir = checkout[0] / "batch_state/reports/probe' 'valuable"
    scratch_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(scratch_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    (scratch_dir / "probe.txt").write_text("pushed data\n")
    subprocess.run(["git", "add", "probe.txt"], cwd=scratch_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "probe"], cwd=scratch_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=scratch_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(
        ["git", "fetch", "origin"], cwd=scratch_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30
    )

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact is a nested git repository with no unpushed commits" in reason
    assert "clear with: " in reason

    import shlex

    cmd_part = reason.split("clear with: ")[1].split(";")[0].strip()
    tokens = shlex.split(cmd_part)
    assert tokens[:2] == ["rm", "-rf"]
    assert len(tokens) == 3, f"Expected exactly 1 target path, got: {tokens[2:]}"
    assert tokens[2] == "batch_state/reports/probe' 'valuable"


def test_ignored_artifact_nested_repo_unpushed_tag_never_discarded(checkout, tmp_path):
    """P1: unpushed commits referenced only by a local tag refuse removal without recommending deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/tag_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "base.txt").write_text("base\n")
    subprocess.run(["git", "add", "base.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Add commit on tag only, then move branch back to base
    (repo_dir / "tagged.txt").write_text("tagged commit\n")
    subprocess.run(["git", "add", "tagged.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "tagged commit"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "tag", "v0.9.0"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact is a nested git repository with unpushed commits" in reason
    assert "unpushed work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_unpushed_stash_never_discarded(checkout, tmp_path):
    """P1: unpushed commits referenced only by refs/stash refuse removal without recommending deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/stash_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "base.txt").write_text("base\n")
    subprocess.run(["git", "add", "base.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Modify file and stash changes
    (repo_dir / "base.txt").write_text("stashed modification\n")
    subprocess.run(["git", "stash"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact is a nested git repository with unpushed commits" in reason
    assert "unpushed work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_dirty_working_tree_never_discarded(checkout, tmp_path):
    """P1: repositories with uncommitted working-tree or index changes refuse removal without recommending deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/dirty_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "base.txt").write_text("base\n")
    subprocess.run(["git", "add", "base.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Modify file without committing
    (repo_dir / "base.txt").write_text("uncommitted dirty changes\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact is a nested git repository with uncommitted" in reason
    assert "uncommitted work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_fsmonitor_hook_disabled(checkout):
    """P1: nested repository core.fsmonitor hooks must never execute during inspection."""
    repo_dir = checkout[0] / "batch_state/reports/fsmonitor_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    marker = repo_dir / "hook_executed.marker"
    hook_script = repo_dir / "fsmonitor_hook.sh"
    hook_script.write_text(f"#!/bin/sh\ntouch '{marker}'\nexit 0\n")
    hook_script.chmod(0o755)
    subprocess.run(
        ["git", "config", "core.fsmonitor", str(hook_script)], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )

    guard(checkout)
    assert not marker.exists(), "core.fsmonitor hook script in nested repository was executed!"


def test_ignored_artifact_nested_repo_ignored_evidence_never_discarded(checkout, tmp_path):
    """P1: non-disposable ignored files in a nested repository must never be recommended for deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/ignored_evidence_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / ".gitignore").write_text("*.json\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "ignore json"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Add ignored evidence file
    (repo_dir / "valuable.json").write_text('{"evidence": "important probe"}')

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact is a nested git repository with uncommitted or ignored changes" in reason
    assert "uncommitted work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_reflog_only_commits_never_discarded(checkout, tmp_path):
    """P1: unpushed commits referenced only by reflogs must refuse removal without recommending deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/reflog_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "base.txt").write_text("base\n")
    subprocess.run(["git", "add", "base.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Add unpushed commit then reset --hard back to base
    (repo_dir / "reflog_work.txt").write_text("unpushed reflog work\n")
    subprocess.run(["git", "add", "reflog_work.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "commit", "-m", "unpushed reflog commit"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )
    subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact is a nested git repository with unpushed commits" in reason
    assert "unpushed work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_clean_filter_hook_rejected_without_execution(checkout):
    """P1: nested repository clean filter configuration is rejected before git execution."""
    repo_dir = checkout[0] / "batch_state/reports/clean_filter_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    marker = repo_dir / "clean_filter_executed.marker"
    script = repo_dir / "clean_hook.sh"
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n")
    script.chmod(0o755)
    subprocess.run(
        ["git", "config", "filter.probe.clean", str(script)], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )
    (repo_dir / ".gitattributes").write_text("* filter=probe\n")
    (repo_dir / "tracked.txt").write_text("initial content\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact is a nested git repository with executable or filter configuration" in reason
    assert not marker.exists(), "clean filter was executed!"


def test_ignored_artifact_nested_repo_assume_unchanged_never_discarded(checkout, tmp_path):
    """P1: tracked files marked assume-unchanged refuse removal without recommending deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/assume_unchanged_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "probe.txt").write_text("base content\n")
    subprocess.run(["git", "add", "probe.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Mark assume-unchanged and modify content
    subprocess.run(
        ["git", "update-index", "--assume-unchanged", "probe.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )
    (repo_dir / "probe.txt").write_text("modified concealed\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "concealed tracked changes" in reason
    assert "uncommitted work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_skip_worktree_never_discarded(checkout, tmp_path):
    """P1: tracked files marked skip-worktree refuse removal without recommending deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/skip_worktree_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "probe.txt").write_text("base content\n")
    subprocess.run(["git", "add", "probe.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Mark skip-worktree and modify content
    subprocess.run(
        ["git", "update-index", "--skip-worktree", "probe.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )
    (repo_dir / "probe.txt").write_text("modified concealed\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "concealed tracked changes" in reason
    assert "uncommitted work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_include_indirection_rejected_without_execution(checkout):
    """P1: nested repository include indirection is rejected before git execution."""
    repo_dir = checkout[0] / "batch_state/reports/include_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    marker = repo_dir / "filter_executed.marker"
    script = repo_dir / "clean_hook.sh"
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n")
    script.chmod(0o755)
    extra_cfg = repo_dir / "extra.config"
    extra_cfg.write_text(f'[filter "probe"]\n  clean = "{script}"\n')
    cfg = repo_dir / ".git" / "config"
    with open(cfg, "a", encoding="utf-8") as fp:
        fp.write(f"\n[include]\n  path = {extra_cfg}\n")
    (repo_dir / ".gitattributes").write_text("* filter=probe\n")
    (repo_dir / "tracked.txt").write_text("initial content\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "configuration indirection (include/includeIf)" in reason
    assert not marker.exists(), "clean filter was executed via include indirection!"
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_includeif_indirection_rejected_without_execution(checkout):
    """P1: nested repository includeIf indirection is rejected before git execution."""
    repo_dir = checkout[0] / "batch_state/reports/includeif_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    marker = repo_dir / "filter_executed.marker"
    script = repo_dir / "clean_hook.sh"
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n")
    script.chmod(0o755)
    extra_cfg = repo_dir / "extra.config"
    extra_cfg.write_text(f'[filter "probe"]\n  clean = "{script}"\n')
    cfg = repo_dir / ".git" / "config"
    with open(cfg, "a", encoding="utf-8") as fp:
        fp.write(f'\n[includeIf "gitdir:*"]\n  path = {extra_cfg}\n')
    (repo_dir / ".gitattributes").write_text("* filter=probe\n")
    (repo_dir / "tracked.txt").write_text("initial content\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "configuration indirection (include/includeIf)" in reason
    assert not marker.exists(), "clean filter was executed via includeIf indirection!"
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_config_worktree_filter_rejected_without_execution(checkout):
    """P1: nested repository config.worktree filter is rejected before git execution."""
    repo_dir = checkout[0] / "batch_state/reports/config_worktree_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(
        ["git", "config", "extensions.worktreeConfig", "true"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )
    marker = repo_dir / "filter_executed.marker"
    script = repo_dir / "clean_hook.sh"
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n")
    script.chmod(0o755)
    cfg_wt = repo_dir / ".git" / "config.worktree"
    cfg_wt.write_text(f'[filter "probe"]\n  clean = "{script}"\n')
    (repo_dir / ".gitattributes").write_text("* filter=probe\n")
    (repo_dir / "tracked.txt").write_text("initial content\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "artifact is a nested git repository with executable or filter configuration" in reason
    assert not marker.exists(), "clean filter was executed via config.worktree!"
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_core_worktree_redirection_never_discarded(checkout, tmp_path):
    """P1: nested repo with core.worktree pointing to clean dir never discards dirty artifact."""
    upstream = tmp_path / "upstream"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    clean_external = tmp_path / "clean_external"
    clean_external.mkdir()

    repo_dir = checkout[0] / "batch_state/reports/redirected_worktree_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "probe.txt").write_text("base content\n")
    subprocess.run(["git", "add", "probe.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Modify the actual artifact file so it has uncommitted bytes
    (repo_dir / "probe.txt").write_text("modified dirty content in artifact\n")

    # Mirror base file to external clean dir and point core.worktree there
    (clean_external / "probe.txt").write_text("base content\n")
    subprocess.run(
        ["git", "config", "core.worktree", str(clean_external)], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "redirected worktree (core.worktree)" in reason or "does not match expected directory" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_commondir_clean_filter_rejected_without_execution(checkout, tmp_path):
    """P1: nested repo with commondir clean filter is rejected before git execution."""
    common = tmp_path / "common"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(common)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    marker = tmp_path / "filter_executed.marker"
    script = tmp_path / "clean_hook.sh"
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n")
    script.chmod(0o755)
    with open(common / "config", "a", encoding="utf-8") as fp:
        fp.write(f'\n[filter "probe"]\n  clean = "{script}"\n')

    repo_dir = checkout[0] / "batch_state/reports/commondir_filter_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "-b", "main", str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "tracked.txt").write_text("initial content\n")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    (repo_dir / ".gitattributes").write_text("* filter=probe\n")
    (repo_dir / ".git/commondir").write_text(f"{common}\n")

    # Modify tracked file with same size so clean filter would trigger on status
    (repo_dir / "tracked.txt").write_text("updated content\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "executable or filter configuration" in reason or "commondir metadata indirection" in reason
    assert not marker.exists(), "commondir clean filter was executed!"
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_commondir_metadata_indirection_rejected(checkout, tmp_path):
    """P1: nested repo with commondir metadata indirection is rejected before git execution."""
    common = tmp_path / "clean_common"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(common)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/commondir_clean_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "-b", "main", str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "tracked.txt").write_text("initial content\n")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    (repo_dir / ".git/commondir").write_text(f"{common}\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "commondir metadata indirection" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_submodule_ignored_dirty_never_discarded(checkout, tmp_path):
    """P1: nested repo with submodule.<name>.ignore=all and dirty child file never discards work."""
    upstream_child = tmp_path / "upstream_child"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(upstream_child)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    upstream_parent = tmp_path / "upstream_parent"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(upstream_parent)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    child_init = tmp_path / "child_init"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream_child), str(child_init)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (child_init / "valuable.txt").write_text("child base content\n")
    subprocess.run(["git", "add", "valuable.txt"], cwd=child_init, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init child"], cwd=child_init, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/main"],
        cwd=child_init,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/submodule_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream_parent), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "parent.txt").write_text("parent content\n")
    subprocess.run(["git", "add", "parent.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init parent"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "-c",
            "core.hooksPath=/dev/null",
            "submodule",
            "add",
            "-b",
            "main",
            str(upstream_child),
            "sub",
        ],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "commit", "-m", "add submodule"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Configure submodule.sub.ignore=all
    subprocess.run(["git", "config", "submodule.sub.ignore", "all"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)

    # Modify child file
    (repo_dir / "sub/valuable.txt").write_text("modified dirty content in submodule\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "uncommitted or ignored changes" in reason or "unverified submodules" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_submodule_clean_never_recommended_for_rm_rf(checkout, tmp_path):
    """P1: nested repo with submodules never recommended for deletion without independent verification."""
    upstream_child = tmp_path / "upstream_child"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(upstream_child)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    upstream_parent = tmp_path / "upstream_parent"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(upstream_parent)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    child_init = tmp_path / "child_init"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream_child), str(child_init)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (child_init / "valuable.txt").write_text("child base content\n")
    subprocess.run(["git", "add", "valuable.txt"], cwd=child_init, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init child"], cwd=child_init, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/main"],
        cwd=child_init,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/clean_submodule_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream_parent), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "parent.txt").write_text("parent content\n")
    subprocess.run(["git", "add", "parent.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init parent"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "-c",
            "core.hooksPath=/dev/null",
            "submodule",
            "add",
            "-b",
            "main",
            str(upstream_child),
            "sub",
        ],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "commit", "-m", "add submodule"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "unverified submodules" in reason
    assert "submodules must not be discarded without independent verification" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_submodule_clean_filter_rejected_without_execution(checkout, tmp_path):
    """P1: nested repo with submodule clean filter is rejected before git execution."""
    upstream_child = tmp_path / "upstream_child"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(upstream_child)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    upstream_parent = tmp_path / "upstream_parent"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(upstream_parent)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    child_init = tmp_path / "child_init"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream_child), str(child_init)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (child_init / "valuable.txt").write_text("child base content\n")
    subprocess.run(["git", "add", "valuable.txt"], cwd=child_init, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init child"], cwd=child_init, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/main"],
        cwd=child_init,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/submodule_filter_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream_parent), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "parent.txt").write_text("parent content\n")
    subprocess.run(["git", "add", "parent.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init parent"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "-c",
            "core.hooksPath=/dev/null",
            "submodule",
            "add",
            "-b",
            "main",
            str(upstream_child),
            "sub",
        ],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "commit", "-m", "add submodule"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Configure clean filter in submodule gitdir
    marker = tmp_path / "filter_executed.marker"
    script = tmp_path / "clean_hook.sh"
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n")
    script.chmod(0o755)
    sub_gitdir = repo_dir / ".git/modules/sub"
    with open(sub_gitdir / "config", "a", encoding="utf-8") as fp:
        fp.write(f'\n[filter "probe"]\n  clean = "{script}"\n')
    (repo_dir / "sub/.gitattributes").write_text("* filter=probe\n")

    # Modify tracked file with same size so clean filter would trigger on status
    (repo_dir / "sub/valuable.txt").write_text("child same-size!\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "unverified submodules" in reason
    assert not marker.exists(), "submodule clean filter was executed!"
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_unregistered_gitlink_filter_rejected_without_execution(checkout, tmp_path):
    """P1: nested repo with unregistered gitlink (mode 160000) clean filter is rejected before git execution."""
    upstream_child = tmp_path / "upstream_child"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(upstream_child)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    upstream_parent = tmp_path / "upstream_parent"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(upstream_parent)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/unregistered_gitlink_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream_parent), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "parent.txt").write_text("parent content\n")
    subprocess.run(["git", "add", "parent.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init parent"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)

    # Clone child directly into sub directory (unregistered gitlink, no git submodule add)
    sub_dir = repo_dir / "sub"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream_child), str(sub_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (sub_dir / "valuable.txt").write_text("child base content\n")
    subprocess.run(["git", "add", "valuable.txt"], cwd=sub_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init child"], cwd=sub_dir, check=True, env=_GIT_ENV, timeout=30)

    # In parent, add sub directory as a gitlink (mode 160000 in index) without .gitmodules
    subprocess.run(["git", "add", "sub"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "commit", "-m", "add unregistered gitlink"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Configure clean filter in child repository gitdir
    marker = tmp_path / "unregistered_filter_executed.marker"
    script = tmp_path / "clean_hook.sh"
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n")
    script.chmod(0o755)
    with open(sub_dir / ".git/config", "a", encoding="utf-8") as fp:
        fp.write(f'\n[filter "probe"]\n  clean = "{script}"\n')
    (sub_dir / ".gitattributes").write_text("* filter=probe\n")

    # Modify child file so git status on child would evaluate the filter
    (sub_dir / "valuable.txt").write_text("child same-size!\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "unverified submodules" in reason
    assert not marker.exists(), "clean filter in unregistered gitlink was executed!"
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_unregistered_gitlink_no_child_gitdir_rejected(checkout, tmp_path):
    """P1: nested repo with indexed gitlink whose child .git was deleted is still rejected before status."""
    upstream_child = tmp_path / "upstream_child"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(upstream_child)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    upstream_parent = tmp_path / "upstream_parent"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(upstream_parent)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/unregistered_gitlink_nogit_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream_parent), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "parent.txt").write_text("parent content\n")
    subprocess.run(["git", "add", "parent.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init parent"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)

    sub_dir = repo_dir / "sub"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream_child), str(sub_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (sub_dir / "valuable.txt").write_text("child content\n")
    subprocess.run(["git", "add", "valuable.txt"], cwd=sub_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init child"], cwd=sub_dir, check=True, env=_GIT_ENV, timeout=30)

    subprocess.run(["git", "add", "sub"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "commit", "-m", "add unregistered gitlink"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Delete child .git directory so pure-python walk won't see .git in sub
    import shutil

    shutil.rmtree(sub_dir / ".git")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "unverified submodules" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_promisor_ext_helper_rejected_without_execution(checkout, tmp_path):
    """P1: nested repo with promisor ext:: transport helper is rejected without helper execution."""
    upstream = tmp_path / "upstream"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(upstream)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/promisor_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / "file.txt").write_text("content\n")
    subprocess.run(["git", "add", "file.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    marker = tmp_path / "helper_executed.marker"
    helper = tmp_path / "helper.sh"
    helper.write_text(f"#!/bin/sh\ntouch '{marker}'\nexit 1\n")
    helper.chmod(0o755)

    # Configure partial clone with ext:: remote helper
    subprocess.run(
        ["git", "config", "core.repositoryformatversion", "1"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )
    subprocess.run(
        ["git", "config", "extensions.partialclone", "origin"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )
    subprocess.run(
        ["git", "config", "remote.origin.promisor", "true"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )
    subprocess.run(
        ["git", "config", "remote.origin.url", f"ext::{helper}"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )
    subprocess.run(
        ["git", "config", "protocol.ext.allow", "always"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30
    )

    # Delete tree object to trigger lazy fetch if not disabled
    tree_sha = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
        env=_GIT_ENV,
        timeout=30,
    ).stdout.strip()
    tree_obj = repo_dir / ".git/objects" / tree_sha[:2] / tree_sha[2:]
    if tree_obj.exists():
        tree_obj.unlink()

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert not marker.exists(), "promisor ext:: transport helper was executed!"
    assert "executable or filter configuration" in reason or "invalid nested git repository" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_global_clean_filter_rejected_without_execution(checkout, tmp_path, monkeypatch):
    """P1: global clean filter configuration is ignored during inspection and never executed."""
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    marker = tmp_path / "global_filter_executed.marker"
    script = tmp_path / "global_filter.sh"
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n")
    script.chmod(0o755)

    (fake_home / ".gitconfig").write_text(
        f'[user]\n  name = Tester\n  email = test@example.com\n[filter "probe"]\n  clean = "{script}"\n'
    )

    repo_dir = checkout[0] / "batch_state/reports/global_filter_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    (repo_dir / ".gitattributes").write_text("* filter=probe\n")
    (repo_dir / "tracked.txt").write_text("initial content\n")
    # Select the fixture config explicitly: the test harness may suppress global
    # configuration through GIT_CONFIG_GLOBAL, overriding HOME's .gitconfig.
    fixture_env = {**_GIT_ENV, "HOME": str(fake_home), "GIT_CONFIG_GLOBAL": str(fake_home / ".gitconfig")}
    subprocess.run(
        ["git", "add", ".gitattributes", "tracked.txt"], cwd=repo_dir, check=True, env=fixture_env, timeout=30
    )
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, env=fixture_env, timeout=30)
    if marker.exists():
        marker.unlink()

    # Modify tracked file with same length to ensure git status evaluates filter if active
    (repo_dir / "tracked.txt").write_text("updated content\n")

    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(fake_home / ".gitconfig"))
    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "uncommitted or ignored changes" in reason
    assert not marker.exists(), "global clean filter was executed!"
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_trustctime_config_rejected(checkout):
    """P1: nested repository with core.trustctime configured is rejected before deletion advice."""
    repo_dir = checkout[0] / "batch_state/reports/trustctime_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "config", "core.trustctime", "false"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    (repo_dir / "file.txt").write_text("hello\n")
    subprocess.run(["git", "add", "file.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "executable or filter configuration" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_same_mtime_modified_bytes_rejected_without_deletion_advice(checkout, tmp_path):
    """P1: modified tracked bytes with restored mtime are verified independently and never recommended for deletion."""
    import time

    upstream = tmp_path / "upstream_same_mtime"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "-b", "main", str(upstream)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    repo_dir = checkout[0] / "batch_state/reports/stat_repo"
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    probe = repo_dir / "probe.txt"
    probe.write_text("original bytes\n")
    # Set mtime in past so it is non-racy with index timestamp
    past = time.time() - 100
    os.utime(probe, (past, past))
    subprocess.run(["git", "add", "probe.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    st = probe.stat()
    with open(probe, "r+b") as fp:
        fp.write(b"modified bytes\n")
    os.utime(probe, ns=(st.st_atime_ns, st.st_mtime_ns))

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata["retention_disposition"] == "retained"
    assert "uncommitted tracked changes" in reason or "uncommitted or ignored changes" in reason
    assert "clear with: rm -rf" not in reason


def _fd_count() -> int:
    return len(os.listdir("/proc/self/fd"))


def test_walk_reports_descriptor_type_not_a_byte_prefix(tmp_path):
    payload = b"symlink\npretend-target"
    note = tmp_path / "note.txt"
    note.write_bytes(payload)
    before = _fd_count()
    walked = wa._read_preserved_bytes(note, root=tmp_path)
    assert walked.file_type == "regular"
    assert walked.target is None
    assert walked.payload == payload
    link = tmp_path / "link"
    link.symlink_to("pretend-target")
    walked = wa._read_preserved_bytes(link, root=tmp_path)
    assert walked.file_type == "symlink"
    assert walked.target == "pretend-target"
    assert walked.payload == b"symlink\n" + os.fsencode("pretend-target")
    assert _fd_count() == before


def test_walk_refuses_a_target_longer_than_the_path_limit(tmp_path, monkeypatch):
    target = "too-long-target"
    (tmp_path / "link").symlink_to(target)
    real = os.pathconf

    def short_limit(path, name):
        if name == "PC_PATH_MAX":
            return 4
        return real(path, name)

    monkeypatch.setattr(os, "pathconf", short_limit)
    before = _fd_count()
    with pytest.raises(wa.SymlinkTargetRefusal) as caught:
        wa._read_preserved_bytes(tmp_path / "link", root=tmp_path)
    assert caught.value.kind == "target-too-long"
    assert caught.value.args == ("target-too-long",)
    assert target not in str(caught.value)
    assert _fd_count() == before
