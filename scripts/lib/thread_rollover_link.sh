#!/usr/bin/env bash
# Bootstrap Codex checkouts without copying provider history or the .agent tree.

ensure_thread_rollover_link() {
  local canonical_root="$1"
  local worktree_root="$2"
  local source="$canonical_root/.agent/thread-rollovers"
  local target="$worktree_root/.agent/thread-rollovers"

  if [ "$canonical_root" = "$worktree_root" ]; then
    mkdir -p "$source"
    return 0
  fi

  mkdir -p "$source" "$worktree_root/.agent"
  if [ -L "$target" ]; then
    if [ "$(readlink "$target")" != "$source" ]; then
      printf 'Error: rollover symlink at %s points somewhere other than %s.\n' "$target" "$source" >&2
      return 1
    fi
    return 0
  fi
  if [ -e "$target" ]; then
    printf 'Error: real or broken rollover path at %s blocks canonical state sharing.\n' "$target" >&2
    return 1
  fi
  ln -s "$source" "$target"
}

ensure_codex_venv_link() {
  local canonical_root="$1"
  local worktree_root="$2"
  local source="$canonical_root/.venv"
  local target="$worktree_root/.venv"

  if [ "$canonical_root" = "$worktree_root" ]; then
    return 0
  fi
  if [ -L "$target" ]; then
    if [ "$(readlink "$target")" != "$source" ]; then
      printf 'Error: virtualenv symlink at %s points somewhere other than %s.\n' "$target" "$source" >&2
      return 1
    fi
    return 0
  fi
  if [ -e "$target" ]; then
    return 0
  fi
  if [ ! -d "$source" ]; then
    printf 'Error: canonical virtualenv not found at %s.\n' "$source" >&2
    return 1
  fi
  ln -s "$source" "$target"
}

clear_codex_launcher_rollover_env() {
  unset CODEX_LAUNCHER_ROLLOVER_AGENT
  unset CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID
  unset CODEX_LAUNCHER_ROLLOVER_ID
}

resolve_codex_pending_rollover() {
  local project_dir="$1"
  local handoff_agent="$2"
  local python_bin="$project_dir/.venv/bin/python"
  local handoff_script="$project_dir/scripts/orchestration/thread_handoff.py"
  local detect_output=""
  local detect_rc=0
  local parsed=""
  local status=""
  local packet_agent=""
  local lineage_id=""
  local rollover_id=""
  local native_title_supported=""
  local title_state=""
  local replacement_task_id=""

  clear_codex_launcher_rollover_env

  if [ ! -x "$python_bin" ] || [ ! -f "$handoff_script" ]; then
    printf 'Error: Codex rollover preflight is unavailable under %s.\n' "$project_dir" >&2
    return 1
  fi

  detect_output="$(
    "$python_bin" "$handoff_script" --repo-root "$project_dir" \
      detect --agent "$handoff_agent" --format json 2>&1
  )" || detect_rc=$?
  if [ "$detect_rc" -ne 0 ]; then
    printf 'Error: Codex rollover preflight refused launch for %s.\n' "$handoff_agent" >&2
    printf '%s\n' "$detect_output" >&2
    return 1
  fi

  if ! parsed="$(
    printf '%s' "$detect_output" | "$python_bin" -c '
import json
import re
import sys

payload = json.load(sys.stdin)
status = payload.get("status")
if status == "none":
    print("none")
    raise SystemExit(0)
if status not in {"pending_start", "resumed"}:
    raise SystemExit(f"unexpected rollover status: {status!r}")

fields = {
    "packet_agent": payload.get("packet_agent"),
    "lineage_id": payload.get("lineage_id"),
    "rollover_id": payload.get("rollover_id"),
}
for name, value in fields.items():
    if not isinstance(value, str) or not value or any(char in value for char in "\t\r\n"):
        raise SystemExit(f"invalid {name} in rollover preflight")

if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", fields["packet_agent"]):
    raise SystemExit("invalid packet_agent in rollover preflight")
if not re.fullmatch(r"lineage-[a-z0-9][a-z0-9-]{0,63}", fields["lineage_id"]):
    raise SystemExit("invalid lineage_id in rollover preflight")
if not re.fullmatch(r"rollover-[a-z0-9][a-z0-9-]{0,63}", fields["rollover_id"]):
    raise SystemExit("invalid rollover_id in rollover preflight")

