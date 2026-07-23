#!/bin/bash
# Sonnet-5 in DRIVER mode for an allowlisted lane selector (judgment-dense sessions: incidents,
# architecture cutovers, contested reviews).
#   ./start-sonnet-drive.sh <lane-or-lane.topic> [extra flags]
# Which epic routes to which model? -> docs/runbooks/epic-orchestrator-roster.md
# Thin wrapper over start-claude.sh pinned to Sonnet-5 (does NOT consume the Opus
# review seat). The driver should load the `drive-epic` skill — automatic once the
# cold-prompt wiring lands (follow-up PR); invoke $drive-epic manually until then; the
# wrapper does NOT force it. Override the slug with SONNET_DRIVER_MODEL if the native
# Claude CLI expects a different id.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/handoff_identity.sh
source "$ROOT/scripts/lib/handoff_identity.sh"
usage() {
  echo "Usage: $(basename "$0") <lane-or-lane.topic> [Claude flags]"
  launcher_selector_help
}
if [ $# -lt 1 ]; then
  usage >&2
  exit 2
fi
case "$1" in
  --help|--help-launcher|-h)
    usage
    exit 0
    ;;
esac
SELECTOR="$1"; shift
if ! launcher_selector_resolve "$SELECTOR" >/dev/null; then
  echo "Error: unknown lane selector '$SELECTOR'." >&2
  launcher_selector_help >&2
  exit 2
fi
exec "$ROOT/start-claude.sh" --model "${SONNET_DRIVER_MODEL:-claude-sonnet-5}" --epic "$SELECTOR" "$@"
