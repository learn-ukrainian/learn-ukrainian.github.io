"""Each restore step replaces only its own databases and leaves no stale sidecars.

A directory restore (--path data) applies one scoped step per database of a
shared lu-part-db snapshot, then the file-phase base snapshot. A step must not
delete a database an earlier step already restored, or the base snapshot puts
back its older copy (or nothing at all). The base snapshot can also hold an
older -wal/-shm/-journal beside a restored database; those must be gone after
every step, including when a later step fails.
"""

from __future__ import annotations

import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from tests.backup_data_script._support import (
    _real_restic_complete_snapshot,
    _real_restic_snapshot,
    _run,
    _use_local_restic,
    _write_executable,
)


def _rows(database: Path) -> list[str]:
    # closing(): a sqlite3 connection's own context manager commits but stays open.
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        return [row[0] for row in connection.execute("SELECT value FROM recovery_probe ORDER BY value")]


def _sidecars(database: Path) -> list[Path]:
    return [
        sidecar
        for suffix in ("-wal", "-shm", "-journal")
        if (sidecar := database.with_name(f"{database.name}{suffix}")).exists()
    ]


def _database_pair(source: Path) -> list[str]:
    # A bare data/... literal is a store path; derive it from the fixture root.
    project = source.parent
    return [(source / name).relative_to(project).as_posix() for name in ("first.db", "second.db")]


def _fail_after_restoring(environment: dict[str, str], snapshot_id: str) -> None:
    """Let restic write the named snapshot's files, then exit 70 as a failed restore."""
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    (fake_bin / "restic").rename(fake_bin / "restic-local")
    environment["TEST_FAIL_AFTER_RESTORE_OF"] = snapshot_id
    _write_executable(
        fake_bin / "restic",
        r"""#!/bin/bash
set -u
inner="${BASH_SOURCE[0]%/*}/restic-local"
if [[ "${1:-}" == restore && "${2:-}" == "$TEST_FAIL_AFTER_RESTORE_OF" ]]; then
  "$inner" "$@" || exit
  exit 70
fi
exec "$inner" "$@"
""",
    )


def _write_run(
    environment: dict[str, str],
    tmp_path: Path,
    relatives: list[str],
    *,
    base_databases: bool,
    base_sidecars: bool,
    shared_batch: bool,
) -> str:
    """Write a completed schema-3 run; return the base snapshot ID.

    Each database holds 'old' in the base snapshot and 'old' plus 'new' in its
    consistent lu-part-db copy.
    """
    live_root = tmp_path / "live-generation"
    base_root = tmp_path / "base-generation"
    batch_root = tmp_path / "batch-generation"
    (base_root / "data").mkdir(parents=True)
    (base_root / "data" / "notes.txt").write_text("base-file\n", encoding="utf-8")
    connections = []
    try:
        for relative in relatives:
            live = live_root / relative
            live.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(live)
            connections.append(connection)
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA wal_autocheckpoint=0")
            connection.execute("CREATE TABLE recovery_probe(value TEXT NOT NULL)")
            connection.execute("INSERT INTO recovery_probe VALUES ('old')")
            connection.commit()
            if base_databases:
                suffixes = ["", "-wal", "-shm"]
                if not base_sidecars:
                    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    suffixes = [""]
                for suffix in suffixes:
                    shutil.copy2(live.parent / f"{live.name}{suffix}", base_root / f"{relative}{suffix}")
                if base_sidecars:
                    (base_root / f"{relative}-journal").write_bytes(b"stale-journal")
            connection.execute("INSERT INTO recovery_probe VALUES ('new')")
            connection.commit()
            consistent = batch_root / relative
            consistent.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(consistent)) as copy:
                connection.backup(copy)
            assert _rows(consistent) == ["new", "old"]
            if base_sidecars:
                # Paired with the base sidecars, the consistent copy loses 'new'.
                paired = tmp_path / "paired-proof" / relative
                paired.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(consistent, paired)
                for suffix in ("-wal", "-shm"):
                    shutil.copy2(base_root / f"{relative}{suffix}", paired.with_name(f"{paired.name}{suffix}"))
                assert _rows(paired) == ["old"]
    finally:
        for connection in connections:
            connection.close()

    base_id = _real_restic_snapshot(environment, "steps", base_root, "data", "--tag", "lu-part-base")
    if shared_batch:
        shared_id = _real_restic_snapshot(environment, "steps", batch_root, "data", "--tag", "lu-part-db")
        database_ids = [shared_id] * len(relatives)
    else:
        database_ids = []
        for relative in relatives:
            single_root = tmp_path / f"single-{Path(relative).stem}"
            (single_root / relative).parent.mkdir(parents=True)
            shutil.copy2(batch_root / relative, single_root / relative)
            database_ids.append(
                _real_restic_snapshot(environment, "steps", single_root, relative, "--tag", "lu-part-db")
            )
    receipt = {
        "schema_version": 3,
        "linux_run": {
            "run_id": "steps",
            "base_snapshot_id": base_id,
            "databases": [
                {"path": relative, "snapshot_id": database_id, "mode": "644"}
                for relative, database_id in zip(relatives, database_ids, strict=True)
            ],
        },
    }
    _real_restic_complete_snapshot(environment, "steps", tmp_path / "project", receipt)
    return base_id


@pytest.mark.parametrize("base_databases", [True, False], ids=["older-base", "database-free-base"])
def test_directory_restore_keeps_every_database_of_a_shared_batch(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    base_databases: bool,
) -> None:
    """A later scoped step must not delete the database an earlier step restored."""
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    relatives = _database_pair(source)
    _write_run(
        environment,
        tmp_path,
        relatives,
        base_databases=base_databases,
        base_sidecars=False,
        shared_batch=True,
    )

    target = tmp_path / "restored-data"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--path", "data", "--execute")

    assert restored.returncode == 0, restored.stderr
    assert (target / "data" / "notes.txt").read_text(encoding="utf-8") == "base-file\n"
    for relative in relatives:
        database = target / relative
        assert database.is_file(), relative
        assert _sidecars(database) == [], relative
        assert _rows(database) == ["new", "old"], relative


def test_failed_later_step_leaves_no_stale_sidecars_beside_restored_databases(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    """A step that fails after writing base sidecars must not leave them beside restored databases."""
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    relatives = _database_pair(source)
    base_id = _write_run(
        environment,
        tmp_path,
        relatives,
        base_databases=True,
        base_sidecars=True,
        shared_batch=False,
    )
    # The database steps complete first; the base step writes its stale
    # sidecars and then fails.
    _fail_after_restoring(environment, base_id)

    target = tmp_path / "restored-data"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--path", "data", "--execute")

    assert restored.returncode == 70, restored.stderr
    assert (target / "data" / "notes.txt").read_text(encoding="utf-8") == "base-file\n"
    for relative in relatives:
        database = target / relative
        assert _sidecars(database) == [], relative
        assert _rows(database) == ["new", "old"], relative
