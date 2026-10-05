#!/bin/bash
# Hook: UserPromptSubmit and PreCompact (matcher auto) — hold a session whose
# context profile uses rollover_mode operator_restart at its prepared handoff
# until the operator restarts it (#8511). Other profiles are untouched.
#
# UserPromptSubmit: after context-monitor.sh has announced the final tier for
# this session (its tier state file holds tier 3), each later prompt carries
# one short reminder so it does not restart large work.
# PreCompact: automatic compaction is blocked with exit code 2, which the Claude
# Code hooks reference documents as "Blocks compaction" (supported since
# 2.1.105). Manual /compact stays allowed. Claude Code discards a PreCompact
# hook's systemMessage, so the reason goes to stderr.

# Same harness and context exits as context-monitor.sh.
if [ "${SESSION_HANDOFF_AGENT:-}" = "codex" ] \
  || [[ "${0:-}" == *"/.codex/"* ]] \
  || [ -n "${CODEX_THREAD_ID:-}${CODEX_SESSION_ID:-}" ]; then
  exit 0
fi
if [ -n "${CLAUDE_NON_INTERACTIVE:-}" ] || [ -n "${LEARN_UK_PIPELINE:-}" ] \
  || [ -n "${LEARN_UKRAINIAN_PIPELINE:-}" ] || [ -n "${GEMINI_SESSION:-}" ]; then
  exit 0
fi
if [ -n "${GROK_AGENT:-}" ] || [ "${SESSION_HANDOFF_AGENT:-}" = "grok" ] \
  || [ "${SESSION_HANDOFF_AGENT:-}" = "grok-build" ]; then
  exit 0
fi

command -v jq >/dev/null 2>&1 || exit 0
# shellcheck source=agents_extensions/shared/hooks/context-rollover-lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/context-rollover-lib.sh" 2>/dev/null || exit 0

INPUT=$(cat)
EVENT=$(printf '%s' "$INPUT" | jq -r '.hook_event_name // empty' 2>/dev/null)
SESSION_ID=$(printf '%s' "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
[ -z "$SESSION_ID" ] && SESSION_ID="${LEARN_UKRAINIAN_SESSION_ID:-}"
[ -z "$SESSION_ID" ] && exit 0
case "$SESSION_ID" in */*|*..*) exit 0 ;; esac
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"

ROLLOVER_MODE="${LEARN_UKRAINIAN_ROLLOVER_MODE:-}"
RECORD_FILE=$(context_session_record_file "$PROJECT_DIR" "$SESSION_ID")
if [ -f "$RECORD_FILE" ] && [ ! -L "$RECORD_FILE" ]; then
  ROLLOVER_MODE=$(jq -r '.rollover_mode // empty' "$RECORD_FILE" 2>/dev/null || true)
fi
[ "$(context_effective_rollover_mode "$ROLLOVER_MODE")" = "operator_restart" ] || exit 0

case "$EVENT" in
  PreCompact)
    TRIGGER=$(printf '%s' "$INPUT" | jq -r '.trigger // empty' 2>/dev/null)
    [ "$TRIGGER" = "auto" ] || exit 0
    printf '%s\n' "Automatic compaction is blocked for this session (rollover_mode operator_restart, #8511): prepare the handoff with the thread-rollover skill and restart the session instead. Manual /compact remains available." >&2
    exit 2
    ;;
  UserPromptSubmit)
    TIER_STATE_FILE="$PROJECT_DIR/batch_state/context_monitor/${SESSION_ID}.tier"
    [ -f "$TIER_STATE_FILE" ] || exit 0
    LAST_TIER=0
    LAST_TOKENS=0
    read -r LAST_TIER LAST_TOKENS < "$TIER_STATE_FILE" 2>/dev/null || true
    [ "$LAST_TIER" = "3" ] || exit 0
    case "$LAST_TOKENS" in ''|*[!0-9]*) LAST_TOKENS=0 ;; esac
    TOKENS=0
    TRANSCRIPT=$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
    [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ] && TOKENS=$(context_latest_usage_tokens "$TRANSCRIPT")
    case "$TOKENS" in ''|*[!0-9]*) TOKENS=0 ;; esac
    # A compaction-scale drop (a manual /compact) re-arms context-monitor.sh's
    # tiers on the next tool call; do not remind about a context that is gone.
    if [ "$TOKENS" -gt 0 ] && [ $((TOKENS * 100)) -lt $((LAST_TOKENS * 60)) ]; then
      exit 0
    fi
    [ "$TOKENS" -gt 0 ] || TOKENS="$LAST_TOKENS"
    MSG="Context is above this session's final rollover tier (~$((TOKENS / 1000))k tokens) and the handoff should already be prepared. Only answer briefly; do not start new work or dispatches. If the handoff is not prepared yet, prepare it now, then tell the operator to restart the session."
    jq -n --arg msg "$MSG" '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":$msg}}'
    ;;
esac
exit 0
