"""Unsafe copy roots and repeated receipt scans in the regenerable-output copy proof."""

import os

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.fleet import regenerable_output as classifier
from tests.fleet.test_reaper_regenerable_cap import prepare, put
from tests.fleet.test_reaper_regenerable_cap import proof_repo as proof_repo
from tests.orchestration.test_worktree_git import _add_dispatch_worktree, _run
from tests.orchestration.test_worktree_git import hermetic_repo as hermetic_repo


@pytest.mark.parametrize("location", ["same", "other", "symlink", "primary"])
def test_external_copy_cannot_be_inside_any_worktree(proof_repo, location):
    """The review's same-tree and other-tree reproducers must now refuse."""
    repo, _, tree = prepare(proof_repo)
    if location == "same":
        put(tree, ".cache/evidence.txt", b"same bytes")
        name = ".worktrees/dispatch/codex/proof-cap/.cache/evidence.txt"
    elif location == "other":
        other = _add_dispatch_worktree(repo, "codex", "live-other")
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
    assert classifier.is_regenerable_ignored_path(name, worktree=tree, tracked=set(), ignored={name}) is (
        location == "primary"
    )


def test_receipt_lookup_is_once_per_inventory_not_once_per_file(proof_repo, monkeypatch):
    repo, _, tree = prepare(proof_repo)
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
def test_copy_proof_short_circuits_and_reuses_only_unchanged_identity(proof_repo, monkeypatch, kind):
    repo, _, tree = prepare(proof_repo)
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


def test_worker_git_pointer_cannot_choose_primary_proof_root(proof_repo):
    repo, _, tree = prepare(proof_repo)
    name = "data/atlas.db"
    put(tree, name, b"worker bytes")
    put(repo, name, b"other bytes!")
    # A worker-controlled pointer cannot substitute a root with a matching copy.
    fake = tree.parent / "fake-primary"
    put(fake, name, b"worker bytes")
    (tree / ".git").write_text(f"gitdir: {fake}/.git/worktrees/proof-cap\n")
    assert not classifier.is_regenerable_ignored_path(name, worktree=tree, tracked=set(), ignored={name})


def test_copy_proof_without_trusted_caller_root_refuses(proof_repo):
    repo, _, tree = prepare(proof_repo)
    name = "data/atlas.db"
    put(tree, name, b"same")
    put(repo, name, b"same")
    token = classifier._COPY_PROOF_RUN.set(None)
    try:
        assert not classifier.is_regenerable_ignored_path(name, worktree=tree, tracked=set(), ignored={name})
    finally:
        classifier._COPY_PROOF_RUN.reset(token)


@pytest.mark.parametrize("primary_state", ["tracked", "ignored", "untracked"])
def test_primary_copy_requires_tracked_or_ignored_data_path(proof_repo, primary_state):
    repo, _, tree = prepare(proof_repo)
    name = "data/atlas.db"
    put(tree, name, b"same bytes")
    put(repo, name, b"same bytes")
    if primary_state != "ignored":
        ignore = repo / ".gitignore"
        ignore.write_text(ignore.read_text().replace("data/\n", ""))
    if primary_state == "tracked":
        _run(["git", "add", name], cwd=repo)
    assert classifier.is_regenerable_ignored_path(name, worktree=tree, tracked=set(), ignored={name}) is (
        primary_state != "untracked"
    )


def test_registered_worktree_outside_dispatch_root_cannot_supply_proof(proof_repo):
    repo, _, tree = prepare(proof_repo)
    other = repo / "data/other-worker"
    _run(["git", "worktree", "add", "-b", "other-worker", str(other), "main"], cwd=repo)
    put(other, ".cache/notes.txt", b"same bytes")
    name = "data/other-worker/.cache/notes.txt"
    put(tree, name, b"same bytes")
    assert not classifier.is_regenerable_ignored_path(name, worktree=tree, tracked=set(), ignored={name})


def test_primary_proof_cannot_follow_symlink_to_ignored_file(proof_repo):
    repo, _, tree = prepare(proof_repo)
    name = ".cache/source.bin"
    put(tree, name, b"same bytes")
    target = put(repo, ".cache/kept.bin", b"same bytes")
    (repo / name).symlink_to(target)
    assert not classifier.is_regenerable_ignored_path(name, worktree=tree, tracked=set(), ignored={name})
