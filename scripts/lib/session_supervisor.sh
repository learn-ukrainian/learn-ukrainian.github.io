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

# Load the selector SSOT when this helper is sourced independently.  The
# launcher normally sources handoff_identity.sh first; this guarded import also
# keeps stream resolution available to direct session-supervisor consumers.
if ! declare -F launcher_selector_stream >/dev/null 2>&1; then
  _session_supervisor_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [ -f "$_session_supervisor_lib_dir/handoff_identity.sh" ]; then
    # shellcheck disable=SC1091
    source "$_session_supervisor_lib_dir/handoff_identity.sh"
  fi
  unset _session_supervisor_lib_dir
fi

# stream_id_for_epic <lane-or-lane.topic>
# Return the canonical session stream id.  The exact allowlist lives in
# launcher_selector_resolve in handoff_identity.sh; unknown selectors return
# empty and must be rejected by callers.
stream_id_for_epic() {
  if declare -F launcher_selector_stream >/dev/null 2>&1; then
    launcher_selector_stream "${1:-}"
  else
    return 1
  fi
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

  local state_root
  state_root="$(_canonical_state_root "$project_dir")" || return 1
  local python_bin="$state_root/.venv/bin/python"
  if [ ! -x "$python_bin" ]; then
    echo "Error: project Python not found at ${python_bin}" >&2
    return 1
  fi

  local supervisor_tmp
  supervisor_tmp="$(mktemp)"
  # Ensure cleanup even on early return.
  # shellcheck disable=SC2064
  trap "rm -f '$supervisor_tmp'" RETURN

  local stream_normalized="${stream//:/-}"
  local lineage_id="lineage-${stream_normalized}-${agent}-${$}"
  # Remote v1 uses the design-note TTL; liveness is carried by the independent
  # launcher renew loop, never by a server-side PID probe.
  local ttl_seconds=900
  local host_id
  if [ "${LU_MONITOR_HOST_ID+x}" = x ]; then
    host_id="${LU_MONITOR_HOST_ID:-local}"
  else
    host_id="$("$python_bin" -m scripts.api.occupancy_local resolve-host-id 2>/dev/null)" || host_id="local"
    if [ -z "$host_id" ]; then
      host_id="local"
    fi
  fi
  export LU_MONITOR_HOST_ID="$host_id"
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
    "--host-id" "$host_id"
  )
  if [ -n "$task_id" ]; then
    supervisor_args+=("--task-id" "$task_id")
  fi

  local expected_generation=""
  if [ -n "${SESSION_SUPERVISOR_WAKE_DELIVERY:-}" ]; then
    if [ "${SESSION_SUPERVISOR_WAKE_STREAM:-}" != "$stream" ]; then
      echo "Error: supervisory event stream does not match this launcher." >&2
      return 1
    fi
    local watcher launch_plan launch_identity
    watcher="$(cd "$(dirname "${BASH_SOURCE[0]}")/../ai_agent_bridge" && pwd)/inbox_watch.sh"
    launch_plan="$("$watcher" "$agent" --launch-plan "$SESSION_SUPERVISOR_WAKE_DELIVERY" --stream "$stream")" || return 1
    launch_identity="$("$python_bin" -c 'import json,sys; p=json.loads(sys.argv[1]); print(p["session_id"]); print(p["generation"])' "$launch_plan")" || return 1
    expected_generation="${launch_identity##*$'\n'}"
    supervisor_args+=("--session-id" "${launch_identity%%$'\n'*}")
  fi

  if ! "$python_bin" "${supervisor_args[@]}" > "$supervisor_tmp" 2>&1; then
    echo "Error: session supervisor failed to claim ${stream}" >&2
    sed 's/^/  supervisor: /' "$supervisor_tmp" >&2
    # Remote v1 is TTL-only: an unexpired lease is live regardless of PID.
    # Local --local callers retain proof-gated dead-process recovery; launchers
    # must not silently switch to that local path when Monitor refuses a claim.
    if grep -q "already has live session" "$supervisor_tmp" 2>/dev/null; then
      echo "  hint: another process still holds this epic stream." >&2
      echo "  diagnose: .venv/bin/python -m agents_extensions.shared.session_streams handoff-status --stream ${stream}" >&2
      echo "  remote leases remain live until expires_at; wait for TTL expiry or obtain an attributed operator release." >&2
    fi
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

  # Read/claim races can advance the stream between preflight and CAS. Never
  # start a provider for a generation beyond this event's one-successor budget.
  if [ -n "$expected_generation" ] && [ "${SESSION_STREAM_GENERATION:-}" != "$expected_generation" ]; then
    "$python_bin" -m scripts.session_supervisor close --role driver >/dev/null || true
    echo "Error: supervisory wake was superseded before the lease claim." >&2
    return 1
  fi

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
  local capsule_name
  capsule_name="$(_iso_timestamp)-$$.json"
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

  # FAIL-HANDOFF lanes close the *exact* launcher-owned lease later by reading
  # this receipt. Keep it derived from the export payload above so the running
  # environment, diagnostic capsule, and close receipt cannot drift.
  local lease_receipt_dir="$project_dir/.claude/${epic}-epic"
  local lease_receipt_path="$lease_receipt_dir/session-lease.env"
  if ! mkdir -p "$lease_receipt_dir"; then
    echo "Warning: could not create session lease receipt directory: ${lease_receipt_dir}" >&2
  elif ! printf '%s\n' "$exports" > "$lease_receipt_path"; then
    echo "Warning: could not write session lease receipt: ${lease_receipt_path}" >&2
  fi

  echo "Session supervisor: claimed ${SESSION_STREAM_ID} session ${SESSION_STREAM_SESSION_ID}"
  echo "Session capsule: ${capsule_path#"$state_root/"}"

  # Export the capsule path for consumers / tests.
  export SESSION_SUPERVISOR_CAPSULE_PATH="$capsule_path"
}

