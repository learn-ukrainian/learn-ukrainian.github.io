from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.hygiene import tmp_sweep as sweep
from scripts.hygiene.retention_engine import reap_attributed_temp


@pytest.fixture
def inventory(tmp_path, monkeypatch):
    root = tmp_path / "system-temp"
    root.mkdir()
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    monkeypatch.setattr(sweep, "process_snapshot", lambda: ([], True))
    monkeypatch.setattr(sweep, "registered_worktrees", lambda _: set())
    monkeypatch.setattr(sweep, "protected_roots", lambda: set())

    def make(name="impl-8755-probe", status="done", finished="2020-01-01T00:00:00Z"):
        path = root / name
        path.mkdir()
        (path / "payload").write_bytes(b"x" * 8192)
        for entry in (path / "payload", path):
            os.utime(entry, (time.time() - 86400, time.time() - 86400))
        (tasks / "impl-8755.json").write_text(
            json.dumps({"task_id": "impl-8755", "status": status, "finished_at": finished})
        )
        return path

    def run(**kwargs):
        return sweep.sweep(temp_root=root, task_root=tasks, repo_root=tmp_path, **kwargs)

    return SimpleNamespace(root=root, tasks=tasks, make=make, run=run)


def test_dead_task_dry_run_and_common_reap(inventory):
    path = inventory.make()
    before = path.stat()
    report = inventory.run()
    assert path.is_dir()
    assert report["mode"] == "dry-run" and report["bytes_reclaimed"] == 0
    assert report["rows"][0]["decision"] == "would_reap"
    assert report["bytes_reclaimable"] > 0
    assert report["projected_free_bytes"] == report["free_bytes"] + report["bytes_reclaimable"]
    assert report["rows"][0]["identity"][:2] == [before.st_dev, before.st_ino]
    applied = inventory.run(apply=True)
    assert applied["errors"] == 0
    assert applied["rows"][0]["decision"] == "reaped" and not path.exists()
    assert applied["bytes_reclaimed"] == report["bytes_reclaimable"]


@pytest.mark.parametrize("status", ["running", "spawning", "needs_finalize", "blocked", "dry_run", None])
def test_unsettled_tasks_preserved(inventory, status):
    path = inventory.make(status=status)
    report = inventory.run(apply=True)
    assert path.exists() and report["rows"][0]["reason"] == "task_not_settled"


@pytest.mark.parametrize("finished", [None, "bad", "2039-01-01T00:00:00Z", "2020-01-01T00:00:00"])
def test_unknown_completion_preserved(inventory, finished):
    path = inventory.make(finished=finished)
    assert inventory.run(apply=True)["rows"][0]["reason"] == "task_completion_unknown"
    assert path.exists()


def test_prefix_or_issue_number_is_not_attribution(inventory):
    path = inventory.make(name="impl8755-probe")
    assert inventory.run(apply=True)["rows"][0]["reason"] == "unattributed"
    assert path.exists()
    assert sweep.task_attribution("impl-87550", {"impl-8755": {}}) == []
    assert sweep.task_attribution("impl-8755-r2-probe", {"impl-8755": {}, "impl-8755-r2": {}}) == ["impl-8755-r2"]


def test_latest_descendant_write_is_age_gate(inventory):
    path = inventory.make()
    os.utime(path / "payload", None)
    assert inventory.run(apply=True)["rows"][0]["reason"] == "too_young"
    assert path.exists()


@pytest.mark.parametrize(
    "kind",
    ["live", "unknown", "registered", "registration_unknown", "managed", "harness", "git", "mount_unknown", "mount"],
)
def test_protected_paths_never_reaped(inventory, monkeypatch, kind):
    path = inventory.make(name="claude-123" if kind == "harness" else "impl-8755-probe")
    if kind == "live":
        monkeypatch.setattr(sweep, "process_snapshot", lambda: ([(99, path / "payload")], True))
    elif kind == "unknown":
        monkeypatch.setattr(sweep, "process_snapshot", lambda: ([], False))
    elif kind.startswith("registration") or kind == "registered":
        monkeypatch.setattr(
            sweep, "registered_worktrees", lambda _: {path / "nested"} if kind == "registered" else None
        )
    elif kind == "managed":
        monkeypatch.setattr(sweep, "protected_roots", lambda: {path / "task-scratch"})
    elif kind == "git":
        (path / ".git").write_text("gitdir: elsewhere")
    elif kind == "mount_unknown":
        monkeypatch.setattr(sweep, "mount_points", lambda: None)
    elif kind == "mount":
        monkeypatch.setattr(sweep, "mount_points", lambda: frozenset({str(path)}))
    report = inventory.run(apply=True)
    assert report["rows"][0]["decision"] == "preserve" and path.exists()
    assert report["bytes_reclaimed"] == 0
    if kind == "live":
        assert report["rows"][0]["live_pids"] == [99]


