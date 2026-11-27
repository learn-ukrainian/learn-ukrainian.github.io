#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "[project-python] ERROR: missing Python command arguments" >&2
  exit 2
fi

# The deployment, never the interpreter under check, decides whether the host binding governs
# (machinery#1531): it does when LU_HOST_CONTEXT is present or the protected default binding of
# lu_machinery.host_context exists. Then only the bound LU_PYTHON locates the machinery library,
# and a release without the binding check is refused. Otherwise the legacy configuration selects
# the interpreter, as before. Git metadata never selects either.
if [[ -n "${LU_HOST_CONTEXT+set}" || -e /etc/machinery/host.v1.json || -L /etc/machinery/host.v1.json ]]; then
  host_bound=1 interpreter_setting=LU_PYTHON
  bootstrap_python="${LU_PYTHON:-}"
else
  host_bound=0 interpreter_setting=LEARN_UKRAINIAN_PYTHON
  bootstrap_python="${LEARN_UKRAINIAN_PYTHON:-${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:+$LEARN_UKRAINIAN_PRIMARY_REPO_ROOT/.venv/bin/python}}"
fi
case "$bootstrap_python" in
  /*) ;;
  *) echo "Set $interpreter_setting to an absolute trusted interpreter path" >&2; exit 2 ;;
esac
source "$("$bootstrap_python" -I -c 'from lu_machinery.common.repo_root import machinery_path; print(machinery_path("lib/project_interpreter.sh"))')"
if declare -F project_host_context >/dev/null; then
  # The release validates the binding and names the interpreter; without a binding, or with an
  # invalid one, it refuses with its reason on stderr before Python starts.
  project_host_context || exit 127
  exec "$LU_PYTHON" "$@"
fi
if (( host_bound )); then
  echo "[project-python] ERROR [host_binding_unsupported]: the LU_PYTHON release predates the host binding this host requires" >&2
  exit 127
fi
# An earlier release validates the worktree backlinks and selects only the primary interpreter.
if ! project_hook_context_resolve; then
  echo "[project-python] ERROR: project context unavailable" >&2
  exit 127
fi
exec "$LEARN_UKRAINIAN_PYTHON" "$@"
