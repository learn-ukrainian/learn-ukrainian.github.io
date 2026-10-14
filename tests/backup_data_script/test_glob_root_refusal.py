"""A project or staging root that contains a find -path glob is refused.

On ddc51bb20d a root named project* backed up and restored with exit 0 while
the restored nested database had only the stale main-file row, and a root
named project[1] uploaded batch_state/tasks/run-home/held.md. Both now refuse
before restic writes a snapshot.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from tests.backup_data_script._restic_exclude_prune import path_is_excluded
from tests.backup_data_script._support import (
    _log,
    _make_database,
    _repository_snapshots,
    _run,
    _use_local_restic,
)

WAL_ONLY_ROW = "committed"


def _snapshot_files(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_symlink() or path.is_file()}


def _plant(scenario: str, project: Path) -> list[sqlite3.Connection]:
    connections: list[sqlite3.Connection] = []
    if scenario == "worker-home":
        database = _make_database(project / ".agent" / "worker-home" / "state.db", "main-file")
    elif scenario == "nested-home":
        database = _make_database(
            project / ".agent" / "batch_state" / "nested-home" / "state.db",
            "main-file",
        )
        database.with_name("note.json").write_text("keep the sibling\n", encoding="utf-8")
        secret = project / "batch_state" / "fleet-comms" / "scratch-home" / "secret.txt"
        secret.parent.mkdir(parents=True)
        secret.write_text("drop\n", encoding="utf-8")
    elif scenario == "ancestor-home":
        secret = project / "batch_state" / "real-home" / "secret.txt"
        secret.parent.mkdir(parents=True)
        secret.write_text("drop\n", encoding="utf-8")
        return connections
    else:
        raise AssertionError(scenario)
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA wal_autocheckpoint=0")
    connection.execute("INSERT INTO recovery_probe VALUES (?)", (WAL_ONLY_ROW,))
    connection.commit()
    assert database.with_name(f"{database.name}-wal").stat().st_size > 0
    connections.append(connection)
    return connections


def _assert_refused(result: object, label: str) -> None:
    assert result.returncode != 0, result.stderr
    assert f"Refusing to run: {label} contains a glob metacharacter" in result.stderr
    assert "find -path" in result.stderr


@pytest.mark.parametrize("backup_environment", ["project*"], indirect=True)
def test_star_root_refuses_before_upload(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    """The nested-home database that ddc51bb20d restored as ['main-file'] is not uploaded."""
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    database = _make_database(
        project / ".agent" / "batch_state" / "deeper" / "nested-home" / "state.db",
        "main-file",
    )
    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA wal_autocheckpoint=0")
        connection.execute("INSERT INTO recovery_probe VALUES (?)", (WAL_ONLY_ROW,))
        connection.commit()

        backed_up = _run(environment, "backup", "--execute")
    finally:
        connection.close()

    _assert_refused(backed_up, "project root")
    assert _repository_snapshots(environment) == []


@pytest.mark.parametrize("backup_environment", ["project[1]"], indirect=True)
def test_bracket_root_refuses_before_uploading_run_home(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    """held.md under batch_state/tasks/run-home is not uploaded when the root is project[1]."""
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    held = project / "batch_state" / "tasks" / "run-home" / "held.md"
    held.parent.mkdir(parents=True)
    held.write_text("excluded record\n", encoding="utf-8")
    kept = project / "batch_state" / "tasks" / "kept.md"
    kept.write_text("keep\n", encoding="utf-8")

    backed_up = _run(environment, "backup", "--execute")

    _assert_refused(backed_up, "project root")
    assert _repository_snapshots(environment) == []


@pytest.mark.parametrize("backup_environment", ["project?", "proj]ect"], indirect=True)
def test_question_and_bracket_close_roots_refuse(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment

    backed_up = _run(environment, "backup", "--execute")

    _assert_refused(backed_up, "project root")
    assert "arg=<backup>" not in _log(environment)


def test_staging_root_glob_refuses_before_upload(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    staging_root = tmp_path / "stage*"
    staging_root.mkdir()
    environment["LU_BACKUP_TMPDIR"] = str(staging_root)

    backed_up = _run(environment, "backup", "--execute")

    _assert_refused(backed_up, "staging root")
    assert "arg=<backup>" not in _log(environment)


@pytest.mark.parametrize(
    ("backup_environment", "scenario"),
    [
        ("project", "worker-home"),
        ("project", "nested-home"),
        ("batch_state/project-home/project", "ancestor-home"),
    ],
    indirect=["backup_environment"],
)
def test_fake_and_real_restic_select_the_same_files(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    scenario: str,
) -> None:
    """The three home-boundary regressions keep the same file set on both tools."""
    environment, source, _staging, _legacy = backup_environment
    project = source.parent
    connections = _plant(scenario, project)
    try:
        fake_backup = _run(environment, "backup", "--execute")
        assert fake_backup.returncode == 0, fake_backup.stderr
        fake_files = _snapshot_files(Path(environment["FAKE_SNAPSHOT_DIR"]))

        _use_local_restic(environment, tmp_path)
        real_backup = _run(environment, "backup", "--execute")
        assert real_backup.returncode == 0, real_backup.stderr
        target = tmp_path / "real-restored"
        restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")
        assert restored.returncode == 0, restored.stderr
    finally:
        for connection in connections:
            connection.close()

    real_files = _snapshot_files(target)
    assert fake_files == real_files, (
        f"only fake={sorted(fake_files - real_files)} only real={sorted(real_files - fake_files)}"
    )
    if scenario == "worker-home":
        assert ".agent/worker-home/state.db" in fake_files
        assert not any(path.endswith("state.db-wal") for path in fake_files)
    elif scenario == "nested-home":
        assert ".agent/batch_state/nested-home/note.json" in fake_files
        assert ".agent/batch_state/nested-home/state.db" in fake_files
        assert not any("scratch-home" in path for path in fake_files)
    else:
        assert "batch_state/fleet-comms/state.txt" in fake_files
        assert not any("real-home" in path for path in fake_files)


def test_exclude_patterns_match_restic_home_boundaries() -> None:
    """Anchored patterns keep a nested home and drop only this project's batch_state home."""
    root = "/work/project"
    patterns = [
        f"{root}/batch_state/**/*-home",
        f"{root}/batch_state/**/*-home/**",
        f"{root}/batch_state/review-receipts/**/home",
        f"{root}/batch_state/review-receipts/**/home/**",
    ]
    assert not path_is_excluded(patterns, f"{root}/.agent/worker-home/state.db")
    assert not path_is_excluded(patterns, f"{root}/.agent/batch_state/nested-home/state.db")
    assert path_is_excluded(patterns, f"{root}/batch_state/fleet-comms/scratch-home/secret.txt")
    assert path_is_excluded(patterns, f"{root}/batch_state/real-home/secret.txt")
    escaped = root + "[1]"
    literal = escaped.replace("[", "\\[").replace("]", "\\]")
    bracket_patterns = [f"{literal}/batch_state/**/*-home"]
    assert path_is_excluded(bracket_patterns, f"{escaped}/batch_state/tasks/run-home/held.md")
    assert not path_is_excluded(bracket_patterns, f"{escaped}/.agent/batch_state/deeper/nested-home/state.db")
