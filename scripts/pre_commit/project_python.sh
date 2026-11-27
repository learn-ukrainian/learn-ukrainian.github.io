#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "[project-python] ERROR: missing Python command arguments" >&2
  exit 2
fi

# The configured interpreter locates the installed machinery library; Git metadata never selects
# it. LU_PYTHON is its canonical name (machinery#1531); a host-bound release refuses a legacy
# LEARN_UKRAINIAN_PYTHON that disagrees with the binding.
bootstrap_python="${LEARN_UKRAINIAN_PYTHON:-${LU_PYTHON:-${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:+$LEARN_UKRAINIAN_PRIMARY_REPO_ROOT/.venv/bin/python}}}"
case "$bootstrap_python" in
  /*) ;;
  *) echo "Set LU_PYTHON to an absolute trusted interpreter path" >&2; exit 2 ;;
esac
source "$("$bootstrap_python" -I -c 'from lu_machinery.common.repo_root import machinery_path; print(machinery_path("lib/project_interpreter.sh"))')"
if declare -F project_host_context >/dev/null; then
  # A host-bound release validates the binding and names the interpreter; it refuses, with its
  # reason on stderr, before Python starts.
  project_host_context || exit 127
  exec "$LU_PYTHON" "$@"
fi
# An earlier release validates the worktree backlinks and selects only the primary interpreter;
# its shell resolver reads only the legacy alias.
export LEARN_UKRAINIAN_PYTHON="${LEARN_UKRAINIAN_PYTHON:-${LU_PYTHON:-}}"
if ! project_hook_context_resolve; then
  echo "[project-python] ERROR: project context unavailable" >&2
  exit 127
fi
exec "$LEARN_UKRAINIAN_PYTHON" "$@"
