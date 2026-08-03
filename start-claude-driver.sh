#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# Default Anthropic driver seat: Opus 5 @ xhigh. Override with --model /
# LAUNCHER_MODEL, or with --effort (any position; normalized after the
# selector so launcher_core can forward it to `claude`).
export LAUNCHER_MODEL="${LAUNCHER_MODEL:-claude-opus-5}"

effort_value="xhigh"
args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --effort)
      if [ -z "${2:-}" ] || [[ "${2:-}" == -* ]]; then
        echo "Error: --effort requires a value; run --help." >&2
        exit 2
      fi
      effort_value="$2"
      shift 2
      ;;
    --effort=*)
      effort_value="${1#*=}"
      if [ -z "$effort_value" ]; then
        echo "Error: --effort requires a value; run --help." >&2
        exit 2
      fi
      shift
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done
args+=(--effort "$effort_value")

launcher_main claude driver "${args[@]}"
