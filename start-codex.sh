#!/bin/bash
# Learn Ukrainian - Codex Wrapper
# Starts Codex in this project with explicit sandbox defaults

set -e

# Ensure common local bin paths are available
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
hash -r 2>/dev/null || true

# Get script directory (project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Codex in Learn Ukrainian project..."
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
    echo "Current branch: $CURRENT_BRANCH"

    if [ -n "$(git status --porcelain)" ]; then
        echo "Uncommitted changes detected"
    fi
fi

echo ""
echo "LEARN UKRAINIAN - Ukrainian Language Learning"
echo ""
echo "   Codex startup defaults:"
echo "       Interactive Codex: dangerous bypass"
echo "       dispatch.py Codex subprocesses: repo defaults unless env overrides are set"
echo "       ai_agent_bridge Codex subprocesses: repo defaults unless env overrides are set"
echo ""
echo "   Quick reference: npm run generate, npm run vocab:enrich, npm run pipeline"
echo ""

echo "Launching Codex with dangerous sandbox bypass..."
export CODEX_SESSION=1
codex --dangerously-bypass-approvals-and-sandbox -C "$PROJECT_DIR" "$@"
