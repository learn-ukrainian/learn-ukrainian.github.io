#!/usr/bin/env bash
#
# Versioned, encrypted backup and staging-only restore for recovery-critical
# project state.
#
# This script intentionally does not write to the Google Drive Desktop mount.
# It uses restic's rclone backend so snapshots are versioned, deduplicated, and
# transferred without hydrating Drive's local File Provider cache.
#
# Covers:
#   .claude/*-epic/  Gitignored driver plans and handoffs
#   batch_state/     Gitignored local fleet/delegate state
#   data/            SQLite databases, embeddings, and private inputs
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
# Mutating commands are previews unless --execute is present. There is no
# prune/delete command. See docs/runbooks/data-backup.md.

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
readonly MAX_FULL_COPY_BYTES=$((64 * 1024 * 1024))
readonly CLOUD_ROOT="${HOME}/Library/CloudStorage"
readonly TMP_ROOT="${LU_BACKUP_TMPDIR:-${TMPDIR:-/tmp}}"
readonly LOCK_DIR="$TMP_ROOT/learn-ukrainian-backup.${UID}.lock"
readonly STAGE_PATH="$TMP_ROOT/learn-ukrainian-backup.${UID}.stage"

STAGE_DIR=""
STAGED_ROOT=""
LOCK_HELD=0
LEGACY_DIR=""
RESTIC_EXCLUDES=()
LEGACY_EXCLUDES=()
BACKUP_PATHS=()

