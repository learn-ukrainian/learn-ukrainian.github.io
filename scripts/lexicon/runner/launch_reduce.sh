#!/usr/bin/env bash
# Detached, idempotent launcher for #5230 offline reduce (ULIF cache → candidate).
# Mirrors run-20k/launch.sh resume pattern under MemoryHigh=1.5G MemoryMax=2.0G.
set -euo pipefail

if [[ -z "${ATLAS_RUN_ROOT:-}" ]]; then
  echo "ATLAS_RUN_ROOT is required" >&2
  exit 2
fi
RUN_ROOT="$ATLAS_RUN_ROOT"

# Job memory caps (MiB): generic defaults (contracts.GENERIC_JOB_MEMORY_*);
# a deployment sets LU_LEXICON_JOB_MEMORY_HIGH_MIB / LU_LEXICON_JOB_MEMORY_MAX_MIB.
# Strip surrounding ASCII whitespace; unset or blank uses the default, like
# contracts.env_mib(). Refuse non-positive values before any launch.
_trim_mib() {
  local s="$1"
  local ws=$' \t\n\r\v\f'
  s="${s#"${s%%[!$ws]*}"}"
  s="${s%"${s##*[!$ws]}"}"
  printf '%s' "$s"
}
_require_positive_mib() {
  local name="$1" value="$2"
  if [[ ! "$value" =~ ^[0-9]{1,18}$ ]] || (( 10#$value == 0 )); then
    printf '%s must be a positive whole number of MiB, got %q\n' "$name" "$value" >&2
    exit 2
  fi
}
JOB_MEMORY_HIGH_MIB="$(_trim_mib "${LU_LEXICON_JOB_MEMORY_HIGH_MIB-}")"
[[ -n "$JOB_MEMORY_HIGH_MIB" ]] || JOB_MEMORY_HIGH_MIB=1280
JOB_MEMORY_MAX_MIB="$(_trim_mib "${LU_LEXICON_JOB_MEMORY_MAX_MIB-}")"
[[ -n "$JOB_MEMORY_MAX_MIB" ]] || JOB_MEMORY_MAX_MIB=1792
_require_positive_mib LU_LEXICON_JOB_MEMORY_HIGH_MIB "$JOB_MEMORY_HIGH_MIB"
_require_positive_mib LU_LEXICON_JOB_MEMORY_MAX_MIB "$JOB_MEMORY_MAX_MIB"
JOB_MEMORY_HIGH_MIB="$((10#$JOB_MEMORY_HIGH_MIB))"
JOB_MEMORY_MAX_MIB="$((10#$JOB_MEMORY_MAX_MIB))"
# Children started without the service manager inherit the resolved values.
export LU_LEXICON_JOB_MEMORY_HIGH_MIB="$JOB_MEMORY_HIGH_MIB" LU_LEXICON_JOB_MEMORY_MAX_MIB="$JOB_MEMORY_MAX_MIB"
# The caps come only from this configuration, so the unit and the runner
# always agree; refuse caller-supplied memory flags (including abbreviations).
for _arg in "$@"; do
  _opt="${_arg%%=*}"
  if [[ ${#_opt} -ge 3 && ( "--memory-high-mib" == "$_opt"* || "--memory-max-mib" == "$_opt"* ) ]]; then
    printf '%s is not accepted; set LU_LEXICON_JOB_MEMORY_HIGH_MIB / LU_LEXICON_JOB_MEMORY_MAX_MIB instead\n' "$_arg" >&2
    exit 2
  fi
done

REPO="${ATLAS_REPO:-$RUN_ROOT/repo}"
WORK_DIR="${ATLAS_WORK_DIR:-$RUN_ROOT/run-20k}"
UNIT="${ATLAS_REDUCE_UNIT:-atlas-20k-reduce.service}"
LOG="$WORK_DIR/reduce.log"
PID_FILE="$WORK_DIR/reduce-driver.pid"
WRAPPER_PID_FILE="$WORK_DIR/reduce-systemd-run.pid"
DRIVER="${ATLAS_REDUCE_DRIVER:-$REPO/scripts/lexicon/runner/reduce_ulif_20k.py}"

mkdir -p "$WORK_DIR"
cd "$REPO"

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  printf 'pid=%s log=%s\n' "$(cat "$PID_FILE")" "$LOG"
  exit 0
fi

# Prefer in-repo driver; fall back to work-dir copy if repo checkout is stale.
if [[ ! -f "$DRIVER" ]]; then
  DRIVER="$WORK_DIR/reduce_ulif_20k.py"
fi
if [[ ! -f "$DRIVER" ]]; then
  echo "reduce driver not found: $DRIVER" >&2
  exit 1
fi

EXTRA_ARGS=("$@")

if systemctl --user is-system-running >/dev/null 2>&1 && command -v systemd-run >/dev/null 2>&1; then
  rm -f "$PID_FILE" "$WRAPPER_PID_FILE"
  nohup systemd-run --user --wait --collect --unit="${UNIT%.service}" \
    --working-directory="$REPO" \
    --property=MemoryHigh="${JOB_MEMORY_HIGH_MIB}M" \
    --property=MemoryMax="${JOB_MEMORY_MAX_MIB}M" \
    --property=Environment=LU_LEXICON_JOB_MEMORY_HIGH_MIB="${JOB_MEMORY_HIGH_MIB}" \
    --property=Environment=LU_LEXICON_JOB_MEMORY_MAX_MIB="${JOB_MEMORY_MAX_MIB}" \
    --property=StandardOutput="append:$LOG" \
    --property=StandardError="append:$LOG" \
    /usr/bin/nice -n 10 /usr/bin/ionice -c3 "$REPO/.venv/bin/python" \
    "$DRIVER" \
    --repo "$REPO" \
    --work-dir "$WORK_DIR" \
    --network-cache "$WORK_DIR/network-cache.sqlite" \
    --cohort "$REPO/registry/lexicon/cohort-20k-20260717.txt" \
    --require-memory-cap \
    --memory-high-mib "$JOB_MEMORY_HIGH_MIB" \
    --memory-max-mib "$JOB_MEMORY_MAX_MIB" \
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
  --repo "$REPO" \
  --work-dir "$WORK_DIR" \
  --network-cache "$WORK_DIR/network-cache.sqlite" \
  --cohort "$REPO/registry/lexicon/cohort-20k-20260717.txt" \
  --require-memory-cap \
  --memory-high-mib "$JOB_MEMORY_HIGH_MIB" \
  --memory-max-mib "$JOB_MEMORY_MAX_MIB" \
  "${EXTRA_ARGS[@]}" >> "$LOG" 2>&1 &
printf '%s\n' "$!" > "$PID_FILE"
printf 'pid=%s log=%s\n' "$(cat "$PID_FILE")" "$LOG"
