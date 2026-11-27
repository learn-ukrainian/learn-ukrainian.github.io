#!/usr/bin/env bash
# Shared path and runtime helpers for the tracked Git hook chain.

set -euo pipefail

hook_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
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
worktree_root='' main_root=''
if declare -F project_host_context >/dev/null; then
  # The release validates the binding, then names the interpreter, the invocation checkout and
  # its primary; without a binding, or with an invalid one, it refuses with its reason on stderr.
  project_host_context --require-checkout || exit 127
  if [[ -z "$worktree_root" || -z "$main_root" ]]; then
    echo "Git hook error [missing_checkout_binding]: the host binding named no checkout." >&2
    exit 127
  fi
elif (( host_bound )); then
  echo "Git hook error [host_binding_unsupported]: the LU_PYTHON release predates the host binding this host requires." >&2
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
