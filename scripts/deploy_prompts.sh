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
# .agent/ is special (preserve-by-default since #4741): runtime scratch
# written by agents (handoffs, dispatch-briefs, canaries, tmp/, etc.)
# must never be deleted by deploy. We rsync WITHOUT --delete for .agent/
# so the preflight orphan check and ORPHAN_PATHS_AGENT no longer apply to it.
# Source content (if any) from agents_extensions/shared is overlaid.
#
# For other targets, if you add a destination-only path, add it to
# ORPHAN_PATHS_<TARGET> in scripts/deploy_orphan_paths.sh.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# shellcheck disable=SC1091
source "$PROJECT_ROOT/scripts/deploy_orphan_paths.sh"

AGENT_EXTENSIONS_ROOT="agents_extensions"
SHARED_EXTENSIONS="$AGENT_EXTENSIONS_ROOT/shared"
CODEX_EXTENSIONS="$AGENT_EXTENSIONS_ROOT/codex"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

# Build rsync --exclude arguments from a space-separated path list.
build_excludes() {
    local paths="$1"
    local args=""
    for p in $paths; do
        args+=" --exclude=$p"
    done
    echo "$args"
}

build_shared_skill_overlay_excludes() {
    local shared_skill
    for shared_skill in "$SHARED_EXTENSIONS"/skills/*; do
        [[ -d "$shared_skill" ]] || continue
        echo "--exclude=/skills/$(basename "$shared_skill")/"
    done
}

remove_claude_autoload_rules() {
    local p
    for p in "${CLAUDE_RULE_AUTOLOAD_EXCLUDES[@]}"; do
        rm -f ".claude/$p"
    done
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
            if [[ "$orphan" == "$d" || "$orphan" == $d || "$orphan" == "$d"* || "$orphan/" == "$d" ]]; then
                matched=true
                break
            fi
        done
        if [[ "$matched" == false ]]; then
            echo "  ⚠️  $label: undeclared orphan '$orphan' in destination"
            echo "     rsync --delete would wipe this. Either:"
            echo "       1. Move it to the source extensions/ dir, OR"
            echo "       2. Add it to ORPHAN_PATHS_* in scripts/deploy_orphan_paths.sh"
            return 1
        fi
    done
    return 0
}

check_shared_skill_collisions() {
    local shared_skill skill_name
    for shared_skill in "$SHARED_EXTENSIONS"/skills/*; do
        [[ -d "$shared_skill" ]] || continue
        skill_name="$(basename "$shared_skill")"
        if [[ -e "gemini_extensions/skills/$skill_name" ]]; then
            echo "  ⚠️  shared/Gemini skill collision: $skill_name"
            echo "     Keep one canonical source; rename or remove the provider-specific duplicate."
            return 1
        fi
    done
    return 0
}

# Step 0: Preflight — assert no undeclared orphan paths in destinations
echo "=== Preflight (orphan-path guard) ==="
orphan_fail=false
check_orphans "$SHARED_EXTENSIONS" ".claude" "$ORPHAN_PATHS_CLAUDE" "$SHARED_EXTENSIONS → .claude" || orphan_fail=true
# .agent/ is preserve-by-default (runtime state written by agents/lanes).
# No orphan check or --delete here — see #4741. Shared source (if any)
# is overlaid; everything else in .agent/ is left alone.
check_orphans "$SHARED_EXTENSIONS/skills" ".agents/skills" "$ORPHAN_PATHS_AGENTS" "$SHARED_EXTENSIONS/skills → .agents/skills" || orphan_fail=true
check_orphans "$SHARED_EXTENSIONS" ".codex" "$ORPHAN_PATHS_CODEX $CODEX_OVERLAY_PATHS" "$SHARED_EXTENSIONS → .codex" || orphan_fail=true
check_orphans "gemini_extensions" ".gemini" "$ORPHAN_PATHS_GEMINI $GEMINI_SHARED_SKILL_OVERLAY_PATHS" "gemini_extensions → .gemini" || orphan_fail=true
check_orphans "$SHARED_EXTENSIONS/rules" ".gemini/rules" "" "$SHARED_EXTENSIONS/rules → .gemini/rules" || orphan_fail=true
check_shared_skill_collisions || orphan_fail=true
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

echo "=== Lint agent skills ==="
.venv/bin/python scripts/lint/lint_agent_skills.py
echo ""

if [[ "$DRY_RUN" == false ]]; then
    remove_claude_autoload_rules
fi

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
    local normalized
    for p in $orphans; do
        # Strip trailing slash for diff --exclude
        normalized="${p%/}"
        # A subtree declaration such as skills/* must exclude the subtree
        # root. Passing its basename ("*") to diff would mask every path.
        if [[ "$normalized" == */\* ]]; then
            normalized="${normalized%/\*}"
        fi
        diff_args+=(--exclude="$normalized")
        if [[ "$normalized" == */* ]]; then
            diff_args+=(--exclude="${normalized##*/}")
        fi
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

diff_overlay_files() {
    local src="$1" dst="$2" label="$3"
    if [[ ! -d "$dst" ]]; then
        echo "  $label: destination does not exist yet (will be created)"
        has_changes=true
        return
    fi

    local diff_out=""
    local rel
    while IFS= read -r rel; do
        if [[ ! -f "$dst/$rel" ]]; then
            diff_out+="Only in $src: $rel"$'\n'
        elif ! cmp -s "$src/$rel" "$dst/$rel"; then
            diff_out+="Files $src/$rel and $dst/$rel differ"$'\n'
        fi
    done < <(cd "$src" && find . -type f ! -name '.DS_Store' -print | sed 's#^\./##' | sort)

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

diff_shared_skill_overlays() {
    local shared_skill skill_name
    for shared_skill in "$SHARED_EXTENSIONS"/skills/*; do
        [[ -d "$shared_skill" ]] || continue
        skill_name="$(basename "$shared_skill")"
        diff_dirs \
            "$shared_skill" \
            ".gemini/skills/$skill_name" \
            "$shared_skill → .gemini/skills/$skill_name" \
            ""
    done
}

diff_gemini_skill_owners() {
    local deployed_skill skill_name
    [[ -d .gemini/skills ]] || return 0
    for deployed_skill in .gemini/skills/*; do
        [[ -d "$deployed_skill" ]] || continue
        skill_name="$(basename "$deployed_skill")"
        if [[ ! -d "$SHARED_EXTENSIONS/skills/$skill_name" && ! -d "gemini_extensions/skills/$skill_name" ]]; then
            echo "  .gemini/skills: stale unowned skill '$skill_name' (will be removed)"
            has_changes=true
        fi
    done
}

diff_dirs \
    "$SHARED_EXTENSIONS" \
    ".claude" \
    "$SHARED_EXTENSIONS → .claude" \
    "$ORPHAN_PATHS_CLAUDE $CLAUDE_RULE_AUTOLOAD_EXCLUDE_PATHS"
# .agent/ diff is best-effort (no declared orphans, preserve-by-default)
diff_dirs "$SHARED_EXTENSIONS" ".agent" "$SHARED_EXTENSIONS → .agent" ""
diff_dirs "$SHARED_EXTENSIONS/skills" ".agents/skills" "$SHARED_EXTENSIONS/skills → .agents/skills" "$ORPHAN_PATHS_AGENTS"
diff_dirs "$SHARED_EXTENSIONS" ".codex" "$SHARED_EXTENSIONS → .codex" "$ORPHAN_PATHS_CODEX $CODEX_OVERLAY_PATHS"
if [[ -d "$CODEX_EXTENSIONS" ]]; then
    diff_overlay_files "$CODEX_EXTENSIONS" ".codex" "$CODEX_EXTENSIONS → .codex"
fi
diff_overlay_files "gemini_extensions" ".gemini" "gemini_extensions → .gemini"
diff_shared_skill_overlays
diff_gemini_skill_owners
diff_dirs "$SHARED_EXTENSIONS/rules" ".gemini/rules" "$SHARED_EXTENSIONS/rules → .gemini/rules" ""
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
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_CLAUDE $CLAUDE_RULE_AUTOLOAD_EXCLUDE_PATHS") "$SHARED_EXTENSIONS/" .claude/
# .agent/ uses plain rsync (no --delete) — runtime scratch is preserve-by-default.
# Source files from agents_extensions/shared are overlaid if present; agent-written
# files (dispatch briefs, canaries, handoffs, tmp/, etc.) are never deleted. #4741
rsync -av "$SHARED_EXTENSIONS/" .agent/
# shellcheck disable=SC2046
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_CODEX $CODEX_OVERLAY_PATHS") "$SHARED_EXTENSIONS/" .codex/
if [[ -d "$CODEX_EXTENSIONS" ]]; then
    rsync -av "$CODEX_EXTENSIONS/" .codex/
fi
# shellcheck disable=SC2046
# rsync needs the destination's parent dir to exist before it can create
# `.agents/skills/`. On a clean checkout (e.g. the test fixture in
# tests/test_deploy_script_idempotency.py) `.agents/` does not exist yet,
# and rsync fails with `mkdir ".agents/skills" failed: No such file or
# directory (2)`. Pre-create the parent so a fresh clone works.
mkdir -p .agents
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_AGENTS") "$SHARED_EXTENSIONS/skills/" .agents/skills/
# shellcheck disable=SC2046
rsync -av --delete \
    $(build_excludes "$ORPHAN_PATHS_GEMINI") \
    $(build_shared_skill_overlay_excludes) \
    gemini_extensions/ .gemini/
for shared_skill in "$SHARED_EXTENSIONS"/skills/*; do
    [[ -d "$shared_skill" ]] || continue
    skill_name="$(basename "$shared_skill")"
    mkdir -p ".gemini/skills/$skill_name"
    rsync -av --delete "$shared_skill/" ".gemini/skills/$skill_name/"
done
rsync -av --delete "$SHARED_EXTENSIONS/rules/" .gemini/rules/
echo ""
echo "Deploy complete."
