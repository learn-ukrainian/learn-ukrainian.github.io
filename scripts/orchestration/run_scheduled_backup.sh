#!/usr/bin/env bash
#
# Scheduled backup entry point for the learn-ukrainian-backup systemd user
# service. Runs `backup-data.sh backup --execute`, then records the outcome in
# batch_state/backups/last-run.json so `systemctl --user list-timers`,
# journalctl, and the receipt file all show the last run's fate.
#
# Modes:
#   run_scheduled_backup.sh                 Run the backup and record last-run.json.
#   run_scheduled_backup.sh retention       Run retention with journal redaction.
#   run_scheduled_backup.sh record ...      Write last-run.json from a captured log
#                                           (the writer, callable on its own).
#
# record options:
#   --status N       Exit status of the backup run (required).
#   --started ISO    UTC start timestamp (required).
#   --log FILE       Captured backup stdout/stderr (required).
#   --finished ISO   UTC end timestamp (default: now).
#   --last-run PATH  Output path (default: $LU_BACKUP_LAST_RUN or
#                    <project>/batch_state/backups/last-run.json).
#
# The record mode exits 0 when the receipt was written. The run mode exits
# with the backup's own status, and exits non-zero when the log capture (tee)
# or the receipt write fails even if the backup itself succeeded: a run whose
# status record is not valid is a failed run.

set -Eeuo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
readonly SCRIPT_DIR
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
readonly REPO_ROOT
readonly PROJECT_ROOT="${LU_BACKUP_PROJECT_ROOT:-$REPO_ROOT}"
readonly BACKUP_SCRIPT="${LU_BACKUP_SCRIPT:-$REPO_ROOT/scripts/backup-data.sh}"
readonly BACKUP_TAG="${LU_BACKUP_TAG:-learn-ukrainian-data}"
readonly BACKUP_HOST="${LU_BACKUP_HOST:-learn-ukrainian}"

utc_now() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

default_last_run_path() {
  printf '%s\n' "$PROJECT_ROOT/batch_state/backups/last-run.json"
}

last_run_path() {
  printf '%s\n' "${LU_BACKUP_LAST_RUN:-$(default_last_run_path)}"
}

parse_run_id() {
  local log=$1
  grep -oE 'Linux backup run [0-9A-Za-z-]+ complete' "$log" | awk 'NR == 1 {print $4}' && return
  grep -oE 'Backup run [0-9A-Za-z-]+ failed' "$log" | awk 'NR == 1 {print $3}' || true
}

parse_bytes_added() {
  local log=$1
  jq -R 'fromjson? | select(.message_type? == "summary") | .data_added // empty' "$log" |
    awk '{total += $1} END {if (NR > 0) printf "%d\n", total}'
}

# Total snapshots of this backup family in the repository; best effort — the
# receipt must still be written when the repository is unreachable.
query_snapshot_count() {
  command -v restic >/dev/null 2>&1 || return 0
  RESTIC_REPOSITORY="${LU_BACKUP_REPOSITORY:-${RESTIC_REPOSITORY:-}}" \
    timeout 120 restic snapshots --option rclone.connections=1 --retry-lock 5m --json \
    --host "$BACKUP_HOST" --tag "$BACKUP_TAG" 2>/dev/null | jq -er 'length' 2>/dev/null || true
}

write_last_run() {
  local status=$1 started=$2 finished=$3 log=$4 output=$5
  local run_id bytes_added snapshot_count temporary

  run_id="$(parse_run_id "$log")" || return 1
  bytes_added="$(parse_bytes_added "$log")" || return 1
  snapshot_count="$(query_snapshot_count)" || return 1

  mkdir -p "$(dirname "$output")" || return 1
  temporary="$output.tmp.$$"
  jq -n \
    --arg started "$started" \
    --arg finished "$finished" \
    --argjson status "$status" \
    --arg run_id "$run_id" \
    --arg bytes_added "$bytes_added" \
    --arg snapshot_count "$snapshot_count" \
    '{
      schema_version: 1,
      started_at_utc: $started,
      finished_at_utc: $finished,
      exit_status: $status,
      run_id: (if $run_id == "" then null else $run_id end),
      snapshot_count: (if $snapshot_count == "" then null else ($snapshot_count | tonumber) end),
      bytes_added: (if $bytes_added == "" then null else ($bytes_added | tonumber) end)
    }' > "$temporary" || { rm -f "$temporary"; return 1; }
  mv "$temporary" "$output" || { rm -f "$temporary"; return 1; }
  chmod 600 "$output" || return 1
}

