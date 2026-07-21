#!/usr/bin/env bash
# Common session supervisor helper for non-Claude launchers (Grok, Kimi, ...).
#
# Launchers source this file and call claim_session_supervisor_env to open or
# resume an epic stream lease through the agent-agnostic session-stream
# supervisor (`scripts.session_supervisor`). The supervisor emits a JSON
# bootstrap capsule; this helper parses it, exports the full SESSION_STREAM_*
# envelope the hook surface expects, verifies the required subset, and writes a
# JSON capsule for later diagnostics.
#
# Usage:
#   source "${PROJECT_DIR}/scripts/lib/session_supervisor.sh"
#   claim_session_supervisor_env \
#       "epic:4707" "grok" "grok-tui" "5512-pr-j1-launchers" "grok-$$" \
#       "${PROJECT_DIR}" "start-grok.sh" "harness"
#
# The helper fails the launch closed (exit 1) if the supervisor returns an
# error or if the exported lease envelope is incomplete.

# stream_id_for_epic <epic-name>
# Return the canonical session stream id (epic:<n>) for a launcher shorthand.
# This is intentionally a small, stable launcher lookup; the authoritative
# stream→epic mapping lives in scripts/config/issue_streams.yaml.
stream_id_for_epic() {
  case "${1:-}" in
    atlas|practice|practice-hub) printf '%s' 'epic:4387' ;;
    harness|infra) printf '%s' 'epic:4707' ;;
    hramatka) printf '%s' 'epic:4542' ;;
    folk|seminars-folk) printf '%s' 'epic:2836' ;;
    bio|seminars-bio) printf '%s' 'epic:4431' ;;
  esac
}

# _git_env
# Print a sanitized environment block that ignores inherited Git redirection
# variables, so commands run against the repo root the launcher is starting in.
_git_env() {
  env -u GIT_ALTERNATE_OBJECT_DIRECTORIES \
      -u GIT_COMMON_DIR \
      -u GIT_DIR \
      -u GIT_INDEX_FILE \
      -u GIT_OBJECT_DIRECTORY \
      -u GIT_PREFIX \
      -u GIT_WORK_TREE \
      "$@"
}

# _canonical_state_root <repo-root>
# Print the primary checkout path that owns shared .agent runtime state.
_canonical_state_root() {
  local repo_root="${1:-$(pwd)}"
  local common_dir
  common_dir="$(_git_env git -C "$repo_root" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"
  if [ -z "$common_dir" ] || [ "$(basename "$common_dir")" != ".git" ]; then
    echo "Error: cannot resolve canonical state root for ${repo_root}" >&2
    return 1
  fi
  dirname "$common_dir"
}

# _iso_timestamp
# Print current UTC timestamp in ISO-8601 Z format.
_iso_timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# _shell_json_string <value>
# Escape a string for inclusion in a JSON object (no surrounding quotes).
_shell_json_string() {
  local text="$1"
  text="${text//\\/\\\\}"
  text="${text//\"/\\\"}"
  text="${text//$'\n'/\\n}"
  text="${text//$'\r'/\\r}"
  text="${text//$'\t'/\\t}"
  printf '%s' "$text"
}

