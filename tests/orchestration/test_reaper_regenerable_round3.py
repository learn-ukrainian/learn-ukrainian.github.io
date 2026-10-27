"""Reproduce descriptor exhaustion, unsafe copy roots and repeated receipt scans."""

import hashlib
import json
import os
import signal
import subprocess
import sys

import pytest

from scripts.common import task_scratch
from scripts.fleet import ignored_task_output as output
from scripts.fleet import regenerable_output as classifier
from scripts.orchestration import reap_worktrees as rw
from tests.fleet.test_reaper_regenerable_cap import hermetic_base as hermetic_base
from tests.fleet.test_reaper_regenerable_cap import hermetic_reap as hermetic_reap
from tests.fleet.test_reaper_regenerable_cap import prepare, put, reap
from tests.orchestration.test_worktree_artifacts import assert_record_only


def test_killed_measurement_pins_use_existing_managed_recovery(tmp_path):
    """A killed measurer must not strand unregistered inode pins."""
    tree = tmp_path / "tree"
    tree.mkdir()
    source = put(tree, "source", b"retained bytes")
    root = tmp_path / "managed"
    env = dict(os.environ, LU_SCRATCH_ROOT=str(root))
    code = '''
import os, signal, sys
from pathlib import Path
from scripts.orchestration import reap_worktrees as rw
with rw._measured_removal({})(Path(sys.argv[1])):
    os.kill(os.getpid(), signal.SIGKILL)
'''
    result = subprocess.run([sys.executable, "-c", code, str(tree)], env=env, capture_output=True, text=True, timeout=60)
    assert result.returncode == -signal.SIGKILL, result.stderr
    assert list((root / "task-scratch").glob("*/lease.json"))
    assert source.stat().st_nlink == 2
    report = task_scratch.recover_orphans(
        root=root, apply=True, min_age_s=0, pressure_min_age_s=0, min_free_gb=0,
    )
    assert not report["errors"], report
    assert not list((root / "task-scratch").iterdir()), report
    assert source.read_bytes() == b"retained bytes"
    assert source.stat().st_nlink == 1


