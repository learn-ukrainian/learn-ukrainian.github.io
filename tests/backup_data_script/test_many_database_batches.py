"""Database exclude files, archives, and batched uploads."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import time
from pathlib import Path

import pytest

from tests.backup_data_script._support import (
    REPO_ROOT,
    SCRIPT,
    _assert_restored,
    _backup_invocations,
    _base_backup_lines,
    _file_sha256,
    _log,
    _logical_sha256,
    _make_database,
    _many_database_fixture,
    _run,
    _uploaded_databases,
    _use_local_restic,
    _write_archive,
    _write_executable,
)


def test_database_excludes_go_through_an_exclude_file_not_argv(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    project = source.parent
    plain = _make_database(source / "plain.db")
    odd = _make_database(project / "batch_state" / "odd $HOME name.sqlite3")

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    log = _log(environment)
    base = _base_backup_lines(log)
    assert len(base) == 1
    assert "arg=<--exclude>" not in base[0]
    assert "arg=<--exclude-file>" in base[0]
    assert f"exclude=<{plain}>" in log
    assert f"exclude=<{plain}-wal>" in log
    # $ and spaces stay literal: restic expands $VAR and trims each line.
    literal_odd = str(odd).replace("$", "[$]").replace(" ", "[ ]")
    assert f"exclude=<{literal_odd}>" in log
    assert _uploaded_databases(log) == {"data/plain.db", "batch_state/odd $HOME name.sqlite3"}
    assert "SQLite databases backed up: 2 of 2 (pytest scratch skipped: 0, archived: 0)." in result.stdout
    # The private exclude file is removed with the run.
    exclude_files = re.findall(r"arg=<--exclude-file> arg=<([^>]*)>", log)
    assert exclude_files and not any(Path(path).exists() for path in exclude_files)


def test_preview_also_uses_the_exclude_file(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    database = _make_database(source / "plain.db")

    result = _run(environment, "backup")

    assert result.returncode == 0, result.stderr
    log = _log(environment)
    assert "arg=<--exclude>" not in log
    assert "arg=<--dry-run>" in log
    assert f"exclude=<{database}>" in log


def test_pytest_scratch_databases_are_skipped_and_excluded(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    project = source.parent
    keep = _make_database(project / "batch_state" / "tasks" / "write-ownership.sqlite3")
    scratch = [
        _make_database(project / "batch_state" / "proof" / "pytest-RC2" / "stores0" / "7" / "write-ownership.sqlite3"),
        _make_database(project / "batch_state" / "proof" / "pytest-of-user" / "pytest-3" / "t0" / "atlas.db"),
    ]
    # A name that merely mentions pytest is not a pytest base temp directory.
    lookalike = _make_database(project / "batch_state" / "pytest-results.sqlite3")

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    log = _log(environment)
    assert _uploaded_databases(log) == {
        str(keep.relative_to(project)),
        str(lookalike.relative_to(project)),
    }
    for database in scratch:
        assert f"exclude=<{database}>" in log
    assert "SQLite databases backed up: 2 of 2 (pytest scratch skipped: 2, archived: 0)." in result.stdout
    receipt = json.loads((Path(environment["FAKE_SNAPSHOT_DIR"]) / "BACKUP-RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["linux_run"]["databases_backed_up"] == 2
    assert receipt["linux_run"]["transient_databases_skipped"] == 2
    assert "2 pytest scratch SQLite databases skipped" in receipt["exclusions"]


def test_archived_databases_are_covered_by_the_archive(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    project = source.parent
    live = _make_database(source / "live.db")
    preserved = [
        _make_database(project / "batch_state" / "preserved" / "atlas-1" / "atlas.db"),
        _make_database(project / "batch_state" / "codex-atlas" / "s1" / "sources.db"),
    ]
    _write_archive(project, "atlas-preserved-dbs-20261007.tar.zst", preserved)
    environment["FAKE_REQUIRED_RELATIVE"] = "batch_state/backups/archives/atlas-preserved-dbs-20261007.tar.zst"

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    log = _log(environment)
    assert _uploaded_databases(log) == {str(live.relative_to(project))}
    for database in preserved:
        assert f"exclude=<{database}>" in log
        assert database.exists()  # never deleted
    assert "staged_required=<batch_state/backups/archives/atlas-preserved-dbs-20261007.tar.zst>" in log
    assert "SQLite databases backed up: 1 of 1 (pytest scratch skipped: 0, archived: 2)." in result.stdout
    receipt = json.loads((Path(environment["FAKE_SNAPSHOT_DIR"]) / "BACKUP-RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["linux_run"]["archived_databases"] == 2
    assert receipt["linux_run"]["database_archives"] == ["atlas-preserved-dbs-20261007.tar.zst"]
    assert "loose SQLite databases covered by archive atlas-preserved-dbs-20261007.tar.zst" in receipt["exclusions"]


def test_database_changed_after_archiving_is_backed_up_loose(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    project = source.parent
    unchanged = _make_database(project / "batch_state" / "preserved" / "a" / "atlas.db")
    changed = _make_database(project / "batch_state" / "preserved" / "b" / "atlas.db")
    _write_archive(project, "dbs-20261007.tar.zst", [unchanged, changed])
    _make_database(changed, "written after archiving")
    os.utime(changed, (time.time() + 5, time.time() + 5))

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert "changed since it was archived; backing up the live copy: batch_state/preserved/b/atlas.db" in result.stderr
    assert _uploaded_databases(_log(environment)) == {"batch_state/preserved/b/atlas.db"}


@pytest.mark.parametrize("problem", ["size-mismatch", "missing-archive"])
def test_unverifiable_archive_is_ignored_and_databases_are_backed_up(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    problem: str,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    project = source.parent
    database = _make_database(project / "batch_state" / "preserved" / "a" / "atlas.db")
    archive = _write_archive(
        project, "dbs-20261007.tar.zst", [database], archive_bytes=1 if problem == "size-mismatch" else None
    )
    if problem == "missing-archive":
        archive.unlink()

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert "WARNING: Ignoring SQLite archive" in result.stderr
    assert _uploaded_databases(_log(environment)) == {"batch_state/preserved/a/atlas.db"}


def test_many_databases_upload_in_one_snapshot_and_restore_hash_matched(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    database_hashes, file_hashes = _many_database_fixture(project)
    originals = {relative: _file_sha256(project / relative) for relative in database_hashes}

    backed_up = _run(environment, "backup", "--execute")

    assert backed_up.returncode == 0, backed_up.stderr
    # One repository run per part, not one per database: 34 databases, 4 uploads.
    assert _backup_invocations(environment) == [
        "backup lu-part-base",
        "backup lu-part-db",
        "backup lu-part-receipt",
        "backup lu-part-complete",
    ]
    assert Path(environment["TEST_PEAK_LOG"]).read_text(encoding="utf-8").splitlines() == ["34", "0", "0"]
    assert "SQLite databases backed up: 34 of 34 (pytest scratch skipped: 1, archived: 0)." in backed_up.stdout
    assert list(staging.iterdir()) == []
    assert {relative: _file_sha256(project / relative) for relative in database_hashes} == originals

    target = tmp_path / "restored"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")

    assert restored.returncode == 0, restored.stderr
    _assert_restored(target, database_hashes, file_hashes)
    assert (target / "data" / "atlas.db").stat().st_mode & 0o777 == 0o600
    receipt = json.loads((target / "BACKUP-RECEIPT.json").read_text(encoding="utf-8"))
    inventory = receipt["linux_run"]["databases"]
    assert sorted(entry["path"] for entry in inventory) == sorted(database_hashes)
    assert len({entry["snapshot_id"] for entry in inventory}) == 1
    assert receipt["linux_run"]["databases_backed_up"] == 34

    scoped_target = tmp_path / "restored-one"
    scoped = _run(
        environment,
        "restore",
        "latest",
        "--to",
        str(scoped_target),
        "--path",
        "batch_state/fixtures/run-07/corpus.db",
        "--execute",
    )
    assert scoped.returncode == 0, scoped.stderr
    assert [path.relative_to(scoped_target).as_posix() for path in scoped_target.rglob("*") if path.is_file()] == [
        "batch_state/fixtures/run-07/corpus.db"
    ]
    assert (
        _logical_sha256(scoped_target / "batch_state/fixtures/run-07/corpus.db")
        == database_hashes["batch_state/fixtures/run-07/corpus.db"]
    )


def test_batch_budget_splits_database_uploads(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    for index in range(4):
        _make_database(project / "batch_state" / "fixtures" / f"run-{index}" / "sources.db")
    size = (project / "batch_state" / "fixtures" / "run-0" / "sources.db").stat().st_size
    environment["LU_BACKUP_DB_BATCH_MAX_BYTES"] = str(2 * size)

    backed_up = _run(environment, "backup", "--execute")

    assert backed_up.returncode == 0, backed_up.stderr
    assert _backup_invocations(environment).count("backup lu-part-db") == 2
    assert Path(environment["TEST_PEAK_LOG"]).read_text(encoding="utf-8").splitlines() == ["2", "2", "0", "0"]


@pytest.mark.parametrize("budget", ["0", "-1", "1e9", "abc", "1000000000000000000000"])
def test_invalid_batch_budget_fails_before_any_upload(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    budget: str,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _make_database(source / "a.db")
    environment["LU_BACKUP_DB_BATCH_MAX_BYTES"] = budget

    result = _run(environment, "backup", "--execute")

    assert result.returncode != 0
    assert "LU_BACKUP_DB_BATCH_MAX_BYTES must be a positive whole number of bytes." in result.stderr
    assert "arg=<backup>" not in _log(environment)


def test_database_batch_upload_failure_fails_every_member_and_never_completes(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    project = source.parent
    databases = [_make_database(source / "a.db"), _make_database(project / "batch_state" / "fixtures" / "b.db")]
    before = {database: _file_sha256(database) for database in databases}
    environment["FAKE_DB_PHASE_EXIT"] = "1"

    result = _run(environment, "backup", "--execute")

    assert result.returncode != 0
    assert "Database data/a.db: restic upload failed" in result.stderr
    assert "Database batch_state/fixtures/b.db: restic upload failed" in result.stderr
    assert "SQLite databases backed up: 0 of 2" in result.stdout
    assert "arg=<lu-part-complete>" not in _log(environment)
    assert not (Path(environment["FAKE_SNAPSHOT_DIR"]) / "BACKUP-RECEIPT.json").exists()
    assert list(staging.iterdir()) == []
    assert {database: _file_sha256(database) for database in databases} == before


def test_receipt_inventory_larger_than_one_argument_is_recorded(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    project = source.parent
    deep = project / "batch_state" / "fixtures"
    stage = Path(environment["LU_BACKUP_TMPDIR"]) / f"learn-ukrainian-backup.{os.getuid()}.stage"
    # Long paths, kept under SQLite's 512-byte pathname limit for both the
    # source and its staged copy (made under db-incoming, then moved into
    # db-batch), make each inventory entry large so a few hundred databases
    # pass 128 KiB.
    staged = max(len(str(stage / "db-incoming")), len(str(stage / "db-batch")))
    remaining = 500 - max(len(str(project)), staged) - len("/batch_state/fixtures/000.db")
    while remaining > 1:
        component = min(remaining - 1, 200)
        deep = deep / ("d" * component)
        remaining -= component + 1
    entry_bytes = len(
        json.dumps({"path": f"{deep.relative_to(project)}/000.db", "snapshot_id": "a" * 64, "mode": "644"})
    )
    count = 131072 // entry_bytes + 20
    for index in range(count):
        _make_database(deep / f"{index:03d}.db")

    result = subprocess.run(
        ["/bin/bash", str(SCRIPT), "backup", "--execute"],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        timeout=110,
    )

    assert result.returncode == 0, result.stderr
    receipt = json.loads((Path(environment["FAKE_SNAPSHOT_DIR"]) / "BACKUP-RECEIPT.json").read_text(encoding="utf-8"))
    # The inventory exceeds the kernel's 128 KiB single-argument limit.
    assert len(json.dumps(receipt["linux_run"]["databases"])) > 131072
    assert receipt["linux_run"]["databases_backed_up"] == count
    assert _log(environment).count("arg=<lu-part-db>") == 1


def test_wal_backed_copies_are_charged_their_staged_size_against_the_batch_budget(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    budget = 1024 * 1024
    environment["LU_BACKUP_DB_BATCH_MAX_BYTES"] = str(budget)
    # Most of each WAL database lives in its open -wal file, so its main file
    # understates the online copy that joins the batch.
    connections = []
    try:
        for name in ("first.db", "second.db"):
            connection = sqlite3.connect(source / name)
            connections.append(connection)
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA wal_autocheckpoint=0")
            connection.execute("CREATE TABLE recovery_probe (value BLOB NOT NULL)")
            connection.execute("INSERT INTO recovery_probe VALUES (zeroblob(700000))")
            connection.commit()
            assert (source / name).stat().st_size < budget // 8
            assert (source / f"{name}-wal").stat().st_size > budget // 2
        # A database larger than the budget still uploads, alone. data/ is
        # walked before batch_state/, so it follows the WAL databases.
        large = sqlite3.connect(source.parent / "batch_state" / "large.db")
        try:
            large.execute("CREATE TABLE recovery_probe (value BLOB NOT NULL)")
            large.execute("INSERT INTO recovery_probe VALUES (zeroblob(1200000))")
            large.commit()
        finally:
            large.close()
        files = [source / name for name in ("first.db", "first.db-wal", "second.db", "second.db-wal")]
        files.append(source.parent / "batch_state" / "large.db")
        before = {path: _file_sha256(path) for path in files}

        result = _run(environment, "backup", "--execute")
        after = {path: _file_sha256(path) for path in files}
    finally:
        for connection in connections:
            connection.close()

    assert result.returncode == 0, result.stderr
    assert after == before
    batches = [tuple(map(int, batch.split())) for batch in re.findall(r"db_batch=<(\d+ \d+)>", _log(environment))]
    assert sorted(count for count, _bytes in batches) == [1, 1, 1], batches
    assert all(staged <= budget or count == 1 for count, staged in batches), batches
    assert _uploaded_databases(_log(environment)) == {"data/first.db", "data/second.db", "batch_state/large.db"}
    snapshot = Path(environment["FAKE_SNAPSHOT_DIR"])
    for relative, blob in (("data/first.db", 700000), ("data/second.db", 700000), ("batch_state/large.db", 1200000)):
        with sqlite3.connect(f"file:{snapshot / relative}?mode=ro", uri=True) as connection:
            assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert connection.execute("SELECT length(value) FROM recovery_probe").fetchall() == [(blob,)]
    assert list(staging.iterdir()) == []


def test_backup_fails_closed_when_required_repo_state_is_missing(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    atlas_epic = source.parent / ".claude" / "atlas-epic"
    (atlas_epic / "HANDOFF.md").unlink()
    atlas_epic.rmdir()

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "Required recovery path is missing: .claude/atlas-epic" in result.stderr
    assert "arg=<backup>" not in _log(environment)


def test_backup_fails_closed_when_agent_recovery_root_is_missing(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    agent_root = source.parent / ".agent"
    (agent_root / "recovery-state.json").unlink()
    agent_root.rmdir()

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "Required recovery path is missing: .agent" in result.stderr
    assert "arg=<backup>" not in _log(environment)


def test_backup_fails_closed_when_agent_recovery_root_is_a_symlink(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    agent_root = source.parent / ".agent"
    external_root = tmp_path / "external-agent"
    agent_root.rename(external_root)
    agent_root.symlink_to(external_root, target_is_directory=True)

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "Required recovery path must not be a symlink: .agent" in result.stderr
    assert "arg=<backup>" not in _log(environment)


def test_backup_fails_closed_for_uncovered_untracked_path(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    (source.parent / "sole-copy.txt").write_text("not declared\n", encoding="utf-8")

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "UNBACKED untracked Git path: sole-copy.txt" in result.stderr
    assert "outside Git and declared recovery roots" in result.stderr
    assert "arg=<backup>" not in _log(environment)


def test_refuses_legacy_mutable_backup_as_restic_repository(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    environment["LU_BACKUP_REPOSITORY"] = "rclone:testdrive:Projects/learn-ukrainian-data"

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "Refusing to initialize or write restic inside the legacy" in result.stderr
    assert "arg=<backup>" not in _log(environment)


def test_data_root_must_not_be_a_symlink(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    external_data = tmp_path / "external-data"
    external_data.mkdir()
    source.rmdir()
    source.symlink_to(external_data)

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "Backup source must not be a symlink: data" in result.stderr
    assert "arg=<backup>" not in _log(environment)


def test_claude_parent_must_not_be_a_symlink(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    claude_directory = source.parent / ".claude"
    external_claude = tmp_path / "external-claude"
    claude_directory.rename(external_claude)
    claude_directory.symlink_to(external_claude, target_is_directory=True)

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "Recovery parent must not be a symlink: .claude" in result.stderr
    assert "arg=<backup>" not in _log(environment)


def test_doctor_summarizes_validation_failure(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    atlas_epic = source.parent / ".claude" / "atlas-epic"
    (atlas_epic / "HANDOFF.md").unlink()
    atlas_epic.rmdir()

    result = _run(environment, "doctor")

    assert result.returncode != 0
    assert "NOT READY: ERROR: Required recovery path is missing" in result.stderr
    assert "Doctor found 1 blocking problem(s)." in result.stderr


def test_refuses_staging_inside_script_checkout(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    environment["LU_BACKUP_TMPDIR"] = str(REPO_ROOT / "scripts")

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "Staging directory must be outside the project checkout" in result.stderr


def test_refuses_staging_inside_selected_project_checkout(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    environment["LU_BACKUP_TMPDIR"] = str(source.parent / "batch_state")

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "Staging directory must be outside the selected project checkout" in result.stderr


def test_data_volume_staging_location_requires_linux(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    data_staging = source / ".backup-staging"
    data_staging.mkdir()
    environment["LU_BACKUP_TMPDIR"] = str(data_staging)
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    _write_executable(fake_bin / "uname", "#!/bin/bash\nprintf '%s\\n' Darwin\n")

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "Staging directory and backup source overlap" in result.stderr


def test_refuses_non_designated_staging_inside_selected_checkout(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    other_staging = source.parent / "scratch-staging"
    other_staging.mkdir()
    environment["LU_BACKUP_TMPDIR"] = str(other_staging)

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "Staging directory must be outside the selected project checkout" in result.stderr
