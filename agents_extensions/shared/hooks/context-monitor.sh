#!/bin/bash
# Hook: PostToolUse — warn at the active session profile's rollover tiers.
#
# The official hook session/transcript identity and canonical session record are
# authoritative. Latest assistant input/cache usage is preferred; transcript
# size is a compatibility estimate only. Unknown capacity suppresses percentage
# warnings rather than fabricating a 1M or auto-compaction denominator.
# A profile with rollover_mode operator_restart gets hand-off-and-wait texts at
# its critical and final tiers instead of the continuation texts (#8511).

# Native Codex owns context compaction. A PostToolUse warning is injected as
# higher-priority context, so imperative rollover text can trap the agent:
# every tool call re-injects STOP, while the suggested `prepare` command is not
# repeatable once a pending lease exists. Keep this manual rollover hook silent
# for Codex; its native runtime remains responsible for compaction/continuation.
if [ "${SESSION_HANDOFF_AGENT:-}" = "codex" ] \
  || [[ "${0:-}" == *"/.codex/"* ]] \
  || [ -n "${CODEX_THREAD_ID:-}${CODEX_SESSION_ID:-}" ]; then
  exit 0
fi

# Skip in non-interactive / subagent / pipeline contexts.
if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$LEARN_UK_PIPELINE" ] || [ -n "$GEMINI_SESSION" ]; then
  exit 0
fi

# Grok TUI: Claude PostToolUse context-monitor is high-frequency noise and was
# never designed for Grok compaction (hook audit 2026-08-06). Skip unless
# explicitly re-enabled.
if [ -n "${GROK_AGENT:-}" ] || [ "${SESSION_HANDOFF_AGENT:-}" = "grok" ] \
  || [ "${SESSION_HANDOFF_AGENT:-}" = "grok-build" ]; then
  if [ "${GROK_CONTEXT_MONITOR:-}" != "1" ]; then
    exit 0
  fi
fi

command -v jq >/dev/null 2>&1 || exit 0
# shellcheck source=agents_extensions/shared/hooks/context-rollover-lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/context-rollover-lib.sh" 2>/dev/null || exit 0

INPUT=$(cat)
SESSION_ID=$(printf '%s' "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
[ -z "$SESSION_ID" ] && SESSION_ID="${LEARN_UKRAINIAN_SESSION_ID:-${CODEX_THREAD_ID:-}}"
[ -z "$SESSION_ID" ] && exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
TRANSCRIPT=$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
[ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ] && exit 0

# Prefer the latest assistant input/cache usage. Output tokens are not current
# context usage and therefore are deliberately excluded.
USAGE_SOURCE="transcript-size estimate"
TOKENS=$(context_latest_usage_tokens "$TRANSCRIPT")
case "$TOKENS" in ''|*[!0-9]*) TOKENS=0 ;; esac
[ "$TOKENS" -gt 0 ] && USAGE_SOURCE="latest assistant input/cache usage"
if [ "$TOKENS" -le 0 ]; then
  RAW_SIZE=$(LC_ALL=C wc -c < "$TRANSCRIPT" 2>/dev/null) || RAW_SIZE=0
  B64_EXCESS=$(LC_ALL=C tr -cs 'A-Za-z0-9+/=' '\n' < "$TRANSCRIPT" 2>/dev/null \
    | LC_ALL=C awk 'length($0) >= 800 { removed += length($0) - 3 } END { print removed + 0 }')
  [ -z "$B64_EXCESS" ] && B64_EXCESS=0
  SIZE=$((RAW_SIZE - B64_EXCESS))
  [ "$SIZE" -lt 0 ] && SIZE=0
  TOKENS=$((SIZE / 7))
fi
[ "$TOKENS" -le 0 ] && exit 0

