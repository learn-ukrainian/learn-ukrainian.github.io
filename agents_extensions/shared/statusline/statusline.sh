#!/usr/bin/env bash
# Claude Code statusline — learn-ukrainian project.
#
# Reads Claude Code status JSON from stdin and renders:
#   [MODEL] [acct: A|B|?] [ctx: UK/BK (N%)] cwd-basename [wt:worktree-name] (branch*)
#   [effort: level] [think] [5h: N% left] [7d: N% left] [$cost]
#
# Segments:
#   [MODEL]        .model.display_name, omitted if missing
#   [acct: A|B|?]  Claude account, from the basename of $CLAUDE_CONFIG_DIR only
#                    (the directory is never read): unset/empty or `.claude`
#                    is A, `.claude-b` is B, anything else is `?` (never
#                    guessed, the path is never printed). Placed right after
#                    MODEL.
#   [ctx: UK/BK (N%)] context window — placed immediately after MODEL so
#                    usage is the first thing visible on the line. Bold +
#                    color-coded: green<50, yellow 50-79, red 80+.
#                    U=used Ktokens, B=budget Ktokens, N=percent used.
#                    Used tokens prefer official Claude Code fields:
#                      1) .context_window.total_input_tokens;
#                      2) input/cache fields inside .context_window.current_usage;
#                      3) legacy direct token keys;
#                      4) latest assistant input/cache usage from transcript JSONL.
#                    Output tokens are never added to current-context usage.
#                    Capacity prefers .context_window.context_window_size, then
#                    the canonical per-session record. There is no universal 1M
#                    or auto-compaction fallback; unknown capacity stays hidden.
#   cwd-basename   basename(.workspace.current_dir), pwd fallback
#   [wt:...]       basename(.workspace.git_worktree), omitted if not in a worktree
#   (branch*)      git branch (--no-optional-locks, subsecond) + `*` if dirty
#   [effort: ...]  .effort.level — low/medium default, high/xhigh bold,
#                    max red. Omitted for pre-2.1.119 clients.
#   [think]        .thinking.enabled — emitted only when true. Omitted for
#                    pre-2.1.119 clients.
#   [5h: N% left]  room left in the 5-hour subscription window: 100 minus
#                    .rate_limits.five_hour.used_percentage, rounded and
#                    clamped to 0-100. Shown when the field is a number;
#                    otherwise the capacity file below supplies it (known
#                    account only); omitted if neither does. Colour by
#                    remaining room: under 20 red, under 40 yellow,
#                    otherwise default.
#   [7d: N% left]  same for .rate_limits.seven_day.used_percentage (weekly).
#   [$cost]        .cost.total_cost_usd, formatted to 2 decimals, shown only
#                    when the input JSON provides the field. Kept last/low-
#                    emphasis: for Claude Max subscribers the 5h/7d rate-limit
#                    windows above remain the actionable subscription signal;
#                    this is supplementary session telemetry, shown whenever
#                    the schema includes it and dropped silently otherwise.
#
# Capacity file (optional fallback for the 5h/7d segments):
#   Set LU_STATUSLINE_CAPACITY_FILE to a capacity-history path (never
#   committed, never printed). JSON Lines, one object per row:
#     {"account": "a", "five_hour_left_pct": 62, "seven_day_left_pct": 35}
#   account            "a" or "b", case-insensitive; a "claude:" prefix is
#                      accepted ("claude:b").
#   five_hour_left_pct / seven_day_left_pct
#                      numbers 0..100 (percent LEFT); either may be absent.
#   The LAST row whose account matches this session's account supplies any
#   window Claude Code's own rate_limits did not; Claude Code's field always
#   wins. Only the last 64 KiB of the file is read (`tail -c`), so a long
#   history is cheap and a row cut by the window is ignored. A missing
#   variable/file, unreadable file, malformed row, or a non-numeric or
#   out-of-range value shows nothing for that window (no error, no clamping).
#   Not used when the account is `?`. No network.
#
# Schema reference: https://code.claude.com/docs/en/statusline.md
#
# Graceful degradation:
#   - If `jq` is not installed, script exits silently (empty status line).
#   - Any missing / null JSON field is dropped from output silently.
#   - Claude Code <2.1.119 does not provide effort/thinking fields; those
#     segments are omitted silently.
#   - If any git op fails, branch segment is omitted.
#
# Design notes:
#   - ANSI escapes use printf '%b' at render time so terminals that don't
#     support color still render the text (codes just show as literals in
#     the rare case the terminal is truly ancient — acceptable fallback).
#   - Script is intentionally cheap: no network, no external state beyond the
#     optional capacity-file tail, only `git` + `jq` + `printf` (+ `tail`). Statusline fires on every event.
#
# Debug: uncomment the tee line below to capture incoming JSON at
#        /tmp/.statusline-input.json for schema inspection.

