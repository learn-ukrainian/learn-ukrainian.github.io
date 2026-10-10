#!/usr/bin/env bash
# Resolve the canonical interpreter explicitly, including linked worktrees (#9484).
set -euo pipefail
trap 'printf "%s\n" "BLOCKED: guard wrapper failed; repair the hook environment" >&2; exit 2' ERR
HOOKS_DIR="$(cd "$(dirname "$0")" && pwd)"
case "${1:-}" in
    guard-pr-merge.py|guard-branch-switch-in-main.py|guard-admin-merge.py) ;;
    *) printf '%s\n' 'BLOCKED: unknown guard hook' >&2; exit 2 ;;
esac
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || PROJECT_ROOT=""
fi
HOOK_PYTHON=""
if [ -d "$PROJECT_ROOT" ] && [ -f "$PROJECT_ROOT/scripts/lib/project_interpreter.sh" ]; then
    # Isolate helper errors (including exit) so none can become an allow exit.
    HOOK_PYTHON="$(source "$PROJECT_ROOT/scripts/lib/project_interpreter.sh" && project_interpreter_resolve "$PROJECT_ROOT")" || HOOK_PYTHON=""
fi
if [ -z "$HOOK_PYTHON" ] || [ ! -x "$HOOK_PYTHON" ]; then
    # The hook's dependency-free raw gate keeps unrelated commands and repair
    # usable. Guarded commands refuse on missing modules or mismatched PINS.
    HOOK_PYTHON="$(command -v python3)" || {
        printf '%s\n' 'BLOCKED: no guard interpreter; repair: uv sync the canonical project environment' >&2
        exit 2
    }
fi
if "$HOOK_PYTHON" "$HOOKS_DIR/$1"; then
    exit 0
else
    status=$?
    if [ "$status" -eq 2 ]; then
        exit 2
    fi
    printf '%s\n' 'BLOCKED: guard failed; repair: uv sync the canonical project environment and npm run agents:deploy' >&2
    exit 2
fi
