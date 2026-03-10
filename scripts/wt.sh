#!/usr/bin/env bash
# Worktree helper — build-aware worktree management for safe code changes.
#
# Usage:
#   scripts/wt.sh create <issue-number> [description]  — create worktree for an issue
#   scripts/wt.sh list                                  — list active worktrees
#   scripts/wt.sh merge <issue-number>                  — merge worktree branch to main (build-aware)
#   scripts/wt.sh clean <issue-number>                  — remove worktree and branch
#   scripts/wt.sh status                                — show build status + active worktrees
#
# Workflow:
#   1. scripts/wt.sh create 817 "fix v4 terminology"
#   2. cd ../learn-ukrainian-wt-817 && make changes
#   3. git add/commit/push, create PR, get reviews
#   4. scripts/wt.sh merge 817   (safe during builds, blocks new builds)
#   5. scripts/wt.sh clean 817

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WT_BASE="$(dirname "$REPO_ROOT")"
API_BASE="http://localhost:8765"

red()    { printf '\033[0;31m%s\033[0m\n' "$*"; }
green()  { printf '\033[0;32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }
bold()   { printf '\033[1m%s\033[0m\n' "$*"; }

# Check for active builds — process detection (always works) + API (when available)
# Returns: 0 = no builds, 2 = builds active
# Prints build info to stdout when builds detected
check_active_builds() {
    local found=0

    # Method 1: Process detection (reliable, no server needed)
    local pids
    pids=$(pgrep -f 'build_module_v5\.py' 2>/dev/null || true)
    if [ -n "$pids" ]; then
        local -a pid_array
        mapfile -t pid_array <<< "$pids"
        local count=${#pid_array[@]}
        echo "  $count build_module_v5.py process(es) running (PIDs: ${pids//$'\n'/ })"
        found=1
    fi

    # Method 2: API check (skip health pre-check — curl already handles timeouts)
    local active
    active=$(curl -s --max-time 3 "$API_BASE/api/batch/active" 2>/dev/null || true)
    if [ -n "$active" ] && [ "$active" != "[]" ] && [ "$active" != "null" ]; then
        echo "  API reports active batch builds"
        found=1
    fi

    if [ $found -eq 1 ]; then
        return 2  # builds active
    fi
    return 0
}

# Capture build check result — avoids duplicating set +e/set -e pattern
# Sets BUILD_INFO and BUILD_RC in caller's scope
run_build_check() {
    set +e
    BUILD_INFO=$(check_active_builds 2>&1)
    BUILD_RC=$?
    set -e
}

cmd_create() {
    local issue="$1"
    local desc="${2:-issue-$issue}"
    local branch="fix/$issue-$(echo "$desc" | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g')"
    local wt_dir="$WT_BASE/learn-ukrainian-wt-$issue"

    if [ -d "$wt_dir" ]; then
        red "Worktree already exists: $wt_dir"
        exit 1
    fi

    bold "Creating worktree for #$issue..."
    cd "$REPO_ROOT"
    git worktree add -b "$branch" "$wt_dir" main
    green "Worktree created:"
    echo "  Branch: $branch"
    echo "  Path:   $wt_dir"
    echo ""
    echo "Next steps:"
    echo "  cd $wt_dir"
    echo "  # make changes, commit, push"
    echo "  git push -u origin $branch"
    echo "  gh pr create --title 'fix: description (#$issue)'"
}

cmd_list() {
    cd "$REPO_ROOT"
    bold "Active worktrees:"
    git worktree list
    echo ""

    bold "Build status:"
    run_build_check
    if [ $BUILD_RC -eq 0 ]; then
        green "No active builds"
    else
        yellow "Active builds:"
        echo "$BUILD_INFO"
    fi
}

cmd_merge() {
    local issue="$1"
    local wt_dir="$WT_BASE/learn-ukrainian-wt-$issue"
    local branch

    if [ ! -d "$wt_dir" ]; then
        red "No worktree found at $wt_dir"
        exit 1
    fi

    branch=$(git -C "$wt_dir" rev-parse --abbrev-ref HEAD)

    bold "Merging $branch to main..."

    # Check for uncommitted changes in worktree (single git call)
    if ! git -C "$wt_dir" diff --quiet HEAD 2>/dev/null; then
        red "Worktree has uncommitted changes. Commit or stash first."
        exit 1
    fi

    # Build awareness: merging is safe during builds, but inform the user
    run_build_check
    if [ $BUILD_RC -eq 2 ]; then
        yellow "Builds detected (merge is safe — code already loaded):"
        echo "$BUILD_INFO"
        yellow "Do NOT start new builds until merge + push completes."
        echo ""
        read -p "Continue merge? [y/N] " confirm
        if [ "${confirm:-n}" != "y" ] && [ "${confirm:-n}" != "Y" ]; then
            echo "Aborted."
            exit 0
        fi
    fi

    # Merge to main
    cd "$REPO_ROOT"
    git fetch origin main 2>/dev/null || true
    if ! git merge "$branch" --no-ff -m "Merge $branch into main

Closes #$issue"; then
        red "Merge failed — resolve conflicts, then: git merge --continue"
        exit 1
    fi

    green "Merged $branch into main"
    echo ""
    if [ $BUILD_RC -eq 2 ]; then
        red "REMINDER: Builds are running. Push now, but do NOT start new builds until current ones finish."
    fi
    echo "  git push origin main"
}

cmd_clean() {
    local issue="$1"
    local wt_dir="$WT_BASE/learn-ukrainian-wt-$issue"

    if [ ! -d "$wt_dir" ]; then
        yellow "No worktree at $wt_dir (may already be cleaned)"
    else
        local branch
        branch=$(git -C "$wt_dir" rev-parse --abbrev-ref HEAD)
        cd "$REPO_ROOT"
        git worktree remove "$wt_dir"
        git branch -d "$branch" 2>/dev/null || yellow "Branch $branch not deleted (may not be merged)"
        green "Worktree removed: $wt_dir"
    fi
}

cmd_status() {
    cmd_list

    echo ""
    bold "Recent commits on main:"
    cd "$REPO_ROOT"
    git log --oneline -5
}

# Main dispatch
case "${1:-help}" in
    create)
        [ -z "${2:-}" ] && { echo "Usage: wt.sh create <issue-number> [description]"; exit 1; }
        cmd_create "$2" "${3:-}"
        ;;
    list)
        cmd_list
        ;;
    merge)
        [ -z "${2:-}" ] && { echo "Usage: wt.sh merge <issue-number>"; exit 1; }
        cmd_merge "$2"
        ;;
    clean)
        [ -z "${2:-}" ] && { echo "Usage: wt.sh clean <issue-number>"; exit 1; }
        cmd_clean "$2"
        ;;
    status)
        cmd_status
        ;;
    *)
        echo "Usage: scripts/wt.sh {create|list|merge|clean|status}"
        echo ""
        echo "Commands:"
        echo "  create <issue> [desc]  Create worktree + branch for issue"
        echo "  list                   Show worktrees + build status"
        echo "  merge <issue>          Merge worktree branch to main"
        echo "  clean <issue>          Remove worktree + branch"
        echo "  status                 Full status overview"
        ;;
esac
