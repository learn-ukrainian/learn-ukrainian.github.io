#!/bin/bash
# HRAMATKA lane driver — teacher lesson service, user-gated (stream hramatka #4542).
# Default seat: Grok 4.5.
# The name says it: run this to drive the hramatka lane. No params to remember.
#
# Thin wrapper over start-grok.sh (peer of start-bio-driver.sh); forwards any extra
# flags. The driver runs the model-agnostic `drive-epic` skill to orchestrate its lane.
# To drive hramatka on a different seat instead: ./start-<model>.sh --epic hramatka
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/start-grok.sh" --epic hramatka "$@"