transition = payload.get("title_transition")
identity = payload.get("identity")
if not isinstance(transition, dict) or not isinstance(identity, dict):
    raise SystemExit("rollover preflight is missing task identity state")
native = transition.get("native_title_supported")
if not isinstance(native, bool):
    raise SystemExit("rollover preflight has invalid native-title capability")
title_state = transition.get("state")
if not isinstance(title_state, str) or any(char in title_state for char in "\t\r\n"):
    raise SystemExit("rollover preflight has invalid title state")
replacement = identity.get("replacement_task_id")
if replacement is not None and (
    not isinstance(replacement, str) or any(char in replacement for char in "\t\r\n")
):
    raise SystemExit("rollover preflight has invalid replacement task ID")

print(
    "\t".join(
        [
            status,
            fields["packet_agent"],
            fields["lineage_id"],
            fields["rollover_id"],
            "true" if native else "false",
            title_state,
            replacement or "",
        ]
    )
)
'
  )"; then
    printf 'Error: Codex rollover preflight returned malformed state.\n' >&2
    printf '%s\n' "$detect_output" >&2
    return 1
  fi

  IFS=$'\t' read -r status packet_agent lineage_id rollover_id \
    native_title_supported title_state replacement_task_id <<< "$parsed"
  if [ "$status" = "none" ]; then
    printf 'Rollover preflight: no pending packet for %s; starting a fresh task.\n' \
      "$handoff_agent"
    return 0
  fi
  if [ "$status" = "resumed" ]; then
    printf 'Error: rollover %s is already resumed; refusing to reuse it for a new Codex task.\n' \
      "$rollover_id" >&2
    return 1
  fi
  if [ "$native_title_supported" != "false" ]; then
    printf 'Error: rollover %s requires its native app adapter; Codex CLI will not bind it.\n' \
      "$rollover_id" >&2
    return 1
  fi
  if [ "$title_state" != "awaiting_replacement_binding" ] \
    || [ -n "$replacement_task_id" ]; then
    printf 'Error: rollover %s is not a fresh unbound CLI packet; refusing launch.\n' \
      "$rollover_id" >&2
    return 1
  fi

  export CODEX_LAUNCHER_ROLLOVER_AGENT="$packet_agent"
  export CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID="$lineage_id"
  export CODEX_LAUNCHER_ROLLOVER_ID="$rollover_id"
  printf 'Rollover preflight: exact fresh packet %s / %s.\n' \
    "$lineage_id" "$rollover_id"
}

verify_codex_pending_rollover() {
  local project_dir="$1"
  local handoff_agent="$2"
  local expected_agent="$3"
  local expected_lineage_id="$4"
  local expected_rollover_id="$5"

  if ! resolve_codex_pending_rollover "$project_dir" "$handoff_agent"; then
    return 1
  fi
  if [ "${CODEX_LAUNCHER_ROLLOVER_AGENT:-}" != "$expected_agent" ] \
    || [ "${CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID:-}" != "$expected_lineage_id" ] \
    || [ "${CODEX_LAUNCHER_ROLLOVER_ID:-}" != "$expected_rollover_id" ]; then
    printf 'Error: exact Codex rollover changed between launcher preflight and SessionStart.\n' >&2
    return 1
  fi
}

bootstrap_codex_checkout() {
  local canonical_root="$1"
  local worktree_root="$2"
  local deploy_failure_policy="${3:-fail}"
  local deploy_helper="$worktree_root/scripts/lib/deploy_extensions.sh"

  ensure_codex_venv_link "$canonical_root" "$worktree_root" || return 1
  ensure_thread_rollover_link "$canonical_root" "$worktree_root" || return 1

  if [ ! -f "$deploy_helper" ]; then
    printf 'Error: Codex deploy helper not found at %s.\n' "$deploy_helper" >&2
    return 1
  fi
  # shellcheck disable=SC1090
  source "$deploy_helper"
  local deploy_exit=0
  deploy_agent_extensions "$worktree_root" agents:deploy || deploy_exit=$?
  if [ "$deploy_exit" -eq 0 ]; then
    return 0
  fi

  if [ "$deploy_failure_policy" = "continue" ]; then
    echo "Continuing launch despite deploy failure (see banner above)."
    return 0
  fi
  return "$deploy_exit"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  if [ "$#" -ne 2 ]; then
    echo "Usage: bash scripts/lib/thread_rollover_link.sh <canonical-repo-root> <checkout-root>" >&2
    exit 2
  fi
  bootstrap_codex_checkout "$1" "$2"
fi
