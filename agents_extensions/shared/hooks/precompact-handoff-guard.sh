#!/bin/bash
# PreCompact(auto): pause only for this interactive Claude session's own proven
# operator-restart handoff. Unavailable, unsafe or timed-out evidence fails open.
case "${SESSION_HANDOFF_AGENT:-claude}" in
  claude|claude-*) ;;
  *) exit 0 ;;
esac
if [[ "${0:-}" == *"/.codex/"* ]] \
  || [ -n "${CODEX_THREAD_ID:-}${CODEX_SESSION_ID:-}${CODEX_SESSION:-}" ] \
  || [ -n "${CLAUDE_NON_INTERACTIVE:-}${LEARN_UK_PIPELINE:-}${LEARN_UKRAINIAN_PIPELINE:-}" ] \
  || [ -n "${GEMINI_SESSION:-}${GROK_AGENT:-}${LEARN_UKRAINIAN_DISPATCH_TASK_ID:-}" ]; then
  exit 0
fi

# shellcheck source=agents_extensions/shared/hooks/context-rollover-lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/context-rollover-lib.sh" 2>/dev/null || exit 0
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
CANONICAL_ROOT=$(context_canonical_root "$PROJECT_DIR") || exit 0
BOUNDED_PYTHON="${THREAD_ROLLOVER_PYTHON:-$CANONICAL_ROOT/.venv/bin/python}"
BOUNDED_RUNNER="${SESSION_BOUNDED_RUNNER:-$PROJECT_DIR/scripts/agent_runtime/bounded_command.py}"
[ -x "$BOUNDED_PYTHON" ] && [ -f "$BOUNDED_RUNNER" ] || exit 0
cd "$PROJECT_DIR" 2>/dev/null || exit 0

RESULT=$("$BOUNDED_PYTHON" "$BOUNDED_RUNNER" --timeout 2 -- \
  "$BOUNDED_PYTHON" -m scripts.orchestration.precompact_handoff_check \
  --state-root "$CANONICAL_ROOT" --agent "${SESSION_HANDOFF_AGENT:-claude}" 2>/dev/null) || exit 0
[ "$RESULT" = "prepared" ] || exit 0
printf '%s\n' 'Automatic compaction paused: this session has prepared its rollover handoff. Restart the session to continue.' >&2
exit 2
