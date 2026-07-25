#!/bin/bash
# Hook: PostToolUse — throttled thread-lease heartbeat refresh (issue #5759).
#
# The Stop hook (goal-driver-stop.sh) only refreshes this session's durable
# thread-lease heartbeat when a turn completes. A single tool call inside one
# turn can run far longer than claim_thread_lease's 900s emergency TTL (the
# fallback used only when the previous owner's liveness cannot be checked),
# during which this session's own lease would look stale to a competing
# SessionStart even though it is very much alive. This hook closes that gap
# by firing on the much more frequent PostToolUse event instead.
#
# Throttled to stay cheap: refresh_thread_lease_heartbeat only rewrites the
# lease file when the existing heartbeat is already older than 60s, so the
# common case (many tool calls per minute) is a read, never a write. It is
# best-effort and never a takeover — a no-op for a lease this session does
# not already own, exactly like the Stop-hook refresh.
#
# Residual gap (documented, not fixed here): a single tool call that itself
# runs longer than the emergency TTL, with a genuinely uncheckable owner and
# no OTHER tool call firing in between, is still theoretically stealable —
# this hook only ever runs between tool calls, never during one.
#
# Skip in non-interactive / pipeline contexts, matching every other
# thread-lease hook.

if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$LEARN_UKRAINIAN_PIPELINE" ] || [ -n "$GEMINI_SESSION" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
PYTHON="$PROJECT_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  # Fail open: never let a missing venv slow down or block a tool call.
  exit 0
fi

cd "$PROJECT_DIR" || exit 0

HANDOFF_AGENT="${SESSION_HANDOFF_AGENT:-claude}"
case "$HANDOFF_AGENT" in
  claude|claude-*) ;;
  *) exit 0 ;;
esac

STDIN_JSON=""
if [ ! -t 0 ]; then
  STDIN_JSON=$(cat)
fi
if [ -z "$STDIN_JSON" ]; then
  exit 0
fi

SESSION_ID=$(printf '%s' "$STDIN_JSON" | jq -r '.session_id // empty' 2>/dev/null)
if [ -z "$SESSION_ID" ]; then
  exit 0
fi

if [ -n "${CODEX_CANONICAL_REPO_ROOT:-}" ]; then
  CANONICAL_ROOT="$CODEX_CANONICAL_REPO_ROOT"
else
  GIT_COMMON_DIR=$(git -C "$PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
  if [ -n "$GIT_COMMON_DIR" ] && [ "$(basename "$GIT_COMMON_DIR")" = ".git" ]; then
    CANONICAL_ROOT=$(dirname "$GIT_COMMON_DIR")
  else
    CANONICAL_ROOT="$PROJECT_DIR"
  fi
fi

"$PYTHON" "$PROJECT_DIR/scripts/orchestration/thread_handoff.py" \
  --repo-root "$CANONICAL_ROOT" refresh-thread-lease-heartbeat \
  --agent "$HANDOFF_AGENT" --current-thread-id "$SESSION_ID" \
  --min-refresh-interval-seconds 60 \
  >/dev/null 2>&1 || true

exit 0