WINDOW=""
WINDOW_PROVENANCE="unavailable"
WARNING_TIERS=""
ROLLOVER_MODE=""
# The session record is plain JSON at <canonical>/.agent/sessions/<id>.json —
# read it with jq directly instead of spawning a ~130 ms interpreter on
# EVERY tool call (PR #6413 finding #3). This also fixes worktree sessions,
# where the old $PROJECT_DIR/.venv interpreter check silently disabled the monitor
# (linked worktrees carry no venv — F001 r5 class).
RECORD_FILE=$(context_session_record_file "$PROJECT_DIR" "$SESSION_ID")
if [ -f "$RECORD_FILE" ] && [ ! -L "$RECORD_FILE" ]; then
  RECORD_ROW=$(jq -r '
    [ (.actual_context_window_tokens // "" | tostring),
      (.actual_context_window_provenance // "unavailable"),
      (.rollover_warning_percentages | if type == "array" and length == 3 then join(" ") else "" end),
      (.rollover_mode // "")
    ] | join("\u0001")' "$RECORD_FILE" 2>/dev/null || true)
  if [ -n "$RECORD_ROW" ]; then
    IFS=$'\001' read -r WINDOW WINDOW_PROVENANCE WARNING_TIERS ROLLOVER_MODE <<< "$RECORD_ROW"
  fi
  unset RECORD_ROW
fi

# Compatibility fallback before SessionStart has written a record: only an
# explicitly trusted route may supply a denominator and warning policy.
WINDOW_VALID=1
case "$WINDOW" in
  ""|*[!0-9]*) WINDOW_VALID=0 ;;
  *) [ "$WINDOW" -gt 0 ] || WINDOW_VALID=0 ;;
esac
if [ "$WINDOW_VALID" -eq 0 ]; then
  # Project root is selected at runtime.
  # shellcheck disable=SC1091
  source "$PROJECT_DIR/scripts/lib/profile_resolver.sh" 2>/dev/null || exit 0
  if ! resolve_context_profile \
    "${LEARN_UKRAINIAN_REQUESTED_PROFILE_ID:-${LEARN_UKRAINIAN_PROFILE_ID:-}}" \
    "${LEARN_UKRAINIAN_OBSERVED_MODEL_ID:-${LEARN_UKRAINIAN_MAIN_MODEL_ID:-}}" \
    >/dev/null 2>&1; then
    exit 0
  fi
  [ "${LEARN_UKRAINIAN_TRUSTED:-0}" = "1" ] || exit 0
  WINDOW="${LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS:-}"
  WINDOW_PROVENANCE="declared-profile"
  WARNING_TIERS="${LEARN_UKRAINIAN_ROLLOVER_WARNING_PERCENTAGES:-}"
  ROLLOVER_MODE="${LEARN_UKRAINIAN_ROLLOVER_MODE:-}"
fi
ROLLOVER_MODE=$(context_effective_rollover_mode "$ROLLOVER_MODE")

case "$WINDOW" in
  ""|*[!0-9]*) exit 0 ;;
esac
[ "$WINDOW" -gt 0 ] || exit 0
read -r TIER1_RAW TIER2_RAW TIER3_RAW <<< "$WARNING_TIERS"
[ -n "$TIER1_RAW" ] && [ -n "$TIER2_RAW" ] && [ -n "$TIER3_RAW" ] || exit 0
TIER1_PCT=$(printf '%.0f' "$TIER1_RAW" 2>/dev/null) || exit 0
TIER2_PCT=$(printf '%.0f' "$TIER2_RAW" 2>/dev/null) || exit 0
TIER3_PCT=$(printf '%.0f' "$TIER3_RAW" 2>/dev/null) || exit 0
PCT=$((TOKENS * 100 / WINDOW))

if [ -n "${SESSION_HANDOFF_AGENT:-}" ]; then
  HANDOFF_AGENT="$SESSION_HANDOFF_AGENT"
elif [[ "${0:-}" == *"/.gemini/"* ]]; then
  HANDOFF_AGENT="gemini"
else
  HANDOFF_AGENT="claude"
fi

HANDOFF_IDENTITY_SH="${CLAUDE_HANDOFF_IDENTITY_SH:-$PROJECT_DIR/scripts/lib/handoff_identity.sh}"
if [ -f "$HANDOFF_IDENTITY_SH" ]; then
  # shellcheck disable=SC1090
  source "$HANDOFF_IDENTITY_SH"
fi
ROLLOVER_STREAM=""
ROLLOVER_STREAM_EPIC=""
if [ -n "${SESSION_EPIC:-}" ] && declare -f launcher_selector_stream >/dev/null 2>&1; then
  ROLLOVER_STREAM="$(launcher_selector_stream "$SESSION_EPIC" 2>/dev/null || true)"
  case "$ROLLOVER_STREAM" in
    epic:*) ROLLOVER_STREAM_EPIC="${ROLLOVER_STREAM#epic:}" ;;
    *) ROLLOVER_STREAM=""; ROLLOVER_STREAM_EPIC="" ;;
  esac
