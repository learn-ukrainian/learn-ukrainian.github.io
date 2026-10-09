#!/bin/sh
# AGY PreInvocation hook: re-inject the pinned driver state before every model
# call (see scripts/driver_state.py). AGY runs hooks from the directory that
# holds hooks.json (.agents/), so resolve the checkout from this script.
# Fail-open: always print a JSON object and exit 0.
root=$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd) || { echo '{}'; exit 0; }
if [ -z "${LU_DRIVER_STATE_FILE:-}" ]; then
  cat >/dev/null 2>&1
  echo '{}'
  exit 0
fi
py="${LU_DRIVER_STATE_PYTHON:-$root/.venv/bin/python}"
if [ ! -x "$py" ]; then
  cat >/dev/null 2>&1
  echo '{}'
  exit 0
fi
cd "$root" && exec "$py" -m scripts.driver_state agy-hook
