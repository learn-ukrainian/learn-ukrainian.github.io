#!/usr/bin/env bash
# Claude Code statusline — learn-ukrainian project.
#
# Reads Claude Code status JSON from stdin and renders:
#   [MODEL] cwd-basename [wt:worktree-name] (branch*) [ctx: N%] [$0.XX] [5h: N%]
#
# Segments:
#   [MODEL]        .model.display_name, omitted if missing
#   cwd-basename   basename(.workspace.current_dir), pwd fallback
#   [wt:...]       basename(.workspace.git_worktree), omitted if not in a worktree
#   (branch*)      git branch + `*` if dirty
#   [ctx: N%]      .context_window.used_percentage — color-coded:
#                    green <50, yellow 50–79, red 80+. Omitted until the
#                    first API call populates the field.
#   [$0.XX]        .cost.total_cost_usd — omitted if < $0.01 (session start)
#   [5h: N%]       .rate_limits.five_hour.used_percentage — only shown when
#                    elevated (60%+ yellow, 80%+ red). Stays silent while healthy.
#
# Schema reference: https://code.claude.com/docs/en/statusline.md
#
# Graceful degradation:
#   - If `jq` is not installed, script exits silently (empty status line).
#   - Any missing / null JSON field is dropped from output silently.
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

input=$(cat)
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

# Context window %
ctx_seg=""
ctx_pct=$(json_get '.context_window.used_percentage')
if [ -n "$ctx_pct" ]; then
  ctx_int=$(printf '%.0f' "$ctx_pct" 2>/dev/null) || ctx_int=""
  if [ -n "$ctx_int" ]; then
    if   [ "$ctx_int" -ge 80 ]; then ctx_color="\033[31m"   # red
    elif [ "$ctx_int" -ge 50 ]; then ctx_color="\033[33m"   # yellow
    else                             ctx_color="\033[32m"   # green
    fi
    ctx_seg="${ctx_color}[ctx: ${ctx_int}%]\033[0m"
  fi
fi

# Cost in USD — only if ≥ $0.01 (hide session-start "$0.00" clutter)
cost_seg=""
cost_usd=$(json_get '.cost.total_cost_usd')
if [ -n "$cost_usd" ]; then
  if awk -v c="$cost_usd" 'BEGIN { exit !(c+0 >= 0.01) }'; then
    cost_fmt=$(printf '%.2f' "$cost_usd" 2>/dev/null)
    [ -n "$cost_fmt" ] && cost_seg="[\$${cost_fmt}]"
  fi
fi

# 5-hour rate-limit — only surface when elevated
rl_seg=""
rl_5h=$(json_get '.rate_limits.five_hour.used_percentage')
if [ -n "$rl_5h" ]; then
  rl_int=$(printf '%.0f' "$rl_5h" 2>/dev/null) || rl_int=""
  if [ -n "$rl_int" ]; then
    if   [ "$rl_int" -ge 80 ]; then rl_seg="\033[31m[5h: ${rl_int}%]\033[0m"
    elif [ "$rl_int" -ge 60 ]; then rl_seg="\033[33m[5h: ${rl_int}%]\033[0m"
    fi
  fi
fi

# ── Assemble ────────────────────────────────────────────────────

parts=()
[ -n "$model" ]      && parts+=("[$model]")
parts+=("$cwd_name")
[ -n "$wt_seg" ]     && parts+=("$wt_seg")
[ -n "$branch_seg" ] && parts+=("$branch_seg")
[ -n "$ctx_seg" ]    && parts+=("$ctx_seg")
[ -n "$cost_seg" ]   && parts+=("$cost_seg")
[ -n "$rl_seg" ]     && parts+=("$rl_seg")

# %b interprets the ANSI escape codes embedded in ctx_seg / rl_seg.
printf '%b\n' "${parts[*]}"
