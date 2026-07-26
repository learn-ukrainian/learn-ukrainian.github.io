#!/bin/bash
# Opus in DRIVER mode for an allowlisted lane selector — the hardest-judgment Anthropic seat
# (contested cross-family verdicts, architecture cutovers, live incidents).
#   ./start-opus-drive.sh <lane-or-lane.topic> [extra flags]
# Which epic routes to which model? -> docs/runbooks/epic-orchestrator-roster.md
#
# Thin wrapper over start-claude.sh, peer of start-sonnet-drive.sh. The driver should load
# the `drive-epic` skill — automatic once the cold-prompt wiring lands (follow-up PR);
# invoke $drive-epic manually until then; the wrapper does NOT force it.
#
# MODEL PIN: claude-fable-5 (operator 2026-07-26 — Fable is the Anthropic judgment seat;
# Opus 5 is neither an advisor nor an orchestrator: weak in the role and over-verbose).
# The wrapper NAME is kept until the renames-last migration step of the taxonomy work.
# Override with OPUS_DRIVER_MODEL when a rotation needs to be held back or tested.
#
# HANDOFF SLOT: both Anthropic wrappers resolve to `claude-<lane>` (handoff_identity_for_epic),
# so an Opus driver and a Sonnet driver on the SAME lane contend for one stream lease and the
# second one fails closed. That is intentional — one Anthropic driver per lane.
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
# Reserved-seat notice (roster "least-bite" logic): Opus is the fleet's cross-family
# review-of-record seat. Driving a lane with it spends that capacity, so say so out loud
# rather than letting a habit-launch quietly consume it. Informational only — never blocks.
echo "Note: Fable 5 is the fleet's judgment/advisor seat (docs/runbooks/epic-orchestrator-roster.md)." >&2
echo "      Summoned cadence only: short judgment sessions, dispatch-heavy. Prefer ./start-grok-drive.sh for daily loops," >&2
echo "      ./start-sonnet-drive.sh for routine Anthropic driving." >&2
exec "$ROOT/start-claude.sh" --model "${OPUS_DRIVER_MODEL:-claude-fable-5}" --epic "$SELECTOR" "$@"
