"""Unattributed-scratch class of the temp sweep (#9737)."""

from __future__ import annotations

import errno
import fcntl
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


def _quarantines(root):
    return sorted(root.glob(sweep.QUARANTINE_PREFIX + "*"))


def _target(scratch, kind):
    """A quiet candidate and the file inside it that writers and holders use."""
    if kind == "file":
        regular = scratch.file()
        return regular, regular
    directory = scratch.tree()
    return directory, directory / "deep" / "payload"


def _assert_restored(scratch, report, entry, reason):
    row = scratch.row(report, entry.name)
    assert (row["decision"], row["reason"]) == ("preserve", reason)
    assert entry.exists() and not _quarantines(scratch.root) and report["errors"] == 0


@pytest.mark.parametrize("kind", ["directory", "file"])
@pytest.mark.parametrize(
    "point", ["after_snapshot", "before_rename", "after_rename", "during_task_check", "during_process_scan"]
)
def test_write_between_snapshot_and_removal_is_preserved_and_restored(scratch, monkeypatch, kind, point):
    """A real write at every point from the pre-rename snapshot to removal keeps the entry.

    Before the rename the writer uses the entry's path. Afterwards the old
    path is gone, so the writer is this process: it opens the payload just
    before the rename and writes and closes it before the post-rename scan,
    which therefore cannot see it; only the post-rename write check can.
    """
    entry, payload = _target(scratch, kind)
    monkeypatch.setattr(sweep, "process_snapshot", real_references_complete)
    held, wrote, renames = [], [], []
    scans, task_reads = [0], [0]
    real_rename, real_load = sweep.rename_noreplace, sweep.load_tasks

    def write_and_close():
        handle = held.pop() if held else open(payload, "r+b")  # noqa: SIM115 - closed below
        with handle:
            handle.write(b"fresh write")
        wrote.append(point)

    def scan(*args, **kwargs):
        scans[0] += 1
        if (point, scans[0]) in {("after_snapshot", 2), ("during_process_scan", 3)}:
            write_and_close()
        return real_references_complete()

    def rename(src_fd, src, dst_fd, dst):
        forward = not renames
        renames.append(src)
        if forward and point == "before_rename":
            write_and_close()
        elif forward and point != "after_snapshot":
            held.append(open(payload, "r+b"))  # noqa: SIM115 - the writer opens just before the rename
        real_rename(src_fd, src, dst_fd, dst)
        if forward and point == "after_rename":
            write_and_close()

    def load(root):
        task_reads[0] += 1
        if point == "during_task_check" and task_reads[0] == 3:
            write_and_close()
        return real_load(root)

    monkeypatch.setattr(sweep, "process_snapshot", scan)
    monkeypatch.setattr(sweep, "rename_noreplace", rename)
    monkeypatch.setattr(sweep, "load_tasks", load)
    report = scratch.run(apply=True)
    assert wrote == [point] and not held
    expected = "proof_changed" if point == "after_snapshot" else "quarantine_write"
    _assert_restored(scratch, report, entry, expected)
    assert payload.read_bytes().startswith(b"fresh write")


def test_metadata_only_change_is_seen_through_change_time(scratch, monkeypatch):
    """Same size, mtime put back: only the inode change time records the write."""
    entry, payload = _target(scratch, "directory")
    real_rename = sweep.rename_noreplace
    renames = []

    def rename(src_fd, src, dst_fd, dst):
        if not renames:
            payload.write_bytes(b"z" * 8192)
            os.utime(payload, (OLD, OLD))
        renames.append(src)
        real_rename(src_fd, src, dst_fd, dst)

    monkeypatch.setattr(sweep, "rename_noreplace", rename)
    _assert_restored(scratch, scratch.run(apply=True), entry, "quarantine_write")
    assert payload.read_bytes() == b"z" * 8192


def test_write_during_final_process_scan_is_never_lost(scratch, monkeypatch):
    """The round-2 reproduction: a path write during the last process scan before removal.

    With the rename boundary the old path no longer exists at that scan, so
    the write either fails with ENOENT (nothing was written and removal is
    correct) or lands and the entry survives. Removing a landed write fails.
    The writer is this test process, which the scan therefore leaves out, as
    the reviewer's out-of-process writer would be absent from it.
    """
    entry, payload = _target(scratch, "directory")
    outcomes = []
    scans = [0]

    def scan(*args, **kwargs):
        scans[0] += 1
        if scans[0] == 3:
            try:
                payload.write_bytes(b"fresh write")
                outcomes.append("written")
            except FileNotFoundError:
                outcomes.append("enoent")
        return [(pid, ref) for pid, ref in real_references_complete()[0] if pid != os.getpid()], True

    monkeypatch.setattr(sweep, "process_snapshot", scan)
    report = scratch.run(apply=True)
    assert outcomes, "the final scan never ran"
    if outcomes == ["written"]:
        assert payload.read_bytes() == b"fresh write"
    else:
        assert scratch.row(report, entry.name)["decision"] == "reaped" and not entry.exists()


