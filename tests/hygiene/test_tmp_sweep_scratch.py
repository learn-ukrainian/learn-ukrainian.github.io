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
HOLDER = "import sys, time; sys.stdout.write('ready\\n'); sys.stdout.flush(); time.sleep(60)"
# A same-user process that makes itself non-dumpable (PR_SET_DUMPABLE = 4):
# the kernel then refuses /proc/<pid>/cwd and /proc/<pid>/fd to its owner too.
NON_DUMPABLE_HOLDER = (
    "import ctypes, os, sys, time\n"
    "if ctypes.CDLL(None, use_errno=True).prctl(4, 0, 0, 0, 0) != 0:\n"
    "    sys.stdout.write('unsupported\\n'); sys.stdout.flush(); sys.exit(0)\n"
    "if sys.argv[1] == 'cwd':\n"
    "    os.chdir(sys.argv[2])\n"
    "else:\n"
    "    held = open(sys.argv[2], 'rb')\n"
    "sys.stdout.write('ready\\n'); sys.stdout.flush(); time.sleep(60)\n"
)


def real_references_complete(*_args, **_kwargs):
    """Real cwd/FD references with enumeration isolated from other users' processes."""
    return REAL_PROCESS_SNAPSHOT()[0], True


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
    code = HOLDER
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


def test_uninspectable_processes_preserve_scratch(scratch, monkeypatch):
    directory, regular = scratch.tree(), scratch.file()
    monkeypatch.setattr(sweep, "process_snapshot", lambda *a, **kw: ([], False))
    report = scratch.run(apply=True)
    assert report["process_probe_complete"] is False
    assert {r["reason"] for r in report["rows"]} == {"liveness_unknown"}
    assert directory.exists() and regular.exists() and report["bytes_reclaimed"] == 0


def test_process_snapshot_permission_denial_is_incomplete(tmp_path, monkeypatch):
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


@pytest.mark.parametrize("hold", ["cwd", "fd"])
def test_non_dumpable_holder_preserves_scratch(scratch, monkeypatch, tmp_path, hold):
    """A real same-user process the kernel will not let us inspect keeps the entry."""
    directory = scratch.tree()
    target = directory / "deep" if hold == "cwd" else directory / "deep" / "payload"
    child = subprocess.Popen(
        [sys.executable, "-c", NON_DUMPABLE_HOLDER, hold, str(target)], stdout=subprocess.PIPE, cwd=tmp_path
    )
    try:
        line = child.stdout.readline()
        if line == b"unsupported\n":
            pytest.skip("prctl(PR_SET_DUMPABLE, 0) is unavailable on this platform")
        assert line == b"ready\n"
        try:
            os.readlink(f"/proc/{child.pid}/cwd")
        except PermissionError:
            pass
        else:
            pytest.skip("this user may inspect non-dumpable processes (privileged runner)")
        # Enumerate only the holder; every read below is a real kernel check.
        view = tmp_path / "proc-view"
        view.mkdir()
        (view / str(child.pid)).symlink_to(f"/proc/{child.pid}", target_is_directory=True)
        monkeypatch.setattr(sweep, "process_snapshot", lambda *a, **kw: REAL_PROCESS_SNAPSHOT(view, **kw))
        report = scratch.run(apply=True)
        assert report["process_probe_complete"] is False
        assert scratch.row(report, directory.name)["reason"] == "liveness_unknown"
        assert target.exists() and child.poll() is None
    finally:
        child.kill()
        child.wait()


@pytest.mark.parametrize("field", ["runtime_tmp_root", "worktree_path", "cwd", "nested_env", "temp_root"])
def test_unsettled_task_path_reference_preserves(scratch, field):
    directory, regular = scratch.tree(), scratch.file()
    record = {"task_id": "impl-unrelated", "status": "running"}
    if field == "nested_env":
        record["launch"] = {"env": {"TMPDIR": str(directory / "deep")}, "argv": ["tool", str(regular)]}
    elif field == "temp_root":
        record["runtime_tmp_root"] = str(scratch.root)
    else:
        record[field] = str(directory if field != "cwd" else directory / "deep")
        record["log"] = str(regular)
    (scratch.tasks / "impl-unrelated.json").write_text(json.dumps(record))
    report = scratch.run(apply=True)
    assert {r["name"]: r["reason"] for r in report["rows"]} == {
        directory.name: "task_reference",
        regular.name: "task_reference",
    }
    assert directory.exists() and regular.exists()
    # The same references stop holding once the task has settled.
    (scratch.tasks / "impl-unrelated.json").write_text(json.dumps(record | {"status": "done"}))
    assert {r["decision"] for r in scratch.run(apply=True)["rows"]} == {"reaped"}


def test_superseded_task_run_claims_nothing(scratch):
    directory = scratch.tree()
    superseded = {"task_id": "impl-old", "status": "running", "runtime_tmp_root": str(directory)}
    (scratch.tasks / "impl-old.20260101T000000123456Z.archived.json").write_text(json.dumps(superseded))
    report = scratch.run(apply=True)
    assert report["task_inventory_complete"] is True
    assert scratch.row(report, directory.name)["decision"] == "reaped"


