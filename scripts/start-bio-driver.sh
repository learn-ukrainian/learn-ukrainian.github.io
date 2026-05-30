#!/bin/bash
# Launch a Claude session as the BIO-EPIC (curriculum-track) DRIVER — NOT the main orchestrator.
# Uses the curriculum-track-orchestrator agent, whose initialPrompt disregards the orchestrator
# cold-start and bootstraps from docs/bio-epic/CLAUDE-DRIVER-HANDOFF.md instead.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/start-claude.sh" --agent curriculum-track-orchestrator "$@"
