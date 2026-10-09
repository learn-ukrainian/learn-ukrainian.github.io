#!/usr/bin/env bash
# Single-source orphan allowlist for scripts/deploy_prompts.sh and
# scripts/check_rules_deployment.sh.
#
# Variable assignments plus bytecode_cache_path(). Source from consumers;
# do not execute directly.
#
# Declared orphan paths (relative to destination). Space-separated.
# Format: paths that exist in destination but NOT in source. rsync
# --delete will skip these, preserving them on every deploy.

# --- shared → .claude ---
# scheduled_tasks.lock is a runtime state file managed by Claude
# Code's task scheduler — it must never be deleted by the deploy
# script or in-flight scheduled tasks get orphaned.
# *-epic/ — curriculum-track driver handoffs (CLAUDE-DRIVER-HANDOFF.md), e.g.
#          folk-epic/ bio-epic/ atlas-epic/. Live here as gitignored LOCAL state,
#          NOT a source artifact (user policy 2026-06-23: driver handoffs out of
#          git/PRs, in .claude/). Runtime-only, machine-specific. Declared as a
#          GLOB so rsync --delete preserves them AND future epics don't re-break
#          deploy (the enumerated form silently orphaned atlas-epic — a new epic
#          the allowlist hadn't been told about — aborting every deploy).
# settings.local.json — machine-local agent settings, UNTRACKED since 2026-07-07
#          (#4717, public-repo privacy: carries local absolute paths). The deployed
#          target copies are the live runtime config and must survive rsync --delete
#          now that the shared source copy is gone from git/disk.
ORPHAN_PATHS_CLAUDE="scheduled_tasks.lock worktrees *-epic settings.local.json"

# --- shared → .agent ---
# .agent/ is preserve-by-default (see #4741 and deploy_prompts.sh).
# Runtime scratch (handoffs, dispatch-briefs, canaries, tmp/, wake/, cache/, etc.)
# is never deleted by deploy rsync. The previous ORPHAN_PATHS_AGENT list and
# --delete handling have been removed; only source content (if any) from
# agents_extensions/shared is overlaid on top.
# (Old list retained for test/docs compatibility; .agent/ no longer uses it.)
ORPHAN_PATHS_AGENT=""  # .agent/ is preserve-by-default (#4741); see deploy_prompts.sh
# (historical) ORPHAN_PATHS_AGENT="wake cache prompts tmp *-thread-bootstrap.md *-handoff.md *-thread-lease.json *-brief.md dispatch-*.md dispatch-briefs canary-*.json settings.local.json"

# --- shared/skills → .agents/skills ---
ORPHAN_PATHS_AGENTS=""

# --- shared → .codex (rsync orphan excludes only; overlay paths below) ---
# settings.local.json is machine-local runtime configuration.
# retired-skills/ retains atomically captured legacy discovery trees, including
# concurrent writes. Deploy never deletes or overwrites this recovery storage.
ORPHAN_PATHS_CODEX="settings.local.json retired-skills"

# --- deploy-owned: Codex overlay paths (checker mirrors for .codex drift) ---
# Managed by agents_extensions/codex/, not by the shared tree. Exclude them from
# the shared rsync/delete pass, then verify them with the overlay drift check.
# hooks.json and config.toml are intentionally here, not in ORPHAN_PATHS_CODEX.
CODEX_OVERLAY_PATHS="config.toml hooks.json memory"

# --- gemini_extensions → .gemini ---
# tmp/ — Gemini CLI runtime workspace (e.g. .gemini/tmp/learn-ukrainian/);
#        local working state, NOT a deploy artifact. Preserve across rsync --delete.
# config.yaml — repository-level Gemini Code Assist for GitHub configuration.
#        It disables GitHub PR reviews while preserving local Gemini CLI tooling.
ORPHAN_PATHS_GEMINI="config.yaml docs/ rules/ tmp/"

# Shared skills overlay into .gemini/skills. Gemini-specific skills remain
# sourced from gemini_extensions/skills; shared skill names are overlaid after
# that sync. The glob is a preflight/diff exclusion only and MUST NOT be passed
# to the gemini_extensions rsync --exclude list.
GEMINI_SHARED_SKILL_OVERLAY_PATHS="skills/*"

# --- deploy-owned: Claude autoload excludes (checker mirrors for .claude drift) ---
# Claude Code auto-loads every unscoped file in `.claude/rules/` into the system
# prompt. These always-load rules are served by the Monitor API and must not be
# deployed to the Claude target. Other targets still receive them from shared.
CLAUDE_RULE_AUTOLOAD_EXCLUDES=(
    "rules/critical-rules.md"
    "rules/non-negotiable-rules.md"
    "rules/workflow.md"
    "rules/fleet-comms-coordination.md"
    "rules/delegate-must-use-worktree.md"
    "rules/cli-help-standard.md"
    "rules/model-assignment.md"
    "rules/catalog-routing-tables.md"
    "rules/operator-expectations.md"
    "rules/fleet-driver-routing.md"
    # Draft rules core and its content-seat addendum: stay out of Claude autoload
    # until their loading contract lands.
    "rules/core.md"
    "rules/core-curriculum.md"
)
CLAUDE_RULE_AUTOLOAD_EXCLUDE_PATHS="${CLAUDE_RULE_AUTOLOAD_EXCLUDES[*]}"

