#!/bin/bash
# Shared helpers for context-monitor.sh and context-rollover-guard.sh (#8511).
# Sourced, never registered as a hook; executing it directly does nothing.
# State I/O is delegated to the descriptor-relative Python helper (#9791).

# Match the existing rollover hooks' explicit interpreter override; otherwise
# use the shared project interpreter resolver. Never fall back to PATH Python.
context_hook_state() {
  local operation="$1" project_dir="$2" session_id="$3" interpreter helper
  shift 3
  interpreter="${THREAD_ROLLOVER_PYTHON:-}"
  if [ -z "$interpreter" ]; then
    # shellcheck source=scripts/lib/project_interpreter.sh
    source "$project_dir/scripts/lib/project_interpreter.sh" 2>/dev/null || return 0
    interpreter=$(project_interpreter_resolve "$project_dir" 2>/dev/null) || return 0
  fi
  [ -x "$interpreter" ] || return 0
  helper="$(dirname "${BASH_SOURCE[0]}")/context-hook-state.py"
  "$interpreter" "$helper" "$operation" "$project_dir" "$session_id" "$@" 2>/dev/null || true
}

# Latest assistant input/cache usage from a Claude Code transcript, or 0.
# Output tokens are not current context usage and are deliberately excluded.
# An optional usage object lets statuslines apply the same rule to current_usage.
context_latest_usage_tokens() {
  local transcript="$1" usage="${2:-}"
  if [ -z "$usage" ]; then
    usage=$(tail -200 "$transcript" 2>/dev/null \
      | jq -s '[.[] | select(.type == "assistant" and (.message.usage | type) == "object")] | last | .message.usage // empty' 2>/dev/null)
  fi
  if [ -z "$usage" ] || [ "$usage" = "null" ]; then
    printf '0\n'
    return 0
  fi
  # The #10471 measurement found top-level usage summed both main passes around
  # an advisor call. Only the last message iteration describes current main context.
  printf '%s' "$usage" | jq -r '
    def tokens:
      (if type == "number" then .
       elif type == "string" then (tonumber? // 0)
       else 0 end) | [., 0] | max | floor;
    (if (.iterations | type) == "array" then
       ([.iterations[] | select(type == "object" and .type == "message")] | last) // .
     else . end)
    | (.input_tokens | tokens) + (.cache_read_input_tokens | tokens) + (.cache_creation_input_tokens | tokens)
  ' 2>/dev/null || printf '0\n'
}

# Canonical checkout that owns runtime state (.agent/): CODEX_CANONICAL_REPO_ROOT
# when set, else the git common dir's checkout, so linked worktrees share the
# primary checkout's session records and rollover leases.
context_canonical_root() {
  local project_dir="$1" git_common_dir
  if [ -n "${CODEX_CANONICAL_REPO_ROOT:-}" ]; then
    printf '%s\n' "$CODEX_CANONICAL_REPO_ROOT"
    return 0
  fi
  git_common_dir=$(git -C "$project_dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
  if [ -n "$git_common_dir" ] && [ "$(basename "$git_common_dir")" = ".git" ]; then
    dirname "$git_common_dir"
  else
    printf '%s\n' "$project_dir"
  fi
}

# Canonical session record path: an explicit existing override, else
# <canonical checkout>/.agent/sessions/<session id>.json.
context_session_record_file() {
  local project_dir="$1" session_id="$2"
  if [ -n "${LEARN_UKRAINIAN_SESSION_RECORD:-}" ] && [ -f "$LEARN_UKRAINIAN_SESSION_RECORD" ]; then
    printf '%s\n' "$LEARN_UKRAINIAN_SESSION_RECORD"
    return 0
  fi
  printf '%s\n' "$(context_canonical_root "$project_dir")/.agent/sessions/$session_id.json"
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
