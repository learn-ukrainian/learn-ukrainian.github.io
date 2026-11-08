"""Salvage refs, retention holds, squash-merged recovery and borrowed worktrees."""

import concurrent.futures
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

import pytest
from lu_machinery.dispatcher import git, store, worker

from tests.dispatcher.conftest import await_file, in_process_repo, local_branches, run_git


@pytest.mark.parametrize("unique_output", [False, True])
def test_salvage_release_pins_remove_published_tracked_work_but_retain_unique_output(
        sandbox, monkeypatch, synthetic_opsec, unique_output):
    """Defect class: salvage ignores committed release pins and retains published tracked work."""
    from lu_machinery.common import github_client
    from lu_machinery.fleet.regenerable_output import committed_release_pins

    from tests.fleet.test_regenerable_release_output import pinned_checkout

    pinned_checkout((sandbox.repo, sandbox.repo, sandbox.tasks))
    run_git(sandbox.repo, "push", "origin", "main")
    assets = (sandbox.repo.parent / "release-store.json").read_text()
    monkeypatch.setattr(github_client, "run", lambda *args, **kwargs: subprocess.CompletedProcess(
        args, 0, json.dumps({"assets": json.loads(assets)})))
    monkeypatch.setattr(git, "SALVAGE_IGNORED_LIMIT", 1)
    record = sandbox.settle(sandbox.dispatch("pushed-dirty", "--mode", "workspace-write",
                                            "--sparse-include", "site/src/data"), expected=1)
    tree = Path(record["worktree_path"])
    # Copy only the ignored release outputs; pointers and hydrators came from the committed base.
    for name in ("site/src/data/lexicon-manifest.json", "site/public/lexicon/practice-index.A1.json"):
        (tree / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sandbox.repo / name, tree / name)
    run_git(tree, "add", "delivered.txt")
    published = run_git(tree, "commit-tree", run_git(tree, "write-tree"), "-p", "HEAD", "-m", "published PR head")
    run_git(tree, "push", "origin", f"{published}:refs/pull/12424/head")
    assert run_git(sandbox.remote, "show", f"{published}:delivered.txt") == "uncommitted delivery"
    assert run_git(tree, "status", "--porcelain") == "M  delivered.txt"
    if unique_output:
        (tree / "ignored").mkdir()
        (tree / "ignored/evidence.bin").write_bytes(b"unpublished evidence")

    in_process_repo(sandbox, monkeypatch)
    assert set(committed_release_pins(tree, set(run_git(tree, "ls-files").splitlines()))) == {
        "site/src/data/lexicon-manifest.json", "site/public/lexicon/practice-index.A1.json"}
    worker.settle_left_worktrees(salvage=True)
    settled = json.loads((sandbox.tasks / f"{record['task_id']}.json").read_text())
    if unique_output:
        assert (settled["worktree_disposition"], settled["worktree_disposition_reason"]) == (
            "retained", "large_ignored_output")
        assert (tree / "ignored/evidence.bin").read_bytes() == b"unpublished evidence"
        assert run_git(sandbox.remote, "for-each-ref", f"refs/heads/salvage/{record['task_id']}") == ""
    else:
        assert (settled["worktree_disposition"], settled["worktree_disposition_reason"]) == ("removed", "salvaged")
        assert not tree.exists()


