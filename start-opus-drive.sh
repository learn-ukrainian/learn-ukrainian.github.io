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
# MODEL PIN: we pass the CLI's `opus` ALIAS, not a versioned id. Two reasons:
#   1. The Anthropic lane rotates (Opus 4.6 -> 4.8 -> 5). A pinned id silently points at a
#      retired model — scripts/config/model_catalog.yaml still reads claude-opus-4-8 while
#      the live seat is claude-opus-5. The alias always resolves to the current Opus.
#   2. `opus` matches the `^(opus|sonnet|haiku)$` pattern in scripts/config/context_profiles.yaml,
#      so the session resolves the TRUSTED native_claude profile (1M window) instead of
#      falling back to the untrusted `fallback` profile with a 0-token denominator.
# Pin a specific build with OPUS_DRIVER_MODEL when a rotation needs to be held back.
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
echo "Note: Opus is the fleet's cross-family review-of-record seat (docs/runbooks/epic-orchestrator-roster.md)." >&2
echo "      Driving with it spends that capacity — prefer ./start-sonnet-drive.sh unless this is a hardest-judgment session." >&2
exec "$ROOT/start-claude.sh" --model "${OPUS_DRIVER_MODEL:-opus}" --epic "$SELECTOR" "$@"
