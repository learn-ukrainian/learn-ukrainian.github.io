#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LU_PRODUCT_ROOT="$ROOT"
bootstrap_python="${LEARN_UKRAINIAN_PYTHON:-${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:+$LEARN_UKRAINIAN_PRIMARY_REPO_ROOT/.venv/bin/python}}"
case "$bootstrap_python" in
  /*) ;;
  *) echo "Set LEARN_UKRAINIAN_PYTHON to an absolute trusted interpreter path" >&2; exit 2 ;;
esac
source "$("$bootstrap_python" -I -c 'from lu_machinery.common.repo_root import machinery_path; print(machinery_path("lib/launcher_core.sh"))')"

# Model/effort: inject only when --model / --effort (or LAUNCHER_MODEL /
# LAUNCHER_EFFORT) are set. Otherwise Claude Code resolves its model from
# settings (repository default: Sonnet 5.5 + Opus 5.5 advisor) or a resumed
# session. Explicit named agents stay pinned; the driver launcher pins Opus.
launcher_main claude interactive "$@"
