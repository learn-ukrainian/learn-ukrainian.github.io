"""Safety and recovery tests for scripts/backup-data.sh."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path

import pytest

from scripts.lexicon.runner.durable_mirror import DurableMirrorError, require_durable

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "backup-data.sh"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o700)


@pytest.fixture
def backup_environment(tmp_path: Path) -> tuple[dict[str, str], Path, Path, Path]:
    fake_bin = tmp_path / "bin"
    project = tmp_path / "project"
    source = project / "data"
    staging = tmp_path / "staging"
    legacy = tmp_path / "legacy"
    password_file = tmp_path / "restic-password"
    log = tmp_path / "restic.log"

    for directory in (
        fake_bin,
        source,
        project / ".claude" / "atlas-epic",
        project / ".agent",
        project / "batch_state",
        staging,
        legacy,
        tmp_path / "home",
    ):
        directory.mkdir(parents=True)
    (project / "README.md").write_text("fixture\n", encoding="utf-8")
    (project / ".gitignore").write_text(
        ".agent\n.claude\nbatch_state\n",
        encoding="utf-8",
    )
    (project / ".claude" / "atlas-epic" / "HANDOFF.md").write_text(
        "recover me\n",
        encoding="utf-8",
    )
    (project / "batch_state" / "state.txt").write_text(
        "recover me too\n",
        encoding="utf-8",
    )
    (project / ".agent" / "recovery-state.json").write_text(
        '{"schema_version": 1}\n',
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q", str(project)], check=True)
    subprocess.run(
        ["git", "-C", str(project), "add", "README.md", ".gitignore"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(project),
            "-c",
            "user.name=Backup Test",
            "-c",
            "user.email=backup-test@example.invalid",
            "commit",
            "-qm",
            "test fixture",
        ],
        check=True,
    )
    password_file.write_text("test-only-password\n", encoding="utf-8")
    password_file.chmod(0o600)

    _write_executable(
        fake_bin / "rclone",
        """#!/bin/bash
set -eu
if [[ "${1:-}" == "listremotes" ]]; then
  printf '%s\n' 'testdrive:'
  exit 0
fi
exit 64
""",
    )
    _write_executable(
        fake_bin / "restic",
        """#!/bin/bash
set -eu
if [[ "${1:-}" == "version" ]]; then
  printf '%s\n' 'restic 0.19.1 compiled with go1.24.0 on darwin/arm64'
  exit 0
fi
{
  printf 'cwd=<%s>' "$PWD"
  printf ' arg=<%s>' "$@"
  printf '\n'
} >> "$FAKE_RESTIC_LOG"
if [[ "${1:-}" == "cat" && "${FAKE_REPOSITORY_STATE:-initialized}" != "initialized" ]]; then
  exit 1
fi
if [[ "${1:-}" == "cat" && -z "${RESTIC_REPOSITORY:-}" ]]; then
  exit 78
fi
if [[ "${1:-}" == "backup" && -n "${FAKE_DB_RELATIVE:-}" ]]; then
  rows="$(sqlite3 "file:$PWD/$FAKE_DB_RELATIVE?mode=ro&immutable=1" \
    'SELECT COUNT(*) FROM recovery_probe;')"
  printf 'db_rows=<%s>\n' "$rows" >> "$FAKE_RESTIC_LOG"
fi
if [[ "${1:-}" == "backup" && -n "${FAKE_REQUIRED_RELATIVE:-}" ]]; then
  test -f "$PWD/$FAKE_REQUIRED_RELATIVE"
  printf 'staged_required=<%s>\n' "$FAKE_REQUIRED_RELATIVE" \
    >> "$FAKE_RESTIC_LOG"
fi
if [[ "${1:-}" == "backup" && -n "${FAKE_FORBIDDEN_RELATIVES:-}" ]]; then
  for forbidden in $FAKE_FORBIDDEN_RELATIVES; do
    test ! -e "$PWD/$forbidden"
    printf 'staged_excluded=<%s>\n' "$forbidden" >> "$FAKE_RESTIC_LOG"
  done
fi
if [[ "${1:-}" == "backup" && -f "$PWD/BACKUP-RECEIPT.json" ]]; then
  jq -c '{
    status: .receipt_status,
    paths: [.paths[].path],
    agent: (.paths[] | select(.path == ".agent")),
    data: (.paths[] | select(.path == "data"))
  }' \
    "$PWD/BACKUP-RECEIPT.json" >> "$FAKE_RESTIC_LOG"
