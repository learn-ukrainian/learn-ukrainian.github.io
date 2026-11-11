"""Settle-time worktree removal and retention, scheduled recovery and publication proof."""

import json
import os
import signal
import time
from pathlib import Path

import pytest

from scripts.dispatcher import git, worker
from tests.dispatcher.conftest import await_file, in_process_repo, local_branches, run_git


def test_read_only_task_removes_its_worktree_at_settle(sandbox):
    """Defect: the dispatcher left every task worktree it created for a separate reaper."""
    record = sandbox.settle(sandbox.dispatch())
    assert record["status"] == "done"
    assert not Path(record["worktree_path"]).exists()
    assert (record["worktree_disposition"], record["worktree_disposition_reason"]) == ("removed", "clean")
    assert record["worktree_branch"] not in local_branches(sandbox.repo)
    assert Path(record["result_file"]).read_text() == "literal final response"


@pytest.mark.parametrize("model,flags,status", [
    ("pushed", [], "done"),
    # A fix round starts at its publish branch's tip; the task branch never exists on origin.
    ("echo", ["--branch", "release"], "no_deliverable"),
])
def test_pushed_write_task_removes_its_worktree_at_settle(sandbox, model, flags, status):
    """Defect: published write work kept its worktree and local branch after the task ended."""
    run_git(sandbox.repo, "push", "origin", "main:release")
    record = sandbox.settle(sandbox.dispatch(model, "--mode", "workspace-write", *flags),
                            expected=0 if status == "done" else 1)
    assert record["status"] == status
    assert not Path(record["worktree_path"]).exists()
    assert (record["worktree_disposition"], record["worktree_disposition_reason"]) == ("removed", "clean")
    assert record["worktree_branch"] not in local_branches(sandbox.repo)
    published = record.get("publish_branch") or record["worktree_branch"]
    assert run_git(sandbox.remote, "rev-parse", f"refs/heads/{published}") == record["head_sha"]


@pytest.mark.parametrize("model,flags,reason", [
    ("pushed-dirty", [], "dirty"),
    ("unpushed", [], "unpublished"),
    ("unpushed", ["--branch", "release"], "remote_mismatch"),
])
def test_dirty_or_unpublished_write_task_keeps_worktree_with_reason(sandbox, model, flags, reason):
    """Defect: settlement must never discard uncommitted or unpublished work, and must say why it kept it."""
    run_git(sandbox.repo, "push", "origin", "main:release")
    record = sandbox.settle(sandbox.dispatch(model, "--mode", "workspace-write", *flags), expected=1)
    assert record["status"] == "no_deliverable"
    assert (record["worktree_disposition"], record["worktree_disposition_reason"]) == ("retained", reason)
    tree = Path(record["worktree_path"])
    assert (tree / "delivered.txt").exists()
    assert record["worktree_branch"] in local_branches(sandbox.repo)
    assert run_git(tree, "rev-parse", "HEAD") == record["head_sha"]


def test_dirty_worktree_is_retried_and_removed_once_its_changes_are_gone(sandbox):
    """Defect: a tree retained as dirty was never looked at again, even after only ignored files were left."""
    record = sandbox.settle(sandbox.dispatch("pushed-dirty", "--mode", "workspace-write"), expected=1)
    assert (record["worktree_disposition"], record["worktree_disposition_reason"]) == ("retained", "dirty")
    assert record["worktree_disposition_detail"]
    tree = Path(record["worktree_path"])
    sandbox.sweep()  # scheduled recovery finds the same change and keeps the tree
    kept = json.loads((sandbox.tasks / f"{record['task_id']}.json").read_text())
    assert (kept["worktree_disposition"], kept["worktree_disposition_reason"]) == ("retained", "dirty")
    assert tree.is_dir()
    run_git(tree, "reset", "--hard")
    run_git(tree, "clean", "-fd")
    (tree / ".pytest_cache").mkdir()
    (tree / ".pytest_cache/ignored.txt").write_text("ignored output\n")
    (sandbox.repo / ".git/info/exclude").write_text("/.pytest_cache/\n")
    sandbox.sweep()
    settled = json.loads((sandbox.tasks / f"{record['task_id']}.json").read_text())
    assert (settled["worktree_disposition"], settled["worktree_disposition_reason"]) == ("removed", "clean")
    assert "worktree_disposition_detail" not in settled
    assert not tree.exists()


