#!/bin/bash
# Hook: PostToolUse — monitors context size and warns before auto-compact
# triggers, demanding a gitignored local thread handoff instead.
#
# Tiers (% of autoCompactWindow):
#   75% -> heads-up: prepare handoff soon
#   85% -> critical: finish current task, write handoff, end session
#   95% -> emergency: stop now, write handoff this turn, /exit immediately
#
# Compaction is far more expensive than session handoff: the local rollover
# packet is small and gitignored; compaction is a billed model call
# summarizing your entire conversation.
#
# Design adopted from kubedojo project (2026-04-14) with:
#   * divisor fixed to 7 chars/token (measured; JSON tool overhead heavier than prose)
#   * printf-based message bodies (robust vs heredoc-in-cmdsub paren issues)
#   * adapted paths to learn-ukrainian's gitignored .agent/ thread handoff
#   * autoCompactWindow default 1000000 to match this project's 1M-context variant

# Skip in non-interactive / subagent / pipeline contexts
if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$LEARN_UK_PIPELINE" ] || [ -n "$GEMINI_SESSION" ]; then
  exit 0
fi

# Read hook input (JSON on stdin)
INPUT=$(cat)
SESSION_ID=$(printf '%s' "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
[ -z "$SESSION_ID" ] && SESSION_ID="${CODEX_THREAD_ID:-}"
[ -z "$SESSION_ID" ] && exit 0

# Resolve project + transcript path
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
PROJECT_SLUG=$(printf '%s' "$PROJECT_DIR" | sed 's|/|-|g')
TRANSCRIPT="$HOME/.claude/projects/${PROJECT_SLUG}/${SESSION_ID}.jsonl"

if [ ! -f "$TRANSCRIPT" ]; then
  TRANSCRIPT=$(find "$HOME/.codex/sessions" -type f -name "*${SESSION_ID}.jsonl" 2>/dev/null | sort | tail -1)
fi

[ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ] && exit 0

# Estimate tokens from transcript size: ~7 chars/token for the jsonl transcript.
# JSON envelope + tool-call metadata pushes the ratio above the 4 chars/token
# that raw prose hits. Conservative (slight over-estimate on warnings is safe).
#
# CRITICAL: strip base64 blobs first. A browser screenshot is ~1MB of base64 in
# the transcript but only ~1.5K tokens to the model; counting its bytes inflates
# the estimate 2-3x (measured 2026-06-10: raw bytes/7 read 52-115% while the live
# context was a true 38% — the gap was entirely screenshot base64). Collapse any
# run of >=800 base64-charset chars (real text/JSON never has such a run) so the
# size reflects actual text tokens, not encoded image bytes.
SIZE=$(LC_ALL=C sed -E 's#[A-Za-z0-9+/]{800,}={0,2}#B64#g' "$TRANSCRIPT" 2>/dev/null | wc -c)
[ -z "$SIZE" ] && SIZE=0
TOKENS=$((SIZE / 7))

# Read autoCompactWindow from settings; default to 1M (this project's variant).
SETTINGS_FILE="$PROJECT_DIR/.claude/settings.json"
WINDOW=1000000
if [ -f "$SETTINGS_FILE" ]; then
  CONFIGURED=$(jq -r '.autoCompactWindow // empty' "$SETTINGS_FILE" 2>/dev/null)
  if [ -n "$CONFIGURED" ] && [ "$CONFIGURED" -gt 0 ] 2>/dev/null; then
    WINDOW=$CONFIGURED
  fi
fi
if [ -f "$HOME/.codex/config.toml" ]; then
  CONFIGURED=$(awk -F= '/^[[:space:]]*model_auto_compact_token_limit[[:space:]]*=/{gsub(/[[:space:]]/, "", $2); print $2; exit}' "$HOME/.codex/config.toml")
  if [ -n "$CONFIGURED" ] && [ "$CONFIGURED" -gt 0 ] 2>/dev/null; then
    WINDOW=$CONFIGURED
  fi
fi

[ "$WINDOW" -le 0 ] && exit 0
PCT=$((TOKENS * 100 / WINDOW))

if [ -n "${SESSION_HANDOFF_AGENT:-}" ]; then
    HANDOFF_AGENT="$SESSION_HANDOFF_AGENT"
elif [[ "${0:-}" == *"/.codex/"* ]]; then
    HANDOFF_AGENT="codex"
elif [[ "${0:-}" == *"/.gemini/"* ]]; then
    HANDOFF_AGENT="gemini"
elif [ -n "${CODEX_THREAD_ID:-}${CODEX_SESSION_ID:-}" ]; then
    HANDOFF_AGENT="codex"
else
    HANDOFF_AGENT="claude"
fi

PREPARE_CMD=".venv/bin/python scripts/orchestration/thread_handoff.py prepare --agent ${HANDOFF_AGENT} --context-percent ${PCT}"
BOOTSTRAP_FILE=".agent/${HANDOFF_AGENT}-thread-bootstrap.md"
HANDOFF_FILE=".agent/${HANDOFF_AGENT}-thread-handoff.md"

# Build tiered message via printf to avoid heredoc-in-cmdsub paren issues
if [ "$PCT" -ge 95 ]; then
  MSG=$(printf '%s\n%s\n%s\n%s\n%s\n%s\n' \
    "EMERGENCY: Context at ${PCT}% of auto-compact window [~${TOKENS}/${WINDOW} tokens]. AUTO-COMPACT IS IMMINENT." \
    "" \
    "STOP all current work THIS TURN. Do not start any new tool calls beyond what is needed to:" \
    "1. Run: ${PREPARE_CMD}. This writes only gitignored local files: ${HANDOFF_FILE}, ${BOOTSTRAP_FILE}, and .agent/${HANDOFF_AGENT}-thread-lease.json. Do NOT write docs/session-state/current.md or any git-tracked handoff file for rollover." \
    "2. If Codex thread-management tools are available, create/fork/send the continuation using ${BOOTSTRAP_FILE}. Otherwise tell the user to start a fresh thread with that bootstrap prompt." \
    "3. After the replacement thread is actually running, confirm it with: .venv/bin/python scripts/orchestration/thread_handoff.py confirm-started --agent ${HANDOFF_AGENT} --new-thread-id <replacement-thread-id>.")
elif [ "$PCT" -ge 85 ]; then
  MSG=$(printf '%s\n%s\n%s\n%s\n%s\n%s\n' \
    "CRITICAL: Context at ${PCT}% of auto-compact window [~${TOKENS}/${WINDOW} tokens]." \
    "" \
    "Finish your current task ASAP, then:" \
    "1. Run: ${PREPARE_CMD}. This writes only gitignored local files: ${HANDOFF_FILE}, ${BOOTSTRAP_FILE}, and .agent/${HANDOFF_AGENT}-thread-lease.json. Do NOT write docs/session-state/current.md or any git-tracked handoff file for rollover." \
    "2. Use Codex thread-management tools for continuation when available, or tell the user to start fresh with ${BOOTSTRAP_FILE}." \
    "Do NOT start any new multi-step work or large operations. Handoff is much cheaper than the auto-compact that is about to trigger.")
elif [ "$PCT" -ge 75 ]; then
  MSG=$(printf '%s\n%s\n%s\n' \
    "HEADS UP: Context at ${PCT}% of auto-compact window [~${TOKENS}/${WINDOW} tokens]." \
    "" \
    "Wrap up your current logical unit of work soon. For rollover, run ${PREPARE_CMD}; it writes gitignored .agent/ thread handoff files and must not dirty docs/session-state/current.md.")
else
  exit 0
fi

# Inject the warning back into Claude's context
jq -n --arg msg "$MSG" '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":$msg}}'
