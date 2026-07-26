#!/bin/bash
# Hook: PostToolUse / PostToolUseFailure — fire-and-forget tool timing telemetry.

set -u

command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(</dev/stdin)
TS=$(date -u +'%Y-%m-%dT%H:%M:%S.000Z')

# macOS ships Bash 3.2, whose printf lacks the %(... )T formatter. Build the
# complete request with jq instead of regex/string interpolation so timestamps
# and JSON strings remain valid for the FastAPI ToolTimingIngest contract.
PAYLOAD=$(printf '%s' "$INPUT" | jq -ce --arg ts "$TS" '
  . as $input
  | ($input.tool_name | select(type == "string" and length > 0)) as $tool_name
  | ($input.duration_ms | select(type == "number" and . >= 0) | round) as $duration_ms
  | {
      ts: $ts,
      tool_name: $tool_name,
      duration_ms: $duration_ms,
      tool_use_id: (
        if (($input.tool_use_id? | type) == "string" and ($input.tool_use_id | length) > 0)
        then $input.tool_use_id else null end
      ),
      session_id: (
        if (($input.session_id? | type) == "string" and ($input.session_id | length) > 0)
        then $input.session_id else null end
      ),
      failed: (
        ($input.hook_event_name == "PostToolUseFailure")
        or (($input.tool_response.exit_code? | type) == "number" and $input.tool_response.exit_code != 0)
        or ($input.tool_response.is_error? == true)
        or ($input.tool_response.status? == "failed")
      )
    }
') || exit 0

(
  curl -sS -m 0.5 \
    -H 'Content-Type: application/json' \
    -X POST \
    --data "$PAYLOAD" \
    "${TOOL_TIMING_API_URL:-http://127.0.0.1:8765/api/telemetry/tool-timings}" \
    >/dev/null 2>&1
) &
disown 2>/dev/null || true

exit 0
