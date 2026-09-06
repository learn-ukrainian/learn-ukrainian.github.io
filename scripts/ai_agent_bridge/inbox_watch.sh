#!/usr/bin/env bash
# Inbox notifications and bounded Fleet Comms supervisory wakes.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/../.." && pwd -P)"
source "$repo_root/scripts/lib/session_supervisor.sh"
state_root="$(_canonical_state_root "$repo_root")"

PYTHONPATH="$repo_root/scripts${PYTHONPATH:+:$PYTHONPATH}" \
  exec "$state_root/.venv/bin/python" -m ai_agent_bridge._inbox_watch "$@"