set -u

command -v jq >/dev/null 2>&1 || exit 0

# Deployed statuslines have sibling hooks; the Gemini source overlay shares them.
context_lib="$(dirname "${BASH_SOURCE[0]}")/../hooks/context-rollover-lib.sh"
[ -f "$context_lib" ] || context_lib="$(dirname "${BASH_SOURCE[0]}")/../../shared/hooks/context-rollover-lib.sh"
# shellcheck disable=SC1090
source "$context_lib" 2>/dev/null || exit 0

input=$(</dev/stdin)
# printf '%s' "$input" > /tmp/.statusline-input.json  # debug

json_get() {
  printf '%s' "$input" | jq -r "$1 // empty" 2>/dev/null
}

# ── Segments ────────────────────────────────────────────────────

model=$(json_get '.model.display_name')

cwd=$(json_get '.workspace.current_dir')
[ -z "$cwd" ] && cwd=$(json_get '.cwd')
[ -z "$cwd" ] && cwd=$(pwd)
cwd_name=$(basename "$cwd")

worktree=$(json_get '.workspace.git_worktree')
wt_seg=""
[ -n "$worktree" ] && wt_seg="[wt:$(basename "$worktree")]"

# Branch + dirty marker.
# --no-optional-locks: never blocks on / contends for the repo lock, since
# the statusline fires on every event and must stay subsecond regardless of
# what other git operations (hooks, other agents) are doing concurrently.
branch_seg=""
if git --no-optional-locks -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch=$(git --no-optional-locks -C "$cwd" symbolic-ref --quiet --short HEAD 2>/dev/null \
           || git --no-optional-locks -C "$cwd" rev-parse --short HEAD 2>/dev/null \
           || true)
  dirty=""
  [ -n "$(git --no-optional-locks -C "$cwd" status --porcelain 2>/dev/null)" ] && dirty="*"
  [ -n "$branch" ] && branch_seg="($branch$dirty)"
fi

# Official Claude Code identity and context fields.
session_id=$(json_get '.session_id')
transcript_path=$(json_get '.transcript_path')
observed_model_id=$(json_get '.model.id')
observed_window=$(json_get '.context_window.context_window_size')
ctx_budget="$observed_window"
ctx_used=$(json_get '.context_window.total_input_tokens')
if [ -z "$ctx_used" ]; then
  usage_json=$(json_get '.context_window.current_usage | select(type == "object")')
  if [ -n "$usage_json" ]; then
    ctx_used=$(context_latest_usage_tokens "" "$usage_json")
    [ "$ctx_used" = "0" ] && ctx_used=""
  fi
fi

is_positive_integer() {
  case "${1:-}" in
    ""|*[!0-9]*) return 1 ;;
    *) [ "$1" -gt 0 ] ;;
  esac
}

# Locate the checkout containing the canonical session-record helper. The helper
# itself resolves linked worktrees back to the primary checkout's private state.
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$cwd}"
if [ ! -f "$PROJECT_DIR/scripts/lib/session_record.py" ]; then
  PROJECT_DIR=$(git --no-optional-locks -C "$cwd" rev-parse --show-toplevel 2>/dev/null || printf '%s' "$cwd")
