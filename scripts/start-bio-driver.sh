#!/usr/bin/env bash
# Launch a Claude session as the BIO-EPIC (curriculum-track) DRIVER — NOT the main orchestrator.
# Uses the curriculum-track-orchestrator agent, whose initialPrompt disregards the orchestrator
# cold-start and bootstraps from .claude/bio-epic/CLAUDE-DRIVER-HANDOFF.md instead
# (gitignored local state — driver handoffs are out of git/PRs, user policy 2026-06-23).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"
# The agent is a provider argument, so launcher options parse as for
# start-claude.sh. It leads the caller's provider arguments, added once even
# when scope re-entry replays this wrapper (#9624).
LC_WRAPPER_PROVIDER_ARGS=(--agent curriculum-track-orchestrator)
launcher_main claude interactive "$@"
