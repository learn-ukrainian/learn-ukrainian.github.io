#!/usr/bin/env bash
# Single-source orphan allowlist for scripts/deploy_prompts.sh and
# scripts/check_rules_deployment.sh.
#
# Pure variable assignments — no side effects. Source from both consumers;
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
# agents/curriculum-orchestrator.toml and agents/curriculum-writer.toml —
# Codex agent definitions with no source equivalent.
# config.toml — Codex CLI configuration managed directly by Codex.
ORPHAN_PATHS_CODEX="agents/curriculum-orchestrator.toml agents/curriculum-writer.toml config.toml settings.local.json"

# --- deploy-owned: Codex overlay paths (checker mirrors for .codex drift) ---
# Managed by agents_extensions/codex/, not by the shared tree. Exclude them from
# the shared rsync/delete pass, then verify them with the overlay drift check.
# hooks.json is intentionally here, not in ORPHAN_PATHS_CODEX.
CODEX_OVERLAY_PATHS="hooks.json memory"

# --- gemini_extensions → .gemini ---
# tmp/ — Gemini CLI runtime workspace (e.g. .gemini/tmp/learn-ukrainian/);
#        local working state, NOT a deploy artifact. Preserve across rsync --delete.
# config.yaml — repository-level Gemini Code Assist for GitHub configuration.
#        It disables GitHub PR reviews while preserving local Gemini CLI tooling.
ORPHAN_PATHS_GEMINI="config.yaml docs/ rules/ tmp/"

# --- deploy-owned: Claude autoload excludes (checker mirrors for .claude drift) ---
# Claude Code auto-loads every unscoped file in `.claude/rules/` into the system
# prompt. These always-load rules are served by the Monitor API and must not be
# deployed to the Claude target. Other targets still receive them from shared.
CLAUDE_RULE_AUTOLOAD_EXCLUDES=(
    "rules/critical-rules.md"
    "rules/non-negotiable-rules.md"
    "rules/workflow.md"
    "rules/delegate-must-use-worktree.md"
    "rules/cli-help-standard.md"
    "rules/model-assignment.md"
    "rules/operator-expectations.md"
)
CLAUDE_RULE_AUTOLOAD_EXCLUDE_PATHS="${CLAUDE_RULE_AUTOLOAD_EXCLUDES[*]}"
