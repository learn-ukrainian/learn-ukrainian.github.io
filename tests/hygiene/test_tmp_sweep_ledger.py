"""Deletion ledger, recoverable quarantine, purge and restore of the temp sweep (#9887).

Real files, renames and processes throughout; a crash is a real child
process killed between two steps with ``os._exit``.
"""

from __future__ import annotations

import errno
import itertools
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.hygiene import tmp_sweep as sweep
from scripts.hygiene import tmp_sweep_ledger as ledger_mod

DAY = 86400
OLD = time.time() - 3 * DAY
REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_PROCESS_SNAPSHOT = sweep.process_snapshot
HOLDER = "import os, sys, time; os.chdir(sys.argv[1]); sys.stdout.write('ready\\n'); sys.stdout.flush(); time.sleep(60)"
# Runs one apply sweep as a separate process and kills itself at ``point``.
CRASH_DRIVER = """
import os, sys, time
from pathlib import Path
from types import SimpleNamespace
from scripts.hygiene import tmp_sweep as sweep

root, tasks, repo, point, offset = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], float(sys.argv[5])
now = float(sys.argv[6]) + offset
sweep.time = SimpleNamespace(time=lambda: now)
sweep.process_snapshot = lambda *a, **kw: ([], True)
sweep.registered_worktrees = lambda _: set()
sweep.protected_roots = lambda: set()
real_rename, real_reap = sweep.rename_noreplace, sweep.reap_attributed_temp

def rename(*args):
    if point == "before_rename":
        os._exit(137)
    real_rename(*args)
    if point == "after_rename":
        os._exit(137)

def reap(*args, **kwargs):
    if point == "before_reap":
        os._exit(137)
    real_reap(*args, **kwargs)
    os._exit(137)

sweep.rename_noreplace = rename
sweep.reap_attributed_temp = reap
sweep.sweep(temp_root=root, task_root=tasks, repo_root=repo, scratch=sweep.ScratchPolicy(), apply=True)
os._exit(0)
"""


