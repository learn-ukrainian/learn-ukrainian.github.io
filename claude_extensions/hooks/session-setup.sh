#!/bin/bash
# Hook: SessionStart — runs on new sessions AND resumed sessions
# Validates environment and reports project state.
# Skips in headless/pipeline mode to avoid adding latency.

# Skip in non-interactive (headless) mode
if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$LEARN_UKRAINIAN_PIPELINE" ] || [ -n "$GEMINI_SESSION" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
ISSUES=()
INFO=()

# 1. Check .venv exists and has correct Python
if [ ! -f "$PROJECT_DIR/.venv/bin/python" ]; then
  ISSUES+=("VENV MISSING: .venv/bin/python not found. Recreate: rm -rf .venv && ~/.pyenv/versions/3.12.8/bin/python -m venv .venv")
else
  PY_VERSION=$("$PROJECT_DIR/.venv/bin/python" --version 2>/dev/null)
  if [[ "$PY_VERSION" != *"3.12"* ]]; then
    ISSUES+=("VENV WRONG PYTHON: Expected 3.12.x, got $PY_VERSION")
  fi
fi

# 2. Check CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS is set
if [ -z "$CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS" ]; then
  ISSUES+=("ENV MISSING: CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS not set. Add to .bashrc: export CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS=32000")
fi

# 3. Check message broker DB exists
MCP_DB="$PROJECT_DIR/.mcp/servers/message-broker/messages.db"
if [ ! -f "$MCP_DB" ]; then
  INFO+=("Message broker DB not found at $MCP_DB — Gemini comms unavailable")
fi

# 4. Check for stale orchestration state (in-progress builds older than 24h)
STALE_COUNT=0
if [ -d "$PROJECT_DIR/curriculum" ]; then
  while IFS= read -r -d '' state_file; do
    if [ -f "$state_file" ]; then
      if grep -q '"in_progress"' "$state_file" 2>/dev/null; then
        MOD_TIME=$(stat -f %m "$state_file" 2>/dev/null || stat -c %Y "$state_file" 2>/dev/null)
        NOW=$(date +%s)
        AGE=$(( (NOW - MOD_TIME) / 3600 ))
        if [ "$AGE" -gt 24 ]; then
          STALE_COUNT=$((STALE_COUNT + 1))
        fi
      fi
    fi
  done < <(find "$PROJECT_DIR/curriculum" -name "state-v3.json" -print0 2>/dev/null)
fi

if [ "$STALE_COUNT" -gt 0 ]; then
  INFO+=("$STALE_COUNT stale orchestration state file(s) found (in_progress > 24h old). Consider cleanup.")
fi

# 5. Report in-progress module builds
IN_PROGRESS_COUNT=0
if [ -d "$PROJECT_DIR/curriculum" ]; then
  IN_PROGRESS_COUNT=$(find "$PROJECT_DIR/curriculum" -name "state-v3.json" -exec grep -l '"in_progress"' {} \; 2>/dev/null | wc -l | tr -d ' ')
fi

if [ "$IN_PROGRESS_COUNT" -gt 0 ]; then
  INFO+=("$IN_PROGRESS_COUNT module build(s) currently in progress")
fi

# 6. Check MEMORY.md line count (truncated at 200 lines by system)
MEMORY_DIR="$HOME/.claude/projects/-Users-krisztiankoos-projects-learn-ukrainian/memory"
MEMORY_FILE="$MEMORY_DIR/MEMORY.md"
if [ -f "$MEMORY_FILE" ]; then
  MEMORY_LINES=$(wc -l < "$MEMORY_FILE" | tr -d ' ')
  if [ "$MEMORY_LINES" -gt 150 ]; then
    ISSUES+=("MEMORY.md is $MEMORY_LINES lines (limit: 200, budget: 150). Lines after 200 are INVISIBLE. Trim NOW before doing anything else. Move reference data to topic files in memory/.")
  elif [ "$MEMORY_LINES" -gt 120 ]; then
    INFO+=("MEMORY.md is $MEMORY_LINES/150 lines — approaching budget. Be selective about new entries.")
  fi
