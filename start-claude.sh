#!/bin/bash
# Learn Ukrainian - Claude Code Wrapper
# Ensures skills are deployed and starts Claude

set -e

# Ensure ~/.local/bin is in PATH (where claude installs by default)
export PATH="$HOME/.local/bin:$PATH"
hash -r 2>/dev/null || true  # Clear command cache

# Get script directory (project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Claude in Learn Ukrainian project..."
echo "Project: $PROJECT_DIR"

# Preflight check: Verify required tools
echo "Preflight check..."
MISSING_TOOLS=""
for tool in git gh node npm; do
    if ! command -v $tool &> /dev/null; then
        MISSING_TOOLS="$MISSING_TOOLS $tool"
    fi
done

if [ -n "$MISSING_TOOLS" ]; then
    echo "Warning: Optional tools not found:$MISSING_TOOLS"
    echo "   (These are recommended but not required to start)"
fi

# Check for npx (required to run Claude Code)
if ! command -v npx &> /dev/null; then
    echo "Error: npx not found (install Node.js)"
    exit 1
fi
echo "npx found — will launch Claude Code via npx @latest"

# Change to project directory
cd "$PROJECT_DIR"

# Show current branch
if git rev-parse --git-dir > /dev/null 2>&1; then
    CURRENT_BRANCH=$(git branch --show-current)
    echo "Current branch: $CURRENT_BRANCH"

    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        echo "Uncommitted changes detected"
    fi
fi

# Deploy Claude skills (always run to ensure up-to-date)
if [ -f "package.json" ] && grep -q "claude:deploy" package.json 2>/dev/null; then
    echo "Checking Claude skills..."
    npm run claude:deploy --silent 2>/dev/null || true
    echo "Skills deployed"
fi

# Show project status
echo ""
echo "LEARN UKRAINIAN - Ukrainian Language Learning"

# Show completion status from CLAUDE.md
if [ -f "CLAUDE.md" ]; then
    echo "   Completion Status:"
    # Extract completion status (lines between "### Completion Status" and next "###")
    sed -n '/^### Completion Status/,/^###/p' CLAUDE.md 2>/dev/null | \
        grep -E "^- \*\*[ABC][12]" | \
        sed 's/^- /       /' | \
        head -4
fi

# Count modules per level
echo ""
echo "   Module counts:"
for level in a1 a2 b1 b2 c1 c2; do
    if [ -d "curriculum/l2-uk-en/$level" ]; then
        COUNT=$(ls -1 curriculum/l2-uk-en/$level/*.md 2>/dev/null | wc -l | xargs)
        LEVEL_UPPER=$(echo "$level" | tr 'a-z' 'A-Z')
        echo "       $LEVEL_UPPER: $COUNT modules"
    fi
done

# List available skills dynamically
echo ""
if [ -d ".claude/skills" ]; then
    SKILL_COUNT=$(ls -1d .claude/skills/*/ 2>/dev/null | wc -l | xargs)
    echo "   Skills ($SKILL_COUNT available):"
    ls -1 .claude/skills/ 2>/dev/null | head -5 | sed 's/^/       /'
    if [ "$SKILL_COUNT" -gt 5 ]; then
        echo "       ... and $((SKILL_COUNT - 5)) more"
    fi
fi

# List available commands dynamically
echo ""
if [ -d ".claude/commands" ]; then
    CMD_COUNT=$(ls -1 .claude/commands/*.md 2>/dev/null | wc -l | xargs)
    echo "   Commands ($CMD_COUNT available):"
    ls -1 .claude/commands/*.md 2>/dev/null | \
        sed 's|.claude/commands/||' | \
        sed 's|.md$||' | \
        sed 's/^/       \//' | \
        head -4
    if [ "$CMD_COUNT" -gt 4 ]; then
        echo "       ... and $((CMD_COUNT - 4)) more"
    fi
fi

echo ""
echo "   Quick reference: npm run generate, npm run vocab:enrich, npm run pipeline"

echo ""

# Autocompact at 75% of 1M context (~750K tokens)
# Balances: using the 1M window we pay for vs. leaving buffer before degradation
# Subagents handle isolated work in their own windows, so main thread stays clean
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=750000

# Launch via npx to avoid cache bugs (stale binary + prompt caching issues)
echo "Launching Claude Code via npx (cache-safe)..."
npx @anthropic-ai/claude-code@latest --chrome --permission-mode bypassPermissions "$@"
