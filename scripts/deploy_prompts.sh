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
# scheduled_tasks.lock is a runtime state file managed by Claude
# Code's task scheduler — it must never be deleted by the deploy
# script or in-flight scheduled tasks get orphaned.
ORPHAN_PATHS_CLAUDE="scheduled_tasks.lock worktrees"
# wake/  — scheduled-task state written by the Claude Code wake scheduler.
# cache/ — Monitor API client disk cache (see scripts/ai_agent_bridge/_monitor_cache.py),
#          stores rules.body/session.body + ETag metadata so cold-start is ~780 B instead of 75 KB.
#          Runtime-only; NOT source-tracked. rsync --delete must preserve both.
ORPHAN_PATHS_AGENT="wake cache"
ORPHAN_PATHS_AGENTS=""
# agents/curriculum-orchestrator.toml and agents/curriculum-writer.toml —
# Codex agent definitions with no claude_extensions equivalent.
# config.toml and hooks.json — Codex CLI configuration files managed directly by Codex.
ORPHAN_PATHS_CODEX="agents/curriculum-orchestrator.toml agents/curriculum-writer.toml config.toml hooks.json"
ORPHAN_PATHS_GEMINI="docs/ rules/"

# Claude Code auto-loads every unscoped file in `.claude/rules/` into
# the system prompt. These six always-load rules are now served by the
# Monitor API (`/api/rules?format=markdown`) and must not be deployed
# to the Claude target. Other targets still receive them from
# claude_extensions unchanged.
CLAUDE_RULE_AUTOLOAD_EXCLUDES=(
    "rules/critical-rules.md"
    "rules/non-negotiable-rules.md"
    "rules/workflow.md"
    "rules/delegate-must-use-worktree.md"
    "rules/cli-help-standard.md"
    "rules/model-assignment.md"
)
CLAUDE_RULE_AUTOLOAD_EXCLUDE_PATHS="${CLAUDE_RULE_AUTOLOAD_EXCLUDES[*]}"

# Build rsync --exclude arguments from a space-separated path list.
build_excludes() {
    local paths="$1"
    local args=""
    for p in $paths; do
        args+=" --exclude=$p"
    done
    echo "$args"
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
check_orphans "claude_extensions/skills" ".agents/skills" "$ORPHAN_PATHS_AGENTS" "claude_extensions/skills → .agents/skills" || orphan_fail=true
check_orphans "claude_extensions" ".codex" "$ORPHAN_PATHS_CODEX" "claude_extensions → .codex" || orphan_fail=true
check_orphans "gemini_extensions" ".gemini" "$ORPHAN_PATHS_GEMINI" "gemini_extensions → .gemini" || orphan_fail=true
check_orphans "claude_extensions/rules" ".gemini/rules" "" "claude_extensions/rules → .gemini/rules" || orphan_fail=true
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
    for p in $orphans; do
        # Strip trailing slash for diff --exclude
        diff_args+=(--exclude="${p%/}")
        if [[ "$p" == */* ]]; then
            diff_args+=(--exclude="${p##*/}")
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

diff_dirs \
    "claude_extensions" \
    ".claude" \
    "claude_extensions → .claude" \
    "$ORPHAN_PATHS_CLAUDE $CLAUDE_RULE_AUTOLOAD_EXCLUDE_PATHS"
diff_dirs "claude_extensions" ".agent" "claude_extensions → .agent" "$ORPHAN_PATHS_AGENT"
diff_dirs "claude_extensions/skills" ".agents/skills" "claude_extensions/skills → .agents/skills" "$ORPHAN_PATHS_AGENTS"
diff_dirs "claude_extensions" ".codex" "claude_extensions → .codex" "$ORPHAN_PATHS_CODEX"
diff_dirs "gemini_extensions" ".gemini" "gemini_extensions → .gemini" "$ORPHAN_PATHS_GEMINI"
diff_dirs "claude_extensions/rules" ".gemini/rules" "claude_extensions/rules → .gemini/rules" ""
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
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_CLAUDE $CLAUDE_RULE_AUTOLOAD_EXCLUDE_PATHS") claude_extensions/ .claude/
# shellcheck disable=SC2046
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_AGENT") claude_extensions/ .agent/
# shellcheck disable=SC2046
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_CODEX") claude_extensions/ .codex/
# shellcheck disable=SC2046
# rsync needs the destination's parent dir to exist before it can create
# `.agents/skills/`. On a clean checkout (e.g. the test fixture in
# tests/test_deploy_script_idempotency.py) `.agents/` does not exist yet,
# and rsync fails with `mkdir ".agents/skills" failed: No such file or
# directory (2)`. Pre-create the parent so a fresh clone works.
mkdir -p .agents
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_AGENTS") claude_extensions/skills/ .agents/skills/
# shellcheck disable=SC2046
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_GEMINI") gemini_extensions/ .gemini/
rsync -av --delete claude_extensions/rules/ .gemini/rules/
echo ""
echo "Deploy complete."
