#!/usr/bin/env bash

set -euo pipefail

PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/gdrive-backup.log"
RCLONE_CONFIG_FILE="${RCLONE_CONFIG:-$HOME/.config/rclone/rclone.conf}"
BACKUP_ROOT="${RCLONE_BACKUP_ROOT:-learn-ukrainian-backups}"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S%z'
}

log() {
  mkdir -p "$LOG_DIR"
  printf '[%s] [backup] %s\n' "$(timestamp)" "$1" | tee -a "$LOG_FILE"
}

fail() {
  log "ERROR: $1"
  exit 1
}

lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

detect_remote() {
  if [[ -n "${RCLONE_REMOTE:-}" ]]; then
    printf '%s\n' "$RCLONE_REMOTE"
    return 0
  fi

  if [[ ! -f "$RCLONE_CONFIG_FILE" ]]; then
    return 1
  fi

  local drive_remotes
  drive_remotes="$(
    awk '
      /^\[.*\]$/ {
        section = $0
        gsub(/^\[/, "", section)
        gsub(/\]$/, "", section)
        next
      }
      /^[[:space:]]*type[[:space:]]*=[[:space:]]*drive[[:space:]]*$/ {
        if (section != "") {
          print section
        }
      }
    ' "$RCLONE_CONFIG_FILE"
  )"

  if [[ -z "$drive_remotes" ]]; then
    return 1
  fi

  local preferred
  local remote
  local remote_lc
  local match

  for preferred in learn-ukrainian learn_ukrainian learnukrainian gdrive google-drive googledrive drive; do
    match="$(
      printf '%s\n' "$drive_remotes" | while IFS= read -r remote; do
        remote_lc="$(lower "$remote")"
        if [[ "$remote_lc" == "$preferred" ]]; then
          printf '%s\n' "$remote"
          break
        fi
      done
    )"
    if [[ -n "$match" ]]; then
      printf '%s\n' "$match"
      return 0
    fi
  done

  match="$(
    printf '%s\n' "$drive_remotes" | while IFS= read -r remote; do
      remote_lc="$(lower "$remote")"
      case "$remote_lc" in
        *learn*ukrainian*|*gdrive*|*google*drive*)
          printf '%s\n' "$remote"
          break
          ;;
      esac
    done
  )"
  if [[ -n "$match" ]]; then
    printf '%s\n' "$match"
    return 0
  fi

  if [[ "$(printf '%s\n' "$drive_remotes" | sed '/^$/d' | wc -l | tr -d ' ')" == "1" ]]; then
    printf '%s\n' "$drive_remotes"
    return 0
  fi

  return 1
}

main() {
  command -v rclone >/dev/null 2>&1 || fail "rclone is not installed. Install it with 'brew install rclone'."

  local required_files
  required_files=(
    "$PROJECT_ROOT/data/sources.db"
    "$PROJECT_ROOT/data/vesum.db"
  )

  local file_path
  for file_path in "${required_files[@]}"; do
    [[ -f "$file_path" ]] || fail "Required backup source is missing: $file_path"
  done

  local remote_name
  remote_name="$(detect_remote || true)"
  if [[ -z "$remote_name" ]]; then
    fail "No Google Drive rclone remote found. Run 'rclone config' first or set RCLONE_REMOTE. See docs/ops/gdrive-backup.md."
  fi

  local backup_date
  backup_date="$(date '+%Y-%m-%d')"

  local destination
  destination="${remote_name}:${BACKUP_ROOT}/${backup_date}"

  log "Using remote ${remote_name}:${BACKUP_ROOT}"
  if [[ -f "$PROJECT_ROOT/data/sources.db-wal" ]]; then
    log "Warning: data/sources.db-wal exists; this job uploads only data/sources.db."
  fi
  if [[ -f "$PROJECT_ROOT/data/vesum.db-wal" ]]; then
    log "Warning: data/vesum.db-wal exists; this job uploads only data/vesum.db."
  fi

  log "Ensuring destination exists: $destination"
  rclone mkdir "$destination"

  local db_name
  for db_name in sources.db vesum.db; do
    file_path="$PROJECT_ROOT/data/$db_name"
    log "Copying $db_name to $destination/"
    rclone copy --checksum "$file_path" "$destination"
  done

  log "Backup complete: $destination"
}

main "$@"
