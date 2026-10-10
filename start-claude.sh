#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# Model/effort: inject only when --model / --effort (or LAUNCHER_MODEL /
# LAUNCHER_EFFORT) are set. Otherwise Claude Code resolves its model from
# settings (repository default: Sonnet 5.5 + Opus 5.5 advisor) or a resumed
# session. Explicit named agents stay pinned; the driver launcher pins Opus.
launcher_main claude interactive "$@"
