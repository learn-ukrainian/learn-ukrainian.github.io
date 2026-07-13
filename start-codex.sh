#!/bin/bash
# Learn Ukrainian - Codex Wrapper
# Default: starts Codex in a dedicated git worktree so it has its own
# .git/index and never races with another agent on git locks.
# Optional: pass --main (or set CODEX_TARGET=main) to run in the repository's
# primary main checkout instead when Codex needs to take over that workspace.

set -e

# shellcheck source=scripts/lib/thread_rollover_link.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/scripts/lib/thread_rollover_link.sh"

# Ensure common local bin paths are available
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
hash -r 2>/dev/null || true

# Get the checkout containing this script, then resolve the repository's
# primary main checkout so the launcher behaves consistently from any worktree.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
CODEX_TARGET="${CODEX_TARGET:-worktree}"
CODEX_ARGS=()
CODEX_FLAGS=(--dangerously-bypass-approvals-and-sandbox --search)

if [ "${CODEX_ENABLE_MULTI_AGENT:-1}" != "0" ]; then
    CODEX_FLAGS+=(--enable multi_agent)
fi

while [ "$#" -gt 0 ]; do
    case "$1" in
        --help-wrapper)
            cat <<'EOF'
Usage: ./start-codex.sh [--main|--worktree] [codex args...]

Learn Ukrainian Codex launcher:
 - runs Codex in .worktrees/codex-interactive by default
 - use --main only when intentionally running in the primary checkout
 - always adds --dangerously-bypass-approvals-and-sandbox
 - always adds --search (live web search; user-policy 2026-05-08)
 - enables Codex multi-agent support by default
 - set CODEX_ENABLE_MULTI_AGENT=0 to disable multi-agent support
 - forwards all other arguments to codex unchanged
EOF
            exit 0
            ;;
        --main)
            CODEX_TARGET="main"
            shift
            ;;
        --worktree)
            CODEX_TARGET="worktree"
            shift
            ;;
        *)
            CODEX_ARGS+=("$1")
            shift
            ;;
    esac
done

case "$CODEX_TARGET" in
    main|worktree)
        ;;
    *)
        echo "Error: CODEX_TARGET must be 'main' or 'worktree' (got '$CODEX_TARGET')"
        exit 1
        ;;
esac

echo "Starting Codex in Learn Ukrainian project..."
echo "Launcher checkout: $SCRIPT_DIR"

echo "Preflight check..."
MISSING_TOOLS=""
for tool in git gh codex; do
    if ! command -v "$tool" &> /dev/null; then
        MISSING_TOOLS="$MISSING_TOOLS $tool"
    fi
done

if [ -n "$MISSING_TOOLS" ]; then
    echo "Error: Required tools not found:$MISSING_TOOLS"
    exit 1
fi

if git -C "$SCRIPT_DIR" rev-parse --git-dir > /dev/null 2>&1; then
    MAIN_WORKTREE_DIR=$(
        git -C "$SCRIPT_DIR" worktree list --porcelain | awk '
            $1 == "worktree" { path = $2 }
            $1 == "branch" && $2 == "refs/heads/main" { print path; exit }
        '
    )
    if [ -n "$MAIN_WORKTREE_DIR" ]; then
        PROJECT_DIR="$MAIN_WORKTREE_DIR"
    fi
fi

WORKTREE_DIR="$PROJECT_DIR/.worktrees/codex-interactive"

echo "Project root: $PROJECT_DIR"
echo "Target checkout: $CODEX_TARGET"

cd "$PROJECT_DIR"

if git rev-parse --git-dir > /dev/null 2>&1; then
    CURRENT_BRANCH=$(git branch --show-current)
    echo "Primary checkout branch: $CURRENT_BRANCH"
fi

TARGET_DIR="$PROJECT_DIR"

