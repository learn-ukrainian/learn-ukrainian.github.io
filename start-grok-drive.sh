#!/bin/bash
# Grok 4.5 in DRIVER mode for an epic lane.
#   ./start-grok-drive.sh <epic> [extra flags]      e.g.  ./start-grok-drive.sh atlas
# Which epic routes to which model? -> docs/runbooks/epic-orchestrator-roster.md
# Thin wrapper over start-grok.sh. The driver should load the `drive-epic` skill —
# automatic once the cold-prompt wiring lands (follow-up PR); invoke $drive-epic
# manually until then. This wrapper does NOT itself force the skill to load.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ $# -lt 1 ]; then
  echo "usage: $(basename "$0") <epic> [flags]" >&2
  echo "  epics: harness  atlas  hramatka  bio  folk  corpus  (see docs/runbooks/epic-orchestrator-roster.md)" >&2
  exit 2
fi
EPIC="$1"; shift
exec "$ROOT/start-grok.sh" --epic "$EPIC" "$@"
