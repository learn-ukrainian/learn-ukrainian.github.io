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
# Fenced by process identity, not generation: release_thread_lease re-derives
# this calling process's harness-ancestor pid/start time and requires it to
# match what the lease recorded (require_proof=True) before releasing
# anything — this is the fence that makes the previous paragraph true, and it
# is strictly stronger than a caller-supplied generation. This used to
# require --generation (exported by session-setup.sh into $CLAUDE_ENV_FILE as
# LEARN_UKRAINIAN_THREAD_LEASE_GENERATION), but that export reaches only Bash
# tool calls, never this hook's own subprocess, so the generation gate was
# silently dead code in every real session — every SessionEnd release
# no-oped, which is exactly how a 4h-ended session was still able to lock out
# its successor. This hook no longer requires a generation at all.
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

# NO generation is carried here — deliberately (formal CF F001 round 3 on
# #5896): a sidecar keyed only by SESSION_ID is MUTABLE across a same-id
# resume, so a delayed SessionEnd from a dead predecessor could read the
# SUCCESSOR's generation and tombstone the successor's live lease — defeating
# the exact ABA protection the generation fence exists for. Identity proof is
# the sole fence on this path: release no-ops when the process identity cannot
# be reconfirmed, and claim_thread_lease's pid-liveness check reclaims any
# stale lease that leaves behind. If a repo checkout still has an OLDER
# thread_handoff.py that hard-requires --generation, the CLI error is
# swallowed by `|| true` — a safe no-op in a mixed deploy.
"$PYTHON" "$PROJECT_DIR/scripts/orchestration/thread_handoff.py" --repo-root "$CANONICAL_ROOT" \
  release-thread-lease --agent "$HANDOFF_AGENT" --current-thread-id "$SESSION_ID" \
  >/dev/null 2>&1 || true

exit 0