fi
if [[ "${1:-}" == "backup" && -n "${FAKE_SNAPSHOT_DIR:-}" ]]; then
  mkdir -p "$FAKE_SNAPSHOT_DIR"
  cp -a "$PWD/." "$FAKE_SNAPSHOT_DIR/"
fi
if [[ "${1:-}" == "restore" && -n "${FAKE_SNAPSHOT_DIR:-}" ]]; then
  dry_run=0
  restore_target=""
  shift
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run) dry_run=1 ;;
      --target)
        shift
        restore_target="${1:-}"
        ;;
    esac
    shift
  done
  if [[ "$dry_run" == 0 ]]; then
    test -n "$restore_target"
    mkdir -p "$restore_target"
    cp -a "$FAKE_SNAPSHOT_DIR/." "$restore_target/"
  fi
fi
if [[ "${1:-}" == "backup" && -n "${FAKE_MUTATED_LIVE_STATE_SOURCE:-}" ]]; then
  cp "$FAKE_MUTATED_LIVE_STATE_SOURCE" "$FAKE_MUTATED_LIVE_STATE_DESTINATION"
  cp "$FAKE_MUTATED_LIVE_MANIFEST_SOURCE" "$FAKE_MUTATED_LIVE_MANIFEST_DESTINATION"
fi
if [[ "${1:-}" == "backup" ]]; then
  for argument in "$@"; do
    if [[ "$argument" == "--json" ]]; then
      printf '%s\n' '{"message_type":"summary","snapshot_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}'
      break
    fi
  done
fi
if [[ "${1:-}" == "check" && "${FAKE_RESTIC_CHECK_FAIL:-0}" == "1" ]]; then
  exit 70
