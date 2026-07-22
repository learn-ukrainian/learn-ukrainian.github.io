#!/bin/bash
# Claude (Opus 4.8 default) in DRIVER mode for an epic lane.
#   ./start-claude-drive.sh <epic> [extra flags]    e.g.  ./start-claude-drive.sh bio
# Which epic routes to which model? -> docs/runbooks/epic-orchestrator-roster.md
# Thin wrapper over start-claude.sh; --epic pins the lane + handoff slot and the
# SessionStart hook cold-starts the driver. For a curriculum track add
# `--agent curriculum-track-orchestrator` (cf. scripts/start-bio-driver.sh).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ $# -lt 1 ]; then
  echo "usage: $(basename "$0") <epic> [flags]" >&2
  echo "  epics: harness  atlas  hramatka  bio  folk  corpus  (see docs/runbooks/epic-orchestrator-roster.md)" >&2
  exit 2
fi
EPIC="$1"; shift
exec "$ROOT/start-claude.sh" --epic "$EPIC" "$@"
