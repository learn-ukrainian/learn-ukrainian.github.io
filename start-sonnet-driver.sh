#!/bin/bash
# Launch a Claude session pinned to Sonnet-5 as a JUDGMENT-DENSE epic driver.
#
# Roster rationale (docs/runbooks/epic-orchestrator-roster.md): Sonnet-5 gives a
# 1M-window, near-Opus judgment driver at much lower cost, WITHOUT consuming the
# scarce Opus review-of-record seat. Use it for incidents, architecture cutovers,
# and contested-review sessions; use start-grok.sh for coordination-dense track
# driving and start-gemini.sh --epic harness for infra.
#
# Thin wrapper over start-claude.sh (peer of scripts/start-bio-driver.sh): it only
# pins --model, then forwards --epic / --agent / everything else. The driver runs
# the model-agnostic `drive-epic` skill to orchestrate its lane.
#
#   ./start-sonnet-driver.sh --epic harness --agent infra-orchestrator
#   ./start-sonnet-driver.sh --epic atlas
#
# Model slug defaults to the model_catalog.yaml id `claude-sonnet-5`; override with
# SONNET_DRIVER_MODEL if the native Claude CLI expects a different slug. The #5512
# cold-start smoke validates the launch end-to-end.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/start-claude.sh" --model "${SONNET_DRIVER_MODEL:-claude-sonnet-5}" "$@"
