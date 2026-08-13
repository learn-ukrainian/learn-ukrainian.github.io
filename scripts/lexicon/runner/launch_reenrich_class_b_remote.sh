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
# Steps: sync (live manifest + residual slugs + driver + launcher) -> launch
# (detached, idempotent, memory-capped) -> optional poll -> pull manifest + log +
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
#   ATLAS_PRIMARY_ROOT (default: primary checkout from shared .git common dir),
#   ATLAS_RE_ENRICH_WORK_DIR, ATLAS_RE_ENRICH_RESIDUAL (local slugs dump),
#   ATLAS_LOCAL_VESUM_DB, ATLAS_LOCAL_SLOVNYK_CACHE
#   (local enrichment data for the work-dir overlay),
#   ATLAS_RE_ENRICH_PYTHON (default shared project interpreter),
#   ATLAS_RE_ENRICH_OUT_DIR (local pull-back dir),
#   ATLAS_RE_ENRICH_POLL_TIMEOUT_S (default 900),
#   ATLAS_RE_ENRICH_POLL_INTERVAL_S (default 15)
set -euo pipefail

WORKTREE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

# Primary checkout root (shared .git common dir), portable across operators
# instead of a hardcoded /Users/... path (#6571). In a worktree,
# `git rev-parse --git-common-dir` returns <primary>/.git; its parent is the
# primary checkout root. Explicit override wins (fixtures / other hosts).
_primary_common_dir="$(git -C "$WORKTREE" rev-parse --git-common-dir 2>/dev/null || true)"
if [[ -z "$_primary_common_dir" ]]; then
  echo "cannot resolve primary checkout root (git rev-parse --git-common-dir failed)" >&2
  exit 1
