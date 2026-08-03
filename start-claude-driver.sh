#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# Default Anthropic driver seat: Opus 5 @ xhigh. Override with --model /
# LAUNCHER_MODEL, or with --effort after --epic (forwarded to `claude`).
export LAUNCHER_MODEL="${LAUNCHER_MODEL:-claude-opus-5}"

has_effort=0
for arg in "$@"; do
  case "$arg" in
    --effort|--effort=*) has_effort=1 ;;
  esac
done

args=("$@")
if [ "$has_effort" = 0 ]; then
  args+=(--effort xhigh)
fi

launcher_main claude driver "${args[@]}"
