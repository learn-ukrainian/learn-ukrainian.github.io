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
#   .agent/          Gitignored agent recovery state
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
EPHEMERAL_HOME_EXCLUDES=()
LINUX_DB_SNAPSHOTS='[]'
LINUX_BASE_SNAPSHOT=""
LINUX_PATCH_SNAPSHOT=""
RUN_ID=""
LINUX_MODE=0
BACKUP_FAILURES=()

write_restic_gate_receipt() {
  local snapshot_id=$1
  local staged_mirror_root="$STAGED_ROOT/data/lexicon/runner-mirror"
  local live_mirror_root="$SOURCE/lexicon/runner-mirror"
  local git_sha
  local project_python
  local common_dir
  local primary_root

  if [[ "${2:-}" == verified-live ]]; then
    staged_mirror_root="$live_mirror_root"
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

  # Layout A: dispatch worktrees have no local .venv. Prefer an explicit
  # override, then the script checkout's .venv, then the primary checkout
  # resolved via REPO_ROOT's git common dir (not PROJECT_ROOT — fixtures and
  # LU_BACKUP_PROJECT_ROOT overrides are often separate git trees).
  project_python="${LU_BACKUP_PYTHON:-}"
  if [[ -z "$project_python" || ! -x "$project_python" ]]; then
    if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
      project_python="$REPO_ROOT/.venv/bin/python"
    else
      common_dir="$(git -C "$REPO_ROOT" rev-parse --git-common-dir 2>/dev/null || true)"
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
  git_sha="$(git -C "$PROJECT_ROOT" rev-parse HEAD)"
  "$project_python" "$REPO_ROOT/scripts/lexicon/runner/durable_mirror.py" \
    write-restic-gate-receipt \
    --mirror-root "$staged_mirror_root" \
    --receipt-root "$live_mirror_root" \
    --restic-snapshot-id "$snapshot_id" \
    --host "$BACKUP_HOST" \
    --git-sha "$git_sha" \
    --mirror-root-relative-to-data "lexicon/runner-mirror" ||
    die "Could not write the runner mirror restic gate receipt after backup."
}

verify_linux_runner_mirror_and_receipt() {
  local snapshot_id=$1 mirror="$SOURCE/lexicon/runner-mirror"
  local snapshot_files="$STAGE_DIR/mirror-snapshot-files"
  local live_files="$STAGE_DIR/mirror-live-files"
  local path snapshot_hash live_hash
  [[ -e "$mirror" || -L "$mirror" ]] || return 0
  [[ -d "$mirror" && ! -L "$mirror" ]] || die "Runner mirror root must be a real directory."
  restic_repository_command ls --json --recursive "$snapshot_id" \
    /data/lexicon/runner-mirror \
    | jq -r 'select(.struct_type == "node" and .type == "file") | .path' \
    | LC_ALL=C sort > "$snapshot_files"
  find "$mirror" -type f -printf '/data/lexicon/runner-mirror/%P\n' \
    | LC_ALL=C sort > "$live_files"
  cmp -s "$snapshot_files" "$live_files" ||
    die "Runner mirror file set changed during backup; refusing to write a durability receipt."
  while IFS= read -r path; do
    snapshot_hash="$(restic_repository_command dump "$snapshot_id" "$path" | sha256sum | awk '{print $1}')"
    live_hash="$(sha256sum "$PROJECT_ROOT${path}" | awk '{print $1}')"
    [[ "$snapshot_hash" == "$live_hash" ]] ||
      die "Runner mirror content changed during backup; refusing to write a durability receipt."
  done < "$snapshot_files"
  write_restic_gate_receipt "$snapshot_id" verified-live
}

