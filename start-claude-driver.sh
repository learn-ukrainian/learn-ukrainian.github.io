#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# Model/effort: driver defaults to claude-opus-5-5[1m] at high effort.
# Until the weekly reset, defaulted Opus switches to claude-sonnet-5-5;
# explicit Opus is refused regardless of usage. Explicit Sonnet launches below 99%.
# Every Claude launch is refused at 99% or when trusted usage is unavailable.
# Cap limits and telemetry routing cannot be overridden through the environment.
# Override with --model / --effort or LAUNCHER_MODEL / LAUNCHER_EFFORT;
# command-line options take precedence over the environment defaults.
launcher_main claude driver "$@"