def test_symlink_is_not_followed(inventory):
    target = inventory.make()
    link = inventory.root / "impl-8755-link"
    link.symlink_to(target, target_is_directory=True)
    report = inventory.run()
    row = next(row for row in report["rows"] if row["name"] == link.name)
    assert row["reason"] == "symlink_or_not_directory" and row["bytes"] is None


def test_apply_rechecks_live_process_and_task_record(inventory, monkeypatch):
    path = inventory.make()
    probes = iter([([], True), ([(10, path)], True)])
    monkeypatch.setattr(sweep, "process_snapshot", lambda: next(probes))
    assert inventory.run(apply=True)["rows"][0]["reason"] == "proof_changed"
    assert path.exists()
    calls = 0

    def change_task():
        nonlocal calls
        calls += 1
        if calls == 2:
            (inventory.tasks / "impl-8755.json").write_text(json.dumps({"task_id": "impl-8755", "status": "running"}))
        return [], True

    monkeypatch.setattr(sweep, "process_snapshot", change_task)
    assert inventory.run(apply=True)["rows"][0]["reason"] == "proof_changed"
    assert path.exists()


def test_identity_swap_rejected_by_common_reaper(inventory):
    path = inventory.make()
    old = path.stat()
    path.rename(inventory.root / "retained")
    path.mkdir()
    (path / "sentinel").write_text("keep")
    with pytest.raises(Exception, match="device/inode"):
        reap_attributed_temp(
            path,
            temp_root=inventory.root,
            repo_root=inventory.root.parent,
            expected_dev=old.st_dev,
            expected_ino=old.st_ino,
        )
    assert (path / "sentinel").exists()


def test_reaper_refuses_symlink_or_nonchild(inventory):
    path = inventory.make()
    link = inventory.root / "link"
    link.symlink_to(path)
    info = path.stat()
    for target in (link, path / "payload"):
        with pytest.raises(ValueError, match="direct child"):
            reap_attributed_temp(
                target,
                temp_root=inventory.root,
                repo_root=inventory.root.parent,
                expected_dev=info.st_dev,
                expected_ino=info.st_ino,
            )


def test_scan_error_and_reap_error_are_reported(inventory, monkeypatch):
    path = inventory.make()

    def broken(*args, **kwargs):
        raise OSError("fixture error")

    monkeypatch.setattr(sweep, "reap_attributed_temp", broken)
    report = inventory.run(apply=True)
    assert report["errors"] == 1 and path.exists()
    monkeypatch.setattr(sweep, "tree_facts", lambda _: (0, 0, 0, "tree_unknown"))
    assert inventory.run()["rows"][0]["reason"] == "tree_unknown"


def test_task_loader_rejects_malformed_or_mismatched_records(tmp_path):
    (tmp_path / "bad.json").write_text("not json")
    (tmp_path / "wrong.json").write_text(json.dumps({"task_id": "someone-else"}))
    (tmp_path / "list.json").write_text("[]")
    inventory = sweep.load_tasks(tmp_path)
    assert set(inventory.records) == {"bad", "wrong", "list"}
    assert all(record["status"] is None for record in inventory.records.values())
    assert inventory.complete is False
    assert sweep.load_tasks(tmp_path / "absent").complete is False


def test_process_snapshot_cwd_fd_zombie_and_unknown(tmp_path):
    proc = tmp_path / "proc"
    proc.mkdir()
    live = proc / "11"
    live.mkdir()
    (live / "stat").write_text("11 (fixture) S 0")
    (live / "cwd").symlink_to(tmp_path)
    (live / "fd").mkdir()
    (live / "fd" / "4").symlink_to(tmp_path / "held")
    zombie = proc / "12"
    zombie.mkdir()
    (zombie / "stat").write_text("12 (fixture) Z 0")
    refs, complete = sweep.process_snapshot(proc)
    assert complete and (11, tmp_path) in refs and (11, tmp_path / "held") in refs
    unknown = proc / "13"
    unknown.mkdir()
    assert sweep.process_snapshot(proc)[1] is False
    assert sweep.process_snapshot(tmp_path / "absent") == ([], False)


def test_real_process_fd_and_cwd_are_seen(tmp_path):
    # Held by this test process: the sweep must include its own caller too.
    with (tmp_path / "held").open("w"):
        refs, _ = sweep.process_snapshot()
        assert (os.getpid(), tmp_path / "held") in refs
        assert (os.getpid(), Path.cwd()) in refs


def test_registration_probe_preserves_on_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(returncode=0, stdout=b"worktree /generic/fixture\0HEAD abc\0\0"),
    )
    assert sweep.registered_worktrees(tmp_path) == {Path("/generic/fixture")}
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=1))
    assert sweep.registered_worktrees(tmp_path) is None


