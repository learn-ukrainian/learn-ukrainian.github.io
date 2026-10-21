"""Ephemeral homes are excluded only under this project's own batch_state.

Discovery, classification, and restic excludes share that project-root
boundary. A `batch_state` directory nested under another allowlisted root, or
an ancestor of the project root, is not an ephemeral home.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from tests.backup_data_script._support import _make_database, _run, _use_local_restic

WAL_ONLY_ROW = "committed"


def test_live_database_under_non_batch_state_home_keeps_wal_rows(
    backup_environment,
    tmp_path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    database = _make_database(project / ".agent" / "worker-home" / "state.db", "main-file")
    relative = database.relative_to(project).as_posix()
    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA wal_autocheckpoint=0")
        connection.execute("INSERT INTO recovery_probe VALUES (?)", (WAL_ONLY_ROW,))
        connection.commit()
        assert database.with_name(f"{database.name}-wal").stat().st_size > 0

        backed_up = _run(environment, "backup", "--execute")
        assert backed_up.returncode == 0, backed_up.stderr

        target = tmp_path / "restored"
        restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")
        assert restored.returncode == 0, restored.stderr
    finally:
        connection.close()

    restored_database = target / relative
    assert not restored_database.with_name(f"{restored_database.name}-wal").exists()
    with sqlite3.connect(restored_database) as restored_connection:
        assert restored_connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        rows = [row[0] for row in restored_connection.execute("SELECT value FROM recovery_probe ORDER BY value")]
    assert rows == [WAL_ONLY_ROW, "main-file"]


@pytest.mark.parametrize("backup_environment", ["batch_state/project-home/project"], indirect=True)
def test_ancestor_batch_state_home_does_not_exclude_the_project(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    """An ancestor named `batch_state/<name>-home` is outside the project boundary."""
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    assert project.parts[-3:-1] == ("batch_state", "project-home")
    secret = project / "batch_state" / "real-home" / "secret.txt"
    secret.parent.mkdir(parents=True)
    secret.write_text("drop\n", encoding="utf-8")

    backed_up = _run(environment, "backup", "--execute")
    assert backed_up.returncode == 0, backed_up.stderr
    target = tmp_path / "restored"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")
    assert restored.returncode == 0, restored.stderr

    assert (target / ".agent" / "recovery-state.json").read_text(encoding="utf-8") == '{"schema_version": 1}\n'
    assert (target / ".claude" / "atlas-epic" / "HANDOFF.md").read_text(encoding="utf-8") == "recover me\n"
    assert (target / "batch_state" / "fleet-comms" / "state.txt").read_text(encoding="utf-8") == "recover me too\n"
    assert not (target / "batch_state" / "real-home").exists()