usage() {
  cat <<'EOF'
Usage:
  ./scripts/backup-data.sh doctor
  ./scripts/backup-data.sh init [--execute]
  ./scripts/backup-data.sh backup [--execute]
  ./scripts/backup-data.sh snapshots
  ./scripts/backup-data.sh verify [--read-data]
  ./scripts/backup-data.sh restore SNAPSHOT --to ABSOLUTE_EMPTY_DIR [--path RELATIVE_PATH] [--execute]

Safety:
  - init, backup, and restore are previews unless --execute is supplied.
  - backup requires epic state, .agent/, batch_state/, data/, and full source coverage.
  - successful snapshots contain BACKUP-RECEIPT.json and a restore command.
  - restore refuses non-empty, project, cloud, and legacy-backup targets.
  - restore first measures exactly what it will write (restic stats, restore-size)
    and refuses, writing nothing, unless the target filesystem has that much free
    space plus a margin (default 10%). The preview reports the same numbers.
  - restore --path RELATIVE_PATH restores only that file or directory of the run
    (for example data/atlas.db, read from its database snapshot via the receipt;
    other paths come from the file-phase snapshot). Same guards and preflight.
  - no command prunes or deletes snapshots.

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
  LU_BACKUP_TMPDIR      Private staging parent (default: $TMPDIR or /tmp).
  LU_BACKUP_TAG         Restic tag (default: learn-ukrainian-data).
  LU_BACKUP_HOST        Stable restic host label (default: learn-ukrainian).

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

restic_repository_command() {
  restic "$@" --option rclone.connections=1
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
  RESTIC_REPOSITORY="$REPOSITORY" \
    RESTIC_PASSWORD_FILE="$PASSWORD_FILE" \
    restic_repository_command cat config >/dev/null 2>&1
}

require_initialized_repository() {
  repository_is_initialized ||
    die "Restic repository is inaccessible or not initialized; verify remote authentication and repository status."
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

    if [[ "$relative" == "textbooks" || "$relative" == "vesum" ]]; then
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
      continue
    fi

    resolved="$(realpath "$link" 2>/dev/null)" ||
      die "Broken symlink in backup source: $relative -> $target"
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
    is_ephemeral_home_path "$link" && continue
    relative=${link#"$tree"/}
    target="$(readlink "$link")"
    [[ -e "$link" ]] ||
      die "Broken symlink in $label: $relative -> $target"
    resolved="$(realpath "$link" 2>/dev/null)" ||
      die "Broken symlink in $label: $relative -> $target"
    [[ "$target" != /* ]] ||
      die "Absolute symlink is not backup-safe in $label: $relative -> $target"
    path_is_within "$resolved" "$tree_real" ||
      die "Symlink escapes $label: $relative -> $target"
  done < <(find "$tree" -type l -print0)
}

discover_ephemeral_homes() {
  local home
  EPHEMERAL_HOME_EXCLUDES=()
  while IFS= read -r -d '' home; do
    EPHEMERAL_HOME_EXCLUDES+=("$home")
  done < <(find "$PROJECT_ROOT/batch_state" \( -type d -o -type l \) -name '*-home' -prune -print0)
  if [[ -d "$PROJECT_ROOT/batch_state/review-receipts" ]]; then
    while IFS= read -r -d '' home; do
      EPHEMERAL_HOME_EXCLUDES+=("$home")
    done < <(find "$PROJECT_ROOT/batch_state/review-receipts" \( -type d -o -type l \) -name home -prune -print0)
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
  done < <(find "$tree" ! -type d ! -type f ! -type l -print0)
}

discover_backup_paths() {
  local epic

  BACKUP_PATHS=()
  [[ ! -L "$PROJECT_ROOT/.claude" ]] ||
    die "Recovery parent must not be a symlink: .claude"
  [[ -d "$PROJECT_ROOT/.claude/atlas-epic" ]] ||
    die "Required recovery path is missing: .claude/atlas-epic"
  [[ ! -L "$PROJECT_ROOT/.claude/atlas-epic" ]] ||
    die "Required recovery path must not be a symlink: .claude/atlas-epic"
  [[ -d "$PROJECT_ROOT/batch_state" ]] ||
    die "Required recovery path is missing: batch_state"
  [[ ! -L "$PROJECT_ROOT/batch_state" ]] ||
    die "Required recovery path must not be a symlink: batch_state"
  [[ -d "$PROJECT_ROOT/.agent" ]] ||
    die "Required recovery path is missing: .agent"
  [[ ! -L "$PROJECT_ROOT/.agent" ]] ||
    die "Required recovery path must not be a symlink: .agent"

  for epic in "$PROJECT_ROOT"/.claude/*-epic; do
    [[ -d "$epic" ]] || continue
    [[ ! -L "$epic" ]] ||
      die "Epic recovery path must not be a symlink: ${epic#"$PROJECT_ROOT"/}"
    [[ "$(basename "$epic")" =~ ^[a-z0-9-]+-epic$ ]] ||
      die "Epic recovery path has an unsafe label: $(basename "$epic")"
    BACKUP_PATHS+=(".claude/$(basename "$epic")")
  done
  BACKUP_PATHS+=(".agent" "batch_state" "data")
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
  discover_ephemeral_homes
  validate_untracked_coverage
  validate_source_symlinks
  for relative in "${BACKUP_PATHS[@]}"; do
    [[ "$relative" != "data" && "$relative" != "GIT-WORKTREE.patch" && "$relative" != "BACKUP-RECEIPT.json" ]] || continue
    validate_tree_symlinks "$PROJECT_ROOT/$relative" "$relative"
  done
  validate_tree_file_types "$PROJECT_ROOT/.agent" ".agent"
}

acquire_lock() {
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    die "Another backup operation holds the local lock: $LOCK_DIR"
  fi
  LOCK_HELD=1
}

list_sqlite_sources() {
  local relative database

  while IFS= read -r -d '' database; do
    is_sqlite_database "$database" && printf '%s\0' "$database"
  done < <(find "$SOURCE" \
    \( -path "$SOURCE/qdrant" -o -type d -name __pycache__ \) -prune -o \
    -type f \( -name '*.db' -o -name '*.sqlite*' \) \
    ! -name '*-wal' ! -name '*-shm' ! -name '*-journal' \
    -print0)
  for relative in "${BACKUP_PATHS[@]}"; do
    [[ "$relative" != "data" && "$relative" != "GIT-WORKTREE.patch" && "$relative" != "BACKUP-RECEIPT.json" ]] || continue
    while IFS= read -r -d '' database; do
      is_ephemeral_home_path "$database" && continue
      [[ "$database" == */__pycache__/* ]] && continue
      is_sqlite_database "$database" && printf '%s\0' "$database"
    done < <(find "$PROJECT_ROOT/$relative" \
      -type f \( -name '*.db' -o -name '*.sqlite*' \) \
      ! -name '*-wal' ! -name '*-shm' ! -name '*-journal' -print0)
  done
}

is_sqlite_database() {
  local database=$1
  head -c 16 "$database" 2>/dev/null | cmp -s - <(printf 'SQLite format 3\0')
}

unreadable_backup_paths() {
  local relative root found path
  for relative in "${BACKUP_PATHS[@]}"; do
    [[ "$relative" == GIT-WORKTREE.patch || "$relative" == BACKUP-RECEIPT.json ]] && continue
    root="$(source_for_backup_path "$relative")"
    # Prune inaccessible directories so find can continue through other roots.
    # Capture any remaining permission errors without propagating find's status
    # into the caller's command substitution under set -e.
    found="$(LC_ALL=C find "$root" \
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

build_restic_excludes() {
  local root=$1
  local relative

  RESTIC_EXCLUDES=(
    --exclude "$root/qdrant"
    --exclude '**/*.db-wal'
    --exclude '**/*.db-shm'
    --exclude '**/*.db-journal'
    --exclude '**/*.sqlite-wal'
    --exclude '**/*.sqlite-shm'
    --exclude '**/*.sqlite-journal'
    --exclude '**/*.sqlite3-wal'
    --exclude '**/*.sqlite3-shm'
    --exclude '**/*.sqlite3-journal'
    --exclude '**/*.sqlite*-wal'
    --exclude '**/*.sqlite*-shm'
    --exclude '**/*.sqlite*-journal'
    --exclude '**/__pycache__/**'
    --exclude '**/.DS_Store'
    --exclude '**/batch_state/**/*-home'
    --exclude '**/batch_state/**/*-home/**'
    --exclude '**/batch_state/review-receipts/**/home'
    --exclude '**/batch_state/review-receipts/**/home/**'
  )
  if ((${#LEGACY_EXCLUDES[@]} > 0)); then
    for relative in "${LEGACY_EXCLUDES[@]}"; do
      RESTIC_EXCLUDES+=(--exclude "$root/$relative")
    done
  fi
  for relative in "${EPHEMERAL_HOME_EXCLUDES[@]}"; do
    RESTIC_EXCLUDES+=(--exclude "$relative")
  done
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
    find "$tree" -type f -printf '%s\n' |
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
  done < <(find "$tree" -type f -print0)
  printf '%s %s\n' "$total" "$count"
}

source_tree_stats() {
  local tree=$1 total=0 count=0 file relative size
  while IFS= read -r -d '' file && IFS= read -r -d '' size; do
    is_ephemeral_home_path "$file" && continue
    relative=${file#"$PROJECT_ROOT"/}
    case "$relative" in
      data/qdrant/*|*/__pycache__/*|*/.DS_Store|*.db-wal|*.db-shm|*.db-journal|*.sqlite*-wal|*.sqlite*-shm|*.sqlite*-journal) continue ;;
    esac
    total=$((total + size))
    count=$((count + 1))
  done < <(find "$tree" -type f -printf '%p\0%s\0')
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
  exclusions_json='["data/qdrant", "SQLite WAL/SHM/journal sidecars", "batch_state scoped review homes", "__pycache__", ".DS_Store"]'
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
    --argjson linux_mode "$([[ "$LINUX_MODE" -eq 1 ]] && echo true || echo false)" \
    --arg run_id "$RUN_ID" \
    --arg base_snapshot_id "$LINUX_BASE_SNAPSHOT" \
    --arg patch_snapshot_id "$LINUX_PATCH_SNAPSHOT" \
    --argjson databases "$LINUX_DB_SNAPSHOTS" \
    '{
      schema_version: (if $linux_mode then 2 else 1 end),
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
      linux_run: (if $linux_mode then {run_id: $run_id, base_snapshot_id: $base_snapshot_id, patch_snapshot_id: $patch_snapshot_id, databases: $databases} else null end)
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

linux_backup_database() {
  local source_db=$1 relative=$2 staged_db check_output snapshot_id source_mode error
  staged_db="$STAGED_ROOT/$relative"
  if ! error="$(check_one_db_space "$source_db" "$relative" 2>&1)"; then
    BACKUP_FAILURES+=("Database $relative: $error")
    return 1
  fi
  if ! mkdir -p "$(dirname "$staged_db")"; then
    BACKUP_FAILURES+=("Database $relative: could not create staging directory")
    return 1
  fi
  info "Creating consistent SQLite snapshot: $relative"
  if ! error="$(sqlite_backup_command "$source_db" "$staged_db" 2>&1)"; then
    BACKUP_FAILURES+=("Database $relative: SQLite online backup failed: ${error:-unknown error}")
    find "$staged_db" -maxdepth 0 -type f -delete
    return 1
  fi
  [[ -z "$error" ]] || printf '%s\n' "$error"
  if ! source_mode="$(file_mode "$source_db")" ||
    ! chmod "$source_mode" "$staged_db" ||
    ! touch -r "$source_db" "$staged_db"; then
    BACKUP_FAILURES+=("Database $relative: could not preserve source metadata")
    find "$staged_db" -maxdepth 0 -type f -delete
    return 1
  fi
  if ! check_output="$(sqlite3 "$(sqlite_immutable_uri "$staged_db")" 'PRAGMA integrity_check;' 2>&1)"; then
    BACKUP_FAILURES+=("Database $relative: SQLite integrity_check failed: $check_output")
    find "$staged_db" -maxdepth 0 -type f -delete
    return 1
  fi
  if [[ "$check_output" != ok ]]; then
    BACKUP_FAILURES+=("Database $relative: SQLite integrity_check rejected staged database: $check_output")
    find "$staged_db" -maxdepth 0 -type f -delete
    return 1
  fi
  if ! restic_repository_command backup --stdin --stdin-filename "$relative" \
    --host "$BACKUP_HOST" --tag "$BACKUP_TAG" --tag "lu-run-$RUN_ID" \
    --tag lu-part-db --json < "$staged_db" | tee "$STAGE_DIR/db-backup.jsonl"; then
    BACKUP_FAILURES+=("Database $relative: restic upload failed")
    find "$staged_db" -maxdepth 0 -type f -delete
    return 1
  fi
  if ! snapshot_id="$(snapshot_id_from_output "$STAGE_DIR/db-backup.jsonl" 2>&1)"; then
    BACKUP_FAILURES+=("Database $relative: $snapshot_id")
    find "$staged_db" -maxdepth 0 -type f -delete
    return 1
  fi
  if ! LINUX_DB_SNAPSHOTS="$(jq -cn --argjson previous "$LINUX_DB_SNAPSHOTS" \
    --arg path "$relative" --arg snapshot_id "$snapshot_id" --arg mode "$source_mode" \
    '$previous + [{path: $path, snapshot_id: $snapshot_id, mode: $mode}]')"; then
    BACKUP_FAILURES+=("Database $relative: could not record snapshot ID")
    find "$staged_db" -maxdepth 0 -type f -delete
    return 1
  fi
  find "$staged_db" -maxdepth 0 -type f -delete
}

run_linux_backup() {
  local relative source_db snapshot_id backup_output unreadable
  local -a live_paths=()

  LINUX_MODE=1
  RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$(printf '%04x%04x' "$RANDOM" "$RANDOM")"
  STAGE_DIR="$STAGE_PATH"
  [[ ! -L "$STAGE_DIR" ]] || die "Refusing symlink at the private staging path: $STAGE_DIR"
  [[ ! -e "$STAGE_DIR" ]] || die "Stale staging path exists; inspect it before retrying: $STAGE_DIR"
  mkdir -m 700 "$STAGE_DIR"
  STAGED_ROOT="$STAGE_DIR/project-state"
  mkdir -m 700 "$STAGED_ROOT"
  create_worktree_patch

  for relative in "${BACKUP_PATHS[@]}"; do
    [[ "$relative" == "GIT-WORKTREE.patch" ]] || live_paths+=("$relative")
  done
  build_restic_excludes "$SOURCE"
  while IFS= read -r -d '' source_db; do
    RESTIC_EXCLUDES+=(--exclude "$source_db")
    RESTIC_EXCLUDES+=(--exclude "$source_db-wal" --exclude "$source_db-shm" --exclude "$source_db-journal")
  done < <(list_sqlite_sources)
  info "Streaming non-database recovery files from the live tree."
  backup_output="$STAGE_DIR/base-backup.jsonl"
  if (
    cd "$PROJECT_ROOT"
    restic_repository_command backup "${live_paths[@]}" \
      --host "$BACKUP_HOST" --tag "$BACKUP_TAG" --tag "lu-run-$RUN_ID" \
      --tag lu-part-base --json "${RESTIC_EXCLUDES[@]}"
  ) | tee "$backup_output"; then
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

  while IFS= read -r -d '' source_db; do
    relative=${source_db#"$PROJECT_ROOT"/}
    if [[ "$relative" == *$'\n'* || "$relative" == *$'\t'* ]]; then
      BACKUP_FAILURES+=("Database path cannot be recorded safely: $relative")
      continue
    fi
    linux_backup_database "$source_db" "$relative" || true
  done < <(list_sqlite_sources)

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

  info "Checking repository metadata after backup."
  restic_repository_command check || BACKUP_FAILURES+=("Repository check failed")
  if ((${#BACKUP_FAILURES[@]} > 0)); then
    printf 'Backup run %s failed:\n' "$RUN_ID" >&2
    printf '  %s\n' "${BACKUP_FAILURES[@]}" >&2
    return 1
  fi

  write_backup_receipt
  restic_repository_command backup --stdin --stdin-filename BACKUP-RECEIPT.json \
    --host "$BACKUP_HOST" --tag "$BACKUP_TAG" --tag "lu-run-$RUN_ID" \
    --tag lu-part-complete --json < "$STAGED_ROOT/BACKUP-RECEIPT.json" \
    | tee "$STAGE_DIR/complete-backup.jsonl"
  snapshot_id="$(snapshot_id_from_output "$STAGE_DIR/complete-backup.jsonl")"
  restic_repository_command check
  verify_linux_runner_mirror_and_receipt "$LINUX_BASE_SNAPSHOT"
  info "Linux backup run $RUN_ID complete; receipt snapshot $snapshot_id."
}

run_backup() {
  local execute=$1
  local backup_root backup_output snapshot_id

  validate_environment
  validate_source
  print_backup_selection

  if [[ "$execute" -eq 0 ]]; then
    info "Backup preview only; no snapshot will be written."
    backup_root="$SOURCE"
    build_restic_excludes "$backup_root"
    if [[ "$(uname -s)" == Linux ]]; then
      while IFS= read -r -d '' source_db; do
        RESTIC_EXCLUDES+=(--exclude "$source_db")
        RESTIC_EXCLUDES+=(--exclude "$source_db-wal" --exclude "$source_db-shm" --exclude "$source_db-journal")
        echo "  SQLite online backup preview: ${source_db#"$PROJECT_ROOT"/}"
      done < <(list_sqlite_sources)
    fi
    require_initialized_repository
    (
      cd "$PROJECT_ROOT"
      restic_repository_command backup "${BACKUP_PATHS[@]}" \
        --dry-run \
        --verbose=2 \
        --host "$BACKUP_HOST" \
        --tag "$BACKUP_TAG" \
        "${RESTIC_EXCLUDES[@]}"
    )
    echo "Preview complete. Re-run with --execute to create a snapshot."
    return
  fi

  require_initialized_repository
  acquire_lock
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
  info "Creating encrypted, versioned restic snapshot."
  backup_output="$STAGE_DIR/restic-backup.jsonl"
  (
    cd "$STAGED_ROOT"
    restic_repository_command backup "${BACKUP_PATHS[@]}" \
      --host "$BACKUP_HOST" \
      --tag "$BACKUP_TAG" \
      --json \
      "${RESTIC_EXCLUDES[@]}"
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
  printf '%s\n' "$margin"
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
  [[ "$scope" != /* && "$scope" != "" ]] ||
    die "--path must be a non-empty path relative to the run root (for example data/atlas.db)."
  [[ "/$scope/" != *"/../"* && "/$scope/" != *"/./"* && "$scope" != *//* ]] ||
    die "--path must not contain '.', '..', or empty components: $scope"
  [[ "$scope" != *[\*\?\[\\]* && "$scope" != *$'\n'* && "$scope" != *$'\t'* ]] ||
    die "--path must be a literal path (no glob characters): $scope"
}

run_restore() {
  local snapshot=$1
  local target=$2
  local execute=$3
  local scope=${4:-}
  local target_real receipt receipt_json receipt_schema base_id patch_id database_id database_path database_mode check_output
  local manifest_id snapshots_json size_bytes path_info path_count path_bytes index
  local scope_is_database=0 databases_selected=0
  local -a whole_ids=() step_ids=() step_includes=() step_db_paths=() step_db_modes=()

  validate_environment
  require_initialized_repository
  [[ -n "$snapshot" && "$snapshot" != -* ]] || die "Invalid snapshot ID."
  restore_margin_percent >/dev/null
  [[ -z "$scope" ]] || validate_restore_scope "${scope%/}"
  scope="${scope%/}"
  target_real="$(validate_restore_target "$target")"

  manifest_id="$snapshot"
  if [[ "$snapshot" == latest && "$(uname -s)" == Linux ]]; then
    snapshots_json="$(restic_repository_command snapshots --json --host "$BACKUP_HOST" --tag "$BACKUP_TAG")"
    manifest_id="$(jq -r '[.[] | select(.tags | index("lu-part-complete"))] | sort_by(.time) | last | .id // empty' <<< "$snapshots_json")"
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
  [[ "$receipt_schema" == 1 || "$receipt_schema" == 2 ]] || die "Unsupported restored receipt schema."

  if [[ "$receipt_schema" == 1 ]]; then
    step_ids+=("$manifest_id")
    step_includes+=("${scope:+/$scope}")
    step_db_paths+=("")
    step_db_modes+=("")
  else
    jq -e '
      .linux_run.run_id | type == "string" and length > 0
    ' <<< "$receipt_json" >/dev/null || die "Restored Linux receipt has no run ID."
    jq -e '(.linux_run.databases | type == "array") and
      (.linux_run.databases | all(.[]; (.path | type == "string") and
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
      step_db_paths+=("" "")
      step_db_modes+=("" "")
      if [[ -n "$patch_id" ]]; then
        step_ids+=("$patch_id")
        step_includes+=("")
        step_db_paths+=("")
        step_db_modes+=("")
      fi
    elif [[ "$scope" == GIT-WORKTREE.patch ]]; then
      [[ -n "$patch_id" ]] || die "This run has no GIT-WORKTREE.patch (the worktree was clean)."
      step_ids+=("$patch_id")
      step_includes+=("")
      step_db_paths+=("")
      step_db_modes+=("")
    fi
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
      if [[ -z "$scope" || "$database_path" == "$scope" || "$database_path" == "$scope"/* ]]; then
        step_ids+=("$database_id")
        step_includes+=("")
        step_db_paths+=("$database_path")
        step_db_modes+=("$database_mode")
        databases_selected=$((databases_selected + 1))
        [[ "$database_path" != "$scope" ]] || scope_is_database=1
      fi
    done < <(jq -r '.linux_run.databases[] | [.path, .snapshot_id, .mode] | @tsv' <<< "$receipt_json")
    if [[ -n "$scope" && "$scope" != GIT-WORKTREE.patch && "$scope_is_database" -eq 0 ]]; then
      # Not a single database: the path lives in the file-phase snapshot (and
      # any databases beneath it were already selected above).
      step_ids+=("$base_id")
      step_includes+=("/$scope")
      step_db_paths+=("")
      step_db_modes+=("")
    fi
  fi

  # Exact size of what will be restored: whole snapshots via restic stats,
  # path-scoped file-phase reads via ls.
  size_bytes=0
  path_count=0
  for index in "${!step_ids[@]}"; do
    if [[ -z "${step_includes[$index]}" ]]; then
      whole_ids+=("${step_ids[$index]}")
    else
      path_info="$(snapshot_path_size "${step_ids[$index]}" "$scope")"
      read -r path_count path_bytes <<< "$path_info"
      size_bytes=$((size_bytes + path_bytes))
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

  acquire_lock
  for index in "${!step_ids[@]}"; do
    restic_repository_command restore "${step_ids[$index]}" --target "$target_real" --overwrite never \
      ${step_includes[$index]:+--include "${step_includes[$index]}"}
    if [[ -z "$scope" && "$index" -eq 0 ]]; then
      receipt="$target_real/BACKUP-RECEIPT.json"
      [[ -f "$receipt" && ! -L "$receipt" ]] ||
        die "Restored snapshot has no safe BACKUP-RECEIPT.json; refusing to claim a complete restore."
    fi
    database_path="${step_db_paths[$index]}"
    if [[ -n "$database_path" ]]; then
      [[ -f "$target_real/$database_path" && ! -L "$target_real/$database_path" ]] ||
        die "Restored database is missing or unsafe: $database_path"
      chmod "${step_db_modes[$index]}" "$target_real/$database_path"
    fi
  done
  while IFS= read -r -d '' database_path; do
    check_output="$(sqlite3 "$(sqlite_immutable_uri "$database_path")" 'PRAGMA integrity_check;')" ||
      die "SQLite integrity_check failed on restored database: ${database_path#"$target_real"/}"
    [[ "$check_output" == ok ]] ||
      die "SQLite integrity_check rejected restored database: ${database_path#"$target_real"/}"
  done < <(find "$target_real" -type f \( -name '*.db' -o -name '*.sqlite*' \) \
    ! -name '*-wal' ! -name '*-shm' ! -name '*-journal' -print0)
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
  restic_repository_command init
  restic_repository_command check
  info "Repository initialized and checked."
}

run_doctor() {
  local failures=0 validation_output unreadable unreadable_count

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
            [[ -z "$scope" ]] || die "restore accepts exactly one --path."
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
      run_restore "$snapshot" "$target" "$execute" "$scope"
      ;;
    *)
      usage >&2
      die "Unknown command: $command"
      ;;
  esac
}

main "$@"
