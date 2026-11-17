#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "[project-python] ERROR: missing Python command arguments" >&2
  exit 2
fi

# Resolve the invocation checkout before starting Python. The shared resolver
# validates worktree backlinks and selects only the primary interpreter.
helper_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
bootstrap_python="${LEARN_UKRAINIAN_PYTHON:-${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:+$LEARN_UKRAINIAN_PRIMARY_REPO_ROOT/.venv/bin/python}}"
case "$bootstrap_python" in
  /*) ;;
  *) echo "Set LEARN_UKRAINIAN_PYTHON to an absolute trusted interpreter path" >&2; exit 2 ;;
esac
source "$("$bootstrap_python" -I -c 'from lu_machinery.common.repo_root import machinery_path; print(machinery_path("lib/project_interpreter.sh"))')"
if ! project_hook_context_resolve; then
  echo "[project-python] ERROR: project context unavailable" >&2
  exit 127
fi
exec "$LEARN_UKRAINIAN_PYTHON" "$@"