fi
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
SESSION_RECORD="$PROJECT_DIR/scripts/lib/session_record.py"
record_json=""
if [ -n "$session_id" ] && [ -x "$PYTHON_BIN" ] && [ -f "$SESSION_RECORD" ]; then
  record_json=$("$PYTHON_BIN" "$SESSION_RECORD" get --session-id "$session_id" 2>/dev/null || true)

  # Persist only changed official observations. This makes the record the shared
  # denominator for hooks and Monitor telemetry without rewriting it per event.
  stored_model=$(printf '%s' "$record_json" | jq -r '.observed_model_id // empty' 2>/dev/null)
  stored_window=$(printf '%s' "$record_json" | jq -r '.observed_context_window_tokens // empty' 2>/dev/null)
  stored_transcript=$(printf '%s' "$record_json" | jq -r '.transcript_path // empty' 2>/dev/null)
  update_args=(update --session-id "$session_id" --provenance statusline)
  update_needed=0
  if [ -n "$observed_model_id" ] && [ "$observed_model_id" != "$stored_model" ]; then
    update_args+=(--observed-model "$observed_model_id" --observed-model-provenance statusline.model.id)
    update_needed=1
  fi
  if is_positive_integer "$observed_window" && [ "$observed_window" != "$stored_window" ]; then
    update_args+=(--observed-context-window "$observed_window" --observed-context-window-provenance statusline.context_window.context_window_size)
    update_needed=1
  fi
  if [ -n "$transcript_path" ] && [ "${transcript_path#/}" != "$transcript_path" ] \
     && [ "$transcript_path" != "$stored_transcript" ]; then
    update_args+=(--transcript-path "$transcript_path" --transcript-path-provenance statusline.transcript_path)
    update_needed=1
  fi
  if [ "$update_needed" -eq 1 ]; then
    if [ -z "$record_json" ] && [ -n "${LEARN_UKRAINIAN_REQUESTED_PROFILE_ID:-}" ]; then
      update_args+=(--profile-id "$LEARN_UKRAINIAN_REQUESTED_PROFILE_ID")
    fi
    "$PYTHON_BIN" "$SESSION_RECORD" "${update_args[@]}" >/dev/null 2>&1 || true
    record_json=$("$PYTHON_BIN" "$SESSION_RECORD" get --session-id "$session_id" 2>/dev/null || true)
  fi
fi

declared_model=$(printf '%s' "$record_json" | jq -r '.expected_model_id // .effective_model_id // empty' 2>/dev/null)
declared_window=$(printf '%s' "$record_json" | jq -r '.expected_context_window_tokens // .effective_context_window_tokens // empty' 2>/dev/null)
actual_window=$(printf '%s' "$record_json" | jq -r '.actual_context_window_tokens // empty' 2>/dev/null)
model_mismatch=$(printf '%s' "$record_json" | jq -r '.model_mismatch // false' 2>/dev/null)
window_mismatch=$(printf '%s' "$record_json" | jq -r '.window_mismatch // false' 2>/dev/null)
[ -z "$ctx_budget" ] && ctx_budget="$actual_window"
[ -z "$observed_model_id" ] && observed_model_id=$(printf '%s' "$record_json" | jq -r '.observed_model_id // .effective_model_id // empty' 2>/dev/null)

mismatch_seg=""
if [ "$model_mismatch" = "true" ]; then
  mismatch_seg="\033[31m[MISMATCH MODEL: ${observed_model_id:-unknown} vs ${declared_model:-unknown}]\033[0m"
fi
if [ "$window_mismatch" = "true" ]; then
  mismatch_seg="${mismatch_seg:+$mismatch_seg }\033[31m[MISMATCH WINDOW: ${ctx_budget:-unknown} vs ${declared_window:-unknown}]\033[0m"
fi