def preserved_copy(sandbox, record, relative):
    """The bytes settlement copied out of the task's worktree before removing it."""
    receipt = record["branch_holder_archive"]
    assert (receipt["owner"], receipt["retention_disposition"]) == (record["task_id"], "retrieved")
    return (sandbox.repo / receipt["location"] / relative).read_text()


@pytest.mark.parametrize("model,status", [("dirty", "no_deliverable"), ("capacity-dirty", "rate_limited")])
def test_untracked_scratch_is_preserved_and_the_worktree_removed_at_settle(sandbox, model, status):
    """Defect (FR-01): an untracked file a worker left kept its worktree forever; copy it out, then remove."""
    record = sandbox.settle(sandbox.dispatch(model, "--mode", "workspace-write"), expected=1)
    assert record["status"] == status
    assert (record["worktree_disposition"], record["worktree_disposition_reason"]) == ("removed", "clean")
    assert not Path(record["worktree_path"]).exists()
    assert record["worktree_branch"] not in local_branches(sandbox.repo)
    assert preserved_copy(sandbox, record, "delivered.txt") == "literal delivered value\n"
    assert json.loads((sandbox.tasks / f"{record['task_id']}.json").read_text()) == record


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_tracked_edit_hidden_by_an_index_flag_keeps_the_worktree(sandbox, flag):
    """Review F1: status omits edits under these flags, so untracked scratch beside one forced a removal."""
    task = sandbox.dispatch("blocked", "--mode", "workspace-write")
    await_file(sandbox.tasks / f"{task[0]}.started")
    tree = Path(json.loads((sandbox.tasks / f"{task[0]}.json").read_text())["worktree_path"])
    run_git(tree, "update-index", flag, "scripts/dispatch.py")
    (tree / "scripts/dispatch.py").write_text("uncommitted tracked edit\n")
    (tree / "scratch.txt").write_text("scratch\n")
    (sandbox.tasks / f"{task[0]}.release").touch()
    record = sandbox.settle(task, expected=1)
    assert (record["worktree_disposition"], record["worktree_disposition_reason"]) == ("retained", "dirty")
    assert (tree / "scripts/dispatch.py").read_text() == "uncommitted tracked edit\n"


def test_lingering_provider_process_is_ended_at_settlement_before_the_worktree_goes(sandbox):
    """Defect (FR-45, #12520): a provider child alive past settlement kept the tree with no retry; now the
    settling supervisor ends it, so the tree is released only after the process is gone."""
    task = sandbox.dispatch("tree")
    grandchild = int(await_file(sandbox.tasks / f"{task[0]}.grandchild"))
    (sandbox.tasks / f"{task[0]}.release").touch()
    record = sandbox.settle(task)
    assert (record["worktree_disposition"], record["worktree_disposition_reason"]) == ("removed", "clean")
    assert worker._identity(grandchild) is None
    assert not Path(record["worktree_path"]).exists()