fi
PREPARE_CMD=".venv/bin/python scripts/orchestration/thread_handoff.py prepare --agent ${HANDOFF_AGENT} --context-percent ${PCT}"
[ -n "$ROLLOVER_STREAM" ] && PREPARE_CMD="$PREPARE_CMD --stream $ROLLOVER_STREAM --stream-epic $ROLLOVER_STREAM_EPIC"
unset HANDOFF_IDENTITY_SH ROLLOVER_STREAM ROLLOVER_STREAM_EPIC
BOOTSTRAP_FILE=".agent/${HANDOFF_AGENT}-thread-bootstrap.md"
HANDOFF_FILE=".agent/${HANDOFF_AGENT}-thread-handoff.md"
CONTEXT_FACT="${PCT}% of the ${WINDOW}-token context window [~${TOKENS}/${WINDOW}; ${USAGE_SOURCE}; capacity: ${WINDOW_PROVENANCE}]"

# Announce each tier once per session, the first time it is crossed. Re-injecting
# the same rollover instruction on every tool call is the trap the Codex/Grok
# guards above describe, and a running context-budget countdown makes the model
# wrap up early (claude-api skill, model-migration.md -> Claude Fable 5.1
# "context anxiety"). Tiers are monotonic: a usage estimate that dips and rises
# around a boundary does not re-announce. Only a compaction-scale drop - usage
# below 60% of the level at the last announcement - re-arms the tiers, so a fresh
# climb after compaction is announced again. State lives in gitignored runtime
# storage as "<tier> <tokens>".
TIER_STATE_DIR="$PROJECT_DIR/batch_state/context_monitor"
TIER_STATE_FILE="$TIER_STATE_DIR/${SESSION_ID}.tier"
LAST_TIER=0
LAST_TOKENS=0
if [ -f "$TIER_STATE_FILE" ]; then
  read -r LAST_TIER LAST_TOKENS < "$TIER_STATE_FILE" 2>/dev/null || true
fi
case "$LAST_TIER" in ''|*[!0-9]*) LAST_TIER=0 ;; esac
case "$LAST_TOKENS" in ''|*[!0-9]*) LAST_TOKENS=0 ;; esac
if [ "$LAST_TIER" -gt 0 ] && [ $((TOKENS * 100)) -lt $((LAST_TOKENS * 60)) ]; then
  rm -f "$TIER_STATE_FILE" 2>/dev/null
  LAST_TIER=0
  LAST_TOKENS=0
fi
if [ "$PCT" -ge "$TIER3_PCT" ]; then TIER=3
elif [ "$PCT" -ge "$TIER2_PCT" ]; then TIER=2
elif [ "$PCT" -ge "$TIER1_PCT" ]; then TIER=1
else TIER=0
fi
[ "$TIER" -gt "$LAST_TIER" ] || exit 0
mkdir -p "$TIER_STATE_DIR" 2>/dev/null && printf '%s %s\n' "$TIER" "$TOKENS" > "$TIER_STATE_FILE" 2>/dev/null

