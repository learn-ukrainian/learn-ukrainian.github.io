#!/usr/bin/env bash
# Canonical thread-rollover state is shared deliberately across linked worktrees.

ensure_thread_rollover_link() {
  local canonical_root="$1"
  local worktree_root="$2"
  local source="$canonical_root/.agent/thread-rollovers"
  local target="$worktree_root/.agent/thread-rollovers"

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