def test_hourly_salvage_removes_a_dirty_tree_only_after_its_work_is_on_a_new_salvage_ref(
        sandbox, monkeypatch, synthetic_opsec):
    """#12043 AC-06a: a finished task's dirty tree stayed forever; a failed salvage push must still keep it.

    The synthetic matcher lets the push scan run where the private install is absent, so a refused
    push is still salvage_failed rather than a scan that could not start.
    """
    record = sandbox.settle(sandbox.dispatch("pushed-dirty", "--mode", "workspace-write"), expected=1)
    assert record["worktree_disposition_reason"] == "dirty"
    tree, ref = Path(record["worktree_path"]), f"refs/heads/salvage/{record['task_id']}"
    (tree / "notes.txt").write_text("untracked note\n")
    in_process_repo(sandbox, monkeypatch)
    verification_git = git._verification_git

    def refused_push(path, *args, **kwargs):
        if args[0] == "push":
            raise subprocess.CalledProcessError(1, ["git", "push"])
        return verification_git(path, *args, **kwargs)

    def settled():
        return json.loads((sandbox.tasks / f"{record['task_id']}.json").read_text())

    monkeypatch.setattr(git, "_verification_git", refused_push)
    worker.settle_left_worktrees(salvage=True)
    assert (settled()["worktree_disposition"], settled()["worktree_disposition_reason"]) == (
        "retained", "salvage_failed")
    assert tree.is_dir() and run_git(sandbox.remote, "for-each-ref", ref) == ""

    monkeypatch.setattr(git, "_verification_git", verification_git)
    worker.settle_left_worktrees(salvage=True)
    assert (settled()["worktree_disposition"], settled()["worktree_disposition_reason"]) == ("removed", "salvaged")
    assert not tree.exists()
    salvaged = run_git(sandbox.remote, "rev-parse", ref)
    assert run_git(sandbox.remote, "rev-parse", f"{salvaged}^") == record["head_sha"]
    assert run_git(sandbox.remote, "show", f"{salvaged}:delivered.txt") == "uncommitted delivery"
    assert run_git(sandbox.remote, "show", f"{salvaged}:notes.txt") == "untracked note"


def _salvage_ref(record):
    return f"refs/heads/salvage/{record['task_id']}"


def test_salvage_keeps_a_tree_when_the_push_scan_refuses(sandbox, monkeypatch, synthetic_opsec):
    """Defect class: salvage pushes a range the OPSEC push scan would refuse because hooksPath is /dev/null."""
    from lu_machinery.orchestration.scheduled_worktree_cleanup import SAFETY_STOP_REASONS

    from tests.opsec_fixtures import TOKEN

    record = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    assert record["worktree_disposition_reason"] == "unpublished"
    tree, ref = Path(record["worktree_path"]), _salvage_ref(record)
    run_git(tree, "-c", "core.hooksPath=/dev/null", "commit", "--allow-empty", "-m", f"note {TOKEN}")
    in_process_repo(sandbox, monkeypatch)

    def settled():
        return json.loads((sandbox.tasks / f"{record['task_id']}.json").read_text())

    worker.settle_left_worktrees(salvage=True)
    first = settled()
    assert (first["worktree_disposition"], first["worktree_disposition_reason"]) == ("retained", "opsec_refused")
    assert first["worktree_disposition_reason"] not in worker.RETRY_REASONS
    assert first["worktree_disposition_reason"] in SAFETY_STOP_REASONS
    assert first["worktree_disposition_detail"] == git.OPSEC_REFUSAL_DETAIL
    assert TOKEN not in json.dumps(first)
    assert tree.is_dir() and run_git(sandbox.remote, "for-each-ref", ref) == ""
    worker.settle_left_worktrees(salvage=True)
    assert settled()["worktree_disposition_reason"] == "opsec_refused"
    assert tree.is_dir() and run_git(sandbox.remote, "for-each-ref", ref) == ""


def test_salvage_still_publishes_a_range_the_push_scan_accepts(sandbox, monkeypatch, synthetic_opsec):
    """Defect class: regression of clean public salvage. A range the push scan accepts is still published."""
    record = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    assert record["worktree_disposition_reason"] == "unpublished"
    tree, ref = Path(record["worktree_path"]), _salvage_ref(record)
    head = run_git(tree, "rev-parse", "HEAD")
    in_process_repo(sandbox, monkeypatch)
    worker.settle_left_worktrees(salvage=True)
    settled = json.loads((sandbox.tasks / f"{record['task_id']}.json").read_text())
    assert (settled["worktree_disposition"], settled["worktree_disposition_reason"]) == ("removed", "salvaged")
    assert not tree.exists()
    assert run_git(sandbox.remote, "rev-parse", ref) == head


