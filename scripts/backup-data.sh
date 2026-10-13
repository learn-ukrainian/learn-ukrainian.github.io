#!/usr/bin/env bash
#
# Versioned, encrypted backup and staging-only restore for recovery-critical
# project state.
#
# This script intentionally does not write to the Google Drive Desktop mount.
# It uses restic's rclone backend so snapshots are versioned, deduplicated, and
# transferred without hydrating Drive's local File Provider cache.
#
# Covers the allowlist in scripts/config/backup-allowlist.json, and nothing
# else under batch_state/ or data/. A path that is not on that list is not
# walked. SQLite files on the list are copied with SQLite's online backup
# into the same nightly run as the other files. A hard-linked SQLite file
# stops the backup before a snapshot is written: sidecars belong to the path
# SQLite opened, and another name would omit committed WAL rows. A clean
# Linux run writes one base snapshot, ceil(database count / databases per
# batch) database-batch snapshots, and the two receipt snapshots. Snapshot directories are excluded
# only under batch_state/tasks, from the same list discovery and restic use.
#
# Required environment:
#   LU_BACKUP_REPOSITORY=rclone:<remote>:<path>
#   RESTIC_PASSWORD_FILE=/absolute/path/to/mode-600-password-file
#
# Start with:
#   ./scripts/backup-data.sh doctor
#   ./scripts/backup-data.sh init
#   ./scripts/backup-data.sh init --execute
#   ./scripts/backup-data.sh backup
#   ./scripts/backup-data.sh backup --execute
#
# Mutating commands are previews unless --execute is present. The only
# prune/delete command is `retention`, which applies the operator-approved
# weekly keep policy run-aware: it selects the completed runs to keep, then
# forgets by explicit snapshot ID only the snapshots of runs outside the keep
# set, so a retained receipt never loses a snapshot it references. See
# docs/runbooks/data-backup.md.

set -Eeuo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
readonly SCRIPT_DIR
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
readonly REPO_ROOT
readonly PROJECT_ROOT="${LU_BACKUP_PROJECT_ROOT:-$REPO_ROOT}"
readonly SOURCE="$PROJECT_ROOT/data"
readonly REPOSITORY="${LU_BACKUP_REPOSITORY:-${RESTIC_REPOSITORY:-}}"
readonly PASSWORD_FILE="${RESTIC_PASSWORD_FILE:-}"
readonly BACKUP_TAG="${LU_BACKUP_TAG:-learn-ukrainian-data}"
readonly BACKUP_HOST="${LU_BACKUP_HOST:-learn-ukrainian}"
readonly MIN_RESTIC_VERSION="0.19.0"
readonly CLOUD_ROOT="${HOME}/Library/CloudStorage"
readonly TMP_ROOT="${LU_BACKUP_TMPDIR:-${TMPDIR:-/tmp}}"
if [[ -n "${XDG_RUNTIME_DIR:-}" ]]; then
  readonly LOCK_ROOT="$XDG_RUNTIME_DIR"
elif [[ -d "/run/user/$UID" ]]; then
  readonly LOCK_ROOT="/run/user/$UID"
else
  readonly LOCK_ROOT="/tmp"
fi
readonly LOCK_FILE="$LOCK_ROOT/learn-ukrainian-backup.${UID}.lock"
readonly LOCK_WAIT_SECONDS="${LU_BACKUP_LOCK_WAIT_SECONDS:-3600}"
# rclone backend connection limit. One connection keeps backups gentle on the
# remote; restic prune refuses to run below two, so prune always gets at least
# PRUNE_MIN_RCLONE_CONNECTIONS whatever this is set to.
readonly RCLONE_CONNECTIONS="${LU_BACKUP_RCLONE_CONNECTIONS:-1}"
readonly PRUNE_MIN_RCLONE_CONNECTIONS=2
readonly STAGE_PATH="$TMP_ROOT/learn-ukrainian-backup.${UID}.stage"
# Dated compressed archives of preserved SQLite evidence. Each
# NAME.tar.zst ships with NAME.tar.zst.manifest (see load_db_archive_manifests);
# a listed database whose size and mtime still match is covered by the archive,
# which the file phase uploads, so the loose copy is not uploaded again.
readonly DB_ARCHIVE_DIR="${LU_BACKUP_DB_ARCHIVE_DIR:-$PROJECT_ROOT/batch_state/backups/archives}"
# Operator-approved retention policy (2026-09-26), applied weekly by
# `retention --execute` to completed backup runs (never to individual
# snapshots) of this backup family's tag only.
readonly KEEP_DAILY=7
readonly KEEP_WEEKLY=4
readonly KEEP_MONTHLY=6
# Staged-byte budget for one Linux database upload. Consistent SQLite copies
# accumulate in a private batch that is uploaded as one lu-part-db snapshot
# once the next database would exceed this budget (a larger database goes
# alone). A pending batch and the next incoming online copy coexist until the
# flush, so peak staging is at most this budget plus the largest copy.
readonly DB_BATCH_MAX_BYTES="${LU_BACKUP_DB_BATCH_MAX_BYTES:-1073741824}"
# Snapshot directories are excluded only under these allowlist roots.
# Discovery walks and restic excludes are both generated from this list.
SNAPSHOT_EXCLUDE_ROOTS=(
  batch_state/tasks
)

STAGE_DIR=""
STAGED_ROOT=""
LOCK_FD=""
LEGACY_DIR=""
# restic exclude patterns, one per entry. They are written to a private file
# and passed with --exclude-file: thousands of per-database --exclude flags
# overflow the kernel argument limit ("Argument list too long").
RESTIC_EXCLUDES=()
RESTIC_EXCLUDE_FILE=""
LEGACY_EXCLUDES=()
BACKUP_PATHS=()
# The allowlist lives next to this script, not under PROJECT_ROOT. Fixtures
# override the project root and must still read the repository file.
ALLOWLIST_FILE="$SCRIPT_DIR/config/backup-allowlist.json"
ENUMERATED_FILE_COUNT=0
ENUMERATED_RELATIVE_PATHS=()
STAGED_CANDIDATES=()
STAGED_RELATIVE_PATHS=()
ALLOWLIST_TREE_ROOTS=()
ALLOWLIST_FILE_ROOTS=()
FILES_FROM_FILE=""
# Built in the current shell before any pipeline so the EXIT trap can see it.
RESTIC_SELECTION_ARGS=()
RESTIC_SELECTION_READY=0
EPHEMERAL_HOME_EXCLUDES=()
# Absolute paths of broken (dangling) symlinks found in the recovery roots.
# They are skipped with a warning and excluded from the snapshot instead of
# aborting the whole backup; the receipt records each one.
BROKEN_SYMLINK_EXCLUDES=()
# JSON array of {path, snapshot_id, mode}. A file, never a shell argument:
# the array grows with every database in the run.
DB_INVENTORY_FILE=""
# Databases staged under DB_BATCH_ROOT and not yet uploaded (relative paths,
# source modes, staged bytes); flush_database_batch uploads and clears them.
DB_BATCH_ROOT=""
# Where each online copy is made and measured before it joins the batch.
DB_INCOMING_ROOT=""
PENDING_DB_PATHS=()
PENDING_DB_MODES=()
PENDING_DB_BYTES=0
# SQLite sources split by classify_sqlite_sources: uploaded in batches,
# skipped as per-run test scratch, or covered by a verified archive.
SQLITE_BACKUP_SOURCES=()
SQLITE_TRANSIENT_SOURCES=()
SQLITE_ARCHIVED_SOURCES=()
DB_ARCHIVES_USED=()
# Project-relative paths of every classified database. Explicit file arguments
# bypass restic exclude patterns, so the base selection must omit these paths
# instead of relying on the exclude file.
declare -A CLASSIFIED_SQLITE_RELATIVE=()
declare -A ARCHIVED_DB_STAT=()
declare -A ARCHIVED_DB_ARCHIVE=()
LINUX_BASE_SNAPSHOT=""
LINUX_PATCH_SNAPSHOT=""
# Both Linux receipt snapshots (pending, then completion) carry this time, so
# the completion snapshot reuses the tree the repository check verified.
RECEIPT_TIME=""
# A gate receipt written but not yet renamed into place; removed on failure.
STAGED_GATE_RECEIPT=""
# Private copy used so the restore integrity check can apply a sidecar without
# creating -wal/-shm files beside the restored database.
RESTORE_CHECK_DIR=""
RUN_ID=""
LINUX_MODE=0
BACKUP_FAILURES=()

