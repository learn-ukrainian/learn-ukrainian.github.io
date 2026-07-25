#!/bin/bash
# Hook: SessionEnd — best-effort release of this session's durable thread lease.
#
# session-setup.sh claims a single-writer lease per agent slot at SessionStart
# so two driver sessions can never double-drive the same queue. Historically
# there was no release path at all: an exited or crashed session held the
# slot until its heartbeat aged past a fixed clock window, which is exactly
# the operator-restart lockout this lease exists to prevent from recurring in
# the *other* direction.
#
# This hook is the fast, cooperative release path. It is intentionally
# best-effort: SessionEnd does not fire on SIGKILL or a hard crash, so the
# owner-pid liveness check in claim_thread_lease (scripts/orchestration/
# thread_handoff.py) remains the primary mechanism. Release is a no-op unless
# this exact session id still owns the lease, so a hook that fires late (or
# fires after another session has already taken the lease over) can never
# clobber a newer owner's lease.
#
# Generation is REQUIRED for a non-force release (thread_handoff.py raises
# without it) — it is the fence that makes the previous paragraph true. The
# generation this session actually claimed at SessionStart is exported by
# session-setup.sh into $CLAUDE_ENV_FILE as LEARN_UKRAINIAN_THREAD_LEASE_GENERATION;
# without it we cannot safely release (a missing/wrong generation could only
# ever match by accident), so this hook no-ops rather than guessing one.
#
# Skip in non-interactive / pipeline contexts, matching session-setup.sh.

if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$LEARN_UKRAINIAN_PIPELINE" ] || [ -n "$GEMINI_SESSION" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
PYTHON="$PROJECT_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  # Fail open: never let a missing venv block SessionEnd.
  exit 0
fi

cd "$PROJECT_DIR" || exit 0

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

HANDOFF_AGENT="${SESSION_HANDOFF_AGENT:-claude}"
case "$HANDOFF_AGENT" in
  claude|claude-*) ;;
  *) exit 0 ;;
esac

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

if [ -z "${LEARN_UKRAINIAN_THREAD_LEASE_GENERATION:-}" ]; then
  # No generation to fence with — release-thread-lease.py now refuses a non-force
  # release without one. Leaving the lease in place is safe: claim_thread_lease's
  # pid-liveness check is the primary defense and will reclaim it once this
  # process is confirmed dead, regardless of this cooperative path.
  exit 0
fi

"$PYTHON" "$PROJECT_DIR/scripts/orchestration/thread_handoff.py" --repo-root "$CANONICAL_ROOT" \
  release-thread-lease --agent "$HANDOFF_AGENT" --current-thread-id "$SESSION_ID" \
  --generation "$LEARN_UKRAINIAN_THREAD_LEASE_GENERATION" \
  >/dev/null 2>&1 || true

exit 0
