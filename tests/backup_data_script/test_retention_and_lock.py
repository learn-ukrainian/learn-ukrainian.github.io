"""Backup lock behaviour and a few fast policy checks."""

from __future__ import annotations

import fcntl
import os
import subprocess
import time
from pathlib import Path

from tests.backup_data_script._support import (
    SCRIPT,
    _log,
    _run,
    _run_snapshots,
    _write_snapshots,
)


def test_backup_and_retention_share_lock_before_listing(
    backup_environment: tuple[dict[str, str], Path, Path, Path], tmp_path: Path
) -> None:
    environment, _source, staging, _legacy = backup_environment
    hold = tmp_path / "backup-held"
    environment["FAKE_BACKUP_HOLD_FILE"] = str(hold)
    _write_snapshots(environment, tmp_path, _run_snapshots("run", "2026-09-26", id_byte="a"))
    backup = subprocess.Popen(
        ["/bin/bash", str(SCRIPT), "backup", "--execute"],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    retention = None
    try:
        deadline = time.monotonic() + 10
        while not hold.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert hold.exists(), backup.communicate(timeout=10)
        retention_environment = {key: value for key, value in environment.items() if key != "LU_BACKUP_TMPDIR"}
        retention = subprocess.Popen(
            ["/bin/bash", str(SCRIPT), "retention", "--execute"],
            env=retention_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(0.2)
        assert "arg=<snapshots>" not in _log(environment)
        assert retention.poll() is None
        hold.with_name(hold.name + ".release").touch()
        backup_output, backup_error = backup.communicate(timeout=30)
        assert backup.returncode == 0, backup_output + backup_error
        retention_output, retention_error = retention.communicate(timeout=30)
        assert retention.returncode == 0, retention_output + retention_error
        assert "arg=<snapshots>" in _log(environment)
        assert not (staging / f"learn-ukrainian-backup.{os.getuid()}.stage").exists()
    finally:
        hold.with_name(hold.name + ".release").touch()
        if backup.poll() is None:
            backup.kill()
            backup.communicate(timeout=10)
        if retention is not None and retention.poll() is None:
            retention.kill()
            retention.communicate(timeout=10)


def test_retention_plans_after_lock_and_closed_fd_releases_it(
    backup_environment: tuple[dict[str, str], Path, Path, Path], tmp_path: Path
) -> None:
    environment, _source, staging, _legacy = backup_environment
    _write_snapshots(environment, tmp_path, "[]\n")
    lock_path = Path(environment["XDG_RUNTIME_DIR"]) / f"learn-ukrainian-backup.{os.getuid()}.lock"
    lock_fd = lock_path.open("a+")
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    stale = staging / f"learn-ukrainian-backup.{os.getuid()}.stage"
    stale.mkdir()
    (stale / "partial").write_text("interrupted", encoding="utf-8")
    process = subprocess.Popen(
        ["/bin/bash", str(SCRIPT), "retention", "--execute"],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(0.2)
        assert "arg=<snapshots>" not in _log(environment)
        _write_snapshots(environment, tmp_path, _run_snapshots("run", "2026-09-26", id_byte="a"))
        lock_fd.close()  # Simulates holder death: the kernel releases the descriptor lock.
        stdout, stderr = process.communicate(timeout=20)
        assert process.returncode == 0, stdout + stderr
        assert "Runs kept: 1" in stdout
        assert not stale.exists()
    finally:
        if not lock_fd.closed:
            lock_fd.close()
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=10)


def test_backup_fails_closed_for_agent_special_file(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    fifo = source.parent / ".agent" / "writer.pipe"
    os.mkfifo(fifo)

    result = _run(environment, "backup")

    assert result.returncode != 0
    assert "Unsupported special file type in .agent: writer.pipe" in result.stderr
    assert "arg=<backup>" not in _log(environment)


def test_symlink_policy_rejects_resolving_legacy_symlink_outside_legacy_dir(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    outside_dir = tmp_path / "outside-legacy"
    outside_dir.mkdir()
    (source / "textbooks").symlink_to(outside_dir)

    result = _run(environment, "backup")
    assert result.returncode != 0
    assert "Known legacy symlink points outside the legacy backup: textbooks ->" in result.stderr


def test_verify_checks_repository_and_rejects_snapshot_arguments(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment

    metadata_check = _run(environment, "verify")

    assert metadata_check.returncode == 0, metadata_check.stderr
    assert "arg=<check>" in _log(environment)
    assert "arg=<--read-data>" not in _log(environment)

    Path(environment["FAKE_RESTIC_LOG"]).write_text("", encoding="utf-8")
    data_check = _run(environment, "verify", "--read-data")

    assert data_check.returncode == 0, data_check.stderr
    assert "arg=<check> arg=<--read-data>" in _log(environment)

    Path(environment["FAKE_RESTIC_LOG"]).write_text("", encoding="utf-8")
    rejected = _run(environment, "verify", "latest")

    assert rejected.returncode != 0
    assert "does not accept snapshot IDs" in rejected.stderr
    assert _log(environment) == ""
