"""Unattributed-scratch class of the temp sweep (#9737)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from scripts.common import task_scratch
from scripts.hygiene import tmp_sweep as sweep
from scripts.hygiene.retention_engine import reap_attributed_temp

DAY = 86400
OLD = time.time() - 3 * DAY
REAL_PROCESS_SNAPSHOT = sweep.process_snapshot


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    """A temp root whose entries look three days old to the sweep.

    Change time cannot be backdated, so the sweep's clock moves forward
    instead; mtimes are pinned to the real present minus three days.
    """
    root = tmp_path / "system-temp"
    root.mkdir()
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    now = time.time() + 3 * DAY
    monkeypatch.setattr(sweep, "time", SimpleNamespace(time=lambda: now))
    monkeypatch.setattr(sweep, "process_snapshot", lambda *a, **kw: ([], True))
    monkeypatch.setattr(sweep, "registered_worktrees", lambda _: set())
    monkeypatch.setattr(sweep, "protected_roots", lambda: set())

    def tree(name="hand-made-scratch"):
        path = root / name
        (path / "deep").mkdir(parents=True)
        (path / "deep" / "payload").write_bytes(b"x" * 8192)
        for entry in (path / "deep" / "payload", path / "deep", path):
            os.utime(entry, (OLD, OLD))
        return path

    def file(name="scratch.log"):
        path = root / name
        path.write_bytes(b"y" * 4096)
        os.utime(path, (OLD, OLD))
        return path

    def run(**kwargs):
        kwargs.setdefault("scratch", sweep.ScratchPolicy())
        return sweep.sweep(temp_root=root, task_root=tasks, repo_root=tmp_path, **kwargs)

    def row(report, name):
        return next(item for item in report["rows"] if item["name"] == name)

    return SimpleNamespace(root=root, tasks=tasks, now=now, tree=tree, file=file, run=run, row=row)


def test_dry_run_lists_then_apply_removes_quiet_scratch(scratch):
    directory, regular = scratch.tree(), scratch.file()
    report = scratch.run()
    assert {r["name"]: (r["decision"], r["reason"]) for r in report["rows"]} == {
        directory.name: ("would_reap", "unattributed_scratch"),
        regular.name: ("would_reap", "unattributed_scratch"),
    }
    assert directory.exists() and regular.exists() and report["bytes_reclaimed"] == 0
    assert (report["directories"], report["files"]) == (1, 1)
    assert report["bytes_reclaimable"] > 0 and report["scratch_policy"] == {"min_age_hours": 24, "quiet_hours": 24}
    applied = scratch.run(apply=True)
    assert applied["errors"] == 0 and not directory.exists() and not regular.exists()
    assert {r["decision"] for r in applied["rows"]} == {"reaped"}
    assert applied["bytes_reclaimed"] == report["bytes_reclaimable"]


def test_class_is_opt_in(scratch):
    directory, regular = scratch.tree(), scratch.file()
    report = scratch.run(scratch=None, apply=True)
    assert [(r["name"], r["reason"]) for r in report["rows"]] == [(directory.name, "unattributed")]
    assert directory.exists() and regular.exists()


def test_recent_deep_write_preserves_entry(scratch):
    directory = scratch.tree()
    deep = directory / "deep" / "payload"
    os.utime(deep, (scratch.now - 3600, scratch.now - 3600))
    report = scratch.run(apply=True)
    assert scratch.row(report, directory.name)["reason"] == "recent_deep_write" and deep.exists()


def test_top_level_age_threshold_is_configurable(scratch):
    directory = scratch.tree()
    os.utime(directory, (scratch.now - 10 * 3600, scratch.now - 10 * 3600))
    assert scratch.row(scratch.run(apply=True), directory.name)["reason"] == "too_young"
    policy = sweep.ScratchPolicy(min_age_s=6 * 3600, quiet_s=6 * 3600)
    assert scratch.row(scratch.run(scratch=policy), directory.name)["reason"] == "unattributed_scratch"


def test_change_time_keeps_freshly_extracted_archives(scratch, monkeypatch):
    # Old preserved mtimes, but every inode change time is the real present.
    directory = scratch.tree()
    now = time.time() + 60
    monkeypatch.setattr(sweep, "time", SimpleNamespace(time=lambda: now))
    assert scratch.row(scratch.run(apply=True), directory.name)["reason"] == "too_young"
    # Even with the top-level gate satisfied, a recent change deep inside holds the tree.
    policy = sweep.ScratchPolicy(min_age_s=1)
    assert scratch.row(scratch.run(scratch=policy, apply=True), directory.name)["reason"] == "recent_deep_write"
    assert directory.exists()


@pytest.mark.parametrize("threshold", [0, -1, float("nan"), float("inf")])
def test_invalid_scratch_thresholds_refused(threshold):
    with pytest.raises(ValueError):
        sweep.ScratchPolicy(min_age_s=threshold)
    with pytest.raises(ValueError):
        sweep.ScratchPolicy(quiet_s=threshold)


@pytest.mark.parametrize(
    "name", [".hidden", ".X11-unix", "claude-1000", "tmux-1000", "ssh-abcdef", "systemd-private-x", "codex-run"]
)
def test_excluded_names_preserved(scratch, name):
    path = scratch.tree(name)
    report = scratch.run(apply=True)
    assert scratch.row(report, name)["reason"] in {"excluded_name", "harness_runtime"} and path.exists()


@pytest.mark.parametrize("hold", ["cwd", "fd"])
def test_live_process_cwd_or_open_file_preserved(scratch, monkeypatch, hold):
    directory = scratch.tree()
    monkeypatch.setattr(sweep, "process_snapshot", REAL_PROCESS_SNAPSHOT)
    code = "import sys, time; sys.stdout.write('ready\\n'); sys.stdout.flush(); time.sleep(60)"
    if hold == "cwd":
        child = subprocess.Popen([sys.executable, "-c", code], cwd=directory / "deep", stdout=subprocess.PIPE)
    else:
        held = open(directory / "deep" / "payload", "rb")  # noqa: SIM115 - inherited by the child below
        child = subprocess.Popen(
            [sys.executable, "-c", code], stdout=subprocess.PIPE, pass_fds=(held.fileno(),), cwd=scratch.root.parent
        )
        held.close()
    try:
        assert child.stdout.readline() == b"ready\n"
        row = scratch.row(scratch.run(apply=True), directory.name)
        assert row["reason"] == "live_process" and child.pid in row["live_pids"]
        assert directory.exists()
    finally:
        child.kill()
        child.wait()


def test_uninspectable_processes_tolerated_only_for_scratch(scratch, monkeypatch):
    directory = scratch.tree()
    monkeypatch.setattr(
        sweep, "process_snapshot", lambda *a, tolerate_uninspectable=False: ([], tolerate_uninspectable)
    )
    report = scratch.run()
    assert report["process_probe_complete"] is False and report["scratch_process_probe_complete"] is True
    assert scratch.row(report, directory.name)["decision"] == "would_reap"
    monkeypatch.setattr(sweep, "process_snapshot", lambda *a, **kw: ([], False))
    assert scratch.row(scratch.run(apply=True), directory.name)["reason"] == "liveness_unknown"
    assert directory.exists()


def test_process_snapshot_tolerates_only_permission_denial(tmp_path, monkeypatch):
    proc = tmp_path / "proc"
    (proc / "21").mkdir(parents=True)
    (proc / "21" / "stat").write_text("21 (fixture) S 0")
    real_readlink = os.readlink

    def denied(path, *args, **kwargs):
        if str(path).startswith(str(proc / "21")):
            raise PermissionError(13, "denied")
        return real_readlink(path, *args, **kwargs)

    monkeypatch.setattr(sweep.os, "readlink", denied)
    assert sweep.process_snapshot(proc) == ([], False)
    assert sweep.process_snapshot(proc, tolerate_uninspectable=True) == ([], True)
    (proc / "22").mkdir()  # no stat file: unknown state, never tolerated
    assert sweep.process_snapshot(proc, tolerate_uninspectable=True)[1] is False


def test_symlink_entries_are_not_followed_or_removed(scratch, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep").write_text("keep")
    os.utime(outside / "keep", (OLD, OLD))
    link = scratch.root / "escape"
    link.symlink_to(outside, target_is_directory=True)
    os.utime(link, (OLD, OLD), follow_symlinks=False)
    report = scratch.run(apply=True)
    assert scratch.row(report, "escape")["reason"] == "symlink_or_not_directory"
    assert link.is_symlink() and (outside / "keep").exists()


def test_inner_symlink_is_not_followed(scratch, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep").write_text("keep")
    directory = scratch.tree()
    (directory / "deep" / "link").symlink_to(outside, target_is_directory=True)
    os.utime(directory / "deep" / "link", (OLD, OLD), follow_symlinks=False)
    os.utime(directory / "deep", (OLD, OLD))
    assert scratch.row(scratch.run(apply=True), directory.name)["decision"] == "reaped"
    assert (outside / "keep").exists()


@pytest.mark.parametrize("where", ["top_directory", "nested_directory", "top_file"])
def test_mount_points_are_never_crossed(scratch, monkeypatch, where):
    directory, regular = scratch.tree(), scratch.file()
    mount = {"top_directory": directory, "nested_directory": directory / "deep", "top_file": regular}[where]
    monkeypatch.setattr(sweep, "mount_points", lambda: frozenset({str(mount)}))
    target = regular if where == "top_file" else directory
    report = scratch.run(apply=True)
    assert scratch.row(report, target.name)["reason"] == "mount_point" and mount.exists()


def test_common_reaper_refuses_file_mount_point_and_hard_links(scratch, monkeypatch):
    regular = scratch.file()
    info = regular.stat()
    kwargs = {"temp_root": scratch.root, "repo_root": scratch.root.parent}
    monkeypatch.setattr(task_scratch, "mount_points", lambda: frozenset({str(regular)}))
    with pytest.raises(task_scratch.ContainmentError, match="mount point"):
        reap_attributed_temp(regular, expected_dev=info.st_dev, expected_ino=info.st_ino, **kwargs)
    monkeypatch.setattr(task_scratch, "mount_points", lambda: frozenset())
    os.link(regular, scratch.root.parent / "second-name")
    with pytest.raises(task_scratch.ContainmentError, match="hard links"):
        reap_attributed_temp(regular, expected_dev=info.st_dev, expected_ino=info.st_ino, **kwargs)
    os.unlink(scratch.root.parent / "second-name")
    with pytest.raises(task_scratch.ContainmentError, match="device/inode"):
        reap_attributed_temp(regular, expected_dev=info.st_dev, expected_ino=info.st_ino + 1, **kwargs)
    assert regular.exists()
    reap_attributed_temp(regular, expected_dev=info.st_dev, expected_ino=info.st_ino, **kwargs)
    assert not regular.exists()


def test_non_agent_owner_preserved(scratch, monkeypatch):
    directory, regular = scratch.tree(), scratch.file()
    real_uid = os.geteuid()
    monkeypatch.setattr(sweep.os, "geteuid", lambda: real_uid + 1)
    report = scratch.run(apply=True)
    assert {r["reason"] for r in report["rows"]} == {"foreign_owner"}
    assert directory.exists() and regular.exists()


def test_attributed_entries_keep_task_rules(scratch):
    directory = scratch.tree("impl-9737-probe")
    (scratch.tasks / "impl-9737.json").write_text(json.dumps({"task_id": "impl-9737", "status": "needs_finalize"}))
    report = scratch.run(apply=True)
    assert scratch.row(report, directory.name)["reason"] == "task_not_settled" and directory.exists()


def test_apply_rechecks_new_task_attribution(scratch, monkeypatch):
    directory = scratch.tree("impl-9737-probe")
    calls = 0
    original = sweep.load_tasks

    def appearing(root):
        nonlocal calls
        calls += 1
        if calls == 3:  # after the fresh reclassification, before the reaper
            (root / "impl-9737.json").write_text(json.dumps({"task_id": "impl-9737", "status": "running"}))
        return original(root)

    monkeypatch.setattr(sweep, "load_tasks", appearing)
    row = scratch.row(scratch.run(apply=True), directory.name)
    assert row["reason"] == "final_liveness_or_task_changed" and directory.exists()


def test_scratch_class_refuses_roots_outside_system_temp(scratch, monkeypatch, tmp_path):
    managed = tmp_path / "managed"
    managed.mkdir()
    monkeypatch.setattr(sweep, "SYSTEM_TEMP_AREAS", (tmp_path / "elsewhere",))
    monkeypatch.setattr(sweep, "protected_roots", lambda: {managed})
    with pytest.raises(ValueError, match="system temp"):
        sweep.sweep(temp_root=managed, task_root=scratch.tasks, repo_root=tmp_path, scratch=sweep.ScratchPolicy())


def test_cli_summary_has_counts_without_names(scratch, capsys):
    scratch.tree()
    argv = ["--temp-root", str(scratch.root), "--task-root", str(scratch.tasks), "--unattributed-scratch"]
    assert sweep.main([*argv, "--summary"]) == 0
    out = capsys.readouterr().out
    summary = json.loads(out)
    assert "rows" not in summary and "hand-made-scratch" not in out
    assert summary["by_reason"] == {"unattributed_scratch": 1} and summary["bytes_reclaimed"] == 0
    with pytest.raises(SystemExit) as exc:
        sweep.main([*argv, "--scratch-quiet-hours", "0"])
    assert exc.value.code == 2
