"""Completion snapshots, and restore when publication fails or the snapshot is corrupt."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import sqlite3
import time
from pathlib import Path

import pytest

from scripts.lexicon.runner.durable_mirror import DurableMirrorError, require_durable
from tests.backup_data_script._support import (
    _completed_run_ids,
    _dangling_recovery_links,
    _fresh_runner_mirror,
    _log,
    _logical_sha256,
    _make_database,
    _real_restic,
    _repository_snapshots,
    _restored_run_id,
    _run,
    _run_id,
    _run_interrupted,
    _use_local_restic,
    _write_executable,
)


@pytest.mark.parametrize("failure", ["every-check", "check-after-marker", "mirror-changed"])
def test_a_failed_run_never_leaves_a_completed_run_for_restore_latest(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    failure: str,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    mirror = source / "lexicon" / "runner-mirror" / "run-20k"
    mirror.mkdir(parents=True)
    state = mirror / "state.txt"
    state.write_text("state\n", encoding="utf-8")
    (mirror / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "atlas-runner-mirror-manifest",
                "schema_version": 1,
                "generated_at": 1.0,
                "file_count": 1,
                "total_bytes": 6,
                "files": [{"path": "state.txt", "bytes": 6, "sha256": hashlib.sha256(b"state\n").hexdigest()}],
            }
        ),
        encoding="utf-8",
    )
    _make_database(source / "first.db")
    if failure == "every-check":
        environment["TEST_FAIL_CHECK"] = "always"
    elif failure == "check-after-marker":
        environment["TEST_FAIL_CHECK"] = "after-marker"
    else:
        environment["TEST_MUTATE_FILE"] = str(state)

    result = _run(environment, "backup", "--execute")
    invocations = Path(environment["TEST_INVOCATION_LOG"]).read_text(encoding="utf-8").splitlines()
    target = tmp_path / "restore-latest"
    latest = _run(environment, "restore", "latest", "--to", str(target))

    completed = "backup lu-part-complete" in invocations
    # Publishing the completion marker is the run's last repository operation.
    assert not completed or invocations[-1] == "backup lu-part-complete", invocations
    assert completed == (result.returncode == 0), (invocations, result.stderr)
    if failure != "check-after-marker":
        assert result.returncode != 0
    if result.returncode != 0:
        assert latest.returncode != 0
        assert "No completed Linux backup run is available" in latest.stderr
        assert not (mirror.parent / "RESTIC-GATE-RECEIPT.json").exists()
    else:
        assert latest.returncode == 0, latest.stderr
        assert (mirror.parent / "RESTIC-GATE-RECEIPT.json").is_file()
    assert not target.exists()


def test_completed_run_publishes_one_completion_snapshot_reusing_the_checked_pending_tree(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    mirror = _fresh_runner_mirror(source)
    (source / "datasets").mkdir()
    (source / "datasets" / "ordinary.txt").write_text("recover me\n", encoding="utf-8")
    database_hashes = {
        "data/datasets/first.db": _logical_sha256(_make_database(source / "datasets" / "first.db", "first")),
        "batch_state/fleet-comms/second.db": _logical_sha256(
            _make_database(source.parent / "batch_state" / "fleet-comms" / "second.db", "two")
        ),
    }

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    invocations = Path(environment["TEST_INVOCATION_LOG"]).read_text(encoding="utf-8").splitlines()
    assert [line for line in invocations if line.startswith("backup ")] == [
        "backup lu-part-base",
        "backup lu-part-db",
        "backup lu-part-receipt",
        "backup lu-part-complete",
    ]
    # The repository check follows the pending receipt; the completion upload
    # is the last repository operation. No snapshot is ever retagged or removed.
    assert invocations.index("check ") > invocations.index("backup lu-part-receipt")
    assert invocations[-1] == "backup lu-part-complete"
    assert not {line.split(" ")[0] for line in invocations} & {"tag", "forget", "prune", "rewrite"}

    snapshots = _repository_snapshots(environment)
    pending = [snapshot for snapshot in snapshots if "lu-part-receipt" in snapshot["tags"]]
    complete = [snapshot for snapshot in snapshots if "lu-part-complete" in snapshot["tags"]]
    assert len(pending) == len(complete) == 1
    assert "lu-part-complete" not in pending[0]["tags"]
    assert complete[0]["tree"] == pending[0]["tree"]
    assert complete[0]["time"] == pending[0]["time"]
    assert _run_id(complete[0]) == _run_id(pending[0])
    pending_receipt = _real_restic(environment, "dump", pending[0]["id"], "/BACKUP-RECEIPT.json")
    complete_receipt = _real_restic(environment, "dump", complete[0]["id"], "/BACKUP-RECEIPT.json")
    assert pending_receipt.returncode == complete_receipt.returncode == 0
    assert pending_receipt.stdout == complete_receipt.stdout

    gate = json.loads((mirror.parent / "RESTIC-GATE-RECEIPT.json").read_text(encoding="utf-8"))
    assert gate["restic_snapshot_id"] == json.loads(complete_receipt.stdout)["linux_run"]["base_snapshot_id"]
    assert not (mirror.parent / "RESTIC-GATE-RECEIPT.json.tmp").exists()
    require_durable(mirror)

    target = tmp_path / "restored"
    assert _restored_run_id(environment, target) == _run_id(complete[0])
    for relative, expected in database_hashes.items():
        assert _logical_sha256(target / relative) == expected, relative
    assert (target / "data" / "datasets" / "ordinary.txt").read_text(encoding="utf-8") == "recover me\n"
    assert (target / "BACKUP-RECEIPT.json").read_text(encoding="utf-8") == complete_receipt.stdout


@pytest.mark.parametrize("window", ["sigkill-after-completion", "gate-rename-fails"])
def test_a_failure_after_completion_leaves_a_restorable_run_and_no_gate_receipt(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    window: str,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    mirror = _fresh_runner_mirror(source)
    database_hash = _logical_sha256(_make_database(source / "datasets" / "first.db", "first"))
    gate = mirror.parent / "RESTIC-GATE-RECEIPT.json"

    if window == "gate-rename-fails":
        # A directory in the way makes the final rename fail for real.
        gate.mkdir()
        result = _run(environment, "backup", "--execute")
        assert result.returncode == 1
        assert "could not be renamed into place; the pre-wipe gate stays closed" in result.stderr
        assert not (mirror.parent / "RESTIC-GATE-RECEIPT.json.tmp").exists()
    else:
        environment["TEST_HOLD_FILE"] = str(tmp_path / "hold")
        environment["TEST_HOLD_AFTER"] = "backup lu-part-complete"
        result = _run_interrupted(environment, signal.SIGKILL)
        assert result.returncode == -9

    # The accepted commit-follower window: the run is complete and restorable,
    # the exit is non-zero, and no gate receipt exists, so no wipe may proceed.
    [completed] = _completed_run_ids(environment)
    target = tmp_path / "restored"
    assert _restored_run_id(environment, target) == completed
    assert _logical_sha256(target / "data" / "datasets" / "first.db") == database_hash
    assert not gate.is_file()
    with pytest.raises(DurableMirrorError, match="no restic gate receipt"):
        require_durable(mirror)


def test_a_corrupted_completion_snapshot_is_skipped_by_restore_and_fails_the_next_check(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    """Corruption after the completion upload is outside what the run itself can verify."""
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    first_hash = _logical_sha256(_make_database(source / "datasets" / "first.db", "first"))
    assert _run(environment, "backup", "--execute").returncode == 0
    [previous_run] = _completed_run_ids(environment)
    second_hash = _logical_sha256(_make_database(source / "datasets" / "second.db", "second"))
    latest = _run(environment, "backup", "--execute")
    assert latest.returncode == 0, latest.stderr
    snapshots = _repository_snapshots(environment)
    [latest_run] = set(_completed_run_ids(environment)) - {previous_run}
    [marker] = [s for s in snapshots if "lu-part-complete" in s["tags"] and _run_id(s) == latest_run]
    [pending] = [s for s in snapshots if "lu-part-receipt" in s["tags"] and _run_id(s) == latest_run]

    # Damage the completion snapshot object itself: it is the only object the
    # completion upload adds, because it reuses the checked pending tree.
    marker_file = Path(environment["TEST_LOCAL_RESTIC_REPOSITORY"]) / "snapshots" / marker["id"]
    marker_file.chmod(0o600)
    with marker_file.open("r+b") as handle:
        handle.seek(20)
        handle.write(b"corrupted")

    # restic skips the unreadable snapshot, so restore latest on a cold cache
    # selects the previous completed run rather than the damaged one.
    environment["RESTIC_CACHE_DIR"] = str(tmp_path / "cold-cache")
    assert _restored_run_id(environment, tmp_path / "restored-latest") == previous_run
    assert _real_restic(environment, "check").returncode != 0
    # The damaged run stays recoverable through its checked pending receipt.
    by_pending = tmp_path / "restored-by-pending"
    restored = _run(environment, "restore", pending["id"], "--to", str(by_pending), "--execute")
    assert restored.returncode == 0, restored.stderr
    assert _logical_sha256(by_pending / "data" / "datasets" / "first.db") == first_hash
    assert _logical_sha256(by_pending / "data" / "datasets" / "second.db") == second_hash
    # The next run's repository check fails it before it can publish.
    environment.pop("RESTIC_CACHE_DIR")
    following = _run(environment, "backup", "--execute")
    assert following.returncode == 1
    assert "Repository check failed" in following.stderr
    assert set(_completed_run_ids(environment)) == {previous_run}


@pytest.mark.skipif(not Path("/proc/self/fd").is_dir(), reason="Linux fd inspection required")
def test_restic_and_git_children_do_not_inherit_backup_lock(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    restic = fake_bin / "restic"
    original_restic = fake_bin / "restic-original"
    restic.rename(original_restic)
    environment["REAL_GIT"] = shutil.which("git") or ""
    assert environment["REAL_GIT"]
    environment["TEST_LOCK_PATH"] = str(
        Path(environment["XDG_RUNTIME_DIR"]) / f"learn-ukrainian-backup.{os.getuid()}.lock"
    )
    lock_probe = 'for fd in /proc/self/fd/*; do\n  [[ "$(readlink "$fd")" == "$TEST_LOCK_PATH" ]] && exit 91\ndone\n'
    _write_executable(restic, "#!/bin/bash\n" + lock_probe + 'exec "$(dirname "$0")/restic-original" "$@"\n')
    _write_executable(fake_bin / "git", "#!/bin/bash\n" + lock_probe + 'exec "$REAL_GIT" "$@"\n')

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert "arg=<backup>" in _log(environment)


def test_review_homes_are_excluded_but_other_absolute_links_still_fail(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    home = source.parent / "batch_state" / "review-receipts" / "attempt-1" / "a1.agy-home"
    home.mkdir(parents=True)
    credential = tmp_path / "dummy-credential"
    credential.write_text("fixture only\n", encoding="utf-8")
    (home / "credential-link").symlink_to(credential)

    doctor = _run(environment, "doctor")
    assert doctor.returncode == 0, doctor.stderr
    assert "Doctor checks passed." in doctor.stdout
    preview = _run(environment, "backup")
    assert preview.returncode == 0, preview.stderr
    assert str(home) in _log(environment)
    executed = _run(environment, "backup", "--execute")
    assert executed.returncode == 0, executed.stderr
    assert not (
        Path(environment["FAKE_SNAPSHOT_DIR"]) / "batch_state" / "review-receipts" / "attempt-1" / "a1.agy-home"
    ).exists()

    other = source.parent / "batch_state" / "fleet-comms" / "unsafe-link"
    other.symlink_to(credential)
    doctor_batch_state = _run(environment, "doctor")
    assert doctor_batch_state.returncode == 0, doctor_batch_state.stderr
    assert "WARNING: Skipping absolute symlink in batch_state/fleet-comms: unsafe-link" in doctor_batch_state.stdout

    agent_link = source.parent / ".agent" / "unsafe-link"
    agent_link.symlink_to(credential)
    rejected = _run(environment, "doctor")
    assert rejected.returncode != 0
    assert "Absolute symlink is not backup-safe in .agent" in rejected.stderr


def test_linux_checks_free_space_before_each_database(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    # sources.db is the first database. One more database is enough to prove
    # the pending batch is uploaded and the failing database is checked again.
    (source / "datasets").mkdir()
    with sqlite3.connect(source / "datasets" / "a.db") as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")
    counter = tmp_path / "df-count"
    environment["FAKE_DF_COUNT"] = str(counter)
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    _write_executable(
        fake_bin / "df",
        r"""#!/bin/bash
