"""Temp-dir proof for read-only snapshot digests and the batch_state sweep (#8783)."""

from __future__ import annotations

import contextlib
import errno
import json
import os
import stat
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts import delegate
from scripts.maintenance.batch_state_retention import DEFAULT_MIN_AGE_DAYS, plan_retention
from scripts.orchestration import scheduled_worktree_cleanup, stale_task_records
from scripts.orchestration.scheduled_worktree_cleanup import batch_state_retention_reports

NOW = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)


def _batch(tmp_path: Path) -> Path:
    root = tmp_path / "batch_state"
    (root / "tasks").mkdir(parents=True)
    return root


def _write_record(tasks: Path, name: str, *, status: str, age_days: float, **fields: object) -> None:
    record = {
        "task_id": name,
        "status": status,
        "finished_at": (NOW - timedelta(days=age_days)).isoformat(),
        "read_only_mutation_paths": [],
        "read_only_checkout_snapshot_error": None,
        **fields,
    }
    (tasks / f"{name}.json").write_text(json.dumps(record), encoding="utf-8")


def _write_full_sidecars(tasks: Path, name: str, *, entries: int = 40) -> Path:
    snapshot_dir = tasks / f"{name}.snapshots"
    snapshot_dir.mkdir()
    payload = json.dumps({f"path-{index}.txt": " M" for index in range(entries)}, separators=(",", ":"))
    for phase in ("pre", "post"):
        (snapshot_dir / f"read_only_checkout_{phase}.json").write_text(payload, encoding="utf-8")
    return snapshot_dir


def _names(snapshot_dir: Path) -> set[str]:
    return {path.name for path in snapshot_dir.iterdir()}


def test_dry_run_changes_nothing_and_apply_shrinks_only_allowlisted_terminal_sidecars(tmp_path: Path) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    _write_record(tasks, "old-clean", status="done", age_days=10)
    clean = _write_full_sidecars(tasks, "old-clean")
    _write_record(
        tasks,
        "old-mutation",
        status="failed",
        age_days=10,
        read_only_mutation_paths=["tracked.txt"],
    )
    mutated = _write_full_sidecars(tasks, "old-mutation")
    _write_record(tasks, "still-running", status="running", age_days=30)
    running = _write_full_sidecars(tasks, "still-running")
    _write_record(tasks, "young-clean", status="done", age_days=1)
    young = _write_full_sidecars(tasks, "young-clean")
    other = root / "open-model-data"
    other.mkdir()
    (other / "blob.bin").write_bytes(b"x" * 128)
    stray = root / "stray.snapshots"
    stray.mkdir()
    (stray / "read_only_checkout_pre.json").write_text("{}", encoding="utf-8")

    before = {
        "clean": _names(clean),
        "mutated": _names(mutated),
        "running": _names(running),
        "young": _names(young),
        "other": (other / "blob.bin").read_bytes(),
        "stray": _names(stray),
    }
    dry = plan_retention(root, min_age_days=7, apply=False, now=NOW)

    assert dry["mode"] == "dry-run"
    assert _names(clean) == before["clean"]
    assert _names(mutated) == before["mutated"]
    assert (other / "blob.bin").read_bytes() == before["other"]
    by_name = {row["name"]: row for row in dry["subtrees"]}
    assert by_name["tasks"]["reclaimable_bytes"] > 0
    assert by_name["open-model-data"]["bytes"] == 128
    assert by_name["open-model-data"]["reclaimable_bytes"] == 0
    assert by_name["stray.snapshots"]["reclaimable_bytes"] == 0
    assert dry["totals"]["reclaimable_bytes"] == by_name["tasks"]["reclaimable_bytes"]
    assert [row["snapshot_dir"] for row in dry["selected"]] == ["tasks/old-clean.snapshots"]

    applied = plan_retention(root, min_age_days=7, apply=True, now=NOW)

    assert applied["selected"][0]["action"] == "digested"
    assert _names(clean) == {"digest.json"}
    digest = json.loads((clean / "digest.json").read_text(encoding="utf-8"))
    assert digest["pre"]["entries"] == 40
    assert len(digest["pre"]["sha256"]) == 64
    assert _names(mutated) == before["mutated"]
    assert _names(running) == before["running"]
    assert _names(young) == before["young"]
    assert _names(stray) == before["stray"]
    assert (other / "blob.bin").read_bytes() == before["other"]
    record = json.loads((tasks / "old-clean.json").read_text(encoding="utf-8"))
    assert record["read_only_snapshot_retention"] == "digest"
    assert "read_only_checkout_pre" not in record


