#!/bin/bash
# Learn Ukrainian - Claude Code Wrapper
# Ensures skills are deployed and starts Claude

set -e

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

# Check for claude
if ! command -v claude &> /dev/null; then
    echo "Error: Claude CLI not found"
    echo "   Install with: npm install -g @anthropic-ai/claude-code"
    exit 1
fi
echo "Claude CLI found"

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

# Show level status from CLAUDE.md enrichment status table
if [ -f "CLAUDE.md" ]; then
    echo "   Enrichment Status:"
    # Extract only the enrichment status table (matches pattern: | Level | XX-YY | Status |)
    grep -E "^\| [ABC][12] \| [0-9]+-[0-9]+ \| " CLAUDE.md 2>/dev/null | while read line; do
        LEVEL=$(echo "$line" | cut -d'|' -f2 | xargs)
        MODULES=$(echo "$line" | cut -d'|' -f3 | xargs)
        STATUS=$(echo "$line" | cut -d'|' -f4 | xargs)
        echo "       $LEVEL ($MODULES): $STATUS"
    done
fi

# Count modules per level
echo "   Module counts:"
for level in a1 a2 b1 b2 c1 c2; do
    if [ -d "curriculum/l2-uk-en/$level" ]; then
        COUNT=$(ls -1 curriculum/l2-uk-en/$level/*.md 2>/dev/null | wc -l | xargs)
        LEVEL_UPPER=$(echo "$level" | tr 'a-z' 'A-Z')
        echo "       $LEVEL_UPPER: $COUNT modules"
    fi
done

echo "   Skills: grammar-check, module-architect, vocab-enrichment"
echo "   Commands:"
echo "       /module-create [level] [num]   - Full pipeline (4 stages)"
echo "       /module-stage-1..4 [level] [num] - Individual stages"
echo "       npm run generate, npm run vocab:enrich"

echo ""

# Start Claude
echo "Launching Claude Code..."
claude "$@"
