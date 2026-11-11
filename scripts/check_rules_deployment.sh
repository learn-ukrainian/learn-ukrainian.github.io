#!/usr/bin/env bash
# Verify that scripts/deploy_prompts.sh produced destination trees that
# match the source extensions it actually manages.
#
# Run this after scripts/deploy_prompts.sh. It does not run the deploy.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# The machinery package directory this script sits in, from its own location, so
# the commands printed below name it in either checkout layout.
MACHINERY_REL="$(basename "$(cd "$(dirname "$0")" && pwd)")"
cd "$PROJECT_ROOT"

# shellcheck disable=SC1091
source "$PROJECT_ROOT/scripts/deploy_orphan_paths.sh"

# Entries are anchored at the target root, exactly as deploy excludes them.
path_matches_declared_entry() {
    declared_paths_match "$1" "$2"
}

tracked_mirror_source() {
    local mirror="$1"
    local relative

    case "$mirror" in
        .claude/*)
            relative="${mirror#.claude/}"
            path_matches_declared_entry "$relative" "$ORPHAN_PATHS_CLAUDE" && return 1
            path_matches_declared_entry "$relative" "$CLAUDE_RULE_AUTOLOAD_EXCLUDE_PATHS" && return 1
            printf '%s\n' "agents_extensions/shared/$relative"
            ;;
        .agent/*)
            relative="${mirror#.agent/}"
            [[ -e "agents_extensions/shared/$relative" || -L "agents_extensions/shared/$relative" ]] || return 1
            printf '%s\n' "agents_extensions/shared/$relative"
            ;;
        .agents/skills/*)
            relative="${mirror#.agents/skills/}"
            path_matches_declared_entry "$relative" "$ORPHAN_PATHS_AGENTS" && return 1
            printf '%s\n' "agents_extensions/shared/skills/$relative"
            ;;
        .codex/*)
            relative="${mirror#.codex/}"
            path_matches_declared_entry "$relative" "$ORPHAN_PATHS_CODEX" && return 1
            if path_matches_declared_entry "$relative" "$CODEX_OVERLAY_PATHS"; then
                printf '%s\n' "agents_extensions/codex/$relative"
            else
                printf '%s\n' "agents_extensions/shared/$relative"
            fi
            ;;
        *) return 1 ;;
    esac
}

check_tracked_mirrors() {
    local mirror source failed=0
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        echo "::error::Tracked-mirror verification requires a Git checkout."
        return 1
    fi

    while IFS= read -r -d '' mirror; do
        source="$(tracked_mirror_source "$mirror" || true)"
        [[ -n "$source" ]] || continue
        if [[ ! -e "$source" && ! -L "$source" ]]; then
            echo "::error::Tracked deploy mirror has no canonical source: $mirror (expected $source)"
            failed=1
        elif ! cmp -s "$source" "$mirror"; then
            echo "::error::Committed deploy-mirror drift: $source -> $mirror"
            failed=1
        fi
    done < <(git ls-files -z -- .claude .agent .agents .codex)

    if [[ "$failed" -eq 0 ]]; then
        echo "OK: committed deploy mirrors match their canonical sources"
    fi
    return "$failed"
}

if [[ "${1:-}" == "--tracked-mirrors-only" ]]; then
    check_tracked_mirrors
    exit $?
elif [[ $# -ne 0 ]]; then
    echo "Usage: $MACHINERY_REL/check_rules_deployment.sh [--tracked-mirrors-only]" >&2
    exit 2
fi

check_pair() {
    local src="$1"
    local dst="$2"
    shift 2

    local diff_args=(-rq -x .DS_Store)
    local name
    while IFS= read -r name; do
        diff_args+=(-x "$name")
    done < <(declared_diff_excludes "$src" "$dst" "$*")
    if [[ ! -d "$src" ]]; then
        echo "::error::Source dir missing: $src"
        return 1
    fi

    if [[ ! -d "$dst" ]]; then
        echo "::error::Deploy did not create target: $dst"
        return 1
    fi

    local diff_out
    diff_out=$(diff "${diff_args[@]}" "$src" "$dst" | filter_pycache_only_diff || true)
    if [[ -n "$diff_out" ]]; then
        echo "::error::Deploy-script drift between $src and $dst:"
        echo "$diff_out"
        echo
        echo "This means $MACHINERY_REL/deploy_prompts.sh is out of sync with its source."
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
        bytecode_cache_path "$rel" && continue
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
        echo "This means $MACHINERY_REL/deploy_prompts.sh is out of sync with its source overlay."
        return 1
    fi

    echo "OK: $src -> $dst"
}

drift=0
# Duplicate skill discovery is an error even when the two copies agree.
if [[ -e .codex/skills || -L .codex/skills ]]; then
    echo "::error::Legacy .codex/skills discovery path remains; run $MACHINERY_REL/deploy_prompts.sh and reconcile any unverified content."
    drift=1
fi

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
    $CODEX_OVERLAY_PATHS \
    $CODEX_DISCOVERY_EXCLUDES || drift=1
check_overlay "agents_extensions/codex" ".codex" || drift=1
# shellcheck disable=SC2086
check_pair "agents_extensions/shared/skills" ".agents/skills" $ORPHAN_PATHS_AGENTS || drift=1

exit "$drift"