# The interpreter that runs the runner mirror receipt writer.
runner_mirror_python() {
  local project_python common_dir primary_root

  # Layout A: dispatch worktrees have no local .venv. Prefer an explicit
  # override, then the script checkout's .venv, then the primary checkout
  # resolved via REPO_ROOT's git common dir (not PROJECT_ROOT — fixtures and
  # LU_BACKUP_PROJECT_ROOT overrides are often separate git trees).
  project_python="${LU_BACKUP_PYTHON:-}"
  if [[ -z "$project_python" || ! -x "$project_python" ]]; then
    if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
      project_python="$REPO_ROOT/.venv/bin/python"
    else
      common_dir="$(git_command -C "$REPO_ROOT" rev-parse --git-common-dir 2>/dev/null || true)"
      case "$common_dir" in
        /*) : ;;
        "") common_dir="" ;;
        *) common_dir="$REPO_ROOT/$common_dir" ;;
      esac
      if [[ -n "$common_dir" ]]; then
        primary_root="$(cd "$common_dir/.." && pwd -P)"
        project_python="$primary_root/.venv/bin/python"
      fi
    fi
  fi
  [[ -x "$project_python" ]] ||
    die "Runner mirror receipt writer requires the shared project interpreter (.venv/bin/python via primary checkout)"
  printf '%s\n' "$project_python"
}

write_restic_gate_receipt() {
  local snapshot_id=$1
  local staged_mirror_root="$STAGED_ROOT/data/lexicon/runner-mirror"
  local live_mirror_root="$SOURCE/lexicon/runner-mirror"
  local git_sha
  local project_python
  local -a stage_arguments=()

  # Linux stages the receipt beside its destination; publish_staged_gate_receipt
  # renames it into place only after the run is published as complete.
  if [[ "${2:-}" == stage-verified-live ]]; then
    staged_mirror_root="$live_mirror_root"
    stage_arguments=(--staged-receipt-path "$live_mirror_root/RESTIC-GATE-RECEIPT.json.tmp")
  fi
  # The staged tree is the copy restic uploaded. Do not create unrelated data
  # paths when it has no mirror; if a live mirror appeared after staging, it is
  # not covered by this snapshot and must not receive a receipt.
  if [[ ! -e "$staged_mirror_root" ]]; then
    [[ ! -e "$live_mirror_root" && ! -L "$live_mirror_root" ]] ||
      die "Runner mirror appeared after staging; refusing to claim restic durability."
    return 0
  fi
  [[ ! -L "$staged_mirror_root" && -d "$staged_mirror_root" ]] ||
    die "Staged runner mirror root must be a real directory: $staged_mirror_root"

  project_python="$(runner_mirror_python)" || exit 1
  git_sha="$(git_command -C "$PROJECT_ROOT" rev-parse HEAD)"
  ((${#stage_arguments[@]} == 0)) || STAGED_GATE_RECEIPT="${stage_arguments[1]}"
  "$project_python" "$REPO_ROOT/scripts/lexicon/runner/durable_mirror.py" \
    write-restic-gate-receipt \
    --mirror-root "$staged_mirror_root" \
    --receipt-root "$live_mirror_root" \
    --restic-snapshot-id "$snapshot_id" \
    --host "$BACKUP_HOST" \
    --git-sha "$git_sha" \
    --mirror-root-relative-to-data "lexicon/runner-mirror" \
    ${stage_arguments[@]+"${stage_arguments[@]}"} ||
    die "Could not write the runner mirror restic gate receipt after backup."
}

# Rename a staged gate receipt into place. This follows the completion
# snapshot. The run is already selectable. A failed rename leaves exit 1 and
# no gate receipt, so the pre-wipe gate stays closed.
publish_staged_gate_receipt() {
  local source destination

  [[ -n "$STAGED_GATE_RECEIPT" ]] || return 0
  source=$STAGED_GATE_RECEIPT
  destination="${source%.tmp}"
  # Same directory, mv -T: the rename is atomic and does not follow a
  # directory sitting on the destination. Then require a readable regular file.
  if [[ "$destination" == "$source" || "$(dirname -- "$source")" != "$(dirname -- "$destination")" ]] ||
    ! mv -fT -- "$source" "$destination" ||
    [[ ! -f "$destination" || -L "$destination" || ! -r "$destination" ]]; then
    die "Run $RUN_ID is complete and restorable, but its runner mirror gate receipt could not be renamed into place; the pre-wipe gate stays closed. Re-run the backup."
  fi
  STAGED_GATE_RECEIPT=""
}

# "HASH PATH" lines for every file of the live runner mirror, in path order.
live_runner_mirror_hashes() {
  local mirror=$1 path
  find "$mirror" -type f -printf '/data/lexicon/runner-mirror/%P\n' | LC_ALL=C sort |
    while IFS= read -r path; do
      printf '%s %s\n' "$(sha256sum < "$PROJECT_ROOT$path" | awk '{print $1}')" "$path"
    done
}

# Record every runner-mirror file in one snapshot. The same path in two
# snapshots is not one file set.
add_snapshot_mirror_files() {
  local snapshot_id=$1
  local -n file_sources=$2
  local path part_files="$STAGE_DIR/mirror-part-files"

  restic_repository_command ls --json --recursive "$snapshot_id" \
    /data/lexicon/runner-mirror \
    | jq -r 'select(.struct_type == "node" and .type == "file") | .path' \
    | LC_ALL=C sort -u > "$part_files" ||
    die "Runner mirror file set changed during backup; refusing to write a durability receipt."
  while IFS= read -r path; do
    [[ -n "$path" ]] || continue
    if [[ -n "${file_sources[$path]+set}" && "${file_sources[$path]}" != "$snapshot_id" ]]; then
      die "Runner mirror file set changed during backup; refusing to write a durability receipt."
    fi
    file_sources["$path"]="$snapshot_id"
  done < "$part_files"
}

# Live byte hash when the snapshot matches the live file. SQLite online backup
# rewrites pages, so a database matches on sqlite3 .dump instead of raw bytes.
# Prints the live file's raw hash. Must not be called from a command
# substitution that needs die(): a mismatch returns 1.
mirror_snapshot_matches_live() {
  local snapshot_id=$1 path=$2
  local live="$PROJECT_ROOT$path"
  local dumped="$STAGE_DIR/mirror-dumped-file"
  local snapshot_hash live_hash snapshot_logical live_logical

  restic_repository_command dump "$snapshot_id" "$path" > "$dumped" || return 1
  snapshot_hash="$(sha256sum "$dumped" | awk '{print $1}')" || return 1
  live_hash="$(sha256sum "$live" | awk '{print $1}')" || return 1
  if [[ "$snapshot_hash" == "$live_hash" ]]; then
    printf '%s\n' "$live_hash"
    return 0
  fi
  is_sqlite_database "$live" || return 1
  is_sqlite_database "$dumped" || return 1
  snapshot_logical="$(sqlite3 "$dumped" .dump | sha256sum | awk '{print $1}')" || return 1
  live_logical="$(sqlite3 "$live" .dump | sha256sum | awk '{print $1}')" || return 1
  [[ "$snapshot_logical" == "$live_logical" ]] || return 1
  printf '%s\n' "$live_hash"
}

# Prove, before the run is published, that the base snapshot plus the database
# batches that hold this tree match the live mirror and its manifest. Hashes
# are kept for the gate receipt step. An absent mirror returns without a receipt.
verify_linux_runner_mirror() {
  local snapshot_id=$1 mirror="$SOURCE/lexicon/runner-mirror"
  local snapshot_files="$STAGE_DIR/mirror-snapshot-files"
  local live_files="$STAGE_DIR/mirror-live-files"
  local verified="$STAGE_DIR/mirror-verified-hashes"
  local db_snapshots="$STAGE_DIR/mirror-db-snapshots"
  local path live_hash db_snapshot manifest manifest_dir relative_root rel expected
  local -A mirror_source=()

  [[ -e "$mirror" || -L "$mirror" ]] || return 0
  [[ -d "$mirror" && ! -L "$mirror" ]] || die "Runner mirror root must be a real directory."
  runner_mirror_python > /dev/null || exit 1
  add_snapshot_mirror_files "$snapshot_id" mirror_source
  if [[ -n "$DB_INVENTORY_FILE" && -f "$DB_INVENTORY_FILE" ]]; then
    jq -r --arg prefix "data/lexicon/runner-mirror/" \
      '[.[] | select(.path | startswith($prefix)) | .snapshot_id] | unique | .[]' \
      "$DB_INVENTORY_FILE" > "$db_snapshots" ||
      die "Runner mirror file set changed during backup; refusing to write a durability receipt."
    while IFS= read -r db_snapshot; do
      [[ -n "$db_snapshot" ]] || continue
      [[ "$db_snapshot" =~ ^[0-9a-f]{64}$ ]] ||
        die "Runner mirror file set changed during backup; refusing to write a durability receipt."
      add_snapshot_mirror_files "$db_snapshot" mirror_source
    done < "$db_snapshots"
  fi
  : > "$snapshot_files"
  if ((${#mirror_source[@]} > 0)); then
    for path in "${!mirror_source[@]}"; do
      printf '%s\n' "$path"
    done | LC_ALL=C sort > "$snapshot_files"
  fi
  find "$mirror" -type f -printf '/data/lexicon/runner-mirror/%P\n' \
    | LC_ALL=C sort > "$live_files"
  cmp -s "$snapshot_files" "$live_files" ||
    die "Runner mirror file set changed during backup; refusing to write a durability receipt."
  while IFS= read -r -d '' manifest; do
    manifest_dir="$(dirname -- "$manifest")"
    relative_root="${manifest_dir#"$SOURCE"/}"
    while IFS= read -r rel || [[ -n "$rel" ]]; do
      [[ -n "$rel" ]] || continue
      expected="/data/${relative_root}/${rel}"
      grep -Fxq -e "$expected" "$snapshot_files" ||
        die "Runner mirror file set changed during backup; refusing to write a durability receipt."
    done < <(jq -r '.files[]?.path // empty' "$manifest")
  done < <(find "$mirror" -type f -name manifest.json -print0)
  : > "$verified"
  while IFS= read -r path; do
    [[ -n "$path" ]] || continue
    if ! live_hash="$(mirror_snapshot_matches_live "${mirror_source[$path]}" "$path")"; then
      die "Runner mirror content changed during backup; refusing to write a durability receipt."
    fi
    printf '%s %s\n' "$live_hash" "$path" >> "$verified"
  done < "$snapshot_files"
}

# Before the run is published, stage the mirror's gate receipt only if the
# live mirror still holds exactly what verify_linux_runner_mirror proved.
stage_verified_linux_runner_mirror_receipt() {
  local snapshot_id=$1 mirror="$SOURCE/lexicon/runner-mirror"
  local verified="$STAGE_DIR/mirror-verified-hashes"
  if [[ ! -f "$verified" ]]; then
    [[ ! -e "$mirror" && ! -L "$mirror" ]] ||
      die "Runner mirror appeared during backup; refusing to write a durability receipt."
    return 0
  fi
  [[ -d "$mirror" && ! -L "$mirror" ]] || die "Runner mirror root must be a real directory."
  live_runner_mirror_hashes "$mirror" | cmp -s "$verified" - ||
    die "Runner mirror content changed during backup; refusing to write a durability receipt."
  write_restic_gate_receipt "$snapshot_id" stage-verified-live
}

usage() {
  cat <<'EOF'
Usage:
  ./scripts/backup-data.sh doctor
  ./scripts/backup-data.sh init [--execute]
  ./scripts/backup-data.sh backup [--execute]
  ./scripts/backup-data.sh retention [--execute]
  ./scripts/backup-data.sh snapshots
  ./scripts/backup-data.sh verify [--read-data]
  ./scripts/backup-data.sh restore SNAPSHOT --to ABSOLUTE_EMPTY_DIR [--path RELATIVE_PATH] [--execute]

Safety:
  - init, backup, retention, and restore are previews unless --execute is supplied.
  - backup requires the allowlist's required paths (see docs/runbooks/data-backup.md).
    A missing optional path is logged and skipped. Paths outside the allowlist
    are not walked and do not fail the run.
  - successful snapshots contain BACKUP-RECEIPT.json and a restore command.
  - restore refuses non-empty, project, cloud, and legacy-backup targets.
  - restore first measures exactly what it will write (restic stats, restore-size)
    and refuses, writing nothing, unless the target filesystem has that much free
    space plus a margin (default 10%). The preview reports the same numbers.
  - restore --path RELATIVE_PATH restores only that file or directory of the run
    (for example data/atlas.db, read from its database snapshot via the receipt;
    other paths come from the file-phase snapshot). Same guards and preflight.
  - a hard-linked SQLite database stops the backup before any snapshot is written.
  - restore removes -wal, -shm, and -journal files paired with each receipt-listed
    database after every snapshot is written, then checks integrity read-only.
  - retention applies --keep-daily 7 --keep-weekly 4 --keep-monthly 6 to the
    completed runs of this backup family's tag, then forgets by explicit
    snapshot ID only the snapshots of runs outside the keep set; other tags
    are untouched. Runs newer than the newest completed run are always kept.
    Prune is a separate explicit step. Run it weekly, not on every backup.

Required environment:
  LU_BACKUP_REPOSITORY  Restic rclone backend, for example:
                        rclone:lu-gdrive:Projects/learn-ukrainian-restic
  RESTIC_PASSWORD_FILE Absolute path to a mode-600 restic password file.

Optional environment:
  LU_BACKUP_RESTORE_MARGIN_PERCENT
                        Extra free space required over the restore size (default: 10).
  LU_BACKUP_PROJECT_ROOT
                        Project checkout (default: script's repository).
  LU_BACKUP_LEGACY_DIR Read-only legacy Drive directory used for symlink checks.
  LU_BACKUP_TMPDIR      Private staging parent (default: $TMPDIR or /tmp). On
                        Linux it may also be the designated data-volume staging
                        directory <project>/data/.backup-staging, which keeps
                        staging on the same filesystem as data/.
  LU_BACKUP_TAG         Restic tag (default: learn-ukrainian-data).
  LU_BACKUP_HOST        Stable restic host label (default: learn-ukrainian).
  LU_BACKUP_RCLONE_CONNECTIONS
                        rclone backend connection limit, 1-16 (default: 1).
                        prune always uses at least 2, which restic requires.
  LU_BACKUP_DB_BATCH_MAX_BYTES
                        Linux staged-byte budget per SQLite upload batch
                        (default: 1073741824). A larger database goes alone.

Examples:
  ./scripts/backup-data.sh restore latest --to /scratch/restore              # preview
  ./scripts/backup-data.sh restore latest --to /scratch/restore --execute    # whole run
  ./scripts/backup-data.sh restore latest --to /scratch/one --path data/atlas.db --execute

Exit codes:
  0  success (or preview complete)
  1  any refusal or failure, including too little free space for a restore

Related: docs/SCRIPTS.md (backup-data), issue #8829.
EOF
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

info() {
  echo "==> $*"
}

restic_rclone_connections() {
  local subcommand=${1:-}
  local connections=$RCLONE_CONNECTIONS

  [[ "$connections" =~ ^[1-9][0-9]?$ ]] && ((connections <= 16)) ||
    die "LU_BACKUP_RCLONE_CONNECTIONS must be a whole number from 1 to 16."
  if [[ "$subcommand" == prune ]] && ((connections < PRUNE_MIN_RCLONE_CONNECTIONS)); then
    connections=$PRUNE_MIN_RCLONE_CONNECTIONS
  fi
  printf '%s\n' "$connections"
}

restic_repository_command() {
  local connections

  connections="$(restic_rclone_connections "${1:-}")" || exit 1
  if [[ -n "$LOCK_FD" ]]; then
    restic "$@" --option "rclone.connections=$connections" --retry-lock 5m {LOCK_FD}>&-
  else
    restic "$@" --option "rclone.connections=$connections" --retry-lock 5m
  fi
}

git_command() {
  if [[ -n "$LOCK_FD" ]]; then
    git "$@" {LOCK_FD}>&-
  else
    git "$@"
  fi
}

cleanup() {
  local status=$?

  if [[ -n "$STAGE_DIR" && -d "$STAGE_DIR" ]]; then
    case "$STAGE_DIR" in
      "$TMP_ROOT"/learn-ukrainian-backup.*)
        find "$STAGE_DIR" -depth -delete
        ;;
      *)
        echo "WARNING: refusing to clean unexpected staging path: $STAGE_DIR" >&2
        ;;
    esac
  fi

  if [[ -n "$RESTIC_EXCLUDE_FILE" && -f "$RESTIC_EXCLUDE_FILE" ]]; then
    find "$RESTIC_EXCLUDE_FILE" -maxdepth 0 -type f -delete
  fi
  if [[ -n "$FILES_FROM_FILE" && -f "$FILES_FROM_FILE" ]]; then
    find "$FILES_FROM_FILE" -maxdepth 0 -type f -delete
  fi

  # Set only while a staged gate receipt has not been renamed into place.
  if [[ -n "$STAGED_GATE_RECEIPT" && -f "$STAGED_GATE_RECEIPT" && ! -L "$STAGED_GATE_RECEIPT" ]]; then
    find "$STAGED_GATE_RECEIPT" -maxdepth 0 -type f -delete
  fi
  if [[ -n "$RESTORE_CHECK_DIR" && -d "$RESTORE_CHECK_DIR" ]]; then
    case "$RESTORE_CHECK_DIR" in
      "$TMP_ROOT"/learn-ukrainian-restore-check.*)
        find "$RESTORE_CHECK_DIR" -depth -delete
        ;;
      *)
        echo "WARNING: refusing to clean unexpected integrity-check path: $RESTORE_CHECK_DIR" >&2
        ;;
    esac
  fi

  if [[ -n "$LOCK_FD" ]]; then
    exec {LOCK_FD}>&-
  fi

  return "$status"
}

trap cleanup EXIT
trap 'exit 130' INT TERM

require_command() {
  local name=$1
  local install_hint=${2:-}

  if ! command -v "$name" >/dev/null 2>&1; then
    if [[ -n "$install_hint" ]]; then
      die "$name is required. Install it with: $install_hint"
    fi
    die "$name is required but was not found in PATH."
  fi
}

version_at_least() {
  local actual=$1
  local minimum=$2
  local actual_major actual_minor actual_patch
  local minimum_major minimum_minor minimum_patch

  actual=${actual%%-*}
  minimum=${minimum%%-*}
  IFS=. read -r actual_major actual_minor actual_patch <<<"$actual"
  IFS=. read -r minimum_major minimum_minor minimum_patch <<<"$minimum"
  actual_minor=${actual_minor:-0}
  actual_patch=${actual_patch:-0}
  minimum_minor=${minimum_minor:-0}
  minimum_patch=${minimum_patch:-0}

  ((actual_major > minimum_major)) ||
    ((actual_major == minimum_major && actual_minor > minimum_minor)) ||
    ((actual_major == minimum_major && actual_minor == minimum_minor &&
      actual_patch >= minimum_patch))
}

check_restic_version() {
  local version
  version="$(restic version | awk 'NR == 1 {print $2}')"
  [[ -n "$version" ]] || die "Could not determine the installed restic version."
  version_at_least "$version" "$MIN_RESTIC_VERSION" ||
    die "restic $MIN_RESTIC_VERSION or newer is required; found $version."
}

file_mode() {
  local path=$1
  local mode

  if mode="$(stat -f '%Lp' "$path" 2>/dev/null)"; then
    printf '%s\n' "$mode"
    return
  fi
  stat -c '%a' "$path"
}

filesystem_device() {
  local path=$1
  local device

  if device="$(stat -f '%d' "$path" 2>/dev/null)" &&
    [[ "$device" =~ ^[0-9]+$ ]]; then
    printf '%s\n' "$device"
    return
  fi
  device="$(stat -c '%d' "$path")" || return 1
  [[ "$device" =~ ^[0-9]+$ ]] || return 1
  printf '%s\n' "$device"
}

file_link_count() {
  local path=$1
  local links=""

  if links="$(stat -c '%h' "$path" 2>/dev/null)" && [[ "$links" =~ ^[0-9]+$ ]]; then
    printf '%s\n' "$links"
    return 0
  fi
  if links="$(stat -f '%l' "$path" 2>/dev/null)" && [[ "$links" =~ ^[0-9]+$ ]]; then
    printf '%s\n' "$links"
    return 0
  fi
  return 1
}

canonical_existing_dir() {
  local path=$1
  [[ -d "$path" ]] || return 1
  (cd "$path" && pwd -P)
}

canonical_target() {
  local path=$1
  local parent base

  [[ "$path" == /* ]] || die "Path must be absolute: $path"
  [[ "$path" != "/" ]] || {
    printf '/\n'
    return
  }
  parent="$(dirname "$path")"
  base="$(basename "$path")"
  [[ "$base" != "." && "$base" != ".." ]] || die "Unsafe target path: $path"
  parent="$(canonical_existing_dir "$parent")" ||
    die "Target parent does not exist: $(dirname "$path")"
  printf '%s/%s\n' "$parent" "$base"
}

path_is_within() {
  local child=$1
  local parent=$2
  [[ "$parent" == "/" && "$child" == /* ]] && return
  [[ "$child" == "$parent" || "$child" == "$parent/"* ]]
}

paths_overlap() {
  local first=$1
  local second=$2
  path_is_within "$first" "$second" || path_is_within "$second" "$first"
}

# The one staging location allowed inside the backup source: an explicit
# LU_BACKUP_TMPDIR at data/.backup-staging, on Linux only, so SQLite staging
# follows data/ onto its (future) dedicated volume and the per-database free
# space preflight measures the data filesystem. Every scan and restic phase
# excludes this directory; the scheduled unit creates it and it is gitignored.
staging_on_data_volume_allowed() {
  local tmp_real=$1
  local source_real=$2
  [[ "$(uname -s)" == Linux ]] || return 1
  [[ -n "${LU_BACKUP_TMPDIR:-}" ]] || return 1
  [[ "$tmp_real" == "$source_real/.backup-staging" ]]
}

resolve_legacy_dir() {
  local mount candidate

  if [[ -n "${LU_BACKUP_LEGACY_DIR:-}" ]]; then
    LEGACY_DIR="$(canonical_existing_dir "$LU_BACKUP_LEGACY_DIR")" ||
      die "LU_BACKUP_LEGACY_DIR is not an existing directory."
    return
  fi

  for mount in "$CLOUD_ROOT"/GoogleDrive-*; do
    candidate="$mount/My Drive/Projects/learn-ukrainian-data"
    if [[ -d "$candidate" ]]; then
      LEGACY_DIR="$(canonical_existing_dir "$candidate")"
      return
    fi
  done
}

validate_password_file() {
  local mode

  [[ -n "$PASSWORD_FILE" ]] ||
    die "RESTIC_PASSWORD_FILE must point to a mode-600 password file."
  [[ "$PASSWORD_FILE" == /* ]] ||
    die "RESTIC_PASSWORD_FILE must be an absolute path."
  [[ -f "$PASSWORD_FILE" ]] ||
    die "RESTIC_PASSWORD_FILE is set but the file does not exist."
  mode="$(file_mode "$PASSWORD_FILE")"
  (( (8#$mode & 077) == 0 )) ||
    die "Password file must not be accessible by group/others (mode is $mode)."
  export RESTIC_PASSWORD_FILE="$PASSWORD_FILE"
}

validate_repository_config() {
  local remote_spec remote_name remote_path

  [[ -n "$REPOSITORY" ]] ||
    die "Set LU_BACKUP_REPOSITORY to rclone:<remote>:<path>."
  [[ "$REPOSITORY" == rclone:*:* ]] ||
    die "LU_BACKUP_REPOSITORY must use restic's rclone:<remote>:<path> backend."

  remote_spec=${REPOSITORY#rclone:}
  remote_name=${remote_spec%%:*}
  remote_path=${remote_spec#*:}
  [[ -n "$remote_name" && "$remote_spec" == *:* && "${remote_spec#*:}" != "" ]] ||
    die "Invalid rclone repository. Expected rclone:<remote>:<path>."
  remote_path=${remote_path%/}
  case "$remote_path" in
    learn-ukrainian-data|*/learn-ukrainian-data)
      die "Refusing to initialize or write restic inside the legacy mutable backup path."
      ;;
  esac

  if ! rclone listremotes | grep -Fqx "$remote_name:"; then
    die "The rclone remote named in LU_BACKUP_REPOSITORY is not configured. Run 'rclone config' first."
  fi
  export RESTIC_REPOSITORY="$REPOSITORY"
}

