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
# written by agents (handoffs, dispatch-briefs, canaries, tmp/, etc.) must
# never be deleted by deploy. A deploy-owned manifest records exactly the
# source paths previously copied there. On a later deploy, only paths in that
# manifest which have disappeared from source may be reaped. This propagates
# retired hooks without treating a colliding namespace (such as prompts/) as
# wholly deploy-owned.
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
DEPLOY_STATE_DIR="${DEPLOY_STATE_DIR:-$PROJECT_ROOT/.deploy-state}"
AGENT_SHARED_MANIFEST="$DEPLOY_STATE_DIR/shared-to-agent.manifest"

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

# A manifest entry is TYPE<TAB>PATH, where TYPE is d, f, or l.  Paths are
# source-controlled, but validate persisted entries before acting on them so a
# corrupt local state file can never escape .agent/.
agent_manifest_path_is_safe() {
    local path="$1"
    [[ -n "$path" && "$path" != /* && "$path" != *$'\n'* && "$path" != *$'\t'* ]] || return 1
    case "/$path/" in
        *"//"*|*"/./"*|*"/../"*) return 1 ;;
    esac
}

# A lexically safe manifest path can still escape through a symlinked
# intermediate component.  This check is deliberately separate from the
# lexical check above: defence in depth matters because .agent/ is writable
# runtime state and its manifest is persisted locally.
#
# A manifest symlink entry is the one safe exception at the leaf: rm -f on the
# link removes the link itself and never follows it.  Every intermediate
# component must be a real directory, and all other leaf types must be real
# filesystem objects.  The resolved parent is then required to sit beneath the
# physical .agent/ root before any deletion is attempted.

shared_source_path_exists() {
    local relative="$1"
    [[ -e "$SHARED_EXTENSIONS/$relative" || -L "$SHARED_EXTENSIONS/$relative" ]]
}

write_current_shared_agent_paths() {
    local kind
    for kind in d f l; do
        (
            cd "$SHARED_EXTENSIONS"
            find . -mindepth 1 -type "$kind" -print
        ) | while IFS= read -r path; do
            agent_manifest_path_is_safe "${path#./}" || {
                echo "Cannot record unsafe shared source path: $path" >&2
                exit 1
            }
            printf '%s\t%s\n' "$kind" "${path#./}"
        done
    done
}

# Before this manifest existed, the only safe legacy paths to adopt are files
# whose bytes still match the last tracked source version deleted from Git.
# This lets the migration reap an old deployed hook on the *next* deploy while
# refusing to claim arbitrary .agent/ scratch as deploy-owned.
legacy_agent_file_matches_deleted_source() {
    local relative="$1" destination="$2" deletion_commit
    [[ -f "$destination" && ! -L "$destination" ]] || return 1
    git rev-parse --git-dir >/dev/null 2>&1 || return 1
    deletion_commit="$(git log --diff-filter=D --format=%H -1 -- "$SHARED_EXTENSIONS/$relative" 2>/dev/null)"
    [[ -n "$deletion_commit" ]] || return 1
    git show "$deletion_commit^:$SHARED_EXTENSIONS/$relative" 2>/dev/null | cmp -s - "$destination"
}

write_legacy_shared_agent_paths() {
    local source_path relative
    git rev-parse --git-dir >/dev/null 2>&1 || return 0
    git log -z --diff-filter=D --name-only --format= -- "$SHARED_EXTENSIONS" 2>/dev/null \
        | while IFS= read -r -d '' source_path; do
            case "$source_path" in
                "$SHARED_EXTENSIONS"/*) relative="${source_path#"$SHARED_EXTENSIONS/"}" ;;
                *) continue ;;
            esac
            agent_manifest_path_is_safe "$relative" || continue
            shared_source_path_exists "$relative" && continue
            if legacy_agent_file_matches_deleted_source "$relative" ".agent/$relative"; then
                printf 'f\t%s\n' "$relative"
            fi
        done
}

write_shared_agent_manifest() {
    local manifest_tmp
    mkdir -p "$DEPLOY_STATE_DIR"
    manifest_tmp="$(mktemp "$DEPLOY_STATE_DIR/shared-to-agent.manifest.XXXXXX")"
    write_current_shared_agent_paths >"$manifest_tmp"
    if [[ ! -f "$AGENT_SHARED_MANIFEST" ]]; then
        write_legacy_shared_agent_paths >>"$manifest_tmp"
    fi
    sort -u "$manifest_tmp" -o "$manifest_tmp"
    mv "$manifest_tmp" "$AGENT_SHARED_MANIFEST"
}

reap_retired_shared_agent_paths() {
    # Delegated to Python: the reap must not be redirectable between validation and
    # deletion. Shell can only validate a PATH and then delete by that same PATH, and
    # a review reproduced a symlink swapped in between those two steps deleting a file
    # OUTSIDE the repository. The helper walks components with O_NOFOLLOW|O_DIRECTORY
    # and unlinks relative to the resulting directory fd, so the entry removed is the
    # one inside the directory actually opened. See scripts/deploy/reap_agent_mirrors.py.
    "$PROJECT_ROOT/.venv/bin/python" "$PROJECT_ROOT/scripts/deploy/reap_agent_mirrors.py" \
        --agent-root .agent \
        --manifest "$AGENT_SHARED_MANIFEST" \
        --source-root "$SHARED_EXTENSIONS"
}

sync_shared_agent_mirror() {
    # The source is absolute because the helper fchdirs into a descriptor for
    # .agent before it execs rsync.  Passing . as the destination keeps the write
    # bound to that descriptor even if another agent swaps the .agent pathname.
    "$PROJECT_ROOT/.venv/bin/python" "$PROJECT_ROOT/scripts/deploy/sync_agent_mirror.py" \
        --source-root "$PROJECT_ROOT/$SHARED_EXTENSIONS" \
        --agent-root .agent
}

remove_claude_autoload_rules() {
    local p
    for p in "${CLAUDE_RULE_AUTOLOAD_EXCLUDES[@]}"; do
        rm -f ".claude/$p"
    done
}

# A destination-only path is a STALE DEPLOY ARTIFACT, not an undeclared
# orphan, when git shows the source path was tracked and has since been
# deleted. Removing the destination copy is the intended propagation of that
# deletion — aborting on it deadlocks every future deploy until a human
# hand-deletes the target file.
#
# Git is the SSOT, so git decides: tracked in HEAD -> still owned by source;
# absent from HEAD but deleted in history -> stale artifact. Anything git has
# never heard of stays an undeclared orphan and still aborts (fail-closed).
#
# Incident 2026-07-26: #5783 deleted hooks/guard-push-pytest.py from source.
# Every local deploy aborted from then on, so .claude/settings.json kept the
# retired hook registered and live. CI never caught it — CI deploys into a
# clean checkout where the gitignored destination trees carry no stale copy.
git_source_deleted() {
    local src="$1" rel="$2"
    git rev-parse --git-dir >/dev/null 2>&1 || return 1
    # Still tracked at HEAD → source owns it; not a deletion.
    git cat-file -e "HEAD:$src/$rel" 2>/dev/null && return 1
    # Absent from HEAD and history records a deletion → stale deploy artifact.
    [[ -n "$(git log --diff-filter=D --format=%H -1 -- "$src/$rel" 2>/dev/null)" ]]
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
        if [[ "$matched" == false ]] && git_source_deleted "$src" "$orphan"; then
            echo "  ♻️  $label: stale deploy artifact '$orphan' (deleted from source in git) — deploy will remove it"
            continue
        fi
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

# Verify that all hooks in source directories are executable on disk
echo "=== Verify hook permissions ==="
hook_perm_fail=false
for hook_dir in "$SHARED_EXTENSIONS/hooks" "gemini_extensions/hooks"; do
    if [[ -d "$hook_dir" ]]; then
        for hook in "$hook_dir"/*; do
            if [[ -f "$hook" && ! -x "$hook" ]]; then
                echo "  ❌ Hook file '$hook' is not executable." >&2
                hook_perm_fail=true
            fi
        done
    fi
done

if [[ "$hook_perm_fail" == true ]]; then
    echo "❌ Deploy aborted: Hook files must be executable." >&2
    exit 1
fi
echo "  ✅ All hook files are executable."
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
# .agent/ overlays source without --delete. A deploy-owned manifest reaps only
# retired paths which an earlier deploy recorded, preserving all other runtime
# scratch even when it shares a source directory such as prompts/. #4741
reap_retired_shared_agent_paths
# The .agent overlay is descriptor-bound all the way through rsync.  A late
# pathname check is not sufficient: another local agent can swap the directory
# after the check and redirect a path-based write outside this repository.
sync_shared_agent_mirror
write_shared_agent_manifest
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

# Ensure deployed hooks are executable in the destination
echo "=== Ensuring deployed hooks are executable ==="
for dest_hooks in .claude/hooks .agent/hooks .codex/hooks .gemini/hooks; do
    if [[ -d "$dest_hooks" ]]; then
        chmod +x "$dest_hooks"/* 2>/dev/null || true
    fi
done
echo "  ✅ Destination hooks verified/chmod'd."
echo ""

echo "Deploy complete."
