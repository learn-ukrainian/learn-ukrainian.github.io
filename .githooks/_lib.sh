#!/usr/bin/env bash
# Shared path and runtime helpers for the tracked Git hook chain.

set -euo pipefail

hook_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
worktree_root="$(git rev-parse --show-toplevel)"
git_common_dir="$(git rev-parse --git-common-dir)"
if [[ "$git_common_dir" != /* ]]; then
  git_common_dir="$worktree_root/$git_common_dir"
fi
main_root="$(cd "$git_common_dir/.." && pwd -P)"

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
# owned paths; settlement still refuses such a delivery (#12113). Work outside a task skips it.
check_owned_paths() {
  if [[ -z "${LEARN_UKRAINIAN_DISPATCH_TASK_ID:-}" || ! -f "$source_root/scripts/dispatcher/ownership.py" ]]; then
    return 0
  fi
  (cd "$source_root" && run_project_python -m scripts.dispatcher.ownership --worktree "$worktree_root" "$@")
}

require_git_lfs() {
  if ! command -v git-lfs >/dev/null 2>&1; then
    echo "Git hook error: this repository uses Git LFS, but git-lfs is not installed." >&2
    exit 2
  fi
}