if [ "$CODEX_TARGET" = "worktree" ]; then
    # ── Worktree setup ──────────────────────────────────────────────
    # Creates a linked worktree at .worktrees/codex-interactive/ that
    # shares the same git objects but has its OWN index file. This means
    # Codex can run git status/add/commit freely without creating
    # .git/index.lock races with other agents in the main checkout.
    #
    # The worktree tracks the same branch (main) and stays up to date
    # via a detached checkout before each launch.
    if [ ! -d "$WORKTREE_DIR" ]; then
        echo "Creating Codex worktree at $WORKTREE_DIR..."
        git worktree add "$WORKTREE_DIR" HEAD --detach
        echo "Worktree created."
    else
        echo "Codex worktree exists at $WORKTREE_DIR"
        cd "$WORKTREE_DIR"
        git checkout --detach origin/main 2>/dev/null || git checkout --detach HEAD
        cd "$PROJECT_DIR"
        echo "Worktree updated to latest."
    fi

    # Symlink .venv into the worktree so Codex has the same Python env
    if [ ! -e "$WORKTREE_DIR/.venv" ]; then
        ln -s "$PROJECT_DIR/.venv" "$WORKTREE_DIR/.venv"
        echo "Symlinked .venv into worktree"
    fi

    # Symlink node_modules so npm/vitest work
    if [ -d "$PROJECT_DIR/site/node_modules" ] && [ ! -e "$WORKTREE_DIR/site/node_modules" ]; then
        mkdir -p "$WORKTREE_DIR/site"
        ln -s "$PROJECT_DIR/site/node_modules" "$WORKTREE_DIR/site/node_modules"
        echo "Symlinked site/node_modules into worktree"
    fi

    # Symlink data/ (sources.db, vesum.db) so MCP tools work
    if [ ! -e "$WORKTREE_DIR/data" ]; then
        ln -s "$PROJECT_DIR/data" "$WORKTREE_DIR/data"
        echo "Symlinked data/ into worktree"
    fi

    # Bridge only the canonical rollover directory, never the whole .agent tree.
    ensure_thread_rollover_link "$PROJECT_DIR" "$WORKTREE_DIR"
    echo "Verified .agent/thread-rollovers canonical bridge"

    TARGET_DIR="$WORKTREE_DIR"
fi

# Deploy shared agent extensions into ignored runtime dirs for the checkout
# Codex will actually use. This keeps .codex/.agents generated while
# agents_extensions/ remains the tracked source of truth. Fail-honest: a
# failing deploy prints a loud banner + the real output instead of the old
# silent `|| true` that claimed success over stale deploy targets.
# shellcheck source=scripts/lib/deploy_extensions.sh
source "$PROJECT_DIR/scripts/lib/deploy_extensions.sh"
deploy_agent_extensions "$TARGET_DIR" agents:deploy \
    || echo "Continuing launch despite deploy failure (see banner above)."

echo ""
echo "LEARN UKRAINIAN - Ukrainian Language Learning"
echo ""
if [ "$CODEX_TARGET" = "worktree" ]; then
    echo "   Codex runs in worktree: $WORKTREE_DIR"
    echo "   This isolates git operations from the main checkout."
    echo "   Any commits Codex makes stay in the worktree until you merge them."
    echo ""
    echo "   To pull latest from main into the worktree:"
    echo "       cd $WORKTREE_DIR && git checkout --detach origin/main"
    echo ""
    echo "   To clean up the worktree when done:"
    echo "       git worktree remove $WORKTREE_DIR"
else
    echo "   Codex runs in the main checkout: $PROJECT_DIR"
    echo "   Use this when Codex needs to continue work directly in main."
    echo "   Git operations here are not isolated from other agents."
fi
echo ""
if [ "${CODEX_ENABLE_MULTI_AGENT:-1}" != "0" ]; then
    echo "   Multi-agent: enabled"
else
    echo "   Multi-agent: disabled"
fi
echo ""

echo "Launching Codex in $CODEX_TARGET checkout..."
export CODEX_SESSION=1
export CODEX_CANONICAL_REPO_ROOT="$PROJECT_DIR"
codex "${CODEX_FLAGS[@]}" -C "$TARGET_DIR" "${CODEX_ARGS[@]}"
