#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# Model/effort: driver defaults to claude-opus-5-5[1m] at high effort; the Claude cap
# guard refuses any launch at >=90% weekly and drops a defaulted Opus to Sonnet at >=80%.
# Override with --model / --effort or LAUNCHER_MODEL / LAUNCHER_EFFORT;
# command-line options take precedence over the environment defaults.
launcher_main claude driver "$@"
