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
      # The supported host start (lu-start-cto) always passes --model claude-opus-5-5;
      # without --model the cap guard keeps this wrapper on Sonnet (#12496).
      printf 'CTO defaults (these replace the generic driver defaults below): --epic epics --effort high;\n'
      printf '  --model claude-sonnet-5-5 unless --model is given. lu-start-cto passes --model claude-opus-5-5.\n'
      printf '  --force is refused.\n'
      ;;
  esac
done
# The lane is a fixed wrapper option: scope re-entry and successors replay the
# caller's argv, and this wrapper adds it exactly once.
LC_WRAPPER_LAUNCHER_ARGS=(--epic epics)
LAUNCHER_MODEL="${LAUNCHER_MODEL:-claude-sonnet-5-5}" \
LAUNCHER_EFFORT="${LAUNCHER_EFFORT:-high}" \
launcher_main claude driver "$@"
