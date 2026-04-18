#!/usr/bin/env bash

set -euo pipefail

PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/gdrive-backup.log"
RCLONE_CONFIG_FILE="${RCLONE_CONFIG:-$HOME/.config/rclone/rclone.conf}"
BACKUP_ROOT="${RCLONE_BACKUP_ROOT:-learn-ukrainian-backups}"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S%z'
}

log() {
  mkdir -p "$LOG_DIR"
  printf '[%s] [prune] %s\n' "$(timestamp)" "$1" | tee -a "$LOG_FILE"
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
  [[ -x "$PYTHON_BIN" ]] || fail "Expected Python environment at $PYTHON_BIN"

  local remote_name
  remote_name="$(detect_remote || true)"
  if [[ -z "$remote_name" ]]; then
    fail "No Google Drive rclone remote found. Run 'rclone config' first or set RCLONE_REMOTE. See docs/ops/gdrive-backup.md."
  fi

  local remote_root
  remote_root="${remote_name}:${BACKUP_ROOT}"
  local directories_output

  if ! directories_output="$(rclone lsf "$remote_root" --dirs-only 2>&1)"; then
    case "$directories_output" in
      *"directory not found"*|*"Dir not found"*|*"didn't find section"*|*"path does not exist"*)
        log "No backup directories found under $remote_root"
        exit 0
        ;;
      *)
        fail "Unable to list backup directories under $remote_root: $directories_output"
        ;;
    esac
  fi

  local delete_dirs
  delete_dirs="$(
    BACKUP_DIRS="$directories_output" "$PYTHON_BIN" - <<'PY'
import datetime as dt
import os
import re

raw = os.environ.get("BACKUP_DIRS", "")
dates = []

for line in raw.splitlines():
    name = line.strip().rstrip("/")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", name):
        continue
    dates.append(dt.date.fromisoformat(name))

dates = sorted(set(dates), reverse=True)
keep = set(dates[:7])
keep.update([day for day in dates if day.weekday() == 6][:4])
delete = sorted(day for day in dates if day not in keep)

for day in delete:
    print(day.isoformat())
PY
  )"

  if [[ -z "$delete_dirs" ]]; then
    log "Retention already satisfied under $remote_root"
    exit 0
  fi

  local delete_dir
  while IFS= read -r delete_dir; do
    [[ -n "$delete_dir" ]] || continue
    log "Removing $remote_root/$delete_dir"
    rclone purge "$remote_root/$delete_dir"
  done <<< "$delete_dirs"

  log "Prune complete under $remote_root"
}

main "$@"