def test_settlement_removes_only_recreatable_caches_from_the_task_output_directories(sandbox):
    """Defect (C-4946(a)): settled tasks kept venv, node_modules and __pycache__ copies in their .artifacts and
    .evidence directories for good. Settlement and the scheduled sweep remove those caches from a finished
    task only, keep every other file, and remove a cache-named link without following it."""
    task = sandbox.dispatch("blocked")
    await_file(sandbox.tasks / f"{task[0]}.started")
    artifacts, evidence = sandbox.tasks / f"{task[0]}.artifacts", sandbox.tasks / f"{task[0]}.evidence"
    caches = [artifacts / "venv", artifacts / "node_modules", artifacts / "probe/__pycache__"]
    for cache in caches:
        (cache / "sub").mkdir(parents=True)
        (cache / "sub/file").write_text("re-creatable")
    kept = {artifacts / "run.log": "log", artifacts / "probe/result.json": "{}", evidence / "receipt.json": "{}"}
    evidence.mkdir()
    for path, text in kept.items():
        path.write_text(text)
    elsewhere = sandbox.tasks.parent / "linked-cache"
    elsewhere.mkdir()
    (elsewhere / "outside.txt").write_text("not the task's")
    (evidence / ".cache").symlink_to(elsewhere, target_is_directory=True)

    sandbox.sweep()
    assert all((cache / "sub/file").exists() for cache in caches)
    assert (evidence / ".cache").is_symlink()

    (sandbox.tasks / f"{task[0]}.release").touch()
    record = sandbox.settle(task)
    assert record["status"] == "done" and "task_cache_residue" not in record
    assert not any(os.path.lexists(cache) for cache in [*caches, evidence / ".cache"])
    assert {path: path.read_text() for path in kept} == kept
    assert (elsewhere / "outside.txt").read_text() == "not the task's"

    # A cache that appears once the task has settled is removed by the scheduled sweep.
    (artifacts / ".venv/lib").mkdir(parents=True)
    sandbox.sweep()
    assert not (artifacts / ".venv").exists()
    assert {path: path.read_text() for path in kept} == kept


def _owner_rwx(path: Path) -> None:
    """Give owner rwx so a failed case cannot leave a mode-0555 tree for tmp cleanup."""
    if path.is_symlink() or not path.exists():
        return
    path.chmod(0o755)
    if path.is_dir():
        for child in path.iterdir():
            _owner_rwx(child)


def test_settlement_removes_a_read_only_cache_subtree(sandbox):
    """Defect class: read-only cache residue. A cache directory whose children are mode 0555
    (the Go module-cache layout) made removal raise PermissionError, so the residue was
    retried every hour and never cleared. Settlement and the hourly sweep remove that tree
    from a finished task, leave an active task's tree in place, and do not change a sibling
    directory's mode or a file outside the task outputs."""
    task = sandbox.dispatch("blocked")
    await_file(sandbox.tasks / f"{task[0]}.started")
    artifacts, evidence = sandbox.tasks / f"{task[0]}.artifacts", sandbox.tasks / f"{task[0]}.evidence"
    evidence.mkdir()
    (evidence / "receipt.json").write_text("{}")
    trees = []
    for root_name, cache_name in ((artifacts, ".cache"), (evidence, "pip-cache")):
        sub = root_name / cache_name / "ro" / "sub"
        sub.mkdir(parents=True)
        (sub / "mod").write_text("module")
        (root_name / cache_name / "ro").chmod(0o555)
        sub.chmod(0o555)
        trees.append(root_name / cache_name)
    (artifacts / "run.log").write_text("log")
    sibling = artifacts / "notes"
    sibling.mkdir()
    (sibling / "keep.txt").write_text("keep")
    outside = sandbox.tasks.parent / "outside-keep.txt"
    outside.write_text("outside")
    try:
        sibling.chmod(0o555)
        sandbox.sweep()
        assert all((tree / "ro/sub/mod").read_text() == "module" for tree in trees)
        assert sibling.stat().st_mode & 0o777 == 0o555

        (sandbox.tasks / f"{task[0]}.release").touch()
        record = sandbox.settle(task)
        assert record["status"] == "done"
        assert [tree.exists() for tree in trees] == [False, False], record.get("task_cache_residue")
        assert "task_cache_residue" not in record
        for root_name, cache_name in ((artifacts, ".cache"), (evidence, "pip-cache")):
            sub = root_name / cache_name / "ro" / "sub"
            sub.mkdir(parents=True)
            (sub / "mod").write_text("module")
            (root_name / cache_name / "ro").chmod(0o555)
            sub.chmod(0o555)
        sandbox.sweep()
        disk = json.loads((sandbox.tasks / f"{task[0]}.json").read_text())
        assert [tree.exists() for tree in trees] == [False, False], disk.get("task_cache_residue")
        assert "task_cache_residue" not in disk
        assert (artifacts / "run.log").read_text() == "log"
        assert (evidence / "receipt.json").read_text() == "{}"
        assert (sibling / "keep.txt").read_text() == "keep"
        assert sibling.stat().st_mode & 0o777 == 0o555
        assert outside.read_text() == "outside"
    finally:
        _owner_rwx(sibling)
        for tree in trees:
            _owner_rwx(tree)