def test_real_process_scan_reaps_unheld_entries(scratch, monkeypatch):
    """Under the real scan, the sweep's own descriptors never count as a holder of the entry."""
    directory, regular = scratch.tree(), scratch.file()
    monkeypatch.setattr(sweep, "process_snapshot", real_references_complete)
    report = scratch.run(apply=True)
    assert {r["name"]: r["decision"] for r in report["rows"]} == {directory.name: "reaped", regular.name: "reaped"}
    assert not directory.exists() and not regular.exists() and report["errors"] == 0


def test_old_path_is_gone_once_quarantined(scratch, monkeypatch):
    entry, payload = _target(scratch, "directory")
    real_reap = sweep.reap_attributed_temp
    seen = []

    def reap(path, **kwargs):
        with pytest.raises(FileNotFoundError):
            payload.open("rb")
        seen.append(path.parent.name)
        return real_reap(path, **kwargs)

    monkeypatch.setattr(sweep, "reap_attributed_temp", reap)
    report = scratch.run(apply=True)
    assert seen and seen[0].startswith(sweep.QUARANTINE_PREFIX)
    assert scratch.row(report, entry.name)["decision"] == "reaped" and not _quarantines(scratch.root)


HOLDER_BY_MODE = (
    "import mmap, os, sys, time\n"
    "mode, target = sys.argv[1], sys.argv[2]\n"
    "if mode == 'cwd':\n"
    "    os.chdir(target)\n"
    "elif mode == 'fd':\n"
    "    held = open(target, 'rb')\n"
    "else:\n"
    "    with open(target, 'rb') as handle:\n"
    "        mapped = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)\n"
    "sys.stdout.write('ready\\n'); sys.stdout.flush(); time.sleep(60)\n"
)


@pytest.mark.parametrize(
    ("kind", "mode"),
    [("directory", "cwd"), ("directory", "fd"), ("directory", "mmap"), ("file", "fd"), ("file", "mmap")],
)
def test_holder_opening_just_before_rename_is_found_after_it(scratch, monkeypatch, tmp_path, kind, mode):
    entry, payload = _target(scratch, kind)
    monkeypatch.setattr(sweep, "process_snapshot", real_references_complete)
    real_rename = sweep.rename_noreplace
    children = []

    def rename(src_fd, src, dst_fd, dst):
        if not children:
            target = payload.parent if mode == "cwd" else payload
            child = subprocess.Popen(
                [sys.executable, "-c", HOLDER_BY_MODE, mode, str(target)], stdout=subprocess.PIPE, cwd=tmp_path
            )
            children.append(child)
            assert child.stdout.readline() == b"ready\n"
        real_rename(src_fd, src, dst_fd, dst)

    monkeypatch.setattr(sweep, "rename_noreplace", rename)
    try:
        report = scratch.run(apply=True)
        assert children, "the holder never started"
        _assert_restored(scratch, report, entry, "quarantine_live_process")
        assert children[0].poll() is None
    finally:
        for child in children:
            child.kill()
            child.wait()


def test_uninspectable_process_after_rename_restores(scratch, monkeypatch):
    entry, _ = _target(scratch, "directory")
    probes = iter([([], True), ([], True), ([], False)])
    monkeypatch.setattr(sweep, "process_snapshot", lambda *a, **kw: next(probes))
    _assert_restored(scratch, scratch.run(apply=True), entry, "quarantine_liveness_unknown")


@pytest.mark.parametrize("code", [errno.EXDEV, errno.EBUSY, errno.EACCES, errno.ENOSYS])
def test_rename_failure_preserves_with_typed_reason(scratch, monkeypatch, code):
    entry, payload = _target(scratch, "directory")

    def failing(*_args):
        raise OSError(code, os.strerror(code))

    monkeypatch.setattr(sweep, "rename_noreplace", failing)
    row = scratch.row(scratch.run(apply=True), entry.name)
    assert (row["decision"], row["reason"], row["error"]) == ("preserve", "quarantine_failed", errno.errorcode[code])
    assert payload.exists() and not _quarantines(scratch.root)


def test_real_rename_failure_preserves_moved_entry(scratch, monkeypatch):
    """The entry moves away just before the rename: the kernel's ENOENT preserves it."""
    entry, _ = _target(scratch, "directory")
    real_rename = sweep.rename_noreplace
    moved = scratch.root / "moved-away"

    def rename(src_fd, src, dst_fd, dst):
        if not moved.exists():
            entry.rename(moved)
        real_rename(src_fd, src, dst_fd, dst)

    monkeypatch.setattr(sweep, "rename_noreplace", rename)
    row = scratch.row(scratch.run(apply=True), entry.name)
    assert (row["reason"], row["error"]) == ("quarantine_failed", "ENOENT")
    assert (moved / "deep" / "payload").exists()


