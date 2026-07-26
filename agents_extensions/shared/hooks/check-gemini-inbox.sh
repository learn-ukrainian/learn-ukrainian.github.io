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

# Count unclaimed, unacknowledged messages for this hook's provider.
COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM messages WHERE to_llm='$RECIPIENT' AND acknowledged=0 AND claimed_by IS NULL" 2>/dev/null)

if [ -z "$COUNT" ] || [ "$COUNT" -eq 0 ]; then
  exit 0
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