def test_settlement_removes_a_dangling_or_file_cache_link(sandbox):
    """Defect class: cache-named link kept. fwalk puts a dangling link and a link to a file in
    ``files``, which cache removal never inspected, so both stayed. Settlement and the hourly
    sweep unlink those names and leave the file target, a non-cache symlink, and an active
    task's links in place."""
    task = sandbox.dispatch("blocked")
    await_file(sandbox.tasks / f"{task[0]}.started")
    artifacts, evidence = sandbox.tasks / f"{task[0]}.artifacts", sandbox.tasks / f"{task[0]}.evidence"
    artifacts.mkdir()
    evidence.mkdir()
    (evidence / "receipt.json").write_text("{}")
    (artifacts / "run.log").write_text("log")
    target = sandbox.tasks.parent / "cache-file-target"
    target.write_text("target-bytes")
    note_target = sandbox.tasks.parent / "note-target"
    note_target.write_text("note")
    dangling = artifacts / "node_modules"
    file_link = evidence / "venv"
    other = artifacts / "notes"
    dangling.symlink_to("/nonexistent")
    file_link.symlink_to(target)
    other.symlink_to(note_target)
    links = (dangling, file_link)

    sandbox.sweep()
    assert all(link.is_symlink() for link in links)
    assert target.read_text() == "target-bytes"

    (sandbox.tasks / f"{task[0]}.release").touch()
    record = sandbox.settle(task)
    assert record["status"] == "done"
    assert [os.path.lexists(link) for link in links] == [False, False], record.get("task_cache_residue")
    assert "task_cache_residue" not in record
    dangling.symlink_to("/nonexistent")
    file_link.symlink_to(target)
    sandbox.sweep()
    disk = json.loads((sandbox.tasks / f"{task[0]}.json").read_text())
    assert [os.path.lexists(link) for link in links] == [False, False], disk.get("task_cache_residue")
    assert "task_cache_residue" not in disk
    assert target.read_text() == "target-bytes"
    assert note_target.read_text() == "note"
    assert other.is_symlink() and other.read_text() == "note"
    assert (artifacts / "run.log").read_text() == "log"
    assert (evidence / "receipt.json").read_text() == "{}"


def test_settlement_after_a_dispatcher_module_changes_on_disk_removes_the_worktree(sandbox):
    """Defect (#12634): a worker running while a dispatcher change landed settled with old in-memory and new
    on-disk modules, so removal failed with an ImportError and left a clean tree. The worker now loads its
    post-start code when it starts, so a later edit on disk never reaches its settlement."""
    task = sandbox.dispatch("blocked")
    await_file(sandbox.tasks / f"{task[0]}.started")
    # The change a merge brings: store gains a function, and the module that settlement loads imports it.
    with (sandbox.repo / "scripts/dispatcher/store.py").open("a") as stream:
        stream.write("\n\ndef added_after_the_worker_started():\n    return None\n")
    consumer = sandbox.repo / "scripts/fleet/ignored_task_output.py"
    consumer.write_text("from scripts.dispatcher.store import added_after_the_worker_started\n" + consumer.read_text())
    (sandbox.tasks / f"{task[0]}.release").touch()
    record = sandbox.settle(task)
    assert (record["worktree_disposition"], record["worktree_disposition_reason"]) == ("removed", "clean"), (
        record.get("worktree_disposition_detail"))
    assert not Path(record["worktree_path"]).exists()


