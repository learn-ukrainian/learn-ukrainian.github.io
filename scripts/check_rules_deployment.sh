#!/usr/bin/env bash
# Verify that scripts/deploy_prompts.sh produced destination trees that
# match the source extensions it actually manages.
#
# Run this after scripts/deploy_prompts.sh. It does not run the deploy.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# shellcheck disable=SC1091
source "$PROJECT_ROOT/scripts/deploy_orphan_paths.sh"

check_pair() {
    local src="$1"
    local dst="$2"
    shift 2

    local diff_args=(-rq -x .DS_Store)
    local orphan
    for orphan in "$@"; do
        diff_args+=(-x "${orphan%/}")
        if [[ "$orphan" == */* ]]; then
            diff_args+=(-x "${orphan##*/}")
        fi
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

check_overlay() {
    local src="$1"
    local dst="$2"

    if [[ ! -d "$src" ]]; then
        echo "::error::Overlay source dir missing: $src"
        return 1
    fi

    if [[ ! -d "$dst" ]]; then
        echo "::error::Deploy did not create target: $dst"
        return 1
    fi

    local diff_out=""
    local rel
    while IFS= read -r rel; do
        if [[ ! -f "$dst/$rel" ]]; then
            diff_out+="Missing deployed overlay file: $dst/$rel"$'\n'
        elif ! cmp -s "$src/$rel" "$dst/$rel"; then
            diff_out+="Deploy-script overlay drift between $src/$rel and $dst/$rel"$'\n'
        fi
    done < <(cd "$src" && find . -type f ! -name '.DS_Store' -print | sed 's#^\./##' | sort)

    if [[ -n "$diff_out" ]]; then
        echo "::error::Deploy-script drift between $src and $dst:"
        echo "$diff_out"
        echo
        echo "This means scripts/deploy_prompts.sh is out of sync with its source overlay."
        return 1
    fi

    echo "OK: $src -> $dst"
}

drift=0

# Orphan exclusions must stay in lock-step with scripts/deploy_orphan_paths.sh
# and the rsync calls in scripts/deploy_prompts.sh. Word-splitting matches deploy.
# shellcheck disable=SC2086
check_pair \
    "agents_extensions/shared" \
    ".claude" \
    $ORPHAN_PATHS_CLAUDE \
    $CLAUDE_RULE_AUTOLOAD_EXCLUDE_PATHS || drift=1
# .agent/ is preserve-by-default (#4741): skip orphan/delete for runtime state
# (handoffs, briefs, canaries, tmp/ etc.), but still verify any source-managed
# overlay from agents_extensions/shared into .agent/.
# shellcheck disable=SC2086
check_overlay "agents_extensions/shared" ".agent" || drift=1
# shellcheck disable=SC2086
check_pair \
    "agents_extensions/shared" \
    ".codex" \
    $ORPHAN_PATHS_CODEX \
    $CODEX_OVERLAY_PATHS || drift=1
check_overlay "agents_extensions/codex" ".codex" || drift=1
# shellcheck disable=SC2086
check_pair "agents_extensions/shared/skills" ".agents/skills" $ORPHAN_PATHS_AGENTS || drift=1
# shellcheck disable=SC2086
check_pair "gemini_extensions" ".gemini" $ORPHAN_PATHS_GEMINI || drift=1
check_pair "agents_extensions/shared/rules" ".gemini/rules" || drift=1

exit "$drift"