ctx_seg=""
ctx_pct=$(json_get '.context_window.used_percentage')

# Compatibility fallbacks for older Claude Code clients.
[ -z "$ctx_used" ] && ctx_used=$(json_get '.context_window.used_tokens')
[ -z "$ctx_used" ] && ctx_used=$(json_get '.context_window.input_tokens')
[ -z "$ctx_used" ] && ctx_used=$(json_get '.context_window.tokens.used')
if [ -z "$ctx_used" ] && [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
  ctx_used=$(context_latest_usage_tokens "$transcript_path")
  [ "$ctx_used" = "0" ] && ctx_used=""
fi

# Compute a percentage only when both values are trustworthy positive integers.
if [ -z "$ctx_pct" ] && is_positive_integer "$ctx_used" && is_positive_integer "$ctx_budget"; then
  ctx_pct=$(( ctx_used * 100 / ctx_budget ))
fi

if [ -n "$ctx_pct" ]; then
  ctx_int=$(printf '%.0f' "$ctx_pct" 2>/dev/null) || ctx_int=""
  if [ -n "$ctx_int" ]; then
    if   [ "$ctx_int" -ge 80 ]; then ctx_color="\033[1;31m"   # red, bold
    elif [ "$ctx_int" -ge 50 ]; then ctx_color="\033[1;33m"   # yellow, bold
    else                             ctx_color="\033[1;32m"   # green, bold
    fi
    if is_positive_integer "$ctx_used" && is_positive_integer "$ctx_budget"; then
      ctx_used_k=$(( (ctx_used + 500) / 1000 ))
      ctx_budget_k=$(( (ctx_budget + 500) / 1000 ))
      ctx_seg="${ctx_color}[ctx: ${ctx_used_k}K/${ctx_budget_k}K (${ctx_int}%)]\033[0m"
    else
      ctx_seg="${ctx_color}[ctx: ${ctx_int}%]\033[0m"
    fi
  fi
fi

# Execution mode segment
mode_seg=""
mode=$(json_get '.mode // .execution_mode // .agent_mode // .task_mode')
if [ -n "$mode" ]; then
  case "$mode" in
    plan)         mode_seg="\033[1;33m[mode: ${mode}]\033[0m" ;;
    accept-edits) mode_seg="\033[1;32m[mode: ${mode}]\033[0m" ;;
    *)            mode_seg="[mode: ${mode}]" ;;
  esac
fi

# ── Steps & Compactions Telemetry ─────────────────────────────
steps_seg=""
compacts_seg=""
handoff_seg=""
steps_count=0
compacts_count=0

# Fallback transcript resolution for AGY / Antigravity CLI / Claude Code paths
if [ -n "$transcript_path" ] && [ ! -f "$transcript_path" ]; then
  alt_path=$(printf '%s' "$transcript_path" | sed 's#/\.gemini/antigravity/#/.gemini/antigravity-cli/#')
  [ -f "$alt_path" ] && transcript_path="$alt_path"
fi
if [ -z "$transcript_path" ] || [ ! -f "$transcript_path" ]; then
  if [ -n "$session_id" ]; then
    for cand in \
      "$HOME/.gemini/antigravity-cli/brain/$session_id/.system_generated/logs/transcript.jsonl" \
      "$HOME/.gemini/antigravity/brain/$session_id/.system_generated/logs/transcript.jsonl" \
      "$HOME/.claude/transcripts/$session_id.jsonl"; do
      if [ -f "$cand" ]; then
        transcript_path="$cand"
        break
      fi
    done
  fi
fi

