"""Tests for scripts/orchestration/run_scheduled_backup.sh (last-run.json writer)."""

from __future__ import annotations

import json
import os
import shutil
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
    environment = {key: value for key, value in os.environ.items() if not key.startswith(("RESTIC_", "LU_BACKUP_"))}
    environment.update(
        {
            "PATH": f"{fake_bin}:{environment['PATH']}",
            "HOME": str(home),
            "LU_BACKUP_PROJECT_ROOT": str(project),
            "TMPDIR": str(tmp_path),
        }
    )
    return environment, project, fake_bin


def _run_wrapper(environment: dict[str, str], *arguments: str) -> subprocess.CompletedProcess[str]:
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


def test_shell_env_file_is_expanded_and_exported_to_backup_tools(
    writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path
) -> None:
    environment, _project, fake_bin = writer_environment
    env_file = tmp_path / "backup.env"
    env_file.write_text(
        'export OTHER="rclone:fake:Projects/test"\n'
        'export RESTIC_REPOSITORY="${OTHER}"\n'
        'export LU_BACKUP_REPOSITORY="$RESTIC_REPOSITORY"\n'
        'export RCLONE_CONFIG="$HOME/.config/rclone/rclone.conf"\n'
        'export LU_BACKUP_LAST_RUN="${TEST_RECEIPT}"\n',
        encoding="utf-8",
    )
    env_file.chmod(0o600)
    stub_log = tmp_path / "stub.log"
    backup = tmp_path / "backup.sh"
    _write_executable(
        backup,
        '#!/bin/bash\nrestic backup\nrclone lsd\n'
        "printf '%s\\n' '==> Linux backup run 20260926T033000Z-test complete;'\n",
    )
    _fake_restic(
        fake_bin,
        '#!/bin/bash\nprintf "restic:%s:%s\\n" "$RESTIC_REPOSITORY" "$RCLONE_CONFIG" >> "$STUB_LOG"\n'
        'if [[ "$1" == snapshots ]]; then printf "[]\\n"; fi\n',
    )
    _write_executable(
        fake_bin / "rclone",
        '#!/bin/bash\nprintf "rclone:%s:%s\\n" "$RESTIC_REPOSITORY" "$RCLONE_CONFIG" >> "$STUB_LOG"\n',
    )
    environment.update({
        "LU_BACKUP_ENV_FILE": str(env_file),
        "LU_BACKUP_SCRIPT": str(backup),
        "TEST_RECEIPT": str(tmp_path / "last-run.json"),
        "STUB_LOG": str(stub_log),
    })

    result = _run_wrapper(environment)

    assert result.returncode == 0, result.stderr
    lines = stub_log.read_text(encoding="utf-8").splitlines()
    expected = f"rclone:fake:Projects/test:{environment['HOME']}/.config/rclone/rclone.conf"
    assert f"restic:{expected}" in lines
    assert f"rclone:{expected}" in lines
    assert json.loads(Path(environment["TEST_RECEIPT"]).read_text(encoding="utf-8"))["exit_status"] == 0


