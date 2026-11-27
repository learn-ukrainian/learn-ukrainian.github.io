#!/usr/bin/env bash
# Shared path and runtime helpers for the tracked Git hook chain.

set -euo pipefail

hook_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# The host binding (machinery#1531) governs when LU_HOST_CONTEXT is present, when the protected
# default binding of lu_machinery.host_context exists, or when the canonical LU_PYTHON carries a
# release that checks the binding; a signal only ever adds the requirement. A canonical LU_PYTHON
# with that check locates the machinery library and validates the binding. Otherwise the legacy
# alias, then the primary checkout's interpreter, then LU_PYTHON locate it, as on 0.1.82; under a
# binding, that interpreter keeps its legacy validation only while the binding declares it and
# its release as the host's runtime, and is refused otherwise. Git metadata never selects any.
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
host_bound=0 canonical_checks_binding=0 library=''
if [[ -n "${LU_HOST_CONTEXT+set}" || -e /etc/machinery/host.v1.json || -L /etc/machinery/host.v1.json ]]; then
  host_bound=1
fi
if [[ "${LU_PYTHON:-}" = /* && -f "$LU_PYTHON" && -x "$LU_PYTHON" ]] \
  && library="$(machinery_library "$LU_PYTHON" 2>/dev/null)" \
  && (source "$library" && declare -F project_host_context) >/dev/null 2>&1; then
  host_bound=1 canonical_checks_binding=1
fi
if (( canonical_checks_binding )); then
  interpreter_setting=LU_PYTHON bootstrap_python="$LU_PYTHON"
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
worktree_root='' main_root=''
if declare -F project_host_context >/dev/null; then
  # The release validates the binding, then names the interpreter, the invocation checkout and
  # its primary; without a binding, or with an invalid one, it refuses with its reason on stderr.
  project_host_context --require-checkout || exit 127
  if [[ -z "$worktree_root" || -z "$main_root" ]]; then
    echo "Git hook error [missing_checkout_binding]: the host binding named no checkout." >&2
    exit 127
  fi
elif (( host_bound )) && ! binding_declares_runtime "$bootstrap_python"; then
  echo "Git hook error [host_binding_unsupported]: the selected interpreter's release predates the host binding check, and the binding does not declare it as the host's runtime." >&2
  exit 127
else
  # An earlier release validates the Git metadata itself; it never trusts commondir for execution.
  worktree_root="$(git rev-parse --show-toplevel)"
  project_hook_context_resolve "$worktree_root" || {
    echo "Git hook error: hook context unavailable (step=${PROJECT_HOOK_BOOTSTRAP_STEP:-unknown}); configure the primary-state anchor and interpreter." >&2
    exit 127
  }
  main_root="$(project_primary_root_resolve "$worktree_root")" || {
    echo "Git hook error: primary checkout unavailable (step=${PROJECT_HOOK_BOOTSTRAP_STEP:-unknown})." >&2
    exit 127
  }
  # Hooks that locate installed machinery resources (post-checkout) use the resolved interpreter.
  bootstrap_python="$LEARN_UKRAINIAN_PYTHON"
fi

source_root="$worktree_root"
if [[ ! -x "$source_root/scripts/pre_commit/project_python.sh" || ! -f "$source_root/.pre-commit-config.yaml" ]]; then
  source_root="$main_root"
fi

project_python="$source_root/scripts/pre_commit/project_python.sh"
if [[ ! -x "$project_python" ]]; then
  echo "Git hook error: project Python launcher not found at $project_python" >&2
  exit 127
fi

run_project_python() {
  bash "$project_python" "$@"
}

run_pre_commit() {
  local hook_type="$1"
  shift
  run_project_python \
    -m pre_commit hook-impl \
    -c "$source_root/.pre-commit-config.yaml" \
    --hook-type "$hook_type" \
    --hook-dir "$hook_dir" \
    -- "$@"
}

# A dispatched write task learns at commit or push time that it changed a path outside its
# owned paths; settlement still refuses such a delivery (#12113). Work outside a task skips
# it. Inside a task the checker is the installed lu-machinery release (pinned in uv.lock);
# -P keeps a stray in-tree package from shadowing it. A checker that cannot be imported refuses
# the commit or push: a missing checker must not skip enforcement.
check_owned_paths() {
  if [[ -z "${LEARN_UKRAINIAN_DISPATCH_TASK_ID:-}" ]]; then
    return 0
  fi
  local import_error
  if ! import_error="$(cd "$source_root" && run_project_python -P -c 'import lu_machinery.dispatcher.ownership' 2>&1 >/dev/null </dev/null)"; then
    echo "Git hook error: owned-path checker is not installed; refusing to skip enforcement." >&2
    [[ -n "$import_error" ]] && echo "  ${import_error##*$'\n'}" >&2
    exit 1
  fi
  (cd "$source_root" && run_project_python -P -m lu_machinery.dispatcher.ownership --worktree "$worktree_root" "$@") || exit 1
}

require_git_lfs() {
  if ! command -v git-lfs >/dev/null 2>&1; then
    echo "Git hook error: this repository uses Git LFS, but git-lfs is not installed." >&2
    exit 2
  fi
}