validate_environment() {
  require_command restic "brew install restic"
  require_command rclone "brew install rclone"
  require_command sqlite3
  require_command find
  require_command git
  require_command jq "brew install jq"
  require_command realpath
  require_command touch
  require_command flock "brew install flock"
  check_restic_version
  validate_password_file
  validate_repository_config

  [[ "$PROJECT_ROOT" == /* ]] || die "LU_BACKUP_PROJECT_ROOT must be absolute."
  [[ -d "$PROJECT_ROOT" ]] || die "Project checkout does not exist: $PROJECT_ROOT"
  [[ -d "$SOURCE" ]] || die "Backup source does not exist: $SOURCE"
  [[ -d "$TMP_ROOT" ]] || die "Staging parent does not exist: $TMP_ROOT"
}

repository_is_initialized() {
  RESTIC_REPOSITORY="$REPOSITORY" \
    RESTIC_PASSWORD_FILE="$PASSWORD_FILE" \
    restic_repository_command cat config >/dev/null 2>&1
}

require_initialized_repository() {
  repository_is_initialized ||
    die "Restic repository is inaccessible or not initialized; verify remote authentication and repository status."
}

# A broken symlink carries no data; refusing the whole backup over one only
# loses every other path. Warn, exclude it, and record it in the receipt.
# Absolute and escaping links that do resolve still fail closed.
skip_broken_symlink() {
  local link=$1 label=$2 relative=$3 target=$4 reason=${5:-broken symlink}

  echo "WARNING: Skipping $reason in $label: $relative -> $target" >&2
  BROKEN_SYMLINK_EXCLUDES+=("$link")
}

# Legacy Drive links are named files, not a walk of data/. Other symlinks are
# checked only inside allowlisted directories.
validate_source_symlinks() {
  local name link target resolved relative

  [[ ! -L "$SOURCE" ]] || die "Backup source must not be a symlink: data"
  LEGACY_EXCLUDES=()
  for name in textbooks vesum; do
    link="$SOURCE/$name"
    [[ -L "$link" ]] || continue
    relative=$name
    target="$(readlink "$link")"
    if ! resolved="$(realpath "$link" 2>/dev/null)"; then
      LEGACY_EXCLUDES+=("$relative")
      echo "EXCLUDED legacy Drive symlink: $relative"
      continue
    fi
    [[ -n "$LEGACY_DIR" ]] ||
      die "Legacy symlink found but the legacy Drive directory is unavailable: $relative"
    path_is_within "$resolved" "$LEGACY_DIR" ||
      die "Known legacy symlink points outside the legacy backup: $relative -> $target"
    LEGACY_EXCLUDES+=("$relative")
    echo "EXCLUDED legacy Drive symlink: $relative -> $target"
  done
}

# Prune snapshot directories named by SNAPSHOT_EXCLUDE_ROOTS, then run find.
find_pruning_snapshot_dirs() {
  local root=$1
  shift
  local -a pruning=()
  local snapshot_root

  for snapshot_root in "${SNAPSHOT_EXCLUDE_ROOTS[@]}"; do
    pruning+=(
      \( -type d -name '*.snapshots' -path "$PROJECT_ROOT/$snapshot_root/*" -prune \) -o
    )
  done
  find "$root" "${pruning[@]}" "$@"
}

snapshot_path_is_excluded() {
  local relative=$1 snapshot_root

  for snapshot_root in "${SNAPSHOT_EXCLUDE_ROOTS[@]}"; do
    [[ "$relative" == "$snapshot_root"/* && "$relative" == *.snapshots/* ]] && return 0
  done
  return 1
}

# Every allowlist content walk prunes the same trees restic excludes:
# task snapshot directories, bytecode, ephemeral homes, and staging.
allowlist_find() {
  local root=$1
  shift

  find_pruning_snapshot_dirs "$root" \
    \( -type d \( -name '__pycache__' -o -name '*-home' \) -prune \) -o \
    \( -type d -path "$PROJECT_ROOT/batch_state/review-receipts/*" -name home -prune \) -o \
    \( -path "$TMP_ROOT" -prune \) -o \
    "$@"
}

validate_tree_symlinks() {
  local tree=$1
  local label=$2
  local link relative target resolved tree_real

  [[ ! -L "$tree" ]] || die "Backup root must not be a symlink: $label"
  tree_real="$(canonical_existing_dir "$tree")"
  while IFS= read -r -d '' link; do
    is_ephemeral_home_path "$link" && continue
    relative=${link#"$tree"/}
    target="$(readlink "$link")"
    if [[ ! -e "$link" ]] || ! resolved="$(realpath "$link" 2>/dev/null)"; then
      skip_broken_symlink "$link" "$label" "$relative" "$target"
      continue
    fi
    if [[ "$target" == /* ]]; then
      if [[ "$label" == "batch_state" || "$label" == batch_state/* ]]; then
        skip_broken_symlink "$link" "$label" "$relative" "$target" "absolute symlink"
        continue
      fi
      die "Absolute symlink is not backup-safe in $label: $relative -> $target"
    fi
    if ! path_is_within "$resolved" "$tree_real"; then
      if [[ "$label" == "batch_state" || "$label" == batch_state/* ]]; then
        skip_broken_symlink "$link" "$label" "$relative" "$target" "escaping symlink"
        continue
      fi
      die "Symlink escapes $label: $relative -> $target"
    fi
  done < <(allowlist_find "$tree" -type l -print0)
}

discover_ephemeral_homes() {
  local root home
  EPHEMERAL_HOME_EXCLUDES=()
  for root in "${ALLOWLIST_TREE_ROOTS[@]+"${ALLOWLIST_TREE_ROOTS[@]}"}"; do
    [[ "$root" == batch_state || "$root" == batch_state/* ]] || continue
    while IFS= read -r -d '' home; do
      EPHEMERAL_HOME_EXCLUDES+=("$home")
    done < <(find_pruning_snapshot_dirs "$PROJECT_ROOT/$root" \( -type d -o -type l \) -name '*-home' -prune -print0)
  done
  if [[ -d "$PROJECT_ROOT/batch_state/review-receipts" && ! -L "$PROJECT_ROOT/batch_state/review-receipts" ]]; then
    while IFS= read -r -d '' home; do
      EPHEMERAL_HOME_EXCLUDES+=("$home")
    done < <(find_pruning_snapshot_dirs "$PROJECT_ROOT/batch_state/review-receipts" \( -type d -o -type l \) -name home -prune -print0)
  fi
}

is_ephemeral_home_path() {
  local path=$1 home
  case "$path" in
    "$PROJECT_ROOT/batch_state/"*-home|"$PROJECT_ROOT/batch_state/"*-home/*|\
    "$PROJECT_ROOT/batch_state/review-receipts/"*/home|\
    "$PROJECT_ROOT/batch_state/review-receipts/"*/home/*) return 0 ;;
  esac
  for home in "${EPHEMERAL_HOME_EXCLUDES[@]}"; do
    path_is_within "$path" "$home" && return 0
  done
  return 1
}

validate_tree_file_types() {
  local tree=$1
  local label=$2
  local entry relative

  while IFS= read -r -d '' entry; do
    is_ephemeral_home_path "$entry" && continue
    relative=${entry#"$tree"/}
    die "Unsupported special file type in $label: $relative"
  done < <(allowlist_find "$tree" ! -type d ! -type f ! -type l -print0)
}

# The nightly walks only scripts/config/backup-allowlist.json keep entries.
# Drop entries are not exclusion rules: the script never opens them, so the
# kept file data/lexicon/cache/ulif_raw.sqlite is not cancelled by the dropped
# parent data/lexicon/cache.
validate_allowlist_file() {
  [[ -f "$ALLOWLIST_FILE" && ! -L "$ALLOWLIST_FILE" ]] ||
    die "Backup allowlist is missing: $ALLOWLIST_FILE"
  if ! jq -e '
    .version == 1
    and (.keep | type == "array" and length > 0)
    and (.drop | type == "array" and length > 0)
    and ((.keep + .drop) | all(
      (.path | type == "string"
        and length > 0
        and (startswith("/") | not)
        and (contains("..") | not)
        and (test("[\n\r\t]") | not))
      and (.kind | IN("epic_glob", "tree", "file", "glob_files", "task_records"))
      and (.required | type == "boolean")
      and (.action | IN("keep", "drop"))
      and (.reason | type == "string" and length > 0)
    ))
    and ((.keep | map(.path) | unique | length) == (.keep | length))
    and ((.drop | map(.path) | unique | length) == (.drop | length))
    and ([.keep[].action] | all(. == "keep"))
    and ([.drop[].action] | all(. == "drop"))
  ' "$ALLOWLIST_FILE" >/dev/null; then
    die "Backup allowlist is invalid: $ALLOWLIST_FILE"
  fi
}

allowlist_absent() {
  local path=$1 required=$2

  if [[ "$required" == true ]]; then
    die "Required recovery path is missing: $path"
  fi
  info "Optional backup path is absent: $path"
}

refuse_leaf_symlink() {
  local path=$1 required=$2

  [[ -L "$PROJECT_ROOT/$path" ]] || return 0
  if [[ "$required" == true ]]; then
    die "Required recovery path must not be a symlink: $path"
  fi
  die "Recovery path must not be a symlink: $path"
}

# Ancestors of an allowlisted path must be real directories. The leaf is
# checked by the expander so a required symlink keeps its existing message.
refuse_path_ancestors() {
  local relative=$1
  local accumulator="" part index
  local -a parts=()

  IFS=/ read -r -a parts <<< "$relative"
  for ((index = 0; index < ${#parts[@]} - 1; index++)); do
    part=${parts[$index]}
    [[ "$part" == *'*'* || "$part" == *'?'* || "$part" == '['* ]] && return 0
    if [[ -n "$accumulator" ]]; then
      accumulator="$accumulator/$part"
    else
      accumulator=$part
    fi
    [[ ! -L "$PROJECT_ROOT/$accumulator" ]] || {
      case "$accumulator" in
        .claude) die "Recovery parent must not be a symlink: .claude" ;;
        data) die "Backup source must not be a symlink: data" ;;
        batch_state) die "Recovery path must not have a symlink parent: batch_state" ;;
        *) die "Recovery path must not have a symlink parent: $accumulator" ;;
      esac
    }
  done
}

is_backup_sidecar() {
  local base=${1##*/}

  case "$base" in
    .DS_Store|*.db-wal|*.db-shm|*.db-journal|*.sqlite*-wal|*.sqlite*-shm|*.sqlite*-journal)
      return 0
      ;;
  esac
  return 1
}

# Task records are the named extensions, plus every regular file under
# batch_state/tasks/archive. Lock files and *.snapshots directories under
# batch_state/tasks are not records. Those snapshot directories are the only
# ones excluded, and discovery does not walk them.
task_record_is_staged() {
  local relative=$1
  local base=${relative##*/}

  [[ "$base" == *.lock ]] && return 1
  [[ "$relative" == batch_state/tasks/archive/* ]] && return 0
  case "$base" in
    *.json|*.result|*.diag|*.md|*.prompt) return 0 ;;
  esac
  return 1
}

note_selected_file() {
  local absolute=$1
  local relative=${absolute#"$PROJECT_ROOT"/}

  ENUMERATED_RELATIVE_PATHS+=("$relative")
  ENUMERATED_FILE_COUNT=$((ENUMERATED_FILE_COUNT + 1))
  if is_backup_sidecar "$relative"; then
    return 0
  fi
  if [[ "$relative" == batch_state/tasks/* ]] && ! task_record_is_staged "$relative"; then
    return 0
  fi
  STAGED_CANDIDATES+=("$relative")
}

# Regular files under one allowlisted root. Do not follow symlinks. Prune the
# same trees allowlist_find prunes, including snapshot directories only under
# SNAPSHOT_EXCLUDE_ROOTS.
find_regular_files() {
  local root=$1

  allowlist_find "$root" -type f -print0
}

walk_tree_files() {
  local root=$1
  local file

  while IFS= read -r -d '' file; do
    note_selected_file "$file"
  done < <(find_regular_files "$root")
}

reject_non_sqlite_name() {
  local relative=$1
  local absolute=$2

  case "$relative" in
    *.sqlite|*.sqlite3)
      is_sqlite_database "$absolute" ||
        die "Allowlist entry is not a SQLite database: $relative"
      ;;
  esac
}

expand_tree() {
  local relative=$1 required=$2
  local absolute="$PROJECT_ROOT/$relative"

  refuse_path_ancestors "$relative"
  if [[ ! -e "$absolute" && ! -L "$absolute" ]]; then
    allowlist_absent "$relative" "$required"
    return 0
  fi
  refuse_leaf_symlink "$relative" "$required"
  [[ -d "$absolute" ]] || die "Allowlist tree is not a directory: $relative"
  BACKUP_PATHS+=("$relative")
  ALLOWLIST_TREE_ROOTS+=("$relative")
  walk_tree_files "$absolute"
}

expand_file() {
  local relative=$1 required=$2
  local absolute="$PROJECT_ROOT/$relative"

  refuse_path_ancestors "$relative"
  if [[ ! -e "$absolute" && ! -L "$absolute" ]]; then
    allowlist_absent "$relative" "$required"
    return 0
  fi
  refuse_leaf_symlink "$relative" "$required"
  [[ -f "$absolute" ]] || die "Allowlist file is not a regular file: $relative"
  reject_non_sqlite_name "$relative" "$absolute"
  BACKUP_PATHS+=("$relative")
  ALLOWLIST_FILE_ROOTS+=("$relative")
  note_selected_file "$absolute"
}

expand_glob_files() {
  local pattern=$1 required=$2
  local directory=${pattern%/*}
  local base=${pattern##*/}
  local absolute match relative count=0
  local -a matches=()

  [[ "$directory" != "$pattern" ]] || die "Allowlist glob must name a parent directory: $pattern"
  refuse_path_ancestors "$directory/placeholder"
  absolute="$PROJECT_ROOT/$directory"
  if [[ -L "$absolute" ]]; then
    die "Recovery path must not be a symlink: $directory"
  fi
  if [[ ! -d "$absolute" ]]; then
    allowlist_absent "$pattern" "$required"
    return 0
  fi
  shopt -s nullglob
  # shellcheck disable=SC2206 # the basename is an allowlisted glob, one word
  matches=("$absolute"/$base)
  shopt -u nullglob
  for match in "${matches[@]+"${matches[@]}"}"; do
    [[ -n "$match" && -f "$match" && ! -L "$match" ]] || continue
    relative=${match#"$PROJECT_ROOT"/}
    reject_non_sqlite_name "$relative" "$match"
    BACKUP_PATHS+=("$relative")
    ALLOWLIST_FILE_ROOTS+=("$relative")
    note_selected_file "$match"
    count=$((count + 1))
  done
  if [[ "$count" -eq 0 ]]; then
    allowlist_absent "$pattern" "$required"
  fi
}

expand_epic_glob() {
  local pattern=$1 required=$2
  local epic name relative count=0

  [[ "$pattern" == ".claude/*-epic" ]] ||
    die "Unsupported epic allowlist pattern: $pattern"
  refuse_path_ancestors ".claude/placeholder"
  shopt -s nullglob
  for epic in "$PROJECT_ROOT"/.claude/*-epic; do
    name=$(basename "$epic")
    [[ "$name" =~ ^[a-z0-9-]+-epic$ ]] ||
      die "Epic recovery path has an unsafe label: $name"
    if [[ -L "$epic" ]]; then
      die "Epic recovery path must not be a symlink: .claude/$name"
    fi
    [[ -d "$epic" ]] || continue
    relative=".claude/$name"
    BACKUP_PATHS+=("$relative")
    ALLOWLIST_TREE_ROOTS+=("$relative")
    walk_tree_files "$epic"
    count=$((count + 1))
  done
  shopt -u nullglob
  if [[ "$count" -eq 0 ]]; then
    allowlist_absent "$pattern" "$required"
  fi
}

# Pass the archive directory, plus record files outside it. The tasks
# directory itself is not a restic root: locks and non-record files must not
# ride along with it.
expand_task_records() {
  local relative=$1 required=$2
  local absolute="$PROJECT_ROOT/$relative"
  local archive="$absolute/archive"
  local candidate

  refuse_path_ancestors "$relative"
  if [[ ! -e "$absolute" && ! -L "$absolute" ]]; then
    allowlist_absent "$relative" "$required"
    return 0
  fi
  refuse_leaf_symlink "$relative" "$required"
  [[ -d "$absolute" ]] || die "Allowlist tree is not a directory: $relative"
  walk_tree_files "$absolute"
  if [[ -L "$archive" ]]; then
    die "Recovery path must not be a symlink: $relative/archive"
  fi
  if [[ -d "$archive" ]]; then
    BACKUP_PATHS+=("$relative/archive")
    ALLOWLIST_TREE_ROOTS+=("$relative/archive")
  fi
  for candidate in "${STAGED_CANDIDATES[@]+"${STAGED_CANDIDATES[@]}"}"; do
    [[ "$candidate" == "$relative"/* ]] || continue
    [[ "$candidate" == "$relative"/archive/* ]] && continue
    BACKUP_PATHS+=("$candidate")
    ALLOWLIST_FILE_ROOTS+=("$candidate")
  done
}

discover_backup_paths() {
  local path kind required

  BACKUP_PATHS=()
  ENUMERATED_FILE_COUNT=0
  ENUMERATED_RELATIVE_PATHS=()
  STAGED_CANDIDATES=()
  STAGED_RELATIVE_PATHS=()
  ALLOWLIST_TREE_ROOTS=()
  ALLOWLIST_FILE_ROOTS=()
  validate_allowlist_file
  while IFS=$'\t' read -r path kind required; do
    case "$kind" in
      epic_glob) expand_epic_glob "$path" "$required" ;;
      tree) expand_tree "$path" "$required" ;;
      file) expand_file "$path" "$required" ;;
      glob_files) expand_glob_files "$path" "$required" ;;
      task_records) expand_task_records "$path" "$required" ;;
      *) die "Unknown allowlist kind: $kind" ;;
    esac
  done < <(jq -r '.keep[] | [.path, .kind, (.required | tostring)] | @tsv' "$ALLOWLIST_FILE")
  info "Allowlist enumerated files: ${ENUMERATED_FILE_COUNT}"
}

path_is_allowlist_tree() {
  local relative=$1 root

  for root in "${ALLOWLIST_TREE_ROOTS[@]+"${ALLOWLIST_TREE_ROOTS[@]}"}"; do
    path_is_within "$relative" "$root" && return 0
  done
  return 1
}

# Untracked files outside an allowlisted tree do not fail the run. A file
# inside a selected tree that no backup path covers still fails closed.
untracked_path_is_uncovered() {
  local relative=$1

  path_is_allowlist_tree "$relative" || return 1
  path_has_backup_coverage "$relative" && return 1
  return 0
}

finalize_staged_paths() {
  local relative database
  local -A drop=()

  STAGED_RELATIVE_PATHS=()
  for database in \
    "${SQLITE_TRANSIENT_SOURCES[@]+"${SQLITE_TRANSIENT_SOURCES[@]}"}" \
    "${SQLITE_ARCHIVED_SOURCES[@]+"${SQLITE_ARCHIVED_SOURCES[@]}"}"; do
    drop[${database#"$PROJECT_ROOT"/}]=1
  done
  for relative in "${STAGED_CANDIDATES[@]+"${STAGED_CANDIDATES[@]}"}"; do
    [[ -z "${drop[$relative]+set}" ]] || continue
    STAGED_RELATIVE_PATHS+=("$relative")
  done
}

publish_selection_manifest() {
  [[ -n "${LU_BACKUP_SELECTION_MANIFEST:-}" ]] || return 0
  [[ "${LU_BACKUP_SELECTION_MANIFEST}" != *$'\n'* ]] ||
    die "LU_BACKUP_SELECTION_MANIFEST must not contain a newline."
  [[ "${LU_BACKUP_SELECTION_MANIFEST}" == /* ]] ||
    die "LU_BACKUP_SELECTION_MANIFEST must be absolute."
  {
    printf 'enumerated %s\n' "$ENUMERATED_FILE_COUNT"
    if ((${#ENUMERATED_RELATIVE_PATHS[@]} > 0)); then
      printf '%s\n' "${ENUMERATED_RELATIVE_PATHS[@]}" | LC_ALL=C sort -u | sed 's/^/seen /'
    fi
    if ((${#STAGED_RELATIVE_PATHS[@]} > 0)); then
      printf '%s\n' "${STAGED_RELATIVE_PATHS[@]}" | LC_ALL=C sort -u | sed 's/^/staged /'
    fi
  } > "$LU_BACKUP_SELECTION_MANIFEST" ||
    die "Could not write the backup selection manifest."
}

# Directory paths stay on argv. File paths stay on argv until there are more
# than 50, then they move to a NUL-delimited --files-from-raw list so a name
# containing a newline stays one path. restic rejects an empty name in that
# list, and a NUL would end the name early. The list is created here, in the
# current shell: a later pipeline must not create it, or the EXIT trap never
# learns the path. When the stage directory already exists the list lives
# inside it, which that trap deletes even if this assignment is lost.
build_restic_selection_args() {
  local relative absolute list_file
  local -a directories=() files=()

  RESTIC_SELECTION_ARGS=()
  for relative in "${BACKUP_PATHS[@]+"${BACKUP_PATHS[@]}"}"; do
    [[ "$relative" == GIT-WORKTREE.patch || "$relative" == BACKUP-RECEIPT.json ]] && continue
    # A classified database is uploaded from its consistent online copy, or
    # skipped. Naming the live file here would store that stale main file in
    # the base snapshot as well; restic does not exclude an explicit path.
    [[ -z "${CLASSIFIED_SQLITE_RELATIVE[$relative]+set}" ]] || continue
    absolute="$PROJECT_ROOT/$relative"
    if [[ -d "$absolute" && ! -L "$absolute" ]]; then
      directories+=("$relative")
    else
      files+=("$relative")
    fi
  done
  RESTIC_SELECTION_ARGS=("${directories[@]+"${directories[@]}"}")
  if ((${#files[@]} > 50)); then
    if [[ -n "$STAGE_DIR" && -d "$STAGE_DIR" && ! -L "$STAGE_DIR" ]]; then
      list_file="$STAGE_DIR/restic-files-from"
      : > "$list_file" || die "Could not write the restic file list."
    else
      list_file="$(mktemp "${TMP_ROOT}/learn-ukrainian-backup-files.XXXXXX")" ||
        die "Could not create the restic file list."
    fi
    FILES_FROM_FILE="$list_file"
    for relative in "${files[@]}"; do
      # restic --files-from-raw rejects an empty name. A NUL cannot be stored
      # in a shell variable, so every non-empty path is representable.
      [[ -n "$relative" ]] ||
        die "Cannot express an empty backup path in the restic file list."
      printf '%s\0' "$relative" >> "$list_file" ||
        die "Could not write the restic file list."
    done
    RESTIC_SELECTION_ARGS+=(--files-from-raw "$list_file")
  elif ((${#files[@]} > 0)); then
    RESTIC_SELECTION_ARGS+=("${files[@]}")
  fi
  RESTIC_SELECTION_READY=1
}

# Extra restic arguments follow. Call build_restic_selection_args in this
# shell first when the backup command is on the left of a pipeline.
backup_selected_paths() {
  [[ "$RESTIC_SELECTION_READY" -eq 1 ]] || build_restic_selection_args
  (
    cd "$PROJECT_ROOT" || die "Could not enter the project root."
    restic_repository_command backup \
      "${RESTIC_SELECTION_ARGS[@]+"${RESTIC_SELECTION_ARGS[@]}"}" "$@"
  )
}
path_has_backup_coverage() {
  local relative=$1
  local backup_path

  for backup_path in "${BACKUP_PATHS[@]+"${BACKUP_PATHS[@]}"}"; do
    path_is_within "$relative" "$backup_path" && return 0
  done
  return 1
}

validate_untracked_coverage() {
  local relative uncovered=0

  while IFS= read -r -d '' relative; do
    untracked_path_is_uncovered "$relative" || continue
    echo "UNBACKED untracked Git path: $relative" >&2
    uncovered=$((uncovered + 1))
  done < <(git_command -C "$PROJECT_ROOT" ls-files --others --exclude-standard -z)
  [[ "$uncovered" -eq 0 ]] ||
    die "$uncovered untracked path(s) are outside Git and declared recovery roots."
}

validate_source() {
  local source_real repo_real project_real tmp_real git_root relative

  source_real="$(canonical_existing_dir "$SOURCE")"
  repo_real="$(canonical_existing_dir "$REPO_ROOT")"
  project_real="$(canonical_existing_dir "$PROJECT_ROOT")"
  tmp_real="$(canonical_existing_dir "$TMP_ROOT")"
  git_root="$(git_command -C "$PROJECT_ROOT" rev-parse --show-toplevel 2>/dev/null)" ||
    die "Project root is not a Git checkout: $PROJECT_ROOT"
  git_root="$(canonical_existing_dir "$git_root")"
  [[ "$git_root" == "$project_real" ]] ||
    die "LU_BACKUP_PROJECT_ROOT must be the Git checkout root."

  if ! staging_on_data_volume_allowed "$tmp_real" "$source_real"; then
    paths_overlap "$source_real" "$tmp_real" &&
      die "Staging directory and backup source overlap."
    paths_overlap "$repo_real" "$tmp_real" &&
      die "Staging directory must be outside the project checkout."
    paths_overlap "$project_real" "$tmp_real" &&
      die "Staging directory must be outside the selected project checkout."
  fi
  [[ "$source_real" != "$project_real" ]] ||
    die "Refusing to back up the entire repository as data/."
  resolve_legacy_dir
  BROKEN_SYMLINK_EXCLUDES=()
  discover_backup_paths
  discover_ephemeral_homes
  validate_untracked_coverage
  validate_source_symlinks
  for relative in "${BACKUP_PATHS[@]+"${BACKUP_PATHS[@]}"}"; do
    [[ "$relative" != "GIT-WORKTREE.patch" && "$relative" != "BACKUP-RECEIPT.json" ]] || continue
    [[ -d "$PROJECT_ROOT/$relative" && ! -L "$PROJECT_ROOT/$relative" ]] || continue
    validate_tree_symlinks "$PROJECT_ROOT/$relative" "$relative"
    validate_tree_file_types "$PROJECT_ROOT/$relative" "$relative"
  done
  refuse_hardlinked_sqlite_aliases
}

acquire_lock() {
  [[ "$LOCK_WAIT_SECONDS" =~ ^[0-9]+$ ]] || die "LU_BACKUP_LOCK_WAIT_SECONDS must be whole seconds."
  [[ -d "$LOCK_ROOT" ]] || die "Backup lock directory does not exist: $LOCK_ROOT"
  [[ ! -L "$LOCK_FILE" ]] || die "Refusing symlink at backup lock path: $LOCK_FILE"
  exec {LOCK_FD}>>"$LOCK_FILE" || die "Could not open backup lock file: $LOCK_FILE"
  if ! flock -n "$LOCK_FD"; then
    info "waiting for lock (up to ${LOCK_WAIT_SECONDS}s): $LOCK_FILE"
    if ! flock -w "$LOCK_WAIT_SECONDS" "$LOCK_FD"; then
      die "Timed out after ${LOCK_WAIT_SECONDS}s waiting for backup lock: $LOCK_FILE"
    fi
  fi
  # A killed backup can leave private staging; only the lock holder may clear it.
  [[ ! -L "$STAGE_PATH" ]] || die "Refusing symlink at the private staging path: $STAGE_PATH"
  if [[ -d "$STAGE_PATH" ]]; then
    find "$STAGE_PATH" -depth -delete || die "Could not clear stale private staging: $STAGE_PATH"
  elif [[ -e "$STAGE_PATH" ]]; then
    die "Private staging path is not a directory: $STAGE_PATH"
  fi
}

# SQLite discovery follows the allowlist enumeration. Dropped trees are never
# opened, including the old whole-data scan.
list_sqlite_sources() {
  local relative absolute base

  for relative in "${STAGED_CANDIDATES[@]+"${STAGED_CANDIDATES[@]}"}"; do
    absolute="$PROJECT_ROOT/$relative"
    is_ephemeral_home_path "$absolute" && continue
    [[ "$relative" == */__pycache__/* ]] && continue
    base=${relative##*/}
    case "$base" in
      *.db|*.sqlite|*.sqlite3|*.sqlite*) ;;
      *) continue ;;
    esac
    case "$base" in
      *-wal|*-shm|*-journal) continue ;;
    esac
    is_sqlite_database "$absolute" && printf '%s\0' "$absolute"
  done
}

