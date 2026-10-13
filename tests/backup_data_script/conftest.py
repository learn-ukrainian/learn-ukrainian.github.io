"""Fixtures for the backup script safety tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tests.backup_data_script._support import _make_database, _write_executable


@pytest.fixture
def backup_environment(tmp_path: Path) -> tuple[dict[str, str], Path, Path, Path]:
    fake_bin = tmp_path / "bin"
    project = tmp_path / "project"
    source = project / "data"
    staging = tmp_path / "staging"
    legacy = tmp_path / "legacy"
    password_file = tmp_path / "restic-password"
    log = tmp_path / "restic.log"
    runtime = tmp_path / "runtime"

    for directory in (
        fake_bin,
        source,
        project / ".claude" / "atlas-epic",
        project / ".agent",
        project / "batch_state" / "fleet-comms",
        project / "batch_state" / "review-receipts",
        staging,
        legacy,
        tmp_path / "home",
        runtime,
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
    (project / "batch_state" / "fleet-comms" / "state.txt").write_text(
        "recover me too\n",
        encoding="utf-8",
    )
    _make_database(source / "sources.db", "sources")
    (project / ".agent" / "recovery-state.json").write_text(
        '{"schema_version": 1}\n',
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q", str(project)], check=True, timeout=30)
    subprocess.run(
        ["git", "-C", str(project), "add", "README.md", ".gitignore"],
        check=True,
        timeout=30,
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
        timeout=30,
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
  previous=""
  for argument in "$@"; do
    if [[ "$previous" == "--exclude-file" ]]; then
      while IFS= read -r pattern; do
        printf 'exclude=<%s>\n' "$pattern"
      done < "$argument"
    fi
    previous="$argument"
  done
} >> "$FAKE_RESTIC_LOG"
if [[ "${1:-}" == "backup" && -n "${FAKE_BACKUP_HOLD_FILE:-}" ]]; then
  touch "$FAKE_BACKUP_HOLD_FILE"
  while [[ ! -e "$FAKE_BACKUP_HOLD_FILE.release" ]]; do sleep 0.05; done
fi
if [[ "${1:-}" == "cat" && "${FAKE_REPOSITORY_STATE:-initialized}" != "initialized" ]]; then
  exit 1
fi
if [[ "${1:-}" == "cat" && -z "${RESTIC_REPOSITORY:-}" ]]; then
  exit 78
fi
stdin_filename=""
database_part=0
if [[ "${1:-}" == "backup" ]]; then
  previous=""
  for argument in "$@"; do
    [[ "$previous" == "--stdin-filename" ]] && stdin_filename="$argument"
    [[ "$argument" == "lu-part-db" ]] && database_part=1
    previous="$argument"
  done
  if [[ -n "$stdin_filename" ]]; then
    mkdir -p "$(dirname "$FAKE_SNAPSHOT_DIR/$stdin_filename")"
    cat > "$FAKE_SNAPSHOT_DIR/$stdin_filename"
  elif [[ "$database_part" == 1 ]]; then
    if [[ -n "${FAKE_DB_PHASE_EXIT:-}" ]]; then
      exit "$FAKE_DB_PHASE_EXIT"
    fi
    batch_files=0
    batch_bytes=0
    while IFS= read -r -d '' staged; do
      staged="${staged#./}"
      mkdir -p "$(dirname "$FAKE_SNAPSHOT_DIR/$staged")"
      cp -p "$staged" "$FAKE_SNAPSHOT_DIR/$staged"
      printf 'db_file=<%s>\n' "$staged" >> "$FAKE_RESTIC_LOG"
      batch_files=$((batch_files + 1))
      batch_bytes=$((batch_bytes + $(stat -c '%s' "$staged")))
    done < <(find . -type f -print0)
    printf 'db_batch=<%s %s>\n' "$batch_files" "$batch_bytes" >> "$FAKE_RESTIC_LOG"
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
if [[ "${1:-}" == "backup" && -n "${FAKE_DB_RELATIVE:-}" && "$database_part" == 1 && -f "$FAKE_DB_RELATIVE" ]]; then
  rows="$(sqlite3 "file:$FAKE_SNAPSHOT_DIR/$FAKE_DB_RELATIVE?mode=ro&immutable=1" \
    'SELECT COUNT(*) FROM recovery_probe;')"
  printf 'db_rows=<%s>\n' "$rows" >> "$FAKE_RESTIC_LOG"
fi
if [[ "${1:-}" == "backup" && -n "${FAKE_REQUIRED_RELATIVE:-}" && -f "$FAKE_SNAPSHOT_DIR/$FAKE_REQUIRED_RELATIVE" ]]; then
  printf 'staged_required=<%s>\n' "$FAKE_REQUIRED_RELATIVE" >> "$FAKE_RESTIC_LOG"
fi
if [[ "${1:-}" == "backup" && -n "${FAKE_FORBIDDEN_RELATIVES:-}" && -z "$stdin_filename" && "$database_part" == 0 ]]; then
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
    data: ([.paths[] | select(.path == "data/datasets")][0])
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
if [[ "${1:-}" == "snapshots" ]]; then
  if [[ -n "${FAKE_SNAPSHOTS_JSON:-}" ]]; then
    cat "$FAKE_SNAPSHOTS_JSON"
  fi
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
if [[ "${1:-}" == "backup" && -n "${FAKE_MUTATED_LIVE_STATE_SOURCE:-}" ]] &&
  [[ -z "${FAKE_MUTATE_ON_PART:-}" || " $* " == *" ${FAKE_MUTATE_ON_PART} "* ]]; then
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
        "XDG_RUNTIME_DIR": str(runtime),
    }
    return environment, source, staging, legacy