count=0
[[ ! -f "$FAKE_DF_COUNT" ]] || count="$(cat "$FAKE_DF_COUNT")"
count=$((count + 1))
printf '%s\n' "$count" > "$FAKE_DF_COUNT"
available=4194304
[[ "$count" -eq 1 ]] || available=2097152
printf '%s\n' 'Filesystem 1024-blocks Used Available Capacity Mounted on'
printf 'testfs 8388608 0 %s 0%% /staging\n' "$available"
""",
    )
    result = _run(environment, "backup", "--execute")
    assert result.returncode != 0
    assert "Insufficient staging space for data/datasets/a.db" in result.stderr
    # sources.db passes; a.db fails, the pending batch uploads, a.db fails again.
    assert counter.read_text(encoding="utf-8").strip() == "3"
    assert _log(environment).count("arg=<lu-part-db>") == 1
    assert "db_file=<data/sources.db>" in _log(environment)
    assert "db_file=<data/datasets/a.db>" not in _log(environment)
    assert "arg=<lu-part-complete>" not in _log(environment)


def test_linux_local_restic_round_trip_stages_one_db_at_a_time(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    # A one-byte batch budget keeps every database in its own upload.
    environment["LU_BACKUP_DB_BATCH_MAX_BYTES"] = "1"
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    _write_executable(fake_bin / "cp", "#!/bin/bash\nexit 97\n")
    (source / "datasets").mkdir()
    (source / "datasets" / "ordinary.txt").write_text("recover me\n", encoding="utf-8")
    first_connection = sqlite3.connect(source / "datasets" / "first.db")
    first_connection.execute("PRAGMA journal_mode=WAL")
    first_connection.execute("CREATE TABLE recovery_probe(value TEXT)")
    first_connection.execute("INSERT INTO recovery_probe VALUES ('first')")
    first_connection.commit()
    (source / "datasets" / "first.db").chmod(0o600)
    second = source.parent / "batch_state" / "fleet-comms" / "second.sqlite3"
    with sqlite3.connect(second) as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")
        connection.execute("INSERT INTO recovery_probe VALUES ('second')")
    (source / "datasets" / "orphan.db-journal").write_text("transient", encoding="utf-8")
    home = source.parent / "batch_state" / "review-receipts" / "attempt" / "a1.agy-home"
    home.mkdir(parents=True)
    (home / "token-link").symlink_to(tmp_path / "nonexistent-token")
    symlink_home = source.parent / "batch_state" / "review-receipts" / "attempt-2" / "b2.agy-home"
    symlink_home.parent.mkdir(parents=True)
    symlink_home.symlink_to(tmp_path / "nonexistent-scoped-home")

    try:
        backed_up = _run(environment, "backup", "--execute")
    finally:
        first_connection.close()
    assert backed_up.returncode == 0, backed_up.stderr
    assert Path(environment["TEST_PEAK_LOG"]).read_text(encoding="utf-8").splitlines() == ["1", "1", "1", "0", "0"]
    assert list(staging.iterdir()) == []
    target = tmp_path / "restored"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")
    assert restored.returncode == 0, restored.stderr
    assert (target / "data" / "datasets" / "ordinary.txt").read_text(encoding="utf-8") == "recover me\n"
    assert not (target / "data" / "datasets" / "first.db-wal").exists()
    assert not (target / "data" / "datasets" / "first.db-shm").exists()
    assert not (target / "data" / "datasets" / "orphan.db-journal").exists()
    assert not (target / "batch_state" / "review-receipts" / "attempt" / "a1.agy-home").exists()
    assert not (target / "batch_state" / "review-receipts" / "attempt-2" / "b2.agy-home").exists()
    for database in (
        target / "data" / "datasets" / "first.db",
        target / "batch_state" / "fleet-comms" / "second.sqlite3",
    ):
        with sqlite3.connect(database) as connection:
            assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert connection.execute("SELECT COUNT(*) FROM recovery_probe").fetchone() == (1,)
    assert (target / "data" / "datasets" / "first.db").stat().st_mode & 0o777 == 0o600
    receipt = json.loads((target / "BACKUP-RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["schema_version"] == 3
    assert len(receipt["linux_run"]["databases"]) == 3


def test_execute_stages_a_consistent_wal_database_and_cleans_up(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    database = source / "datasets" / "live.db"
    database.parent.mkdir()
    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA wal_autocheckpoint=0")
        connection.execute("CREATE TABLE recovery_probe (value TEXT NOT NULL)")
        connection.execute("INSERT INTO recovery_probe VALUES ('first')")
        connection.commit()
        connection.execute("INSERT INTO recovery_probe VALUES ('latest')")
        connection.commit()
        assert database.with_name("live.db-wal").exists()
        environment["FAKE_DB_RELATIVE"] = "data/datasets/live.db"
        environment["FAKE_REQUIRED_RELATIVE"] = ".claude/atlas-epic/HANDOFF.md"

        result = _run(environment, "backup", "--execute")
    finally:
        connection.close()

    assert result.returncode == 0, result.stderr
    assert "Creating consistent SQLite snapshot: data/datasets/live.db" in result.stdout
    assert "db_rows=<2>" in _log(environment)
    assert "staged_required=<.claude/atlas-epic/HANDOFF.md>" in _log(environment)
    assert '"status":"prepared-before-snapshot-write"' in _log(environment)
    assert '".claude/atlas-epic"' in _log(environment)
    assert '".agent"' in _log(environment)
    assert '"batch_state/fleet-comms"' in _log(environment)
    assert list(staging.iterdir()) == []


def test_execute_writes_live_restic_gate_receipt_only_after_check(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    mirror = source / "lexicon" / "runner-mirror" / "run-20k"
    mirror.mkdir(parents=True)
    (mirror / "runner-state.txt").write_bytes(b"runner-state")
    manifest = {
        "schema": "atlas-runner-mirror-manifest",
        "schema_version": 1,
        "generated_at": 1.0,
        "file_count": 1,
        "total_bytes": 12,
        "files": [{"path": "runner-state.txt", "bytes": 12, "sha256": hashlib.sha256(b"runner-state").hexdigest()}],
    }
    (mirror / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    receipt_path = mirror.parent / "RESTIC-GATE-RECEIPT.json"

    preview = _run(environment, "backup")

    assert preview.returncode == 0, preview.stderr
    assert not receipt_path.exists()

    executed = _run(environment, "backup", "--execute")

    assert executed.returncode == 0, executed.stderr
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["restic_snapshot_id"] == "a" * 64
    assert (
        receipt["mirrors"]["run-20k"]["manifest_sha256"]
        == hashlib.sha256((mirror / "manifest.json").read_bytes()).hexdigest()
    )


def test_execute_does_not_write_restic_gate_receipt_when_check_fails(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    mirror = source / "lexicon" / "runner-mirror" / "run-20k"
    mirror.mkdir(parents=True)
    (mirror / "state.txt").write_text("state\n", encoding="utf-8")
    (mirror / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "atlas-runner-mirror-manifest",
                "schema_version": 1,
                "generated_at": 1.0,
                "file_count": 1,
                "total_bytes": 6,
                "files": [{"path": "state.txt", "bytes": 6, "sha256": hashlib.sha256(b"state\n").hexdigest()}],
            }
        ),
        encoding="utf-8",
    )
    environment["FAKE_RESTIC_CHECK_FAIL"] = "1"

    result = _run(environment, "backup", "--execute")

    assert result.returncode != 0
    assert not (mirror.parent / "RESTIC-GATE-RECEIPT.json").exists()
    assert "arg=<lu-part-complete>" not in _log(environment)


def test_execute_fails_closed_when_live_runner_mirror_changes_after_staging(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    """A staged manifest A must never produce a live receipt for mutated manifest B."""
    environment, source, staging, _legacy = backup_environment
    mirror = source / "lexicon" / "runner-mirror" / "run-20k"
    mirror.mkdir(parents=True)
    state_path = mirror / "runner-state.txt"
    original_state = b"runner-state-before-race"
    state_path.write_bytes(original_state)
    (mirror / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "atlas-runner-mirror-manifest",
                "schema_version": 1,
                "generated_at": time.time(),
                "file_count": 1,
                "total_bytes": len(original_state),
                "files": [
                    {
                        "path": "runner-state.txt",
                        "bytes": len(original_state),
                        "sha256": hashlib.sha256(original_state).hexdigest(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    original_manifest = (mirror / "manifest.json").read_bytes()
    mutated_state = b"runner-state-after-race"
    mutation_dir = staging.parent / "race-mutation"
    mutation_dir.mkdir()
    mutated_state_source = mutation_dir / "runner-state.txt"
    mutated_state_source.write_bytes(mutated_state)
    mutated_manifest_source = mutation_dir / "manifest.json"
    mutated_manifest_source.write_text(
        json.dumps(
            {
                "schema": "atlas-runner-mirror-manifest",
                "schema_version": 1,
                "generated_at": time.time(),
                "file_count": 1,
                "total_bytes": len(mutated_state),
                "files": [
                    {
                        "path": "runner-state.txt",
                        "bytes": len(mutated_state),
                        "sha256": hashlib.sha256(mutated_state).hexdigest(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    environment.update(
        {
            "FAKE_MUTATED_LIVE_STATE_SOURCE": str(mutated_state_source),
            "FAKE_MUTATED_LIVE_STATE_DESTINATION": str(state_path),
            "FAKE_MUTATED_LIVE_MANIFEST_SOURCE": str(mutated_manifest_source),
            "FAKE_MUTATED_LIVE_MANIFEST_DESTINATION": str(mirror / "manifest.json"),
        }
    )

    result = _run(environment, "backup", "--execute")

    assert result.returncode != 0
    assert "refusing to write a durability receipt" in result.stderr
    assert not (mirror.parent / "RESTIC-GATE-RECEIPT.json").exists()
    with pytest.raises(DurableMirrorError, match="no restic gate receipt"):
        require_durable(mirror)
    # The mismatch is found before the run is published as complete.
    assert "arg=<lu-part-complete>" not in _log(environment)

    # A change while the pending receipt uploads is still found before the run
    # is published as complete.
    state_path.write_bytes(original_state)
    (mirror / "manifest.json").write_bytes(original_manifest)
    Path(environment["FAKE_RESTIC_LOG"]).unlink()
    shutil.rmtree(environment["FAKE_SNAPSHOT_DIR"])
    environment["FAKE_MUTATE_ON_PART"] = "lu-part-receipt"
    mutated_pending = _run(environment, "backup", "--execute")

    assert mutated_pending.returncode != 0
    assert "refusing to write a durability receipt" in mutated_pending.stderr
    assert not (mirror.parent / "RESTIC-GATE-RECEIPT.json").exists()
    assert not (mirror.parent / "RESTIC-GATE-RECEIPT.json.tmp").exists()
    assert "arg=<lu-part-receipt>" in _log(environment)
    assert "arg=<lu-part-complete>" not in _log(environment)

    # A change while the completion snapshot uploads comes after the last
    # check. The run is complete, and its gate receipt binds only the verified
    # manifest, so the gate refuses the live content it never verified.
    state_path.write_bytes(original_state)
    (mirror / "manifest.json").write_bytes(original_manifest)
    Path(environment["FAKE_RESTIC_LOG"]).unlink()
    shutil.rmtree(environment["FAKE_SNAPSHOT_DIR"])
    environment["FAKE_MUTATE_ON_PART"] = "lu-part-complete"
    mutated_again = _run(environment, "backup", "--execute")

    assert mutated_again.returncode == 0, mutated_again.stderr
    receipt = json.loads((mirror.parent / "RESTIC-GATE-RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["mirrors"]["run-20k"]["manifest_sha256"] == hashlib.sha256(original_manifest).hexdigest()
    assert (mirror / "manifest.json").read_bytes() != original_manifest
    with pytest.raises(DurableMirrorError, match="manifest_sha256 mismatch"):
        require_durable(mirror)


def test_execute_snapshots_checkpointed_wal_database_without_sidecars(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    database = source / "datasets" / "checkpointed.db"
    database.parent.mkdir()
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("CREATE TABLE recovery_probe (value TEXT NOT NULL)")
    connection.execute("INSERT INTO recovery_probe VALUES ('checkpointed')")
    connection.commit()
    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    connection.close()
    assert not database.with_name("checkpointed.db-wal").exists()
    assert not database.with_name("checkpointed.db-shm").exists()
    environment["FAKE_DB_RELATIVE"] = "data/datasets/checkpointed.db"
    real_sqlite3 = shutil.which("sqlite3", path=os.environ["PATH"])
    assert real_sqlite3 is not None
    environment["REAL_SQLITE3"] = real_sqlite3
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    _write_executable(
        fake_bin / "sqlite3",
        """#!/bin/bash