def test_restore_blocked_keeps_entry_quarantined_and_reports(scratch, monkeypatch):
    entry, _ = _target(scratch, "directory")
    real_rename = sweep.rename_noreplace
    renames = []

    def rename(src_fd, src, dst_fd, dst):
        real_rename(src_fd, src, dst_fd, dst)
        if not renames:
            # A held descriptor wrote the tree, and a newcomer took the old name.
            quarantined = _quarantines(scratch.root)[0] / entry.name
            (quarantined / "deep" / "payload").write_bytes(b"fresh write")
            entry.mkdir()
            (entry / "newcomer").write_text("unrelated")
        renames.append(src)

    monkeypatch.setattr(sweep, "rename_noreplace", rename)
    report = scratch.run(apply=True)
    blocked = next(r for r in report["rows"] if r["reason"] == "restore_blocked")
    assert (blocked["found"], blocked["error"]) == ("quarantine_write", "EEXIST") and report["errors"] == 1
    [quarantine] = _quarantines(scratch.root)
    assert (quarantine / entry.name / "deep" / "payload").read_bytes() == b"fresh write"
    assert (entry / "newcomer").read_text() == "unrelated"
    # A later run still cannot restore while the name is taken, and deletes nothing.
    # Real time: the newcomer is minutes old, not three days.
    monkeypatch.setattr(sweep, "rename_noreplace", real_rename)
    monkeypatch.setattr(sweep, "time", time)
    again = scratch.run(apply=True)
    assert [r["reason"] for r in again["rows"] if r.get("quarantine") == quarantine.name] == ["restore_blocked"]
    assert (quarantine / entry.name / "deep" / "payload").exists() and (entry / "newcomer").exists()


def _leftover(scratch, name="hand-made-scratch"):
    quarantine = scratch.root / f"{sweep.QUARANTINE_PREFIX}crashed"
    quarantine.mkdir(mode=0o700)
    original = scratch.tree(name)
    original.rename(quarantine / name)
    return quarantine, quarantine / name


def test_crash_leftover_is_reported_in_dry_run_and_untouched(scratch):
    quarantine, entry = _leftover(scratch)
    row = scratch.row(scratch.run(), entry.name)
    assert (row["decision"], row["reason"], row["quarantine"]) == ("preserve", "quarantine_leftover", quarantine.name)
    assert (entry / "deep" / "payload").exists()


def test_crash_leftover_is_restored_then_held_by_a_live_process(scratch, monkeypatch, tmp_path):
    """A leftover is never deleted from quarantine; restored, it meets every check again."""
    quarantine, entry = _leftover(scratch)
    monkeypatch.setattr(sweep, "process_snapshot", real_references_complete)
    child = subprocess.Popen(
        [sys.executable, "-c", HOLDER_BY_MODE, "cwd", str(entry / "deep")], stdout=subprocess.PIPE, cwd=tmp_path
    )
    try:
        assert child.stdout.readline() == b"ready\n"
        report = scratch.run(apply=True)
        assert report["quarantine_restored"] == 1 and not quarantine.exists()
        assert scratch.row(report, entry.name)["reason"] == "live_process"
        assert (scratch.root / entry.name / "deep" / "payload").exists() and child.poll() is None
    finally:
        child.kill()
        child.wait()


def test_crash_leftover_without_holder_goes_through_the_whole_boundary(scratch, monkeypatch):
    _quarantine, entry = _leftover(scratch)
    real_rename = sweep.rename_noreplace
    renames = []

    def rename(src_fd, src, dst_fd, dst):
        renames.append(src)
        real_rename(src_fd, src, dst_fd, dst)

    monkeypatch.setattr(sweep, "rename_noreplace", rename)
    report = scratch.run(apply=True)
    # Restored first, then quarantined afresh and re-verified before removal.
    assert renames == [entry.name, entry.name] and report["quarantine_restored"] == 1
    assert scratch.row(report, entry.name)["decision"] == "reaped" and not _quarantines(scratch.root)


def test_crash_leftover_with_taken_name_stays_quarantined(scratch):
    quarantine, entry = _leftover(scratch)
    (scratch.root / entry.name).mkdir()
    report = scratch.run(apply=True)
    row = next(r for r in report["rows"] if r.get("quarantine") == quarantine.name)
    assert (row["reason"], row["error"]) == ("restore_blocked", "EEXIST") and report["errors"] == 1
    assert (entry / "deep" / "payload").exists()


def test_quarantine_of_a_live_run_is_left_alone(scratch):
    quarantine, entry = _leftover(scratch)
    fd = os.open(quarantine, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report = scratch.run(apply=True)
    finally:
        os.close(fd)
    assert report["quarantine_restored"] == 0 and (entry / "deep" / "payload").exists()
    assert all(r.get("quarantine") != quarantine.name for r in report["rows"])


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
    # Third read: the post-rename check on the quarantined entry.
    directory = scratch.tree("impl-9737-probe")
    calls = 0
    original = sweep.load_tasks

    def appearing(root):
        nonlocal calls
        calls += 1
        if calls == 3:  # after the fresh reclassification and the rename
            (root / "impl-9737.json").write_text(json.dumps({"task_id": "impl-9737", "status": "running"}))
        return original(root)

    monkeypatch.setattr(sweep, "load_tasks", appearing)
    row = scratch.row(scratch.run(apply=True), directory.name)
    assert row["reason"] == "quarantine_task_reference" and directory.exists()


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
