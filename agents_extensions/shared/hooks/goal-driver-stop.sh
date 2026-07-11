#!/bin/bash
# Hook: Stop — /goal driver async-dispatch awareness.
#
# Reads the Stop-event JSON on stdin and asks scripts/goal_driver/stop_hook.py
# to inspect the transcript's last status line. The Python module emits
# additionalContext if (a) the last turn was GOAL_WAIT, or (b) the last turn
# was GOAL_STATUS while /api/delegate/active reports an in-flight dispatch.
#
# This hook NEVER blocks Stop. /goal's native predicate enforcement is
# unchanged; this hook only annotates state so the next turn's counters
# stay honest under async-heavy work. See issue #1933.
#
# Skip in non-interactive / pipeline contexts to avoid latency in batch jobs.

if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$LEARN_UKRAINIAN_PIPELINE" ] || [ -n "$GEMINI_SESSION" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
PYTHON="$PROJECT_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  # Fail open: never let a missing venv kill a Stop event.
  exit 0
fi

# `python -m` resolves the module against the CURRENT working directory, so a
# session whose cwd is not the repo root (worktree, other dir) hits
# "ModuleNotFoundError: No module named 'scripts'". Anchor cwd to the project
# root first; fail open if it is unreachable. (cwd-drift bug family: #4912/#4899.)
cd "$PROJECT_DIR" || exit 0

exec "$PYTHON" -m scripts.goal_driver.stop_hook
