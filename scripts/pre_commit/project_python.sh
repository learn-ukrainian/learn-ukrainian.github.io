#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "[project-python] ERROR: missing Python command arguments" >&2
  exit 2
fi

# The host binding (machinery#1531) governs when LU_HOST_CONTEXT is present, when the protected
# default binding of lu_machinery.host_context exists, or when the canonical LU_PYTHON carries a
# release that checks the binding; a signal only ever adds the requirement. Then only LU_PYTHON
# locates the machinery library. A release that predates the check keeps its legacy validation
# only while the binding declares that interpreter and release as the host's runtime; otherwise
# it is refused. Without a binding, the legacy alias, then the primary checkout's interpreter,
# then LU_PYTHON locate the library, as on 0.1.82. Git metadata never selects any of them.
machinery_library() {
  "$1" -I -c 'from lu_machinery.common.repo_root import machinery_path; print(machinery_path("lib/project_interpreter.sh"))'
}
host_context_file="${LU_HOST_CONTEXT-/etc/machinery/host.v1.json}"
binding_declares_runtime() {
  "$1" -I -c 'import importlib.metadata, json, sys
with open(sys.argv[2], encoding="utf-8") as stream:
    runtime = json.load(stream)["runtime"]
current = runtime["python"] == sys.argv[1] and runtime["lu_machinery"] == importlib.metadata.version("lu-machinery")
raise SystemExit(0 if current else 1)' "$1" "$host_context_file" </dev/null >/dev/null 2>&1
}
host_bound=0 library=''
if [[ -n "${LU_HOST_CONTEXT+set}" || -e /etc/machinery/host.v1.json || -L /etc/machinery/host.v1.json ]]; then
  host_bound=1
elif [[ "${LU_PYTHON:-}" = /* && -f "$LU_PYTHON" && -x "$LU_PYTHON" ]] \
  && library="$(machinery_library "$LU_PYTHON" 2>/dev/null)" \
  && (source "$library" && declare -F project_host_context) >/dev/null 2>&1; then
  host_bound=1
fi
if (( host_bound )); then
  interpreter_setting=LU_PYTHON bootstrap_python="${LU_PYTHON:-}"
else
  interpreter_setting=LEARN_UKRAINIAN_PYTHON
  bootstrap_python="${LEARN_UKRAINIAN_PYTHON:-${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:+$LEARN_UKRAINIAN_PRIMARY_REPO_ROOT/.venv/bin/python}}"
  if [[ -z "${LEARN_UKRAINIAN_PYTHON:-}" && -n "${LU_PYTHON:-}" && ( -z "$bootstrap_python" || ! -x "$bootstrap_python" ) ]]; then
    # The 0.1.82 shell resolver reads only the legacy alias.
    interpreter_setting=LU_PYTHON bootstrap_python="$LU_PYTHON"
    export LEARN_UKRAINIAN_PYTHON="$LU_PYTHON"
  fi
fi
case "$bootstrap_python" in
  /*) ;;
  *) echo "Set $interpreter_setting to an absolute trusted interpreter path" >&2; exit 2 ;;
esac
if [[ -z "$library" || "$bootstrap_python" != "${LU_PYTHON:-}" ]]; then
  library="$(machinery_library "$bootstrap_python")"
fi
source "$library"
if declare -F project_host_context >/dev/null; then
  # The release validates the binding and names the interpreter; without a binding, or with an
  # invalid one, it refuses with its reason on stderr before Python starts.
  project_host_context || exit 127
  exec "$LU_PYTHON" "$@"
fi
if (( host_bound )) && ! binding_declares_runtime "$bootstrap_python"; then
  echo "[project-python] ERROR [host_binding_unsupported]: the LU_PYTHON release predates the host binding check, and the binding does not declare it as the host's runtime" >&2
  exit 127
fi
# An earlier release validates the worktree backlinks and selects only the primary interpreter.
if ! project_hook_context_resolve; then
  echo "[project-python] ERROR: project context unavailable" >&2
  exit 127
fi
exec "$LEARN_UKRAINIAN_PYTHON" "$@"
