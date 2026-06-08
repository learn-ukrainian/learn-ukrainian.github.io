#!/bin/bash
# Hook: FileChanged — auto-audit when curriculum .md files change
# Runs audit_module.py on the changed file to catch issues immediately.

# Skip in non-interactive mode or during pipeline builds (would be recursive)
if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$LEARN_UKRAINIAN_PIPELINE" ] || [ -n "$GEMINI_SESSION" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"

# The changed file path is passed as the first argument
CHANGED_FILE="${1:-}"

if [ -z "$CHANGED_FILE" ]; then
  exit 0
fi

# Only audit actual module content files (not orchestration, not plans)
# Pattern: curriculum/l2-uk-en/{level}/{slug}.md
if [[ "$CHANGED_FILE" =~ curriculum/l2-uk-en/[^/]+/[^/]+\.md$ ]] && [[ ! "$CHANGED_FILE" =~ /orchestration/ ]] && [[ ! "$CHANGED_FILE" =~ /audit/ ]] && [[ ! "$CHANGED_FILE" =~ /review/ ]]; then
  AUDIT_RESULT=$("$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/audit_module.py" "$CHANGED_FILE" 2>&1 | tail -5)

  if [ -n "$AUDIT_RESULT" ]; then
    printf '{"additionalContext": %s}' "$(printf '%s' "AUTO-AUDIT ($CHANGED_FILE): $AUDIT_RESULT" | jq -Rs '.')"
  fi
fi

exit 0