def test_descriptor_exhaustion_on_three_thousand_files(tmp_path):
    tree = tmp_path / "tree"
    tree.mkdir()
    for index in range(3000):
        put(tree, f"f{index}", b"x")
    # The review's reproducer, with a stricter service limit and real fixture removal.
    code = '''
import resource, shutil, sys
from pathlib import Path
from scripts.orchestration import reap_worktrees as rw
resource.setrlimit(resource.RLIMIT_NOFILE, (256, resource.getrlimit(resource.RLIMIT_NOFILE)[1]))
tree = Path(sys.argv[1])
measurement = {}
with rw._measured_removal(measurement)(tree):
    shutil.rmtree(tree)
assert rw._freed_bytes(measurement, None) == 3000
assert not tree.exists()
'''
    result = subprocess.run([sys.executable, "-c", code, str(tree)], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert not tree.exists()
    assert set(tmp_path.iterdir()) <= {task_scratch.resolve_scratch_root()}
    assert not list(task_scratch.task_scratch_namespace().iterdir())


@pytest.mark.parametrize("location", ["same", "other", "symlink", "primary"])
def test_external_copy_cannot_be_inside_any_worktree(hermetic_reap, location):
    """The review's same-tree and other-tree reproducers must now refuse."""
    repo, _, tree = prepare(hermetic_reap)
    if location == "same":
        put(tree, ".cache/evidence.txt", b"same bytes")
        name = ".worktrees/dispatch/codex/proof-cap/.cache/evidence.txt"
    elif location == "other":
        from tests import test_fleet_post_task_reap as fixtures
        other = fixtures._add_dispatch_worktree(repo, "codex", "live-other")
        put(other, ".cache/notes.txt", b"same bytes")
        name = ".worktrees/dispatch/codex/live-other/.cache/notes.txt"
    else:
        name = "data/atlas.db"
        if location == "symlink":
            put(tree, ".cache/copy.db", b"same bytes")
            (repo / "data").symlink_to(tree / ".cache", target_is_directory=True)
            name = "data/copy.db"
        else:
            put(repo, name, b"same bytes")
    put(tree, name, b"same bytes")
    assert classifier.is_regenerable_ignored_path(
        name, worktree=tree, tracked=set(), ignored={name}
    ) is (location == "primary")


def test_receipt_lookup_is_once_per_inventory_not_once_per_file(hermetic_reap, monkeypatch):
    repo, _, tree = prepare(hermetic_reap)
    for index in range(50):
        put(tree, f".cache/unique-{index}.txt", b"unique")
    original = output.matching_worktree_records
    calls = 0

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(output, "matching_worktree_records", counted)
    files = output._ignored_output_files(tree, repo, {})
    assert len(files) == 50
    assert calls <= 1


@pytest.mark.parametrize("kind", ["size", "bytes", "unchanged", "changed"])
def test_copy_proof_short_circuits_and_reuses_only_unchanged_identity(hermetic_reap, monkeypatch, kind):
    repo, _, tree = prepare(hermetic_reap)
    name = "data/atlas.db"
    put(tree, name, b"x" * (3 * 1024 * 1024))
    external = put(repo, name, b"x" * (3 * 1024 * 1024))
    if kind == "size":
        external.write_bytes(b"x")
    elif kind == "bytes":
        external.write_bytes(b"y" * (3 * 1024 * 1024))
    calls = 0
    original = classifier.os.read
    watched = {(path.stat().st_dev, path.stat().st_ino) for path in (tree / name, external)}

    def counted(fd, size):
        nonlocal calls
        info = os.fstat(fd)
        if (info.st_dev, info.st_ino) in watched:
            calls += 1
        return original(fd, size)

    monkeypatch.setattr(classifier.os, "read", counted)
    def classify():
        return classifier.is_regenerable_ignored_path(name, worktree=tree, tracked=set(), ignored={name})

    assert classify() is (kind in {"unchanged", "changed"})
    if kind == "size":
        assert calls == 0
    elif kind == "bytes":
        assert calls == 2
    else:
        reads = calls
        if kind == "changed":
            external.write_bytes(b"z" * (3 * 1024 * 1024))
            assert not classify()
            assert calls > reads
        else:
            assert classify()
            assert calls == reads


def test_worker_git_pointer_cannot_choose_primary_proof_root(hermetic_reap):
    repo, _, tree = prepare(hermetic_reap)
    name = "data/atlas.db"
    put(tree, name, b"worker bytes")
    put(repo, name, b"other bytes!")
    # A worker-controlled pointer cannot substitute a root with a matching copy.
    fake = tree.parent / "fake-primary"
    put(fake, name, b"worker bytes")
    (tree / ".git").write_text(f"gitdir: {fake}/.git/worktrees/proof-cap\n")
    assert not classifier.is_regenerable_ignored_path(name, worktree=tree, tracked=set(), ignored={name})


def test_copy_proof_without_trusted_caller_root_refuses(hermetic_reap):
    repo, _, tree = prepare(hermetic_reap)
    name = "data/atlas.db"
    put(tree, name, b"same")
    put(repo, name, b"same")
    token = classifier._COPY_PROOF_RUN.set(None)
    try:
        assert not classifier.is_regenerable_ignored_path(name, worktree=tree, tracked=set(), ignored={name})
    finally:
        classifier._COPY_PROOF_RUN.reset(token)


@pytest.mark.parametrize("primary_state", ["tracked", "ignored", "untracked"])
def test_primary_copy_requires_tracked_or_ignored_data_path(hermetic_reap, primary_state):
    repo, _, tree = prepare(hermetic_reap)
    name = "data/atlas.db"
    put(tree, name, b"same bytes")
    put(repo, name, b"same bytes")
    if primary_state != "ignored":
        ignore = repo / ".gitignore"
        ignore.write_text(ignore.read_text().replace("data/\n", ""))
    if primary_state == "tracked":
        from tests import test_fleet_post_task_reap as fixtures
        fixtures._run(["git", "add", name], cwd=repo)
    assert classifier.is_regenerable_ignored_path(
        name, worktree=tree, tracked=set(), ignored={name}
    ) is (primary_state != "untracked")


def test_registered_worktree_outside_dispatch_root_cannot_supply_proof(hermetic_reap):
    repo, _, tree = prepare(hermetic_reap)
    from tests import test_fleet_post_task_reap as fixtures
    other = repo / "data/other-worker"
    fixtures._run(["git", "worktree", "add", "-b", "other-worker", str(other), "main"], cwd=repo)
    put(other, ".cache/notes.txt", b"same bytes")
    name = "data/other-worker/.cache/notes.txt"
    put(tree, name, b"same bytes")
    assert not classifier.is_regenerable_ignored_path(name, worktree=tree, tracked=set(), ignored={name})


def test_copy_receipt_publication_failure_retains_tree(hermetic_reap, monkeypatch):
    repo, tasks, tree = prepare(hermetic_reap)
    put(tree, "site/dist/index.html", b"regenerable")

    def refuse(_self):
        raise ValueError("fixture publication failure")

    monkeypatch.setattr(classifier.CopyProofRun, "retain_receipts", refuse)
    row = reap(repo, tasks)
    assert row["action"] != "removed" and tree.exists(), row
    assert "copy proof receipt publication unproven" in row["error"]


@pytest.mark.parametrize("evidence_size", [12, 129])
def test_prior_preservation_locator_survives_new_receipt(hermetic_reap, monkeypatch, evidence_size):
    repo, tasks, tree = prepare(hermetic_reap)
    put(tree, "screenshots/first.png", b"earlier evidence")
    record_path = tasks / "proof-cap.json"
    record = json.loads(record_path.read_text())
    record["run_nonce"] = "proof-cap-run"
    earlier, _ = output.capture_abandon_output(tree, primary=repo, record=record)
    output.publish_abandon_output(tree, primary=repo, record=record, locator=earlier)
    earlier.update(
        schema=output.PRESERVED_ARTIFACTS_SCHEMA,
        owner="proof-cap", task_id="proof-cap", run_nonce=record["run_nonce"],
        worktree_sha256=hashlib.sha256(str(tree.resolve()).encode()).hexdigest(),
        retrieval_proof_sha256=output.verify_retrieval(repo, earlier),
    )
    record["preserved_artifacts"] = earlier
    record_path.write_text(json.dumps(record))
    put(tree, ".cache/new-evidence.txt", b"n" * evidence_size)
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 64)
    row = reap(repo, tasks)
    assert row["action"] == "removed" and not tree.exists(), row
    assert_record_only(row["preserved_artifacts"], {".cache/new-evidence.txt": b"n" * evidence_size})
    record = json.loads((tasks / "proof-cap.json").read_text())
    assert earlier["location"] in {
        entry["location"] for entry in record["preserved_artifacts"]["external_copies"]
    }
    assert (repo / earlier["location"] / "screenshots/first.png").read_bytes() == b"earlier evidence"