@pytest.mark.parametrize("salvage", [False, True])
@pytest.mark.parametrize("damage", ["missing", "unreadable", "json", "non-object", "encoding"])
def test_retention_refuses_unreadable_durable_record(tmp_path, monkeypatch, damage, salvage):
    """F3: a damaged durable record must not fall back to a stale unheld copy."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    tree = tmp_path / "tree"
    tree.mkdir()
    record = {"task_id": "retention-refusal", "worktree_path": str(tree), "worktree_retention_hold": False}
    path = tmp_path / "retention-refusal.json"
    if damage != "missing":
        path.write_bytes({"json": b"{", "non-object": b"[]", "encoding": b"\xff"}.get(
            damage, json.dumps(record).encode()))
    original_read = Path.read_text

    def read_text(self, *args, **kwargs):
        if self == path and damage == "unreadable":
            raise PermissionError("record cannot be read")
        return original_read(self, *args, **kwargs)

    def forbidden(*args, **kwargs):
        pytest.fail("retention refusal reached Git inspection, push or removal")

    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr(git, "_tree_changes", forbidden)
    monkeypatch.setattr(git, "_git", forbidden)
    monkeypatch.setattr(git, "_salvage", forbidden)
    result = git.settle_worktree(record, salvage=salvage)
    assert result == {
        "worktree_disposition": "retained",
        "worktree_disposition_reason": "task_record_damaged",
        "worktree_disposition_detail": "retention decision requires a readable on-disk task record",
    }
    assert tree.is_dir()


@pytest.mark.parametrize("salvage", [False, True])
@pytest.mark.parametrize("source", ["disk", "memory"])
@pytest.mark.parametrize("value", [None, "true", "false", 1, 0, [], {}, 1.0])
def test_retention_refuses_non_boolean_hold(tmp_path, monkeypatch, value, source, salvage):
    """F4: malformed holds must retain the tree and survive stale record writes."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    tree = tmp_path / "tree"
    tree.mkdir()
    record = {"task_id": "retention-refusal", "run_nonce": "same-run", "worktree_path": str(tree)}
    disk = dict(record)
    (disk if source == "disk" else record)["worktree_retention_hold"] = value
    path = tmp_path / "retention-refusal.json"
    path.write_text(json.dumps(disk))
    if source == "disk":
        store.replace(dict(record), path)
        assert json.loads(path.read_text())["worktree_retention_hold"] == value

    def forbidden(*args, **kwargs):
        pytest.fail("retention refusal reached Git inspection, push or removal")

    monkeypatch.setattr(git, "_tree_changes", forbidden)
    monkeypatch.setattr(git, "_git", forbidden)
    monkeypatch.setattr(git, "_salvage", forbidden)
    result = git.settle_worktree(record, salvage=salvage)
    assert result == {
        "worktree_disposition": "retained",
        "worktree_disposition_reason": "retention_hold_invalid",
        "worktree_disposition_detail": f"worktree_retention_hold must be a boolean; got {value!r}",
    }
    assert tree.is_dir()


def test_retention_hold_blocks_settlement_salvage_and_cleanup(sandbox, monkeypatch, synthetic_opsec):
    """Defect class: an unpublished tree has no owner hold, so salvage retries it."""
    from lu_machinery.orchestration import scheduled_worktree_cleanup as cleanup

    record = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    assert record["worktree_disposition_reason"] == "unpublished"
    tree, ref = Path(record["worktree_path"]), _salvage_ref(record)
    sandbox.cli("retain-worktree", record["task_id"], "--set")
    held = json.loads((sandbox.tasks / f"{record['task_id']}.json").read_text())
    assert held["worktree_retention_hold"] is True
    assert held["worktree_disposition_reason"] == "retention_hold"
    assert "retention_hold" not in worker.RETRY_REASONS
    in_process_repo(sandbox, monkeypatch)
    assert git.settle_worktree(held) == {
        "worktree_disposition": "retained", "worktree_disposition_reason": "retention_hold",
    }
    assert tree.is_dir() and run_git(sandbox.remote, "for-each-ref", ref) == ""
    worker.settle_left_worktrees(salvage=True)
    assert tree.is_dir() and run_git(sandbox.remote, "for-each-ref", ref) == ""
    (sandbox.repo / "batch_state").mkdir()
    (sandbox.repo / "batch_state/tasks").symlink_to(sandbox.tasks, target_is_directory=True)
    report = cleanup.settle_terminal_worktrees(sandbox.repo, apply=True, github=cleanup.GitHubReads())
    assert report["complete"] and report["error"] is None
    assert tree.is_dir() and run_git(sandbox.remote, "for-each-ref", ref) == ""
    listed = report["trees"][0]
    assert listed["reason"] == "retention_hold" and listed["safety_stop"] is False
    sandbox.cli("retain-worktree", record["task_id"], "--clear")
    cleared = json.loads((sandbox.tasks / f"{record['task_id']}.json").read_text())
    assert "worktree_retention_hold" not in cleared
    assert "worktree_disposition" not in cleared
    cleared["worktree_retention_hold"] = False
    (sandbox.tasks / f"{record['task_id']}.json").write_text(json.dumps(cleared))
    worker.settle_left_worktrees(salvage=True)
    settled = json.loads((sandbox.tasks / f"{record['task_id']}.json").read_text())
    assert (settled["worktree_disposition"], settled["worktree_disposition_reason"]) == ("removed", "salvaged")
    assert not tree.exists()
    assert run_git(sandbox.remote, "rev-parse", ref)


