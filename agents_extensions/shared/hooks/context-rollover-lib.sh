#!/bin/bash
# Shared helpers for context-monitor.sh and context-rollover-guard.sh (#8511).
# Sourced, never registered as a hook; executing it directly does nothing.

# Latest assistant input/cache usage from a Claude Code transcript, or 0.
# Output tokens are not current context usage and are deliberately excluded.
context_latest_usage_tokens() {
  local transcript="$1" usage input_tokens cache_read cache_create
  usage=$(tail -200 "$transcript" 2>/dev/null \
    | jq -s '[.[] | select(.type == "assistant" and (.message.usage | type) == "object")] | last | .message.usage // empty' 2>/dev/null)
  if [ -z "$usage" ] || [ "$usage" = "null" ]; then
    printf '0\n'
    return 0
  fi
  input_tokens=$(printf '%s' "$usage" | jq -r '.input_tokens // 0' 2>/dev/null)
  cache_read=$(printf '%s' "$usage" | jq -r '.cache_read_input_tokens // 0' 2>/dev/null)
  cache_create=$(printf '%s' "$usage" | jq -r '.cache_creation_input_tokens // 0' 2>/dev/null)
  printf '%s\n' "$(( ${input_tokens:-0} + ${cache_read:-0} + ${cache_create:-0} ))"
}

# Canonical session record path: an explicit existing override, else
# <canonical checkout>/.agent/sessions/<session id>.json, resolved through the
# git common dir so linked worktrees share the primary checkout's records.
context_session_record_file() {
  local project_dir="$1" session_id="$2" canonical_root git_common_dir
  if [ -n "${LEARN_UKRAINIAN_SESSION_RECORD:-}" ] && [ -f "$LEARN_UKRAINIAN_SESSION_RECORD" ]; then
    printf '%s\n' "$LEARN_UKRAINIAN_SESSION_RECORD"
    return 0
  fi
  if [ -n "${CODEX_CANONICAL_REPO_ROOT:-}" ]; then
    canonical_root="$CODEX_CANONICAL_REPO_ROOT"
  else
    git_common_dir=$(git -C "$project_dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
    if [ -n "$git_common_dir" ] && [ "$(basename "$git_common_dir")" = ".git" ]; then
      canonical_root=$(dirname "$git_common_dir")
    else
      canonical_root="$project_dir"
    fi
  fi
  printf '%s\n' "$canonical_root/.agent/sessions/$session_id.json"
}

# Effective rollover mode for this session. operator_restart applies only when
# an operator can restart the session: a delegated worker has nobody to wait
# for, so it keeps the continuation behaviour and its native compaction.
context_effective_rollover_mode() {
  if [ "${1:-}" = "operator_restart" ] && [ -z "${LEARN_UKRAINIAN_DISPATCH_TASK_ID:-}" ]; then
    printf 'operator_restart\n'
  else
    printf 'continuation\n'
  fi
}