set -eu
if [[ "${1:-}" == "-readonly" && "${2:-}" == */checkpointed.db ]]; then
  printf '%s\n' 'simulated read-only open failure' >&2
  exit 14
fi
exec "$REAL_SQLITE3" "$@"
""",
    )

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert "Using verified immutable fallback" in result.stdout
    assert "db_rows=<1>" in _log(environment)
    assert list(staging.iterdir()) == []


def test_non_sqlite_candidate_is_backed_up_as_a_file(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    fence = source.parent / "batch_state" / "fleet-comms" / "comms.sqlite3.pg-fence"
    fence.write_text('{"fence": true}\n', encoding="utf-8")
    environment["FAKE_REQUIRED_RELATIVE"] = "batch_state/fleet-comms/comms.sqlite3.pg-fence"

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert "staged_required=<batch_state/fleet-comms/comms.sqlite3.pg-fence>" in _log(environment)
    assert "Creating consistent SQLite snapshot: batch_state/fleet-comms/comms.sqlite3.pg-fence" not in result.stdout


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read mode-000 paths")
def test_unreadable_file_does_not_skip_database_phase(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    unreadable = source.parent / "batch_state" / "fleet-comms" / "unreadable.txt"
    unreadable.write_text("private\n", encoding="utf-8")
    unreadable.chmod(0)
    (source / "datasets").mkdir(exist_ok=True)
    with sqlite3.connect(source / "datasets" / "healthy.db") as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")
    environment["FAKE_FILE_PHASE_EXIT"] = "3"

    try:
        result = _run(environment, "backup", "--execute")
    finally:
        unreadable.chmod(0o600)

    assert result.returncode != 0
    assert "batch_state/fleet-comms/unreadable.txt" in result.stderr
    assert "File phase: restic backup failed" in result.stderr
    assert "arg=<lu-part-db>" in _log(environment)
    assert "arg=<lu-part-complete>" not in _log(environment)


@pytest.mark.skipif(os.geteuid() == 0, reason="root can traverse mode-000 directories")
def test_unreadable_directory_does_not_skip_database_phase(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    unreadable = source.parent / "batch_state" / "fleet-comms" / "unreadable-dir"
    unreadable.mkdir()
    (unreadable / "hidden.txt").write_text("private\n", encoding="utf-8")
    (source / "datasets").mkdir(exist_ok=True)
    with sqlite3.connect(source / "datasets" / "healthy.db") as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")
    unreadable.chmod(0)

    try:
        result = _run(environment, "backup", "--execute")
    finally:
        unreadable.chmod(0o700)
        snapshot_copy = Path(environment["FAKE_SNAPSHOT_DIR"]) / "batch_state" / "fleet-comms" / unreadable.name
        if snapshot_copy.exists():
            snapshot_copy.chmod(0o700)

    assert result.returncode != 0
    assert "Backup run " in result.stderr
    assert "Unreadable paths:" in result.stderr
    assert "batch_state/fleet-comms/unreadable-dir" in result.stderr
    assert "db_file=<data/datasets/healthy.db>" in _log(environment)
    assert "arg=<lu-part-complete>" not in _log(environment)


def test_corrupt_database_does_not_skip_later_databases(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    (source / "datasets").mkdir(exist_ok=True)
    (source / "datasets" / "corrupt.db").write_bytes(b"SQLite format 3\0" + b"corrupt data")
    with sqlite3.connect(source / "datasets" / "healthy.db") as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")

    result = _run(environment, "backup", "--execute")

    assert result.returncode != 0
    assert "Database data/datasets/corrupt.db: SQLite online backup failed" in result.stderr
    assert "db_file=<data/datasets/healthy.db>" in _log(environment)
    assert "arg=<lu-part-complete>" not in _log(environment)


def test_find_permission_error_keeps_reported_paths_and_database_phase(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    (source / "datasets").mkdir(exist_ok=True)
    with sqlite3.connect(source / "datasets" / "healthy.db") as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")
    real_find = shutil.which("find", path=os.environ["PATH"])
    assert real_find is not None
    environment["REAL_FIND"] = real_find
    environment["FAKE_FIND_ROOT"] = str(source.parent / "batch_state" / "fleet-comms")
    environment["FAKE_FILE_PHASE_EXIT"] = "3"
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    _write_executable(
        fake_bin / "find",
        """#!/bin/bash
