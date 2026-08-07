#!/usr/bin/env bash
# Mac-side orchestrator for #6369 Class-B residual EN re-enrich. Runs the job
# on the pilot VPS (atlas-runner), never on this laptop.
#
# The VPS repo checkout is routinely stale (large data/ dirs deliberately
# deleted for disk headroom, uncommitted local diffs) — this script never
# runs `git pull`/`checkout`/`reset` there. Instead it scp's the current
# worktree's driver + launcher into the *work-dir* only, leaving the VPS repo
# checkout untouched. This is the "OR scp the script from PR branch" fallback
# from the #6369 dispatch brief.
#
# Steps: sync (residual slugs + driver + launcher) -> launch (detached,
# idempotent, memory-capped) -> optional poll -> pull manifest + log +
# summary back into this worktree for the PR / publish gate.
#
# Usage:
#   scripts/lexicon/runner/launch_reenrich_class_b_remote.sh              # full run
#   scripts/lexicon/runner/launch_reenrich_class_b_remote.sh --limit 5    # smoke
#   scripts/lexicon/runner/launch_reenrich_class_b_remote.sh --no-poll    # fire-and-forget
#   scripts/lexicon/runner/launch_reenrich_class_b_remote.sh --pull-only  # just pull artifacts back
#
# Env overrides:
#   ATLAS_RUNNER_HOST (default vps), ATLAS_RUN_ROOT, ATLAS_REPO,
#   ATLAS_RE_ENRICH_WORK_DIR, ATLAS_RE_ENRICH_RESIDUAL (local slugs dump),
#   ATLAS_RE_ENRICH_OUT_DIR (local pull-back dir),
#   ATLAS_RE_ENRICH_POLL_TIMEOUT_S (default 900),
#   ATLAS_RE_ENRICH_POLL_INTERVAL_S (default 15)
set -euo pipefail

WORKTREE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

HOST="${ATLAS_RUNNER_HOST:-vps}"
RUN_ROOT="${ATLAS_RUN_ROOT:-/home/ops/atlas-runner}"
REMOTE_REPO="${ATLAS_REPO:-$RUN_ROOT/repo}"
REMOTE_WORK_DIR="${ATLAS_RE_ENRICH_WORK_DIR:-$RUN_ROOT/run-class-b-reenrich}"

LOCAL_RESIDUAL="${ATLAS_RE_ENRICH_RESIDUAL:-$WORKTREE/batch_state/atlas-6369-class-b-no-en.json}"
LOCAL_OUT_DIR="${ATLAS_RE_ENRICH_OUT_DIR:-$WORKTREE/batch_state/class-b-reenrich-pulled}"
LOCAL_DRIVER="$WORKTREE/scripts/lexicon/reenrich_thin_manifest_entries.py"
LOCAL_LAUNCHER="$WORKTREE/scripts/lexicon/runner/launch_reenrich_class_b.sh"

POLL_TIMEOUT_S="${ATLAS_RE_ENRICH_POLL_TIMEOUT_S:-900}"
POLL_INTERVAL_S="${ATLAS_RE_ENRICH_POLL_INTERVAL_S:-15}"

do_poll=1
do_sync_and_launch=1
EXTRA_ARGS=()
for arg in "$@"; do
  case "$arg" in
    --no-poll) do_poll=0 ;;
    --pull-only) do_sync_and_launch=0; do_poll=0 ;;
    *) EXTRA_ARGS+=("$arg") ;;
  esac
done

ssh_q() { ssh -o BatchMode=yes -o ConnectTimeout=10 -- "$HOST" "$@"; }
scp_q() { scp -o BatchMode=yes -o ConnectTimeout=10 -- "$@"; }

if ! ssh_q "true" 2>/dev/null; then
  echo "cannot reach $HOST over SSH (BatchMode); check ~/.ssh/config" >&2
  exit 1
fi

