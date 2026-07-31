#!/bin/bash
# Hook: Claude invokes this as PostCompact after context compaction. Codex invokes
# it from SessionStart(source=compact), because Codex PostCompact cannot emit
# model-visible additionalContext. Inject a concise context reminder so the agent
# doesn't lose track.

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

emit_context() {
  local context="$1"
  if [ "${CODEX_COMPACT_SESSION_START:-}" = "1" ]; then
    printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}' \
      "$(printf '%s' "$context" | jq -Rs '.')"
  else
    printf '{"additionalContext": %s}' "$(printf '%s' "$context" | jq -Rs '.')"
  fi
}

# Ordinary Codex tasks use the runtime's native remote compaction and need no
# repository-authored context replay. A launcher-bound fleet driver is the
# exception: hydrate only its exact stream and point at the durable shadow
# diary instead of scanning every rollover or curriculum artifact.
POST_COMPACT_AGENT="${SESSION_HANDOFF_AGENT:-}"
if [ -z "$POST_COMPACT_AGENT" ] \
  && { [[ "${0:-}" == *"/.codex/"* ]] || [ -n "${CODEX_THREAD_ID:-}${CODEX_SESSION_ID:-}${CODEX_SESSION:-}" ]; }; then
  POST_COMPACT_AGENT="codex"
fi
case "$POST_COMPACT_AGENT" in
  codex|codex-*)
    if [ -z "${SESSION_EPIC:-}" ]; then
      # Native Codex compaction is self-contained for non-driver tasks. This
      # includes explicitly tagged Codex sessions: they must never fall through
      # into the shared Claude-oriented replay below.
      exit 0
    else
      DIARY_REL=".claude/${SESSION_EPIC}-epic/CODEX-DRIVER-HANDOFF.md"
      if [ ! -f "$PROJECT_DIR/$DIARY_REL" ]; then
        HYDRATION_RC=2
        HYDRATION="Exact Codex driver handoff is missing: $DIARY_REL"
      else
        HYDRATION_RC=0
        HYDRATION=$(run_bounded 2 "$BOUNDED_PYTHON" \
          -m scripts.session_canary.codex_lane hydrate --epic "$SESSION_EPIC" 2>&1) \
          || HYDRATION_RC=$?
      fi
      if [ "$HYDRATION_RC" -eq 0 ]; then
        CONTEXT="CODEX FLEET-DRIVER HYDRATION
$HYDRATION
Shadow diary: $DIARY_REL
Native Codex still owns compaction; continue only from the capsule's next_drive_boundary."
      else
        CONTEXT="CODEX FLEET-DRIVER HYDRATION BLOCKED
${HYDRATION:-Hydration helper unavailable.}
Shadow diary: $DIARY_REL
Do not select the next queue action until the stream lease or diary is repaired."
      fi
      emit_context "$CONTEXT"
      exit 0
    fi
    ;;
esac

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

emit_context "CONTEXT RESTORED AFTER COMPACTION:$CONTEXT"
exit 0
