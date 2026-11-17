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

# Model/effort: driver defaults to claude-opus-5-5[1m] at high effort.
# Opus is always blocked here: defaulted Opus switches to claude-sonnet-5-5 and
# explicit Opus is refused. Only start-claude-cto.sh on the epics lane permits
# explicit CLI Opus without --force. All Claude launches stop at 99% weekly used.
# LU_CLAUDE_CAP_OVERRIDE=1 bypasses only the 99% stop, with a warning.
# LU_MONITOR_LOOPBACK configures telemetry; unknown usage warns and allows launch.
# Override with --model / --effort or LAUNCHER_MODEL / LAUNCHER_EFFORT;
# command-line options take precedence over the environment defaults.
launcher_main claude driver "$@"