# claim_session_supervisor_env <stream> <agent> <harness> <task-id> <instance-id> <project-dir> <launcher> <epic>
#
# Calls the common supervisor to open the stream lease, parses the returned
# JSON capsule, exports SESSION_STREAM_* variables, and writes a capsule under
# <canonical-state-root>/.agent/session-capsules/<stream-safe>/<iso>-<pid>.json.
claim_session_supervisor_env() {
  if [ "$#" -lt 8 ]; then
    echo "Error: claim_session_supervisor_env requires 8 arguments." >&2
    return 1
  fi

  local stream="$1"
  local agent="$2"
  local harness="$3"
  local task_id="$4"
  local instance_id="${5:-${2}-$$}"
  local project_dir="$6"
  local launcher="$7"
  local epic="$8"

  local python_bin="$project_dir/.venv/bin/python"
  if [ ! -x "$python_bin" ]; then
    echo "Error: project Python not found at ${python_bin}" >&2
    return 1
  fi

  local state_root
  state_root="$(_canonical_state_root "$project_dir")" || return 1

  local supervisor_tmp
  supervisor_tmp="$(mktemp)"
  # Ensure cleanup even on early return.
  # shellcheck disable=SC2064
  trap "rm -f '$supervisor_tmp'" RETURN

  local stream_normalized="${stream//:/-}"
  local lineage_id="lineage-${stream_normalized}-${agent}-${$}"
  local ttl_seconds=21600
  local heartbeat_at
  heartbeat_at="$(_iso_timestamp)"

  local -a supervisor_args=(
    "-m" "scripts.session_supervisor"
    "open"
    "--role" "driver"
    "--stream" "$stream"
    "--agent" "$agent"
    "--harness" "$harness"
    "--instance-id" "$instance_id"
    "--process-id" "$$"
    "--lineage-id" "$lineage_id"
    "--ttl-seconds" "$ttl_seconds"
  )
  if [ -n "$task_id" ]; then
    supervisor_args+=("--task-id" "$task_id")
  fi

  if ! "$python_bin" "${supervisor_args[@]}" > "$supervisor_tmp" 2>&1; then
    echo "Error: session supervisor failed to claim ${stream}" >&2
    sed 's/^/  supervisor: /' "$supervisor_tmp" >&2
    return 1
  fi

  # Parse the supervisor's JSON capsule into sourceable export statements.
  local exports
  exports="$($python_bin - "$stream" "$agent" "$harness" "$instance_id" "$$" "$task_id" "$ttl_seconds" "$heartbeat_at" "$supervisor_tmp" <<'PY'
import json, shlex, sys

capsule_path = sys.argv[-1]
with open(capsule_path, encoding="utf-8") as handle:
    capsule = json.load(handle)
lease = (capsule.get("identity") or {}).get("lease") or {}
stream, agent, harness, instance_id, process_id, task_id, ttl, heartbeat_at = sys.argv[1:-1]

exports = {
    "SESSION_STREAM_ID": stream,
    "SESSION_STREAM_SESSION_ID": lease.get("session_id", ""),
    "SESSION_STREAM_LEASE_ID": lease.get("lease_id", ""),
    "SESSION_STREAM_GENERATION": str(lease.get("generation", "")),
    "SESSION_STREAM_FENCING_TOKEN": str(lease.get("fencing_token", "")),
    "SESSION_STREAM_AGENT": agent,
    "SESSION_STREAM_HARNESS": harness,
    "SESSION_STREAM_INSTANCE_ID": instance_id,
    "SESSION_STREAM_PROCESS_ID": process_id,
    "SESSION_STREAM_HEARTBEAT_AT": heartbeat_at,
    "SESSION_STREAM_EXPIRES_AT": lease.get("expires_at", ""),
    "SESSION_STREAM_TTL_SECONDS": ttl,
    "SESSION_STREAM_VERSION": "1",
}
if task_id:
    exports["SESSION_STREAM_TASK_ID"] = task_id

for key, value in exports.items():
    print(f"export {shlex.quote(key)}={shlex.quote(str(value))}")
PY
)"
  if [ -z "$exports" ]; then
    echo "Error: failed to parse supervisor capsule for ${stream}." >&2
    cat "$supervisor_tmp" >&2
    return 1
  fi

  # shellcheck source=/dev/null
  eval "$exports"

  # Required envelope check.
  if [ -z "${SESSION_STREAM_ID:-}" ] || [ -z "${SESSION_STREAM_SESSION_ID:-}" ] || [ -z "${SESSION_STREAM_LEASE_ID:-}" ]; then
    echo "Error: supervisor output is missing required SESSION_STREAM_* fields." >&2
    cat "$supervisor_tmp" >&2
    return 1
  fi

  # Write a versioned capsule for diagnostics and resume.
  local stream_safe="${stream//:/-}"
  stream_safe="${stream_safe// /-}"
  local capsule_dir="$state_root/.agent/session-capsules/$stream_safe"
  mkdir -p "$capsule_dir"
  local capsule_name="$(_iso_timestamp)-$$.json"
  # Normalize to a safe filename (replace colons and spaces).
  capsule_name="${capsule_name//:/-}"
  capsule_name="${capsule_name// /-}"
  local capsule_path="$capsule_dir/$capsule_name"

  local task_id_json
  if [ -n "${SESSION_STREAM_TASK_ID:-}" ]; then
    task_id_json="\"$(_shell_json_string "$SESSION_STREAM_TASK_ID")\""
  else
    task_id_json="null"
  fi

  cat > "$capsule_path" <<EOF
{
  "schema_version": 1,
  "written_at": "$(_iso_timestamp)",
  "launcher": "$(_shell_json_string "$launcher")",
  "epic": "$(_shell_json_string "$epic")",
  "stream_id": "$(_shell_json_string "$SESSION_STREAM_ID")",
  "session_id": "$(_shell_json_string "$SESSION_STREAM_SESSION_ID")",
  "lease_id": "$(_shell_json_string "$SESSION_STREAM_LEASE_ID")",
  "agent": "$(_shell_json_string "$SESSION_STREAM_AGENT")",
  "harness": "$(_shell_json_string "$SESSION_STREAM_HARNESS")",
  "instance_id": "$(_shell_json_string "$SESSION_STREAM_INSTANCE_ID")",
  "process_id": ${SESSION_STREAM_PROCESS_ID},
  "task_id": $task_id_json
}
EOF

  echo "Session supervisor: claimed ${SESSION_STREAM_ID} session ${SESSION_STREAM_SESSION_ID}"
  echo "Session capsule: ${capsule_path#"$state_root/"}"

  # Export the capsule path for consumers / tests.
  export SESSION_SUPERVISOR_CAPSULE_PATH="$capsule_path"
}
