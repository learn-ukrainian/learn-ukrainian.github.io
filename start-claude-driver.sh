#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# Model/effort: driver defaults to claude-opus-5-5[1m] at high effort.
# Opus is always blocked: defaulted Opus switches to claude-sonnet-5-5 and
# explicit Opus is refused. All Claude launches stop at 99% weekly used.
# LU_CLAUDE_CAP_OVERRIDE=1 bypasses only the 99% stop, with a warning.
# LU_MONITOR_LOOPBACK configures telemetry; unknown usage warns and allows launch.
# Override with --model / --effort or LAUNCHER_MODEL / LAUNCHER_EFFORT;
# command-line options take precedence over the environment defaults.
launcher_main claude driver "$@"
