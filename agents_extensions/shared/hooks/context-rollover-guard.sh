#!/bin/bash
# Hook: UserPromptSubmit - remind a session whose context profile uses
# rollover_mode operator_restart that it is past its final rollover tier and
# waits for the operator to restart it (#8511). Other profiles are untouched.
#
# The mode comes only from this session's own record (SessionStart writes it);
# no record, a record for another session, or an unreadable record means the
# guard does nothing.
#
# After context-monitor.sh has announced the final tier for this session (its
# tier state file holds tier 3), each later prompt carries one short reminder
# so it does not restart large work. This hook does not block compaction:
# Claude Code may still auto-compact near its own limit if the session keeps
# going. Holding compaction for a prepared handoff is tracked in #9790.

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

RECORD_FILE=$(context_session_record_file "$PROJECT_DIR" "$SESSION_ID")
[ -f "$RECORD_FILE" ] && [ ! -L "$RECORD_FILE" ] || exit 0
ROLLOVER_MODE=$(jq -r --arg sid "$SESSION_ID" \
  'if .session_id == $sid then .rollover_mode // empty else empty end' "$RECORD_FILE" 2>/dev/null || true)
[ "$(context_effective_rollover_mode "$ROLLOVER_MODE")" = "operator_restart" ] || exit 0

[ "$EVENT" = "UserPromptSubmit" ] || exit 0
LAST_TIER=0
LAST_TOKENS=0
read -r LAST_TIER LAST_TOKENS <<< "$(context_hook_state read "$PROJECT_DIR" "$SESSION_ID")"
[ "$LAST_TIER" = "3" ] || exit 0
case "$LAST_TOKENS" in ''|*[!0-9]*) LAST_TOKENS=0 ;; esac
TOKENS=0
TRANSCRIPT=$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
[ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ] && TOKENS=$(context_latest_usage_tokens "$TRANSCRIPT")
case "$TOKENS" in ''|*[!0-9]*) TOKENS=0 ;; esac
# A compaction-scale drop (manual or automatic compaction) re-arms context-monitor.sh's
# tiers on the next tool call; do not remind about a context that is gone.
if [ "$TOKENS" -gt 0 ] && [ $((TOKENS * 100)) -lt $((LAST_TOKENS * 60)) ]; then
  exit 0
fi
[ "$TOKENS" -gt 0 ] || TOKENS="$LAST_TOKENS"
MSG="Context is above this session's final rollover tier (~$((TOKENS / 1000))k tokens) and the handoff should already be prepared. Only answer briefly; do not start new work or dispatches. If the handoff is not prepared yet, prepare it now, then tell the operator to restart the session."
jq -n --arg msg "$MSG" '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":$msg}}'
exit 0