def test_primary_proof_cannot_follow_symlink_to_ignored_file(hermetic_reap):
    repo, _, tree = prepare(hermetic_reap)
    name = ".cache/source.bin"
    put(tree, name, b"same bytes")
    target = put(repo, ".cache/kept.bin", b"same bytes")
    (repo / name).symlink_to(target)
    assert not classifier.is_regenerable_ignored_path(name, worktree=tree, tracked=set(), ignored={name})


def test_measurement_refuses_changed_inode_between_hardlinked_names(tmp_path, monkeypatch):
    """Pin creation must not hide an earlier alias's changed ctime."""
    tree = tmp_path / "tree"
    tree.mkdir()
    source = put(tree, "a", b"original")
    os.link(source, tree / "z")
    before = source.stat()
    original_stat = rw.os.stat
    changed = False

    def mutate(name, *args, **kwargs):
        nonlocal changed
        if name == "z" and kwargs.get("dir_fd") is not None and not changed:
            changed = True
            source.write_bytes(b"modified")
            os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
        return original_stat(name, *args, **kwargs)

    monkeypatch.setattr(rw.os, "stat", mutate)
    with pytest.raises(rw.worktree_claims.RemovalStageRefused, match="inventory unproven"):
        with rw._measured_removal({})(tree):
            pytest.fail("changed bytes reached removal")
    assert source.read_bytes() == b"modified"
    assert source.stat().st_nlink == 2
    assert set(tmp_path.iterdir()) <= {tree, task_scratch.resolve_scratch_root()}
    assert not list(task_scratch.task_scratch_namespace().iterdir())
