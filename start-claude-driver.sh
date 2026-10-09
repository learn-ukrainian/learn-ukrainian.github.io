#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# Model/effort: default to claude-opus-5-5[1m] at high effort. Override with
# --model / --effort or LAUNCHER_MODEL / LAUNCHER_EFFORT. The interactive
# ./start-claude.sh instead keeps the last TUI/session selection by default.
launcher_main claude driver "$@"
