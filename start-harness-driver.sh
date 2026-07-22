#!/bin/bash
# HARNESS / infra lane driver — default seat: Gemini 3.6 Flash (AGY).
# Scope: infra & fleet reliability — hooks, deps, dispatch, routing (stream infra-harness #4707).
# The name says it: run this to drive the harness lane. No params to remember.
#
# Thin wrapper over start-gemini.sh (peer of start-bio-driver.sh); forwards any extra
# flags. The driver runs the model-agnostic `drive-epic` skill to orchestrate its lane.
# To drive harness on a different seat instead: ./start-<model>.sh --epic harness
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/start-gemini.sh" --epic harness "$@"
