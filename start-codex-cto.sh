#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# CTO coordination uses the registered epics driver lane, without takeover.
for arg in "$@"; do
  case "$arg" in
    --) break ;;
    --force) launcher_error "CTO launchers reject --force; run --help."; exit 2 ;;
    -h|--help)
      printf 'CTO defaults: --epic epics --model gpt-6.1-sol --effort high. --force is refused.\n'
      ;;
  esac
done
# The lane is a fixed wrapper option: scope re-entry and successors replay the
# caller's argv, and this wrapper adds it exactly once.
LC_WRAPPER_LAUNCHER_ARGS=(--epic epics)
LAUNCHER_MODEL="${LAUNCHER_MODEL:-gpt-6.1-sol}" \
LAUNCHER_EFFORT="${LAUNCHER_EFFORT:-high}" \
launcher_main codex driver "$@"
