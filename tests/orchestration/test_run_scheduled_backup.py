"""Tests for scripts/orchestration/run_scheduled_backup.sh (last-run.json writer)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "scripts" / "orchestration" / "run_scheduled_backup.sh"

SUCCESS_LOG = """\
==> Creating consistent SQLite snapshot: data/live.db
{"message_type":"status","percent_done":0.5}
{"message_type":"summary","snapshot_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","data_added":1024}
{"message_type":"summary","snapshot_id":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","data_added":2048}
==> Linux backup run 20260926T033000Z-ab12cd34 complete; receipt snapshot cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc.
"""

FAILURE_LOG = """\
==> Streaming non-database recovery files from the live tree.
Backup run 20260926T033000Z-ab12cd34 failed:
  File phase: restic backup failed
"""


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o700)


@pytest.fixture
def writer_environment(tmp_path: Path) -> tuple[dict[str, str], Path, Path]:
    home = tmp_path / "home"
    home.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("RESTIC_", "LU_BACKUP_"))
    }
    environment.update(
        {
            "PATH": f"{fake_bin}:{environment['PATH']}",
            "HOME": str(home),
            "LU_BACKUP_PROJECT_ROOT": str(project),
            "TMPDIR": str(tmp_path),
        }
    )
    return environment, project, fake_bin


def _run_wrapper(
    environment: dict[str, str], *arguments: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(WRAPPER), *arguments],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        timeout=60,
    )


def _fake_restic(fake_bin: Path, body: str) -> None:
    _write_executable(fake_bin / "restic", body)


def test_record_writes_success_receipt(
    writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path
) -> None:
    environment, project, fake_bin = writer_environment
    log = tmp_path / "backup.log"
    log.write_text(SUCCESS_LOG, encoding="utf-8")
    _fake_restic(
        fake_bin,
        "#!/bin/bash\nprintf '%s\\n' '[{\"id\":\"one\"},{\"id\":\"two\"}]'\n",
    )

    result = _run_wrapper(
        environment,
        "record",
        "--status",
        "0",
        "--started",
        "2026-09-26T03:30:00Z",
        "--finished",
        "2026-09-26T03:54:12Z",
        "--log",
        str(log),
    )

    assert result.returncode == 0, result.stderr
    receipt_path = project / "batch_state" / "backups" / "last-run.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt == {
        "schema_version": 1,
        "started_at_utc": "2026-09-26T03:30:00Z",
        "finished_at_utc": "2026-09-26T03:54:12Z",
        "exit_status": 0,
        "run_id": "20260926T033000Z-ab12cd34",
        "snapshot_count": 2,
        "bytes_added": 3072,
    }
    assert receipt_path.stat().st_mode & 0o777 == 0o600


def test_record_writes_failure_receipt_without_repository(
    writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path
) -> None:
    environment, project, fake_bin = writer_environment
    log = tmp_path / "backup.log"
    log.write_text(FAILURE_LOG, encoding="utf-8")
    _fake_restic(fake_bin, "#!/bin/bash\nexit 1\n")

    result = _run_wrapper(
        environment,
        "record",
        "--status",
        "1",
        "--started",
        "2026-09-26T03:30:00Z",
        "--finished",
        "2026-09-26T03:41:07Z",
        "--log",
        str(log),
    )

    assert result.returncode == 0, result.stderr
    receipt = json.loads(
        (project / "batch_state" / "backups" / "last-run.json").read_text(encoding="utf-8")
    )
    assert receipt["exit_status"] == 1
    assert receipt["run_id"] == "20260926T033000Z-ab12cd34"
    assert receipt["snapshot_count"] is None
    assert receipt["bytes_added"] is None
    assert receipt["started_at_utc"] == "2026-09-26T03:30:00Z"
    assert receipt["finished_at_utc"] == "2026-09-26T03:41:07Z"


def test_run_propagates_backup_status_and_records_receipt(
    writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path
) -> None:
    environment, _project, fake_bin = writer_environment
    last_run = tmp_path / "last-run.json"
    fake_backup = tmp_path / "fake-backup-data.sh"
    _write_executable(
        fake_backup,
        """#!/bin/bash
printf '%s\n' '==> Streaming non-database recovery files from the live tree.'
printf '%s\n' '{"message_type":"summary","snapshot_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","data_added":512}'
printf '%s\n' 'Backup run 20260926T033000Z-ab12cd34 failed:' >&2
exit 3
""",
    )
    _fake_restic(fake_bin, "#!/bin/bash\nexit 1\n")
    environment["LU_BACKUP_SCRIPT"] = str(fake_backup)
    environment["LU_BACKUP_LAST_RUN"] = str(last_run)

    result = _run_wrapper(environment)

    assert result.returncode == 3
    receipt = json.loads(last_run.read_text(encoding="utf-8"))
    assert receipt["exit_status"] == 3
    assert receipt["run_id"] == "20260926T033000Z-ab12cd34"
    assert receipt["bytes_added"] == 512
    assert receipt["snapshot_count"] is None
