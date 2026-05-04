#!/bin/bash
# Hook: PostToolUse / PostToolUseFailure — fire-and-forget tool timing telemetry.

set -u

command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(</dev/stdin)
TZ=UTC0 printf -v TS '%(%Y-%m-%dT%H:%M:%S.000Z)T' -1

[[ "$INPUT" =~ \"tool_name\"[[:space:]]*:[[:space:]]*\"([^\"]+)\" ]] || exit 0
TOOL_NAME="${BASH_REMATCH[1]}"

[[ "$INPUT" =~ \"duration_ms\"[[:space:]]*:[[:space:]]*([0-9]+(\.[0-9]+)?) ]] || exit 0
DURATION_RAW="${BASH_REMATCH[1]}"
DURATION_MS="${DURATION_RAW%%.*}"
if [[ "$DURATION_RAW" == *.* ]]; then
  FRACTION="${DURATION_RAW#*.}"
  FIRST_DECIMAL="${FRACTION:0:1}"
  if [ "$FIRST_DECIMAL" -ge 5 ] 2>/dev/null; then
    DURATION_MS=$((DURATION_MS + 1))
  fi
fi

TOOL_USE_ID=""
if [[ "$INPUT" =~ \"tool_use_id\"[[:space:]]*:[[:space:]]*\"([^\"]*)\" ]]; then
  TOOL_USE_ID="${BASH_REMATCH[1]}"
fi
TOOL_USE_JSON=null
[ -n "$TOOL_USE_ID" ] && TOOL_USE_JSON="\"$TOOL_USE_ID\""

SESSION_ID=""
if [[ "$INPUT" =~ \"session_id\"[[:space:]]*:[[:space:]]*\"([^\"]*)\" ]]; then
  SESSION_ID="${BASH_REMATCH[1]}"
fi
SESSION_JSON=null
[ -n "$SESSION_ID" ] && SESSION_JSON="\"$SESSION_ID\""

FAILED=false
if [[ "$INPUT" =~ \"hook_event_name\"[[:space:]]*:[[:space:]]*\"PostToolUseFailure\" ]]; then
  FAILED=true
fi

PAYLOAD=$(printf '{"ts":"%s","tool_name":"%s","duration_ms":%s,"tool_use_id":%s,"session_id":%s,"failed":%s}' \
  "$TS" \
  "$TOOL_NAME" \
  "$DURATION_MS" \
  "$TOOL_USE_JSON" \
  "$SESSION_JSON" \
  "$FAILED")

(
  curl -sS -m 0.5 \
    -H 'Content-Type: application/json' \
    -X POST \
    --data "$PAYLOAD" \
    http://localhost:8765/api/telemetry/tool-timings \
    >/dev/null 2>&1
) &
disown 2>/dev/null || true

exit 0
