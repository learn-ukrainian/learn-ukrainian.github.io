#!/bin/bash
# Hook: PostToolUse — throttled thread-lease heartbeat refresh (issue #5759).
#
# This is diagnostic, not a safety mechanism: claim_thread_lease never takes
# an uncheckable owner over on clock age at all (no emergency TTL exists
# anymore — see thread_handoff.py), so there is no steal window left for a
# fresh heartbeat to protect against. This hook exists only to keep
# heartbeat_at meaningful for operators inspecting a lease file, refreshing
# it far more often than the Stop hook (which only fires once per turn) by
# also firing on the much more frequent PostToolUse event.
#
# Throttled to stay cheap: refresh_thread_lease_heartbeat only rewrites the
# lease file when the existing heartbeat is already older than 60s, so the
# common case (many tool calls per minute) is a read, never a write. It is
# best-effort and never a takeover — a no-op for a lease this session does
# not already own, at a different generation, or whose process identity it
# cannot reconfirm, exactly like the Stop-hook refresh.
#
# Fenced by process identity, not generation: refresh_thread_lease_heartbeat
# re-derives this calling process's harness-ancestor pid/start time and
# requires it to match what the lease recorded (require_proof=True) before
# writing anything — a thread-id-only check could otherwise let a late
# predecessor heartbeat rewrite a successor's recorded process identity
# (issue #5759 round 2). This is strictly stronger than the old generation
# fence, and load-bearing: $CLAUDE_ENV_FILE exports (including
# LEARN_UKRAINIAN_THREAD_LEASE_GENERATION, set by session-setup.sh) reach
# only Bash tool calls, never this hook's own subprocess, so a generation
# gate here was silently dead code in every real session — this hook no
# longer requires one at all, only current-thread-id.
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

# No --generation: identity proof is the sole fence (see above). If this repo
# checkout still has an OLDER thread_handoff.py that hard-requires
# --generation, the CLI's argparse error is swallowed by `|| true` below —
# a safe no-op in a mixed-deploy, exactly like the old missing-env-var path.
"$PYTHON" "$PROJECT_DIR/scripts/orchestration/thread_handoff.py" \
  --repo-root "$CANONICAL_ROOT" refresh-thread-lease-heartbeat \
  --agent "$HANDOFF_AGENT" --current-thread-id "$SESSION_ID" \
  --min-refresh-interval-seconds 60 \
  >/dev/null 2>&1 || true

exit 0
