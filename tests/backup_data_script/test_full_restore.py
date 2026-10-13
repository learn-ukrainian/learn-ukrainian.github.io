"""Restore dry-runs, space preflight, path restore, and historical receipt schemas."""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest

from tests.backup_data_script._support import (
    ATLAS_ID,
    BASE_ID,
    GIB,
    MANIFEST_ID,
    OTHER_ID,
    PRE_BATCHING_BASE_SHA,
    REPO_ROOT,
    _assert_restored,
    _backup_invocations,
    _fake_free_space,
    _log,
    _logical_sha256,
    _make_database,
    _many_database_fixture,
    _real_restic_base_snapshot,
    _real_restic_complete_snapshot,
    _real_restic_snapshot,
    _restore_ids,
    _restored_files,
    _run,
    _run_snapshots,
    _snapshot,
    _use_local_restic,
    _write_executable,
    _write_fake_run,
    _write_snapshots,
)


def test_restore_is_a_dry_run_and_refuses_unsafe_targets(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    restore_target = tmp_path / "restore-target"
    snapshot = Path(environment["FAKE_SNAPSHOT_DIR"])
    snapshot.mkdir()
    (snapshot / "BACKUP-RECEIPT.json").write_text('{"schema_version": 1}\n', encoding="utf-8")

    preview = _run(environment, "restore", "latest", "--to", str(restore_target))

    assert preview.returncode == 0, preview.stderr
    assert "Restore preview only" in preview.stdout
    assert "Restore size" in preview.stdout
    assert "arg=<restore>" in _log(environment)
    assert "arg=<--dry-run>" in _log(environment)
    assert "arg=<--overwrite> arg=<never>" in _log(environment)
    assert not restore_target.exists()

    restore_target.mkdir()
    (restore_target / "keep.txt").write_text("occupied\n", encoding="utf-8")
    Path(environment["FAKE_RESTIC_LOG"]).write_text("", encoding="utf-8")
    occupied = _run(environment, "restore", "latest", "--to", str(restore_target))

    assert occupied.returncode != 0
    assert "Restore target must be empty" in occupied.stderr
    assert "arg=<restore>" not in _log(environment)

    file_target = tmp_path / "not-a-directory"
    file_target.write_text("keep\n", encoding="utf-8")
    file_result = _run(environment, "restore", "latest", "--to", str(file_target))
    assert file_result.returncode != 0
    assert "is not a directory" in file_result.stderr

    symlink_target = tmp_path / "symlink-target"
    symlink_target.symlink_to(REPO_ROOT / "data")
    symlink_result = _run(
        environment,
        "restore",
        "latest",
        "--to",
        str(symlink_target),
    )
    assert symlink_result.returncode != 0
    assert "must not be a symlink" in symlink_result.stderr


def test_restore_latest_uses_parsed_time_with_mixed_offsets(
    backup_environment: tuple[dict[str, str], Path, Path, Path], tmp_path: Path
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    older_id = "a" * 64
    newer_id = "b" * 64
    snapshots = _snapshot(older_id, "older", ["complete"], "2026-09-26T04:00:00+02:00")
    snapshots += _snapshot(newer_id, "newer", ["complete"], "2026-09-26T03:00:00Z")
    _write_snapshots(environment, tmp_path, snapshots)
    snapshot_dir = Path(environment["FAKE_SNAPSHOT_DIR"])
    snapshot_dir.mkdir()
    (snapshot_dir / "BACKUP-RECEIPT.json").write_text('{"schema_version":1}\n', encoding="utf-8")

    result = _run(environment, "restore", "latest", "--to", str(tmp_path / "restore-target"))

    assert result.returncode == 0, result.stderr
    assert f"arg=<dump> arg=<{newer_id}>" in _log(environment)
    assert f"arg=<dump> arg=<{older_id}>" not in _log(environment)


def test_restore_refuses_filesystem_root_as_project_overlap(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment

    result = _run(environment, "restore", "latest", "--to", "/")

    assert result.returncode != 0
    assert "Restore target must be outside the project checkout" in result.stderr
    assert "arg=<restore>" not in _log(environment)


def test_restore_refuses_when_target_lacks_space_for_the_whole_run(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    _write_fake_run(environment)
    environment["FAKE_STATS_TOTAL_SIZE"] = str(10 * GIB)
    _fake_free_space(environment, 1 * GIB)
    target = tmp_path / "small-disk-restore"

    result = _run(environment, "restore", MANIFEST_ID, "--to", str(target), "--execute")

    assert result.returncode != 0
    assert "Insufficient free space" in result.stderr
    assert "need 11.0 GiB" in result.stderr
    assert "have 1.0 GiB" in result.stderr
    assert "testfs mounted at /scratch" in result.stderr
    assert "Nothing was restored" in result.stderr
    assert _restore_ids(environment) == []
    assert not target.exists()

    preview = _run(environment, "restore", MANIFEST_ID, "--to", str(target))
    assert preview.returncode != 0
    assert "Insufficient free space" in preview.stderr
    assert _restore_ids(environment) == []


def test_restore_measures_exactly_the_snapshots_it_restores(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    _write_fake_run(environment)
    _fake_free_space(environment, 50 * GIB)
    target = tmp_path / "big-disk-restore"

    result = _run(environment, "restore", MANIFEST_ID, "--to", str(target), "--execute")

    assert result.returncode == 0, result.stderr
    stats = [line for line in _log(environment).splitlines() if "arg=<stats>" in line]
    assert len(stats) == 1
    assert "arg=<--mode> arg=<restore-size>" in stats[0]
    for snapshot_id in (MANIFEST_ID, BASE_ID, ATLAS_ID, OTHER_ID):
        assert f"arg=<{snapshot_id}>" in stats[0]
    assert _restore_ids(environment) == [MANIFEST_ID, BASE_ID, ATLAS_ID, OTHER_ID]
    assert (target / "BACKUP-RECEIPT.json").is_file()
    assert (target / "data" / "atlas.db").is_file()
    assert (target / "data" / "other.db").is_file()


def test_restore_margin_is_configurable(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    _write_fake_run(environment)
    environment["FAKE_STATS_TOTAL_SIZE"] = str(GIB)
    _fake_free_space(environment, GIB + GIB // 20)
    target = tmp_path / "tight-restore"

    refused = _run(environment, "restore", MANIFEST_ID, "--to", str(target))
    assert refused.returncode != 0
    assert "10% margin" in refused.stderr

    environment["LU_BACKUP_RESTORE_MARGIN_PERCENT"] = "0"
    accepted = _run(environment, "restore", MANIFEST_ID, "--to", str(target))
    assert accepted.returncode == 0, accepted.stderr
    assert "Restore preview only" in accepted.stdout

    # Leading zeros are decimal, not octal: 010 is 10 % (not 8 %), 08 is 8 % (not an error).
    _fake_free_space(environment, GIB + GIB * 9 // 100)
    environment["LU_BACKUP_RESTORE_MARGIN_PERCENT"] = "010"
    ten = _run(environment, "restore", MANIFEST_ID, "--to", str(target))
    assert ten.returncode != 0
    assert "+ 10% margin" in ten.stderr
    environment["LU_BACKUP_RESTORE_MARGIN_PERCENT"] = "08"
    eight = _run(environment, "restore", MANIFEST_ID, "--to", str(target))
    assert eight.returncode == 0, eight.stderr
    assert "Restore preview only" in eight.stdout

    environment["LU_BACKUP_RESTORE_MARGIN_PERCENT"] = "ten"
    invalid = _run(environment, "restore", MANIFEST_ID, "--to", str(target))
    assert invalid.returncode != 0
    assert "LU_BACKUP_RESTORE_MARGIN_PERCENT" in invalid.stderr


def test_restore_accepts_schema_3_and_rejects_an_unknown_schema_before_writing(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    _write_fake_run(environment, schema_version=4)
    _fake_free_space(environment, 50 * GIB)
    target = tmp_path / "unknown-schema"

    for mode in ((), ("--execute",)):
        for scope in ((), ("--path", "data/atlas.db")):
            rejected = _run(environment, "restore", MANIFEST_ID, "--to", str(target), *scope, *mode)
            assert rejected.returncode != 0, (scope, mode)
            assert "Unsupported restored receipt schema." in rejected.stderr, (scope, mode)
            assert _restore_ids(environment) == [], (scope, mode)
            assert not target.exists(), (scope, mode)

    shutil.rmtree(Path(environment["FAKE_SNAPSHOT_DIR"]) / "by-id")
    _write_fake_run(environment, schema_version=3)
    accepted = _run(environment, "restore", MANIFEST_ID, "--to", str(target), "--execute")

    assert accepted.returncode == 0, accepted.stderr
    assert _restore_ids(environment) == [MANIFEST_ID, BASE_ID, ATLAS_ID, OTHER_ID]
    assert (target / "data" / "atlas.db").is_file()
    assert (target / "data" / "other.db").is_file()


def test_restore_path_restores_one_database_snapshot(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    _write_fake_run(environment)
    _fake_free_space(environment, 50 * GIB)
    target = tmp_path / "one-database"

    preview = _run(
        environment,
        "restore",
        MANIFEST_ID,
        "--to",
        str(target),
        "--path",
        "data/atlas.db",
    )
    assert preview.returncode == 0, preview.stderr
    assert "Restore preview only" in preview.stdout
    assert not target.exists()

    result = _run(
        environment,
        "restore",
        MANIFEST_ID,
        "--to",
        str(target),
        "--path",
        "data/atlas.db",
        "--execute",
    )

    assert result.returncode == 0, result.stderr
    stats = [line for line in _log(environment).splitlines() if "arg=<stats>" in line]
    assert stats
    assert all(f"arg=<{ATLAS_ID}>" in line for line in stats)
    assert all(f"arg=<{OTHER_ID}>" not in line and f"arg=<{BASE_ID}>" not in line for line in stats)
    assert _restore_ids(environment) == [ATLAS_ID, ATLAS_ID]
    assert (target / "data" / "atlas.db").stat().st_mode & 0o777 == 0o600
    assert not (target / "data" / "other.db").exists()
    assert not (target / "BACKUP-RECEIPT.json").exists()
    assert not (target / "data" / "notes.txt").exists()


def test_restore_path_gets_the_same_space_preflight_and_guards(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    _write_fake_run(environment)
    environment["FAKE_STATS_TOTAL_SIZE"] = str(2 * GIB)
    _fake_free_space(environment, GIB)
    target = tmp_path / "small-one-database"

    result = _run(
        environment,
        "restore",
        MANIFEST_ID,
        "--to",
        str(target),
        "--path",
        "data/atlas.db",
        "--execute",
    )
    assert result.returncode != 0
    assert "Insufficient free space" in result.stderr
    assert _restore_ids(environment) == []

    # Free space is ample from here on, so only the --path guard can refuse; and
    # --execute is set, so a bypass would restore for real (visible in the log).
    _fake_free_space(environment, 50 * GIB)
    for unsafe in ("/etc/passwd", "../data/atlas.db", "data/../x", "data/*.db", "", " ", "/"):
        for mode in ((), ("--execute",)):
            rejected = _run(
                environment,
                "restore",
                MANIFEST_ID,
                "--to",
                str(target),
                "--path",
                unsafe,
                *mode,
            )
            assert rejected.returncode != 0, (unsafe, mode)
            assert "--path" in rejected.stderr, (unsafe, mode)
            assert "Insufficient free space" not in rejected.stderr, (unsafe, mode)
            assert _restore_ids(environment) == [], (unsafe, mode)
            assert not target.exists(), (unsafe, mode)
    twice = _run(
        environment,
        "restore",
        MANIFEST_ID,
        "--to",
        str(target),
        "--path",
        "",
        "--path",
        "data/atlas.db",
        "--execute",
    )
    assert twice.returncode != 0
    assert "exactly one --path" in twice.stderr
    assert _restore_ids(environment) == []
    missing = _run(environment, "restore", MANIFEST_ID, "--to", str(target), "--path")
    assert missing.returncode != 0
    assert "--path requires" in missing.stderr


def test_restore_path_real_restic_restores_only_the_named_file(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    (source / "ordinary.txt").write_text("recover me\n", encoding="utf-8")
    (source / "other.txt").write_text("not this one\n", encoding="utf-8")
    with sqlite3.connect(source / "first.db") as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")
        connection.execute("INSERT INTO recovery_probe VALUES ('first')")
    with sqlite3.connect(source / "second.db") as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")
    backed_up = _run(environment, "backup", "--execute")
    assert backed_up.returncode == 0, backed_up.stderr

    database_target = tmp_path / "restored-database"
    database = _run(
        environment,
        "restore",
        "latest",
        "--to",
        str(database_target),
        "--path",
        "data/first.db",
        "--execute",
    )
    assert database.returncode == 0, database.stderr
    assert sorted(
        path.relative_to(database_target).as_posix() for path in database_target.rglob("*") if path.is_file()
    ) == ["data/first.db"]

    file_target = tmp_path / "restored-file"
    plain = _run(
        environment,
        "restore",
        "latest",
        "--to",
        str(file_target),
        "--path",
        "data/ordinary.txt",
        "--execute",
    )
    assert plain.returncode == 0, plain.stderr
    assert sorted(path.relative_to(file_target).as_posix() for path in file_target.rglob("*") if path.is_file()) == [
        "data/ordinary.txt"
    ]

    absent_target = tmp_path / "restored-absent"
    absent = _run(
        environment,
        "restore",
        "latest",
        "--to",
        str(absent_target),
        "--path",
        "data/no-such-file.txt",
        "--execute",
    )
    assert absent.returncode != 0
    assert "Nothing at --path" in absent.stderr
    assert not absent_target.exists()


def test_restore_of_historical_one_snapshot_per_database_run_is_hash_matched(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    # One restic process per database for both backup and restore, so a few
    # databases across every recovery root keep the run inside the timeout.
    database_hashes, file_hashes = _many_database_fixture(project, fixture_runs=3)

    # The layout every completed run used before batching: one stdin snapshot per database.
    base_id = _real_restic_base_snapshot(environment, "historical", project, list(database_hashes), tmp_path)
    inventory = []
    for relative in database_hashes:
        database_id = _real_restic_snapshot(
            environment,
            "historical",
            project,
            "--stdin",
            "--stdin-filename",
            relative,
            "--tag",
            "lu-part-db",
            stdin=(project / relative).read_bytes(),
        )
        inventory.append({"path": relative, "snapshot_id": database_id, "mode": "644"})
    receipt = {
        "schema_version": 2,
        "linux_run": {"run_id": "historical", "base_snapshot_id": base_id, "databases": inventory},
    }
    _real_restic_complete_snapshot(environment, "historical", project, receipt)

    target = tmp_path / "restored-historical"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")

    assert restored.returncode == 0, restored.stderr
    _assert_restored(target, database_hashes, file_hashes)

    scoped_target = tmp_path / "restored-historical-one"
    scoped = _run(environment, "restore", "latest", "--to", str(scoped_target), "--path", "data/atlas.db", "--execute")
    assert scoped.returncode == 0, scoped.stderr
    assert [path.relative_to(scoped_target).as_posix() for path in scoped_target.rglob("*") if path.is_file()] == [
        "data/atlas.db"
    ]
    assert _logical_sha256(scoped_target / "data" / "atlas.db") == database_hashes["data/atlas.db"]


def test_schema_2_run_with_a_shared_database_snapshot_restores_scoped_and_whole(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    database_hashes, file_hashes = _many_database_fixture(project)

    # The layout the batching build wrote under schema 2: every database in one
    # lu-part-db snapshot, uploaded from a private batch tree.
    base_id = _real_restic_base_snapshot(environment, "shared", project, list(database_hashes), tmp_path)
    batch = tmp_path / "db-batch"
    for relative in database_hashes:
        (batch / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project / relative, batch / relative)
    shared_id = _real_restic_snapshot(
        environment, "shared", batch, "data", "batch_state", ".agent", ".claude", "--force", "--tag", "lu-part-db"
    )
    receipt = {
        "schema_version": 2,
        "linux_run": {
            "run_id": "shared",
            "base_snapshot_id": base_id,
            "databases": [{"path": relative, "snapshot_id": shared_id, "mode": "644"} for relative in database_hashes],
        },
    }
    _real_restic_complete_snapshot(environment, "shared", project, receipt)

    scoped_target = tmp_path / "restored-shared-one"
    scoped = _run(environment, "restore", "latest", "--to", str(scoped_target), "--path", "data/atlas.db", "--execute")

    assert scoped.returncode == 0, scoped.stderr
    assert _restored_files(scoped_target) == ["data/atlas.db"]
    assert _logical_sha256(scoped_target / "data" / "atlas.db") == database_hashes["data/atlas.db"]

    target = tmp_path / "restored-shared"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")

    assert restored.returncode == 0, restored.stderr
    _assert_restored(target, database_hashes, file_hashes)


def test_pre_batching_script_refuses_a_schema_3_run_before_restoring(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    (source / "ordinary.txt").write_text("recover me\n", encoding="utf-8")
    _make_database(source / "first.db", "first")
    _make_database(source.parent / "batch_state" / "second.db", "second")
    backed_up = _run(environment, "backup", "--execute")
    assert backed_up.returncode == 0, backed_up.stderr

    old_script = tmp_path / "pre-batching-checkout" / "scripts" / "backup-data.sh"
    old_script.parent.mkdir(parents=True)
    old_script.write_bytes(
        subprocess.run(
            ["git", "-C", str(REPO_ROOT), "show", f"{PRE_BATCHING_BASE_SHA}:scripts/backup-data.sh"],
            check=True,
            capture_output=True,
            timeout=30,
        ).stdout
    )
    old_script.chmod(0o700)

    for name, scope in (("whole", ()), ("scoped", ("--path", "data/first.db"))):
        target = tmp_path / f"old-reader-{name}"
        refused = subprocess.run(
            ["/bin/bash", str(old_script), "restore", "latest", "--to", str(target), *scope, "--execute"],
            check=False,
            capture_output=True,
            env=environment,
            text=True,
            timeout=30,
        )
        assert refused.returncode != 0, name
        assert "Unsupported restored receipt schema" in refused.stderr, (name, refused.stderr)
        assert not target.exists() or _restored_files(target) == [], name

    # The current script restores the same run.
    current_target = tmp_path / "current-reader"
    restored = _run(environment, "restore", "latest", "--to", str(current_target), "--execute")
    assert restored.returncode == 0, restored.stderr
    assert {"data/first.db", "batch_state/second.db", "data/ordinary.txt"} <= set(_restored_files(current_target))


@pytest.mark.parametrize("schema_version", [2, 3])
def test_restore_plans_a_shared_database_snapshot_once_and_scopes_it_literally(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    schema_version: int,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    snapshot = Path(environment["FAKE_SNAPSHOT_DIR"])
    databases = ["data/atlas.db", "batch_state/odd name $HOME.db"]
    for relative in databases:
        _make_database(snapshot / "by-id" / ATLAS_ID / relative)
    (snapshot / "by-id" / BASE_ID / "data").mkdir(parents=True)
    receipt = {
        "schema_version": schema_version,
        "linux_run": {
            "run_id": "run-1",
            "base_snapshot_id": BASE_ID,
            "databases": [{"path": path, "snapshot_id": ATLAS_ID, "mode": "600"} for path in databases],
        },
    }
    (snapshot / "BACKUP-RECEIPT.json").write_text(json.dumps(receipt), encoding="utf-8")
    (snapshot / "by-id" / MANIFEST_ID).mkdir(parents=True)
    shutil.copy(snapshot / "BACKUP-RECEIPT.json", snapshot / "by-id" / MANIFEST_ID)
    _fake_free_space(environment, 50 * GIB)

    whole = _run(environment, "restore", MANIFEST_ID, "--to", str(tmp_path / "whole"), "--execute")

    assert whole.returncode == 0, whole.stderr
    assert _restore_ids(environment) == [MANIFEST_ID, BASE_ID, ATLAS_ID]
    for relative in databases:
        assert (tmp_path / "whole" / relative).stat().st_mode & 0o777 == 0o600

    Path(environment["FAKE_RESTIC_LOG"]).unlink()
    scoped = _run(
        environment,
        "restore",
        MANIFEST_ID,
        "--to",
        str(tmp_path / "scoped"),
        "--path",
        "batch_state/odd name $HOME.db",
        "--execute",
    )

    assert scoped.returncode == 0, scoped.stderr
    restores = [line for line in _log(environment).splitlines() if "arg=<restore>" in line]
    assert len(restores) == 1
    assert f"arg=<{ATLAS_ID}>" in restores[0]
    assert "arg=<--include> arg=</batch_state/odd[ ]name[ ][$]HOME.db>" in restores[0]
    listings = [line for line in _log(environment).splitlines() if "arg=<ls>" in line]
    assert listings
    assert all(f"arg=<{ATLAS_ID}> arg=</batch_state/odd name $HOME.db>" in line for line in listings)


def test_database_paths_with_glob_characters_restore_scoped_and_whole(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    literal = "data/w*e?i[r]d\\x.db"
    # What the literal path would match if it were read as a glob.
    lookalike = "data/wZZeQirdx.db"
    nested = "batch_state/run[1]/state*.sqlite3"
    databases = [literal, lookalike, nested]
    for index, relative in enumerate(databases):
        _make_database(project / relative, f"row-{index}")
    (source / "ordinary.txt").write_text("recover me\n", encoding="utf-8")
    database_hashes = {relative: _logical_sha256(project / relative) for relative in databases}

    backed_up = _run(environment, "backup", "--execute")

    assert backed_up.returncode == 0, backed_up.stderr
    assert _backup_invocations(environment).count("backup lu-part-db") == 1

    for relative in (literal, nested):
        scoped_target = tmp_path / f"scoped-{databases.index(relative)}"
        scoped = _run(environment, "restore", "latest", "--to", str(scoped_target), "--path", relative, "--execute")
        assert scoped.returncode == 0, scoped.stderr
        assert _restored_files(scoped_target) == [relative]
        assert _logical_sha256(scoped_target / relative) == database_hashes[relative]

    target = tmp_path / "whole"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")
    assert restored.returncode == 0, restored.stderr
    for relative, expected in database_hashes.items():
        assert _logical_sha256(target / relative) == expected, relative
    assert (target / "data" / "ordinary.txt").read_text(encoding="utf-8") == "recover me\n"

    # A wildcard that names no recorded database is still refused before any write.
    for wildcard in ("data/w*", "data/*.db", "batch_state/run[1]"):
        refused_target = tmp_path / "refused"
        refused = _run(environment, "restore", "latest", "--to", str(refused_target), "--path", wildcard, "--execute")
        assert refused.returncode != 0, wildcard
        assert "--path must be a literal path" in refused.stderr, (wildcard, refused.stderr)
        assert not refused_target.exists(), wildcard


def test_schema_1_snapshot_restores_hash_matched(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    # The single-snapshot layout (macOS, and Linux before runs): the receipt
    # sits at the root beside the recovery roots and there is no run tag.
    tree = tmp_path / "schema-1-tree"
    database_hash = _logical_sha256(_make_database(tree / "data" / "atlas.db", "atlas"))
    (tree / "data" / "ordinary.txt").write_text("recover me\n", encoding="utf-8")
    (tree / "BACKUP-RECEIPT.json").write_text('{"schema_version": 1}\n', encoding="utf-8")
    subprocess.run(
        [
            environment["TEST_REAL_RESTIC"],
            "-r",
            environment["TEST_LOCAL_RESTIC_REPOSITORY"],
            "--password-file",
            environment["RESTIC_PASSWORD_FILE"],
            "backup",
            "BACKUP-RECEIPT.json",
            "data",
            "--host",
            "learn-ukrainian",
            "--tag",
            "learn-ukrainian-data",
        ],
        cwd=tree,
        check=True,
        capture_output=True,
        timeout=60,
    )

    target = tmp_path / "restored"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")

    assert restored.returncode == 0, restored.stderr
    assert _logical_sha256(target / "data" / "atlas.db") == database_hash
    assert (target / "data" / "ordinary.txt").read_text(encoding="utf-8") == "recover me\n"


def test_retention_counts_pending_only_runs_incomplete_and_pending_plus_complete_as_one_run(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    snapshots = [
        *_run_snapshots("pending-old", "2026-09-01", parts=["base", "db", "receipt"], id_byte="1"),
        *_run_snapshots("complete", "2026-09-02", parts=["base", "db", "receipt", "complete"], id_byte="2"),
        *_run_snapshots("pending-new", "2026-09-03", parts=["base", "db", "receipt"], id_byte="3"),
    ]
    _write_snapshots(environment, tmp_path, snapshots)

    result = _run(environment, "retention")

    assert result.returncode == 0, result.stderr
    assert "Runs kept: 2" in result.stdout
    assert re.search(r"keep lu-run-complete time=\S+ snapshots=4\n", result.stdout), result.stdout
    # A newer pending-only run is protected; an older one is a failed run.
    assert re.search(r"keep lu-run-pending-new time=\S+ snapshots=3\n", result.stdout), result.stdout
    assert re.search(r"drop lu-run-pending-old time=\S+ snapshots=3\n", result.stdout), result.stdout

    only_pending = _run_snapshots("pending-only", "2026-09-04", parts=["base", "db", "receipt"], id_byte="4")
    _write_snapshots(environment, tmp_path, only_pending)
    refused = _run(environment, "retention")
    assert refused.returncode != 0
    assert "no completed run" in refused.stderr


def test_backup_defaults_to_repository_dry_run(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    source_file = source / "valuable.txt"
    source_file.write_text("do not mutate\n", encoding="utf-8")

    result = _run(environment, "backup")

    assert result.returncode == 0, result.stderr
    assert "Backup preview only" in result.stdout
    assert "arg=<backup>" in _log(environment)
    assert "arg=<--dry-run>" in _log(environment)
    assert "arg=<--option> arg=<rclone.connections=1>" in _log(environment)
    assert source_file.read_text(encoding="utf-8") == "do not mutate\n"
    assert list(staging.iterdir()) == []


def test_execute_rejects_a_corrupt_database_before_upload(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    (source / "corrupt.db").write_bytes(b"SQLite format 3\0" + b"corrupt data")

    result = _run(environment, "backup", "--execute")

    assert result.returncode != 0
    assert "Database data/corrupt.db: SQLite online backup failed" in result.stderr
    assert "arg=<lu-part-db>" not in _log(environment)
    assert "arg=<lu-part-complete>" not in _log(environment)
    assert list(staging.iterdir()) == []


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read mode-000 paths")
def test_doctor_warns_about_unreadable_file(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    unreadable = source / "unreadable.txt"
    unreadable.write_text("private\n", encoding="utf-8")
    unreadable.chmod(0)

    try:
        result = _run(environment, "doctor")
    finally:
        unreadable.chmod(0o600)

    assert result.returncode == 0, result.stderr
    assert "WARNING: 1 path(s) under backup roots are unreadable" in result.stderr
    assert str(unreadable) in result.stderr


@pytest.mark.skipif(os.geteuid() == 0, reason="root can traverse mode-000 directories")
def test_doctor_warns_about_unreadable_directory(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    unreadable = source.parent / "batch_state" / "unreadable-dir"
    unreadable.mkdir()
    (unreadable / "hidden.txt").write_text("private\n", encoding="utf-8")
    unreadable.chmod(0)

    try:
        result = _run(environment, "doctor")
    finally:
        unreadable.chmod(0o700)

    assert result.returncode == 0, result.stderr
    assert "WARNING: 1 path(s) under backup roots are unreadable" in result.stderr
    assert str(unreadable) in result.stderr
    assert "Doctor checks passed." in result.stdout


def test_execute_refuses_when_one_database_would_exceed_staging_space(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    (source / "valuable.txt").write_text("sole copy\n", encoding="utf-8")
    database = source / "large.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    _write_executable(
        fake_bin / "df",
        """#!/bin/bash
printf '%s\\n' 'Filesystem 1024-blocks Used Available Capacity Mounted on'
printf '%s\\n' 'testfs 4194304 0 2097152 0% /staging'
""",
    )

    result = _run(environment, "backup", "--execute")

    assert result.returncode != 0
    assert "Insufficient staging space" in result.stderr
    assert "arg=<lu-part-db>" not in _log(environment)


def test_darwin_rejects_cross_volume_copy_on_write_staging(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    _write_executable(fake_bin / "uname", "#!/bin/bash\nprintf '%s\\n' Darwin\n")
    _write_executable(
        fake_bin / "stat",
        """#!/bin/bash
if [[ "${1:-}" == '-f' && "${2:-}" == '%d' ]]; then
  case "${3:-}" in
    */project/*) printf '%s\\n' 101 ;;
    *) printf '%s\\n' 202 ;;
  esac
  exit 0
fi
exec /usr/bin/stat "$@"
""",
    )

    result = _run(environment, "backup", "--execute")

    assert result.returncode != 0
    assert "requires source and staging on the same volume" in result.stderr
    assert "arg=<backup>" not in _log(environment)


@pytest.mark.parametrize(
    ("target", "expected_error"),
    [
        ("/tmp/agent-outside", "Absolute symlink is not backup-safe in .agent"),
        ("../agent-outside", "Symlink escapes .agent"),
    ],
)
def test_backup_fails_closed_for_unsafe_agent_symlink(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    target: str,
    expected_error: str,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    agent_root = source.parent / ".agent"
    if target == "../agent-outside":
        (source.parent / "agent-outside").mkdir()
    elif target == "/tmp/agent-outside":
        external_root = tmp_path / "agent-outside"
        external_root.mkdir()
        target = str(external_root)
    (agent_root / "unsafe-link").symlink_to(target)

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert expected_error in result.stderr
    assert "arg=<backup>" not in _log(environment)


def test_symlink_policy_excludes_known_legacy_links_and_rejects_escapes(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, legacy = backup_environment
    (legacy / "textbooks").mkdir()
    (source / "textbooks").symlink_to(legacy / "textbooks")

    accepted = _run(environment, "backup")

    assert accepted.returncode == 0, accepted.stderr
    assert "EXCLUDED legacy Drive symlink: textbooks" in accepted.stdout

    escaped_target = tmp_path / "outside-source"
    escaped_target.mkdir()
    (source / "unexpected-link").symlink_to(escaped_target)
    rejected = _run(environment, "backup")

    assert rejected.returncode != 0
    assert "Absolute symlink is not backup-safe" in rejected.stderr


def test_doctor_and_backup_exclude_dangling_legacy_drive_symlinks(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    environment.pop("LU_BACKUP_LEGACY_DIR", None)
    dangling_target = tmp_path / "nonexistent-drive-path" / "textbooks"
    (source / "textbooks").symlink_to(dangling_target)
    (source / "vesum").symlink_to(tmp_path / "nonexistent-drive-path" / "vesum")

    doctor_result = _run(environment, "doctor")
    assert doctor_result.returncode == 0, doctor_result.stderr
    assert "EXCLUDED legacy Drive symlink: textbooks\n" in doctor_result.stdout
    assert "EXCLUDED legacy Drive symlink: vesum\n" in doctor_result.stdout
    assert str(dangling_target) not in doctor_result.stdout
    assert "Doctor checks passed." in doctor_result.stdout

    backup_result = _run(environment, "backup")
    assert backup_result.returncode == 0, backup_result.stderr
    assert "EXCLUDED legacy Drive symlink: textbooks\n" in backup_result.stdout
    assert "EXCLUDED legacy Drive symlink: vesum\n" in backup_result.stdout
    assert str(dangling_target) not in backup_result.stdout


def test_backup_skips_dangling_non_legacy_symlink_in_source_with_warning(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    (source / "broken-link.txt").symlink_to("missing-dir/missing.txt")

    result = _run(environment, "backup")
    assert result.returncode == 0, result.stderr
    assert (
        "WARNING: Skipping broken symlink in backup source: broken-link.txt -> missing-dir/missing.txt" in result.stderr
    )
    assert f"exclude=<{source}/broken-link.txt>" in _log(environment)


def test_init_requires_execute_before_creating_repository(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    environment["FAKE_REPOSITORY_STATE"] = "missing"

    preview = _run(environment, "init")

    assert preview.returncode == 0, preview.stderr
    assert "Initialization preview only" in preview.stdout
    assert "arg=<init>" not in _log(environment)

    Path(environment["FAKE_RESTIC_LOG"]).write_text("", encoding="utf-8")
    executed = _run(environment, "init", "--execute")

    assert executed.returncode == 0, executed.stderr
    assert "arg=<init>" in _log(environment)
    assert "arg=<check>" in _log(environment)


def test_doctor_checks_initialized_repository_with_validated_environment(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment

    result = _run(environment, "doctor")

    assert result.returncode == 0, result.stderr
    assert "OK: restic repository is initialized" in result.stdout
    assert "Doctor checks passed." in result.stdout
