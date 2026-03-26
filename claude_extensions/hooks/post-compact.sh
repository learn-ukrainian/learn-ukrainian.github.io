#!/bin/bash
# Hook: PostCompact — fires after context compaction
# Injects a concise context reminder so the agent doesn't lose track.

# Skip in non-interactive mode
if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$LEARN_UKRAINIAN_PIPELINE" ] || [ -n "$GEMINI_SESSION" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
CONTEXT=""

# 1. Find current in-progress modules
IN_PROGRESS=""
if [ -d "$PROJECT_DIR/curriculum" ]; then
  IN_PROGRESS=$(find "$PROJECT_DIR/curriculum" -name "state-v3.json" -exec grep -l '"in_progress"' {} \; 2>/dev/null | head -3)
fi

if [ -n "$IN_PROGRESS" ]; then
  MODULE_LIST=$(echo "$IN_PROGRESS" | while read -r f; do
    slug=$(basename "$(dirname "$f")")
    track=$(basename "$(dirname "$(dirname "$(dirname "$f")")")")
    echo "  - $track/$slug"
  done)
  CONTEXT="$CONTEXT
IN-PROGRESS MODULES:
$MODULE_LIST"
fi

# 2. Current open GH issues (top 5)
if command -v gh >/dev/null 2>&1; then
  ISSUES=$(gh issue list --state open --limit 5 --json number,title 2>/dev/null | jq -r '.[] | "  #\(.number): \(.title)"' 2>/dev/null)
  if [ -n "$ISSUES" ]; then
    CONTEXT="$CONTEXT
OPEN ISSUES (top 5):
$ISSUES"
  fi
fi

# 3. Key reminders
CONTEXT="$CONTEXT
KEY REMINDERS:
  - Word targets are MINIMUMS (check config.py)
  - Edit claude_extensions/, not .claude/ directly
  - .venv/bin/python only
  - Pre-commit: ruff + /simplify + Gemini review
  - Read audit/ and review/ files before fixing modules
  - MEMORY: ~/.claude/projects/-Users-krisztiankoos-projects-learn-ukrainian/memory/MEMORY.md"

printf '{"additionalContext": %s}' "$(printf '%s' "CONTEXT RESTORED AFTER COMPACTION:$CONTEXT" | jq -Rs '.')"
exit 0
