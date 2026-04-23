#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

ORPHAN_PATHS_AGENT="wake cache"
ORPHAN_PATHS_GEMINI="docs/"

drift_found=false

check_sync() {
    local src="$1"
    local dst="$2"
    local label="$3"
    local orphans="$4"
    local source_hint="$5"

    if [[ ! -d "$src" ]]; then
        echo "::error::Missing source directory for $label: $src"
        drift_found=true
        return
    fi

    if [[ ! -d "$dst" ]]; then
        echo "Skipping $label: destination $dst is not present in this checkout."
        return
    fi

    local diff_args=(-rq --exclude='.DS_Store')
    for p in $orphans; do
        diff_args+=(--exclude="${p%/}")
    done

    local diff_out
    diff_out=$(diff "${diff_args[@]}" "$src" "$dst" || true)
    if [[ -z "$diff_out" ]]; then
        echo "OK: $label"
        return
    fi

    drift_found=true
    echo "::error::Rules/prompts drift detected for $label. Run 'npm run claude:deploy' and commit the deployed mirror."
    echo "Files out of sync:"
    echo "$diff_out"
    echo "Fix: edit the source in $source_hint, then run \`npm run claude:deploy\`,"
    echo "commit both $source_hint and the deployed mirror."
    echo "See: claude_extensions/rules/critical-rules.md §1."
    echo ""
}

check_sync "claude_extensions/rules" ".claude/rules" "claude_extensions/rules -> .claude/rules" "" "claude_extensions/rules/"
check_sync "claude_extensions/rules" ".agent/rules" "claude_extensions/rules -> .agent/rules" "$ORPHAN_PATHS_AGENT" "claude_extensions/rules/"
check_sync "gemini_extensions" ".gemini" "gemini_extensions -> .gemini" "$ORPHAN_PATHS_GEMINI" "gemini_extensions/"

if [[ "$drift_found" == true ]]; then
    exit 1
fi

echo "All deployed prompt/rule mirrors are in sync."
