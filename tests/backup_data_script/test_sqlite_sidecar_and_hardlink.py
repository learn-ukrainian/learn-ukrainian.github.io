"""Stale restore sidecars and hard-linked SQLite aliases.

A base snapshot can hold an older -wal/-shm/-journal beside the main file.
The consistent batch is a single database that already contains the later
commit. Pairing that file with the older sidecars makes a normal reader
replay the stale WAL. A hard link is a second name for the same inode;
SQLite keeps sidecars beside the path it opened, so backing up the other
name stores the main file without those committed rows.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

from tests.backup_data_script._support import (
    _completed_run_ids,
    _real_restic_complete_snapshot,
    _real_restic_snapshot,
    _run,
    _use_local_restic,
)


def _rows(database: Path) -> list[str]:
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        return [row[0] for row in connection.execute("SELECT value FROM recovery_probe ORDER BY value")]


def _assert_no_sidecars(database: Path) -> None:
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = database.with_name(f"{database.name}{suffix}")
        assert not sidecar.exists(), sidecar


def _restore(environment: dict[str, str], target: Path, *arguments: str) -> Path:
    restored = _run(environment, "restore", "latest", "--to", str(target), *arguments, "--execute")
    assert restored.returncode == 0, restored.stderr
    return target


def test_stale_base_sidecars_do_not_hide_rows_on_full_or_directory_restore(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    """Full restore and --path data both leave the consistent rows visible."""
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    relative = "data/sources.db"
    live = tmp_path / "live-generation" / relative
    live.parent.mkdir(parents=True)
    connection = sqlite3.connect(live)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA wal_autocheckpoint=0")
        connection.execute("CREATE TABLE recovery_probe(value TEXT NOT NULL)")
        connection.execute("INSERT INTO recovery_probe VALUES ('old')")
        connection.commit()

        base_root = tmp_path / "base-generation"
        base_dir = base_root / "data"
        base_dir.mkdir(parents=True)
        for name in ("sources.db", "sources.db-wal", "sources.db-shm"):
            shutil.copy2(live.parent / name, base_dir / name)
        (base_dir / "sources.db-journal").write_bytes(b"stale-journal")
        (base_dir / "notes.txt").write_text("base-file\n", encoding="utf-8")

        connection.execute("INSERT INTO recovery_probe VALUES ('new')")
        connection.commit()
        batch_root = tmp_path / "batch-generation"
        consistent = batch_root / relative
        consistent.parent.mkdir(parents=True)
        subprocess.run(
            ["sqlite3", str(live), f".backup '{consistent}'"],
            check=True,
            timeout=30,
        )
        paired = tmp_path / "paired-proof"
        paired.mkdir()
        shutil.copy2(consistent, paired / "sources.db")
        shutil.copy2(base_dir / "sources.db-wal", paired / "sources.db-wal")
        shutil.copy2(base_dir / "sources.db-shm", paired / "sources.db-shm")
        assert _rows(paired / "sources.db") == ["old"]
        assert _rows(consistent) == ["new", "old"]

        mode = f"{consistent.stat().st_mode & 0o777:03o}"
        base_id = _real_restic_snapshot(environment, "sidecars", base_root, "data", "--tag", "lu-part-base")
        database_id = _real_restic_snapshot(environment, "sidecars", batch_root, "data", "--tag", "lu-part-db")
        receipt = {
            "schema_version": 3,
            "linux_run": {
                "run_id": "sidecars",
                "base_snapshot_id": base_id,
                "databases": [{"path": relative, "snapshot_id": database_id, "mode": mode}],
            },
        }
        _real_restic_complete_snapshot(environment, "sidecars", project, receipt)
    finally:
        connection.close()

    full = _restore(environment, tmp_path / "restored-full")
    scoped = _restore(environment, tmp_path / "restored-data", "--path", "data")
    for target in (full, scoped):
        assert (target / "data" / "notes.txt").read_text(encoding="utf-8") == "base-file\n"
        restored_database = target / relative
        _assert_no_sidecars(restored_database)
        assert _rows(restored_database) == ["new", "old"]


def _hardlinked_alias(project: Path, alias: Path, scratch: Path) -> sqlite3.Connection:
    """Open a WAL database outside the allowlist and link an allowlisted alias to it."""
    live = project / "data" / "backups" / "live.db"
    live.parent.mkdir(parents=True)
    connection = sqlite3.connect(live)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA wal_autocheckpoint=0")
    connection.execute("CREATE TABLE recovery_probe(value TEXT NOT NULL)")
    connection.execute("INSERT INTO recovery_probe VALUES ('checkpointed')")
    connection.commit()
    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    connection.execute("INSERT INTO recovery_probe VALUES ('committed')")
    connection.commit()
    assert (live.parent / "live.db-wal").stat().st_size > 0
    alias.parent.mkdir(parents=True, exist_ok=True)
    os.link(live, alias)
    assert alias.stat().st_ino == live.stat().st_ino
    assert alias.stat().st_nlink > 1
    main_only = scratch / "main-only.db"
    shutil.copy2(alias, main_only)
    assert _rows(main_only) == ["checkpointed"]
    assert _rows(live) == ["checkpointed", "committed"]
    return connection


def test_hardlinked_database_name_is_refused(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    """An allowlisted *.db hard link must not be published without its WAL."""
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    alias = project / "data" / "datasets" / "alias.db"
    connection = _hardlinked_alias(project, alias, tmp_path)
    try:
        backed_up = _run(environment, "backup", "--execute")
    finally:
        connection.close()

    assert backed_up.returncode != 0
    assert "Refusing hard-linked SQLite database data/datasets/alias.db" in backed_up.stderr
    assert _completed_run_ids(environment) == []


def test_hardlinked_non_database_name_is_refused(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    """A hard link without a database filename must not enter the base snapshot as raw bytes."""
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    alias = project / "data" / "datasets" / "alias.txt"
    connection = _hardlinked_alias(project, alias, tmp_path)
    try:
        backed_up = _run(environment, "backup", "--execute")
    finally:
        connection.close()

    assert backed_up.returncode != 0
    assert "Refusing hard-linked SQLite database data/datasets/alias.txt" in backed_up.stderr
    assert _completed_run_ids(environment) == []