# HARD GATE — sources.db on VPS must match local Mac (operator 2026-08-06).
# Stale VPS DBs silently underfill EN residual. Compare byte size; rsync if
# mismatched; fail closed if still mismatched after sync.
#
# LOCAL_SOURCES_DB is resolved to its real target below (data/sources.db is a
# symlink into the primary checkout in worktree layouts) — `stat` on macOS
# does NOT dereference symlinks by default, and neither does `rsync -a`
# (which preserves them as symlinks, i.e. -l). Without resolving first, a
# size mismatch against the symlink's own tiny size (the length of its
# target path, not the file it points to) causes rsync to overwrite the
# remote's real multi-GB file with a dangling symlink pointing at a
# Mac-only path — a real data-loss incident hit exactly this on 2026-08-06,
# recovered from a /home/ops/atlas-runner/data/sources.db backup copy.
# Always resolve to a real regular-file path before comparing or syncing.
LOCAL_SOURCES_DB_CANDIDATE="${ATLAS_LOCAL_SOURCES_DB:-$WORKTREE/data/sources.db}"
REMOTE_SOURCES_DB="${ATLAS_SOURCES_DB:-$REMOTE_REPO/data/sources.db}"
if [[ ! -e "$LOCAL_SOURCES_DB_CANDIDATE" ]]; then
  # Fall back to primary checkout data path (worktrees often sparse/omit data/)
  if [[ -e "/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db" ]]; then
    LOCAL_SOURCES_DB_CANDIDATE="/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db"
  else
    echo "local sources.db not found (tried worktree + primary checkout)" >&2
    exit 1
  fi
fi
LOCAL_SOURCES_DB="$(python3 -c "import pathlib, sys; print(pathlib.Path(sys.argv[1]).resolve())" "$LOCAL_SOURCES_DB_CANDIDATE")"
if [[ ! -f "$LOCAL_SOURCES_DB" ]]; then
  echo "resolved local sources.db is not a regular file: $LOCAL_SOURCES_DB" >&2
  exit 1
fi

_local_sz() {
  if stat -f '%z' "$1" >/dev/null 2>&1; then
    stat -f '%z' "$1"
  else
    stat -c '%s' "$1"
  fi
}

local_sz="$(_local_sz "$LOCAL_SOURCES_DB")"
remote_sz="$(ssh_q "if test -f $(printf '%q' "$REMOTE_SOURCES_DB"); then stat -L -c '%s' $(printf '%q' "$REMOTE_SOURCES_DB"); else echo 0; fi")"
echo "sources.db preflight local=$local_sz remote=$remote_sz path=$REMOTE_SOURCES_DB"
if [[ "$local_sz" != "$remote_sz" ]]; then
  echo "sources.db STALE on $HOST — rsync local -> remote (this is network I/O, not Mac CPU burn)"
  # Checkpoint WAL when possible so single-file rsync is consistent
  if command -v sqlite3 >/dev/null 2>&1 && [[ -f "${LOCAL_SOURCES_DB}-wal" ]]; then
    sqlite3 "$LOCAL_SOURCES_DB" 'PRAGMA wal_checkpoint(TRUNCATE);' >/dev/null 2>&1 || true
    local_sz="$(_local_sz "$LOCAL_SOURCES_DB")"
  fi
  ssh_q "mkdir -p $(printf '%q' "$(dirname "$REMOTE_SOURCES_DB")")"
  # --copy-links: source may still be a symlink race; belt-and-braces since
  # LOCAL_SOURCES_DB is already resolve()d above.
  rsync -a --copy-links --partial "$LOCAL_SOURCES_DB" "$HOST:$REMOTE_SOURCES_DB"
  remote_sz="$(ssh_q "stat -L -c '%s' $(printf '%q' "$REMOTE_SOURCES_DB")")"
  echo "sources.db after rsync local=$local_sz remote=$remote_sz"
  if [[ "$local_sz" != "$remote_sz" ]]; then
    echo "FAIL CLOSED: sources.db still mismatched after rsync (local=$local_sz remote=$remote_sz)" >&2
    exit 1
  fi
fi
echo "sources.db OK (sizes match)"

