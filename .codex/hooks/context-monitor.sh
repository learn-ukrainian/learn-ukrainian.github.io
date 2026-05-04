#!/bin/bash
# Hook: PostToolUse — monitors context size and warns Claude before auto-compact
# triggers, demanding a session handoff to docs/session-state/current.md instead.
#
# Tiers (% of autoCompactWindow):
#   75% -> heads-up: prepare handoff soon
#   85% -> critical: finish current task, write handoff, end session
#   95% -> emergency: stop now, write handoff this turn, /exit immediately
#
# Compaction is far more expensive than session handoff: handoff is just a
# small markdown file the next session reads on startup; compaction is a
# billed model call summarizing your entire conversation.
#
# Design adopted from kubedojo project (2026-04-14) with:
#   * divisor fixed to 7 chars/token (measured; JSON tool overhead heavier than prose)
#   * printf-based message bodies (robust vs heredoc-in-cmdsub paren issues)
#   * adapted paths to learn-ukrainian's docs/session-state/ convention
#   * autoCompactWindow default 1000000 to match this project's 1M-context variant

# Skip in non-interactive / subagent / pipeline contexts
if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$LEARN_UK_PIPELINE" ] || [ -n "$GEMINI_SESSION" ] || [ -n "$CODEX_SESSION" ]; then
  exit 0
fi

# Read hook input (JSON on stdin)
INPUT=$(cat)
SESSION_ID=$(printf '%s' "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
[ -z "$SESSION_ID" ] && exit 0

# Resolve project + transcript path
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
PROJECT_SLUG=$(printf '%s' "$PROJECT_DIR" | sed 's|/|-|g')
TRANSCRIPT="$HOME/.claude/projects/${PROJECT_SLUG}/${SESSION_ID}.jsonl"

[ ! -f "$TRANSCRIPT" ] && exit 0

# Estimate tokens from transcript size: ~7 chars/token for the jsonl transcript.
# JSON envelope + tool-call metadata pushes the ratio above the 4 chars/token
# that raw prose hits. Conservative (slight over-estimate on warnings is safe).
SIZE=$(wc -c < "$TRANSCRIPT" 2>/dev/null || echo 0)
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

[ "$WINDOW" -le 0 ] && exit 0
PCT=$((TOKENS * 100 / WINDOW))

# Build tiered message via printf to avoid heredoc-in-cmdsub paren issues
if [ "$PCT" -ge 95 ]; then
  MSG=$(printf '%s\n%s\n%s\n%s\n%s\n' \
    "EMERGENCY: Context at ${PCT}% of auto-compact window [~${TOKENS}/${WINDOW} tokens]. AUTO-COMPACT IS IMMINENT." \
    "" \
    "STOP all current work THIS TURN. Do not start any new tool calls beyond what is needed to:" \
    "1. Write or update docs/session-state/current.md NOW with: current HEAD SHA on main, branch, last 5 commit subjects, modified files, open GH issues touched this session, running background tasks [task-id + PID + output file], what was just completed, what is left to do, and the EXACT next-step commands the new session should run." \
    "2. Tell the user to /exit immediately and start a fresh session that reads docs/session-state/current.md first. Auto-compaction is a billed model call that summarizes your entire conversation: much more expensive than a 3KB handoff file the next session reads cheaply.")
elif [ "$PCT" -ge 85 ]; then
  MSG=$(printf '%s\n%s\n%s\n%s\n%s\n%s\n' \
    "CRITICAL: Context at ${PCT}% of auto-compact window [~${TOKENS}/${WINDOW} tokens]." \
    "" \
    "Finish your current task ASAP, then:" \
    "1. Write or update docs/session-state/current.md with HEAD SHA, branch, recent commits, modified files, open issues, in-flight tasks, next steps, restart commands." \
    "2. Tell the user to /exit and start fresh." \
    "Do NOT start any new multi-step work or large operations. Handoff is much cheaper than the auto-compact that is about to trigger.")
elif [ "$PCT" -ge 75 ]; then
  MSG=$(printf '%s\n%s\n%s\n' \
    "HEADS UP: Context at ${PCT}% of auto-compact window [~${TOKENS}/${WINDOW} tokens]." \
    "" \
    "Wrap up your current logical unit of work soon. Once it lands, prepare docs/session-state/current.md so we can hand off to a fresh session before auto-compact triggers. Handoff costs ~3KB; compaction costs a full model summarization call.")
else
  exit 0
fi

# Inject the warning back into Claude's context
jq -n --arg msg "$MSG" '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":$msg}}'