def test_dispatch_and_worker_exit_leave_unrelated_retained_worktrees_unchanged(sandbox):
    """Defect: unrelated admission and exit repeatedly rewrite and retry retained worktrees."""
    record = sandbox.settle(sandbox.dispatch("pushed-dirty", "--mode", "workspace-write"), expected=1)
    record_file = sandbox.tasks / f"{record['task_id']}.json"
    tree = Path(record["worktree_path"])
    with record_file.open("rb") as retained:
        before = retained.read()
        inode = os.fstat(retained.fileno()).st_ino
        task = sandbox.dispatch()
        assert record_file.read_bytes() == before
        assert record_file.stat().st_ino == inode, "admission retried an unrelated retained worktree"
        own = sandbox.settle(task)
        assert record_file.read_bytes() == before
        assert record_file.stat().st_ino == inode, "worker exit retried an unrelated retained worktree"
        assert (tree / "delivered.txt").read_text() == "uncommitted delivery\n"
        assert own["worktree_disposition"] == "removed"
        assert not Path(own["worktree_path"]).exists()
        sandbox.sweep()
        assert record_file.stat().st_ino != inode, "scheduled settlement did not retry the retained worktree"
    retried = json.loads(record_file.read_text())
    assert (retried["worktree_disposition"], retried["worktree_disposition_reason"]) == ("retained", "dirty")
    assert tree.is_dir()
    assert (tree / "delivered.txt").read_text() == "uncommitted delivery\n"
    assert run_git(tree, "rev-parse", "HEAD") == record["head_sha"]


def settled_by_scheduled_sweep(sandbox, retained_id, before_release=lambda _kept: None):
    """Retry a retained tree explicitly, as scheduled cleanup does.

    ``before_release`` sees the first sweep's retained record. A second sweep retries it
    after the callback has had the opportunity to clear the cause.
    """
    record_file = sandbox.tasks / f"{retained_id}.json"
    sandbox.sweep()
    with record_file.open("rb") as retained:
        before = os.fstat(retained.fileno()).st_ino
        before_release(json.loads(retained.read()))
        sandbox.sweep()
        assert record_file.stat().st_ino != before, "scheduled settlement never retried the retained worktree"
    return json.loads(record_file.read_text())


@pytest.mark.parametrize("model,reason", [("pushed-dirty", "dirty"), ("unpushed", "unpublished")])
def test_settlement_retry_keeps_a_worktree_that_still_holds_content(sandbox, model, reason):
    """The retry removes only with settlement's proofs: uncommitted or unpublished work stays."""
    record = sandbox.settle(sandbox.dispatch(model, "--mode", "workspace-write"), expected=1)
    assert (record["worktree_disposition"], record["worktree_disposition_reason"]) == ("retained", reason)
    retried = settled_by_scheduled_sweep(sandbox, record["task_id"])
    assert (retried["worktree_disposition"], retried["worktree_disposition_reason"]) == ("retained", reason)
    tree = Path(record["worktree_path"])
    assert (tree / "delivered.txt").exists()
    assert run_git(tree, "rev-parse", "HEAD") == record["head_sha"]


def process_group_exists(pgid):
    """Settlement's own liveness probe (worker._provider_alive): a group with any member, zombies included."""
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    return True


def test_scheduled_recovery_settles_terminal_task_left_by_crash(sandbox):
    """Defect: a supervisor killed before settlement left its worktree behind for good."""
    task = sandbox.dispatch("blocked")
    provider = int(await_file(sandbox.tasks / f"{task[0]}.started"))
    record = json.loads((sandbox.tasks / f"{task[0]}.json").read_text())
    os.kill(record["pid"], signal.SIGKILL)
    deadline = time.monotonic() + 10
    while worker._identity(record["pid"]) == record["process_start"]:
        assert time.monotonic() < deadline, "supervisor survived SIGKILL"
        time.sleep(0.02)
    os.killpg(provider, signal.SIGKILL)
    # The orphaned group exists, as zombies, until init reaps it; settlement rightly keeps the tree until then.
    deadline = time.monotonic() + 10
    while process_group_exists(provider):
        assert time.monotonic() < deadline, "provider process group survived SIGKILL"
        time.sleep(0.02)
    assert Path(record["worktree_path"]).is_dir()
    sandbox.sweep()
    crashed = json.loads((sandbox.tasks / f"{task[0]}.json").read_text())
    assert crashed["status"] == "crashed"
    assert not Path(record["worktree_path"]).exists()
    assert (crashed["worktree_disposition"], crashed["worktree_disposition_reason"]) == ("removed", "clean")
    assert record["worktree_branch"] not in local_branches(sandbox.repo)