fi
exit 0
""",
    )

    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "HOME": str(tmp_path / "home"),
        "LU_BACKUP_REPOSITORY": "rclone:testdrive:Projects/test-restic",
        "RESTIC_PASSWORD_FILE": str(password_file),
        "LU_BACKUP_PROJECT_ROOT": str(project),
        "LU_BACKUP_TMPDIR": str(staging),
        "LU_BACKUP_LEGACY_DIR": str(legacy),
        "FAKE_RESTIC_LOG": str(log),
        "FAKE_REPOSITORY_STATE": "initialized",
    }
    return environment, source, staging, legacy


def _run(
    environment: dict[str, str],
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(SCRIPT), *arguments],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
    )


def _log(environment: dict[str, str]) -> str:
    path = Path(environment["FAKE_RESTIC_LOG"])
    return path.read_text(encoding="utf-8") if path.exists() else ""


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


def test_execute_stages_a_consistent_wal_database_and_cleans_up(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    database = source / "live.db"
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
        environment["FAKE_DB_RELATIVE"] = "data/live.db"
        environment["FAKE_REQUIRED_RELATIVE"] = ".claude/atlas-epic/HANDOFF.md"

        result = _run(environment, "backup", "--execute")
    finally:
        connection.close()

    assert result.returncode == 0, result.stderr
    assert "Creating consistent SQLite snapshot: data/live.db" in result.stdout
    assert "db_rows=<2>" in _log(environment)
    assert "staged_required=<.claude/atlas-epic/HANDOFF.md>" in _log(environment)
    assert '"status":"prepared-before-snapshot-write"' in _log(environment)
    assert '".claude/atlas-epic"' in _log(environment)
    assert '".agent"' in _log(environment)
    assert '"batch_state"' in _log(environment)
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
    assert "refusing to write a receipt for content not backed up" in result.stderr
    assert not (mirror.parent / "RESTIC-GATE-RECEIPT.json").exists()
    with pytest.raises(DurableMirrorError, match="no restic gate receipt"):
        require_durable(mirror)


def test_execute_snapshots_checkpointed_wal_database_without_sidecars(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    database = source / "checkpointed.db"
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("CREATE TABLE recovery_probe (value TEXT NOT NULL)")
    connection.execute("INSERT INTO recovery_probe VALUES ('checkpointed')")
    connection.commit()
    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    connection.close()
    assert not database.with_name("checkpointed.db-wal").exists()
    assert not database.with_name("checkpointed.db-shm").exists()
    environment["FAKE_DB_RELATIVE"] = "data/checkpointed.db"
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


def test_execute_rejects_a_corrupt_database_before_upload(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    (source / "corrupt.db").write_bytes(b"not a sqlite database")

    result = _run(environment, "backup", "--execute")

    assert result.returncode != 0
    assert "SQLite online backup failed: data/corrupt.db" in result.stderr
    assert "arg=<backup>" not in _log(environment)
    assert list(staging.iterdir()) == []


def test_receipt_counts_match_post_exclusion_snapshot_contents(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    (source / "qdrant").mkdir()
    (source / "qdrant" / "retired.bin").write_bytes(b"not recoverable")
    (source / "__pycache__").mkdir()
    (source / "__pycache__" / "cache.pyc").write_bytes(b"not recoverable")
    (source / "sidecar.db-wal").write_bytes(b"not recoverable")
    (source / ".DS_Store").write_bytes(b"not recoverable")
    (source / "keep.txt").write_bytes(b"keep\n")
    (source / "keep-wal").write_bytes(b"keep\n")
    environment.update(
        {
            "FAKE_FORBIDDEN_RELATIVES": (
                "data/qdrant data/__pycache__ data/sidecar.db-wal data/.DS_Store"
            ),
            "FAKE_REQUIRED_RELATIVE": "data/keep-wal",
        }
    )

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert '"data":{"path":"data","files":2,"bytes":10}' in _log(environment)
    assert _log(environment).count("staged_excluded=<") == 4
    assert list(staging.iterdir()) == []


def test_execute_refuses_when_full_tree_would_exceed_staging_space(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    (source / "valuable.txt").write_text("sole copy\n", encoding="utf-8")
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
    assert "arg=<backup>" not in _log(environment)


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


def test_execute_snapshots_sqlite3_database_from_batch_state(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    database = (
        source.parent / "batch_state" / "fleet-comms" / "v1" / "comms.sqlite3"
    )
    database.parent.mkdir(parents=True)
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE recovery_probe (value TEXT NOT NULL)")
    connection.execute("INSERT INTO recovery_probe VALUES ('batch')")
    connection.commit()
    connection.close()
    environment["FAKE_DB_RELATIVE"] = "batch_state/fleet-comms/v1/comms.sqlite3"

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert (
        "consistent SQLite snapshot: batch_state/fleet-comms/v1/comms.sqlite3"
        in result.stdout
    )
    assert "db_rows=<1>" in _log(environment)
    assert list(staging.iterdir()) == []


def test_execute_restores_agent_wal_database_without_sidecars(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, staging, _legacy = backup_environment
    database = (
        source.parent
        / ".agent"
        / "session-streams"
        / "v1"
        / "session-streams.sqlite3"
    )
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
    restored_database = (
        restore_target / ".agent" / "session-streams" / "v1" / database.name
    )
    assert not restored_database.with_name(f"{database.name}-wal").exists()
    assert not restored_database.with_name(f"{database.name}-shm").exists()
    with sqlite3.connect(f"file:{restored_database}?mode=ro", uri=True) as restored_connection:
        rows = restored_connection.execute(
            "SELECT value FROM recovery_probe ORDER BY rowid"
        ).fetchall()
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


@pytest.mark.parametrize(
    ("target", "expected_error"),
    [
        ("missing-target", "Broken symlink in .agent"),
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


def test_real_textbooks_directory_is_included(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    textbooks = source / "textbooks"
    textbooks.mkdir()
    (textbooks / "local-source.txt").write_text("preserve\n", encoding="utf-8")
    environment["FAKE_REQUIRED_RELATIVE"] = "data/textbooks/local-source.txt"

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert "staged_required=<data/textbooks/local-source.txt>" in _log(environment)
    assert str(textbooks) not in _log(environment)
    assert list(staging.iterdir()) == []


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


def test_restore_is_a_dry_run_and_refuses_unsafe_targets(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    restore_target = tmp_path / "restore-target"

    preview = _run(environment, "restore", "latest", "--to", str(restore_target))

    assert preview.returncode == 0, preview.stderr
    assert "Restore preview only" in preview.stdout
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


def test_restore_refuses_filesystem_root_as_project_overlap(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment

    result = _run(environment, "restore", "latest", "--to", "/")

    assert result.returncode != 0
    assert "Restore target must be outside the project checkout" in result.stderr
    assert "arg=<restore>" not in _log(environment)


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


def test_doctor_checks_initialized_repository_with_validated_environment(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment

    result = _run(environment, "doctor")

    assert result.returncode == 0, result.stderr
    assert "OK: restic repository is initialized" in result.stdout
    assert "Doctor checks passed." in result.stdout


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
