#!/usr/bin/env bash
# Claude Code statusline — learn-ukrainian project.
#
# Reads Claude Code status JSON from stdin and renders:
#   [MODEL] cwd-basename [wt:worktree-name] (branch*) [ctx: N%]
#   [effort: level] [think] [5h: N%] [7d: N%]
#
# Segments:
#   [MODEL]        .model.display_name, omitted if missing
#   cwd-basename   basename(.workspace.current_dir), pwd fallback
#   [wt:...]       basename(.workspace.git_worktree), omitted if not in a worktree
#   (branch*)      git branch + `*` if dirty
#   [ctx: UK/BK (N%)] context window — color-coded green<50, yellow 50-79,
#                    red 80+. U=used Ktokens, B=budget Ktokens, N=percent.
#                    Used tokens prefer official Claude Code fields:
#                      1) .context_window.total_input_tokens;
#                      2) input/cache fields inside .context_window.current_usage;
#                      3) legacy direct token keys;
#                      4) latest assistant input/cache usage from transcript JSONL.
#                    Output tokens are never added to current-context usage.
#                    Capacity prefers .context_window.context_window_size, then
#                    the canonical per-session record. There is no universal 1M
#                    or auto-compaction fallback; unknown capacity stays hidden.
#   [effort: ...]  .effort.level — low/medium default, high/xhigh bold,
#                    max red. Omitted for pre-2.1.119 clients.
#   [think]        .thinking.enabled — emitted only when true. Omitted for
#                    pre-2.1.119 clients.
#   [5h: N%]       .rate_limits.five_hour.used_percentage — subscription
#                    budget. Only shown when elevated (60%+ yellow, 80%+ red).
#                    Stays silent while healthy — no noise in normal use.
#   [7d: N%]       .rate_limits.seven_day.used_percentage — weekly budget.
#                    Same threshold scheme as 5h.
#
# NOTE: .cost.total_cost_usd is deliberately NOT rendered. The field is a
# client-side API-equivalent estimate that is meaningless for Claude Max
# subscription users (which is the primary intended user of this project).
# The actionable subscription metrics are the 5h and 7d rate-limit windows.
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
#   - Script is intentionally cheap: no network, no external state, only
#     `git` + `jq` + `printf`. Statusline fires on every event.
#
# Debug: uncomment the tee line below to capture incoming JSON at
#        /tmp/.statusline-input.json for schema inspection.

set -u

command -v jq >/dev/null 2>&1 || exit 0

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

