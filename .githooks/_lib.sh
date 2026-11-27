#!/usr/bin/env bash
# Shared path and runtime helpers for the tracked Git hook chain.

set -euo pipefail

hook_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# The delegator that the release's installer writes supplies LU_PYTHON, the host binding's
# machinery interpreter. Its isolated entry validates the binding before it inspects the
# invocation's Git metadata, then names that checkout and its primary.
if [[ "${LU_PYTHON:-}" != /* || ! -f "$LU_PYTHON" || ! -x "$LU_PYTHON" ]]; then
  printf '%s\n' 'Git hook error [missing_interpreter_binding]: LU_PYTHON must name an absolute executable.' >&2
  exit 127
fi
hook_context="$("$LU_PYTHON" -I -B -m lu_machinery.host_context shell --require-checkout)" || exit 127
worktree_root='' main_root=''
eval "$hook_context"
unset hook_context
if [[ -z "$worktree_root" || -z "$main_root" ]]; then
  printf '%s\n' 'Git hook error [missing_checkout_binding]: the hook entry returned no checkout.' >&2
  exit 127
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