# Redact backup output once, before it reaches either the journal or the
# captured log used to build last-run.json. Split/join replaces literal values,
# including regex metacharacters in rclone paths, without treating them as code.
redact_backup_output() {
  jq -Rr --unbuffered '
      ($ENV.LU_BACKUP_REPOSITORY // $ENV.RESTIC_REPOSITORY // "") as $repository
      | ($ENV.RESTIC_PASSWORD_FILE // "") as $password_file
      | (
      reduce ([
        {value: $repository, replacement: "<repository>"},
        {value: ($repository | sub("^rclone:"; "")), replacement: "<repository>"},
        {value: $password_file, replacement: "<password-file>"}
      ] | map(select(.value != "")) | sort_by(.value | length) | reverse)[] as $item
        (. ; split($item.value) | join($item.replacement))
      )
    '
}

run_redacted_retention() {
  local -a pipe_status
  command -v jq >/dev/null 2>&1 ||
    { echo "scheduled-retention: jq is required" >&2; exit 78; }
  [[ -f "$BACKUP_SCRIPT" ]] ||
    { echo "scheduled-retention: backup script is missing: $BACKUP_SCRIPT" >&2; exit 78; }
  "$BACKUP_SCRIPT" retention --execute 2>&1 | redact_backup_output || {
    pipe_status=("${PIPESTATUS[@]}")
    if [[ "${pipe_status[1]}" -ne 0 ]]; then
      echo "ERROR: could not redact the retention log (filter exited ${pipe_status[1]})." >&2
    fi
    [[ "${pipe_status[0]}" -ne 0 ]] && exit "${pipe_status[0]}"
    exit 1
  }
}

run_record() {
  local status="" started="" finished="" log="" output=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --status)
        shift
        [[ $# -gt 0 ]] || { echo "record: --status requires a value" >&2; exit 2; }
        status=$1
        ;;
      --started)
        shift
        [[ $# -gt 0 ]] || { echo "record: --started requires a value" >&2; exit 2; }
        started=$1
        ;;
      --finished)
        shift
        [[ $# -gt 0 ]] || { echo "record: --finished requires a value" >&2; exit 2; }
        finished=$1
        ;;
      --log)
        shift
        [[ $# -gt 0 ]] || { echo "record: --log requires a value" >&2; exit 2; }
        log=$1
        ;;
      --last-run)
        shift
        [[ $# -gt 0 ]] || { echo "record: --last-run requires a value" >&2; exit 2; }
        output=$1
        ;;
      *)
        echo "record: unknown option: $1" >&2
        exit 2
        ;;
    esac
    shift
  done

  [[ -n "$status" && "$status" =~ ^[0-9]+$ ]] ||
    { echo "record: --status must be a non-negative integer" >&2; exit 2; }
  [[ -n "$started" ]] || { echo "record: --started is required" >&2; exit 2; }
  [[ -n "$log" && -f "$log" ]] || { echo "record: --log must be an existing file" >&2; exit 2; }
  finished=${finished:-$(utc_now)}
  output=${output:-$(last_run_path)}

  write_last_run "$status" "$started" "$finished" "$log" "$output"
  echo "last-run receipt written: $output (exit_status=$status)"
}

run_backup_and_record() {
  local started finished log status redact_status tee_status exit_status output
  local -a pipe_status

  command -v jq >/dev/null 2>&1 ||
    { echo "scheduled-backup: jq is required" >&2; exit 78; }
  [[ -f "$BACKUP_SCRIPT" ]] ||
    { echo "scheduled-backup: backup script is missing: $BACKUP_SCRIPT" >&2; exit 78; }
  if [[ -n "${LU_BACKUP_TMPDIR:-}" ]]; then
    mkdir -p "$LU_BACKUP_TMPDIR"
    chmod 700 "$LU_BACKUP_TMPDIR"
  fi

  log="$(mktemp "${TMPDIR:-/tmp}/learn-ukrainian-scheduled-backup.XXXXXX")"
  # shellcheck disable=SC2064  # expand $log now: it is per-run state
  trap "rm -f '$log'" EXIT

  started="$(utc_now)"
  status=0
  redact_status=0
  tee_status=0
  # pipefail makes the pipeline fail when either side fails; capture PIPESTATUS
  # in one assignment (any simple command resets it) so the receipt keeps the
  # backup's own exit status even when tee also failed.
  "$BACKUP_SCRIPT" backup --execute 2>&1 | redact_backup_output | tee "$log" || {
    pipe_status=("${PIPESTATUS[@]}")
    status=${pipe_status[0]}
    redact_status=${pipe_status[1]}
    tee_status=${pipe_status[2]}
  }
  finished="$(utc_now)"

  # The receipt records the backup command's own status; the service exit
  # additionally fails when the log capture or the receipt write failed.
  exit_status=$status
  if [[ "$redact_status" -ne 0 ]]; then
    echo "ERROR: could not redact the backup log (filter exited $redact_status)." >&2
    [[ "$exit_status" -ne 0 ]] || exit_status=1
  fi
  if [[ "$tee_status" -ne 0 ]]; then
    echo "ERROR: could not capture the backup log (tee exited $tee_status)." >&2
    [[ "$exit_status" -ne 0 ]] || exit_status=1
  fi

  output="$(last_run_path)"
  if ! write_last_run "$status" "$started" "$finished" "$log" "$output"; then
    echo "ERROR: could not write the last-run receipt: $output" >&2
    [[ "$exit_status" -ne 0 ]] || exit_status=1
  fi
  exit "$exit_status"
}

main() {
  local command=${1:-run}
  [[ $# -eq 0 ]] || shift
  case "$command" in
    run)
      [[ $# -eq 0 ]] || { echo "usage: run_scheduled_backup.sh [retention | record ...]" >&2; exit 2; }
      run_backup_and_record
      ;;
    record)
      run_record "$@"
      ;;
    retention)
      [[ $# -eq 0 ]] || { echo "usage: run_scheduled_backup.sh retention" >&2; exit 2; }
      run_redacted_retention
      ;;
    *)
      echo "usage: run_scheduled_backup.sh [retention | record ...]" >&2
      exit 2
      ;;
  esac
}

main "$@"