# Codex discovers shared skills only via .agents/skills. Preserve the legacy
# path from rsync deletion; capture verified copies into retained storage.
CODEX_DISCOVERY_EXCLUDES="skills"

# Every declared entry above is anchored at its target root. A glob never
# crosses a "/": *-epic names .claude/atlas-epic/, never
# .claude/skills/drive-epic/. deploy_prompts.sh passes each entry to rsync as
# --exclude=/<entry>; the bash matchers below apply the same rule.

# True when RELATIVE (a path under a target root) is ENTRY or a descendant.
declared_path_match() {
    local relative="$1" entry="${2%/}" slashes rest head prefix="" i
    slashes="${entry//[^\/]/}"
    rest="$relative"
    for ((i = 0; i <= ${#slashes}; i++)); do
        [[ -n "$rest" ]] || return 1
        head="${rest%%/*}"
        if [[ "$rest" == */* ]]; then rest="${rest#*/}"; else rest=""; fi
        prefix+="${prefix:+/}$head"
    done
    # PREFIX has exactly as many components as ENTRY, so no * spans a "/".
    # shellcheck disable=SC2053
    [[ "$prefix" == $entry ]]
}

# True when RELATIVE matches any entry of a space-separated list.
declared_paths_match() {
    local relative="$1" entries="$2" entry
    local -
    set -f
    for entry in $entries; do
        declared_path_match "$relative" "$entry" && return 0
    done
    return 1
}

# Print one `diff --exclude` name per line for declared entries of SRC → DST.
# diff matches an exclude against every basename in the tree, so a glob is
# expanded to the concrete top-level names it matches; *-epic must not hide
# skills/drive-epic from the drift report. A subtree entry such as skills/*
# excludes its root, and a nested entry excludes its own basename.
declared_diff_excludes() {
    local src="$1" dst="$2" entries="$3" entry path
    local -
    set -f
    for entry in $entries; do
        entry="${entry%/}"
        [[ "$entry" == */\* ]] && entry="${entry%/\*}"
        if [[ "$entry" == */* ]]; then
            printf '%s\n' "${entry##*/}"
        elif [[ "$entry" == *[\*\?\[]* ]]; then
            set +f
            for path in "$src"/$entry "$dst"/$entry; do
                [[ -e "$path" || -L "$path" ]] && printf '%s\n' "${path##*/}"
            done
            set -f
        else
            printf '%s\n' "$entry"
        fi
    done
}

# Interpreter cache written beside deployed hooks (#9108). Not declared runtime
# state. rsync has no name rule for these: a *.pyc pattern also matches a
# directory or a symlink, and would omit real source content. The preflight and
# this diff filter ignore only a regular non-symlink file ending in .pyc, plus
# a __pycache__ directory whose entries are all such files. --delete removes a
# destination-only regular cache when a real sync runs.
BYTECODE_CACHE_EXCLUDES=('*.pyc')

# True for a path whose final component is *.pyc or exactly __pycache__.
# Callers still have to check the file type. A directory or symlink keeps its
# own name and is not cache.
bytecode_cache_path() {
    local base="${1##*/}"
    case "$base" in
        *.pyc | __pycache__) return 0 ;;
    esac
    return 1
}

# A regular file, not a symlink. -f follows links, so the -L test comes first.
regular_file() {
    [[ -f "$1" && ! -L "$1" ]]
}

# Drop diff lines that are only regular bytecode files.
filter_pycache_only_diff() {
    local line parent name path left right rest
    while IFS= read -r line || [[ -n "$line" ]]; do
        case "$line" in
            "Files "*.pyc" and "*.pyc" differ")
                rest="${line#Files }"
                rest="${rest% differ}"
                left="${rest%% and *}"
                right="${rest#* and }"
                if regular_file "$left" && regular_file "$right"; then
                    continue
                fi
                ;;
            "Only in "*": "*)
                parent="${line#"Only in "}"
                parent="${parent%": "*}"
                name="${line##*: }"
                path="$parent/$name"
                if [[ "$name" == *.pyc ]] && regular_file "$path"; then
                    continue
                fi
                if [[ "$name" == "__pycache__" && -d "$path" && ! -L "$path" ]] \
                    && ! find "$path" -mindepth 1 \( -type l -o ! -type f -o ! -name '*.pyc' \) -print -quit | grep -q .; then
                    continue
                fi
                ;;
        esac
        printf '%s\n' "$line"
    done
}
