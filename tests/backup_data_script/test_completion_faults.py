"""Faults before the completion snapshot must not publish a restorable run."""

from __future__ import annotations

import fcntl
import os
import shutil
import signal
import sys
from pathlib import Path

import pytest

from tests.backup_data_script._support import (
    PRE_COMPLETION_FAULTS,
    _completed_run_ids,
    _forget_ids,
    _fresh_runner_mirror,
    _log,
    _logical_sha256,
    _make_database,
    _repository_snapshots,
    _restored_run_id,
    _run,
    _run_id,
    _run_interrupted,
    _run_snapshots,
    _snapshot,
    _use_local_restic,
    _write_executable,
    _write_snapshots,
)


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores the read-only snapshot directory")
@pytest.mark.parametrize("fault", PRE_COMPLETION_FAULTS)
def test_a_fault_before_completion_never_publishes_the_run(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    fault: str,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    mirror = _fresh_runner_mirror(source)
    first_hash = _logical_sha256(_make_database(source / "datasets" / "first.db", "first"))
    previous = _run(environment, "backup", "--execute")
    assert previous.returncode == 0, previous.stderr
    [previous_run] = _completed_run_ids(environment)
    gate = mirror.parent / "RESTIC-GATE-RECEIPT.json"
    previous_gate = gate.read_bytes()

    _make_database(source / "datasets" / "second.db", "second")
    environment["TEST_HOLD_FILE"] = str(tmp_path / "hold")
    if fault == "check-fails":
        environment["TEST_FAIL_CHECK"] = "always"
    elif fault == "pending-summary-invalid":
        environment["TEST_CORRUPT_SUMMARY_AT"] = "backup lu-part-receipt"
    elif fault == "mirror-mutated":
        environment["TEST_MUTATE_FILE"] = str(mirror / "state.txt")
    elif fault == "pending-pack-corrupted":
        environment["TEST_CORRUPT_PACKS_AFTER"] = "backup lu-part-receipt"
    elif fault == "term-in-gate-staging":
        # Hold the gate receipt writer: the last step before completion.
        writer = tmp_path / "hold-python"
        _write_executable(
            writer,
            "#!/bin/bash\n"
            'if [[ " $* " == *" write-restic-gate-receipt "* ]]; then\n'
            '  touch "$TEST_HOLD_FILE"\n'
            '  while [[ ! -e "$TEST_HOLD_FILE.release" ]]; do sleep 0.05; done\n'
            "fi\n"
            f'exec "{sys.executable}" "$@"\n',
        )
        environment["LU_BACKUP_PYTHON"] = str(writer)
    elif fault == "gate-staging-fails":
        (mirror.parent / "RESTIC-GATE-RECEIPT.json.tmp").mkdir()
    elif fault == "completion-upload-fails":
        environment["TEST_READONLY_SNAPSHOTS_AT"] = "backup lu-part-complete"
    else:
        environment["TEST_HOLD_BEFORE"] = "backup lu-part-complete"
    snapshots_directory = Path(environment["TEST_LOCAL_RESTIC_REPOSITORY"]) / "snapshots"
    try:
        if fault == "term-in-gate-staging":
            result = _run_interrupted(environment, signal.SIGTERM)
        elif fault == "sigkill-before-completion":
            result = _run_interrupted(environment, signal.SIGKILL)
        else:
            result = _run(environment, "backup", "--execute")
    finally:
        snapshots_directory.chmod(0o700)

    assert result.returncode != 0, result.stdout
    assert result.returncode == {"term-in-gate-staging": 130, "sigkill-before-completion": -9}.get(fault, 1)
    runs = {_run_id(snapshot) for snapshot in _repository_snapshots(environment)}
    assert len(runs) == 2, runs
    assert _completed_run_ids(environment) == [previous_run]
    # The failed run writes no gate receipt; the previous one is untouched.
    assert gate.read_bytes() == previous_gate
    staged = mirror.parent / "RESTIC-GATE-RECEIPT.json.tmp"
    if fault == "gate-staging-fails":
        assert staged.is_dir()
    elif fault != "sigkill-before-completion":
        assert not staged.exists()

    target = tmp_path / "restored"
    assert _restored_run_id(environment, target) == previous_run
    assert _logical_sha256(target / "data" / "datasets" / "first.db") == first_hash
    assert not (target / "data" / "datasets" / "second.db").exists()
    if fault == "pending-pack-corrupted":
        assert "Repository check failed" in result.stderr


def test_retention_previews_run_aware_plan_by_default(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    snapshots = _run_snapshots("20260910T033000Z-00000001", "2026-09-10", id_byte="1")
    snapshots += _run_snapshots("20260911T033000Z-00000002", "2026-09-11", id_byte="2")
    _write_snapshots(environment, tmp_path, snapshots)

    result = _run(environment, "retention")

    assert result.returncode == 0, result.stderr
    assert "Retention preview only" in result.stdout
    assert "Runs kept: 2" in result.stdout
    assert "Runs dropped: 0" in result.stdout
    assert "Snapshots to forget: 0" in result.stdout
    log = _log(environment)
    assert "arg=<snapshots>" in log
    assert "arg=<forget>" not in log
    assert "arg=<prune>" not in log
    assert "arg=<check>" not in log


def test_retention_execute_forgets_by_snapshot_id_then_prunes_and_checks(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    snapshots: list[dict[str, object]] = []
    for day in range(1, 10):
        snapshots += _run_snapshots(f"202609{day:02d}T033000Z-0000000{day}", f"2026-09-{day:02d}", id_byte=str(day))
    _write_snapshots(environment, tmp_path, snapshots)

    result = _run(environment, "retention", "--execute")

    assert result.returncode == 0, result.stderr
    assert "Retention plan for tag learn-ukrainian-data" in result.stdout
    assert "Runs kept: 7" in result.stdout
    assert "Runs dropped: 2" in result.stdout
    log_lines = _log(environment).splitlines()
    forget_lines = [line for line in log_lines if "arg=<forget>" in line]
    assert len(forget_lines) == 1
    assert "arg=<--tag>" not in forget_lines[0]
    assert "arg=<--keep-daily>" not in forget_lines[0]
    assert "arg=<--prune>" not in forget_lines[0]
    assert _forget_ids(environment) == sorted(
        snapshot["id"] for snapshot in snapshots if snapshot["id"].startswith(("1", "2"))
    )
    forget_index = next(i for i, line in enumerate(log_lines) if "arg=<forget>" in line)
    prune_index = next(i for i, line in enumerate(log_lines) if "arg=<prune>" in line)
    check_index = next(i for i, line in enumerate(log_lines) if "arg=<check>" in line)
    assert forget_index < prune_index < check_index
    # restic prune refuses a backend connection limit below two.
    assert "arg=<--option> arg=<rclone.connections=2>" in log_lines[prune_index]
    assert "arg=<--option> arg=<rclone.connections=1>" in log_lines[forget_index]
    assert "arg=<--option> arg=<rclone.connections=1>" in log_lines[check_index]


@pytest.mark.parametrize(("configured", "forget", "prune"), [("2", "2", "2"), ("4", "4", "4")])
def test_retention_honours_configured_rclone_connections(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    configured: str,
    forget: str,
    prune: str,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    environment["LU_BACKUP_RCLONE_CONNECTIONS"] = configured
    snapshots: list[dict[str, object]] = []
    for day in range(1, 10):
        snapshots += _run_snapshots(f"202609{day:02d}T033000Z-0000000{day}", f"2026-09-{day:02d}", id_byte=str(day))
    _write_snapshots(environment, tmp_path, snapshots)

    result = _run(environment, "retention", "--execute")

    assert result.returncode == 0, result.stderr
    log_lines = _log(environment).splitlines()
    forget_line = next(line for line in log_lines if "arg=<forget>" in line)
    prune_line = next(line for line in log_lines if "arg=<prune>" in line)
    assert f"arg=<rclone.connections={forget}>" in forget_line
    assert f"arg=<rclone.connections={prune}>" in prune_line


@pytest.mark.parametrize("configured", ["0", "17", "two", "1 --no-lock", "08"])
def test_invalid_rclone_connections_fail_before_any_repository_command(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    configured: str,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    environment["LU_BACKUP_RCLONE_CONNECTIONS"] = configured

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "LU_BACKUP_RCLONE_CONNECTIONS must be a whole number from 1 to 16." in result.stderr
    assert "arg=<backup>" not in _log(environment)


def test_retention_partial_newer_run_never_displaces_a_retained_run(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    snapshots: list[dict[str, object]] = []
    for day in range(1, 10):
        snapshots += _run_snapshots(
            f"202609{day:02d}T033000Z-0000000{day}",
            f"2026-09-{day:02d}",
            parts=["base", "db", "complete"],
            id_byte=str(day),
        )
    # A newer run that started but never wrote its receipt snapshot.
    snapshots += _run_snapshots("20260910T033000Z-00000010", "2026-09-10", parts=["base"], id_byte="f")
    _write_snapshots(environment, tmp_path, snapshots)

    result = _run(environment, "retention", "--execute")

    assert result.returncode == 0, result.stderr
    forgotten = _forget_ids(environment)
    dropped = {snapshot["id"] for snapshot in snapshots if snapshot["id"][0] in "12"}
    retained = {snapshot["id"] for snapshot in snapshots} - dropped
    assert set(forgotten) == dropped
    assert retained.isdisjoint(forgotten)
    partial_id = next(snapshot["id"] for snapshot in snapshots if snapshot["id"][0] == "f")
    assert partial_id not in forgotten


def test_retention_preserves_reviewers_newer_offset_partial_run(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    complete_id = "a" * 64
    partial_id = "b" * 64
    snapshots = _snapshot(complete_id, "20260926T033000Z-complete", ["complete"], "2026-09-26T03:30:00Z")
    snapshots += _snapshot(partial_id, "20260926T034500Z-partial", ["base"], "2026-09-26T02:45:00-01:00")
    _write_snapshots(environment, tmp_path, snapshots)

    result = _run(environment, "retention", "--execute")

    assert result.returncode == 0, result.stderr
    assert _forget_ids(environment) == []
    assert "Runs kept: 2" in result.stdout
    assert "Runs dropped: 0" in result.stdout


def test_retention_orders_fractional_and_mixed_offset_instants(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    complete_id = "a" * 64
    newer_partial_id = "b" * 64
    older_partial_id = "c" * 64
    snapshots = _snapshot(complete_id, "complete", ["complete"], "2026-09-26T03:30:00.100Z")
    snapshots += _snapshot(newer_partial_id, "newer", ["base"], "2026-09-26T04:30:00.200+01:00")
    snapshots += _snapshot(older_partial_id, "older", ["base"], "2026-09-26T02:30:00.050-01:00")
    _write_snapshots(environment, tmp_path, snapshots)

    result = _run(environment, "retention", "--execute")

    assert result.returncode == 0, result.stderr
    assert _forget_ids(environment) == [older_partial_id]
    assert newer_partial_id not in _forget_ids(environment)


def test_retention_uses_utc_day_for_mixed_offset_policy_buckets(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    older_id = "a" * 64
    newer_id = "b" * 64
    snapshots = _snapshot(older_id, "older", ["complete"], "2026-09-02T00:15:00+01:00")
    snapshots += _snapshot(newer_id, "newer", ["complete"], "2026-09-01T23:50:00Z")
    _write_snapshots(environment, tmp_path, snapshots)

    result = _run(environment, "retention", "--execute")

    assert result.returncode == 0, result.stderr
    assert _forget_ids(environment) == [older_id]
    assert "Runs kept: 1" in result.stdout


def test_retention_policy_counts_runs_not_snapshots(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    snapshots: list[dict[str, object]] = []
    for day in range(1, 9):
        snapshots += _run_snapshots(
            f"202609{day:02d}T033000Z-0000000{day}",
            f"2026-09-{day:02d}",
            parts=["base", "db-one", "db-two", "db-three", "complete"],
            id_byte=str(day),
        )
    # A second, older completed run on the newest day: only the day's newest
    # run survives the daily bucket, however many snapshots each run holds.
    snapshots += _run_snapshots("20260908T013000Z-00000088", "2026-09-08", parts=["base", "complete"], id_byte="e")
    _write_snapshots(environment, tmp_path, snapshots)

    result = _run(environment, "retention", "--execute")

    assert result.returncode == 0, result.stderr
    assert "Runs kept: 7" in result.stdout
    assert "Runs dropped: 2" in result.stdout
    forgotten = _forget_ids(environment)
    dropped = {snapshot["id"] for snapshot in snapshots if snapshot["id"][0] in "1e"}
    assert set(forgotten) == dropped


def test_retention_forgets_orphan_snapshots_of_dropped_runs(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    snapshots: list[dict[str, object]] = []
    for day in range(1, 9):
        snapshots += _run_snapshots(f"202609{day:02d}T033000Z-0000000{day}", f"2026-09-{day:02d}", id_byte=str(day))
    # A failed run older than the newest completed run leaves orphan snapshots.
    snapshots += _run_snapshots("20260905T053000Z-00000099", "2026-09-05", parts=["base", "db"], id_byte="d")
    _write_snapshots(environment, tmp_path, snapshots)

    result = _run(environment, "retention", "--execute")

    assert result.returncode == 0, result.stderr
    forgotten = _forget_ids(environment)
    dropped = {snapshot["id"] for snapshot in snapshots if snapshot["id"][0] in "1d"}
    assert set(forgotten) == dropped


def test_retention_empty_snapshot_list_forgets_nothing_and_fails(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    _write_snapshots(environment, tmp_path, "[]\n")

    result = _run(environment, "retention", "--execute")

    assert result.returncode != 0
    assert "forgetting nothing" in result.stderr
    log = _log(environment)
    assert "arg=<forget>" not in log
    assert "arg=<prune>" not in log


def test_retention_unparsable_snapshot_list_forgets_nothing_and_fails(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    _write_snapshots(environment, tmp_path, "this is not json\n")

    result = _run(environment, "retention", "--execute")

    assert result.returncode != 0
    assert "forgetting nothing" in result.stderr
    log = _log(environment)
    assert "arg=<forget>" not in log
    assert "arg=<prune>" not in log


def test_retention_unparsable_snapshot_time_forgets_nothing(
    backup_environment: tuple[dict[str, str], Path, Path, Path], tmp_path: Path
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    snapshots = _snapshot("a" * 64, "complete", ["complete"], "2026-09-26T03:30:00Z")
    snapshots += _snapshot("b" * 64, "partial", ["base"], "unparsable")
    _write_snapshots(environment, tmp_path, snapshots)

    result = _run(environment, "retention", "--execute")

    assert result.returncode != 0
    assert "forgetting nothing" in result.stderr
    assert _forget_ids(environment) == []
    assert "arg=<prune>" not in _log(environment)


def test_backup_lock_wait_is_bounded_and_loud(backup_environment: tuple[dict[str, str], Path, Path, Path]) -> None:
    environment, _source, _staging, _legacy = backup_environment
    environment["LU_BACKUP_LOCK_WAIT_SECONDS"] = "0"
    lock_path = Path(environment["XDG_RUNTIME_DIR"]) / f"learn-ukrainian-backup.{os.getuid()}.lock"
    with lock_path.open("a+") as lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        result = _run(environment, "retention", "--execute")
    assert result.returncode != 0
    assert "Timed out after 0s waiting for backup lock" in result.stderr
    assert "waiting for lock" in result.stdout
    assert "arg=<snapshots>" not in _log(environment)


@pytest.mark.parametrize("invalid_output", ["bad-id", "jq-failure"])
def test_retention_refuses_invalid_or_unreadable_forget_ids(
    backup_environment: tuple[dict[str, str], Path, Path, Path], tmp_path: Path, invalid_output: str
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    snapshots: list[dict[str, object]] = []
    for day in range(1, 10):
        snapshots += _run_snapshots(f"202609{day:02d}T033000Z-0000000{day}", f"2026-09-{day:02d}", id_byte=str(day))
    _write_snapshots(environment, tmp_path, snapshots)
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    environment["REAL_JQ"] = shutil.which("jq") or ""
    assert environment["REAL_JQ"]
    environment["TEST_INVALID_OUTPUT"] = invalid_output
    _write_executable(
        fake_bin / "jq",
        "#!/bin/bash\n"
        'if [[ "$1" == "-er" && "$2" == ".forget_ids[]" ]]; then\n'
        '  [[ "$TEST_INVALID_OUTPUT" == "bad-id" ]] && { printf "bad-id\\n"; exit 0; }\n'
        "  exit 42\n"
        "fi\n"
        'exec "$REAL_JQ" "$@"\n',
    )

    result = _run(environment, "retention", "--execute")

    assert result.returncode != 0
    assert "forgetting nothing" in result.stderr
    assert _forget_ids(environment) == []
    assert "arg=<prune>" not in _log(environment)


def test_missing_flock_error_includes_macos_install_hint(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    for command in ("dirname", "pwd", "sqlite3", "find", "git", "jq", "realpath", "touch", "uname"):
        executable = shutil.which(command, path=os.environ["PATH"])
        assert executable
        (fake_bin / command).symlink_to(executable)
    environment["PATH"] = str(fake_bin)

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "brew install flock" in result.stderr


def test_password_file_validation_names_variable_not_its_value(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    missing = tmp_path / "fake-secret-password-location"
    environment["RESTIC_PASSWORD_FILE"] = str(missing)

    result = _run(environment, "backup")

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert str(missing) not in output
    assert "RESTIC_PASSWORD_FILE is set but the file does not exist" in output


def test_remote_validation_names_variable_not_the_remote_name(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    environment["LU_BACKUP_REPOSITORY"] = "rclone:fakesecretremote:Projects/test-restic"

    result = _run(environment, "backup")

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "fakesecretremote" not in output
    assert "LU_BACKUP_REPOSITORY" in output