# Branch + dirty marker
branch_seg=""
if git -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch=$(git -C "$cwd" symbolic-ref --quiet --short HEAD 2>/dev/null \
           || git -C "$cwd" rev-parse --short HEAD 2>/dev/null \
           || true)
  dirty=""
  [ -n "$(git -C "$cwd" status --porcelain 2>/dev/null)" ] && dirty="*"
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
  ctx_used=$(json_get '
    if (.context_window.current_usage | type) == "object" then
      ((.context_window.current_usage.input_tokens // 0)
       + (.context_window.current_usage.cache_read_input_tokens // 0)
       + (.context_window.current_usage.cache_creation_input_tokens // 0))
    else empty end')
  [ "$ctx_used" = "0" ] && ctx_used=""
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
  PROJECT_DIR=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || printf '%s' "$cwd")
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
  usage_json=$(tail -200 "$transcript_path" 2>/dev/null \
    | jq -s '[.[] | select(.type == "assistant" and .message.usage != null)] | last | .message.usage // empty' 2>/dev/null)
  if [ -n "$usage_json" ] && [ "$usage_json" != "null" ] && [ "$usage_json" != "empty" ]; then
    inp=$(printf '%s' "$usage_json" | jq -r '.input_tokens // 0' 2>/dev/null)
    cr=$(printf '%s' "$usage_json" | jq -r '.cache_read_input_tokens // 0' 2>/dev/null)
    cc=$(printf '%s' "$usage_json" | jq -r '.cache_creation_input_tokens // 0' 2>/dev/null)
    ctx_used=$(( ${inp:-0} + ${cr:-0} + ${cc:-0} ))
    [ "$ctx_used" = "0" ] && ctx_used=""
  fi
fi

# Compute a percentage only when both values are trustworthy positive integers.
if [ -z "$ctx_pct" ] && is_positive_integer "$ctx_used" && is_positive_integer "$ctx_budget"; then
  ctx_pct=$(( ctx_used * 100 / ctx_budget ))
fi

if [ -n "$ctx_pct" ]; then
  ctx_int=$(printf '%.0f' "$ctx_pct" 2>/dev/null) || ctx_int=""
  if [ -n "$ctx_int" ]; then
    if   [ "$ctx_int" -ge 80 ]; then ctx_color="\033[31m"   # red
    elif [ "$ctx_int" -ge 50 ]; then ctx_color="\033[33m"   # yellow
    else                             ctx_color="\033[32m"   # green
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

# ── Steps & Compactions Telemetry ─────────────────────────────
steps_seg=""
compacts_seg=""
handoff_seg=""
steps_count=0
compacts_count=0

if [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
  steps_count=$(wc -l < "$transcript_path" 2>/dev/null | tr -d ' ')
  if is_positive_integer "$steps_count"; then
    steps_seg="[steps: ${steps_count}]"
  else
    steps_count=0
  fi

  compacts_count=$(grep -i -c 'compact' "$transcript_path" 2>/dev/null || true)
  if is_positive_integer "$compacts_count"; then
    if [ "$compacts_count" -ge 2 ]; then
      compacts_seg="\033[31m[compacts: ${compacts_count}]\033[0m"
    else
      compacts_seg="\033[33m[compacts: ${compacts_count}]\033[0m"
    fi
  else
    compacts_count=0
  fi
fi

# Handoff recommendation badge based on context %, step count, and compaction count
# Policy: Prefer handoff over compaction. A single compaction warns; 2+ compactions require immediate handoff.
if [ -n "${ctx_int:-}" ] && is_positive_integer "$ctx_int" && [ "$ctx_int" -ge 80 ] \
   || [ "$compacts_count" -ge 2 ] || [ "$steps_count" -ge 80 ]; then
  handoff_seg="\033[1;41;37m[HANDOFF NOW (prefer handoff over compact)]\033[0m"
elif [ -n "${ctx_int:-}" ] && is_positive_integer "$ctx_int" && [ "$ctx_int" -ge 70 ] \
     || [ "$compacts_count" -ge 1 ] || [ "$steps_count" -ge 60 ]; then
  handoff_seg="\033[1;33m[HANDOFF SUGGESTED]\033[0m"
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

# Rate-limit segment helper — only surface when elevated (60%+).
# Accepts a label (e.g. "5h", "7d") and a jq path, returns coloured
# segment on stdout or empty string.
rate_limit_seg() {
  local label=$1 path=$2 pct int
  pct=$(json_get "$path")
  [ -z "$pct" ] && return 0
  int=$(printf '%.0f' "$pct" 2>/dev/null) || return 0
  if   [ "$int" -ge 80 ]; then printf '\033[31m[%s: %d%%]\033[0m' "$label" "$int"
  elif [ "$int" -ge 60 ]; then printf '\033[33m[%s: %d%%]\033[0m' "$label" "$int"
  fi
}

rl5h_seg=$(rate_limit_seg "5h" ".rate_limits.five_hour.used_percentage")
rl7d_seg=$(rate_limit_seg "7d" ".rate_limits.seven_day.used_percentage")

# ── Assemble ────────────────────────────────────────────────────

parts=()
[ -n "$model" ]        && parts+=("[$model]")
parts+=("$cwd_name")
[ -n "$wt_seg" ]       && parts+=("$wt_seg")
[ -n "$branch_seg" ]   && parts+=("$branch_seg")
[ -n "$ctx_seg" ]      && parts+=("$ctx_seg")
[ -n "$steps_seg" ]    && parts+=("$steps_seg")
[ -n "$compacts_seg" ] && parts+=("$compacts_seg")
[ -n "$handoff_seg" ]  && parts+=("$handoff_seg")
[ -n "$mismatch_seg" ] && parts+=("$mismatch_seg")
[ -n "$effort_seg" ]   && parts+=("$effort_seg")
[ -n "$thinking_seg" ] && parts+=("$thinking_seg")
[ -n "$rl5h_seg" ]     && parts+=("$rl5h_seg")
[ -n "$rl7d_seg" ]     && parts+=("$rl7d_seg")

# %b interprets the ANSI escape codes embedded in coloured segments.
printf '%b\n' "${parts[*]}"

