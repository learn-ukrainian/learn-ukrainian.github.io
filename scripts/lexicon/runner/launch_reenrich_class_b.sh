#!/usr/bin/env bash
# Detached, idempotent launcher for #6369 Class-B residual EN re-enrich.
# Mirrors launch_enrich.sh under MemoryHigh=1.5G MemoryMax=2.0G.
#
# Runs entirely against the atlas-runner *work-dir* — it never mutates the
# VPS repo checkout at $REPO. This matters because the checkout there is
# routinely stale/dirty (large data/ dirs deliberately deleted for disk
# headroom); this launcher only ever reads from it (sources.db, kaikki
# lookup, the live hydrated manifest) and writes into $ATLAS_RE_ENRICH_WORK_DIR.
#
# Prerequisites (in the work-dir, deployed by
# launch_reenrich_class_b_remote.sh from the Mac side):
#   - class-b-no-en.json   residual slug allowlist (#6369 class_b_detail dump)
#   - reenrich_thin_manifest_entries.py   driver copy with --slugs-file
#     support, IF the in-repo checkout at $REPO is still stale (no
#     --slugs-file flag). The in-repo driver is preferred once it catches up.
#
# Does NOT finalize, publish, or pin-flip. This mutates a *work-dir copy* of
# the manifest only (snapshotted once from the live checkout, then re-used
# across resumes) — never the live $REPO/site/src/data/lexicon-manifest.json.
# Pulling the result back for the PR / publish gate is
# launch_reenrich_class_b_remote.sh's job, run from the Mac-side worktree.
#
# Usage (on the VPS):
#   scripts/lexicon/runner/launch_reenrich_class_b.sh
#   scripts/lexicon/runner/launch_reenrich_class_b.sh --limit 5   # smoke
#
# Env overrides:
#   ATLAS_RUN_ROOT, ATLAS_REPO, ATLAS_RE_ENRICH_WORK_DIR,
#   ATLAS_RE_ENRICH_UNIT, ATLAS_RE_ENRICH_DRIVER, ATLAS_RE_ENRICH_SLUGS_FILE,
#   ATLAS_SOURCES_DB, ATLAS_KAIKKI_JSON, ATLAS_LIVE_MANIFEST
set -euo pipefail

RUN_ROOT="${ATLAS_RUN_ROOT:-/home/ops/atlas-runner}"
REPO="${ATLAS_REPO:-$RUN_ROOT/repo}"
WORK_DIR="${ATLAS_RE_ENRICH_WORK_DIR:-$RUN_ROOT/run-class-b-reenrich}"
UNIT="${ATLAS_RE_ENRICH_UNIT:-atlas-class-b-reenrich.service}"
LOG="$WORK_DIR/reenrich.log"
PID_FILE="$WORK_DIR/reenrich-driver.pid"
WRAPPER_PID_FILE="$WORK_DIR/reenrich-systemd-run.pid"
SUMMARY_FILE="$WORK_DIR/reenrich-summary.json"

SLUGS_FILE="${ATLAS_RE_ENRICH_SLUGS_FILE:-$WORK_DIR/class-b-no-en.json}"
SOURCES_DB="${ATLAS_SOURCES_DB:-$REPO/data/sources.db}"
KAIKKI_JSON="${ATLAS_KAIKKI_JSON:-$REPO/data/lexicon/kaikki_uk_lookup.json}"
LIVE_MANIFEST="${ATLAS_LIVE_MANIFEST:-$REPO/site/src/data/lexicon-manifest.json}"
WORK_MANIFEST="$WORK_DIR/manifest.json"

IN_REPO_DRIVER="$REPO/scripts/lexicon/reenrich_thin_manifest_entries.py"
WORKDIR_DRIVER="$WORK_DIR/reenrich_thin_manifest_entries.py"

EXTRA_ARGS=("$@")

