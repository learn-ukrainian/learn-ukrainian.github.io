#!/usr/bin/env bash
# Deploy prompt/skill files from source dirs to agent dirs.
# Shows a diff summary before syncing so changes are auditable.
#
# Usage: scripts/deploy_prompts.sh [--dry-run]
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

# Step 1: Lint prompts (blocks deploy on failure)
echo "=== Lint prompts ==="
.venv/bin/python scripts/lint_prompts.py
echo ""

# Step 2: Show diffs before sync
echo "=== Deploy diff ==="
has_changes=false

diff_dirs() {
    local src="$1" dst="$2" label="$3"
    if [[ ! -d "$dst" ]]; then
        echo "  $label: destination does not exist yet (will be created)"
        has_changes=true
        return
    fi
    # Use diff -rq for a brief summary; ignore .DS_Store
    local diff_out
    diff_out=$(diff -rq --exclude='.DS_Store' "$src" "$dst" 2>/dev/null || true)
    if [[ -n "$diff_out" ]]; then
        echo "  $label:"
        echo "$diff_out" | head -30 | sed 's/^/    /'
        local count
        count=$(echo "$diff_out" | wc -l | tr -d ' ')
        if (( count > 30 )); then
            echo "    ... ($count total changes)"
        fi
        has_changes=true
    else
        echo "  $label: no changes"
    fi
}

diff_dirs "claude_extensions" ".claude" "claude_extensions → .claude"
diff_dirs "claude_extensions" ".agent" "claude_extensions → .agent"
diff_dirs "claude_extensions/commands" ".agent/workflows" "commands → .agent/workflows"
diff_dirs "gemini_extensions" ".gemini" "gemini_extensions → .gemini"
echo ""

if [[ "$has_changes" == false ]]; then
    echo "No changes to deploy."
    exit 0
fi

if [[ "$DRY_RUN" == true ]]; then
    echo "Dry run — no files synced."
    exit 0
fi

# Step 3: Sync
echo "=== Syncing ==="
rsync -av --delete claude_extensions/ .claude/
rsync -av --delete claude_extensions/ .agent/
rsync -av --delete claude_extensions/commands/ .agent/workflows/
rsync -av --delete gemini_extensions/ .gemini/
echo ""
echo "Deploy complete."