def test_salvage_uses_the_trusted_linter_when_the_worktree_copy_exits_clean(sandbox, monkeypatch, synthetic_opsec):
    """Defect: a worktree can replace its blob linter with a script that exits 0 and salvage will push."""
    record = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    tree, ref = Path(record["worktree_path"]), _salvage_ref(record)
    (tree / "scripts/audit/lint_opsec_leaks.py").write_text("raise SystemExit(0)\n")
    (tree / "notes.txt").write_text(".".join(("10", "1", "2", "3")) + "\n")
    in_process_repo(sandbox, monkeypatch)
    worker.settle_left_worktrees(salvage=True)
    settled = json.loads((sandbox.tasks / f"{record['task_id']}.json").read_text())
    assert (settled["worktree_disposition"], settled["worktree_disposition_reason"]) == ("retained", "opsec_refused")
    assert tree.is_dir() and run_git(sandbox.remote, "for-each-ref", ref) == ""


def test_retention_hold_survives_a_stale_record_write_and_skips_inspection(sandbox, monkeypatch):
    """Defect: a supervisor write from an older copy drops the hold, and the old-tree report still reads Git."""
    from datetime import UTC, datetime, timedelta

    from lu_machinery.orchestration import scheduled_worktree_cleanup as cleanup

    record = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    tree = Path(record["worktree_path"])
    sandbox.cli("retain-worktree", record["task_id"], "--set")
    path = sandbox.tasks / f"{record['task_id']}.json"
    stale = json.loads(path.read_text())
    stale.pop("worktree_retention_hold")
    stale["worktree_disposition"] = "removed"
    stale["worktree_disposition_reason"] = "clean"
    in_process_repo(sandbox, monkeypatch)
    store.replace(stale, path)
    kept = json.loads(path.read_text())
    assert kept["worktree_retention_hold"] is True
    assert kept["worktree_disposition_reason"] == "retention_hold"
    naked = dict(record)
    naked.pop("worktree_retention_hold", None)
    assert git.settle_worktree(naked)["worktree_disposition_reason"] == "retention_hold"
    assert tree.is_dir()
    kept["finished_at"] = (datetime.now(UTC) - timedelta(hours=7)).isoformat()
    path.write_text(json.dumps(kept))
    (sandbox.repo / "batch_state").mkdir()
    (sandbox.repo / "batch_state/tasks").symlink_to(sandbox.tasks, target_is_directory=True)
    monkeypatch.setattr(cleanup.worktree_git, "control_plane_root", lambda root: sandbox.repo)

    def refused(*args, **kwargs):
        raise AssertionError("held tree was inspected")

    monkeypatch.setattr(cleanup, "_inspect_terminal_git", refused)
    report = cleanup.report_terminal_worktrees(sandbox.repo)
    assert report["tasks"] == []
    sandbox.cli("retain-worktree", record["task_id"], "--clear")
    cleared = json.loads(path.read_text())
    assert "worktree_retention_hold" not in cleared
    cleared["worktree_disposition"] = "removed"
    cleared["worktree_disposition_reason"] = "clean"
    store.replace(cleared, path)
    assert "worktree_retention_hold" not in json.loads(path.read_text())