# Effective target: default missing-translation (this launcher's original,
# residual-slug-scoped behavior), but a caller-supplied --target in
# EXTRA_ARGS (e.g. #6466 full-catalog campaigns) overrides it. Mirrors
# argparse's own last-value-wins semantics for a repeated flag.
TARGET="missing-translation"
for ((_i = 0; _i < ${#EXTRA_ARGS[@]}; _i++)); do
  if [[ "${EXTRA_ARGS[_i]}" == "--target" && $((_i + 1)) -lt ${#EXTRA_ARGS[@]} ]]; then
    TARGET="${EXTRA_ARGS[_i + 1]}"
  elif [[ "${EXTRA_ARGS[_i]}" == --target=* ]]; then
    TARGET="${EXTRA_ARGS[_i]#--target=}"
  fi
done

# Test/debug hook: print the resolved target and exit before any
# filesystem/systemd side effect (tests/test_launch_reenrich_target_detection.py).
for arg in "${EXTRA_ARGS[@]-}"; do
  if [[ "$arg" == "--print-target" ]]; then
    printf '%s\n' "$TARGET"
    exit 0
  fi
done

mkdir -p "$WORK_DIR"
cd "$REPO"

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  printf 'pid=%s log=%s\n' "$(cat "$PID_FILE")" "$LOG"
  exit 0
fi

# Prefer the in-repo driver once it has caught up (post-#6398 merge); fall
# back to the work-dir copy scp'd over by the Mac-side orchestrator.
DRIVER="${ATLAS_RE_ENRICH_DRIVER:-}"
if [[ -z "$DRIVER" ]]; then
  if [[ -f "$IN_REPO_DRIVER" ]] && grep -q -- '--slugs-file' "$IN_REPO_DRIVER" 2>/dev/null; then
    DRIVER="$IN_REPO_DRIVER"
  elif [[ -f "$WORKDIR_DRIVER" ]]; then
    DRIVER="$WORKDIR_DRIVER"
  else
    DRIVER="$IN_REPO_DRIVER"
  fi
fi

if [[ ! -f "$DRIVER" ]]; then
  echo "reenrich driver not found: $DRIVER" >&2
  exit 1
fi
if ! grep -q -- '--slugs-file' "$DRIVER" 2>/dev/null; then
  echo "reenrich driver at $DRIVER lacks --slugs-file support; scp the #6398 driver into $WORKDIR_DRIVER or update the checkout" >&2
  exit 1
fi
# --slugs-file (and its residual-dump prerequisite) only applies to the
# missing-translation target — see the guarded COMMON_ARGS block below for
# why stacking it onto full-catalog would be wrong, not just redundant.
if [[ "$TARGET" == "missing-translation" && ! -f "$SLUGS_FILE" ]]; then
  echo "residual slugs file not found: $SLUGS_FILE (sync it from the Mac worktree first)" >&2
  exit 1
fi
if [[ ! -f "$SOURCES_DB" ]]; then
  echo "sources.db not found: $SOURCES_DB" >&2
  exit 1
fi
if [[ ! -f "$REPO/.venv/bin/python" ]]; then
  echo "repo venv python not found: $REPO/.venv/bin/python" >&2
  exit 1
fi

# Snapshot the live hydrated manifest into the work-dir exactly once. Resumes
# reuse this same copy so a prior run's fills are not thrown away — the
# missing-translation target predicate already skips entries that got filled,
# so a resumed run only touches what's still outstanding.
if [[ ! -f "$WORK_MANIFEST" ]]; then
  if [[ ! -f "$LIVE_MANIFEST" ]]; then
    echo "live manifest not found: $LIVE_MANIFEST (nothing to snapshot)" >&2
    exit 1
  fi
  cp "$LIVE_MANIFEST" "$WORK_MANIFEST"
fi

COMMON_ARGS=(
  --manifest "$WORK_MANIFEST"
  --local
  --target "$TARGET"
  --sources-db "$SOURCES_DB"
  --write
)
# --slugs-file restricts re-enrichment to a residual slug allowlist (see
# reenrich_thin_manifest_entries.py::reenrich_thin_entries). That's correct
# for missing-translation (this launcher's original purpose) but WRONG for
# full-catalog: full-catalog already selects every manifest entry, and
# stacking a stale --slugs-file on top would silently narrow it back down to
# whatever residual set happened to be synced to $SLUGS_FILE, defeating the
# whole point of a full-catalog run while still exiting 0 and looking done.
# (Existence of $SLUGS_FILE for this target was already validated above.)
if [[ "$TARGET" == "missing-translation" ]]; then
  COMMON_ARGS+=(--slugs-file "$SLUGS_FILE")
fi
if [[ -f "$KAIKKI_JSON" ]]; then
  COMMON_ARGS+=(--kaikki-lookup "$KAIKKI_JSON")
fi

# Wrap in bash -c so we can tee stdout (the driver's one JSON summary print)
# into its own artifact without fighting systemd-run's StandardOutput
# property. stderr still folds into the shared log.
#
# PYTHONPATH=$REPO is required when DRIVER is the work-dir copy: that file's
# own `sys.path` bootstrap assumes it lives 2 levels under the real repo
# root (scripts/lexicon/<file>.py -> parents[2] == repo root) to import its
# sibling `scripts.audit.*` / `scripts.lexicon.*` packages. A flat work-dir
# copy breaks that assumption; PYTHONPATH makes the real package tree
# resolvable regardless of where the file itself was invoked from.
# systemd-run --user starts units with a fresh environment (it does not
# inherit the launching shell's exports), so this must be set inside the
# wrapped command, not via `export` before systemd-run.
run_cmd() {
  printf '%q ' "$REPO/.venv/bin/python" "$DRIVER" "${COMMON_ARGS[@]}"
  # Bash <4.4 (e.g. macOS's stock /bin/bash 3.2) throws "unbound variable"
  # on "${arr[@]}" for a zero-element array under `set -u` — guard rather
  # than rely on the expansion, in case this script is ever invoked there.
  if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
    printf '%q ' "${EXTRA_ARGS[@]}"
  fi
}
WRAPPED="cd $(printf '%q' "$REPO") && PYTHONPATH=$(printf '%q' "$REPO") exec /usr/bin/nice -n 10 /usr/bin/ionice -c3 $(run_cmd) 2>>$(printf '%q' "$LOG") | tee -a $(printf '%q' "$LOG") > $(printf '%q' "$SUMMARY_FILE")"

if systemctl --user is-system-running >/dev/null 2>&1 && command -v systemd-run >/dev/null 2>&1; then
  rm -f "$PID_FILE" "$WRAPPER_PID_FILE"
  nohup systemd-run --user --wait --collect --unit="${UNIT%.service}" \
    --working-directory="$REPO" \
    --property=MemoryHigh=1536M \
    --property=MemoryMax=2048M \
    /bin/bash -c "$WRAPPED" >> "$LOG" 2>&1 &
  wrapper_pid=$!
  printf '%s\n' "$wrapper_pid" > "$WRAPPER_PID_FILE"
  for _ in $(seq 1 50); do
    driver_pid=$(systemctl --user show "$UNIT" --property=MainPID --value 2>/dev/null || true)
    if [[ "$driver_pid" =~ ^[1-9][0-9]*$ ]]; then
      printf '%s\n' "$driver_pid" > "$PID_FILE"
      printf 'pid=%s wrapper_pid=%s unit=%s log=%s\n' "$driver_pid" "$wrapper_pid" "$UNIT" "$LOG"
      exit 0
    fi
    if ! kill -0 "$wrapper_pid" 2>/dev/null; then
      tail -n 80 "$LOG" || true
      exit 1
    fi
    sleep 0.1
  done
  tail -n 80 "$LOG" || true
  exit 1
fi

rm -f "$PID_FILE" "$WRAPPER_PID_FILE"
nohup /bin/bash -c "$WRAPPED" >> "$LOG" 2>&1 &
printf '%s\n' "$!" > "$PID_FILE"
printf 'pid=%s log=%s\n' "$(cat "$PID_FILE")" "$LOG"
