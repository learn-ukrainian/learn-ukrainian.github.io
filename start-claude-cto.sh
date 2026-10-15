#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# Explicit CLI Opus escalation is limited to this wrapper's epics driver lane.
for arg in "$@"; do
  case "$arg" in
    --) break ;;
    --force) launcher_error "CTO launchers reject --force; run --help."; exit 2 ;;
    -h|--help)
      printf 'CTO defaults: --epic epics --model claude-sonnet-5-5 --effort high. --force is refused.\n'
      ;;
  esac
done
# The lane is a fixed wrapper option: scope re-entry and successors replay the
# caller's argv, and this wrapper adds it exactly once.
LC_WRAPPER_LAUNCHER_ARGS=(--epic epics)
LAUNCHER_MODEL="${LAUNCHER_MODEL:-claude-sonnet-5-5}" \
LAUNCHER_EFFORT="${LAUNCHER_EFFORT:-high}" \
launcher_main claude driver "$@"