usage() {
  cat <<'EOF'
Usage:
  ./scripts/backup-data.sh doctor
  ./scripts/backup-data.sh init [--execute]
  ./scripts/backup-data.sh backup [--execute]
  ./scripts/backup-data.sh snapshots
  ./scripts/backup-data.sh verify [SNAPSHOT] [--read-data]
  ./scripts/backup-data.sh restore SNAPSHOT --to ABSOLUTE_EMPTY_DIR [--execute]

Safety:
  - init, backup, and restore are previews unless --execute is supplied.
  - backup requires epic state, batch_state/, data/, and full source coverage.
  - successful snapshots contain BACKUP-RECEIPT.json and a restore command.
  - restore refuses non-empty, project, cloud, and legacy-backup targets.
  - no command prunes or deletes snapshots.

Required environment:
  LU_BACKUP_REPOSITORY  Restic rclone backend, for example:
                        rclone:lu-gdrive:Projects/learn-ukrainian-restic
  RESTIC_PASSWORD_FILE Absolute path to a mode-600 restic password file.

Optional environment:
  LU_BACKUP_PROJECT_ROOT
                        Project checkout (default: script's repository).
  LU_BACKUP_LEGACY_DIR Read-only legacy Drive directory used for symlink checks.
  LU_BACKUP_TMPDIR      Private staging parent (default: $TMPDIR or /tmp).
  LU_BACKUP_TAG         Restic tag (default: learn-ukrainian-data).
  LU_BACKUP_HOST        Stable restic host label (default: learn-ukrainian).
EOF
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

info() {
  echo "==> $*"
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

  if [[ "$LOCK_HELD" -eq 1 && -d "$LOCK_DIR" ]]; then
    rmdir "$LOCK_DIR" 2>/dev/null || true
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

canonical_existing_dir() {
  local path=$1
  [[ -d "$path" ]] || return 1
  (cd "$path" && pwd -P)
}

canonical_target() {
  local path=$1
  local parent base

  [[ "$path" == /* ]] || die "Path must be absolute: $path"
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
  [[ "$child" == "$parent" || "$child" == "$parent/"* ]]
}

paths_overlap() {
  local first=$1
  local second=$2
  path_is_within "$first" "$second" || path_is_within "$second" "$first"
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
  [[ -f "$PASSWORD_FILE" ]] || die "Password file does not exist: $PASSWORD_FILE"
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
    die "rclone remote '$remote_name:' is not configured. Run 'rclone config' first."
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
  check_restic_version
  validate_password_file
  validate_repository_config

  [[ "$PROJECT_ROOT" == /* ]] || die "LU_BACKUP_PROJECT_ROOT must be absolute."
  [[ -d "$PROJECT_ROOT" ]] || die "Project checkout does not exist: $PROJECT_ROOT"
  [[ -d "$SOURCE" ]] || die "Backup source does not exist: $SOURCE"
  [[ -d "$TMP_ROOT" ]] || die "Staging parent does not exist: $TMP_ROOT"
}

repository_is_initialized() {
  restic cat config >/dev/null 2>&1
}

require_initialized_repository() {
  repository_is_initialized ||
    die "Restic repository is not initialized. Preview and run 'init --execute'."
}

validate_source_symlinks() {
  local link relative target resolved
  local source_real

  [[ ! -L "$SOURCE" ]] || die "Backup source must not be a symlink: data"
  source_real="$(canonical_existing_dir "$SOURCE")"
  LEGACY_EXCLUDES=()
  while IFS= read -r -d '' link; do
    relative=${link#"$SOURCE"/}
    target="$(readlink "$link")"
    resolved="$(realpath "$link" 2>/dev/null)" ||
      die "Broken symlink in backup source: $relative -> $target"

    if [[ "$relative" == "textbooks" || "$relative" == "vesum" ]]; then
      [[ -n "$LEGACY_DIR" ]] ||
        die "Legacy symlink found but the legacy Drive directory is unavailable: $relative"
      path_is_within "$resolved" "$LEGACY_DIR" ||
        die "Known legacy symlink points outside the legacy backup: $relative -> $target"
      LEGACY_EXCLUDES+=("$relative")
      echo "EXCLUDED legacy Drive symlink: $relative -> $target"
      continue
    fi

    [[ "$target" != /* ]] ||
      die "Absolute symlink is not backup-safe: $relative -> $target"
    path_is_within "$resolved" "$source_real" ||
      die "Symlink escapes the backup source: $relative -> $target"
  done < <(
    find "$SOURCE" \
      -path "$SOURCE/qdrant" -prune -o \
      -type l -print0
  )
}

validate_tree_symlinks() {
  local tree=$1
  local label=$2
  local link relative target resolved tree_real

  [[ ! -L "$tree" ]] || die "Backup root must not be a symlink: $label"
  tree_real="$(canonical_existing_dir "$tree")"
  while IFS= read -r -d '' link; do
    relative=${link#"$tree"/}
    target="$(readlink "$link")"
    resolved="$(realpath "$link" 2>/dev/null)" ||
      die "Broken symlink in $label: $relative -> $target"
    [[ "$target" != /* ]] ||
      die "Absolute symlink is not backup-safe in $label: $relative -> $target"
    path_is_within "$resolved" "$tree_real" ||
      die "Symlink escapes $label: $relative -> $target"
  done < <(find "$tree" -type l -print0)
}

discover_backup_paths() {
  local epic

  BACKUP_PATHS=()
  [[ -d "$PROJECT_ROOT/.claude/atlas-epic" ]] ||
    die "Required recovery path is missing: .claude/atlas-epic"
  [[ ! -L "$PROJECT_ROOT/.claude/atlas-epic" ]] ||
    die "Required recovery path must not be a symlink: .claude/atlas-epic"
  [[ -d "$PROJECT_ROOT/batch_state" ]] ||
    die "Required recovery path is missing: batch_state"
  [[ ! -L "$PROJECT_ROOT/batch_state" ]] ||
    die "Required recovery path must not be a symlink: batch_state"

  for epic in "$PROJECT_ROOT"/.claude/*-epic; do
    [[ -d "$epic" ]] || continue
    [[ ! -L "$epic" ]] ||
      die "Epic recovery path must not be a symlink: ${epic#"$PROJECT_ROOT"/}"
    [[ "$(basename "$epic")" =~ ^[a-z0-9-]+-epic$ ]] ||
      die "Epic recovery path has an unsafe label: $(basename "$epic")"
    BACKUP_PATHS+=(".claude/$(basename "$epic")")
  done
  BACKUP_PATHS+=("batch_state" "data")
}

path_has_backup_coverage() {
  local relative=$1
  local backup_path

  for backup_path in "${BACKUP_PATHS[@]}"; do
    path_is_within "$relative" "$backup_path" && return 0
  done
  return 1
}

validate_untracked_coverage() {
  local relative uncovered=0

  while IFS= read -r -d '' relative; do
    path_has_backup_coverage "$relative" && continue
    echo "UNBACKED untracked Git path: $relative" >&2
    uncovered=$((uncovered + 1))
  done < <(git -C "$PROJECT_ROOT" ls-files --others --exclude-standard -z)
  [[ "$uncovered" -eq 0 ]] ||
    die "$uncovered untracked path(s) are outside Git and declared recovery roots."
}

validate_source() {
  local source_real repo_real project_real tmp_real git_root relative

  source_real="$(canonical_existing_dir "$SOURCE")"
  repo_real="$(canonical_existing_dir "$REPO_ROOT")"
  project_real="$(canonical_existing_dir "$PROJECT_ROOT")"
  tmp_real="$(canonical_existing_dir "$TMP_ROOT")"
  git_root="$(git -C "$PROJECT_ROOT" rev-parse --show-toplevel 2>/dev/null)" ||
    die "Project root is not a Git checkout: $PROJECT_ROOT"
  git_root="$(canonical_existing_dir "$git_root")"
  [[ "$git_root" == "$project_real" ]] ||
    die "LU_BACKUP_PROJECT_ROOT must be the Git checkout root."

  paths_overlap "$source_real" "$tmp_real" &&
    die "Staging directory and backup source overlap."
  paths_overlap "$repo_real" "$tmp_real" &&
    die "Staging directory must be outside the project checkout."
  paths_overlap "$project_real" "$tmp_real" &&
    die "Staging directory must be outside the selected project checkout."
  [[ "$source_real" != "$project_real" ]] ||
    die "Refusing to back up the entire repository as data/."
  resolve_legacy_dir
  discover_backup_paths
  validate_untracked_coverage
  validate_source_symlinks
  for relative in "${BACKUP_PATHS[@]}"; do
    [[ "$relative" != "data" ]] || continue
    validate_tree_symlinks "$PROJECT_ROOT/$relative" "$relative"
  done
}

acquire_lock() {
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    die "Another backup operation holds the local lock: $LOCK_DIR"
  fi
  LOCK_HELD=1
}

list_sqlite_sources() {
  local relative

  find "$SOURCE" \
    -path "$SOURCE/qdrant" -prune -o \
    -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) \
    -print0
  for relative in "${BACKUP_PATHS[@]}"; do
    [[ "$relative" != "data" ]] || continue
    find "$PROJECT_ROOT/$relative" \
      -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) \
      -print0
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
  local db_bytes required_kib free_kib
  local -r safety_kib=$((2 * 1024 * 1024))

  db_bytes="$(db_size_bytes)"
  required_kib=$(((db_bytes + 1023) / 1024 + safety_kib))
  free_kib="$(available_kib)"
  [[ "$free_kib" =~ ^[0-9]+$ ]] || die "Could not determine staging free space."
  ((free_kib >= required_kib)) ||
    die "Insufficient staging space: need at least ${required_kib} KiB, have ${free_kib} KiB."
}

clone_tree() {
  local source=$1
  local destination=$2
  local source_bytes source_files

  case "$(uname -s)" in
    Darwin)
      /bin/cp -cRp "$source" "$destination" ||
        die "APFS copy-on-write staging failed; refusing a full data copy."
      ;;
    Linux)
      if cp -a --reflink=always "$source" "$destination" 2>/dev/null; then
        return
      fi
      if [[ -e "$destination" ]]; then
        find "$destination" -depth -delete
      fi
      read -r source_bytes source_files < <(tree_file_stats "$source")
      ((source_bytes <= MAX_FULL_COPY_BYTES)) ||
        die "Copy-on-write staging failed for $source_files files (${source_bytes} bytes); refusing a large full copy."
      info "Copy-on-write unavailable; using bounded full-copy fallback (${source_bytes} bytes)."
      cp -a "$source" "$destination" ||
        die "Bounded full-copy staging failed."
      ;;
    *)
      die "Copy-on-write staging is unsupported on this operating system."
      ;;
  esac
}

sqlite_backup_command() {
  local source_db=$1
  local destination_db=$2

  [[ "$source_db" != *"'"* && "$destination_db" != *"'"* ]] ||
    die "SQLite backup paths may not contain a single quote."
  sqlite3 -readonly "$source_db" ".backup '$destination_db'"
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

build_restic_excludes() {
  local root=$1
  local relative

  RESTIC_EXCLUDES=(
    --exclude "$root/qdrant"
    --exclude '**/*.db-wal'
    --exclude '**/*.db-shm'
    --exclude '**/__pycache__/**'
    --exclude '**/.DS_Store'
  )
  if ((${#LEGACY_EXCLUDES[@]} > 0)); then
    for relative in "${LEGACY_EXCLUDES[@]}"; do
      RESTIC_EXCLUDES+=(--exclude "$root/$relative")
    done
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

  while IFS= read -r -d '' file; do
    if size="$(stat -f '%z' "$file" 2>/dev/null)"; then
      :
    else
      size="$(stat -c '%s' "$file")"
    fi
    total=$((total + size))
    count=$((count + 1))
  done < <(find "$tree" -type f -print0)
  printf '%s %s\n' "$total" "$count"
}

print_backup_selection() {
  local relative source_path bytes files
  local missing_seed="$PROJECT_ROOT/.claude/atlas-epic/plans/curated-seed"

  info "Recovery roots selected (repo-local sole copies first):"
  for relative in "${BACKUP_PATHS[@]}"; do
    source_path="$(source_for_backup_path "$relative")"
    read -r bytes files < <(tree_file_stats "$source_path")
    printf '  %s files=%s bytes=%s\n' "$relative" "$files" "$bytes"
  done
  echo "  BACKUP-RECEIPT.json generated during an executed backup"
  echo "  GIT-WORKTREE.patch generated when tracked changes are present"
  if [[ ! -d "$missing_seed" ]]; then
    echo "WARNING: known previously lost path is absent: .claude/atlas-epic/plans/curated-seed" >&2
  fi
}

create_worktree_patch() {
  if ! git -C "$PROJECT_ROOT" diff --quiet HEAD --; then
    git -C "$PROJECT_ROOT" diff --binary HEAD -- \
      > "$STAGED_ROOT/GIT-WORKTREE.patch"
    BACKUP_PATHS+=("GIT-WORKTREE.patch")
  fi
}

write_backup_receipt() {
  local inventory_file="$STAGE_DIR/path-inventory.jsonl"
  local relative bytes files git_sha git_dirty untracked_count
  local inventory_json known_missing created_at exclusions_json

  : > "$inventory_file"
  for relative in "${BACKUP_PATHS[@]}"; do
    read -r bytes files < <(tree_file_stats "$STAGED_ROOT/$relative")
    jq -cn \
      --arg path "$relative" \
      --argjson files "$files" \
      --argjson bytes "$bytes" \
      '{path: $path, files: $files, bytes: $bytes}' \
      >> "$inventory_file"
  done
  inventory_json="$(jq -s '.' "$inventory_file")"
  find "$inventory_file" -maxdepth 0 -type f -delete

  git_sha="$(git -C "$PROJECT_ROOT" rev-parse HEAD)"
  git_dirty=false
  git -C "$PROJECT_ROOT" diff --quiet HEAD -- || git_dirty=true
  untracked_count=0
  while IFS= read -r -d '' relative; do
    path_has_backup_coverage "$relative" && continue
    untracked_count=$((untracked_count + 1))
  done < <(git -C "$PROJECT_ROOT" ls-files --others --exclude-standard -z)
  known_missing='[]'
  if [[ ! -d "$PROJECT_ROOT/.claude/atlas-epic/plans/curated-seed" ]]; then
    known_missing='[".claude/atlas-epic/plans/curated-seed"]'
  fi
  created_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  exclusions_json='["data/qdrant", "*.db-wal", "*.db-shm", "__pycache__", ".DS_Store"]'
  if ((${#LEGACY_EXCLUDES[@]} > 0)); then
    for relative in "${LEGACY_EXCLUDES[@]}"; do
      exclusions_json="$(
        jq -cn \
          --argjson current "$exclusions_json" \
          --arg path "data/$relative legacy symlink" \
          '$current + [$path]'
      )"
    done
  fi

  jq -n \
    --arg created_at "$created_at" \
    --arg host "$BACKUP_HOST" \
    --arg git_sha "$git_sha" \
    --arg tag "$BACKUP_TAG" \
    --argjson git_dirty "$git_dirty" \
    --argjson untracked_count "$untracked_count" \
    --argjson paths "$inventory_json" \
    --argjson known_missing "$known_missing" \
    --argjson exclusions "$exclusions_json" \
    '{
      schema_version: 1,
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
      restore_command: "./scripts/backup-data.sh restore latest --to /absolute/empty/directory --execute"
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
  create_worktree_patch
  write_backup_receipt
}

run_backup() {
  local execute=$1
  local backup_root

  validate_environment
  validate_source
  require_initialized_repository
  print_backup_selection

  if [[ "$execute" -eq 0 ]]; then
    info "Backup preview only; no snapshot will be written."
    backup_root="$SOURCE"
    build_restic_excludes "$backup_root"
    (
      cd "$PROJECT_ROOT"
      restic backup "${BACKUP_PATHS[@]}" \
        --dry-run \
        --verbose=2 \
        --host "$BACKUP_HOST" \
        --tag "$BACKUP_TAG" \
        "${RESTIC_EXCLUDES[@]}"
    )
    echo "Preview complete. Re-run with --execute to create a snapshot."
    return
  fi

  acquire_lock
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
  info "Creating encrypted, versioned restic snapshot."
  (
    cd "$STAGED_ROOT"
    restic backup "${BACKUP_PATHS[@]}" \
      --host "$BACKUP_HOST" \
      --tag "$BACKUP_TAG" \
      "${RESTIC_EXCLUDES[@]}"
  )
  info "Checking repository metadata after backup."
  restic check
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

run_restore() {
  local snapshot=$1
  local target=$2
  local execute=$3
  local target_real
  local -a args

  validate_environment
  require_initialized_repository
  [[ -n "$snapshot" && "$snapshot" != -* ]] || die "Invalid snapshot ID."
  target_real="$(validate_restore_target "$target")"

  args=(restore "$snapshot" --target "$target_real" --overwrite never)
  if [[ "$execute" -eq 0 ]]; then
    info "Restore preview only; no files will be written."
    restic "${args[@]}" --dry-run --verbose=2
    echo "Preview complete. Re-run with --execute to restore into: $target_real"
    return
  fi

  acquire_lock
  restic "${args[@]}"
  info "Restore complete. Validate the staged data before any live import: $target_real"
}

run_init() {
  local execute=$1

  validate_environment
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
  acquire_lock
  restic init
  restic check
  info "Repository initialized and checked."
}

run_doctor() {
  local failures=0 validation_output

  echo "Backup source: $SOURCE"
  echo "Repository: ${REPOSITORY:-<unset>}"
  echo "Legacy Drive directory: read-only discovery"

  for command in restic rclone sqlite3 find git jq realpath touch; do
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
      if repository_is_initialized; then
        echo "OK: restic repository is initialized"
      else
        echo "NOT READY: restic repository is not initialized"
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
    snapshots)
      [[ $# -eq 0 ]] || die "snapshots does not accept arguments."
      validate_environment
      require_initialized_repository
      restic snapshots --host "$BACKUP_HOST" --tag "$BACKUP_TAG"
      ;;
    verify)
      snapshot=""
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
            [[ -z "$snapshot" ]] || die "verify accepts at most one snapshot ID."
            snapshot=$1
            ;;
        esac
        shift
      done
      validate_environment
      require_initialized_repository
      if [[ "$read_data" -eq 1 ]]; then
        if [[ -n "$snapshot" ]]; then
          restic check --read-data "$snapshot"
        else
          restic check --read-data
        fi
      elif [[ -n "$snapshot" ]]; then
        restic check "$snapshot"
      else
        restic check
      fi
      ;;
    restore)
      snapshot=""
      target=""
      execute=0
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --to)
            shift
            [[ $# -gt 0 ]] || die "--to requires an absolute directory."
            target=$1
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
      run_restore "$snapshot" "$target" "$execute"
      ;;
    *)
      usage >&2
      die "Unknown command: $command"
      ;;
  esac
}

main "$@"
