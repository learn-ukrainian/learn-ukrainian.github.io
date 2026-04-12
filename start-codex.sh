#!/bin/bash
# Learn Ukrainian - Codex Wrapper (worktree-isolated)
# Starts Codex in a git worktree so it has its own .git/index
# and never races with Claude Code on git locks.

set -e

# Ensure common local bin paths are available
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
hash -r 2>/dev/null || true

# Get script directory (project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKTREE_DIR="$PROJECT_DIR/.worktrees/codex-interactive"
WORKTREE_BRANCH="codex-interactive"

echo "Starting Codex in Learn Ukrainian project (worktree-isolated)..."
echo "Project: $PROJECT_DIR"

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

cd "$PROJECT_DIR"

if git rev-parse --git-dir > /dev/null 2>&1; then
    CURRENT_BRANCH=$(git branch --show-current)
    echo "Main checkout branch: $CURRENT_BRANCH"
fi

# ── Worktree setup ──────────────────────────────────────────────
# Creates a linked worktree at .worktrees/codex-interactive/ that
# shares the same git objects but has its OWN index file. This means
# Codex can run git status/add/commit freely without creating
# .git/index.lock races with Claude Code in the main checkout.
#
# The worktree tracks the same branch (main) and stays up to date
# via a pull before each launch.

if [ ! -d "$WORKTREE_DIR" ]; then
    echo "Creating Codex worktree at $WORKTREE_DIR..."
    # Create an orphan branch for the worktree (tracks main but has its own HEAD)
    git worktree add "$WORKTREE_DIR" HEAD --detach
    echo "Worktree created."
else
    echo "Codex worktree exists at $WORKTREE_DIR"
    # Update to latest main so Codex sees all recent commits
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

echo ""
echo "LEARN UKRAINIAN - Ukrainian Language Learning"
echo ""
echo "   Codex runs in worktree: $WORKTREE_DIR"
echo "   This isolates git operations from Claude Code's main checkout."
echo "   Any commits Codex makes stay in the worktree until you merge them."
echo ""
echo "   To pull latest from main into the worktree:"
echo "       cd $WORKTREE_DIR && git checkout --detach origin/main"
echo ""
echo "   To clean up the worktree when done:"
echo "       git worktree remove $WORKTREE_DIR"
echo ""

echo "Launching Codex in worktree..."
export CODEX_SESSION=1
codex --dangerously-bypass-approvals-and-sandbox -C "$WORKTREE_DIR" "$@"