# These hooks are called by the existing launcher process loop. The watcher
# may prepare a handoff, but never owns lease renewal/release or process exit.
session_supervisor_start_inbox_watch() {
  local watcher
  watcher="$(cd "$(dirname "${BASH_SOURCE[0]}")/../ai_agent_bridge" && pwd)/inbox_watch.sh" || return 1
  [ -x "$watcher" ] || return 1
  LC_SUPERVISORY_WAKE_FILE="$(mktemp)" || return 1
  # Read by the launcher_core.sh process wait loop.
  # shellcheck disable=SC2034
  LC_SUPERVISORY_EVENT=0
  LC_SUPERVISORY_DELIVERY=""
  trap 'LC_SUPERVISORY_EVENT=1' USR1
  (
    trap - EXIT INT TERM HUP USR1
    exec "$watcher" "${LC_DRIVER_HANDOFF:-$LC_PROVIDER}" --live-supervisory --notify-parent
  ) > "$LC_SUPERVISORY_WAKE_FILE" &
  LC_SUPERVISORY_WATCH_PID=$!
}

session_supervisor_read_wake() {
  local watcher_rc=0
  wait "$LC_SUPERVISORY_WATCH_PID" || watcher_rc=$?
  LC_SUPERVISORY_WATCH_PID=""
  if [ "$watcher_rc" -eq 76 ]; then
    echo "supervisory inbox watcher: waiting for Monitor API to recover; restarting watcher" >&2
    session_supervisor_stop_inbox_watch
    session_supervisor_start_inbox_watch || return 1
    return 76
  fi
  if [ "$watcher_rc" -ne 75 ]; then
    echo "Error: supervisory inbox watcher failed; stopping this driver closed." >&2
    return 1
  fi
  IFS= read -r LC_SUPERVISORY_DELIVERY < "$LC_SUPERVISORY_WAKE_FILE" || return 1
  [ -n "$LC_SUPERVISORY_DELIVERY" ] || return 1
}

session_supervisor_stop_inbox_watch() {
  local attempt
  if [ -n "${LC_SUPERVISORY_WATCH_PID:-}" ]; then
    kill "$LC_SUPERVISORY_WATCH_PID" 2>/dev/null || true
    # A provider can exit while the watcher is still crossing its exec boundary.
    # Bound cleanup even if that startup race loses the initial TERM.
    for ((attempt=0; attempt<20; attempt++)); do
      kill -0 "$LC_SUPERVISORY_WATCH_PID" 2>/dev/null || break
      sleep 0.05
    done
    if kill -0 "$LC_SUPERVISORY_WATCH_PID" 2>/dev/null; then
      kill -KILL "$LC_SUPERVISORY_WATCH_PID" 2>/dev/null || true
    fi
    wait "$LC_SUPERVISORY_WATCH_PID" 2>/dev/null || true
    LC_SUPERVISORY_WATCH_PID=""
  fi
  trap - USR1
  if [ -n "${LC_SUPERVISORY_WAKE_FILE:-}" ]; then
    rm -f "$LC_SUPERVISORY_WAKE_FILE"
    LC_SUPERVISORY_WAKE_FILE=""
  fi
}

session_supervisor_stop_provider_for_wake() {
  local attempt
  kill -TERM "$LC_DRIVER_CHILD_PID" 2>/dev/null || true
  # Preparation is already durable. Give the provider a bounded clean exit;
  # never release its lease while its launcher-owned process is still alive.
  for ((attempt=0; attempt<100; attempt++)); do
    kill -0 "$LC_DRIVER_CHILD_PID" 2>/dev/null || break
    sleep 0.1
  done
  if kill -0 "$LC_DRIVER_CHILD_PID" 2>/dev/null; then
    kill -KILL "$LC_DRIVER_CHILD_PID" 2>/dev/null || true
  fi
  wait "$LC_DRIVER_CHILD_PID" 2>/dev/null || true
}

session_supervisor_exec_successor() {
  [ "${LC_DRIVER_LEASE_CLOSED:-0}" = 1 ] || return 1
  [ -n "${LC_SUPERVISORY_DELIVERY:-}" ] || return 1
  export SESSION_SUPERVISOR_WAKE_DELIVERY="$LC_SUPERVISORY_DELIVERY"
  export SESSION_SUPERVISOR_WAKE_STREAM="$SESSION_STREAM_ID"
  local name
  for name in ${!SESSION_STREAM_@}; do
    unset "$name"
  done
  # Replace this supervisor shell. Its successor uses the same approved public
  # entrypoint and original argv, then makes a fresh Monitor TTL/CAS claim.
  exec "$LC_ROOT/start-${LC_PROVIDER}-driver.sh" "${LC_DRIVER_ORIGINAL_ARGS[@]}"
}
