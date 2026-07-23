#!/usr/bin/env bash
# Read-only wakeup watcher for harness Monitor-equivalent tools.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/../.." && pwd -P)"

PYTHONPATH="$repo_root/scripts${PYTHONPATH:+:$PYTHONPATH}" \
  exec "$repo_root/.venv/bin/python" -m ai_agent_bridge._inbox_watch "$@"
