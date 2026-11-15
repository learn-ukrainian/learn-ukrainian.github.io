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
# Transcripts use the latest real model turn: Code Mode appends synthetic
# assistant entries (model "<synthetic>") whose usage is all zeros, so those are
# skipped; a real turn reporting zero is unknown usage, never an older turn's.
# The #10471 measurement found top-level usage summed both main passes around
# an advisor call. Only the last message iteration describes current main context.
CONTEXT_USAGE_JQ='
    def tokens:
      (if type == "number" then .
       elif type == "string" then
         # Absolute anchors reject even a final newline: digits, optional fraction.
         if test("\\A[0-9]+(\\.[0-9]+)?\\z") then (tonumber? // 0) else 0 end
       else 0 end)
      | if isnan or (isfinite | not) or . > 1000000000000000 then 0
        else [., 0] | max | floor end;
    def context_tokens:
      (if (.iterations | type) == "array" then
         ([.iterations[] | select(type == "object" and .type == "message")] | last) // .
       else . end)
      | ((.input_tokens | tokens) + (.cache_read_input_tokens | tokens) + (.cache_creation_input_tokens | tokens))
      | floor;
  '
context_latest_usage_tokens() {
  local transcript="$1" usage="${2:-}"
  if [ -n "$usage" ]; then
    printf '%s' "$usage" | jq -r "$CONTEXT_USAGE_JQ"' if type == "object" then context_tokens else 0 end' 2>/dev/null \
      || printf '0\n'
    return 0
  fi
  context_transcript_usage "$transcript" | cut -f1
}

# The transcript's latest usage observation as "<tokens>\t<epoch seconds>"; tokens
# 0 means unknown and epoch 0 means the time is unknown. Only turns after the
# last compaction boundary (type=system, subtype=compact_boundary) count: the
# turns before it describe a context that compaction replaced. A boundary with no
# real turn after it is itself the latest observation, with unknown usage.
context_transcript_usage() {
  local transcript="$1"
  tail -200 "$transcript" 2>/dev/null | jq -rs "$CONTEXT_USAGE_JQ"'
    def epoch:
      (.timestamp | strings | sub("\\.[0-9]+"; "") | fromdateiso8601? | floor) // 0;
    [.[] | select(type == "object")] as $entries
    | ([range(0; $entries | length)
        | select($entries[.].type == "system" and $entries[.].subtype == "compact_boundary")]
       | last) as $boundary
    | (if $boundary == null then $entries else $entries[$boundary:] end) as $current
    | ([$current[] | select(.type == "assistant" and (.message | type) == "object")
         | select(.message.model != "<synthetic>" and (.message.usage | type) == "object")
         | [(.message.usage | context_tokens), epoch]] | last) as $turn
    | if $turn != null then "\($turn[0])\t\($turn[1])"
      elif $boundary != null then "0\t\($entries[$boundary] | epoch)"
      else "0\t0" end
  ' 2>/dev/null || printf '0\t0\n'
}

# Live context usage for a session as "<tokens>\t<source>"; tokens 0 means
# unknown. Usage is never estimated from transcript size. The newest harness
# observation wins, and a newer one supersedes an older one even when it reports
# no usage:
#   - the status line's figure from this session's record (the status line
#     records every value it sees, 0 included, with the time it saw it), while
#     at most 300 seconds old;
#   - the transcript's latest real model turn after the last compaction
#     boundary (headless sessions have no status line), or that boundary.
# A status-line figure older than the transcript's latest observation is
# superseded by it. A status-line zero (no usage yet, or none since /compact)
# falls back to the transcript. Anything else is unknown.
# 300 seconds: the status line runs after every model response and re-records
# at least once a minute while it runs, so at PostToolUse its figure is about as
# old as the tool call that just finished. An older figure means the status
# line is not running, and the transcript reports the same latest turn anyway.
CONTEXT_STATUSLINE_MAX_AGE_SECONDS=300
context_live_usage() {
  local record_file="$1" session_id="$2" transcript="$3"
  local tokens=0 observed_at=0 turn_tokens=0 turn_at=0 now
  if [ -n "$transcript" ] && [ -f "$transcript" ]; then
    IFS=$'\t' read -r turn_tokens turn_at < <(context_transcript_usage "$transcript")
    case "$turn_tokens" in ''|*[!0-9]*) turn_tokens=0 ;; esac
    case "$turn_at" in ''|*[!0-9]*) turn_at=0 ;; esac
  fi
  if [ -f "$record_file" ] && [ ! -L "$record_file" ]; then
    printf -v now '%(%s)T' -1
    IFS=$'\t' read -r tokens observed_at < <(jq -r --arg sid "$session_id" --argjson now "$now" \
      --argjson max "$CONTEXT_STATUSLINE_MAX_AGE_SECONDS" '
      (.observed_context_used_tokens) as $used | (.observed_context_used_at_epoch) as $at
      | if .session_id == $sid and ($used | type) == "number" and ($at | type) == "number"
           and $used >= 0 and ($now - $at) <= $max and ($at - $now) <= 60
        then "\($used | floor)\t\($at | floor)" else "0\t0" end' "$record_file" 2>/dev/null)
    case "$tokens" in ''|*[!0-9]*) tokens=0 ;; esac
    case "$observed_at" in ''|*[!0-9]*) observed_at=0 ;; esac
    if [ "$tokens" -gt 0 ] && [ "$observed_at" -ge "$turn_at" ]; then
      printf '%s\tstatus line (harness live usage)\n' "$tokens"
      return 0
    fi
  fi
  if [ "$turn_tokens" -gt 0 ]; then
    printf '%s\tlatest assistant input/cache usage\n' "$turn_tokens"
    return 0
  fi
  printf '0\tunknown\n'
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