if [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
  steps_count=$(wc -l < "$transcript_path" 2>/dev/null | tr -d ' ')
  if is_positive_integer "$steps_count"; then
    steps_seg="[steps: ${steps_count}]"
  else
    steps_count=0
  fi

  strict_compacts=$(jq -r 'select(.type == "compact" or .type == "COMPACT" or .type == "CONTEXT_COMPACT" or .subtype == "compact" or (.type == "SYSTEM_MESSAGE" and (.content | type == "string") and (.content | test("history compacted|context window compacted|auto-compacted"; "i")))) | .type' "$transcript_path" 2>/dev/null | wc -l | tr -d ' ')
  if is_positive_integer "$strict_compacts"; then
    compacts_count="$strict_compacts"
    if [ "$compacts_count" -ge 2 ]; then
      compacts_seg="\033[31m[compacts: ${compacts_count}]\033[0m"
    else
      compacts_seg="\033[33m[compacts: ${compacts_count}]\033[0m"
    fi
  fi
fi

if [ -z "$steps_seg" ]; then
  direct_steps=$(json_get '.steps // .step_count // .step')
  if is_positive_integer "$direct_steps"; then
    steps_seg="[steps: ${direct_steps}]"
  fi
fi

# Handoff recommendation badge: warn to prepare for session handoff at 725K+ tokens.
# Policy: Hand off at 725K+ tokens to avoid compactions, or if an actual compaction occurs.
handoff_seg=""
if is_positive_integer "$ctx_used" && [ "$ctx_used" -ge 850000 ] \
   || [ -n "${ctx_int:-}" ] && is_positive_integer "$ctx_int" && [ "$ctx_int" -ge 85 ] \
   || [ "$compacts_count" -ge 2 ]; then
  handoff_seg="\033[1;41;37m[HANDOFF NOW]\033[0m"
elif is_positive_integer "$ctx_used" && [ "$ctx_used" -ge 725000 ] \
     || [ -n "${ctx_int:-}" ] && is_positive_integer "$ctx_int" && [ "$ctx_int" -ge 70 ] \
     || [ "$compacts_count" -ge 1 ]; then
  handoff_seg="\033[1;33m[HANDOFF SUGGESTED (725K+)]\033[0m"
fi
# Effort level
effort_seg=""
effort_level=$(json_get '.effort.level')
if [ -n "$effort_level" ]; then
  case "$effort_level" in
    high|xhigh) effort_seg="\033[1m[effort: ${effort_level}]\033[0m" ;;
    max)        effort_seg="\033[31m[effort: ${effort_level}]\033[0m" ;;
    *)          effort_seg="[effort: ${effort_level}]" ;;
  esac
fi

# Thinking mode
thinking_seg=""
thinking_enabled=$(json_get '.thinking.enabled')
[ "$thinking_enabled" = "true" ] && thinking_seg="[think]"

# Claude account — derived only from the basename of CLAUDE_CONFIG_DIR; the
# directory is never read and the path is never printed. Unset/empty or
# `.claude` is A, `.claude-b` is B, anything else (including a bare "/") is `?`.
# Computed before the rate-limit segments: the capacity fallback keys on it.
acct_letter="?"
acct_dir="${CLAUDE_CONFIG_DIR:-}"
while [ "${acct_dir%/}" != "$acct_dir" ]; do acct_dir="${acct_dir%/}"; done
if [ -z "${CLAUDE_CONFIG_DIR:-}" ]; then
  acct_letter="A"
else
  case "${acct_dir##*/}" in
    .claude)   acct_letter="A" ;;
    .claude-b) acct_letter="B" ;;
  esac
fi
acct_seg="[acct: ${acct_letter}]"

# Rate-limit room left. Claude Code's own field wins: 100 minus
# .rate_limits.<window>.used_percentage, rounded and clamped to 0-100, when it
# is a JSON number (anything else yields empty, never an error). Only a window
# Claude Code did not supply falls back to the capacity file (see header), and
# only for a known account.
json_left() {
  json_get "($1 | select(type == \"number\") | 100 - . | if . < 0 then 0 elif . > 100 then 100 else . end | round)"
}

rl5h_left=$(json_left ".rate_limits.five_hour.used_percentage")
rl7d_left=$(json_left ".rate_limits.seven_day.used_percentage")

