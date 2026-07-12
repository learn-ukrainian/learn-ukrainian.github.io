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
    local orphan normalized
    for orphan in "$@"; do
        normalized="${orphan%/}"
        # A subtree declaration such as skills/* must exclude the subtree
        # root. Passing its basename ("*") to diff would mask every path.
        if [[ "$normalized" == */\* ]]; then
            normalized="${normalized%/\*}"
        fi
        diff_args+=(-x "$normalized")
        if [[ "$normalized" == */* ]]; then
            diff_args+=(-x "${normalized##*/}")
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

check_shared_skill_pairs() {
    local shared_skill skill_name failed=0
    for shared_skill in agents_extensions/shared/skills/*; do
        [[ -d "$shared_skill" ]] || continue
        skill_name="$(basename "$shared_skill")"
        check_pair "$shared_skill" ".gemini/skills/$skill_name" || failed=1
    done
    return "$failed"
}

check_gemini_provider_skill_pairs() {
    local provider_skill skill_name failed=0
    for provider_skill in gemini_extensions/skills/*; do
        [[ -d "$provider_skill" ]] || continue
        skill_name="$(basename "$provider_skill")"
        check_pair "$provider_skill" ".gemini/skills/$skill_name" || failed=1
    done
    return "$failed"
}

check_gemini_skill_owners() {
    local deployed_skill skill_name failed=0
    [[ -d .gemini/skills ]] || return 0
    for deployed_skill in .gemini/skills/*; do
        [[ -d "$deployed_skill" ]] || continue
        skill_name="$(basename "$deployed_skill")"
        if [[ ! -d "agents_extensions/shared/skills/$skill_name" && ! -d "gemini_extensions/skills/$skill_name" ]]; then
            echo "::error::Unowned deployed Gemini skill: .gemini/skills/$skill_name"
            failed=1
        fi
    done
    return "$failed"
}

gemini_path_is_declared_orphan() {
    local relative="$1" orphan normalized
    for orphan in $ORPHAN_PATHS_GEMINI; do
        normalized="${orphan%/}"
        if [[ "$relative" == "$normalized" || "$relative" == "$normalized/"* ]]; then
            return 0
        fi
    done
    return 1
}

check_gemini_file_owners() {
    local deployed_file relative failed=0
    [[ -d .gemini ]] || return 0
    while IFS= read -r deployed_file; do
        relative="${deployed_file#.gemini/}"
        if [[ "$relative" == skills/* || "$relative" == rules/* ]]; then
            continue
        fi
        if gemini_path_is_declared_orphan "$relative"; then
            continue
        fi
        if [[ ! -e "gemini_extensions/$relative" ]]; then
            echo "::error::Unowned deployed Gemini file: .gemini/$relative"
            failed=1
        fi
    done < <(find .gemini \( -type f -o -type l \) -print | sort)
    return "$failed"
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
check_pair \
    "gemini_extensions" \
    ".gemini" \
    $ORPHAN_PATHS_GEMINI \
    $GEMINI_SHARED_SKILL_OVERLAY_PATHS || drift=1
check_gemini_provider_skill_pairs || drift=1
check_shared_skill_pairs || drift=1
check_gemini_skill_owners || drift=1
check_gemini_file_owners || drift=1
check_pair "agents_extensions/shared/rules" ".gemini/rules" || drift=1

exit "$drift"