for argument in "$@"; do
  if [[ "$1" == "$FAKE_FIND_ROOT" && "$argument" == "-readable" ]]; then
    printf '%s\\n' "$FAKE_FIND_ROOT/already-found.txt"
    printf "find: '%s': Permission denied\\n" "$FAKE_FIND_ROOT/denied-dir" >&2
    exit 1
  fi
done
exec "$REAL_FIND" "$@"
""",
    )

    doctor = _run(environment, "doctor")
    run = _run(environment, "backup", "--execute")

    assert doctor.returncode == 0, doctor.stderr
    assert "WARNING: 2 path(s) under backup roots are unreadable" in doctor.stderr
    assert str(source.parent / "batch_state" / "fleet-comms" / "already-found.txt") in doctor.stderr
    assert str(source.parent / "batch_state" / "fleet-comms" / "denied-dir") in doctor.stderr
    assert run.returncode != 0
    assert "batch_state/fleet-comms/already-found.txt" in run.stderr
    assert "batch_state/fleet-comms/denied-dir" in run.stderr
    assert "db_file=<data/datasets/healthy.db>" in _log(environment)
    assert "arg=<lu-part-complete>" not in _log(environment)


def test_receipt_counts_match_post_exclusion_snapshot_contents(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    datasets = source / "datasets"
    datasets.mkdir()
    (datasets / "qdrant").mkdir()
    (datasets / "qdrant" / "retired.bin").write_bytes(b"not recoverable")
    (datasets / "__pycache__").mkdir()
    (datasets / "__pycache__" / "cache.pyc").write_bytes(b"not recoverable")
    (datasets / "sidecar.db-wal").write_bytes(b"not recoverable")
    (datasets / ".DS_Store").write_bytes(b"not recoverable")
    (datasets / "keep.txt").write_bytes(b"keep\n")
    (datasets / "keep-wal").write_bytes(b"keep\n")
    environment.update(
        {
            "FAKE_FORBIDDEN_RELATIVES": (
                "data/datasets/qdrant data/datasets/__pycache__ data/datasets/sidecar.db-wal data/datasets/.DS_Store"
            ),
            "FAKE_REQUIRED_RELATIVE": "data/datasets/keep-wal",
        }
    )

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert '"data":{"path":"data/datasets","files":2,"bytes":10}' in _log(environment)
    assert _log(environment).count("staged_excluded=<") == 4
    assert list(staging.iterdir()) == []


def test_execute_snapshots_sqlite3_database_from_batch_state(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    database = source.parent / "batch_state" / "fleet-comms" / "v1" / "comms.sqlite3"
    database.parent.mkdir(parents=True)
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE recovery_probe (value TEXT NOT NULL)")
    connection.execute("INSERT INTO recovery_probe VALUES ('batch')")
    connection.commit()
    connection.close()
    environment["FAKE_DB_RELATIVE"] = "batch_state/fleet-comms/v1/comms.sqlite3"

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert "consistent SQLite snapshot: batch_state/fleet-comms/v1/comms.sqlite3" in result.stdout
    assert "db_rows=<1>" in _log(environment)
    assert list(staging.iterdir()) == []


def test_execute_restores_agent_wal_database_without_sidecars(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, staging, _legacy = backup_environment
    database = source.parent / ".agent" / "session-streams" / "v1" / "session-streams.sqlite3"
    database.parent.mkdir(parents=True)
    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA wal_autocheckpoint=0")
        connection.execute("CREATE TABLE recovery_probe (value TEXT NOT NULL)")
        connection.execute("INSERT INTO recovery_probe VALUES ('first')")
        connection.commit()
        connection.execute("INSERT INTO recovery_probe VALUES ('latest')")
        connection.commit()
        assert database.with_name("session-streams.sqlite3-wal").exists()
        environment.update(
            {
                "FAKE_DB_RELATIVE": ".agent/session-streams/v1/session-streams.sqlite3",
                "FAKE_FORBIDDEN_RELATIVES": " ".join(
                    [
                        ".agent/session-streams/v1/session-streams.sqlite3-wal",
                        ".agent/session-streams/v1/session-streams.sqlite3-shm",
                    ]
                ),
                "FAKE_SNAPSHOT_DIR": str(tmp_path / "snapshot"),
            }
        )

        backed_up = _run(environment, "backup", "--execute")
    finally:
        connection.close()

    assert backed_up.returncode == 0, backed_up.stderr
    assert "db_rows=<2>" in _log(environment)
    assert _log(environment).count("staged_excluded=<") == 2
    assert list(staging.iterdir()) == []

    restore_target = tmp_path / "separate-restore-target"
    restored = _run(
        environment,
        "restore",
        "latest",
        "--to",
        str(restore_target),
        "--execute",
    )

    assert restored.returncode == 0, restored.stderr
    restored_database = restore_target / ".agent" / "session-streams" / "v1" / database.name
    assert not restored_database.with_name(f"{database.name}-wal").exists()
    assert not restored_database.with_name(f"{database.name}-shm").exists()
    with sqlite3.connect(f"{Path(restored_database).resolve().as_uri()}?mode=ro", uri=True) as restored_connection:
        rows = restored_connection.execute("SELECT value FROM recovery_probe ORDER BY rowid").fetchall()
    assert rows == [("first",), ("latest",)]
    assert (restore_target / ".agent").is_dir()
    assert restore_target != source.parent


def test_execute_stages_agent_recovery_file_and_receipt_label(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, staging, _legacy = backup_environment
    environment["FAKE_REQUIRED_RELATIVE"] = ".agent/recovery-state.json"
    snapshot = tmp_path / "snapshot"
    environment["FAKE_SNAPSHOT_DIR"] = str(snapshot)

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert "staged_required=<.agent/recovery-state.json>" in _log(environment)
    assert '"agent":{"path":".agent","files":1,"bytes":22}' in _log(environment)
    receipt_path = snapshot / "BACKUP-RECEIPT.json"
    receipt_text = receipt_path.read_text(encoding="utf-8")
    receipt = json.loads(receipt_text)
    assert next(path for path in receipt["paths"] if path["path"] == ".agent") == {
        "path": ".agent",
        "files": 1,
        "bytes": 22,
    }
    assert ".agent/recovery-state.json" not in receipt_text
    assert list(staging.iterdir()) == []


def test_execute_preserves_tracked_changes_as_a_patch(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    (source.parent / "README.md").write_text("changed locally\n", encoding="utf-8")
    environment["FAKE_REQUIRED_RELATIVE"] = "GIT-WORKTREE.patch"

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert "staged_required=<GIT-WORKTREE.patch>" in _log(environment)
    assert '"GIT-WORKTREE.patch"' in _log(environment)
    assert list(staging.iterdir()) == []


def test_backup_skips_dangling_symlinks_in_every_recovery_root_with_warning(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    project = source.parent
    links = _dangling_recovery_links(project)

    doctor = _run(environment, "doctor")
    assert doctor.returncode == 0, doctor.stderr
    assert "Doctor checks passed." in doctor.stdout
    # doctor folds validation output into stdout; backup keeps warnings on stderr.
    doctor_output = doctor.stdout + doctor.stderr
    assert (
        "WARNING: Skipping broken symlink in batch_state/fleet-comms: "
        "session/pytest-RC/dispatch-storescurrent -> ../../../../../.worktrees/removed/stores"
    ) in doctor_output
    assert "WARNING: Skipping broken symlink in .agent: stale-pointer -> missing-target" in doctor_output
    assert "WARNING: Skipping broken symlink in .claude/atlas-epic: gone[1]*?.md -> HANDOFF-old.md" in doctor_output
    assert "WARNING: Skipping broken symlink in data/datasets: moved-dataset -> missing-target" in doctor_output

    preview = _run(environment, "backup")
    assert preview.returncode == 0, preview.stderr
    assert "WARNING: Skipping broken symlink in .agent: stale-pointer -> missing-target" in preview.stderr
    log = _log(environment)
    assert f"exclude=<{links['batch_state/fleet-comms']}>" in log
    assert f"exclude=<{links['.agent']}>" in log
    assert f"exclude=<{links['data/datasets']}>" in log
    # Glob metacharacters in a skipped link name are matched literally.
    escaped = str(links[".claude/atlas-epic"]).replace("[", "\\[").replace("]", "\\]")
    escaped = escaped.replace("*", "\\*").replace("?", "\\?")
    assert f"exclude=<{escaped}>" in log

    executed = _run(environment, "backup", "--execute")
    assert executed.returncode == 0, executed.stderr
    receipt = json.loads((Path(environment["FAKE_SNAPSHOT_DIR"]) / "BACKUP-RECEIPT.json").read_text(encoding="utf-8"))
    assert {
        "batch_state/fleet-comms/session/pytest-RC/dispatch-storescurrent broken symlink skipped",
        ".agent/stale-pointer broken symlink skipped",
        ".claude/atlas-epic/gone[1]*?.md broken symlink skipped",
        "data/datasets/moved-dataset broken symlink skipped",
    } <= set(receipt["exclusions"])


def test_backup_without_dangling_symlinks_adds_no_broken_symlink_exclusions(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment

    executed = _run(environment, "backup", "--execute")

    assert executed.returncode == 0, executed.stderr
    assert "Skipping broken symlink" not in executed.stderr
    receipt = json.loads((Path(environment["FAKE_SNAPSHOT_DIR"]) / "BACKUP-RECEIPT.json").read_text(encoding="utf-8"))
    assert not [entry for entry in receipt["exclusions"] if entry.endswith("broken symlink skipped")]


def test_directory_outside_the_allowlist_is_not_selected(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    textbooks = source / "textbooks"
    textbooks.mkdir()
    (textbooks / "local-source.txt").write_text("preserve\n", encoding="utf-8")
    chunks = source / "textbook_chunks"
    chunks.mkdir()
    (chunks / "local-source.txt").write_text("preserve\n", encoding="utf-8")
    environment["FAKE_REQUIRED_RELATIVE"] = "data/textbook_chunks/local-source.txt"

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    log = _log(environment)
    assert "staged_required=<data/textbook_chunks/local-source.txt>" in log
    assert "arg=<data/textbook_chunks>" in log
    assert "arg=<data/textbooks>" not in log
    assert str(textbooks) not in log
    assert list(staging.iterdir()) == []


def test_linux_allows_designated_staging_on_the_data_volume(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    data_staging = source / ".backup-staging"
    data_staging.mkdir()
    environment["LU_BACKUP_TMPDIR"] = str(data_staging)
    with sqlite3.connect(source / "live.db") as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert f"exclude=<{data_staging}>" in _log(environment)
    assert list(data_staging.iterdir()) == []