# operator_restart (#8511): the session never continues itself. It hands off,
# tells the operator it is ready for a restart, and waits; context-rollover-guard.sh
# reminds on later prompts and blocks automatic compaction.
RESTART_HINT=""
[ -n "${SESSION_EPIC:-}" ] && RESTART_HINT=" (./start-claude-driver.sh --epic ${SESSION_EPIC})"
if [ "$ROLLOVER_MODE" = "operator_restart" ] && [ "$PCT" -ge "$TIER3_PCT" ]; then
  MSG=$(printf '%s\n%s\n%s\n%s\n%s\n%s\n%s\n' \
    "EMERGENCY: Context is at ${CONTEXT_FACT}. The profile's final rollover tier is ${TIER3_PCT}%: this session hands off and waits for the operator to restart it." \
    "" \
    "STOP all current work THIS TURN. Do not dispatch, start new work, or start a continuation thread. Only:" \
    "1. Refresh your lane handoff file with current state, in-flight work, and next steps." \
    "2. Follow the thread-rollover skill's prepare phase (references/prepare.md): run ${PREPARE_CMD}. This writes the gitignored rollover lease plus ${HANDOFF_FILE} and ${BOOTSTRAP_FILE}." \
    "3. Tell the operator in one plain message that the handoff is ready and they should restart this session${RESTART_HINT}." \
    "4. END THE TURN and wait. Automatic compaction is blocked for this session; the restart replaces it.")
elif [ "$ROLLOVER_MODE" = "operator_restart" ] && [ "$PCT" -ge "$TIER2_PCT" ]; then
  MSG=$(printf '%s\n%s\n%s\n%s\n' \
    "CRITICAL: Context is at ${CONTEXT_FACT}. The profile's critical rollover tier is ${TIER2_PCT}%." \
    "" \
    "Finish the current logical unit. Do not start new multi-step work, dispatches, or large operations." \
    "At ${TIER3_PCT}% this session refreshes its handoff, prepares the rollover (${PREPARE_CMD}), tells the operator it is ready for a restart, and waits.")
elif [ "$PCT" -ge "$TIER3_PCT" ]; then
  MSG=$(printf '%s\n%s\n%s\n%s\n%s\n%s\n' \
    "EMERGENCY: Context is at ${CONTEXT_FACT}. The profile's final rollover tier is ${TIER3_PCT}%." \
    "" \
    "STOP all current work THIS TURN. Do not start new tool calls beyond what is needed to:" \
    "1. Run: ${PREPARE_CMD}. This writes the gitignored rollover lease plus ${HANDOFF_FILE} and ${BOOTSTRAP_FILE}." \
    "2. Start the supported continuation for this harness, or tell the user to start a fresh thread with ${BOOTSTRAP_FILE}." \
    "3. Confirm the replacement only after it is actually running; do not delete the prepared lease early.")
elif [ "$PCT" -ge "$TIER2_PCT" ]; then
  MSG=$(printf '%s\n%s\n%s\n%s\n%s\n%s\n' \
    "CRITICAL: Context is at ${CONTEXT_FACT}. The profile's critical rollover tier is ${TIER2_PCT}%." \
    "" \
    "Finish the current logical unit, then:" \
    "1. Run: ${PREPARE_CMD}. This writes only gitignored rollover state and handoff files." \
    "2. Start the supported continuation for this harness, or use ${BOOTSTRAP_FILE} in a fresh thread." \
    "Do not start new multi-step work or large operations before rollover.")
elif [ "$PCT" -ge "$TIER1_PCT" ]; then
  MSG=$(printf '%s\n%s\n%s\n' \
    "HEADS UP: Context is at ${CONTEXT_FACT}. The profile's first rollover tier is ${TIER1_PCT}%." \
    "" \
    "Wrap up the current logical unit soon. For rollover, run ${PREPARE_CMD}; it writes gitignored .agent/ handoff state.")
else
  exit 0
fi

jq -n --arg msg "$MSG" '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":$msg}}'
