#!/bin/bash
# ATLAS lane driver — Word Atlas + Practice Hub product (stream atlas-practice #4387).
# Default seat: Grok 4.5 (coordination-dense product driving).
# The name says it: run this to drive the atlas lane. No params to remember.
#
# Thin wrapper over start-grok.sh (peer of start-bio-driver.sh); forwards any extra
# flags. The driver runs the model-agnostic `drive-epic` skill to orchestrate its lane.
# To drive atlas on a different seat instead: ./start-<model>.sh --epic atlas
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/start-grok.sh" --epic atlas "$@"