@pytest.fixture
def box(tmp_path, monkeypatch, isolated_state_home):
    """A temp root with a three-day-old tree and file, a task root, and a movable sweep clock."""
    root = tmp_path / "system-temp"
    root.mkdir()
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    start = time.time() + 3 * DAY
    clock = SimpleNamespace(now=start)
    monkeypatch.setattr(sweep, "time", SimpleNamespace(time=lambda: clock.now))
    monkeypatch.setattr(sweep, "process_snapshot", lambda *a, **kw: ([], True))
    monkeypatch.setattr(sweep, "registered_worktrees", lambda _: set())
    monkeypatch.setattr(sweep, "protected_roots", lambda: set())
    state = isolated_state_home / "learn-ukrainian" / "tmp-sweep"

    def tree(name="hand-made-scratch"):
        path = root / name
        (path / "deep" / "empty").mkdir(parents=True)
        (path / "deep" / "payload").write_bytes(os.urandom(8192))
        (path / "run.sh").write_bytes(b"#!/bin/sh\necho hi\n")
        os.chmod(path / "run.sh", 0o750)
        (path / "link").symlink_to("deep/payload")
        for entry in (path / "deep" / "payload", path / "deep" / "empty", path / "run.sh", path / "deep", path):
            os.utime(entry, (OLD, OLD))
        os.utime(path / "link", (OLD, OLD), follow_symlinks=False)
        return path

    def run(**kwargs):
        kwargs.setdefault("scratch", sweep.ScratchPolicy())
        return sweep.sweep(temp_root=root, task_root=tasks, repo_root=tmp_path, **kwargs)

    def at(days):
        clock.now = start + days * DAY

    def records():
        return [json.loads(line) for line in (state / "ledger.jsonl").read_text().splitlines()]

    def entries():
        return ledger_mod.Ledger(state).entries()[0]

    def crash(point, days=0.0):
        child = subprocess.run(
            [
                sys.executable,
                "-c",
                CRASH_DRIVER,
                str(root),
                str(tasks),
                str(tmp_path),
                point,
                str(days * DAY),
                str(start),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
            timeout=60,
        )
        assert child.returncode == 137, child.stderr.decode()

    return SimpleNamespace(
        root=root,
        tasks=tasks,
        tmp=tmp_path,
        state=state,
        tree=tree,
        run=run,
        at=at,
        records=records,
        entries=entries,
        crash=crash,
    )


def snapshot(path: Path) -> dict[str, tuple]:
    """Bytes, permission bits, mtime and link target of every node below ``path``."""
    nodes = {}
    for node in [path, *sorted(path.rglob("*"))]:
        info = node.lstat()
        content = os.readlink(node) if node.is_symlink() else node.read_bytes() if node.is_file() else None
        nodes[str(node.relative_to(path))] = (info.st_mode, info.st_mtime_ns, content)
    return nodes


def only(entries):
    [entry] = entries.values()
    return entry


def quarantines(root):
    return sorted(root.glob(sweep.QUARANTINE_PREFIX + "*"))


def test_ledger_record_is_durable_before_the_rename(box, monkeypatch):
    entry = box.tree()
    real_rename = sweep.rename_noreplace
    seen = []

    def rename(src_fd, src, dst_fd, dst):
        if not seen:
            # A fresh reader sees the complete record while the entry is still at its path.
            seen.append(box.records())
            assert entry.is_dir()
        real_rename(src_fd, src, dst_fd, dst)

    monkeypatch.setattr(sweep, "rename_noreplace", rename)
    report = box.run(apply=True)
    [[record]] = seen
    assert record["event"] == "quarantine" and record["schema"] == ledger_mod.SCHEMA
    assert record["original_path"] == str(entry) and record["run_id"] == report["run_id"]
    assert Path(record["quarantine_path"]).parent.name.startswith(sweep.QUARANTINE_PREFIX)
    assert record["owner_uid"] == os.getuid() and record["reason"] == "unattributed_scratch"
    assert (record["file_count"], record["total_bytes"]) == (2, 8192 + 18)
    manifest = {item["path"]: item for item in record["manifest"]}
    assert set(manifest) == {".", "deep", "deep/empty", "deep/payload", "link", "run.sh"}
    assert manifest["link"]["target"] == "deep/payload" and manifest["run.sh"]["mode"] == 0o750
    assert len(manifest["deep/payload"]["sha256"]) == 64
    row = next(r for r in report["rows"] if r["name"] == entry.name)
    assert (row["decision"], row["ledger_id"]) == ("quarantined", record["ledger_id"])
    assert [r["event"] for r in box.records()] == ["quarantine", "quarantined"]


def test_large_files_are_recorded_without_digest(box):
    entry = box.tree()
    box.run(apply=True, digest_limit=4096)
    manifest = {item["path"]: item for item in only(box.entries()).intent["manifest"]}
    assert manifest["deep/payload"] == manifest["deep/payload"] | {"digest_skipped_size": True, "size": 8192}
    assert "sha256" not in manifest["deep/payload"] and "sha256" in manifest["run.sh"]
    assert not entry.exists()


def test_crash_between_ledger_write_and_rename_is_reconciled(box):
    entry = box.tree()
    box.crash("before_rename")
    first = only(box.entries())
    assert first.state == "pending" and entry.is_dir()
    dry = box.run()
    assert next(r for r in dry["rows"] if r.get("ledger_id") == first.ledger_id)["reason"] == "ledger_unreconciled"
    box.run(apply=True)
    states = {key: value.state for key, value in box.entries().items()}
    assert states.pop(first.ledger_id) == "at_origin" and list(states.values()) == ["quarantined"]
    reconciled = [r for r in box.records() if r["ledger_id"] == first.ledger_id][-1]
    assert (reconciled["event"], reconciled["outcome"]) == ("reconciled", "at_origin")


def test_crash_after_rename_before_confirmation_returns_the_entry(box):
    entry = box.tree()
    before = snapshot(entry)
    box.crash("after_rename")
    first = only(box.entries())
    assert first.state == "pending" and not entry.exists() and first.location.is_dir()
    box.run(apply=True)
    events = [(r["event"], r.get("outcome")) for r in box.records() if r["ledger_id"] == first.ledger_id]
    assert events == [("quarantine", None), ("reconciled", "returned")]
    # Returned unverified, then quarantined afresh under a new ledger id.
    [second] = [e for e in box.entries().values() if e.ledger_id != first.ledger_id]
    assert second.state == "quarantined" and snapshot(second.location) == before


@pytest.mark.parametrize("point", ["before_reap", "after_reap"])
def test_interrupted_purge_is_completed_or_reconciled(box, point):
    box.tree()
    box.run(apply=True)
    entry = only(box.entries())
    box.crash(point, days=8)
    assert box.entries()[entry.ledger_id].state == "purging"
    box.at(8)
    report = box.run(apply=True)
    events = [r["event"] for r in box.records() if r["ledger_id"] == entry.ledger_id]
    if point == "before_reap":
        assert events[-3:] == ["purge", "purge", "purged"] and report["purged_entries"] == 1
    else:
        assert events[-2:] == ["purge", "reconciled"] and box.records()[-1]["outcome"] == "purged"
    assert box.entries()[entry.ledger_id].state == "purged" and not entry.location.exists()


def test_restore_round_trip_is_byte_identical(box, capsys):
    entry = box.tree()
    before = snapshot(entry)
    box.run(apply=True)
    held = only(box.entries())
    assert not entry.exists() and snapshot(held.location) == before
    assert sweep.main(["restore", held.ledger_id]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result | {"restored": True, "verified": True, "mismatch_count": 0} == result
    assert snapshot(entry) == before and not quarantines(box.root)
    assert [r["event"] for r in box.records()][-2:] == ["restore", "restored"]
    assert box.entries()[held.ledger_id].state == "restored"
    # Restored means back in the pipeline, never twice.
    assert sweep.main(["restore", held.ledger_id]) == 1
    assert json.loads(capsys.readouterr().out)["reason"] == "state_restored"


def test_restore_reports_a_tree_changed_in_quarantine(box, capsys):
    entry = box.tree()
    box.run(apply=True)
    held = only(box.entries())
    (held.location / "deep" / "payload").write_bytes(b"changed")
    assert sweep.main(["restore", held.ledger_id]) == 1
    result = json.loads(capsys.readouterr().out)
    assert (result["restored"], result["verified"], result["mismatches"]) == (True, False, ["deep/payload"])
    assert (entry / "deep" / "payload").read_bytes() == b"changed"


def test_restore_never_overwrites(box, capsys, monkeypatch):
    entry = box.tree()
    box.run(apply=True)
    held = only(box.entries())
    entry.mkdir()
    (entry / "newcomer").write_text("unrelated")
    count = len(box.records())
    assert sweep.main(["restore", held.ledger_id]) == 1
    assert json.loads(capsys.readouterr().out)["reason"] == "original_path_exists"
    assert len(box.records()) == count and (entry / "newcomer").read_text() == "unrelated"
    # The name is taken between the check and the rename: renameat2 refuses, and the ledger says so.
    shutil.rmtree(entry)
    real_rename = sweep.rename_noreplace

    def racing(*args):
        entry.mkdir()
        real_rename(*args)

    monkeypatch.setattr(sweep, "rename_noreplace", racing)
    assert sweep.main(["restore", held.ledger_id]) == 1
    result = json.loads(capsys.readouterr().out)
    assert (result["restored"], result["reason"], result["error"]) == (False, "original_path_exists", "EEXIST")
    assert [r["event"] for r in box.records()][-2:] == ["restore", "restore_failed"]
    assert box.entries()[held.ledger_id].state == "quarantined" and (held.location / "deep" / "payload").exists()
    assert list(entry.iterdir()) == []


def test_restore_unknown_id_creates_nothing(box):
    with pytest.raises(SystemExit) as exc:
        sweep.main(["restore", "000000000000"])
    assert exc.value.code == 2 and not box.state.exists()


def test_restore_unknown_id_and_busy_ledger(box, capsys):
    box.tree()
    box.run(apply=True)
    held = only(box.entries())
    with pytest.raises(SystemExit) as exc:
        sweep.main(["restore", "000000000000"])
    assert exc.value.code == 2
    with ledger_mod.Ledger(box.state).exclusive(wait=False):
        assert sweep.main(["restore", held.ledger_id]) == 1
    assert "holds the ledger" in capsys.readouterr().err
    assert held.location.is_dir()


def test_purge_happens_only_after_the_window(box):
    entry = box.tree()
    box.run(apply=True)
    held = only(box.entries())
    box.at(6.9)
    inside = box.run(apply=True)
    assert inside["purged_entries"] == 0 and inside["quarantine_held_entries"] == 1 and held.location.is_dir()
    box.at(7.1)
    dry = box.run()
    assert (dry["purgeable_entries"], dry["bytes_purgeable"]) == (1, held.intent["allocated_bytes"])
    assert dry["projected_free_bytes"] == dry["free_bytes"] + dry["bytes_purgeable"] and held.location.is_dir()
    applied = box.run(apply=True)
    assert applied["purged_entries"] == 1 and applied["bytes_reclaimed"] == held.intent["allocated_bytes"]
    assert applied["quarantine_held_entries"] == 0 and not held.location.exists() and not quarantines(box.root)
    assert [r["event"] for r in box.records()] == ["quarantine", "quarantined", "purge", "purged"]
    assert not entry.exists()


def test_quarantine_window_is_configurable(box):
    box.tree()
    box.run(apply=True)
    box.at(2)
    assert box.run(apply=True)["purged_entries"] == 0
    assert box.run(apply=True, quarantine_s=DAY)["purged_entries"] == 1


def test_purge_keeps_an_entry_held_again(box, monkeypatch, tmp_path):
    box.tree()
    box.run(apply=True)
    held = only(box.entries())
    monkeypatch.setattr(sweep, "process_snapshot", lambda *a, **kw: (REAL_PROCESS_SNAPSHOT()[0], True))
    child = subprocess.Popen(
        [sys.executable, "-c", HOLDER, str(held.location / "deep")], stdout=subprocess.PIPE, cwd=tmp_path
    )
    try:
        assert child.stdout.readline() == b"ready\n"
        box.at(8)
        report = box.run(apply=True)
        row = next(r for r in report["rows"] if r.get("ledger_id") == held.ledger_id)
        assert (row["decision"], row["reason"]) == ("preserve", "purge_live_process")
        assert held.location.is_dir() and [r["event"] for r in box.records()] == ["quarantine", "quarantined"]
    finally:
        child.kill()
        child.wait()
    assert box.run(apply=True)["purged_entries"] == 1


@pytest.mark.parametrize("probe", ["task_reference", "task_inventory", "liveness"])
def test_purge_keeps_an_entry_on_any_unproven_predicate(box, monkeypatch, probe):
    entry = box.tree()
    box.run(apply=True)
    held = only(box.entries())
    if probe == "task_reference":
        (box.tasks / "impl-x.json").write_text(
            json.dumps({"task_id": "impl-x", "status": "running", "cwd": str(entry)})
        )
    elif probe == "task_inventory":
        (box.tasks / "impl-x.json").write_text("{torn")
    else:
        monkeypatch.setattr(sweep, "process_snapshot", lambda *a, **kw: ([], False))
    box.at(8)
    row = next(r for r in box.run(apply=True)["rows"] if r.get("ledger_id") == held.ledger_id)
    expected = {"task_reference": "purge_task_reference", "task_inventory": "purge_task_inventory_unknown"}
    assert row["reason"] == expected.get(probe, "purge_liveness_unknown") and held.location.is_dir()


def test_purge_keeps_an_entry_whose_contents_changed(box):
    box.tree()
    box.run(apply=True)
    held = only(box.entries())
    (held.location / "deep" / "payload").write_bytes(b"new bytes")
    box.at(8)
    row = next(r for r in box.run(apply=True)["rows"] if r.get("ledger_id") == held.ledger_id)
    assert (
        row["reason"] == "purge_manifest_changed" and (held.location / "deep" / "payload").read_bytes() == b"new bytes"
    )


def test_purge_keeps_an_entry_written_after_confirmation_with_an_identical_manifest(box, monkeypatch):
    """Same bytes, mtime put back: only the change time shows the write, so the real clock runs here."""
    monkeypatch.setattr(sweep, "time", time)
    entry = box.tree()
    os.utime(entry, (OLD, OLD))
    time.sleep(0.05)
    box.run(apply=True, scratch=sweep.ScratchPolicy(min_age_s=0.01, quiet_s=0.01))
    held = only(box.entries())
    payload = held.location / "deep" / "payload"
    time.sleep(0.05)  # past the coarse kernel clock tick, so the write's ctime is after the confirmation
    info = payload.stat()
    payload.write_bytes(payload.read_bytes())
    os.utime(payload, ns=(info.st_atime_ns, info.st_mtime_ns))
    assert sweep.verify_restored(held, held.location)["verified"] is True
    monkeypatch.setattr(sweep, "time", SimpleNamespace(time=lambda: time.time() + 8 * DAY))
    row = next(r for r in box.run(apply=True)["rows"] if r.get("ledger_id") == held.ledger_id)
    assert row["reason"] == "purge_recent_write" and payload.exists()


def _fail_reap(*_args, **_kwargs):
    raise OSError(errno.EIO, "injected before deletion")


def _partial_reap(path, **_kwargs):
    """Delete part of the tree, then fail, as an interrupted common reaper would."""
    (path / "deep" / "payload").unlink()
    (path / "link").unlink()
    raise OSError(errno.EIO, "injected mid-deletion")


def _interrupt_purge(box, monkeypatch, reaper):
    """Quarantine the fixture tree, then let a purge past the window fail inside ``reaper``."""
    box.tree()
    box.run(apply=True)
    held = only(box.entries())
    real = sweep.reap_attributed_temp
    monkeypatch.setattr(sweep, "reap_attributed_temp", reaper)
    box.at(8)
    report = box.run(apply=True)
    monkeypatch.setattr(sweep, "reap_attributed_temp", real)
    assert report["errors"] == 1 and box.entries()[held.ledger_id].state == "purging"
    return held


def test_purge_retry_after_failure_before_deletion_purges_an_untouched_tree(box, monkeypatch):
    held = _interrupt_purge(box, monkeypatch, _fail_reap)
    report = box.run(apply=True)
    events = [r["event"] for r in box.records() if r["ledger_id"] == held.ledger_id]
    assert report["purged_entries"] == 1 and report["errors"] == 0 and not held.location.exists()
    assert events[-4:] == ["purge", "purge_failed", "purge", "purged"]


@pytest.mark.parametrize("change", ["rewritten", "added"])
def test_purge_retry_after_failure_before_deletion_refuses_changed_contents(box, monkeypatch, capsys, change):
    held = _interrupt_purge(box, monkeypatch, _fail_reap)
    if change == "rewritten":
        (held.location / "deep" / "payload").write_bytes(b"modified payload")
    else:
        (held.location / "deep" / "newcomer").write_bytes(b"not in the manifest")
    report = box.run(apply=True)
    row = next(r for r in report["rows"] if r.get("ledger_id") == held.ledger_id)
    assert (row["decision"], row["reason"], report["errors"]) == ("preserve", "purge_kept_ambiguous", 1)
    assert [r["event"] for r in box.records()][-3:] == ["purge", "purge_failed", "purge_kept_ambiguous"]
    assert box.entries()[held.ledger_id].state == "purge_kept_ambiguous"
    # The refused entry can still go back to its path; the verification shows what differs.
    assert sweep.main(["restore", held.ledger_id]) == 1
    result = json.loads(capsys.readouterr().out)
    assert (result["restored"], result["verification"]) == (True, "mismatch")
    changed = held.original / "deep" / ("payload" if change == "rewritten" else "newcomer")
    assert changed.exists() and changed.relative_to(held.original).as_posix() in result["mismatches"]


@pytest.mark.parametrize("change", [None, "rewritten", "added"])
def test_purge_retry_after_partial_deletion_keeps_the_survivors(box, monkeypatch, capsys, change):
    """A deletion that stopped part-way changed the survivors' directories, so nothing left is deleted on a guess."""
    held = _interrupt_purge(box, monkeypatch, _partial_reap)
    assert not (held.location / "deep" / "payload").exists() and (held.location / "run.sh").exists()
    if change == "rewritten":
        (held.location / "run.sh").write_bytes(b"#!/bin/sh\necho changed\n")
    elif change == "added":
        (held.location / "deep" / "newcomer").write_bytes(b"not in the manifest")
    report = box.run(apply=True)
    row = next(r for r in report["rows"] if r.get("ledger_id") == held.ledger_id)
    assert (row["decision"], row["reason"], report["errors"]) == ("preserve", "purge_kept_ambiguous", 1)
    assert report["purged_entries"] == 0 and report["quarantine_kept_ambiguous_entries"] == 1
    events = [r["event"] for r in box.records() if r["ledger_id"] == held.ledger_id]
    assert events[-3:] == ["purge", "purge_failed", "purge_kept_ambiguous"]
    assert (held.location / "run.sh").exists() and (held.location / "deep").is_dir()
    # Later runs keep it, report it and count it, without another record, until a person disposes of it.
    box.at(30)
    later = box.run(apply=True)
    row = next(r for r in later["rows"] if r.get("ledger_id") == held.ledger_id)
    assert (row["reason"], later["errors"], later["quarantine_kept_ambiguous_entries"]) == (
        "purge_kept_ambiguous",
        1,
        1,
    )
    assert sweep.summarize(later)["by_reason"]["purge_kept_ambiguous"] == 1
    assert [r["event"] for r in box.records() if r["ledger_id"] == held.ledger_id] == events
    # Disposal: restore brings the survivors back, and the verification names what is missing or changed.
    assert sweep.main(["restore", held.ledger_id]) == 1
    result = json.loads(capsys.readouterr().out)
    assert (result["restored"], result["verification"]) == (True, "mismatch")
    assert "deep/payload" in result["mismatches"] and (held.original / "run.sh").exists()
    assert box.entries()[held.ledger_id].state == "restored"


def test_purge_kept_ambiguous_removed_by_hand_is_reconciled_missing(box, monkeypatch):
    held = _interrupt_purge(box, monkeypatch, _partial_reap)
    box.run(apply=True)
    assert box.entries()[held.ledger_id].state == "purge_kept_ambiguous"
    shutil.rmtree(held.location)
    report = box.run(apply=True)
    assert report["quarantine_kept_ambiguous_entries"] == 0 and report["errors"] == 0
    last = box.records()[-1]
    assert (last["ledger_id"], last["event"], last["outcome"]) == (held.ledger_id, "reconciled", "missing")


def test_purge_retry_keeps_a_directory_whose_xattr_changed_after_partial_deletion(box, monkeypatch):
    """The review probe: real clock, deletion stopped part-way, then a surviving directory's xattr is changed."""
    monkeypatch.setattr(sweep, "time", time)
    entry = box.tree()
    os.utime(entry, (OLD, OLD))
    time.sleep(0.05)
    box.run(apply=True, scratch=sweep.ScratchPolicy(min_age_s=0.01, quiet_s=0.01))
    held = only(box.entries())
    real_reap = sweep.reap_attributed_temp
    monkeypatch.setattr(sweep, "time", SimpleNamespace(time=lambda: time.time() + 8 * DAY))
    monkeypatch.setattr(sweep, "reap_attributed_temp", _partial_reap)
    box.run(apply=True)
    assert box.entries()[held.ledger_id].state == "purging"
    deep = held.location / "deep"
    time.sleep(0.05)  # past the coarse kernel clock tick
    os.setxattr(deep, "user.lu-probe", b"changed after confirmation")
    assert deep.stat().st_ctime > held.confirmed_at
    monkeypatch.setattr(sweep, "reap_attributed_temp", real_reap)
    report = box.run(apply=True)
    row = next(r for r in report["rows"] if r.get("ledger_id") == held.ledger_id)
    assert (row["reason"], report["purged_entries"], report["quarantine_kept_ambiguous_entries"]) == (
        "purge_kept_ambiguous",
        0,
        1,
    )
    assert deep.is_dir() and os.getxattr(deep, "user.lu-probe") == b"changed after confirmation"


def test_purge_retry_refuses_a_survivor_written_after_confirmation(box, monkeypatch):
    """Same bytes, mtime put back: only the change time shows the write, so the real clock runs here."""
    monkeypatch.setattr(sweep, "time", time)
    entry = box.tree()
    os.utime(entry, (OLD, OLD))
    time.sleep(0.05)
    box.run(apply=True, scratch=sweep.ScratchPolicy(min_age_s=0.01, quiet_s=0.01))
    held = only(box.entries())
    real_reap = sweep.reap_attributed_temp
    monkeypatch.setattr(sweep, "time", SimpleNamespace(time=lambda: time.time() + 8 * DAY))
    monkeypatch.setattr(sweep, "reap_attributed_temp", _fail_reap)
    box.run(apply=True)
    assert box.entries()[held.ledger_id].state == "purging"
    script = held.location / "run.sh"
    time.sleep(0.05)  # past the coarse kernel clock tick
    info = script.stat()
    script.write_bytes(script.read_bytes())
    os.utime(script, ns=(info.st_atime_ns, info.st_mtime_ns))
    monkeypatch.setattr(sweep, "reap_attributed_temp", real_reap)
    row = next(r for r in box.run(apply=True)["rows"] if r.get("ledger_id") == held.ledger_id)
    assert row["reason"] == "purge_kept_ambiguous" and script.exists()


@pytest.mark.parametrize("rewrite", [False, True])
def test_restore_of_unhashed_files_is_reported_unverified(box, capsys, rewrite):
    entry = box.tree()
    box.run(apply=True, digest_limit=4096)
    held = only(box.entries())
    assert held.intent["digest_skipped_files"] == 1
    payload = held.location / "deep" / "payload"
    if rewrite:
        # Same size, mtime put back: size and mtime cannot tell, so the result must not claim the bytes.
        info = payload.stat()
        payload.write_bytes(os.urandom(8192))
        os.utime(payload, ns=(info.st_atime_ns, info.st_mtime_ns))
    assert sweep.main(["restore", held.ledger_id]) == 3
    result = json.loads(capsys.readouterr().out)
    expected = {
        "restored": True,
        "verified": False,
        "verification": "unverified_digest_skipped",
        "mismatch_count": 0,
        "digest_unverified_count": 1,
        "digest_unverified": ["deep/payload"],
    }
    assert result | expected == result and (entry / "deep" / "payload").exists()
    record = box.records()[-1]
    del expected["restored"]
    assert record["event"] == "restored" and record | expected == record


def test_purge_accepts_unhashed_files_by_size_mtime_and_ctime(box):
    box.tree()
    box.run(apply=True, digest_limit=4096)
    held = only(box.entries())
    box.at(8)
    assert box.run(apply=True, digest_limit=4096)["purged_entries"] == 1 and not held.location.exists()


@pytest.fixture
def syncs(monkeypatch):
    """Every ``fsync`` target in call order, with ``rename`` and ``reap`` markers between them."""
    seen: list[str] = []
    real_fsync, real_rename, real_reap = os.fsync, sweep.rename_noreplace, sweep.reap_attributed_temp

    def fsync(fd):
        seen.append(os.readlink(f"/proc/self/fd/{fd}"))
        real_fsync(fd)

    def rename(*args):
        real_rename(*args)
        seen.append("rename")

    def reap(*args, **kwargs):
        real_reap(*args, **kwargs)
        seen.append("reap")

    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(sweep, "rename_noreplace", rename)
    monkeypatch.setattr(sweep, "reap_attributed_temp", reap)
    return seen


def state_chain(state: Path) -> list[str]:
    """The ledger directory, then every directory holding an entry this user may have created, bottom up."""
    chain = [state]
    while chain[-1] != chain[-1].parent and chain[-1].lstat().st_uid == os.getuid():
        if chain[-1].lstat().st_dev != chain[-1].parent.lstat().st_dev:
            break
        chain.append(chain[-1].parent)
    return [str(path) for path in chain]


def test_new_state_directories_are_synced_into_their_parents(tmp_path, syncs):
    state = tmp_path / "a" / "b" / "c"
    ledger_mod.Ledger(state).append({"event": "quarantine", "ledger_id": "x"})
    chain = state_chain(state)
    assert chain[:4] == [str(state), str(tmp_path / "a" / "b"), str(tmp_path / "a"), str(tmp_path)]
    assert syncs == [*chain, str(state / "ledger.jsonl"), str(state)]
    assert os.stat(state).st_mode & 0o777 == 0o700


def test_failed_ancestor_sync_is_rerun_before_the_next_record(tmp_path, syncs, monkeypatch):
    """A creation whose parent sync failed exists but may not be durable; the next ledger re-syncs it first."""
    state = tmp_path / "a" / "b" / "c"
    real_sync = ledger_mod.sync_directory

    def failing(directory):
        if directory == tmp_path / "a":
            raise ledger_mod.DurabilityError("directory sync failed: Input/output error")
        real_sync(directory)

    monkeypatch.setattr(ledger_mod, "sync_directory", failing)
    with pytest.raises(ledger_mod.DurabilityError):
        ledger_mod.Ledger(state).append({"event": "quarantine", "ledger_id": "x"})
    # "b" was created, but the sync that makes it durable in "a" failed.
    assert (tmp_path / "a" / "b").is_dir() and not (state / "ledger.jsonl").exists()
    monkeypatch.setattr(ledger_mod, "sync_directory", real_sync)
    syncs.clear()
    ledger_mod.Ledger(state).append({"event": "quarantine", "ledger_id": "x"})
    assert syncs == [*state_chain(state), str(state / "ledger.jsonl"), str(state)]
    assert str(tmp_path / "a") in syncs[: syncs.index(str(state / "ledger.jsonl"))]


def test_failed_ancestor_sync_is_rerun_before_reconciliation_records(box, syncs, monkeypatch, isolated_state_home):
    entry = box.tree()
    real_sync = ledger_mod.sync_directory

    def failing(directory):
        if directory == isolated_state_home:
            raise ledger_mod.DurabilityError("directory sync failed: Input/output error")
        real_sync(directory)

    monkeypatch.setattr(ledger_mod, "sync_directory", failing)
    with pytest.raises(ledger_mod.DurabilityError):
        box.run(apply=True)
    assert box.state.parent.is_dir() and entry.exists() and not (box.state / "ledger.jsonl").exists()
    monkeypatch.setattr(ledger_mod, "sync_directory", real_sync)
    syncs.clear()
    box.run(apply=True)
    chain = state_chain(box.state)
    assert chain[:3] == [str(box.state), str(box.state.parent), str(isolated_state_home)]
    assert syncs[: len(chain)] == chain and str(box.state / "ledger.jsonl") not in syncs[: len(chain)]


def test_quarantine_creation_and_renames_are_synced_before_they_are_recorded(
    box, syncs, isolated_state_home, monkeypatch
):
    box.tree()
    box.tree("second")
    real_problem = sweep.quarantined_problem
    monkeypatch.setattr(
        sweep,
        "quarantined_problem",
        lambda path, *a: "quarantine_write" if path.name == "second" else real_problem(path, *a),
    )
    box.run(apply=True)
    held = next(e for e in box.entries().values() if e.state == "quarantined")
    root, quarantine, ledger = str(box.root), str(held.location.parent), str(box.state / "ledger.jsonl")
    chain = state_chain(box.state)
    assert chain[1:3] == [str(isolated_state_home / "learn-ukrainian"), str(isolated_state_home)]
    assert syncs == [
        *chain,  # the ledger directory and the parents of the ones created
        root,  # quarantine directory created
        ledger,  # "quarantine" record (creates the ledger file)
        str(box.state),
        "rename",  # into quarantine
        root,
        quarantine,
        ledger,  # "quarantined"
        ledger,  # "quarantine" record of "second"
        "rename",
        root,
        quarantine,
        "rename",  # the re-check found something: back out
        quarantine,
        root,
        ledger,  # "returned"
    ]


def test_restore_and_purge_are_synced_before_they_are_recorded(box, syncs, capsys):
    box.tree()
    box.tree("second")
    box.run(apply=True)
    first, _second = sorted(box.entries().values(), key=lambda e: e.original.name)
    ledger, root, quarantine = str(box.state / "ledger.jsonl"), str(box.root), str(first.location.parent)
    chain = state_chain(box.state)
    syncs.clear()
    assert sweep.main(["restore", first.ledger_id]) == 0
    capsys.readouterr()
    assert syncs == [*chain, ledger, "rename", quarantine, root, ledger]
    syncs.clear()
    box.at(8)
    assert box.run(apply=True)["purged_entries"] == 1
    # The restored entry is a candidate again and is quarantined afresh after the purge.
    assert syncs[: len(chain) + 4] == [*chain, ledger, "reap", quarantine, ledger]


def test_interrupted_restore_is_resynced_before_reconciliation_confirms_it(box, syncs, monkeypatch, capsys):
    """The review probe: the restore's destination sync fails, so reconciliation must re-run both syncs first."""
    box.tree()
    box.run(apply=True)
    held = only(box.entries())
    ledger, root, quarantine = str(box.state / "ledger.jsonl"), str(box.root), str(held.location.parent)
    real_sync = sweep.sync_directory

    def failing(directory):
        if isinstance(directory, int) and os.readlink(f"/proc/self/fd/{directory}") == root:
            raise ledger_mod.DurabilityError("directory sync failed: Input/output error")
        real_sync(directory)

    monkeypatch.setattr(sweep, "sync_directory", failing)
    assert sweep.main(["restore", held.ledger_id]) == 1
    assert "not durable" in capsys.readouterr().err
    assert box.entries()[held.ledger_id].state == "restoring" and held.original.exists()
    monkeypatch.setattr(sweep, "sync_directory", real_sync)
    chain = state_chain(box.state)
    syncs.clear()
    box.run(apply=True)
    assert syncs[: len(chain) + 3] == [*chain, quarantine, root, ledger]
    restored = [r for r in box.records() if r["ledger_id"] == held.ledger_id][-1]
    assert (restored["event"], restored["reconciled"], restored["verified"]) == ("restored", True, True)


@pytest.mark.parametrize("step", ["quarantine", "purge"])
def test_interrupted_step_is_resynced_before_reconciliation_confirms_it(box, syncs, monkeypatch, step):
    """A quarantine rename or a purge whose sync failed: both directories are synced again before the record."""
    box.tree()
    real_sync = sweep.sync_directory
    if step == "purge":
        box.run(apply=True)
        box.at(8)

    def failing(directory):
        target = os.readlink(f"/proc/self/fd/{directory}") if isinstance(directory, int) else str(directory)
        if Path(target).name.startswith(sweep.QUARANTINE_PREFIX):
            raise ledger_mod.DurabilityError("directory sync failed: Input/output error")
        real_sync(directory)

    monkeypatch.setattr(sweep, "sync_directory", failing)
    with pytest.raises(ledger_mod.DurabilityError):
        box.run(apply=True)
    held = only(box.entries())
    assert held.state == ("pending" if step == "quarantine" else "purging")
    quarantine, root, ledger = str(held.location.parent), str(box.root), str(box.state / "ledger.jsonl")
    monkeypatch.setattr(sweep, "sync_directory", real_sync)
    chain = state_chain(box.state)
    syncs.clear()
    box.run(apply=True)
    expected = "returned" if step == "quarantine" else "purged"
    last = [r for r in box.records() if r["ledger_id"] == held.ledger_id][-1]
    assert (last["event"], last["outcome"]) == ("reconciled", expected)
    assert syncs[: len(chain) + 2] == [*chain, quarantine, root]


def test_failed_sync_after_rename_stops_the_run_unconfirmed(box, monkeypatch, capsys):
    entry = box.tree()
    real_sync = sweep.sync_directory

    def failing(directory):
        if isinstance(directory, int) and os.readlink(f"/proc/self/fd/{directory}").startswith(
            str(box.root / sweep.QUARANTINE_PREFIX)
        ):
            raise ledger_mod.DurabilityError("directory sync failed: Input/output error")
        real_sync(directory)

    monkeypatch.setattr(sweep, "sync_directory", failing)
    argv = ["--temp-root", str(box.root), "--task-root", str(box.tasks), "--unattributed-scratch", "--apply"]
    assert sweep.main(argv) == 1
    assert "run stopped" in capsys.readouterr().err
    assert only(box.entries()).state == "pending" and not entry.exists()
    pending = only(box.entries())
    monkeypatch.setattr(sweep, "sync_directory", real_sync)
    box.run(apply=True)
    last = [r for r in box.records() if r["ledger_id"] == pending.ledger_id][-1]
    assert (last["event"], last["outcome"]) == ("reconciled", "returned")


def test_ledger_is_append_only(box, capsys):
    box.tree()
    box.tree("second")
    path = box.state / "ledger.jsonl"
    box.run(apply=True)
    history = [path.read_bytes()]
    first, second = sorted(box.entries().values(), key=lambda e: e.original.name)
    assert sweep.main(["restore", first.ledger_id]) == 0
    capsys.readouterr()
    history.append(path.read_bytes())
    # A torn record from a crash is closed off, never merged with the next one or rewritten.
    with path.open("ab") as handle:
        handle.write(b'{"event":"quar')
    history.append(path.read_bytes())
    box.at(8)
    report = box.run(apply=True)
    history.append(path.read_bytes())
    assert report["ledger_malformed_lines"] == 1 and report["purged_entries"] == 1
    for earlier, later in itertools.pairwise(history):
        assert later.startswith(earlier) and len(later) > len(earlier)
    lines = history[-1].decode().splitlines()
    assert lines.count('{"event":"quar') == 1
    assert all(json.loads(line)["schema"] == ledger_mod.SCHEMA for line in lines if line != '{"event":"quar')
    assert box.entries()[second.ledger_id].state == "purged"
    assert os.stat(path).st_mode & 0o777 == 0o600


def test_ledger_survives_the_temp_root_being_cleaned(box, capsys):
    entry = box.tree()
    box.run(apply=True)
    held = only(box.entries())
    shutil.rmtree(box.root)
    box.root.mkdir()
    assert sweep.main(["quarantine", "--json"]) == 0
    [listed] = json.loads(capsys.readouterr().out)
    assert (listed["ledger_id"], listed["present"]) == (held.ledger_id, False)
    report = box.run(apply=True)
    assert next(r for r in report["rows"] if r.get("ledger_id") == held.ledger_id)["reason"] == "ledger_missing"
    assert sweep.main(["ledger", "--path", entry.name, "--json"]) == 0
    events = [(r["event"], r.get("outcome")) for r in json.loads(capsys.readouterr().out)]
    assert events == [("quarantine", None), ("quarantined", None), ("reconciled", "missing")]


def test_ledger_failure_moves_nothing(box, monkeypatch, capsys):
    entry = box.tree()

    def refuse(self, record):
        raise ledger_mod.LedgerError("ledger write failed: fixture")

    monkeypatch.setattr(ledger_mod.Ledger, "append", refuse)
    argv = ["--temp-root", str(box.root), "--task-root", str(box.tasks), "--unattributed-scratch", "--apply"]
    assert sweep.main(argv) == 1
    assert "run stopped" in capsys.readouterr().err
    assert entry.is_dir() and not any((q / entry.name).exists() for q in quarantines(box.root))


def test_state_dir_must_be_outside_temp_root_and_repository(box):
    with pytest.raises(ledger_mod.LedgerError):
        box.run(apply=True, state_dir=box.root / "ledger")
    with pytest.raises(ledger_mod.LedgerError):
        box.run(state_dir=box.tmp / "state")
    assert not (box.root / "ledger").exists()


def test_default_state_dir_follows_xdg(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert ledger_mod.default_state_dir() == tmp_path / "learn-ukrainian" / "tmp-sweep"
    monkeypatch.setenv("XDG_STATE_HOME", "relative/state")
    assert ledger_mod.default_state_dir() == Path.home() / ".local" / "state" / "learn-ukrainian" / "tmp-sweep"


def test_ledger_and_quarantine_listings(box, capsys):
    entry = box.tree()
    box.tree("other-scratch")
    report = box.run(apply=True)
    held = {e.original.name: e for e in box.entries().values()}
    assert sweep.main(["ledger", "--path", entry.name, "--json"]) == 0
    records = json.loads(capsys.readouterr().out)
    assert {r["ledger_id"] for r in records} == {held[entry.name].ledger_id} and "manifest" not in records[0]
    assert sweep.main(["ledger", "--ledger-id", held[entry.name].ledger_id, "--manifest", "--json"]) == 0
    assert "manifest" in json.loads(capsys.readouterr().out)[0]
    assert sweep.main(["ledger", "--run-id", report["run_id"], "--json"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 4
    assert sweep.main(["ledger", "--run-id", "another-run", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == []
    day = held[entry.name].intent["at"][:10]
    assert sweep.main(["ledger", "--since", day, "--until", day, "--json"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 4
    assert sweep.main(["ledger", "--until", day + "T00:00:00Z", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == []
    assert sweep.main(["ledger"]) == 0
    table = capsys.readouterr().out
    assert table.startswith("| at | event | ledger_id |") and table.count("quarantined") == 2
    assert sweep.main(["quarantine"]) == 0
    listing = capsys.readouterr().out
    assert held[entry.name].ledger_id in listing and "| quarantined |" in listing
    with pytest.raises(SystemExit) as exc:
        sweep.main(["ledger", "--since", "yesterday"])
    assert exc.value.code == 2


def test_dry_run_summary_reports_ledger_location_and_quarantine_counts(box, capsys):
    box.tree()
    box.run(apply=True)
    box.tree("newer-scratch")
    argv = ["--temp-root", str(box.root), "--task-root", str(box.tasks), "--unattributed-scratch", "--summary"]
    box.at(8)
    assert sweep.main(argv) == 0
    out = capsys.readouterr().out
    summary = json.loads(out)
    assert summary["ledger_path"].endswith("learn-ukrainian/tmp-sweep/ledger.jsonl")
    assert (summary["quarantine_held_entries"], summary["purgeable_entries"], summary["purged_entries"]) == (1, 1, 0)
    assert summary["by_decision"] == {"would_purge": 1, "would_reap": 1}
    assert "hand-made-scratch" not in out and "newer-scratch" not in out


def test_cli_help_documents_subcommands(capsys):
    for argv in (["--help"], ["ledger", "--help"], ["quarantine", "--help"], ["restore", "--help"]):
        with pytest.raises(SystemExit) as exc:
            sweep.main(argv)
        assert exc.value.code == 0
        text = capsys.readouterr().out
        assert "Example" in text and "Exit codes" in text and "Related:" in text and "Use " in text