@pytest.mark.parametrize(
    "state", ["missing_root", "unreadable_root", "malformed", "mismatched", "unreadable", "symlink"]
)
def test_unknown_task_inventory_preserves(scratch, tmp_path, state):
    directory, regular = scratch.tree(), scratch.file()
    task_root = scratch.tasks
    record = scratch.tasks / "impl-other.json"
    if state == "missing_root":
        task_root = tmp_path / "absent-tasks"
    elif state == "unreadable_root":
        os.chmod(task_root, 0)
    elif state == "malformed":
        record.write_text("{truncated")
    elif state == "mismatched":
        record.write_text(json.dumps({"task_id": "someone-else", "status": "done"}))
    elif state == "unreadable":
        record.write_text(json.dumps({"task_id": "impl-other", "status": "done"}))
        os.chmod(record, 0)
    else:
        (tmp_path / "real.json").write_text(json.dumps({"task_id": "impl-other", "status": "done"}))
        record.symlink_to(tmp_path / "real.json")
    try:
        if state.startswith("unreadable") and os.access(task_root if state == "unreadable_root" else record, os.R_OK):
            pytest.skip("this user reads files regardless of mode bits (privileged runner)")
        report = sweep.sweep(
            temp_root=scratch.root,
            task_root=task_root,
            repo_root=tmp_path,
            scratch=sweep.ScratchPolicy(),
            apply=True,
        )
    finally:
        os.chmod(scratch.tasks, 0o700)
        if record.exists() and not record.is_symlink():
            os.chmod(record, 0o600)
    assert report["task_inventory_complete"] is False
    assert {r["reason"] for r in report["rows"]} == {"task_inventory_unknown"}
    assert directory.exists() and regular.exists() and report["bytes_reclaimed"] == 0


@pytest.mark.parametrize("race", ["holder", "write"])
def test_holder_or_write_during_reaper_preflight_preserves(scratch, monkeypatch, race):
    """Interleave a real holder or write with the common remover's own tree traversal."""
    directory = scratch.tree()
    monkeypatch.setattr(sweep, "process_snapshot", real_references_complete)
    real_walk = task_scratch._walk_stats
    children = []

    def racing_walk(*args, **kwargs):
        if not children and race == "holder":
            children.append(
                subprocess.Popen([sys.executable, "-c", HOLDER], cwd=directory / "deep", stdout=subprocess.PIPE)
            )
            assert children[0].stdout.readline() == b"ready\n"
        elif not children:
            children.append(None)
            (directory / "deep" / "payload").write_bytes(b"fresh write")
        return real_walk(*args, **kwargs)

    monkeypatch.setattr(task_scratch, "_walk_stats", racing_walk)
    try:
        report = scratch.run(apply=True)
        row = scratch.row(report, directory.name)
        assert children, "the race hook never ran: the remover skipped its preflight"
        assert (row["decision"], row["reason"]) == ("preserve", "final_liveness_or_task_changed")
        assert (directory / "deep" / "payload").exists() and report["errors"] == 0
    finally:
        for child in children:
            if child is not None:
                child.kill()
                child.wait()


def test_write_during_file_reaper_checks_preserves(scratch, monkeypatch):
    regular = scratch.file()
    real_mounts = task_scratch.mount_points
    raced = []

    def racing_mounts():
        if not raced:
            raced.append(True)
            regular.write_bytes(b"fresh write")
        return real_mounts()

    monkeypatch.setattr(task_scratch, "mount_points", racing_mounts)
    row = scratch.row(scratch.run(apply=True), regular.name)
    assert raced and (row["decision"], row["reason"]) == ("preserve", "final_liveness_or_task_changed")
    assert regular.read_bytes() == b"fresh write"


def test_removal_recheck_runs_after_reaper_preflight(scratch, monkeypatch):
    """The final check is the last step before the first unlink, not before the reaper call."""
    directory = scratch.tree()
    events = []
    real_walk, real_rmtree = task_scratch._walk_stats, task_scratch._rmtree_fd
    real_recheck = sweep.removal_recheck

    def recording_recheck(*args, **kwargs):
        check = real_recheck(*args, **kwargs)
        return lambda: (events.append("recheck"), check())

    monkeypatch.setattr(sweep, "removal_recheck", recording_recheck)
    monkeypatch.setattr(
        task_scratch, "_walk_stats", lambda *a, **kw: (events.append("preflight"), real_walk(*a, **kw))[1]
    )
    monkeypatch.setattr(
        task_scratch, "_rmtree_fd", lambda *a, **kw: (events.append("unlink"), real_rmtree(*a, **kw))[1]
    )
    assert scratch.row(scratch.run(apply=True), directory.name)["decision"] == "reaped"
    # Both tree walkers recurse; collapse repeats to see the phase order.
    phases = [event for index, event in enumerate(events) if index == 0 or events[index - 1] != event]
    assert phases == ["preflight", "recheck", "unlink"]


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
    # Third read: the removal-time recheck inside the common reaper.
    directory = scratch.tree("impl-9737-probe")
    calls = 0
    original = sweep.load_tasks

    def appearing(root):
        nonlocal calls
        calls += 1
        if calls == 3:  # after the fresh reclassification, inside the reaper
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
