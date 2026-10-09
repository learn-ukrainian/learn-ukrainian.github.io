#!/bin/sh
# AGY hook entry point for the pinned driver state (scripts/driver_state.py).
#   driver_state_inject.sh [agy-hook|agy-stop-hook|agy-pretool-hook]
# AGY runs hooks from the directory that holds hooks.json (.agents/), so
# resolve the checkout from this script. Fail-open: always print a JSON
# object and exit 0, so a broken hook never blocks the agent loop.
mode="${1:-agy-hook}"
case "$mode" in
  agy-hook|agy-stop-hook|agy-pretool-hook) ;;
  *) mode=agy-hook ;;
esac
fallback='{}'
[ "$mode" = agy-pretool-hook ] && fallback='{"decision": "ask"}'
root=$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd) || { echo "$fallback"; exit 0; }
if [ -z "${LU_DRIVER_STATE_FILE:-}" ]; then
  cat >/dev/null 2>&1
  echo "$fallback"
  exit 0
fi
py="${LU_DRIVER_STATE_PYTHON:-$root/.venv/bin/python}"
if [ ! -x "$py" ]; then
  cat >/dev/null 2>&1
  echo "$fallback"
  exit 0
fi
cd "$root" && exec "$py" -m scripts.driver_state "$mode"
