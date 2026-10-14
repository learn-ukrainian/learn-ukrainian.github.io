"""An explicit SQLite file root restores from its consistent database batch.

Restic does not apply exclude patterns to a file named on the backup command,
so a classified database stays out of the base snapshot. A full restore of an
older run that already stored both copies uses the receipt-listed database.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path

from tests.backup_data_script._support import (
    _real_restic,
    _real_restic_complete_snapshot,
    _real_restic_snapshot,
    _repository_snapshots,
    _run,
    _use_local_restic,
)

WAL_ONLY_ROW = "committed"


def _commit_wal_only_row(database: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA wal_autocheckpoint=0")
    connection.execute("INSERT INTO recovery_probe VALUES (?)", (WAL_ONLY_ROW,))
    connection.commit()
    assert database.with_name(f"{database.name}-wal").stat().st_size > 0
    return connection


def _drop_sidecars(database: Path) -> None:
    for sidecar in database.parent.glob(f"{database.name}-*"):
        sidecar.unlink()


def _rows(database: Path) -> list[str]:
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        return [row[0] for row in connection.execute("SELECT value FROM recovery_probe ORDER BY value")]


def _snapshot_file_paths(environment: dict[str, str], snapshot_id: str) -> set[str]:
    listed = _real_restic(environment, "ls", "--json", snapshot_id)
    assert listed.returncode == 0, listed.stderr
    paths: set[str] = set()
    for line in listed.stdout.splitlines():
        if not line.startswith("{"):
            continue
        node = json.loads(line)
        if node.get("struct_type") != "node" or node.get("type") != "file":
            continue
        path = str(node["path"])
        paths.add(path[1:] if path.startswith("/") else path)
    return paths


def _base_snapshot_id(environment: dict[str, str]) -> str:
    return next(snapshot["id"] for snapshot in _repository_snapshots(environment) if "lu-part-base" in snapshot["tags"])


def test_explicit_file_root_backup_restores_the_wal_only_row(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    """A fresh run stores the allowlisted database only in its database batch."""
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    database = source / "sources.db"
    relative = database.relative_to(project).as_posix()
    connection = _commit_wal_only_row(database)
    try:
        main_only = tmp_path / "main-only.db"
        shutil.copy2(database, main_only)
        assert _rows(main_only) == ["sources"]

        backed_up = _run(environment, "backup", "--execute")

        assert backed_up.returncode == 0, backed_up.stderr
        assert relative not in _snapshot_file_paths(environment, _base_snapshot_id(environment))
        assert "batch_state/fleet-comms/state.txt" in _snapshot_file_paths(environment, _base_snapshot_id(environment))
        target = tmp_path / "restored-fresh"
        restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")
        assert restored.returncode == 0, restored.stderr
        restored_database = target / relative
        assert not restored_database.with_name(f"{restored_database.name}-wal").exists()
        assert _rows(restored_database) == ["committed", "sources"]
    finally:
        connection.close()


def test_colliding_existing_run_restores_the_receipt_database(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    """An older run that stored both copies restores the receipt-listed database."""
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    database = source / "sources.db"
    relative = database.relative_to(project).as_posix()
    connection = _commit_wal_only_row(database)
    try:
        stale_root = tmp_path / "stale-root"
        stale_database = stale_root / relative
        stale_database.parent.mkdir(parents=True)
        shutil.copy2(database, stale_database)
        (stale_database.parent / "notes.txt").write_text("base-file\n", encoding="utf-8")
        stale_probe = tmp_path / "stale-probe.db"
        shutil.copy2(stale_database, stale_probe)
        assert _rows(stale_probe) == ["sources"]

        batch = tmp_path / "consistent-batch"
        consistent = batch / relative
        consistent.parent.mkdir(parents=True)
        with sqlite3.connect(consistent) as destination:
            connection.backup(destination)
        consistent_probe = tmp_path / "consistent-probe.db"
        shutil.copy2(consistent, consistent_probe)
        assert _rows(consistent_probe) == ["committed", "sources"]
        _drop_sidecars(stale_database)
        _drop_sidecars(consistent)
        mode = f"{consistent.stat().st_mode & 0o777:03o}"

        base_id = _real_restic_snapshot(environment, "colliding", stale_root, "data", "--tag", "lu-part-base")
        database_id = _real_restic_snapshot(environment, "colliding", batch, "data", "--tag", "lu-part-db")
        assert relative in _snapshot_file_paths(environment, base_id)
        receipt = {
            "schema_version": 3,
            "linux_run": {
                "run_id": "colliding",
                "base_snapshot_id": base_id,
                "databases": [{"path": relative, "snapshot_id": database_id, "mode": mode}],
            },
        }
        _real_restic_complete_snapshot(environment, "colliding", project, receipt)
    finally:
        connection.close()

    target = tmp_path / "restored-colliding"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")

    assert restored.returncode == 0, restored.stderr
    assert (target / "data" / "notes.txt").read_text(encoding="utf-8") == "base-file\n"
    restored_database = target / relative
    assert not restored_database.with_name(f"{restored_database.name}-wal").exists()
    assert _rows(restored_database) == ["committed", "sources"]
