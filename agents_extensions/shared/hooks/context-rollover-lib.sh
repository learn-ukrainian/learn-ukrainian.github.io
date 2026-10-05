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

# Claim <tier> for this session at <tokens> under an exclusive lock, so
# concurrent PostToolUse hooks announce each tier exactly once. The state file
# holds "<tier> <tokens>". A compaction-scale drop (usage below 60% of the
# level at the last claim) re-arms every tier. Prints "claimed" when this call
# raised the tier; prints nothing otherwise (including when the lock cannot be
# taken within about two seconds - the next tool call retries).
context_claim_tier() {
  local state_file="$1" tier="$2" tokens="$3" lock_file waited=0
  mkdir -p "$(dirname "$state_file")" 2>/dev/null || return 0
  if command -v flock >/dev/null 2>&1; then
    (
      flock -w 2 9 || exit 0
      _context_claim_tier_locked "$state_file" "$tier" "$tokens"
    ) 9>>"$state_file.lock"
    return 0
  fi
  # No flock (e.g. stock macOS): bash's noclobber redirection is an exclusive
  # create (O_EXCL) done by the shell itself. Not a mkdir binary: some
  # implementations (uutils coreutils 0.8) report success to several racing
  # callers. The holder removes the lock on exit or signal. Never test a
  # lock's age and then delete it: a lock taken between the test and the
  # delete would be lost. Only a lock still held after about two seconds -
  # far longer than this millisecond critical section - is treated as left by
  # a SIGKILLed hook: it is renamed aside and this call claims nothing (the
  # next tool call retries).
  lock_file="$state_file.lockfile"
  while ! (set -o noclobber; : > "$lock_file") 2>/dev/null; do
    waited=$((waited + 1))
    if [ "$waited" -ge 40 ]; then
      mv "$lock_file" "$lock_file.stale.$$" 2>/dev/null && rm -f "$lock_file.stale.$$"
      return 0
    fi
    sleep 0.05
  done
  (
    trap 'rm -f "$lock_file"' EXIT
    trap 'exit 1' HUP INT TERM
    _context_claim_tier_locked "$state_file" "$tier" "$tokens"
  )
}

_context_claim_tier_locked() {
  local state_file="$1" tier="$2" tokens="$3" last_tier=0 last_tokens=0
  if [ -f "$state_file" ]; then
    read -r last_tier last_tokens < "$state_file" 2>/dev/null || true
  fi
  case "$last_tier" in ''|*[!0-9]*) last_tier=0 ;; esac
  case "$last_tokens" in ''|*[!0-9]*) last_tokens=0 ;; esac
  if [ "$last_tier" -gt 0 ] && [ $((tokens * 100)) -lt $((last_tokens * 60)) ]; then
    rm -f "$state_file" 2>/dev/null
    last_tier=0
  fi
  [ "$tier" -gt "$last_tier" ] || return 0
  printf '%s %s\n' "$tier" "$tokens" > "$state_file.tmp.$$" 2>/dev/null \
    && mv -f "$state_file.tmp.$$" "$state_file" 2>/dev/null \
    && printf 'claimed\n'
}