if [[ "$do_sync_and_launch" == "1" ]]; then
  if [[ ! -f "$LOCAL_RESIDUAL" ]]; then
    echo "local residual dump not found: $LOCAL_RESIDUAL" >&2
    exit 1
  fi
  if ! grep -q -- '--slugs-file' "$LOCAL_DRIVER"; then
    echo "local driver at $LOCAL_DRIVER lacks --slugs-file support; this worktree is out of date" >&2
    exit 1
  fi

  echo "syncing residual + driver + launcher -> $HOST:$REMOTE_WORK_DIR"
  ssh_q "mkdir -p $(printf '%q' "$REMOTE_WORK_DIR")"
  scp_q "$LOCAL_RESIDUAL" "$HOST:$REMOTE_WORK_DIR/class-b-no-en.json"
  scp_q "$LOCAL_DRIVER" "$HOST:$REMOTE_WORK_DIR/reenrich_thin_manifest_entries.py"
  scp_q "$LOCAL_LAUNCHER" "$HOST:$REMOTE_WORK_DIR/launch_reenrich_class_b.sh"
  ssh_q "chmod +x $(printf '%q' "$REMOTE_WORK_DIR/launch_reenrich_class_b.sh")"

  echo "launching on $HOST"
  # ATLAS_RE_ENRICH_DRIVER pins the work-dir copy explicitly so a stale
  # in-repo checkout on the VPS can never win the launcher's auto-detection.
  remote_cmd="ATLAS_RUN_ROOT=$(printf '%q' "$RUN_ROOT") ATLAS_REPO=$(printf '%q' "$REMOTE_REPO") ATLAS_RE_ENRICH_WORK_DIR=$(printf '%q' "$REMOTE_WORK_DIR") ATLAS_RE_ENRICH_DRIVER=$(printf '%q' "$REMOTE_WORK_DIR/reenrich_thin_manifest_entries.py") bash $(printf '%q' "$REMOTE_WORK_DIR/launch_reenrich_class_b.sh")"
  # macOS ships bash 3.2, where "${arr[@]}" on a zero-element array throws
  # "unbound variable" under `set -u` (fixed upstream in bash 4.4+) — guard
  # the iteration instead of relying on the expansion alone.
  if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
    for extra in "${EXTRA_ARGS[@]}"; do
      remote_cmd+=" $(printf '%q' "$extra")"
    done
  fi
  ssh_q "$remote_cmd"
fi

if [[ "$do_poll" == "1" ]]; then
  echo "polling (timeout=${POLL_TIMEOUT_S}s interval=${POLL_INTERVAL_S}s)"
  elapsed=0
  while (( elapsed < POLL_TIMEOUT_S )); do
    if ! ssh_q "test -f $(printf '%q' "$REMOTE_WORK_DIR/reenrich-driver.pid") && kill -0 \"\$(cat $(printf '%q' "$REMOTE_WORK_DIR/reenrich-driver.pid"))\" 2>/dev/null"; then
      echo "job no longer running (elapsed=${elapsed}s)"
      break
    fi
    sleep "$POLL_INTERVAL_S"
    elapsed=$(( elapsed + POLL_INTERVAL_S ))
  done
  echo "--- log tail ---"
  ssh_q "tail -n 60 $(printf '%q' "$REMOTE_WORK_DIR/reenrich.log") 2>/dev/null" || true
fi

echo "pulling artifacts -> $LOCAL_OUT_DIR"
mkdir -p "$LOCAL_OUT_DIR"
scp_q "$HOST:$REMOTE_WORK_DIR/manifest.json" "$LOCAL_OUT_DIR/manifest.json" 2>/dev/null || echo "  (no manifest.json yet)"
scp_q "$HOST:$REMOTE_WORK_DIR/reenrich.log" "$LOCAL_OUT_DIR/reenrich.log" 2>/dev/null || echo "  (no reenrich.log yet)"
scp_q "$HOST:$REMOTE_WORK_DIR/reenrich-summary.json" "$LOCAL_OUT_DIR/reenrich-summary.json" 2>/dev/null || echo "  (no reenrich-summary.json yet)"

if [[ -f "$LOCAL_OUT_DIR/reenrich-summary.json" ]]; then
  echo "--- summary ---"
  python3 -c "
import json, sys
try:
    data = json.load(open('$LOCAL_OUT_DIR/reenrich-summary.json'))
except Exception as exc:
    print(f'  (could not parse summary: {exc})', file=sys.stderr)
    sys.exit(0)
for key in ('target', 'targets', 'changed', 'filled_translation', 'gained_english_anchor', 'remaining_old_gate_no_english_anchor'):
    if key in data:
        print(f'  {key}: {data[key]}')
"
fi

echo "done. Merge $LOCAL_OUT_DIR/manifest.json into the publish gate on this worktree before opening a PR."
