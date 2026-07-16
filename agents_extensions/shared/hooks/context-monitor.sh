#!/bin/bash
# Hook: PostToolUse — warn at the active session profile's rollover tiers.
#
# The official hook session/transcript identity and canonical session record are
# authoritative. Latest assistant input/cache usage is preferred; transcript
# size is a compatibility estimate only. Unknown capacity suppresses percentage
# warnings rather than fabricating a 1M or auto-compaction denominator.

# Skip in non-interactive / subagent / pipeline contexts.
if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$LEARN_UK_PIPELINE" ] || [ -n "$GEMINI_SESSION" ]; then
  exit 0
fi

command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(cat)
SESSION_ID=$(printf '%s' "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
[ -z "$SESSION_ID" ] && SESSION_ID="${LEARN_UKRAINIAN_SESSION_ID:-${CODEX_THREAD_ID:-}}"
[ -z "$SESSION_ID" ] && exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
TRANSCRIPT=$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
[ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ] && exit 0

# Prefer the latest assistant input/cache usage. Output tokens are not current
# context usage and therefore are deliberately excluded.
TOKENS=0
USAGE_SOURCE="transcript-size estimate"
USAGE_JSON=$(tail -200 "$TRANSCRIPT" 2>/dev/null \
  | jq -s '[.[] | select(.type == "assistant" and (.message.usage | type) == "object")] | last | .message.usage // empty' 2>/dev/null)
if [ -n "$USAGE_JSON" ] && [ "$USAGE_JSON" != "null" ]; then
  INPUT_TOKENS=$(printf '%s' "$USAGE_JSON" | jq -r '.input_tokens // 0' 2>/dev/null)
  CACHE_READ=$(printf '%s' "$USAGE_JSON" | jq -r '.cache_read_input_tokens // 0' 2>/dev/null)
  CACHE_CREATE=$(printf '%s' "$USAGE_JSON" | jq -r '.cache_creation_input_tokens // 0' 2>/dev/null)
  TOKENS=$(( ${INPUT_TOKENS:-0} + ${CACHE_READ:-0} + ${CACHE_CREATE:-0} ))
  [ "$TOKENS" -gt 0 ] && USAGE_SOURCE="latest assistant input/cache usage"
fi
if [ "$TOKENS" -le 0 ]; then
  RAW_SIZE=$(LC_ALL=C wc -c < "$TRANSCRIPT" 2>/dev/null) || RAW_SIZE=0
  B64_EXCESS=$(LC_ALL=C tr -cs 'A-Za-z0-9+/=' '\n' < "$TRANSCRIPT" 2>/dev/null \
    | LC_ALL=C awk 'length($0) >= 800 { removed += length($0) - 3 } END { print removed + 0 }')
  [ -z "$B64_EXCESS" ] && B64_EXCESS=0
  SIZE=$((RAW_SIZE - B64_EXCESS))
  [ "$SIZE" -lt 0 ] && SIZE=0
  TOKENS=$((SIZE / 7))
fi
[ "$TOKENS" -le 0 ] && exit 0

WINDOW=""
WINDOW_PROVENANCE="unavailable"
WARNING_TIERS=""
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
SESSION_RECORD="$PROJECT_DIR/scripts/lib/session_record.py"
if [ -x "$PYTHON_BIN" ] && [ -f "$SESSION_RECORD" ]; then
  RECORD_JSON=$("$PYTHON_BIN" "$SESSION_RECORD" get --session-id "$SESSION_ID" 2>/dev/null || true)
  if [ -n "$RECORD_JSON" ]; then
    WINDOW=$(printf '%s' "$RECORD_JSON" | jq -r '.actual_context_window_tokens // empty' 2>/dev/null)
    WINDOW_PROVENANCE=$(printf '%s' "$RECORD_JSON" | jq -r '.actual_context_window_provenance // "unavailable"' 2>/dev/null)
    WARNING_TIERS=$(printf '%s' "$RECORD_JSON" | jq -r '.rollover_warning_percentages | select(type == "array" and length == 3) | join(" ")' 2>/dev/null)
  fi
fi

# Compatibility fallback before SessionStart has written a record: only an
# explicitly trusted route may supply a denominator and warning policy.
WINDOW_VALID=1
case "$WINDOW" in
  ""|*[!0-9]*) WINDOW_VALID=0 ;;
  *) [ "$WINDOW" -gt 0 ] || WINDOW_VALID=0 ;;
