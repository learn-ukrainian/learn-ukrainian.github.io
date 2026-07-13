#!/usr/bin/env bash
# Bootstrap Codex checkouts without copying provider history or the .agent tree.

ensure_thread_rollover_link() {
  local canonical_root="$1"
  local worktree_root="$2"
  local source="$canonical_root/.agent/thread-rollovers"
  local target="$worktree_root/.agent/thread-rollovers"

  if [ "$canonical_root" = "$worktree_root" ]; then
    mkdir -p "$source"
    return 0
  fi

  mkdir -p "$source" "$worktree_root/.agent"
  if [ -L "$target" ]; then
    if [ "$(readlink "$target")" != "$source" ]; then
      printf 'Error: rollover symlink at %s points somewhere other than %s.\n' "$target" "$source" >&2
      return 1
    fi
    return 0
  fi
  if [ -e "$target" ]; then
    printf 'Error: real or broken rollover path at %s blocks canonical state sharing.\n' "$target" >&2
    return 1
  fi
  ln -s "$source" "$target"
}

ensure_codex_venv_link() {
  local canonical_root="$1"
  local worktree_root="$2"
  local source="$canonical_root/.venv"
  local target="$worktree_root/.venv"

  if [ "$canonical_root" = "$worktree_root" ]; then
    return 0
  fi
  if [ -L "$target" ]; then
    if [ "$(readlink "$target")" != "$source" ]; then
      printf 'Error: virtualenv symlink at %s points somewhere other than %s.\n' "$target" "$source" >&2
      return 1
    fi
    return 0
  fi
  if [ -e "$target" ]; then
    return 0
  fi
  if [ ! -d "$source" ]; then
    printf 'Error: canonical virtualenv not found at %s.\n' "$source" >&2
    return 1
  fi
  ln -s "$source" "$target"
}

bootstrap_codex_checkout() {
  local canonical_root="$1"
  local worktree_root="$2"
  local deploy_failure_policy="${3:-fail}"
  local deploy_helper="$worktree_root/scripts/lib/deploy_extensions.sh"

  ensure_codex_venv_link "$canonical_root" "$worktree_root" || return 1
  ensure_thread_rollover_link "$canonical_root" "$worktree_root" || return 1

  if [ ! -f "$deploy_helper" ]; then
    printf 'Error: Codex deploy helper not found at %s.\n' "$deploy_helper" >&2
    return 1
  fi
  # shellcheck disable=SC1090
  source "$deploy_helper"
  local deploy_exit=0
  deploy_agent_extensions "$worktree_root" agents:deploy || deploy_exit=$?
  if [ "$deploy_exit" -eq 0 ]; then
    return 0
  fi

  if [ "$deploy_failure_policy" = "continue" ]; then
    echo "Continuing launch despite deploy failure (see banner above)."
    return 0
  fi
  return "$deploy_exit"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  if [ "$#" -ne 2 ]; then
    echo "Usage: bash scripts/lib/thread_rollover_link.sh <canonical-repo-root> <checkout-root>" >&2
    exit 2
  fi
  bootstrap_codex_checkout "$1" "$2"
fi
