#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"

# Launcher drivers use Opus 5.5[1m] at high by default (launcher_defaults).
# Ignore settings advisorModel for drivers; interactive sessions keep it.
# The Haiku junior coder's fleet advisory envelope is a separate contract.
export CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1
launcher_main claude driver "$@"
