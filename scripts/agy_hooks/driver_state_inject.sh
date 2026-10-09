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
# Drain the hook input before any child can fail without reading it. Preserve
# trailing newlines with a sentinel removed after command substitution.
payload=$(cat; printf '.')
payload=${payload%.}
root=$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd) || { echo "$fallback"; exit 0; }
if [ -z "${LU_DRIVER_STATE_FILE:-}" ]; then
  echo "$fallback"
  exit 0
fi
py="${LU_DRIVER_STATE_PYTHON:-$root/.venv/bin/python}"
if [ ! -x "$py" ]; then
  echo "$fallback"
  exit 0
fi
# Validate the original bytes: shell variables would silently remove NULs.
output_file=$(mktemp) || { echo "$fallback"; exit 0; }
trap 'rm -f "$output_file"' 0
if (cd "$root" && printf '%s' "$payload" | "$py" -m scripts.driver_state "$mode" >"$output_file" 2>/dev/null); then
  # A successful child must produce exactly one strict JSON object. Keep the
  # validator's output private too: a broken interpreter is not validation.
  if validation=$("$py" -c '
import json
import sys

def reject_constant(value):
    raise ValueError("Invalid JSON constant")

value = json.load(sys.stdin, parse_constant=reject_constant)
if not isinstance(value, dict):
    sys.exit(1)
print("valid")
' <"$output_file" 2>/dev/null) && [ "$validation" = valid ]; then
    cat "$output_file"
    exit 0
  fi
fi
printf '%s\n' "$fallback"
exit 0
