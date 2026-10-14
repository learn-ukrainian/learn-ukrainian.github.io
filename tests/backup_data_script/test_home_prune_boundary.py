"""Discovery prunes `*-home` directories only under batch_state.

The approved exclusion boundary is `**/batch_state/**/*-home`. A live SQLite
database under a `*-home` directory anywhere else is an allowlisted database:
discovery must classify it so its committed WAL rows reach the database batch.
"""

from __future__ import annotations

import sqlite3

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
