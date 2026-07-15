#!/bin/bash
# Launch interactive Codex from the repository's canonical main checkout.

set -euo pipefail

export PATH="$HOME/.local/bin:/opt/homebrew/bin:${PATH:-}"
# Avoid optional index refresh locks while the primary checkout is used for
# orientation. Task writes still belong in scoped dispatch worktrees.
export GIT_OPTIONAL_LOCKS=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_COMMON_DIR="$(git -C "$SCRIPT_DIR" rev-parse --path-format=absolute --git-common-dir)"
PROJECT_DIR="$(dirname "$GIT_COMMON_DIR")"

if [ "$(git -C "$PROJECT_DIR" branch --show-current)" != "main" ]; then
    printf 'Error: canonical checkout must be on main: %s\n' "$PROJECT_DIR" >&2
    exit 1
fi

# Keep generated Codex config and the canonical rollover state ready before
# replacing this wrapper process with the interactive CLI.
# PROJECT_DIR is resolved dynamically.
# shellcheck disable=SC1091
source "$PROJECT_DIR/scripts/lib/thread_rollover_link.sh"
bootstrap_codex_checkout "$PROJECT_DIR" "$PROJECT_DIR" continue

export CODEX_SESSION=1
export CODEX_CANONICAL_REPO_ROOT="$PROJECT_DIR"

printf 'Starting Codex in %s\n' "$PROJECT_DIR"
exec codex \
    --dangerously-bypass-approvals-and-sandbox \
    --search \
    --enable multi_agent \
    -C "$PROJECT_DIR" \
    "$@"