# The name of the guard-managed driver lane this session runs in, or nothing.
# scripts/ops/context_guard.py hands off and restarts the lanes in
# scripts/config/driver_lanes.json by tmux session name, so the operator is not
# the one who restarts such a session. Both facts must hold: the launcher's
# exported SESSION_EPIC names a lane epic, and this pane's tmux session is that
# lane's session. The registry is read with the guard's own loader, so a
# registry the guard rejects (duplicate session, malformed file) yields no lane.
# Anything missing or failing means "not guard-managed": the operator text stays.
context_driver_lane_name() {
  local project_dir="$1" interpreter session name
  local registry_module=scripts.ops.driver_lanes
  [ -n "${SESSION_EPIC:-}" ] && [ -n "${TMUX:-}" ] && [ -n "${TMUX_PANE:-}" ] || return 0
  command -v tmux >/dev/null 2>&1 || return 0
  session=$(tmux display-message -p -t "$TMUX_PANE" '#{session_name}' 2>/dev/null) || return 0
  [ -n "$session" ] || return 0
  interpreter="${THREAD_ROLLOVER_PYTHON:-}"
  if [ -z "$interpreter" ]; then
    # shellcheck source=scripts/lib/project_interpreter.sh
    source "$project_dir/scripts/lib/project_interpreter.sh" 2>/dev/null || return 0
    interpreter=$(project_interpreter_resolve "$project_dir" 2>/dev/null) || return 0
  fi
  [ -x "$interpreter" ] || return 0
  name=$("$interpreter" -I -c '
import importlib
import sys
sys.path.insert(0, sys.argv[1])
load_registry = importlib.import_module(sys.argv[2]).load_registry
lanes = [
    lane.name
    for lane in load_registry().lanes
    if lane.session == sys.argv[3] and lane.epic == sys.argv[4] and lane.kind == "claude"
]
print(lanes[0] if len(lanes) == 1 else "")
' "$project_dir" "$registry_module" "$session" "$SESSION_EPIC" 2>/dev/null) || return 0
  printf '%s\n' "$name"
}
