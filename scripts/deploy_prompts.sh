#!/usr/bin/env bash
# Deploy prompt/skill files from source dirs to agent dirs.
# Shows a diff summary before syncing so changes are auditable.
#
# Usage: scripts/deploy_prompts.sh [--dry-run]
#
# ── Protected paths ─────────────────────────────────────────────────
# Some paths live in the destination dirs but have NO equivalent in the
# source extensions/ dirs. rsync --delete would wipe them on every
# deploy, so we exclude them explicitly.
#
# Known orphan today:
#   .gemini/docs/{LINGUISTICS,TOOLS,WORKFLOW}.md — context files that
#   GEMINI.md tells Gemini to always read. They're tracked in git under
#   .gemini/docs/ and restored via `fix(bridge): restore .gemini/docs/
#   context files (#1127)`. They are NOT in gemini_extensions/ because
#   moving them would require a git mv + consumer path updates that
#   we haven't done yet.
#
# If you add another destination-only path, add it to ORPHAN_PATHS_<TARGET>
# below. The preflight assertion in step 0 will warn you if a new
# orphan appears without being declared.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

# Declared orphan paths (relative to destination). Space-separated.
# Format: paths that exist in destination but NOT in source. rsync
# --delete will skip these, preserving them on every deploy.
ORPHAN_PATHS_CLAUDE=""
ORPHAN_PATHS_AGENT=""
ORPHAN_PATHS_GEMINI="docs/"

# Build rsync --exclude arguments from a space-separated path list.
build_excludes() {
    local paths="$1"
    local args=""
    for p in $paths; do
        args+=" --exclude=$p"
    done
    echo "$args"
}

# Preflight assertion: warn if an undeclared orphan is in the destination
# but missing from source. This catches "someone dropped a new file in
# .gemini/ without updating ORPHAN_PATHS_GEMINI" situations before the
# next deploy silently deletes it.
check_orphans() {
    local src="$1" dst="$2" declared="$3" label="$4"
    [[ -d "$dst" ]] || return 0
    local orphans
    orphans=$(diff -rq --exclude='.DS_Store' "$src" "$dst" 2>/dev/null \
        | awk -v dst="$dst" '$0 ~ "^Only in "dst {sub("^Only in "dst"[/:]* *",""); sub(": ","/"); print}')
    for orphan in $orphans; do
        local matched=false
        for d in $declared; do
            # Match if orphan is exactly d or starts with d (for directories)
            if [[ "$orphan" == "$d" || "$orphan" == "$d"* || "$orphan/" == "$d" ]]; then
                matched=true
                break
            fi
        done
        if [[ "$matched" == false ]]; then
            echo "  ⚠️  $label: undeclared orphan '$orphan' in destination"
            echo "     rsync --delete would wipe this. Either:"
            echo "       1. Move it to the source extensions/ dir, OR"
            echo "       2. Add it to ORPHAN_PATHS_* in this script"
            return 1
        fi
    done
    return 0
}

# Step 0: Preflight — assert no undeclared orphan paths in destinations
echo "=== Preflight (orphan-path guard) ==="
orphan_fail=false
check_orphans "claude_extensions" ".claude" "$ORPHAN_PATHS_CLAUDE" "claude_extensions → .claude" || orphan_fail=true
check_orphans "claude_extensions" ".agent" "$ORPHAN_PATHS_AGENT" "claude_extensions → .agent" || orphan_fail=true
check_orphans "gemini_extensions" ".gemini" "$ORPHAN_PATHS_GEMINI" "gemini_extensions → .gemini" || orphan_fail=true
if [[ "$orphan_fail" == true ]]; then
    echo ""
    echo "❌ Deploy aborted: undeclared orphan paths would be deleted."
    exit 1
fi
echo "  ✅ All orphan paths are declared."
echo ""

# Step 1: Lint prompts (blocks deploy on failure)
echo "=== Lint prompts ==="
.venv/bin/python scripts/lint_prompts.py
echo ""

# Step 2: Show diffs before sync
echo "=== Deploy diff ==="
has_changes=false

diff_dirs() {
    local src="$1" dst="$2" label="$3" orphans="$4"
    if [[ ! -d "$dst" ]]; then
        echo "  $label: destination does not exist yet (will be created)"
        has_changes=true
        return
    fi
    # Use diff -rq for a brief summary; ignore .DS_Store and declared orphan
    # paths (they'd always show as "Only in <dst>..." noise)
    local diff_args=(-rq --exclude='.DS_Store')
    for p in $orphans; do
        # Strip trailing slash for diff --exclude
        diff_args+=(--exclude="${p%/}")
    done
    local diff_out
    diff_out=$(diff "${diff_args[@]}" "$src" "$dst" 2>/dev/null || true)
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

diff_dirs "claude_extensions" ".claude" "claude_extensions → .claude" "$ORPHAN_PATHS_CLAUDE"
diff_dirs "claude_extensions" ".agent" "claude_extensions → .agent" "$ORPHAN_PATHS_AGENT"
diff_dirs "gemini_extensions" ".gemini" "gemini_extensions → .gemini" "$ORPHAN_PATHS_GEMINI"
echo ""

if [[ "$has_changes" == false ]]; then
    echo "No changes to deploy."
    exit 0
fi

if [[ "$DRY_RUN" == true ]]; then
    echo "Dry run — no files synced."
    exit 0
fi

# Step 3: Sync — with per-target --exclude for declared orphan paths
echo "=== Syncing ==="
# shellcheck disable=SC2046  # intentional word-splitting of build_excludes output
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_CLAUDE") claude_extensions/ .claude/
# shellcheck disable=SC2046
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_AGENT") claude_extensions/ .agent/
# shellcheck disable=SC2046
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_GEMINI") gemini_extensions/ .gemini/
echo ""
echo "Deploy complete."