def test_sweep_refuses_a_directory_that_is_not_batch_state(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="batch_state"):
        plan_retention(tmp_path, apply=True, now=NOW)


def test_archive_restore_of_a_digest_only_task(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    _write_record(tasks, "digested", status="done", age_days=20, read_only_snapshot_retention="digest")
    snapshot_dir = tasks / "digested.snapshots"
    snapshot_dir.mkdir()
    digest = {"pre": {"sha256": "ab" * 32, "entries": 3}, "post": {"sha256": "cd" * 32, "entries": 3}}
    (snapshot_dir / "digest.json").write_text(json.dumps(digest), encoding="utf-8")

    archived = stale_task_records.archive_terminal(tasks, min_age_days=14, apply=True, now=NOW)
    assert archived["records"][0]["action"] == "archived"
    assert not snapshot_dir.exists()
    stored = tasks / "archive" / "digested.snapshots" / "digest.json"
    assert json.loads(stored.read_text(encoding="utf-8")) == digest

    restored = stale_task_records.restore_archived(tasks, ["digested"], apply=True)
    assert restored["records"][0]["action"] == "restored"
    assert json.loads((snapshot_dir / "digest.json").read_text(encoding="utf-8")) == digest
    assert not (snapshot_dir / "read_only_checkout_pre.json").exists()


def test_default_age_reclaims_a_two_day_old_clean_dir(tmp_path: Path) -> None:
    assert DEFAULT_MIN_AGE_DAYS == 1.0
    root = _batch(tmp_path)
    tasks = root / "tasks"
    _write_record(tasks, "two-day", status="done", age_days=2, run_nonce="same")
    old = _write_full_sidecars(tasks, "two-day")
    _write_record(tasks, "hours-old", status="done", age_days=0.5, run_nonce="same")
    young = _write_full_sidecars(tasks, "hours-old")

    dry = plan_retention(root, apply=False, now=NOW)

    assert dry["min_age_days"] == 1.0
    assert [row["snapshot_dir"] for row in dry["selected"]] == ["tasks/two-day.snapshots"]
    applied = plan_retention(root, apply=True, now=NOW)
    assert applied["selected"][0]["action"] == "digested"
    assert _names(old) == {"digest.json"}
    assert _names(young) == {"read_only_checkout_pre.json", "read_only_checkout_post.json"}


def test_missing_clean_verdict_keys_are_kept(tmp_path: Path) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    finished = (NOW - timedelta(days=10)).isoformat()
    for name, extra in (
        ("no-keys", {}),
        ("no-error-key", {"read_only_mutation_paths": []}),
        ("no-mutation-key", {"read_only_checkout_snapshot_error": None}),
    ):
        (tasks / f"{name}.json").write_text(
            json.dumps({"task_id": name, "status": "done", "finished_at": finished, **extra}),
            encoding="utf-8",
        )
        _write_full_sidecars(tasks, name)

    report = plan_retention(root, min_age_days=0, apply=True, now=NOW)

    assert report["selected"] == []
    for name in ("no-keys", "no-error-key", "no-mutation-key"):
        assert _names(tasks / f"{name}.snapshots") == {
            "read_only_checkout_pre.json",
            "read_only_checkout_post.json",
        }
        record = json.loads((tasks / f"{name}.json").read_text(encoding="utf-8"))
        assert "read_only_snapshot_retention" not in record


def test_status_flip_between_check_and_act_leaves_sidecars_untouched(tmp_path: Path) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    _write_record(tasks, "reused", status="done", age_days=10, run_nonce="old-run")
    snapshot = _write_full_sidecars(tasks, "reused", entries=2)
    record_path = tasks / "reused.json"
    fresh = json.dumps({"fresh.txt": "??"}, separators=(",", ":"))

    def _redispatch() -> None:
        # Still a released, explicitly clean record, so age and verdict checks
        # would allow the rewrite. Only the status/nonce recheck must refuse.
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["status"] = "failed"
        record["run_nonce"] = "new-run"
        record_path.write_text(json.dumps(record), encoding="utf-8")
        (snapshot / "read_only_checkout_pre.json").write_text(fresh, encoding="utf-8")

    report = plan_retention(root, min_age_days=0, apply=True, now=NOW, on_before_lock=_redispatch)

    assert report["selected"] == []
    assert (snapshot / "read_only_checkout_pre.json").read_text(encoding="utf-8") == fresh
    assert (snapshot / "read_only_checkout_post.json").is_file()
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["status"] == "failed"
    assert record["run_nonce"] == "new-run"
    assert "read_only_snapshot_retention" not in record


def test_symlink_phase_file_is_refused(tmp_path: Path) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    _write_record(tasks, "linked", status="done", age_days=10, run_nonce="same")
    snapshot = _write_full_sidecars(tasks, "linked", entries=1)
    outside = tmp_path / "outside.json"
    outside.write_text('{"secret.txt": " M"}', encoding="utf-8")
    phase = snapshot / "read_only_checkout_pre.json"
    phase.unlink()
    phase.symlink_to(outside)
    outside_record = tmp_path / "outside-record.json"
    outside_record.write_text(
        json.dumps(
            {
                "task_id": "record-link",
                "status": "done",
                "finished_at": (NOW - timedelta(days=10)).isoformat(),
                "read_only_mutation_paths": [],
                "read_only_checkout_snapshot_error": None,
            }
        ),
        encoding="utf-8",
    )
    (tasks / "record-link.json").symlink_to(outside_record)
    _write_full_sidecars(tasks, "record-link", entries=1)

    report = plan_retention(root, min_age_days=0, apply=True, now=NOW)

    assert report["selected"] == []
    assert outside.read_text(encoding="utf-8") == '{"secret.txt": " M"}'
    assert phase.is_symlink()
    assert (snapshot / "read_only_checkout_post.json").is_file()
    assert "read_only_snapshot_retention" not in json.loads(outside_record.read_text(encoding="utf-8"))
    assert _names(tasks / "record-link.snapshots") == {
        "read_only_checkout_pre.json",
        "read_only_checkout_post.json",
    }


def _crash_case(tmp_path: Path, name: str) -> tuple[Path, Path]:
    root = tmp_path / name
    root.mkdir()
    batch = _batch(root)
    tasks = batch / "tasks"
    _write_record(tasks, "task", status="done", age_days=3, run_nonce="same")
    return batch, _write_full_sidecars(tasks, "task", entries=2)


def test_crash_between_digest_record_and_delete_stays_consistent(tmp_path: Path) -> None:
    digest_root, digest_dir = _crash_case(tmp_path, "after-digest")
    with pytest.raises(RuntimeError, match="crash after digest"):
        plan_retention(digest_root, min_age_days=0, apply=True, now=NOW, crash_after="digest")

    assert (digest_dir / "digest.json").is_file()
    assert (digest_dir / "read_only_checkout_pre.json").is_file()
    assert (digest_dir / "read_only_checkout_post.json").is_file()
    digest_record = json.loads((digest_dir.parent / "task.json").read_text(encoding="utf-8"))
    assert "read_only_snapshot_retention" not in digest_record

    record_root, record_dir = _crash_case(tmp_path, "after-record")
    with pytest.raises(RuntimeError, match="crash after record"):
        plan_retention(record_root, min_age_days=0, apply=True, now=NOW, crash_after="record")

    stored = json.loads((record_dir / "digest.json").read_text(encoding="utf-8"))
    assert stored["pre"]["entries"] == 2
    assert (record_dir / "read_only_checkout_pre.json").is_file()
    assert (record_dir / "read_only_checkout_post.json").is_file()
    record = json.loads((record_dir.parent / "task.json").read_text(encoding="utf-8"))
    assert record["read_only_snapshot_retention"] == "digest"


def test_stage_digest_keeps_phase_files_until_discard(tmp_path: Path) -> None:
    snapshot = _write_full_sidecars(tmp_path, "worker", entries=1)
    pre = {"a.txt": " M"}
    post = {"a.txt": " M"}
    delegate.stage_read_only_snapshot_digest(snapshot, pre, post)
    assert (snapshot / "digest.json").is_file()
    assert (snapshot / "read_only_checkout_pre.json").is_file()
    assert (snapshot / "read_only_checkout_post.json").is_file()
    delegate.discard_read_only_snapshot_phases(snapshot)
    assert _names(snapshot) == {"digest.json"}


def test_hygiene_cadence_dry_run_then_apply_keeps_the_allowlist(tmp_path: Path) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    finished = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    (tasks / "old-clean.json").write_text(
        json.dumps(
            {
                "task_id": "old-clean",
                "status": "done",
                "finished_at": finished,
                "run_nonce": "same",
                "read_only_mutation_paths": [],
                "read_only_checkout_snapshot_error": None,
            }
        ),
        encoding="utf-8",
    )
    snapshot = _write_full_sidecars(tasks, "old-clean", entries=1)
    other = root / "open-model-data"
    other.mkdir()
    (other / "blob.bin").write_bytes(b"keep")

    dry = batch_state_retention_reports([tmp_path], apply=False)
    assert dry[0]["dry_run"]["mode"] == "dry-run"
    assert "apply" not in dry[0]
    assert _names(snapshot) == {"read_only_checkout_pre.json", "read_only_checkout_post.json"}
    assert dry[0]["dry_run"]["allowlist"] == ["tasks/*.snapshots", "tasks/archive/*.snapshots"]

    applied = batch_state_retention_reports([tmp_path], apply=True)
    assert applied[0]["apply"]["selected"][0]["action"] == "digested"
    assert _names(snapshot) == {"digest.json"}
    assert (other / "blob.bin").read_bytes() == b"keep"


def test_archive_between_digest_and_record_does_not_recreate_the_hot_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    _write_record(tasks, "moving", status="done", age_days=20, run_nonce="same")
    snapshot = _write_full_sidecars(tasks, "moving", entries=2)
    record_path = tasks / "moving.json"

    def _archive_midway() -> None:
        # The sweep already holds the checkout lock. Archive takes that same
        # lock; this call drops it so the move lands between the digest write
        # and the record write, which is the interleaving under test.
        monkeypatch.setattr(delegate, "worktree_lock", lambda *_args, **_kwargs: contextlib.nullcontext())
        stale_task_records.archive_terminal(tasks, min_age_days=0, apply=True, now=NOW)

    report = plan_retention(root, min_age_days=0, apply=True, now=NOW, on_after_digest=_archive_midway)

    assert not record_path.exists()
    assert report["selected"] == []
    assert not snapshot.exists()
    archived = json.loads((tasks / "archive" / "moving.json").read_text(encoding="utf-8"))
    assert "read_only_snapshot_retention" not in archived
    assert (tasks / "archive" / "moving.snapshots").is_dir()


def test_parent_swap_to_symlink_between_check_and_open_touches_nothing_outside(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    _write_record(tasks, "swap", status="done", age_days=10, run_nonce="same")
    _write_full_sidecars(tasks, "swap", entries=1)
    outside = tmp_path / "outside"
    outside_snap = outside / "swap.snapshots"
    outside_snap.mkdir(parents=True)
    payload = json.dumps({"stolen.txt": " M"}, separators=(",", ":"))
    for phase in ("pre", "post"):
        (outside_snap / f"read_only_checkout_{phase}.json").write_text(payload, encoding="utf-8")
    (outside_snap / "digest.json").write_text("OUTSIDE-DIGEST", encoding="utf-8")
    (outside / "swap.json").write_text((tasks / "swap.json").read_text(encoding="utf-8"), encoding="utf-8")
    (outside / "untouched.txt").write_bytes(b"leave-me")
    before = {path.relative_to(outside).as_posix(): path.read_bytes() for path in outside.rglob("*") if path.is_file()}
    swapped = False
    real_open = os.open

    def _swap() -> None:
        saved = tmp_path / "tasks.real"
        os.rename(tasks, saved)
        tasks.symlink_to(outside, target_is_directory=True)

    def _wrapped_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        target = Path(path)
        if dir_fd is None and not swapped and target != root and root in target.parents:
            swapped = True
            _swap()
        fd = real_open(path, flags, mode) if dir_fd is None else real_open(path, flags, mode, dir_fd=dir_fd)
        if dir_fd is None and not swapped and target == root:
            swapped = True
            _swap()
        return fd

    monkeypatch.setattr(os, "open", _wrapped_open)

    report = plan_retention(root, min_age_days=0, apply=True, now=NOW)

    assert report["selected"] == []
    after = {path.relative_to(outside).as_posix(): path.read_bytes() for path in outside.rglob("*") if path.is_file()}
    assert after == before


def test_help_is_two_lines_and_has_no_host_path() -> None:
    repo = Path(__file__).resolve().parents[2]
    proc = subprocess.run(
        [sys.executable, "scripts/maintenance/batch_state_retention.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
        cwd=repo,
    )
    text = proc.stdout
    collapsed = " ".join(text.split())
    assert "/home/" not in text
    assert "forensic value after a day" in collapsed
    assert "replace explicitly clean terminal snapshot sidecars with a digest." in collapsed
    assert "do not use it to delete any other batch_state subtree." in collapsed
    assert ".venv/bin/python scripts/maintenance/batch_state_retention.py" in text


def test_force_new_archive_after_digest_does_not_recreate_the_hot_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    _write_record(tasks, "moving", status="done", age_days=20, run_nonce="same")
    _write_full_sidecars(tasks, "moving", entries=2)
    monkeypatch.setattr(delegate, "_TASKS_DIR", tasks)
    locked: list[Path] = []

    @contextlib.contextmanager
    def _record_lock(path: Path):
        # The sweep already holds this lock. Drop it so the rename lands
        # between the digest write and the record write.
        locked.append(path)
        yield

    monkeypatch.setattr(delegate, "task_state_lock", _record_lock)

    def _archive_midway() -> None:
        delegate._archive_task_artifacts("moving", stamp="fixed")

    report = plan_retention(root, min_age_days=0, apply=True, now=NOW, on_after_digest=_archive_midway)

    assert locked == [tasks / "moving.json"]
    assert not (tasks / "moving.json").exists()
    assert not (tasks / "moving.snapshots").exists()
    assert report["selected"] == []
    archived = json.loads((tasks / "moving.fixed.archived.json").read_text(encoding="utf-8"))
    assert "read_only_snapshot_retention" not in archived
    assert (tasks / "moving.snapshots.fixed.archived" / "digest.json").is_file()


def test_restore_after_digest_does_not_recreate_the_archived_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    archive = tasks / "archive"
    archive.mkdir()
    _write_record(archive, "moving", status="done", age_days=20, run_nonce="same")
    _write_full_sidecars(archive, "moving", entries=2)
    locked: list[Path] = []

    @contextlib.contextmanager
    def _record_lock(path: Path):
        locked.append(path)
        yield

    monkeypatch.setattr(stale_task_records, "task_state_lock", _record_lock)

    def _restore_midway() -> None:
        stale_task_records.restore_archived(tasks, ["moving"], apply=True)

    report = plan_retention(root, min_age_days=0, apply=True, now=NOW, on_after_digest=_restore_midway)

    assert locked == [archive / "moving.json"]
    assert not (archive / "moving.json").exists()
    assert report["selected"] == []
    restored = json.loads((tasks / "moving.json").read_text(encoding="utf-8"))
    assert "read_only_snapshot_retention" not in restored


def test_stale_pid_temp_does_not_block_or_get_deleted(tmp_path: Path) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    _write_record(tasks, "old-clean", status="done", age_days=3, run_nonce="same")
    snapshot = _write_full_sidecars(tasks, "old-clean", entries=1)
    stale = snapshot / f".digest.json.tmp.{os.getpid()}"
    stale.write_text("killed-run", encoding="utf-8")

    report = plan_retention(root, min_age_days=0, apply=True, now=NOW)

    assert report["selected"][0]["action"] == "digested"
    assert (snapshot / "digest.json").is_file()
    assert stale.read_text(encoding="utf-8") == "killed-run"
    assert not list(snapshot.glob(".digest.json.*.tmp"))


def _hygiene_receipt(root: Path, receipt_dir: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.setattr(
        scheduled_worktree_cleanup,
        "build_receipt",
        lambda *_args, **_kwargs: {
            "schema_version": 2,
            "observed_at": "2026-09-25T12:00:00+00:00",
            "mode": "apply",
            "summary": {"errors": 0},
            "repositories": [],
        },
    )
    monkeypatch.setattr(scheduled_worktree_cleanup.home_session_retention_check, "build_report", lambda: {})
    monkeypatch.setattr(scheduled_worktree_cleanup.home_session_retention_check, "warning_lines", lambda _report: [])
    assert (
        scheduled_worktree_cleanup.main(["--repo-root", str(root.parent), "--apply", "--receipt-dir", str(receipt_dir)])
        == 0
    )
    receipts = list(receipt_dir.glob("*.json"))
    assert len(receipts) == 1
    return json.loads(receipts[0].read_text(encoding="utf-8"))


@pytest.mark.parametrize("code", [errno.ELOOP, errno.EACCES, errno.EEXIST, errno.ENOSPC])
def test_one_record_oserror_does_not_abort_the_sweep_or_the_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, code: int
) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    _write_record(tasks, "bad", status="done", age_days=3, run_nonce="same")
    bad = _write_full_sidecars(tasks, "bad", entries=1)
    _write_record(tasks, "good", status="done", age_days=3, run_nonce="same")
    good = _write_full_sidecars(tasks, "good", entries=1)
    real_open = os.open

    def _open(path, flags, mode=0o777, *, dir_fd=None):
        if path == "bad.json.lock":
            raise OSError(code, os.strerror(code))
        if dir_fd is None:
            return real_open(path, flags, mode)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", _open)
    receipt = _hygiene_receipt(root, tmp_path / "receipts", monkeypatch)

    applied = receipt["batch_state_retention"][0]["apply"]["selected"]
    by_dir = {row["snapshot_dir"]: row for row in applied}
    assert by_dir["tasks/bad.snapshots"]["action"] == "error"
    assert by_dir["tasks/bad.snapshots"]["error"] == errno.errorcode[code]
    assert by_dir["tasks/good.snapshots"]["action"] == "digested"
    assert _names(bad) == {"read_only_checkout_pre.json", "read_only_checkout_post.json"}
    assert _names(good) == {"digest.json"}
    public = scheduled_worktree_cleanup.build_public_summary(receipt)
    assert public["batch_state_retention"][0]["errors"] == {errno.errorcode[code]: 1}
    dumped = json.dumps(public["batch_state_retention"])
    assert "bad.snapshots" not in dumped
    assert "good.json" not in dumped


def test_public_summary_counts_apply_errors_by_errno_and_ignores_the_dry_run() -> None:
    receipt = {
        "batch_state_retention": [
            {
                "dry_run": {
                    "mode": "dry-run",
                    "allowlist": ["tasks/*.snapshots"],
                    "totals": {"reclaimable_bytes": 10},
                    "selected": [
                        {"action": "would_digest", "snapshot_dir": "tasks/a.snapshots"},
                        {"action": "error", "error": "EACCES", "snapshot_dir": "tasks/ignored.snapshots"},
                    ],
                },
                "apply": {
                    "mode": "apply",
                    "selected": [
                        {"action": "digested", "snapshot_dir": "tasks/ok.snapshots"},
                        {"action": "error", "error": "EACCES", "snapshot_dir": "tasks/a.snapshots"},
                        {"action": "error", "error": "ENOSPC", "snapshot_dir": "tasks/b.snapshots"},
                        {"action": "error", "error": "EACCES", "snapshot_dir": "tasks/c.snapshots"},
                    ],
                },
            }
        ]
    }
    public = scheduled_worktree_cleanup.build_public_summary(receipt)
    assert public["batch_state_retention"] == [
        {
            "mode": "apply",
            "reclaimable_bytes": 10,
            "selected": 2,
            "allowlist": ["tasks/*.snapshots"],
            "errors": {"EACCES": 2, "ENOSPC": 1},
        }
    ]
    dumped = json.dumps(public["batch_state_retention"])
    assert "ignored.snapshots" not in dumped
    assert "a.snapshots" not in dumped


def test_sweep_reaps_its_own_stale_temps_and_reports_them(tmp_path: Path) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    archive = tasks / "archive"
    archive.mkdir()
    _write_record(tasks, "old-clean", status="done", age_days=3, run_nonce="same")
    snapshot = _write_full_sidecars(tasks, "old-clean", entries=1)

    def _plant(directory: Path, name: str, pid: int, *, age_s: float) -> Path:
        path = directory / f".{name}.{pid}.{'ab' * 8}.tmp"
        path.write_text("killed", encoding="utf-8")
        stamp = (NOW - timedelta(seconds=age_s)).timestamp()
        os.utime(path, (stamp, stamp))
        return path

    stale_record = _plant(tasks, "old-clean.json", 4242, age_s=3700)
    stale_digest = _plant(snapshot, "digest.json", 4243, age_s=7200)
    stale_archive = _plant(archive, "moved.json", 4244, age_s=3700)
    young = _plant(snapshot, "digest.json", 7, age_s=600)
    young.write_text("live", encoding="utf-8")
    os.utime(young, ((NOW - timedelta(seconds=600)).timestamp(),) * 2)
    foreign = snapshot / f".digest.json.tmp.{os.getpid()}"
    foreign.write_text("other-writer", encoding="utf-8")
    os.utime(foreign, ((NOW - timedelta(hours=5)).timestamp(),) * 2)
    outside = tmp_path / "outside-secret"
    outside.write_text("secret", encoding="utf-8")
    linked = snapshot / f".digest.json.9.{'ef' * 8}.tmp"
    linked.symlink_to(outside)
    os.utime(linked, ((NOW - timedelta(hours=5)).timestamp(),) * 2, follow_symlinks=False)

    expected = [
        {"dir": "tasks", "name": stale_record.name},
        {"dir": "tasks/old-clean.snapshots", "name": stale_digest.name},
        {"dir": "tasks/archive", "name": stale_archive.name},
    ]
    dry = plan_retention(root, min_age_days=0, apply=False, now=NOW)

    assert stale_record.read_text(encoding="utf-8") == "killed"
    assert stale_digest.read_text(encoding="utf-8") == "killed"
    assert stale_archive.read_text(encoding="utf-8") == "killed"
    assert young.read_text(encoding="utf-8") == "live"
    assert foreign.read_text(encoding="utf-8") == "other-writer"
    assert linked.is_symlink()
    assert outside.read_text(encoding="utf-8") == "secret"
    assert dry["temps_would_remove"] == expected
    assert dry["temps_removed"] == []
    assert _names(snapshot) >= {"read_only_checkout_pre.json", "read_only_checkout_post.json"}

    applied = plan_retention(root, min_age_days=0, apply=True, now=NOW)

    assert not stale_record.exists()
    assert not stale_digest.exists()
    assert not stale_archive.exists()
    assert young.read_text(encoding="utf-8") == "live"
    assert foreign.read_text(encoding="utf-8") == "other-writer"
    assert linked.is_symlink()
    assert outside.read_text(encoding="utf-8") == "secret"
    assert applied["temps_removed"] == expected
    assert applied["temps_would_remove"] == []
    assert (snapshot / "digest.json").is_file()
    assert "read_only_checkout_pre.json" not in _names(snapshot)
    assert "read_only_checkout_post.json" not in _names(snapshot)


def _tree_fingerprint(root: Path) -> list[tuple[str, int, int, int]]:
    """Every path under ``root``, with size, mtime, and mode from ``lstat``."""
    rows: list[tuple[str, int, int, int]] = []

    def walk(directory: Path, rel: str) -> None:
        info = directory.lstat()
        rows.append((rel, info.st_size, info.st_mtime_ns, info.st_mode))
        for name in sorted(os.listdir(directory)):
            path = directory / name
            child = name if not rel else f"{rel}/{name}"
            st = path.lstat()
            if stat.S_ISDIR(st.st_mode) and not stat.S_ISLNK(st.st_mode):
                walk(path, child)
            else:
                rows.append((child, st.st_size, st.st_mtime_ns, st.st_mode))

    walk(root, "")
    return rows


def test_dry_run_leaves_the_whole_batch_state_tree_unchanged(tmp_path: Path) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    archive = tasks / "archive"
    archive.mkdir()
    _write_record(tasks, "old-clean", status="done", age_days=3, run_nonce="same")
    snapshot = _write_full_sidecars(tasks, "old-clean", entries=4)
    _write_record(archive, "moved", status="done", age_days=9, run_nonce="same")
    archived = _write_full_sidecars(archive, "moved", entries=2)
    other = root / "open-model-data"
    other.mkdir()
    (other / "blob.bin").write_bytes(b"x" * 64)
    stray = root / "stray.snapshots"
    stray.mkdir()
    (stray / "read_only_checkout_pre.json").write_text("{}", encoding="utf-8")

    def _plant(directory: Path, name: str, pid: int, *, age_s: float, body: str) -> None:
        path = directory / f".{name}.{pid}.{'ab' * 8}.tmp"
        path.write_text(body, encoding="utf-8")
        stamp = (NOW - timedelta(seconds=age_s)).timestamp()
        os.utime(path, (stamp, stamp))

    _plant(tasks, "old-clean.json", 4242, age_s=3700, body="killed")
    _plant(snapshot, "digest.json", 4243, age_s=7200, body="killed")
    _plant(archive, "moved.json", 4244, age_s=3700, body="killed")
    _plant(archived, "digest.json", 7, age_s=600, body="live")
    outside = tmp_path / "outside-secret"
    outside.write_text("secret", encoding="utf-8")
    linked = snapshot / f".digest.json.9.{'ef' * 8}.tmp"
    linked.symlink_to(outside)

    before = _tree_fingerprint(root)
    report = plan_retention(root, min_age_days=0, apply=False, now=NOW)

    assert report["mode"] == "dry-run"
    assert _tree_fingerprint(root) == before
    assert report["temps_removed"] == []
    assert report["temps_would_remove"]


def test_rewrite_preserves_the_record_mode(tmp_path: Path) -> None:
    root = _batch(tmp_path)
    tasks = root / "tasks"
    _write_record(tasks, "old-clean", status="done", age_days=3, run_nonce="same")
    record = tasks / "old-clean.json"
    record.chmod(0o640)
    snapshot = _write_full_sidecars(tasks, "old-clean", entries=1)

    report = plan_retention(root, min_age_days=0, apply=True, now=NOW)

    assert report["selected"][0]["action"] == "digested"
    assert stat.S_IMODE(record.stat().st_mode) == 0o640
    assert stat.S_IMODE((snapshot / "digest.json").stat().st_mode) == 0o600
