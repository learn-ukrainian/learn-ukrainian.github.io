#!/usr/bin/env bash
# Verify that scripts/deploy_prompts.sh produced destination trees that
# match the source extensions it actually manages.
#
# Run this after scripts/deploy_prompts.sh. It does not run the deploy.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

check_pair() {
    local src="$1"
    local dst="$2"
    shift 2

    local diff_args=(-rq -x .DS_Store)
    local orphan
    for orphan in "$@"; do
        diff_args+=(-x "${orphan%/}")
    done

    if [[ ! -d "$src" ]]; then
        echo "::error::Source dir missing: $src"
        return 1
    fi

    if [[ ! -d "$dst" ]]; then
        echo "::error::Deploy did not create target: $dst"
        return 1
    fi

    local diff_out
    diff_out=$(diff "${diff_args[@]}" "$src" "$dst" || true)
    if [[ -n "$diff_out" ]]; then
        echo "::error::Deploy-script drift between $src and $dst:"
        echo "$diff_out"
        echo
        echo "This means scripts/deploy_prompts.sh is out of sync with its source."
        echo "Fix the deploy script, not the target tree."
        return 1
    fi

    echo "OK: $src -> $dst"
}

drift=0

# These pairs and orphan exclusions must stay in lock-step with the
# rsync calls and ORPHAN_PATHS_* declarations in scripts/deploy_prompts.sh.
check_pair "claude_extensions" ".claude" "scheduled_tasks.lock" "worktrees" || drift=1
check_pair "claude_extensions" ".agent" "wake" "cache" || drift=1
check_pair "gemini_extensions" ".gemini" "docs/" || drift=1

exit "$drift"
