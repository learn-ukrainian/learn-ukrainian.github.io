"""Temp-dir proof for read-only snapshot digests and the batch_state sweep (#8783)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts import delegate
from scripts.maintenance.batch_state_retention import DEFAULT_MIN_AGE_DAYS, plan_retention
from scripts.orchestration import stale_task_records
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