@pytest.mark.parametrize("redirect", ["set-url", "insteadOf"])
def test_settlement_proves_publication_only_on_the_recorded_canonical_remote(sandbox, monkeypatch, redirect):
    """Defect (F1): settlement trusted the shared, mutable origin instead of the URL recorded at dispatch."""
    record = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    assert record["worktree_disposition_reason"] == "unpublished"
    assert record["worktree_remote_url"] == str(sandbox.remote)
    tree = Path(record["worktree_path"])
    decoy = sandbox.repo.parent / "decoy.git"
    run_git(sandbox.repo, "init", "--bare", str(decoy))
    run_git(tree, "push", str(decoy), f"HEAD:refs/heads/{record['worktree_branch']}")
    if redirect == "set-url":
        run_git(sandbox.repo, "remote", "set-url", "origin", str(decoy))
    else:
        run_git(sandbox.repo, "config", f"url.{decoy}.insteadOf", str(sandbox.remote))
    in_process_repo(sandbox, monkeypatch)
    assert git.settle_worktree(record) == dict(worktree_disposition="retained", worktree_disposition_reason="unpublished")
    assert tree.is_dir()
    assert record["worktree_branch"] in local_branches(sandbox.repo)


def test_write_task_merged_into_main_counts_as_published_after_its_branch_is_deleted(sandbox, monkeypatch):
    """CTO D3: work the canonical main already contains is published, though its branch left the remote."""
    record = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    tree, branch = Path(record["worktree_path"]), record["worktree_branch"]
    run_git(tree, "push", str(sandbox.remote), f"HEAD:refs/heads/{branch}")
    run_git(tree, "push", str(sandbox.remote), "HEAD:refs/heads/main")
    run_git(tree, "push", str(sandbox.remote), f":refs/heads/{branch}")
    in_process_repo(sandbox, monkeypatch)
    assert git.settle_worktree(record) == dict(worktree_disposition="removed", worktree_disposition_reason="clean")
    assert not tree.exists()
    assert branch not in local_branches(sandbox.repo)


def test_publication_check_accepts_head_contained_in_successor_branch(sandbox, monkeypatch):
    """Defect class: successor-branch ancestry was missed by ordinary publication checks."""
    record = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    tree = Path(record["worktree_path"])
    successor = run_git(tree, "commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m", "successor")
    run_git(tree, "push", str(sandbox.remote), f"{successor}:refs/heads/successor")
    in_process_repo(sandbox, monkeypatch)
    verification_git = git._verification_git
    fetches = []

    def counted(path, *args, **kwargs):
        if args[0] == "fetch":
            fetches.append(args)
        return verification_git(path, *args, **kwargs)

    monkeypatch.setattr(git, "_verification_git", counted)
    assert git.settle_worktree(record) == dict(worktree_disposition="removed", worktree_disposition_reason="clean")
    assert len(fetches) == 1
    assert not tree.exists()


@pytest.mark.parametrize("unknown", [False, True])
def test_settlement_ignores_setup_links_and_regenerable_caches_and_records_unknown_ignored_files(
        sandbox, monkeypatch, unknown):
    """Defect: a clean published write task kept its worktree for the links, caches and ignored output it held.

    Ignored output follows the removal chokepoint's rule: inventoried in the task record, then removed.
    """
    record = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    tree, branch = Path(record["worktree_path"]), record["worktree_branch"]
    # As in the project, tracked files keep these directories from collapsing into one ignored entry.
    for tracked in ("data/README", "site/README", ".githooks/pre-commit"):
        (tree / tracked).parent.mkdir(exist_ok=True)
        (tree / tracked).write_text("tracked\n")
    run_git(tree, "add", ".")
    run_git(tree, "commit", "-m", "tracked directories")
    run_git(tree, "push", str(sandbox.remote), f"HEAD:refs/heads/{branch}")
    ignored = [*git.DATABASE_LINKS, *git.NODE_LINKS, "scripts/__pycache__/", ".pytest_cache/", ".ruff_cache/",
               ".mypy_cache/", ".pytest_breadcrumbs/", ".githooks/__pycache__/"]
    if unknown:
        ignored.append("unknown-output/")
    (sandbox.repo / ".git/info/exclude").write_text("".join(f"/{name}\n" for name in ignored))
    for relative in (*git.DATABASE_LINKS, *git.NODE_LINKS):
        target = sandbox.repo / relative  # provision_links links each entry to the primary's own path
        target.parent.mkdir(parents=True, exist_ok=True)
        (tree / relative).parent.mkdir(parents=True, exist_ok=True)
        if relative.endswith(".db"):
            target.write_text("database")
        else:
            target.mkdir()
        (tree / relative).symlink_to(target)
    for name in ignored:
        if name.endswith("/"):
            (tree / name).mkdir(parents=True)
            (tree / name / "artifact").write_text("regenerated")
    in_process_repo(sandbox, monkeypatch)
    assert git.settle_worktree(record) == dict(worktree_disposition="removed", worktree_disposition_reason="clean")
    assert not tree.exists()
    recorded = [entry["path"] for entry in record.get("preserved_artifacts", {}).get("paths", [])]
    assert recorded == (["unknown-output/artifact"] if unknown else [])