fi
# git rev-parse may emit a path relative to $WORKTREE; make it absolute.
case "$_primary_common_dir" in
  /*) : ;;
  *)  _primary_common_dir="$WORKTREE/$_primary_common_dir" ;;
esac
PRIMARY_ROOT="${ATLAS_PRIMARY_ROOT:-$(cd "$_primary_common_dir/.." && pwd)}"
PYTHON_BIN="${ATLAS_RE_ENRICH_PYTHON:-$PRIMARY_ROOT/.venv/bin/python}"

HOST="${ATLAS_RUNNER_HOST:-vps}"
RUN_ROOT="${ATLAS_RUN_ROOT:-/home/ops/atlas-runner}"
REMOTE_REPO="${ATLAS_REPO:-$RUN_ROOT/repo}"
REMOTE_WORK_DIR="${ATLAS_RE_ENRICH_WORK_DIR:-$RUN_ROOT/run-class-b-reenrich}"

LOCAL_RESIDUAL="${ATLAS_RE_ENRICH_RESIDUAL:-$WORKTREE/batch_state/atlas-6369-class-b-no-en.json}"
LOCAL_OUT_DIR="${ATLAS_RE_ENRICH_OUT_DIR:-$WORKTREE/batch_state/class-b-reenrich-pulled}"
LOCAL_DRIVER="$WORKTREE/scripts/lexicon/reenrich_thin_manifest_entries.py"
LOCAL_LAUNCHER="$WORKTREE/scripts/lexicon/runner/launch_reenrich_class_b.sh"
# Full-catalog runs must begin from the Mac's live catalog, not the stale
# manifest retained in the VPS checkout. Prefer the dispatched worktree when
# it contains the large catalog; sparse worktrees normally fall back to the
# operator's primary checkout.
LOCAL_LIVE_MANIFEST_CANDIDATE="$WORKTREE/site/src/data/lexicon-manifest.json"
PRIMARY_LIVE_MANIFEST="$PRIMARY_ROOT/site/src/data/lexicon-manifest.json"
MIN_LIVE_MANIFEST_BYTES=1048576
# The driver imports ``scripts.lexicon.enrich_manifest`` and its supporting
# modules. The VPS checkout is deliberately allowed to stay stale, so deploy
# the current scripts package tree into the work-dir instead of trying to
# maintain a brittle transitive-import allowlist against $REMOTE_REPO.
LOCAL_SCRIPTS_PACKAGE="$WORKTREE/scripts"

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

# Effective target (see launch_reenrich_class_b.sh for the same detection):
# the class-b residual slug dump is only meaningful for missing-translation
# runs. A #6466 full-catalog run has no use for it, so don't require or sync
# a residual file that has nothing to do with the requested target.
TARGET="missing-translation"
for ((_i = 0; _i < ${#EXTRA_ARGS[@]}; _i++)); do
  if [[ "${EXTRA_ARGS[_i]}" == "--target" && $((_i + 1)) -lt ${#EXTRA_ARGS[@]} ]]; then
    TARGET="${EXTRA_ARGS[_i + 1]}"
  elif [[ "${EXTRA_ARGS[_i]}" == --target=* ]]; then
    TARGET="${EXTRA_ARGS[_i]#--target=}"
  fi
done

ssh_q() { ssh -o BatchMode=yes -o ConnectTimeout=10 -- "$HOST" "$@"; }
scp_q() { scp -o BatchMode=yes -o ConnectTimeout=10 -- "$@"; }
rsync_q() { rsync -a --delete -e "ssh -o BatchMode=yes -o ConnectTimeout=10" -- "$@"; }

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "shared project Python not executable: $PYTHON_BIN" >&2
  exit 1
fi

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
  if [[ -e "$PRIMARY_ROOT/data/sources.db" ]]; then
    LOCAL_SOURCES_DB_CANDIDATE="$PRIMARY_ROOT/data/sources.db"
  else
    echo "local sources.db not found (tried worktree + primary checkout)" >&2
    exit 1
  fi
fi
LOCAL_SOURCES_DB="$("$PYTHON_BIN" -c "import pathlib, sys; print(pathlib.Path(sys.argv[1]).resolve())" "$LOCAL_SOURCES_DB_CANDIDATE")"
if [[ ! -f "$LOCAL_SOURCES_DB" ]]; then
  echo "resolved local sources.db is not a regular file: $LOCAL_SOURCES_DB" >&2
  exit 1
fi

# Current enrichment also needs VESUM for morphology and to verify dictionary
# content before learner-facing sections are admitted. The VPS intentionally
# keeps only sources.db in its stale repo checkout, so materialize VESUM in the
# disposable work-dir overlay rather than changing that checkout.
LOCAL_VESUM_DB_CANDIDATE="${ATLAS_LOCAL_VESUM_DB:-$WORKTREE/data/vesum.db}"
if [[ ! -e "$LOCAL_VESUM_DB_CANDIDATE" ]]; then
  if [[ -e "$PRIMARY_ROOT/data/vesum.db" ]]; then
    LOCAL_VESUM_DB_CANDIDATE="$PRIMARY_ROOT/data/vesum.db"
  else
    echo "local vesum.db not found (tried worktree + primary checkout)" >&2
    exit 1
  fi
fi
LOCAL_VESUM_DB="$("$PYTHON_BIN" -c "import pathlib, sys; print(pathlib.Path(sys.argv[1]).resolve())" "$LOCAL_VESUM_DB_CANDIDATE")"
if [[ ! -f "$LOCAL_VESUM_DB" ]]; then
  echo "resolved local vesum.db is not a regular file: $LOCAL_VESUM_DB" >&2
  exit 1
fi
LOCAL_SLOVNYK_CACHE="${ATLAS_LOCAL_SLOVNYK_CACHE:-$WORKTREE/data/lexicon/slovnyk_cache}"
if [[ ! -d "$LOCAL_SLOVNYK_CACHE" ]]; then
  LOCAL_SLOVNYK_CACHE="$PRIMARY_ROOT/data/lexicon/slovnyk_cache"
fi
if [[ ! -d "$LOCAL_SLOVNYK_CACHE" ]]; then
  echo "local slovnyk cache not found (tried worktree + primary checkout)" >&2
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
  LOCAL_LIVE_MANIFEST=""
  if [[ -f "$LOCAL_LIVE_MANIFEST_CANDIDATE" ]] && (( $(_local_sz "$LOCAL_LIVE_MANIFEST_CANDIDATE") >= MIN_LIVE_MANIFEST_BYTES )); then
    LOCAL_LIVE_MANIFEST="$LOCAL_LIVE_MANIFEST_CANDIDATE"
  elif [[ -f "$PRIMARY_LIVE_MANIFEST" ]] && (( $(_local_sz "$PRIMARY_LIVE_MANIFEST") >= MIN_LIVE_MANIFEST_BYTES )); then
    LOCAL_LIVE_MANIFEST="$PRIMARY_LIVE_MANIFEST"
  else
    echo "live lexicon manifest not found or too small (tried worktree + primary checkout)" >&2
    exit 1
  fi

  if [[ "$TARGET" == "missing-translation" ]]; then
    if [[ ! -f "$LOCAL_RESIDUAL" ]]; then
      echo "local residual dump not found: $LOCAL_RESIDUAL" >&2
      exit 1
    fi
    if ! grep -q -- '--slugs-file' "$LOCAL_DRIVER"; then
      echo "local driver at $LOCAL_DRIVER lacks --slugs-file support; this worktree is out of date" >&2
      exit 1
    fi
  fi

  echo "syncing driver + current enrichment package -> $HOST:$REMOTE_WORK_DIR (target=$TARGET)"
  ssh_q "mkdir -p $(printf '%q' "$REMOTE_WORK_DIR/scripts")"
  # Always replace the work-dir input before launch. The VPS checkout's
  # catalog is deliberately allowed to be stale, but the local launcher uses
  # this work-dir path as its --manifest input for every target.
  local_manifest_sz="$(_local_sz "$LOCAL_LIVE_MANIFEST")"
  echo "syncing live manifest local=$local_manifest_sz path=$LOCAL_LIVE_MANIFEST -> $REMOTE_WORK_DIR/manifest.json"
  rsync -a --copy-links --partial "$LOCAL_LIVE_MANIFEST" "$HOST:$REMOTE_WORK_DIR/manifest.json"
  remote_manifest_sz="$(ssh_q "stat -L -c '%s' $(printf '%q' "$REMOTE_WORK_DIR/manifest.json")")"
  if [[ "$local_manifest_sz" != "$remote_manifest_sz" ]]; then
    echo "FAIL CLOSED: live manifest still mismatched after rsync (local=$local_manifest_sz remote=$remote_manifest_sz)" >&2
    exit 1
  fi
  echo "live manifest OK (sizes match)"
  # Modules deployed under $REMOTE_WORK_DIR derive their project root from
  # that directory. Materialize a work-dir-only data overlay: the live repo
  # remains read-only, while VESUM sits next to the synced code.
  ssh_q "if test -L $(printf '%q' "$REMOTE_WORK_DIR/data"); then data_target=\$(readlink -f $(printf '%q' "$REMOTE_WORK_DIR/data")); if test \"\$data_target\" != $(printf '%q' "$REMOTE_REPO/data"); then echo 'refusing to replace unexpected work-dir data symlink' >&2; exit 1; fi; rm $(printf '%q' "$REMOTE_WORK_DIR/data"); mkdir -p $(printf '%q' "$REMOTE_WORK_DIR/data"); ln -s $(printf '%q' "$REMOTE_REPO/data/sources.db") $(printf '%q' "$REMOTE_WORK_DIR/data/sources.db"); ln -s $(printf '%q' "$REMOTE_REPO/data/lexicon") $(printf '%q' "$REMOTE_WORK_DIR/data/lexicon"); elif test ! -d $(printf '%q' "$REMOTE_WORK_DIR/data"); then echo 'work-dir data path is not a directory' >&2; exit 1; fi"
  # Slovnyk is deliberately offline during VPS runs. Materialize only its
  # cache directory locally in the overlay, while all other lexicon artifacts
  # remain linked to the hydrated VPS repo data.
  ssh_q "if test -L $(printf '%q' "$REMOTE_WORK_DIR/data/lexicon"); then lexicon_target=\$(readlink -f $(printf '%q' "$REMOTE_WORK_DIR/data/lexicon")); if test \"\$lexicon_target\" != $(printf '%q' "$REMOTE_REPO/data/lexicon"); then echo 'refusing to replace unexpected work-dir lexicon symlink' >&2; exit 1; fi; rm $(printf '%q' "$REMOTE_WORK_DIR/data/lexicon"); mkdir -p $(printf '%q' "$REMOTE_WORK_DIR/data/lexicon"); for source_path in $(printf '%q' "$REMOTE_REPO/data/lexicon")/*; do name=\$(basename \"\$source_path\"); if test \"\$name\" != slovnyk_cache; then ln -s \"\$source_path\" $(printf '%q' "$REMOTE_WORK_DIR/data/lexicon")/\"\$name\"; fi; done; elif test ! -d $(printf '%q' "$REMOTE_WORK_DIR/data/lexicon"); then echo 'work-dir lexicon path is not a directory' >&2; exit 1; fi"
  echo "syncing Slovnyk cache into work-dir overlay"
  rsync_q "$LOCAL_SLOVNYK_CACHE/" "$HOST:$REMOTE_WORK_DIR/data/lexicon/slovnyk_cache/"
  REMOTE_VESUM_DB="$REMOTE_WORK_DIR/data/vesum.db"
  local_vesum_sz="$(_local_sz "$LOCAL_VESUM_DB")"
  remote_vesum_sz="$(ssh_q "if test -f $(printf '%q' "$REMOTE_VESUM_DB"); then stat -L -c '%s' $(printf '%q' "$REMOTE_VESUM_DB"); else echo 0; fi")"
  echo "vesum.db preflight local=$local_vesum_sz remote=$remote_vesum_sz path=$REMOTE_VESUM_DB"
  if [[ "$local_vesum_sz" != "$remote_vesum_sz" ]]; then
    echo "syncing vesum.db into work-dir overlay"
    rsync -a --partial "$LOCAL_VESUM_DB" "$HOST:$REMOTE_VESUM_DB"
    remote_vesum_sz="$(ssh_q "stat -L -c '%s' $(printf '%q' "$REMOTE_VESUM_DB")")"
    echo "vesum.db after rsync local=$local_vesum_sz remote=$remote_vesum_sz"
    if [[ "$local_vesum_sz" != "$remote_vesum_sz" ]]; then
      echo "FAIL CLOSED: vesum.db still mismatched after rsync (local=$local_vesum_sz remote=$remote_vesum_sz)" >&2
      exit 1
    fi
  fi
  if [[ "$TARGET" == "missing-translation" ]]; then
    scp_q "$LOCAL_RESIDUAL" "$HOST:$REMOTE_WORK_DIR/class-b-no-en.json"
  fi
  scp_q "$LOCAL_DRIVER" "$HOST:$REMOTE_WORK_DIR/reenrich_thin_manifest_entries.py"
  scp_q "$LOCAL_LAUNCHER" "$HOST:$REMOTE_WORK_DIR/launch_reenrich_class_b.sh"
  # Keep every direct and lazy transitive import current.  The package is
  # small enough to sync cheaply, and this avoids rerunning a new driver
  # against a mixture of Mac-current and VPS-stale helper modules.
  rsync_q "$LOCAL_SCRIPTS_PACKAGE/" "$HOST:$REMOTE_WORK_DIR/scripts/"
  ssh_q "chmod +x $(printf '%q' "$REMOTE_WORK_DIR/launch_reenrich_class_b.sh")"

  echo "launching on $HOST"
  # ATLAS_RE_ENRICH_DRIVER pins the work-dir copy explicitly so a stale
  # in-repo checkout on the VPS can never win the launcher's auto-detection.
  remote_cmd="ATLAS_RUN_ROOT=$(printf '%q' "$RUN_ROOT") ATLAS_REPO=$(printf '%q' "$REMOTE_REPO") ATLAS_RE_ENRICH_WORK_DIR=$(printf '%q' "$REMOTE_WORK_DIR") ATLAS_RE_ENRICH_CODE_ROOT=$(printf '%q' "$REMOTE_WORK_DIR") ATLAS_RE_ENRICH_DRIVER=$(printf '%q' "$REMOTE_WORK_DIR/reenrich_thin_manifest_entries.py") bash $(printf '%q' "$REMOTE_WORK_DIR/launch_reenrich_class_b.sh")"
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
  "$PYTHON_BIN" -c "
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
