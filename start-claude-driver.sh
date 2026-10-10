#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# Model/effort: driver defaults to claude-opus-5-5[1m] at high effort.
# Override with --model / --effort or LAUNCHER_MODEL / LAUNCHER_EFFORT;
# command-line options take precedence over the environment defaults.
launcher_main claude driver "$@"
