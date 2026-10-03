#!/usr/bin/env bash
# Resolve the canonical interpreter explicitly, including linked worktrees (#9484).
set -euo pipefail
HOOKS_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"
source "$PROJECT_ROOT/scripts/lib/project_interpreter.sh"
if ! HOOK_PYTHON="$(project_interpreter_resolve "$PROJECT_ROOT")"; then
    printf '%s\n' 'BLOCKED: project interpreter unavailable; repair: uv sync the canonical project environment' >&2
    exit 2
fi
case "${1:-}" in
    guard-pr-merge.py|guard-branch-switch-in-main.py|guard-admin-merge.py) ;;
    *) printf '%s\n' 'BLOCKED: unknown guard hook' >&2; exit 2 ;;
esac
exec "$HOOK_PYTHON" "$HOOKS_DIR/$1"
