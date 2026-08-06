#!/usr/bin/env bash
# Opt-in wrapper: HOOK_TIMING=1 logs wall-ms to batch_state/hook-timing.jsonl
# while preserving the underlying hook's stdin/stdout/stderr/rc.
#
# Usage (Claude settings command field):
#   HOOK_EVENT_NAME=PreToolUse HOOK_MATCHER=Bash \
#     $CLAUDE_PROJECT_DIR/scripts/hooks/run_hook_timed.sh \
#     $CLAUDE_PROJECT_DIR/.claude/hooks/enforce-venv.sh
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PYTHON="${ROOT}/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  exec "$@"
fi
if [ "${HOOK_TIMING:-}" = "1" ] || [ "${HOOK_TIMING:-}" = "true" ] || [ "${HOOK_TIMING:-}" = "always" ]; then
  exec "$PYTHON" -m scripts.hooks.hook_timing wrap -- "$@"
fi
exec "$@"
