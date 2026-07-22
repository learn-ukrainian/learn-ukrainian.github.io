#!/bin/bash
# Gemini 3.6 Flash (AGY) in DRIVER mode for an epic lane.
#   ./start-gemini-drive.sh <epic> [extra flags]    e.g.  ./start-gemini-drive.sh harness
# Which epic routes to which model? -> docs/runbooks/epic-orchestrator-roster.md
# Thin wrapper over start-gemini.sh; the driver runs the `drive-epic` skill.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ $# -lt 1 ]; then
  echo "usage: $(basename "$0") <epic> [flags]" >&2
  echo "  epics: harness  atlas  hramatka  bio  folk  corpus  (see docs/runbooks/epic-orchestrator-roster.md)" >&2
  exit 2
fi
EPIC="$1"; shift
exec "$ROOT/start-gemini.sh" --epic "$EPIC" "$@"
