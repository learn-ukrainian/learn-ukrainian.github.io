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
    subprocess.run(["git", "init", "-q", str(project)], check=True, timeout=30)
    subprocess.run(
        ["git", "-C", str(project), "add", "README.md", ".gitignore"],
        check=True, timeout=30,
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
        check=True, timeout=30,
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
        r"""#!/bin/bash
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
stdin_filename=""
if [[ "${1:-}" == "backup" ]]; then
  previous=""
  for argument in "$@"; do
    [[ "$previous" == "--stdin-filename" ]] && stdin_filename="$argument"
    previous="$argument"
  done
  if [[ -n "$stdin_filename" ]]; then
    mkdir -p "$(dirname "$FAKE_SNAPSHOT_DIR/$stdin_filename")"
    cat > "$FAKE_SNAPSHOT_DIR/$stdin_filename"
  else
    if [[ -n "${FAKE_FILE_PHASE_EXIT:-}" ]]; then
      exit "$FAKE_FILE_PHASE_EXIT"
    fi
    mkdir -p "$FAKE_SNAPSHOT_DIR"
    cp -a "$PWD/.claude" "$PWD/.agent" "$PWD/batch_state" "$PWD/data" "$FAKE_SNAPSHOT_DIR/"
    find "$FAKE_SNAPSHOT_DIR" -type f \
      \( -name '*-wal' -o -name '*-shm' -o -name '*-journal' -o -name '.DS_Store' \) -delete
    find "$FAKE_SNAPSHOT_DIR" -type d \
      \( -name qdrant -o -name __pycache__ -o -name '*-home' \) -prune -exec find '{}' -depth -delete \;
    while IFS= read -r -d '' candidate; do
      if head -c 16 "$candidate" | cmp -s - <(printf 'SQLite format 3\0'); then
        rm "$candidate"
      fi
    done < <(find "$FAKE_SNAPSHOT_DIR" -type f \( -name '*.db' -o -name '*.sqlite*' \) -print0)
  fi
fi
if [[ "${1:-}" == "backup" && -n "${FAKE_DB_RELATIVE:-}" && "$stdin_filename" == "$FAKE_DB_RELATIVE" ]]; then
  rows="$(sqlite3 "file:$FAKE_SNAPSHOT_DIR/$stdin_filename?mode=ro&immutable=1" \
    'SELECT COUNT(*) FROM recovery_probe;')"
  printf 'db_rows=<%s>\n' "$rows" >> "$FAKE_RESTIC_LOG"
fi
if [[ "${1:-}" == "backup" && -n "${FAKE_REQUIRED_RELATIVE:-}" && -f "$FAKE_SNAPSHOT_DIR/$FAKE_REQUIRED_RELATIVE" ]]; then
  printf 'staged_required=<%s>\n' "$FAKE_REQUIRED_RELATIVE" >> "$FAKE_RESTIC_LOG"
fi
if [[ "${1:-}" == "backup" && -n "${FAKE_FORBIDDEN_RELATIVES:-}" && -z "$stdin_filename" ]]; then
  for forbidden in $FAKE_FORBIDDEN_RELATIVES; do
    test ! -e "$FAKE_SNAPSHOT_DIR/$forbidden"
    printf 'staged_excluded=<%s>\n' "$forbidden" >> "$FAKE_RESTIC_LOG"
  done
fi
if [[ "${1:-}" == "backup" && "$stdin_filename" == "BACKUP-RECEIPT.json" ]]; then
  jq -c '{
    status: .receipt_status,
    paths: [.paths[].path],
    agent: (.paths[] | select(.path == ".agent")),
    data: (.paths[] | select(.path == "data"))
  }' \
    "$FAKE_SNAPSHOT_DIR/BACKUP-RECEIPT.json" >> "$FAKE_RESTIC_LOG"
fi
if [[ "${1:-}" == "ls" ]]; then
  find "$FAKE_SNAPSHOT_DIR/data/lexicon/runner-mirror" -type f -printf '%p\n' 2>/dev/null \
    | while IFS= read -r path; do
      relative="${path#"$FAKE_SNAPSHOT_DIR"}"
      jq -cn --arg path "$relative" '{struct_type:"node",type:"file",path:$path}'
    done
  exit 0
fi
if [[ "${1:-}" == "dump" ]]; then
  cat "$FAKE_SNAPSHOT_DIR/${3#/}"
  exit 0
fi
if [[ "${1:-}" == "stats" ]]; then
  printf '{"total_size":%s,"total_file_count":1,"snapshots_count":1}\n' "${FAKE_STATS_TOTAL_SIZE:-1000}"
  exit 0
fi
if [[ "${1:-}" == "restore" && -n "${FAKE_SNAPSHOT_DIR:-}" ]]; then
  dry_run=0
  restore_target=""
  restore_id="${2:-}"
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
    if [[ -d "$FAKE_SNAPSHOT_DIR/by-id/$restore_id" ]]; then
      cp -a "$FAKE_SNAPSHOT_DIR/by-id/$restore_id/." "$restore_target/"
    else
      cp -a "$FAKE_SNAPSHOT_DIR/." "$restore_target/"
    fi
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
        "FAKE_SNAPSHOT_DIR": str(tmp_path / "snapshot"),
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
        text=True, timeout=30,
    )


def _log(environment: dict[str, str]) -> str:
    path = Path(environment["FAKE_RESTIC_LOG"])
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _use_local_restic(
    environment: dict[str, str],
    tmp_path: Path,
) -> None:
    """Route the fake `restic` on PATH to a real local restic repository."""
    real_restic = shutil.which("restic", path=os.environ["PATH"])
    if real_restic is None:
        pytest.skip("restic unavailable")
    repository = tmp_path / "local-restic-repository"
    subprocess.run(
        [real_restic, "-r", str(repository), "init"],
        env={**os.environ, "RESTIC_PASSWORD_FILE": environment["RESTIC_PASSWORD_FILE"]},
        check=True, capture_output=True, text=True, timeout=30,
    )
    environment["TEST_LOCAL_RESTIC_REPOSITORY"] = str(repository)
    environment["TEST_REAL_RESTIC"] = real_restic
    environment["TEST_PEAK_LOG"] = str(tmp_path / "peak.log")
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    _write_executable(
        fake_bin / "restic",
        r"""#!/bin/bash
set -eu
args=()
while [[ "$#" -gt 0 ]]; do
  if [[ "$1" == "--option" && "${2:-}" == "rclone.connections=1" ]]; then
    shift 2
    continue
  fi
  args+=("$1")
  shift
done
if [[ "${args[0]:-}" == "backup" ]]; then
  for argument in "${args[@]}"; do
    if [[ "$argument" == "--stdin" ]]; then
      count="$(find "$LU_BACKUP_TMPDIR" -type f \( -name '*.db' -o -name '*.sqlite*' \) | wc -l)"
      printf '%s\n' "$count" >> "$TEST_PEAK_LOG"
      break
    fi
  done
fi
export RESTIC_REPOSITORY="$TEST_LOCAL_RESTIC_REPOSITORY"
exec "$TEST_REAL_RESTIC" "${args[@]}"
""",
    )


def test_review_homes_are_excluded_but_other_absolute_links_still_fail(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    home = (
        source.parent / "batch_state" / "review-receipts"
        / "attempt-1" / "a1.agy-home"
    )
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
    assert not (Path(environment["FAKE_SNAPSHOT_DIR"]) / "batch_state"
                / "review-receipts" / "attempt-1" / "a1.agy-home").exists()

    other = source.parent / "batch_state" / "unsafe-link"
    other.symlink_to(credential)
    rejected = _run(environment, "doctor")
    assert rejected.returncode != 0
    assert "Absolute symlink is not backup-safe in batch_state" in rejected.stderr


def test_linux_checks_free_space_before_each_database(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    for name in ("a.db", "b.db"):
        with sqlite3.connect(source / name) as connection:
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
    assert "Insufficient staging space for data/b.db" in result.stderr
    assert counter.read_text(encoding="utf-8").strip() == "2"
    assert _log(environment).count("arg=<lu-part-db>") == 1
    assert "arg=<lu-part-complete>" not in _log(environment)


def test_linux_local_restic_round_trip_stages_one_db_at_a_time(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    _write_executable(fake_bin / "cp", "#!/bin/bash\nexit 97\n")
    (source / "ordinary.txt").write_text("recover me\n", encoding="utf-8")
    first_connection = sqlite3.connect(source / "first.db")
    first_connection.execute("PRAGMA journal_mode=WAL")
    first_connection.execute("CREATE TABLE recovery_probe(value TEXT)")
    first_connection.execute("INSERT INTO recovery_probe VALUES ('first')")
    first_connection.commit()
    (source / "first.db").chmod(0o600)
    second = source.parent / "batch_state" / "second.sqlite3"
    with sqlite3.connect(second) as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")
        connection.execute("INSERT INTO recovery_probe VALUES ('second')")
    (source / "orphan.db-journal").write_text("transient", encoding="utf-8")
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
    assert Path(environment["TEST_PEAK_LOG"]).read_text(encoding="utf-8").splitlines() == ["1", "1", "0"]
    assert list(staging.iterdir()) == []
    target = tmp_path / "restored"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")
    assert restored.returncode == 0, restored.stderr
    assert (target / "data" / "ordinary.txt").read_text(encoding="utf-8") == "recover me\n"
    assert not (target / "data" / "first.db-wal").exists()
    assert not (target / "data" / "first.db-shm").exists()
    assert not (target / "data" / "orphan.db-journal").exists()
    assert not (target / "batch_state" / "review-receipts" / "attempt" / "a1.agy-home").exists()
    assert not (target / "batch_state" / "review-receipts" / "attempt-2" / "b2.agy-home").exists()
    for database in (target / "data" / "first.db", target / "batch_state" / "second.sqlite3"):
        with sqlite3.connect(database) as connection:
            assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert connection.execute("SELECT COUNT(*) FROM recovery_probe").fetchone() == (1,)
    assert (target / "data" / "first.db").stat().st_mode & 0o777 == 0o600
    receipt = json.loads((target / "BACKUP-RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["schema_version"] == 2
    assert len(receipt["linux_run"]["databases"]) == 2


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
    assert "refusing to write a durability receipt" in result.stderr
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
    (source / "corrupt.db").write_bytes(b"SQLite format 3\0" + b"corrupt data")

    result = _run(environment, "backup", "--execute")

    assert result.returncode != 0
    assert "Database data/corrupt.db: SQLite online backup failed" in result.stderr
    assert "arg=<lu-part-db>" not in _log(environment)
    assert "arg=<lu-part-complete>" not in _log(environment)
    assert list(staging.iterdir()) == []


def test_non_sqlite_candidate_is_backed_up_as_a_file(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    fence = source.parent / "batch_state" / "comms.sqlite3.pg-fence"
    fence.write_text('{"fence": true}\n', encoding="utf-8")
    environment["FAKE_REQUIRED_RELATIVE"] = "batch_state/comms.sqlite3.pg-fence"

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert "staged_required=<batch_state/comms.sqlite3.pg-fence>" in _log(environment)
    assert "Creating consistent SQLite snapshot: batch_state/comms.sqlite3.pg-fence" not in result.stdout


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read mode-000 paths")
def test_unreadable_file_does_not_skip_database_phase(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    unreadable = source.parent / "batch_state" / "unreadable.txt"
    unreadable.write_text("private\n", encoding="utf-8")
    unreadable.chmod(0)
    with sqlite3.connect(source / "healthy.db") as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")
    environment["FAKE_FILE_PHASE_EXIT"] = "3"

    try:
        result = _run(environment, "backup", "--execute")
    finally:
        unreadable.chmod(0o600)

    assert result.returncode != 0
    assert "batch_state/unreadable.txt" in result.stderr
    assert "File phase: restic backup failed" in result.stderr
    assert "arg=<lu-part-db>" in _log(environment)
    assert "arg=<lu-part-complete>" not in _log(environment)


@pytest.mark.skipif(os.geteuid() == 0, reason="root can traverse mode-000 directories")
def test_unreadable_directory_does_not_skip_database_phase(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    unreadable = source.parent / "batch_state" / "unreadable-dir"
    unreadable.mkdir()
    (unreadable / "hidden.txt").write_text("private\n", encoding="utf-8")
    with sqlite3.connect(source / "healthy.db") as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")
    unreadable.chmod(0)

    try:
        result = _run(environment, "backup", "--execute")
    finally:
        unreadable.chmod(0o700)
        snapshot_copy = Path(environment["FAKE_SNAPSHOT_DIR"]) / "batch_state" / unreadable.name
        if snapshot_copy.exists():
            snapshot_copy.chmod(0o700)

    assert result.returncode != 0
    assert "Backup run " in result.stderr
    assert "Unreadable paths:" in result.stderr
    assert "batch_state/unreadable-dir" in result.stderr
    assert "arg=<--stdin-filename> arg=<data/healthy.db>" in _log(environment)
    assert "arg=<lu-part-complete>" not in _log(environment)


def test_corrupt_database_does_not_skip_later_databases(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    (source / "corrupt.db").write_bytes(b"SQLite format 3\0" + b"corrupt data")
    with sqlite3.connect(source / "healthy.db") as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")

    result = _run(environment, "backup", "--execute")

    assert result.returncode != 0
    assert "Database data/corrupt.db: SQLite online backup failed" in result.stderr
    assert "arg=<--stdin-filename> arg=<data/healthy.db>" in _log(environment)
    assert "arg=<lu-part-complete>" not in _log(environment)


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


def test_find_permission_error_keeps_reported_paths_and_database_phase(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    with sqlite3.connect(source / "healthy.db") as connection:
        connection.execute("CREATE TABLE recovery_probe(value TEXT)")
    real_find = shutil.which("find", path=os.environ["PATH"])
    assert real_find is not None
    environment["REAL_FIND"] = real_find
    environment["FAKE_FIND_ROOT"] = str(source.parent / "batch_state")
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
    assert str(source.parent / "batch_state" / "already-found.txt") in doctor.stderr
    assert str(source.parent / "batch_state" / "denied-dir") in doctor.stderr
    assert run.returncode != 0
    assert "batch_state/already-found.txt" in run.stderr
    assert "batch_state/denied-dir" in run.stderr
    assert "arg=<--stdin-filename> arg=<data/healthy.db>" in _log(environment)
    assert "arg=<lu-part-complete>" not in _log(environment)


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


def test_backup_fails_closed_for_dangling_non_legacy_symlink_in_source(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    (source / "broken-link.txt").symlink_to("missing-dir/missing.txt")

    result = _run(environment, "backup")
    assert result.returncode != 0
    assert "Broken symlink in backup source: broken-link.txt -> missing-dir/missing.txt" in result.stderr


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


def test_restore_refuses_filesystem_root_as_project_overlap(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, _source, _staging, _legacy = backup_environment

    result = _run(environment, "restore", "latest", "--to", "/")

    assert result.returncode != 0
    assert "Restore target must be outside the project checkout" in result.stderr
    assert "arg=<restore>" not in _log(environment)


MANIFEST_ID = "0" * 64
BASE_ID = "b" * 64
ATLAS_ID = "a" * 64
OTHER_ID = "c" * 64
GIB = 1024**3


def _write_fake_run(environment: dict[str, str]) -> Path:
    """Publish a schema-2 run (manifest, base, two databases) in the fake repository."""
    snapshot = Path(environment["FAKE_SNAPSHOT_DIR"])
    databases = {"data/atlas.db": ATLAS_ID, "data/other.db": OTHER_ID}
    for relative, snapshot_id in databases.items():
        database = snapshot / "by-id" / snapshot_id / relative
        database.parent.mkdir(parents=True)
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE recovery_probe(value TEXT)")
    (snapshot / "by-id" / BASE_ID / "data").mkdir(parents=True)
    (snapshot / "by-id" / BASE_ID / "data" / "notes.txt").write_text("base\n", encoding="utf-8")
    receipt = {
        "schema_version": 2,
        "linux_run": {
            "run_id": "run-1",
            "base_snapshot_id": BASE_ID,
            "databases": [
                {"path": path, "snapshot_id": snapshot_id, "mode": "600"}
                for path, snapshot_id in databases.items()
            ],
        },
    }
    (snapshot / "BACKUP-RECEIPT.json").write_text(json.dumps(receipt), encoding="utf-8")
    (snapshot / "by-id" / MANIFEST_ID).mkdir(parents=True)
    shutil.copy(snapshot / "BACKUP-RECEIPT.json", snapshot / "by-id" / MANIFEST_ID)
    return snapshot


def _fake_free_space(environment: dict[str, str], available_bytes: int) -> None:
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    _write_executable(
        fake_bin / "df",
        "#!/bin/bash\n"
        "printf '%s\\n' 'Filesystem 1024-blocks Used Available Capacity Mounted on'\n"
        f"printf 'testfs 8388608 0 %s 0%% /scratch\\n' {available_bytes // 1024}\n",
    )


def _restore_ids(environment: dict[str, str]) -> list[str]:
    return [
        line.split("arg=<restore> arg=<", 1)[1].split(">", 1)[0]
        for line in _log(environment).splitlines()
        if "arg=<restore>" in line
    ]


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

    environment["LU_BACKUP_RESTORE_MARGIN_PERCENT"] = "ten"
    invalid = _run(environment, "restore", MANIFEST_ID, "--to", str(target))
    assert invalid.returncode != 0
    assert "LU_BACKUP_RESTORE_MARGIN_PERCENT" in invalid.stderr


def test_restore_path_restores_one_database_snapshot(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    _write_fake_run(environment)
    _fake_free_space(environment, 50 * GIB)
    target = tmp_path / "one-database"

    preview = _run(
        environment, "restore", MANIFEST_ID, "--to", str(target), "--path", "data/atlas.db",
    )
    assert preview.returncode == 0, preview.stderr
    assert "Restore preview only" in preview.stdout
    assert not target.exists()

    result = _run(
        environment, "restore", MANIFEST_ID, "--to", str(target),
        "--path", "data/atlas.db", "--execute",
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
        environment, "restore", MANIFEST_ID, "--to", str(target),
        "--path", "data/atlas.db", "--execute",
    )
    assert result.returncode != 0
    assert "Insufficient free space" in result.stderr
    assert _restore_ids(environment) == []

    for unsafe in ("/etc/passwd", "../data/atlas.db", "data/../x", "data/*.db", ""):
        rejected = _run(
            environment, "restore", MANIFEST_ID, "--to", str(target), "--path", unsafe,
        )
        assert rejected.returncode != 0, unsafe
        assert "--path" in rejected.stderr
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
        environment, "restore", "latest", "--to", str(database_target),
        "--path", "data/first.db", "--execute",
    )
    assert database.returncode == 0, database.stderr
    assert sorted(path.relative_to(database_target).as_posix()
                  for path in database_target.rglob("*") if path.is_file()) == ["data/first.db"]

    file_target = tmp_path / "restored-file"
    plain = _run(
        environment, "restore", "latest", "--to", str(file_target),
        "--path", "data/ordinary.txt", "--execute",
    )
    assert plain.returncode == 0, plain.stderr
    assert sorted(path.relative_to(file_target).as_posix()
                  for path in file_target.rglob("*") if path.is_file()) == ["data/ordinary.txt"]

    absent_target = tmp_path / "restored-absent"
    absent = _run(
        environment, "restore", "latest", "--to", str(absent_target),
        "--path", "data/no-such-file.txt", "--execute",
    )
    assert absent.returncode != 0
    assert "Nothing at --path" in absent.stderr
    assert not absent_target.exists()


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
