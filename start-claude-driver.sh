#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# Model/effort: driver defaults to claude-opus-5-5[1m] at high effort.
# At LU_CLAUDE_OPUS_MAX_PCT (default 80), defaulted Opus switches to Sonnet;
# explicit Opus is refused. All Claude launches stop at LU_CLAUDE_STOP_PCT
# (default 90). LU_CLAUDE_CAP_OVERRIDE=1 bypasses usage limits with a warning.
# LU_MONITOR_LOOPBACK configures telemetry; unknown usage warns and allows launch.
# Override with --model / --effort or LAUNCHER_MODEL / LAUNCHER_EFFORT;
# command-line options take precedence over the environment defaults.
launcher_main claude driver "$@"