@pytest.mark.parametrize("pull_ref,disposition", [(True, ("removed", "clean")), (False, ("retained", "unpublished"))])
def test_recovery_removes_squash_merged_write_task_only_when_a_pull_ref_holds_its_head(sandbox, pull_ref, disposition):
    """CTO residual: after a squash merge and branch deletion, D3 never fired, so the worktree stayed forever."""
    record = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    assert record["worktree_disposition_reason"] == "unpublished"
    tree, branch = Path(record["worktree_path"]), record["worktree_branch"]
    squash = run_git(tree, "commit-tree", "HEAD^{tree}", "-p", record["worktree_base_sha"], "-m", "squash (#7)")
    run_git(tree, "push", str(sandbox.remote), f"HEAD:refs/heads/{branch}", f"{squash}:refs/heads/main")
    if pull_ref:
        run_git(tree, "push", str(sandbox.remote), "HEAD:refs/pull/7/head")
    run_git(tree, "push", str(sandbox.remote), f":refs/heads/{branch}")
    sandbox.sweep()
    settled = json.loads((sandbox.tasks / f"{record['task_id']}.json").read_text())
    assert (settled["worktree_disposition"], settled["worktree_disposition_reason"]) == disposition
    assert tree.exists() is not pull_ref
    assert (branch in local_branches(sandbox.repo)) is not pull_ref


def test_continuation_records_sharing_a_landed_tree_resolve_to_the_creator_and_the_tree_is_removed(sandbox):
    """#12063 AC-06: continuations beside their creator left no single owner, so a landed tree stayed forever."""
    record = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    tree, branch = Path(record["worktree_path"]), record["worktree_branch"]
    (tree / "unknown-output").mkdir()
    (tree / "unknown-output" / "artifact").write_text("ignored output")
    (sandbox.repo / ".git/info/exclude").write_text("/unknown-output/\n")
    squash = run_git(tree, "commit-tree", "HEAD^{tree}", "-p", record["worktree_base_sha"], "-m", "squash (#7)")
    run_git(tree, "push", str(sandbox.remote), f"HEAD:refs/heads/{branch}", f"{squash}:refs/heads/main")
    run_git(tree, "push", str(sandbox.remote), "HEAD:refs/pull/7/head")
    run_git(tree, "push", str(sandbox.remote), f":refs/heads/{branch}")
    # Dispatcher records written before the reuse flag and creation inventory existed.
    creator_file = sandbox.tasks / f"{record['task_id']}.json"
    creator = json.loads(creator_file.read_text())
    creator.pop("worktree_reused", None)
    creator.pop("ignored_output_baseline", None)
    creator_file.write_text(json.dumps(creator))
    for suffix in ("c", "d"):
        continuation = dict(creator, task_id=f"{record['task_id']}{suffix}", run_nonce=f"{suffix}" * 32,
                            worktree_disposition="retained", worktree_disposition_reason="borrowed_worktree",
                            options=dict(creator["options"], cwd=str(tree), task_id=f"{record['task_id']}{suffix}"))
        (sandbox.tasks / f"{continuation['task_id']}.json").write_text(json.dumps(continuation))
    sandbox.sweep()
    settled = json.loads(creator_file.read_text())
    assert (settled["worktree_disposition"], settled["worktree_disposition_reason"]) == ("removed", "clean")
    assert not tree.exists()


def test_crash_recovery_keeps_worktree_while_the_orphaned_provider_runs(sandbox):
    """Defect (F2): recovery removed a crashed task's worktree without proving its provider had exited."""
    task = sandbox.dispatch("blocked")
    provider = int(await_file(sandbox.tasks / f"{task[0]}.started"))
    # The provider can write its marker before Popen returns and the supervisor records its group; a
    # supervisor killed before that record leaves liveness unknown, which this test does not cover.
    deadline = time.monotonic() + 10
    while "provider_pgid" not in (record := json.loads((sandbox.tasks / f"{task[0]}.json").read_text())):
        assert time.monotonic() < deadline, "supervisor never recorded its provider"
        time.sleep(0.02)
    os.kill(record["pid"], signal.SIGKILL)
    deadline = time.monotonic() + 10
    while worker._identity(record["pid"]) == record["process_start"]:
        assert time.monotonic() < deadline, "supervisor survived SIGKILL"
        time.sleep(0.02)
    sandbox.sweep()
    crashed = json.loads((sandbox.tasks / f"{task[0]}.json").read_text())
    assert crashed["status"] == "crashed"
    assert (crashed["worktree_disposition"], crashed["worktree_disposition_reason"]) == (
        "retained", "provider_processes_alive")
    assert Path(record["worktree_path"]).is_dir()
    os.killpg(provider, signal.SIGKILL)
    deadline = time.monotonic() + 10
    while worker._provider_alive(crashed):
        assert time.monotonic() < deadline, "provider survived SIGKILL"
        time.sleep(0.02)
    sandbox.sweep()
    settled = json.loads((sandbox.tasks / f"{task[0]}.json").read_text())
    assert (settled["worktree_disposition"], settled["worktree_disposition_reason"]) == ("removed", "clean")
    assert not Path(record["worktree_path"]).exists()