esac
if [ "$WINDOW_VALID" -eq 0 ]; then
  # Project root is selected at runtime.
  # shellcheck disable=SC1091
  source "$PROJECT_DIR/scripts/lib/profile_resolver.sh" 2>/dev/null || exit 0
  if ! resolve_context_profile \
    "${LEARN_UKRAINIAN_REQUESTED_PROFILE_ID:-${LEARN_UKRAINIAN_PROFILE_ID:-}}" \
    "${LEARN_UKRAINIAN_OBSERVED_MODEL_ID:-${LEARN_UKRAINIAN_MAIN_MODEL_ID:-}}" \
    >/dev/null 2>&1; then
    exit 0
  fi
  [ "${LEARN_UKRAINIAN_TRUSTED:-0}" = "1" ] || exit 0
  WINDOW="${LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS:-}"
  WINDOW_PROVENANCE="declared-profile"
  WARNING_TIERS="${LEARN_UKRAINIAN_ROLLOVER_WARNING_PERCENTAGES:-}"
fi

case "$WINDOW" in
  ""|*[!0-9]*) exit 0 ;;
esac
[ "$WINDOW" -gt 0 ] || exit 0
read -r TIER1_RAW TIER2_RAW TIER3_RAW <<< "$WARNING_TIERS"
[ -n "$TIER1_RAW" ] && [ -n "$TIER2_RAW" ] && [ -n "$TIER3_RAW" ] || exit 0
TIER1_PCT=$(printf '%.0f' "$TIER1_RAW" 2>/dev/null) || exit 0
TIER2_PCT=$(printf '%.0f' "$TIER2_RAW" 2>/dev/null) || exit 0
TIER3_PCT=$(printf '%.0f' "$TIER3_RAW" 2>/dev/null) || exit 0
PCT=$((TOKENS * 100 / WINDOW))

if [ -n "${SESSION_HANDOFF_AGENT:-}" ]; then
  HANDOFF_AGENT="$SESSION_HANDOFF_AGENT"
elif [[ "${0:-}" == *"/.codex/"* ]]; then
  HANDOFF_AGENT="codex"
elif [[ "${0:-}" == *"/.gemini/"* ]]; then
  HANDOFF_AGENT="gemini"
elif [ -n "${CODEX_THREAD_ID:-}${CODEX_SESSION_ID:-}" ]; then
  HANDOFF_AGENT="codex"
else
  HANDOFF_AGENT="claude"
fi

PREPARE_CMD=".venv/bin/python scripts/orchestration/thread_handoff.py prepare --agent ${HANDOFF_AGENT} --context-percent ${PCT}"
BOOTSTRAP_FILE=".agent/${HANDOFF_AGENT}-thread-bootstrap.md"
HANDOFF_FILE=".agent/${HANDOFF_AGENT}-thread-handoff.md"
CONTEXT_FACT="${PCT}% of the ${WINDOW}-token context window [~${TOKENS}/${WINDOW}; ${USAGE_SOURCE}; capacity: ${WINDOW_PROVENANCE}]"

if [ "$PCT" -ge "$TIER3_PCT" ]; then
  MSG=$(printf '%s\n%s\n%s\n%s\n%s\n%s\n' \
    "EMERGENCY: Context is at ${CONTEXT_FACT}. The profile's final rollover tier is ${TIER3_PCT}%." \
    "" \
    "STOP all current work THIS TURN. Do not start new tool calls beyond what is needed to:" \
    "1. Run: ${PREPARE_CMD}. This writes the gitignored rollover lease plus ${HANDOFF_FILE} and ${BOOTSTRAP_FILE}." \
    "2. Start the supported continuation for this harness, or tell the user to start a fresh thread with ${BOOTSTRAP_FILE}." \
    "3. Confirm the replacement only after it is actually running; do not delete the prepared lease early.")
elif [ "$PCT" -ge "$TIER2_PCT" ]; then
  MSG=$(printf '%s\n%s\n%s\n%s\n%s\n%s\n' \
    "CRITICAL: Context is at ${CONTEXT_FACT}. The profile's critical rollover tier is ${TIER2_PCT}%." \
    "" \
    "Finish the current logical unit, then:" \
    "1. Run: ${PREPARE_CMD}. This writes only gitignored rollover state and handoff files." \
    "2. Start the supported continuation for this harness, or use ${BOOTSTRAP_FILE} in a fresh thread." \
    "Do not start new multi-step work or large operations before rollover.")
elif [ "$PCT" -ge "$TIER1_PCT" ]; then
  MSG=$(printf '%s\n%s\n%s\n' \
    "HEADS UP: Context is at ${CONTEXT_FACT}. The profile's first rollover tier is ${TIER1_PCT}%." \
    "" \
    "Wrap up the current logical unit soon. For rollover, run ${PREPARE_CMD}; it writes gitignored .agent/ handoff state.")
else
  exit 0
fi

jq -n --arg msg "$MSG" '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":$msg}}'