@pytest.mark.parametrize("output", ["dependencies", "unique-output", "missing-lockfile"])
def test_scheduled_settlement_does_not_retain_regenerable_dependencies_as_unique_output(sandbox, monkeypatch, output):
    """Defect class: hourly settlement counts lockfile-backed dependencies as unique ignored output."""
    from scripts.orchestration import scheduled_worktree_cleanup as cleanup

    (sandbox.repo / ".gitignore").write_text("site/node_modules/\n.cache/\n")
    if output != "missing-lockfile":
        (sandbox.repo / "site").mkdir()
        (sandbox.repo / "site/package-lock.json").write_text('{"lockfileVersion": 3}\n')
        run_git(sandbox.repo, "add", "site/package-lock.json")
    run_git(sandbox.repo, "add", ".gitignore")
    run_git(sandbox.repo, "commit", "-m", "dependency inputs")
    run_git(sandbox.repo, "push", "origin", "main")
    record = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    assert record["worktree_disposition_reason"] == "unpublished"
    tree = Path(record["worktree_path"])
    dependency = tree / "site/node_modules/package/index.js"
    dependency.parent.mkdir(parents=True)
    with dependency.open("wb") as stream:
        stream.truncate(git.SALVAGE_IGNORED_LIMIT + 1)
    if output == "unique-output":
        unique = tree / ".cache/unique-evidence.bin"
        unique.parent.mkdir()
        with unique.open("wb") as stream:
            stream.write(b"unpublished evidence")
            stream.truncate(git.SALVAGE_IGNORED_LIMIT + 1)

    successor = run_git(tree, "commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m", "successor publication")
    run_git(tree, "push", str(sandbox.remote), f"{successor}:refs/heads/successor")
    assert run_git(sandbox.remote, "show", "successor:delivered.txt") == "literal delivered value"
    in_process_repo(sandbox, monkeypatch)
    (sandbox.repo / "batch_state").mkdir()
    (sandbox.repo / "batch_state/tasks").symlink_to(sandbox.tasks, target_is_directory=True)
    report = cleanup.settle_terminal_worktrees(sandbox.repo, apply=True, github=cleanup.GitHubReads())
    settled = json.loads((sandbox.tasks / f"{record['task_id']}.json").read_text())
    assert report["complete"] and report["error"] is None
    if output == "dependencies":
        assert (settled["worktree_disposition"], settled["worktree_disposition_reason"]) == ("removed", "clean")
        assert not tree.exists() and report["trees"] == []
        assert run_git(sandbox.remote, "for-each-ref", f"refs/heads/salvage/{record['task_id']}") == ""
    else:
        assert (settled["worktree_disposition"], settled["worktree_disposition_reason"]) == ("retained", "large_ignored_output")
        assert dependency.stat().st_size == git.SALVAGE_IGNORED_LIMIT + 1
        assert report["trees"][0]["reason"] == "large_ignored_output"
        if output == "unique-output":
            with unique.open("rb") as stream:
                assert stream.read(20) == b"unpublished evidence"
