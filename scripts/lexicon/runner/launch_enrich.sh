#!/usr/bin/env bash
# Detached, idempotent launcher for #5230 offline enrich (reduce candidate → enriched).
# Mirrors launch_reduce.sh under MemoryHigh=1.5G MemoryMax=2.0G.
#
# Prerequisites (on VPS run-20k):
#   - network-cache.sqlite populated (fetch done)
#   - candidate-ulif-reduce.json present (reduce complete)
#   - data/sources.db + data/lexicon/kaikki_uk_lookup.json available in $REPO
#
# Does NOT finalize, publish, or pin-flip. After enrich completes, operators
# run finalize.py separately under the #5138 / #5331 publish gate.
#
# Usage:
#   scripts/lexicon/runner/launch_enrich.sh
#   scripts/lexicon/runner/launch_enrich.sh --stop-after-chunks 2   # smoke
#   scripts/lexicon/runner/launch_enrich.sh --force-new-run
#
# Env overrides:
#   ATLAS_RUN_ROOT, ATLAS_REPO, ATLAS_WORK_DIR, ATLAS_ENRICH_UNIT,
#   ATLAS_ENRICH_DRIVER, ATLAS_CANDIDATE, ATLAS_SOURCES_DB, ATLAS_KAIKKI_JSON
set -euo pipefail

RUN_ROOT="${ATLAS_RUN_ROOT:-/home/ops/atlas-runner}"
REPO="${ATLAS_REPO:-$RUN_ROOT/repo}"
WORK_DIR="${ATLAS_WORK_DIR:-$RUN_ROOT/run-20k}"
UNIT="${ATLAS_ENRICH_UNIT:-atlas-20k-enrich.service}"
LOG="$WORK_DIR/enrich.log"
PID_FILE="$WORK_DIR/enrich-driver.pid"
WRAPPER_PID_FILE="$WORK_DIR/enrich-systemd-run.pid"
DRIVER="${ATLAS_ENRICH_DRIVER:-$REPO/scripts/lexicon/runner/enrich_offline_20k.py}"
CANDIDATE="${ATLAS_CANDIDATE:-$WORK_DIR/candidate-ulif-reduce.json}"
SOURCES_DB="${ATLAS_SOURCES_DB:-$REPO/data/sources.db}"
KAIKKI_JSON="${ATLAS_KAIKKI_JSON:-$REPO/data/lexicon/kaikki_uk_lookup.json}"
ENRICH_WORK="${ATLAS_ENRICH_WORK_DIR:-$WORK_DIR/offline_enrich}"

mkdir -p "$WORK_DIR" "$ENRICH_WORK"
cd "$REPO"

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  printf 'pid=%s log=%s\n' "$(cat "$PID_FILE")" "$LOG"
  exit 0
fi

# Prefer in-repo driver; fall back to work-dir copy if repo checkout is stale.
if [[ ! -f "$DRIVER" ]]; then
  DRIVER="$WORK_DIR/enrich_offline_20k.py"
fi
if [[ ! -f "$DRIVER" ]]; then
  echo "enrich driver not found: $DRIVER" >&2
  exit 1
fi
if [[ ! -f "$CANDIDATE" ]]; then
  echo "reduce candidate not found: $CANDIDATE (run reduce first)" >&2
  exit 1
fi
if [[ ! -f "$SOURCES_DB" ]]; then
  echo "sources.db not found: $SOURCES_DB" >&2
  exit 1
fi
if [[ ! -f "$KAIKKI_JSON" ]]; then
  echo "kaikki lookup not found: $KAIKKI_JSON" >&2
  exit 1
fi

EXTRA_ARGS=("$@")

COMMON_ARGS=(
  --repo "$REPO"
  --work-dir "$ENRICH_WORK"
  --candidate "$CANDIDATE"
  --sources-db "$SOURCES_DB"
  --kaikki-json "$KAIKKI_JSON"
  --output "$ENRICH_WORK/candidate-enriched.json"
  --chunk-size 25
  --require-memory-cap
)

if systemctl --user is-system-running >/dev/null 2>&1 && command -v systemd-run >/dev/null 2>&1; then
  rm -f "$PID_FILE" "$WRAPPER_PID_FILE"
  nohup systemd-run --user --wait --collect --unit="${UNIT%.service}" \
    --working-directory="$REPO" \
    --property=MemoryHigh=1536M \
    --property=MemoryMax=2048M \
    --property=StandardOutput="append:$LOG" \
    --property=StandardError="append:$LOG" \
    /usr/bin/nice -n 10 /usr/bin/ionice -c3 "$REPO/.venv/bin/python" \
    "$DRIVER" \
    "${COMMON_ARGS[@]}" \
    "${EXTRA_ARGS[@]}" >> "$LOG" 2>&1 &
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
nohup /usr/bin/nice -n 10 /usr/bin/ionice -c3 "$REPO/.venv/bin/python" \
  "$DRIVER" \
  "${COMMON_ARGS[@]}" \
  "${EXTRA_ARGS[@]}" >> "$LOG" 2>&1 &
printf '%s\n' "$!" > "$PID_FILE"
printf 'pid=%s log=%s\n' "$(cat "$PID_FILE")" "$LOG"
