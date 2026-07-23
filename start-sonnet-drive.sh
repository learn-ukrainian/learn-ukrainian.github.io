#!/bin/bash
# Sonnet-5 in DRIVER mode for an epic lane (judgment-dense sessions: incidents,
# architecture cutovers, contested reviews).
#   ./start-sonnet-drive.sh <epic> [extra flags]    e.g.  ./start-sonnet-drive.sh hramatka
# Which epic routes to which model? -> docs/runbooks/epic-orchestrator-roster.md
# Thin wrapper over start-claude.sh pinned to Sonnet-5 (does NOT consume the Opus
# review seat). The driver should load the `drive-epic` skill — automatic once the
# cold-prompt wiring lands (follow-up PR); invoke $drive-epic manually until then; the
# wrapper does NOT force it. Override the slug with SONNET_DRIVER_MODEL if the native
# Claude CLI expects a different id.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ $# -lt 1 ]; then
  echo "usage: $(basename "$0") <epic> [flags]" >&2
  echo "  epics: harness  infra  devops  atlas  hramatka  bio  folk  corpus  (see docs/runbooks/epic-orchestrator-roster.md)" >&2
  exit 2
fi
EPIC="$1"; shift
exec "$ROOT/start-claude.sh" --model "${SONNET_DRIVER_MODEL:-claude-sonnet-5}" --epic "$EPIC" "$@"
