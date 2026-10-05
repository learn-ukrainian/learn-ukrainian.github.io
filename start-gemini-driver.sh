#!/usr/bin/env bash
set -euo pipefail
# Compatibility stub: the shared core refuses every AGY/Gemini driver launch
# before startup. Keep this entrypoint so existing callers get the same reason.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"
LC_ROOT="$ROOT"
LC_PROVIDER=gemini
LC_MODE=driver
launcher_defaults
launcher_refuse_gemini_driver
