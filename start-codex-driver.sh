#!/bin/bash
# Codex driver launcher (sustained driver or bounded governor cycle).
#   Sustained: ./start-codex-driver.sh <lane-or-lane.topic> [extra flags]
#   Governor:  ./start-codex-driver.sh --governor <lane-or-lane.topic|AUTO> [extra flags]
# Which epic routes to which model? -> docs/runbooks/epic-orchestrator-roster.md
# Thin wrapper over start-codex.sh. The driver should load the `drive-epic` skill.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib/handoff_identity.sh"
usage() {
  echo "Usage: $(basename "$0") <lane-or-lane.topic> [Codex flags]"
  echo "       $(basename "$0") --governor <lane-or-lane.topic|AUTO> [Codex flags]"
  launcher_selector_help
}
if [ $# -lt 1 ]; then
  usage >&2
  exit 2
fi

MODE="default"
case "$1" in
  --help|--help-launcher|-h)
    usage
    exit 0
    ;;
  --governor)
    MODE="governor"
    shift
    ;;
esac

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

if [ "$MODE" = "governor" ]; then
  if [ "$SELECTOR" != "AUTO" ]; then
    if ! launcher_selector_resolve "$SELECTOR" >/dev/null; then
      echo "Error: unknown lane selector '$SELECTOR'." >&2
      launcher_selector_help >&2
      exit 2
    fi
  fi
  unset SESSION_EPIC
  PROMPT="Follow agents_extensions/shared/prompts/dynamic-area-epic-fleet-governor.md for one bounded supervision cycle. TARGET=$SELECTOR GOAL=AUTO"
  if [ "${CODEX_DRIVER_DRY_RUN:-0}" = "1" ]; then
    # SESSION_EPIC is echoed so tests can PROVE the lease-claiming path is off
    # (review finding: the unset guard was not observable, so its test was vacuous).
    echo "CODEX_DRIVER_DRY_RUN=1: SESSION_EPIC=${SESSION_EPIC:-<unset>}"
    echo "CODEX_DRIVER_DRY_RUN=1: would exec $ROOT/start-codex.sh --model gpt-5.6-sol \"$PROMPT\" ${*:-}"
    exit 0
  fi
  exec "$ROOT/start-codex.sh" --model gpt-5.6-sol "$PROMPT" "$@"
else
  if ! launcher_selector_resolve "$SELECTOR" >/dev/null; then
    echo "Error: unknown lane selector '$SELECTOR'." >&2
    launcher_selector_help >&2
    exit 2
  fi
  if [ "${CODEX_DRIVER_DRY_RUN:-0}" = "1" ]; then
    echo "CODEX_DRIVER_DRY_RUN=1: would exec $ROOT/start-codex.sh --epic $SELECTOR ${*:-}"
    exit 0
  fi
  exec "$ROOT/start-codex.sh" --epic "$SELECTOR" "$@"
fi
