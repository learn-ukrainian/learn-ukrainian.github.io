#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# #7416: OpenCode GLM-5.3-Flash (Z.AI Coding Plan subscription), not prepaid.
export GLM_OPENCODE_FLASH=1
source "$ROOT/scripts/lib/launcher_core.sh"
launcher_main glm interactive "$@"