fi

# 7. Check claude_extensions/ → .claude/ sync drift
if [ -d "$PROJECT_DIR/claude_extensions" ] && [ -d "$PROJECT_DIR/.claude" ]; then
  DRIFT=$(diff -rq "$PROJECT_DIR/claude_extensions/" "$PROJECT_DIR/.claude/" \
    --exclude='.DS_Store' --exclude='settings.local.json' 2>/dev/null | head -5)
  if [ -n "$DRIFT" ]; then
    DRIFT_COUNT=$(echo "$DRIFT" | wc -l | tr -d ' ')
    ISSUES+=("DEPLOY DRIFT: $DRIFT_COUNT file(s) differ between claude_extensions/ and .claude/. Run: npm run claude:deploy")
  fi
fi

# 8. Check MCP sources server health (historically called the RAG server)
MCP_STATUS=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:8766/sse" 2>/dev/null)
if [ "$MCP_STATUS" != "200" ] && [ "$MCP_STATUS" != "000" ]; then
  # 000 means connection refused (server down), non-200 means server error
  INFO+=("MCP sources server returned HTTP $MCP_STATUS — some tools may be unavailable")
elif [ "$MCP_STATUS" = "000" ]; then
  ISSUES+=("MCP sources server unreachable at 127.0.0.1:8766 — VESUM + textbook + dictionary tools unavailable. Start with: ./services.sh start sources")
fi

# 9. Check gemini-cli auth
if command -v gemini >/dev/null 2>&1; then
  GEMINI_CHECK=$(gemini --version 2>&1)
  if [[ "$GEMINI_CHECK" == *"error"* ]] || [[ "$GEMINI_CHECK" == *"auth"* ]]; then
    INFO+=("gemini-cli may need re-authentication: gemini auth login")
  fi
else
  INFO+=("gemini-cli not found — Gemini builds unavailable")
fi

# 10. Check for stale decisions
if [ -f "$PROJECT_DIR/.venv/bin/python" ] && [ -f "$PROJECT_DIR/scripts/check_decisions.py" ]; then
  STALE_DECISIONS=$("$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/check_decisions.py" --quiet 2>/dev/null)
  if [ -n "$STALE_DECISIONS" ]; then
    INFO+=("$STALE_DECISIONS")
  fi
fi

# 11. Open GH issues summary
if command -v gh >/dev/null 2>&1; then
  OPEN_ISSUES=$(gh issue list --state open --json number,title,labels --limit 10 2>/dev/null)
  if [ $? -eq 0 ] && [ -n "$OPEN_ISSUES" ] && [ "$OPEN_ISSUES" != "[]" ]; then
    ISSUE_COUNT=$(echo "$OPEN_ISSUES" | jq 'length')
    ISSUE_LIST=$(echo "$OPEN_ISSUES" | jq -r '.[] | "  #\(.number): \(.title)"' | head -5)
    INFO+=("$ISSUE_COUNT open issue(s):
$ISSUE_LIST")
  fi
fi

# Build output
if [ ${#ISSUES[@]} -eq 0 ] && [ ${#INFO[@]} -eq 0 ]; then
  exit 0
fi

CONTEXT="SESSION SETUP CHECK:"

if [ ${#ISSUES[@]} -gt 0 ]; then
  CONTEXT="$CONTEXT
ISSUES:"
  for issue in "${ISSUES[@]}"; do
    CONTEXT="$CONTEXT
  - $issue"
  done
fi

if [ ${#INFO[@]} -gt 0 ]; then
  CONTEXT="$CONTEXT
INFO:"
  for info in "${INFO[@]}"; do
    CONTEXT="$CONTEXT
  - $info"
  done
fi

printf '{"additionalContext": %s}' "$(printf '%s' "$CONTEXT" | jq -Rs '.')"
exit 0