is_sqlite_database() {
  local database=$1
  head -c 16 "$database" 2>/dev/null | cmp -s - <(printf 'SQLite format 3\0')
}

# Per-run test scratch: a database anywhere under a pytest base temp
# directory (pytest-of-<user>, --basetemp pytest-RC, pytest-HEAD, ...). It is
# throwaway test state, so it is neither uploaded nor kept in the file phase.
is_transient_sqlite_path() {
  local relative=/${1#"$PROJECT_ROOT"/}
  [[ "$relative" == */pytest-*/* ]]
}

# Sidecars are named beside the path SQLite opened, not beside every hard
# link of the inode. Publishing the other name stores the main file and drops
# committed WAL rows. Refuse before any snapshot is written.
refuse_hardlinked_sqlite_aliases() {
  local relative absolute links

  for relative in "${STAGED_CANDIDATES[@]+"${STAGED_CANDIDATES[@]}"}"; do
    absolute="$PROJECT_ROOT/$relative"
    [[ -f "$absolute" && ! -L "$absolute" ]] || continue
    is_ephemeral_home_path "$absolute" && continue
    [[ "$relative" == */__pycache__/* ]] && continue
    is_transient_sqlite_path "$absolute" && continue
    is_sqlite_database "$absolute" || continue
    links="$(file_link_count "$absolute")" ||
      die "Could not read the link count of SQLite database: $relative"
    if ((links > 1)); then
      die "Refusing hard-linked SQLite database $relative (link count ${links}). Remove the extra name and retry; sidecars follow the path SQLite opened, so this alias would omit committed WAL rows."
    fi
  done
}

# Read NAME.tar.zst.manifest files from DB_ARCHIVE_DIR. Format:
#   # lu-backup-db-archive v1
#   # archive_bytes: <size of NAME.tar.zst>
#   # files: <number of entries below>
#   <size>\t<mtime epoch seconds>\t<project-relative database path>
# A manifest is used only when its archive is a regular file inside a backup
# root with exactly the recorded size and the entry count matches; otherwise it
# is ignored with a warning and every listed database is backed up loose.
load_db_archive_manifests() {
  local manifest archive name line header_bytes header_files actual_bytes count
  local size mtime relative archive_relative
  local -a entries

  ARCHIVED_DB_STAT=()
  ARCHIVED_DB_ARCHIVE=()
  [[ -d "$DB_ARCHIVE_DIR" && ! -L "$DB_ARCHIVE_DIR" ]] || return 0
  # The default archive directory is outside the allowlist. Return before the
  # glob so a dropped directory is never read and never warned about.
  archive_relative=${DB_ARCHIVE_DIR#"$PROJECT_ROOT"/}
  if [[ "$archive_relative" == "$DB_ARCHIVE_DIR" || "$archive_relative" == /* ]] ||
    ! path_has_backup_coverage "$archive_relative"; then
    return 0
  fi
  for manifest in "$DB_ARCHIVE_DIR"/*.tar.zst.manifest; do
    [[ -f "$manifest" && ! -L "$manifest" ]] || continue
    archive=${manifest%.manifest}
    name=$(basename "$archive")
    archive_relative=${archive#"$PROJECT_ROOT"/}
    if [[ "$archive_relative" == "$archive" ]] || ! path_has_backup_coverage "$archive_relative"; then
      echo "WARNING: Ignoring SQLite archive outside the backup roots: $name" >&2
      continue
    fi
    if [[ -L "$archive" || ! -f "$archive" ]]; then
      echo "WARNING: Ignoring SQLite archive manifest without its archive: $name" >&2
      continue
    fi
    header_bytes=""
    header_files=""
    entries=()
    while IFS= read -r line || [[ -n "$line" ]]; do
      case "$line" in
        '# archive_bytes: '*) header_bytes=${line#'# archive_bytes: '} ;;
        '# files: '*) header_files=${line#'# files: '} ;;
        '#'*|'') ;;
        *) entries+=("$line") ;;
      esac
    done < "$manifest"
    actual_bytes="$(stat -c '%s' "$archive" 2>/dev/null || stat -f '%z' "$archive")"
    count=${#entries[@]}
    if [[ ! "$header_bytes" =~ ^[0-9]+$ || "$header_bytes" != "$actual_bytes" ||
          ! "$header_files" =~ ^[0-9]+$ || "$header_files" -ne "$count" ]]; then
      echo "WARNING: Ignoring SQLite archive whose manifest does not match it: $name" >&2
      continue
    fi
    for line in "${entries[@]}"; do
      IFS=$'\t' read -r size mtime relative <<< "$line"
      [[ "$size" =~ ^[0-9]+$ && "$mtime" =~ ^[0-9]+$ && -n "$relative" ]] || {
        echo "WARNING: Skipping malformed SQLite archive manifest entry in $name" >&2
        continue
      }
      ARCHIVED_DB_STAT["$relative"]="$size $mtime"
      ARCHIVED_DB_ARCHIVE["$relative"]=$name
    done
  done
}

# Split list_sqlite_sources into uploaded, transient, and archived databases.
classify_sqlite_sources() {
  local database relative current name classified
  local -A used=()

  SQLITE_BACKUP_SOURCES=()
  SQLITE_TRANSIENT_SOURCES=()
  SQLITE_ARCHIVED_SOURCES=()
  DB_ARCHIVES_USED=()
  CLASSIFIED_SQLITE_RELATIVE=()
  load_db_archive_manifests
  while IFS= read -r -d '' database; do
    relative=${database#"$PROJECT_ROOT"/}
    if is_transient_sqlite_path "$database"; then
      SQLITE_TRANSIENT_SOURCES+=("$database")
      continue
    fi
    if [[ -n "${ARCHIVED_DB_STAT[$relative]+set}" ]]; then
      current="$(stat -c '%s %Y' "$database" 2>/dev/null || stat -f '%z %m' "$database")"
      if [[ "$current" == "${ARCHIVED_DB_STAT[$relative]}" ]]; then
        SQLITE_ARCHIVED_SOURCES+=("$database")
        name=${ARCHIVED_DB_ARCHIVE[$relative]}
        if [[ -z "${used[$name]+set}" ]]; then
          used[$name]=1
          DB_ARCHIVES_USED+=("$name")
        fi
        continue
      fi
      echo "WARNING: SQLite database changed since it was archived; backing up the live copy: $relative" >&2
    fi
    SQLITE_BACKUP_SOURCES+=("$database")
  done < <(list_sqlite_sources)
  for classified in \
    "${SQLITE_BACKUP_SOURCES[@]+"${SQLITE_BACKUP_SOURCES[@]}"}" \
    "${SQLITE_TRANSIENT_SOURCES[@]+"${SQLITE_TRANSIENT_SOURCES[@]}"}" \
    "${SQLITE_ARCHIVED_SOURCES[@]+"${SQLITE_ARCHIVED_SOURCES[@]}"}"; do
    CLASSIFIED_SQLITE_RELATIVE[${classified#"$PROJECT_ROOT"/}]=1
  done
  info "SQLite sources: ${#SQLITE_BACKUP_SOURCES[@]} to back up, ${#SQLITE_TRANSIENT_SOURCES[@]} pytest scratch skipped, ${#SQLITE_ARCHIVED_SOURCES[@]} covered by ${#DB_ARCHIVES_USED[@]} archive(s)."
  finalize_staged_paths
  publish_selection_manifest
}

# Exclude every classified database from the file phase; uploaded ones go
# through the online-backup phase, the others are skipped or archived.
add_classified_sqlite_excludes() {
  local database
  for database in "${SQLITE_BACKUP_SOURCES[@]}" "${SQLITE_TRANSIENT_SOURCES[@]}" "${SQLITE_ARCHIVED_SOURCES[@]}"; do
    add_sqlite_exclude "$database"
  done
}

unreadable_backup_paths() {
  local relative root found path
  for relative in "${BACKUP_PATHS[@]}"; do
    [[ "$relative" == GIT-WORKTREE.patch || "$relative" == BACKUP-RECEIPT.json ]] && continue
    root="$(source_for_backup_path "$relative")"
    # Prune inaccessible directories so find can continue through other roots.
    # Capture any remaining permission errors without propagating find's status
    # into the caller's command substitution under set -e.
    found="$(LC_ALL=C allowlist_find "$root" \
      \( -type d \( ! -readable -o ! -executable \) -print -prune \) -o \
      \( -type f ! -readable -print \) 2>&1)" || true
    [[ -n "$found" ]] || continue
    while IFS= read -r path; do
      if [[ "$path" == 'find: '* ]]; then
        if [[ "$path" == *': Permission denied' ]]; then
          path="${path#find: }"
          path="${path%: Permission denied}"
          path="${path:1:${#path}-2}"
        else
          path="$root"
        fi
      fi
      printf '%s\n' "$path"
    done <<< "$found"
  done
}

db_size_bytes() {
  local total=0 database size

  while IFS= read -r -d '' database; do
    if size="$(stat -f '%z' "$database" 2>/dev/null)"; then
      :
    else
      size="$(stat -c '%s' "$database")"
    fi
    total=$((total + size))
  done < <(list_sqlite_sources)
  printf '%s\n' "$total"
}

available_kib() {
  df -Pk "$TMP_ROOT" | awk 'NR == 2 {print $4}'
}

check_staging_space() {
  local source_bytes db_bytes required_kib free_kib
  local -r safety_kib=$((2 * 1024 * 1024))

  source_bytes="$(backup_tree_size_bytes)"
  db_bytes="$(db_size_bytes)"
  required_kib=$(((source_bytes + db_bytes + 1023) / 1024 + safety_kib))
  free_kib="$(available_kib)"
  [[ "$free_kib" =~ ^[0-9]+$ ]] || die "Could not determine staging free space."
  ((free_kib >= required_kib)) ||
    die "Insufficient staging space: need at least ${required_kib} KiB, have ${free_kib} KiB."
}

check_one_db_space() {
  local database=$1 relative=$2 size wal_size=0 free_kib required_kib
  local -r safety_kib=$((2 * 1024 * 1024))
  size="$(stat -c '%s' "$database")"
  if [[ -f "$database-wal" ]]; then
    wal_size="$(stat -c '%s' "$database-wal")"
  fi
  required_kib=$(((size + wal_size + 1023) / 1024 + safety_kib))
  free_kib="$(available_kib)"
  [[ "$free_kib" =~ ^[0-9]+$ ]] || die "Could not determine staging free space."
  ((free_kib >= required_kib)) ||
    die "Insufficient staging space for $relative: need at least ${required_kib} KiB, have ${free_kib} KiB."
}

clone_tree() {
  local source=$1
  local destination=$2
  local source_device destination_device

  case "$(uname -s)" in
    Darwin)
      source_device="$(filesystem_device "$source")" ||
        die "Could not determine source volume for copy-on-write staging: $source"
      destination_device="$(filesystem_device "$(dirname "$destination")")" ||
        die "Could not determine staging volume for copy-on-write staging: $destination"
      [[ "$source_device" == "$destination_device" ]] ||
        die "APFS copy-on-write staging requires source and staging on the same volume."
      /bin/cp -cRp "$source" "$destination" ||
        die "APFS copy-on-write staging failed; refusing a full data copy."
      ;;
    Linux)
      die "Linux whole-tree staging is disabled; databases must use sequential online backups."
      ;;
    *)
      die "Copy-on-write staging is unsupported on this operating system."
      ;;
  esac
}

sqlite_backup_command() {
  local source_db=$1
  local destination_db=$2
  local immutable_check readonly_error source_uri

  [[ "$source_db" != *"'"* && "$destination_db" != *"'"* ]] ||
    die "SQLite backup paths may not contain a single quote."
  if readonly_error="$(
    sqlite3 -readonly "$source_db" ".backup '$destination_db'" 2>&1
  )"; then
    return
  fi

  if [[ ! -e "$source_db-wal" && ! -e "$source_db-shm" && ! -e "$source_db-journal" ]]; then
    source_uri=${source_db//%/%25}
    source_uri=${source_uri//#/%23}
    source_uri=${source_uri//\?/%3F}
    source_uri="file:$source_uri?mode=ro&immutable=1"
    if immutable_check="$(
      sqlite3 "$source_uri" 'PRAGMA quick_check;' 2>/dev/null
    )" && [[ "$immutable_check" == "ok" ]]; then
      info "Using verified immutable fallback for SQLite source without journal sidecars."
      sqlite3 "$source_uri" ".backup '$destination_db'"
      return
    fi
  fi

  [[ -z "$readonly_error" ]] || printf '%s\n' "$readonly_error" >&2
  return 1
}

sqlite_immutable_uri() {
  local path=$1
  path=${path//%/%25}
  path=${path//#/%23}
  path=${path//\?/%3F}
  printf 'file:%s?mode=ro&immutable=1\n' "$path"
}

# Read-only, and still applies a WAL or journal. immutable=1 would ignore both.
sqlite_readonly_uri() {
  local path=$1
  path=${path//%/%25}
  path=${path//#/%23}
  path=${path//\?/%3F}
  printf 'file:%s?mode=ro\n' "$path"
}

stage_sqlite_databases() {
  local source_db relative staged_db check_output source_mode

  while IFS= read -r -d '' source_db; do
    if path_is_within "$source_db" "$SOURCE"; then
      relative="data/${source_db#"$SOURCE"/}"
    elif path_is_within "$source_db" "$PROJECT_ROOT"; then
      relative=${source_db#"$PROJECT_ROOT"/}
    else
      die "SQLite source escaped configured backup roots: $source_db"
    fi
    staged_db="$STAGED_ROOT/$relative"
    info "Creating consistent SQLite snapshot: $relative"
    find "$staged_db" -maxdepth 0 -type f -delete
    sqlite_backup_command "$source_db" "$staged_db" ||
      die "SQLite online backup failed: $relative"
    source_mode="$(file_mode "$source_db")"
    chmod "$source_mode" "$staged_db"
    touch -r "$source_db" "$staged_db"
    touch -r "$(dirname "$source_db")" "$(dirname "$staged_db")"
    check_output="$(
      sqlite3 "file:$staged_db?mode=ro&immutable=1" 'PRAGMA quick_check;'
    )" || die "SQLite quick_check failed to run: $relative"
    [[ "$check_output" == "ok" ]] ||
      die "SQLite quick_check rejected staged database $relative: $check_output"
  done < <(list_sqlite_sources)
}

remove_staged_path() {
  local path=$1

  [[ -e "$path" || -L "$path" ]] || return 0
  path_is_within "$path" "$STAGED_ROOT" ||
    die "Refusing to remove an exclusion outside the private staging tree."
  find "$path" -depth -delete ||
    die "Could not remove excluded content from private staging: ${path#"$STAGED_ROOT"/}"
}

remove_staged_exclusions() {
  local directory relative

  info "Removing excluded content from the private staging tree."
  remove_staged_path "$STAGED_ROOT/data/qdrant"
  for relative in "${EPHEMERAL_HOME_EXCLUDES[@]}"; do
    remove_staged_path "$STAGED_ROOT/${relative#"$PROJECT_ROOT"/}"
  done
  if ((${#LEGACY_EXCLUDES[@]} > 0)); then
    for relative in "${LEGACY_EXCLUDES[@]}"; do
      remove_staged_path "$STAGED_ROOT/data/$relative"
    done
  fi
  if ((${#BROKEN_SYMLINK_EXCLUDES[@]} > 0)); then
    for relative in "${BROKEN_SYMLINK_EXCLUDES[@]}"; do
      remove_staged_path "$STAGED_ROOT/${relative#"$PROJECT_ROOT"/}"
    done
  fi
  while IFS= read -r -d '' directory; do
    remove_staged_path "$directory"
  done < <(find "$STAGED_ROOT" -type d -name __pycache__ -prune -print0)
  find "$STAGED_ROOT" -type f \
    \( -name '*.db-wal' -o -name '*.db-shm' -o -name '*.db-journal' \
      -o -name '*.sqlite*-wal' -o -name '*.sqlite*-shm' -o -name '*.sqlite*-journal' \
      -o -name '.DS_Store' \) \
    -delete ||
    die "Could not remove excluded sidecars from the private staging tree."
}

# Escape restic exclude pattern metacharacters so a path matches literally.
restic_literal_pattern() {
  local pattern=$1

  pattern=${pattern//\\/\\\\}
  pattern=${pattern//\*/\\*}
  pattern=${pattern//\?/\\?}
  pattern=${pattern//\[/\\[}
  pattern=${pattern//\]/\\]}
  # Exclude files expand $VAR and trim surrounding whitespace on each line;
  # single-character classes keep those characters literal.
  pattern=${pattern//\$/[\$]}
  pattern=${pattern// /[ ]}
  pattern=${pattern//$'\t'/[$'\t']}
  printf '%s\n' "$pattern"
}

# Write RESTIC_EXCLUDES to a private file for --exclude-file. Every restic
# backup call that walks the tree passes this file instead of argv flags.
write_restic_exclude_file() {
  local pattern

  if [[ -z "$RESTIC_EXCLUDE_FILE" ]]; then
    RESTIC_EXCLUDE_FILE="$(mktemp "${TMPDIR:-/tmp}/learn-ukrainian-backup-excludes.XXXXXX")" ||
      die "Could not create the restic exclude file."
  fi
  : > "$RESTIC_EXCLUDE_FILE" || die "Could not write the restic exclude file."
  for pattern in "${RESTIC_EXCLUDES[@]}"; do
    [[ "$pattern" != *$'\n'* ]] ||
      die "Cannot express an exclude pattern containing a newline: ${pattern%%$'\n'*}..."
    printf '%s\n' "$pattern" >> "$RESTIC_EXCLUDE_FILE" ||
      die "Could not write the restic exclude file."
  done
}

# Exclude one SQLite database and its sidecars, matched literally.
add_sqlite_exclude() {
  local database=$1 suffix

  for suffix in "" -wal -shm -journal; do
    RESTIC_EXCLUDES+=("$(restic_literal_pattern "$database$suffix")")
  done
}

build_restic_excludes() {
  local root=$1
  local relative snapshot_root

  RESTIC_EXCLUDES=(
    "$(restic_literal_pattern "$root/qdrant")"
    '**/*.db-wal'
    '**/*.db-shm'
    '**/*.db-journal'
    '**/*.sqlite-wal'
    '**/*.sqlite-shm'
    '**/*.sqlite-journal'
    '**/*.sqlite3-wal'
    '**/*.sqlite3-shm'
    '**/*.sqlite3-journal'
    '**/*.sqlite*-wal'
    '**/*.sqlite*-shm'
    '**/*.sqlite*-journal'
    '**/__pycache__/**'
    '**/.DS_Store'
    '**/batch_state/**/*-home'
    '**/batch_state/**/*-home/**'
    '**/batch_state/review-receipts/**/home'
    '**/batch_state/review-receipts/**/home/**'
    '**/qdrant/**'
    'batch_state/tasks/**/*.lock'
  )
  for snapshot_root in "${SNAPSHOT_EXCLUDE_ROOTS[@]}"; do
    RESTIC_EXCLUDES+=(
      "$snapshot_root/**/*.snapshots"
      "$snapshot_root/**/*.snapshots/**"
    )
  done
  if ((${#LEGACY_EXCLUDES[@]} > 0)); then
    for relative in "${LEGACY_EXCLUDES[@]}"; do
      RESTIC_EXCLUDES+=("$(restic_literal_pattern "$root/$relative")")
    done
  fi
  for relative in "${EPHEMERAL_HOME_EXCLUDES[@]}"; do
    RESTIC_EXCLUDES+=("$(restic_literal_pattern "$relative")")
  done
  # Skipped broken symlinks, re-rooted onto the tree restic reads: the live
  # project on Linux, the private staging copy otherwise. root is <tree>/data.
  if ((${#BROKEN_SYMLINK_EXCLUDES[@]} > 0)); then
    for relative in "${BROKEN_SYMLINK_EXCLUDES[@]}"; do
      RESTIC_EXCLUDES+=("$(restic_literal_pattern "${root%/data}/${relative#"$PROJECT_ROOT"/}")")
    done
  fi
  # Never upload the private staging tree when it lives inside data/
  # (the data-volume staging location).
  if path_is_within "$TMP_ROOT" "$SOURCE"; then
    RESTIC_EXCLUDES+=("$(restic_literal_pattern "$TMP_ROOT")")
  fi
}

source_for_backup_path() {
  local relative=$1

  if [[ "$relative" == "data" ]]; then
    printf '%s\n' "$SOURCE"
  else
    printf '%s/%s\n' "$PROJECT_ROOT" "$relative"
  fi
}

tree_file_stats() {
  local tree=$1
  local total=0 count=0 file size

  if [[ "$(uname -s)" == Linux ]]; then
    allowlist_find "$tree" -type f -printf '%s\n' |
      awk '{total += $1; count++} END {printf "%.0f %d\n", total, count}'
    return
  fi
  while IFS= read -r -d '' file; do
    if size="$(stat -f '%z' "$file" 2>/dev/null)"; then
      :
    else
      size="$(stat -c '%s' "$file")"
    fi
    total=$((total + size))
    count=$((count + 1))
  done < <(allowlist_find "$tree" -type f -print0)
  printf '%s %s\n' "$total" "$count"
}

source_tree_stats() {
  local tree=$1 total=0 count=0 file relative size
  while IFS= read -r -d '' file && IFS= read -r -d '' size; do
    is_ephemeral_home_path "$file" && continue
    relative=${file#"$PROJECT_ROOT"/}
    case "$relative" in
      */qdrant/*|*/__pycache__/*|*/.DS_Store|*.db-wal|*.db-shm|*.db-journal|*.sqlite*-wal|*.sqlite*-shm|*.sqlite*-journal) continue ;;
    esac
    snapshot_path_is_excluded "$relative" && continue
    if [[ "$relative" == batch_state/tasks/*.lock ]]; then
      continue
    fi
    total=$((total + size))
    count=$((count + 1))
  done < <(allowlist_find "$tree" -type f -printf '%p\0%s\0')
  printf '%s %s\n' "$total" "$count"
}

backup_tree_size_bytes() {
  local total=0 relative source_path bytes files

  for relative in "${BACKUP_PATHS[@]}"; do
    source_path="$(source_for_backup_path "$relative")"
    read -r bytes files < <(tree_file_stats "$source_path")
    total=$((total + bytes))
  done
  printf '%s\n' "$total"
}

print_backup_selection() {
  local relative source_path bytes files
  local missing_seed="$PROJECT_ROOT/.claude/atlas-epic/plans/curated-seed"

  info "Recovery roots selected (repo-local sole copies first):"
  for relative in "${BACKUP_PATHS[@]}"; do
    source_path="$(source_for_backup_path "$relative")"
    if [[ "$(uname -s)" == Linux ]]; then
      read -r bytes files < <(source_tree_stats "$source_path")
    else
      read -r bytes files < <(tree_file_stats "$source_path")
    fi
    printf '  %s files=%s bytes=%s\n' "$relative" "$files" "$bytes"
  done
  echo "  BACKUP-RECEIPT.json generated during an executed backup"
  echo "  GIT-WORKTREE.patch generated when tracked changes are present"
  if [[ ! -d "$missing_seed" ]]; then
    echo "WARNING: known previously lost path is absent: .claude/atlas-epic/plans/curated-seed" >&2
  fi
}

create_worktree_patch() {
  if ! git_command -C "$PROJECT_ROOT" diff --quiet HEAD --; then
    git_command -C "$PROJECT_ROOT" diff --binary HEAD -- \
      > "$STAGED_ROOT/GIT-WORKTREE.patch"
    BACKUP_PATHS+=("GIT-WORKTREE.patch")
  fi
}

append_json_string() {
  local file=$1 entry=$2
  jq -cn --arg entry "$entry" '$entry' >> "$file"
}

# Path, exclusion, archive, and database inventories are files. jq loads them
# with --slurpfile. A --arg or --argjson value that grows with the number of
# selected paths, databases, or files can exceed the kernel's per-argument
# limit. Scalar flags stay on argv: one path, one count, one snapshot id, and
# the bounded known-missing list.
write_backup_receipt() {
  local inventory_file="$STAGE_DIR/path-inventory.jsonl"
  local exclusions_file="$STAGE_DIR/exclusions.jsonl"
  local archives_file="$STAGE_DIR/database-archives.jsonl"
  local relative bytes files git_sha git_dirty untracked_count
  local known_missing created_at

  : > "$inventory_file"
  for relative in "${BACKUP_PATHS[@]}"; do
    if [[ "$LINUX_MODE" -eq 1 && "$relative" != "GIT-WORKTREE.patch" ]]; then
      read -r bytes files < <(source_tree_stats "$(source_for_backup_path "$relative")")
    else
      read -r bytes files < <(tree_file_stats "$STAGED_ROOT/$relative")
    fi
    jq -cn \
      --arg path "$relative" \
      --argjson files "$files" \
      --argjson bytes "$bytes" \
      '{path: $path, files: $files, bytes: $bytes}' \
      >> "$inventory_file"
  done

  git_sha="$(git_command -C "$PROJECT_ROOT" rev-parse HEAD)"
  git_dirty=false
  git_command -C "$PROJECT_ROOT" diff --quiet HEAD -- || git_dirty=true
  untracked_count=0
  while IFS= read -r -d '' relative; do
    untracked_path_is_uncovered "$relative" || continue
    untracked_count=$((untracked_count + 1))
  done < <(git_command -C "$PROJECT_ROOT" ls-files --others --exclude-standard -z)
  known_missing='[]'
  if [[ ! -d "$PROJECT_ROOT/.claude/atlas-epic/plans/curated-seed" ]]; then
    known_missing='[".claude/atlas-epic/plans/curated-seed"]'
  fi
  created_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  : > "$exclusions_file"
  append_json_string "$exclusions_file" "data/qdrant"
  append_json_string "$exclusions_file" "SQLite WAL/SHM/journal sidecars"
  append_json_string "$exclusions_file" "batch_state scoped review homes"
  append_json_string "$exclusions_file" "__pycache__"
  append_json_string "$exclusions_file" ".DS_Store"
  if ((${#LEGACY_EXCLUDES[@]} > 0)); then
    for relative in "${LEGACY_EXCLUDES[@]}"; do
      append_json_string "$exclusions_file" "data/$relative legacy symlink"
    done
  fi
  if ((${#SQLITE_TRANSIENT_SOURCES[@]} > 0)); then
    append_json_string "$exclusions_file" \
      "${#SQLITE_TRANSIENT_SOURCES[@]} pytest scratch SQLite databases skipped"
  fi
  : > "$archives_file"
  if ((${#DB_ARCHIVES_USED[@]} > 0)); then
    for relative in "${DB_ARCHIVES_USED[@]}"; do
      append_json_string "$exclusions_file" "loose SQLite databases covered by archive $relative"
      append_json_string "$archives_file" "$relative"
    done
  fi
  if ((${#BROKEN_SYMLINK_EXCLUDES[@]} > 0)); then
    for relative in "${BROKEN_SYMLINK_EXCLUDES[@]}"; do
      append_json_string "$exclusions_file" "${relative#"$PROJECT_ROOT"/} broken symlink skipped"
    done
  fi
  if [[ -z "$DB_INVENTORY_FILE" || ! -f "$DB_INVENTORY_FILE" ]]; then
    DB_INVENTORY_FILE="$STAGE_DIR/database-inventory.json"
    printf '%s\n' '[]' > "$DB_INVENTORY_FILE" ||
      die "Could not create the database inventory."
  fi

  jq -n \
    --arg created_at "$created_at" \
    --arg host "$BACKUP_HOST" \
    --arg git_sha "$git_sha" \
    --arg tag "$BACKUP_TAG" \
    --argjson git_dirty "$git_dirty" \
    --argjson untracked_count "$untracked_count" \
    --slurpfile paths "$inventory_file" \
    --argjson known_missing "$known_missing" \
    --slurpfile exclusions "$exclusions_file" \
    --argjson linux_mode "$([[ "$LINUX_MODE" -eq 1 ]] && echo true || echo false)" \
    --arg run_id "$RUN_ID" \
    --arg base_snapshot_id "$LINUX_BASE_SNAPSHOT" \
    --arg patch_snapshot_id "$LINUX_PATCH_SNAPSHOT" \
    --slurpfile database_inventory "$DB_INVENTORY_FILE" \
    --argjson transient_count "${#SQLITE_TRANSIENT_SOURCES[@]}" \
    --argjson archived_count "${#SQLITE_ARCHIVED_SOURCES[@]}" \
    --slurpfile archives "$archives_file" \
    '$database_inventory[0] as $databases | {
      schema_version: (if $linux_mode then 3 else 1 end),
      created_at_utc: $created_at,
      host: $host,
      git_sha: $git_sha,
      git_tracked_changes: $git_dirty,
      git_untracked_files_not_included: $untracked_count,
      tag: $tag,
      receipt_status: "prepared-before-snapshot-write",
      paths: $paths,
      known_missing_paths: $known_missing,
      exclusions: $exclusions,
      restore_command: "./scripts/backup-data.sh restore latest --to /absolute/empty/directory --execute",
      linux_run: (if $linux_mode then {run_id: $run_id, base_snapshot_id: $base_snapshot_id, patch_snapshot_id: $patch_snapshot_id, databases: $databases, databases_backed_up: ($databases | length), transient_databases_skipped: $transient_count, archived_databases: $archived_count, database_archives: $archives} else null end)
    }' > "$STAGED_ROOT/BACKUP-RECEIPT.json"
  BACKUP_PATHS+=("BACKUP-RECEIPT.json")
}

prepare_staging_tree() {
  local relative source_path destination

  STAGED_ROOT="$STAGE_DIR/project-state"
  mkdir -m 700 "$STAGED_ROOT"
  for relative in "${BACKUP_PATHS[@]}"; do
    source_path="$(source_for_backup_path "$relative")"
    destination="$STAGED_ROOT/$relative"
    mkdir -p "$(dirname "$destination")"
    info "Staging recovery root: $relative"
    clone_tree "$source_path" "$destination"
  done
  stage_sqlite_databases
  remove_staged_exclusions
  create_worktree_patch
  write_backup_receipt
}

snapshot_id_from_output() {
  local output=$1 snapshot_id
  snapshot_id="$(jq -er 'select(.message_type == "summary") | .snapshot_id // empty' "$output")" ||
    die "Restic backup completed without a snapshot ID."
  [[ "$snapshot_id" =~ ^[0-9a-f]{64}$ ]] || die "Restic returned an invalid snapshot ID."
  printf '%s\n' "$snapshot_id"
}

# Stage one selected database into the pending batch: a consistent online
# backup checked with PRAGMA integrity_check. A database that fails any step is
# recorded as a failure and never uploaded. The copy is made outside the batch
# and measured first: it includes committed WAL content, so it can be larger
# than the source's main file.
linux_stage_database() {
  local source_db=$1 relative=$2 incoming_db staged_db check_output source_mode error staged_bytes
  incoming_db="$DB_INCOMING_ROOT/$relative"
  staged_db="$DB_BATCH_ROOT/$relative"
  if ! error="$(check_one_db_space "$source_db" "$relative" 2>&1)"; then
    if ((${#PENDING_DB_PATHS[@]} == 0)); then
      BACKUP_FAILURES+=("Database $relative: $error")
      return 1
    fi
    # The pending batch holds staging space: upload it, then check again.
    flush_database_batch
    if ! error="$(check_one_db_space "$source_db" "$relative" 2>&1)"; then
      BACKUP_FAILURES+=("Database $relative: $error")
      return 1
    fi
  fi
  if ! mkdir -p "$(dirname "$incoming_db")"; then
    BACKUP_FAILURES+=("Database $relative: could not create staging directory")
    return 1
  fi
  info "Creating consistent SQLite snapshot: $relative"
  if ! error="$(sqlite_backup_command "$source_db" "$incoming_db" 2>&1)"; then
    BACKUP_FAILURES+=("Database $relative: SQLite online backup failed: ${error:-unknown error}")
    find "$incoming_db" -maxdepth 0 -type f -delete
    return 1
  fi
  [[ -z "$error" ]] || printf '%s\n' "$error"
  if ! source_mode="$(file_mode "$source_db")" ||
    ! chmod "$source_mode" "$incoming_db" ||
    ! touch -r "$source_db" "$incoming_db"; then
    BACKUP_FAILURES+=("Database $relative: could not preserve source metadata")
    find "$incoming_db" -maxdepth 0 -type f -delete
    return 1
  fi
  if ! check_output="$(sqlite3 "$(sqlite_immutable_uri "$incoming_db")" 'PRAGMA integrity_check;' 2>&1)"; then
    BACKUP_FAILURES+=("Database $relative: SQLite integrity_check failed: $check_output")
    find "$incoming_db" -maxdepth 0 -type f -delete
    return 1
  fi
  if [[ "$check_output" != ok ]]; then
    BACKUP_FAILURES+=("Database $relative: SQLite integrity_check rejected staged database: $check_output")
    find "$incoming_db" -maxdepth 0 -type f -delete
    return 1
  fi
  if ! staged_bytes="$(stat -c '%s' "$incoming_db")"; then
    BACKUP_FAILURES+=("Database $relative: could not measure staged database")
    find "$incoming_db" -maxdepth 0 -type f -delete
    return 1
  fi
  if ((${#PENDING_DB_PATHS[@]} > 0 && PENDING_DB_BYTES + staged_bytes > DB_BATCH_MAX_BYTES)); then
    flush_database_batch
  fi
  if ! mkdir -p "$(dirname "$staged_db")" || ! mv -- "$incoming_db" "$staged_db"; then
    BACKUP_FAILURES+=("Database $relative: could not add the staged copy to the upload batch")
    find "$incoming_db" "$staged_db" -maxdepth 0 -type f -delete 2>/dev/null
    return 1
  fi
  PENDING_DB_PATHS+=("$relative")
  PENDING_DB_MODES+=("$source_mode")
  PENDING_DB_BYTES=$((PENDING_DB_BYTES + staged_bytes))
}

# Upload every pending staged database as one lu-part-db snapshot and record
# each path against that snapshot ID; on failure every pending database is a
# failure. Batching matters because each restic run pays a fixed repository
# open, index load, and lock cost that dwarfs a small database's bytes.
flush_database_batch() {
  local snapshot_id relative index
  local -a roots=() failed=()

  ((${#PENDING_DB_PATHS[@]} > 0)) || return 0
  while IFS= read -r -d '' relative; do
    roots+=("${relative#./}")
  done < <(cd "$DB_BATCH_ROOT" && find . -mindepth 1 -maxdepth 1 -print0)
  info "Uploading ${#PENDING_DB_PATHS[@]} consistent SQLite snapshot(s) in one restic snapshot."
  if ! (
    cd "$DB_BATCH_ROOT"
    restic_repository_command backup "${roots[@]}" --force \
      --host "$BACKUP_HOST" --tag "$BACKUP_TAG" --tag "lu-run-$RUN_ID" \
      --tag lu-part-db --json
  ) | tee "$STAGE_DIR/db-backup.jsonl"; then
    failed=("restic upload failed")
  elif ! snapshot_id="$(snapshot_id_from_output "$STAGE_DIR/db-backup.jsonl" 2>&1)"; then
    failed=("$snapshot_id")
  elif ! jq -cRn --arg snapshot_id "$snapshot_id" --slurpfile previous "$DB_INVENTORY_FILE" \
    '$previous[0] + [inputs | select(length > 0) | split("\t") | {path: .[0], snapshot_id: $snapshot_id, mode: .[1]}]' \
    > "$STAGE_DIR/database-inventory.json.new" \
    < <(
      for index in "${!PENDING_DB_PATHS[@]}"; do
        printf '%s\t%s\n' "${PENDING_DB_PATHS[$index]}" "${PENDING_DB_MODES[$index]}"
      done
    ); then
    failed=("could not record snapshot ID")
  elif ! mv -f -- "$STAGE_DIR/database-inventory.json.new" "$DB_INVENTORY_FILE"; then
    failed=("could not record snapshot ID")
  fi
  if ((${#failed[@]} > 0)); then
    for relative in "${PENDING_DB_PATHS[@]}"; do
      BACKUP_FAILURES+=("Database $relative: ${failed[0]}")
    done
  fi
  find "$DB_BATCH_ROOT" -mindepth 1 -depth -delete ||
    die "Could not clear the private SQLite staging batch."
  PENDING_DB_PATHS=()
  PENDING_DB_MODES=()
  PENDING_DB_BYTES=0
}

run_linux_backup() {
  local relative source_db source_bytes snapshot_id backup_output unreadable

  [[ "$DB_BATCH_MAX_BYTES" =~ ^[1-9][0-9]{0,17}$ ]] ||
    die "LU_BACKUP_DB_BATCH_MAX_BYTES must be a positive whole number of bytes."
  LINUX_MODE=1
  RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$(printf '%04x%04x' "$RANDOM" "$RANDOM")"
  STAGE_DIR="$STAGE_PATH"
  [[ ! -L "$STAGE_DIR" ]] || die "Refusing symlink at the private staging path: $STAGE_DIR"
  [[ ! -e "$STAGE_DIR" ]] || die "Stale staging path exists; inspect it before retrying: $STAGE_DIR"
  mkdir -m 700 "$STAGE_DIR"
  DB_INVENTORY_FILE="$STAGE_DIR/database-inventory.json"
  printf '%s\n' '[]' > "$DB_INVENTORY_FILE" ||
    die "Could not create the database inventory."
  STAGED_ROOT="$STAGE_DIR/project-state"
  mkdir -m 700 "$STAGED_ROOT"
  create_worktree_patch

  build_restic_excludes "$SOURCE"
  classify_sqlite_sources
  add_classified_sqlite_excludes
  write_restic_exclude_file
  info "Streaming non-database recovery files from the live tree."
  backup_output="$STAGE_DIR/base-backup.jsonl"
  # Parent shell: the file list must exist before this pipeline forks.
  build_restic_selection_args
  if backup_selected_paths \
    --host "$BACKUP_HOST" --tag "$BACKUP_TAG" --tag "lu-run-$RUN_ID" \
    --tag lu-part-base --json --exclude-file "$RESTIC_EXCLUDE_FILE" \
    | tee "$backup_output"; then
    if ! LINUX_BASE_SNAPSHOT="$(snapshot_id_from_output "$backup_output" 2>&1)"; then
      BACKUP_FAILURES+=("File phase: $LINUX_BASE_SNAPSHOT")
      LINUX_BASE_SNAPSHOT=""
    fi
  else
    BACKUP_FAILURES+=("File phase: restic backup failed")
  fi
  unreadable="$(unreadable_backup_paths)"
  if [[ -n "$unreadable" ]]; then
    BACKUP_FAILURES+=("Unreadable paths:")
    while IFS= read -r relative; do
      BACKUP_FAILURES+=("  ${relative#"$PROJECT_ROOT"/}")
    done <<< "$unreadable"
  fi

  DB_BATCH_ROOT="$STAGE_DIR/db-batch"
  DB_INCOMING_ROOT="$STAGE_DIR/db-incoming"
  mkdir -m 700 "$DB_BATCH_ROOT" "$DB_INCOMING_ROOT"
  for source_db in "${SQLITE_BACKUP_SOURCES[@]}"; do
    relative=${source_db#"$PROJECT_ROOT"/}
    if [[ "$relative" == *$'\n'* || "$relative" == *$'\t'* ]]; then
      BACKUP_FAILURES+=("Database path cannot be recorded safely: $relative")
      continue
    fi
    # Flushing early on the main file's size keeps peak staging low;
    # linux_stage_database then charges the copy's exact size.
    source_bytes="$(stat -c '%s' "$source_db" 2>/dev/null)" || source_bytes=0
    if ((${#PENDING_DB_PATHS[@]} > 0 && PENDING_DB_BYTES + source_bytes > DB_BATCH_MAX_BYTES)); then
      flush_database_batch
    fi
    linux_stage_database "$source_db" "$relative" || true
  done
  flush_database_batch
  # Parsed into last-run.json and the change-only alert; printed on failure too.
  info "SQLite databases backed up: $(jq -r 'length' "$DB_INVENTORY_FILE") of ${#SQLITE_BACKUP_SOURCES[@]} (pytest scratch skipped: ${#SQLITE_TRANSIENT_SOURCES[@]}, archived: ${#SQLITE_ARCHIVED_SOURCES[@]})."

  if [[ -f "$STAGED_ROOT/GIT-WORKTREE.patch" ]]; then
    if restic_repository_command backup --stdin --stdin-filename GIT-WORKTREE.patch \
      --host "$BACKUP_HOST" --tag "$BACKUP_TAG" --tag "lu-run-$RUN_ID" \
      --tag lu-part-patch --json < "$STAGED_ROOT/GIT-WORKTREE.patch" \
      | tee "$STAGE_DIR/patch-backup.jsonl"; then
      if ! LINUX_PATCH_SNAPSHOT="$(snapshot_id_from_output "$STAGE_DIR/patch-backup.jsonl" 2>&1)"; then
        BACKUP_FAILURES+=("Patch phase: $LINUX_PATCH_SNAPSHOT")
        LINUX_PATCH_SNAPSHOT=""
      fi
    else
      BACKUP_FAILURES+=("Patch phase: restic backup failed")
    fi
  fi

  # Two-phase publication. Once a lu-part-complete snapshot exists, restore
  # latest selects this run, so the receipt is first uploaded as a pending
  # lu-part-receipt snapshot and every step that can fail runs after it.
  if ((${#BACKUP_FAILURES[@]} == 0)); then
    write_backup_receipt
    RECEIPT_TIME="$(date '+%Y-%m-%d %H:%M:%S')"
    if upload_run_receipt lu-part-receipt "$STAGE_DIR/receipt-backup.jsonl"; then
      if ! snapshot_id="$(snapshot_id_from_output "$STAGE_DIR/receipt-backup.jsonl" 2>&1)"; then
        BACKUP_FAILURES+=("Receipt phase: $snapshot_id")
      fi
    else
      BACKUP_FAILURES+=("Receipt phase: restic backup failed")
    fi
  fi
  # This repository check covers every snapshot of the run, including the
  # pending receipt, whose tree the completion snapshot reuses.
  info "Checking repository metadata after backup."
  restic_repository_command check || BACKUP_FAILURES+=("Repository check failed")
  if ((${#BACKUP_FAILURES[@]} > 0)); then
    printf 'Backup run %s failed:\n' "$RUN_ID" >&2
    printf '  %s\n' "${BACKUP_FAILURES[@]}" >&2
    return 1
  fi
  verify_linux_runner_mirror "$LINUX_BASE_SNAPSHOT"
  stage_verified_linux_runner_mirror_receipt "$LINUX_BASE_SNAPSHOT"

  # The run's last repository mutation: the same receipt bytes and time, now
  # tagged lu-part-complete. No tag is ever added to or removed from a snapshot.
  info "Publishing completed run $RUN_ID."
  upload_run_receipt lu-part-complete "$STAGE_DIR/complete-backup.jsonl" ||
    die "Could not publish completed run $RUN_ID; restore latest still selects the previous completed run."
  publish_staged_gate_receipt
  # Informational only: the run is already published.
  snapshot_id="$(jq -r 'select(.message_type == "summary") | .snapshot_id // empty' \
    "$STAGE_DIR/complete-backup.jsonl" 2>/dev/null)" || snapshot_id=""
  info "Linux backup run $RUN_ID complete; receipt snapshot ${snapshot_id:-unknown}." || true
}

# Upload the run receipt as one stdin snapshot of the given part, at
# RECEIPT_TIME, which also becomes the stored file's mtime.
upload_run_receipt() {
  local part=$1 output=$2
  restic_repository_command backup --stdin --stdin-filename BACKUP-RECEIPT.json \
    --time "$RECEIPT_TIME" --host "$BACKUP_HOST" --tag "$BACKUP_TAG" --tag "lu-run-$RUN_ID" \
    --tag "$part" --json < "$STAGED_ROOT/BACKUP-RECEIPT.json" \
    | tee "$output"
}

run_backup() {
  local execute=$1
  local backup_root backup_output snapshot_id source_db

  validate_environment
  if [[ "$execute" -eq 1 ]]; then acquire_lock; fi
  validate_source
  print_backup_selection

  if [[ "$execute" -eq 0 ]]; then
    info "Backup preview only; no snapshot will be written."
    backup_root="$SOURCE"
    build_restic_excludes "$backup_root"
    if [[ "$(uname -s)" == Linux ]]; then
      classify_sqlite_sources
      add_classified_sqlite_excludes
      for source_db in "${SQLITE_BACKUP_SOURCES[@]}"; do
        echo "  SQLite online backup preview: ${source_db#"$PROJECT_ROOT"/}"
      done
    fi
    write_restic_exclude_file
    require_initialized_repository
    backup_selected_paths \
      --dry-run \
      --verbose=2 \
      --host "$BACKUP_HOST" \
      --tag "$BACKUP_TAG" \
      --exclude-file "$RESTIC_EXCLUDE_FILE"
    echo "Preview complete. Re-run with --execute to create a snapshot."
    return
  fi

  require_initialized_repository
  if [[ "$(uname -s)" == Linux ]]; then
    run_linux_backup
    return
  fi
  check_staging_space
  STAGE_DIR="$STAGE_PATH"
  [[ ! -L "$STAGE_DIR" ]] ||
    die "Refusing symlink at the private staging path: $STAGE_DIR"
  if [[ -e "$STAGE_DIR" ]]; then
    die "Stale staging path exists; inspect and remove it before retrying: $STAGE_DIR"
  fi
  mkdir -m 700 "$STAGE_DIR"
  info "Creating private copy-on-write staging tree."
  prepare_staging_tree

  backup_root="$STAGED_ROOT/data"
  build_restic_excludes "$backup_root"
  write_restic_exclude_file
  info "Creating encrypted, versioned restic snapshot."
  backup_output="$STAGE_DIR/restic-backup.jsonl"
  (
    cd "$STAGED_ROOT"
    restic_repository_command backup "${BACKUP_PATHS[@]}" \
      --host "$BACKUP_HOST" \
      --tag "$BACKUP_TAG" \
      --json \
      --exclude-file "$RESTIC_EXCLUDE_FILE"
  ) | tee "$backup_output"
  if ! snapshot_id="$(jq -er 'select(.message_type == "summary") | .snapshot_id // empty' "$backup_output")" ||
    [[ ! "$snapshot_id" =~ ^[0-9a-f]{64}$ ]]; then
    die "Restic backup completed without a valid snapshot ID; refusing to claim runner-mirror durability."
  fi
  info "Checking repository metadata after backup."
  restic_repository_command check
  write_restic_gate_receipt "$snapshot_id"
  info "Backup and repository check complete."
}

validate_restore_target() {
  local target=$1
  local target_real repo_real project_real source_real cloud_real

  target_real="$(canonical_target "$target")"
  repo_real="$(canonical_existing_dir "$REPO_ROOT")"
  project_real="$(canonical_existing_dir "$PROJECT_ROOT")"
  source_real="$(canonical_existing_dir "$SOURCE")"

  [[ ! -L "$target_real" ]] ||
    die "Restore target must not be a symlink: $target_real"
  [[ ! -e "$target_real" || -d "$target_real" ]] ||
    die "Restore target exists and is not a directory: $target_real"
  paths_overlap "$target_real" "$repo_real" &&
    die "Restore target must be outside the project checkout."
  paths_overlap "$target_real" "$project_real" &&
    die "Restore target must be outside the selected project checkout."
  paths_overlap "$target_real" "$source_real" &&
    die "Restore target must not overlap the live backup source."

  if [[ -d "$CLOUD_ROOT" ]]; then
    cloud_real="$(canonical_existing_dir "$CLOUD_ROOT")"
    paths_overlap "$target_real" "$cloud_real" &&
      die "Restore target must be outside CloudStorage."
  fi

  resolve_legacy_dir
  if [[ -n "$LEGACY_DIR" ]] && paths_overlap "$target_real" "$LEGACY_DIR"; then
    die "Restore target must not overlap the read-only legacy backup."
  fi

  if [[ -e "$target_real" ]] &&
    [[ -n "$(find "$target_real" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    die "Restore target must be empty: $target_real"
  fi

  printf '%s\n' "$target_real"
}

format_bytes() {
  awk -v bytes="$1" 'BEGIN {
    split("B KiB MiB GiB TiB", unit, " ")
    i = 1
    while (bytes >= 1024 && i < 5) { bytes /= 1024; i++ }
    if (i == 1) printf "%d B\n", bytes
    else printf "%.1f %s\n", bytes, unit[i]
  }'
}

restore_margin_percent() {
  local margin=${LU_BACKUP_RESTORE_MARGIN_PERCENT:-10}
  [[ "$margin" =~ ^[0-9]{1,4}$ ]] ||
    die "LU_BACKUP_RESTORE_MARGIN_PERCENT must be a whole number of percent (for example 10)."
  # Force base 10: bash arithmetic reads a leading zero as octal (010 -> 8, 08 -> error).
  printf '%s\n' "$((10#$margin))"
}

# Free bytes on the filesystem that will hold the restore target (the target
# itself may not exist yet, so measure its nearest existing ancestor).
target_free_bytes() {
  local probe=$1 free_kib
  while [[ ! -d "$probe" ]]; do
    probe="$(dirname "$probe")"
  done
  free_kib="$(df -Pk "$probe" | awk 'NR == 2 {print $4}')"
  [[ "$free_kib" =~ ^[0-9]+$ ]] || die "Could not determine free space for the restore target."
  printf '%s\n' $((free_kib * 1024))
}

target_filesystem_label() {
  local probe=$1
  while [[ ! -d "$probe" ]]; do
    probe="$(dirname "$probe")"
  done
  df -Pk "$probe" | awk 'NR == 2 {print $1 " mounted at " $6}'
}

# Total restore size (bytes) of whole snapshots, from restic's own accounting.
snapshots_restore_size_bytes() {
  local stats
  [[ $# -gt 0 ]] || { printf '0\n'; return; }
  stats="$(restic_repository_command stats --mode restore-size --json "$@")" ||
    die "Could not compute the restore size of the selected snapshots."
  jq -er '.total_size | select(type == "number")' <<< "$stats" ||
    die "Restic reported no restore size for the selected snapshots."
}

# "COUNT BYTES" of the files under one path of a snapshot (path-scoped restore).
snapshot_path_size() {
  local snapshot=$1 path=$2 listing
  listing="$(restic_repository_command ls --json --recursive "$snapshot" "/$path")" ||
    die "Could not list $path in snapshot $snapshot."
  jq -sr 'map(select(.struct_type == "node" and .type == "file") | .size) | "\(length) \(add // 0)"' \
    <<< "$listing"
}

# Refuse before anything is written when the target cannot hold the restore.
check_restore_space() {
  local target=$1 size_bytes=$2 margin required free
  margin="$(restore_margin_percent)"
  required=$((size_bytes + (size_bytes * margin + 99) / 100))
  free="$(target_free_bytes "$target")"
  info "Restore size $(format_bytes "$size_bytes") (+${margin}% margin = $(format_bytes "$required")); free on target: $(format_bytes "$free")."
  ((free >= required)) ||
    die "Insufficient free space to restore into $target: need $(format_bytes "$required") (restore size $(format_bytes "$size_bytes") + ${margin}% margin), have $(format_bytes "$free") on $(target_filesystem_label "$target"). Nothing was restored. Free space, choose another --to, restore one file with --path RELATIVE_PATH, or lower LU_BACKUP_RESTORE_MARGIN_PERCENT."
}

validate_restore_scope() {
  local scope=$1
  [[ "$scope" != /* && "$scope" =~ [^[:space:]] ]] ||
    die "--path must be a non-empty path relative to the run root (for example data/atlas.db)."
  [[ "/$scope/" != *"/../"* && "/$scope/" != *"/./"* && "$scope" != *//* ]] ||
    die "--path must not contain '.', '..', or empty components: $scope"
  [[ "$scope" != *$'\n'* && "$scope" != *$'\t'* ]] ||
    die "--path must be a literal path (no newline or tab): $scope"
}

# Glob characters in --path are refused unless the run's receipt records that
# exact database path; its restore then matches it literally.
validate_restore_scope_is_literal() {
  local scope=$1 scope_is_database=$2
  [[ "$scope" != *[\*\?\[\\]* || "$scope_is_database" -eq 1 ]] ||
    die "--path must be a literal path (no glob characters unless it names a recorded database): $scope"
}

# A later file-phase snapshot can recreate sidecars after the consistent
# database is written: --overwrite never keeps the new main file and still
# adds a missing -wal, -shm, or -journal. Call this after every step as well
# as before replacing a receipt-listed database.
remove_restored_database_sidecars() {
  local database_path=$1
  local database_target=$2
  local suffix sidecar

  for suffix in -wal -shm -journal; do
    sidecar="${database_target}${suffix}"
    [[ -e "$sidecar" || -L "$sidecar" ]] || continue
    if [[ -L "$sidecar" ]]; then
      rm -f -- "$sidecar" ||
        die "Could not remove the restored database sidecar link: ${database_path}${suffix}"
      continue
    fi
    [[ -f "$sidecar" ]] ||
      die "Refusing to remove a non-regular restored database sidecar: ${database_path}${suffix}"
    rm -f -- "$sidecar" ||
      die "Could not remove the stale restored database sidecar: ${database_path}${suffix}"
  done
}

# Open a private copy so the check applies any remaining sidecar and does not
# create -wal or -shm beside the restored file. mode=ro is the normal reader
# view; immutable=1 would ignore those sidecars.
integrity_check_restored_database() {
  local database_path=$1
  local label=$2
  local check_output suffix

  RESTORE_CHECK_DIR="$(mktemp -d "${TMP_ROOT}/learn-ukrainian-restore-check.XXXXXX")" ||
    die "Could not create a directory for the restored database integrity check."
  # /bin/cp, not PATH: a backup test replaces cp to prove Linux staging does not copy the tree.
  /bin/cp -p -- "$database_path" "$RESTORE_CHECK_DIR/database" ||
    die "Could not stage the restored database integrity check: $label"
  for suffix in -wal -shm -journal; do
    [[ -e "${database_path}${suffix}" || -L "${database_path}${suffix}" ]] || continue
    [[ -f "${database_path}${suffix}" ]] ||
      die "Restored database sidecar is not a regular file: ${label}${suffix}"
    /bin/cp -p -- "${database_path}${suffix}" "$RESTORE_CHECK_DIR/database${suffix}" ||
      die "Could not stage the restored database integrity check: ${label}${suffix}"
  done
  if ! check_output="$(
    sqlite3 "$(sqlite_readonly_uri "$RESTORE_CHECK_DIR/database")" 'PRAGMA integrity_check;'
  )"; then
    die "SQLite integrity_check failed on restored database: $label"
  fi
  find "$RESTORE_CHECK_DIR" -depth -delete ||
    die "Could not remove the restored database integrity check directory."
  RESTORE_CHECK_DIR=""
  [[ "$check_output" == ok ]] ||
    die "SQLite integrity_check rejected restored database: ${label}: $check_output"
}

run_restore() {
  local snapshot=$1
  local target=$2
  local execute=$3
  local scope=${4:-}
  local scope_given=${5:-0}
  local target_real receipt receipt_json receipt_schema base_id patch_id database_id database_path database_mode database_target check_output
  local manifest_id snapshots_json size_bytes path_info path_count index db_index
  local scope_is_database=0 databases_selected=0 step_count step_bytes
  local -a whole_ids=() step_ids=() step_includes=() step_ls_paths=()
  local -a db_paths=() db_ids=() db_modes=() restored_db_paths=() restored_db_modes=()
  local -A db_id_members=() db_id_planned=() restored_db_set=()

  validate_environment
  if [[ "$execute" -eq 1 ]]; then acquire_lock; fi
  require_initialized_repository
  [[ -n "$snapshot" && "$snapshot" != -* ]] || die "Invalid snapshot ID."
  restore_margin_percent >/dev/null
  # A given --path is always validated, even when empty: an empty value must
  # never fall through to a whole-run restore.
  [[ "$scope_given" -eq 0 && -z "$scope" ]] || validate_restore_scope "${scope%/}"
  scope="${scope%/}"
  target_real="$(validate_restore_target "$target")"

  manifest_id="$snapshot"
  if [[ "$snapshot" == latest && "$(uname -s)" == Linux ]]; then
    snapshots_json="$(restic_repository_command snapshots --json --host "$BACKUP_HOST" --tag "$BACKUP_TAG")"
    manifest_id="$(jq -r "$SNAPSHOT_EPOCH_JQ"'[.[] | select(.tags | index("lu-part-complete"))] | sort_by(.time | epoch_seconds) | last | .id // empty' <<< "$snapshots_json")" ||
      die "Could not order completed snapshots by time."
    if [[ -z "$manifest_id" ]]; then
      if jq -e 'any(.[]; any(.tags[]?; startswith("lu-run-")))' <<< "$snapshots_json" >/dev/null; then
        die "No completed Linux backup run is available; specify a verified older snapshot ID."
      fi
      manifest_id=latest
    fi
  fi

  # Read the run's receipt without writing to the target, so the whole plan
  # (which snapshots, how many bytes) is known before any restore starts.
  receipt_json="$(restic_repository_command dump "$manifest_id" /BACKUP-RECEIPT.json)" ||
    die "Could not read BACKUP-RECEIPT.json from snapshot $manifest_id; refusing to restore."
  receipt_schema="$(jq -er '.schema_version' <<< "$receipt_json")" || die "Snapshot receipt is invalid JSON."
  # Schema 3 marks runs whose databases may share one lu-part-db snapshot, so
  # a script that predates shared snapshots refuses them before restoring.
  # Schema 2 runs also restore through the shared-snapshot-aware plan below.
  [[ "$receipt_schema" == 1 || "$receipt_schema" == 2 || "$receipt_schema" == 3 ]] ||
    die "Unsupported restored receipt schema."

  if [[ "$receipt_schema" == 1 ]]; then
    step_ids+=("$manifest_id")
    step_includes+=("${scope:+/$scope}")
    step_ls_paths+=("$scope")
  else
    jq -e '
      .linux_run.run_id | type == "string" and length > 0
    ' <<< "$receipt_json" >/dev/null || die "Restored Linux receipt has no run ID."
    # Tab and newline delimit the inventory read below; the writer never
    # records a path containing them.
    jq -e '(.linux_run.databases | type == "array") and
      (.linux_run.databases | all(.[]; (.path | type == "string") and
        (.path | test("[\t\n]") | not) and
        (.snapshot_id | type == "string") and (.mode | type == "string")))' \
      <<< "$receipt_json" >/dev/null || die "Restored Linux receipt has invalid database inventory."
    base_id="$(jq -r '.linux_run.base_snapshot_id' <<< "$receipt_json")"
    [[ "$base_id" =~ ^[0-9a-f]{64}$ ]] || die "Restored Linux receipt has invalid base snapshot ID."
    patch_id="$(jq -r '.linux_run.patch_snapshot_id // empty' <<< "$receipt_json")"
    [[ -z "$patch_id" || "$patch_id" =~ ^[0-9a-f]{64}$ ]] ||
      die "Restored Linux receipt has invalid patch snapshot ID."
    if [[ -z "$scope" ]]; then
      step_ids+=("$manifest_id" "$base_id")
      step_includes+=("" "")
      step_ls_paths+=("" "")
      if [[ -n "$patch_id" ]]; then
        step_ids+=("$patch_id")
        step_includes+=("")
        step_ls_paths+=("")
      fi
    elif [[ "$scope" == GIT-WORKTREE.patch ]]; then
      [[ -n "$patch_id" ]] || die "This run has no GIT-WORKTREE.patch (the worktree was clean)."
      step_ids+=("$patch_id")
      step_includes+=("")
      step_ls_paths+=("")
    fi
    # Older runs hold one database per lu-part-db snapshot; newer runs share
    # one snapshot across a batch, so count each snapshot's databases first.
    while IFS=$'\t' read -r database_path database_id database_mode; do
      [[ -n "$database_path" ]] || continue
      [[ "$database_path" != /* && "$database_path" != *'..'* ]] ||
        die "Restored Linux receipt has unsafe database path."
      case "$database_path" in
        data/*|batch_state/*|.agent/*|.claude/*-epic/*) : ;;
        *) die "Restored Linux receipt has database outside recovery roots." ;;
      esac
      [[ "$database_id" =~ ^[0-9a-f]{64}$ ]] ||
        die "Restored Linux receipt has invalid database snapshot ID."
      [[ "$database_mode" =~ ^[0-7]{3,4}$ ]] ||
        die "Restored Linux receipt has invalid database mode."
      db_paths+=("$database_path")
      db_ids+=("$database_id")
      db_modes+=("$database_mode")
      db_id_members[$database_id]=$((${db_id_members[$database_id]:-0} + 1))
    done < <(jq -r '.linux_run.databases[] | [.path, .snapshot_id, .mode] | join("\t")' <<< "$receipt_json")
    for index in "${!db_paths[@]}"; do
      database_path=${db_paths[$index]}
      database_id=${db_ids[$index]}
      [[ -z "$scope" || "$database_path" == "$scope" || "$database_path" == "$scope"/* ]] || continue
      restored_db_paths+=("$database_path")
      restored_db_modes+=("${db_modes[$index]}")
      restored_db_set[$database_path]=1
      databases_selected=$((databases_selected + 1))
      [[ "$database_path" != "$scope" ]] || scope_is_database=1
      if [[ -z "$scope" || "${db_id_members[$database_id]}" -eq 1 ]]; then
        # The whole snapshot is wanted: restore it once.
        [[ -z "${db_id_planned[$database_id]+set}" ]] || continue
        db_id_planned[$database_id]=1
        step_ids+=("$database_id")
        step_includes+=("")
        step_ls_paths+=("")
      else
        # A scoped restore from a shared snapshot takes only this database.
        step_ids+=("$database_id")
        step_includes+=("/$(restic_literal_pattern "$database_path")")
        step_ls_paths+=("$database_path")
      fi
    done
    if [[ -n "$scope" && "$scope" != GIT-WORKTREE.patch && "$scope_is_database" -eq 0 ]]; then
      # Not a single database: the path lives in the file-phase snapshot (and
      # any databases beneath it were already selected above).
      step_ids+=("$base_id")
      step_includes+=("/$scope")
      step_ls_paths+=("$scope")
    fi
  fi
  validate_restore_scope_is_literal "$scope" "$scope_is_database"

  # Exact size of what will be restored: whole snapshots via restic stats,
  # path-scoped file-phase reads via ls.
  size_bytes=0
  path_count=0
  for index in "${!step_ids[@]}"; do
    if [[ -z "${step_includes[$index]}" ]]; then
      whole_ids+=("${step_ids[$index]}")
    else
      path_info="$(snapshot_path_size "${step_ids[$index]}" "${step_ls_paths[$index]}")"
      read -r step_count step_bytes <<< "$path_info"
      path_count=$((path_count + step_count))
      size_bytes=$((size_bytes + step_bytes))
    fi
  done
  size_bytes=$((size_bytes + $(snapshots_restore_size_bytes ${whole_ids[@]+"${whole_ids[@]}"})))
  if [[ -n "$scope" ]]; then
    [[ "$path_count" -gt 0 || "$databases_selected" -gt 0 || "$scope" == GIT-WORKTREE.patch ]] ||
      die "Nothing at --path $scope in snapshot $manifest_id."
  fi
  check_restore_space "$target_real" "$size_bytes"

  if [[ "$execute" -eq 0 ]]; then
    info "Restore preview only; no files will be written."
    if [[ -z "$scope" ]]; then
      restic_repository_command restore "$manifest_id" --target "$target_real" --overwrite never --dry-run --verbose=2
    else
      for index in "${!step_ids[@]}"; do
        restic_repository_command restore "${step_ids[$index]}" --target "$target_real" --overwrite never \
          ${step_includes[$index]:+--include "${step_includes[$index]}"} --dry-run --verbose=2
      done
    fi
    echo "Preview complete. Re-run with --execute to restore into: $target_real"
    return
  fi

  for index in "${!step_ids[@]}"; do
    # An older base snapshot can contain the same database the receipt lists
    # in a later batch. --overwrite never would keep that stale main file and
    # skip the consistent copy, so remove the receipt-listed path first.
    for db_index in "${!db_paths[@]}"; do
      [[ "${db_ids[$db_index]}" == "${step_ids[$index]}" ]] || continue
      database_path=${db_paths[$db_index]}
      [[ -n "${restored_db_set[$database_path]+set}" ]] || continue
      database_target="$target_real/$database_path"
      remove_restored_database_sidecars "$database_path" "$database_target"
      [[ -e "$database_target" || -L "$database_target" ]] || continue
      [[ -f "$database_target" && ! -L "$database_target" ]] ||
        die "Refusing to replace a non-regular restored database: $database_path"
      rm -f -- "$database_target" ||
        die "Could not remove the stale restored database: $database_path"
    done
    restic_repository_command restore "${step_ids[$index]}" --target "$target_real" --overwrite never \
      ${step_includes[$index]:+--include "${step_includes[$index]}"}
    if [[ -z "$scope" && "$index" -eq 0 ]]; then
      receipt="$target_real/BACKUP-RECEIPT.json"
      [[ -f "$receipt" && ! -L "$receipt" ]] ||
        die "Restored snapshot has no safe BACKUP-RECEIPT.json; refusing to claim a complete restore."
    fi
  done
  for index in "${!restored_db_paths[@]}"; do
    database_path="${restored_db_paths[$index]}"
    # The file-phase snapshot may have been applied after this database.
    remove_restored_database_sidecars "$database_path" "$target_real/$database_path"
    [[ -f "$target_real/$database_path" && ! -L "$target_real/$database_path" ]] ||
      die "Restored database is missing or unsafe: $database_path"
    chmod "${restored_db_modes[$index]}" "$target_real/$database_path"
  done
  while IFS= read -r -d '' database_path; do
    integrity_check_restored_database "$database_path" "${database_path#"$target_real"/}"
  done < <(find "$target_real" -type f \( -name '*.db' -o -name '*.sqlite*' \) \
    ! -name '*-wal' ! -name '*-shm' ! -name '*-journal' -print0)
  info "Restore complete. Validate the staged data before any live import: $target_real"
}

run_init() {
  local execute=$1

  validate_environment
  if [[ "$execute" -eq 1 ]]; then acquire_lock; fi
  validate_source
  if repository_is_initialized; then
    die "Restic repository is already initialized."
  fi
  if [[ "$execute" -eq 0 ]]; then
    info "Initialization preview only; no repository will be created."
    echo "Repository: $REPOSITORY"
    echo "Re-run with --execute after confirming the remote and password recovery plan."
    return
  fi
  restic_repository_command init
  restic_repository_command check
  info "Repository initialized and checked."
}

# Run-aware retention planner (jq). Input: the `restic snapshots --json` array
# for this backup family. Snapshots are grouped into runs by the lu-run-<id>
# tag the backup command writes; a snapshot without it is a self-contained
# legacy snapshot and forms its own complete run. A run is complete when its
# lu-part-complete receipt snapshot exists. The daily/weekly/monthly keep
# policy applies to completed runs only — counting runs, not snapshots — and
# every run newer than the newest completed run is protected (it may be in
# progress, or a failed run worth inspecting). Whole runs are dropped, so a
# retained receipt never loses a snapshot it references. An empty list or a
# list with no completed run errors out so the caller forgets nothing.
# Snapshot times may carry fractional seconds and a numeric offset. Convert
# each RFC 3339 timestamp to a UTC epoch before ordering or bucketing runs.
# shellcheck disable=SC2016  # $daily/$run/... are jq variables, not shell.
readonly SNAPSHOT_EPOCH_JQ='
def epoch_seconds:
  ([capture("^(?<base>[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\\.(?<fraction>[0-9]+))?(?<zone>Z|[+-][0-9]{2}:[0-9]{2})$")]
   | if length == 1 then .[0] else error("unparsable snapshot time") end) as $timestamp
  | (($timestamp.base + "Z" | strptime("%Y-%m-%dT%H:%M:%SZ") | mktime)
     + ("0." + ($timestamp.fraction // "0") | tonumber)
     - (if $timestamp.zone == "Z" then 0 else
          (if $timestamp.zone[0:1] == "+" then 1 else -1 end)
          * (($timestamp.zone[1:3] | tonumber) * 3600 + ($timestamp.zone[4:6] | tonumber) * 60)
        end));
'
# shellcheck disable=SC2016  # jq variables are not shell variables.
readonly RETENTION_PLAN_JQ="$SNAPSHOT_EPOCH_JQ"'
def run_key:
  ([.tags[]? | select(startswith("lu-run-"))][0]) // ("snapshot:" + .id);
def week_bucket:
  ((.epoch + 259200) / 604800 | floor);
def newest_per_bucket(bucket; limit):
  reduce .[] as $run ({seen: [], keep: []};
    ($run | bucket) as $value
    | if (.seen | any(. == $value)) then .
      elif (.seen | length) < limit then
        {seen: (.seen + [$value]), keep: (.keep + [$run.run])}
      else . end)
  | .keep;
([.[] | . as $snapshot | $snapshot + {run: ($snapshot | run_key)}]
 | group_by(.run)
 | map({
     run: .[0].run,
     time: (max_by(.time | epoch_seconds) | .time),
     epoch: (map(.time | epoch_seconds) | max),
     complete: (any(.[]; (.tags // []) | any(. == "lu-part-complete"))
                or (.[0].run | startswith("snapshot:"))),
     snapshots: [.[].id]
   })
 | sort_by(.epoch)) as $runs
| if ($runs | length) == 0 then error("snapshot list is empty") else . end
| ([$runs[] | select(.complete)]) as $completed
| if ($completed | length) == 0 then error("no completed backup runs in snapshot list") else . end
| ($completed | last | .epoch) as $newest_completed
| ([$runs[] | select(.epoch >= $newest_completed) | .run] | unique) as $protected
| ($completed | reverse) as $newest_first
| ($newest_first | newest_per_bucket(.epoch | strftime("%Y-%m-%d"); $daily)) as $daily_keep
| ($newest_first | newest_per_bucket(week_bucket; $weekly)) as $weekly_keep
| ($newest_first | newest_per_bucket(.epoch | strftime("%Y-%m"); $monthly)) as $monthly_keep
| (($daily_keep + $weekly_keep + $monthly_keep + $protected) | unique) as $keep_runs
| {
    keep: [$runs[] | select(.run as $r | ($keep_runs | any(. == $r)))
           | {run, time, complete, snapshots}],
    drop: [$runs[] | select(.run as $r | (($keep_runs | any(. == $r)) | not))
           | {run, time, complete, snapshots}],
    forget_ids: [$runs[] | select(.run as $r | (($keep_runs | any(. == $r)) | not))
                 | .snapshots[]]
  }
'

retention_snapshot_list() {
  restic_repository_command snapshots --json --host "$BACKUP_HOST" --tag "$BACKUP_TAG"
}

run_retention() {
  local execute=$1 ids_output
  local snapshots_json plan forget_count
  local forget_ids=()

  validate_environment
  acquire_lock
  require_initialized_repository
  snapshots_json="$(retention_snapshot_list)" ||
    die "Could not list snapshots of tag $BACKUP_TAG; refusing to plan retention."
  plan="$(jq -e \
    --argjson daily "$KEEP_DAILY" \
    --argjson weekly "$KEEP_WEEKLY" \
    --argjson monthly "$KEEP_MONTHLY" \
    "$RETENTION_PLAN_JQ" <<< "$snapshots_json")" ||
    die "Retention planning failed (empty or unparsable snapshot list, or no completed run); forgetting nothing."
  forget_count="$(jq -er '.forget_ids | length' <<< "$plan")" ||
    die "Retention plan is malformed; forgetting nothing."

  info "Retention plan for tag $BACKUP_TAG: keep-daily=$KEEP_DAILY keep-weekly=$KEEP_WEEKLY keep-monthly=$KEEP_MONTHLY applied to completed runs."
  jq -er '
    "Runs kept: \(.keep | length)",
    (.keep[] | "  keep \(.run) time=\(.time) snapshots=\(.snapshots | length)"),
    "Runs dropped: \(.drop | length)",
    (.drop[] | "  drop \(.run) time=\(.time) snapshots=\(.snapshots | length)"),
    "Snapshots to forget: \(.forget_ids | length)",
    (.forget_ids[] | "  forget \(.)")
  ' <<< "$plan"

  if [[ "$execute" -eq 0 ]]; then
    info "Retention preview only; no snapshots will be forgotten."
    echo "Preview complete. Re-run with --execute to apply the retention policy."
    return
  fi

  if [[ "$forget_count" -gt 0 ]]; then
    ids_output="$(jq -er '.forget_ids[]' <<< "$plan")" || die "Retention plan IDs could not be read; forgetting nothing."
    mapfile -t forget_ids <<< "$ids_output"
    [[ "${#forget_ids[@]}" -eq "$forget_count" ]] || die "Retention plan IDs could not be read; forgetting nothing."
    for id in "${forget_ids[@]}"; do
      [[ "$id" =~ ^[0-9a-f]{64}$ ]] || die "Retention plan has an invalid snapshot ID; forgetting nothing."
    done
    info "Forgetting ${#forget_ids[@]} snapshot(s) of dropped runs by explicit snapshot ID."
    restic_repository_command forget "${forget_ids[@]}"
  else
    info "Every run is inside the keep set; nothing to forget."
  fi
  info "Pruning unreferenced repository data."
  restic_repository_command prune
  info "Checking repository metadata after retention."
  restic_repository_command check
  info "Retention complete."
}

run_doctor() {
  local failures=0 validation_output unreadable unreadable_count

  echo "Backup source: $SOURCE"
  echo "Repository: ${REPOSITORY:-<unset>}"
  echo "Legacy Drive directory: read-only discovery"

  for command in restic rclone sqlite3 find git jq realpath touch flock; do
    if command -v "$command" >/dev/null 2>&1; then
      echo "OK: $command"
    else
      echo "MISSING: $command"
      failures=$((failures + 1))
    fi
  done

  if [[ "$failures" -eq 0 ]]; then
    if validation_output="$( (validate_environment; validate_source) 2>&1)"; then
      [[ -z "$validation_output" ]] || printf '%s\n' "$validation_output"
      discover_backup_paths
      unreadable="$(unreadable_backup_paths)"
      if [[ -n "$unreadable" ]]; then
        unreadable_count="$(printf '%s\n' "$unreadable" | wc -l)"
        echo "WARNING: $unreadable_count path(s) under backup roots are unreadable by the backup user:" >&2
        printf '%s\n' "$unreadable" | sed -n '1,20p' >&2
        if ((unreadable_count > 20)); then
          echo "  ... $((unreadable_count - 20)) more unreadable path(s)" >&2
        fi
      fi
      if repository_is_initialized; then
        echo "OK: restic repository is initialized"
      else
        echo "NOT READY: restic repository is inaccessible or not initialized; status unknown"
        failures=$((failures + 1))
      fi
    else
      printf 'NOT READY: %s\n' "$validation_output" >&2
      failures=$((failures + 1))
    fi
  fi

  if [[ "$failures" -ne 0 ]]; then
    echo "Doctor found $failures blocking problem(s)." >&2
    return 1
  fi
  echo "Doctor checks passed."
}

parse_execute_only() {
  local execute=0

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --execute)
        execute=1
        ;;
      *)
        die "Unknown option: $1"
        ;;
    esac
    shift
  done
  printf '%s\n' "$execute"
}

main() {
  local command=${1:-help}
  local execute snapshot target read_data
  shift || true

  case "$command" in
    help|-h|--help) ;;
    *) restic_rclone_connections >/dev/null || exit 1 ;;
  esac
  case "$command" in
    help|-h|--help)
      usage
      ;;
    doctor)
      [[ $# -eq 0 ]] || die "doctor does not accept arguments."
      run_doctor
      ;;
    init)
      execute="$(parse_execute_only "$@")"
      run_init "$execute"
      ;;
    backup)
      execute="$(parse_execute_only "$@")"
      run_backup "$execute"
      ;;
    retention)
      execute="$(parse_execute_only "$@")"
      run_retention "$execute"
      ;;
    snapshots)
      [[ $# -eq 0 ]] || die "snapshots does not accept arguments."
      validate_environment
      require_initialized_repository
      restic_repository_command snapshots --host "$BACKUP_HOST" --tag "$BACKUP_TAG"
      ;;
    verify)
      read_data=0
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --read-data)
            read_data=1
            ;;
          -*)
            die "Unknown option: $1"
            ;;
          *)
            die "verify checks the repository and does not accept snapshot IDs."
            ;;
        esac
        shift
      done
      validate_environment
      require_initialized_repository
      if [[ "$read_data" -eq 1 ]]; then
        restic_repository_command check --read-data
      else
        restic_repository_command check
      fi
      ;;
    restore)
      snapshot=""
      target=""
      scope=""
      scope_given=0
      execute=0
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --to)
            shift
            [[ $# -gt 0 ]] || die "--to requires an absolute directory."
            target=$1
            ;;
          --path)
            shift
            [[ $# -gt 0 ]] || die "--path requires a path relative to the run root."
            [[ "$scope_given" -eq 0 ]] || die "restore accepts exactly one --path."
            scope_given=1
            scope=$1
            ;;
          --execute)
            execute=1
            ;;
          -*)
            die "Unknown option: $1"
            ;;
          *)
            [[ -z "$snapshot" ]] || die "restore accepts exactly one snapshot ID."
            snapshot=$1
            ;;
        esac
        shift
      done
      [[ -n "$snapshot" ]] || die "restore requires a snapshot ID."
      [[ -n "$target" ]] || die "restore requires --to ABSOLUTE_EMPTY_DIR."
      run_restore "$snapshot" "$target" "$execute" "$scope" "$scope_given"
      ;;
    *)
      usage >&2
      die "Unknown command: $command"
      ;;
  esac
}

main "$@"
