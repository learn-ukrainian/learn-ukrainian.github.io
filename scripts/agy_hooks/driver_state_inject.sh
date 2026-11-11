#!/usr/bin/env bash
# Harness hook entry point for the pinned driver state (scripts.driver_state).
#   driver_state_inject.sh [agy-hook|agy-stop-hook|agy-pretool-hook|claude-hook|claude-stop-hook]
# The product, shared-state anchor and interpreter come from the one hook rule,
# project_hook_context_resolve (lib/project_interpreter.sh), before any directory
# change or Python start; never from this script's location. Without that
# context the hook answers in its mode's native refusal shape: AGY Stop
# continues, other AGY entries deny, Claude Stop blocks and Claude
# SessionStart/UserPromptSubmit stops. With it, an ordinary session and a
# driver-hook failure keep the fail-open fallback: a JSON object and exit 0.
mode="${1:-agy-hook}"
case "$mode" in
  agy-hook|agy-stop-hook|agy-pretool-hook|claude-hook|claude-stop-hook) ;;
  *) mode=agy-hook ;;
esac
case "$mode" in
  agy-stop-hook|agy-pretool-hook) fallback='{"decision": "allow"}' ;;
  *) fallback='{}' ;;
esac
case "$mode" in
  agy-stop-hook) refusal='{"decision":"continue","reason":"HOOK-BOOTSTRAP-FAILED: hook context unavailable."}' ;;
  agy-*) refusal='{"decision":"deny","reason":"HOOK-BOOTSTRAP-FAILED: hook context unavailable."}' ;;
  claude-stop-hook) refusal='{"decision":"block","reason":"HOOK-BOOTSTRAP-FAILED: hook context unavailable."}' ;;
  *) refusal='{"continue":false,"stopReason":"HOOK-BOOTSTRAP-FAILED: hook context unavailable."}' ;;
esac
bootstrap_failed() {
  cat >/dev/null 2>&1
  printf '%s\n' 'HOOK-BOOTSTRAP-FAILED: product root, shared state, interpreter or machinery unavailable.' >&2
  printf '%s\n' "$refusal"
  exit 0
}
code=$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd) || bootstrap_failed
# shellcheck disable=SC1091
source "$code/scripts/lib/project_interpreter.sh" || bootstrap_failed
project_hook_context_resolve 2>/dev/null || bootstrap_failed
py="$LEARN_UKRAINIAN_PYTHON"
# Drain the hook input before any child can fail without reading it. Keep the
# original bytes in a file because shell variables cannot preserve NULs.
input_file=$(mktemp --tmpdir="$TMPDIR" agy-in.XXXXXX) || { cat >/dev/null; echo "$fallback"; exit 0; }
output_file=
trap 'rm -f "$input_file"; [ -z "$output_file" ] || rm -f "$output_file"' 0
if ! cat >"$input_file"; then
  cat >/dev/null
  echo "$fallback"
  exit 0
fi
if [ -z "${LU_DRIVER_STATE_FILE:-}" ] || [ -z "${SESSION_HANDOFF_AGENT:-}" ]; then
  echo "$fallback"
  exit 0
fi
# Validate output without storing its bytes in a shell variable.
output_file=$(mktemp --tmpdir="$TMPDIR" agy-out.XXXXXX) || { echo "$fallback"; exit 0; }
project_python_command "$py" || { echo "$fallback"; exit 0; }
if (cd "$LU_PRODUCT_ROOT" && "${PROJECT_PYTHON_COMMAND[@]}" -m scripts.driver_state "$mode" <"$input_file" >"$output_file" 2>/dev/null); then
  # A successful child must produce exactly one strict JSON object. Keep the
  # validator's output private too: a broken interpreter is not validation.
  if validation=$("$py" -I -c '
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