@pytest.mark.parametrize(
    "unsafe", ["missing", "group_writable", "world_writable", "wrong_owner", "symlink", "loose_parent"]
)
def test_unsafe_shell_env_file_fails_closed_and_records_failure(
    writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path, unsafe: str
) -> None:
    environment, _project, fake_bin = writer_environment
    if unsafe == "wrong_owner":
        if os.geteuid() == 0:
            pytest.skip("requires a non-root test user")
        env_file = Path("/etc/hosts")  # regular, root-owned; never read by the test
        if not env_file.is_file() or env_file.stat().st_uid == os.geteuid():
            pytest.skip("no other-owned regular fixture")
    else:
        parent = tmp_path / "env-dir" if unsafe == "loose_parent" else tmp_path
        parent.mkdir(exist_ok=True)
        env_file = parent / "backup.env"
        if unsafe != "missing":
            target = tmp_path / "real-backup.env" if unsafe == "symlink" else env_file
            target.write_text('export LU_BACKUP_REPOSITORY="unsafe"\n', encoding="utf-8")
            target.chmod(0o620 if unsafe == "group_writable" else 0o602 if unsafe == "world_writable" else 0o600)
            if unsafe == "symlink":
                env_file.symlink_to(target)
            if unsafe == "loose_parent":
                parent.chmod(0o770)
    sentinel = tmp_path / "backup-invoked"
    backup = tmp_path / "backup.sh"
    _write_executable(backup, f'#!/bin/bash\ntouch "{sentinel}"\n')
    _fake_restic(fake_bin, f'#!/bin/bash\ntouch "{sentinel}"\n')
    receipt = tmp_path / "last-run.json"
    receipt.write_text('{"exit_status":0}\n', encoding="utf-8")
    environment.update({
        "LU_BACKUP_ENV_FILE": str(env_file),
        "LU_BACKUP_SCRIPT": str(backup),
        "LU_BACKUP_LAST_RUN": str(receipt),
    })

    result = _run_wrapper(environment)

    assert result.returncode == 78
    assert "LU_BACKUP_ENV_FILE" in result.stderr
    assert len(result.stderr.splitlines()) == 1
    assert not sentinel.exists()
    assert json.loads(receipt.read_text(encoding="utf-8"))["exit_status"] == 78


@pytest.mark.parametrize(
    "bad_line",
    [
        "export RESTIC_REPOSITORY=rclone:gd:SECRETREPO)x",
        "export RESTIC_REPOSITORY=rclone:gd:SECRETREPO bad-SECRETREPO",
    ],
)
def test_env_source_errors_never_echo_values(
    writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path, bad_line: str
) -> None:
    environment, _project, fake_bin = writer_environment
    env_file = tmp_path / "backup.env"
    env_file.write_text(f"{bad_line}\n", encoding="utf-8")
    env_file.chmod(0o600)
    sentinel = tmp_path / "backup-invoked"
    backup = tmp_path / "backup.sh"
    _write_executable(backup, f'#!/bin/bash\ntouch "{sentinel}"\n')
    _fake_restic(fake_bin, f'#!/bin/bash\ntouch "{sentinel}"\n')
    receipt = tmp_path / "last-run.json"
    environment.update({
        "LU_BACKUP_ENV_FILE": str(env_file),
        "LU_BACKUP_SCRIPT": str(backup),
        "LU_BACKUP_LAST_RUN": str(receipt),
    })

    result = _run_wrapper(environment)

    assert result.returncode == 78
    assert result.stdout == ""
    assert result.stderr == "scheduled-backup: LU_BACKUP_ENV_FILE could not be sourced\n"
    assert not sentinel.exists()
    receipt_text = receipt.read_text(encoding="utf-8")
    assert "SECRETREPO" not in result.stdout + result.stderr + receipt_text
    assert "bad-SECRETREPO" not in result.stdout + result.stderr + receipt_text
    assert json.loads(receipt_text)["exit_status"] == 78


def test_retention_sources_shell_env_file(
    writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path
) -> None:
    environment, _project, _fake_bin = writer_environment
    env_file = tmp_path / "backup.env"
    env_file.write_text('export OTHER="retention-value"\nexport CHECK="$HOME/${OTHER}"\n', encoding="utf-8")
    env_file.chmod(0o600)
    backup = tmp_path / "backup.sh"
    _write_executable(backup, '#!/bin/bash\nprintf "received:%s\\n" "$CHECK"\n')
    environment.update({"LU_BACKUP_ENV_FILE": str(env_file), "LU_BACKUP_SCRIPT": str(backup)})

    result = _run_wrapper(environment, "retention")

    assert result.returncode == 0, result.stderr
    assert f"received:{environment['HOME']}/retention-value" in result.stdout