@pytest.mark.parametrize("borrower_state", ["running", "crashed", "aliased"])
def test_settlement_keeps_a_worktree_that_a_live_task_borrowed(sandbox, borrower_state):
    """Defect (F3): a finished task removed its worktree while another task's provider worked there via --cwd.

    crashed: the borrower's supervisor died, so its record is terminal while its provider still runs.
    aliased: the borrower named the tree by another spelling (TREE/../TREE_NAME).
    """
    owner = sandbox.dispatch("blocked")
    await_file(sandbox.tasks / f"{owner[0]}.started")
    tree = Path(json.loads((sandbox.tasks / f"{owner[0]}.json").read_text())["worktree_path"])
    cwd = tree / ".." / tree.name if borrower_state == "aliased" else tree
    borrower = sandbox.dispatch("blocked", "--cwd", str(cwd))
    provider = int(await_file(sandbox.tasks / f"{borrower[0]}.started"))
    if borrower_state == "crashed":
        # The provider writes its marker before the supervisor records its group. Killing in that
        # window leaves liveness unknown, and the sweep keeps a borrowed tree until the group is
        # proven gone (_provider_alive is False, not merely falsy).
        deadline = time.monotonic() + 10
        while "provider_pgid" not in (
            supervisor := json.loads((sandbox.tasks / f"{borrower[0]}.json").read_text())
        ):
            assert time.monotonic() < deadline, "supervisor never recorded its provider"
            time.sleep(0.02)
        os.kill(supervisor["pid"], signal.SIGKILL)
        deadline = time.monotonic() + 10
        while worker._identity(supervisor["pid"]) == supervisor["process_start"]:
            assert time.monotonic() < deadline, "supervisor survived SIGKILL"
            time.sleep(0.02)
        sandbox.sweep()  # scheduled recovery records the borrower as crashed
        assert json.loads((sandbox.tasks / f"{borrower[0]}.json").read_text())["status"] == "crashed"
    (sandbox.tasks / f"{owner[0]}.release").touch()
    record = sandbox.settle(owner)
    assert (record["worktree_disposition"], record["worktree_disposition_reason"]) == (
        "retained", "borrowed_by_live_task")
    assert tree.is_dir()
    if borrower_state == "crashed":
        os.killpg(provider, signal.SIGKILL)
        deadline = time.monotonic() + 10
        while worker._provider_alive(json.loads((sandbox.tasks / f"{borrower[0]}.json").read_text())) is not False:
            assert time.monotonic() < deadline, "provider survived SIGKILL"
            time.sleep(0.02)
    else:
        (sandbox.tasks / f"{borrower[0]}.release").touch()
        assert sandbox.settle(borrower)["worktree_disposition_reason"] == "borrowed_worktree"
    sandbox.sweep()
    assert json.loads((sandbox.tasks / f"{owner[0]}.json").read_text())["worktree_disposition"] == "removed"
    assert not tree.exists()


def test_wait_does_not_report_a_task_while_its_settlement_holds_the_lock(sandbox, monkeypatch):
    """Defect (F4): wait returned a terminal task while crash recovery was still removing its worktree."""
    task = sandbox.dispatch()
    sandbox.settle(task)
    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    with concurrent.futures.ThreadPoolExecutor(1) as pool:
        with store.task_state_lock(store.record_path(task[0])):
            waiting = pool.submit(worker.wait, task[0], task[1], 15, 0.02)
            with pytest.raises(TimeoutError):
                waiting.result(timeout=0.5)
        assert waiting.result(timeout=15)[1] == 0
