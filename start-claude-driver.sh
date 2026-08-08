#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# Model/effort: inject only when --model / --effort (or LAUNCHER_MODEL /
# LAUNCHER_EFFORT) are set. Otherwise Claude Code keeps the last session
# selection — same contract as ./start-claude.sh.
launcher_main claude driver "$@"
