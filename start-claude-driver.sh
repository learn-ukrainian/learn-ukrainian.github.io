#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# Model/effort: driver defaults to claude-opus-5-5[1m] at high effort.
# Until the weekly reset, LU_CLAUDE_OPUS_BLOCKED=1 (default) switches this
# default to claude-sonnet-5-5 and refuses explicit Opus regardless of usage.
# Every Claude launch is refused at LU_CLAUDE_STOP_PCT (default 99) or above.
# Unknown usage still warns and skips the percentage check; Opus stays blocked.
# Override with --model / --effort or LAUNCHER_MODEL / LAUNCHER_EFFORT;
# command-line options take precedence over the environment defaults.
launcher_main claude driver "$@"
