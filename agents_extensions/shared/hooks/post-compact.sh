#!/bin/bash
# Hook: PostCompact — fires after context compaction
# Injects a concise context reminder so the agent doesn't lose track.

# Skip in non-interactive mode
if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$LEARN_UKRAINIAN_PIPELINE" ] || [ -n "$GEMINI_SESSION" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
CANONICAL_ROOT="${CODEX_CANONICAL_REPO_ROOT:-$PROJECT_DIR}"
BOUNDED_PYTHON="${THREAD_ROLLOVER_PYTHON:-$CANONICAL_ROOT/.venv/bin/python}"
BOUNDED_RUNNER="${SESSION_BOUNDED_RUNNER:-$PROJECT_DIR/scripts/agent_runtime/bounded_command.py}"
run_bounded() {
  local timeout_seconds="$1"
  shift
  if [ ! -x "$BOUNDED_PYTHON" ] || [ ! -f "$BOUNDED_RUNNER" ]; then
    return 127
  fi
  "$BOUNDED_PYTHON" "$BOUNDED_RUNNER" --timeout "$timeout_seconds" -- "$@"
}
CONTEXT=""

# 1. Find current in-progress modules
IN_PROGRESS=""
if [ -d "$PROJECT_DIR/curriculum" ]; then
  IN_PROGRESS=$(run_bounded 2 find "$PROJECT_DIR/curriculum" -name "state-v3.json" \
    -exec grep -l '"in_progress"' {} \; 2>/dev/null | head -3)
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

# 2. Local rollover health only. PostCompact must never prepare, resume, prove,
# confirm, clean up, query GitHub, or manufacture handoff anchors.
HANDOFF_AGENT="${SESSION_HANDOFF_AGENT:-}"
if [ -z "$HANDOFF_AGENT" ]; then
  if [[ "${0:-}" == *"/.codex/"* ]] || [ -n "${CODEX_THREAD_ID:-}${CODEX_SESSION_ID:-}" ]; then
    HANDOFF_AGENT="codex"
  else
    HANDOFF_AGENT="claude"
  fi
fi
ROLLOVER_PYTHON="${THREAD_ROLLOVER_PYTHON:-$PROJECT_DIR/.venv/bin/python}"
ROLLOVER_SCRIPT="${THREAD_ROLLOVER_SCRIPT:-$PROJECT_DIR/scripts/orchestration/thread_handoff.py}"
ROLLOVER_HEALTH=$(run_bounded 2 "$ROLLOVER_PYTHON" "$ROLLOVER_SCRIPT" \
  --repo-root "$CANONICAL_ROOT" detect --agent "$HANDOFF_AGENT" 2>&1) || true

# 3. Key reminders
CONTEXT="$CONTEXT
KEY REMINDERS:
  - Thread rollover health (read-only): $ROLLOVER_HEALTH
  - If a live packet is shown, read its handoff path; SessionStart provides the lifecycle commands.
  - Word targets are MINIMUMS (check config.py)
  - Edit agents_extensions/shared/, not .claude/ directly
  - .venv/bin/python only
  - Pre-commit: ruff + /simplify + Gemini review
  - Read audit/ and review/ files before fixing modules
  - MEMORY: ~/.claude/projects/-Users-krisztiankoos-projects-learn-ukrainian/memory/MEMORY.md"

printf '{"additionalContext": %s}' "$(printf '%s' "CONTEXT RESTORED AFTER COMPACTION:$CONTEXT" | jq -Rs '.')"
exit 0
