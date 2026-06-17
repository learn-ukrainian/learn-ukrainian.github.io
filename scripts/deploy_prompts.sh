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

AGENT_EXTENSIONS_ROOT="agents_extensions"
SHARED_EXTENSIONS="$AGENT_EXTENSIONS_ROOT/shared"
CODEX_EXTENSIONS="$AGENT_EXTENSIONS_ROOT/codex"

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
# *-thread-bootstrap.md / *-thread-handoff.md / *-thread-lease.json — replacement-thread handoff
#          files generated into .agent/ by scripts/orchestration/thread_handoff.py.
#          Runtime-only, machine-specific (live timestamps + snapshot); NOT
#          source-tracked. Without these entries the deploy aborts on any
#          machine where the handoff automation has run.
# prompts/ — per-dispatch prompt files (.agent/prompts/<task_id>.md) written into
#          .agent/ by the dispatch tooling when a dispatch fires. Runtime-only,
#          NOT source-tracked. Without this entry the deploy aborts on any machine
#          where a dispatch has run since the last clean .agent/ deploy.
# tmp/ — runtime scratch (issue/PR draft bodies, transient tarballs) written into
#          .agent/ by orchestration tooling. Runtime-only, NOT source-tracked.
#          Same rationale as prompts/: declare so rsync --delete preserves it.
# *-brief.md / dispatch-*.md — transient dispatch briefs (.agent/atlas-3150-brief.md,
#          .agent/dispatch-3098-slice3.md) hand-authored by orchestrators when firing a
#          dispatch. Same category as prompts/ and tmp/: runtime-only scratch, NOT
#          source-tracked. Without these patterns a single in-flight brief aborts the
#          ENTIRE deploy (every target), so committed source prompt fixes silently never
#          reach .claude/ + .codex/ + .agent/ runtime — agents keep running stale prompts (#3456).
ORPHAN_PATHS_AGENT="wake cache prompts tmp *-thread-bootstrap.md *-thread-handoff.md *-thread-lease.json *-brief.md dispatch-*.md"
ORPHAN_PATHS_AGENTS=""
# agents/curriculum-orchestrator.toml and agents/curriculum-writer.toml —
# Codex agent definitions with no shared equivalent.
# memory/ — Codex-owned durable memory deployed from agents_extensions/codex/.
# config.toml and hooks.json — Codex CLI configuration files managed directly by Codex.
ORPHAN_PATHS_CODEX="agents/curriculum-orchestrator.toml agents/curriculum-writer.toml config.toml hooks.json memory"
# tmp/ — Gemini CLI runtime workspace (e.g. .gemini/tmp/learn-ukrainian/);
#        local working state, NOT a deploy artifact. Preserve across rsync --delete.
# config.yaml — repository-level Gemini Code Assist for GitHub configuration.
#        It disables GitHub PR reviews while preserving local Gemini CLI tooling.
ORPHAN_PATHS_GEMINI="config.yaml docs/ rules/ tmp/"

# Claude Code auto-loads every unscoped file in `.claude/rules/` into
# the system prompt. These six always-load rules are now served by the
# Monitor API (`/api/rules?format=markdown`) and must not be deployed
# to the Claude target. Other targets still receive them from
# agents_extensions/shared unchanged.
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
            if [[ "$orphan" == "$d" || "$orphan" == $d || "$orphan" == "$d"* || "$orphan/" == "$d" ]]; then
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
check_orphans "$SHARED_EXTENSIONS" ".claude" "$ORPHAN_PATHS_CLAUDE" "$SHARED_EXTENSIONS → .claude" || orphan_fail=true
check_orphans "$SHARED_EXTENSIONS" ".agent" "$ORPHAN_PATHS_AGENT" "$SHARED_EXTENSIONS → .agent" || orphan_fail=true
check_orphans "$SHARED_EXTENSIONS/skills" ".agents/skills" "$ORPHAN_PATHS_AGENTS" "$SHARED_EXTENSIONS/skills → .agents/skills" || orphan_fail=true
check_orphans "$SHARED_EXTENSIONS" ".codex" "$ORPHAN_PATHS_CODEX" "$SHARED_EXTENSIONS → .codex" || orphan_fail=true
check_orphans "gemini_extensions" ".gemini" "$ORPHAN_PATHS_GEMINI" "gemini_extensions → .gemini" || orphan_fail=true
check_orphans "$SHARED_EXTENSIONS/rules" ".gemini/rules" "" "$SHARED_EXTENSIONS/rules → .gemini/rules" || orphan_fail=true
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

diff_dirs \
    "$SHARED_EXTENSIONS" \
    ".claude" \
    "$SHARED_EXTENSIONS → .claude" \
    "$ORPHAN_PATHS_CLAUDE $CLAUDE_RULE_AUTOLOAD_EXCLUDE_PATHS"
diff_dirs "$SHARED_EXTENSIONS" ".agent" "$SHARED_EXTENSIONS → .agent" "$ORPHAN_PATHS_AGENT"
diff_dirs "$SHARED_EXTENSIONS/skills" ".agents/skills" "$SHARED_EXTENSIONS/skills → .agents/skills" "$ORPHAN_PATHS_AGENTS"
diff_dirs "$SHARED_EXTENSIONS" ".codex" "$SHARED_EXTENSIONS → .codex" "$ORPHAN_PATHS_CODEX"
if [[ -d "$CODEX_EXTENSIONS" ]]; then
    diff_overlay_files "$CODEX_EXTENSIONS" ".codex" "$CODEX_EXTENSIONS → .codex"
fi
diff_dirs "gemini_extensions" ".gemini" "gemini_extensions → .gemini" "$ORPHAN_PATHS_GEMINI"
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
# shellcheck disable=SC2046
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_AGENT") "$SHARED_EXTENSIONS/" .agent/
# shellcheck disable=SC2046
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_CODEX") "$SHARED_EXTENSIONS/" .codex/
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
rsync -av --delete $(build_excludes "$ORPHAN_PATHS_GEMINI") gemini_extensions/ .gemini/
rsync -av --delete "$SHARED_EXTENSIONS/rules/" .gemini/rules/
echo ""
echo "Deploy complete."
