#!/bin/bash
# Learn Ukrainian - Codex Wrapper
# Default: starts Codex in a dedicated git worktree so it has its own
# .git/index and never races with another agent on git locks.
# Optional: pass --main (or set CODEX_TARGET=main) to run in the repository's
# primary main checkout instead when Codex needs to take over that workspace.

set -e

# Ensure common local bin paths are available
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
hash -r 2>/dev/null || true

# Get the checkout containing this script, then resolve the repository's
# primary main checkout so the launcher behaves consistently from any worktree.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
CODEX_TARGET="${CODEX_TARGET:-worktree}"
CODEX_ARGS=()

while [ "$#" -gt 0 ]; do
    case "$1" in
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
    if [ -d "$PROJECT_DIR/starlight/node_modules" ] && [ ! -e "$WORKTREE_DIR/starlight/node_modules" ]; then
        mkdir -p "$WORKTREE_DIR/starlight"
        ln -s "$PROJECT_DIR/starlight/node_modules" "$WORKTREE_DIR/starlight/node_modules"
        echo "Symlinked starlight/node_modules into worktree"
    fi

    # Symlink data/ (sources.db, vesum.db) so MCP tools work
    if [ ! -e "$WORKTREE_DIR/data" ]; then
        ln -s "$PROJECT_DIR/data" "$WORKTREE_DIR/data"
        echo "Symlinked data/ into worktree"
    fi

    TARGET_DIR="$WORKTREE_DIR"
fi

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

echo "Launching Codex in $CODEX_TARGET checkout..."
export CODEX_SESSION=1
codex --dangerously-bypass-approvals-and-sandbox -C "$TARGET_DIR" "${CODEX_ARGS[@]}"