def test_record_writes_success_receipt(writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path) -> None:
    environment, project, fake_bin = writer_environment
    environment["LU_BACKUP_REPOSITORY"] = "rclone:testdrive:Projects/test-restic"
    environment["LU_BACKUP_HOST"] = "test-host"
    log = tmp_path / "backup.log"
    log.write_text(SUCCESS_LOG, encoding="utf-8")
    _fake_restic(
        fake_bin,
        "#!/bin/bash\n"
        '[[ "$RESTIC_REPOSITORY" == "rclone:testdrive:Projects/test-restic" ]] || exit 1\n'
        '[[ " $* " == *" --host test-host "* ]] || exit 1\n'
        '[[ " $* " == *" --tag learn-ukrainian-data "* ]] || exit 1\n'
        'printf \'%s\\n\' \'[{"id":"one"},{"id":"two"}]\'\n',
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
    receipt = json.loads((project / "batch_state" / "backups" / "last-run.json").read_text(encoding="utf-8"))
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


def test_run_fails_when_tee_fails_even_if_backup_succeeds(
    writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path
) -> None:
    environment, _project, fake_bin = writer_environment
    last_run = tmp_path / "last-run.json"
    fake_backup = tmp_path / "fake-backup-data.sh"
    _write_executable(
        fake_backup,
        """#!/bin/bash
printf '%s\n' '==> Linux backup run 20260926T033000Z-ab12cd34 complete; receipt snapshot cc.'
exit 0
""",
    )
    _fake_restic(fake_bin, "#!/bin/bash\nexit 1\n")
    _write_executable(
        fake_bin / "tee",
        "#!/bin/bash\ncat >/dev/null || true\nexit 1\n",
    )
    environment["LU_BACKUP_SCRIPT"] = str(fake_backup)
    environment["LU_BACKUP_LAST_RUN"] = str(last_run)

    result = _run_wrapper(environment)

    assert result.returncode != 0
    assert "could not capture the backup log" in result.stderr
    # A failed capture makes the scheduled run a failure in the receipt too.
    receipt = json.loads(last_run.read_text(encoding="utf-8"))
    assert receipt["exit_status"] != 0


def test_run_fails_when_last_run_receipt_cannot_be_written(
    writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path
) -> None:
    environment, _project, fake_bin = writer_environment
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory\n", encoding="utf-8")
    fake_backup = tmp_path / "fake-backup-data.sh"
    _write_executable(
        fake_backup,
        """#!/bin/bash
printf '%s\n' '==> Linux backup run 20260926T033000Z-ab12cd34 complete; receipt snapshot cc.'
exit 0
""",
    )
    _fake_restic(fake_bin, "#!/bin/bash\nexit 1\n")
    environment["LU_BACKUP_SCRIPT"] = str(fake_backup)
    # mkdir -p cannot create a directory below a regular file.
    environment["LU_BACKUP_LAST_RUN"] = str(blocker / "last-run.json")

    result = _run_wrapper(environment)

    assert result.returncode != 0
    assert "could not write the last-run receipt" in result.stderr


@pytest.mark.parametrize("failed_command", ["jq", "mv"])
def test_run_fails_when_status_write_command_fails(
    writer_environment: tuple[dict[str, str], Path, Path],
    tmp_path: Path,
    failed_command: str,
) -> None:
    environment, _project, fake_bin = writer_environment
    last_run = tmp_path / "last-run.json"
    fake_backup = tmp_path / "fake-backup-data.sh"
    _write_executable(fake_backup, "#!/bin/bash\nprintf '%s\\n' 'backup succeeded'\n")
    _fake_restic(fake_bin, "#!/bin/bash\nexit 1\n")
    if failed_command == "jq":
        environment["REAL_JQ"] = shutil.which("jq") or ""
        assert environment["REAL_JQ"]
        _write_executable(
            fake_bin / "jq",
            '#!/bin/bash\nif [[ "$1" == "-n" ]]; then exit 42; fi\nexec "$REAL_JQ" "$@"\n',
        )
    else:
        _write_executable(fake_bin / "mv", "#!/bin/bash\nexit 42\n")
    environment["LU_BACKUP_SCRIPT"] = str(fake_backup)
    environment["LU_BACKUP_LAST_RUN"] = str(last_run)

    result = _run_wrapper(environment)

    assert result.returncode != 0
    assert "could not write the last-run receipt" in result.stderr
    assert not last_run.exists()


def test_run_redacts_repository_and_password_path_before_journal_and_receipt(
    writer_environment: tuple[dict[str, str], Path, Path],
    tmp_path: Path,
) -> None:
    environment, _project, fake_bin = writer_environment
    repository = "rclone:review.remote:/var/tmp/lu/nonexistent[review]"
    password_file = "/tmp/secret[review].file"
    last_run = tmp_path / "last-run.json"
    fake_backup = tmp_path / "fake-backup-data.sh"
    _write_executable(
        fake_backup,
        "#!/bin/bash\n"
        'printf "Fatal: repository does not exist: %s\\n" "$LU_BACKUP_REPOSITORY" >&2\n'
        'printf "Password file: %s\\n" "$RESTIC_PASSWORD_FILE"\n'
        'printf "%s\\n" "Backup run 20260926T033000Z-ab12cd34 failed:"\n'
        "exit 3\n",
    )
    _fake_restic(fake_bin, "#!/bin/bash\nexit 1\n")
    environment["REAL_JQ"] = shutil.which("jq") or ""
    assert environment["REAL_JQ"]
    environment["JQ_ARGV_LOG"] = str(tmp_path / "jq-argv.log")
    _write_executable(
        fake_bin / "jq",
        '#!/bin/bash\nprintf "<%s>" "$@" >> "$JQ_ARGV_LOG"\nprintf "\\n" >> "$JQ_ARGV_LOG"\nexec "$REAL_JQ" "$@"\n',
    )
    environment.update(
        {
            "LU_BACKUP_SCRIPT": str(fake_backup),
            "LU_BACKUP_LAST_RUN": str(last_run),
            "LU_BACKUP_REPOSITORY": repository,
            "RESTIC_PASSWORD_FILE": password_file,
        }
    )

    result = _run_wrapper(environment)

    assert result.returncode == 3
    journal_stream = result.stdout + result.stderr
    assert repository not in journal_stream
    assert repository.removeprefix("rclone:") not in journal_stream
    assert password_file not in journal_stream
    assert "<repository>" in journal_stream
    assert "<password-file>" in journal_stream
    receipt_text = last_run.read_text(encoding="utf-8")
    assert repository not in receipt_text
    assert password_file not in receipt_text
    assert json.loads(receipt_text)["exit_status"] == 3
    argv_text = Path(environment["JQ_ARGV_LOG"]).read_text(encoding="utf-8")
    assert repository not in argv_text
    assert password_file not in argv_text


def test_retention_mode_redacts_output_and_preserves_failure_status(
    writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path
) -> None:
    environment, _project, _fake_bin = writer_environment
    repository = "rclone:testdrive:Projects/private"
    password_file = str(tmp_path / "private-password")
    fake_backup = tmp_path / "fake-backup-data.sh"
    _write_executable(
        fake_backup,
        '#!/bin/bash\nprintf "%s\\n" "$LU_BACKUP_REPOSITORY" "${LU_BACKUP_REPOSITORY#rclone:}" "$RESTIC_PASSWORD_FILE"\nexit 7\n',
    )
    environment.update(
        {
            "LU_BACKUP_SCRIPT": str(fake_backup),
            "LU_BACKUP_REPOSITORY": repository,
            "RESTIC_PASSWORD_FILE": password_file,
        }
    )

    result = _run_wrapper(environment, "retention")

    assert result.returncode == 7
    assert repository not in result.stdout + result.stderr
    assert repository.removeprefix("rclone:") not in result.stdout + result.stderr
    assert password_file not in result.stdout + result.stderr
    assert "<repository>" in result.stdout
    assert "<password-file>" in result.stdout


@pytest.mark.parametrize("failure", ["missing-jq", "missing-script", "mktemp", "tmpdir"])
def test_early_failure_invalidates_previous_success_receipt(
    writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path, failure: str
) -> None:
    environment, _project, fake_bin = writer_environment
    last_run = tmp_path / "last-run.json"
    last_run.write_text('{"exit_status":0}\n', encoding="utf-8")
    environment["LU_BACKUP_LAST_RUN"] = str(last_run)
    if failure == "missing-jq":
        for command in ("dirname", "rm"):
            executable = shutil.which(command, path=os.environ["PATH"])
            assert executable
            (fake_bin / command).symlink_to(executable)
        environment["PATH"] = str(fake_bin)
    elif failure == "missing-script":
        environment["LU_BACKUP_SCRIPT"] = str(tmp_path / "missing.sh")
    else:
        script = tmp_path / "backup.sh"
        _write_executable(script, "#!/bin/bash\nexit 0\n")
        environment["LU_BACKUP_SCRIPT"] = str(script)
        if failure == "mktemp":
            _write_executable(fake_bin / "mktemp", "#!/bin/bash\nexit 42\n")
        else:
            blocker = tmp_path / "blocker"
            blocker.write_text("file\n", encoding="utf-8")
            environment["LU_BACKUP_TMPDIR"] = str(blocker / "staging")

    result = _run_wrapper(environment)

    assert result.returncode != 0
    assert not last_run.exists()


def test_invalid_new_receipt_does_not_replace_existing_receipt(
    writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path
) -> None:
    environment, _project, fake_bin = writer_environment
    old_receipt = tmp_path / "last-run.json"
    old_receipt.write_text('{"exit_status":7}\n', encoding="utf-8")
    log = tmp_path / "backup.log"
    log.write_text(FAILURE_LOG, encoding="utf-8")
    environment["REAL_JQ"] = shutil.which("jq") or ""
    assert environment["REAL_JQ"]
    _write_executable(
        fake_bin / "jq",
        '#!/bin/bash\nif [[ "$1" == "-n" ]]; then printf "truncated"; exit 0; fi\nexec "$REAL_JQ" "$@"\n',
    )

    result = _run_wrapper(
        environment, "record", "--status", "1", "--started", "2026-09-26T03:30:00Z",
        "--log", str(log), "--last-run", str(old_receipt),
    )

    assert result.returncode != 0
    assert old_receipt.read_text(encoding="utf-8") == '{"exit_status":7}\n'
    assert not list(tmp_path.glob("last-run.json.tmp.*"))


def test_empty_primary_repository_and_bare_remote_path_are_redacted(
    writer_environment: tuple[dict[str, str], Path, Path], tmp_path: Path
) -> None:
    environment, _project, _fake_bin = writer_environment
    repository = "rclone:testdrive:Projects/private-folder"
    script = tmp_path / "backup.sh"
    _write_executable(
        script,
        "#!/bin/bash\n"
        'printf "%s\\n" "$RESTIC_REPOSITORY" "Google drive root \'Projects/private-folder\'"\n'
        "exit 4\n",
    )
    environment.update({
        "LU_BACKUP_SCRIPT": str(script),
        "LU_BACKUP_LAST_RUN": str(tmp_path / "last-run.json"),
        "LU_BACKUP_REPOSITORY": "",
        "RESTIC_REPOSITORY": repository,
    })

    result = _run_wrapper(environment)

    assert result.returncode == 4
    assert repository not in result.stdout + result.stderr
    assert "Projects/private-folder" not in result.stdout + result.stderr
    assert "Google drive root '<repository>'" in result.stdout
