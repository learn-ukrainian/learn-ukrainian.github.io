"""Deletion receipts must count verified unlinked bytes, excluding preservation."""

import contextlib
import hashlib
import os

import pytest

from scripts.orchestration import reap_worktrees as rw
from tests.fleet.test_reaper_regenerable_cap import hermetic_base as hermetic_base
from tests.fleet.test_reaper_regenerable_cap import hermetic_reap as hermetic_reap
from tests.fleet.test_reaper_regenerable_cap import prepare, put, reap
from tests.orchestration.test_reap_worktrees_clean_pushed import (
    _host_processes_out_of_scope as _host_processes_out_of_scope,
)
from tests.orchestration.test_reap_worktrees_clean_pushed import (
    _template as _template,
)
from tests.orchestration.test_reap_worktrees_clean_pushed import (
    age_tree,
    dispatch_tree,
)
from tests.orchestration.test_reap_worktrees_clean_pushed import (
    free_fuser as free_fuser,
)
from tests.orchestration.test_reap_worktrees_clean_pushed import (
    repo as repo,
)


@pytest.mark.parametrize("evidence_size", [0, 19])
def test_post_task_receipt_counts_unlinked_sizes_without_preserved_bytes(hermetic_reap, evidence_size):
    repo, tasks, tree = prepare(hermetic_reap)
    put(tree, "site/dist/index.html", b"build" * 31)
    if evidence_size:
        put(tree, ".cache/answer.txt", b"e" * evidence_size)
    expected = sum(path.stat().st_size for path in tree.rglob("*") if path.is_file())
    row = reap(repo, tasks)
    assert row["action"] == "removed", row
    assert row["freed_bytes"] == expected
    if evidence_size:
        receipt = row["preserved_artifacts"]
        assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
        assert "location" not in receipt
        assert receipt["paths"] == [{
            "path": ".cache/answer.txt", "size": evidence_size,
            "sha256": hashlib.sha256(b"e" * evidence_size).hexdigest(),
        }]
        assert not (repo / "batch_state/preserved").exists()


def test_hardlinked_bytes_are_not_claimed_as_freed(hermetic_reap):
    repo, tasks, tree = prepare(hermetic_reap)
    source = put(tree, "site/dist/index.html", b"still allocated")
    os.link(source, repo / "kept-build")
    expected = sum(path.stat().st_size for path in tree.rglob("*") if path.is_file() and path != source)
    row = reap(repo, tasks)
    assert row["action"] == "removed", row
    assert row["freed_bytes"] == expected
    assert (repo / "kept-build").read_bytes() == b"still allocated"


@pytest.mark.parametrize("preserved", [False, True])
def test_multiple_unlinked_names_count_one_inode_with_record_only_evidence(hermetic_reap, preserved):
    repo, tasks, tree = prepare(hermetic_reap)
    source = put(tree, "site/dist/index.html", b"shared inode")
    other = tree / (".cache/evidence.txt" if preserved else "site/dist/other.html")
    other.parent.mkdir(parents=True, exist_ok=True)
    os.link(source, other)
    expected = sum(path.stat().st_size for path in tree.rglob("*") if path.is_file() and path not in {source, other})
    expected += len(b"shared inode")
    row = reap(repo, tasks)
    assert row["action"] == "removed", row
    assert row["freed_bytes"] == expected


def test_refused_removal_reports_zero_not_pre_removal_size(hermetic_reap, monkeypatch):
    repo, tasks, tree = prepare(hermetic_reap)
    put(tree, "site/dist/index.html", b"build")
    original = rw.worktree_claims.git_worktree_remove

    def refuse(*args, **kwargs):
        kwargs["stage_removal"] = None
        return "fixture removal refused"

    monkeypatch.setattr(rw.worktree_claims, "git_worktree_remove", refuse)
    row = reap(repo, tasks)
    assert row["action"] != "removed" and tree.exists(), row
    assert row["freed_bytes"] == 0
    monkeypatch.setattr(rw.worktree_claims, "git_worktree_remove", original)


@pytest.mark.parametrize("apply", [True, False])
def test_clean_pushed_receipt_uses_measured_bytes_and_zero_for_dry_run(repo, free_fuser, apply):
    tree = dispatch_tree(repo)
    put(tree, "out/evidence.txt", b"preserved proof")
    age_tree(tree, repo, "task-a")
    expected = sum(path.stat().st_size for path in tree.rglob("*") if path.is_file())
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=not apply, actor="test")
    assert len(report.removed) == 1, report
    assert report.freed_bytes == (expected if apply else 0)
    assert report.as_dict()["removed"][0]["freed_bytes"] == (expected if apply else 0)
    assert tree.exists() is not apply


def test_dry_run_reports_nonzero_legacy_size_estimate(repo, free_fuser):
    tree = dispatch_tree(repo)
    put(tree, "out/build.bin", b"x" * (2 * 1024 * 1024))
    age_tree(tree, repo, "task-a")
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=True, actor="test")
    assert len(report.removed) == 1, report
    assert report.freed_mb == report.removed[0].size_mb >= 2
    assert report.freed_bytes == 0
    assert f"{report.freed_mb} MB" in rw.format_clean_pushed_report(report)
    assert tree.exists()


@pytest.mark.parametrize("mutation", ["replace", "unreadable", "fifo"])
def test_unproven_inventory_refuses_before_destructive_step(tmp_path, monkeypatch, mutation):
    tree = tmp_path / "tree"
    tree.mkdir()
    source = put(tree, "a.txt", b"original")
    put(tree, "z-directory/last.txt", b"later")
    if mutation == "fifo":
        os.mkfifo(tree / "pipe")
    original_listdir = rw.os.listdir
    original_open = rw.os.open

    def mutate_later(fd):
        result = original_listdir(fd)
        if mutation == "replace" and "last.txt" in result and source.read_bytes() == b"original":
            replacement = source.with_suffix(".new")
            replacement.write_bytes(b"replaced")
            replacement.replace(source)
        return result

    def unreadable(path, *args, **kwargs):
        if mutation == "unreadable" and path == "a.txt":
            raise PermissionError("fixture unreadable")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(rw.os, "listdir", mutate_later)
    monkeypatch.setattr(rw.os, "open", unreadable)
    with pytest.raises(rw.worktree_claims.RemovalStageRefused, match="inventory unproven"):
        with rw._measured_removal({})(tree):
            pytest.fail("unproven bytes reached the destructive step")
    assert source.exists()


def test_partial_unlink_counts_only_the_inode_actually_unlinked(tmp_path):
    tree = tmp_path / "tree"
    tree.mkdir()
    first = put(tree, "first", b"one")
    put(tree, "second", b"not removed")
    measured = {}
    with contextlib.suppress(RuntimeError):
        with rw._measured_removal(measured)(tree):
            first.unlink()
            raise RuntimeError("partial deletion")
    assert rw._freed_bytes(measured, None) == 3
    assert rw._freed_bytes(measured, {"paths": [{"path": "first"}]}) == 0
    assert rw._freed_bytes(measured, {"mode": "record-only", "paths": [{"path": "first"}]}) == 3