# Tail of the capacity history (last 64 KiB, never the whole file). The first
# line of the window may be cut mid-row; `fromjson?` drops it with any other
# malformed line. Only the last row of this account counts, and a value must be
# a number within 0..100 or that window shows nothing.
cap_file="${LU_STATUSLINE_CAPACITY_FILE:-}"
if { [ -z "$rl5h_left" ] || [ -z "$rl7d_left" ]; } && [ "$acct_letter" != "?" ] \
   && [ -n "$cap_file" ] && [ -f "$cap_file" ] && [ -r "$cap_file" ]; then
  cap_left=$(tail -c 65536 "$cap_file" 2>/dev/null | jq -rRs --arg acct "$acct_letter" '
    def left: if type == "number" and . >= 0 and . <= 100 then round else "" end;
    [ split("\n")[] | fromjson? | select(type == "object")
      | select((.account | type == "string")
               and ((.account | ascii_downcase | sub("^claude:"; "")) == ($acct | ascii_downcase))) ]
    | if length == 0 then empty else .[-1] | "\(.five_hour_left_pct | left) \(.seven_day_left_pct | left)" end
  ' 2>/dev/null)
  cap_5h="${cap_left%% *}"
  cap_7d="${cap_left#* }"
  [ -z "$rl5h_left" ] && rl5h_left="$cap_5h"
  [ -z "$rl7d_left" ] && rl7d_left="$cap_7d"
fi

# Render one window: label + percent left, coloured by remaining room
# (under 20 red, under 40 yellow). Anything non-numeric yields no segment.
rate_limit_seg() {
  local label=$1 left=$2
  case "$left" in
    ""|*[!0-9]*) return 0 ;;
  esac
  if   [ "$left" -lt 20 ]; then printf '\033[31m[%s: %d%% left]\033[0m' "$label" "$left"
  elif [ "$left" -lt 40 ]; then printf '\033[33m[%s: %d%% left]\033[0m' "$label" "$left"
  else                          printf '[%s: %d%% left]' "$label" "$left"
  fi
}

rl5h_seg=$(rate_limit_seg "5h" "$rl5h_left")
rl7d_seg=$(rate_limit_seg "7d" "$rl7d_left")

# Session cost — some Claude Code schema versions include .cost.total_cost_usd,
# others omit it entirely. Degrade to empty silently either way; never error.
cost_seg=""
cost_usd=$(json_get '.cost.total_cost_usd')
if [ -n "$cost_usd" ]; then
  cost_fmt=$(printf '%.2f' "$cost_usd" 2>/dev/null) || cost_fmt=""
  [ -n "$cost_fmt" ] && cost_seg="[\$${cost_fmt}]"
fi

# ── Assemble ────────────────────────────────────────────────────

parts=()
[ -n "$model" ]        && parts+=("[$model]")
[ -n "$acct_seg" ]     && parts+=("$acct_seg")
[ -n "$ctx_seg" ]      && parts+=("$ctx_seg")
parts+=("$cwd_name")
[ -n "$wt_seg" ]       && parts+=("$wt_seg")
[ -n "$branch_seg" ]   && parts+=("$branch_seg")
[ -n "$mode_seg" ]     && parts+=("$mode_seg")
[ -n "$steps_seg" ]    && parts+=("$steps_seg")
[ -n "$compacts_seg" ] && parts+=("$compacts_seg")
[ -n "$handoff_seg" ]  && parts+=("$handoff_seg")
[ -n "$mismatch_seg" ] && parts+=("$mismatch_seg")
[ -n "$effort_seg" ]   && parts+=("$effort_seg")
[ -n "$thinking_seg" ] && parts+=("$thinking_seg")
[ -n "$rl5h_seg" ]     && parts+=("$rl5h_seg")
[ -n "$rl7d_seg" ]     && parts+=("$rl7d_seg")
[ -n "$cost_seg" ]     && parts+=("$cost_seg")

# %b interprets the ANSI escape codes embedded in coloured segments.
printf '%b\n' "${parts[*]}"
