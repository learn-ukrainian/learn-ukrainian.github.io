"""Temp-dir proof for read-only snapshot digests and the batch_state sweep (#8783)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.maintenance.batch_state_retention import plan_retention
from scripts.orchestration import stale_task_records

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
