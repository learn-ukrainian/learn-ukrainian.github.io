#!/bin/bash
# Hook: Check for unread cross-agent messages on every prompt submit
# Queries the MCP message broker SQLite DB directly (no MCP overhead)
#
# PIPELINE GUARD: Skips during build_module / ai_agent_bridge runs
# to prevent ping-pong between automated pipeline phases.

# Skip in pipeline/headless mode
if [ "${GEMINI_SESSION:-}" = "1" ] || [ "${LEARN_UKRAINIAN_PIPELINE:-}" = "1" ]; then
  exit 0
fi

HOOK_INPUT=$(cat)
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
DB="$PROJECT_DIR/.mcp/servers/message-broker/messages.db"
RECIPIENT="${LEARN_UK_HOOK_RECIPIENT:-claude}"

case "$RECIPIENT" in
  claude|codex|gemini|agy|grok|orchestrator) ;;
  *) exit 0 ;;
esac

RECIPIENT_LABEL=$(printf '%s' "$RECIPIENT" | tr '[:lower:]' '[:upper:]')

if [ ! -f "$DB" ]; then
  exit 0
fi

# Count unclaimed, unacknowledged messages for this hook's provider. Keep the
# pending IDs separate from previews: the session-local dedupe state may never
# contain message content.
PENDING_IDS=$(sqlite3 "$DB" "SELECT id FROM messages WHERE to_llm='$RECIPIENT' AND acknowledged=0 AND claimed_by IS NULL ORDER BY id ASC" 2>/dev/null)
COUNT=$(printf '%s\n' "$PENDING_IDS" | sed '/^$/d' | wc -l | tr -d ' ')

if [ -z "$COUNT" ] || [ "$COUNT" -eq 0 ]; then
  exit 0
fi

# A UserPromptSubmit hook can fire repeatedly before another worker claims or
# acknowledges its message. Suppress only an identical recipient/session ID
# list. No session identity or unavailable state is deliberately fail-open.
SESSION_ID="${LEARN_UK_HOOK_SESSION_ID:-${LEARN_UKRAINIAN_SESSION_ID:-${CODEX_THREAD_ID:-${CODEX_SESSION_ID:-}}}}"
if [ -z "$SESSION_ID" ]; then
  SESSION_ID=$(printf '%s' "$HOOK_INPUT" | jq -r '.session_id // empty' 2>/dev/null)
fi
if [ -n "$SESSION_ID" ]; then
  STATE_DIR="$PROJECT_DIR/.agent/runtime"
  STATE_KEY=""
  if command -v shasum >/dev/null 2>&1; then
    STATE_KEY=$(printf '%s\n%s' "$RECIPIENT" "$SESSION_ID" | shasum -a 256 | awk '{print $1}')
  fi
  STATE_FILE="$STATE_DIR/inbox-${STATE_KEY}.ids"
  if [ -n "$STATE_KEY" ] && mkdir -p "$STATE_DIR" 2>/dev/null; then
    STATE_TMP=$(mktemp "$STATE_DIR/.inbox-${STATE_KEY}.XXXXXX" 2>/dev/null || true)
    if [ -n "$STATE_TMP" ]; then
      printf '%s\n' "$PENDING_IDS" > "$STATE_TMP"
      if [ -f "$STATE_FILE" ] && cmp -s "$STATE_TMP" "$STATE_FILE"; then
        rm -f "$STATE_TMP"
        exit 0
      fi
      if ! mv -f "$STATE_TMP" "$STATE_FILE" 2>/dev/null; then
        rm -f "$STATE_TMP"
      fi
    fi
  fi
fi

# Get message previews (only unclaimed)
PREVIEWS=$(sqlite3 -separator '|' "$DB" "
  SELECT
    id,
    from_llm,
    message_type,
    COALESCE(task_id, '(none)'),
    substr(content, 1, 120),
    timestamp
  FROM messages
  WHERE to_llm='$RECIPIENT' AND acknowledged=0 AND claimed_by IS NULL
  ORDER BY id ASC
  LIMIT 5
" 2>/dev/null)

CONTEXT="${RECIPIENT_LABEL} INBOX: ${COUNT} unread message(s) waiting.
---"

while IFS='|' read -r id from type task preview ts; do
  CONTEXT="${CONTEXT}
[msg #${id}] from ${from} | type: ${type} | task: ${task} | ${ts}
  ${preview}..."
done <<< "$PREVIEWS"

CONTEXT="${CONTEXT}
---
Use mcp__message-broker__receive_messages to read full messages. Acknowledge after processing."

jq -n --arg msg "$CONTEXT" \
  '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":$msg}}'

exit 0
