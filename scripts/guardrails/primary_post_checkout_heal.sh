#!/usr/bin/env bash
# Git post-checkout hook fragment: keep the PRIMARY worktree on main.
#
# Git has already moved HEAD when this runs. If the main worktree is detached
# or on a non-main branch, heal immediately and warn. Added worktrees are
# ignored (feature branches are expected there).
#
# Install via: .venv/bin/python scripts/guardrails/assert_primary_on_main.py
# (or the primary_write_guard install-hooks path). Safe to re-run.

set -euo pipefail

# post-checkout args: previous HEAD, new HEAD, flag (1=branch checkout)
# We do not use them beyond knowing a checkout happened.

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$ROOT" ]; then
  exit 0
fi

# Only act in the main worktree (not .git/worktrees/*)
GIT_DIR="$(git rev-parse --git-dir)"
GIT_COMMON="$(git rev-parse --git-common-dir)"
# Normalize relative paths
GIT_DIR="$(cd "$(dirname "$GIT_DIR")" && pwd)/$(basename "$GIT_DIR")"
GIT_COMMON="$(cd "$(dirname "$GIT_COMMON")" && pwd)/$(basename "$GIT_COMMON")"
if [ "$GIT_DIR" != "$GIT_COMMON" ]; then
  exit 0
fi

if [ ! -f "$ROOT/scripts/guardrails/assert_primary_on_main.py" ]; then
  exit 0
fi

PY="${ROOT}/.venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="python3"
fi

# Heal quietly if broken; always allow the checkout to complete (we already moved).
if ! "$PY" "$ROOT/scripts/guardrails/assert_primary_on_main.py" --cwd "$ROOT" --quiet 2>/dev/null; then
  echo "WARNING: primary left main/detached — auto-healing to main…" >&2
  "$PY" "$ROOT/scripts/guardrails/assert_primary_on_main.py" --cwd "$ROOT" --heal || true
fi

exit 0