def test_protected_root_includes_dispatch_and_managed_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "managed"))
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path / "base"))
    monkeypatch.setenv("TMPDIR", str(tmp_path / "lease"))
    roots = sweep.protected_roots()
    assert {tmp_path / "managed", tmp_path / "base", tmp_path / "lease"} <= roots


@pytest.mark.parametrize("age", [0, -1, float("nan"), float("inf")])
def test_invalid_age_refused(inventory, age):
    with pytest.raises(ValueError):
        inventory.run(min_age_s=age)


def test_cli_dry_run_json_table_and_errors(inventory, capsys):
    inventory.make()
    argv = ["--temp-root", str(inventory.root), "--task-root", str(inventory.tasks)]
    assert sweep.main([*argv, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["bytes_reclaimed"] == 0
    assert sweep.main(argv) == 0
    assert "| Entry |" in capsys.readouterr().out
    with pytest.raises(SystemExit) as exc:
        sweep.main([*argv, "--min-age-hours", "0"])
    assert exc.value.code == 2


def test_hardlinks_are_preserved_without_overstating_reclaim(inventory):
    path = inventory.make()
    os.link(path / "payload", path / "second-link")
    report = inventory.run(apply=True)
    assert path.exists() and report["rows"][0]["reason"] == "hardlinked_content"
    assert report["bytes_reclaimed"] == 0


def test_foreign_ownership_is_preserved(inventory, monkeypatch):
    path = inventory.make()
    real_uid = os.geteuid()
    monkeypatch.setattr(sweep.os, "geteuid", lambda: real_uid + 1)
    report = inventory.run(apply=True)
    assert path.exists() and report["rows"][0]["reason"] == "foreign_owner"


def test_tree_read_error_is_unknown(inventory, monkeypatch):
    path = inventory.make()
    original = Path.iterdir

    def unreadable(self):
        if self == path:
            raise PermissionError("fixture")
        return original(self)

    monkeypatch.setattr(Path, "iterdir", unreadable)
    assert sweep.tree_facts(path)[3] == "tree_unknown"


def test_common_reaper_refuses_unknown_mounts(inventory, monkeypatch):
    from scripts.common import task_scratch

    path = inventory.make()
    info = path.stat()
    monkeypatch.setattr(task_scratch, "mount_points", lambda: None)
    with pytest.raises(task_scratch.ContainmentError, match="mount information unavailable"):
        reap_attributed_temp(
            path,
            temp_root=inventory.root,
            repo_root=inventory.root.parent,
            expected_dev=info.st_dev,
            expected_ino=info.st_ino,
        )
    assert path.exists()


def test_apply_recheck_blocks_directory_replacement(inventory, monkeypatch):
    path = inventory.make()
    calls = 0

    def swap():
        nonlocal calls
        calls += 1
        if calls == 2:
            path.rename(inventory.root / "preserved-original")
            path.mkdir()
            (path / "sentinel").write_text("unrelated data")
        return [], True

    monkeypatch.setattr(sweep, "process_snapshot", swap)
    assert inventory.run(apply=True)["rows"][0]["reason"] == "proof_changed"
    assert (path / "sentinel").exists()


def test_process_snapshot_keeps_known_cwd_when_fds_unknown(tmp_path):
    entry = tmp_path / "14"
    entry.mkdir()
    (entry / "stat").write_text("14 (fixture) S 0")
    (entry / "cwd").symlink_to(tmp_path / "held")
    refs, complete = sweep.process_snapshot(tmp_path)
    assert (14, tmp_path / "held") in refs and not complete


def test_final_process_probe_after_tree_recheck_blocks_reap(inventory, monkeypatch):
    path = inventory.make()
    probes = iter([([], True), ([], True), ([(16, path)], True)])
    monkeypatch.setattr(sweep, "process_snapshot", lambda: next(probes))
    report = inventory.run(apply=True)
    assert path.exists() and report["rows"][0]["reason"] == "final_liveness_or_task_changed"


def test_malformed_specific_run_never_falls_back_to_finished_parent(inventory):
    path = inventory.make(name="impl-8755-r2-probe")
    (inventory.tasks / "impl-8755-r2.json").write_text("incomplete state")
    row = inventory.run(apply=True)["rows"][0]
    assert row["task"] == "impl-8755-r2" and row["reason"] == "task_not_settled"
    assert path.exists()


def test_socket_endpoint_is_preserved_even_without_fd_path_reference(inventory, monkeypatch):
    path = inventory.make()
    monkeypatch.chdir(path)
    try:
        endpoint = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    except PermissionError as error:
        pytest.skip(f"this sandbox forbids AF_UNIX socket creation: {error}")
    with endpoint:
        endpoint.bind("endpoint")
        report = inventory.run(apply=True)
        assert path.exists() and report["rows"][0]["reason"] == "special_file"
        assert report["bytes_reclaimed"] == 0
